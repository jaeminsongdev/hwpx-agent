//! Actual source ancestry regressions over in-memory derivatives, NOT native acceptance.
use super::*;
use domain_ir::SourceAnchorHandle;
use hwpx_package::{
    PreservingXmlDocument, TableCreateHwpxLimits, TextFlow,
    document_import::{
        forms::{FormImportError, ImportedDocumentForms},
        structure::{
            StructureImportError,
            review::table_create_context::{ReviewTableContextError, ReviewTableTemplate},
        },
    },
};

const HP: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const FLAGS: [&str; 3] = ["cell", "lock", "size"];

fn forms_or_original_flag_rejection(
    bytes: &[u8],
    value: &str,
) -> Result<Option<ImportedDocumentForms>, Box<dyn Error>> {
    match original::forms(bytes, "ancestor-review") {
        Ok(forms) => Ok(Some(forms)),
        Err(error) => {
            let expected = if value == "MISSING" {
                "table_layout_hwpx_unsupported_shape"
            } else {
                "table_layout_hwpx_invalid_boolean"
            };
            if value != "0"
                && matches!(error.downcast_ref::<FormImportError>(),
                Some(FormImportError::Body(StructureImportError::Table { code })) if *code == expected)
            {
                // A stronger ORIGINAL importer rejection is not a successful output
                // or evidence that this non-native flag spelling is accepted.
                Ok(None)
            } else {
                Err(error)
            }
        }
    }
}

fn wrapped(markers: &str, flag: &str, value: &str, nested: bool) -> String {
    let paragraph = format!(
        "<hp:p id='810' styleIDRef='0' paraPrIDRef='0'><hp:run charPrIDRef='0'>{markers}</hp:run></hp:p>"
    );
    let mut outer = fixture::table(800).replacen(&fixture::paragraph(0, "CELL-OLD"), &paragraph, 1);
    if nested {
        outer = fixture::table(801).replacen(
            "<hp:t>CELL-OLD</hp:t>",
            &format!("<hp:t>OUTER-MAIN</hp:t>{outer}"),
            1,
        );
    }
    let (from, prefix) = match flag {
        "cell" => ("hasMargin='0' protect='0'", "hasMargin='0'"),
        "lock" => ("lock='0'", ""),
        "size" => (
            "heightRelTo='ABSOLUTE' protect='0'",
            "heightRelTo='ABSOLUTE'",
        ),
        _ => return outer,
    };
    let name = if flag == "lock" { "lock" } else { "protect" };
    let changed = if value == "MISSING" {
        prefix.to_owned()
    } else {
        format!("{prefix} {name}='{value}'")
    };
    outer.replacen(from, changed.trim(), 1)
}

fn package(flag: &str, value: &str, rich: bool, nested: bool) -> Result<Vec<u8>, Box<dyn Error>> {
    if rich {
        fixture::package_variant(|s| wrapped(&s, flag, value, nested))
    } else {
        assembly::package(&wrapped(&assembly::markers("OLD"), flag, value, nested))
    }
}

fn anchor(
    forms: &ImportedDocumentForms,
    bytes: &[u8],
    local: &str,
    id: &str,
) -> Result<SourceAnchorHandle, Box<dyn Error>> {
    forms.source().verify_source(bytes)?;
    let source_parts = parts(bytes)?;
    let raw = source_parts
        .get("Contents/section0.xml")
        .ok_or("source section")?;
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
        .ok_or("actual fixture anchor")?;
    Ok(part.element_anchor(index).ok_or("anchor")?.clone())
}

fn selected_cell(
    forms: &ImportedDocumentForms,
    observation: usize,
) -> Result<SourceAnchorHandle, Box<dyn Error>> {
    // Outer MAIN cells are deliberately excluded using their ACTUAL ancestor body.
    let review = ImportedDocumentReviewBodies::import(forms)?;
    let body = forms.source().resolve_anchor(
        review.observations()[observation]
            .body_anchor
            .as_ref()
            .ok_or("body")?,
    )?;
    let xml = body.part().xml().ok_or("xml")?;
    let body_index = body.element_index().ok_or("body index")?;
    for cell in fixture::cells(forms)? {
        let resolved = forms.source().resolve_anchor(&cell)?;
        let mut parent = xml.elements()[resolved.element_index().ok_or("cell index")?].parent();
        while let Some(index) = parent {
            if index == body_index {
                return Ok(cell);
            }
            parent = xml.elements()[index].parent();
        }
    }
    Err("actual review cell".into())
}

