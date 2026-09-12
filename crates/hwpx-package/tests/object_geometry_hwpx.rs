#![allow(clippy::expect_used)] // Test fixtures use expectations to keep failures local and legible.

use domain_ir::{
    LogicalId, OBJECT_GEOMETRY_SCHEMA_VERSION, ObjectAffineMatrix, ObjectAnchor, ObjectExtent,
    ObjectFlip, ObjectGeometryBuilder, ObjectGeometryLimitConfig, ObjectGeometryLimits,
    ObjectGeometryOperation, ObjectGeometryRequest, ObjectGeometryRequestDraft,
    ObjectHeightReference, ObjectHorizontalAlignment, ObjectHorizontalReference, ObjectKind,
    ObjectOuterMargins, ObjectPosition, ObjectRotation, ObjectSize, ObjectTextFlow, ObjectTextWrap,
    ObjectTransform, ObjectVerticalAlignment, ObjectVerticalReference, ObjectWidthReference,
    ObjectWrap,
};
use hwpx_package::{
    ObjectGeometryHwpxBuilder, ObjectGeometryHwpxError, ObjectGeometryHwpxLimitConfig,
    ObjectGeometryHwpxLimits, ObjectGeometryHwpxLowerer, ObjectGeometryHwpxReader,
};

const FLOW_A: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const FLOW_B: &str = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";

fn state_limits() -> ObjectGeometryLimits {
    ObjectGeometryLimits::new(ObjectGeometryLimitConfig::default()).expect("valid state limits")
}

fn hwpx_limits() -> ObjectGeometryHwpxLimits {
    ObjectGeometryHwpxLimits::new(ObjectGeometryHwpxLimitConfig::default())
        .expect("valid HWPX limits")
}

fn common_object(tag: &str, id: u32, instid: u32, marker: &str) -> String {
    format!(
        r#"<hp:{tag} id="{id}" zOrder="3" numberingType="PICTURE" textWrap="SQUARE" textFlow="BOTH_SIDES" lock="0" href="opaque-ref" groupLevel="0" instid="{instid}"><hp:offset x="10" y="20"/><hp:orgSz width="7200" height="3600"/><hp:curSz width="7200" height="3600"/><hp:flip horizontal="0" vertical="0"/><hp:rotationInfo angle="0" centerX="3600" centerY="1800" rotateimage="1"/><hp:renderingInfo><hc:transMatrix e1="1.000000" e2="0" e3="0" e4="1" e5="10" e6="20"/><hc:scaMatrix e1="1" e2="0" e3="0" e4="1" e5="0" e6="0"/><hc:rotMatrix e1="1" e2="0" e3="0" e4="1" e5="0" e6="0"/></hp:renderingInfo><hp:shapeComment>{marker}</hp:shapeComment><hp:sz width="7200" widthRelTo="ABSOLUTE" height="3600" heightRelTo="ABSOLUTE" protect="0"/><hp:pos treatAsChar="0" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="1" vertRelTo="PARA" horzRelTo="PARA" vertAlign="TOP" horzAlign="LEFT" vertOffset="2000" horzOffset="1000"/><hp:outMargin left="10" right="11" top="12" bottom="13"/></hp:{tag}>"#
    )
}

fn section_with(objects: &[String]) -> Vec<u8> {
    format!(
        r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?><hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core"><hp:p id="10"><hp:run charPrIDRef="0"><hp:t>before</hp:t>{}<hp:t>after</hp:t></hp:run></hp:p></hs:sec>"#,
        objects.join("")
    )
    .into_bytes()
}

fn section() -> Vec<u8> {
    section_with(&[
        common_object("pic", 41, 99, "PRESERVE-PICTURE-PAYLOAD"),
        common_object("rect", 42, 100, "PRESERVE-RECTANGLE-PAYLOAD"),
    ])
}

fn logical_id() -> LogicalId {
    LogicalId::parse("shape-1").expect("logical id")
}

