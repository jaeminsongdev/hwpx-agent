#![allow(clippy::expect_used)] // Test fixtures keep failures local and readable.

use domain_ir::{
    LogicalId, OBJECT_SPECIAL_SCHEMA_VERSION, ObjectIdentity, ObjectSpecialBuilder,
    ObjectSpecialDocumentState, ObjectSpecialDocumentStateDraft, ObjectSpecialLimitConfig,
    ObjectSpecialLimits, ObjectSpecialOperation, ObjectSpecialRequest, ObjectSpecialRequestDraft,
    SpecialObjectKind, SpecialObjectPayload, SpecialObjectState, StaticFormControlKind,
    StaticFormPayload,
};
use hwpx_package::{
    OBJECT_FORM_INSERT_STATIC_EDIT_PROFILE_SHA256, ObjectFormInsertHwpxBuilder,
    ObjectFormInsertHwpxError, ObjectFormInsertHwpxLimitConfig, ObjectFormInsertHwpxLimits,
    ObjectFormInsertHwpxLowerer, ObjectFormInsertHwpxReader,
};

const NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const FLOW_A: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const FLOW_B: &str = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
const STATE_C: &str = "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc";
const STATE_D: &str = "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd";
const STATE_E: &str = "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee";
const STATE_F: &str = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff";

fn state_limits() -> ObjectSpecialLimits {
    ObjectSpecialLimits::new(ObjectSpecialLimitConfig::default()).expect("state limits")
}

fn hwpx_limits() -> ObjectFormInsertHwpxLimits {
    ObjectFormInsertHwpxLimits::default()
}

fn shape_identity() -> ObjectIdentity {
    ObjectIdentity {
        logical_object_id: LogicalId::parse("object-10").expect("logical id"),
        native_object_id: 10,
        native_instance_id: 1_010,
    }
}

fn form_identity() -> ObjectIdentity {
    ObjectIdentity {
        logical_object_id: LogicalId::parse("form-12").expect("logical id"),
        native_object_id: 12,
        native_instance_id: 1_012,
    }
}

