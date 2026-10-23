#![allow(clippy::expect_used)] // Fixtures keep failures local and readable.

use std::error::Error;
use std::fmt::Write as _;

use domain_ir::{
    BasicShapeLimits, CurveSegment, CurveSegmentType, FreeformShape, LogicalId,
    OBJECT_GEOMETRY_SCHEMA_VERSION, ObjectAffineMatrix, ObjectAnchor, ObjectComponentGeometry,
    ObjectExtent, ObjectFlip, ObjectGeometryLimits, ObjectGeometryStateDraft,
    ObjectHeightReference, ObjectHorizontalAlignment, ObjectHorizontalReference, ObjectKind,
    ObjectNumberingType, ObjectOuterMargins, ObjectPoint, ObjectPosition, ObjectRotation,
    ObjectSize, ObjectTextFlow, ObjectTextWrap, ObjectTransform, ObjectVerticalAlignment,
    ObjectVerticalReference, ObjectWidthReference, ObjectWrap, SHAPE_POINTS_SCHEMA_VERSION,
    ShapePoint, ShapePointsBuilder, ShapePointsLimitConfig, ShapePointsLimits, ShapePointsRequest,
    ShapePointsRequestDraft, ShapePointsState, ShapePointsStateDraft,
};
use hwpx_package::{
    ObjectGeometryHwpxLimits, ShapePointsHwpxBuilder, ShapePointsHwpxError,
    ShapePointsHwpxLimitConfig, ShapePointsHwpxLimits, ShapePointsHwpxLowerer,
    ShapePointsHwpxReader,
};

type TestResult = Result<(), Box<dyn Error>>;

const FLOW_BEFORE: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const FLOW_AFTER: &str = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
const APPEARANCE: &str = "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc";
const PROPERTIES: &str = "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd";
const RESOURCES: &str = "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee";
const EMBEDDED: &str = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff";
const OPAQUE: &str = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef";

#[test]
fn polygon_and_curve_lower_only_the_native_payload_island() -> TestResult {
    let cases = [
        (
            ObjectKind::Polygon,
            polygon(&[(0, 0), (1000, 0), (0, 1000)]),
            polygon(&[(0, 0), (2000, 0), (1500, 700), (0, 1000)]),
        ),
        (ObjectKind::Curve, curve(0), curve(250)),
    ];
    for (kind, source_path, target_path) in cases {
        let source_state = state(kind, source_path.clone())?;
        let domain_plan = domain_plan(&source_state, target_path.clone())?;
        let section = section(kind, &source_path);
        let hwpx_plan = ShapePointsHwpxBuilder::plan(
            section.as_bytes(),
            0,
            &domain_plan,
            FLOW_BEFORE,
            ObjectGeometryLimits::default(),
            ObjectGeometryHwpxLimits::default(),
            BasicShapeLimits::default(),
            state_limits(),
            ShapePointsHwpxLimits::default(),
        )?;
        assert_eq!(hwpx_plan.object_ordinal(), 0);
        assert_eq!(hwpx_plan.domain_plan(), &domain_plan);
        assert_eq!(
            hwpx_plan.canonical_json(ShapePointsHwpxLimits::default())?,
            hwpx_plan.canonical_json(ShapePointsHwpxLimits::default())?
        );
        let (output, receipt) = ShapePointsHwpxLowerer::lower_in_section_with_receipt(
            section.as_bytes(),
            &hwpx_plan,
            FLOW_BEFORE,
            ObjectGeometryLimits::default(),
            ObjectGeometryHwpxLimits::default(),
            BasicShapeLimits::default(),
            state_limits(),
            ShapePointsHwpxLimits::default(),
        )?;
        let target_state = ShapePointsBuilder::build(
            &domain_plan,
            &source_state,
            FLOW_BEFORE,
            BasicShapeLimits::default(),
            state_limits(),
        )?
        .state;
        let readback = ShapePointsHwpxReader::read_in_section(
            &output,
            0,
            &target_state,
            ObjectGeometryLimits::default(),
            ObjectGeometryHwpxLimits::default(),
            BasicShapeLimits::default(),
            ShapePointsHwpxLimits::default(),
        )?;
        assert_eq!(readback.freeform, target_path);
        assert_eq!(receipt.capability_id, "obj.shape_edit_points");
        assert_eq!(receipt.target_document_flow_sha256, FLOW_AFTER);
        assert_ne!(receipt.source_payload_sha256, receipt.output_payload_sha256);
        let output = String::from_utf8(output)?;
        for exact in [
            "PRIVATE_LINE_APPEARANCE",
            "PRIVATE_FILL_APPEARANCE",
            "PRIVATE_SHADOW_APPEARANCE",
            "PRIVATE_CAPTION_OR_COMMENT",
            "PRIVATE_AFTER_OBJECT",
        ] {
            assert!(output.contains(exact), "lost outside state: {exact}");
        }
    }
    Ok(())
}

