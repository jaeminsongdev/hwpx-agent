#![allow(clippy::expect_used)] // Test fixtures use expectations to keep failures local.

use domain_ir::{
    ActiveContentPolicy, CanvasBindings, CanvasBounds, CanvasIdentityReservation, CanvasNode,
    CanvasNodeKind, CanvasPictureState, CanvasResource, CanvasResourceKind,
    DRAWING_CANVAS_SCHEMA_VERSION, DrawingCanvasBuilder, DrawingCanvasError,
    DrawingCanvasLimitConfig, DrawingCanvasLimits, DrawingCanvasOperation, DrawingCanvasRequest,
    DrawingCanvasRequestDraft, DrawingCanvasState, DrawingCanvasStateDraft, EffectScalar,
    ImageClip, LogicalId, PictureEffects, SoftEdgeEffect,
};

fn id(value: &str) -> LogicalId {
    LogicalId::parse(value).expect("fixture ID")
}

fn sha(value: u8) -> String {
    format!("{value:02x}").repeat(32)
}

fn limits() -> DrawingCanvasLimits {
    DrawingCanvasLimits::new(DrawingCanvasLimitConfig::default()).expect("limits")
}

fn bindings(seed: u8) -> CanvasBindings {
    CanvasBindings {
        geometry_sha256: sha(seed),
        payload_sha256: sha(seed.saturating_add(1)),
        appearance_sha256: sha(seed.saturating_add(2)),
        composition_sha256: sha(seed.saturating_add(3)),
        opaque_sha256: sha(seed.saturating_add(4)),
        opaque_byte_length: 17,
    }
}

fn bounds(offset: i64) -> CanvasBounds {
    CanvasBounds {
        x_hwpunit: offset,
        y_hwpunit: offset,
        width_hwpunit: 1_000,
        height_hwpunit: 800,
    }
}

fn image_resource(name: &str, relationship: u32, seed: u8) -> CanvasResource {
    CanvasResource {
        resource_id: id(name),
        relationship_id: format!("rId{relationship}"),
        kind: CanvasResourceKind::EmbeddedImage,
        media_type: "image/png".to_owned(),
        content_sha256: sha(seed),
        byte_length: 128,
        external_target_sha256: None,
        active_content_policy: None,
    }
}

fn base_draft() -> DrawingCanvasStateDraft {
    DrawingCanvasStateDraft {
        schema_version: DRAWING_CANVAS_SCHEMA_VERSION.to_owned(),
        document_id: id("document-private"),
        nodes: vec![
            CanvasNode {
                node_id: id("canvas-1"),
                native_object_id: 1,
                native_instance_id: 101,
                kind: CanvasNodeKind::Container,
                parent_id: None,
                ordinal: 0,
                group_level: 0,
                bounds: bounds(0),
                visible: true,
                printable: true,
                protected: false,
                bindings: bindings(10),
                resource_refs: Vec::new(),
                picture: None,
            },
            CanvasNode {
                node_id: id("picture-1"),
                native_object_id: 2,
                native_instance_id: 102,
                kind: CanvasNodeKind::Picture,
                parent_id: Some(id("canvas-1")),
                ordinal: 0,
                group_level: 1,
                bounds: bounds(10),
                visible: true,
                printable: true,
                protected: false,
                bindings: bindings(20),
                resource_refs: vec![id("image-1")],
                picture: Some(CanvasPictureState {
                    image_resource_id: id("image-1"),
                    original_width_px: 640,
                    original_height_px: 480,
                    clip: None,
                    effects: None,
                }),
            },
            CanvasNode {
                node_id: id("shape-1"),
                native_object_id: 3,
                native_instance_id: 103,
                kind: CanvasNodeKind::Rectangle,
                parent_id: Some(id("canvas-1")),
                ordinal: 1,
                group_level: 1,
                bounds: bounds(20),
                visible: true,
                printable: false,
                protected: true,
                bindings: bindings(30),
                resource_refs: Vec::new(),
                picture: None,
            },
        ],
        resources: vec![image_resource("image-1", 1, 40)],
        opaque_document_state_sha256: sha(50),
    }
}

