use std::error::Error;
use std::io::{Cursor, Write};

use hwpx_package::{
    AssetDisposition, AssetLimits, AssetPlan, AssetStoreAdapter, BoundedZipReader,
    IMAGE_HWPX_PROFILE_ID, IMAGE_HWPX_SCHEMA_VERSION, IdIndex, IdIndexLimits, IdRuleProfile,
    ImageAssetBinding, ImageCrop, ImageGeometry, ImageHwpxBuilder, ImageHwpxError,
    ImageHwpxLimitConfig, ImageHwpxLimits, ImageHwpxLowerer, ImageHwpxReader, ImageHwpxRequest,
    ImageHwpxRequestDraft, ImageHwpxSource, ImageLinkMode, PackageGraph, PackageGraphLimits,
    PackageLimits, PatchLimits, PreservingWriter, WriterLimits,
};
use serde_json::Value;
use zip::write::SimpleFileOptions;
use zip::{CompressionMethod, ZipWriter};

type TestResult = Result<(), Box<dyn Error>>;
type TestReader = BoundedZipReader<Cursor<Vec<u8>>>;

const FLOW_BEFORE: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const FLOW_AFTER: &str = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
const SECTION_PATH: &str = "Contents/section0.xml";
const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const SECTION_NS: &str = "http://www.hancom.co.kr/hwpml/2011/section";

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
  <h:borderFill id="1"/>
  <h:charPr id="1" borderFillIDRef="1"><h:fontRef hangul="1" latin="1" hanja="1" japanese="1" other="1" symbol="1" user="1"/></h:charPr>
  <h:tabPr id="1"/><h:numbering id="1"/><h:bullet id="1"/>
  <h:paraPr id="1" tabPrIDRef="1"><h:heading type="OUTLINE" idRef="0"/><h:paraHead charPrIDRef="1"/></h:paraPr>
  <h:style id="1" charPrIDRef="1" paraPrIDRef="1" nextStyleIDRef="1"/><h:memoShape id="1"/>
</h:head>"#;

#[test]
fn new_png_is_lowered_atomically_and_full_artifact_reopens() -> TestResult {
    let payload = png(4, 3);
    let (mut reader, graph) = open_graph(valid_archive(&empty_section(), None)?)?;
    let plan = AssetStoreAdapter::default().build("image/png", &payload, &graph)?;
    assert_eq!(plan.disposition(), AssetDisposition::AddNew);
    let limits = ImageHwpxLimits::default();
    let source = inspect(&mut reader, &graph, &limits)?;
    let request = request(&source, &plan, geometry(4, 3), "도표 & 설명", &limits)?;
    let lowered = ImageHwpxLowerer::lower(&mut reader, &graph, &request, FLOW_BEFORE, limits)?;

    assert_eq!(lowered.patch().changed_parts(), 2);
    assert_eq!(lowered.patch().added_parts(), 1);
    assert!(lowered.receipt().preservation_verified());
    assert!(lowered.receipt().static_readback_verified());
    assert!(lowered.receipt().relationship_closure_verified());
    assert!(lowered.receipt().render_required());
    assert_ne!(
        lowered.receipt().output_section_sha256(),
        source.section_sha256()
    );
    let artifact = PreservingWriter::build(
        lowered.patch(),
        PackageLimits::default(),
        PackageGraphLimits::default(),
        IdIndexLimits::default(),
        WriterLimits::default(),
    )?;
    artifact.verify()?;
    Ok(())
}

#[test]
fn existing_asset_is_reused_without_manifest_or_part_mutation() -> TestResult {
    let payload = png(2, 2);
    let (mut reader, graph) = open_graph(valid_archive(&empty_section(), Some(&payload))?)?;
    let plan = AssetStoreAdapter::default().build("image/png", &payload, &graph)?;
    assert_eq!(plan.disposition(), AssetDisposition::ReusedExisting);
    let limits = ImageHwpxLimits::default();
    let source = inspect(&mut reader, &graph, &limits)?;
    let request = request(&source, &plan, geometry(2, 2), "기존 그림", &limits)?;
    let lowered = ImageHwpxLowerer::lower(&mut reader, &graph, &request, FLOW_BEFORE, limits)?;
    assert_eq!(lowered.patch().changed_parts(), 1);
    assert_eq!(lowered.patch().added_parts(), 0);
    assert!(lowered.receipt().relationship_closure_verified());
    Ok(())
}