#[test]
fn request_and_build_recheck_flow_section_object_and_payload_drift() -> TestResult {
    let source_path = polygon(&[(0, 0), (1000, 0), (0, 1000)]);
    let source_state = state(ObjectKind::Polygon, source_path.clone())?;
    let domain_plan = domain_plan(&source_state, polygon(&[(0, 0), (2000, 0), (0, 1000)]))?;
    let section = section(ObjectKind::Polygon, &source_path);
    assert_code(
        ShapePointsHwpxBuilder::plan(
            section.as_bytes(),
            0,
            &domain_plan,
            FLOW_AFTER,
            ObjectGeometryLimits::default(),
            ObjectGeometryHwpxLimits::default(),
            BasicShapeLimits::default(),
            state_limits(),
            ShapePointsHwpxLimits::default(),
        ),
        "shape_points_hwpx_domain",
    );
    let plan = hwpx_plan(section.as_bytes(), &domain_plan)?;
    assert_code(
        ShapePointsHwpxLowerer::lower_in_section(
            section.as_bytes(),
            &plan,
            FLOW_AFTER,
            ObjectGeometryLimits::default(),
            ObjectGeometryHwpxLimits::default(),
            BasicShapeLimits::default(),
            state_limits(),
            ShapePointsHwpxLimits::default(),
        ),
        "shape_points_hwpx_source_drift",
    );
    for drifted in [
        section.replace("PRIVATE_AFTER_OBJECT", "DRIFT_AFTER_OBJECT"),
        section.replace("x=\"1000\"", "x=\"1001\""),
        section.replace("zOrder=\"3\"", "zOrder=\"4\""),
    ] {
        assert_code(
            ShapePointsHwpxLowerer::lower_in_section(
                drifted.as_bytes(),
                &plan,
                FLOW_BEFORE,
                ObjectGeometryLimits::default(),
                ObjectGeometryHwpxLimits::default(),
                BasicShapeLimits::default(),
                state_limits(),
                ShapePointsHwpxLimits::default(),
            ),
            "shape_points_hwpx_source_drift",
        );
    }
    Ok(())
}

#[test]
fn noncontiguous_payload_wrong_ordinal_and_wrong_kind_fail_closed() -> TestResult {
    let source_path = polygon(&[(0, 0), (1000, 0), (0, 1000)]);
    let source_state = state(ObjectKind::Polygon, source_path.clone())?;
    let domain_plan = domain_plan(&source_state, polygon(&[(0, 0), (2000, 0), (0, 1000)]))?;
    let section = section(ObjectKind::Polygon, &source_path);
    let separated = section.replace(
        "<c:pt x=\"1000\" y=\"0\"/>",
        "<c:pt x=\"1000\" y=\"0\"/><q:shapeComment>BREAK</q:shapeComment>",
    );
    assert_code(
        hwpx_plan(separated.as_bytes(), &domain_plan),
        "shape_points_hwpx_invalid_payload",
    );
    assert_code(
        ShapePointsHwpxBuilder::plan(
            section.as_bytes(),
            1,
            &domain_plan,
            FLOW_BEFORE,
            ObjectGeometryLimits::default(),
            ObjectGeometryHwpxLimits::default(),
            BasicShapeLimits::default(),
            state_limits(),
            ShapePointsHwpxLimits::default(),
        ),
        "shape_points_hwpx_unsupported_shape",
    );
    let rectangle = section
        .replace("<q:polygon", "<q:rect")
        .replace("</q:polygon>", "</q:rect>");
    assert_code(
        hwpx_plan(rectangle.as_bytes(), &domain_plan),
        "shape_points_hwpx_unsupported_shape",
    );
    Ok(())
}

