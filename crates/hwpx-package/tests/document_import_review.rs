//! Actual source parser/mapper path over synthetic envelopes and immutable captures.
//! Synthetic author-like strings are NOT qualified native metadata.
use domain_ir::{DocumentGraph, DocumentGraphLimits, Flow, Inline, Node, PropertyValue};
use hwpx_package::document_import::{
    fields::{
        ImportedDocumentFields,
        semantics::{ImportedDocumentFieldSemantics, ImportedFieldMeaning},
    },
    structure::review::{ImportedDocumentReviewBodies, ReviewBodyKind, ReviewNativeMetadata},
};
use std::error::Error;
#[path = "support/document_import_field_fixture.rs"]
mod fixture;
#[path = "support/document_import_settings_inputs.rs"]
mod inputs;
type TestResult = Result<(), Box<dyn Error>>;

fn paragraph(body: &str) -> String {
    format!("<hp:p id='1'><hp:run>{body}</hp:run></hp:p>")
}
fn body(text: &str) -> String {
    format!(
        "<hp:subList id='raw-body'>{}</hp:subList>",
        paragraph(&format!("<hp:t>{text}</hp:t>"))
    )
}
fn memo(id: u32, payload: &str) -> String {
    format!(
        "<hp:ctrl><hp:fieldBegin id='{id}' type='MEMO' editable='0'>{payload}</hp:fieldBegin></hp:ctrl><hp:t>VISIBLE-CACHE</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='{id}'/></hp:ctrl>"
    )
}
fn hidden(payload: &str) -> String {
    format!("<hp:hiddenComment>{payload}</hp:hiddenComment>")
}
fn visible(flow: &Flow) -> String {
    let mut text = String::new();
    for node in &flow.children {
        match node {
            Node::Paragraph(p) => {
                for inline in &p.inlines {
                    if let Inline::Text { text: value } = inline {
                        text.push_str(value);
                    }
                }
            }
            Node::Table(t) => {
                for cell in &t.cells {
                    text.push_str(&visible(&cell.body));
                }
            }
            Node::Drawing(d) => text.push_str(&visible(&d.children)),
            _ => (),
        }
    }
    text
}
fn unchanged(
    fields: &ImportedDocumentFields<'_>,
    review: &ImportedDocumentReviewBodies<'_>,
) -> TestResult {
    let mut draft = review.graph().clone().into_draft();
    let original = fields.graph().clone().into_draft();
    draft.review = original.review;
    draft.metadata = original.metadata;
    assert_eq!(
        DocumentGraph::from_draft(draft, DocumentGraphLimits::default())?,
        *fields.graph()
    );
    Ok(())
}
fn rejects(body: &str) -> TestResult {
    let bytes = fixture::package(&paragraph(body))?;
    if let Ok(forms) = fixture::forms(&bytes, "review-test") {
        assert!(
            ImportedDocumentReviewBodies::import(&forms).is_err(),
            "invalid review accepted"
        );
    }
    Ok(())
}

#[test]
fn memo_body_reuses_original_field_stack_mapper_and_exact_source_anchors() -> TestResult {
    let bytes = fixture::package(&paragraph(&memo(1, &body("REVIEW-BODY"))))?;
    let forms = fixture::forms(&bytes, "review-test")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let review = ImportedDocumentReviewBodies::import(&forms)?;
    assert_eq!(
        (
            review.receipt().memo_fields,
            review.receipt().hidden_explanations
        ),
        (1, 0)
    );
    assert_eq!(review.receipt().memo_fields_without_body, 0);
    let observed = &review.observations()[0];
    assert_eq!(observed.kind, ReviewBodyKind::MemoField);
    assert_eq!(observed.target_node_id, fields.fields()[0].begin_node_id);
    assert_eq!(observed.marker_anchor, fields.fields()[0].begin_anchor);
    assert_eq!(
        observed.end_anchor.as_ref(),
        Some(&fields.fields()[0].end_anchor)
    );
    assert!(observed.parameter_anchor.is_none());
    assert_eq!(
        visible(observed.body.as_ref().ok_or("body")?),
        "REVIEW-BODY"
    );
    assert_eq!(visible(&review.graph().sections()[0].body), "VISIBLE-CACHE");
    let source = forms.source();
    for anchor in [
        Some(&observed.marker_anchor),
        observed.body_anchor.as_ref(),
        observed.end_anchor.as_ref(),
    ]
    .into_iter()
    .flatten()
    {
        assert!(source.resolve_anchor(anchor)?.element().is_some());
    }
    assert_eq!(
        observed
            .native_attributes
            .iter()
            .find(|(k, _)| *k == "editable")
            .map(|(_, v)| v),
        Some(&PropertyValue::Text("0".into()))
    );
    assert_eq!(
        observed
            .body_attributes
            .as_ref()
            .ok_or("attributes")?
            .iter()
            .find(|(k, _)| *k == "id")
            .map(|(_, v)| v),
        Some(&PropertyValue::Text("raw-body".into()))
    );
    assert_eq!(review.verify_source(&bytes)?, *review.receipt());
    assert_eq!(
        ImportedDocumentReviewBodies::import(&forms)?.observations(),
        review.observations()
    );
    unchanged(&fields, &review)
}

