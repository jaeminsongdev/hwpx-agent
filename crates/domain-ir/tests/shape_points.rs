#![allow(clippy::expect_used)] // Fixtures keep failures local and readable.

use domain_ir::{
    BasicShape, BasicShapeLimitConfig, BasicShapeLimits, CurveSegment, CurveSegmentType,
    FreeformShape, LogicalId, OBJECT_GEOMETRY_SCHEMA_VERSION, ObjectAffineMatrix, ObjectAnchor,
    ObjectComponentGeometry, ObjectExtent, ObjectFlip, ObjectGeometryLimitConfig,
    ObjectGeometryLimits, ObjectGeometryStateDraft, ObjectHeightReference,
    ObjectHorizontalAlignment, ObjectHorizontalReference, ObjectKind, ObjectNumberingType,
    ObjectOuterMargins, ObjectPoint, ObjectPosition, ObjectRotation, ObjectSize, ObjectTextFlow,
    ObjectTextWrap, ObjectTransform, ObjectVerticalAlignment, ObjectVerticalReference,
    ObjectWidthReference, ObjectWrap, SHAPE_POINTS_SCHEMA_VERSION, ShapePoint, ShapePointsBuilder,
    ShapePointsError, ShapePointsLimitConfig, ShapePointsLimits, ShapePointsRequest,
    ShapePointsRequestDraft, ShapePointsState, ShapePointsStateDraft,
};

const FLOW_A: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const FLOW_B: &str = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
const STATE_C: &str = "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc";
const STATE_D: &str = "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd";
const STATE_E: &str = "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee";

fn geometry_limits() -> ObjectGeometryLimits {
    ObjectGeometryLimits::new(ObjectGeometryLimitConfig::default()).expect("geometry limits")
}

fn shape_limits() -> BasicShapeLimits {
    BasicShapeLimits::new(BasicShapeLimitConfig::default()).expect("shape limits")
}

