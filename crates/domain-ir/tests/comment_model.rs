#![allow(clippy::expect_used)] // Fixtures keep failures local and readable.

use std::collections::BTreeSet;

use domain_ir::{
    COMMENT_MODEL_SCHEMA_VERSION, CommentAnchor, CommentAuthor, CommentBuilder,
    CommentDocumentState, CommentDocumentStateDraft, CommentEntry, CommentError, CommentFieldType,
    CommentIdentity, CommentLimitConfig, CommentLimits, CommentLineType, CommentLineWidth,
    CommentMemoType, CommentNativeBeginTag, CommentNativeEndTag, CommentOperation, CommentPoint,
    CommentRequest, CommentRequestDraft, CommentResolution, CommentSectionState,
    CommentSemanticBinding, CommentStyle, CommentTimestamp, CommentVisibility,
    HiddenExplanationEntry, HiddenExplanationIdentity, HiddenExplanationNativeTag, LogicalId,
    OpaqueCommentProperty,
};

const DIGEST_A: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const DIGEST_B: &str = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
const DIGEST_C: &str = "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc";
const FLOW_A: &str = "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd";
const FLOW_B: &str = "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee";

fn limits() -> CommentLimits {
    CommentLimits::new(CommentLimitConfig::default()).expect("valid limits")
}

fn id(value: &str) -> LogicalId {
    LogicalId::parse(value).expect("valid logical id")
}

fn point(paragraph: u32, inline: u32) -> CommentPoint {
    CommentPoint {
        paragraph_ordinal: paragraph,
        run_ordinal: 0,
        inline_ordinal: inline,
    }
}

fn anchor(section: u32, paragraph: u32, start: u32, end: u32) -> CommentAnchor {
    CommentAnchor {
        section_id: id(&format!("section-{section}")),
        start: point(paragraph, start),
        end: point(paragraph, end),
    }
}

fn timestamp(epoch_millis: u64) -> CommentTimestamp {
    CommentTimestamp {
        epoch_millis,
        original_utc_offset_minutes: 540,
    }
}

fn author(author_id: u32) -> CommentAuthor {
    CommentAuthor {
        author_id,
        name_sha256: DIGEST_A.to_owned(),
        email_sha256: Some(DIGEST_B.to_owned()),
        opaque_author_state_sha256: DIGEST_C.to_owned(),
        locked: false,
    }
}

fn style(style_id: u32) -> CommentStyle {
    CommentStyle {
        style_id,
        width_native_units: 2835,
        line_width: CommentLineWidth::Mm0_12,
        line_type: CommentLineType::Solid,
        line_color_rgb: 0x0011_2233,
        fill_color_rgb: 0x00cc_ff99,
        active_color_rgb: 0x00ff_ff99,
        memo_type: CommentMemoType::Normal,
        opaque_style_sha256: DIGEST_A.to_owned(),
        locked: false,
    }
}

fn section(section_id: u32, style_id: u32) -> CommentSectionState {
    CommentSectionState {
        section_id: id(&format!("section-{section_id}")),
        memo_shape_id_ref: style_id,
        opaque_section_state_sha256: DIGEST_B.to_owned(),
        locked: false,
    }
}

fn explanation(index: u32, section_id: u32) -> HiddenExplanationEntry {
    HiddenExplanationEntry {
        identity: HiddenExplanationIdentity {
            logical_explanation_id: id(&format!("explanation-{index}")),
        },
        anchor: anchor(section_id, index, 0, 1),
        native_tag: HiddenExplanationNativeTag::HiddenComment,
        enabled: true,
        body_graph_sha256: DIGEST_A.to_owned(),
        plain_text_sha256: Some(DIGEST_B.to_owned()),
        sub_list_sha256: DIGEST_C.to_owned(),
        opaque_native_payload_sha256: DIGEST_A.to_owned(),
        opaque_properties: vec![OpaqueCommentProperty {
            namespace: "private.hidden".to_owned(),
            name: format!("property-{index}"),
            value_sha256: DIGEST_B.to_owned(),
        }],
        locked: false,
    }
}

fn identity(index: u32) -> CommentIdentity {
    CommentIdentity {
        logical_comment_id: id(&format!("comment-{index}")),
        begin_control_id: 100 + index,
        field_id: 200 + index,
    }
}

