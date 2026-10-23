#![allow(clippy::expect_used)]

use domain_ir::{
    FIELD_ENGINE_SCHEMA_VERSION, FieldAnchor, FieldCacheStatus, FieldCachedResult, FieldDefinition,
    FieldDocumentState, FieldDocumentStateDraft, FieldEngineBuilder, FieldEngineLimitConfig,
    FieldEngineLimits, FieldIdentity, FieldNumberFormat, FieldOperation, FieldPlan, FieldRequest,
    FieldRequestDraft, FieldState, FieldUpdatePolicy, LogicalId, ObjectNumberKind,
};
use hwpx_package::{
    FieldAutoNumberHwpxLimitConfig, FieldAutoNumberHwpxLimits, FieldObjectCaptionHwpxBuilder,
    FieldObjectCaptionHwpxContext, FieldObjectCaptionHwpxError, FieldObjectCaptionHwpxLowerer,
    FieldObjectCaptionHwpxReader, FieldObjectCaptionHwpxTarget,
};

const A: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const B: &str = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
const EMPTY: &str = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";

fn id(value: &str) -> LogicalId {
    LogicalId::parse(value).expect("logical id")
}
fn state_limits() -> FieldEngineLimits {
    FieldEngineLimits::new(FieldEngineLimitConfig::default()).expect("state limits")
}
fn hwpx_limits() -> FieldAutoNumberHwpxLimits {
    FieldAutoNumberHwpxLimits::new(FieldAutoNumberHwpxLimitConfig::default()).expect("hwpx limits")
}

fn target(kind: ObjectNumberKind) -> FieldObjectCaptionHwpxTarget {
    FieldObjectCaptionHwpxTarget {
        logical_object_id: id("object-10"),
        native_object_id: 10,
        object_kind: kind,
    }
}

fn section(name: &str, numbering: &str) -> Vec<u8> {
    format!(concat!(
        "<?xml version=\"1.0\"?><s:sec xmlns:s=\"http://www.hancom.co.kr/hwpml/2011/section\" xmlns:p=\"http://www.hancom.co.kr/hwpml/2011/paragraph\" xmlns:x=\"urn:opaque\">",
        "<p:p id=\"outer\"><p:run><p:t>BEFORE</p:t><p:{name} id=\"10\" numberingType=\"{numbering}\" lock=\"0\" custom=\"opaque\">",
        "<x:payload keep=\"1\">RAW UNTOUCHED</x:payload><p:caption side=\"BOTTOM\" fullSz=\"0\" width=\"7200\" gap=\"360\" lastWidth=\"7200\">",
        "<p:subList><p:p id=\"caption\" paraPrIDRef=\"0\"><p:run charPrIDRef=\"0\"><p:t>LABEL</p:t></p:run></p:p></p:subList></p:caption>",
        "</p:{name}><p:t>AFTER</p:t></p:run></p:p><x:unrelated keep=\"2\"/></s:sec>"
    ), name=name, numbering=numbering).into_bytes()
}

fn state(fields: Vec<FieldState>) -> FieldDocumentState {
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
    .expect("field state")
}

fn insert_plan(
    source: &[u8],
    target: &FieldObjectCaptionHwpxTarget,
    source_state: &FieldDocumentState,
) -> FieldPlan {
    let (paragraph_style_sha256, character_style_sha256) =
        FieldObjectCaptionHwpxReader::style_sha256_at(source, target, 0, 0, hwpx_limits())
            .expect("caption styles");
    let field = FieldState {
        identity: FieldIdentity {
            logical_field_id: id("field-1"),
            native_begin_id: 1,
            native_end_id: 2,
        },
        anchor: FieldAnchor {
            paragraph_id: id("caption-1"),
            run_ordinal: 0,
            inline_ordinal: 1,
        },
        definition: FieldDefinition::ObjectNumber {
            object_kind: target.object_kind,
            format: FieldNumberFormat::Digit,
        },
        cached_result: FieldCachedResult::Number {
            value: 1,
            display: "1".to_owned(),
        },
        update_policy: FieldUpdatePolicy::RecomputeDirect,
        cache_status: FieldCacheStatus::Current,
        locked: false,
        evaluation_context_sha256: None,
        character_style_sha256,
        paragraph_style_sha256,
        field_payload_sha256: EMPTY.to_owned(),
        opaque_properties: Vec::new(),
    };
    operation_plan(
        source_state,
        FieldOperation::Insert {
            insertion_index: 0,
            field,
        },
    )
}

