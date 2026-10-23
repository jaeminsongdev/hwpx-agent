//! Structural deletion fixtures; not native author/time/protection or product acceptance.
use hwpx_package::{
    BoundedZipReader, PackageLimits, WriterLimitConfig, WriterLimits,
    document_import::structure::review::{
        ImportedDocumentReviewBodies, ReviewBodyKind, delete_output::ReviewDeleteError,
    },
};
use sha2::{Digest as _, Sha256};
use std::{error::Error, io::Cursor};
#[path = "support/document_import_field_fixture.rs"]
mod fixture;
type TestResult = Result<(), Box<dyn Error>>;
type Parts = Vec<(String, Vec<u8>)>;
const BEGIN: &str = "<hp:ctrl><hp:fieldBegin id='1' type='MEMO'><hp:parameters cnt='0'/><hp:subList u:tag='opaque'><hp:p id='2'><hp:run><hp:t>PRIVATE-MEMO</hp:t></hp:run></hp:p></hp:subList><hp:metaTag>UNINTERPRETED</hp:metaTag></hp:fieldBegin></hp:ctrl>";
const END: &str = "<hp:ctrl><hp:fieldEnd beginIDRef='1'/></hp:ctrl>";
const HIDDEN: &str = "<hp:hiddenComment><hp:subList><hp:p id='3'><hp:run><hp:t>PRIVATE-HIDDEN</hp:t></hp:run></hp:p></hp:subList></hp:hiddenComment>";
const OTHER: &str = "<hp:ctrl><hp:fieldBegin id='4' type='MEMO'><hp:parameters cnt='0'/></hp:fieldBegin></hp:ctrl><hp:t>OTHER-SELECTED</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='4'/></hp:ctrl>";
fn source(hidden_ctrl: bool) -> Result<Vec<u8>, Box<dyn Error>> {
    let hidden = if hidden_ctrl {
        format!("<hp:ctrl>{HIDDEN}</hp:ctrl>")
    } else {
        HIDDEN.into()
    };
    fixture::package(&format!(
        "<hp:p id='1'><hp:run><hp:t>BEFORE</hp:t>{BEGIN}<hp:t>VISIBLE &amp; &lt;xml&gt;</hp:t>{END}<hp:t>AFTER</hp:t>{hidden}{OTHER}<hp:t>TAIL</hp:t></hp:run></hp:p>"
    ))
}
fn parts(bytes: &[u8]) -> Result<Parts, Box<dyn Error>> {
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let names: Vec<_> = reader
        .entries()
        .iter()
        .map(|e| e.path.as_str().to_owned())
        .collect();
    let mut result = Vec::new();
    for (index, name) in names.into_iter().enumerate() {
        result.push((name, reader.read_entry(index)?));
    }
    result.sort_by(|a, b| a.0.cmp(&b.0));
    Ok(result)
}
fn verify_parts(old: &[u8], new: &[u8], deleted: &[&str]) -> TestResult {
    let before = parts(old)?;
    let after = parts(new)?;
    assert_eq!(before.len(), after.len());
    for ((name, original), (other, output)) in before.into_iter().zip(after) {
        assert_eq!(name, other);
        if name == "Contents/section0.xml" {
            let mut expected = String::from_utf8(original)?;
            for value in deleted {
                assert_eq!(expected.matches(value).count(), 1);
                expected = expected.replacen(value, "", 1);
            }
            assert_eq!(output, expected.as_bytes());
        } else {
            assert_eq!(original, output);
        }
    }
    Ok(())
}
#[test]
fn memo_delete_removes_both_paired_wrappers_not_visible_text_other_reviews_or_parts() -> TestResult
{
    let bytes = source(false)?;
    let forms = fixture::forms(&bytes, "review-delete")?;
    let review = ImportedDocumentReviewBodies::import(&forms)?;
    let output = review.lower_delete(
        &bytes,
        &review.observations()[0].marker_anchor,
        WriterLimits::default(),
    )?;
    assert_eq!(output.receipt().kind, ReviewBodyKind::MemoField);
    assert_eq!(output.receipt().deleted_subtrees, 2);
    assert_eq!(output.receipt().changed_parts, 1);
    assert!(output.receipt().outside_deleted_subtrees_exact);
    assert!(!output.receipt().native_author_time_state_verified);
    assert!(!output.receipt().protection_execution_publication_authority);
    let result = output.with_verified_bytes(<[u8]>::to_vec)?;
    verify_parts(&bytes, &result, &[BEGIN, END])?;
    assert_eq!(
        Sha256::digest(&result).as_slice(),
        output.receipt().output_package_sha256
    );
    let after_forms = fixture::forms(&result, "review-delete")?;
    let after = ImportedDocumentReviewBodies::import(&after_forms)?;
    assert_eq!(after.receipt().memo_fields, 1);
    assert_eq!(after.receipt().hidden_explanations, 1);
    assert_eq!(review.verify_source(&bytes)?, *review.receipt());
    assert!(!format!("{output:?}").contains("PRIVATE"));
    Ok(())
}
#[test]
fn hidden_direct_and_ctrl_delete_preserve_both_memos_exact() -> TestResult {
    for ctrl in [false, true] {
        let bytes = source(ctrl)?;
        let forms = fixture::forms(&bytes, "review-delete")?;
        let review = ImportedDocumentReviewBodies::import(&forms)?;
        let selected = review
            .observations()
            .iter()
            .find(|o| o.kind == ReviewBodyKind::HiddenExplanation)
            .ok_or("hidden")?;
        let output =
            review.lower_delete(&bytes, &selected.marker_anchor, WriterLimits::default())?;
        let result = output.with_verified_bytes(<[u8]>::to_vec)?;
        let fragment = if ctrl {
            format!("<hp:ctrl>{HIDDEN}</hp:ctrl>")
        } else {
            HIDDEN.into()
        };
        verify_parts(&bytes, &result, &[&fragment])?;
        assert_eq!(output.receipt().deleted_subtrees, 1);
        let after_forms = fixture::forms(&result, "review-delete")?;
        let after = ImportedDocumentReviewBodies::import(&after_forms)?;
        assert_eq!(after.receipt().hidden_explanations, 0);
        assert_eq!(after.receipt().memo_fields, 2);
    }
    Ok(())
}
#[test]
fn memo_without_body_is_removed_without_fabricating_body_or_metadata() -> TestResult {
    let bytes = source(false)?;
    let forms = fixture::forms(&bytes, "review-delete")?;
    let review = ImportedDocumentReviewBodies::import(&forms)?;
    let selected = review
        .observations()
        .iter()
        .find(|o| o.kind == ReviewBodyKind::MemoField && o.body.is_none())
        .ok_or("bodyless")?;
    let output = review.lower_delete(&bytes, &selected.marker_anchor, WriterLimits::default())?;
    let result = output.with_verified_bytes(<[u8]>::to_vec)?;
    let begin = "<hp:ctrl><hp:fieldBegin id='4' type='MEMO'><hp:parameters cnt='0'/></hp:fieldBegin></hp:ctrl>";
    let end = "<hp:ctrl><hp:fieldEnd beginIDRef='4'/></hp:ctrl>";
    verify_parts(&bytes, &result, &[begin, end])?;
    Ok(())
}
#[test]
fn stale_wrong_end_body_foreign_and_deleted_selection_do_not_output() -> TestResult {
    let bytes = source(false)?;
    let forms = fixture::forms(&bytes, "review-delete")?;
    let review = ImportedDocumentReviewBodies::import(&forms)?;
    let selected = &review.observations()[0];
    assert_eq!(
        review
            .lower_delete(&[0], &selected.marker_anchor, WriterLimits::default())
            .err(),
        Some(ReviewDeleteError::Source)
    );
    for wrong in [
        selected.end_anchor.as_ref().ok_or("end")?,
        selected.body_anchor.as_ref().ok_or("body")?,
    ] {
        assert_eq!(
            review
                .lower_delete(&bytes, wrong, WriterLimits::default())
                .err(),
            Some(ReviewDeleteError::Selection)
        );
    }
    let foreign_forms = fixture::forms(&bytes, "foreign-review-delete")?;
    let foreign = ImportedDocumentReviewBodies::import(&foreign_forms)?;
    assert_eq!(
        review
            .lower_delete(
                &bytes,
                &foreign.observations()[0].marker_anchor,
                WriterLimits::default()
            )
            .err(),
        Some(ReviewDeleteError::Selection)
    );
    let output = review.lower_delete(&bytes, &selected.marker_anchor, WriterLimits::default())?;
    let result = output.with_verified_bytes(<[u8]>::to_vec)?;
    let after_forms = fixture::forms(&result, "review-delete")?;
    let after = ImportedDocumentReviewBodies::import(&after_forms)?;
    assert_eq!(
        after
            .lower_delete(&result, &selected.marker_anchor, WriterLimits::default())
            .err(),
        Some(ReviewDeleteError::Selection)
    );
    Ok(())
}
#[test]
fn tiny_writer_and_historical_captured_source_without_review_are_rejected() -> TestResult {
    let bytes = source(false)?;
    let forms = fixture::forms(&bytes, "review-delete")?;
    let review = ImportedDocumentReviewBodies::import(&forms)?;
    let tiny = WriterLimits::new(WriterLimitConfig {
        max_output_bytes: 1,
    })?;
    assert_eq!(
        review
            .lower_delete(&bytes, &review.observations()[0].marker_anchor, tiny)
            .err(),
        Some(ReviewDeleteError::Writer)
    );
    let captured = fixture::captured()?;
    let captured_forms = fixture::forms(&captured, "review-delete")?;
    let captured_review = ImportedDocumentReviewBodies::import(&captured_forms)?;
    assert!(captured_review.observations().is_empty());
    assert_eq!(
        captured_review
            .lower_delete(
                &captured,
                &review.observations()[0].marker_anchor,
                WriterLimits::default()
            )
            .err(),
        Some(ReviewDeleteError::Selection)
    );
    Ok(())
}
#[test]
fn nested_hidden_review_is_rejected_by_original_import_before_deletion() -> TestResult {
    let nested = format!("<hp:p id='5'><hp:run><hp:t>OUTER</hp:t>{HIDDEN}</hp:run></hp:p>");
    let begin = BEGIN.replacen(
        "<hp:p id='2'><hp:run><hp:t>PRIVATE-MEMO</hp:t></hp:run></hp:p>",
        &nested,
        1,
    );
    let bytes = fixture::package(&format!(
        "<hp:p id='1'><hp:run>{begin}<hp:t>VISIBLE</hp:t>{END}</hp:run></hp:p>"
    ))?;
    let error = fixture::forms(&bytes, "review-delete")
        .err()
        .ok_or("nested source accepted")?;
    assert!(matches!(
        error.downcast_ref::<hwpx_package::document_import::forms::FormImportError>(),
        Some(hwpx_package::document_import::forms::FormImportError::Body(
            hwpx_package::document_import::structure::StructureImportError::Paragraph {
                code: "text_flow_invalid_field"
            }
        ))
    ));
    Ok(())
}