fn source_state() -> ObjectSpecialDocumentState {
    let resource_ids = Vec::new();
    let relationship_ids = Vec::new();
    let resource_inventory_sha256 = ObjectSpecialDocumentState::resource_inventory_sha256_for(
        &resource_ids,
        &relationship_ids,
        state_limits(),
    )
    .expect("resource digest");
    ObjectSpecialDocumentState::from_draft(
        ObjectSpecialDocumentStateDraft {
            schema_version: OBJECT_SPECIAL_SCHEMA_VERSION.to_owned(),
            document_order: vec![shape_identity().logical_object_id],
            external_objects: vec![shape_identity()],
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
        state_limits(),
    )
    .expect("state")
}

fn form(control_kind: StaticFormControlKind, properties_sha256: &str) -> StaticFormPayload {
    StaticFormPayload {
        control_kind,
        name: "p08field".to_owned(),
        value: "P08 & FORM < VALUE".to_owned(),
        enabled: true,
        printable: true,
        active_content_present: false,
        form_properties_sha256: properties_sha256.to_owned(),
    }
}

fn form_object(control_kind: StaticFormControlKind, properties_sha256: &str) -> SpecialObjectState {
    SpecialObjectState {
        identity: form_identity(),
        object_kind: SpecialObjectKind::FormObject,
        geometry_state_sha256: STATE_C.to_owned(),
        appearance_state_sha256: STATE_D.to_owned(),
        property_state_sha256: STATE_E.to_owned(),
        resource_state_sha256: STATE_F.to_owned(),
        embedded_content_state_sha256: FLOW_A.to_owned(),
        opaque_state_sha256: FLOW_B.to_owned(),
        payload: SpecialObjectPayload::FormObject {
            form: form(control_kind, properties_sha256),
        },
    }
}

fn domain_plan(
    control_kind: StaticFormControlKind,
    properties_sha256: &str,
) -> domain_ir::ObjectSpecialPlan {
    let source = source_state();
    let request = ObjectSpecialRequest::from_draft(
        ObjectSpecialRequestDraft {
            schema_version: OBJECT_SPECIAL_SCHEMA_VERSION.to_owned(),
            request_id: LogicalId::parse("form-request").expect("request id"),
            expected_source_state_sha256: source
                .canonical_sha256(state_limits())
                .expect("state digest"),
            expected_document_flow_sha256: FLOW_A.to_owned(),
            target_document_flow_sha256: FLOW_B.to_owned(),
            operation: ObjectSpecialOperation::InsertFormObject {
                insertion_index: 1,
                object: form_object(control_kind, properties_sha256),
            },
        },
        &source,
        FLOW_A,
        state_limits(),
    )
    .expect("request");
    ObjectSpecialBuilder::plan(&source, &request, FLOW_A, state_limits()).expect("domain plan")
}

fn section() -> Vec<u8> {
    format!(
        "<?xml version=\"1.0\"?><hp:sec xmlns:hp=\"{NS}\"><hp:p id=\"1\"><hp:run><hp:t>BEFORE</hp:t><hp:rect id=\"10\" instid=\"1010\" href=\"\"><hp:outMargin left=\"0\" right=\"0\" top=\"0\" bottom=\"0\"/></hp:rect><hp:t>AFTER</hp:t></hp:run></hp:p></hp:sec>"
    )
    .into_bytes()
}

fn qualified_domain_plan() -> domain_ir::ObjectSpecialPlan {
    domain_plan(
        StaticFormControlKind::EditBox,
        OBJECT_FORM_INSERT_STATIC_EDIT_PROFILE_SHA256,
    )
}

#[test]
fn inserts_one_exact_static_edit_and_preserves_every_other_byte() {
    let source = section();
    let domain = qualified_domain_plan();
    let plan =
        ObjectFormInsertHwpxBuilder::plan(&source, &domain, FLOW_A, state_limits(), hwpx_limits())
            .expect("HWPX plan");
    let (output, receipt) = ObjectFormInsertHwpxLowerer::lower_in_section_with_receipt(
        &source,
        &plan,
        FLOW_A,
        state_limits(),
        hwpx_limits(),
    )
    .expect("lower");
    let output_text = String::from_utf8(output.clone()).expect("UTF-8");
    let start = output_text.find("<hp:edit ").expect("inserted form start");
    let end = output_text[start..]
        .find("</hp:edit>")
        .expect("inserted form end")
        + start
        + "</hp:edit>".len();
    assert_eq!(
        format!("{}{}", &output_text[..start], &output_text[end..]),
        String::from_utf8(source).expect("source UTF-8")
    );
    assert!(output_text.contains("name=\"p08field\""));
    assert!(output_text.contains("<hp:text>P08 &amp; FORM &lt; VALUE</hp:text>"));
    assert_eq!(receipt.capability_id, "obj.form_object_insert");
    assert_eq!(receipt.modified_span_count, 1);
    assert_eq!(receipt.target_document_flow_sha256, FLOW_B);
    let readback =
        ObjectFormInsertHwpxReader::read_in_section(&output, domain.target_state(), hwpx_limits())
            .expect("target readback");
    assert_eq!(readback.object_count, 2);
    assert!(readback.inserted_form_sha256.is_some());
}

#[test]
fn rejects_non_edit_control_and_wrong_profile_digest() {
    for domain in [
        domain_plan(
            StaticFormControlKind::PushButton,
            OBJECT_FORM_INSERT_STATIC_EDIT_PROFILE_SHA256,
        ),
        domain_plan(StaticFormControlKind::EditBox, STATE_C),
    ] {
        assert_eq!(
            ObjectFormInsertHwpxBuilder::plan(
                &section(),
                &domain,
                FLOW_A,
                state_limits(),
                hwpx_limits(),
            ),
            Err(ObjectFormInsertHwpxError::UnsupportedProfile)
        );
    }
}

#[test]
fn stale_source_and_insufficient_output_limit_fail_closed() {
    let source = section();
    let domain = qualified_domain_plan();
    let plan =
        ObjectFormInsertHwpxBuilder::plan(&source, &domain, FLOW_A, state_limits(), hwpx_limits())
            .expect("HWPX plan");
    let mut stale = source.clone();
    stale.extend_from_slice(b" ");
    assert_eq!(
        ObjectFormInsertHwpxLowerer::lower_in_section(
            &stale,
            &plan,
            FLOW_A,
            state_limits(),
            hwpx_limits(),
        ),
        Err(ObjectFormInsertHwpxError::SourceDrift)
    );

    let exact = ObjectFormInsertHwpxLimits::new(ObjectFormInsertHwpxLimitConfig {
        section_bytes: source.len(),
        output_bytes: source.len(),
        ..ObjectFormInsertHwpxLimitConfig::default()
    })
    .expect("tight limits");
    assert_eq!(
        ObjectFormInsertHwpxLowerer::lower_in_section(
            &source,
            &plan,
            FLOW_A,
            state_limits(),
            exact,
        ),
        Err(ObjectFormInsertHwpxError::OutputLimit)
    );
}

#[test]
fn duplicate_identity_root_attribute_and_child_order_drift_are_rejected() {
    let duplicate = String::from_utf8(section())
        .expect("UTF-8")
        .replace(
            "<hp:t>AFTER</hp:t>",
            "<hp:rect id=\"10\" instid=\"1010\"></hp:rect><hp:t>AFTER</hp:t>",
        )
        .into_bytes();
    assert_eq!(
        ObjectFormInsertHwpxReader::read_in_section(&duplicate, &source_state(), hwpx_limits()),
        Err(ObjectFormInsertHwpxError::InvalidIdentity)
    );

    let domain = qualified_domain_plan();
    let plan = ObjectFormInsertHwpxBuilder::plan(
        &section(),
        &domain,
        FLOW_A,
        state_limits(),
        hwpx_limits(),
    )
    .expect("HWPX plan");
    let output = ObjectFormInsertHwpxLowerer::lower_in_section(
        &section(),
        &plan,
        FLOW_A,
        state_limits(),
        hwpx_limits(),
    )
    .expect("lower");
    let root_drift = String::from_utf8(output.clone())
        .expect("UTF-8")
        .replace("alignText=\"LEFT\"", "alignText=\"LEFT\" vendor=\"drift\"")
        .into_bytes();
    assert_eq!(
        ObjectFormInsertHwpxReader::read_in_section(
            &root_drift,
            domain.target_state(),
            hwpx_limits(),
        ),
        Err(ObjectFormInsertHwpxError::ReadbackMismatch)
    );

    let child_order_drift = String::from_utf8(output)
        .expect("UTF-8")
        .replace(
            "<hp:sz width=\"10800\" widthRelTo=\"ABSOLUTE\" height=\"5400\" heightRelTo=\"ABSOLUTE\" protect=\"0\"/><hp:pos",
            "<hp:pos",
        )
        .replace(
            "horzOffset=\"0\"/>",
            "horzOffset=\"0\"/><hp:sz width=\"10800\" widthRelTo=\"ABSOLUTE\" height=\"5400\" heightRelTo=\"ABSOLUTE\" protect=\"0\"/>",
        )
        .into_bytes();
    assert_eq!(
        ObjectFormInsertHwpxReader::read_in_section(
            &child_order_drift,
            domain.target_state(),
            hwpx_limits(),
        ),
        Err(ObjectFormInsertHwpxError::ReadbackMismatch)
    );
}
