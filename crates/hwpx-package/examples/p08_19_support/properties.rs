use domain_ir::{
    BasicShapeLimits, FreeformShape, ImageProperties, LogicalId, OBJECT_GEOMETRY_SCHEMA_VERSION,
    OBJECT_PROPERTIES_SCHEMA_VERSION, ObjectAffineMatrix, ObjectAltText, ObjectAnchor,
    ObjectCaption, ObjectCaptionNumbering, ObjectCaptionSide, ObjectComponentGeometry,
    ObjectExtent, ObjectFlip, ObjectGeometryLimits, ObjectGeometryStateDraft,
    ObjectHeightReference, ObjectHorizontalAlignment, ObjectHorizontalReference, ObjectHyperlink,
    ObjectKind, ObjectNumberingType, ObjectOuterMargins, ObjectPoint, ObjectPosition,
    ObjectPropertiesBuilder, ObjectPropertiesLimitConfig, ObjectPropertiesLimits,
    ObjectPropertiesOperation, ObjectPropertiesRequest, ObjectPropertiesRequestDraft,
    ObjectPropertiesState, ObjectPropertiesStateDraft, ObjectPropertyKind, ObjectPropertyMargins,
    ObjectRotation, ObjectSize, ObjectTextBoxVerticalAlignment, ObjectTextFlow, ObjectTextWrap,
    ObjectTransform, ObjectVerticalAlignment, ObjectVerticalReference, ObjectWidthReference,
    ObjectWrap, OpaqueObjectProperty, SHAPE_POINTS_SCHEMA_VERSION, ShapePoint, ShapePointsBuilder,
    ShapePointsLimitConfig, ShapePointsLimits, ShapePointsRequest, ShapePointsRequestDraft,
    ShapePointsState, ShapePointsStateDraft, TextBoxDirection, TextBoxProperties,
};
use hwpx_package::{
    ObjectCommonPropertiesHwpxBuilder, ObjectCommonPropertiesHwpxLimits,
    ObjectCommonPropertiesHwpxLowerer, ObjectCommonPropertiesHwpxLoweringReceipt,
    ObjectGeometryHwpxLimits, ObjectHyperlinkHwpxBuilder, ObjectHyperlinkHwpxLimits,
    ObjectHyperlinkHwpxLowerer, ObjectHyperlinkHwpxLoweringReceipt, ShapePointsHwpxBuilder,
    ShapePointsHwpxLimits, ShapePointsHwpxLowerer, ShapePointsHwpxLoweringReceipt,
    TextBoxPropertiesHwpxBuilder, TextBoxPropertiesHwpxLimits, TextBoxPropertiesHwpxLowerer,
    TextBoxPropertiesHwpxLoweringReceipt,
};

use super::common::{
    AnyError, FLOW_AFTER, FLOW_BEFORE, LoweringEvidence, PreparedCase, hex, package_with_section,
    prepared_from_section, section_from_package,
};

const STATE_C: &str = "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc";
const STATE_D: &str = "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd";
const STATE_E: &str = "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee";
const STATE_F: &str = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff";
const STATE_0: &str = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef";

pub fn cases(
    shape_package: &[u8],
    image_package: &[u8],
    text_box_package: &[u8],
    freeform_package: &[u8],
) -> Result<Vec<PreparedCase>, AnyError> {
    Ok(vec![
        margin_caption_case(shape_package)?,
        text_box_properties_case(text_box_package)?,
        image_properties_case(image_package)?,
        shape_points_case(freeform_package)?,
        super::geometry::protect_case(shape_package)?,
        printable_case(shape_package)?,
        alt_text_case(image_package)?,
        hyperlink_case(shape_package)?,
    ])
}