#[test]
fn crop_dpi_alt_text_and_native_shape_are_strictly_read() -> TestResult {
    let payload = png(8, 6);
    let graph = open_graph(valid_archive(&empty_section(), None)?)?.1;
    let plan = AssetStoreAdapter::default().build("image/png", &payload, &graph)?;
    let asset = ImageAssetBinding::from_plan(&plan);
    let geometry = ImageGeometry {
        width_hwpunit: 9_000,
        height_hwpunit: 4_500,
        dpi_x: 144,
        dpi_y: 288,
        crop: ImageCrop {
            left_px: 1,
            top_px: 1,
            right_px: 7,
            bottom_px: 5,
        },
        render_required: true,
    };
    let section = native_picture_section(&asset, &geometry, "대체 &lt;설명&gt;", 77, 88);
    let readback = ImageHwpxReader::read_in_section(
        section.as_bytes(),
        0,
        &asset,
        &geometry,
        "대체 <설명>",
        ImageHwpxLimits::default(),
    )?;
    assert_eq!(readback.object_id(), 77);
    assert_eq!(readback.instance_id(), 88);
    assert_eq!(readback.geometry(), &geometry);
    assert_eq!(readback.asset(), &asset);
    assert_eq!(readback.picture_count(), 1);
    assert_eq!(readback.native_object_count(), 1);
    assert_eq!(readback.native_instance_count(), 1);

    for drifted in [
        section.replace("right=\"350\"", "right=\"351\""),
        section.replace("dimwidth=\"400\"", "dimwidth=\"401\""),
        section.replace("대체 &lt;설명&gt;", "변조"),
        section.replace("effect=\"REAL_PIC\"", "effect=\"GRAY_SCALE\""),
    ] {
        assert_code(
            ImageHwpxReader::read_in_section(
                drifted.as_bytes(),
                0,
                &asset,
                &geometry,
                "대체 <설명>",
                ImageHwpxLimits::default(),
            ),
            "image_hwpx_readback_mismatch",
        );
    }
    Ok(())
}

#[test]
fn unsupported_link_geometry_and_alt_text_fail_closed() -> TestResult {
    let payload = png(2, 2);
    let (mut reader, graph) = open_graph(valid_archive(&empty_section(), None)?)?;
    let plan = AssetStoreAdapter::default().build("image/png", &payload, &graph)?;
    let limits = ImageHwpxLimits::default();
    let source = inspect(&mut reader, &graph, &limits)?;

    let mut draft = request_draft(&source, &plan, geometry(2, 2), "설명");
    draft.link_mode = ImageLinkMode::Link;
    assert_code(
        ImageHwpxRequest::from_draft(draft, &source, &plan, FLOW_BEFORE, limits),
        "image_hwpx_unsupported_link_mode",
    );

    let mut bad_geometry = geometry(2, 2);
    bad_geometry.crop.right_px = 3;
    assert_code(
        ImageHwpxRequest::from_draft(
            request_draft(&source, &plan, bad_geometry, "설명"),
            &source,
            &plan,
            FLOW_BEFORE,
            limits,
        ),
        "image_hwpx_invalid_geometry",
    );
    assert_code(
        ImageHwpxRequest::from_draft(
            request_draft(&source, &plan, geometry(2, 2), " \t"),
            &source,
            &plan,
            FLOW_BEFORE,
            limits,
        ),
        "image_hwpx_invalid_alt_text",
    );
    Ok(())
}

