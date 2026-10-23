#![allow(clippy::expect_used)] // Exact fixtures keep failures local and readable.

use domain_ir::{
    FIELD_ENGINE_SCHEMA_VERSION, FieldAnchor, FieldCacheStatus, FieldCachedResult, FieldDefinition,
    FieldDocumentState, FieldDocumentStateDraft, FieldEngineBuilder, FieldEngineLimitConfig,
    FieldEngineLimits, FieldIdentity, FieldNumberFormat, FieldOperation, FieldPlan, FieldRequest,
    FieldRequestDraft, FieldState, FieldUpdatePolicy, LogicalId, ObjectNumberKind,
    OpaqueFieldProperty,
};
use hwpx_package::{
    FIELD_AUTO_NUMBER_HWPX_PROFILE_ID, FieldAutoNumberHwpxBuilder, FieldAutoNumberHwpxError,
    FieldAutoNumberHwpxLimitConfig, FieldAutoNumberHwpxLimits, FieldAutoNumberHwpxLowerer,
    FieldAutoNumberHwpxReader,
};

const A: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const B: &str = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
const EMPTY: &str = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";

const EMPTY_SECTION: &[u8] = br#"<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"><hp:p id="1" paraPrIDRef="0"><hp:run charPrIDRef="0"><hp:t>A</hp:t><hp:t>B</hp:t></hp:run></hp:p></hs:sec>"#;

const PAGE_SECTION: &[u8] = br#"<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"><hp:p id="1" paraPrIDRef="0"><hp:run charPrIDRef="0"><hp:t>A</hp:t><hp:ctrl><hp:autoNum num="1" numType="PAGE"><hp:autoNumFormat type="DIGIT" userChar="" prefixChar="" suffixChar="" supscript="0"/></hp:autoNum></hp:ctrl><hp:t>B</hp:t></hp:run></hp:p></hs:sec>"#;

fn logical_id(value: &str) -> LogicalId {
    LogicalId::parse(value).expect("logical id")
}

fn state_limits() -> FieldEngineLimits {
    FieldEngineLimits::new(FieldEngineLimitConfig::default()).expect("state limits")
}

fn hwpx_limits() -> FieldAutoNumberHwpxLimits {
    FieldAutoNumberHwpxLimits::new(FieldAutoNumberHwpxLimitConfig::default()).expect("HWPX limits")
}

fn empty_state() -> FieldDocumentState {
    FieldDocumentState::from_draft(
        FieldDocumentStateDraft {
            schema_version: FIELD_ENGINE_SCHEMA_VERSION.to_owned(),
            fields: Vec::new(),
            non_field_content_sha256: A.to_owned(),
            style_catalog_sha256: B.to_owned(),
            reference_inventory_sha256: A.to_owned(),
            resource_inventory_sha256: B.to_owned(),
            opaque_document_state_sha256: A.to_owned(),
        },
        state_limits(),
    )
    .expect("empty state")
}

fn auto_field(
    source: &[u8],
    index: u32,
    inline_ordinal: u32,
    definition: FieldDefinition,
    number: i64,
) -> FieldState {
    let (paragraph_style_sha256, character_style_sha256) =
        FieldAutoNumberHwpxReader::style_sha256_at(source, 0, 0, hwpx_limits())
            .expect("style bindings");
    FieldState {
        identity: FieldIdentity {
            logical_field_id: logical_id(&format!("field-{index}")),
            native_begin_id: index * 2 + 1,
            native_end_id: index * 2 + 2,
        },
        anchor: FieldAnchor {
            paragraph_id: logical_id("paragraph-1"),
            run_ordinal: 0,
            inline_ordinal,
        },
        definition,
        cached_result: FieldCachedResult::Number {
            value: number,
            display: number.to_string(),
        },
        update_policy: FieldUpdatePolicy::RecomputeDirect,
        cache_status: FieldCacheStatus::Current,
        locked: false,
        evaluation_context_sha256: None,
        character_style_sha256,
        paragraph_style_sha256,
        field_payload_sha256: EMPTY.to_owned(),
        opaque_properties: Vec::new(),
    }
}

