#![allow(clippy::expect_used)] // Test fixtures keep failures local and readable.

use domain_ir::{
    LogicalId, OBJECT_PROPERTIES_SCHEMA_VERSION, ObjectPropertiesBuilder,
    ObjectPropertiesLimitConfig, ObjectPropertiesLimits, ObjectPropertiesOperation,
    ObjectPropertiesRequest, ObjectPropertiesRequestDraft, ObjectPropertiesState,
    ObjectPropertiesStateDraft, ObjectPropertyKind, ObjectPropertyMargins,
    ObjectTextBoxVerticalAlignment, OpaqueObjectProperty, TextBoxDirection, TextBoxProperties,
};
use hwpx_package::{
    TextBoxPropertiesHwpxBuilder, TextBoxPropertiesHwpxError, TextBoxPropertiesHwpxLimitConfig,
    TextBoxPropertiesHwpxLimits, TextBoxPropertiesHwpxLowerer, TextBoxPropertiesHwpxReader,
};

const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const FLOW_A: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const FLOW_B: &str = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
const DIGEST_1: &str = "1111111111111111111111111111111111111111111111111111111111111111";
const DIGEST_2: &str = "2222222222222222222222222222222222222222222222222222222222222222";
const DIGEST_3: &str = "3333333333333333333333333333333333333333333333333333333333333333";
const DIGEST_4: &str = "4444444444444444444444444444444444444444444444444444444444444444";
const DIGEST_5: &str = "5555555555555555555555555555555555555555555555555555555555555555";

fn state_limits() -> ObjectPropertiesLimits {
    ObjectPropertiesLimits::new(ObjectPropertiesLimitConfig::default()).expect("state limits")
}

fn hwpx_limits() -> TextBoxPropertiesHwpxLimits {
    TextBoxPropertiesHwpxLimits::new(TextBoxPropertiesHwpxLimitConfig::default())
        .expect("HWPX limits")
}

fn source_properties() -> TextBoxProperties {
    TextBoxProperties {
        margins: ObjectPropertyMargins {
            left_hwpunit: 10,
            right_hwpunit: 11,
            top_hwpunit: 12,
            bottom_hwpunit: 13,
        },
        vertical_alignment: ObjectTextBoxVerticalAlignment::Center,
        direction: TextBoxDirection::Horizontal,
    }
}

fn state(properties: TextBoxProperties) -> ObjectPropertiesState {
    ObjectPropertiesState::from_draft(
        ObjectPropertiesStateDraft {
            schema_version: OBJECT_PROPERTIES_SCHEMA_VERSION.to_owned(),
            logical_object_id: LogicalId::parse("textbox-1").expect("logical id"),
            native_object_id: 42,
            native_instance_id: 100,
            object_kind: ObjectPropertyKind::TextBox,
            geometry_state_sha256: DIGEST_1.to_owned(),
            appearance_state_sha256: DIGEST_2.to_owned(),
            payload_state_sha256: DIGEST_3.to_owned(),
            resource_inventory_sha256: DIGEST_4.to_owned(),
            embedded_content_state_sha256: DIGEST_5.to_owned(),
            outer_margins: ObjectPropertyMargins {
                left_hwpunit: 1,
                right_hwpunit: 2,
                top_hwpunit: 3,
                bottom_hwpunit: 4,
            },
            caption: None,
            text_box: Some(properties),
            image: None,
            aspect_locked: false,
            protected: false,
            printable: true,
            alt_text: None,
            hyperlink: None,
            opaque_properties: vec![OpaqueObjectProperty {
                namespace: "vendor.private".to_owned(),
                name: "opaque".to_owned(),
                value: "SECRET-PROPERTY-VALUE".to_owned(),
            }],
        },
        state_limits(),
    )
    .expect("state")
}

fn picture() -> String {
    "<hp:pic id=\"41\" instid=\"99\"><hp:opaque>PRESERVE-PICTURE</hp:opaque></hp:pic>".to_owned()
}