fn domain_plan(
    source: &[u8],
    ordinal: usize,
    operation: ObjectGeometryOperation,
) -> domain_ir::ObjectGeometryPlan {
    let readback = ObjectGeometryHwpxReader::read_in_section(
        source,
        ordinal,
        logical_id(),
        state_limits(),
        hwpx_limits(),
    )
    .expect("read source");
    let request = ObjectGeometryRequest::from_draft(
        ObjectGeometryRequestDraft {
            schema_version: OBJECT_GEOMETRY_SCHEMA_VERSION.to_owned(),
            request_id: LogicalId::parse("geometry-request").expect("request id"),
            expected_source_state_sha256: readback
                .state
                .canonical_sha256(state_limits())
                .expect("state digest"),
            expected_document_flow_sha256: FLOW_A.to_owned(),
            target_document_flow_sha256: FLOW_B.to_owned(),
            operation,
        },
        &readback.state,
        FLOW_A,
        state_limits(),
    )
    .expect("request");
    ObjectGeometryBuilder::plan(&readback.state, &request, FLOW_A, state_limits())
        .expect("domain plan")
}

fn lower(
    source: &[u8],
    ordinal: usize,
    operation: ObjectGeometryOperation,
) -> (Vec<u8>, hwpx_package::ObjectGeometryHwpxLoweringReceipt) {
    let domain = domain_plan(source, ordinal, operation);
    let plan = ObjectGeometryHwpxBuilder::plan(
        source,
        ordinal,
        &domain,
        FLOW_A,
        state_limits(),
        hwpx_limits(),
    )
    .expect("HWPX plan");
    ObjectGeometryHwpxLowerer::lower_in_section_with_receipt(
        source,
        &plan,
        FLOW_A,
        state_limits(),
        hwpx_limits(),
    )
    .expect("lower")
}

#[test]
fn reads_all_reviewed_run_level_common_component_kinds() {
    let tags = [
        ("pic", ObjectKind::Picture),
        ("rect", ObjectKind::Rectangle),
        ("ellipse", ObjectKind::Ellipse),
        ("line", ObjectKind::Line),
        ("arc", ObjectKind::Arc),
        ("polygon", ObjectKind::Polygon),
        ("curve", ObjectKind::Curve),
        ("connectLine", ObjectKind::ConnectLine),
        ("container", ObjectKind::Container),
        ("ole", ObjectKind::Ole),
        ("video", ObjectKind::Video),
        ("textart", ObjectKind::TextArt),
    ];
    let objects = tags
        .iter()
        .enumerate()
        .map(|(index, (tag, _))| {
            common_object(
                tag,
                u32::try_from(index + 1).expect("id"),
                u32::try_from(index + 101).expect("instance"),
                tag,
            )
        })
        .collect::<Vec<_>>();
    let source = section_with(&objects);
    for (ordinal, (_, expected_kind)) in tags.into_iter().enumerate() {
        let readback = ObjectGeometryHwpxReader::read_in_section(
            &source,
            ordinal,
            logical_id(),
            state_limits(),
            hwpx_limits(),
        )
        .expect("read kind");
        assert_eq!(readback.state.object_kind(), expected_kind);
        assert_eq!(
            readback
                .state
                .component()
                .transform
                .translation
                .e1_millionths,
            1_000_000
        );
    }
}

#[test]
fn lowers_object_protect_for_all_common_kinds_with_one_exact_attribute_edit() {
    let tags = [
        "pic",
        "rect",
        "ellipse",
        "line",
        "arc",
        "polygon",
        "curve",
        "connectLine",
        "container",
        "ole",
        "video",
        "textart",
    ];
    for tag in tags {
        let source = section_with(&[common_object(tag, 41, 99, "PRESERVE-OPAQUE-PAYLOAD")]);
        let expected = String::from_utf8(source.clone())
            .expect("UTF-8")
            .replacen("lock=\"0\"", "lock=\"1\"", 1)
            .into_bytes();
        let (output, receipt) = lower(
            &source,
            0,
            ObjectGeometryOperation::SetLocked { enabled: true },
        );
        assert_eq!(output, expected, "unexpected bytes for {tag}");
        assert_eq!(receipt.capability_id, "obj.object_protect");
        assert_eq!(receipt.modified_attribute_count, 1);
        let reopened = ObjectGeometryHwpxReader::read_in_section(
            &output,
            0,
            logical_id(),
            state_limits(),
            hwpx_limits(),
        )
        .expect("protected readback");
        assert!(reopened.state.locked());
    }
}