fn comment(index: u32, section_id: u32, style_id: u32, author_id: u32) -> CommentEntry {
    CommentEntry {
        identity: identity(index),
        anchor: anchor(section_id, 10 + index, 0, 2),
        native_begin_tag: CommentNativeBeginTag::FieldBegin,
        native_end_tag: CommentNativeEndTag::FieldEnd,
        native_field_type: CommentFieldType::Memo,
        semantic_binding: CommentSemanticBinding::UnverifiedMemoParameters,
        name_sha256: Some(DIGEST_C.to_owned()),
        editable: true,
        dirty: false,
        z_order: i32::try_from(index).expect("small fixture"),
        author_id,
        created_at: timestamp(1_700_000_000_000 + u64::from(index)),
        modified_at: Some(timestamp(1_700_000_010_000 + u64::from(index))),
        body_graph_sha256: DIGEST_A.to_owned(),
        plain_text_sha256: Some(DIGEST_B.to_owned()),
        parameters_sha256: DIGEST_C.to_owned(),
        sub_list_sha256: DIGEST_A.to_owned(),
        style_id,
        visibility: CommentVisibility::Shown,
        resolution: CommentResolution {
            resolved: false,
            resolver_author_id: None,
            resolved_at: None,
        },
        opaque_native_payload_sha256: DIGEST_B.to_owned(),
        opaque_properties: vec![OpaqueCommentProperty {
            namespace: "private.memo".to_owned(),
            name: format!("property-{index}"),
            value_sha256: DIGEST_C.to_owned(),
        }],
        locked: false,
    }
}

fn state_with(
    sections: Vec<CommentSectionState>,
    authors: Vec<CommentAuthor>,
    styles: Vec<CommentStyle>,
    hidden_explanations: Vec<HiddenExplanationEntry>,
    comments: Vec<CommentEntry>,
    document_locked: bool,
) -> Result<CommentDocumentState, CommentError> {
    CommentDocumentState::from_draft(
        CommentDocumentStateDraft {
            schema_version: COMMENT_MODEL_SCHEMA_VERSION.to_owned(),
            sections,
            authors,
            styles,
            hidden_explanations,
            comments,
            non_comment_content_sha256: DIGEST_A.to_owned(),
            field_inventory_sha256: DIGEST_B.to_owned(),
            style_catalog_sha256: DIGEST_C.to_owned(),
            reference_inventory_sha256: DIGEST_A.to_owned(),
            resource_inventory_sha256: DIGEST_B.to_owned(),
            document_protection_sha256: DIGEST_C.to_owned(),
            opaque_document_state_sha256: DIGEST_A.to_owned(),
            document_locked,
        },
        limits(),
    )
}

fn state() -> CommentDocumentState {
    state_with(
        vec![section(1, 1), section(2, 2)],
        vec![author(1), author(2)],
        vec![style(1), style(2)],
        vec![explanation(1, 1), explanation(2, 2)],
        vec![comment(1, 1, 1, 1), comment(2, 2, 2, 2)],
        false,
    )
    .expect("valid state")
}

fn request(
    source: &CommentDocumentState,
    operation: CommentOperation,
) -> Result<CommentRequest, CommentError> {
    CommentRequest::from_draft(
        CommentRequestDraft {
            schema_version: COMMENT_MODEL_SCHEMA_VERSION.to_owned(),
            request_id: id("request-1"),
            expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
            expected_document_flow_sha256: FLOW_A.to_owned(),
            target_document_flow_sha256: FLOW_B.to_owned(),
            operation,
        },
        source,
        FLOW_A,
        limits(),
    )
}

fn build(source: &CommentDocumentState, operation: CommentOperation) -> domain_ir::CommentResult {
    let request = request(source, operation).expect("valid request");
    let plan = CommentBuilder::plan(source, &request, FLOW_A, limits()).expect("valid plan");
    CommentBuilder::build(&plan, source, FLOW_A, limits()).expect("valid result")
}

fn value(state: &CommentDocumentState) -> serde_json::Value {
    serde_json::from_slice(&state.canonical_json(limits()).expect("json")).expect("value")
}