#[test]
fn hidden_explanations_direct_and_wrapped_target_only_their_actual_control_nodes() -> TestResult {
    for wrapped in [false, true] {
        let marker = hidden(&body("HIDDEN-TEXT"));
        let marker = if wrapped {
            format!("<hp:ctrl>{marker}</hp:ctrl>")
        } else {
            marker
        };
        let bytes = fixture::package(&paragraph(&format!("<hp:t>MAIN</hp:t>{marker}")))?;
        let forms = fixture::forms(&bytes, "review-test")?;
        let review = ImportedDocumentReviewBodies::import(&forms)?;
        assert_eq!(
            (
                review.receipt().hidden_explanations,
                review.receipt().memo_fields
            ),
            (1, 0)
        );
        let observed = &review.observations()[0];
        assert_eq!(observed.kind, ReviewBodyKind::HiddenExplanation);
        assert!(observed.end_anchor.is_none() && observed.parameter_anchor.is_none());
        assert_eq!(
            visible(observed.body.as_ref().ok_or("body")?),
            "HIDDEN-TEXT"
        );
        assert_eq!(visible(&review.graph().sections()[0].body), "MAIN");
        assert_eq!(
            review.graph().clone().into_draft().review[0].target_node_id,
            observed.target_node_id
        );
        assert_eq!(review.verify_source(&bytes)?, *review.receipt());
    }
    Ok(())
}

#[test]
fn memo_parameters_remain_exact_opaque_not_author_time_or_cached_body_defaults() -> TestResult {
    let parameters = "<hp:parameters cnt='2' name=''><hp:stringParam name='Author'>SYNTHETIC-AUTHOR</hp:stringParam><hp:stringParam name='Time'>SYNTHETIC-TIME</hp:stringParam></hp:parameters>";
    for payload in [
        String::new(),
        parameters.to_owned(),
        format!("{parameters}{}", body("BODY")),
    ] {
        let bytes = fixture::package(&paragraph(&memo(1, &payload)))?;
        let forms = fixture::forms(&bytes, "review-test")?;
        let review = ImportedDocumentReviewBodies::import(&forms)?;
        let observed = &review.observations()[0];
        assert_eq!(observed.parameter_anchor.is_some(), !payload.is_empty());
        assert_eq!(observed.body.is_some(), payload.contains("subList"));
        assert_eq!(
            review.receipt().memo_fields_without_body,
            usize::from(observed.body.is_none())
        );
        assert_eq!(
            observed.metadata,
            ReviewNativeMetadata::UnverifiedNativeMapping
        );
        assert!(!review.receipt().native_author_time_binding_verified);
        assert!(
            !review
                .receipt()
                .native_visibility_resolution_binding_verified
        );
        let fields = ImportedDocumentFields::import(&forms)?;
        let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
        assert!(
            matches!(&meanings.observations()[0].meaning, ImportedFieldMeaning::Unsupported { native_kind } if native_kind == "MEMO")
        );
        assert_eq!(review.verify_source(&bytes)?, *review.receipt());
    }
    Ok(())
}

#[test]
fn duplicate_native_paragraph_and_field_ids_in_separate_paragraphs_are_not_global_identity()
-> TestResult {
    let bytes = fixture::package(&format!(
        "{}{}",
        paragraph(&memo(1, &body("FIRST"))),
        paragraph(&memo(1, &body("SECOND")))
    ))?;
    let forms = fixture::forms(&bytes, "review-test")?;
    let review = ImportedDocumentReviewBodies::import(&forms)?;
    assert_eq!(review.observations().len(), 2);
    assert_ne!(
        review.observations()[0].review_id,
        review.observations()[1].review_id
    );
    assert_ne!(
        review.observations()[0].target_node_id,
        review.observations()[1].target_node_id
    );
    assert_ne!(
        review.observations()[0].body_anchor,
        review.observations()[1].body_anchor
    );
    assert_eq!(review.verify_source(&bytes)?, *review.receipt());
    Ok(())
}

