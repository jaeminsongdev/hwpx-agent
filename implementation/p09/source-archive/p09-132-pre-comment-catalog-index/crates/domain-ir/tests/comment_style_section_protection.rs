//! Synthetic typed model protection cases; NOT native comment import or HWPX acceptance.
use domain_ir::{
    COMMENT_MODEL_SCHEMA_VERSION, CommentBuilder, CommentDocumentState, CommentDocumentStateDraft,
    CommentError, CommentLimitConfig, CommentLimits, CommentOperation, CommentRequest,
    CommentRequestDraft, LogicalId,
};
use serde_json::json;

type TestResult = Result<(), Box<dyn std::error::Error>>;
fn limits() -> Result<CommentLimits, CommentError> {
    CommentLimits::new(CommentLimitConfig::default())
}
fn state(
    locked: bool,
    anchored_section: &str,
) -> Result<CommentDocumentState, Box<dyn std::error::Error>> {
    let digest = "a".repeat(64);
    let style = |id| {
        json!({"style_id":id,"width_native_units":2835,"line_width":"mm0_12",
        "line_type":"solid","line_color_rgb":0,"fill_color_rgb":0,"active_color_rgb":0,
        "memo_type":"normal","opaque_style_sha256":digest,"locked":false})
    };
    let point = |inline| json!({"paragraph_ordinal":0,"run_ordinal":0,"inline_ordinal":inline});
    let draft: CommentDocumentStateDraft = serde_json::from_value(json!({
        "schema_version":COMMENT_MODEL_SCHEMA_VERSION,
        "sections":[{"section_id":"section-1","memo_shape_id_ref":1,"opaque_section_state_sha256":digest,"locked":locked},
                    {"section_id":"section-2","memo_shape_id_ref":1,"opaque_section_state_sha256":digest,"locked":false}],
        "authors":[{"author_id":1,"name_sha256":digest,"email_sha256":null,"opaque_author_state_sha256":digest,"locked":false}],
        "styles":[style(1),style(2)],"hidden_explanations":[],
        "comments":[{"identity":{"logical_comment_id":"comment-1","begin_control_id":1,"field_id":2},
            "anchor":{"section_id":anchored_section,"start":point(0),"end":point(1)},
            "native_begin_tag":"field_begin","native_end_tag":"field_end","native_field_type":"memo",
            "semantic_binding":"unverified_memo_parameters","name_sha256":null,"editable":true,"dirty":false,"z_order":0,
            "author_id":1,"created_at":{"epoch_millis":1_700_000_000_000_u64,"original_utc_offset_minutes":540},
            "modified_at":null,"body_graph_sha256":digest,"plain_text_sha256":null,"parameters_sha256":digest,
            "sub_list_sha256":digest,"style_id":2,"visibility":"shown",
            "resolution":{"resolved":false,"resolver_author_id":null,"resolved_at":null},
            "opaque_native_payload_sha256":digest,"opaque_properties":[],"locked":false}],
        "non_comment_content_sha256":digest,"field_inventory_sha256":digest,"style_catalog_sha256":digest,
        "reference_inventory_sha256":digest,"resource_inventory_sha256":digest,"document_protection_sha256":digest,
        "opaque_document_state_sha256":digest,"document_locked":false
    }))?;
    Ok(CommentDocumentState::from_draft(draft, limits()?)?)
}
fn request(current: &CommentDocumentState, style_id: u32) -> Result<CommentRequest, CommentError> {
    let mut replacement = current
        .styles()
        .iter()
        .find(|s| s.style_id == style_id)
        .ok_or(CommentError::InvalidStyle)?
        .clone();
    replacement.width_native_units += 1;
    CommentRequest::from_draft(
        CommentRequestDraft {
            schema_version: COMMENT_MODEL_SCHEMA_VERSION.into(),
            request_id: LogicalId::parse("section-style-request")
                .map_err(|_| CommentError::InvalidIdentity)?,
            expected_source_state_sha256: current.canonical_sha256(limits()?)?,
            expected_document_flow_sha256: "b".repeat(64),
            target_document_flow_sha256: "b".repeat(64),
            operation: CommentOperation::ReplaceStyle {
                style_id,
                style: replacement,
            },
        },
        current,
        &"b".repeat(64),
        limits()?,
    )
}

#[test]
fn locked_anchor_section_rejects_comment_style_even_when_its_default_style_differs() -> TestResult {
    let current = state(true, "section-1")?;
    assert!(
        matches!(request(&current, 2), Err(CommentError::Protected)),
        "locked_anchor_style_not_rejected"
    );
    Ok(())
}
#[test]
fn unlocked_anchor_with_different_default_style_still_builds() -> TestResult {
    let current = state(false, "section-1")?;
    let request = request(&current, 2)?;
    let plan = CommentBuilder::plan(&current, &request, &"b".repeat(64), limits()?)?;
    let result = CommentBuilder::build(&plan, &current, &"b".repeat(64), limits()?)?;
    assert_ne!(result.state, current);
    Ok(())
}
#[test]
fn unrelated_locked_section_does_not_block_unlocked_comment_style() -> TestResult {
    let current = state(true, "section-2")?;
    assert!(request(&current, 2).is_ok());
    Ok(())
}
#[test]
fn locked_default_style_reference_remains_rejected() -> TestResult {
    let current = state(true, "section-2")?;
    assert!(matches!(request(&current, 1), Err(CommentError::Protected)));
    Ok(())
}
