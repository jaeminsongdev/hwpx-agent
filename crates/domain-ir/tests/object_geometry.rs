#![allow(clippy::expect_used)] // Test fixtures use expectations to keep failures local and legible.

use domain_ir::{
    LogicalId, OBJECT_GEOMETRY_SCHEMA_VERSION, ObjectAffineMatrix, ObjectAnchor,
    ObjectComponentGeometry, ObjectExtent, ObjectFlip, ObjectGeometryBuilder, ObjectGeometryError,
    ObjectGeometryLimitConfig, ObjectGeometryLimits, ObjectGeometryOperation,
    ObjectGeometryRequest, ObjectGeometryRequestDraft, ObjectGeometryState,
    ObjectGeometryStateDraft, ObjectHeightReference, ObjectHorizontalAlignment,
    ObjectHorizontalReference, ObjectKind, ObjectNumberingType, ObjectOuterMargins, ObjectPoint,
    ObjectPosition, ObjectRotation, ObjectSize, ObjectTextFlow, ObjectTextWrap, ObjectTransform,
    ObjectVerticalAlignment, ObjectVerticalReference, ObjectWidthReference, ObjectWrap,
};

const FLOW_A: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const FLOW_B: &str = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";

fn limits() -> ObjectGeometryLimits {
    ObjectGeometryLimits::new(ObjectGeometryLimitConfig::default()).expect("valid limits")
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

fn transform() -> ObjectTransform {
    ObjectTransform {
        translation: ObjectAffineMatrix {
            e5_millionths: 10_000_000,
            e6_millionths: 20_000_000,
            ..identity_matrix()
        },
        scale: identity_matrix(),
        rotation: identity_matrix(),
    }
}

fn component() -> ObjectComponentGeometry {
    ObjectComponentGeometry {
        offset: ObjectPoint {
            x_hwpunit: 10,
            y_hwpunit: 20,
        },
        original_size: ObjectExtent {
            width_hwpunit: 7_200,
            height_hwpunit: 3_600,
        },
        current_size: ObjectExtent {
            width_hwpunit: 7_200,
            height_hwpunit: 3_600,
        },
        flip: ObjectFlip {
            horizontal: false,
            vertical: false,
        },
        rotation: ObjectRotation {
            angle_degrees: 0,
            center_x_hwpunit: 3_600,
            center_y_hwpunit: 1_800,
            rotate_image: true,
        },
        transform: transform(),
    }
}

fn state(kind: ObjectKind) -> ObjectGeometryState {
    ObjectGeometryState::from_draft(
        ObjectGeometryStateDraft {
            schema_version: OBJECT_GEOMETRY_SCHEMA_VERSION.to_owned(),
            object_id: LogicalId::parse("shape-1").expect("logical id"),
            object_kind: kind,
            native_object_id: 41,
            native_instance_id: 99,
            z_order: 3,
            numbering_type: ObjectNumberingType::Picture,
            locked: false,
            size: ObjectSize {
                width_hwpunit: 7_200,
                width_reference: ObjectWidthReference::Absolute,
                height_hwpunit: 3_600,
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
                vertical_offset_hwpunit: 2_000,
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
            component: component(),
        },
        limits(),
    )
    .expect("valid state")
}

fn request(
    source: &ObjectGeometryState,
    operation: ObjectGeometryOperation,
) -> ObjectGeometryRequest {
    ObjectGeometryRequest::from_draft(
        ObjectGeometryRequestDraft {
            schema_version: OBJECT_GEOMETRY_SCHEMA_VERSION.to_owned(),
            request_id: LogicalId::parse("request-1").expect("request id"),
            expected_source_state_sha256: source.canonical_sha256(limits()).expect("state digest"),
            expected_document_flow_sha256: FLOW_A.to_owned(),
            target_document_flow_sha256: FLOW_B.to_owned(),
            operation,
        },
        source,
        FLOW_A,
        limits(),
    )
    .expect("valid request")
}

#[test]
fn plans_and_builds_all_six_exact_geometry_capabilities() {
    let source = state(ObjectKind::Rectangle);
    let target_position = ObjectPosition {
        horizontal_alignment: ObjectHorizontalAlignment::Outside,
        vertical_alignment: ObjectVerticalAlignment::Bottom,
        horizontal_offset_hwpunit: 9_000,
        vertical_offset_hwpunit: 8_000,
    };
    let target_anchor = ObjectAnchor {
        treat_as_character: true,
        affect_line_spacing: true,
        flow_with_text: false,
        allow_overlap: true,
        hold_anchor_and_shape: false,
        horizontal_reference: ObjectHorizontalReference::Page,
        vertical_reference: ObjectVerticalReference::Page,
    };
    let target_wrap = ObjectWrap {
        text_wrap: ObjectTextWrap::BehindText,
        text_flow: ObjectTextFlow::RightOnly,
    };
    let target_margins = ObjectOuterMargins {
        left_hwpunit: 101,
        right_hwpunit: 102,
        top_hwpunit: 103,
        bottom_hwpunit: 104,
    };
    let mut target_component = component();
    target_component.current_size = ObjectExtent {
        width_hwpunit: 14_400,
        height_hwpunit: 7_200,
    };
    let target_size = ObjectSize {
        width_hwpunit: 14_400,
        height_hwpunit: 7_200,
        ..source.size()
    };
    let target_rotation = ObjectRotation {
        angle_degrees: -90,
        center_x_hwpunit: 7_200,
        center_y_hwpunit: 3_600,
        rotate_image: false,
    };
    let target_flip = ObjectFlip {
        horizontal: true,
        vertical: true,
    };
    let operations = [
        ObjectGeometryOperation::SetPosition {
            position: target_position,
        },
        ObjectGeometryOperation::SetSize {
            size: target_size,
            component: target_component,
        },
        ObjectGeometryOperation::SetAnchor {
            anchor: target_anchor,
        },
        ObjectGeometryOperation::SetWrap {
            wrap: target_wrap,
            outer_margins: target_margins,
        },
        ObjectGeometryOperation::SetRotation {
            rotation: target_rotation,
            transform: transform(),
        },
        ObjectGeometryOperation::SetFlip {
            flip: target_flip,
            transform: transform(),
        },
    ];
    let expected_capabilities = [
        "obj.position",
        "obj.size",
        "obj.anchor",
        "obj.wrap",
        "obj.rotate",
        "obj.flip",
    ];
    for (operation, capability) in operations.into_iter().zip(expected_capabilities) {
        let request = request(&source, operation);
        let first =
            ObjectGeometryBuilder::plan(&source, &request, FLOW_A, limits()).expect("first plan");
        let second =
            ObjectGeometryBuilder::plan(&source, &request, FLOW_A, limits()).expect("second plan");
        assert_eq!(first.plan_sha256(), second.plan_sha256());
        assert_eq!(first.capability_id(), capability);
        let result =
            ObjectGeometryBuilder::build(&first, &source, FLOW_A, limits()).expect("exact build");
        assert_eq!(result.state, *first.target_state());
        assert_eq!(result.state.object_id(), source.object_id());
        assert_eq!(result.state.object_kind(), source.object_kind());
        assert_eq!(result.state.native_object_id(), source.native_object_id());
        assert_eq!(
            result.state.native_instance_id(),
            source.native_instance_id()
        );
    }
}

#[test]
fn round_trips_all_admitted_object_kinds_and_preserves_complete_state() {
    let kinds = [
        ObjectKind::Picture,
        ObjectKind::Rectangle,
        ObjectKind::Ellipse,
        ObjectKind::Line,
        ObjectKind::Arc,
        ObjectKind::Polygon,
        ObjectKind::Curve,
        ObjectKind::ConnectLine,
        ObjectKind::Container,
        ObjectKind::Ole,
        ObjectKind::Video,
        ObjectKind::TextArt,
    ];
    for kind in kinds {
        let source = state(kind);
        let json = source.canonical_json(limits()).expect("canonical JSON");
        let reopened = ObjectGeometryState::from_json(&json, limits()).expect("reopen");
        assert_eq!(reopened, source);
        assert_eq!(reopened.z_order(), 3);
        assert_eq!(reopened.numbering_type(), ObjectNumberingType::Picture);
        assert!(!reopened.locked());
        assert_eq!(reopened.anchor(), source.anchor());
        assert_eq!(reopened.position(), source.position());
        assert_eq!(reopened.wrap(), source.wrap());
        assert_eq!(reopened.outer_margins(), source.outer_margins());
        assert_eq!(reopened.component(), source.component());
    }
}

#[test]
fn boundary_values_are_exact_and_over_bound_values_fail_closed() {
    let boundary_limits = ObjectGeometryLimits::new(ObjectGeometryLimitConfig {
        extent_hwpunit: 100,
        matrix_coefficient_millionths: 200,
        ..ObjectGeometryLimitConfig::default()
    })
    .expect("boundary limits");
    let mut draft: ObjectGeometryStateDraft = serde_json::from_slice(
        &state(ObjectKind::Picture)
            .canonical_json(limits())
            .expect("JSON"),
    )
    .expect("draft");
    draft.size.width_hwpunit = 100;
    draft.size.height_hwpunit = 100;
    draft.position.horizontal_offset_hwpunit = 100;
    draft.position.vertical_offset_hwpunit = 100;
    draft.outer_margins = ObjectOuterMargins {
        left_hwpunit: 100,
        right_hwpunit: 100,
        top_hwpunit: 100,
        bottom_hwpunit: 100,
    };
    draft.component.offset = ObjectPoint {
        x_hwpunit: 100,
        y_hwpunit: 100,
    };
    draft.component.original_size = ObjectExtent {
        width_hwpunit: 100,
        height_hwpunit: 100,
    };
    draft.component.current_size = draft.component.original_size;
    draft.component.rotation.center_x_hwpunit = 100;
    draft.component.rotation.center_y_hwpunit = 100;
    draft.component.rotation.angle_degrees = i32::MAX;
    let matrix = ObjectAffineMatrix {
        e1_millionths: 200,
        e2_millionths: -200,
        e3_millionths: 200,
        e4_millionths: -200,
        e5_millionths: 200,
        e6_millionths: -200,
    };
    draft.component.transform = ObjectTransform {
        translation: matrix,
        scale: matrix,
        rotation: matrix,
    };
    ObjectGeometryState::from_draft(draft.clone(), boundary_limits).expect("inclusive boundary");
    draft.size.width_hwpunit = 101;
    assert_eq!(
        ObjectGeometryState::from_draft(draft, boundary_limits),
        Err(ObjectGeometryError::InvalidExtent)
    );
}

#[test]
fn rejects_duplicate_unknown_oversized_and_noncanonical_digest_json() {
    let source = state(ObjectKind::Picture);
    let json = String::from_utf8(source.canonical_json(limits()).expect("JSON")).expect("UTF-8");
    let duplicate = json.replacen(
        "\"schema_version\":",
        "\"schema_version\":\"hwpx-agent.object-geometry/v1\",\"schema_version\":",
        1,
    );
    assert_eq!(
        ObjectGeometryState::from_json(duplicate.as_bytes(), limits()),
        Err(ObjectGeometryError::InvalidJson)
    );
    let unknown = json.replacen('{', "{\"unexpected\":1,", 1);
    assert_eq!(
        ObjectGeometryState::from_json(unknown.as_bytes(), limits()),
        Err(ObjectGeometryError::InvalidJson)
    );
    assert_eq!(
        ObjectGeometryState::from_json(&vec![b' '; limits().config().input_bytes + 1], limits()),
        Err(ObjectGeometryError::InputLimit)
    );
    assert_eq!(
        ObjectGeometryRequest::from_draft(
            ObjectGeometryRequestDraft {
                schema_version: OBJECT_GEOMETRY_SCHEMA_VERSION.to_owned(),
                request_id: LogicalId::parse("bad-request").expect("id"),
                expected_source_state_sha256: "ABC".to_owned(),
                expected_document_flow_sha256: FLOW_A.to_owned(),
                target_document_flow_sha256: FLOW_B.to_owned(),
                operation: ObjectGeometryOperation::SetPosition {
                    position: source.position(),
                },
            },
            &source,
            FLOW_A,
            limits(),
        ),
        Err(ObjectGeometryError::InvalidDigest)
    );
}

#[test]
fn request_and_build_both_reject_state_and_flow_drift() {
    let source = state(ObjectKind::Picture);
    let operation = ObjectGeometryOperation::SetPosition {
        position: ObjectPosition {
            horizontal_offset_hwpunit: 4_000,
            ..source.position()
        },
    };
    let stale = state(ObjectKind::Rectangle);
    assert_eq!(
        ObjectGeometryRequest::from_draft(
            ObjectGeometryRequestDraft {
                schema_version: OBJECT_GEOMETRY_SCHEMA_VERSION.to_owned(),
                request_id: LogicalId::parse("request-drift").expect("id"),
                expected_source_state_sha256: stale.canonical_sha256(limits()).expect("digest"),
                expected_document_flow_sha256: FLOW_A.to_owned(),
                target_document_flow_sha256: FLOW_B.to_owned(),
                operation,
            },
            &source,
            FLOW_A,
            limits(),
        ),
        Err(ObjectGeometryError::SourceStateDrift)
    );
    let request = request(&source, operation);
    assert_eq!(
        ObjectGeometryBuilder::plan(&source, &request, FLOW_B, limits()),
        Err(ObjectGeometryError::DocumentFlowDrift)
    );
    let plan = ObjectGeometryBuilder::plan(&source, &request, FLOW_A, limits()).expect("plan");
    assert_eq!(
        ObjectGeometryBuilder::build(&plan, &stale, FLOW_A, limits()),
        Err(ObjectGeometryError::SourceStateDrift)
    );
    assert_eq!(
        ObjectGeometryBuilder::build(&plan, &source, FLOW_B, limits()),
        Err(ObjectGeometryError::DocumentFlowDrift)
    );
}

#[test]
fn debug_output_redacts_identity_geometry_and_digests() {
    let source = state(ObjectKind::Picture);
    let request = request(
        &source,
        ObjectGeometryOperation::SetPosition {
            position: source.position(),
        },
    );
    let plan = ObjectGeometryBuilder::plan(&source, &request, FLOW_A, limits()).expect("plan");
    let result = ObjectGeometryBuilder::build(&plan, &source, FLOW_A, limits()).expect("build");
    for debug in [
        format!("{source:?}"),
        format!("{request:?}"),
        format!("{plan:?}"),
        format!("{:?}", result.receipt),
    ] {
        assert!(debug.contains("<redacted>"));
        assert!(!debug.contains("shape-1"));
        assert!(!debug.contains(FLOW_A));
    }
}