#[test]
fn namespace_rebound_names_remain_opaque_and_do_not_fabricate_reviews() -> TestResult {
    let bytes = fixture::package(&paragraph(
        "<u:hiddenComment><u:subList><u:p>opaque</u:p></u:subList></u:hiddenComment>",
    ))?;
    let forms = fixture::forms(&bytes, "review-test")?;
    let review = ImportedDocumentReviewBodies::import(&forms)?;
    assert!(review.observations().is_empty());
    assert_eq!(review.verify_source(&bytes)?, *review.receipt());
    rejects(&memo(1, "<u:subList/>"))?;
    rejects(&hidden("<u:subList/>"))
}

#[test]
fn invalid_empty_duplicate_ordered_envelopes_and_parameter_counts_reject() -> TestResult {
    let good = body("BODY");
    let parameters = "<hp:parameters cnt='0'/>";
    for payload in [
        "<hp:subList/>".to_owned(),
        "<hp:subList><hp:run/></hp:subList>".to_owned(),
        "<hp:subList>unmodeled text</hp:subList>".to_owned(),
        format!("{good}{good}"),
        format!("{good}{parameters}"),
        format!("{parameters}{parameters}{good}"),
        format!("<hp:parameters cnt='1'/>{good}"),
        format!("<hp:parameters cnt='bad'/>{good}"),
        format!("<hp:parameters cnt='0' extra='1'/>{good}"),
        format!("<hp:metaTag/>{good}"),
        format!("DIRECT{good}"),
    ] {
        rejects(&memo(1, &payload))?;
    }
    for payload in [
        String::new(),
        format!("{good}{good}"),
        format!("{parameters}{good}"),
        "<hp:subList><u:p/></hp:subList>".into(),
    ] {
        rejects(&hidden(&payload))?;
    }
    Ok(())
}

#[test]
fn malformed_body_paragraph_and_table_semantics_reject_through_original_mapper() -> TestResult {
    for child in [
        "<hp:p id='invalid'><hp:run><hp:t>BODY</hp:t></hp:run></hp:p>",
        "<hp:p id='1'><hp:run><hp:t charStyleIDRef='invalid'>BODY</hp:t></hp:run></hp:p>",
        "<hp:p id='1'><hp:run><hp:t>BODY<hp:tab width='bad' leader='0' type='0'/></hp:t></hp:run></hp:p>",
        "<hp:p id='1'><hp:run><hp:tbl rowCnt='1' colCnt='1'/></hp:run></hp:p>",
    ] {
        let payload = format!("<hp:subList>{child}</hp:subList>");
        rejects(&memo(1, &payload))?;
        rejects(&hidden(&payload))?;
    }
    Ok(())
}

#[test]
fn nested_field_review_note_and_bookmark_semantics_are_not_silently_lost() -> TestResult {
    for nested in [
        "<hp:ctrl><hp:fieldBegin id='2' type='DATE'/></hp:ctrl><hp:ctrl><hp:fieldEnd beginIDRef='2'/></hp:ctrl>".to_owned(),
        hidden(&body("NESTED")),
        "<hp:ctrl><hp:footNote instId='2'><hp:subList><hp:p id='3'><hp:run><hp:t>NOTE</hp:t></hp:run></hp:p></hp:subList></hp:footNote></hp:ctrl>".to_owned(),
        "<hp:ctrl><hp:endNote instId='2'/></hp:ctrl>".to_owned(),
        "<hp:ctrl><hp:bookmark name='nested'/></hp:ctrl>".to_owned(),
    ] {
        let payload = format!("<hp:subList>{}</hp:subList>", paragraph(&nested));
        rejects(&memo(1, &payload))?;
        rejects(&hidden(&payload))?;
    }
    Ok(())
}

