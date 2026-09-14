#![allow(clippy::expect_used)] // Exact fixtures keep failures local and readable.

use domain_ir::{
    ImageProperties, LogicalId, OBJECT_PROPERTIES_SCHEMA_VERSION, ObjectAltText, ObjectCaption,
    ObjectCaptionNumbering, ObjectCaptionSide, ObjectPropertiesBuilder,
    ObjectPropertiesLimitConfig, ObjectPropertiesLimits, ObjectPropertiesOperation,
    ObjectPropertiesRequest, ObjectPropertiesRequestDraft, ObjectPropertiesState,
    ObjectPropertiesStateDraft, ObjectPropertyKind, ObjectPropertyMargins, OpaqueObjectProperty,
};
use hwpx_package::{
    ObjectCommonPropertiesHwpxBuilder, ObjectCommonPropertiesHwpxError,
    ObjectCommonPropertiesHwpxLimitConfig, ObjectCommonPropertiesHwpxLimits,
    ObjectCommonPropertiesHwpxLowerer, ObjectCommonPropertiesHwpxReader,
};

const FLOW_A: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const FLOW_B: &str = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
const STATE_C: &str = "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc";
const STATE_D: &str = "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd";
const STATE_E: &str = "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee";
const NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";

fn state_limits() -> ObjectPropertiesLimits {
    ObjectPropertiesLimits::new(ObjectPropertiesLimitConfig::default()).expect("state limits")
}

fn hwpx_limits() -> ObjectCommonPropertiesHwpxLimits {
    ObjectCommonPropertiesHwpxLimits::new(ObjectCommonPropertiesHwpxLimitConfig::default())
        .expect("HWPX limits")
}

fn margins(seed: u32) -> ObjectPropertyMargins {
    ObjectPropertyMargins {
        left_hwpunit: seed,
        right_hwpunit: seed + 1,
        top_hwpunit: seed + 2,
        bottom_hwpunit: seed + 3,
    }
}

fn caption(side: ObjectCaptionSide, seed: u32, label: &str, text: &str) -> ObjectCaption {
    ObjectCaption {
        side,
        gap_hwpunit: seed,
        width_hwpunit: seed + 1_000,
        numbering: ObjectCaptionNumbering::None,
        label: label.to_owned(),
        text: text.to_owned(),
    }
}

#[allow(clippy::too_many_arguments)]
fn state(
    kind: ObjectPropertyKind,
    native_object_id: u32,
    native_instance_id: u32,
    outer_margins: ObjectPropertyMargins,
    object_caption: Option<ObjectCaption>,
    image: Option<ImageProperties>,
    printable: bool,
    alt_text: Option<ObjectAltText>,
) -> ObjectPropertiesState {
    ObjectPropertiesState::from_draft(
        ObjectPropertiesStateDraft {
            schema_version: OBJECT_PROPERTIES_SCHEMA_VERSION.to_owned(),
            logical_object_id: LogicalId::parse(format!("object-{native_object_id}"))
                .expect("object id"),
            native_object_id,
            native_instance_id,
            object_kind: kind,
            geometry_state_sha256: FLOW_A.to_owned(),
            appearance_state_sha256: FLOW_B.to_owned(),
            payload_state_sha256: STATE_C.to_owned(),
            resource_inventory_sha256: STATE_D.to_owned(),
            embedded_content_state_sha256: STATE_E.to_owned(),
            outer_margins,
            caption: object_caption,
            text_box: None,
            image,
            aspect_locked: false,
            protected: false,
            printable,
            alt_text,
            hyperlink: None,
            opaque_properties: vec![OpaqueObjectProperty {
                namespace: "hp".to_owned(),
                name: "private".to_owned(),
                value: "opaque".to_owned(),
            }],
        },
        state_limits(),
    )
    .expect("state")
}

