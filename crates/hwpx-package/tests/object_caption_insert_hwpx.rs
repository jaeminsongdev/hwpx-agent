#![allow(clippy::expect_used)] // Test fixtures keep failures local and readable.

use domain_ir::{
    LogicalId, OBJECT_SPECIAL_SCHEMA_VERSION, ObjectCaption, ObjectCaptionNumbering,
    ObjectCaptionSide, ObjectIdentity, ObjectSpecialBuilder, ObjectSpecialDocumentState,
    ObjectSpecialDocumentStateDraft, ObjectSpecialLimitConfig, ObjectSpecialLimits,
    ObjectSpecialOperation, ObjectSpecialRequest, ObjectSpecialRequestDraft,
};
use hwpx_package::{
    ObjectCaptionInsertHwpxBuilder, ObjectCaptionInsertHwpxError,
    ObjectCaptionInsertHwpxLimitConfig, ObjectCaptionInsertHwpxLimits,
    ObjectCaptionInsertHwpxLowerer, ObjectCaptionInsertHwpxReader,
};

const NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const FLOW_A: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const FLOW_B: &str = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
const STATE_C: &str = "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc";
const STATE_D: &str = "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd";
const STATE_E: &str = "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee";

fn state_limits() -> ObjectSpecialLimits {
    ObjectSpecialLimits::new(ObjectSpecialLimitConfig::default()).expect("state limits")
}

fn hwpx_limits() -> ObjectCaptionInsertHwpxLimits {
    ObjectCaptionInsertHwpxLimits::default()
}

fn identity() -> ObjectIdentity {
    ObjectIdentity {
        logical_object_id: LogicalId::parse("object-10").expect("logical id"),
        native_object_id: 10,
        native_instance_id: 1_010,
    }
}

fn state() -> ObjectSpecialDocumentState {
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
            document_order: vec![identity().logical_object_id],
            external_objects: vec![identity()],
            special_objects: Vec::new(),
            captions: Vec::new(),
            paragraph_ids: vec![LogicalId::parse("paragraph-1").expect("paragraph")],
            resource_ids,
            relationship_ids,
            document_payload_sha256: STATE_C.to_owned(),
            document_properties_sha256: STATE_D.to_owned(),
            resource_inventory_sha256,
            paragraph_inventory_sha256: STATE_E.to_owned(),
            opaque_document_state_sha256: FLOW_A.to_owned(),
        },
        state_limits(),
    )
    .expect("state")
}

fn caption(numbering: ObjectCaptionNumbering) -> ObjectCaption {
    ObjectCaption {
        side: ObjectCaptionSide::Bottom,
        gap_hwpunit: 360,
        width_hwpunit: 7_200,
        numbering,
        label: "Figure & ".to_owned(),
        text: "one < two".to_owned(),
    }
}

fn section() -> Vec<u8> {
    format!(
        "<?xml version=\"1.0\"?><hp:sec xmlns:hp=\"{NS}\"><hp:p id=\"1\"><hp:run><hp:t>BEFORE</hp:t><hp:rect id=\"10\" instid=\"1010\" href=\"\"><hp:outMargin left=\"0\" right=\"0\" top=\"0\" bottom=\"0\"/></hp:rect><hp:t>AFTER</hp:t></hp:run></hp:p></hp:sec>"
    )
    .into_bytes()
}

fn domain_plan(numbering: ObjectCaptionNumbering) -> domain_ir::ObjectSpecialPlan {
    let source = state();
    let request = ObjectSpecialRequest::from_draft(
        ObjectSpecialRequestDraft {
            schema_version: OBJECT_SPECIAL_SCHEMA_VERSION.to_owned(),
            request_id: LogicalId::parse("caption-request").expect("request id"),
            expected_source_state_sha256: source
                .canonical_sha256(state_limits())
                .expect("state digest"),
            expected_document_flow_sha256: FLOW_A.to_owned(),
            target_document_flow_sha256: FLOW_B.to_owned(),
            operation: ObjectSpecialOperation::InsertCaption {
                target: identity(),
                caption: caption(numbering),
            },
        },
        &source,
        FLOW_A,
        state_limits(),
    )
    .expect("request");
    ObjectSpecialBuilder::plan(&source, &request, FLOW_A, state_limits()).expect("domain plan")
}

#[test]
fn inserts_one_exact_plain_caption_and_preserves_every_other_byte() {
    let source = section();
    let domain = domain_plan(ObjectCaptionNumbering::None);
    let plan = ObjectCaptionInsertHwpxBuilder::plan(
        &source,
        &domain,
        FLOW_A,
        state_limits(),
        hwpx_limits(),
    )
    .expect("HWPX plan");
    let (output, receipt) = ObjectCaptionInsertHwpxLowerer::lower_in_section_with_receipt(
        &source,
        &plan,
        FLOW_A,
        state_limits(),
        hwpx_limits(),
    )
    .expect("lower");
    let output_text = String::from_utf8(output.clone()).expect("UTF-8");
    let fragment = concat!(
        "<hp:caption side=\"BOTTOM\" fullSz=\"0\" width=\"7200\" gap=\"360\" lastWidth=\"7200\">",
        "<hp:subList><hp:p><hp:run><hp:t>Figure &amp; one &lt; two</hp:t></hp:run></hp:p></hp:subList>",
        "</hp:caption>"
    );
    assert!(output_text.contains(fragment));
    assert_eq!(
        output_text.replace(fragment, ""),
        String::from_utf8(source).expect("source UTF-8")
    );
    assert_eq!(receipt.capability_id, "obj.caption_insert");
    assert_eq!(receipt.modified_span_count, 1);
    assert_eq!(receipt.target_document_flow_sha256, FLOW_B);
    ObjectCaptionInsertHwpxReader::read_in_section(
        &output,
        &identity(),
        Some(&caption(ObjectCaptionNumbering::None)),
        hwpx_limits(),
    )
    .expect("target readback");
}

