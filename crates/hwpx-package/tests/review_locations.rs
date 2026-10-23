//! Original XML/IR coordinates, NOT native caret/visual or author/state evidence.
use hwpx_package::document_import::structure::review::{
    ImportedDocumentReviewBodies, ReviewBodyKind, locations::ReviewLocationError,
};
use std::error::Error;
#[path = "support/document_import_field_fixture.rs"]
mod fixture;
type TestResult = Result<(), Box<dyn Error>>;
fn memo(id: u32) -> String {
    format!(
        "<hp:ctrl><hp:fieldBegin id='{id}' type='MEMO'><hp:parameters cnt='0'/><hp:subList><hp:p id='101'><hp:run><hp:t>PRIVATE-BODY</hp:t></hp:run></hp:p></hp:subList><hp:metaTag>UNINTERPRETED</hp:metaTag></hp:fieldBegin></hp:ctrl>"
    )
}
fn end(id: u32) -> String {
    format!("<hp:ctrl><hp:fieldEnd beginIDRef='{id}'/></hp:ctrl>")
}
fn paragraph(id: u32) -> String {
    format!(
        "<hp:p id='{id}'><hp:run><hp:t>BEFORE</hp:t>{}<hp:t>VISIBLE</hp:t></hp:run><hp:run><hp:t>AFTER</hp:t>{}</hp:run></hp:p>",
        memo(1),
        end(1)
    )
}
#[test]
fn memo_source_points_bind_original_paragraph_control_refs_and_cross_run_pair() -> TestResult {
    let bytes = fixture::package(&paragraph(1))?;
    let forms = fixture::forms(&bytes, "review-locations")?;
    let review = ImportedDocumentReviewBodies::import(&forms)?;
    let result = review.locate(&bytes)?;
    let location = &result.locations()[0];
    assert_eq!(location.start.point.paragraph_ordinal, 0);
    assert_eq!(location.start.point.run_ordinal, 0);
    assert_eq!(location.start.point.inline_ordinal, 1);
    assert_eq!(location.end.point.run_ordinal, 1);
    assert_eq!(location.end.point.inline_ordinal, 1);
    assert_eq!(
        location.start.paragraph_anchor,
        location.end.paragraph_anchor
    );
    assert_ne!(location.start.run_anchor, location.end.run_anchor);
    assert_eq!(
        location.target_node_id,
        review.observations()[0].target_node_id
    );
    let simple = location
        .direct_section_item_anchor
        .as_ref()
        .ok_or("simple anchor")?;
    assert_eq!(simple.start, location.start.point);
    assert_eq!(simple.end, location.end.point);
    assert_eq!(result.verify_source(&bytes)?, *result.receipt());
    assert_eq!(result.receipt().direct_section_item_anchors, 1);
    assert!(!result.receipt().native_caret_or_visual_coordinates_verified);
    assert!(!result.receipt().native_author_time_state_verified);
    assert!(!result.receipt().execution_publication_authority);
    let debug = format!("{result:?} {:?}", result.locations());
    assert!(!debug.contains("PRIVATE") && !debug.contains("UNINTERPRETED"));
    Ok(())
}
#[test]
fn sibling_paragraph_order_not_numeric_ids_or_nested_memo_body_paragraphs() -> TestResult {
    let bytes = fixture::package(&format!("{}{}", paragraph(1), paragraph(1)))?;
    let forms = fixture::forms(&bytes, "review-locations")?;
    let review = ImportedDocumentReviewBodies::import(&forms)?;
    let result = review.locate(&bytes)?;
    assert_eq!(result.locations().len(), 2);
    let first = &result.locations()[0];
    let second = &result.locations()[1];
    assert_eq!(first.start.point.paragraph_ordinal, 0);
    assert_eq!(second.start.point.paragraph_ordinal, 1);
    assert_ne!(first.paragraph_node_id, second.paragraph_node_id);
    assert_ne!(first.start.paragraph_anchor, second.start.paragraph_anchor);
    assert_ne!(first.review_id, second.review_id);
    assert_eq!(
        first.start.point.run_ordinal,
        second.start.point.run_ordinal
    );
    Ok(())
}
#[test]
fn hidden_direct_and_ctrl_use_actual_item_and_same_point_not_fabricated_range() -> TestResult {
    let hidden = "<hp:hiddenComment><hp:subList><hp:p id='2'><hp:run><hp:t>HIDDEN</hp:t></hp:run></hp:p></hp:subList></hp:hiddenComment>";
    for ctrl in [false, true] {
        let item = if ctrl {
            format!("<hp:ctrl>{hidden}</hp:ctrl>")
        } else {
            hidden.into()
        };
        let bytes = fixture::package(&format!(
            "<hp:p id='1'><hp:run><hp:t>VISIBLE</hp:t>{item}<hp:t>AFTER</hp:t></hp:run></hp:p>"
        ))?;
        let forms = fixture::forms(&bytes, "review-locations")?;
        let review = ImportedDocumentReviewBodies::import(&forms)?;
        let result = review.locate(&bytes)?;
        let location = &result.locations()[0];
        assert_eq!(location.kind, ReviewBodyKind::HiddenExplanation);
        assert_eq!(location.start, location.end);
        assert_eq!(location.start.point.inline_ordinal, 1);
        let resolved = forms.source().resolve_anchor(&location.start.item_anchor)?;
        assert_eq!(
            resolved.element().ok_or("item")?.name().local_name(),
            if ctrl { "ctrl" } else { "hiddenComment" }
        );
    }
    Ok(())
}
fn table(body: &str) -> String {
    let cell = format!(
        "<hp:tc name='' header='0' hasMargin='0' protect='0' editable='0' dirty='0' borderFillIDRef='1'><hp:cellAddr colAddr='0' rowAddr='0'/><hp:cellSpan colSpan='1' rowSpan='1'/><hp:cellSz width='2000' height='1000'/><hp:cellMargin left='0' right='0' top='0' bottom='0'/><hp:subList id='' textDirection='HORIZONTAL' lineWrap='BREAK' vertAlign='CENTER' linkListIDRef='0' linkListNextIDRef='0' textWidth='0' textHeight='0' hasTextRef='0' hasNumRef='0'>{body}</hp:subList></hp:tc>"
    );
    format!(
        "<hp:tbl id='9' zOrder='0' numberingType='TABLE' textWrap='TOP_AND_BOTTOM' textFlow='BOTH_SIDES' lock='0' dropcapstyle='None' pageBreak='CELL' repeatHeader='0' rowCnt='1' colCnt='1' cellSpacing='0' borderFillIDRef='1' noAdjust='0'><hp:sz width='2000' widthRelTo='ABSOLUTE' height='1000' heightRelTo='ABSOLUTE' protect='0'/><hp:pos treatAsChar='1' affectLSpacing='0' flowWithText='1' allowOverlap='0' holdAnchorAndSO='0' vertRelTo='PARA' horzRelTo='COLUMN' vertAlign='TOP' horzAlign='LEFT' vertOffset='0' horzOffset='0'/><hp:outMargin left='0' right='0' top='0' bottom='0'/><hp:inMargin left='0' right='0' top='0' bottom='0'/><hp:tr>{cell}</hp:tr></hp:tbl>"
    )
}
#[test]
fn nested_table_cell_keeps_complete_path_and_never_flattens_into_simple_section_anchor()
-> TestResult {
    let body = format!(
        "<hp:p id='2'><hp:run><hp:t>BEFORE</hp:t>{}<hp:t>VISIBLE</hp:t>{}</hp:run></hp:p>",
        memo(1),
        end(1)
    );
    let bytes = fixture::package(&format!(
        "<hp:p id='1'><hp:run><hp:t>MAIN</hp:t>{}</hp:run></hp:p>",
        table(&body)
    ))?;
    let forms = fixture::forms(&bytes, "review-locations")?;
    let review = ImportedDocumentReviewBodies::import(&forms)?;
    let result = review.locate(&bytes)?;
    let location = &result.locations()[0];
    assert!(location.direct_section_item_anchor.is_none());
    assert_eq!(result.receipt().nested_source_paths, 1);
    assert_eq!(location.start.point.paragraph_ordinal, 0);
    assert_eq!(location.start.point.inline_ordinal, 1);
    let names = location
        .start
        .container_path
        .iter()
        .map(|anchor| {
            Ok(forms
                .source()
                .resolve_anchor(anchor)?
                .element()
                .ok_or("element")?
                .name()
                .local_name()
                .to_owned())
        })
        .collect::<Result<Vec<_>, Box<dyn Error>>>()?;
    assert_eq!(names, ["sec", "p", "run", "tbl", "tr", "tc", "subList"]);
    assert_eq!(result.verify_source(&bytes)?, *result.receipt());
    Ok(())
}
#[test]
fn stale_other_document_and_metadata_only_source_changes_cannot_rebind_cached_points() -> TestResult
{
    let bytes = fixture::package(&paragraph(1))?;
    let forms = fixture::forms(&bytes, "review-locations")?;
    let review = ImportedDocumentReviewBodies::import(&forms)?;
    let result = review.locate(&bytes)?;
    assert_eq!(
        result.verify_source(&[0]).err(),
        Some(ReviewLocationError::Source)
    );
    let changed = fixture::package(&paragraph(1).replace("UNINTERPRETED", "CHANGED"))?;
    assert_eq!(
        result.verify_source(&changed).err(),
        Some(ReviewLocationError::Source)
    );
    let foreign_forms = fixture::forms(&bytes, "foreign-review-locations")?;
    let foreign_review = ImportedDocumentReviewBodies::import(&foreign_forms)?;
    let foreign = foreign_review.locate(&bytes)?;
    assert_ne!(
        result.locations()[0].paragraph_node_id,
        foreign.locations()[0].paragraph_node_id
    );
    assert_ne!(
        result.receipt().locations_sha256,
        foreign.receipt().locations_sha256
    );
    assert_eq!(review.verify_source(&bytes)?, *review.receipt());
    Ok(())
}
#[test]
fn original_locked_capture_without_reviews_has_no_fabricated_location() -> TestResult {
    let bytes = fixture::captured()?;
    let forms = fixture::forms(&bytes, "review-locations")?;
    let review = ImportedDocumentReviewBodies::import(&forms)?;
    let result = review.locate(&bytes)?;
    assert!(result.locations().is_empty());
    assert_eq!(result.receipt().locations, 0);
    assert_eq!(result.receipt().nested_source_paths, 0);
    assert_eq!(result.verify_source(&bytes)?, *result.receipt());
    Ok(())
}

#[test]
fn full_sibling_inventory_keeps_order_and_complete_bindings_without_numeric_identity_aliases()
-> TestResult {
    let body = (0..256).map(|_| paragraph(1)).collect::<String>();
    let bytes = fixture::package(&body)?;
    let forms = fixture::forms(&bytes, "review-locations")?;
    let review = ImportedDocumentReviewBodies::import(&forms)?;
    let result = review.locate(&bytes)?;
    assert_eq!(result.locations().len(), 256);
    assert_eq!(result.receipt().direct_section_item_anchors, 256);
    for (ordinal, location) in result.locations().iter().enumerate() {
        assert_eq!(
            usize::try_from(location.start.point.paragraph_ordinal)?,
            ordinal
        );
        assert_eq!(
            location.end.point.paragraph_ordinal,
            location.start.point.paragraph_ordinal
        );
        assert_eq!(location.start.point.inline_ordinal, 1);
        assert!(location.direct_section_item_anchor.is_some());
    }
    assert_eq!(result.verify_source(&bytes)?, *result.receipt());
    Ok(())
}