fn margin_caption_case(shape_package: &[u8]) -> Result<PreparedCase, AnyError> {
    let section = section_from_package(shape_package)?;
    let source_caption = ObjectCaption {
        side: ObjectCaptionSide::Top,
        gap_hwpunit: 100,
        width_hwpunit: 1_100,
        numbering: ObjectCaptionNumbering::None,
        label: "P08 ".to_owned(),
        text: "before".to_owned(),
    };
    let target_caption = ObjectCaption {
        side: ObjectCaptionSide::Bottom,
        gap_hwpunit: 200,
        width_hwpunit: 1_200,
        numbering: ObjectCaptionNumbering::None,
        label: "P08 ".to_owned(),
        text: "after".to_owned(),
    };
    let caption = concat!(
        "<hp:caption side=\"TOP\" fullSz=\"0\" width=\"1100\" gap=\"100\" lastWidth=\"1100\">",
        "<hp:subList><hp:p><hp:run><hp:t>P08 before</hp:t></hp:run></hp:p></hp:subList>",
        "</hp:caption>"
    );
    let source_section = insert_before_object_close(&section, "</hp:rect>", caption)?;
    let source_package = package_with_section(shape_package, &source_section)?;
    let source_state = object_state(
        ObjectPropertyKind::BasicShape,
        8_101,
        18_101,
        margins(100),
        Some(source_caption),
        None,
        None,
        true,
        None,
    )?;
    let operation = ObjectPropertiesOperation::SetMarginCaption {
        outer_margins: margins(250),
        caption: Some(target_caption),
    };
    let (output, receipt) = lower_common(&source_section, 0, &source_state, operation)?;
    prepared_from_section(
        "P08-19-C22",
        "OBJ-019",
        "obj.margin_caption",
        "obj-019-margin-caption.hwpx",
        &source_package,
        &output,
        vec![common_evidence(&receipt)],
        "rectangle",
        8_101,
        18_101,
        false,
    )
}

fn text_box_properties_case(text_box_package: &[u8]) -> Result<PreparedCase, AnyError> {
    let section = section_from_package(text_box_package)?;
    let source_properties = TextBoxProperties {
        margins: ObjectPropertyMargins {
            left_hwpunit: 400,
            right_hwpunit: 400,
            top_hwpunit: 300,
            bottom_hwpunit: 300,
        },
        vertical_alignment: ObjectTextBoxVerticalAlignment::Center,
        direction: TextBoxDirection::Horizontal,
    };
    let target = TextBoxProperties {
        margins: ObjectPropertyMargins {
            left_hwpunit: 800,
            right_hwpunit: 600,
            top_hwpunit: 500,
            bottom_hwpunit: 700,
        },
        vertical_alignment: ObjectTextBoxVerticalAlignment::Bottom,
        direction: TextBoxDirection::VerticalRightToLeft,
    };
    let source_state = object_state(
        ObjectPropertyKind::TextBox,
        8_107,
        18_107,
        margins(100),
        None,
        Some(source_properties),
        None,
        true,
        None,
    )?;
    let limits = property_limits()?;
    let request = ObjectPropertiesRequest::from_draft(
        ObjectPropertiesRequestDraft {
            schema_version: OBJECT_PROPERTIES_SCHEMA_VERSION.to_owned(),
            request_id: LogicalId::parse("p08-19-textbox-properties-request")?,
            expected_source_state_sha256: source_state.canonical_sha256(limits)?,
            expected_document_flow_sha256: FLOW_BEFORE.to_owned(),
            target_document_flow_sha256: FLOW_AFTER.to_owned(),
            operation: ObjectPropertiesOperation::SetTextBoxProperties { properties: target },
        },
        &source_state,
        FLOW_BEFORE,
        limits,
    )?;
    let domain = ObjectPropertiesBuilder::plan(&source_state, &request, FLOW_BEFORE, limits)?;
    let plan = TextBoxPropertiesHwpxBuilder::plan(
        &section,
        0,
        &domain,
        FLOW_BEFORE,
        limits,
        TextBoxPropertiesHwpxLimits::default(),
    )?;
    let (output, receipt) = TextBoxPropertiesHwpxLowerer::lower_in_section_with_receipt(
        &section,
        &plan,
        FLOW_BEFORE,
        limits,
        TextBoxPropertiesHwpxLimits::default(),
    )?;
    prepared_from_section(
        "P08-19-C23",
        "OBJ-025",
        "obj.textbox_properties",
        "obj-025-textbox-properties.hwpx",
        text_box_package,
        &output,
        vec![text_box_evidence(&receipt)],
        "textbox",
        8_107,
        18_107,
        false,
    )
}