#[test]
fn malformed_duplicate_nested_and_noncanonical_payload_fail_closed() -> TestResult {
    let source_path = polygon(&[(0, 0), (1000, 0), (0, 1000)]);
    let source_state = state(ObjectKind::Polygon, source_path.clone())?;
    let domain_plan = domain_plan(&source_state, polygon(&[(0, 0), (2000, 0), (0, 1000)]))?;
    let section = section(ObjectKind::Polygon, &source_path);
    for malformed in [
        section.replace("x=\"1000\" y=\"0\"", "x=\"1000\" x=\"1000\" y=\"0\""),
        section.replace("x=\"1000\" y=\"0\"", "x=\"01000\" y=\"0\""),
        section.replace(
            "<c:pt x=\"1000\" y=\"0\"/>",
            "<c:pt x=\"1000\" y=\"0\"></c:pt>",
        ),
        section.replace(
            "<c:pt x=\"1000\" y=\"0\"/>",
            "<c:pt x=\"1000\" y=\"0\" extra=\"1\"/>",
        ),
        section.replace(
            "<c:pt x=\"1000\" y=\"0\"/>",
            "<c:pt xmlns:c=\"http://www.hancom.co.kr/hwpml/2011/core\" x=\"1000\" y=\"0\"/>",
        ),
    ] {
        assert!(hwpx_plan(malformed.as_bytes(), &domain_plan).is_err());
    }
    Ok(())
}

#[test]
fn finite_limits_and_debug_are_fail_closed_and_redacted() -> TestResult {
    assert_code(
        ShapePointsHwpxLimits::new(ShapePointsHwpxLimitConfig {
            payload_bytes: 0,
            ..ShapePointsHwpxLimitConfig::default()
        }),
        "shape_points_hwpx_invalid_limit",
    );
    let source_path = polygon(&[(0, 0), (1000, 0), (0, 1000)]);
    let source_state = state(ObjectKind::Polygon, source_path.clone())?;
    let domain_plan = domain_plan(&source_state, polygon(&[(0, 0), (2000, 0), (0, 1000)]))?;
    let section = section(ObjectKind::Polygon, &source_path);
    let plan = hwpx_plan(section.as_bytes(), &domain_plan)?;
    let (_, receipt) = ShapePointsHwpxLowerer::lower_in_section_with_receipt(
        section.as_bytes(),
        &plan,
        FLOW_BEFORE,
        ObjectGeometryLimits::default(),
        ObjectGeometryHwpxLimits::default(),
        BasicShapeLimits::default(),
        state_limits(),
        ShapePointsHwpxLimits::default(),
    )?;
    let debug = format!("{source_state:?} {domain_plan:?} {plan:?} {receipt:?}");
    for private in [
        "private-freeform-object",
        "PRIVATE_LINE_APPEARANCE",
        FLOW_BEFORE,
        FLOW_AFTER,
        APPEARANCE,
        OPAQUE,
        "2000",
    ] {
        assert!(!debug.contains(private), "debug leaked {private}: {debug}");
    }
    Ok(())
}

fn hwpx_plan(
    section: &[u8],
    domain_plan: &domain_ir::ShapePointsPlan,
) -> Result<hwpx_package::ShapePointsHwpxPlan, ShapePointsHwpxError> {
    ShapePointsHwpxBuilder::plan(
        section,
        0,
        domain_plan,
        FLOW_BEFORE,
        ObjectGeometryLimits::default(),
        ObjectGeometryHwpxLimits::default(),
        BasicShapeLimits::default(),
        state_limits(),
        ShapePointsHwpxLimits::default(),
    )
}

