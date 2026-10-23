use domain_ir::{
    CanvasBindings, CanvasBounds, CanvasIdentityReservation, CanvasNode, CanvasNodeKind,
    CanvasPictureState, CanvasResource, CanvasResourceKind, DRAWING_CANVAS_SCHEMA_VERSION,
    DrawingCanvasLimitConfig, DrawingCanvasLimits, DrawingCanvasOperation, DrawingCanvasRequest,
    DrawingCanvasRequestDraft, DrawingCanvasState, DrawingCanvasStateDraft, ImageClip, LogicalId,
};
use hwpx_package::{
    DRAWING_CANVAS_HWPX_PROFILE_ID, DrawingCanvasHwpxBuilder, DrawingCanvasHwpxLimitConfig,
    DrawingCanvasHwpxLimits, DrawingCanvasHwpxLowerer,
};

use super::common::{
    AnyError, FLOW_AFTER, FLOW_BEFORE, LoweringEvidence, PreparedCase,
    package_with_section_and_text_replacement, prepared_from_section, section_from_package, sha256,
};

const EMPTY_SHA: &str = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";
const IMAGE_SHA: &str = "d68ef153c5e624e18ff00a09f95f2cbb2eecf1e73940c47b7bafcef2f4188e22";

#[allow(clippy::too_many_lines)] // The two canvas rows share one exact source topology.
pub fn cases(image_package: &[u8]) -> Result<Vec<PreparedCase>, AnyError> {
    let package_section = section_from_package(image_package)?;
    let original_resource_id = attribute_value(&package_section, b"binaryItemIDRef=\"")?;
    let source_draft = base_draft("rId1")?;
    let source = state(source_draft.clone())?;
    let source_section = canvas_section(image_package, &source)?;
    let source_package = package_with_section_and_text_replacement(
        image_package,
        &source_section,
        "Contents/content.hpf",
        &format!("id=\"{original_resource_id}\""),
        "id=\"rId1\"",
    )?;

    let mut crop_target = source_draft.clone();
    let picture_id = id("picture-1")?;
    let picture = crop_target
        .nodes
        .iter_mut()
        .find(|node| node.node_id == picture_id)
        .ok_or("canvas picture is missing")?;
    picture
        .picture
        .as_mut()
        .ok_or("canvas picture state is missing")?
        .clip = Some(ImageClip {
        left_px: 25,
        right_px: 575,
        top_px: 40,
        bottom_px: 560,
    });
    picture.bindings.payload_sha256 = sha_label(90);
    let (crop_section, crop_evidence) = lower(
        &source_section,
        &source,
        source_draft.clone(),
        crop_target,
        DrawingCanvasOperation::SetPictureClip {
            picture_id: id("picture-1")?,
        },
        FLOW_BEFORE,
    )?;
    let crop_case = prepared_from_section(
        "P08-19-C35",
        "OBJ-031",
        "obj.crop",
        "obj-031-crop.hwpx",
        &source_package,
        &crop_section,
        vec![crop_evidence],
        "picture",
        8_251,
        18_251,
        true,
    )?;

    let mut insert_target = source_draft.clone();
    insert_target.nodes.extend([
        CanvasNode {
            node_id: id("canvas-2")?,
            native_object_id: 8_260,
            native_instance_id: 18_260,
            kind: CanvasNodeKind::Container,
            parent_id: None,
            ordinal: 1,
            group_level: 0,
            bounds: bounds(18_000, 0, 12_000, 8_000),
            visible: true,
            printable: true,
            protected: false,
            bindings: empty_bindings(),
            resource_refs: Vec::new(),
            picture: None,
        },
        CanvasNode {
            node_id: id("shape-2")?,
            native_object_id: 8_261,
            native_instance_id: 18_261,
            kind: CanvasNodeKind::Rectangle,
            parent_id: Some(id("canvas-2")?),
            ordinal: 0,
            group_level: 1,
            bounds: bounds(500, 500, 6_000, 3_000),
            visible: true,
            printable: true,
            protected: false,
            bindings: empty_bindings(),
            resource_refs: Vec::new(),
            picture: None,
        },
    ]);
    let (insert_section, insert_evidence) = lower(
        &source_section,
        &source,
        source_draft,
        insert_target,
        DrawingCanvasOperation::InsertCanvas {
            root_canvas_id: id("canvas-2")?,
            reservation: CanvasIdentityReservation {
                node_ids: vec![id("canvas-2")?, id("shape-2")?],
                native_object_ids: vec![8_260, 8_261],
                native_instance_ids: vec![18_260, 18_261],
                resource_ids: Vec::new(),
                allocator_proof_sha256: sha_label(91),
            },
        },
        FLOW_AFTER,
    )?;
    let insert_case = prepared_from_section(
        "P08-19-C36",
        "OBJ-010",
        "obj.drawing_object_insert",
        "obj-010-drawing-object-insert.hwpx",
        &source_package,
        &insert_section,
        vec![insert_evidence],
        "container",
        8_260,
        18_260,
        true,
    )?;

    Ok(vec![crop_case, insert_case])
}