#[test]
fn rejects_numbered_or_preexisting_caption_profiles_before_output() {
    let source = section();
    let numbered = domain_plan(ObjectCaptionNumbering::Picture);
    assert_eq!(
        ObjectCaptionInsertHwpxBuilder::plan(
            &source,
            &numbered,
            FLOW_A,
            state_limits(),
            hwpx_limits(),
        ),
        Err(ObjectCaptionInsertHwpxError::UnsupportedProfile)
    );

    let existing = String::from_utf8(source)
        .expect("UTF-8")
        .replace(
            "</hp:rect>",
            "<hp:caption side=\"BOTTOM\" fullSz=\"0\" width=\"7200\" gap=\"360\" lastWidth=\"7200\"><hp:subList><hp:p><hp:run><hp:t>existing</hp:t></hp:run></hp:p></hp:subList></hp:caption></hp:rect>",
        )
        .into_bytes();
    let plain = domain_plan(ObjectCaptionNumbering::None);
    assert_eq!(
        ObjectCaptionInsertHwpxBuilder::plan(
            &existing,
            &plain,
            FLOW_A,
            state_limits(),
            hwpx_limits(),
        ),
        Err(ObjectCaptionInsertHwpxError::ReadbackMismatch)
    );
}

#[test]
fn stale_source_and_insufficient_output_limit_fail_closed() {
    let source = section();
    let domain = domain_plan(ObjectCaptionNumbering::None);
    let plan = ObjectCaptionInsertHwpxBuilder::plan(
        &source,
        &domain,
        FLOW_A,
        state_limits(),
        hwpx_limits(),
    )
    .expect("HWPX plan");
    let mut stale = source.clone();
    stale.extend_from_slice(b" ");
    assert_eq!(
        ObjectCaptionInsertHwpxLowerer::lower_in_section(
            &stale,
            &plan,
            FLOW_A,
            state_limits(),
            hwpx_limits(),
        ),
        Err(ObjectCaptionInsertHwpxError::SourceDrift)
    );

    let exact = ObjectCaptionInsertHwpxLimits::new(ObjectCaptionInsertHwpxLimitConfig {
        section_bytes: source.len(),
        output_bytes: source.len(),
        ..ObjectCaptionInsertHwpxLimitConfig::default()
    })
    .expect("tight limits");
    assert_eq!(
        ObjectCaptionInsertHwpxLowerer::lower_in_section(
            &source,
            &plan,
            FLOW_A,
            state_limits(),
            exact,
        ),
        Err(ObjectCaptionInsertHwpxError::OutputLimit)
    );
}

#[test]
fn wrong_namespace_duplicate_identity_and_caption_attribute_drift_are_rejected() {
    let source = section();
    let wrong_namespace = String::from_utf8(source.clone())
        .expect("UTF-8")
        .replace("xmlns:hp=", "xmlns:hp=\"urn:wrong\" ignored=")
        .into_bytes();
    assert!(
        ObjectCaptionInsertHwpxReader::read_in_section(
            &wrong_namespace,
            &identity(),
            None,
            hwpx_limits(),
        )
        .is_err()
    );

    let duplicate = String::from_utf8(source)
        .expect("UTF-8")
        .replace(
            "<hp:t>AFTER</hp:t>",
            "<hp:rect id=\"10\" instid=\"1010\"></hp:rect><hp:t>AFTER</hp:t>",
        )
        .into_bytes();
    assert_eq!(
        ObjectCaptionInsertHwpxReader::read_in_section(
            &duplicate,
            &identity(),
            None,
            hwpx_limits(),
        ),
        Err(ObjectCaptionInsertHwpxError::InvalidIdentity)
    );

    let domain = domain_plan(ObjectCaptionNumbering::None);
    let plan = ObjectCaptionInsertHwpxBuilder::plan(
        &section(),
        &domain,
        FLOW_A,
        state_limits(),
        hwpx_limits(),
    )
    .expect("HWPX plan");
    let output = ObjectCaptionInsertHwpxLowerer::lower_in_section(
        &section(),
        &plan,
        FLOW_A,
        state_limits(),
        hwpx_limits(),
    )
    .expect("lower");
    let drifted = String::from_utf8(output)
        .expect("UTF-8")
        .replace("lastWidth=\"7200\"", "lastWidth=\"7200\" vendor=\"drift\"")
        .into_bytes();
    assert_eq!(
        ObjectCaptionInsertHwpxReader::read_in_section(
            &drifted,
            &identity(),
            Some(&caption(ObjectCaptionNumbering::None)),
            hwpx_limits(),
        ),
        Err(ObjectCaptionInsertHwpxError::ReadbackMismatch)
    );
}