fn domain_plan(
    source: &ShapePointsState,
    target_freeform: FreeformShape,
) -> Result<domain_ir::ShapePointsPlan, Box<dyn Error>> {
    let request = ShapePointsRequest::from_draft(
        ShapePointsRequestDraft {
            schema_version: SHAPE_POINTS_SCHEMA_VERSION.to_owned(),
            request_id: LogicalId::parse("private-point-request")?,
            expected_source_state_sha256: source.canonical_sha256(state_limits())?,
            expected_document_flow_sha256: FLOW_BEFORE.to_owned(),
            target_document_flow_sha256: FLOW_AFTER.to_owned(),
            target_freeform,
        },
        source,
        FLOW_BEFORE,
        BasicShapeLimits::default(),
        state_limits(),
    )?;
    Ok(ShapePointsBuilder::plan(
        source,
        &request,
        FLOW_BEFORE,
        BasicShapeLimits::default(),
        state_limits(),
    )?)
}

fn state(kind: ObjectKind, freeform: FreeformShape) -> Result<ShapePointsState, Box<dyn Error>> {
    Ok(ShapePointsState::from_draft(
        ShapePointsStateDraft {
            schema_version: SHAPE_POINTS_SCHEMA_VERSION.to_owned(),
            geometry: geometry(kind)?,
            freeform,
            appearance_state_sha256: APPEARANCE.to_owned(),
            property_state_sha256: PROPERTIES.to_owned(),
            resource_inventory_sha256: RESOURCES.to_owned(),
            embedded_content_state_sha256: EMBEDDED.to_owned(),
            opaque_state_sha256: OPAQUE.to_owned(),
        },
        ObjectGeometryLimits::default(),
        BasicShapeLimits::default(),
        state_limits(),
    )?)
}

fn geometry(kind: ObjectKind) -> Result<ObjectGeometryStateDraft, Box<dyn Error>> {
    Ok(ObjectGeometryStateDraft {
        schema_version: OBJECT_GEOMETRY_SCHEMA_VERSION.to_owned(),
        object_id: LogicalId::parse("private-freeform-object")?,
        object_kind: kind,
        native_object_id: 41,
        native_instance_id: 99,
        z_order: 3,
        numbering_type: ObjectNumberingType::None,
        locked: false,
        size: ObjectSize {
            width_hwpunit: 7200,
            width_reference: ObjectWidthReference::Absolute,
            height_hwpunit: 7200,
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
            left_hwpunit: 1,
            right_hwpunit: 2,
            top_hwpunit: 3,
            bottom_hwpunit: 4,
        },
        component: ObjectComponentGeometry {
            offset: ObjectPoint {
                x_hwpunit: 0,
                y_hwpunit: 0,
            },
            original_size: ObjectExtent {
                width_hwpunit: 7200,
                height_hwpunit: 7200,
            },
            current_size: ObjectExtent {
                width_hwpunit: 7200,
                height_hwpunit: 7200,
            },
            flip: ObjectFlip {
                horizontal: false,
                vertical: false,
            },
            rotation: ObjectRotation {
                angle_degrees: 0,
                center_x_hwpunit: 3600,
                center_y_hwpunit: 3600,
                rotate_image: true,
            },
            transform: ObjectTransform {
                translation: identity(),
                scale: identity(),
                rotation: identity(),
            },
        },
    })
}

fn identity() -> ObjectAffineMatrix {
    ObjectAffineMatrix::IDENTITY
}

fn state_limits() -> ShapePointsLimits {
    ShapePointsLimits::new(ShapePointsLimitConfig::default()).expect("state limits")
}

fn polygon(points: &[(i32, i32)]) -> FreeformShape {
    FreeformShape::Polygon {
        points: points
            .iter()
            .map(|&(x, y)| ShapePoint {
                x_hwpunit: x,
                y_hwpunit: y,
            })
            .collect(),
    }
}

fn curve(delta: i32) -> FreeformShape {
    FreeformShape::Curve {
        segments: vec![
            CurveSegment {
                segment_type: CurveSegmentType::Line,
                x1_hwpunit: 0,
                y1_hwpunit: 0,
                x2_hwpunit: 1000 + delta,
                y2_hwpunit: 0,
            },
            CurveSegment {
                segment_type: CurveSegmentType::Curve,
                x1_hwpunit: 1000 + delta,
                y1_hwpunit: 0,
                x2_hwpunit: 1000,
                y2_hwpunit: 1000,
            },
        ],
    }
}

