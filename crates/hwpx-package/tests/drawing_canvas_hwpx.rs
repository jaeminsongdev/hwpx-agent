#![allow(clippy::expect_used)] // Test fixtures keep failures local and readable.

use domain_ir::{
    CanvasBindings, CanvasBounds, CanvasIdentityReservation, CanvasNode, CanvasNodeKind,
    CanvasPictureState, CanvasResource, CanvasResourceKind, DRAWING_CANVAS_SCHEMA_VERSION,
    DrawingCanvasLimitConfig, DrawingCanvasLimits, DrawingCanvasOperation, DrawingCanvasRequest,
    DrawingCanvasRequestDraft, DrawingCanvasState, DrawingCanvasStateDraft, EffectScalar,
    ImageClip, LogicalId, PictureEffects, SoftEdgeEffect,
};
use hwpx_package::{
    DrawingCanvasHwpxBuilder, DrawingCanvasHwpxError, DrawingCanvasHwpxLimitConfig,
    DrawingCanvasHwpxLimits, DrawingCanvasHwpxLowered, DrawingCanvasHwpxLowerer,
    DrawingCanvasHwpxReader,
};

const FLOW_A: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const FLOW_B: &str = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
const EMPTY_SHA: &str = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";
const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const CORE_NS: &str = "http://www.hancom.co.kr/hwpml/2011/core";

fn id(value: &str) -> LogicalId {
    LogicalId::parse(value).expect("ID")
}

fn sha(seed: u8) -> String {
    format!("{seed:02x}").repeat(32)
}

fn state_limits() -> DrawingCanvasLimits {
    DrawingCanvasLimits::new(DrawingCanvasLimitConfig::default()).expect("state limits")
}

