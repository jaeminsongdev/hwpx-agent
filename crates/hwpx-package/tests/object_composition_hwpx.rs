#![allow(clippy::expect_used)] // Test fixtures keep failures local and readable.

use domain_ir::{
    CompositionAxis, CompositionBounds, CompositionObject, CompositionObjectContent,
    CompositionObjectKind, ConnectorControlPoint, ConnectorEndpoint, ConnectorKind,
    ConnectorSubject, ConnectorTopology, LogicalId, NewConnector, NewGroup,
    OBJECT_COMPOSITION_SCHEMA_VERSION, ObjectAlignMode, ObjectCompositionBuilder,
    ObjectCompositionGraph, ObjectCompositionGraphDraft, ObjectCompositionLimitConfig,
    ObjectCompositionLimits, ObjectCompositionOperation, ObjectCompositionRequest,
    ObjectCompositionRequestDraft, ZOrderMove,
};
use hwpx_package::{
    ObjectCompositionHwpxBuilder, ObjectCompositionHwpxError, ObjectCompositionHwpxLimitConfig,
    ObjectCompositionHwpxLimits, ObjectCompositionHwpxLowered, ObjectCompositionHwpxLowerer,
    ObjectCompositionHwpxReader,
};

const FLOW_A: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const FLOW_B: &str = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
const EMPTY_SHA: &str = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";
const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const CORE_NS: &str = "http://www.hancom.co.kr/hwpml/2011/core";

fn graph_limits() -> ObjectCompositionLimits {
    ObjectCompositionLimits::new(ObjectCompositionLimitConfig::default()).expect("graph limits")
}

fn hwpx_limits() -> ObjectCompositionHwpxLimits {
    ObjectCompositionHwpxLimits::new(ObjectCompositionHwpxLimitConfig::default())
        .expect("HWPX limits")
}

fn id(value: &str) -> LogicalId {
    LogicalId::parse(value).expect("id")
}

fn content(seed: u32) -> CompositionObjectContent {
    CompositionObjectContent {
        state_sha256: format!("{seed:064x}"),
        byte_length: u64::from(seed) + 1,
        resource_refs: Vec::new(),
    }
}

fn empty_content() -> CompositionObjectContent {
    CompositionObjectContent {
        state_sha256: EMPTY_SHA.to_owned(),
        byte_length: 0,
        resource_refs: Vec::new(),
    }
}

fn shape(name: &str, native: u32, z: u32, x: i64, y: i64) -> CompositionObject {
    CompositionObject {
        object_id: id(name),
        native_object_id: native,
        native_instance_id: native + 100,
        kind: CompositionObjectKind::BasicShape,
        parent_group_id: None,
        z_order: z,
        group_level: 0,
        bounds: CompositionBounds {
            x_hwpunit: x,
            y_hwpunit: y,
            width_hwpunit: 100,
            height_hwpunit: 80,
        },
        visible: true,
        printable: true,
        content: content(native),
        connector: None,
    }
}

fn graph(objects: Vec<CompositionObject>) -> ObjectCompositionGraph {
    ObjectCompositionGraph::from_draft(
        ObjectCompositionGraphDraft {
            schema_version: OBJECT_COMPOSITION_SCHEMA_VERSION.to_owned(),
            objects,
        },
        graph_limits(),
    )
    .expect("graph")
}

fn standard() -> ObjectCompositionGraph {
    graph(vec![
        shape("a", 1, 0, 0, 0),
        shape("b", 2, 1, 200, 100),
        shape("c", 3, 2, 500, 300),
        shape("d", 4, 3, 900, 600),
    ])
}