fn operation_plan(source_state: &FieldDocumentState, operation: FieldOperation) -> FieldPlan {
    let request = FieldRequest::from_draft(
        FieldRequestDraft {
            schema_version: FIELD_ENGINE_SCHEMA_VERSION.to_owned(),
            request_id: id("request-1"),
            expected_source_state_sha256: source_state
                .canonical_sha256(state_limits())
                .expect("source digest"),
            expected_document_flow_sha256: A.to_owned(),
            target_document_flow_sha256: B.to_owned(),
            operation,
        },
        source_state,
        A,
        state_limits(),
    )
    .expect("request");
    FieldEngineBuilder::plan(source_state, &request, A, state_limits()).expect("domain plan")
}

fn context<'a>(
    target: &'a FieldObjectCaptionHwpxTarget,
    state: &'a FieldDocumentState,
    paragraphs: &'a [LogicalId],
) -> FieldObjectCaptionHwpxContext<'a> {
    FieldObjectCaptionHwpxContext {
        target,
        state,
        document_flow_sha256: A,
        caption_paragraph_ids: paragraphs,
        state_limits: state_limits(),
        hwpx_limits: hwpx_limits(),
    }
}

#[test]
fn attaches_picture_table_equation_numbers_to_their_real_caption_scope() {
    for (kind, name, numbering) in [
        (ObjectNumberKind::Picture, "pic", "PICTURE"),
        (ObjectNumberKind::Table, "tbl", "TABLE"),
        (ObjectNumberKind::Equation, "equation", "EQUATION"),
    ] {
        let source = section(name, numbering);
        let target = target(kind);
        let source_state = state(Vec::new());
        let domain = insert_plan(&source, &target, &source_state);
        let paragraphs = [id("caption-1")];
        let ctx = context(&target, &source_state, &paragraphs);
        let plan = FieldObjectCaptionHwpxBuilder::plan(&source, &ctx, &domain)
            .expect("caption field plan");
        let (output, receipt) =
            FieldObjectCaptionHwpxLowerer::lower_section_with_receipt(&source, &plan, &ctx)
                .expect("lower");
        let text = String::from_utf8(output.clone()).expect("UTF8");
        assert!(text.contains(&format!("<p:autoNum num=\"1\" numType=\"{numbering}\">")));
        let insertion_start = text.find("<p:ctrl>").expect("insertion");
        let insertion_end = text.find("</p:ctrl>").expect("insertion end") + "</p:ctrl>".len();
        let mut without_insert = output.clone();
        without_insert.drain(insertion_start..insertion_end);
        assert_eq!(without_insert, source);
        assert_eq!(receipt.inner.inserted_auto_numbers, 1);
        let read = FieldObjectCaptionHwpxReader::read_section(
            &output,
            &FieldObjectCaptionHwpxContext {
                state: domain.target_state(),
                document_flow_sha256: B,
                ..ctx
            },
        )
        .expect("readback");
        assert_eq!(read.auto_number_count, 1);
        assert_eq!(read.state, *domain.target_state());
        assert_eq!(read.section_sha256, receipt.output_section_sha256);
        let retry = FieldObjectCaptionHwpxLowerer::lower_section_with_receipt(
            &source,
            &plan,
            &context(&target, &source_state, &paragraphs),
        )
        .expect("retry")
        .0;
        assert_eq!(retry, output);
    }
}

#[test]
fn updates_only_the_selected_caption_number_and_preserves_other_objects() {
    let source = section("tbl", "TABLE");
    let target = target(ObjectNumberKind::Table);
    let empty = state(Vec::new());
    let domain = insert_plan(&source, &target, &empty);
    let paragraphs = [id("caption-1")];
    let ctx = context(&target, &empty, &paragraphs);
    let plan = FieldObjectCaptionHwpxBuilder::plan(&source, &ctx, &domain).expect("plan");
    let inserted = FieldObjectCaptionHwpxLowerer::lower_section_with_receipt(&source, &plan, &ctx)
        .expect("insert")
        .0;
    let update = operation_plan(
        domain.target_state(),
        FieldOperation::UpdateResult {
            target: domain.target_state().fields()[0].identity.clone(),
            cached_result: FieldCachedResult::Number {
                value: 12,
                display: "12".to_owned(),
            },
            evaluation_context_sha256: A.to_owned(),
        },
    );
    let ctx = context(&target, domain.target_state(), &paragraphs);
    let plan = FieldObjectCaptionHwpxBuilder::plan(&inserted, &ctx, &update).expect("update plan");
    let (output, receipt) =
        FieldObjectCaptionHwpxLowerer::lower_section_with_receipt(&inserted, &plan, &ctx)
            .expect("update");
    assert_eq!(
        String::from_utf8(output).expect("UTF8"),
        String::from_utf8(inserted)
            .expect("UTF8")
            .replace("num=\"1\"", "num=\"12\"")
    );
    assert_eq!(receipt.inner.updated_auto_numbers, 1);
}