#[test]
fn request_and_lowerer_recheck_source_flow_and_asset_drift() -> TestResult {
    let first_payload = png(2, 2);
    let second_payload = png(3, 2);
    let (mut reader, graph) = open_graph(valid_archive(&empty_section(), None)?)?;
    let adapter = AssetStoreAdapter::default();
    let first_plan = adapter.build("image/png", &first_payload, &graph)?;
    let second_plan = adapter.build("image/png", &second_payload, &graph)?;
    let limits = ImageHwpxLimits::default();
    let source = inspect(&mut reader, &graph, &limits)?;

    let mut source_drift = request_draft(&source, &first_plan, geometry(2, 2), "설명");
    source_drift.expected_run_sha256 = "0".repeat(64);
    assert_code(
        ImageHwpxRequest::from_draft(source_drift, &source, &first_plan, FLOW_BEFORE, limits),
        "image_hwpx_source_drift",
    );
    assert_code(
        ImageHwpxRequest::from_draft(
            request_draft(&source, &first_plan, geometry(2, 2), "설명"),
            &source,
            &first_plan,
            &"c".repeat(64),
            limits,
        ),
        "image_hwpx_flow_drift",
    );
    assert_code(
        ImageHwpxRequest::from_draft(
            request_draft(&source, &first_plan, geometry(2, 2), "설명"),
            &source,
            &second_plan,
            FLOW_BEFORE,
            limits,
        ),
        "image_hwpx_asset_drift",
    );

    let request = request(&source, &first_plan, geometry(2, 2), "설명", &limits)?;
    assert_code(
        ImageHwpxLowerer::lower(&mut reader, &graph, &request, &"d".repeat(64), limits),
        "image_hwpx_flow_drift",
    );
    let drifted_section = empty_section().replace("styleIDRef=\"1\"", "styleIDRef=\"01\"");
    let (mut drifted_reader, drifted_graph) = open_graph(valid_archive(&drifted_section, None)?)?;
    assert_code(
        ImageHwpxLowerer::lower(
            &mut drifted_reader,
            &drifted_graph,
            &request,
            FLOW_BEFORE,
            limits,
        ),
        "image_hwpx_source_drift",
    );
    Ok(())
}

#[test]
fn object_and_instance_collisions_and_nonempty_anchor_fail_closed() -> TestResult {
    let payload = png(2, 2);
    let occupied = empty_section().replace(
        "</hs:sec>",
        "<q:p id=\"2\"><q:run charPrIDRef=\"1\"><q:equation id=\"77\"/><q:t/></q:run></q:p></hs:sec>",
    );
    let (mut reader, graph) = open_graph(valid_archive(&occupied, None)?)?;
    let plan = AssetStoreAdapter::default().build("image/png", &payload, &graph)?;
    let limits = ImageHwpxLimits::default();
    let source = inspect(&mut reader, &graph, &limits)?;
    let request = request(&source, &plan, geometry(2, 2), "설명", &limits)?;
    assert_code(
        ImageHwpxLowerer::lower(&mut reader, &graph, &request, FLOW_BEFORE, limits),
        "image_hwpx_object_id_collision",
    );

    let nonempty = empty_section().replace("<q:t/>", "<q:t>existing</q:t>");
    let (mut nonempty_reader, nonempty_graph) = open_graph(valid_archive(&nonempty, None)?)?;
    assert_code(
        ImageHwpxBuilder::inspect_source(
            &mut nonempty_reader,
            &nonempty_graph,
            SECTION_PATH,
            0,
            0,
            limits,
        ),
        "image_hwpx_unsupported_target",
    );
    Ok(())
}

#[test]
fn strict_json_duplicate_unknown_and_limits_are_rejected() -> TestResult {
    let payload = png(2, 2);
    let (mut reader, graph) = open_graph(valid_archive(&empty_section(), None)?)?;
    let plan = AssetStoreAdapter::default().build("image/png", &payload, &graph)?;
    let limits = ImageHwpxLimits::default();
    let source = inspect(&mut reader, &graph, &limits)?;
    let request = request(&source, &plan, geometry(2, 2), "설명", &limits)?;
    let json = request.canonical_json(limits)?;
    let loaded = ImageHwpxRequest::from_json(&json, &source, &plan, FLOW_BEFORE, limits)?;
    assert_eq!(loaded.canonical_json(limits)?, json);

    let mut duplicate = String::from_utf8(json.clone())?;
    duplicate.insert_str(
        1,
        &format!("\"schema_version\":\"{IMAGE_HWPX_SCHEMA_VERSION}\","),
    );
    assert_code(
        ImageHwpxRequest::from_json(duplicate.as_bytes(), &source, &plan, FLOW_BEFORE, limits),
        "image_hwpx_invalid_json",
    );
    let mut unknown: Value = serde_json::from_slice(&json)?;
    unknown["unknown"] = Value::Bool(true);
    assert_code(
        ImageHwpxRequest::from_json(
            &serde_json::to_vec(&unknown)?,
            &source,
            &plan,
            FLOW_BEFORE,
            limits,
        ),
        "image_hwpx_invalid_json",
    );
    assert_code(
        ImageHwpxRequest::from_json(&[], &source, &plan, FLOW_BEFORE, limits),
        "image_hwpx_input_limit",
    );
    assert_code(
        ImageHwpxLimits::new(
            ImageHwpxLimitConfig {
                dpi: 0,
                ..ImageHwpxLimitConfig::default()
            },
            PackageLimits::default(),
            PackageGraphLimits::default(),
            IdIndexLimits::default(),
            PatchLimits::default(),
            AssetLimits::default(),
        ),
        "image_hwpx_invalid_limit",
    );
    Ok(())
}