fn hwpx_limits() -> DrawingCanvasHwpxLimits {
    DrawingCanvasHwpxLimits::new(DrawingCanvasHwpxLimitConfig::default()).expect("HWPX limits")
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

fn empty_bindings() -> CanvasBindings {
    CanvasBindings {
        geometry_sha256: EMPTY_SHA.to_owned(),
        payload_sha256: EMPTY_SHA.to_owned(),
        appearance_sha256: EMPTY_SHA.to_owned(),
        composition_sha256: EMPTY_SHA.to_owned(),
        opaque_sha256: EMPTY_SHA.to_owned(),
        opaque_byte_length: 0,
    }
}

const fn bounds(x: i64, y: i64, width: u64, height: u64) -> CanvasBounds {
    CanvasBounds {
        x_hwpunit: x,
        y_hwpunit: y,
        width_hwpunit: width,
        height_hwpunit: height,
    }
}

fn common(node: &CanvasNode) -> String {
    format!(
        "<hp:offset x=\"{}\" y=\"{}\"/><hp:orgSz width=\"{}\" height=\"{}\"/><hp:curSz width=\"{}\" height=\"{}\"/><hp:flip horizontal=\"0\" vertical=\"0\"/><hp:rotationInfo angle=\"0\" centerX=\"0\" centerY=\"0\" rotateimage=\"1\"/><hp:renderingInfo><hc:transMatrix e1=\"1\" e2=\"0\" e3=\"0\" e4=\"1\" e5=\"0\" e6=\"0\"/><hc:scaMatrix e1=\"1\" e2=\"0\" e3=\"0\" e4=\"1\" e5=\"0\" e6=\"0\"/><hc:rotMatrix e1=\"1\" e2=\"0\" e3=\"0\" e4=\"1\" e5=\"0\" e6=\"0\"/></hp:renderingInfo><hp:sz width=\"{}\" widthRelTo=\"ABSOLUTE\" height=\"{}\" heightRelTo=\"ABSOLUTE\" protect=\"{}\"/><hp:pos treatAsChar=\"0\" affectLSpacing=\"0\" flowWithText=\"1\" allowOverlap=\"0\" holdAnchorAndSO=\"1\" vertRelTo=\"PARA\" horzRelTo=\"PARA\" vertAlign=\"TOP\" horzAlign=\"LEFT\" vertOffset=\"0\" horzOffset=\"0\"/><hp:outMargin left=\"0\" right=\"0\" top=\"0\" bottom=\"0\"/>",
        node.bounds.x_hwpunit,
        node.bounds.y_hwpunit,
        node.bounds.width_hwpunit,
        node.bounds.height_hwpunit,
        node.bounds.width_hwpunit,
        node.bounds.height_hwpunit,
        node.bounds.width_hwpunit,
        node.bounds.height_hwpunit,
        u8::from(node.protected),
    )
}

fn picture_fragment(node: &CanvasNode) -> String {
    format!(
        "<hp:pic id=\"{}\" zOrder=\"{}\" numberingType=\"PICTURE\" textWrap=\"TOP_AND_BOTTOM\" textFlow=\"BOTH_SIDES\" lock=\"0\" dropcapstyle=\"None\" href=\"\" groupLevel=\"{}\" instid=\"{}\">{}<hp:shapeComment>picture-opaque-marker</hp:shapeComment><hc:img binaryItemIDRef=\"rId1\"/><hp:imgClip left=\"0\" right=\"640\" top=\"0\" bottom=\"480\"/><hp:imgDim dimwidth=\"640\" dimheight=\"480\"/></hp:pic>",
        node.native_object_id,
        node.ordinal,
        node.group_level,
        node.native_instance_id,
        common(node),
    )
}

fn rectangle_fragment(node: &CanvasNode) -> String {
    format!(
        "<hp:rect id=\"{}\" zOrder=\"{}\" numberingType=\"DRAWING\" textWrap=\"TOP_AND_BOTTOM\" textFlow=\"BOTH_SIDES\" lock=\"0\" dropcapstyle=\"None\" href=\"\" groupLevel=\"{}\" instid=\"{}\">{}<hp:shapeComment>rectangle-opaque-marker</hp:shapeComment><hp:pt0 x=\"0\" y=\"0\"/><hp:pt1 x=\"800\" y=\"0\"/><hp:pt2 x=\"800\" y=\"800\"/><hp:pt3 x=\"0\" y=\"800\"/></hp:rect>",
        node.native_object_id,
        node.ordinal,
        node.group_level,
        node.native_instance_id,
        common(node),
    )
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
                bounds: bounds(0, 0, 3_000, 2_000),
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
                bounds: bounds(100, 100, 1_000, 800),
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
                bounds: bounds(1_200, 100, 800, 800),
                visible: true,
                printable: true,
                protected: true,
                bindings: bindings(30),
                resource_refs: Vec::new(),
                picture: None,
            },
        ],
        resources: vec![CanvasResource {
            resource_id: id("image-1"),
            relationship_id: "rId1".to_owned(),
            kind: CanvasResourceKind::EmbeddedImage,
            media_type: "image/png".to_owned(),
            content_sha256: sha(40),
            byte_length: 128,
            external_target_sha256: None,
            active_content_policy: None,
        }],
        opaque_document_state_sha256: sha(50),
    }
}

fn state(draft: DrawingCanvasStateDraft) -> DrawingCanvasState {
    DrawingCanvasState::from_draft(draft, state_limits()).expect("state")
}

fn section(source: &DrawingCanvasState) -> Vec<u8> {
    let root = source.node(&id("canvas-1")).expect("root");
    let picture = source.node(&id("picture-1")).expect("picture");
    let shape = source.node(&id("shape-1")).expect("shape");
    format!(
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?><hp:section xmlns:hp=\"{PARAGRAPH_NS}\" xmlns:hc=\"{CORE_NS}\"><hp:p id=\"1\"><hp:run charPrIDRef=\"1\"><hp:t>outside-before</hp:t><hp:container id=\"{}\" zOrder=\"{}\" numberingType=\"CONTAINER\" textWrap=\"TOP_AND_BOTTOM\" textFlow=\"BOTH_SIDES\" lock=\"0\" dropcapstyle=\"None\" href=\"\" groupLevel=\"{}\" instid=\"{}\">{}<hp:shapeComment>container-opaque-marker</hp:shapeComment>{}{}</hp:container><hp:t>outside-after</hp:t></hp:run></hp:p></hp:section>",
        root.native_object_id,
        root.ordinal,
        root.group_level,
        root.native_instance_id,
        common(root),
        picture_fragment(picture),
        rectangle_fragment(shape),
    )
    .into_bytes()
}

