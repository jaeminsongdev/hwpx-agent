//! Original whole-package path over synthetic rich bodies; NOT native/Gate acceptance.
#[path = "support/review_cell_output_fixture.rs"]
mod fixture;
#[allow(dead_code)]
#[path = "support/document_import_field_fixture.rs"]
mod original;
use hwpx_package::{
    BoundedZipReader, PackageLimits, TextFlowLimits, TextFlowReader, TextFlowWriter, WriterLimits,
    document_import::structure::review::{
        ImportedDocumentReviewBodies, body_output::ReviewBodyOutputError,
    },
};
use std::{collections::BTreeMap, error::Error, io::Cursor};
type TestResult = Result<(), Box<dyn Error>>;
fn parts(bytes: &[u8]) -> Result<BTreeMap<String, Vec<u8>>, Box<dyn Error>> {
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let paths: Vec<_> = reader
        .entries()
        .iter()
        .map(|e| e.path.as_str().to_owned())
        .collect();
    paths
        .into_iter()
        .enumerate()
        .map(|(i, path)| Ok((path, reader.read_entry(i)?)))
        .collect()
}
#[test]
fn memo_and_hidden_cell_output_preserve_every_byte_outside_actual_cell_contents() -> TestResult {
    let bytes = fixture::package()?;
    let forms = original::forms(&bytes, "cell-document")?;
    let review = ImportedDocumentReviewBodies::import(&forms)?;
    let cells = fixture::cells(&forms)?;
    assert_eq!(cells.len(), 4);
    for (observation, cell) in [(0, 0), (1, 2)] {
        let mut second = fixture::target()?;
        second.paragraph.id = Some(902);
        let target = vec![fixture::target()?, second];
        let output = review.lower_table_cell_body(
            &bytes,
            &review.observations()[observation].marker_anchor,
            &cells[cell],
            &target,
            WriterLimits::default(),
        )?;
        assert!(
            output
                .receipt()
                .table_structure_and_other_cell_contents_exact
        );
        assert!(!output.receipt().new_table_inserted);
        assert!(!output.receipt().full_comment_product_acceptance);
        assert!(!output.receipt().output.native_author_time_state_verified);
        let actual = output.with_verified_bytes(<[u8]>::to_vec)?;
        let resolved = forms.source().resolve_anchor(&cells[cell])?;
        let xml = resolved.part().xml().ok_or("xml")?;
        let index = resolved.element_index().ok_or("index")?;
        let content = xml
            .elements()
            .iter()
            .skip(index + 1)
            .find(|e| e.parent() == Some(index) && e.name().local_name() == "subList")
            .ok_or("subList")?
            .content_span()
            .ok_or("span")?;
        let mut replacement = Vec::new();
        for value in &target {
            let lowered = TextFlowWriter::lower(value, TextFlowLimits::default())?;
            let parsed = hwpx_package::PreservingXmlDocument::parse(&lowered)?;
            let root = parsed.elements()[parsed.root_element()]
                .outer_span()
                .ok_or("root")?;
            replacement.extend_from_slice(&lowered[root.start()..root.end()]);
        }
        let mut expected = parts(&bytes)?;
        let old = expected.get_mut("Contents/section0.xml").ok_or("section")?;
        old.splice(content.start()..content.end(), replacement);
        assert_eq!(parts(&actual)?, expected);
        let after_forms = original::forms(&actual, "cell-document")?;
        let after = ImportedDocumentReviewBodies::import(&after_forms)?;
        assert_eq!(after.receipt().memo_fields, 1);
        assert_eq!(after.receipt().hidden_explanations, 1);
        assert_eq!(fixture::cells(&after_forms)?.len(), 4);
        assert_eq!(
            after.observations()[observation].native_attributes,
            review.observations()[observation].native_attributes
        );
        assert!(!format!("{output:?}").contains("NEW-PRIVATE"));
    }
    Ok(())
}
#[test]
fn other_review_cell_non_cell_main_and_foreign_document_selections_reject() -> TestResult {
    let bytes = fixture::package()?;
    let forms = original::forms(&bytes, "cell-document")?;
    let review = ImportedDocumentReviewBodies::import(&forms)?;
    let cells = fixture::cells(&forms)?;
    let other = original::forms(&bytes, "other-document")?;
    let foreign = fixture::cells(&other)?;
    let section = forms
        .source()
        .parts()
        .iter()
        .find(|p| p.path().as_str() == "Contents/section0.xml")
        .ok_or("section")?;
    let root = section
        .element_anchor(section.xml().ok_or("xml")?.root_element())
        .ok_or("root")?;
    for cell in [&cells[2], &foreign[0], root] {
        assert_eq!(
            review
                .lower_table_cell_body(
                    &bytes,
                    &review.observations()[0].marker_anchor,
                    cell,
                    &[fixture::target()?],
                    WriterLimits::default()
                )
                .err(),
            Some(ReviewBodyOutputError::Selection)
        );
    }
    let main = fixture::package_variant(|s| format!("{s}{}", fixture::table(302)))?;
    let main_forms = original::forms(&main, "cell-document")?;
    let main_review = ImportedDocumentReviewBodies::import(&main_forms)?;
    let main_cells = fixture::cells(&main_forms)?;
    assert_eq!(
        main_review
            .lower_table_cell_body(
                &main,
                &main_review.observations()[0].marker_anchor,
                &main_cells[4],
                &[fixture::target()?],
                WriterLimits::default()
            )
            .err(),
        Some(ReviewBodyOutputError::Selection)
    );
    Ok(())
}
#[test]
fn whole_source_drift_and_old_anchor_after_one_output_are_not_rebound() -> TestResult {
    let bytes = fixture::package()?;
    let forms = original::forms(&bytes, "cell-document")?;
    let review = ImportedDocumentReviewBodies::import(&forms)?;
    let cell = fixture::cells(&forms)?.remove(0);
    let marker = &review.observations()[0].marker_anchor;
    let changed = fixture::package_variant(|s| s.replace("VISIBLE-CACHE", "VISIBLE-DRIFT"))?;
    assert_eq!(
        review
            .lower_table_cell_body(
                &changed,
                marker,
                &cell,
                &[fixture::target()?],
                WriterLimits::default()
            )
            .err(),
        Some(ReviewBodyOutputError::Source)
    );
    let output = review
        .lower_table_cell_body(
            &bytes,
            marker,
            &cell,
            &[fixture::target()?],
            WriterLimits::default(),
        )?
        .with_verified_bytes(<[u8]>::to_vec)?;
    let fresh_forms = original::forms(&output, "cell-document")?;
    let fresh = ImportedDocumentReviewBodies::import(&fresh_forms)?;
    assert_eq!(
        fresh
            .lower_table_cell_body(
                &output,
                &fresh.observations()[0].marker_anchor,
                &cell,
                &[fixture::target()?],
                WriterLimits::default()
            )
            .err(),
        Some(ReviewBodyOutputError::Selection)
    );
    Ok(())
}
#[test]
fn unsafe_empty_opaque_style_protection_and_finite_budgets_never_return_partial_artifacts()
-> TestResult {
    let bytes = fixture::package()?;
    let forms = original::forms(&bytes, "cell-document")?;
    let review = ImportedDocumentReviewBodies::import(&forms)?;
    let cell = fixture::cells(&forms)?.remove(0);
    let marker = &review.observations()[0].marker_anchor;
    let opaque = TextFlowReader::read(b"<hp:p xmlns:hp='http://www.hancom.co.kr/hwpml/2011/paragraph' xmlns:u='urn:future' id='9'><hp:run><hp:t>TEXT</hp:t></hp:run><u:opaque/></hp:p>", TextFlowLimits::default())?;
    for values in [vec![], vec![opaque], vec![fixture::target()?; 4097]] {
        assert_eq!(
            review
                .lower_table_cell_body(&bytes, marker, &cell, &values, WriterLimits::default())
                .err(),
            Some(ReviewBodyOutputError::Values)
        );
    }
    let mut bad_style = fixture::target()?;
    bad_style.paragraph.style_id_ref = Some(999_999);
    assert!(
        review
            .lower_table_cell_body(&bytes, marker, &cell, &[bad_style], WriterLimits::default())
            .is_err()
    );
    let tiny = WriterLimits::new(hwpx_package::WriterLimitConfig {
        max_output_bytes: 1,
    })?;
    assert_eq!(
        review
            .lower_table_cell_body(&bytes, marker, &cell, &[fixture::target()?], tiny)
            .err(),
        Some(ReviewBodyOutputError::Writer)
    );
    for (from, to) in [("protect='0'", "protect='1'"), ("lock='0'", "lock='1'")] {
        let protected = fixture::package_variant(|s| s.replacen(from, to, 1))?;
        let forms = original::forms(&protected, "cell-document")?;
        let review = ImportedDocumentReviewBodies::import(&forms)?;
        assert_eq!(
            review
                .lower_table_cell_body(
                    &protected,
                    &review.observations()[0].marker_anchor,
                    &fixture::cells(&forms)?[0],
                    &[fixture::target()?],
                    WriterLimits::default()
                )
                .err(),
            Some(ReviewBodyOutputError::Selection)
        );
    }
    Ok(())
}
#[test]
fn identical_cell_values_and_immutable_no_review_capture_never_fabricate_edits() -> TestResult {
    let bytes = fixture::package()?;
    let forms = original::forms(&bytes, "cell-document")?;
    let review = ImportedDocumentReviewBodies::import(&forms)?;
    let identical = TextFlowReader::read(b"<hp:p xmlns:hp='http://www.hancom.co.kr/hwpml/2011/paragraph' id='0' styleIDRef='0' paraPrIDRef='0'><hp:run charPrIDRef='0'><hp:t>CELL-OLD</hp:t></hp:run></hp:p>", TextFlowLimits::default())?;
    assert_eq!(
        review
            .lower_table_cell_body(
                &bytes,
                &review.observations()[0].marker_anchor,
                &fixture::cells(&forms)?[0],
                &[identical],
                WriterLimits::default()
            )
            .err(),
        Some(ReviewBodyOutputError::NoChange)
    );
    let captured = original::captured()?;
    let captured_forms = original::forms(&captured, "cell-document")?;
    let captured_review = ImportedDocumentReviewBodies::import(&captured_forms)?;
    assert!(captured_review.observations().is_empty());
    assert_eq!(
        captured_review
            .lower_table_cell_body(
                &captured,
                &review.observations()[0].marker_anchor,
                &fixture::cells(&forms)?[0],
                &[fixture::target()?],
                WriterLimits::default()
            )
            .err(),
        Some(ReviewBodyOutputError::Selection)
    );
    Ok(())
}
