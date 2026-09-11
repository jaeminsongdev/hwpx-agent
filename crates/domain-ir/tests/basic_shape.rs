#![allow(clippy::expect_used)] // Test fixtures use expectations to keep failures local and legible.

use domain_ir::{
    BASIC_SHAPE_SCHEMA_VERSION, BasicShape, BasicShapeBuilder, BasicShapeError,
    BasicShapeLimitConfig, BasicShapeLimits, BasicShapeRequest, BasicShapeRequestDraft,
    CurveSegment, CurveSegmentType, EllipseArcType, EllipseShape, FreeformShape, LineShape,
    LogicalId, ObjectAffineMatrix, ObjectAnchor, ObjectComponentGeometry, ObjectExtent, ObjectFlip,
    ObjectGeometryLimitConfig, ObjectGeometryLimits, ObjectGeometryStateDraft,
    ObjectHeightReference, ObjectHorizontalAlignment, ObjectHorizontalReference, ObjectKind,
    ObjectNumberingType, ObjectOuterMargins, ObjectPoint, ObjectPosition, ObjectRotation,
    ObjectSize, ObjectTextFlow, ObjectTextWrap, ObjectTransform, ObjectVerticalAlignment,
    ObjectVerticalReference, ObjectWidthReference, ObjectWrap, RectangleShape, ShapePoint,
    TextBoxContent, TextBoxMargins, TextBoxVerticalAlignment,
};

const FLOW_A: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const FLOW_B: &str = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";

fn limits() -> BasicShapeLimits {
    BasicShapeLimits::new(BasicShapeLimitConfig::default()).expect("valid limits")
}