fn request(
    source: DrawingCanvasStateDraft,
    target: DrawingCanvasStateDraft,
    operation: DrawingCanvasOperation,
    after_flow: &str,
) -> DrawingCanvasRequest {
    let source_state = state(source.clone());
    DrawingCanvasRequest::from_draft(
        DrawingCanvasRequestDraft {
            schema_version: DRAWING_CANVAS_SCHEMA_VERSION.to_owned(),
            request_id: "request-private".to_owned(),
            source,
            target,
            operation,
            source_state_sha256: source_state
                .state_sha256(state_limits())
                .expect("source digest"),
            before_document_flow_sha256: FLOW_A.to_owned(),
            after_document_flow_sha256: after_flow.to_owned(),
        },
        state_limits(),
    )
    .expect("request")
}

fn lower(
    xml: &[u8],
    source: &DrawingCanvasState,
    request: &DrawingCanvasRequest,
) -> DrawingCanvasHwpxLowered {
    let plan = DrawingCanvasHwpxBuilder::plan(
        xml,
        0,
        source,
        request,
        FLOW_A,
        state_limits(),
        hwpx_limits(),
    )
    .expect("plan");
    DrawingCanvasHwpxLowerer::lower(&plan, xml, source, FLOW_A, state_limits(), hwpx_limits())
        .expect("lower")
}

#[test]
fn crop_lowers_exact_clip_and_preserves_opaque_and_outside_bytes() {
    let source_draft = base_draft();
    let mut target_draft = source_draft.clone();
    let picture = target_draft
        .nodes
        .iter_mut()
        .find(|node| node.node_id == id("picture-1"))
        .expect("picture");
    picture.picture.as_mut().expect("picture state").clip = Some(ImageClip {
        left_px: 10,
        right_px: 600,
        top_px: 20,
        bottom_px: 460,
    });
    picture.bindings.payload_sha256 = sha(90);
    let source = state(source_draft.clone());
    let request = request(
        source_draft,
        target_draft,
        DrawingCanvasOperation::SetPictureClip {
            picture_id: id("picture-1"),
        },
        FLOW_A,
    );
    let lowered = lower(&section(&source), &source, &request);
    let text = String::from_utf8(lowered.section_xml).expect("UTF-8");
    assert!(text.contains("<hp:imgClip left=\"10\" right=\"600\" top=\"20\" bottom=\"460\"/>"));
    assert!(text.contains("picture-opaque-marker"));
    assert!(text.contains("rectangle-opaque-marker"));
    assert!(text.contains("outside-before"));
    assert!(text.contains("outside-after"));
    assert!(lowered.receipt.semantic_reopen());
    assert!(lowered.receipt.outside_island_preserved());
}