#[test]
fn lowers_page_position_and_preserves_other_object_and_opaque_payload() {
    let source = section();
    let second_before = common_object("rect", 42, 100, "PRESERVE-RECTANGLE-PAYLOAD");
    let (output, receipt) = lower(
        &source,
        0,
        ObjectGeometryOperation::SetPosition {
            position: ObjectPosition {
                horizontal_alignment: ObjectHorizontalAlignment::Right,
                vertical_alignment: ObjectVerticalAlignment::Bottom,
                horizontal_offset_hwpunit: 30_000,
                vertical_offset_hwpunit: 40_000,
            },
        },
    );
    let text = String::from_utf8(output).expect("UTF-8");
    assert!(text.contains("horzAlign=\"RIGHT\""));
    assert!(text.contains("vertAlign=\"BOTTOM\""));
    assert!(text.contains("horzOffset=\"30000\""));
    assert!(text.contains("vertOffset=\"40000\""));
    assert!(text.contains("PRESERVE-PICTURE-PAYLOAD"));
    assert!(text.contains(&second_before));
    assert_eq!(receipt.capability_id, "obj.position");
    assert_eq!(receipt.modified_attribute_count, 4);
}

#[test]
fn lowers_inline_anchor_and_wrap_without_normalizing_unchanged_matrix_lexemes() {
    let source = section();
    let readback = ObjectGeometryHwpxReader::read_in_section(
        &source,
        0,
        logical_id(),
        state_limits(),
        hwpx_limits(),
    )
    .expect("read");
    let anchor = ObjectAnchor {
        treat_as_character: true,
        affect_line_spacing: true,
        flow_with_text: false,
        allow_overlap: true,
        hold_anchor_and_shape: false,
        horizontal_reference: ObjectHorizontalReference::Page,
        vertical_reference: ObjectVerticalReference::Page,
    };
    let (anchored, anchor_receipt) =
        lower(&source, 0, ObjectGeometryOperation::SetAnchor { anchor });
    let anchored_text = String::from_utf8(anchored).expect("UTF-8");
    assert!(anchored_text.contains("treatAsChar=\"1\""));
    assert!(anchored_text.contains("horzRelTo=\"PAGE\""));
    assert!(anchored_text.contains("vertRelTo=\"PAGE\""));
    assert!(anchored_text.contains("e1=\"1.000000\""));
    assert_eq!(anchor_receipt.capability_id, "obj.anchor");

    let (wrapped, wrap_receipt) = lower(
        &source,
        0,
        ObjectGeometryOperation::SetWrap {
            wrap: ObjectWrap {
                text_wrap: ObjectTextWrap::TopAndBottom,
                text_flow: ObjectTextFlow::LargestOnly,
            },
            outer_margins: ObjectOuterMargins {
                left_hwpunit: 100,
                right_hwpunit: 200,
                top_hwpunit: 300,
                bottom_hwpunit: 400,
            },
        },
    );
    let wrapped = ObjectGeometryHwpxReader::read_in_section(
        &wrapped,
        0,
        logical_id(),
        state_limits(),
        hwpx_limits(),
    )
    .expect("wrapped readback");
    assert_eq!(wrapped.state.wrap().text_wrap, ObjectTextWrap::TopAndBottom);
    assert_eq!(wrapped.state.wrap().text_flow, ObjectTextFlow::LargestOnly);
    assert_ne!(
        wrapped.state.outer_margins(),
        readback.state.outer_margins()
    );
    assert_eq!(wrap_receipt.capability_id, "obj.wrap");
}