fn state_with(fields: Vec<FieldState>) -> FieldDocumentState {
    FieldDocumentState::from_draft(
        FieldDocumentStateDraft {
            schema_version: FIELD_ENGINE_SCHEMA_VERSION.to_owned(),
            fields,
            non_field_content_sha256: A.to_owned(),
            style_catalog_sha256: B.to_owned(),
            reference_inventory_sha256: A.to_owned(),
            resource_inventory_sha256: B.to_owned(),
            opaque_document_state_sha256: A.to_owned(),
        },
        state_limits(),
    )
    .expect("state")
}

fn domain_plan(source: &FieldDocumentState, operation: FieldOperation) -> FieldPlan {
    let request = FieldRequest::from_draft(
        FieldRequestDraft {
            schema_version: FIELD_ENGINE_SCHEMA_VERSION.to_owned(),
            request_id: logical_id("request-1"),
            expected_source_state_sha256: source
                .canonical_sha256(state_limits())
                .expect("state digest"),
            expected_document_flow_sha256: A.to_owned(),
            target_document_flow_sha256: B.to_owned(),
            operation,
        },
        source,
        A,
        state_limits(),
    )
    .expect("request");
    FieldEngineBuilder::plan(source, &request, A, state_limits()).expect("domain plan")
}

fn lower(
    source_xml: &[u8],
    source_state: &FieldDocumentState,
    domain: &FieldPlan,
) -> Result<Vec<u8>, FieldAutoNumberHwpxError> {
    let paragraph_ids = [logical_id("paragraph-1")];
    let plan = FieldAutoNumberHwpxBuilder::plan(
        source_xml,
        source_state,
        domain,
        A,
        &paragraph_ids,
        state_limits(),
        hwpx_limits(),
    )?;
    FieldAutoNumberHwpxLowerer::lower_section(
        source_xml,
        &plan,
        source_state,
        A,
        &paragraph_ids,
        state_limits(),
        hwpx_limits(),
    )
}

#[test]
fn inserts_page_and_all_three_object_number_kinds_with_exact_projection() {
    let cases = [
        (
            FieldDefinition::PageNumber {
                format: FieldNumberFormat::Digit,
            },
            "PAGE",
        ),
        (
            FieldDefinition::ObjectNumber {
                object_kind: ObjectNumberKind::Picture,
                format: FieldNumberFormat::Digit,
            },
            "PICTURE",
        ),
        (
            FieldDefinition::ObjectNumber {
                object_kind: ObjectNumberKind::Table,
                format: FieldNumberFormat::Digit,
            },
            "TABLE",
        ),
        (
            FieldDefinition::ObjectNumber {
                object_kind: ObjectNumberKind::Equation,
                format: FieldNumberFormat::Digit,
            },
            "EQUATION",
        ),
    ];
    for (case_index, (definition, expected_kind)) in cases.into_iter().enumerate() {
        let source_state = empty_state();
        let field = auto_field(
            EMPTY_SECTION,
            u32::try_from(case_index + 1).expect("small case"),
            1,
            definition,
            i64::try_from(case_index + 1).expect("small case"),
        );
        let domain = domain_plan(
            &source_state,
            FieldOperation::Insert {
                insertion_index: 0,
                field,
            },
        );
        let output = lower(EMPTY_SECTION, &source_state, &domain).expect("lower");
        let text = String::from_utf8(output.clone()).expect("UTF-8");
        assert!(text.contains(&format!("numType=\"{expected_kind}\"")));
        assert!(text.contains("autoNumFormat type=\"DIGIT\""));
        assert_eq!(
            lower(EMPTY_SECTION, &source_state, &domain).expect("retry"),
            output
        );
    }
}

#[test]
fn updates_only_the_exact_numeric_attribute_and_reads_back_target_state() {
    let source_field = auto_field(
        PAGE_SECTION,
        1,
        1,
        FieldDefinition::PageNumber {
            format: FieldNumberFormat::Digit,
        },
        1,
    );
    let source_state = state_with(vec![source_field.clone()]);
    let domain = domain_plan(
        &source_state,
        FieldOperation::UpdateResult {
            target: source_field.identity,
            cached_result: FieldCachedResult::Number {
                value: 9,
                display: "9".to_owned(),
            },
            evaluation_context_sha256: B.to_owned(),
        },
    );
    let output = lower(PAGE_SECTION, &source_state, &domain).expect("update");
    let before = String::from_utf8(PAGE_SECTION.to_vec()).expect("UTF-8");
    let after = String::from_utf8(output).expect("UTF-8");
    assert_eq!(after, before.replacen("num=\"1\"", "num=\"9\"", 1));
}