#[test]
fn insert_lowers_one_reserved_container_rectangle_tree_and_reopens() {
    let source_draft = base_draft();
    let mut target_draft = source_draft.clone();
    target_draft.nodes.extend([
        CanvasNode {
            node_id: id("canvas-2"),
            native_object_id: 10,
            native_instance_id: 110,
            kind: CanvasNodeKind::Container,
            parent_id: None,
            ordinal: 1,
            group_level: 0,
            bounds: bounds(4_000, 0, 2_000, 1_500),
            visible: true,
            printable: true,
            protected: false,
            bindings: empty_bindings(),
            resource_refs: Vec::new(),
            picture: None,
        },
        CanvasNode {
            node_id: id("shape-2"),
            native_object_id: 11,
            native_instance_id: 111,
            kind: CanvasNodeKind::Rectangle,
            parent_id: Some(id("canvas-2")),
            ordinal: 0,
            group_level: 1,
            bounds: bounds(100, 100, 500, 400),
            visible: true,
            printable: true,
            protected: false,
            bindings: empty_bindings(),
            resource_refs: Vec::new(),
            picture: None,
        },
    ]);
    let source = state(source_draft.clone());
    let request = request(
        source_draft,
        target_draft,
        DrawingCanvasOperation::InsertCanvas {
            root_canvas_id: id("canvas-2"),
            reservation: CanvasIdentityReservation {
                node_ids: vec![id("canvas-2"), id("shape-2")],
                native_object_ids: vec![10, 11],
                native_instance_ids: vec![110, 111],
                resource_ids: Vec::new(),
                allocator_proof_sha256: sha(91),
            },
        },
        FLOW_B,
    );
    let target = request.target().clone();
    let lowered = lower(&section(&source), &source, &request);
    let text = String::from_utf8(lowered.section_xml.clone()).expect("UTF-8");
    assert!(text.contains("<hp:container id=\"10\" zOrder=\"1\""));
    assert!(text.contains("<hp:rect id=\"11\" zOrder=\"0\""));
    assert!(text.contains("picture-opaque-marker"));
    assert_eq!(lowered.readback.node_count(), 5);
    DrawingCanvasHwpxReader::read(
        &lowered.section_xml,
        &target,
        0,
        state_limits(),
        hwpx_limits(),
    )
    .expect("semantic reopen");
}

#[test]
fn request_and_lowering_recheck_flow_and_source_xml_drift() {
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
    target_draft.nodes[1].bindings.payload_sha256 = sha(92);
    let source = state(source_draft.clone());
    let xml = section(&source);
    let request = request(
        source_draft,
        target_draft,
        DrawingCanvasOperation::SetPictureClip {
            picture_id: id("picture-1"),
        },
        FLOW_A,
    );
    assert!(matches!(
        DrawingCanvasHwpxBuilder::plan(
            &xml,
            0,
            &source,
            &request,
            FLOW_B,
            state_limits(),
            hwpx_limits(),
        ),
        Err(DrawingCanvasHwpxError::DocumentFlowDrift)
    ));
    let plan = DrawingCanvasHwpxBuilder::plan(
        &xml,
        0,
        &source,
        &request,
        FLOW_A,
        state_limits(),
        hwpx_limits(),
    )
    .expect("plan");
    let tampered = String::from_utf8(xml)
        .expect("UTF-8")
        .replace("picture-opaque-marker", "picture-tampered-marker");
    assert!(matches!(
        DrawingCanvasHwpxLowerer::lower(
            &plan,
            tampered.as_bytes(),
            &source,
            FLOW_A,
            state_limits(),
            hwpx_limits(),
        ),
        Err(DrawingCanvasHwpxError::SourceStateDrift)
    ));
}

#[test]
fn native_identity_geometry_and_resource_tampering_fail_closed() {
    let source = state(base_draft());
    let xml = String::from_utf8(section(&source)).expect("UTF-8");
    for tampered in [
        xml.replace("id=\"2\" zOrder=\"0\"", "id=\"20\" zOrder=\"0\""),
        xml.replace(
            "<hp:offset x=\"100\" y=\"100\"/>",
            "<hp:offset x=\"101\" y=\"100\"/>",
        ),
        xml.replace("binaryItemIDRef=\"rId1\"", "binaryItemIDRef=\"rId9\""),
    ] {
        assert!(matches!(
            DrawingCanvasHwpxReader::read(
                tampered.as_bytes(),
                &source,
                0,
                state_limits(),
                hwpx_limits(),
            ),
            Err(DrawingCanvasHwpxError::UnsupportedProfile)
        ));
    }
}