#[test]
fn unmatched_field_pairs_and_unrepresented_parent_controls_never_admit_reviews() -> TestResult {
    let good = memo(1, &body("BODY"));
    for marker in [
        good.replace("beginIDRef='1'", "beginIDRef='2'"),
        good.replace("<hp:ctrl><hp:fieldEnd beginIDRef='1'/></hp:ctrl>", ""),
        good.replace("id='1' type='MEMO'", "id='bad' type='MEMO'"),
        good.replace("<hp:ctrl>", "<hp:ctrl unknown='1'>"),
        format!("<u:wrapper>{}</u:wrapper>", hidden(&body("BODY"))),
        format!("<hp:ctrl>{}<u:other/></hp:ctrl>", hidden(&body("BODY"))),
    ] {
        rejects(&marker)?;
    }
    Ok(())
}

#[test]
fn non_memo_payload_and_public_typed_reader_boundaries_are_unchanged() -> TestResult {
    let memo = memo(1, &body("BODY"));
    for kind in ["DATE", "FORMULA", "HYPERLINK", "BOOKMARK"] {
        rejects(&memo.replace("type='MEMO'", &format!("type='{kind}'")))?;
    }
    let standalone = format!(
        "<hp:p xmlns:hp='http://www.hancom.co.kr/hwpml/2011/paragraph' id='1'><hp:run>{memo}</hp:run></hp:p>"
    );
    assert_eq!(
        hwpx_package::TextFlowReader::read(
            standalone.as_bytes(),
            hwpx_package::TextFlowLimits::default()
        ),
        Err(hwpx_package::TextFlowError::UnsupportedShape)
    );
    Ok(())
}

#[test]
fn source_review_depth_item_and_text_budgets_remain_enforced() -> TestResult {
    let deep = format!(
        "{}BODY{}",
        "<u:opaque>".repeat(300),
        "</u:opaque>".repeat(300)
    );
    rejects(&memo(
        1,
        &format!("<hp:subList>{}</hp:subList>", paragraph(&deep)),
    ))?;
    let repeated = "<u:opaque/>".repeat(16_385);
    rejects(&memo(
        1,
        &format!("<hp:subList>{}</hp:subList>", paragraph(&repeated)),
    ))?;
    let oversized = body(&"B".repeat(1_048_577));
    rejects(&memo(1, &oversized))?;
    // Every subsequent body is scoped to its own contiguous XML subtree.
    let mut markers = String::new();
    for id in 1..=80 {
        markers.push_str(&memo(id, &body("BODY")));
    }
    let bytes = fixture::package(&paragraph(&markers))?;
    let forms = fixture::forms(&bytes, "review-test")?;
    let review = ImportedDocumentReviewBodies::import(&forms)?;
    assert_eq!(review.observations().len(), 80);
    assert_eq!(review.verify_source(&bytes)?, *review.receipt());
    Ok(())
}