fn inserted_nodes() -> [CanvasNode; 4] {
    [
        CanvasNode {
            node_id: id("canvas-2"),
            native_object_id: 10,
            native_instance_id: 110,
            kind: CanvasNodeKind::Container,
            parent_id: None,
            ordinal: 1,
            group_level: 0,
            bounds: bounds(100),
            visible: true,
            printable: true,
            protected: false,
            bindings: bindings(60),
            resource_refs: Vec::new(),
            picture: None,
        },
        CanvasNode {
            node_id: id("nested"),
            native_object_id: 11,
            native_instance_id: 111,
            kind: CanvasNodeKind::Container,
            parent_id: Some(id("canvas-2")),
            ordinal: 0,
            group_level: 1,
            bounds: bounds(110),
            visible: true,
            printable: true,
            protected: false,
            bindings: bindings(70),
            resource_refs: Vec::new(),
            picture: None,
        },
        CanvasNode {
            node_id: id("ole"),
            native_object_id: 12,
            native_instance_id: 112,
            kind: CanvasNodeKind::OpaqueOle,
            parent_id: Some(id("canvas-2")),
            ordinal: 1,
            group_level: 1,
            bounds: bounds(120),
            visible: true,
            printable: true,
            protected: true,
            bindings: bindings(80),
            resource_refs: vec![id("ole-bin"), id("ole-preview")],
            picture: None,
        },
        CanvasNode {
            node_id: id("picture-2"),
            native_object_id: 13,
            native_instance_id: 113,
            kind: CanvasNodeKind::Picture,
            parent_id: Some(id("nested")),
            ordinal: 0,
            group_level: 2,
            bounds: bounds(130),
            visible: true,
            printable: true,
            protected: false,
            bindings: bindings(90),
            resource_refs: vec![id("image-2")],
            picture: Some(CanvasPictureState {
                image_resource_id: id("image-2"),
                original_width_px: 800,
                original_height_px: 600,
                clip: Some(ImageClip {
                    left_px: 10,
                    right_px: 790,
                    top_px: 20,
                    bottom_px: 580,
                }),
                effects: Some(PictureEffects {
                    soft_edge: Some(SoftEdgeEffect {
                        radius: EffectScalar(25_000),
                    }),
                    ..PictureEffects::default()
                }),
            }),
        },
    ]
}

fn inserted_resources() -> [CanvasResource; 3] {
    [
        image_resource("image-2", 2, 100),
        CanvasResource {
            resource_id: id("ole-bin"),
            relationship_id: "rId3".to_owned(),
            kind: CanvasResourceKind::OpaqueOle,
            media_type: "application/x-ole-storage".to_owned(),
            content_sha256: sha(101),
            byte_length: 256,
            external_target_sha256: None,
            active_content_policy: Some(ActiveContentPolicy::Blocked),
        },
        CanvasResource {
            resource_id: id("ole-preview"),
            relationship_id: "rId4".to_owned(),
            kind: CanvasResourceKind::Preview,
            media_type: "image/png".to_owned(),
            content_sha256: sha(102),
            byte_length: 64,
            external_target_sha256: None,
            active_content_policy: None,
        },
    ]
}

fn inserted_draft() -> DrawingCanvasStateDraft {
    let mut draft = base_draft();
    draft.nodes.extend(inserted_nodes());
    draft.resources.extend(inserted_resources());
    draft
}

fn state(draft: DrawingCanvasStateDraft) -> DrawingCanvasState {
    DrawingCanvasState::from_draft(draft, limits()).expect("state")
}

fn request(
    source: DrawingCanvasStateDraft,
    target: DrawingCanvasStateDraft,
    operation: DrawingCanvasOperation,
    before_flow: String,
    after_flow: String,
) -> DrawingCanvasRequest {
    let source_state = state(source.clone());
    DrawingCanvasRequest::from_draft(
        DrawingCanvasRequestDraft {
            schema_version: DRAWING_CANVAS_SCHEMA_VERSION.to_owned(),
            request_id: "request-private".to_owned(),
            source,
            target,
            operation,
            source_state_sha256: source_state.state_sha256(limits()).expect("source digest"),
            before_document_flow_sha256: before_flow,
            after_document_flow_sha256: after_flow,
        },
        limits(),
    )
    .expect("request")
}

#[test]
fn canonicalizes_complete_tree_and_resource_inventory() {
    let state = state(inserted_draft());
    assert_eq!(state.nodes().len(), 7);
    assert_eq!(state.resources().len(), 4);
    assert!(state.node(&id("ole")).is_some());
    assert_eq!(
        state
            .resource(&id("ole-bin"))
            .expect("OLE")
            .active_content_policy,
        Some(ActiveContentPolicy::Blocked)
    );
    let json = state.to_canonical_json(limits()).expect("JSON");
    assert_eq!(
        state,
        DrawingCanvasState::from_json(&json, limits()).expect("roundtrip")
    );
}

