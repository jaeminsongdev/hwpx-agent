#![allow(clippy::expect_used)] // Fixtures keep failures local and readable.

use domain_ir::{
    DrawingGalleryPayload, GalleryAssetKind, LogicalId, OBJECT_SPECIAL_SCHEMA_VERSION,
    ObjectCaption, ObjectCaptionNumbering, ObjectCaptionSide, ObjectIdentity, ObjectSpecialBuilder,
    ObjectSpecialDocumentState, ObjectSpecialDocumentStateDraft, ObjectSpecialError,
    ObjectSpecialLimitConfig, ObjectSpecialLimits, ObjectSpecialOperation, ObjectSpecialRequest,
    ObjectSpecialRequestDraft, ParagraphBandPayload, ParagraphBandPlacement, SpecialObjectKind,
    SpecialObjectPayload, SpecialObjectState, StaticFormControlKind, StaticFormPayload,
};

const FLOW_A: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const FLOW_B: &str = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
const STATE_C: &str = "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc";
const STATE_D: &str = "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd";
const STATE_E: &str = "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee";
const STATE_F: &str = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff";

fn limits() -> ObjectSpecialLimits {
    ObjectSpecialLimits::new(ObjectSpecialLimitConfig::default()).expect("valid limits")
}

fn identity(name: &str, native: u32) -> ObjectIdentity {
    ObjectIdentity {
        logical_object_id: LogicalId::parse(name).expect("logical id"),
        native_object_id: native,
        native_instance_id: native + 1_000,
    }
}

fn source() -> ObjectSpecialDocumentState {
    let resource_ids = vec!["asset-existing".to_owned()];
    let relationship_ids = vec!["rId-existing".to_owned()];
    let resource_inventory_sha256 = ObjectSpecialDocumentState::resource_inventory_sha256_for(
        &resource_ids,
        &relationship_ids,
        limits(),
    )
    .expect("resource digest");
    ObjectSpecialDocumentState::from_draft(
        ObjectSpecialDocumentStateDraft {
            schema_version: OBJECT_SPECIAL_SCHEMA_VERSION.to_owned(),
            document_order: vec![
                LogicalId::parse("existing-a").expect("id"),
                LogicalId::parse("existing-b").expect("id"),
            ],
            external_objects: vec![identity("existing-a", 10), identity("existing-b", 20)],
            special_objects: Vec::new(),
            captions: Vec::new(),
            paragraph_ids: vec![LogicalId::parse("paragraph-1").expect("paragraph")],
            resource_ids,
            relationship_ids,
            document_payload_sha256: STATE_C.to_owned(),
            document_properties_sha256: STATE_D.to_owned(),
            resource_inventory_sha256,
            paragraph_inventory_sha256: STATE_E.to_owned(),
            opaque_document_state_sha256: STATE_F.to_owned(),
        },
        limits(),
    )
    .expect("valid source")
}

fn base_object(
    name: &str,
    native: u32,
    kind: SpecialObjectKind,
    payload: SpecialObjectPayload,
) -> SpecialObjectState {
    SpecialObjectState {
        identity: identity(name, native),
        object_kind: kind,
        geometry_state_sha256: FLOW_A.to_owned(),
        appearance_state_sha256: FLOW_B.to_owned(),
        property_state_sha256: STATE_C.to_owned(),
        resource_state_sha256: STATE_D.to_owned(),
        embedded_content_state_sha256: STATE_E.to_owned(),
        opaque_state_sha256: STATE_F.to_owned(),
        payload,
    }
}

fn gallery(name: &str, native: u32) -> SpecialObjectState {
    base_object(
        name,
        native,
        SpecialObjectKind::DrawingGallery,
        SpecialObjectPayload::DrawingGallery {
            gallery: DrawingGalleryPayload {
                asset_id: format!("asset-{name}"),
                relationship_id: format!("rId-{name}"),
                asset_kind: GalleryAssetKind::Shape,
                media_type: "application/x-hwpx-shape".to_owned(),
                byte_len: 128,
                payload_sha256: STATE_C.to_owned(),
                template_family: "callout".to_owned(),
                template_key: "rounded-1".to_owned(),
            },
        },
    )
}

fn form(name: &str, native: u32, active: bool) -> SpecialObjectState {
    base_object(
        name,
        native,
        SpecialObjectKind::FormObject,
        SpecialObjectPayload::FormObject {
            form: StaticFormPayload {
                control_kind: StaticFormControlKind::CheckBox,
                name: "consent".to_owned(),
                value: "private value".to_owned(),
                enabled: true,
                printable: true,
                active_content_present: active,
                form_properties_sha256: STATE_D.to_owned(),
            },
        },
    )
}