#[test]
fn hidden_explanation_changes_only_enabled_and_binds_exact_capability() {
    let source = state();
    let before = value(&source);
    let operation = CommentOperation::SetHiddenExplanation {
        target: HiddenExplanationIdentity {
            logical_explanation_id: id("explanation-1"),
        },
        enabled: false,
    };
    assert_eq!(operation.capability_id(), "ref.hidden_explanation");
    let after = value(&build(&source, operation).state);
    assert_eq!(after["hidden_explanations"][0]["enabled"], false);
    for field in [
        "identity",
        "anchor",
        "native_tag",
        "body_graph_sha256",
        "plain_text_sha256",
        "sub_list_sha256",
        "opaque_native_payload_sha256",
        "opaque_properties",
        "locked",
    ] {
        assert_eq!(
            before["hidden_explanations"][0][field],
            after["hidden_explanations"][0][field]
        );
    }
    assert_eq!(
        before["hidden_explanations"][1],
        after["hidden_explanations"][1]
    );
    assert_eq!(before["comments"], after["comments"]);
}

#[test]
fn insert_comment_binds_exact_identity_anchor_author_time_style_and_native_shape() {
    let source = state();
    let before = value(&source);
    let inserted = comment(3, 1, 2, 2);
    let operation = CommentOperation::InsertComment {
        insertion_index: 1,
        comment: Box::new(inserted.clone()),
    };
    assert_eq!(operation.capability_id(), "ref.comment_insert");
    let result = build(&source, operation);
    let after = value(&result.state);
    assert_eq!(result.state.comments().len(), 3);
    assert_eq!(result.state.comments()[1], inserted);
    assert_eq!(after["comments"][1]["native_begin_tag"], "field_begin");
    assert_eq!(after["comments"][1]["native_end_tag"], "field_end");
    assert_eq!(after["comments"][1]["native_field_type"], "memo");
    assert_eq!(
        after["comments"][1]["semantic_binding"],
        "unverified_memo_parameters"
    );
    for field in [
        "sections",
        "authors",
        "styles",
        "hidden_explanations",
        "non_comment_content_sha256",
        "field_inventory_sha256",
        "style_catalog_sha256",
        "reference_inventory_sha256",
        "resource_inventory_sha256",
        "document_protection_sha256",
        "opaque_document_state_sha256",
        "document_locked",
    ] {
        assert_eq!(before[field], after[field]);
    }
    assert_eq!(before["comments"][0], after["comments"][0]);
    assert_eq!(before["comments"][1], after["comments"][2]);
}

#[test]
fn replace_style_changes_only_the_exact_style_and_preserves_references() {
    let source = state();
    let before = value(&source);
    let mut replacement = style(2);
    replacement.width_native_units = 5670;
    replacement.line_width = CommentLineWidth::Mm5_0;
    replacement.line_type = CommentLineType::DoubleWave;
    replacement.line_color_rgb = 0x00ab_cdef;
    replacement.memo_type = CommentMemoType::UserUpdate;
    replacement.opaque_style_sha256 = DIGEST_C.to_owned();
    let operation = CommentOperation::ReplaceStyle {
        style_id: 2,
        style: replacement.clone(),
    };
    assert_eq!(operation.capability_id(), "ref.comment_style");
    let result = build(&source, operation);
    let after = value(&result.state);
    assert_eq!(result.state.styles()[1], replacement);
    assert_eq!(before["styles"][0], after["styles"][0]);
    assert_eq!(before["sections"], after["sections"]);
    assert_eq!(before["comments"], after["comments"]);
    assert_eq!(before["authors"], after["authors"]);
    assert_eq!(before["hidden_explanations"], after["hidden_explanations"]);
}

#[test]
fn visibility_changes_only_the_selected_comment() {
    let source = state();
    let before = value(&source);
    let operation = CommentOperation::SetVisibility {
        target: identity(2),
        visibility: CommentVisibility::Hidden,
    };
    assert_eq!(operation.capability_id(), "ref.comment_show_hide");
    let after = value(&build(&source, operation).state);
    assert_eq!(after["comments"][1]["visibility"], "hidden");
    for field in [
        "identity",
        "anchor",
        "native_begin_tag",
        "native_end_tag",
        "native_field_type",
        "semantic_binding",
        "author_id",
        "created_at",
        "modified_at",
        "body_graph_sha256",
        "parameters_sha256",
        "sub_list_sha256",
        "style_id",
        "resolution",
        "opaque_native_payload_sha256",
        "opaque_properties",
        "locked",
    ] {
        assert_eq!(before["comments"][1][field], after["comments"][1][field]);
    }
    assert_eq!(before["comments"][0], after["comments"][0]);
}

