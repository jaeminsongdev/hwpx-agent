#![allow(clippy::expect_used)] // Test fixtures use expectations to keep failures local and legible.

use std::error::Error;
use std::io::{Cursor, Write};

use domain_ir::{
    BASIC_SHAPE_SCHEMA_VERSION, BasicShape, BasicShapeBuilder, BasicShapeLimits, BasicShapeRequest,
    BasicShapeRequestDraft, CurveSegment, CurveSegmentType, EllipseArcType, EllipseShape,
    FreeformShape, LineShape, LogicalId, ObjectAffineMatrix, ObjectAnchor, ObjectComponentGeometry,
    ObjectExtent, ObjectFlip, ObjectGeometryLimits, ObjectGeometryStateDraft,
    ObjectHeightReference, ObjectHorizontalAlignment, ObjectHorizontalReference, ObjectKind,
    ObjectNumberingType, ObjectOuterMargins, ObjectPoint, ObjectPosition, ObjectRotation,
    ObjectSize, ObjectTextFlow, ObjectTextWrap, ObjectTransform, ObjectVerticalAlignment,
    ObjectVerticalReference, ObjectWidthReference, ObjectWrap, RectangleShape, ShapePoint,
    TextBoxContent, TextBoxMargins, TextBoxVerticalAlignment,
};
use hwpx_package::{
    BasicShapeHwpxBuilder, BasicShapeHwpxError, BasicShapeHwpxLimitConfig, BasicShapeHwpxLimits,
    BasicShapeHwpxLowerer, BoundedZipReader, IdIndex, IdIndexLimits, IdRuleProfile,
    ObjectGeometryHwpxLimits, PackageGraph, PackageGraphLimits, PackageLimits, PatchLimits,
    PreservingWriter, WriterLimits,
};
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
fn every_basic_shape_family_lowers_and_full_package_reopens() -> TestResult {
    for (shape, kind) in shapes() {
        let (mut reader, graph) = open_graph(valid_archive(&empty_section())?)?;
        let source = BasicShapeHwpxBuilder::inspect_source(
            &mut reader,
            &graph,
            SECTION_PATH,
            0,
            0,
            BasicShapeHwpxLimits::default(),
        )?;
        let domain_plan = domain_plan(shape.clone(), kind, 91, 191)?;
        let plan = BasicShapeHwpxBuilder::plan(
            &mut reader,
            &graph,
            SECTION_PATH,
            0,
            0,
            &domain_plan,
            FLOW_BEFORE,
            BasicShapeLimits::default(),
            ObjectGeometryLimits::default(),
            BasicShapeHwpxLimits::default(),
        )?;
        assert_eq!(plan.source(), &source);
        let lowered = BasicShapeHwpxLowerer::lower(
            &mut reader,
            &graph,
            &plan,
            FLOW_BEFORE,
            BasicShapeLimits::default(),
            ObjectGeometryLimits::default(),
            ObjectGeometryHwpxLimits::default(),
            BasicShapeHwpxLimits::default(),
        )?;
        assert_eq!(lowered.patch().changed_parts(), 1);
        assert_eq!(lowered.patch().added_parts(), 0);
        assert_eq!(
            lowered.patch().profile_version(),
            "hwpml-2011-shape-static/v6"
        );
        assert_eq!(lowered.receipt().target_document_flow_sha256(), FLOW_AFTER);
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
    }
    Ok(())
}