#[test]
fn wrong_number_kind_and_wrong_object_category_are_rejected_before_output() {
    let source = section("tbl", "TABLE");
    let table = target(ObjectNumberKind::Table);
    let empty = state(Vec::new());
    let domain = insert_plan(&source, &table, &empty);
    let paragraphs = [id("caption-1")];
    let wrong = target(ObjectNumberKind::Picture);
    assert!(matches!(
        FieldObjectCaptionHwpxBuilder::plan(
            &source,
            &context(&wrong, &empty, &paragraphs),
            &domain
        ),
        Err(FieldObjectCaptionHwpxError::KindMismatch)
    ));
    let wrong_native = String::from_utf8(source)
        .expect("UTF8")
        .replace("numberingType=\"TABLE\"", "numberingType=\"PICTURE\"");
    assert!(matches!(
        FieldObjectCaptionHwpxBuilder::plan(
            wrong_native.as_bytes(),
            &context(&table, &empty, &paragraphs),
            &domain
        ),
        Err(FieldObjectCaptionHwpxError::KindMismatch)
    ));
}

#[test]
fn source_selector_flow_and_map_drift_return_no_bytes() {
    let source = section("equation", "EQUATION");
    let target = target(ObjectNumberKind::Equation);
    let empty = state(Vec::new());
    let domain = insert_plan(&source, &target, &empty);
    let paragraphs = [id("caption-1")];
    let ctx = context(&target, &empty, &paragraphs);
    let plan = FieldObjectCaptionHwpxBuilder::plan(&source, &ctx, &domain).expect("plan");
    let drifted = String::from_utf8(source.clone())
        .expect("UTF8")
        .replace("BEFORE", "DRIFT");
    assert!(matches!(
        FieldObjectCaptionHwpxLowerer::lower_section_with_receipt(drifted.as_bytes(), &plan, &ctx),
        Err(FieldObjectCaptionHwpxError::SourceDrift)
    ));
    let changed = FieldObjectCaptionHwpxTarget {
        native_object_id: 11,
        ..target.clone()
    };
    assert!(matches!(
        FieldObjectCaptionHwpxLowerer::lower_section_with_receipt(
            &source,
            &plan,
            &FieldObjectCaptionHwpxContext {
                target: &changed,
                ..ctx
            }
        ),
        Err(FieldObjectCaptionHwpxError::SourceDrift)
    ));
    assert!(
        FieldObjectCaptionHwpxLowerer::lower_section_with_receipt(
            &source,
            &plan,
            &FieldObjectCaptionHwpxContext {
                document_flow_sha256: B,
                ..ctx
            }
        )
        .is_err()
    );
    let incorrect_map = [id("wrong")];
    assert!(
        FieldObjectCaptionHwpxLowerer::lower_section_with_receipt(
            &source,
            &plan,
            &FieldObjectCaptionHwpxContext {
                caption_paragraph_ids: &incorrect_map,
                ..ctx
            }
        )
        .is_err()
    );
}

#[test]
fn missing_duplicate_locked_or_shadowed_caption_identity_fails_closed() {
    let source = String::from_utf8(section("pic", "PICTURE")).expect("UTF8");
    let target = target(ObjectNumberKind::Picture);
    let variants = [
        source.replace("id=\"10\"", "id=\"11\""),
        source.replace("lock=\"0\"", "lock=\"1\""),
        source.replace(
            "<p:subList>",
            "<p:subList xmlns:p=\"urn:unqualified-caption-prefix\">",
        ),
        source.replace(
            "</p:pic>",
            "</p:pic><p:pic id=\"10\" numberingType=\"PICTURE\" lock=\"0\"/>",
        ),
        source
            .replace("<p:caption ", "<p:wrong ")
            .replace("</p:caption>", "</p:wrong>"),
        source.replace("</p:pic>", "<p:caption><p:subList/></p:caption></p:pic>"),
    ];
    for value in variants {
        assert!(
            FieldObjectCaptionHwpxReader::style_sha256_at(
                value.as_bytes(),
                &target,
                0,
                0,
                hwpx_limits()
            )
            .is_err()
        );
    }
}