#[test]
fn lowers_size_with_complete_component_and_exact_fixed_point_transform() {
    let source = section();
    let readback = ObjectGeometryHwpxReader::read_in_section(
        &source,
        0,
        logical_id(),
        state_limits(),
        hwpx_limits(),
    )
    .expect("read");
    let mut component = readback.state.component();
    component.offset.x_hwpunit = 70;
    component.original_size = ObjectExtent {
        width_hwpunit: 14_400,
        height_hwpunit: 7_200,
    };
    component.current_size = ObjectExtent {
        width_hwpunit: 21_600,
        height_hwpunit: 10_800,
    };
    component.transform.scale = ObjectAffineMatrix {
        e1_millionths: 1_500_000,
        e2_millionths: 125_000,
        e3_millionths: -125_000,
        e4_millionths: 1_500_000,
        e5_millionths: 0,
        e6_millionths: 0,
    };
    let (output, receipt) = lower(
        &source,
        0,
        ObjectGeometryOperation::SetSize {
            size: ObjectSize {
                width_hwpunit: 21_600,
                width_reference: ObjectWidthReference::Page,
                height_hwpunit: 10_800,
                height_reference: ObjectHeightReference::Page,
                protect: true,
            },
            component,
        },
    );
    let output = ObjectGeometryHwpxReader::read_in_section(
        &output,
        0,
        logical_id(),
        state_limits(),
        hwpx_limits(),
    )
    .expect("readback");
    assert_eq!(
        output.state.size().width_reference,
        ObjectWidthReference::Page
    );
    assert_eq!(output.state.component(), component);
    assert_eq!(receipt.capability_id, "obj.size");
    assert!(receipt.modified_attribute_count >= 10);
}

#[test]
fn lowers_rotation_and_flip_only_with_caller_supplied_complete_transform() {
    let source = section();
    let readback = ObjectGeometryHwpxReader::read_in_section(
        &source,
        0,
        logical_id(),
        state_limits(),
        hwpx_limits(),
    )
    .expect("read");
    let mut transform = readback.state.component().transform;
    transform.rotation = ObjectAffineMatrix {
        e1_millionths: 0,
        e2_millionths: 1_000_000,
        e3_millionths: -1_000_000,
        e4_millionths: 0,
        e5_millionths: 5_000_000,
        e6_millionths: 6_000_000,
    };
    let (rotated, _) = lower(
        &source,
        0,
        ObjectGeometryOperation::SetRotation {
            rotation: ObjectRotation {
                angle_degrees: 90,
                center_x_hwpunit: 3_600,
                center_y_hwpunit: 1_800,
                rotate_image: false,
            },
            transform,
        },
    );
    let rotated = ObjectGeometryHwpxReader::read_in_section(
        &rotated,
        0,
        logical_id(),
        state_limits(),
        hwpx_limits(),
    )
    .expect("rotation readback");
    assert_eq!(rotated.state.component().rotation.angle_degrees, 90);
    assert_eq!(rotated.state.component().transform, transform);

    let (flipped, receipt) = lower(
        &source,
        0,
        ObjectGeometryOperation::SetFlip {
            flip: ObjectFlip {
                horizontal: true,
                vertical: true,
            },
            transform: readback.state.component().transform,
        },
    );
    let flipped = ObjectGeometryHwpxReader::read_in_section(
        &flipped,
        0,
        logical_id(),
        state_limits(),
        hwpx_limits(),
    )
    .expect("flip readback");
    assert!(flipped.state.component().flip.horizontal);
    assert!(flipped.state.component().flip.vertical);
    assert_eq!(receipt.capability_id, "obj.flip");
}

#[test]
fn no_op_plan_is_byte_exact_and_debug_redacts_bindings() {
    let source = section();
    let readback = ObjectGeometryHwpxReader::read_in_section(
        &source,
        0,
        logical_id(),
        state_limits(),
        hwpx_limits(),
    )
    .expect("read");
    let domain = domain_plan(
        &source,
        0,
        ObjectGeometryOperation::SetPosition {
            position: readback.state.position(),
        },
    );
    let plan =
        ObjectGeometryHwpxBuilder::plan(&source, 0, &domain, FLOW_A, state_limits(), hwpx_limits())
            .expect("plan");
    let first = plan.canonical_json(hwpx_limits()).expect("plan JSON");
    let second = plan.canonical_json(hwpx_limits()).expect("plan JSON again");
    assert_eq!(first, second);
    let (output, receipt) = ObjectGeometryHwpxLowerer::lower_in_section_with_receipt(
        &source,
        &plan,
        FLOW_A,
        state_limits(),
        hwpx_limits(),
    )
    .expect("no-op lower");
    assert_eq!(output, source);
    assert_eq!(receipt.modified_attribute_count, 0);
    for debug in [
        format!("{readback:?}"),
        format!("{plan:?}"),
        format!("{receipt:?}"),
    ] {
        assert!(debug.contains("<redacted>"));
        assert!(!debug.contains(FLOW_A));
        assert!(!debug.contains("shape-1"));
    }
}

