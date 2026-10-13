//! Synthetic caller complete-comment fixtures derived from P09-93 helpers; never native capture.
use domain_ir::*;
use hwpx_agent_cli::comment_operation::*;
use serde_json::{Value, json};
pub(super) fn id(value: &str) -> LogicalId {
    LogicalId::parse(value).expect("fixture logical ID")
}
pub(super) fn limits() -> CommentLimits {
    CommentLimits::new(CommentLimitConfig::default()).expect("fixture limits")
}
fn digest() -> String {
    "a".repeat(64)
}
fn anchor(section: &str, paragraph: u32) -> Value {
    json!({"section_id":section,"start":{"paragraph_ordinal":paragraph,"run_ordinal":0,"inline_ordinal":0},
        "end":{"paragraph_ordinal":paragraph,"run_ordinal":0,"inline_ordinal":1}})
}
fn comment(index: u32, section: &str) -> Value {
    json!({"identity":{"logical_comment_id":format!("comment-{index}"),"begin_control_id":100+index,"field_id":200+index},
        "anchor":anchor(section,0),"native_begin_tag":"field_begin","native_end_tag":"field_end","native_field_type":"memo",
        "semantic_binding":"unverified_memo_parameters","name_sha256":null,"editable":true,"dirty":false,"z_order":0,
        "author_id":1,"created_at":{"epoch_millis":1_700_000_000_000_u64,"original_utc_offset_minutes":540},"modified_at":null,
        "body_graph_sha256":digest(),"plain_text_sha256":null,"parameters_sha256":digest(),"sub_list_sha256":digest(),
        "style_id":12,"visibility":"shown","resolution":{"resolved":false,"resolver_author_id":null,"resolved_at":null},
        "opaque_native_payload_sha256":digest(),"opaque_properties":[],"locked":false})
}
pub(super) fn state() -> Result<CommentDocumentState, Box<dyn std::error::Error>> {
    let draft = json!({
        "schema_version":COMMENT_MODEL_SCHEMA_VERSION,
        "sections":[{"section_id":"section-1","memo_shape_id_ref":12,"opaque_section_state_sha256":digest(),"locked":false},
                    {"section_id":"section-2","memo_shape_id_ref":12,"opaque_section_state_sha256":digest(),"locked":false}],
        "authors":[{"author_id":1,"name_sha256":digest(),"email_sha256":null,"opaque_author_state_sha256":digest(),"locked":false}],
        "styles":[{"style_id":12,"width_native_units":2835,"line_width":"mm0_12","line_type":"solid",
                   "line_color_rgb":17,"fill_color_rgb":34,"active_color_rgb":51,"memo_type":"normal",
                   "opaque_style_sha256":digest(),"locked":false}],
        "hidden_explanations":[{"identity":{"logical_explanation_id":"explanation-1"},"anchor":anchor("section-1",1),
            "native_tag":"hidden_comment","enabled":true,"body_graph_sha256":digest(),"plain_text_sha256":null,
            "sub_list_sha256":digest(),"opaque_native_payload_sha256":digest(),"opaque_properties":[],"locked":false}],
        "comments":[comment(1,"section-1"),comment(2,"section-2")],
        "non_comment_content_sha256":digest(),"field_inventory_sha256":digest(),"style_catalog_sha256":digest(),
        "reference_inventory_sha256":digest(),"resource_inventory_sha256":digest(),"document_protection_sha256":digest(),
        "opaque_document_state_sha256":digest(),"document_locked":false
    });
    Ok(CommentDocumentState::from_draft(
        serde_json::from_value(draft)?,
        limits(),
    )?)
}
fn paragraph(value: &str) -> Node {
    Node::Paragraph(ParagraphNode {
        common: NodeCommon::new(id(value)),
        inlines: vec![Inline::Text {
            text: "synthetic caller text".into(),
        }],
        paragraph_properties: Properties::new(),
    })
}
fn property(key: &str, value: String) -> Properties {
    let mut p = Properties::new();
    p.insert(key, PropertyValue::Text(value));
    p
}
pub(super) fn graph(
    state: &CommentDocumentState,
) -> Result<DocumentGraph, Box<dyn std::error::Error>> {
    let sections = state
        .sections()
        .iter()
        .enumerate()
        .map(|(index, section)| Section {
            section_id: section.section_id.clone(),
            properties: property(
                COMMENT_SECTION_PROPERTY,
                serde_json::to_string(section).expect("fixture section"),
            ),
            master_pages: vec![],
            headers_footers: vec![],
            body: Flow {
                children: if index == 0 {
                    vec![
                        paragraph("body-1"),
                        paragraph("body-2"),
                        paragraph("body-3"),
                    ]
                } else {
                    vec![paragraph("body-4")]
                },
            },
        })
        .collect();
    let mut draft = DocumentGraphDraft::new(DocumentId::parse("comment-document")?, sections);
    draft.metadata = property(
        COMMENT_STATE_PROPERTY,
        String::from_utf8(state.canonical_json(limits())?)?,
    );
    draft
        .metadata
        .insert("unrelated", PropertyValue::Text("kept".into()));
    draft
        .settings
        .insert("setting", PropertyValue::Boolean(true));
    draft.styles = state
        .styles()
        .iter()
        .map(|s| Style {
            style_id: id(&format!("caller-style-{}", s.style_id)),
            based_on: None,
            properties: property(
                COMMENT_STYLE_PROPERTY,
                serde_json::to_string(s).expect("fixture style"),
            ),
        })
        .collect();
    draft.styles.push(Style {
        style_id: id("unrelated-style"),
        based_on: None,
        properties: Properties::new(),
    });
    draft.notes.push(Note {
        note_id: id("unrelated-note"),
        body: Flow {
            children: vec![paragraph("note-body")],
        },
        properties: Properties::new(),
    });
    for hidden in state.hidden_explanations() {
        draft.review.push(ReviewEntry {
            review_id: hidden.identity.logical_explanation_id.clone(),
            target_node_id: id("body-2"),
            properties: property(COMMENT_ENTRY_PROPERTY, serde_json::to_string(hidden)?),
        });
    }
    for (i, entry) in state.comments().iter().enumerate() {
        let mut properties = property(COMMENT_ENTRY_PROPERTY, serde_json::to_string(entry)?);
        properties.insert("preserved-opaque", PropertyValue::Text("kept".into()));
        draft.review.push(ReviewEntry {
            review_id: entry.identity.logical_comment_id.clone(),
            target_node_id: id(if i == 0 { "body-1" } else { "body-4" }),
            properties,
        });
    }
    draft.review.push(ReviewEntry {
        review_id: id("unrelated-review"),
        target_node_id: id("body-1"),
        properties: Properties::new(),
    });
    Ok(DocumentGraph::from_draft(
        draft,
        DocumentGraphLimits::default(),
    )?)
}
pub(super) fn request(
    ctx: &CommentOperationContext<'_>,
    state: &CommentDocumentState,
    operation: CommentOperation,
) -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    Ok(serde_json::to_vec(&CommentRequestDraft {
        schema_version: COMMENT_MODEL_SCHEMA_VERSION.into(),
        request_id: id("request-1"),
        expected_source_state_sha256: state.canonical_sha256(limits())?,
        expected_document_flow_sha256: ctx.document_flow_sha256().into(),
        target_document_flow_sha256: ctx.document_flow_sha256().into(),
        operation,
    })?)
}
pub(super) fn operations(state: &CommentDocumentState) -> Vec<CommentOperation> {
    let mut new = state.comments()[0].clone();
    new.identity.logical_comment_id = id("comment-3");
    new.identity.begin_control_id = 103;
    new.identity.field_id = 203;
    new.anchor.start.paragraph_ordinal = 2;
    new.anchor.end.paragraph_ordinal = 2;
    let mut style = state.styles()[0].clone();
    style.width_native_units += 1;
    vec![
        CommentOperation::SetHiddenExplanation {
            target: state.hidden_explanations()[0].identity.clone(),
            enabled: false,
        },
        CommentOperation::InsertComment {
            insertion_index: 1,
            comment: Box::new(new),
        },
        CommentOperation::ReplaceStyle {
            style_id: 12,
            style,
        },
        CommentOperation::SetVisibility {
            target: state.comments()[0].identity.clone(),
            visibility: CommentVisibility::Hidden,
        },
        CommentOperation::SetResolution {
            target: state.comments()[0].identity.clone(),
            resolution: CommentResolution {
                resolved: true,
                resolver_author_id: Some(1),
                resolved_at: Some(CommentTimestamp {
                    epoch_millis: 1_700_000_000_010,
                    original_utc_offset_minutes: 540,
                }),
            },
        },
    ]
}