fn lower(
    section: &[u8],
    source: &DrawingCanvasState,
    source_draft: DrawingCanvasStateDraft,
    target_draft: DrawingCanvasStateDraft,
    operation: DrawingCanvasOperation,
    after_flow: &str,
) -> Result<(Vec<u8>, LoweringEvidence), AnyError> {
    let capability_id = operation.capability_id();
    let limits = state_limits()?;
    let request = DrawingCanvasRequest::from_draft(
        DrawingCanvasRequestDraft {
            schema_version: DRAWING_CANVAS_SCHEMA_VERSION.to_owned(),
            request_id: "p08-19-canvas-request".to_owned(),
            source: source_draft,
            target: target_draft,
            operation,
            source_state_sha256: source.state_sha256(limits)?,
            before_document_flow_sha256: FLOW_BEFORE.to_owned(),
            after_document_flow_sha256: after_flow.to_owned(),
        },
        limits,
    )?;
    let plan = DrawingCanvasHwpxBuilder::plan(
        section,
        2,
        source,
        &request,
        FLOW_BEFORE,
        limits,
        hwpx_limits()?,
    )?;
    let plan_sha256 = plan.plan_sha256().to_owned();
    let lowered = DrawingCanvasHwpxLowerer::lower(
        &plan,
        section,
        source,
        FLOW_BEFORE,
        limits,
        hwpx_limits()?,
    )?;
    if !lowered.receipt.semantic_reopen() || !lowered.receipt.outside_island_preserved() {
        return Err("canvas lowering evidence is incomplete".into());
    }
    Ok((
        lowered.section_xml.clone(),
        LoweringEvidence {
            profile_id: DRAWING_CANVAS_HWPX_PROFILE_ID.to_owned(),
            capability_id: capability_id.to_owned(),
            plan_sha256,
            source_section_sha256: sha256(section),
            output_section_sha256: sha256(&lowered.section_xml),
            modified_unit_count: 1,
        },
    ))
}

fn base_draft(relationship_id: &str) -> Result<DrawingCanvasStateDraft, AnyError> {
    Ok(DrawingCanvasStateDraft {
        schema_version: DRAWING_CANVAS_SCHEMA_VERSION.to_owned(),
        document_id: id("p08-19-document")?,
        nodes: vec![
            CanvasNode {
                node_id: id("canvas-1")?,
                native_object_id: 8_250,
                native_instance_id: 18_250,
                kind: CanvasNodeKind::Container,
                parent_id: None,
                ordinal: 0,
                group_level: 0,
                bounds: bounds(0, 0, 17_000, 9_000),
                visible: true,
                printable: true,
                protected: false,
                bindings: bindings(10),
                resource_refs: Vec::new(),
                picture: None,
            },
            CanvasNode {
                node_id: id("picture-1")?,
                native_object_id: 8_251,
                native_instance_id: 18_251,
                kind: CanvasNodeKind::Picture,
                parent_id: Some(id("canvas-1")?),
                ordinal: 0,
                group_level: 1,
                bounds: bounds(500, 500, 7_200, 7_200),
                visible: true,
                printable: true,
                protected: false,
                bindings: bindings(20),
                resource_refs: vec![id("image-1")?],
                picture: Some(CanvasPictureState {
                    image_resource_id: id("image-1")?,
                    original_width_px: 600,
                    original_height_px: 600,
                    clip: None,
                    effects: None,
                }),
            },
            CanvasNode {
                node_id: id("shape-1")?,
                native_object_id: 8_252,
                native_instance_id: 18_252,
                kind: CanvasNodeKind::Rectangle,
                parent_id: Some(id("canvas-1")?),
                ordinal: 1,
                group_level: 1,
                bounds: bounds(8_500, 500, 7_200, 3_600),
                visible: true,
                printable: true,
                protected: true,
                bindings: bindings(30),
                resource_refs: Vec::new(),
                picture: None,
            },
        ],
        resources: vec![CanvasResource {
            resource_id: id("image-1")?,
            relationship_id: relationship_id.to_owned(),
            kind: CanvasResourceKind::EmbeddedImage,
            media_type: "image/png".to_owned(),
            content_sha256: IMAGE_SHA.to_owned(),
            byte_length: 85,
            external_target_sha256: None,
            active_content_policy: None,
        }],
        opaque_document_state_sha256: sha_label(50),
    })
}