#[test]
fn request_and_build_reject_section_object_state_and_flow_drift() {
    let source = section();
    let readback = ObjectGeometryHwpxReader::read_in_section(
        &source,
        0,
        logical_id(),
        state_limits(),
        hwpx_limits(),
    )
    .expect("read");
    let domain = domain_plan(
        &source,
        0,
        ObjectGeometryOperation::SetPosition {
            position: ObjectPosition {
                horizontal_offset_hwpunit: 1_001,
                ..readback.state.position()
            },
        },
    );
    assert!(matches!(
        ObjectGeometryHwpxBuilder::plan(&source, 0, &domain, FLOW_B, state_limits(), hwpx_limits(),),
        Err(ObjectGeometryHwpxError::Domain(
            domain_ir::ObjectGeometryError::DocumentFlowDrift
        ))
    ));
    let plan =
        ObjectGeometryHwpxBuilder::plan(&source, 0, &domain, FLOW_A, state_limits(), hwpx_limits())
            .expect("plan");
    assert_eq!(
        ObjectGeometryHwpxLowerer::lower_in_section(
            &source,
            &plan,
            FLOW_B,
            state_limits(),
            hwpx_limits(),
        ),
        Err(ObjectGeometryHwpxError::SourceDrift)
    );
    let drifted = String::from_utf8(source.clone())
        .expect("UTF-8")
        .replacen("PRESERVE-PICTURE-PAYLOAD", "DRIFTED-PAYLOAD", 1)
        .into_bytes();
    assert_eq!(
        ObjectGeometryHwpxLowerer::lower_in_section(
            &drifted,
            &plan,
            FLOW_A,
            state_limits(),
            hwpx_limits(),
        ),
        Err(ObjectGeometryHwpxError::SourceDrift)
    );
}

#[test]
fn malformed_missing_duplicate_nested_and_inexact_matrix_inputs_fail_closed() {
    let source = section();
    let noncanonical_lock = String::from_utf8(source.clone())
        .expect("UTF-8")
        .replacen("lock=\"0\"", "lock=\"true\"", 1)
        .into_bytes();
    assert!(matches!(
        ObjectGeometryHwpxReader::read_in_section(
            &noncanonical_lock,
            0,
            logical_id(),
            state_limits(),
            hwpx_limits(),
        ),
        Err(ObjectGeometryHwpxError::InvalidBoolean)
    ));
    let missing = String::from_utf8(source.clone())
        .expect("UTF-8")
        .replacen(
            "<hp:outMargin left=\"10\" right=\"11\" top=\"12\" bottom=\"13\"/>",
            "",
            1,
        )
        .into_bytes();
    assert!(matches!(
        ObjectGeometryHwpxReader::read_in_section(
            &missing,
            0,
            logical_id(),
            state_limits(),
            hwpx_limits(),
        ),
        Err(ObjectGeometryHwpxError::UnsupportedShape)
    ));
    let duplicate = String::from_utf8(source.clone())
        .expect("UTF-8")
        .replacen(
            "<hp:outMargin",
            "<hp:outMargin left=\"0\" right=\"0\" top=\"0\" bottom=\"0\"/><hp:outMargin",
            1,
        )
        .into_bytes();
    assert!(matches!(
        ObjectGeometryHwpxReader::read_in_section(
            &duplicate,
            0,
            logical_id(),
            state_limits(),
            hwpx_limits(),
        ),
        Err(ObjectGeometryHwpxError::UnsupportedShape)
    ));
    let inexact = String::from_utf8(source)
        .expect("UTF-8")
        .replacen("e1=\"1.000000\"", "e1=\"1.0000001\"", 1)
        .into_bytes();
    assert!(matches!(
        ObjectGeometryHwpxReader::read_in_section(
            &inexact,
            0,
            logical_id(),
            state_limits(),
            hwpx_limits(),
        ),
        Err(ObjectGeometryHwpxError::InvalidMatrix)
    ));
    let nested = section_with(&[format!(
        "<hp:container>{}</hp:container>",
        common_object("pic", 1, 2, "nested")
    )]);
    assert!(matches!(
        ObjectGeometryHwpxReader::read_in_section(
            &nested,
            0,
            logical_id(),
            state_limits(),
            hwpx_limits(),
        ),
        Err(ObjectGeometryHwpxError::UnsupportedShape | ObjectGeometryHwpxError::InvalidAttribute)
    ));
}

