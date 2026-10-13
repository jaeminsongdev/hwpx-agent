//! Actual package pipeline over synthetic rich review bodies; no native acceptance.
#[path = "support/document_import_review_assembly_fixture.rs"]
mod assembly;
#[path = "support/review_paragraph_output_fixture.rs"]
mod fixture;
#[allow(dead_code)]
#[path = "support/document_import_field_fixture.rs"]
mod original;
#[path = "support/review_cell_output_fixture.rs"]
mod rich;
use hwpx_package::{
    document_import::structure::review::{
        body_output::ReviewBodyOutputError, ImportedDocumentReviewBodies,
    },
    BoundedZipReader, PackageLimits, PreservingXmlDocument, TextFlowLimits, TextFlowReader,
    TextFlowWriter, WriterLimits,
};
use std::{collections::BTreeMap, error::Error, io::Cursor};
type TestResult = Result<(), Box<dyn Error>>;
fn parts(bytes: &[u8]) -> Result<BTreeMap<String, Vec<u8>>, Box<dyn Error>> {
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let names: Vec<_> = reader
        .entries()
        .iter()
        .map(|e| e.path.as_str().to_owned())
        .collect();
    names
        .into_iter()
        .enumerate()
        .map(|(i, p)| Ok((p, reader.read_entry(i)?)))
        .collect()
}
#[test]
fn memo_and_hidden_plain_paragraph_edits_preserve_all_rich_siblings_and_other_parts() -> TestResult
{
    let bytes = fixture::package()?;
    let forms = original::forms(&bytes, "paragraph-document")?;
    let review = ImportedDocumentReviewBodies::import(&forms)?;
    assert_eq!(rich::cells(&forms)?.len(), 4);
    for (observation, id) in [(0, 700), (1, 701)] {
        let anchor = fixture::anchor(&forms, &bytes, id)?;
        let target = fixture::target()?;
        let result = review.lower_paragraph(
            &bytes,
            &review.observations()[observation].marker_anchor,
            &anchor,
            &target,
            WriterLimits::default(),
        )?;
        let actual = result.with_verified_bytes(<[u8]>::to_vec)?;
        let selected = forms.source().resolve_anchor(&anchor)?;
        let old = selected
            .element()
            .ok_or("paragraph")?
            .outer_span()
            .ok_or("span")?;
        let lowered = TextFlowWriter::lower(&target, TextFlowLimits::default())?;
        let parsed = PreservingXmlDocument::parse(&lowered)?;
        let span = parsed.elements()[parsed.root_element()]
            .outer_span()
            .ok_or("root")?;
        let mut expected = parts(&bytes)?;
        expected
            .get_mut("Contents/section0.xml")
            .ok_or("section")?
            .splice(
                old.start()..old.end(),
                lowered[span.start()..span.end()].to_vec(),
            );
        assert_eq!(parts(&actual)?, expected);
        let after = original::forms(&actual, "paragraph-document")?;
        assert_eq!(rich::cells(&after)?.len(), 4);
        ImportedDocumentReviewBodies::import(&after)?.verify_source(&actual)?;
        assert!(result.receipt().rich_siblings_preserved_exact);
        assert!(result.receipt().outside_selected_paragraph_exact);
        assert!(!result.receipt().full_comment_product_acceptance);
        assert!(!result.receipt().output.native_author_time_state_verified);
        assert!(!format!("{result:?}").contains("PRIVATE"));
    }
    Ok(())
}
#[test]
fn foreign_other_review_main_nonparagraph_and_whole_source_drift_reject() -> TestResult {
    let bytes = fixture::package()?;
    let forms = original::forms(&bytes, "paragraph-document")?;
    let other = original::forms(&bytes, "foreign-document")?;
    let review = ImportedDocumentReviewBodies::import(&forms)?;
    let marker = &review.observations()[0].marker_anchor;
    let target = fixture::target()?;
    for anchor in [
        fixture::anchor(&other, &bytes, 700)?,
        fixture::anchor(&forms, &bytes, 701)?,
        fixture::anchor(&forms, &bytes, 0)?,
        rich::cells(&forms)?[0].clone(),
        marker.clone(),
    ] {
        assert_eq!(
            review
                .lower_paragraph(&bytes, marker, &anchor, &target, WriterLimits::default())
                .err(),
            Some(ReviewBodyOutputError::Selection)
        );
    }
    let drift = rich::package_variant(|s| s.replace("VISIBLE-CACHE", "DRIFT"))?;
    assert_eq!(
        review
            .lower_paragraph(
                &drift,
                marker,
                &fixture::anchor(&forms, &bytes, 700)?,
                &target,
                WriterLimits::default()
            )
            .err(),
        Some(ReviewBodyOutputError::Source)
    );
    Ok(())
}
#[test]
fn no_op_opaque_bad_style_id_and_finite_writer_values_never_return_artifacts() -> TestResult {
    let bytes = fixture::package()?;
    let forms = original::forms(&bytes, "paragraph-document")?;
    let review = ImportedDocumentReviewBodies::import(&forms)?;
    let anchor = fixture::anchor(&forms, &bytes, 700)?;
    let same = TextFlowReader::read(b"<hp:p xmlns:hp='http://www.hancom.co.kr/hwpml/2011/paragraph' id='700' styleIDRef='0' paraPrIDRef='0'><hp:run charPrIDRef='0'><hp:t>PLAIN-MEMO-PRIVATE</hp:t></hp:run></hp:p>", TextFlowLimits::default())?;
    let marker = &review.observations()[0].marker_anchor;
    assert_eq!(
        review
            .lower_paragraph(&bytes, marker, &anchor, &same, WriterLimits::default())
            .err(),
        Some(ReviewBodyOutputError::NoChange)
    );
    let opaque = TextFlowReader::read(b"<hp:p xmlns:hp='http://www.hancom.co.kr/hwpml/2011/paragraph' xmlns:u='urn:future' id='9'><hp:run><hp:t>TEXT</hp:t></hp:run><u:future/></hp:p>",TextFlowLimits::default())?;
    assert_eq!(
        review
            .lower_paragraph(&bytes, marker, &anchor, &opaque, WriterLimits::default())
            .err(),
        Some(ReviewBodyOutputError::Values)
    );
    let mut bad = fixture::target()?;
    bad.paragraph.style_id_ref = Some(999_999);
    assert!(review
        .lower_paragraph(&bytes, marker, &anchor, &bad, WriterLimits::default())
        .is_err());
    let tiny = WriterLimits::new(hwpx_package::WriterLimitConfig {
        max_output_bytes: 1,
    })?;
    assert_eq!(
        review
            .lower_paragraph(&bytes, marker, &anchor, &fixture::target()?, tiny)
            .err(),
        Some(ReviewBodyOutputError::Writer)
    );
    Ok(())
}
#[test]
fn nested_cell_paragraph_edits_reuse_original_ancestor_protection_guards() -> TestResult {
    let nested = |s: String| {
        s.replacen(
            "<hp:t>CELL-OLD</hp:t>",
            &format!(
                "<hp:t>OUTER</hp:t>{}",
                rich::table(302).replacen("<hp:p id='0'", "<hp:p id='702'", 1)
            ),
            1,
        )
    };
    let bytes = rich::package_variant(nested)?;
    let forms = original::forms(&bytes, "paragraph-document")?;
    let review = ImportedDocumentReviewBodies::import(&forms)?;
    let output = review
        .lower_paragraph(
            &bytes,
            &review.observations()[0].marker_anchor,
            &fixture::anchor(&forms, &bytes, 702)?,
            &fixture::target()?,
            WriterLimits::default(),
        )?
        .with_verified_bytes(<[u8]>::to_vec)?;
    assert_eq!(
        rich::cells(&original::forms(&output, "paragraph-document")?)?.len(),
        6
    );
    for (from, to) in [
        ("lock='0'", "lock='1'"),
        (
            "<hp:tc name='' header='0' hasMargin='0' protect='0'",
            "<hp:tc name='' header='0' hasMargin='0' protect='1'",
        ),
        (
            "heightRelTo='ABSOLUTE' protect='0'",
            "heightRelTo='ABSOLUTE' protect='1'",
        ),
    ] {
        let bytes = rich::package_variant(|s| nested(s).replacen(from, to, 1))?;
        let forms = original::forms(&bytes, "paragraph-document")?;
        let review = ImportedDocumentReviewBodies::import(&forms)?;
        assert_eq!(
            review
                .lower_paragraph(
                    &bytes,
                    &review.observations()[0].marker_anchor,
                    &fixture::anchor(&forms, &bytes, 702)?,
                    &fixture::target()?,
                    WriterLimits::default()
                )
                .err(),
            Some(ReviewBodyOutputError::Selection)
        );
    }
    Ok(())
}
#[test]
fn nested_review_paragraph_is_owned_by_nearest_body_not_outer_marker() -> TestResult {
    let bytes = rich::package_variant(|s| {
        s.replacen("<hp:t>CELL-OLD</hp:t>",&format!("<hp:t>CELL-OLD</hp:t><hp:hiddenComment><hp:subList>{}</hp:subList></hp:hiddenComment>",rich::paragraph(702,"NESTED-PRIVATE")),1)
    })?;
    let forms = original::forms(&bytes, "paragraph-document")?;
    let review = ImportedDocumentReviewBodies::import(&forms)?;
    assert_eq!(review.observations().len(), 3);
    let anchor = fixture::anchor(&forms, &bytes, 702)?;
    assert_eq!(
        review
            .lower_paragraph(
                &bytes,
                &review.observations()[0].marker_anchor,
                &anchor,
                &fixture::target()?,
                WriterLimits::default()
            )
            .err(),
        Some(ReviewBodyOutputError::Selection)
    );
    review.lower_paragraph(
        &bytes,
        &review.observations()[1].marker_anchor,
        &anchor,
        &fixture::target()?,
        WriterLimits::default(),
    )?;
    Ok(())
}
#[test]
fn fresh_output_requires_new_anchors_and_immutable_capture_does_not_fabricate_reviews() -> TestResult
{
    let bytes = fixture::package()?;
    let forms = original::forms(&bytes, "paragraph-document")?;
    let review = ImportedDocumentReviewBodies::import(&forms)?;
    let anchor = fixture::anchor(&forms, &bytes, 700)?;
    let result = review
        .lower_paragraph(
            &bytes,
            &review.observations()[0].marker_anchor,
            &anchor,
            &fixture::target()?,
            WriterLimits::default(),
        )?
        .with_verified_bytes(<[u8]>::to_vec)?;
    let after_forms = original::forms(&result, "paragraph-document")?;
    let after = ImportedDocumentReviewBodies::import(&after_forms)?;
    assert_eq!(
        after
            .lower_paragraph(
                &result,
                &after.observations()[0].marker_anchor,
                &anchor,
                &fixture::target()?,
                WriterLimits::default()
            )
            .err(),
        Some(ReviewBodyOutputError::Selection)
    );
    let mut changed = fixture::target()?;
    changed.paragraph.id = 902;
    after.lower_paragraph(
        &result,
        &after.observations()[0].marker_anchor,
        &fixture::anchor(&after_forms, &result, 901)?,
        &changed,
        WriterLimits::default(),
    )?;
    let captured = original::captured()?;
    let actual_forms = original::forms(&captured, "paragraph-document")?;
    let actual = ImportedDocumentReviewBodies::import(&actual_forms)?;
    assert!(actual.observations().is_empty());
    assert_eq!(
        actual
            .lower_paragraph(
                &captured,
                &review.observations()[0].marker_anchor,
                &anchor,
                &fixture::target()?,
                WriterLimits::default()
            )
            .err(),
        Some(ReviewBodyOutputError::Selection)
    );
    Ok(())
}