fn text_box() -> String {
    concat!(
        "<hp:rect id=\"42\" instid=\"100\" zOrder=\"7\" vendor=\"PRESERVE-ROOT\">",
        "<hp:before keep=\"yes\">PRESERVE-BEFORE</hp:before>",
        "<hp:drawText lastWidth=\"7200\" name=\"Private title\" editable=\"1\" vendor=\"PRESERVE-DRAWTEXT\">",
        "<hp:textMargin left=\"10\" right=\"11\" top=\"12\" bottom=\"13\" vendor=\"PRESERVE-MARGIN\"/>",
        "<hp:subList id=\"501\" textDirection=\"HORIZONTAL\" lineWrap=\"BREAK\" vertAlign=\"CENTER\" ",
        "linkListIDRef=\"0\" linkListNextIDRef=\"0\" textWidth=\"7000\" textHeight=\"3500\" ",
        "hasTextRef=\"0\" hasNumRef=\"0\" vendor=\"PRESERVE-SUBLIST\">",
        "<hp:p id=\"601\"><hp:run><hp:t>PRESERVE &amp; PRIVATE TEXT</hp:t></hp:run></hp:p>",
        "</hp:subList></hp:drawText>",
        "<hp:after keep=\"yes\">PRESERVE-AFTER</hp:after>",
        "</hp:rect>"
    )
    .to_owned()
}

fn section() -> Vec<u8> {
    format!(
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?><hp:sec xmlns:hp=\"{PARAGRAPH_NS}\"><hp:p><hp:run>{}{}</hp:run></hp:p><!--PRESERVE-TAIL--></hp:sec>",
        picture(),
        text_box()
    )
    .into_bytes()
}

fn domain_plan(
    source: &ObjectPropertiesState,
    target: TextBoxProperties,
) -> domain_ir::ObjectPropertiesPlan {
    let request = ObjectPropertiesRequest::from_draft(
        ObjectPropertiesRequestDraft {
            schema_version: OBJECT_PROPERTIES_SCHEMA_VERSION.to_owned(),
            request_id: LogicalId::parse("textbox-properties-request").expect("request id"),
            expected_source_state_sha256: source
                .canonical_sha256(state_limits())
                .expect("source digest"),
            expected_document_flow_sha256: FLOW_A.to_owned(),
            target_document_flow_sha256: FLOW_B.to_owned(),
            operation: ObjectPropertiesOperation::SetTextBoxProperties { properties: target },
        },
        source,
        FLOW_A,
        state_limits(),
    )
    .expect("request");
    ObjectPropertiesBuilder::plan(source, &request, FLOW_A, state_limits()).expect("domain plan")
}

fn lower(
    target: TextBoxProperties,
) -> (Vec<u8>, hwpx_package::TextBoxPropertiesHwpxLoweringReceipt) {
    let source = section();
    let current = state(source_properties());
    let domain = domain_plan(&current, target);
    let plan = TextBoxPropertiesHwpxBuilder::plan(
        &source,
        1,
        &domain,
        FLOW_A,
        state_limits(),
        hwpx_limits(),
    )
    .expect("HWPX plan");
    TextBoxPropertiesHwpxLowerer::lower_in_section_with_receipt(
        &source,
        &plan,
        FLOW_A,
        state_limits(),
        hwpx_limits(),
    )
    .expect("lower")
}

#[test]
fn reads_exact_text_box_and_redacts_complete_state() {
    let source = section();
    let expected = state(source_properties());
    let readback = TextBoxPropertiesHwpxReader::read_in_section(
        &source,
        1,
        &expected,
        state_limits(),
        hwpx_limits(),
    )
    .expect("read");
    assert_eq!(readback.properties, source_properties());
    assert_eq!(readback.object_ordinal, 1);
    let debug = format!("{readback:?}");
    assert!(debug.contains("<redacted>"));
    assert!(!debug.contains("SECRET-PROPERTY-VALUE"));
    assert!(!debug.contains("Private title"));
}