#[test]
fn textbox_escaped_payload_and_debug_are_exact_and_redacted() -> TestResult {
    let shape = BasicShape::TextBox {
        rectangle: rectangle(),
        content: text_box(),
    };
    let domain_plan = domain_plan(shape, ObjectKind::Rectangle, 91, 191)?;
    let (mut reader, graph) = open_graph(valid_archive(&empty_section())?)?;
    let plan = BasicShapeHwpxBuilder::plan(
        &mut reader,
        &graph,
        SECTION_PATH,
        0,
        0,
        &domain_plan,
        FLOW_BEFORE,
        BasicShapeLimits::default(),
        ObjectGeometryLimits::default(),
        BasicShapeHwpxLimits::default(),
    )?;
    let lowered = BasicShapeHwpxLowerer::lower(
        &mut reader,
        &graph,
        &plan,
        FLOW_BEFORE,
        BasicShapeLimits::default(),
        ObjectGeometryLimits::default(),
        ObjectGeometryHwpxLimits::default(),
        BasicShapeHwpxLimits::default(),
    )?;
    for debug in [
        format!("{domain_plan:?}"),
        format!("{plan:?}"),
        format!("{lowered:?}"),
    ] {
        for secret in [
            "SECRET_NAME",
            "SECRET_TEXT",
            SECTION_PATH,
            FLOW_BEFORE,
            FLOW_AFTER,
        ] {
            assert!(!debug.contains(secret), "debug leaked {secret}: {debug}");
        }
    }
    Ok(())
}

#[test]
fn object_instance_paragraph_and_sublist_collisions_fail_closed() -> TestResult {
    for occupied in [
        "<q:line id=\"91\" instid=\"991\"/>",
        "<q:line id=\"991\" instid=\"191\"/>",
        "<q:p id=\"401\"><q:run charPrIDRef=\"1\"><q:t/></q:run></q:p>",
        "<q:subList id=\"301\"/>",
    ] {
        let section = empty_section().replace("</hs:sec>", &format!("{occupied}</hs:sec>"));
        let (mut reader, graph) = open_graph(valid_archive(&section)?)?;
        let shape = BasicShape::TextBox {
            rectangle: rectangle(),
            content: text_box(),
        };
        let domain_plan = domain_plan(shape, ObjectKind::Rectangle, 91, 191)?;
        assert_code(
            BasicShapeHwpxBuilder::plan(
                &mut reader,
                &graph,
                SECTION_PATH,
                0,
                0,
                &domain_plan,
                FLOW_BEFORE,
                BasicShapeLimits::default(),
                ObjectGeometryLimits::default(),
                BasicShapeHwpxLimits::default(),
            ),
            "basic_shape_hwpx_id_collision",
        );
    }
    Ok(())
}

#[test]
fn plan_rechecks_exact_source_and_document_flow() -> TestResult {
    let (mut reader, graph) = open_graph(valid_archive(&empty_section())?)?;
    let domain_plan = domain_plan(shapes().remove(0).0, ObjectKind::Line, 91, 191)?;
    let plan = BasicShapeHwpxBuilder::plan(
        &mut reader,
        &graph,
        SECTION_PATH,
        0,
        0,
        &domain_plan,
        FLOW_BEFORE,
        BasicShapeLimits::default(),
        ObjectGeometryLimits::default(),
        BasicShapeHwpxLimits::default(),
    )?;
    assert_code(
        BasicShapeHwpxLowerer::lower(
            &mut reader,
            &graph,
            &plan,
            &"c".repeat(64),
            BasicShapeLimits::default(),
            ObjectGeometryLimits::default(),
            ObjectGeometryHwpxLimits::default(),
            BasicShapeHwpxLimits::default(),
        ),
        "basic_shape_build_drift",
    );
    let drifted = empty_section().replace("styleIDRef=\"1\"", "styleIDRef=\"0\"");
    let (mut drifted_reader, drifted_graph) = open_graph(valid_archive(&drifted)?)?;
    assert_code(
        BasicShapeHwpxLowerer::lower(
            &mut drifted_reader,
            &drifted_graph,
            &plan,
            FLOW_BEFORE,
            BasicShapeLimits::default(),
            ObjectGeometryLimits::default(),
            ObjectGeometryHwpxLimits::default(),
            BasicShapeHwpxLimits::default(),
        ),
        "basic_shape_hwpx_build_drift",
    );
    Ok(())
}

