#![allow(clippy::expect_used)] // Synthetic bounded fixtures only.
use domain_ir::*;
use hwpx_agent_cli::comment_operation::*;
use serde_json::{Value, json};
type TestResult = Result<(), Box<dyn std::error::Error>>;
fn id(value: &str) -> LogicalId { LogicalId::parse(value).expect("fixture logical ID") }
fn limits() -> CommentLimits {
    CommentLimits::new(CommentLimitConfig::default()).expect("fixture limits")
}
fn digest() -> String { "a".repeat(64) }
fn anchor(section: &str, paragraph: u32) -> Value {
    json!({"section_id":section,"start":{"paragraph_ordinal":paragraph,"run_ordinal":0,"inline_ordinal":0},
        "end":{"paragraph_ordinal":paragraph,"run_ordinal":0,"inline_ordinal":1}})
}
fn comment(index: u32, section: &str) -> Value {
    json!({"identity":{"logical_comment_id":format!("comment-{index}"),"begin_control_id":100+index,"field_id":200+index},
        "anchor":anchor(section,0),"native_begin_tag":"field_begin","native_end_tag":"field_end","native_field_type":"memo",
        "semantic_binding":"unverified_memo_parameters","name_sha256":null,"editable":true,"dirty":false,"z_order":0,
        "author_id":1,"created_at":{"epoch_millis":1700000000000_u64,"original_utc_offset_minutes":540},"modified_at":null,
        "body_graph_sha256":digest(),"plain_text_sha256":null,"parameters_sha256":digest(),"sub_list_sha256":digest(),
        "style_id":12,"visibility":"shown","resolution":{"resolved":false,"resolver_author_id":null,"resolved_at":null},
        "opaque_native_payload_sha256":digest(),"opaque_properties":[],"locked":false})
}
fn state() -> Result<CommentDocumentState, Box<dyn std::error::Error>> {
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
    Ok(CommentDocumentState::from_draft(serde_json::from_value(draft)?,limits())?)
}
fn paragraph(value: &str) -> Node {
    Node::Paragraph(ParagraphNode {common:NodeCommon::new(id(value)),
        inlines:vec![Inline::Text{text:"synthetic caller text".into()}],paragraph_properties:Properties::new()})
}
fn property(key: &str, value: String) -> Properties {
    let mut p=Properties::new();p.insert(key,PropertyValue::Text(value));p
}
fn graph(state: &CommentDocumentState) -> Result<DocumentGraph, Box<dyn std::error::Error>> {
    let sections=state.sections().iter().enumerate().map(|(index, section)| Section {
        section_id:section.section_id.clone(),
        properties:property(COMMENT_SECTION_PROPERTY,serde_json::to_string(section).expect("fixture section")),
        master_pages:vec![],headers_footers:vec![],
        body:Flow {children:if index==0 {vec![paragraph("body-1"),paragraph("body-2"),paragraph("body-3")]}
                             else {vec![paragraph("body-4")]}},
    }).collect();
    let mut draft=DocumentGraphDraft::new(DocumentId::parse("comment-document")?,sections);
    draft.metadata=property(COMMENT_STATE_PROPERTY,String::from_utf8(state.canonical_json(limits())?)?);
    draft.metadata.insert("unrelated",PropertyValue::Text("kept".into()));
    draft.settings.insert("setting",PropertyValue::Boolean(true));
    draft.styles=state.styles().iter().map(|s| Style {style_id:id(&format!("caller-style-{}",s.style_id)),
        based_on:None,properties:property(COMMENT_STYLE_PROPERTY,serde_json::to_string(s).expect("fixture style"))}).collect();
    draft.styles.push(Style{style_id:id("unrelated-style"),based_on:None,properties:Properties::new()});
    draft.notes.push(Note{note_id:id("unrelated-note"),body:Flow{children:vec![paragraph("note-body")]},properties:Properties::new()});
    for hidden in state.hidden_explanations() {
        draft.review.push(ReviewEntry{review_id:hidden.identity.logical_explanation_id.clone(),target_node_id:id("body-2"),
            properties:property(COMMENT_ENTRY_PROPERTY,serde_json::to_string(hidden)?)});
    }
    for (i, entry) in state.comments().iter().enumerate() {
        let mut properties=property(COMMENT_ENTRY_PROPERTY,serde_json::to_string(entry)?);
        properties.insert("preserved-opaque",PropertyValue::Text("kept".into()));
        draft.review.push(ReviewEntry{review_id:entry.identity.logical_comment_id.clone(),
            target_node_id:id(if i==0 {"body-1"} else {"body-4"}),properties});
    }
    draft.review.push(ReviewEntry{review_id:id("unrelated-review"),target_node_id:id("body-1"),properties:Properties::new()});
    Ok(DocumentGraph::from_draft(draft,DocumentGraphLimits::default())?)
}
fn context<'a>(graph: &'a DocumentGraph, state: &'a CommentDocumentState)
    -> Result<CommentOperationContext<'a>, Box<dyn std::error::Error>> {
    Ok(CommentOperationContext::bind(graph,state,graph.canonical_sha256()?,[7;32],RevisionId::parse("r1")?)?)
}
fn request(ctx: &CommentOperationContext<'_>, state: &CommentDocumentState, operation: CommentOperation)
    -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    Ok(serde_json::to_vec(&CommentRequestDraft {schema_version:COMMENT_MODEL_SCHEMA_VERSION.into(),
        request_id:id("request-1"),expected_source_state_sha256:state.canonical_sha256(limits())?,
        expected_document_flow_sha256:ctx.document_flow_sha256().into(),
        target_document_flow_sha256:ctx.document_flow_sha256().into(),operation})?)
}
fn operations(state: &CommentDocumentState) -> Vec<CommentOperation> {
    let mut new=state.comments()[0].clone();
    new.identity.logical_comment_id=id("comment-3");new.identity.begin_control_id=103;new.identity.field_id=203;
    new.anchor.start.paragraph_ordinal=2;new.anchor.end.paragraph_ordinal=2;
    let mut style=state.styles()[0].clone();style.width_native_units+=1;
    vec![
        CommentOperation::SetHiddenExplanation{target:state.hidden_explanations()[0].identity.clone(),enabled:false},
        CommentOperation::InsertComment{insertion_index:1,comment:Box::new(new)},
        CommentOperation::ReplaceStyle{style_id:12,style},
        CommentOperation::SetVisibility{target:state.comments()[0].identity.clone(),visibility:CommentVisibility::Hidden},
        CommentOperation::SetResolution{target:state.comments()[0].identity.clone(),resolution:CommentResolution {
            resolved:true,resolver_author_id:Some(1),resolved_at:Some(CommentTimestamp {
                epoch_millis:1700000000010,original_utc_offset_minutes:540})}},
    ]
}
#[test]
fn all_five_original_operations_compile_on_real_paths_and_preserve_complete_document() -> TestResult {
    let state=state()?;let source=graph(&state)?;let ctx=context(&source,&state)?;
    let original=source.canonical_json()?;
    for operation in operations(&state) {
        let insertion=if let CommentOperation::InsertComment{comment,..}=&operation {
            Some(CommentInsertionTarget{anchor:comment.anchor.clone(),node_id:id("body-3")})
        } else {None};
        let capability=operation.capability_id();
        let prepared=CommentOperationPreparation::prepare_json(&ctx,PlanId::parse("p1")?,
            &request(&ctx,&state,operation)?,insertion)?;
        assert_eq!(prepared.receipt().capability_id,capability);
        assert!(prepared.compiled().operations().iter().all(|op| op.capability_id().as_str()==capability));
        assert_eq!(prepared.verify(&ctx)?,*prepared.receipt());
        assert_eq!(prepared.require_current_product_route(&ctx),Err(CommentOperationError::RouteUnqualified));
        assert!(!prepared.receipt().native_author_time_state_verified);
        assert!(!prepared.receipt().hwpx_lowered);
        assert!(!prepared.receipt().execution_authority_verified);
        assert_ne!(source, *prepared.target_graph());
        let before=source.clone().into_draft();let mut after=prepared.target_graph().clone().into_draft();
        // Exactly the complete state/entry/style properties, or the one new entry, may change.
        after.metadata=before.metadata.clone();after.styles=before.styles.clone();after.review=before.review.clone();
        assert_eq!(DocumentGraph::from_draft(after,DocumentGraphLimits::default())?,source);
        assert_eq!(source.canonical_json()?,original);
        assert!(!format!("{prepared:?}").contains("synthetic caller text"));
    }
    Ok(())
}
#[test]
fn missing_extra_reordered_wrong_section_and_nontext_views_are_rejected() -> TestResult {
    let state=state()?;let source=graph(&state)?;
    for fault in 0..7 {
        let mut draft=source.clone().into_draft();
        match fault {
            0=>{draft.review.remove(1);},
            1=>draft.review[3].properties.insert(COMMENT_ENTRY_PROPERTY,PropertyValue::Text("{}".into())),
            2=>draft.review.swap(1,2),
            3=>draft.review[1].target_node_id=id("body-4"),
            4=>draft.styles[0].properties.insert(COMMENT_STYLE_PROPERTY,PropertyValue::Boolean(true)),
            5=>draft.metadata.insert(COMMENT_STATE_PROPERTY,PropertyValue::Text("{}".into())),
            _=>draft.sections[0].properties.insert(COMMENT_SECTION_PROPERTY,PropertyValue::Text("{}".into())),
        }
        let changed=DocumentGraph::from_draft(draft,DocumentGraphLimits::default())?;
        assert!(context(&changed,&state).is_err());
    }
    Ok(())
}
#[test]
fn partial_native_import_markers_and_protection_never_become_full_comment_authority() -> TestResult {
    let state=state()?;let source=graph(&state)?;
    for fault in 0..4 {
        let mut draft=source.clone().into_draft();
        match fault {
            0=>draft.metadata.insert("review_body_import_profile",PropertyValue::Text(
                hwpx_package::document_import::structure::review::REVIEW_BODY_IMPORT_PROFILE.into())),
            1=>draft.security_state.protected=true,
            2=>draft.security_state.signed=true,
            _=>draft.security_state.encrypted=true,
        }
        let changed=DocumentGraph::from_draft(draft,DocumentGraphLimits::default())?;
        assert!(context(&changed,&state).is_err());
    }
    Ok(())
}
#[test]
fn stale_state_flow_unknown_duplicate_oversized_and_delete_requests_fail_closed() -> TestResult {
    let state=state()?;let source=graph(&state)?;let ctx=context(&source,&state)?;
    let operation=operations(&state).remove(3);
    let original=request(&ctx,&state,operation)?;
    for fault in 0..7 {
        let mut value:Value=serde_json::from_slice(&original)?;
        match fault {
            0=>value["expected_source_state_sha256"]=json!("b".repeat(64)),
            1=>value["expected_document_flow_sha256"]=json!("c".repeat(64)),
            2=>value["target_document_flow_sha256"]=json!("d".repeat(64)),
            3=>value["extra"]=json!(true),
            4=>value["operation"]["kind"]=json!("delete_comment"),
            5=>value["schema_version"]=json!("unqualified/v2"),
            _=>value["operation"]["visibility"]=json!("shown"),
        }
        assert!(CommentOperationPreparation::prepare_json(&ctx,PlanId::parse("p1")?,
            &serde_json::to_vec(&value)?,None).is_err());
    }
    let duplicated=String::from_utf8(original)?.replacen("{","{\"request_id\":\"duplicate\",",1);
    assert!(CommentOperationPreparation::prepare_json(&ctx,PlanId::parse("p1")?,duplicated.as_bytes(),None).is_err());
    assert!(CommentOperationPreparation::prepare_json(&ctx,PlanId::parse("p1")?,&vec![b' ';1024*1024+1],None).is_err());
    Ok(())
}
#[test]
fn insertion_requires_the_exact_anchor_and_an_actual_node_in_the_same_section() -> TestResult {
    let state=state()?;let source=graph(&state)?;let ctx=context(&source,&state)?;
    let operation=operations(&state).remove(1);
    let CommentOperation::InsertComment{comment,..}=&operation else {return Err("fixture kind".into());};
    let mut wrong_anchor=comment.anchor.clone();wrong_anchor.start.inline_ordinal=1;
    let bindings=[None,Some(CommentInsertionTarget{anchor:comment.anchor.clone(),node_id:id("missing")}),
        Some(CommentInsertionTarget{anchor:comment.anchor.clone(),node_id:id("body-4")}),
        Some(CommentInsertionTarget{anchor:wrong_anchor,node_id:id("body-3")})];
    let raw=request(&ctx,&state,operation.clone())?;
    for binding in bindings {
        assert!(CommentOperationPreparation::prepare_json(&ctx,PlanId::parse("p1")?,&raw,binding).is_err());
    }
    let extra=Some(CommentInsertionTarget{anchor:comment.anchor.clone(),node_id:id("body-3")});
    assert!(CommentOperationPreparation::prepare_json(&ctx,PlanId::parse("p1")?,
        &request(&ctx,&state,operations(&state).remove(3))?,extra).is_err());
    Ok(())
}
#[test]
fn fresh_package_revision_graph_and_model_protection_drift_are_rejected() -> TestResult {
    let state=state()?;let source=graph(&state)?;let ctx=context(&source,&state)?;
    let prepared=CommentOperationPreparation::prepare_json(&ctx,PlanId::parse("p1")?,
        &request(&ctx,&state,operations(&state).remove(3))?,None)?;
    for fault in 0..3 {
        let mut draft=source.clone().into_draft();
        if fault==2 {draft.metadata.insert("unrelated",PropertyValue::Text("changed".into()));}
        let graph=DocumentGraph::from_draft(draft,DocumentGraphLimits::default())?;
        let fresh=CommentOperationContext::bind(&graph,&state,graph.canonical_sha256()?,
            if fault==0 {[8;32]} else {[7;32]},RevisionId::parse(if fault==1 {"r2"} else {"r1"})?)?;
        assert!(prepared.verify(&fresh).is_err());
    }
    let mut draft:CommentDocumentStateDraft=serde_json::from_slice(&state.canonical_json(limits())?)?;
    draft.document_locked=true;
    let locked=CommentDocumentState::from_draft(draft,limits())?;
    let graph=graph(&locked)?;let ctx=context(&graph,&locked)?;
    assert!(CommentOperationPreparation::prepare_json(&ctx,PlanId::parse("p1")?,
        &request(&ctx,&locked,operations(&locked).remove(3))?,None).is_err());
    Ok(())
}