fn band(name: &str, native: u32) -> SpecialObjectState {
    base_object(
        name,
        native,
        SpecialObjectKind::ParagraphBand,
        SpecialObjectPayload::ParagraphBand {
            band: ParagraphBandPayload {
                paragraph_id: LogicalId::parse("paragraph-1").expect("paragraph"),
                placement: ParagraphBandPlacement::BehindParagraph,
                height_hwpunit: 3_600,
                width_hwpunit: 14_400,
                band_style_sha256: STATE_E.to_owned(),
            },
        },
    )
}

fn caption() -> ObjectCaption {
    ObjectCaption {
        side: ObjectCaptionSide::Bottom,
        gap_hwpunit: 360,
        width_hwpunit: 7_200,
        numbering: ObjectCaptionNumbering::Picture,
        label: "Figure".to_owned(),
        text: "private caption".to_owned(),
    }
}

fn request(
    source: &ObjectSpecialDocumentState,
    operation: ObjectSpecialOperation,
) -> Result<ObjectSpecialRequest, ObjectSpecialError> {
    ObjectSpecialRequest::from_draft(
        ObjectSpecialRequestDraft {
            schema_version: OBJECT_SPECIAL_SCHEMA_VERSION.to_owned(),
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
    source: &ObjectSpecialDocumentState,
    operation: ObjectSpecialOperation,
) -> ObjectSpecialDocumentState {
    let request = request(source, operation).expect("request");
    let plan = ObjectSpecialBuilder::plan(source, &request, FLOW_A, limits()).expect("plan");
    ObjectSpecialBuilder::build(&plan, source, FLOW_A, limits())
        .expect("build")
        .state
}

#[test]
fn plans_and_builds_all_four_exact_special_capabilities() {
    let source = source();
    let cases = vec![
        ObjectSpecialOperation::InsertDrawingGallery {
            insertion_index: 1,
            object: gallery("gallery-1", 30),
        },
        ObjectSpecialOperation::InsertFormObject {
            insertion_index: 1,
            object: form("form-1", 40, false),
        },
        ObjectSpecialOperation::InsertParagraphBand {
            insertion_index: 1,
            object: band("band-1", 50),
        },
        ObjectSpecialOperation::InsertCaption {
            target: identity("existing-a", 10),
            caption: caption(),
        },
    ];
    let expected = [
        "obj.drawing_gallery",
        "obj.form_object_insert",
        "obj.paragraph_band_object",
        "obj.caption_insert",
    ];
    for (operation, capability) in cases.into_iter().zip(expected) {
        assert_eq!(operation.capability_id(), capability);
        let target = build(&source, operation);
        if capability == "obj.caption_insert" {
            assert_eq!(target.captions().len(), 1);
            assert_eq!(target.special_objects().len(), 0);
        } else {
            assert_eq!(target.special_objects().len(), 1);
            assert_eq!(target.document_order().len(), 3);
        }
    }
}

#[test]
fn insertion_preserves_document_state_and_updates_only_exact_inventories() {
    let source = source();
    let target = build(
        &source,
        ObjectSpecialOperation::InsertDrawingGallery {
            insertion_index: 1,
            object: gallery("gallery-1", 30),
        },
    );
    let before: serde_json::Value =
        serde_json::from_slice(&source.canonical_json(limits()).expect("json")).expect("value");
    let after: serde_json::Value =
        serde_json::from_slice(&target.canonical_json(limits()).expect("json")).expect("value");
    for field in [
        "external_objects",
        "captions",
        "paragraph_ids",
        "document_payload_sha256",
        "document_properties_sha256",
        "paragraph_inventory_sha256",
        "opaque_document_state_sha256",
    ] {
        assert_eq!(before[field], after[field], "field {field}");
    }
    assert_ne!(before["document_order"], after["document_order"]);
    assert_ne!(before["resource_ids"], after["resource_ids"]);
    assert_ne!(
        before["resource_inventory_sha256"],
        after["resource_inventory_sha256"]
    );
}

#[test]
fn identity_resource_kind_and_index_collisions_fail_closed() {
    let source = source();
    assert_eq!(
        request(
            &source,
            ObjectSpecialOperation::InsertDrawingGallery {
                insertion_index: 3,
                object: gallery("gallery-1", 30)
            }
        ),
        Err(ObjectSpecialError::InvalidInsertionIndex)
    );
    assert_eq!(
        request(
            &source,
            ObjectSpecialOperation::InsertDrawingGallery {
                insertion_index: 1,
                object: gallery("existing-a", 30)
            }
        ),
        Err(ObjectSpecialError::InvalidIdentity)
    );
    assert_eq!(
        request(
            &source,
            ObjectSpecialOperation::InsertFormObject {
                insertion_index: 1,
                object: gallery("gallery-1", 30)
            }
        ),
        Err(ObjectSpecialError::KindMismatch)
    );
    let mut collision = gallery("gallery-1", 30);
    if let SpecialObjectPayload::DrawingGallery { gallery } = &mut collision.payload {
        gallery.asset_id = "asset-existing".to_owned();
    }
    assert_eq!(
        request(
            &source,
            ObjectSpecialOperation::InsertDrawingGallery {
                insertion_index: 1,
                object: collision
            }
        ),
        Err(ObjectSpecialError::InvalidPayload)
    );
}

#[test]
fn active_form_missing_paragraph_and_duplicate_caption_are_denied() {
    let source = source();
    assert_eq!(
        request(
            &source,
            ObjectSpecialOperation::InsertFormObject {
                insertion_index: 1,
                object: form("form-1", 40, true)
            }
        ),
        Err(ObjectSpecialError::ActiveContentDenied)
    );
    let mut missing = band("band-1", 50);
    if let SpecialObjectPayload::ParagraphBand { band } = &mut missing.payload {
        band.paragraph_id = LogicalId::parse("missing-paragraph").expect("id");
    }
    assert_eq!(
        request(
            &source,
            ObjectSpecialOperation::InsertParagraphBand {
                insertion_index: 1,
                object: missing
            }
        ),
        Err(ObjectSpecialError::InvalidPayload)
    );
    let captioned = build(
        &source,
        ObjectSpecialOperation::InsertCaption {
            target: identity("existing-a", 10),
            caption: caption(),
        },
    );
    assert_eq!(
        request(
            &captioned,
            ObjectSpecialOperation::InsertCaption {
                target: identity("existing-a", 10),
                caption: caption()
            }
        ),
        Err(ObjectSpecialError::InvalidCaption)
    );
}

#[test]
fn request_and_build_recheck_exact_state_and_flow() {
    let source = source();
    let request = request(
        &source,
        ObjectSpecialOperation::InsertFormObject {
            insertion_index: 1,
            object: form("form-1", 40, false),
        },
    )
    .expect("request");
    assert_eq!(
        ObjectSpecialBuilder::plan(&source, &request, FLOW_B, limits()),
        Err(ObjectSpecialError::DocumentFlowDrift)
    );
    let plan = ObjectSpecialBuilder::plan(&source, &request, FLOW_A, limits()).expect("plan");
    let drifted = build(
        &source,
        ObjectSpecialOperation::InsertCaption {
            target: identity("existing-b", 20),
            caption: caption(),
        },
    );
    assert_eq!(
        ObjectSpecialBuilder::build(&plan, &drifted, FLOW_A, limits()),
        Err(ObjectSpecialError::SourceStateDrift)
    );
    assert_eq!(
        ObjectSpecialBuilder::build(&plan, &source, FLOW_B, limits()),
        Err(ObjectSpecialError::DocumentFlowDrift)
    );
}

#[test]
fn strict_json_rejects_duplicate_unknown_and_oversized_input() {
    let source = source();
    let request = request(
        &source,
        ObjectSpecialOperation::InsertCaption {
            target: identity("existing-a", 10),
            caption: caption(),
        },
    )
    .expect("request");
    let json = request.canonical_json(limits()).expect("json");
    assert!(ObjectSpecialRequest::from_json(&json, &source, FLOW_A, limits()).is_ok());
    let duplicate = br#"{"schema_version":"hwpx-agent.object-special/v1","schema_version":"hwpx-agent.object-special/v1"}"#;
    assert_eq!(
        ObjectSpecialRequest::from_json(duplicate, &source, FLOW_A, limits()),
        Err(ObjectSpecialError::InvalidJson)
    );
    let mut unknown: serde_json::Value = serde_json::from_slice(&json).expect("value");
    unknown
        .as_object_mut()
        .expect("object")
        .insert("unknown".to_owned(), serde_json::Value::Bool(true));
    assert_eq!(
        ObjectSpecialRequest::from_json(
            &serde_json::to_vec(&unknown).expect("bytes"),
            &source,
            FLOW_A,
            limits()
        ),
        Err(ObjectSpecialError::InvalidJson)
    );
    assert_eq!(
        ObjectSpecialRequest::from_json(
            &vec![b' '; limits().config().input_bytes + 1],
            &source,
            FLOW_A,
            limits()
        ),
        Err(ObjectSpecialError::InputLimit)
    );
}

#[test]
fn debug_redacts_values_identifiers_resources_and_digests() {
    let source = source();
    let request = request(
        &source,
        ObjectSpecialOperation::InsertFormObject {
            insertion_index: 1,
            object: form("private-form-1", 40, false),
        },
    )
    .expect("request");
    let plan = ObjectSpecialBuilder::plan(&source, &request, FLOW_A, limits()).expect("plan");
    let debug = format!("{source:?} {request:?} {plan:?}");
    for private in [
        "private-form-1",
        "private value",
        "asset-existing",
        "paragraph-1",
        FLOW_A,
        STATE_C,
    ] {
        assert!(!debug.contains(private));
    }
}