fn assert_exact_patch(
    bytes: &[u8],
    forms: &ImportedDocumentForms,
    selected: &SourceAnchorHandle,
    paragraph: bool,
    cell: bool,
    target: &TextFlow,
    actual: &[u8],
) -> TestResult {
    let resolved = forms.source().resolve_anchor(selected)?;
    let xml = resolved.part().xml().ok_or("xml")?;
    let mut index = resolved.element_index().ok_or("index")?;
    if cell {
        index = xml
            .elements()
            .iter()
            .enumerate()
            .find(|(_, e)| {
                e.parent() == Some(index)
                    && e.name().namespace() == Some(HP)
                    && e.name().local_name() == "subList"
            })
            .map(|(i, _)| i)
            .ok_or("cell subList")?;
    }
    let span = if paragraph {
        xml.elements()[index].outer_span()
    } else {
        xml.elements()[index].content_span()
    }
    .ok_or("span")?;
    let lowered = TextFlowWriter::lower(target, TextFlowLimits::default())?;
    let parsed = PreservingXmlDocument::parse(&lowered)?;
    let fragment = parsed.elements()[parsed.root_element()]
        .outer_span()
        .ok_or("fragment")?;
    let mut expected = parts(bytes)?;
    expected
        .get_mut("Contents/section0.xml")
        .ok_or("section")?
        .splice(
            span.start()..span.end(),
            lowered[fragment.start()..fragment.end()].iter().copied(),
        );
    assert_eq!(parts(actual)?, expected);
    let after = original::forms(actual, "ancestor-review")?;
    let after_review = ImportedDocumentReviewBodies::import(&after)?;
    assert_eq!(after_review.receipt().memo_fields, 1);
    assert_eq!(after_review.receipt().hidden_explanations, 1);
    after_review.verify_source(actual)?;
    Ok(())
}