#[test]
fn lowers_all_six_attributes_and_preserves_every_other_byte() {
    let target = TextBoxProperties {
        margins: ObjectPropertyMargins {
            left_hwpunit: 100,
            right_hwpunit: 200,
            top_hwpunit: 300,
            bottom_hwpunit: 400,
        },
        vertical_alignment: ObjectTextBoxVerticalAlignment::Bottom,
        direction: TextBoxDirection::VerticalRightToLeft,
    };
    let (output, receipt) = lower(target);
    let text = String::from_utf8(output.clone()).expect("UTF-8");
    for preserved in [
        "PRESERVE-PICTURE",
        "PRESERVE-ROOT",
        "PRESERVE-BEFORE",
        "PRESERVE-DRAWTEXT",
        "PRESERVE-MARGIN",
        "PRESERVE-SUBLIST",
        "PRESERVE &amp; PRIVATE TEXT",
        "PRESERVE-AFTER",
        "PRESERVE-TAIL",
    ] {
        assert!(text.contains(preserved));
    }
    assert!(text.contains("left=\"100\" right=\"200\" top=\"300\" bottom=\"400\""));
    assert!(text.contains("textDirection=\"VERTICALALL\""));
    assert!(text.contains("vertAlign=\"BOTTOM\""));
    assert_eq!(receipt.modified_attribute_count, 6);
    assert_eq!(receipt.capability_id, "obj.textbox_properties");
    let target_state = state(target);
    let readback = TextBoxPropertiesHwpxReader::read_in_section(
        &output,
        1,
        &target_state,
        state_limits(),
        hwpx_limits(),
    )
    .expect("target readback");
    assert_eq!(readback.properties, target);
}

#[test]
fn covers_three_directions_three_alignments_and_margin_boundaries() {
    let maximum = state_limits().config().extent_hwpunit;
    for (direction_index, direction) in [
        TextBoxDirection::Horizontal,
        TextBoxDirection::Vertical,
        TextBoxDirection::VerticalRightToLeft,
    ]
    .into_iter()
    .enumerate()
    {
        for (alignment_index, vertical_alignment) in [
            ObjectTextBoxVerticalAlignment::Top,
            ObjectTextBoxVerticalAlignment::Center,
            ObjectTextBoxVerticalAlignment::Bottom,
        ]
        .into_iter()
        .enumerate()
        {
            let seed = u32::try_from(direction_index * 3 + alignment_index).expect("seed");
            let target = TextBoxProperties {
                margins: ObjectPropertyMargins {
                    left_hwpunit: if seed == 0 { 0 } else { seed },
                    right_hwpunit: maximum - seed,
                    top_hwpunit: seed + 20,
                    bottom_hwpunit: seed + 30,
                },
                vertical_alignment,
                direction,
            };
            let (output, _) = lower(target);
            let readback = TextBoxPropertiesHwpxReader::read_in_section(
                &output,
                1,
                &state(target),
                state_limits(),
                hwpx_limits(),
            )
            .expect("variant readback");
            assert_eq!(readback.properties, target);
        }
    }
}

#[test]
fn deterministic_bounded_plan_and_receipt_debug_hide_bindings() {
    let source = section();
    let current = state(source_properties());
    let target = TextBoxProperties {
        direction: TextBoxDirection::Vertical,
        ..source_properties()
    };
    let domain = domain_plan(&current, target);
    let plan = TextBoxPropertiesHwpxBuilder::plan(
        &source,
        1,
        &domain,
        FLOW_A,
        state_limits(),
        hwpx_limits(),
    )
    .expect("plan");
    assert_eq!(
        plan.canonical_json(hwpx_limits()).expect("JSON 1"),
        plan.canonical_json(hwpx_limits()).expect("JSON 2")
    );
    let (_, receipt) = TextBoxPropertiesHwpxLowerer::lower_in_section_with_receipt(
        &source,
        &plan,
        FLOW_A,
        state_limits(),
        hwpx_limits(),
    )
    .expect("lower");
    for debug in [format!("{plan:?}"), format!("{receipt:?}")] {
        assert!(debug.contains("<redacted>"));
        assert!(!debug.contains(FLOW_A));
        assert!(!debug.contains(DIGEST_1));
        assert!(!debug.contains("textbox-1"));
    }
}

