use std::env;
use std::error::Error;
use std::fmt::Write as _;
use std::fs::OpenOptions;
use std::io::{Cursor, Read, Write};
use std::path::{Path, PathBuf};

use domain_ir::{
    BASIC_SHAPE_SCHEMA_VERSION, BasicShape, BasicShapeBuilder, BasicShapeLimits, BasicShapeRequest,
    BasicShapeRequestDraft, FreeformShape, LogicalId, ObjectAffineMatrix, ObjectAnchor,
    ObjectComponentGeometry, ObjectExtent, ObjectFlip, ObjectGeometryLimits,
    ObjectGeometryStateDraft, ObjectHeightReference, ObjectHorizontalAlignment,
    ObjectHorizontalReference, ObjectKind, ObjectNumberingType, ObjectOuterMargins, ObjectPoint,
    ObjectPosition, ObjectRotation, ObjectSize, ObjectTextFlow, ObjectTextWrap, ObjectTransform,
    ObjectVerticalAlignment, ObjectVerticalReference, ObjectWidthReference, ObjectWrap,
    RectangleShape, ShapePoint, TextBoxContent, TextBoxMargins, TextBoxVerticalAlignment,
};
use hwpx_agent_foundation::workdir::SecureWorkspace;
use hwpx_package::{
    AssetStoreAdapter, AtomicPackagePublisher, BasicShapeHwpxBuilder, BasicShapeHwpxLimits,
    BasicShapeHwpxLowerer, BoundedZipReader, Hancom2020Vs0Builder, IdIndexLimits,
    ImageAssetBinding, ImageCrop, ImageGeometry, ImageHwpxBuilder, ImageHwpxLimits,
    ImageHwpxLowerer, ImageHwpxRequest, ImageHwpxRequestDraft, ImageLinkMode,
    ObjectGeometryHwpxLimits, PackageArtifact, PackageGraph, PackageGraphLimits, PackageLimits,
    PreservingWriter, WriterLimits,
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use zip::write::SimpleFileOptions;
use zip::{DateTime, ZipArchive, ZipWriter};

const SECTION_PATH: &str = "Contents/section0.xml";
const FLOW_BEFORE: &str = "6dbb7d71c2b613710791078547572170b0ed4c941fd57dfae241b15a0bbf2b58";
const FLOW_AFTER: &str = "bf8224d4c930213a409e214e88e3fbbcf8c57e80872d075bcdcb058882e61e85";
const MAX_BASE_BYTES: usize = 2 * 1024 * 1024;
const MAX_PART_BYTES: usize = 1024 * 1024;
const MAX_PARTS: usize = 32;
const IMAGE_PNG_HEX: &str = concat!(
    "89504e470d0a1a0a0000000d4948445200000008000000080806000000c40fbe8b",
    "0000001c49444154789c6390abb8f3ffc316b9ffb868067c92209a615898000095",
    "23a6411080e1d00000000049454e44ae426082"
);

#[derive(Serialize)]
struct Manifest {
    schema_version: &'static str,
    target_profile: TargetProfile,
    cases: Vec<ManifestCase>,
    actual_hangul_2020: bool,
    save_reopen: &'static str,
    object_bounds: &'static str,
    render: &'static str,
    differential: &'static str,
    rollback_or_retry: &'static str,
}

#[derive(Serialize)]
struct TargetProfile {
    product: &'static str,
    build: &'static str,
    architecture: &'static str,
    locale: &'static str,
    executable_sha256: &'static str,
}

#[derive(Serialize)]
struct ManifestCase {
    case_id: &'static str,
    feature_id: &'static str,
    capability_id: &'static str,
    file: &'static str,
    package_sha256: String,
    package_bytes: usize,
    output_section_sha256: String,
    plan_or_request_sha256: String,
    lowering_receipt_sha256: String,
    object_kind: &'static str,
    native_object_id: u32,
    native_instance_id: u32,
    resource: Option<ResourceEvidence>,
}

#[derive(Serialize)]
struct ResourceEvidence {
    media_type: &'static str,
    payload_sha256: String,
    payload_bytes: usize,
}

struct BuiltCase {
    manifest: ManifestCase,
    artifact: PackageArtifact,
}

fn main() -> Result<(), Box<dyn Error>> {
    let output_directory = parse_output_directory()?;
    if output_directory.exists() {
        return Err("output directory already exists".into());
    }
    let parent = output_directory
        .parent()
        .ok_or("output directory has no parent")?;
    if !parent.is_dir() {
        return Err("output parent does not exist".into());
    }

    let cases = build_cases()?;

    let workspace = SecureWorkspace::create(&output_directory)?;
    for case in &cases {
        let staging = PathBuf::from("p08-18").join(case.manifest.file);
        let output = Path::new(case.manifest.file);
        let publication =
            AtomicPackagePublisher::publish(&case.artifact, &workspace, &staging, output)?;
        if hex(publication.sha256()) != case.manifest.package_sha256
            || usize::try_from(publication.size_bytes())? != case.manifest.package_bytes
            || publication.output_relative() != output
        {
            return Err("published target fixture differs from its manifest evidence".into());
        }
    }
    let manifest = Manifest {
        schema_version: "hwpx-agent.p08-18-object-insert-target-fixture/v1",
        target_profile: TargetProfile {
            product: "Hancom Hangul 2020",
            build: "11.0.0.9136",
            architecture: "x86",
            locale: "ko-KR",
            executable_sha256: "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce",
        },
        cases: cases.into_iter().map(|case| case.manifest).collect(),
        actual_hangul_2020: false,
        save_reopen: "not_run",
        object_bounds: "not_run",
        render: "not_run",
        differential: "not_run",
        rollback_or_retry: "not_run",
    };
    let manifest_bytes = serde_json::to_vec_pretty(&manifest)?;
    write_new(
        &output_directory.join("output/fixture-manifest.json"),
        &manifest_bytes,
    )?;
    println!(
        "{}",
        serde_json::to_string(&serde_json::json!({
            "state": "pass",
            "schema_version": manifest.schema_version,
            "output_directory": output_directory.join("output"),
            "case_count": manifest.cases.len(),
            "manifest_sha256": sha256(&manifest_bytes),
            "actual_hangul_2020": false
        }))?
    );
    Ok(())
}

fn build_cases() -> Result<Vec<BuiltCase>, Box<dyn Error>> {
    Ok(vec![
        build_basic_case(
            "P08-18-C01",
            "OBJ-001",
            "obj.shape_insert",
            "obj-001-shape-insert.hwpx",
            8_101,
            18_101,
            BasicShape::Rectangle {
                rectangle: rectangle(),
            },
            ObjectKind::Rectangle,
            "rectangle",
        )?,
        build_basic_case(
            "P08-18-C02",
            "OBJ-007",
            "obj.textbox_insert",
            "obj-007-textbox-insert.hwpx",
            8_107,
            18_107,
            BasicShape::TextBox {
                rectangle: rectangle(),
                content: text_box(),
            },
            ObjectKind::Rectangle,
            "textbox",
        )?,
        build_basic_case(
            "P08-18-C03",
            "OBJ-042",
            "obj.freeform",
            "obj-042-freeform-insert.hwpx",
            8_142,
            18_142,
            BasicShape::Freeform {
                freeform: FreeformShape::Polygon {
                    points: vec![point(0, 0), point(7_200, 0), point(3_600, 3_600)],
                },
            },
            ObjectKind::Polygon,
            "polygon",
        )?,
        build_image_case()?,
    ])
}

#[allow(clippy::too_many_arguments)]
fn build_basic_case(
    case_id: &'static str,
    feature_id: &'static str,
    capability_id: &'static str,
    file: &'static str,
    object_id: u32,
    instance_id: u32,
    shape: BasicShape,
    kind: ObjectKind,
    object_kind: &'static str,
) -> Result<BuiltCase, Box<dyn Error>> {
    let source_bytes = build_base(&format!("{feature_id} {capability_id}"))?;
    let mut reader = BoundedZipReader::open(
        Cursor::new(source_bytes.as_slice()),
        PackageLimits::default(),
    )?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    let limits = BasicShapeHwpxLimits::default();
    BasicShapeHwpxBuilder::inspect_source(&mut reader, &graph, SECTION_PATH, 1, 0, limits)?;
    let request = BasicShapeRequest::from_draft(
        BasicShapeRequestDraft {
            schema_version: BASIC_SHAPE_SCHEMA_VERSION.to_owned(),
            request_id: LogicalId::parse(format!("{}-request", feature_id.to_ascii_lowercase()))?,
            expected_document_flow_sha256: FLOW_BEFORE.to_owned(),
            target_document_flow_sha256: FLOW_AFTER.to_owned(),
            geometry: geometry(kind, object_id, instance_id)?,
            shape,
        },
        FLOW_BEFORE,
        ObjectGeometryLimits::default(),
        BasicShapeLimits::default(),
    )?;
    let domain_plan = BasicShapeBuilder::plan(
        &request,
        FLOW_BEFORE,
        ObjectGeometryLimits::default(),
        BasicShapeLimits::default(),
    )?;
    let plan = BasicShapeHwpxBuilder::plan(
        &mut reader,
        &graph,
        SECTION_PATH,
        1,
        0,
        &domain_plan,
        FLOW_BEFORE,
        BasicShapeLimits::default(),
        ObjectGeometryLimits::default(),
        limits,
    )?;
    let plan_sha256 = plan.plan_sha256().to_owned();
    let lowered = BasicShapeHwpxLowerer::lower(
        &mut reader,
        &graph,
        &plan,
        FLOW_BEFORE,
        BasicShapeLimits::default(),
        ObjectGeometryLimits::default(),
        ObjectGeometryHwpxLimits::default(),
        limits,
    )?;
    let output_section_sha256 = lowered.receipt().output_section_sha256().to_owned();
    let receipt_bytes = serde_json::to_vec(lowered.receipt())?;
    let artifact = PreservingWriter::build(
        lowered.patch(),
        PackageLimits::default(),
        PackageGraphLimits::default(),
        IdIndexLimits::default(),
        WriterLimits::default(),
    )?;
    artifact.verify()?;
    let package_sha256 = hex(artifact.sha256());
    let package_bytes = artifact.size_bytes();
    Ok(BuiltCase {
        manifest: ManifestCase {
            case_id,
            feature_id,
            capability_id,
            file,
            package_sha256,
            package_bytes,
            output_section_sha256,
            plan_or_request_sha256: plan_sha256,
            lowering_receipt_sha256: sha256(&receipt_bytes),
            object_kind,
            native_object_id: object_id,
            native_instance_id: instance_id,
            resource: None,
        },
        artifact,
    })
}

fn build_image_case() -> Result<BuiltCase, Box<dyn Error>> {
    let feature_id = "OBJ-002";
    let capability_id = "obj.image_insert";
    let source_bytes = build_base(&format!("{feature_id} {capability_id}"))?;
    let mut reader = BoundedZipReader::open(
        Cursor::new(source_bytes.as_slice()),
        PackageLimits::default(),
    )?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    let payload = decode_hex(IMAGE_PNG_HEX)?;
    let asset_plan = AssetStoreAdapter::default().build("image/png", &payload, &graph)?;
    let limits = ImageHwpxLimits::default();
    let source = ImageHwpxBuilder::inspect_source(&mut reader, &graph, SECTION_PATH, 1, 0, limits)?;
    let request = ImageHwpxRequest::from_draft(
        ImageHwpxRequestDraft {
            schema_version: hwpx_package::IMAGE_HWPX_SCHEMA_VERSION.to_owned(),
            profile_id: hwpx_package::IMAGE_HWPX_PROFILE_ID.to_owned(),
            section_part: source.section_part().to_owned(),
            paragraph_ordinal: 1,
            run_ordinal: 0,
            expected_package_state_sha256: source.package_state_sha256().to_owned(),
            expected_section_sha256: source.section_sha256().to_owned(),
            expected_paragraph_sha256: source.paragraph_sha256().to_owned(),
            expected_run_sha256: source.run_sha256().to_owned(),
            expected_object_ids_sha256: source.object_ids_sha256().to_owned(),
            expected_instance_ids_sha256: source.instance_ids_sha256().to_owned(),
            expected_document_flow_sha256: FLOW_BEFORE.to_owned(),
            target_document_flow_sha256: FLOW_AFTER.to_owned(),
            object_id: 8_102,
            instance_id: 18_102,
            link_mode: ImageLinkMode::Embed,
            geometry: ImageGeometry {
                width_hwpunit: 7_200,
                height_hwpunit: 7_200,
                dpi_x: 96,
                dpi_y: 96,
                crop: ImageCrop::full(8, 8),
                render_required: true,
            },
            alt_text: "P08-18 embedded checker image".to_owned(),
            asset: ImageAssetBinding::from_plan(&asset_plan),
        },
        &source,
        &asset_plan,
        FLOW_BEFORE,
        limits,
    )?;
    let request_sha256 = sha256(&request.canonical_json(limits)?);
    let lowered = ImageHwpxLowerer::lower(&mut reader, &graph, &request, FLOW_BEFORE, limits)?;
    let output_section_sha256 = lowered.receipt().output_section_sha256().to_owned();
    let receipt_bytes = lowered.receipt().canonical_json(limits)?;
    let artifact = PreservingWriter::build(
        lowered.patch(),
        PackageLimits::default(),
        PackageGraphLimits::default(),
        IdIndexLimits::default(),
        WriterLimits::default(),
    )?;
    artifact.verify()?;
    let package_sha256 = hex(artifact.sha256());
    let package_bytes = artifact.size_bytes();
    Ok(BuiltCase {
        manifest: ManifestCase {
            case_id: "P08-18-C04",
            feature_id,
            capability_id,
            file: "obj-002-image-insert.hwpx",
            package_sha256,
            package_bytes,
            output_section_sha256,
            plan_or_request_sha256: request_sha256,
            lowering_receipt_sha256: sha256(&receipt_bytes),
            object_kind: "picture",
            native_object_id: 8_102,
            native_instance_id: 18_102,
            resource: Some(ResourceEvidence {
                media_type: "image/png",
                payload_sha256: sha256(&payload),
                payload_bytes: payload.len(),
            }),
        },
        artifact,
    })
}

fn build_base(visible_text: &str) -> Result<Vec<u8>, Box<dyn Error>> {
    let base = Hancom2020Vs0Builder::build(visible_text)?;
    let bytes = base.with_verified_bytes(<[u8]>::to_vec)?;
    if bytes.len() > MAX_BASE_BYTES {
        return Err("base artifact exceeds target-fixture limit".into());
    }
    let mut archive = ZipArchive::new(Cursor::new(bytes))?;
    if archive.is_empty() || archive.len() > MAX_PARTS {
        return Err("base artifact part count is invalid".into());
    }
    let mut parts = Vec::with_capacity(archive.len());
    for index in 0..archive.len() {
        let mut entry = archive.by_index(index)?;
        if entry.size() > MAX_PART_BYTES as u64 || entry.name().contains('\\') {
            return Err("base artifact part is outside fixture policy".into());
        }
        let mut part = Vec::new();
        entry.read_to_end(&mut part)?;
        let method = entry.compression();
        let name = entry.name().to_owned();
        if name == SECTION_PATH {
            part = insert_empty_object_paragraph(&part)?;
        }
        parts.push((name, part, method));
    }
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    for (name, part, method) in parts {
        let options = SimpleFileOptions::default()
            .compression_method(method)
            .last_modified_time(DateTime::default());
        writer.start_file(name, options)?;
        writer.write_all(&part)?;
    }
    Ok(writer.finish()?.into_inner())
}

fn insert_empty_object_paragraph(section: &[u8]) -> Result<Vec<u8>, Box<dyn Error>> {
    let source = std::str::from_utf8(section)?;
    let closing = source
        .rfind("</hs:sec>")
        .ok_or("section closing tag is missing")?;
    if source.contains("id=\"2\"") {
        return Err("base section already owns the target paragraph identity".into());
    }
    let paragraph = concat!(
        "<hp:p id=\"2\" paraPrIDRef=\"0\" styleIDRef=\"0\" pageBreak=\"0\" ",
        "columnBreak=\"0\" merged=\"0\"><hp:run charPrIDRef=\"0\"><hp:t/>",
        "</hp:run></hp:p>"
    );
    let mut output = String::with_capacity(source.len() + paragraph.len());
    output.push_str(&source[..closing]);
    output.push_str(paragraph);
    output.push_str(&source[closing..]);
    Ok(output.into_bytes())
}

fn geometry(
    kind: ObjectKind,
    object_id: u32,
    instance_id: u32,
) -> Result<ObjectGeometryStateDraft, Box<dyn Error>> {
    Ok(ObjectGeometryStateDraft {
        schema_version: "hwpx-agent.object-geometry/v1".to_owned(),
        object_id: LogicalId::parse(format!("object-{object_id}"))?,
        object_kind: kind,
        native_object_id: object_id,
        native_instance_id: instance_id,
        z_order: 1,
        numbering_type: ObjectNumberingType::None,
        locked: false,
        size: ObjectSize {
            width_hwpunit: 10_800,
            width_reference: ObjectWidthReference::Absolute,
            height_hwpunit: 5_400,
            height_reference: ObjectHeightReference::Absolute,
            protect: false,
        },
        anchor: ObjectAnchor {
            treat_as_character: false,
            affect_line_spacing: false,
            flow_with_text: true,
            allow_overlap: false,
            hold_anchor_and_shape: true,
            horizontal_reference: ObjectHorizontalReference::Paragraph,
            vertical_reference: ObjectVerticalReference::Paragraph,
        },
        position: ObjectPosition {
            horizontal_alignment: ObjectHorizontalAlignment::Left,
            vertical_alignment: ObjectVerticalAlignment::Top,
            horizontal_offset_hwpunit: 1_000,
            vertical_offset_hwpunit: 1_000,
        },
        wrap: ObjectWrap {
            text_wrap: ObjectTextWrap::TopAndBottom,
            text_flow: ObjectTextFlow::BothSides,
        },
        outer_margins: ObjectOuterMargins {
            left_hwpunit: 100,
            right_hwpunit: 100,
            top_hwpunit: 100,
            bottom_hwpunit: 100,
        },
        component: ObjectComponentGeometry {
            offset: ObjectPoint {
                x_hwpunit: 0,
                y_hwpunit: 0,
            },
            original_size: ObjectExtent {
                width_hwpunit: 10_800,
                height_hwpunit: 5_400,
            },
            current_size: ObjectExtent {
                width_hwpunit: 10_800,
                height_hwpunit: 5_400,
            },
            flip: ObjectFlip {
                horizontal: false,
                vertical: false,
            },
            rotation: ObjectRotation {
                angle_degrees: 0,
                center_x_hwpunit: 5_400,
                center_y_hwpunit: 2_700,
                rotate_image: true,
            },
            transform: ObjectTransform {
                translation: identity_matrix(),
                scale: identity_matrix(),
                rotation: identity_matrix(),
            },
        },
    })
}

fn rectangle() -> RectangleShape {
    RectangleShape {
        ratio: 0,
        corners: [
            point(0, 0),
            point(10_800, 0),
            point(10_800, 5_400),
            point(0, 5_400),
        ],
    }
}

fn text_box() -> TextBoxContent {
    TextBoxContent {
        last_width_hwpunit: 10_000,
        name: "P08-18 text box".to_owned(),
        editable: true,
        margins: TextBoxMargins {
            left_hwpunit: 400,
            right_hwpunit: 400,
            top_hwpunit: 300,
            bottom_hwpunit: 300,
        },
        sublist_id: 28_107,
        paragraph_id: 38_107,
        paragraph_properties_id: 0,
        style_id: 0,
        character_properties_id: 0,
        text_width_hwpunit: 10_000,
        text_height_hwpunit: 4_800,
        vertical_alignment: TextBoxVerticalAlignment::Center,
        text: "P08-18 TEXT BOX".to_owned(),
    }
}

const fn point(x_hwpunit: i32, y_hwpunit: i32) -> ShapePoint {
    ShapePoint {
        x_hwpunit,
        y_hwpunit,
    }
}

const fn identity_matrix() -> ObjectAffineMatrix {
    ObjectAffineMatrix::IDENTITY
}

fn parse_output_directory() -> Result<PathBuf, Box<dyn Error>> {
    let mut arguments = env::args_os();
    let _program = arguments.next();
    let output = arguments
        .next()
        .map(PathBuf::from)
        .ok_or("output directory is required")?;
    if arguments.next().is_some() {
        return Err("too many arguments".into());
    }
    if !output.is_absolute() {
        return Err("output directory must be absolute".into());
    }
    Ok(output)
}

fn write_new(path: &Path, bytes: &[u8]) -> Result<(), Box<dyn Error>> {
    let mut file = OpenOptions::new().write(true).create_new(true).open(path)?;
    file.write_all(bytes)?;
    file.sync_all()?;
    Ok(())
}

fn decode_hex(value: &str) -> Result<Vec<u8>, Box<dyn Error>> {
    if !value.len().is_multiple_of(2) || !value.bytes().all(|byte| byte.is_ascii_hexdigit()) {
        return Err("embedded image hex is malformed".into());
    }
    let mut output = Vec::with_capacity(value.len() / 2);
    for pair in value.as_bytes().chunks_exact(2) {
        let text = std::str::from_utf8(pair)?;
        output.push(u8::from_str_radix(text, 16)?);
    }
    Ok(output)
}

fn sha256(bytes: &[u8]) -> String {
    hex(Sha256::digest(bytes).into())
}

fn hex(bytes: [u8; 32]) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let mut output = String::with_capacity(64);
    for byte in bytes {
        let _ = write!(output, "{byte:02x}");
    }
    debug_assert!(output.bytes().all(|byte| DIGITS.contains(&byte)));
    output
}