fn rect(object: &CompositionObject) -> String {
    format!(
        "<hp:rect id=\"{}\" zOrder=\"{}\" numberingType=\"DRAWING\" textWrap=\"TOP_AND_BOTTOM\" textFlow=\"BOTH_SIDES\" lock=\"0\" dropcapstyle=\"None\" href=\"\" groupLevel=\"{}\" instid=\"{}\"><hp:offset x=\"{}\" y=\"{}\"/><hp:orgSz width=\"{}\" height=\"{}\"/><hp:curSz width=\"{}\" height=\"{}\"/><hp:flip horizontal=\"0\" vertical=\"0\"/><hp:rotationInfo angle=\"0\" centerX=\"50\" centerY=\"40\" rotateimage=\"1\"/><hp:renderingInfo><hc:transMatrix e1=\"1\" e2=\"0\" e3=\"0\" e4=\"1\" e5=\"0\" e6=\"0\"/><hc:scaMatrix e1=\"1\" e2=\"0\" e3=\"0\" e4=\"1\" e5=\"0\" e6=\"0\"/><hc:rotMatrix e1=\"1\" e2=\"0\" e3=\"0\" e4=\"1\" e5=\"0\" e6=\"0\"/></hp:renderingInfo><hp:shapeComment>opaque-{}</hp:shapeComment><hp:sz width=\"{}\" widthRelTo=\"ABSOLUTE\" height=\"{}\" heightRelTo=\"ABSOLUTE\" protect=\"0\"/><hp:pos treatAsChar=\"0\" affectLSpacing=\"0\" flowWithText=\"1\" allowOverlap=\"0\" holdAnchorAndSO=\"1\" vertRelTo=\"PARA\" horzRelTo=\"PARA\" vertAlign=\"TOP\" horzAlign=\"LEFT\" vertOffset=\"0\" horzOffset=\"0\"/><hp:outMargin left=\"0\" right=\"0\" top=\"0\" bottom=\"0\"/><hp:pt0 x=\"0\" y=\"0\"/><hp:pt1 x=\"100\" y=\"0\"/><hp:pt2 x=\"100\" y=\"80\"/><hp:pt3 x=\"0\" y=\"80\"/></hp:rect>",
        object.native_object_id,
        object.z_order,
        object.group_level,
        object.native_instance_id,
        object.bounds.x_hwpunit,
        object.bounds.y_hwpunit,
        object.bounds.width_hwpunit,
        object.bounds.height_hwpunit,
        object.bounds.width_hwpunit,
        object.bounds.height_hwpunit,
        object.native_object_id,
        object.bounds.width_hwpunit,
        object.bounds.height_hwpunit,
    )
}

fn section(source: &ObjectCompositionGraph) -> Vec<u8> {
    let mut roots: Vec<_> = source
        .objects()
        .iter()
        .filter(|object| object.parent_group_id.is_none())
        .collect();
    roots.sort_by_key(|object| object.z_order);
    let objects = roots.into_iter().map(rect).collect::<Vec<_>>().join("\n");
    format!(
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?><hp:section xmlns:hp=\"{PARAGRAPH_NS}\" xmlns:hc=\"{CORE_NS}\"><hp:p id=\"1\"><hp:run charPrIDRef=\"1\"><hp:t>before</hp:t>{objects}<hp:t>after</hp:t></hp:run></hp:p></hp:section>"
    )
    .into_bytes()
}

fn request(
    source: &ObjectCompositionGraph,
    operation: ObjectCompositionOperation,
) -> ObjectCompositionRequest {
    ObjectCompositionRequest::from_draft(
        ObjectCompositionRequestDraft {
            schema_version: OBJECT_COMPOSITION_SCHEMA_VERSION.to_owned(),
            request_id: id("request"),
            expected_source_state_sha256: source
                .canonical_sha256(graph_limits())
                .expect("source digest"),
            expected_document_flow_sha256: FLOW_A.to_owned(),
            target_document_flow_sha256: FLOW_B.to_owned(),
            operation,
        },
        source,
        FLOW_A,
        graph_limits(),
    )
    .expect("request")
}

fn lower(
    xml: &[u8],
    source: &ObjectCompositionGraph,
    operation: ObjectCompositionOperation,
) -> (ObjectCompositionHwpxLowered, ObjectCompositionGraph) {
    let request = request(source, operation);
    let domain_plan = ObjectCompositionBuilder::plan(source, &request, FLOW_A, graph_limits())
        .expect("domain plan");
    let target = domain_plan.target_state().clone();
    let plan = ObjectCompositionHwpxBuilder::plan(
        xml,
        source,
        &request,
        FLOW_A,
        graph_limits(),
        hwpx_limits(),
    )
    .expect("HWPX plan");
    let lowered = ObjectCompositionHwpxLowerer::lower(
        &plan,
        xml,
        source,
        FLOW_A,
        graph_limits(),
        hwpx_limits(),
    )
    .expect("lower");
    (lowered, target)
}

