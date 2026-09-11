#![allow(clippy::expect_used)] // Test fixtures use expectations to keep failures local and legible.

use std::collections::BTreeMap;

use domain_ir::{
    CompositionAxis, CompositionBounds, CompositionObject, CompositionObjectContent,
    CompositionObjectKind, ConnectorControlPoint, ConnectorEndpoint, ConnectorKind,
    ConnectorSubject, ConnectorTopology, LogicalId, NewConnector, NewGroup,
    OBJECT_COMPOSITION_SCHEMA_VERSION, ObjectAlignMode, ObjectCompositionBuilder,
    ObjectCompositionError, ObjectCompositionGraph, ObjectCompositionGraphDraft,
    ObjectCompositionLimitConfig, ObjectCompositionLimits, ObjectCompositionOperation,
    ObjectCompositionRequest, ObjectCompositionRequestDraft, ZOrderMove,
};

const FLOW_A: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const FLOW_B: &str = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";

fn limits() -> ObjectCompositionLimits {
    ObjectCompositionLimits::new(ObjectCompositionLimitConfig::default()).expect("limits")
}

fn id(value: &str) -> LogicalId {
    LogicalId::parse(value).expect("logical id")
}

fn content(seed: u32) -> CompositionObjectContent {
    CompositionObjectContent {
        state_sha256: format!("{seed:064x}"),
        byte_length: u64::from(seed) + 10,
        resource_refs: if seed.is_multiple_of(2) {
            vec![id(&format!("resource-{seed}"))]
        } else {
            Vec::new()
        },
    }
}

fn shape(
    name: &str,
    native: u32,
    z_order: u32,
    x: i64,
    y: i64,
    width: u64,
    height: u64,
) -> CompositionObject {
    CompositionObject {
        object_id: id(name),
        native_object_id: native,
        native_instance_id: native + 100,
        kind: CompositionObjectKind::BasicShape,
        parent_group_id: None,
        z_order,
        group_level: 0,
        bounds: CompositionBounds {
            x_hwpunit: x,
            y_hwpunit: y,
            width_hwpunit: width,
            height_hwpunit: height,
        },
        visible: true,
        printable: native.is_multiple_of(2),
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
        limits(),
    )
    .expect("graph")
}

fn standard() -> ObjectCompositionGraph {
    graph(vec![
        shape("a", 1, 0, 0, 0, 10, 10),
        shape("b", 2, 1, 30, 20, 20, 20),
        shape("c", 3, 2, 80, 40, 10, 30),
        shape("d", 4, 3, 110, 70, 10, 10),
    ])
}

fn new_group(name: &str, native: u32) -> NewGroup {
    NewGroup {
        object_id: id(name),
        native_object_id: native,
        native_instance_id: native + 100,
        visible: true,
        printable: true,
        content: content(native),
    }
}

fn execute(
    source: &ObjectCompositionGraph,
    operation: ObjectCompositionOperation,
) -> Result<ObjectCompositionGraph, ObjectCompositionError> {
    let request = ObjectCompositionRequest::from_draft(
        ObjectCompositionRequestDraft {
            schema_version: OBJECT_COMPOSITION_SCHEMA_VERSION.to_owned(),
            request_id: id("request"),
            expected_source_state_sha256: source.canonical_sha256(limits())?,
            expected_document_flow_sha256: FLOW_A.to_owned(),
            target_document_flow_sha256: FLOW_B.to_owned(),
            operation,
        },
        source,
        FLOW_A,
        limits(),
    )?;
    let plan = ObjectCompositionBuilder::plan(source, &request, FLOW_A, limits())?;
    ObjectCompositionBuilder::build(&plan, source, FLOW_A, limits()).map(|result| result.state)
}

fn sibling_order(graph: &ObjectCompositionGraph, parent: Option<&LogicalId>) -> Vec<String> {
    let mut objects: Vec<_> = graph
        .objects()
        .iter()
        .filter(|object| object.parent_group_id.as_ref() == parent)
        .collect();
    objects.sort_by_key(|object| object.z_order);
    objects
        .into_iter()
        .map(|object| object.object_id.as_str().to_owned())
        .collect()
}