#[test]
fn rejects_noncanonical_or_extended_native_shapes() {
    let field = auto_field(
        PAGE_SECTION,
        1,
        1,
        FieldDefinition::PageNumber {
            format: FieldNumberFormat::Digit,
        },
        1,
    );
    let expected = state_with(vec![field]);
    let paragraph_ids = [logical_id("paragraph-1")];
    for malformed in [
        String::from_utf8(PAGE_SECTION.to_vec())
            .expect("UTF-8")
            .replace("num=\"1\"", "num=\"01\""),
        String::from_utf8(PAGE_SECTION.to_vec())
            .expect("UTF-8")
            .replace("num=\"1\"", "num=\"&#49;\""),
        String::from_utf8(PAGE_SECTION.to_vec())
            .expect("UTF-8")
            .replace("type=\"DIGIT\"", "type=\"D&#73;GIT\""),
        String::from_utf8(PAGE_SECTION.to_vec())
            .expect("UTF-8")
            .replace("numType=\"PAGE\"", "numType=\"TOTAL_PAGE\""),
        String::from_utf8(PAGE_SECTION.to_vec())
            .expect("UTF-8")
            .replace("supscript=\"0\"", "supscript=\"1\""),
        String::from_utf8(PAGE_SECTION.to_vec())
            .expect("UTF-8")
            .replace("<hp:autoNum num=", "<hp:autoNum extra=\"x\" num="),
    ] {
        assert_eq!(
            FieldAutoNumberHwpxReader::read_section(
                malformed.as_bytes(),
                &expected,
                &paragraph_ids,
                state_limits(),
                hwpx_limits(),
            ),
            Err(FieldAutoNumberHwpxError::InvalidAutoNumber)
        );
    }
}

#[test]
fn insertion_anchor_and_domain_field_order_must_agree() {
    let source_field = auto_field(
        PAGE_SECTION,
        1,
        1,
        FieldDefinition::PageNumber {
            format: FieldNumberFormat::Digit,
        },
        1,
    );
    for (insertion_index, inline_ordinal, should_pass) in
        [(0, 0, true), (1, 0, false), (1, 2, true)]
    {
        let source_state = state_with(vec![source_field.clone()]);
        let inserted = auto_field(
            PAGE_SECTION,
            2,
            inline_ordinal,
            FieldDefinition::ObjectNumber {
                object_kind: ObjectNumberKind::Table,
                format: FieldNumberFormat::Digit,
            },
            2,
        );
        let domain = domain_plan(
            &source_state,
            FieldOperation::Insert {
                insertion_index,
                field: inserted,
            },
        );
        let result = lower(PAGE_SECTION, &source_state, &domain);
        if should_pass {
            let output = String::from_utf8(result.expect("ordered lower")).expect("UTF-8");
            let table = output.find("numType=\"TABLE\"").expect("table marker");
            let page = output.find("numType=\"PAGE\"").expect("page marker");
            assert_eq!(table < page, insertion_index == 0);
        } else {
            assert_eq!(result, Err(FieldAutoNumberHwpxError::NonRepresentable));
        }
    }
}

#[test]
fn rejects_non_digit_unrelated_field_locked_or_opaque_profiles() {
    let cases = [
        auto_field(
            EMPTY_SECTION,
            1,
            1,
            FieldDefinition::PageNumber {
                format: FieldNumberFormat::RomanUpper,
            },
            1,
        ),
        {
            let mut value = auto_field(
                EMPTY_SECTION,
                2,
                1,
                FieldDefinition::PageNumber {
                    format: FieldNumberFormat::Digit,
                },
                1,
            );
            value.locked = true;
            value
        },
        {
            let mut value = auto_field(
                EMPTY_SECTION,
                3,
                1,
                FieldDefinition::PageNumber {
                    format: FieldNumberFormat::Digit,
                },
                1,
            );
            value.opaque_properties.push(OpaqueFieldProperty {
                namespace: "hp".to_owned(),
                name: "private".to_owned(),
                value_sha256: A.to_owned(),
            });
            value
        },
    ];
    for field in cases {
        let source_state = empty_state();
        let domain = domain_plan(
            &source_state,
            FieldOperation::Insert {
                insertion_index: 0,
                field,
            },
        );
        assert!(matches!(
            FieldAutoNumberHwpxBuilder::plan(
                EMPTY_SECTION,
                &source_state,
                &domain,
                A,
                &[logical_id("paragraph-1")],
                state_limits(),
                hwpx_limits(),
            ),
            Err(FieldAutoNumberHwpxError::NonRepresentable)
        ));
    }
}

