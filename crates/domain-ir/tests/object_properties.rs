#![allow(clippy::expect_used)] // Fixtures keep failures local and readable.

use domain_ir::{
    ImageProperties, LogicalId, OBJECT_PROPERTIES_SCHEMA_VERSION, ObjectAltText, ObjectCaption,
    ObjectCaptionNumbering, ObjectCaptionSide, ObjectHyperlink, ObjectPropertiesBuilder,
    ObjectPropertiesError, ObjectPropertiesLimitConfig, ObjectPropertiesLimits,
    ObjectPropertiesOperation, ObjectPropertiesRequest, ObjectPropertiesRequestDraft,
    ObjectPropertiesState, ObjectPropertiesStateDraft, ObjectPropertyKind, ObjectPropertyMargins,
    ObjectTextBoxVerticalAlignment, OpaqueObjectProperty, TextBoxDirection, TextBoxProperties,
};

const FLOW_A: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const FLOW_B: &str = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
const STATE_C: &str = "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc";
const STATE_D: &str = "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd";
const STATE_E: &str = "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee";

fn limits() -> ObjectPropertiesLimits {
    ObjectPropertiesLimits::new(ObjectPropertiesLimitConfig::default()).expect("valid limits")
}

fn margins(seed: u32) -> ObjectPropertyMargins {
    ObjectPropertyMargins {
        left_hwpunit: seed,
        right_hwpunit: seed + 1,
        top_hwpunit: seed + 2,
        bottom_hwpunit: seed + 3,
    }
}

fn text_box() -> TextBoxProperties {
    TextBoxProperties {
        margins: margins(20),
        vertical_alignment: ObjectTextBoxVerticalAlignment::Center,
        direction: TextBoxDirection::Horizontal,
    }
}

fn image() -> ImageProperties {
    ImageProperties {
        original_width_px: 1_920,
        original_height_px: 1_080,
        horizontal_scale_millionths: 1_000_000,
        vertical_scale_millionths: 1_000_000,
        horizontal_dpi: 96,
        vertical_dpi: 96,
    }
}

fn state(kind: ObjectPropertyKind) -> ObjectPropertiesState {
    ObjectPropertiesState::from_draft(
        ObjectPropertiesStateDraft {
            schema_version: OBJECT_PROPERTIES_SCHEMA_VERSION.to_owned(),
            logical_object_id: LogicalId::parse("private-object-1").expect("object id"),
            native_object_id: 41,
            native_instance_id: 99,
            object_kind: kind,
            geometry_state_sha256: FLOW_A.to_owned(),
            appearance_state_sha256: FLOW_B.to_owned(),
            payload_state_sha256: STATE_C.to_owned(),
            resource_inventory_sha256: STATE_D.to_owned(),
            embedded_content_state_sha256: STATE_E.to_owned(),
            outer_margins: margins(10),
            caption: None,
            text_box: (kind == ObjectPropertyKind::TextBox).then(text_box),
            image: (kind == ObjectPropertyKind::Picture).then(image),
            aspect_locked: false,
            protected: false,
            printable: true,
            alt_text: None,
            hyperlink: None,
            opaque_properties: vec![OpaqueObjectProperty {
                namespace: "hp".to_owned(),
                name: "extension".to_owned(),
                value: "private-opaque-value".to_owned(),
            }],
        },
        limits(),
    )
    .expect("valid state")
}

fn request(
    source: &ObjectPropertiesState,
    operation: ObjectPropertiesOperation,
) -> Result<ObjectPropertiesRequest, ObjectPropertiesError> {
    ObjectPropertiesRequest::from_draft(
        ObjectPropertiesRequestDraft {
            schema_version: OBJECT_PROPERTIES_SCHEMA_VERSION.to_owned(),
            request_id: LogicalId::parse("request-1").expect("request id"),
            expected_source_state_sha256: source.canonical_sha256(limits()).expect("state digest"),
            expected_document_flow_sha256: FLOW_A.to_owned(),
            target_document_flow_sha256: FLOW_B.to_owned(),
            operation,
        },
        source,
        FLOW_A,
        limits(),
    )
}

fn build(
    source: &ObjectPropertiesState,
    operation: ObjectPropertiesOperation,
) -> ObjectPropertiesState {
    let request = request(source, operation).expect("request");
    let plan = ObjectPropertiesBuilder::plan(source, &request, FLOW_A, limits()).expect("plan");
    ObjectPropertiesBuilder::build(&plan, source, FLOW_A, limits())
        .expect("build")
        .state
}