#[test]
fn inserts_one_complete_reserved_canvas_and_preserves_existing_state() {
    let source_draft = base_draft();
    let target_draft = inserted_draft();
    let source = state(source_draft.clone());
    let request = request(
        source_draft,
        target_draft,
        DrawingCanvasOperation::InsertCanvas {
            root_canvas_id: id("canvas-2"),
            reservation: CanvasIdentityReservation {
                node_ids: vec![id("canvas-2"), id("nested"), id("ole"), id("picture-2")],
                native_object_ids: vec![10, 11, 12, 13],
                native_instance_ids: vec![110, 111, 112, 113],
                resource_ids: vec![id("image-2"), id("ole-bin"), id("ole-preview")],
                allocator_proof_sha256: sha(110),
            },
        },
        sha(111),
        sha(112),
    );
    let builder = DrawingCanvasBuilder;
    let plan = builder
        .plan(request, &source, &sha(111), limits())
        .expect("plan");
    let result = builder
        .build(&plan, &source, &sha(111), limits())
        .expect("build");
    assert_eq!(result.receipt.capability_id(), "obj.drawing_object_insert");
    for original in source.nodes() {
        assert_eq!(result.target.node(&original.node_id), Some(original));
    }
    assert_eq!(
        result.target.state_sha256(limits()).expect("digest"),
        result.receipt.target_state_sha256()
    );
}

#[test]
fn changes_only_clip_and_payload_binding() {
    let source_draft = base_draft();
    let mut target_draft = source_draft.clone();
    let picture = target_draft
        .nodes
        .iter_mut()
        .find(|node| node.node_id == id("picture-1"))
        .expect("picture");
    picture.picture.as_mut().expect("image").clip = Some(ImageClip {
        left_px: 1,
        right_px: 639,
        top_px: 2,
        bottom_px: 479,
    });
    picture.bindings.payload_sha256 = sha(120);
    let source = state(source_draft.clone());
    let request = request(
        source_draft,
        target_draft,
        DrawingCanvasOperation::SetPictureClip {
            picture_id: id("picture-1"),
        },
        sha(121),
        sha(121),
    );
    let result = DrawingCanvasBuilder
        .build(
            &DrawingCanvasBuilder
                .plan(request, &source, &sha(121), limits())
                .expect("plan"),
            &source,
            &sha(121),
            limits(),
        )
        .expect("build");
    assert_eq!(result.receipt.capability_id(), "obj.crop");
    assert_eq!(
        result.target.node(&id("shape-1")),
        source.node(&id("shape-1"))
    );
    assert_eq!(result.target.resources(), source.resources());
}

#[test]
fn changes_only_effects_and_appearance_binding() {
    let source_draft = base_draft();
    let mut target_draft = source_draft.clone();
    let picture = target_draft
        .nodes
        .iter_mut()
        .find(|node| node.node_id == id("picture-1"))
        .expect("picture");
    picture.picture.as_mut().expect("image").effects = Some(PictureEffects {
        soft_edge: Some(SoftEdgeEffect {
            radius: EffectScalar(50_000),
        }),
        ..PictureEffects::default()
    });
    picture.bindings.appearance_sha256 = sha(122);
    let source = state(source_draft.clone());
    let request = request(
        source_draft,
        target_draft,
        DrawingCanvasOperation::SetPictureEffects {
            picture_id: id("picture-1"),
        },
        sha(123),
        sha(123),
    );
    let plan = DrawingCanvasBuilder
        .plan(request, &source, &sha(123), limits())
        .expect("plan");
    let result = DrawingCanvasBuilder
        .build(&plan, &source, &sha(123), limits())
        .expect("build");
    assert_eq!(result.receipt.capability_id(), "obj.picture_effects");
    assert_eq!(
        result.target.node(&id("shape-1")),
        source.node(&id("shape-1"))
    );
}