#[test]
fn resolution_changes_only_the_selected_comment_with_exact_author_and_time() {
    let source = state();
    let before = value(&source);
    let resolution = CommentResolution {
        resolved: true,
        resolver_author_id: Some(2),
        resolved_at: Some(timestamp(1_800_000_000_000)),
    };
    let operation = CommentOperation::SetResolution {
        target: identity(1),
        resolution,
    };
    assert_eq!(operation.capability_id(), "ref.comment_resolve");
    let result = build(&source, operation);
    assert_eq!(result.state.comments()[0].resolution, resolution);
    let after = value(&result.state);
    assert_eq!(before["comments"][1], after["comments"][1]);
    assert_eq!(before["authors"], after["authors"]);
    assert_eq!(before["styles"], after["styles"]);

    let unresolved = build(
        &result.state,
        CommentOperation::SetResolution {
            target: identity(1),
            resolution: CommentResolution {
                resolved: false,
                resolver_author_id: None,
                resolved_at: None,
            },
        },
    );
    assert!(!unresolved.state.comments()[0].resolution.resolved);
}

#[test]
fn official_line_width_line_type_and_memo_type_catalogs_are_complete_and_distinct() {
    let line_types = [
        CommentLineType::None,
        CommentLineType::Solid,
        CommentLineType::Dot,
        CommentLineType::Dash,
        CommentLineType::DashDot,
        CommentLineType::DashDotDot,
        CommentLineType::LongDash,
        CommentLineType::Circle,
        CommentLineType::DoubleSlim,
        CommentLineType::SlimThick,
        CommentLineType::ThickSlim,
        CommentLineType::SlimThickSlim,
        CommentLineType::Wave,
        CommentLineType::DoubleWave,
        CommentLineType::Thick3d,
        CommentLineType::ThickReverse3d,
        CommentLineType::ThreeDimensional,
        CommentLineType::Reverse3d,
    ];
    let line_widths = [
        CommentLineWidth::Mm0_1,
        CommentLineWidth::Mm0_12,
        CommentLineWidth::Mm0_15,
        CommentLineWidth::Mm0_2,
        CommentLineWidth::Mm0_25,
        CommentLineWidth::Mm0_3,
        CommentLineWidth::Mm0_4,
        CommentLineWidth::Mm0_5,
        CommentLineWidth::Mm0_6,
        CommentLineWidth::Mm0_7,
        CommentLineWidth::Mm1_0,
        CommentLineWidth::Mm1_5,
        CommentLineWidth::Mm2_0,
        CommentLineWidth::Mm3_0,
        CommentLineWidth::Mm4_0,
        CommentLineWidth::Mm5_0,
    ];
    let memo_types = [
        CommentMemoType::Normal,
        CommentMemoType::UserInsert,
        CommentMemoType::UserDelete,
        CommentMemoType::UserUpdate,
    ];
    assert_eq!(line_types.len(), 18);
    assert_eq!(line_widths.len(), 16);
    assert_eq!(memo_types.len(), 4);
    for values in [
        line_types
            .iter()
            .map(|value| serde_json::to_string(value).expect("json"))
            .collect::<BTreeSet<_>>(),
        line_widths
            .iter()
            .map(|value| serde_json::to_string(value).expect("json"))
            .collect::<BTreeSet<_>>(),
        memo_types
            .iter()
            .map(|value| serde_json::to_string(value).expect("json"))
            .collect::<BTreeSet<_>>(),
    ] {
        assert!(!values.is_empty());
    }
    assert_eq!(
        line_types
            .iter()
            .map(|value| serde_json::to_string(value).expect("json"))
            .collect::<BTreeSet<_>>()
            .len(),
        line_types.len()
    );
    assert_eq!(
        line_widths
            .iter()
            .map(|value| serde_json::to_string(value).expect("json"))
            .collect::<BTreeSet<_>>()
            .len(),
        line_widths.len()
    );
    assert_eq!(
        memo_types
            .iter()
            .map(|value| serde_json::to_string(value).expect("json"))
            .collect::<BTreeSet<_>>()
            .len(),
        memo_types.len()
    );
}