#[test]
fn group_and_ungroup_lower_as_native_container_and_preserve_outside_island() {
    let source = standard();
    let xml = section(&source);
    let (grouped, grouped_graph) = lower(
        &xml,
        &source,
        ObjectCompositionOperation::Group {
            group: NewGroup {
                object_id: id("group"),
                native_object_id: 20,
                native_instance_id: 120,
                visible: true,
                printable: true,
                content: empty_content(),
            },
            member_ids: vec![id("a"), id("b")],
        },
    );
    let grouped_text = String::from_utf8(grouped.section_xml.clone()).expect("UTF-8");
    assert!(grouped_text.contains("<hp:container id=\"20\""));
    assert!(grouped_text.contains("<hp:t>before</hp:t>"));
    assert!(grouped_text.contains("<hp:t>after</hp:t>"));
    assert!(grouped.receipt.semantic_reopen());
    assert!(grouped.receipt.outside_island_preserved());

    let (ungrouped, final_graph) = lower(
        &grouped.section_xml,
        &grouped_graph,
        ObjectCompositionOperation::Ungroup {
            group_id: id("group"),
        },
    );
    assert_eq!(final_graph, source);
    assert!(
        !String::from_utf8(ungrouped.section_xml)
            .expect("UTF-8")
            .contains("<hp:container id=\"20\"")
    );
}

#[test]
fn all_z_order_movements_reopen_with_exact_native_order_attributes() {
    for (object, movement, expected) in [
        ("a", ZOrderMove::BringToFront, 3),
        ("d", ZOrderMove::SendToBack, 0),
        ("b", ZOrderMove::ForwardOne, 2),
        ("c", ZOrderMove::BackwardOne, 1),
    ] {
        let source = standard();
        let (lowered, target) = lower(
            &section(&source),
            &source,
            ObjectCompositionOperation::SetZOrder {
                object_id: id(object),
                movement,
            },
        );
        assert_eq!(lowered.readback.object_count(), 4);
        assert_eq!(
            target.object(&id(object)).expect("object").z_order,
            expected
        );
        assert!(
            String::from_utf8(lowered.section_xml)
                .expect("UTF-8")
                .contains(&format!("zOrder=\"{expected}\""))
        );
    }
}

#[test]
fn align_and_distribute_lower_exact_offsets_without_payload_loss() {
    let source = standard();
    let (aligned, aligned_graph) = lower(
        &section(&source),
        &source,
        ObjectCompositionOperation::Align {
            object_ids: vec![id("a"), id("b"), id("c")],
            mode: ObjectAlignMode::Left,
        },
    );
    let aligned_text = String::from_utf8(aligned.section_xml).expect("UTF-8");
    assert!(aligned_text.matches("<hp:offset x=\"0\"").count() >= 3);
    assert!(aligned_text.contains("opaque-2"));

    let (distributed, _) = lower(
        aligned_text.as_bytes(),
        &aligned_graph,
        ObjectCompositionOperation::Distribute {
            object_ids: vec![id("a"), id("b"), id("c"), id("d")],
            axis: CompositionAxis::Vertical,
        },
    );
    ObjectCompositionHwpxReader::read(
        &distributed.section_xml,
        &lower_target(
            &aligned_graph,
            ObjectCompositionOperation::Distribute {
                object_ids: vec![id("a"), id("b"), id("c"), id("d")],
                axis: CompositionAxis::Vertical,
            },
        ),
        graph_limits(),
        hwpx_limits(),
    )
    .expect("reopen");
}

fn endpoint(x: i64, y: i64, subject: &str, index: u32) -> ConnectorEndpoint {
    ConnectorEndpoint {
        x_hwpunit: x,
        y_hwpunit: y,
        subject: Some(ConnectorSubject {
            object_id: id(subject),
            connection_index: index,
        }),
    }
}

fn connector_operation(kind: ConnectorKind) -> ObjectCompositionOperation {
    ObjectCompositionOperation::CreateConnector {
        connector: NewConnector {
            object_id: id("connector"),
            native_object_id: 30,
            native_instance_id: 130,
            parent_group_id: None,
            z_order: 4,
            visible: true,
            printable: true,
            content: empty_content(),
            topology: ConnectorTopology {
                kind,
                start: endpoint(100, 40, "a", 1),
                end: endpoint(200, 140, "b", 2),
                control_points: Vec::new(),
            },
        },
    }
}