#[test]
fn unrepresented_visibility_and_nonempty_generated_payload_are_rejected() {
    let mut invisible = base_draft();
    invisible.nodes[2].visible = false;
    let invisible_state = state(invisible);
    assert!(matches!(
        DrawingCanvasHwpxReader::read(
            &section(&state(base_draft())),
            &invisible_state,
            0,
            state_limits(),
            hwpx_limits(),
        ),
        Err(DrawingCanvasHwpxError::UnsupportedProfile)
    ));

    let source_draft = base_draft();
    let mut target_draft = source_draft.clone();
    target_draft.nodes.extend([
        CanvasNode {
            node_id: id("canvas-2"),
            native_object_id: 10,
            native_instance_id: 110,
            kind: CanvasNodeKind::Container,
            parent_id: None,
            ordinal: 1,
            group_level: 0,
            bounds: bounds(4_000, 0, 2_000, 1_500),
            visible: true,
            printable: true,
            protected: false,
            bindings: bindings(60),
            resource_refs: Vec::new(),
            picture: None,
        },
        CanvasNode {
            node_id: id("shape-2"),
            native_object_id: 11,
            native_instance_id: 111,
            kind: CanvasNodeKind::Rectangle,
            parent_id: Some(id("canvas-2")),
            ordinal: 0,
            group_level: 1,
            bounds: bounds(100, 100, 500, 400),
            visible: true,
            printable: true,
            protected: false,
            bindings: empty_bindings(),
            resource_refs: Vec::new(),
            picture: None,
        },
    ]);
    let source = state(source_draft.clone());
    let insert = request(
        source_draft.clone(),
        target_draft,
        DrawingCanvasOperation::InsertCanvas {
            root_canvas_id: id("canvas-2"),
            reservation: CanvasIdentityReservation {
                node_ids: vec![id("canvas-2"), id("shape-2")],
                native_object_ids: vec![10, 11],
                native_instance_ids: vec![110, 111],
                resource_ids: Vec::new(),
                allocator_proof_sha256: sha(93),
            },
        },
        FLOW_B,
    );
    assert!(matches!(
        DrawingCanvasHwpxBuilder::plan(
            &section(&source),
            0,
            &source,
            &insert,
            FLOW_A,
            state_limits(),
            hwpx_limits(),
        ),
        Err(DrawingCanvasHwpxError::UnsupportedProfile)
    ));
}

#[test]
fn picture_effects_are_explicitly_rejected_by_the_static_profile() {
    let source_draft = base_draft();
    let source = state(source_draft.clone());
    let mut effects_target = source_draft.clone();
    effects_target.nodes[1]
        .picture
        .as_mut()
        .expect("picture")
        .effects = Some(PictureEffects {
        soft_edge: Some(SoftEdgeEffect {
            radius: EffectScalar(25_000),
        }),
        ..PictureEffects::default()
    });
    effects_target.nodes[1].bindings.appearance_sha256 = sha(94);
    let effects = request(
        source_draft,
        effects_target,
        DrawingCanvasOperation::SetPictureEffects {
            picture_id: id("picture-1"),
        },
        FLOW_A,
    );
    assert!(matches!(
        DrawingCanvasHwpxBuilder::plan(
            &section(&source),
            0,
            &source,
            &effects,
            FLOW_A,
            state_limits(),
            hwpx_limits(),
        ),
        Err(DrawingCanvasHwpxError::UnsupportedProfile)
    ));
}

#[test]
fn output_is_bounded_and_debug_does_not_expose_digest_material() {
    let source = state(base_draft());
    let readback =
        DrawingCanvasHwpxReader::read(&section(&source), &source, 0, state_limits(), hwpx_limits())
            .expect("readback");
    let debug = format!("{readback:?}");
    assert!(debug.contains("<redacted>"));
    assert!(!debug.contains(&sha(50)));

    let tiny = DrawingCanvasHwpxLimits::new(DrawingCanvasHwpxLimitConfig {
        section_bytes: 1,
        output_bytes: 1,
        elements: 1,
        nodes: 1,
    })
    .expect("tiny limits");
    assert!(matches!(
        DrawingCanvasHwpxReader::read(&section(&source), &source, 0, state_limits(), tiny,),
        Err(DrawingCanvasHwpxError::InputLimit)
    ));
}