#[test]
fn whole_memo_and_hidden_bodies_reject_all_three_main_ancestor_flags() -> TestResult {
    for flag in FLAGS {
        let bytes = package(flag, "1", false, false)?;
        let forms = original::forms(&bytes, "ancestor-review")?;
        let review = ImportedDocumentReviewBodies::import(&forms)?;
        assert_eq!(review.observations().len(), 2);
        for observation in review.observations() {
            assert_eq!(
                review
                    .lower_body(
                        &bytes,
                        &observation.marker_anchor,
                        &[fixture::target()?],
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
fn review_cells_reject_all_three_main_ancestor_flags() -> TestResult {
    for flag in FLAGS {
        let bytes = package(flag, "1", true, false)?;
        let forms = original::forms(&bytes, "ancestor-review")?;
        let review = ImportedDocumentReviewBodies::import(&forms)?;
        assert_eq!(fixture::cells(&forms)?.len(), 6);
        for observation in 0..2 {
            assert_eq!(
                review
                    .lower_table_cell_body(
                        &bytes,
                        &review.observations()[observation].marker_anchor,
                        &selected_cell(&forms, observation)?,
                        &[fixture::target()?],
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
fn individual_review_paragraphs_reject_protected_main_ancestors() -> TestResult {
    for flag in FLAGS {
        let bytes = package(flag, "1", false, false)?;
        let forms = original::forms(&bytes, "ancestor-review")?;
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
fn protection_outside_multiple_main_tables_is_not_hidden_by_review_boundary() -> TestResult {
    for flag in FLAGS {
        let bytes = package(flag, "1", true, true)?;
        let forms = original::forms(&bytes, "ancestor-review")?;
        let review = ImportedDocumentReviewBodies::import(&forms)?;
        assert_eq!(fixture::cells(&forms)?.len(), 8);
        for observation in 0..2 {
            assert_eq!(
                review
                    .lower_table_cell_body(
                        &bytes,
                        &review.observations()[observation].marker_anchor,
                        &selected_cell(&forms, observation)?,
                        &[fixture::target()?],
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
fn unknown_observed_flag_values_are_not_reinterpreted_as_unprotected() -> TestResult {
    for flag in FLAGS {
        for value in ["", "TRUE", "False", "-1", "unknown"] {
            let bytes = package(flag, value, false, false)?;
            let Some(forms) = forms_or_original_flag_rejection(&bytes, value)? else {
                continue;
            };
            let review = ImportedDocumentReviewBodies::import(&forms)?;
            assert_eq!(
                review
                    .lower_body(
                        &bytes,
                        &review.observations()[0].marker_anchor,
                        &[fixture::target()?],
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
fn zero_flags_preserve_exact_patches_and_other_spellings_never_bypass_original_admission()
-> TestResult {
    for flag in FLAGS {
        for value in ["0", "false", "MISSING"] {
            for rich in [false, true] {
                let bytes = package(flag, value, rich, true)?;
                let Some(forms) = forms_or_original_flag_rejection(&bytes, value)? else {
                    continue;
                };
                let review = ImportedDocumentReviewBodies::import(&forms)?;
                let target = fixture::target()?;
                for observation in 0..2 {
                    let marker = &review.observations()[observation].marker_anchor;
                    if rich {
                        let cell = selected_cell(&forms, observation)?;
                        let output = review.lower_table_cell_body(
                            &bytes,
                            marker,
                            &cell,
                            std::slice::from_ref(&target),
                            WriterLimits::default(),
                        )?;
                        assert!(!output.receipt().full_comment_product_acceptance);
                        assert!(!output.receipt().output.native_author_time_state_verified);
                        let actual = output.with_verified_bytes(<[u8]>::to_vec)?;
                        assert_exact_patch(&bytes, &forms, &cell, false, true, &target, &actual)?;
                    } else {
                        let body = review.observations()[observation]
                            .body_anchor
                            .as_ref()
                            .ok_or("body")?;
                        let output = review.lower_body(
                            &bytes,
                            marker,
                            std::slice::from_ref(&target),
                            WriterLimits::default(),
                        )?;
                        assert!(!output.receipt().native_author_time_state_verified);
                        assert!(!output.receipt().execution_publication_authority);
                        assert_exact_patch(
                            &bytes,
                            &forms,
                            body,
                            false,
                            false,
                            &target,
                            &output.with_verified_bytes(<[u8]>::to_vec)?,
                        )?;
                        let p = anchor(
                            &forms,
                            &bytes,
                            "p",
                            if observation == 0 { "101" } else { "102" },
                        )?;
                        let output = review.lower_paragraph(
                            &bytes,
                            marker,
                            &p,
                            &target,
                            WriterLimits::default(),
                        )?;
                        assert_exact_patch(
                            &bytes,
                            &forms,
                            &p,
                            true,
                            false,
                            &target,
                            &output.with_verified_bytes(<[u8]>::to_vec)?,
                        )?;
                    }
                }
            }
        }
    }
    Ok(())
}

#[test]
fn protection_rejects_before_noop_values_or_writer_but_source_drift_still_wins() -> TestResult {
    let bytes = package("cell", "1", false, false)?;
    let forms = original::forms(&bytes, "ancestor-review")?;
    let review = ImportedDocumentReviewBodies::import(&forms)?;
    let identical = TextFlowReader::read(
        fixture::paragraph(101, "OLD")
            .replacen("<hp:p ", &format!("<hp:p xmlns:hp='{HP}' "), 1)
            .as_bytes(),
        TextFlowLimits::default(),
    )?;
    let marker = &review.observations()[0].marker_anchor;
    for values in [vec![identical], vec![], vec![fixture::target()?]] {
        assert_eq!(
            review
                .lower_body(&bytes, marker, &values, WriterLimits::default())
                .err(),
            Some(ReviewBodyOutputError::Selection)
        );
    }
    let tiny = WriterLimits::new(hwpx_package::WriterLimitConfig {
        max_output_bytes: 1,
    })?;
    assert_eq!(
        review
            .lower_body(&bytes, marker, &[fixture::target()?], tiny)
            .err(),
        Some(ReviewBodyOutputError::Selection)
    );
    let changed = package("cell", "0", false, false)?;
    assert_eq!(
        review
            .lower_body(
                &changed,
                marker,
                &[fixture::target()?],
                WriterLimits::default()
            )
            .err(),
        Some(ReviewBodyOutputError::Source)
    );
    Ok(())
}

#[test]
fn table_insertion_selection_checks_outer_protection_before_template_admission() -> TestResult {
    // This tests source admission priority; the existing native-context suite tests
    // valid original 2x2 templates. The selected 1x2 MAIN fixture is NOT a create template.
    for flag in FLAGS {
        let markers = assembly::markers("").replace("<hp:t>HIDDEN-REVIEW</hp:t>", "<hp:t/>");
        for value in ["0", "1"] {
            let bytes = assembly::package(&wrapped(&markers, flag, value, false))?;
            let forms = original::forms(&bytes, "ancestor-review")?;
            let review = ImportedDocumentReviewBodies::import(&forms)?;
            let table = anchor(&forms, &bytes, "tbl", "800")?;
            for (observation, id) in [(0, "101"), (1, "102")] {
                let error = review
                    .prepare_table_creation(
                        &bytes,
                        &review.observations()[observation].marker_anchor,
                        &anchor(&forms, &bytes, "p", id)?,
                        ReviewTableTemplate {
                            forms: &forms,
                            fresh: &bytes,
                            table: &table,
                        },
                        TableCreateHwpxLimits::default(),
                    )
                    .err()
                    .ok_or("invalid original 1x2 template unexpectedly admitted")?;
                if value == "1" {
                    assert!(matches!(error, ReviewTableContextError::Selection));
                } else {
                    assert!(!matches!(error, ReviewTableContextError::Selection));
                }
            }
        }
    }
    Ok(())
}