fn geometry_limits() -> ObjectGeometryLimits {
    ObjectGeometryLimits::new(ObjectGeometryLimitConfig::default()).expect("valid geometry limits")
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

fn geometry(kind: ObjectKind, object_id: u32, instance_id: u32) -> ObjectGeometryStateDraft {
    ObjectGeometryStateDraft {
        schema_version: "hwpx-agent.object-geometry/v1".to_owned(),
        object_id: LogicalId::parse("logical-shape").expect("logical id"),
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
        name: "body".to_owned(),
        editable: true,
        margins: TextBoxMargins {
            left_hwpunit: 100,
            right_hwpunit: 101,
            top_hwpunit: 102,
            bottom_hwpunit: 103,
        },
        sublist_id: 301,
        paragraph_id: 401,
        paragraph_properties_id: 0,
        style_id: 0,
        character_properties_id: 0,
        text_width_hwpunit: 7000,
        text_height_hwpunit: 3400,
        vertical_alignment: TextBoxVerticalAlignment::Center,
        text: "한글 <shape> & text".to_owned(),
    }
}

fn request(shape: BasicShape, kind: ObjectKind) -> BasicShapeRequest {
    BasicShapeRequest::from_draft(
        BasicShapeRequestDraft {
            schema_version: BASIC_SHAPE_SCHEMA_VERSION.to_owned(),
            request_id: LogicalId::parse("shape-request").expect("request id"),
            expected_document_flow_sha256: FLOW_A.to_owned(),
            target_document_flow_sha256: FLOW_B.to_owned(),
            geometry: geometry(kind, 91, 191),
            shape,
        },
        FLOW_A,
        geometry_limits(),
        limits(),
    )
    .expect("request")
}

#[test]
#[allow(clippy::too_many_lines)]
fn plans_and_builds_all_five_semantic_shape_families() {
    let shapes = [
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
                    center: ShapePoint {
                        x_hwpunit: 3600,
                        y_hwpunit: 1800,
                    },
                    axis_1: ShapePoint {
                        x_hwpunit: 7200,
                        y_hwpunit: 1800,
                    },
                    axis_2: ShapePoint {
                        x_hwpunit: 3600,
                        y_hwpunit: 3600,
                    },
                    start_1: ShapePoint {
                        x_hwpunit: 7200,
                        y_hwpunit: 1800,
                    },
                    start_2: ShapePoint {
                        x_hwpunit: 3600,
                        y_hwpunit: 3600,
                    },
                    end_1: ShapePoint {
                        x_hwpunit: 0,
                        y_hwpunit: 1800,
                    },
                    end_2: ShapePoint {
                        x_hwpunit: 3600,
                        y_hwpunit: 0,
                    },
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
                    points: vec![
                        ShapePoint {
                            x_hwpunit: 0,
                            y_hwpunit: 0,
                        },
                        ShapePoint {
                            x_hwpunit: 1000,
                            y_hwpunit: 0,
                        },
                        ShapePoint {
                            x_hwpunit: 500,
                            y_hwpunit: 800,
                        },
                    ],
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
    ];
    for (shape, kind) in shapes {
        let request = request(shape.clone(), kind);
        let first = BasicShapeBuilder::plan(&request, FLOW_A, geometry_limits(), limits())
            .expect("first plan");
        let second = BasicShapeBuilder::plan(&request, FLOW_A, geometry_limits(), limits())
            .expect("second plan");
        assert_eq!(
            first.canonical_json(limits()).expect("plan JSON"),
            second.canonical_json(limits()).expect("plan JSON")
        );
        let result =
            BasicShapeBuilder::build(&first, FLOW_A, geometry_limits(), limits()).expect("build");
        assert_eq!(result.shape(), &shape);
        assert_eq!(result.geometry().object_kind(), kind);
        assert_eq!(result.receipt().target_document_flow_sha256(), FLOW_B);
    }
}

#[test]
fn text_box_capability_and_redacted_debug_are_exact() {
    let request = request(
        BasicShape::TextBox {
            rectangle: rectangle(),
            content: text_box(),
        },
        ObjectKind::Rectangle,
    );
    assert_eq!(request.shape().capability_id(), "obj.textbox_insert");
    let debug = format!("{request:?}");
    assert!(!debug.contains("한글"));
    assert!(!debug.contains("shape-request"));
    assert!(!debug.contains(FLOW_A));
    assert!(debug.contains("<redacted>"));
}

#[test]
fn kind_flow_and_native_identity_drift_fail_closed() {
    let wrong_kind = BasicShapeRequest::from_draft(
        BasicShapeRequestDraft {
            schema_version: BASIC_SHAPE_SCHEMA_VERSION.to_owned(),
            request_id: LogicalId::parse("shape-request").expect("request id"),
            expected_document_flow_sha256: FLOW_A.to_owned(),
            target_document_flow_sha256: FLOW_B.to_owned(),
            geometry: geometry(ObjectKind::Ellipse, 91, 191),
            shape: BasicShape::Rectangle {
                rectangle: rectangle(),
            },
        },
        FLOW_A,
        geometry_limits(),
        limits(),
    )
    .expect_err("kind mismatch");
    assert_eq!(wrong_kind.code(), "basic_shape_kind_mismatch");

    let flow = BasicShapeRequest::from_draft(
        BasicShapeRequestDraft {
            schema_version: BASIC_SHAPE_SCHEMA_VERSION.to_owned(),
            request_id: LogicalId::parse("shape-request").expect("request id"),
            expected_document_flow_sha256: FLOW_A.to_owned(),
            target_document_flow_sha256: FLOW_B.to_owned(),
            geometry: geometry(ObjectKind::Rectangle, 91, 191),
            shape: BasicShape::Rectangle {
                rectangle: rectangle(),
            },
        },
        FLOW_B,
        geometry_limits(),
        limits(),
    )
    .expect_err("flow mismatch");
    assert_eq!(flow.code(), "basic_shape_flow_drift");

    let mut same_id = geometry(ObjectKind::Rectangle, 91, 191);
    same_id.native_instance_id = 91;
    let identity = BasicShapeRequest::from_draft(
        BasicShapeRequestDraft {
            schema_version: BASIC_SHAPE_SCHEMA_VERSION.to_owned(),
            request_id: LogicalId::parse("shape-request").expect("request id"),
            expected_document_flow_sha256: FLOW_A.to_owned(),
            target_document_flow_sha256: FLOW_B.to_owned(),
            geometry: same_id,
            shape: BasicShape::Rectangle {
                rectangle: rectangle(),
            },
        },
        FLOW_A,
        geometry_limits(),
        limits(),
    )
    .expect_err("identity alias");
    assert_eq!(identity.code(), "basic_shape_kind_mismatch");
}

#[test]
fn invalid_rectangle_ellipse_polygon_curve_and_text_fail_closed() {
    let mut flat = rectangle();
    flat.corners[2] = flat.corners[1];
    assert!(matches!(
        BasicShapeRequest::from_draft(
            BasicShapeRequestDraft {
                schema_version: BASIC_SHAPE_SCHEMA_VERSION.to_owned(),
                request_id: LogicalId::parse("request").expect("id"),
                expected_document_flow_sha256: FLOW_A.to_owned(),
                target_document_flow_sha256: FLOW_B.to_owned(),
                geometry: geometry(ObjectKind::Rectangle, 1, 2),
                shape: BasicShape::Rectangle { rectangle: flat },
            },
            FLOW_A,
            geometry_limits(),
            limits()
        ),
        Err(BasicShapeError::InvalidTopology)
    ));

    let invalids = [
        BasicShape::Freeform {
            freeform: FreeformShape::Polygon {
                points: vec![
                    ShapePoint {
                        x_hwpunit: 0,
                        y_hwpunit: 0,
                    },
                    ShapePoint {
                        x_hwpunit: 1,
                        y_hwpunit: 1,
                    },
                    ShapePoint {
                        x_hwpunit: 2,
                        y_hwpunit: 2,
                    },
                ],
            },
        },
        BasicShape::Freeform {
            freeform: FreeformShape::Curve {
                segments: vec![CurveSegment {
                    segment_type: CurveSegmentType::Curve,
                    x1_hwpunit: 7,
                    y1_hwpunit: 7,
                    x2_hwpunit: 7,
                    y2_hwpunit: 7,
                }],
            },
        },
    ];
    for shape in invalids {
        let kind = shape.object_kind();
        let error = BasicShapeRequest::from_draft(
            BasicShapeRequestDraft {
                schema_version: BASIC_SHAPE_SCHEMA_VERSION.to_owned(),
                request_id: LogicalId::parse("request").expect("id"),
                expected_document_flow_sha256: FLOW_A.to_owned(),
                target_document_flow_sha256: FLOW_B.to_owned(),
                geometry: geometry(kind, 1, 2),
                shape,
            },
            FLOW_A,
            geometry_limits(),
            limits(),
        )
        .expect_err("invalid topology");
        assert_eq!(error.code(), "basic_shape_invalid_topology");
    }

    let mut content = text_box();
    content.text = "bad\u{1}text".to_owned();
    let error = BasicShapeRequest::from_draft(
        BasicShapeRequestDraft {
            schema_version: BASIC_SHAPE_SCHEMA_VERSION.to_owned(),
            request_id: LogicalId::parse("request").expect("id"),
            expected_document_flow_sha256: FLOW_A.to_owned(),
            target_document_flow_sha256: FLOW_B.to_owned(),
            geometry: geometry(ObjectKind::Rectangle, 1, 2),
            shape: BasicShape::TextBox {
                rectangle: rectangle(),
                content,
            },
        },
        FLOW_A,
        geometry_limits(),
        limits(),
    )
    .expect_err("invalid text");
    assert_eq!(error.code(), "basic_shape_invalid_text");
}

#[test]
fn strict_json_rejects_duplicate_unknown_and_oversized_input() {
    let request = request(
        BasicShape::Rectangle {
            rectangle: rectangle(),
        },
        ObjectKind::Rectangle,
    );
    let bytes = request.canonical_json(limits()).expect("request JSON");
    let duplicate = bytes
        .strip_suffix(b"}")
        .expect("object suffix")
        .iter()
        .copied()
        .chain(
            b",\"schema_version\":\"hwpx-agent.basic-shape/v1\"}"
                .iter()
                .copied(),
        )
        .collect::<Vec<_>>();
    assert_eq!(
        BasicShapeRequest::from_json(&duplicate, FLOW_A, geometry_limits(), limits())
            .expect_err("duplicate")
            .code(),
        "basic_shape_duplicate_json_key"
    );
    let unknown = bytes
        .strip_suffix(b"}")
        .expect("object suffix")
        .iter()
        .copied()
        .chain(b",\"unknown\":1}".iter().copied())
        .collect::<Vec<_>>();
    assert_eq!(
        BasicShapeRequest::from_json(&unknown, FLOW_A, geometry_limits(), limits())
            .expect_err("unknown")
            .code(),
        "basic_shape_invalid_json"
    );
    let tiny = BasicShapeLimits::new(BasicShapeLimitConfig {
        input_bytes: 16,
        output_bytes: 16,
        ..BasicShapeLimitConfig::default()
    })
    .expect("tiny limits");
    assert_eq!(
        BasicShapeRequest::from_json(&bytes, FLOW_A, geometry_limits(), tiny)
            .expect_err("oversized")
            .code(),
        "basic_shape_input_limit"
    );
}

#[test]
fn build_rechecks_current_flow() {
    let request = request(
        BasicShape::Rectangle {
            rectangle: rectangle(),
        },
        ObjectKind::Rectangle,
    );
    let plan =
        BasicShapeBuilder::plan(&request, FLOW_A, geometry_limits(), limits()).expect("plan");
    assert_eq!(
        BasicShapeBuilder::build(&plan, FLOW_B, geometry_limits(), limits())
            .expect_err("stale flow")
            .code(),
        "basic_shape_build_drift"
    );
}