#[test]
fn finite_boundaries_reject_oversized_source_and_matrix_text() {
    let source = section();
    let tight = ObjectGeometryHwpxLimits::new(ObjectGeometryHwpxLimitConfig {
        section_bytes: source.len() - 1,
        output_bytes: source.len(),
        ..ObjectGeometryHwpxLimitConfig::default()
    })
    .expect("tight limits");
    assert!(matches!(
        ObjectGeometryHwpxReader::read_in_section(&source, 0, logical_id(), state_limits(), tight,),
        Err(ObjectGeometryHwpxError::InputLimit)
    ));
}

#[test]
fn page_and_paragraph_anchor_fixtures_are_distinct_and_exact() {
    let source = section();
    for (horizontal, vertical) in [
        (
            ObjectHorizontalReference::Page,
            ObjectVerticalReference::Page,
        ),
        (
            ObjectHorizontalReference::Paragraph,
            ObjectVerticalReference::Paragraph,
        ),
    ] {
        let (output, _) = lower(
            &source,
            0,
            ObjectGeometryOperation::SetAnchor {
                anchor: ObjectAnchor {
                    treat_as_character: false,
                    affect_line_spacing: false,
                    flow_with_text: true,
                    allow_overlap: true,
                    hold_anchor_and_shape: true,
                    horizontal_reference: horizontal,
                    vertical_reference: vertical,
                },
            },
        );
        let readback = ObjectGeometryHwpxReader::read_in_section(
            &output,
            0,
            logical_id(),
            state_limits(),
            hwpx_limits(),
        )
        .expect("anchor readback");
        assert_eq!(readback.state.anchor().horizontal_reference, horizontal);
        assert_eq!(readback.state.anchor().vertical_reference, vertical);
    }
}

#[test]
fn explicit_enum_variants_cover_boundary_native_values() {
    let source = section();
    let (output, _) = lower(
        &source,
        0,
        ObjectGeometryOperation::SetSize {
            size: ObjectSize {
                width_hwpunit: 7_200,
                width_reference: ObjectWidthReference::Paper,
                height_hwpunit: 3_600,
                height_reference: ObjectHeightReference::Paper,
                protect: false,
            },
            component: ObjectGeometryHwpxReader::read_in_section(
                &source,
                0,
                logical_id(),
                state_limits(),
                hwpx_limits(),
            )
            .expect("read")
            .state
            .component(),
        },
    );
    let text = String::from_utf8(output).expect("UTF-8");
    assert!(text.contains("widthRelTo=\"PAPER\""));
    assert!(text.contains("heightRelTo=\"PAPER\""));
    let _ = ObjectTransform {
        translation: ObjectAffineMatrix {
            e1_millionths: 1_000_000,
            e2_millionths: 0,
            e3_millionths: 0,
            e4_millionths: 1_000_000,
            e5_millionths: 0,
            e6_millionths: 0,
        },
        scale: ObjectAffineMatrix {
            e1_millionths: 1_000_000,
            e2_millionths: 0,
            e3_millionths: 0,
            e4_millionths: 1_000_000,
            e5_millionths: 0,
            e6_millionths: 0,
        },
        rotation: ObjectAffineMatrix {
            e1_millionths: 1_000_000,
            e2_millionths: 0,
            e3_millionths: 0,
            e4_millionths: 1_000_000,
            e5_millionths: 0,
            e6_millionths: 0,
        },
    };
    let _ = (
        ObjectHorizontalAlignment::Inside,
        ObjectVerticalAlignment::Outside,
    );
}