fn stable_fields(
    graph: &ObjectCompositionGraph,
) -> BTreeMap<String, (u32, u32, bool, bool, CompositionObjectContent)> {
    graph
        .objects()
        .iter()
        .map(|object| {
            (
                object.object_id.as_str().to_owned(),
                (
                    object.native_object_id,
                    object.native_instance_id,
                    object.visible,
                    object.printable,
                    object.content.clone(),
                ),
            )
        })
        .collect()
}

#[test]
fn group_and_ungroup_round_trip_members_identity_content_geometry_and_order() {
    let source = standard();
    let grouped = execute(
        &source,
        ObjectCompositionOperation::Group {
            group: new_group("group", 20),
            member_ids: vec![id("a"), id("b")],
        },
    )
    .expect("group");

    assert_eq!(sibling_order(&grouped, None), ["group", "c", "d"]);
    assert_eq!(sibling_order(&grouped, Some(&id("group"))), ["a", "b"]);
    let group = grouped.object(&id("group")).expect("group object");
    assert_eq!(
        group.bounds,
        CompositionBounds {
            x_hwpunit: 0,
            y_hwpunit: 0,
            width_hwpunit: 50,
            height_hwpunit: 40,
        }
    );
    for name in ["a", "b"] {
        let before = source.object(&id(name)).expect("source member");
        let after = grouped.object(&id(name)).expect("grouped member");
        assert_eq!(before.bounds, after.bounds);
        assert_eq!(before.content, after.content);
        assert_eq!(after.group_level, 1);
    }

    let ungrouped = execute(
        &grouped,
        ObjectCompositionOperation::Ungroup {
            group_id: id("group"),
        },
    )
    .expect("ungroup");
    assert_eq!(ungrouped, source);
}

#[test]
fn every_z_order_move_is_exact_and_keeps_non_order_state() {
    let source = standard();
    let stable = stable_fields(&source);
    let front = execute(
        &source,
        ObjectCompositionOperation::SetZOrder {
            object_id: id("a"),
            movement: ZOrderMove::BringToFront,
        },
    )
    .expect("front");
    assert_eq!(sibling_order(&front, None), ["b", "c", "d", "a"]);

    let backward = execute(
        &front,
        ObjectCompositionOperation::SetZOrder {
            object_id: id("a"),
            movement: ZOrderMove::BackwardOne,
        },
    )
    .expect("backward");
    assert_eq!(sibling_order(&backward, None), ["b", "c", "a", "d"]);

    let back = execute(
        &backward,
        ObjectCompositionOperation::SetZOrder {
            object_id: id("d"),
            movement: ZOrderMove::SendToBack,
        },
    )
    .expect("back");
    assert_eq!(sibling_order(&back, None), ["d", "b", "c", "a"]);

    let forward = execute(
        &back,
        ObjectCompositionOperation::SetZOrder {
            object_id: id("d"),
            movement: ZOrderMove::ForwardOne,
        },
    )
    .expect("forward");
    assert_eq!(sibling_order(&forward, None), ["b", "d", "c", "a"]);
    assert_eq!(stable_fields(&forward), stable);
}

#[test]
fn six_alignment_modes_are_deterministic_and_preserve_content() {
    let source = standard();
    let selection = || vec![id("a"), id("b"), id("c")];
    let expected = [
        (ObjectAlignMode::Left, [(0, 0), (0, 20), (0, 40)]),
        (
            ObjectAlignMode::HorizontalCenter,
            [(40, 0), (35, 20), (40, 40)],
        ),
        (ObjectAlignMode::Right, [(80, 0), (70, 20), (80, 40)]),
        (ObjectAlignMode::Top, [(0, 0), (30, 0), (80, 0)]),
        (
            ObjectAlignMode::VerticalMiddle,
            [(0, 30), (30, 25), (80, 20)],
        ),
        (ObjectAlignMode::Bottom, [(0, 60), (30, 50), (80, 40)]),
    ];
    for (mode, positions) in expected {
        let target = execute(
            &source,
            ObjectCompositionOperation::Align {
                object_ids: selection(),
                mode,
            },
        )
        .expect("align");
        for (name, position) in ["a", "b", "c"].into_iter().zip(positions) {
            let object = target.object(&id(name)).expect("aligned object");
            assert_eq!((object.bounds.x_hwpunit, object.bounds.y_hwpunit), position);
            assert_eq!(
                object.content,
                source.object(&id(name)).expect("source object").content
            );
        }
    }
}

