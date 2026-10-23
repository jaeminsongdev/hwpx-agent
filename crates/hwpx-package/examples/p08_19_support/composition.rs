use domain_ir::{
    CompositionAxis, CompositionBounds, CompositionObject, CompositionObjectContent,
    CompositionObjectKind, ConnectorEndpoint, ConnectorKind, ConnectorSubject, ConnectorTopology,
    LogicalId, NewConnector, NewGroup, OBJECT_COMPOSITION_SCHEMA_VERSION, ObjectAlignMode,
    ObjectCompositionBuilder, ObjectCompositionGraph, ObjectCompositionGraphDraft,
    ObjectCompositionLimitConfig, ObjectCompositionLimits, ObjectCompositionOperation,
    ObjectCompositionRequest, ObjectCompositionRequestDraft, ZOrderMove,
};
use hwpx_package::{
    OBJECT_COMPOSITION_HWPX_PROFILE_ID, ObjectCompositionHwpxBuilder,
    ObjectCompositionHwpxLimitConfig, ObjectCompositionHwpxLimits, ObjectCompositionHwpxLowerer,
};

use super::common::{
    AnyError, FLOW_AFTER, FLOW_BEFORE, LoweringEvidence, PreparedCase, prepared_from_section,
    section_from_package, sha256,
};

const EMPTY_SHA: &str = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";

#[allow(clippy::too_many_lines)] // One ordered table keeps all six composition rows auditable.
pub fn cases(shape_package: &[u8]) -> Result<Vec<PreparedCase>, AnyError> {
    let source_graph = standard()?;
    let source_section = composition_section(shape_package, &source_graph)?;

    let group_operation = ObjectCompositionOperation::Group {
        group: NewGroup {
            object_id: id("group")?,
            native_object_id: 8_220,
            native_instance_id: 18_220,
            visible: true,
            printable: true,
            content: empty_content(),
        },
        member_ids: vec![id("a")?, id("b")?],
    };
    let (grouped_section, grouped_graph, grouped_evidence) =
        lower(&source_section, &source_graph, group_operation.clone())?;
    let group_case = prepared_from_section(
        "P08-19-C29",
        "OBJ-036",
        "obj.group",
        "obj-036-group.hwpx",
        shape_package,
        &grouped_section,
        vec![grouped_evidence.clone()],
        "container",
        8_220,
        18_220,
        false,
    )?;

    let (ungrouped_section, _, ungrouped_evidence) = lower(
        &grouped_section,
        &grouped_graph,
        ObjectCompositionOperation::Ungroup {
            group_id: id("group")?,
        },
    )?;
    let ungroup_case = prepared_from_section(
        "P08-19-C30",
        "OBJ-037",
        "obj.ungroup",
        "obj-037-ungroup.hwpx",
        shape_package,
        &ungrouped_section,
        vec![grouped_evidence, ungrouped_evidence],
        "composition_graph",
        8_201,
        18_301,
        false,
    )?;

    let z_order_case = independent_case(
        shape_package,
        &source_section,
        &source_graph,
        "P08-19-C31",
        "OBJ-038",
        "obj.z_order",
        "obj-038-z-order.hwpx",
        ObjectCompositionOperation::SetZOrder {
            object_id: id("b")?,
            movement: ZOrderMove::BringToFront,
        },
        "rectangle",
        8_202,
        18_302,
    )?;
    let align_case = independent_case(
        shape_package,
        &source_section,
        &source_graph,
        "P08-19-C32",
        "OBJ-039",
        "obj.align",
        "obj-039-align.hwpx",
        ObjectCompositionOperation::Align {
            object_ids: vec![id("a")?, id("b")?, id("c")?],
            mode: ObjectAlignMode::Left,
        },
        "composition_graph",
        8_201,
        18_301,
    )?;
    let distribute_case = independent_case(
        shape_package,
        &source_section,
        &source_graph,
        "P08-19-C33",
        "OBJ-040",
        "obj.distribute",
        "obj-040-distribute.hwpx",
        ObjectCompositionOperation::Distribute {
            object_ids: vec![id("a")?, id("b")?, id("c")?, id("d")?],
            axis: CompositionAxis::Vertical,
        },
        "composition_graph",
        8_201,
        18_301,
    )?;
    let connector_case = independent_case(
        shape_package,
        &source_section,
        &source_graph,
        "P08-19-C34",
        "OBJ-041",
        "obj.connector",
        "obj-041-connector.hwpx",
        connector_operation()?,
        "connector",
        8_230,
        18_330,
    )?;

    Ok(vec![
        group_case,
        ungroup_case,
        z_order_case,
        align_case,
        distribute_case,
        connector_case,
    ])
}