fn limits() -> ShapePointsLimits {
    ShapePointsLimits::new(ShapePointsLimitConfig::default()).expect("point limits")
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

fn geometry(kind: ObjectKind) -> ObjectGeometryStateDraft {
    ObjectGeometryStateDraft {
        schema_version: OBJECT_GEOMETRY_SCHEMA_VERSION.to_owned(),
        object_id: LogicalId::parse("private-shape-1").expect("object id"),
        object_kind: kind,
        native_object_id: 41,
        native_instance_id: 99,
        z_order: 3,
        numbering_type: ObjectNumberingType::None,
        locked: false,
        size: ObjectSize {
            width_hwpunit: 7_200,
            width_reference: ObjectWidthReference::Absolute,
            height_hwpunit: 7_200,
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
                width_hwpunit: 7_200,
                height_hwpunit: 7_200,
            },
            current_size: ObjectExtent {
                width_hwpunit: 7_200,
                height_hwpunit: 7_200,
            },
            flip: ObjectFlip {
                horizontal: false,
                vertical: false,
            },
            rotation: ObjectRotation {
                angle_degrees: 0,
                center_x_hwpunit: 3_600,
                center_y_hwpunit: 3_600,
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

fn polygon(points: &[(i32, i32)]) -> FreeformShape {
    FreeformShape::Polygon {
        points: points
            .iter()
            .map(|(x, y)| ShapePoint {
                x_hwpunit: *x,
                y_hwpunit: *y,
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
                x2_hwpunit: 1_000 + delta,
                y2_hwpunit: 0,
            },
            CurveSegment {
                segment_type: CurveSegmentType::Curve,
                x1_hwpunit: 1_000 + delta,
                y1_hwpunit: 0,
                x2_hwpunit: 1_000,
                y2_hwpunit: 1_000,
            },
        ],
    }
}

fn state(kind: ObjectKind, freeform: FreeformShape) -> ShapePointsState {
    ShapePointsState::from_draft(
        ShapePointsStateDraft {
            schema_version: SHAPE_POINTS_SCHEMA_VERSION.to_owned(),
            geometry: geometry(kind),
            freeform,
            appearance_state_sha256: FLOW_A.to_owned(),
            property_state_sha256: FLOW_B.to_owned(),
            resource_inventory_sha256: STATE_C.to_owned(),
            embedded_content_state_sha256: STATE_D.to_owned(),
            opaque_state_sha256: STATE_E.to_owned(),
        },
        geometry_limits(),
        shape_limits(),
        limits(),
    )
    .expect("valid state")
}

fn request(
    source: &ShapePointsState,
    target_freeform: FreeformShape,
) -> Result<ShapePointsRequest, ShapePointsError> {
    ShapePointsRequest::from_draft(
        ShapePointsRequestDraft {
            schema_version: SHAPE_POINTS_SCHEMA_VERSION.to_owned(),
            request_id: LogicalId::parse("request-1").expect("request id"),
            expected_source_state_sha256: source.canonical_sha256(limits()).expect("state digest"),
            expected_document_flow_sha256: FLOW_A.to_owned(),
            target_document_flow_sha256: FLOW_B.to_owned(),
            target_freeform,
        },
        source,
        FLOW_A,
        shape_limits(),
        limits(),
    )
}

#[test]
fn freeform_insert_has_its_exact_capability_id() {
    let shape = BasicShape::Freeform {
        freeform: polygon(&[(0, 0), (1_000, 0), (0, 1_000)]),
    };
    assert_eq!(shape.capability_id(), "obj.freeform");
}

#[test]
fn edits_polygon_and_curve_points_without_touching_other_state() {
    let cases = [
        (
            state(
                ObjectKind::Polygon,
                polygon(&[(0, 0), (1_000, 0), (0, 1_000)]),
            ),
            polygon(&[(0, 0), (2_000, 0), (0, 1_000)]),
        ),
        (state(ObjectKind::Curve, curve(0)), curve(100)),
    ];
    for (source, target_path) in cases {
        let request = request(&source, target_path.clone()).expect("request");
        assert_eq!(request.capability_id(), "obj.shape_edit_points");
        let plan = ShapePointsBuilder::plan(&source, &request, FLOW_A, shape_limits(), limits())
            .expect("plan");
        let target = ShapePointsBuilder::build(&plan, &source, FLOW_A, shape_limits(), limits())
            .expect("build")
            .state;
        assert_eq!(target.freeform(), &target_path);

        let before: serde_json::Value =
            serde_json::from_slice(&source.canonical_json(limits()).expect("source json"))
                .expect("source value");
        let after: serde_json::Value =
            serde_json::from_slice(&target.canonical_json(limits()).expect("target json"))
                .expect("target value");
        for field in [
            "geometry",
            "appearance_state_sha256",
            "property_state_sha256",
            "resource_inventory_sha256",
            "embedded_content_state_sha256",
            "opaque_state_sha256",
        ] {
            assert_eq!(before[field], after[field], "field {field}");
        }
    }
}

#[test]
fn topology_kind_mismatch_degenerate_and_noop_edits_fail_closed() {
    let source = state(
        ObjectKind::Polygon,
        polygon(&[(0, 0), (1_000, 0), (0, 1_000)]),
    );
    assert_eq!(
        request(&source, source.freeform().clone()),
        Err(ShapePointsError::Noop)
    );
    assert!(matches!(
        request(&source, curve(10)),
        Err(ShapePointsError::TopologyInvalid)
    ));
    assert!(matches!(
        request(&source, polygon(&[(0, 0), (1, 1), (2, 2)])),
        Err(ShapePointsError::TopologyInvalid)
    ));
}

#[test]
fn request_and_build_recheck_exact_source_state_and_flow() {
    let source = state(
        ObjectKind::Polygon,
        polygon(&[(0, 0), (1_000, 0), (0, 1_000)]),
    );
    let request = request(&source, polygon(&[(0, 0), (2_000, 0), (0, 1_000)])).expect("request");
    assert_eq!(
        ShapePointsBuilder::plan(&source, &request, FLOW_B, shape_limits(), limits()),
        Err(ShapePointsError::DocumentFlowDrift)
    );
    let plan = ShapePointsBuilder::plan(&source, &request, FLOW_A, shape_limits(), limits())
        .expect("plan");
    let drifted = state(
        ObjectKind::Polygon,
        polygon(&[(0, 0), (1_500, 0), (0, 1_000)]),
    );
    assert_eq!(
        ShapePointsBuilder::build(&plan, &drifted, FLOW_A, shape_limits(), limits()),
        Err(ShapePointsError::SourceStateDrift)
    );
    assert_eq!(
        ShapePointsBuilder::build(&plan, &source, FLOW_B, shape_limits(), limits()),
        Err(ShapePointsError::DocumentFlowDrift)
    );
}

#[test]
fn strict_json_rejects_duplicate_unknown_and_oversized_input() {
    let source = state(
        ObjectKind::Polygon,
        polygon(&[(0, 0), (1_000, 0), (0, 1_000)]),
    );
    let request = request(&source, polygon(&[(0, 0), (2_000, 0), (0, 1_000)])).expect("request");
    let json = request.canonical_json(limits()).expect("json");
    assert!(
        ShapePointsRequest::from_json(&json, &source, FLOW_A, shape_limits(), limits()).is_ok()
    );
    let duplicate = br#"{"schema_version":"hwpx-agent.shape-points/v1","schema_version":"hwpx-agent.shape-points/v1"}"#;
    assert_eq!(
        ShapePointsRequest::from_json(duplicate, &source, FLOW_A, shape_limits(), limits()),
        Err(ShapePointsError::InvalidJson)
    );
    let mut unknown: serde_json::Value = serde_json::from_slice(&json).expect("value");
    unknown
        .as_object_mut()
        .expect("object")
        .insert("unknown".to_owned(), serde_json::Value::Bool(true));
    assert_eq!(
        ShapePointsRequest::from_json(
            &serde_json::to_vec(&unknown).expect("bytes"),
            &source,
            FLOW_A,
            shape_limits(),
            limits()
        ),
        Err(ShapePointsError::InvalidJson)
    );
    assert_eq!(
        ShapePointsRequest::from_json(
            &vec![b' '; limits().config().input_bytes + 1],
            &source,
            FLOW_A,
            shape_limits(),
            limits()
        ),
        Err(ShapePointsError::InputLimit)
    );
}

#[test]
fn debug_redacts_identity_path_and_all_state_bindings() {
    let source = state(
        ObjectKind::Polygon,
        polygon(&[(0, 0), (1_000, 0), (0, 1_000)]),
    );
    let request = request(&source, polygon(&[(0, 0), (2_000, 0), (0, 1_000)])).expect("request");
    let plan = ShapePointsBuilder::plan(&source, &request, FLOW_A, shape_limits(), limits())
        .expect("plan");
    let debug = format!("{source:?} {request:?} {plan:?}");
    for private in ["private-shape-1", "2000", FLOW_A, FLOW_B, STATE_C] {
        assert!(!debug.contains(private));
    }
}