fn image_properties_case(image_package: &[u8]) -> Result<PreparedCase, AnyError> {
    let (source_package, source_section, source_image) = normalized_image_source(image_package)?;
    let source_state = object_state(
        ObjectPropertyKind::Picture,
        8_102,
        18_102,
        margins(0),
        None,
        None,
        Some(source_image),
        true,
        Some(ObjectAltText {
            title: String::new(),
            description: "P08-18 embedded checker image".to_owned(),
        }),
    )?;
    let target = ImageProperties {
        original_width_px: 300,
        original_height_px: 300,
        horizontal_scale_millionths: 500_000,
        vertical_scale_millionths: 500_000,
        horizontal_dpi: 300,
        vertical_dpi: 300,
    };
    let (output, receipt) = lower_common(
        &source_section,
        0,
        &source_state,
        ObjectPropertiesOperation::SetImageProperties { properties: target },
    )?;
    prepared_from_section(
        "P08-19-C24",
        "OBJ-030",
        "obj.image_properties",
        "obj-030-image-properties.hwpx",
        &source_package,
        &output,
        vec![common_evidence(&receipt)],
        "picture",
        8_102,
        18_102,
        true,
    )
}

fn shape_points_case(freeform_package: &[u8]) -> Result<PreparedCase, AnyError> {
    let section = section_from_package(freeform_package)?;
    let source_freeform = polygon(&[(0, 0), (7_200, 0), (3_600, 3_600)]);
    let target_freeform = polygon(&[(0, 0), (7_200, 0), (7_200, 3_600), (0, 3_600)]);
    let source_state = ShapePointsState::from_draft(
        ShapePointsStateDraft {
            schema_version: SHAPE_POINTS_SCHEMA_VERSION.to_owned(),
            geometry: freeform_geometry()?,
            freeform: source_freeform,
            appearance_state_sha256: STATE_C.to_owned(),
            property_state_sha256: STATE_D.to_owned(),
            resource_inventory_sha256: STATE_E.to_owned(),
            embedded_content_state_sha256: STATE_F.to_owned(),
            opaque_state_sha256: STATE_0.to_owned(),
        },
        ObjectGeometryLimits::default(),
        BasicShapeLimits::default(),
        shape_points_limits()?,
    )?;
    let request = ShapePointsRequest::from_draft(
        ShapePointsRequestDraft {
            schema_version: SHAPE_POINTS_SCHEMA_VERSION.to_owned(),
            request_id: LogicalId::parse("p08-19-shape-points-request")?,
            expected_source_state_sha256: source_state.canonical_sha256(shape_points_limits()?)?,
            expected_document_flow_sha256: FLOW_BEFORE.to_owned(),
            target_document_flow_sha256: FLOW_AFTER.to_owned(),
            target_freeform,
        },
        &source_state,
        FLOW_BEFORE,
        BasicShapeLimits::default(),
        shape_points_limits()?,
    )?;
    let domain = ShapePointsBuilder::plan(
        &source_state,
        &request,
        FLOW_BEFORE,
        BasicShapeLimits::default(),
        shape_points_limits()?,
    )?;
    let plan = ShapePointsHwpxBuilder::plan(
        &section,
        0,
        &domain,
        FLOW_BEFORE,
        ObjectGeometryLimits::default(),
        ObjectGeometryHwpxLimits::default(),
        BasicShapeLimits::default(),
        shape_points_limits()?,
        ShapePointsHwpxLimits::default(),
    )?;
    let (output, receipt) = ShapePointsHwpxLowerer::lower_in_section_with_receipt(
        &section,
        &plan,
        FLOW_BEFORE,
        ObjectGeometryLimits::default(),
        ObjectGeometryHwpxLimits::default(),
        BasicShapeLimits::default(),
        shape_points_limits()?,
        ShapePointsHwpxLimits::default(),
    )?;
    prepared_from_section(
        "P08-19-C25",
        "OBJ-043",
        "obj.shape_edit_points",
        "obj-043-shape-edit-points.hwpx",
        freeform_package,
        &output,
        vec![shape_points_evidence(&receipt)],
        "polygon",
        8_142,
        18_142,
        false,
    )
}