fn domain_plan(
    source: &ObjectPropertiesState,
    operation: ObjectPropertiesOperation,
) -> domain_ir::ObjectPropertiesPlan {
    let request = ObjectPropertiesRequest::from_draft(
        ObjectPropertiesRequestDraft {
            schema_version: OBJECT_PROPERTIES_SCHEMA_VERSION.to_owned(),
            request_id: LogicalId::parse("request-1").expect("request id"),
            expected_source_state_sha256: source
                .canonical_sha256(state_limits())
                .expect("state digest"),
            expected_document_flow_sha256: FLOW_A.to_owned(),
            target_document_flow_sha256: FLOW_B.to_owned(),
            operation,
        },
        source,
        FLOW_A,
        state_limits(),
    )
    .expect("request");
    ObjectPropertiesBuilder::plan(source, &request, FLOW_A, state_limits()).expect("domain plan")
}

fn section(object: &str) -> Vec<u8> {
    format!("<hp:sec xmlns:hp=\"{NS}\"><hp:p><hp:run>{object}</hp:run></hp:p></hp:sec>")
        .into_bytes()
}

#[test]
fn margin_and_existing_plain_caption_patch_exact_native_spans() {
    let source_caption = caption(ObjectCaptionSide::Top, 100, "Figure ", "before & one");
    let target_caption = caption(ObjectCaptionSide::Bottom, 200, "Figure ", "after < two");
    let source_state = state(
        ObjectPropertyKind::BasicShape,
        41,
        99,
        margins(10),
        Some(source_caption.clone()),
        None,
        true,
        None,
    );
    let xml = section(&format!(
        concat!(
            "<hp:rect id=\"41\" instid=\"99\">",
            "<hp:outMargin left=\"10\" right=\"11\" top=\"12\" bottom=\"13\"/>",
            "<hp:caption side=\"TOP\" fullSz=\"0\" width=\"1100\" gap=\"100\" lastWidth=\"1100\">",
            "<hp:subList><hp:p><hp:run><hp:t>{}</hp:t></hp:run></hp:p></hp:subList>",
            "</hp:caption></hp:rect>"
        ),
        "Figure before &amp; one"
    ));
    let plan = domain_plan(
        &source_state,
        ObjectPropertiesOperation::SetMarginCaption {
            outer_margins: margins(20),
            caption: Some(target_caption),
        },
    );
    let hwpx_plan = ObjectCommonPropertiesHwpxBuilder::plan(
        &xml,
        0,
        &plan,
        FLOW_A,
        state_limits(),
        hwpx_limits(),
    )
    .expect("HWPX plan");
    let (output, receipt) = ObjectCommonPropertiesHwpxLowerer::lower_in_section_with_receipt(
        &xml,
        &hwpx_plan,
        FLOW_A,
        state_limits(),
        hwpx_limits(),
    )
    .expect("lower");
    let output_text = String::from_utf8(output.clone()).expect("UTF-8");
    assert!(
        output_text.contains("<hp:outMargin left=\"20\" right=\"21\" top=\"22\" bottom=\"23\"/>")
    );
    assert!(
        output_text
            .contains("side=\"BOTTOM\" fullSz=\"0\" width=\"1200\" gap=\"200\" lastWidth=\"1200\"")
    );
    assert!(output_text.contains("<hp:t>Figure after &lt; two</hp:t>"));
    assert_eq!(receipt.capability_id, "obj.margin_caption");
    assert_eq!(receipt.modified_span_count, 9);
    ObjectCommonPropertiesHwpxReader::read_in_section(
        &output,
        0,
        "obj.margin_caption",
        plan.target_state(),
        state_limits(),
        hwpx_limits(),
    )
    .expect("target readback");
}