#[test]
fn complete_multi_paragraph_caption_map_and_opaque_content_are_preserved() {
    let source = String::from_utf8(section("pic", "PICTURE"))
        .expect("UTF8")
        .replace(
            "</p:subList>",
            "<p:p id=\"second\"><p:run><p:t>KEEP SECOND</p:t></p:run></p:p></p:subList>",
        )
        .into_bytes();
    let target = target(ObjectNumberKind::Picture);
    let empty = state(Vec::new());
    let domain = insert_plan(&source, &target, &empty);
    let map = [id("caption-1"), id("caption-2")];
    let ctx = context(&target, &empty, &map);
    let plan = FieldObjectCaptionHwpxBuilder::plan(&source, &ctx, &domain).expect("complete map");
    let output = FieldObjectCaptionHwpxLowerer::lower_section_with_receipt(&source, &plan, &ctx)
        .expect("lower")
        .0;
    let text = String::from_utf8(output).expect("UTF8");
    assert!(text.contains("KEEP SECOND"));
    assert!(text.contains("RAW UNTOUCHED"));
    assert!(
        FieldObjectCaptionHwpxBuilder::plan(&source, &context(&target, &empty, &map[..1]), &domain)
            .is_err()
    );
}

#[test]
fn exact_redundant_root_namespace_declarations_are_preserved() {
    let source = String::from_utf8(section("pic", "PICTURE"))
        .expect("UTF8")
        .replace(
            "<p:pic ",
            "<p:pic xmlns:p=\"http://www.hancom.co.kr/hwpml/2011/paragraph\" ",
        )
        .replace(
            "<p:subList>",
            "<p:subList xmlns:p=\"http://www.hancom.co.kr/hwpml/2011/paragraph\">",
        )
        .into_bytes();
    let target = target(ObjectNumberKind::Picture);
    let empty = state(Vec::new());
    let domain = insert_plan(&source, &target, &empty);
    let paragraphs = [id("caption-1")];
    let ctx = context(&target, &empty, &paragraphs);
    let plan = FieldObjectCaptionHwpxBuilder::plan(&source, &ctx, &domain)
        .expect("redundant declarations");
    let output = FieldObjectCaptionHwpxLowerer::lower_section_with_receipt(&source, &plan, &ctx)
        .expect("lower")
        .0;
    let text = String::from_utf8(output.clone()).expect("UTF8");
    let start = text.find("<p:ctrl>").expect("control");
    let end = text.find("</p:ctrl>").expect("control end") + "</p:ctrl>".len();
    let mut restored = output;
    restored.drain(start..end);
    assert_eq!(restored, source);
}

#[test]
fn tables_do_not_require_an_invented_instance_id_and_picture_shapes_are_admitted() {
    for name in [
        "rect",
        "ellipse",
        "line",
        "arc",
        "polygon",
        "curve",
        "connectLine",
    ] {
        let source = section(name, "PICTURE");
        let target = target(ObjectNumberKind::Picture);
        let empty = state(Vec::new());
        let domain = insert_plan(&source, &target, &empty);
        let paragraphs = [id("caption-1")];
        let ctx = context(&target, &empty, &paragraphs);
        assert!(FieldObjectCaptionHwpxBuilder::plan(&source, &ctx, &domain).is_ok());
    }
    assert!(
        !String::from_utf8(section("tbl", "TABLE"))
            .expect("UTF8")
            .contains("instid")
    );
}

#[test]
fn debug_is_redacted_and_finite_limits_fail_before_output() {
    let source = section("pic", "PICTURE");
    let target = target(ObjectNumberKind::Picture);
    let empty = state(Vec::new());
    let domain = insert_plan(&source, &target, &empty);
    let paragraphs = [id("caption-1")];
    let ctx = context(&target, &empty, &paragraphs);
    let plan = FieldObjectCaptionHwpxBuilder::plan(&source, &ctx, &domain).expect("plan");
    let (_, receipt) =
        FieldObjectCaptionHwpxLowerer::lower_section_with_receipt(&source, &plan, &ctx)
            .expect("lower");
    let debug = format!("{target:?} {ctx:?} {plan:?} {receipt:?}");
    assert!(!debug.contains("object-10"));
    assert!(!debug.contains("LABEL"));
    assert!(!debug.contains(A));
    let small = FieldAutoNumberHwpxLimits::new(FieldAutoNumberHwpxLimitConfig {
        section_bytes: 16,
        output_bytes: 16,
        ..FieldAutoNumberHwpxLimitConfig::default()
    })
    .expect("limits");
    assert!(matches!(
        FieldObjectCaptionHwpxBuilder::plan(
            &source,
            &FieldObjectCaptionHwpxContext {
                hwpx_limits: small,
                ..ctx
            },
            &domain
        ),
        Err(FieldObjectCaptionHwpxError::InputLimit)
    ));
}