#[test]
fn horizontal_and_vertical_distribution_use_balanced_integer_gaps() {
    let horizontal = graph(vec![
        shape("a", 1, 0, 0, 0, 10, 10),
        shape("b", 2, 1, 25, 20, 10, 10),
        shape("c", 3, 2, 61, 45, 10, 10),
        shape("d", 4, 3, 100, 100, 10, 10),
    ]);
    let ids = || vec![id("a"), id("b"), id("c"), id("d")];
    let distributed = execute(
        &horizontal,
        ObjectCompositionOperation::Distribute {
            object_ids: ids(),
            axis: CompositionAxis::Horizontal,
        },
    )
    .expect("horizontal distribution");
    assert_eq!(
        ["a", "b", "c", "d"].map(|name| {
            distributed
                .object(&id(name))
                .expect("object")
                .bounds
                .x_hwpunit
        }),
        [0, 34, 67, 100]
    );

    let vertical = execute(
        &horizontal,
        ObjectCompositionOperation::Distribute {
            object_ids: ids(),
            axis: CompositionAxis::Vertical,
        },
    )
    .expect("vertical distribution");
    assert_eq!(
        ["a", "b", "c", "d"]
            .map(|name| { vertical.object(&id(name)).expect("object").bounds.y_hwpunit }),
        [0, 34, 67, 100]
    );
}

fn endpoint(x: i64, y: i64, subject: &str, connection_index: u32) -> ConnectorEndpoint {
    ConnectorEndpoint {
        x_hwpunit: x,
        y_hwpunit: y,
        subject: Some(ConnectorSubject {
            object_id: id(subject),
            connection_index,
        }),
    }
}

#[test]
fn connector_create_update_and_closed_group_preserve_exact_subject_edges() {
    let source = graph(vec![
        shape("a", 1, 0, 0, 0, 10, 10),
        shape("b", 2, 1, 20, 0, 10, 10),
    ]);
    let created = execute(
        &source,
        ObjectCompositionOperation::CreateConnector {
            connector: NewConnector {
                object_id: id("connector"),
                native_object_id: 3,
                native_instance_id: 103,
                parent_group_id: None,
                z_order: 2,
                visible: true,
                printable: true,
                content: content(3),
                topology: ConnectorTopology {
                    kind: ConnectorKind::StraightOneWay,
                    start: endpoint(10, 5, "a", 1),
                    end: endpoint(20, 5, "b", 2),
                    control_points: Vec::new(),
                },
            },
        },
    )
    .expect("connector create");
    assert_eq!(sibling_order(&created, None), ["a", "b", "connector"]);
    assert_eq!(
        created.object(&id("connector")).expect("connector").bounds,
        CompositionBounds {
            x_hwpunit: 10,
            y_hwpunit: 5,
            width_hwpunit: 10,
            height_hwpunit: 0,
        }
    );

    let updated = execute(
        &created,
        ObjectCompositionOperation::UpdateConnector {
            connector_id: id("connector"),
            topology: ConnectorTopology {
                kind: ConnectorKind::StrokeBoth,
                start: endpoint(10, 5, "a", 1),
                end: endpoint(25, 10, "b", 3),
                control_points: vec![ConnectorControlPoint {
                    x_hwpunit: 15,
                    y_hwpunit: 12,
                    point_type: 7,
                }],
            },
        },
    )
    .expect("connector update");
    assert_eq!(
        updated.object(&id("connector")).expect("connector").content,
        created.object(&id("connector")).expect("connector").content
    );

    let grouped = execute(
        &updated,
        ObjectCompositionOperation::Group {
            group: new_group("group", 20),
            member_ids: vec![id("connector"), id("b"), id("a")],
        },
    )
    .expect("closed connector group");
    let topology = grouped
        .object(&id("connector"))
        .and_then(|object| object.connector.as_ref())
        .expect("topology");
    assert_eq!(
        topology
            .start
            .subject
            .as_ref()
            .expect("start subject")
            .object_id,
        id("a")
    );
    assert_eq!(
        topology
            .end
            .subject
            .as_ref()
            .expect("end subject")
            .object_id,
        id("b")
    );
}