#[test]
fn picture_dimensions_scale_and_dpi_patch_as_one_bound_operation() {
    let source_image = ImageProperties {
        original_width_px: 600,
        original_height_px: 300,
        horizontal_scale_millionths: 500_000,
        vertical_scale_millionths: 500_000,
        horizontal_dpi: 300,
        vertical_dpi: 300,
    };
    let target_image = ImageProperties {
        original_width_px: 1_200,
        original_height_px: 600,
        horizontal_scale_millionths: 1_000_000,
        vertical_scale_millionths: 1_000_000,
        horizontal_dpi: 600,
        vertical_dpi: 600,
    };
    let source_state = state(
        ObjectPropertyKind::Picture,
        42,
        100,
        margins(0),
        None,
        Some(source_image),
        true,
        None,
    );
    let xml = section(concat!(
        "<hp:pic id=\"42\" instid=\"100\">",
        "<hp:orgSz width=\"14400\" height=\"7200\"/>",
        "<hp:curSz width=\"7200\" height=\"3600\"/>",
        "<hp:imgDim dimwidth=\"600\" dimheight=\"300\"/>",
        "</hp:pic>"
    ));
    let plan = domain_plan(
        &source_state,
        ObjectPropertiesOperation::SetImageProperties {
            properties: target_image,
        },
    );
    let hwpx_plan = ObjectCommonPropertiesHwpxBuilder::plan(
        &xml,
        0,
        &plan,
        FLOW_A,
        state_limits(),
        hwpx_limits(),
    )
    .expect("HWPX plan");
    let (output, receipt) = ObjectCommonPropertiesHwpxLowerer::lower_in_section_with_receipt(
        &xml,
        &hwpx_plan,
        FLOW_A,
        state_limits(),
        hwpx_limits(),
    )
    .expect("lower");
    let output_text = String::from_utf8(output).expect("UTF-8");
    assert!(output_text.contains("<hp:curSz width=\"14400\" height=\"7200\"/>"));
    assert!(output_text.contains("<hp:imgDim dimwidth=\"1200\" dimheight=\"600\"/>"));
    assert_eq!(receipt.capability_id, "obj.image_properties");
    assert_eq!(receipt.modified_span_count, 4);
}

#[test]
fn form_printability_uses_only_the_form_root_attribute() {
    let source_state = state(
        ObjectPropertyKind::FormObject,
        43,
        101,
        margins(0),
        None,
        None,
        true,
        None,
    );
    let xml = section(
        "<hp:edit id=\"43\" instid=\"101\" printable=\"1\" name=\"field\"><hp:text>value</hp:text></hp:edit>",
    );
    let plan = domain_plan(
        &source_state,
        ObjectPropertiesOperation::SetPrintable { enabled: false },
    );
    let hwpx_plan = ObjectCommonPropertiesHwpxBuilder::plan(
        &xml,
        0,
        &plan,
        FLOW_A,
        state_limits(),
        hwpx_limits(),
    )
    .expect("HWPX plan");
    let (output, receipt) = ObjectCommonPropertiesHwpxLowerer::lower_in_section_with_receipt(
        &xml,
        &hwpx_plan,
        FLOW_A,
        state_limits(),
        hwpx_limits(),
    )
    .expect("lower");
    assert!(
        String::from_utf8(output)
            .expect("UTF-8")
            .contains("printable=\"0\"")
    );
    assert_eq!(receipt.capability_id, "obj.printable");
    assert_eq!(receipt.modified_span_count, 1);
}

#[test]
fn description_only_alt_text_maps_to_shape_comment_without_touching_title() {
    let source_state = state(
        ObjectPropertyKind::BasicShape,
        44,
        102,
        margins(0),
        None,
        None,
        true,
        Some(ObjectAltText {
            title: String::new(),
            description: "before & one".to_owned(),
        }),
    );
    let xml = section(
        "<hp:ellipse id=\"44\" instid=\"102\"><hp:shapeComment>before &amp; one</hp:shapeComment></hp:ellipse>",
    );
    let plan = domain_plan(
        &source_state,
        ObjectPropertiesOperation::SetAltText {
            value: Some(ObjectAltText {
                title: String::new(),
                description: "after < two".to_owned(),
            }),
        },
    );
    let hwpx_plan = ObjectCommonPropertiesHwpxBuilder::plan(
        &xml,
        0,
        &plan,
        FLOW_A,
        state_limits(),
        hwpx_limits(),
    )
    .expect("HWPX plan");
    let output = ObjectCommonPropertiesHwpxLowerer::lower_in_section(
        &xml,
        &hwpx_plan,
        FLOW_A,
        state_limits(),
        hwpx_limits(),
    )
    .expect("lower");
    assert!(
        String::from_utf8(output)
            .expect("UTF-8")
            .contains("<hp:shapeComment>after &lt; two</hp:shapeComment>")
    );
}