fn printable_case(shape_package: &[u8]) -> Result<PreparedCase, AnyError> {
    let section = section_from_package(shape_package)?;
    let form = concat!(
        "<hp:edit id=\"8146\" zOrder=\"0\" numberingType=\"NONE\" textWrap=\"TOP_AND_BOTTOM\" ",
        "textFlow=\"BOTH_SIDES\" lock=\"0\" dropcapstyle=\"None\" href=\"\" groupLevel=\"0\" instid=\"18146\" ",
        "name=\"p08field\" foreColor=\"#000000\" backColor=\"#FFFFFF\" groupName=\"\" tabStop=\"1\" editable=\"1\" ",
        "tabOrder=\"0\" enabled=\"1\" borderTypeIDRef=\"0\" drawFrame=\"1\" printable=\"1\" command=\"\" ",
        "multiLine=\"0\" passwordChar=\"*\" maxLength=\"64\" scrollBars=\"NONE\" tabKeyBehavior=\"NEXT_OBJECT\" ",
        "numOnly=\"0\" readOnly=\"0\" alignText=\"LEFT\">",
        "<hp:sz width=\"10800\" widthRelTo=\"ABSOLUTE\" height=\"5400\" heightRelTo=\"ABSOLUTE\" protect=\"0\"/>",
        "<hp:pos treatAsChar=\"1\" affectLSpacing=\"1\" flowWithText=\"1\" allowOverlap=\"0\" holdAnchorAndSO=\"0\" ",
        "vertRelTo=\"PARA\" horzRelTo=\"COLUMN\" vertAlign=\"TOP\" horzAlign=\"LEFT\" vertOffset=\"0\" horzOffset=\"0\"/>",
        "<hp:outMargin left=\"0\" right=\"0\" top=\"0\" bottom=\"0\"/>",
        "<hp:formCharPr charPrIDRef=\"0\" followContext=\"0\" autoSz=\"0\" wordWrap=\"1\"/>",
        "<hp:text>P08 FORM</hp:text></hp:edit>"
    );
    let source_section = replace_direct_object(&section, "<hp:rect ", "</hp:rect>", form)?;
    let source_package = package_with_section(shape_package, &source_section)?;
    let source_state = object_state(
        ObjectPropertyKind::FormObject,
        8_146,
        18_146,
        margins(0),
        None,
        None,
        None,
        true,
        None,
    )?;
    let (output, receipt) = lower_common(
        &source_section,
        0,
        &source_state,
        ObjectPropertiesOperation::SetPrintable { enabled: false },
    )?;
    prepared_from_section(
        "P08-19-C27",
        "OBJ-046",
        "obj.printable",
        "obj-046-printable.hwpx",
        &source_package,
        &output,
        vec![common_evidence(&receipt)],
        "form_object",
        8_146,
        18_146,
        false,
    )
}

fn alt_text_case(image_package: &[u8]) -> Result<PreparedCase, AnyError> {
    let (source_package, source_section, source_image) = normalized_image_source(image_package)?;
    let source_state = object_state(
        ObjectPropertyKind::Picture,
        8_102,
        18_102,
        margins(0),
        None,
        None,
        Some(source_image),
        true,
        Some(ObjectAltText {
            title: String::new(),
            description: "P08-18 embedded checker image".to_owned(),
        }),
    )?;
    let (output, receipt) = lower_common(
        &source_section,
        0,
        &source_state,
        ObjectPropertiesOperation::SetAltText {
            value: Some(ObjectAltText {
                title: String::new(),
                description: "P08-19 verified alternative description".to_owned(),
            }),
        },
    )?;
    prepared_from_section(
        "P08-19-C28",
        "OBJ-047",
        "obj.alt_text",
        "obj-047-alt-text.hwpx",
        &source_package,
        &output,
        vec![common_evidence(&receipt)],
        "picture",
        8_102,
        18_102,
        true,
    )
}