#[test]
fn request_and_lower_reject_state_flow_section_and_payload_drift() {
    let source = section();
    let current = state(source_properties());
    let target = TextBoxProperties {
        direction: TextBoxDirection::Vertical,
        ..source_properties()
    };
    let domain = domain_plan(&current, target);
    assert!(matches!(
        TextBoxPropertiesHwpxBuilder::plan(
            &source,
            1,
            &domain,
            FLOW_B,
            state_limits(),
            hwpx_limits(),
        ),
        Err(TextBoxPropertiesHwpxError::SourceDrift)
    ));
    let plan = TextBoxPropertiesHwpxBuilder::plan(
        &source,
        1,
        &domain,
        FLOW_A,
        state_limits(),
        hwpx_limits(),
    )
    .expect("plan");
    assert!(matches!(
        TextBoxPropertiesHwpxLowerer::lower_in_section(
            &source,
            &plan,
            FLOW_B,
            state_limits(),
            hwpx_limits(),
        ),
        Err(TextBoxPropertiesHwpxError::SourceDrift)
    ));
    for needle in ["PRESERVE-AFTER", "PRESERVE-MARGIN", "PRESERVE-SUBLIST"] {
        let drifted = String::from_utf8(source.clone())
            .expect("UTF-8")
            .replacen(needle, "DRIFTED", 1)
            .into_bytes();
        assert!(matches!(
            TextBoxPropertiesHwpxLowerer::lower_in_section(
                &drifted,
                &plan,
                FLOW_A,
                state_limits(),
                hwpx_limits(),
            ),
            Err(TextBoxPropertiesHwpxError::SourceDrift)
        ));
    }
    let wrong_identity = ObjectPropertiesState::from_draft(
        ObjectPropertiesStateDraft {
            native_object_id: 43,
            ..serde_json::from_slice::<ObjectPropertiesStateDraft>(
                &state(source_properties())
                    .canonical_json(state_limits())
                    .expect("state JSON"),
            )
            .expect("state draft")
        },
        state_limits(),
    )
    .expect("wrong identity");
    assert!(matches!(
        TextBoxPropertiesHwpxReader::read_in_section(
            &source,
            1,
            &wrong_identity,
            state_limits(),
            hwpx_limits(),
        ),
        Err(TextBoxPropertiesHwpxError::SourceDrift)
    ));
}