#[test]
fn invalid_topology_selection_and_cross_parent_edges_fail_closed() {
    let mut gap = standard().objects().to_vec();
    gap.iter_mut()
        .find(|object| object.object_id == id("b"))
        .expect("b")
        .z_order = 9;
    assert_eq!(
        ObjectCompositionGraph::from_draft(
            ObjectCompositionGraphDraft {
                schema_version: OBJECT_COMPOSITION_SCHEMA_VERSION.to_owned(),
                objects: gap,
            },
            limits(),
        ),
        Err(ObjectCompositionError::InvalidZOrder)
    );

    let source = graph(vec![
        shape("a", 1, 0, 0, 0, 10, 10),
        shape("b", 2, 1, 20, 0, 10, 10),
    ]);
    assert_eq!(
        execute(
            &source,
            ObjectCompositionOperation::Group {
                group: new_group("group", 20),
                member_ids: vec![id("a")],
            },
        ),
        Err(ObjectCompositionError::InvalidSelection)
    );

    let with_connector = execute(
        &source,
        ObjectCompositionOperation::CreateConnector {
            connector: NewConnector {
                object_id: id("connector"),
                native_object_id: 3,
                native_instance_id: 103,
                parent_group_id: None,
                z_order: 2,
                visible: true,
                printable: true,
                content: content(3),
                topology: ConnectorTopology {
                    kind: ConnectorKind::StraightNoArrow,
                    start: endpoint(10, 5, "a", 0),
                    end: endpoint(20, 5, "b", 0),
                    control_points: Vec::new(),
                },
            },
        },
    )
    .expect("connector");
    assert_eq!(
        execute(
            &with_connector,
            ObjectCompositionOperation::Group {
                group: new_group("group", 20),
                member_ids: vec![id("a"), id("b")],
            },
        ),
        Err(ObjectCompositionError::InvalidConnector)
    );
}

#[test]
fn strict_json_limits_source_flow_drift_and_debug_redaction_hold() {
    let source = standard();
    let source_sha = source.canonical_sha256(limits()).expect("source digest");
    let draft = ObjectCompositionRequestDraft {
        schema_version: OBJECT_COMPOSITION_SCHEMA_VERSION.to_owned(),
        request_id: id("private-request"),
        expected_source_state_sha256: source_sha.clone(),
        expected_document_flow_sha256: FLOW_A.to_owned(),
        target_document_flow_sha256: FLOW_B.to_owned(),
        operation: ObjectCompositionOperation::SetZOrder {
            object_id: id("a"),
            movement: ZOrderMove::BringToFront,
        },
    };
    let json = serde_json::to_vec(&draft).expect("json");
    let request = ObjectCompositionRequest::from_json(&json, &source, FLOW_A, limits())
        .expect("strict request");
    let debug = format!("{request:?}");
    assert!(!debug.contains("private-request"));
    assert!(!debug.contains(&source_sha));
    assert!(!debug.contains(FLOW_A));

    let duplicate = String::from_utf8(json.clone()).expect("utf8").replace(
        "\"schema_version\":",
        "\"schema_version\":\"hwpx-agent.object-composition/v1\",\"schema_version\":",
    );
    assert_eq!(
        ObjectCompositionRequest::from_json(duplicate.as_bytes(), &source, FLOW_A, limits()),
        Err(ObjectCompositionError::InvalidJson)
    );
    let unknown = String::from_utf8(json)
        .expect("utf8")
        .replacen('{', "{\"unknown\":true,", 1);
    assert_eq!(
        ObjectCompositionRequest::from_json(unknown.as_bytes(), &source, FLOW_A, limits()),
        Err(ObjectCompositionError::InvalidJson)
    );

    let mut drifted = source.objects().to_vec();
    drifted[0].content.state_sha256 = "f".repeat(64);
    let drifted = graph(drifted);
    assert_eq!(
        ObjectCompositionRequest::from_draft(draft.clone(), &drifted, FLOW_A, limits()),
        Err(ObjectCompositionError::SourceStateDrift)
    );
    assert_eq!(
        ObjectCompositionRequest::from_draft(draft, &source, FLOW_B, limits()),
        Err(ObjectCompositionError::DocumentFlowDrift)
    );
}

