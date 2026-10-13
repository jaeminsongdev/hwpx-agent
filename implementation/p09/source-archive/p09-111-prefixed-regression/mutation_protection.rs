//! Actual deletion/replacement protection, original fixtures, NOT native execution authority.
use super::*;
use domain_ir::SourceAnchorHandle;
use hwpx_package::{
    TextFlow,
    document_import::{
        forms::ImportedDocumentForms,
        structure::review::{ReviewBodyKind, delete_output::ReviewDeleteError},
    },
};

const HP: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const FLAGS: [&str; 3] = ["cell", "lock", "size"];

fn protect(mut table: String, flag: &str) -> String {
    let (from, to) = match flag {
        "cell" => ("hasMargin='0' protect='0'", "hasMargin='0' protect='1'"),
        "lock" => ("lock='0'", "lock='1'"),
        "size" => (
            "heightRelTo='ABSOLUTE' protect='0'",
            "heightRelTo='ABSOLUTE' protect='1'",
        ),
        _ => return table,
    };
    assert!(table.contains(from));
    table = table.replacen(from, to, 1);
    table
}

fn main(markers: &str, flag: &str) -> String {
    let p = format!(
        "<hp:p id='811' styleIDRef='0' paraPrIDRef='0'><hp:run charPrIDRef='0'>{markers}</hp:run></hp:p>"
    );
    protect(
        fixture::table(810).replacen(&fixture::paragraph(0, "CELL-OLD"), &p, 1),
        flag,
    )
}

fn anchor(
    forms: &ImportedDocumentForms,
    bytes: &[u8],
    local: &str,
    id: &str,
) -> Result<SourceAnchorHandle, Box<dyn Error>> {
    forms.source().verify_source(bytes)?;
    let expanded = parts(bytes)?;
    let raw = expanded.get("Contents/section0.xml").ok_or("section")?;
    let part = forms
        .source()
        .parts()
        .iter()
        .find(|p| p.path().as_str() == "Contents/section0.xml")
        .ok_or("part")?;
    let xml = part.xml().ok_or("xml")?;
    let (index, _) = xml
        .elements()
        .iter()
        .enumerate()
        .find(|(_, e)| {
            e.name().namespace() == Some(HP)
                && e.name().local_name() == local
                && e.attributes().iter().any(|a| {
                    a.name().namespace().is_none()
                        && a.name().local_name() == "id"
                        && &raw[a.value_span().start()..a.value_span().end()] == id.as_bytes()
                })
        })
        .ok_or("anchor")?;
    Ok(part.element_anchor(index).ok_or("source identity")?.clone())
}

fn assert_delete_rejected(bytes: &[u8], forms: &ImportedDocumentForms) -> TestResult {
    let review = ImportedDocumentReviewBodies::import(forms)?;
    assert_eq!(review.observations().len(), 2);
    for selected in review.observations() {
        assert_eq!(
            review
                .lower_delete(bytes, &selected.marker_anchor, WriterLimits::default())
                .err(),
            Some(ReviewDeleteError::Selection)
        );
    }
    review.verify_source(bytes)?;
    Ok(())
}

#[test]
fn deletion_rejects_all_three_main_ancestor_flags_for_both_review_kinds() -> TestResult {
    for flag in FLAGS {
        let bytes = assembly::package(&main(&assembly::markers("OLD"), flag))?;
        let forms = original::forms(&bytes, "mutation-review")?;
        assert_delete_rejected(&bytes, &forms)?;
    }
    Ok(())
}

#[test]
fn deletion_rejects_protected_tables_or_cells_consumed_inside_either_review() -> TestResult {
    for flag in FLAGS {
        let bytes = fixture::package_variant(|s| {
            s.replacen(&fixture::table(300), &protect(fixture::table(300), flag), 1)
                .replacen(&fixture::table(301), &protect(fixture::table(301), flag), 1)
        })?;
        let forms = original::forms(&bytes, "mutation-review")?;
        assert_delete_rejected(&bytes, &forms)?;
    }
    Ok(())
}