#[test]
fn source_flow_and_paragraph_map_drift_fail_before_output() {
    let source_state = empty_state();
    let field = auto_field(
        EMPTY_SECTION,
        1,
        1,
        FieldDefinition::PageNumber {
            format: FieldNumberFormat::Digit,
        },
        1,
    );
    let domain = domain_plan(
        &source_state,
        FieldOperation::Insert {
            insertion_index: 0,
            field,
        },
    );
    let paragraph_ids = [logical_id("paragraph-1")];
    let plan = FieldAutoNumberHwpxBuilder::plan(
        EMPTY_SECTION,
        &source_state,
        &domain,
        A,
        &paragraph_ids,
        state_limits(),
        hwpx_limits(),
    )
    .expect("plan");
    let drifted = String::from_utf8(EMPTY_SECTION.to_vec())
        .expect("UTF-8")
        .replace(">A<", ">X<");
    assert_eq!(
        FieldAutoNumberHwpxLowerer::lower_section(
            drifted.as_bytes(),
            &plan,
            &source_state,
            A,
            &paragraph_ids,
            state_limits(),
            hwpx_limits(),
        ),
        Err(FieldAutoNumberHwpxError::SourceDrift)
    );
    assert_eq!(
        FieldAutoNumberHwpxLowerer::lower_section(
            EMPTY_SECTION,
            &plan,
            &source_state,
            B,
            &paragraph_ids,
            state_limits(),
            hwpx_limits(),
        ),
        Err(FieldAutoNumberHwpxError::SourceDrift)
    );
    assert_eq!(
        FieldAutoNumberHwpxLowerer::lower_section(
            EMPTY_SECTION,
            &plan,
            &source_state,
            A,
            &[logical_id("different-paragraph")],
            state_limits(),
            hwpx_limits(),
        ),
        Err(FieldAutoNumberHwpxError::SourceDrift)
    );
}

#[test]
fn alternate_namespace_prefixes_are_preserved() {
    let source = br#"<s:sec xmlns:s="http://www.hancom.co.kr/hwpml/2011/section" xmlns:q="http://www.hancom.co.kr/hwpml/2011/paragraph"><q:p id="1"><q:run charPrIDRef="0"><q:t>A</q:t></q:run></q:p></s:sec>"#;
    let source_state = empty_state();
    let field = auto_field(
        source,
        1,
        1,
        FieldDefinition::ObjectNumber {
            object_kind: ObjectNumberKind::Table,
            format: FieldNumberFormat::Digit,
        },
        7,
    );
    let domain = domain_plan(
        &source_state,
        FieldOperation::Insert {
            insertion_index: 0,
            field,
        },
    );
    let output = lower(source, &source_state, &domain).expect("alternate prefix");
    let text = String::from_utf8(output).expect("UTF-8");
    assert!(text.contains("<q:ctrl><q:autoNum"));
    assert!(!text.contains("<hp:autoNum"));
}

#[test]
fn limits_and_debug_surfaces_remain_bounded_and_redacted() {
    let invalid = FieldAutoNumberHwpxLimitConfig {
        output_bytes: 1,
        ..FieldAutoNumberHwpxLimitConfig::default()
    };
    assert_eq!(
        FieldAutoNumberHwpxLimits::new(invalid),
        Err(FieldAutoNumberHwpxError::InvalidLimit)
    );
    assert_eq!(
        FIELD_AUTO_NUMBER_HWPX_PROFILE_ID,
        "hwpx-agent.field-auto-number-hwpx.hwpml-2011-digit/v1"
    );
    assert!(!format!("{:?}", FieldAutoNumberHwpxError::SourceDrift).contains(A));
}