#[test]
fn malformed_missing_duplicate_nested_qualified_and_noncanonical_inputs_fail_closed() {
    let source = String::from_utf8(section()).expect("UTF-8");
    let expected = state(source_properties());
    let cases = [
        source.replacen("<hp:textMargin ", "<hp:notMargin ", 1),
        source.replacen(
            "</hp:drawText>",
            "</hp:drawText><hp:drawText><hp:textMargin left=\"1\" right=\"1\" top=\"1\" bottom=\"1\"/><hp:subList textDirection=\"HORIZONTAL\" vertAlign=\"TOP\"/></hp:drawText>",
            1,
        ),
        source.replacen(
            "<hp:p id=\"601\">",
            "<hp:drawText/><hp:p id=\"601\">",
            1,
        ),
        source.replacen("left=\"10\"", "left=\"10\" left=\"10\"", 1),
        source
            .replacen(
                &format!("xmlns:hp=\"{PARAGRAPH_NS}\""),
                &format!("xmlns:hp=\"{PARAGRAPH_NS}\" xmlns:x=\"urn:private\""),
                1,
            )
            .replacen("left=\"10\"", "x:left=\"10\"", 1),
        source.replacen("left=\"10\"", "left=\"01\"", 1),
        source.replacen("left=\"10\"", "left=\"&#49;0\"", 1),
        source.replacen("textDirection=\"HORIZONTAL\"", "textDirection=\"RTL\"", 1),
        source.replacen("vertAlign=\"CENTER\"", "vertAlign=\"JUSTIFY\"", 1),
    ];
    for malformed in cases {
        assert!(
            TextBoxPropertiesHwpxReader::read_in_section(
                malformed.as_bytes(),
                1,
                &expected,
                state_limits(),
                hwpx_limits(),
            )
            .is_err()
        );
    }
    assert!(matches!(
        TextBoxPropertiesHwpxReader::read_in_section(
            section().as_slice(),
            0,
            &expected,
            state_limits(),
            hwpx_limits(),
        ),
        Err(TextBoxPropertiesHwpxError::UnsupportedTextBox)
    ));
}

#[test]
fn wrong_capability_noop_and_finite_limits_fail_closed() {
    let source = section();
    let current = state(source_properties());
    let noop = ObjectPropertiesRequest::from_draft(
        ObjectPropertiesRequestDraft {
            schema_version: OBJECT_PROPERTIES_SCHEMA_VERSION.to_owned(),
            request_id: LogicalId::parse("noop-request").expect("request id"),
            expected_source_state_sha256: current.canonical_sha256(state_limits()).expect("digest"),
            expected_document_flow_sha256: FLOW_A.to_owned(),
            target_document_flow_sha256: FLOW_B.to_owned(),
            operation: ObjectPropertiesOperation::SetTextBoxProperties {
                properties: source_properties(),
            },
        },
        &current,
        FLOW_A,
        state_limits(),
    );
    assert!(noop.is_err());

    let margin_request = ObjectPropertiesRequest::from_draft(
        ObjectPropertiesRequestDraft {
            schema_version: OBJECT_PROPERTIES_SCHEMA_VERSION.to_owned(),
            request_id: LogicalId::parse("wrong-capability").expect("request id"),
            expected_source_state_sha256: current.canonical_sha256(state_limits()).expect("digest"),
            expected_document_flow_sha256: FLOW_A.to_owned(),
            target_document_flow_sha256: FLOW_B.to_owned(),
            operation: ObjectPropertiesOperation::SetMarginCaption {
                outer_margins: ObjectPropertyMargins {
                    left_hwpunit: 20,
                    right_hwpunit: 21,
                    top_hwpunit: 22,
                    bottom_hwpunit: 23,
                },
                caption: None,
            },
        },
        &current,
        FLOW_A,
        state_limits(),
    )
    .expect("margin request");
    let wrong_plan =
        ObjectPropertiesBuilder::plan(&current, &margin_request, FLOW_A, state_limits())
            .expect("margin plan");
    assert!(matches!(
        TextBoxPropertiesHwpxBuilder::plan(
            &source,
            1,
            &wrong_plan,
            FLOW_A,
            state_limits(),
            hwpx_limits(),
        ),
        Err(TextBoxPropertiesHwpxError::SourceDrift)
    ));

    let tight = TextBoxPropertiesHwpxLimits::new(TextBoxPropertiesHwpxLimitConfig {
        section_bytes: source.len() - 1,
        output_bytes: source.len(),
        ..TextBoxPropertiesHwpxLimitConfig::default()
    })
    .expect("tight limits");
    assert!(matches!(
        TextBoxPropertiesHwpxReader::read_in_section(&source, 1, &current, state_limits(), tight,),
        Err(TextBoxPropertiesHwpxError::InputLimit)
    ));
}