fn hyperlink_case(shape_package: &[u8]) -> Result<PreparedCase, AnyError> {
    let section = section_from_package(shape_package)?;
    let source_state = object_state(
        ObjectPropertyKind::BasicShape,
        8_101,
        18_101,
        margins(100),
        None,
        None,
        None,
        true,
        None,
    )?;
    let limits = property_limits()?;
    let request = ObjectPropertiesRequest::from_draft(
        ObjectPropertiesRequestDraft {
            schema_version: OBJECT_PROPERTIES_SCHEMA_VERSION.to_owned(),
            request_id: LogicalId::parse("p08-19-object-hyperlink-request")?,
            expected_source_state_sha256: source_state.canonical_sha256(limits)?,
            expected_document_flow_sha256: FLOW_BEFORE.to_owned(),
            target_document_flow_sha256: FLOW_AFTER.to_owned(),
            operation: ObjectPropertiesOperation::SetObjectHyperlink {
                value: Some(ObjectHyperlink::Https {
                    uri: "https://example.test/p08-object".to_owned(),
                }),
            },
        },
        &source_state,
        FLOW_BEFORE,
        limits,
    )?;
    let domain = ObjectPropertiesBuilder::plan(&source_state, &request, FLOW_BEFORE, limits)?;
    let plan = ObjectHyperlinkHwpxBuilder::plan(
        &section,
        0,
        &domain,
        FLOW_BEFORE,
        limits,
        ObjectHyperlinkHwpxLimits::default(),
    )?;
    let (output, receipt) = ObjectHyperlinkHwpxLowerer::lower_in_section_with_receipt(
        &section,
        &plan,
        FLOW_BEFORE,
        limits,
        ObjectHyperlinkHwpxLimits::default(),
    )?;
    prepared_from_section(
        "P08-19-C37",
        "OBJ-048",
        "obj.object_hyperlink",
        "obj-048-object-hyperlink.hwpx",
        shape_package,
        &output,
        vec![hyperlink_evidence(&receipt)],
        "rectangle",
        8_101,
        18_101,
        false,
    )
}

fn normalized_image_source(
    image_package: &[u8],
) -> Result<(Vec<u8>, Vec<u8>, ImageProperties), AnyError> {
    let section = section_from_package(image_package)?;
    let text = std::str::from_utf8(&section)?;
    if text
        .match_indices("<hp:curSz width=\"7200\" height=\"7200\"/>")
        .count()
        != 1
    {
        return Err("image source current size was not normalized".into());
    }
    Ok((
        image_package.to_vec(),
        section,
        ImageProperties {
            original_width_px: 600,
            original_height_px: 600,
            horizontal_scale_millionths: 1_000_000,
            vertical_scale_millionths: 1_000_000,
            horizontal_dpi: 600,
            vertical_dpi: 600,
        },
    ))
}

fn lower_common(
    section: &[u8],
    object_ordinal: usize,
    source: &ObjectPropertiesState,
    operation: ObjectPropertiesOperation,
) -> Result<(Vec<u8>, ObjectCommonPropertiesHwpxLoweringReceipt), AnyError> {
    let limits = property_limits()?;
    let request = ObjectPropertiesRequest::from_draft(
        ObjectPropertiesRequestDraft {
            schema_version: OBJECT_PROPERTIES_SCHEMA_VERSION.to_owned(),
            request_id: LogicalId::parse("p08-19-common-properties-request")?,
            expected_source_state_sha256: source.canonical_sha256(limits)?,
            expected_document_flow_sha256: FLOW_BEFORE.to_owned(),
            target_document_flow_sha256: FLOW_AFTER.to_owned(),
            operation,
        },
        source,
        FLOW_BEFORE,
        limits,
    )?;
    let domain = ObjectPropertiesBuilder::plan(source, &request, FLOW_BEFORE, limits)?;
    let plan = ObjectCommonPropertiesHwpxBuilder::plan(
        section,
        object_ordinal,
        &domain,
        FLOW_BEFORE,
        limits,
        ObjectCommonPropertiesHwpxLimits::default(),
    )?;
    Ok(
        ObjectCommonPropertiesHwpxLowerer::lower_in_section_with_receipt(
            section,
            &plan,
            FLOW_BEFORE,
            limits,
            ObjectCommonPropertiesHwpxLimits::default(),
        )?,
    )
}