#[test]
fn invalid_identity_anchor_style_author_time_and_duplicates_fail_closed() {
    let mut bad_anchor = comment(1, 1, 1, 1);
    bad_anchor.anchor.start = point(99, 0);
    assert_eq!(
        state_with(
            vec![section(1, 1)],
            vec![author(1)],
            vec![style(1)],
            Vec::new(),
            vec![bad_anchor],
            false,
        ),
        Err(CommentError::InvalidAnchor)
    );

    let mut bad_identity = comment(1, 1, 1, 1);
    bad_identity.identity.field_id = 0;
    assert_eq!(
        state_with(
            vec![section(1, 1)],
            vec![author(1)],
            vec![style(1)],
            Vec::new(),
            vec![bad_identity],
            false,
        ),
        Err(CommentError::InvalidIdentity)
    );

    let mut bad_style = style(1);
    bad_style.fill_color_rgb = 0x0100_0000;
    assert_eq!(
        state_with(
            vec![section(1, 1)],
            vec![author(1)],
            vec![bad_style],
            Vec::new(),
            Vec::new(),
            false,
        ),
        Err(CommentError::InvalidStyle)
    );

    let mut bad_time = comment(1, 1, 1, 1);
    bad_time.modified_at = Some(timestamp(1));
    assert_eq!(
        state_with(
            vec![section(1, 1)],
            vec![author(1)],
            vec![style(1)],
            Vec::new(),
            vec![bad_time],
            false,
        ),
        Err(CommentError::InvalidAuthorTime)
    );

    let mut missing_author = comment(1, 1, 1, 9);
    missing_author.resolution = CommentResolution {
        resolved: true,
        resolver_author_id: Some(9),
        resolved_at: Some(timestamp(1_800_000_000_000)),
    };
    assert_eq!(
        state_with(
            vec![section(1, 1)],
            vec![author(1)],
            vec![style(1)],
            Vec::new(),
            vec![missing_author],
            false,
        ),
        Err(CommentError::InvalidIdentity)
    );

    let source = state();
    assert_eq!(
        request(
            &source,
            CommentOperation::InsertComment {
                insertion_index: 3,
                comment: Box::new(comment(3, 1, 1, 1)),
            },
        ),
        Err(CommentError::InvalidInsertionIndex)
    );
    let mut duplicate = comment(3, 1, 1, 1);
    duplicate.identity.field_id = source.comments()[0].identity.field_id;
    assert_eq!(
        request(
            &source,
            CommentOperation::InsertComment {
                insertion_index: 2,
                comment: Box::new(duplicate),
            },
        ),
        Err(CommentError::InvalidIdentity)
    );
}

#[test]
fn protection_and_noop_rules_fail_without_partial_state() {
    let locked_document = state_with(
        vec![section(1, 1)],
        vec![author(1)],
        vec![style(1)],
        vec![explanation(1, 1)],
        Vec::new(),
        true,
    )
    .expect("locked state");
    assert_eq!(
        request(
            &locked_document,
            CommentOperation::SetHiddenExplanation {
                target: HiddenExplanationIdentity {
                    logical_explanation_id: id("explanation-1"),
                },
                enabled: false,
            },
        ),
        Err(CommentError::Protected)
    );

    let mut locked_comment = comment(1, 1, 1, 1);
    locked_comment.locked = true;
    let locked_comment_state = state_with(
        vec![section(1, 1)],
        vec![author(1)],
        vec![style(1)],
        Vec::new(),
        vec![locked_comment],
        false,
    )
    .expect("locked comment state");
    assert_eq!(
        request(
            &locked_comment_state,
            CommentOperation::SetVisibility {
                target: identity(1),
                visibility: CommentVisibility::Hidden,
            },
        ),
        Err(CommentError::Protected)
    );

    let mut locked_style = style(1);
    locked_style.locked = true;
    let locked_style_state = state_with(
        vec![section(1, 1)],
        vec![author(1)],
        vec![locked_style],
        Vec::new(),
        Vec::new(),
        false,
    )
    .expect("locked style state");
    let mut replacement = style(1);
    replacement.width_native_units = 1;
    assert_eq!(
        request(
            &locked_style_state,
            CommentOperation::ReplaceStyle {
                style_id: 1,
                style: replacement,
            },
        ),
        Err(CommentError::Protected)
    );

    let source = state();
    assert_eq!(
        request(
            &source,
            CommentOperation::SetVisibility {
                target: identity(1),
                visibility: CommentVisibility::Shown,
            },
        ),
        Err(CommentError::Noop)
    );
    assert_eq!(
        request(
            &source,
            CommentOperation::SetResolution {
                target: identity(1),
                resolution: CommentResolution {
                    resolved: false,
                    resolver_author_id: Some(1),
                    resolved_at: None,
                },
            },
        ),
        Err(CommentError::InvalidAuthorTime)
    );
}