#[test]
fn rich_review_paragraphs_tables_and_unknown_xml_stay_in_the_original_body_flow() -> TestResult {
    // Synthetic one-cell envelope exercises the existing table grid mapper;
    // this is not a new native capture or a parallel table implementation.
    let cell = "<hp:tc name='' header='0' hasMargin='0' protect='0' editable='0' dirty='0' borderFillIDRef='1'><hp:cellAddr colAddr='0' rowAddr='0'/><hp:cellSpan colSpan='1' rowSpan='1'/><hp:cellSz width='2000' height='1000'/><hp:cellMargin left='0' right='0' top='0' bottom='0'/><hp:subList id='' textDirection='HORIZONTAL' lineWrap='BREAK' vertAlign='CENTER' linkListIDRef='0' linkListNextIDRef='0' textWidth='0' textHeight='0' hasTextRef='0' hasNumRef='0'><hp:p id='1'><hp:run><hp:t>CELL</hp:t></hp:run></hp:p></hp:subList></hp:tc>";
    let table = format!(
        "<hp:tbl id='9' zOrder='0' numberingType='TABLE' textWrap='TOP_AND_BOTTOM' textFlow='BOTH_SIDES' lock='0' dropcapstyle='None' pageBreak='CELL' repeatHeader='0' rowCnt='1' colCnt='1' cellSpacing='0' borderFillIDRef='1' noAdjust='0'><hp:sz width='2000' widthRelTo='ABSOLUTE' height='1000' heightRelTo='ABSOLUTE' protect='0'/><hp:pos treatAsChar='1' affectLSpacing='0' flowWithText='1' allowOverlap='0' holdAnchorAndSO='0' vertRelTo='PARA' horzRelTo='COLUMN' vertAlign='TOP' horzAlign='LEFT' vertOffset='0' horzOffset='0'/><hp:outMargin left='0' right='0' top='0' bottom='0'/><hp:inMargin left='0' right='0' top='0' bottom='0'/><hp:tr>{cell}</hp:tr></hp:tbl>"
    );
    let payload = format!(
        "<hp:subList><hp:p id='1' styleIDRef='3'><hp:run charPrIDRef='4'><hp:t>한글&amp;e&#x301;<hp:tab width='8000' leader='4' type='3'/><hp:lineBreak/></hp:t>{table}<u:future private='retained'/></hp:run></hp:p>{}</hp:subList>",
        paragraph("<hp:t>LAST</hp:t>")
    );
    for marker in [memo(1, &payload), hidden(&payload)] {
        let bytes = fixture::package(&paragraph(&marker))?;
        let forms = fixture::forms(&bytes, "review-test")?;
        let review = ImportedDocumentReviewBodies::import(&forms)?;
        let body = review.observations()[0].body.as_ref().ok_or("body")?;
        assert_eq!(visible(body), "한글&e\u{301}CELLLAST");
        assert_eq!(
            body.children
                .iter()
                .filter(|n| matches!(n, Node::Table(_)))
                .count(),
            1
        );
        assert_eq!(
            body.children
                .iter()
                .filter(|n| matches!(n, Node::EmbeddedObject(_)))
                .count(),
            1
        );
        for node in &body.children {
            assert!(
                forms
                    .source()
                    .resolve_anchor(node.common().source_anchor.as_ref().ok_or("anchor")?)?
                    .element()
                    .is_some()
            );
        }
        assert_eq!(review.verify_source(&bytes)?, *review.receipt());
    }
    Ok(())
}

#[test]
fn whole_source_drift_rejects_even_when_visible_cache_is_unchanged() -> TestResult {
    let first = fixture::package(&paragraph(&memo(1, &body("FIRST"))))?;
    let forms = fixture::forms(&first, "review-test")?;
    let review = ImportedDocumentReviewBodies::import(&forms)?;
    for changed in [
        body("SECOND"),
        body("FIRST").replace("raw-body", "new-attribute"),
    ] {
        let bytes = fixture::package(&paragraph(&memo(1, &changed)))?;
        assert!(review.verify_source(&bytes).is_err());
    }
    assert_eq!(review.verify_source(&first)?, *review.receipt());
    Ok(())
}

#[test]
fn debug_redacts_body_parameters_and_paths_without_claiming_full_comments() -> TestResult {
    let bytes = fixture::package(&paragraph(&memo(1, &body("SYNTHETIC-SECRET-BODY"))))?;
    let forms = fixture::forms(&bytes, "review-test")?;
    let review = ImportedDocumentReviewBodies::import(&forms)?;
    let debug = format!(
        "{review:?} {:?} {:?}",
        review.observations(),
        review.receipt()
    );
    for forbidden in ["SYNTHETIC-SECRET-BODY", "raw-body", "Contents/", "<hp:"] {
        assert!(!debug.contains(forbidden));
    }
    let draft = review.graph().clone().into_draft();
    assert_eq!(
        draft.source_profile,
        forms.graph().clone().into_draft().source_profile
    );
    assert_eq!(
        draft.security_state,
        forms.graph().clone().into_draft().security_state
    );
    assert!(review.receipt().qualification.contains("not_author_time"));
    Ok(())
}

#[test]
fn thirty_six_immutable_historical_inputs_retain_original_whole_graph_without_invented_reviews()
-> TestResult {
    let inputs = inputs::actual_corpus()?;
    assert_eq!(inputs.len(), 36);
    for bytes in inputs {
        let forms = fixture::forms(&bytes, "review-actual-test")?;
        let fields = ImportedDocumentFields::import(&forms)?;
        let review = ImportedDocumentReviewBodies::import(&forms)?;
        assert!(review.observations().is_empty());
        assert!(!review.receipt().native_author_time_binding_verified);
        assert_eq!(review.verify_source(&bytes)?, *review.receipt());
        unchanged(&fields, &review)?;
    }
    let captured = fixture::captured()?;
    let forms = fixture::forms(&captured, "review-captured-test")?;
    assert!(
        ImportedDocumentReviewBodies::import(&forms)?
            .observations()
            .is_empty()
    );
    Ok(())
}