#[test]
fn nonempty_ambiguous_and_nonspine_targets_fail_closed() -> TestResult {
    let nonempty = empty_section().replace("<q:t/>", "<q:t>existing</q:t>");
    let (mut reader, graph) = open_graph(valid_archive(&nonempty)?)?;
    assert_code(
        BasicShapeHwpxBuilder::inspect_source(
            &mut reader,
            &graph,
            SECTION_PATH,
            0,
            0,
            BasicShapeHwpxLimits::default(),
        ),
        "basic_shape_hwpx_unsupported_target",
    );
    let (mut reader, graph) = open_graph(valid_archive(&empty_section())?)?;
    assert_code(
        BasicShapeHwpxBuilder::inspect_source(
            &mut reader,
            &graph,
            "Contents/header.xml",
            0,
            0,
            BasicShapeHwpxLimits::default(),
        ),
        "basic_shape_hwpx_unsupported_target",
    );
    Ok(())
}

#[test]
fn shape_profile_types_object_and_instance_ids_and_rejects_duplicates() -> TestResult {
    let section = native_line_section();
    let (mut reader, graph) = open_graph(valid_archive(&section)?)?;
    let index = IdIndex::build(
        &mut reader,
        &graph,
        IdRuleProfile::hwpml_2011_shape_v6(),
        IdIndexLimits::default(),
    )?;
    assert_eq!(index.profile_version(), "hwpml-2011-shape-static/v6");

    let duplicate = section.replace("<q:t/>", "<q:line id=\"91\" instid=\"192\"/><q:t/>");
    let (mut reader, graph) = open_graph(valid_archive(&duplicate)?)?;
    assert!(
        IdIndex::build(
            &mut reader,
            &graph,
            IdRuleProfile::hwpml_2011_shape_v6(),
            IdIndexLimits::default(),
        )
        .is_err()
    );
    Ok(())
}

#[test]
fn limits_are_finite_and_invalid_configuration_fails_closed() {
    assert_code(
        BasicShapeHwpxLimits::new(
            BasicShapeHwpxLimitConfig {
                fragment_bytes: 0,
                ..BasicShapeHwpxLimitConfig::default()
            },
            PackageLimits::default(),
            PackageGraphLimits::default(),
            IdIndexLimits::default(),
            PatchLimits::default(),
        ),
        "basic_shape_hwpx_invalid_limit",
    );
}

fn domain_plan(
    shape: BasicShape,
    kind: ObjectKind,
    object_id: u32,
    instance_id: u32,
) -> Result<domain_ir::BasicShapePlan, Box<dyn Error>> {
    let request = BasicShapeRequest::from_draft(
        BasicShapeRequestDraft {
            schema_version: BASIC_SHAPE_SCHEMA_VERSION.to_owned(),
            request_id: LogicalId::parse("shape-request")?,
            expected_document_flow_sha256: FLOW_BEFORE.to_owned(),
            target_document_flow_sha256: FLOW_AFTER.to_owned(),
            geometry: geometry(kind, object_id, instance_id)?,
            shape,
        },
        FLOW_BEFORE,
        ObjectGeometryLimits::default(),
        BasicShapeLimits::default(),
    )?;
    Ok(BasicShapeBuilder::plan(
        &request,
        FLOW_BEFORE,
        ObjectGeometryLimits::default(),
        BasicShapeLimits::default(),
    )?)
}