#[allow(clippy::too_many_arguments)]
fn object_state(
    kind: ObjectPropertyKind,
    native_object_id: u32,
    native_instance_id: u32,
    outer_margins: ObjectPropertyMargins,
    caption: Option<ObjectCaption>,
    text_box: Option<TextBoxProperties>,
    image: Option<ImageProperties>,
    printable: bool,
    alt_text: Option<ObjectAltText>,
) -> Result<ObjectPropertiesState, AnyError> {
    Ok(ObjectPropertiesState::from_draft(
        ObjectPropertiesStateDraft {
            schema_version: OBJECT_PROPERTIES_SCHEMA_VERSION.to_owned(),
            logical_object_id: LogicalId::parse(format!("object-{native_object_id}"))?,
            native_object_id,
            native_instance_id,
            object_kind: kind,
            geometry_state_sha256: FLOW_BEFORE.to_owned(),
            appearance_state_sha256: FLOW_AFTER.to_owned(),
            payload_state_sha256: STATE_C.to_owned(),
            resource_inventory_sha256: STATE_D.to_owned(),
            embedded_content_state_sha256: STATE_E.to_owned(),
            outer_margins,
            caption,
            text_box,
            image,
            aspect_locked: false,
            protected: false,
            printable,
            alt_text,
            hyperlink: None,
            opaque_properties: vec![OpaqueObjectProperty {
                namespace: "hp".to_owned(),
                name: "p08-private".to_owned(),
                value: "opaque".to_owned(),
            }],
        },
        property_limits()?,
    )?)
}