#[test]
fn connector_create_and_update_cover_native_subjects_control_points_and_all_types() {
    let kinds = [
        ConnectorKind::StraightNoArrow,
        ConnectorKind::StraightOneWay,
        ConnectorKind::StraightBoth,
        ConnectorKind::StrokeNoArrow,
        ConnectorKind::StrokeOneWay,
        ConnectorKind::StrokeBoth,
        ConnectorKind::ArcNoArrow,
        ConnectorKind::ArcOneWay,
        ConnectorKind::ArcBoth,
    ];
    for kind in kinds {
        let source = standard();
        let (created, target) = lower(&section(&source), &source, connector_operation(kind));
        ObjectCompositionHwpxReader::read(
            &created.section_xml,
            &target,
            graph_limits(),
            hwpx_limits(),
        )
        .expect("connector kind reopen");
    }

    let source = standard();
    let (created, created_graph) = lower(
        &section(&source),
        &source,
        connector_operation(ConnectorKind::StraightOneWay),
    );
    let created_text = String::from_utf8(created.section_xml.clone()).expect("UTF-8");
    assert!(created_text.contains("type=\"STRAIGHT_ONEWAY\""));
    assert!(created_text.contains("subjectIDRef=\"1\" subjectIdx=\"1\""));

    let topology = ConnectorTopology {
        kind: ConnectorKind::ArcBoth,
        start: endpoint(100, 40, "a", 3),
        end: endpoint(500, 340, "c", 4),
        control_points: vec![ConnectorControlPoint {
            x_hwpunit: 300,
            y_hwpunit: 50,
            point_type: 7,
        }],
    };
    let (updated, _) = lower(
        &created.section_xml,
        &created_graph,
        ObjectCompositionOperation::UpdateConnector {
            connector_id: id("connector"),
            topology,
        },
    );
    let text = String::from_utf8(updated.section_xml).expect("UTF-8");
    assert!(text.contains("type=\"ARC_BOTH\""));
    assert!(text.contains("<hp:point x=\"300\" y=\"50\" type=\"7\"/>"));
}

#[test]
fn source_flow_and_native_topology_drift_fail_closed() {
    let source = standard();
    let xml = section(&source);
    let request = request(
        &source,
        ObjectCompositionOperation::SetZOrder {
            object_id: id("a"),
            movement: ZOrderMove::BringToFront,
        },
    );
    assert!(matches!(
        ObjectCompositionHwpxBuilder::plan(
            &xml,
            &source,
            &request,
            FLOW_B,
            graph_limits(),
            hwpx_limits(),
        ),
        Err(ObjectCompositionHwpxError::DocumentFlowDrift)
    ));
    let tampered = String::from_utf8(xml)
        .expect("UTF-8")
        .replace("id=\"2\" zOrder=\"1\"", "id=\"2\" zOrder=\"9\"");
    assert!(matches!(
        ObjectCompositionHwpxReader::read(
            tampered.as_bytes(),
            &source,
            graph_limits(),
            hwpx_limits()
        ),
        Err(ObjectCompositionHwpxError::UnsupportedProfile)
    ));
}

#[test]
fn generated_objects_reject_unrepresentable_noncomposition_payloads() {
    let source = standard();
    let operation = ObjectCompositionOperation::Group {
        group: NewGroup {
            object_id: id("group"),
            native_object_id: 20,
            native_instance_id: 120,
            visible: true,
            printable: true,
            content: content(20),
        },
        member_ids: vec![id("a"), id("b")],
    };
    let request = request(&source, operation);
    assert!(matches!(
        ObjectCompositionHwpxBuilder::plan(
            &section(&source),
            &source,
            &request,
            FLOW_A,
            graph_limits(),
            hwpx_limits(),
        ),
        Err(ObjectCompositionHwpxError::UnsupportedProfile)
    ));
}

fn lower_target(
    source: &ObjectCompositionGraph,
    operation: ObjectCompositionOperation,
) -> ObjectCompositionGraph {
    let request = request(source, operation);
    ObjectCompositionBuilder::plan(source, &request, FLOW_A, graph_limits())
        .expect("plan")
        .target_state()
        .clone()
}