#[test]
fn plans_and_builds_all_six_common_property_capabilities() {
    let source = state(ObjectPropertyKind::BasicShape);
    let caption = ObjectCaption {
        side: ObjectCaptionSide::Bottom,
        gap_hwpunit: 360,
        width_hwpunit: 7_200,
        numbering: ObjectCaptionNumbering::Picture,
        label: "Figure".to_owned(),
        text: "private caption".to_owned(),
    };
    let cases = vec![
        (
            ObjectPropertiesOperation::SetMarginCaption {
                outer_margins: margins(100),
                caption: Some(caption),
            },
            "obj.margin_caption",
        ),
        (
            ObjectPropertiesOperation::SetAspectLock { enabled: true },
            "obj.aspect_lock",
        ),
        (
            ObjectPropertiesOperation::SetObjectProtect { enabled: true },
            "obj.object_protect",
        ),
        (
            ObjectPropertiesOperation::SetPrintable { enabled: false },
            "obj.printable",
        ),
        (
            ObjectPropertiesOperation::SetAltText {
                value: Some(ObjectAltText {
                    title: "private title".to_owned(),
                    description: "private description".to_owned(),
                }),
            },
            "obj.alt_text",
        ),
        (
            ObjectPropertiesOperation::SetObjectHyperlink {
                value: Some(ObjectHyperlink::Https {
                    uri: "https://example.invalid/object".to_owned(),
                }),
            },
            "obj.object_hyperlink",
        ),
    ];
    for (operation, capability) in cases {
        assert_eq!(operation.capability_id(), capability);
        assert_ne!(build(&source, operation), source);
    }
}

#[test]
fn textbox_and_image_properties_are_exact_kind_specific_transitions() {
    let source = state(ObjectPropertyKind::TextBox);
    let target = build(
        &source,
        ObjectPropertiesOperation::SetTextBoxProperties {
            properties: TextBoxProperties {
                margins: margins(200),
                vertical_alignment: ObjectTextBoxVerticalAlignment::Bottom,
                direction: TextBoxDirection::VerticalRightToLeft,
            },
        },
    );
    assert_eq!(
        target.text_box().expect("text box").vertical_alignment,
        ObjectTextBoxVerticalAlignment::Bottom
    );

    let source = state(ObjectPropertyKind::Picture);
    let mut properties = image();
    properties.horizontal_scale_millionths = 1_500_000;
    properties.vertical_dpi = 300;
    let target = build(
        &source,
        ObjectPropertiesOperation::SetImageProperties { properties },
    );
    assert_eq!(target.image(), Some(properties));
}

#[test]
fn every_transition_preserves_identity_payload_resources_and_opaque_state() {
    let source = state(ObjectPropertyKind::BasicShape);
    let target = build(
        &source,
        ObjectPropertiesOperation::SetAspectLock { enabled: true },
    );
    let before: serde_json::Value =
        serde_json::from_slice(&source.canonical_json(limits()).expect("json")).expect("value");
    let after: serde_json::Value =
        serde_json::from_slice(&target.canonical_json(limits()).expect("json")).expect("value");
    for field in [
        "logical_object_id",
        "native_object_id",
        "native_instance_id",
        "object_kind",
        "geometry_state_sha256",
        "appearance_state_sha256",
        "payload_state_sha256",
        "resource_inventory_sha256",
        "embedded_content_state_sha256",
        "outer_margins",
        "caption",
        "text_box",
        "image",
        "protected",
        "printable",
        "alt_text",
        "hyperlink",
        "opaque_properties",
    ] {
        assert_eq!(before[field], after[field], "field {field}");
    }
    assert_ne!(before["aspect_locked"], after["aspect_locked"]);
}

#[test]
fn noops_cross_kind_operations_and_invalid_values_fail_closed() {
    let shape = state(ObjectPropertyKind::BasicShape);
    assert_eq!(
        request(
            &shape,
            ObjectPropertiesOperation::SetPrintable { enabled: true }
        ),
        Err(ObjectPropertiesError::Noop)
    );
    assert_eq!(
        request(
            &shape,
            ObjectPropertiesOperation::SetImageProperties {
                properties: image()
            }
        ),
        Err(ObjectPropertiesError::KindMismatch)
    );
    let picture = state(ObjectPropertyKind::Picture);
    let mut invalid = image();
    invalid.horizontal_dpi = 0;
    assert_eq!(
        request(
            &picture,
            ObjectPropertiesOperation::SetImageProperties {
                properties: invalid
            }
        ),
        Err(ObjectPropertiesError::InvalidValue)
    );
}