fn canvas_section(image_package: &[u8], source: &DrawingCanvasState) -> Result<Vec<u8>, AnyError> {
    let section = section_from_package(image_package)?;
    let root = source
        .node(&id("canvas-1")?)
        .ok_or("canvas root is missing")?;
    let picture = source
        .node(&id("picture-1")?)
        .ok_or("canvas picture is missing")?;
    let shape = source
        .node(&id("shape-1")?)
        .ok_or("canvas shape is missing")?;
    let fragment = format!(
        concat!(
            "<hp:container id=\"{}\" zOrder=\"{}\" numberingType=\"NONE\" textWrap=\"TOP_AND_BOTTOM\" ",
            "textFlow=\"BOTH_SIDES\" lock=\"0\" dropcapstyle=\"None\" href=\"\" groupLevel=\"{}\" instid=\"{}\">",
            "{}<hp:shapeComment>container-opaque-marker</hp:shapeComment>{}{}</hp:container>"
        ),
        root.native_object_id,
        root.ordinal,
        root.group_level,
        root.native_instance_id,
        common(root),
        picture_fragment(picture, &source.resources()[0].relationship_id),
        rectangle_fragment(shape),
    );
    replace_direct_object(&section, "<hp:pic ", "</hp:pic>", &fragment)
}

fn common(node: &CanvasNode) -> String {
    format!(
        concat!(
            "<hp:offset x=\"{}\" y=\"{}\"/><hp:orgSz width=\"{}\" height=\"{}\"/>",
            "<hp:curSz width=\"{}\" height=\"{}\"/><hp:flip horizontal=\"0\" vertical=\"0\"/>",
            "<hp:rotationInfo angle=\"0\" centerX=\"{}\" centerY=\"{}\" rotateimage=\"1\"/>",
            "<hp:renderingInfo><hc:transMatrix e1=\"1\" e2=\"0\" e3=\"0\" e4=\"0\" e5=\"1\" e6=\"0\"/>",
            "<hc:scaMatrix e1=\"1\" e2=\"0\" e3=\"0\" e4=\"0\" e5=\"1\" e6=\"0\"/>",
            "<hc:rotMatrix e1=\"1\" e2=\"0\" e3=\"0\" e4=\"0\" e5=\"1\" e6=\"0\"/></hp:renderingInfo>",
            "<hp:sz width=\"{}\" widthRelTo=\"ABSOLUTE\" height=\"{}\" heightRelTo=\"ABSOLUTE\" protect=\"{}\"/>",
            "<hp:pos treatAsChar=\"0\" affectLSpacing=\"0\" flowWithText=\"1\" allowOverlap=\"0\" holdAnchorAndSO=\"1\" ",
            "vertRelTo=\"PARA\" horzRelTo=\"PARA\" vertAlign=\"TOP\" horzAlign=\"LEFT\" vertOffset=\"0\" horzOffset=\"0\"/>",
            "<hp:outMargin left=\"0\" right=\"0\" top=\"0\" bottom=\"0\"/>"
        ),
        node.bounds.x_hwpunit,
        node.bounds.y_hwpunit,
        node.bounds.width_hwpunit,
        node.bounds.height_hwpunit,
        node.bounds.width_hwpunit,
        node.bounds.height_hwpunit,
        node.bounds.width_hwpunit / 2,
        node.bounds.height_hwpunit / 2,
        node.bounds.width_hwpunit,
        node.bounds.height_hwpunit,
        u8::from(node.protected),
    )
}

fn picture_fragment(node: &CanvasNode, relationship_id: &str) -> String {
    format!(
        concat!(
            "<hp:pic id=\"{}\" zOrder=\"{}\" numberingType=\"PICTURE\" textWrap=\"TOP_AND_BOTTOM\" textFlow=\"BOTH_SIDES\" ",
            "lock=\"0\" dropcapstyle=\"None\" href=\"\" groupLevel=\"{}\" instid=\"{}\" reverse=\"0\">{}",
            "<hp:imgRect><hc:pt0 x=\"0\" y=\"0\"/><hc:pt1 x=\"7200\" y=\"0\"/>",
            "<hc:pt2 x=\"7200\" y=\"7200\"/><hc:pt3 x=\"0\" y=\"7200\"/></hp:imgRect>",
            "<hp:imgClip left=\"0\" right=\"600\" top=\"0\" bottom=\"600\"/>",
            "<hp:inMargin left=\"0\" right=\"0\" top=\"0\" bottom=\"0\"/>",
            "<hp:imgDim dimwidth=\"600\" dimheight=\"600\"/>",
            "<hc:img binaryItemIDRef=\"{}\" bright=\"0\" contrast=\"0\" effect=\"REAL_PIC\" alpha=\"0\"/>",
            "<hp:effects/><hp:shapeComment>picture-opaque-marker</hp:shapeComment></hp:pic>"
        ),
        node.native_object_id,
        native_ordinal(node),
        node.group_level,
        node.native_instance_id,
        common(node),
        relationship_id,
    )
}