#[test]
fn replacement_of_a_paragraph_does_not_erase_a_protected_descendant_table() -> TestResult {
    for flag in FLAGS {
        let bytes = fixture::package_variant(|s| {
            s.replacen(&fixture::table(300), &protect(fixture::table(300), flag), 1)
                .replacen(&fixture::table(301), &protect(fixture::table(301), flag), 1)
        })?;
        let forms = original::forms(&bytes, "mutation-review")?;
        let review = ImportedDocumentReviewBodies::import(&forms)?;
        for (observation, id) in [(0, "101"), (1, "102")] {
            assert_eq!(
                review
                    .lower_paragraph(
                        &bytes,
                        &review.observations()[observation].marker_anchor,
                        &anchor(&forms, &bytes, "p", id)?,
                        &fixture::target()?,
                        WriterLimits::default()
                    )
                    .err(),
                Some(ReviewBodyOutputError::Selection)
            );
        }
    }
    Ok(())
}

#[test]
fn whole_body_replacement_checks_consumed_protection_before_values_or_writer() -> TestResult {
    for flag in FLAGS {
        let bytes = fixture::package_variant(|s| {
            s.replacen(&fixture::table(300), &protect(fixture::table(300), flag), 1)
        })?;
        let forms = original::forms(&bytes, "mutation-review")?;
        let review = ImportedDocumentReviewBodies::import(&forms)?;
        assert_eq!(
            review
                .lower_body(
                    &bytes,
                    &review.observations()[0].marker_anchor,
                    &[],
                    WriterLimits::default()
                )
                .err(),
            Some(ReviewBodyOutputError::Selection)
        );
        let tiny = WriterLimits::new(hwpx_package::WriterLimitConfig {
            max_output_bytes: 1,
        })?;
        assert_eq!(
            review
                .lower_body(
                    &bytes,
                    &review.observations()[0].marker_anchor,
                    &[fixture::target()?],
                    tiny
                )
                .err(),
            Some(ReviewBodyOutputError::Selection)
        );
    }
    Ok(())
}

