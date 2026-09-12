#![allow(clippy::expect_used)] // Test fixtures keep failures local and readable.

use domain_ir::{
    ImageProperties, LogicalId, OBJECT_PROPERTIES_SCHEMA_VERSION, ObjectHyperlink,
    ObjectPropertiesBuilder, ObjectPropertiesLimitConfig, ObjectPropertiesLimits,
    ObjectPropertiesOperation, ObjectPropertiesRequest, ObjectPropertiesRequestDraft,
    ObjectPropertiesState, ObjectPropertiesStateDraft, ObjectPropertyKind, ObjectPropertyMargins,
    ObjectTextBoxVerticalAlignment, OpaqueObjectProperty, TextBoxDirection, TextBoxProperties,
};
use hwpx_package::{
    ObjectHyperlinkHwpxBuilder, ObjectHyperlinkHwpxError, ObjectHyperlinkHwpxLimitConfig,
    ObjectHyperlinkHwpxLimits, ObjectHyperlinkHwpxLowerer, ObjectHyperlinkHwpxReader,
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

fn hwpx_limits() -> ObjectHyperlinkHwpxLimits {
    ObjectHyperlinkHwpxLimits::new(ObjectHyperlinkHwpxLimitConfig::default()).expect("HWPX limits")
}

fn text_box_properties() -> TextBoxProperties {
    TextBoxProperties {
        margins: ObjectPropertyMargins {
            left_hwpunit: 1,
            right_hwpunit: 2,
            top_hwpunit: 3,
            bottom_hwpunit: 4,
        },
        vertical_alignment: ObjectTextBoxVerticalAlignment::Center,
        direction: TextBoxDirection::Horizontal,
    }
}

fn image_properties() -> ImageProperties {
    ImageProperties {
        original_width_px: 640,
        original_height_px: 480,
        horizontal_scale_millionths: 1_000_000,
        vertical_scale_millionths: 1_000_000,
        horizontal_dpi: 96,
        vertical_dpi: 96,
    }
}

fn state(
    kind: ObjectPropertyKind,
    native_object_id: u32,
    native_instance_id: u32,
    hyperlink: Option<ObjectHyperlink>,
) -> ObjectPropertiesState {
    ObjectPropertiesState::from_draft(
        ObjectPropertiesStateDraft {
            schema_version: OBJECT_PROPERTIES_SCHEMA_VERSION.to_owned(),
            logical_object_id: LogicalId::parse("object-1").expect("logical id"),
            native_object_id,
            native_instance_id,
            object_kind: kind,
            geometry_state_sha256: DIGEST_1.to_owned(),
            appearance_state_sha256: DIGEST_2.to_owned(),
            payload_state_sha256: DIGEST_3.to_owned(),
            resource_inventory_sha256: DIGEST_4.to_owned(),
            embedded_content_state_sha256: DIGEST_5.to_owned(),
            outer_margins: ObjectPropertyMargins {
                left_hwpunit: 10,
                right_hwpunit: 11,
                top_hwpunit: 12,
                bottom_hwpunit: 13,
            },
            caption: None,
            text_box: (kind == ObjectPropertyKind::TextBox).then(text_box_properties),
            image: (kind == ObjectPropertyKind::Picture).then(image_properties),
            aspect_locked: false,
            protected: false,
            printable: true,
            alt_text: None,
            hyperlink,
            opaque_properties: vec![OpaqueObjectProperty {
                namespace: "vendor.private".to_owned(),
                name: "opaque".to_owned(),
                value: "PRIVATE-PRESERVE".to_owned(),
            }],
        },
        state_limits(),
    )
    .expect("state")
}

fn object(tag: &str, id: u32, instid: u32, href: &str, child: &str) -> String {
    format!(
        "<hp:{tag} id=\"{id}\" instid=\"{instid}\" href=\"{href}\" vendor=\"PRESERVE-ROOT\">{child}<hp:opaque keep=\"yes\">PRESERVE-PAYLOAD</hp:opaque></hp:{tag}>"
    )
}

fn section(objects: &[String]) -> Vec<u8> {
    format!(
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?><hs:sec xmlns:hs=\"http://www.hancom.co.kr/hwpml/2011/section\" xmlns:hp=\"{PARAGRAPH_NS}\"><hp:p id=\"1\"><hp:run><hp:t>BEFORE</hp:t>{}<hp:t>AFTER</hp:t></hp:run></hp:p></hs:sec>",
        objects.join("")
    )
    .into_bytes()
}

fn domain_plan(
    source: &ObjectPropertiesState,
    target: Option<ObjectHyperlink>,
) -> domain_ir::ObjectPropertiesPlan {
    let request = ObjectPropertiesRequest::from_draft(
        ObjectPropertiesRequestDraft {
            schema_version: OBJECT_PROPERTIES_SCHEMA_VERSION.to_owned(),
            request_id: LogicalId::parse("hyperlink-request").expect("request id"),
            expected_source_state_sha256: source
                .canonical_sha256(state_limits())
                .expect("state digest"),
            expected_document_flow_sha256: FLOW_A.to_owned(),
            target_document_flow_sha256: FLOW_B.to_owned(),
            operation: ObjectPropertiesOperation::SetObjectHyperlink { value: target },
        },
        source,
        FLOW_A,
        state_limits(),
    )
    .expect("request");
    ObjectPropertiesBuilder::plan(source, &request, FLOW_A, state_limits()).expect("domain plan")
}

fn lower(
    bytes: &[u8],
    ordinal: usize,
    source: &ObjectPropertiesState,
    target: Option<ObjectHyperlink>,
) -> (Vec<u8>, hwpx_package::ObjectHyperlinkHwpxLoweringReceipt) {
    let domain = domain_plan(source, target);
    let plan = ObjectHyperlinkHwpxBuilder::plan(
        bytes,
        ordinal,
        &domain,
        FLOW_A,
        state_limits(),
        hwpx_limits(),
    )
    .expect("HWPX plan");
    ObjectHyperlinkHwpxLowerer::lower_in_section_with_receipt(
        bytes,
        &plan,
        FLOW_A,
        state_limits(),
        hwpx_limits(),
    )
    .expect("lower")
}

#[test]
fn reads_every_admitted_common_object_kind() {
    let cases = [
        ("pic", "", ObjectPropertyKind::Picture),
        ("rect", "", ObjectPropertyKind::BasicShape),
        ("rect", "<hp:drawText/>", ObjectPropertyKind::TextBox),
        ("ellipse", "", ObjectPropertyKind::BasicShape),
        ("line", "", ObjectPropertyKind::BasicShape),
        ("arc", "", ObjectPropertyKind::BasicShape),
        ("polygon", "", ObjectPropertyKind::BasicShape),
        ("curve", "", ObjectPropertyKind::BasicShape),
        ("connectLine", "", ObjectPropertyKind::BasicShape),
        ("container", "", ObjectPropertyKind::DrawingCanvas),
        ("ole", "", ObjectPropertyKind::EmbeddedObject),
        ("video", "", ObjectPropertyKind::EmbeddedObject),
    ];
    let objects = cases
        .iter()
        .enumerate()
        .map(|(index, (tag, child, _))| {
            object(
                tag,
                u32::try_from(index + 1).expect("id"),
                u32::try_from(index + 101).expect("instid"),
                "",
                child,
            )
        })
        .collect::<Vec<_>>();
    let bytes = section(&objects);
    for (ordinal, (_, _, kind)) in cases.into_iter().enumerate() {
        let expected = state(
            kind,
            u32::try_from(ordinal + 1).expect("id"),
            u32::try_from(ordinal + 101).expect("instid"),
            None,
        );
        let readback = ObjectHyperlinkHwpxReader::read_in_section(
            &bytes,
            ordinal,
            &expected,
            state_limits(),
            hwpx_limits(),
        )
        .expect("readback");
        assert_eq!(readback.state.object_kind(), kind);
        assert_eq!(readback.hyperlink, None);
    }
}

#[test]
fn lowers_https_mailto_bookmark_and_removal_with_exact_escaping() {
    let none = state(ObjectPropertyKind::BasicShape, 41, 99, None);
    let bytes = section(&[object("rect", 41, 99, "", "")]);
    let https = ObjectHyperlink::Https {
        uri: "https://example.test/a?x=1&y=two".to_owned(),
    };
    let (https_bytes, receipt) = lower(&bytes, 0, &none, Some(https.clone()));
    let https_xml = String::from_utf8(https_bytes.clone()).expect("UTF-8");
    assert!(https_xml.contains("href=\"https://example.test/a?x=1&amp;y=two\""));
    assert_eq!(receipt.capability_id, "obj.object_hyperlink");
    assert_eq!(receipt.modified_attribute_count, 1);
    assert!(https_xml.contains("PRESERVE-PAYLOAD"));

    let https_state = state(ObjectPropertyKind::BasicShape, 41, 99, Some(https));
    let mailto = ObjectHyperlink::Mailto {
        address: "person@example.test".to_owned(),
    };
    let (mailto_bytes, _) = lower(&https_bytes, 0, &https_state, Some(mailto.clone()));
    assert!(
        String::from_utf8(mailto_bytes.clone())
            .expect("UTF-8")
            .contains("href=\"mailto:person@example.test\"")
    );

    let mailto_state = state(ObjectPropertyKind::BasicShape, 41, 99, Some(mailto));
    let bookmark = ObjectHyperlink::Bookmark {
        name: "section_1.anchor".to_owned(),
    };
    let (bookmark_bytes, _) = lower(&mailto_bytes, 0, &mailto_state, Some(bookmark.clone()));
    assert!(
        String::from_utf8(bookmark_bytes.clone())
            .expect("UTF-8")
            .contains("href=\"#section_1.anchor\"")
    );

    let bookmark_state = state(ObjectPropertyKind::BasicShape, 41, 99, Some(bookmark));
    let (removed, _) = lower(&bookmark_bytes, 0, &bookmark_state, None);
    assert!(
        String::from_utf8(removed)
            .expect("UTF-8")
            .contains("href=\"\"")
    );
}

#[test]
fn edits_only_selected_href_and_preserves_other_object_byte_exactly() {
    let first = object("pic", 40, 98, "https://keep.example", "");
    let second = object("ole", 41, 99, "", "<hp:vendor>PRIVATE-OLE</hp:vendor>");
    let bytes = section(&[first.clone(), second.clone()]);
    let expected = state(ObjectPropertyKind::EmbeddedObject, 41, 99, None);
    let (output, _) = lower(
        &bytes,
        1,
        &expected,
        Some(ObjectHyperlink::Bookmark {
            name: "chart-anchor".to_owned(),
        }),
    );
    let output = String::from_utf8(output).expect("UTF-8");
    assert!(output.contains(&first));
    assert!(output.contains(&second.replace("href=\"\"", "href=\"#chart-anchor\"")));
}

#[test]
fn rejects_unreviewed_unsafe_missing_duplicate_and_namespaced_href() {
    let expected = state(ObjectPropertyKind::BasicShape, 41, 99, None);
    for href in [
        "http://example.test",
        "file:///private/path",
        "javascript:alert(1)",
        "mailto:",
        "#",
    ] {
        let bytes = section(&[object("rect", 41, 99, href, "")]);
        assert_eq!(
            ObjectHyperlinkHwpxReader::read_in_section(
                &bytes,
                0,
                &expected,
                state_limits(),
                hwpx_limits(),
            ),
            Err(ObjectHyperlinkHwpxError::InvalidHyperlink)
        );
    }

    let missing = section(&[object("rect", 41, 99, "", "").replace(" href=\"\"", "")]);
    let duplicate = section(&[
        object("rect", 41, 99, "", "").replace(" href=\"\"", " href=\"\" href=\"#other\"")
    ]);
    let namespaced =
        section(&[object("rect", 41, 99, "", "").replace(" href=\"\"", " hp:href=\"\"")]);
    for bytes in [missing, namespaced] {
        assert_eq!(
            ObjectHyperlinkHwpxReader::read_in_section(
                &bytes,
                0,
                &expected,
                state_limits(),
                hwpx_limits(),
            ),
            Err(ObjectHyperlinkHwpxError::InvalidAttribute)
        );
    }
    assert!(matches!(
        ObjectHyperlinkHwpxReader::read_in_section(
            &duplicate,
            0,
            &expected,
            state_limits(),
            hwpx_limits(),
        ),
        Err(ObjectHyperlinkHwpxError::Preserving(_))
    ));
}

#[test]
fn rejects_unsupported_textart_nested_only_and_ambiguous_textbox_shape() {
    let basic = state(ObjectPropertyKind::BasicShape, 41, 99, None);
    let textart = section(&[object("textart", 41, 99, "", "")]);
    assert_eq!(
        ObjectHyperlinkHwpxReader::read_in_section(
            &textart,
            0,
            &basic,
            state_limits(),
            hwpx_limits(),
        ),
        Err(ObjectHyperlinkHwpxError::UnsupportedObject)
    );

    let chart = section(&[object("chart", 41, 99, "", "")]);
    let chart_state = state(ObjectPropertyKind::Chart, 41, 99, None);
    assert_eq!(
        ObjectHyperlinkHwpxReader::read_in_section(
            &chart,
            0,
            &chart_state,
            state_limits(),
            hwpx_limits(),
        ),
        Err(ObjectHyperlinkHwpxError::UnsupportedObject)
    );

    let nested = format!(
        "<?xml version=\"1.0\"?><hs:sec xmlns:hs=\"http://www.hancom.co.kr/hwpml/2011/section\" xmlns:hp=\"{PARAGRAPH_NS}\"><hp:p><hp:run><hp:container id=\"1\" instid=\"2\" href=\"\"><hp:rect id=\"41\" instid=\"99\" href=\"\"/></hp:container></hp:run></hp:p></hs:sec>"
    )
    .into_bytes();
    assert_eq!(
        ObjectHyperlinkHwpxReader::read_in_section(
            &nested,
            1,
            &basic,
            state_limits(),
            hwpx_limits(),
        ),
        Err(ObjectHyperlinkHwpxError::UnsupportedObject)
    );

    let ambiguous = section(&[object("rect", 41, 99, "", "<hp:drawText/><hp:drawText/>")]);
    assert_eq!(
        ObjectHyperlinkHwpxReader::read_in_section(
            &ambiguous,
            0,
            &basic,
            state_limits(),
            hwpx_limits(),
        ),
        Err(ObjectHyperlinkHwpxError::UnsupportedObject)
    );
}

#[test]
fn source_identity_kind_state_and_flow_drift_fail_before_output() {
    let bytes = section(&[object("rect", 41, 99, "", "")]);
    let source = state(ObjectPropertyKind::BasicShape, 41, 99, None);
    let target = Some(ObjectHyperlink::Https {
        uri: "https://example.test/target".to_owned(),
    });
    let domain = domain_plan(&source, target);
    let plan =
        ObjectHyperlinkHwpxBuilder::plan(&bytes, 0, &domain, FLOW_A, state_limits(), hwpx_limits())
            .expect("plan");

    assert_eq!(
        ObjectHyperlinkHwpxLowerer::lower_in_section(
            &bytes,
            &plan,
            FLOW_B,
            state_limits(),
            hwpx_limits(),
        ),
        Err(ObjectHyperlinkHwpxError::SourceDrift)
    );
    let drifted = String::from_utf8(bytes.clone())
        .expect("UTF-8")
        .replace("PRESERVE-PAYLOAD", "DRIFTED-PAYLOAD")
        .into_bytes();
    assert_eq!(
        ObjectHyperlinkHwpxLowerer::lower_in_section(
            &drifted,
            &plan,
            FLOW_A,
            state_limits(),
            hwpx_limits(),
        ),
        Err(ObjectHyperlinkHwpxError::SourceDrift)
    );

    for wrong in [
        state(ObjectPropertyKind::BasicShape, 42, 99, None),
        state(ObjectPropertyKind::BasicShape, 41, 100, None),
        state(ObjectPropertyKind::Chart, 41, 99, None),
        state(
            ObjectPropertyKind::BasicShape,
            41,
            99,
            Some(ObjectHyperlink::Bookmark {
                name: "wrong".to_owned(),
            }),
        ),
    ] {
        assert_eq!(
            ObjectHyperlinkHwpxReader::read_in_section(
                &bytes,
                0,
                &wrong,
                state_limits(),
                hwpx_limits(),
            ),
            Err(ObjectHyperlinkHwpxError::SourceDrift)
        );
    }
}

#[test]
fn bounded_deterministic_plan_and_redacted_debug_are_enforced() {
    let bytes = section(&[object("rect", 41, 99, "", "")]);
    let source = state(ObjectPropertyKind::BasicShape, 41, 99, None);
    let target = Some(ObjectHyperlink::Https {
        uri: "https://secret.example/private?token=hidden".to_owned(),
    });
    let domain = domain_plan(&source, target);
    let first =
        ObjectHyperlinkHwpxBuilder::plan(&bytes, 0, &domain, FLOW_A, state_limits(), hwpx_limits())
            .expect("plan");
    let second =
        ObjectHyperlinkHwpxBuilder::plan(&bytes, 0, &domain, FLOW_A, state_limits(), hwpx_limits())
            .expect("plan");
    assert_eq!(
        first.canonical_json(hwpx_limits()).expect("JSON"),
        second.canonical_json(hwpx_limits()).expect("JSON")
    );
    assert_eq!(first.plan_sha256(), second.plan_sha256());
    let debug = format!("{first:?}");
    assert!(!debug.contains("secret.example"));
    assert!(!debug.contains("token=hidden"));

    let tiny = ObjectHyperlinkHwpxLimits::new(ObjectHyperlinkHwpxLimitConfig {
        section_bytes: 8,
        output_bytes: 8,
        ..ObjectHyperlinkHwpxLimitConfig::default()
    })
    .expect("tiny limits");
    assert_eq!(
        ObjectHyperlinkHwpxReader::read_in_section(&bytes, 0, &source, state_limits(), tiny,),
        Err(ObjectHyperlinkHwpxError::InputLimit)
    );
    assert_eq!(
        ObjectHyperlinkHwpxLimits::new(ObjectHyperlinkHwpxLimitConfig {
            href_bytes: 0,
            ..ObjectHyperlinkHwpxLimitConfig::default()
        }),
        Err(ObjectHyperlinkHwpxError::InvalidLimit)
    );
}