fn rectangle_fragment(node: &CanvasNode) -> String {
    format!(
        concat!(
            "<hp:rect id=\"{}\" zOrder=\"{}\" numberingType=\"NONE\" textWrap=\"TOP_AND_BOTTOM\" textFlow=\"BOTH_SIDES\" ",
            "lock=\"0\" dropcapstyle=\"None\" href=\"\" groupLevel=\"{}\" instid=\"{}\" ratio=\"0\">{}",
            "<hp:lineShape color=\"#000000\" width=\"283\" style=\"SOLID\" endCap=\"FLAT\" headStyle=\"NORMAL\" ",
            "tailStyle=\"NORMAL\" headfill=\"0\" tailfill=\"0\" headSz=\"SMALL_SMALL\" tailSz=\"SMALL_SMALL\" ",
            "outlineStyle=\"NORMAL\" alpha=\"0\"/>",
            "<hp:shadow type=\"NONE\" color=\"#B2B2B2\" offsetX=\"0\" offsetY=\"0\" alpha=\"0\"/>",
            "<hc:pt0 x=\"0\" y=\"0\"/><hc:pt1 x=\"7200\" y=\"0\"/><hc:pt2 x=\"7200\" y=\"3600\"/>",
            "<hc:pt3 x=\"0\" y=\"3600\"/><hp:shapeComment>rectangle-opaque-marker</hp:shapeComment></hp:rect>"
        ),
        node.native_object_id,
        native_ordinal(node),
        node.group_level,
        node.native_instance_id,
        common(node),
    )
}

const fn native_ordinal(node: &CanvasNode) -> u32 {
    if node.parent_id.is_some() {
        0
    } else {
        node.ordinal
    }
}

fn state(draft: DrawingCanvasStateDraft) -> Result<DrawingCanvasState, AnyError> {
    Ok(DrawingCanvasState::from_draft(draft, state_limits()?)?)
}

fn state_limits() -> Result<DrawingCanvasLimits, AnyError> {
    Ok(DrawingCanvasLimits::new(
        DrawingCanvasLimitConfig::default(),
    )?)
}

fn hwpx_limits() -> Result<DrawingCanvasHwpxLimits, AnyError> {
    Ok(DrawingCanvasHwpxLimits::new(
        DrawingCanvasHwpxLimitConfig::default(),
    )?)
}

fn bindings(seed: u8) -> CanvasBindings {
    CanvasBindings {
        geometry_sha256: sha_label(seed),
        payload_sha256: sha_label(seed.saturating_add(1)),
        appearance_sha256: sha_label(seed.saturating_add(2)),
        composition_sha256: sha_label(seed.saturating_add(3)),
        opaque_sha256: sha_label(seed.saturating_add(4)),
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

const fn bounds(x_hwpunit: i64, y_hwpunit: i64, width: u64, height: u64) -> CanvasBounds {
    CanvasBounds {
        x_hwpunit,
        y_hwpunit,
        width_hwpunit: width,
        height_hwpunit: height,
    }
}

fn sha_label(seed: u8) -> String {
    format!("{seed:02x}").repeat(32)
}

fn id(value: &str) -> Result<LogicalId, AnyError> {
    Ok(LogicalId::parse(value)?)
}

fn attribute_value(section: &[u8], prefix: &[u8]) -> Result<String, AnyError> {
    let start = section
        .windows(prefix.len())
        .position(|window| window == prefix)
        .map(|offset| offset + prefix.len())
        .ok_or("canvas relationship attribute is missing")?;
    let end = section[start..]
        .iter()
        .position(|&byte| byte == b'\"')
        .map(|offset| start + offset)
        .ok_or("canvas relationship attribute is unterminated")?;
    Ok(std::str::from_utf8(&section[start..end])?.to_owned())
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
        .ok_or("canvas source opening is missing")?;
    let end = text[start..]
        .find(closing)
        .map(|offset| start + offset + closing.len())
        .ok_or("canvas source closing is missing")?;
    let mut output = String::with_capacity(text.len() - (end - start) + replacement.len());
    output.push_str(&text[..start]);
    output.push_str(replacement);
    output.push_str(&text[end..]);
    Ok(output.into_bytes())
}