#[test]
fn replacing_outer_cell_contents_cannot_remove_a_protected_nested_table() -> TestResult {
    for flag in FLAGS {
        let bytes = fixture::package_variant(|s| {
            s.replacen(
                "<hp:t>CELL-OLD</hp:t>",
                &format!("<hp:t>OUTER</hp:t>{}", protect(fixture::table(302), flag)),
                1,
            )
        })?;
        let forms = original::forms(&bytes, "mutation-review")?;
        let review = ImportedDocumentReviewBodies::import(&forms)?;
        assert_eq!(fixture::cells(&forms)?.len(), 6);
        assert_eq!(
            review
                .lower_table_cell_body(
                    &bytes,
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
fn protected_unselected_review_does_not_block_an_unrelated_exact_paragraph_edit() -> TestResult {
    let bytes = fixture::package_variant(|s| {
        s.replacen(
            &fixture::table(301),
            &protect(fixture::table(301), "lock"),
            1,
        )
        .replacen(
            "</hp:p></hp:subList></hp:fieldBegin>",
            &format!(
                "</hp:p>{}</hp:subList></hp:fieldBegin>",
                fixture::paragraph(700, "PLAIN")
            ),
            1,
        )
    })?;
    let forms = original::forms(&bytes, "mutation-review")?;
    let review = ImportedDocumentReviewBodies::import(&forms)?;
    let selected = anchor(&forms, &bytes, "p", "700")?;
    let target = fixture::target()?;
    let actual = review
        .lower_paragraph(
            &bytes,
            &review.observations()[0].marker_anchor,
            &selected,
            &target,
            WriterLimits::default(),
        )?
        .with_verified_bytes(<[u8]>::to_vec)?;
    assert_exact_paragraph(&bytes, &forms, &selected, &target, &actual)?;
    Ok(())
}

fn assert_exact_paragraph(
    bytes: &[u8],
    forms: &ImportedDocumentForms,
    selected: &SourceAnchorHandle,
    target: &TextFlow,
    actual: &[u8],
) -> TestResult {
    let resolved = forms.source().resolve_anchor(selected)?;
    let span = resolved
        .element()
        .and_then(hwpx_package::XmlElementToken::outer_span)
        .ok_or("span")?;
    let lowered = TextFlowWriter::lower(target, TextFlowLimits::default())?;
    let xml = hwpx_package::PreservingXmlDocument::parse(&lowered)?;
    let root = xml.elements()[xml.root_element()]
        .outer_span()
        .ok_or("root")?;
    let mut expected = parts(bytes)?;
    expected
        .get_mut("Contents/section0.xml")
        .ok_or("section")?
        .splice(
            span.start()..span.end(),
            lowered[root.start()..root.end()].iter().copied(),
        );
    assert_eq!(parts(actual)?, expected);
    Ok(())
}

#[test]
fn deleting_unprotected_review_preserves_locked_peer_main_geometry_and_all_parts() -> TestResult {
    let bytes = fixture::package_variant(|s| {
        s.replacen(
            &fixture::table(301),
            &protect(fixture::table(301), "lock"),
            1,
        )
    })?;
    let forms = original::forms(&bytes, "mutation-review")?;
    let review = ImportedDocumentReviewBodies::import(&forms)?;
    let selected = &review.observations()[0];
    let output = review.lower_delete(&bytes, &selected.marker_anchor, WriterLimits::default())?;
    assert!(!output.receipt().protection_execution_publication_authority);
    assert!(!output.receipt().native_author_time_state_verified);
    let actual = output.with_verified_bytes(<[u8]>::to_vec)?;
    let mut expected = parts(&bytes)?;
    let mut spans = Vec::new();
    for anchor in [
        &selected.marker_anchor,
        selected.end_anchor.as_ref().ok_or("end")?,
    ] {
        let resolved = forms.source().resolve_anchor(anchor)?;
        let xml = resolved.part().xml().ok_or("xml")?;
        let parent = resolved
            .element()
            .and_then(hwpx_package::XmlElementToken::parent)
            .ok_or("parent")?;
        spans.push(xml.elements()[parent].outer_span().ok_or("ctrl")?);
    }
    spans.sort_by_key(|s| std::cmp::Reverse(s.start()));
    let section = expected.get_mut("Contents/section0.xml").ok_or("section")?;
    for span in spans {
        section.drain(span.start()..span.end());
    }
    assert_eq!(parts(&actual)?, expected);
    let after = original::forms(&actual, "mutation-review")?;
    let after_review = ImportedDocumentReviewBodies::import(&after)?;
    assert_eq!(after_review.observations().len(), 1);
    assert_eq!(
        after_review.observations()[0].kind,
        ReviewBodyKind::HiddenExplanation
    );
    after_review.verify_source(&actual)?;
    Ok(())
}

#[test]
fn source_drift_and_foreign_selection_still_reject_before_mutation() -> TestResult {
    let bytes = assembly::package(&main(&assembly::markers("OLD"), "cell"))?;
    let forms = original::forms(&bytes, "mutation-review")?;
    let review = ImportedDocumentReviewBodies::import(&forms)?;
    let foreign_forms = original::forms(&bytes, "foreign-review")?;
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
    assert_eq!(
        review
            .lower_delete(
                &[0],
                &review.observations()[0].marker_anchor,
                WriterLimits::default()
            )
            .err(),
        Some(ReviewDeleteError::Source)
    );
    let tiny = WriterLimits::new(hwpx_package::WriterLimitConfig {
        max_output_bytes: 1,
    })?;
    assert_eq!(
        review
            .lower_delete(&bytes, &review.observations()[0].marker_anchor, tiny)
            .err(),
        Some(ReviewDeleteError::Selection)
    );
    Ok(())
}