fn section(kind: ObjectKind, freeform: &FreeformShape) -> String {
    let tag = match kind {
        ObjectKind::Polygon => "polygon",
        ObjectKind::Curve => "curve",
        _ => unreachable!("test only uses freeform kinds"),
    };
    let mut payload = String::new();
    match freeform {
        FreeformShape::Polygon { points } => {
            for point in points {
                write!(
                    payload,
                    "<c:pt x=\"{}\" y=\"{}\"/>",
                    point.x_hwpunit, point.y_hwpunit
                )
                .expect("write point fixture");
            }
        }
        FreeformShape::Curve { segments } => {
            for segment in segments {
                let segment_type = match segment.segment_type {
                    CurveSegmentType::Line => "LINE",
                    CurveSegmentType::Curve => "CURVE",
                };
                write!(
                    payload,
                    "<q:seg type=\"{segment_type}\" x1=\"{}\" y1=\"{}\" x2=\"{}\" y2=\"{}\"/>",
                    segment.x1_hwpunit, segment.y1_hwpunit, segment.x2_hwpunit, segment.y2_hwpunit
                )
                .expect("write segment fixture");
            }
        }
    }
    format!(
        concat!(
            "<hs:sec xmlns:hs=\"http://www.hancom.co.kr/hwpml/2011/section\" ",
            "xmlns:q=\"http://www.hancom.co.kr/hwpml/2011/paragraph\" ",
            "xmlns:c=\"http://www.hancom.co.kr/hwpml/2011/core\">",
            "<q:p id=\"10\" paraPrIDRef=\"1\" styleIDRef=\"1\"><q:run charPrIDRef=\"1\">",
            "<q:{tag} id=\"41\" zOrder=\"3\" numberingType=\"NONE\" textWrap=\"SQUARE\" textFlow=\"BOTH_SIDES\" lock=\"0\" dropcapstyle=\"None\" href=\"\" groupLevel=\"0\" instid=\"99\">",
            "<q:offset x=\"0\" y=\"0\"/><q:orgSz width=\"7200\" height=\"7200\"/><q:curSz width=\"7200\" height=\"7200\"/>",
            "<q:flip horizontal=\"0\" vertical=\"0\"/><q:rotationInfo angle=\"0\" centerX=\"3600\" centerY=\"3600\" rotateimage=\"1\"/>",
            "<q:renderingInfo><c:transMatrix e1=\"1\" e2=\"0\" e3=\"0\" e4=\"0\" e5=\"1\" e6=\"0\"/>",
            "<c:scaMatrix e1=\"1\" e2=\"0\" e3=\"0\" e4=\"0\" e5=\"1\" e6=\"0\"/><c:rotMatrix e1=\"1\" e2=\"0\" e3=\"0\" e4=\"0\" e5=\"1\" e6=\"0\"/></q:renderingInfo>",
            "<q:lineShape marker=\"PRIVATE_LINE_APPEARANCE\"/><c:fillBrush marker=\"PRIVATE_FILL_APPEARANCE\"/>",
            "{payload}",
            "<q:shadow marker=\"PRIVATE_SHADOW_APPEARANCE\"/><q:shapeComment>PRIVATE_CAPTION_OR_COMMENT</q:shapeComment>",
            "<q:sz width=\"7200\" widthRelTo=\"ABSOLUTE\" height=\"7200\" heightRelTo=\"ABSOLUTE\" protect=\"0\"/>",
            "<q:pos treatAsChar=\"0\" affectLSpacing=\"0\" flowWithText=\"1\" allowOverlap=\"0\" holdAnchorAndSO=\"1\" vertRelTo=\"PARA\" horzRelTo=\"PARA\" vertAlign=\"TOP\" horzAlign=\"LEFT\" vertOffset=\"200\" horzOffset=\"100\"/>",
            "<q:outMargin left=\"1\" right=\"2\" top=\"3\" bottom=\"4\"/></q:{tag}>",
            "<q:t>PRIVATE_AFTER_OBJECT</q:t></q:run></q:p></hs:sec>"
        ),
        tag = tag,
        payload = payload
    )
}

fn assert_code<T>(result: Result<T, ShapePointsHwpxError>, expected: &str) {
    let Err(error) = result else {
        panic!("operation unexpectedly succeeded")
    };
    assert_eq!(error.code(), expected, "{error:?}");
}