#[allow(clippy::too_many_arguments)]
fn independent_case(
    source_package: &[u8],
    source_section: &[u8],
    source_graph: &ObjectCompositionGraph,
    case_id: &str,
    feature_id: &str,
    capability_id: &str,
    file: &str,
    operation: ObjectCompositionOperation,
    object_kind: &str,
    native_object_id: u32,
    native_instance_id: u32,
) -> Result<PreparedCase, AnyError> {
    let (output, _, evidence) = lower(source_section, source_graph, operation)?;
    if evidence.capability_id != capability_id {
        return Err("composition capability drifted".into());
    }
    prepared_from_section(
        case_id,
        feature_id,
        capability_id,
        file,
        source_package,
        &output,
        vec![evidence],
        object_kind,
        native_object_id,
        native_instance_id,
        false,
    )
}

fn lower(
    section: &[u8],
    source: &ObjectCompositionGraph,
    operation: ObjectCompositionOperation,
) -> Result<(Vec<u8>, ObjectCompositionGraph, LoweringEvidence), AnyError> {
    let capability_id = operation.capability_id();
    let limits = graph_limits()?;
    let request = ObjectCompositionRequest::from_draft(
        ObjectCompositionRequestDraft {
            schema_version: OBJECT_COMPOSITION_SCHEMA_VERSION.to_owned(),
            request_id: id("p08-19-composition-request")?,
            expected_source_state_sha256: source.canonical_sha256(limits)?,
            expected_document_flow_sha256: FLOW_BEFORE.to_owned(),
            target_document_flow_sha256: FLOW_AFTER.to_owned(),
            operation,
        },
        source,
        FLOW_BEFORE,
        limits,
    )?;
    let domain = ObjectCompositionBuilder::plan(source, &request, FLOW_BEFORE, limits)?;
    let target = domain.target_state().clone();
    let plan = ObjectCompositionHwpxBuilder::plan(
        section,
        source,
        &request,
        FLOW_BEFORE,
        limits,
        hwpx_limits()?,
    )?;
    let plan_sha256 = plan.plan_sha256().to_owned();
    let lowered = ObjectCompositionHwpxLowerer::lower(
        &plan,
        section,
        source,
        FLOW_BEFORE,
        limits,
        hwpx_limits()?,
    )?;
    if !lowered.receipt.semantic_reopen() || !lowered.receipt.outside_island_preserved() {
        return Err("composition lowering evidence is incomplete".into());
    }
    let evidence = LoweringEvidence {
        profile_id: OBJECT_COMPOSITION_HWPX_PROFILE_ID.to_owned(),
        capability_id: capability_id.to_owned(),
        plan_sha256,
        source_section_sha256: sha256(section),
        output_section_sha256: sha256(&lowered.section_xml),
        modified_unit_count: 1,
    };
    Ok((lowered.section_xml, target, evidence))
}

fn composition_section(
    shape_package: &[u8],
    graph: &ObjectCompositionGraph,
) -> Result<Vec<u8>, AnyError> {
    let section = section_from_package(shape_package)?;
    let mut roots = graph
        .objects()
        .iter()
        .filter(|object| object.parent_group_id.is_none())
        .collect::<Vec<_>>();
    roots.sort_by_key(|object| object.z_order);
    let replacement = roots.into_iter().map(rect).collect::<String>();
    replace_direct_object(&section, "<hp:rect ", "</hp:rect>", &replacement)
}