#[test]
fn unsafe_links_invalid_text_and_duplicate_opaque_keys_are_rejected() {
    let source = state(ObjectPropertyKind::BasicShape);
    assert_eq!(
        request(
            &source,
            ObjectPropertiesOperation::SetObjectHyperlink {
                value: Some(ObjectHyperlink::Https {
                    uri: "file:///private/path".to_owned()
                })
            }
        ),
        Err(ObjectPropertiesError::InvalidHyperlink)
    );
    assert_eq!(
        request(
            &source,
            ObjectPropertiesOperation::SetAltText {
                value: Some(ObjectAltText {
                    title: "bad\0title".to_owned(),
                    description: String::new()
                })
            }
        ),
        Err(ObjectPropertiesError::InvalidValue)
    );

    let mut draft: ObjectPropertiesStateDraft =
        serde_json::from_slice(&source.canonical_json(limits()).expect("state json"))
            .expect("draft");
    draft.opaque_properties.push(OpaqueObjectProperty {
        namespace: "hp".to_owned(),
        name: "extension".to_owned(),
        value: "collision".to_owned(),
    });
    assert_eq!(
        ObjectPropertiesState::from_draft(draft, limits()),
        Err(ObjectPropertiesError::InvalidOpaqueState)
    );
}

#[test]
fn request_and_build_both_reject_state_and_flow_drift() {
    let source = state(ObjectPropertyKind::BasicShape);
    let request = request(
        &source,
        ObjectPropertiesOperation::SetAspectLock { enabled: true },
    )
    .expect("request");
    assert_eq!(
        ObjectPropertiesBuilder::plan(&source, &request, FLOW_B, limits()),
        Err(ObjectPropertiesError::DocumentFlowDrift)
    );
    let plan = ObjectPropertiesBuilder::plan(&source, &request, FLOW_A, limits()).expect("plan");
    let drifted = build(
        &source,
        ObjectPropertiesOperation::SetObjectProtect { enabled: true },
    );
    assert_eq!(
        ObjectPropertiesBuilder::build(&plan, &drifted, FLOW_A, limits()),
        Err(ObjectPropertiesError::SourceStateDrift)
    );
    assert_eq!(
        ObjectPropertiesBuilder::build(&plan, &source, FLOW_B, limits()),
        Err(ObjectPropertiesError::DocumentFlowDrift)
    );
}

#[test]
fn strict_json_rejects_duplicate_unknown_and_oversized_input() {
    let source = state(ObjectPropertyKind::BasicShape);
    let request = request(
        &source,
        ObjectPropertiesOperation::SetAspectLock { enabled: true },
    )
    .expect("request");
    let json = request.canonical_json(limits()).expect("json");
    assert!(ObjectPropertiesRequest::from_json(&json, &source, FLOW_A, limits()).is_ok());

    let duplicate = br#"{"schema_version":"hwpx-agent.object-properties/v1","schema_version":"hwpx-agent.object-properties/v1"}"#;
    assert_eq!(
        ObjectPropertiesRequest::from_json(duplicate, &source, FLOW_A, limits()),
        Err(ObjectPropertiesError::InvalidJson)
    );
    let mut unknown: serde_json::Value = serde_json::from_slice(&json).expect("value");
    unknown
        .as_object_mut()
        .expect("object")
        .insert("unknown".to_owned(), serde_json::Value::Bool(true));
    assert_eq!(
        ObjectPropertiesRequest::from_json(
            &serde_json::to_vec(&unknown).expect("bytes"),
            &source,
            FLOW_A,
            limits(),
        ),
        Err(ObjectPropertiesError::InvalidJson)
    );
    assert_eq!(
        ObjectPropertiesRequest::from_json(
            &vec![b' '; limits().config().input_bytes + 1],
            &source,
            FLOW_A,
            limits(),
        ),
        Err(ObjectPropertiesError::InputLimit)
    );
}

#[test]
fn debug_and_error_codes_are_bounded_and_redacted() {
    let source = state(ObjectPropertyKind::BasicShape);
    let request = request(
        &source,
        ObjectPropertiesOperation::SetAltText {
            value: Some(ObjectAltText {
                title: "private title".to_owned(),
                description: "private description".to_owned(),
            }),
        },
    )
    .expect("request");
    let plan = ObjectPropertiesBuilder::plan(&source, &request, FLOW_A, limits()).expect("plan");
    let debug = format!("{source:?} {request:?} {plan:?}");
    for secret in [
        "private-object-1",
        "private title",
        "private description",
        "private-opaque-value",
        FLOW_A,
    ] {
        assert!(!debug.contains(secret));
    }
    assert_eq!(
        ObjectPropertiesError::PlanTampered.code(),
        "object_properties_plan_tampered"
    );
}