fn freeform_geometry() -> Result<ObjectGeometryStateDraft, AnyError> {
    Ok(ObjectGeometryStateDraft {
        schema_version: OBJECT_GEOMETRY_SCHEMA_VERSION.to_owned(),
        object_id: LogicalId::parse("object-8142")?,
        object_kind: ObjectKind::Polygon,
        native_object_id: 8_142,
        native_instance_id: 18_142,
        z_order: 1,
        numbering_type: ObjectNumberingType::None,
        locked: false,
        size: ObjectSize {
            width_hwpunit: 10_800,
            width_reference: ObjectWidthReference::Absolute,
            height_hwpunit: 5_400,
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
            vertical_offset_hwpunit: 1_000,
        },
        wrap: ObjectWrap {
            text_wrap: ObjectTextWrap::TopAndBottom,
            text_flow: ObjectTextFlow::BothSides,
        },
        outer_margins: ObjectOuterMargins {
            left_hwpunit: 100,
            right_hwpunit: 100,
            top_hwpunit: 100,
            bottom_hwpunit: 100,
        },
        component: ObjectComponentGeometry {
            offset: ObjectPoint {
                x_hwpunit: 0,
                y_hwpunit: 0,
            },
            original_size: ObjectExtent {
                width_hwpunit: 10_800,
                height_hwpunit: 5_400,
            },
            current_size: ObjectExtent {
                width_hwpunit: 10_800,
                height_hwpunit: 5_400,
            },
            flip: ObjectFlip {
                horizontal: false,
                vertical: false,
            },
            rotation: ObjectRotation {
                angle_degrees: 0,
                center_x_hwpunit: 5_400,
                center_y_hwpunit: 2_700,
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

const fn identity() -> ObjectAffineMatrix {
    ObjectAffineMatrix::IDENTITY
}

fn polygon(points: &[(i32, i32)]) -> FreeformShape {
    FreeformShape::Polygon {
        points: points
            .iter()
            .map(|&(x_hwpunit, y_hwpunit)| ShapePoint {
                x_hwpunit,
                y_hwpunit,
            })
            .collect(),
    }
}

const fn margins(seed: u32) -> ObjectPropertyMargins {
    ObjectPropertyMargins {
        left_hwpunit: seed,
        right_hwpunit: seed,
        top_hwpunit: seed,
        bottom_hwpunit: seed,
    }
}

fn property_limits() -> Result<ObjectPropertiesLimits, AnyError> {
    Ok(ObjectPropertiesLimits::new(
        ObjectPropertiesLimitConfig::default(),
    )?)
}

fn shape_points_limits() -> Result<ShapePointsLimits, AnyError> {
    Ok(ShapePointsLimits::new(ShapePointsLimitConfig::default())?)
}

fn insert_before_object_close(
    section: &[u8],
    closing: &str,
    fragment: &str,
) -> Result<Vec<u8>, AnyError> {
    let text = std::str::from_utf8(section)?;
    let position = text.find(closing).ok_or("object closing is missing")?;
    let mut output = String::with_capacity(text.len() + fragment.len());
    output.push_str(&text[..position]);
    output.push_str(fragment);
    output.push_str(&text[position..]);
    Ok(output.into_bytes())
}

fn replace_direct_object(
    section: &[u8],
    opening: &str,
    closing: &str,
    replacement: &str,
) -> Result<Vec<u8>, AnyError> {
    let text = std::str::from_utf8(section)?;
    let start = text.find(opening).ok_or("object opening is missing")?;
    let end = text[start..]
        .find(closing)
        .map(|offset| start + offset + closing.len())
        .ok_or("object closing is missing")?;
    let mut output = String::with_capacity(text.len() - (end - start) + replacement.len());
    output.push_str(&text[..start]);
    output.push_str(replacement);
    output.push_str(&text[end..]);
    Ok(output.into_bytes())
}

fn common_evidence(receipt: &ObjectCommonPropertiesHwpxLoweringReceipt) -> LoweringEvidence {
    LoweringEvidence {
        profile_id: receipt.profile_id.to_owned(),
        capability_id: receipt.capability_id.to_owned(),
        plan_sha256: receipt.plan_sha256.clone(),
        source_section_sha256: hex(receipt.source_section_sha256),
        output_section_sha256: hex(receipt.output_section_sha256),
        modified_unit_count: receipt.modified_span_count,
    }
}

fn text_box_evidence(receipt: &TextBoxPropertiesHwpxLoweringReceipt) -> LoweringEvidence {
    LoweringEvidence {
        profile_id: receipt.profile_id.to_owned(),
        capability_id: receipt.capability_id.to_owned(),
        plan_sha256: receipt.plan_sha256.clone(),
        source_section_sha256: hex(receipt.source_section_sha256),
        output_section_sha256: hex(receipt.output_section_sha256),
        modified_unit_count: receipt.modified_attribute_count,
    }
}

fn shape_points_evidence(receipt: &ShapePointsHwpxLoweringReceipt) -> LoweringEvidence {
    LoweringEvidence {
        profile_id: receipt.profile_id.to_owned(),
        capability_id: receipt.capability_id.to_owned(),
        plan_sha256: receipt.plan_sha256.clone(),
        source_section_sha256: hex(receipt.source_section_sha256),
        output_section_sha256: hex(receipt.output_section_sha256),
        modified_unit_count: 1,
    }
}

fn hyperlink_evidence(receipt: &ObjectHyperlinkHwpxLoweringReceipt) -> LoweringEvidence {
    LoweringEvidence {
        profile_id: receipt.profile_id.to_owned(),
        capability_id: receipt.capability_id.to_owned(),
        plan_sha256: receipt.plan_sha256.clone(),
        source_section_sha256: hex(receipt.source_section_sha256),
        output_section_sha256: hex(receipt.output_section_sha256),
        modified_unit_count: receipt.modified_attribute_count,
    }
}