#[test]
fn request_plan_and_build_recheck_exact_state_and_document_flow() {
    let source = state();
    let operation = CommentOperation::SetVisibility {
        target: identity(1),
        visibility: CommentVisibility::Hidden,
    };
    let mut draft = CommentRequestDraft {
        schema_version: COMMENT_MODEL_SCHEMA_VERSION.to_owned(),
        request_id: id("request-drift"),
        expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
        expected_document_flow_sha256: FLOW_A.to_owned(),
        target_document_flow_sha256: FLOW_B.to_owned(),
        operation: operation.clone(),
    };
    draft.expected_source_state_sha256 = FLOW_B.to_owned();
    assert_eq!(
        CommentRequest::from_draft(draft, &source, FLOW_A, limits()),
        Err(CommentError::SourceStateDrift)
    );

    let request = request(&source, operation).expect("request");
    assert_eq!(
        CommentBuilder::plan(&source, &request, FLOW_B, limits()),
        Err(CommentError::DocumentFlowDrift)
    );
    let plan = CommentBuilder::plan(&source, &request, FLOW_A, limits()).expect("plan");
    assert_eq!(
        CommentBuilder::build(&plan, &source, FLOW_B, limits()),
        Err(CommentError::DocumentFlowDrift)
    );

    let changed = state_with(
        vec![section(1, 1), section(2, 2)],
        vec![author(1), author(2)],
        vec![style(1), style(2)],
        vec![explanation(1, 1), explanation(2, 2)],
        vec![comment(1, 1, 1, 1)],
        false,
    )
    .expect("changed state");
    assert_eq!(
        CommentBuilder::build(&plan, &changed, FLOW_A, limits()),
        Err(CommentError::SourceStateDrift)
    );
}

#[test]
fn strict_json_limits_error_codes_and_debug_output_are_bounded_and_redacted() {
    let source = state();
    let draft = CommentRequestDraft {
        schema_version: COMMENT_MODEL_SCHEMA_VERSION.to_owned(),
        request_id: id("request-private"),
        expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
        expected_document_flow_sha256: FLOW_A.to_owned(),
        target_document_flow_sha256: FLOW_B.to_owned(),
        operation: CommentOperation::SetVisibility {
            target: identity(1),
            visibility: CommentVisibility::Hidden,
        },
    };
    let bytes = serde_json::to_vec(&draft).expect("json");
    assert!(CommentRequest::from_json(&bytes, &source, FLOW_A, limits()).is_ok());

    let duplicate = String::from_utf8(bytes.clone()).expect("utf8").replacen(
        "\"schema_version\":",
        "\"schema_version\":\"hwpx-agent.comment-model/v1\",\"schema_version\":",
        1,
    );
    assert_eq!(
        CommentRequest::from_json(duplicate.as_bytes(), &source, FLOW_A, limits()),
        Err(CommentError::InvalidJson)
    );
    let unknown = String::from_utf8(bytes)
        .expect("utf8")
        .replacen('{', "{\"unknown\":true,", 1);
    assert_eq!(
        CommentRequest::from_json(unknown.as_bytes(), &source, FLOW_A, limits()),
        Err(CommentError::InvalidJson)
    );

    let tiny = CommentLimits::new(CommentLimitConfig {
        input_bytes: 8,
        output_bytes: 8,
        ..CommentLimitConfig::default()
    })
    .expect("tiny limits");
    assert_eq!(
        CommentRequest::from_json(b"123456789", &source, FLOW_A, tiny),
        Err(CommentError::InputLimit)
    );
    assert_eq!(CommentError::Protected.code(), "comment_protected");
    assert_eq!(CommentError::PlanTampered.code(), "comment_plan_tampered");
    let debug = format!("{draft:?} {source:?}");
    assert!(!debug.contains("request-private"));
    assert!(!debug.contains("comment-1"));
    assert!(!debug.contains(DIGEST_A));
    let point_debug = format!("{:?}", point(1_234_567, 7_654_321));
    let timestamp_debug = format!("{:?}", timestamp(1_800_123_456_789));
    assert!(!point_debug.contains("1234567"));
    assert!(!point_debug.contains("7654321"));
    assert!(!timestamp_debug.contains("1800123456789"));
}