#[test]
fn rejects_topology_identity_and_resource_closure_failures() {
    let mut cycle = base_draft();
    cycle.nodes[0].parent_id = Some(id("canvas-1"));
    assert_eq!(
        DrawingCanvasState::from_draft(cycle, limits()),
        Err(DrawingCanvasError::InvalidTopology)
    );

    let mut duplicate = base_draft();
    duplicate.nodes[1].native_object_id = duplicate.nodes[0].native_object_id;
    assert_eq!(
        DrawingCanvasState::from_draft(duplicate, limits()),
        Err(DrawingCanvasError::DuplicateIdentity)
    );

    let mut dangling = base_draft();
    dangling.nodes[1].resource_refs = vec![id("missing")];
    assert_eq!(
        DrawingCanvasState::from_draft(dangling, limits()),
        Err(DrawingCanvasError::InvalidResourceClosure)
    );

    let mut duplicate_ordinal = base_draft();
    duplicate_ordinal.nodes[2].ordinal = 0;
    assert_eq!(
        DrawingCanvasState::from_draft(duplicate_ordinal, limits()),
        Err(DrawingCanvasError::InvalidTopology)
    );

    let mut empty_relationship_number = base_draft();
    empty_relationship_number.resources[0].relationship_id = "rId".to_owned();
    assert_eq!(
        DrawingCanvasState::from_draft(empty_relationship_number, limits()),
        Err(DrawingCanvasError::InvalidResource)
    );
}

#[test]
fn rejects_invalid_clip_effects_and_unblocked_ole() {
    let mut clip = base_draft();
    clip.nodes[1].picture.as_mut().expect("picture").clip = Some(ImageClip {
        left_px: 100,
        right_px: 100,
        top_px: 0,
        bottom_px: 480,
    });
    assert_eq!(
        DrawingCanvasState::from_draft(clip, limits()),
        Err(DrawingCanvasError::InvalidClip)
    );

    let mut effects = base_draft();
    effects.nodes[1].picture.as_mut().expect("picture").effects = Some(PictureEffects::default());
    assert_eq!(
        DrawingCanvasState::from_draft(effects, limits()),
        Err(DrawingCanvasError::InvalidEffects)
    );

    let mut ole = inserted_draft();
    ole.resources
        .iter_mut()
        .find(|resource| resource.resource_id == id("ole-bin"))
        .expect("OLE")
        .active_content_policy = None;
    assert_eq!(
        DrawingCanvasState::from_draft(ole, limits()),
        Err(DrawingCanvasError::ActiveContentNotBlocked)
    );
}

#[test]
fn rejects_noop_untargeted_mutation_bad_reservation_and_flow_changes() {
    let source_draft = base_draft();
    let source = state(source_draft.clone());
    let noop = DrawingCanvasRequest::from_draft(
        DrawingCanvasRequestDraft {
            schema_version: DRAWING_CANVAS_SCHEMA_VERSION.to_owned(),
            request_id: "noop".to_owned(),
            source: source_draft.clone(),
            target: source_draft.clone(),
            operation: DrawingCanvasOperation::SetPictureClip {
                picture_id: id("picture-1"),
            },
            source_state_sha256: source.state_sha256(limits()).expect("digest"),
            before_document_flow_sha256: sha(130),
            after_document_flow_sha256: sha(130),
        },
        limits(),
    );
    assert_eq!(noop, Err(DrawingCanvasError::NoOp));

    let mut mutated = source_draft.clone();
    mutated.nodes[2].printable = true;
    mutated.nodes[1].picture.as_mut().expect("picture").clip = Some(ImageClip {
        left_px: 1,
        right_px: 639,
        top_px: 1,
        bottom_px: 479,
    });
    mutated.nodes[1].bindings.payload_sha256 = sha(131);
    let bad = DrawingCanvasRequest::from_draft(
        DrawingCanvasRequestDraft {
            schema_version: DRAWING_CANVAS_SCHEMA_VERSION.to_owned(),
            request_id: "mutated".to_owned(),
            source: source_draft.clone(),
            target: mutated,
            operation: DrawingCanvasOperation::SetPictureClip {
                picture_id: id("picture-1"),
            },
            source_state_sha256: source.state_sha256(limits()).expect("digest"),
            before_document_flow_sha256: sha(132),
            after_document_flow_sha256: sha(132),
        },
        limits(),
    );
    assert_eq!(bad, Err(DrawingCanvasError::PreservationViolation));

    let flow = DrawingCanvasRequest::from_draft(
        DrawingCanvasRequestDraft {
            schema_version: DRAWING_CANVAS_SCHEMA_VERSION.to_owned(),
            request_id: "flow".to_owned(),
            source: source_draft.clone(),
            target: {
                let mut target = source_draft.clone();
                target.nodes[1].picture.as_mut().expect("picture").clip = Some(ImageClip {
                    left_px: 1,
                    right_px: 639,
                    top_px: 1,
                    bottom_px: 479,
                });
                target.nodes[1].bindings.payload_sha256 = sha(133);
                target
            },
            operation: DrawingCanvasOperation::SetPictureClip {
                picture_id: id("picture-1"),
            },
            source_state_sha256: source.state_sha256(limits()).expect("digest"),
            before_document_flow_sha256: sha(134),
            after_document_flow_sha256: sha(135),
        },
        limits(),
    );
    assert_eq!(flow, Err(DrawingCanvasError::DocumentFlowDrift));

    let invalid_reservation = DrawingCanvasRequest::from_draft(
        DrawingCanvasRequestDraft {
            schema_version: DRAWING_CANVAS_SCHEMA_VERSION.to_owned(),
            request_id: "reservation".to_owned(),
            source: source_draft,
            target: inserted_draft(),
            operation: DrawingCanvasOperation::InsertCanvas {
                root_canvas_id: id("canvas-2"),
                reservation: CanvasIdentityReservation {
                    node_ids: vec![id("canvas-2")],
                    native_object_ids: vec![10],
                    native_instance_ids: vec![110],
                    resource_ids: vec![id("image-2")],
                    allocator_proof_sha256: sha(136),
                },
            },
            source_state_sha256: source.state_sha256(limits()).expect("digest"),
            before_document_flow_sha256: sha(137),
            after_document_flow_sha256: sha(138),
        },
        limits(),
    );
    assert_eq!(
        invalid_reservation,
        Err(DrawingCanvasError::InvalidReservation)
    );
}