fn rect(object: &CompositionObject) -> String {
    format!(
        concat!(
            "<hp:rect id=\"{}\" zOrder=\"{}\" numberingType=\"NONE\" textWrap=\"TOP_AND_BOTTOM\" ",
            "textFlow=\"BOTH_SIDES\" lock=\"0\" dropcapstyle=\"None\" href=\"\" groupLevel=\"{}\" instid=\"{}\" ratio=\"0\">",
            "<hp:offset x=\"{}\" y=\"{}\"/><hp:orgSz width=\"{}\" height=\"{}\"/>",
            "<hp:curSz width=\"{}\" height=\"{}\"/><hp:flip horizontal=\"0\" vertical=\"0\"/>",
            "<hp:rotationInfo angle=\"0\" centerX=\"3600\" centerY=\"1800\" rotateimage=\"1\"/>",
            "<hp:renderingInfo><hc:transMatrix e1=\"1\" e2=\"0\" e3=\"0\" e4=\"0\" e5=\"1\" e6=\"0\"/>",
            "<hc:scaMatrix e1=\"1\" e2=\"0\" e3=\"0\" e4=\"0\" e5=\"1\" e6=\"0\"/>",
            "<hc:rotMatrix e1=\"1\" e2=\"0\" e3=\"0\" e4=\"0\" e5=\"1\" e6=\"0\"/></hp:renderingInfo>",
            "<hp:lineShape color=\"#000000\" width=\"283\" style=\"SOLID\" endCap=\"FLAT\" ",
            "headStyle=\"NORMAL\" tailStyle=\"NORMAL\" headfill=\"0\" tailfill=\"0\" ",
            "headSz=\"SMALL_SMALL\" tailSz=\"SMALL_SMALL\" outlineStyle=\"NORMAL\" alpha=\"0\"/>",
            "<hp:shadow type=\"NONE\" color=\"#B2B2B2\" offsetX=\"0\" offsetY=\"0\" alpha=\"0\"/>",
            "<hc:pt0 x=\"0\" y=\"0\"/><hc:pt1 x=\"7200\" y=\"0\"/><hc:pt2 x=\"7200\" y=\"3600\"/>",
            "<hc:pt3 x=\"0\" y=\"3600\"/><hp:shapeComment>opaque-{}</hp:shapeComment>",
            "<hp:sz width=\"{}\" widthRelTo=\"ABSOLUTE\" ",
            "height=\"{}\" heightRelTo=\"ABSOLUTE\" protect=\"0\"/>",
            "<hp:pos treatAsChar=\"0\" affectLSpacing=\"0\" flowWithText=\"1\" allowOverlap=\"0\" holdAnchorAndSO=\"1\" ",
            "vertRelTo=\"PARA\" horzRelTo=\"PARA\" vertAlign=\"TOP\" horzAlign=\"LEFT\" vertOffset=\"0\" horzOffset=\"0\"/>",
            "<hp:outMargin left=\"0\" right=\"0\" top=\"0\" bottom=\"0\"/></hp:rect>"
        ),
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

fn standard() -> Result<ObjectCompositionGraph, AnyError> {
    Ok(ObjectCompositionGraph::from_draft(
        ObjectCompositionGraphDraft {
            schema_version: OBJECT_COMPOSITION_SCHEMA_VERSION.to_owned(),
            objects: vec![
                shape("a", 8_201, 0, 0, 0)?,
                shape("b", 8_202, 1, 8_000, 4_000)?,
                shape("c", 8_203, 2, 16_000, 12_000)?,
                shape("d", 8_204, 3, 24_000, 24_000)?,
            ],
        },
        graph_limits()?,
    )?)
}

fn shape(
    name: &str,
    native: u32,
    z_order: u32,
    x_hwpunit: i64,
    y_hwpunit: i64,
) -> Result<CompositionObject, AnyError> {
    Ok(CompositionObject {
        object_id: id(name)?,
        native_object_id: native,
        native_instance_id: native + 10_100,
        kind: CompositionObjectKind::BasicShape,
        parent_group_id: None,
        z_order,
        group_level: 0,
        bounds: CompositionBounds {
            x_hwpunit,
            y_hwpunit,
            width_hwpunit: 7_200,
            height_hwpunit: 3_600,
        },
        visible: true,
        printable: true,
        content: content(native),
        connector: None,
    })
}

fn connector_operation() -> Result<ObjectCompositionOperation, AnyError> {
    Ok(ObjectCompositionOperation::CreateConnector {
        connector: NewConnector {
            object_id: id("connector")?,
            native_object_id: 8_230,
            native_instance_id: 18_330,
            parent_group_id: None,
            z_order: 4,
            visible: true,
            printable: true,
            content: empty_content(),
            topology: ConnectorTopology {
                kind: ConnectorKind::StraightBoth,
                start: endpoint(3_600, 1_800, "a", 1)?,
                end: endpoint(11_600, 5_800, "b", 2)?,
                control_points: Vec::new(),
            },
        },
    })
}

fn endpoint(
    x_hwpunit: i64,
    y_hwpunit: i64,
    subject: &str,
    connection_index: u32,
) -> Result<ConnectorEndpoint, AnyError> {
    Ok(ConnectorEndpoint {
        x_hwpunit,
        y_hwpunit,
        subject: Some(ConnectorSubject {
            object_id: id(subject)?,
            connection_index,
        }),
    })
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

fn graph_limits() -> Result<ObjectCompositionLimits, AnyError> {
    Ok(ObjectCompositionLimits::new(
        ObjectCompositionLimitConfig::default(),
    )?)
}

fn hwpx_limits() -> Result<ObjectCompositionHwpxLimits, AnyError> {
    Ok(ObjectCompositionHwpxLimits::new(
        ObjectCompositionHwpxLimitConfig::default(),
    )?)
}

fn id(value: &str) -> Result<LogicalId, AnyError> {
    Ok(LogicalId::parse(value)?)
}

fn replace_direct_object(
    section: &[u8],
    opening: &str,
    closing: &str,
    replacement: &str,
) -> Result<Vec<u8>, AnyError> {
    let text = std::str::from_utf8(section)?;
    let start = text
        .find(opening)
        .ok_or("composition source opening is missing")?;
    let end = text[start..]
        .find(closing)
        .map(|offset| start + offset + closing.len())
        .ok_or("composition source closing is missing")?;
    let mut output = String::with_capacity(text.len() - (end - start) + replacement.len());
    output.push_str(&text[..start]);
    output.push_str(replacement);
    output.push_str(&text[end..]);
    Ok(output.into_bytes())
}