#[test]
fn plan_and_build_recheck_exact_source_and_document_flow() {
    let source = standard();
    let request = ObjectCompositionRequest::from_draft(
        ObjectCompositionRequestDraft {
            schema_version: OBJECT_COMPOSITION_SCHEMA_VERSION.to_owned(),
            request_id: id("request"),
            expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
            expected_document_flow_sha256: FLOW_A.to_owned(),
            target_document_flow_sha256: FLOW_B.to_owned(),
            operation: ObjectCompositionOperation::SetZOrder {
                object_id: id("a"),
                movement: ZOrderMove::BringToFront,
            },
        },
        &source,
        FLOW_A,
        limits(),
    )
    .expect("request");
    let plan = ObjectCompositionBuilder::plan(&source, &request, FLOW_A, limits()).expect("plan");
    assert_eq!(
        ObjectCompositionBuilder::build(&plan, &source, FLOW_B, limits()),
        Err(ObjectCompositionError::DocumentFlowDrift)
    );
    let mut drifted = source.objects().to_vec();
    drifted[0].bounds.x_hwpunit += 1;
    let drifted = graph(drifted);
    assert_eq!(
        ObjectCompositionBuilder::build(&plan, &drifted, FLOW_A, limits()),
        Err(ObjectCompositionError::SourceStateDrift)
    );
}

#[test]
fn graph_json_coordinate_and_collection_boundaries_are_fail_closed() {
    let source = standard();
    let json = source.canonical_json(limits()).expect("graph json");
    assert_eq!(
        ObjectCompositionGraph::from_json(&json, limits()).expect("strict graph"),
        source
    );

    let duplicate = String::from_utf8(json.clone()).expect("utf8").replacen(
        "\"schema_version\":",
        "\"schema_version\":\"hwpx-agent.object-composition/v1\",\"schema_version\":",
        1,
    );
    assert_eq!(
        ObjectCompositionGraph::from_json(duplicate.as_bytes(), limits()),
        Err(ObjectCompositionError::InvalidJson)
    );

    let tiny_config = ObjectCompositionLimitConfig {
        input_bytes: 128,
        serialized_bytes: 128,
        ..ObjectCompositionLimitConfig::default()
    };
    let tiny = ObjectCompositionLimits::new(tiny_config).expect("tiny limits");
    assert_eq!(
        ObjectCompositionGraph::from_json(&json, tiny),
        Err(ObjectCompositionError::InputLimit)
    );

    let mut invalid_bounds = source.objects().to_vec();
    invalid_bounds[0].bounds.x_hwpunit = limits().config().coordinate_magnitude_hwpunit;
    assert_eq!(
        ObjectCompositionGraph::from_draft(
            ObjectCompositionGraphDraft {
                schema_version: OBJECT_COMPOSITION_SCHEMA_VERSION.to_owned(),
                objects: invalid_bounds,
            },
            limits(),
        ),
        Err(ObjectCompositionError::InvalidGeometry)
    );

    let mut bad_content = source.objects().to_vec();
    bad_content[0].content.resource_refs = vec![id("z"), id("a")];
    assert_eq!(
        ObjectCompositionGraph::from_draft(
            ObjectCompositionGraphDraft {
                schema_version: OBJECT_COMPOSITION_SCHEMA_VERSION.to_owned(),
                objects: bad_content,
            },
            limits(),
        ),
        Err(ObjectCompositionError::InvalidContent)
    );
}