#[test]
fn picture_id_profile_closes_manifest_reference_and_rejects_tamper() -> TestResult {
    let payload = png(2, 2);
    let (_, graph) = open_graph(valid_archive(&empty_section(), Some(&payload))?)?;
    let plan = AssetStoreAdapter::default().build("image/png", &payload, &graph)?;
    let section = native_picture_section(
        &ImageAssetBinding::from_plan(&plan),
        &geometry(2, 2),
        "설명",
        77,
        88,
    );
    let (mut reader, graph) = open_graph(valid_archive(&section, Some(&payload))?)?;
    let index = IdIndex::build(
        &mut reader,
        &graph,
        IdRuleProfile::hwpml_2011_picture_v5(),
        IdIndexLimits::default(),
    )?;
    assert_eq!(index.profile_version(), "hwpml-2011-picture-static/v5");

    let dangling = section.replace(plan.relationship_id(), "missing-resource");
    let bytes = valid_archive(&dangling, Some(&payload))?;
    let (mut dangling_reader, dangling_graph) = open_graph(bytes)?;
    let result = IdIndex::build(
        &mut dangling_reader,
        &dangling_graph,
        IdRuleProfile::hwpml_2011_picture_v5(),
        IdIndexLimits::default(),
    );
    assert!(result.is_err());
    Ok(())
}

#[test]
fn canonical_outputs_are_deterministic_and_debug_is_redacted() -> TestResult {
    let payload = png(2, 2);
    let (mut reader, graph) = open_graph(valid_archive(&empty_section(), None)?)?;
    let plan = AssetStoreAdapter::default().build("image/png", &payload, &graph)?;
    let limits = ImageHwpxLimits::default();
    let source = inspect(&mut reader, &graph, &limits)?;
    let request = request(&source, &plan, geometry(2, 2), "SECRET_ALT", &limits)?;
    assert_eq!(
        request.canonical_json(limits)?,
        request.canonical_json(limits)?
    );
    for debug in [format!("{source:?}"), format!("{request:?}")] {
        for secret in [
            "SECRET_ALT",
            source.section_part(),
            source.section_sha256(),
            plan.relationship_id(),
            plan.target_path().as_str(),
            plan.content_sha256(),
        ] {
            assert!(!debug.contains(secret), "debug leaked {secret}: {debug}");
        }
    }
    Ok(())
}

fn inspect(
    reader: &mut TestReader,
    graph: &PackageGraph,
    limits: &ImageHwpxLimits,
) -> Result<ImageHwpxSource, ImageHwpxError> {
    ImageHwpxBuilder::inspect_source(reader, graph, SECTION_PATH, 0, 0, *limits)
}

fn request(
    source: &ImageHwpxSource,
    plan: &AssetPlan,
    geometry: ImageGeometry,
    alt_text: &str,
    limits: &ImageHwpxLimits,
) -> Result<ImageHwpxRequest, ImageHwpxError> {
    ImageHwpxRequest::from_draft(
        request_draft(source, plan, geometry, alt_text),
        source,
        plan,
        FLOW_BEFORE,
        *limits,
    )
}