#[test]
fn unsupported_or_lossy_profiles_fail_before_any_output() {
    let shape_state = state(
        ObjectPropertyKind::BasicShape,
        45,
        103,
        margins(0),
        None,
        None,
        true,
        None,
    );
    let shape_xml = section(
        "<hp:rect id=\"45\" instid=\"103\"><hp:outMargin left=\"0\" right=\"1\" top=\"2\" bottom=\"3\"/></hp:rect>",
    );
    let aspect = domain_plan(
        &shape_state,
        ObjectPropertiesOperation::SetAspectLock { enabled: true },
    );
    assert_eq!(
        ObjectCommonPropertiesHwpxBuilder::plan(
            &shape_xml,
            0,
            &aspect,
            FLOW_A,
            state_limits(),
            hwpx_limits(),
        )
        .expect_err("aspect lock must remain unavailable"),
        ObjectCommonPropertiesHwpxError::UnsupportedProfile
    );

    let printable = domain_plan(
        &shape_state,
        ObjectPropertiesOperation::SetPrintable { enabled: false },
    );
    assert_eq!(
        ObjectCommonPropertiesHwpxBuilder::plan(
            &shape_xml,
            0,
            &printable,
            FLOW_A,
            state_limits(),
            hwpx_limits(),
        )
        .expect_err("generic printability must remain unavailable"),
        ObjectCommonPropertiesHwpxError::UnsupportedProfile
    );

    let titled = domain_plan(
        &shape_state,
        ObjectPropertiesOperation::SetAltText {
            value: Some(ObjectAltText {
                title: "title cannot be stored".to_owned(),
                description: "description".to_owned(),
            }),
        },
    );
    let alt_xml =
        section("<hp:rect id=\"45\" instid=\"103\"><hp:shapeComment></hp:shapeComment></hp:rect>");
    assert_eq!(
        ObjectCommonPropertiesHwpxBuilder::plan(
            &alt_xml,
            0,
            &titled,
            FLOW_A,
            state_limits(),
            hwpx_limits(),
        )
        .expect_err("title cannot be collapsed into shapeComment"),
        ObjectCommonPropertiesHwpxError::UnsupportedProfile
    );
}

#[test]
fn source_and_flow_drift_are_rejected_at_plan_and_lowering() {
    let source_state = state(
        ObjectPropertyKind::FormObject,
        46,
        104,
        margins(0),
        None,
        None,
        true,
        None,
    );
    let xml = section("<hp:edit id=\"46\" instid=\"104\" printable=\"1\"></hp:edit>");
    let plan = domain_plan(
        &source_state,
        ObjectPropertiesOperation::SetPrintable { enabled: false },
    );
    assert_eq!(
        ObjectCommonPropertiesHwpxBuilder::plan(
            &xml,
            0,
            &plan,
            FLOW_B,
            state_limits(),
            hwpx_limits(),
        )
        .expect_err("flow drift"),
        ObjectCommonPropertiesHwpxError::SourceDrift
    );
    let hwpx_plan = ObjectCommonPropertiesHwpxBuilder::plan(
        &xml,
        0,
        &plan,
        FLOW_A,
        state_limits(),
        hwpx_limits(),
    )
    .expect("HWPX plan");
    let drifted = String::from_utf8(xml.clone())
        .expect("UTF-8")
        .replace("printable=\"1\"", "printable=\"0\"")
        .into_bytes();
    assert_eq!(
        ObjectCommonPropertiesHwpxLowerer::lower_in_section(
            &drifted,
            &hwpx_plan,
            FLOW_A,
            state_limits(),
            hwpx_limits(),
        ),
        Err(ObjectCommonPropertiesHwpxError::SourceDrift)
    );
}