fn geometry(
    kind: ObjectKind,
    object_id: u32,
    instance_id: u32,
) -> Result<ObjectGeometryStateDraft, Box<dyn Error>> {
    Ok(ObjectGeometryStateDraft {
        schema_version: "hwpx-agent.object-geometry/v1".to_owned(),
        object_id: LogicalId::parse("logical-shape")?,
        object_kind: kind,
        native_object_id: object_id,
        native_instance_id: instance_id,
        z_order: 7,
        numbering_type: ObjectNumberingType::None,
        locked: false,
        size: ObjectSize {
            width_hwpunit: 7200,
            width_reference: ObjectWidthReference::Absolute,
            height_hwpunit: 3600,
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
            horizontal_offset_hwpunit: 100,
            vertical_offset_hwpunit: 200,
        },
        wrap: ObjectWrap {
            text_wrap: ObjectTextWrap::Square,
            text_flow: ObjectTextFlow::BothSides,
        },
        outer_margins: ObjectOuterMargins {
            left_hwpunit: 10,
            right_hwpunit: 11,
            top_hwpunit: 12,
            bottom_hwpunit: 13,
        },
        component: ObjectComponentGeometry {
            offset: ObjectPoint {
                x_hwpunit: 0,
                y_hwpunit: 0,
            },
            original_size: ObjectExtent {
                width_hwpunit: 7200,
                height_hwpunit: 3600,
            },
            current_size: ObjectExtent {
                width_hwpunit: 7200,
                height_hwpunit: 3600,
            },
            flip: ObjectFlip {
                horizontal: false,
                vertical: false,
            },
            rotation: ObjectRotation {
                angle_degrees: 0,
                center_x_hwpunit: 3600,
                center_y_hwpunit: 1800,
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

fn identity_matrix() -> ObjectAffineMatrix {
    ObjectAffineMatrix {
        e1_millionths: 1_000_000,
        e2_millionths: 0,
        e3_millionths: 0,
        e4_millionths: 1_000_000,
        e5_millionths: 0,
        e6_millionths: 0,
    }
}

fn rectangle() -> RectangleShape {
    RectangleShape {
        ratio: 0,
        corners: [
            ShapePoint {
                x_hwpunit: 0,
                y_hwpunit: 0,
            },
            ShapePoint {
                x_hwpunit: 7200,
                y_hwpunit: 0,
            },
            ShapePoint {
                x_hwpunit: 7200,
                y_hwpunit: 3600,
            },
            ShapePoint {
                x_hwpunit: 0,
                y_hwpunit: 3600,
            },
        ],
    }
}

fn text_box() -> TextBoxContent {
    TextBoxContent {
        last_width_hwpunit: 7000,
        name: "SECRET_NAME &amp;".to_owned(),
        editable: true,
        margins: TextBoxMargins {
            left_hwpunit: 100,
            right_hwpunit: 101,
            top_hwpunit: 102,
            bottom_hwpunit: 103,
        },
        sublist_id: 301,
        paragraph_id: 401,
        paragraph_properties_id: 1,
        style_id: 1,
        character_properties_id: 1,
        text_width_hwpunit: 7000,
        text_height_hwpunit: 3400,
        vertical_alignment: TextBoxVerticalAlignment::Center,
        text: "SECRET_TEXT <shape> &amp;".to_owned(),
    }
}

fn shapes() -> Vec<(BasicShape, ObjectKind)> {
    vec![
        (
            BasicShape::Line {
                line: LineShape {
                    is_reverse_hv: true,
                    start: ShapePoint {
                        x_hwpunit: -10,
                        y_hwpunit: 20,
                    },
                    end: ShapePoint {
                        x_hwpunit: 7000,
                        y_hwpunit: 3500,
                    },
                },
            },
            ObjectKind::Line,
        ),
        (
            BasicShape::Rectangle {
                rectangle: rectangle(),
            },
            ObjectKind::Rectangle,
        ),
        (
            BasicShape::Ellipse {
                ellipse: EllipseShape {
                    interval_dirty: false,
                    has_arc_properties: true,
                    arc_type: EllipseArcType::Chord,
                    center: point(3600, 1800),
                    axis_1: point(7200, 1800),
                    axis_2: point(3600, 3600),
                    start_1: point(7200, 1800),
                    start_2: point(3600, 3600),
                    end_1: point(0, 1800),
                    end_2: point(3600, 0),
                },
            },
            ObjectKind::Ellipse,
        ),
        (
            BasicShape::TextBox {
                rectangle: rectangle(),
                content: text_box(),
            },
            ObjectKind::Rectangle,
        ),
        (
            BasicShape::Freeform {
                freeform: FreeformShape::Polygon {
                    points: vec![point(0, 0), point(1000, 0), point(500, 800)],
                },
            },
            ObjectKind::Polygon,
        ),
        (
            BasicShape::Freeform {
                freeform: FreeformShape::Curve {
                    segments: vec![
                        CurveSegment {
                            segment_type: CurveSegmentType::Line,
                            x1_hwpunit: 0,
                            y1_hwpunit: 0,
                            x2_hwpunit: 100,
                            y2_hwpunit: 100,
                        },
                        CurveSegment {
                            segment_type: CurveSegmentType::Curve,
                            x1_hwpunit: 100,
                            y1_hwpunit: 100,
                            x2_hwpunit: 1000,
                            y2_hwpunit: 500,
                        },
                    ],
                },
            },
            ObjectKind::Curve,
        ),
    ]
}

fn point(x_hwpunit: i32, y_hwpunit: i32) -> ShapePoint {
    ShapePoint {
        x_hwpunit,
        y_hwpunit,
    }
}

fn empty_section() -> String {
    format!(
        "<hs:sec xmlns:hs=\"{SECTION_NS}\" xmlns:q=\"{PARAGRAPH_NS}\"><q:p id=\"10\" paraPrIDRef=\"1\" styleIDRef=\"1\"><q:run charPrIDRef=\"1\"><q:t/></q:run></q:p></hs:sec>"
    )
}

fn native_line_section() -> String {
    let object = concat!(
        "<q:line id=\"91\" zOrder=\"7\" numberingType=\"NONE\" textWrap=\"SQUARE\" textFlow=\"BOTH_SIDES\" lock=\"0\" dropcapstyle=\"None\" href=\"\" groupLevel=\"0\" instid=\"191\" isReverseHV=\"1\">",
        "<q:offset x=\"0\" y=\"0\"/><q:orgSz width=\"7200\" height=\"3600\"/><q:curSz width=\"7200\" height=\"3600\"/><q:flip horizontal=\"0\" vertical=\"0\"/>",
        "<q:rotationInfo angle=\"0\" centerX=\"3600\" centerY=\"1800\" rotateimage=\"1\"/>",
        "<q:renderingInfo><q:transMatrix e1=\"1\" e2=\"0\" e3=\"0\" e4=\"1\" e5=\"0\" e6=\"0\"/><q:scaMatrix e1=\"1\" e2=\"0\" e3=\"0\" e4=\"1\" e5=\"0\" e6=\"0\"/><q:rotMatrix e1=\"1\" e2=\"0\" e3=\"0\" e4=\"1\" e5=\"0\" e6=\"0\"/></q:renderingInfo>",
        "<q:startPt x=\"-10\" y=\"20\"/><q:endPt x=\"7000\" y=\"3500\"/>",
        "<q:sz width=\"7200\" widthRelTo=\"ABSOLUTE\" height=\"3600\" heightRelTo=\"ABSOLUTE\" protect=\"0\"/>",
        "<q:pos treatAsChar=\"0\" affectLSpacing=\"0\" flowWithText=\"1\" allowOverlap=\"0\" holdAnchorAndSO=\"1\" vertRelTo=\"PARA\" horzRelTo=\"PARA\" vertAlign=\"TOP\" horzAlign=\"LEFT\" vertOffset=\"200\" horzOffset=\"100\"/>",
        "<q:outMargin left=\"10\" right=\"11\" top=\"12\" bottom=\"13\"/></q:line>"
    );
    empty_section().replace("<q:t/>", &format!("{object}<q:t/>"))
}

fn valid_archive(section: &str) -> Result<Vec<u8>, Box<dyn Error>> {
    let opf = r#"<o:package xmlns:o="http://www.idpf.org/2007/opf/" id="pkg" version="2.0">
  <o:manifest><o:item id="header" href="header.xml" media-type="application/xml"/><o:item id="section0" href="section0.xml" media-type="application/xml"/></o:manifest>
  <o:spine><o:itemref idref="section0" linear="yes"/></o:spine>
</o:package>"#;
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
    ])
    .map_err(Into::into)
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

fn assert_code<T>(result: Result<T, BasicShapeHwpxError>, expected: &str) {
    let Err(error) = result else {
        panic!("operation unexpectedly succeeded")
    };
    assert_eq!(error.code(), expected, "{error:?}");
}