fn request_draft(
    source: &ImageHwpxSource,
    plan: &AssetPlan,
    geometry: ImageGeometry,
    alt_text: &str,
) -> ImageHwpxRequestDraft {
    ImageHwpxRequestDraft {
        schema_version: IMAGE_HWPX_SCHEMA_VERSION.to_owned(),
        profile_id: IMAGE_HWPX_PROFILE_ID.to_owned(),
        section_part: source.section_part().to_owned(),
        paragraph_ordinal: 0,
        run_ordinal: 0,
        expected_package_state_sha256: source.package_state_sha256().to_owned(),
        expected_section_sha256: source.section_sha256().to_owned(),
        expected_paragraph_sha256: source.paragraph_sha256().to_owned(),
        expected_run_sha256: source.run_sha256().to_owned(),
        expected_object_ids_sha256: source.object_ids_sha256().to_owned(),
        expected_instance_ids_sha256: source.instance_ids_sha256().to_owned(),
        expected_document_flow_sha256: FLOW_BEFORE.to_owned(),
        target_document_flow_sha256: FLOW_AFTER.to_owned(),
        object_id: 77,
        instance_id: 88,
        link_mode: ImageLinkMode::Embed,
        geometry,
        alt_text: alt_text.to_owned(),
        asset: ImageAssetBinding::from_plan(plan),
    }
}

fn geometry(width_px: u32, height_px: u32) -> ImageGeometry {
    ImageGeometry {
        width_hwpunit: 7_200,
        height_hwpunit: 3_600,
        dpi_x: 96,
        dpi_y: 96,
        crop: ImageCrop::full(width_px, height_px),
        render_required: true,
    }
}

fn empty_section() -> String {
    format!(
        "<hs:sec xmlns:hs=\"{SECTION_NS}\" xmlns:q=\"{PARAGRAPH_NS}\"><q:p id=\"1\" paraPrIDRef=\"1\" styleIDRef=\"1\"><q:run charPrIDRef=\"1\"><q:t/></q:run></q:p></hs:sec>"
    )
}

fn native_picture_section(
    asset: &ImageAssetBinding,
    geometry: &ImageGeometry,
    alt_xml: &str,
    object_id: u32,
    instance_id: u32,
) -> String {
    let clip_left = (u64::from(geometry.crop.left_px) * 7_200 + u64::from(geometry.dpi_x) / 2)
        / u64::from(geometry.dpi_x);
    let clip_right = (u64::from(geometry.crop.right_px) * 7_200 + u64::from(geometry.dpi_x) / 2)
        / u64::from(geometry.dpi_x);
    let clip_top = (u64::from(geometry.crop.top_px) * 7_200 + u64::from(geometry.dpi_y) / 2)
        / u64::from(geometry.dpi_y);
    let clip_bottom = (u64::from(geometry.crop.bottom_px) * 7_200 + u64::from(geometry.dpi_y) / 2)
        / u64::from(geometry.dpi_y);
    let original_width = (u64::from(asset.width_px()) * 7_200 + u64::from(geometry.dpi_x) / 2)
        / u64::from(geometry.dpi_x);
    let original_height = (u64::from(asset.height_px()) * 7_200 + u64::from(geometry.dpi_y) / 2)
        / u64::from(geometry.dpi_y);
    let width = geometry.width_hwpunit;
    let height = geometry.height_hwpunit;
    format!(
        concat!(
            "<hs:sec xmlns:hs=\"{section_ns}\" xmlns:q=\"{ns}\"><q:p id=\"1\" paraPrIDRef=\"1\" styleIDRef=\"1\"><q:run charPrIDRef=\"1\">",
            "<q:pic id=\"{object_id}\" zOrder=\"0\" numberingType=\"PICTURE\" textWrap=\"TOP_AND_BOTTOM\" textFlow=\"BOTH_SIDES\" lock=\"0\" dropcapstyle=\"None\" href=\"\" groupLevel=\"0\" instid=\"{instance_id}\" reverse=\"0\">",
            "<q:offset x=\"0\" y=\"0\"/><q:orgSz width=\"{width}\" height=\"{height}\"/><q:curSz width=\"0\" height=\"0\"/><q:flip horizontal=\"0\" vertical=\"0\"/>",
            "<q:rotationInfo angle=\"0\" centerX=\"{center_x}\" centerY=\"{center_y}\" rotateimage=\"1\"/>",
            "<q:renderingInfo><q:transMatrix e1=\"1\" e2=\"0\" e3=\"0\" e4=\"0\" e5=\"1\" e6=\"0\"/><q:scaMatrix e1=\"1\" e2=\"0\" e3=\"0\" e4=\"0\" e5=\"1\" e6=\"0\"/><q:rotMatrix e1=\"1\" e2=\"0\" e3=\"0\" e4=\"0\" e5=\"1\" e6=\"0\"/></q:renderingInfo>",
            "<q:img binaryItemIDRef=\"{relationship}\" bright=\"0\" contrast=\"0\" effect=\"REAL_PIC\" alpha=\"0\"/>",
            "<q:imgRect><q:pt0 x=\"0\" y=\"0\"/><q:pt1 x=\"{width}\" y=\"0\"/><q:pt2 x=\"{width}\" y=\"{height}\"/><q:pt3 x=\"0\" y=\"{height}\"/></q:imgRect>",
            "<q:imgClip left=\"{clip_left}\" right=\"{clip_right}\" top=\"{clip_top}\" bottom=\"{clip_bottom}\"/><q:inMargin left=\"0\" right=\"0\" top=\"0\" bottom=\"0\"/>",
            "<q:imgDim dimwidth=\"{original_width}\" dimheight=\"{original_height}\"/><q:effects/><q:sz width=\"{width}\" widthRelTo=\"ABSOLUTE\" height=\"{height}\" heightRelTo=\"ABSOLUTE\" protect=\"0\"/>",
            "<q:pos treatAsChar=\"1\" affectLSpacing=\"1\" flowWithText=\"1\" allowOverlap=\"0\" holdAnchorAndSO=\"0\" vertRelTo=\"PARA\" horzRelTo=\"COLUMN\" vertAlign=\"TOP\" horzAlign=\"LEFT\" vertOffset=\"0\" horzOffset=\"0\"/>",
            "<q:outMargin left=\"0\" right=\"0\" top=\"0\" bottom=\"0\"/><q:shapeComment>{alt_xml}</q:shapeComment></q:pic><q:t/></q:run></q:p></hs:sec>"
        ),
        section_ns = SECTION_NS,
        ns = PARAGRAPH_NS,
        object_id = object_id,
        instance_id = instance_id,
        width = width,
        height = height,
        center_x = width / 2,
        center_y = height / 2,
        relationship = asset.relationship_id(),
        clip_left = clip_left,
        clip_right = clip_right,
        clip_top = clip_top,
        clip_bottom = clip_bottom,
        original_width = original_width,
        original_height = original_height,
        alt_xml = alt_xml,
    )
}