#[test]
fn rechecks_request_plan_and_build_drift() {
    let source_draft = base_draft();
    let mut target_draft = source_draft.clone();
    target_draft.nodes[1]
        .picture
        .as_mut()
        .expect("picture")
        .clip = Some(ImageClip {
        left_px: 1,
        right_px: 639,
        top_px: 1,
        bottom_px: 479,
    });
    target_draft.nodes[1].bindings.payload_sha256 = sha(140);
    let source = state(source_draft.clone());
    let request = request(
        source_draft,
        target_draft,
        DrawingCanvasOperation::SetPictureClip {
            picture_id: id("picture-1"),
        },
        sha(141),
        sha(141),
    );
    let builder = DrawingCanvasBuilder;
    assert_eq!(
        builder.plan(request.clone(), &source, &sha(142), limits()),
        Err(DrawingCanvasError::DocumentFlowDrift)
    );
    let plan = builder
        .plan(request, &source, &sha(141), limits())
        .expect("plan");
    let drifted = state(inserted_draft());
    assert_eq!(
        builder.build(&plan, &drifted, &sha(141), limits()),
        Err(DrawingCanvasError::SourceStateDrift)
    );
}

#[test]
fn enforces_json_limits_unknown_duplicate_keys_and_redacted_debug() {
    let state = state(base_draft());
    let json = state.to_canonical_json(limits()).expect("JSON");
    let mut unknown: serde_json::Value = serde_json::from_slice(&json).expect("value");
    unknown
        .as_object_mut()
        .expect("object")
        .insert("unknown".to_owned(), serde_json::Value::Bool(true));
    assert_eq!(
        DrawingCanvasState::from_json(
            &serde_json::to_vec(&unknown).expect("unknown JSON"),
            limits()
        ),
        Err(DrawingCanvasError::InvalidJson)
    );
    assert_eq!(
        DrawingCanvasState::from_json(br#"{"schema_version":"a","schema_version":"b"}"#, limits()),
        Err(DrawingCanvasError::DuplicateJsonKey)
    );
    let tiny = DrawingCanvasLimits::new(DrawingCanvasLimitConfig {
        input_bytes: 1,
        output_bytes: 2,
        ..DrawingCanvasLimitConfig::default()
    })
    .expect("tiny limits");
    assert_eq!(
        DrawingCanvasState::from_json(&json, tiny),
        Err(DrawingCanvasError::InputTooLarge)
    );
    let debug = format!("{state:?}");
    assert!(!debug.contains("document-private"));
    assert!(!debug.contains(&sha(50)));
    assert!(debug.contains("<redacted>"));

    let bounds_debug = format!("{:?}", bounds(12_345));
    assert!(!bounds_debug.contains("12345"));
    assert!(bounds_debug.contains("<redacted>"));
    let clip_debug = format!(
        "{:?}",
        ImageClip {
            left_px: 12_346,
            right_px: 12_347,
            top_px: 12_348,
            bottom_px: 12_349,
        }
    );
    assert!(!clip_debug.contains("1234"));
    assert!(clip_debug.contains("<redacted>"));
}