fn valid_archive(section: &str, existing_asset: Option<&[u8]>) -> Result<Vec<u8>, Box<dyn Error>> {
    let asset_item = if existing_asset.is_some() {
        r#"<o:item id="existing-image" href="../BinData/existing.png" media-type="image/png"/>"#
    } else {
        ""
    };
    let opf = format!(
        r#"<o:package xmlns:o="http://www.idpf.org/2007/opf/" id="pkg" version="2.0">
  <o:manifest><o:item id="header" href="header.xml" media-type="application/xml"/><o:item id="section0" href="section0.xml" media-type="application/xml"/>{asset_item}</o:manifest>
  <o:spine><o:itemref idref="section0" linear="yes"/></o:spine>
</o:package>"#
    );
    let mut entries = vec![
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
        entry(
            "Contents/header.xml",
            HEADER.as_bytes(),
            CompressionMethod::Deflated,
        ),
        entry(
            SECTION_PATH,
            section.as_bytes(),
            CompressionMethod::Deflated,
        ),
    ];
    if let Some(asset) = existing_asset {
        entries.push(entry(
            "BinData/existing.png",
            asset,
            CompressionMethod::Deflated,
        ));
    }
    archive(entries).map_err(Into::into)
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
        writer.start_file(
            name,
            SimpleFileOptions::default().compression_method(method),
        )?;
        writer.write_all(&bytes)?;
    }
    Ok(writer.finish()?.into_inner())
}

fn open_graph(bytes: Vec<u8>) -> Result<(TestReader, PackageGraph), Box<dyn Error>> {
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    Ok((reader, graph))
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
        panic!("test PNG chunk exceeds u32")
    };
    output.extend_from_slice(&length.to_be_bytes());
    output.extend_from_slice(&kind);
    output.extend_from_slice(data);
    let mut crc_data = kind.to_vec();
    crc_data.extend_from_slice(data);
    output.extend_from_slice(&crc32(&crc_data).to_be_bytes());
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

fn assert_code<T>(result: Result<T, ImageHwpxError>, expected: &str) {
    let Err(error) = result else {
        panic!("operation unexpectedly succeeded")
    };
    assert_eq!(error.code(), expected, "{error:?}");
}
