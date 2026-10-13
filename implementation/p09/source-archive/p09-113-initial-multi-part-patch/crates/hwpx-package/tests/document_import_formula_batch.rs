use domain_ir::{FormulaCache, FormulaDecimal, FormulaValue};
use hwpx_package::{
    WriterLimitConfig, WriterLimits,
    document_import::fields::{
        ImportedDocumentFields,
        semantics::{
            ImportedDocumentFieldSemantics, ImportedFieldMeaning,
            evaluation::{ImportedSourceFormulaEvaluation, output::FormulaResultOutputError},
        },
    },
};
#[path = "support/document_import_formula_batch_fixture.rs"]
mod fixture;
#[path = "support/document_import_field_fixture.rs"]
mod forms_fixture;
type TestResult = Result<(), Box<dyn std::error::Error>>;

fn output(
    bytes: &[u8],
    targets: usize,
    changed: usize,
    parts: usize,
) -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    let forms = forms_fixture::forms(bytes, "formula-batch")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    let before = meanings.graph().clone();
    let evaluated = ImportedSourceFormulaEvaluation::import(&meanings)?;
    let candidate = evaluated.lower_results(bytes, WriterLimits::default())?;
    assert_eq!(candidate.receipt().formula_targets, targets);
    assert_eq!(candidate.receipt().changed_formula_results, changed);
    assert_eq!(candidate.receipt().changed_leaves, changed * 3);
    assert_eq!(candidate.receipt().changed_parts, parts);
    assert!(!candidate.receipt().native_recalculation_verified);
    assert_eq!(meanings.graph(), &before);
    assert_eq!(evaluated.verify_source(bytes)?, *evaluated.receipt());
    Ok(candidate.with_verified_bytes(<[u8]>::to_vec)?)
}
fn values(bytes: &[u8]) -> Result<Vec<FormulaDecimal>, Box<dyn std::error::Error>> {
    let forms = forms_fixture::forms(bytes, "formula-batch")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    let evaluation = ImportedSourceFormulaEvaluation::import(&meanings)?;
    // Actual meaning order, not hash-sorted table iteration.
    meanings
        .observations()
        .iter()
        .filter_map(|m| {
            matches!(m.meaning, ImportedFieldMeaning::TableFormula { .. }).then(|| {
                evaluation
                    .values()
                    .iter()
                    .find(|v| v.reference_id == m.reference_id)
                    .map(|v| v.value)
                    .ok_or("source value".into())
            })
        })
        .collect()
}
fn assert_current(bytes: &[u8], expected: &[FormulaDecimal]) -> TestResult {
    assert_eq!(values(bytes)?, expected);
    let forms = forms_fixture::forms(bytes, "formula-batch")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    let evaluated = ImportedSourceFormulaEvaluation::import(&meanings)?;
    for meaning in meanings.observations() {
        if let ImportedFieldMeaning::TableFormula { formula, .. } = &meaning.meaning {
            let value = evaluated
                .values()
                .iter()
                .find(|v| v.reference_id == meaning.reference_id)
                .ok_or("value")?;
            assert!(
                matches!(formula.cache(), FormulaCache::Unverified { value: FormulaValue::Decimal { value: cached }} if cached == &value.value)
            );
        }
    }
    assert!(matches!(
        evaluated.lower_results(bytes, WriterLimits::default()),
        Err(FormulaResultOutputError::NoChange)
    ));
    Ok(())
}
#[test]
fn two_formulas_share_actual_numeric_and_formula_dependencies_without_cache_fallback() -> TestResult
{
    forms_fixture::forms(&forms_fixture::captured()?, "formula-batch")?;
    let original = fixture::batch("5")?;
    assert_eq!(
        values(&original)?,
        vec![FormulaDecimal::new(7, 0), FormulaDecimal::new(6, 0)]
    );
    let next = output(&original, 2, 2, 1)?;
    assert_current(
        &next,
        &[FormulaDecimal::new(7, 0), FormulaDecimal::new(6, 0)],
    )?;
    let old_parts = fixture::entries(&original)?;
    let next_parts = fixture::entries(&next)?;
    assert_eq!(
        old_parts.keys().collect::<Vec<_>>(),
        next_parts.keys().collect::<Vec<_>>()
    );
    for (name, bytes) in old_parts {
        if name != "Contents/section0.xml" {
            assert_eq!(next_parts[&name], bytes);
        }
    }
    Ok(())
}
#[test]
fn distinct_section_tables_preserve_source_value_identity_even_when_anchor_hash_order_changes()
-> TestResult {
    let first = fixture::batch("5")?;
    for input in ["101", "203", "307", "409", "503", "607", "701", "809"] {
        let second = fixture::batch(input)?;
        let bytes = fixture::two_sections(&first, &second)?;
        let value: i64 = input.parse()?;
        let expected = [
            FormulaDecimal::new(7, 0),
            FormulaDecimal::new(6, 0),
            FormulaDecimal::new(value + 2, 0),
            FormulaDecimal::new(value + 1, 0),
        ];
        assert_eq!(values(&bytes)?, expected);
        let candidate = output(&bytes, 4, 4, 2)?;
        assert_current(&candidate, &expected)?;
        let old = fixture::entries(&bytes)?;
        let new = fixture::entries(&candidate)?;
        for (name, bytes) in old {
            if !matches!(
                name.as_str(),
                "Contents/section0.xml" | "Contents/section1.xml"
            ) {
                assert_eq!(new[&name], bytes);
            }
        }
    }
    Ok(())
}
#[test]
fn mixed_current_and_changed_sections_update_only_changed_results() -> TestResult {
    let first = fixture::batch("5")?;
    let current = output(&fixture::batch("101")?, 2, 2, 1)?;
    let mixed = fixture::two_sections(&first, &current)?;
    let next = output(&mixed, 4, 2, 1)?;
    assert_current(
        &next,
        &[
            FormulaDecimal::new(7, 0),
            FormulaDecimal::new(6, 0),
            FormulaDecimal::new(103, 0),
            FormulaDecimal::new(102, 0),
        ],
    )?;
    let old = fixture::entries(&mixed)?;
    let new = fixture::entries(&next)?;
    assert_eq!(old["Contents/section1.xml"], new["Contents/section1.xml"]);
    Ok(())
}
#[test]
fn protection_in_any_changed_or_current_field_denies_whole_batch_before_writer_without_partial_output()
-> TestResult {
    let first = fixture::batch("5")?;
    let second = fixture::batch("101")?;
    let current = output(&second, 2, 2, 1)?;
    let tiny = WriterLimits::new(WriterLimitConfig {
        max_output_bytes: 1,
    })?;
    for other in [&second, &current] {
        let mixed = fixture::two_sections(&first, other)?;
        for part in ["Contents/section0.xml", "Contents/section1.xml"] {
            for target in 0..2 {
                let protected = fixture::protect(&mixed, part, target)?;
                let before = protected.clone();
                let forms = forms_fixture::forms(&protected, "formula-batch")?;
                let fields = ImportedDocumentFields::import(&forms)?;
                let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
                let graph = meanings.graph().clone();
                let evaluated = ImportedSourceFormulaEvaluation::import(&meanings)?;
                assert!(matches!(
                    evaluated.lower_results(&protected, tiny),
                    Err(FormulaResultOutputError::Protection)
                ));
                assert!(matches!(
                    evaluated.lower_results(b"stale", tiny),
                    Err(FormulaResultOutputError::Source)
                ));
                assert_eq!(protected, before);
                assert_eq!(meanings.graph(), &graph);
                assert_eq!(evaluated.verify_source(&protected)?, *evaluated.receipt());
            }
        }
    }
    Ok(())
}

#[test]
fn empty_result_leaf_expansion_across_sections_keeps_all_formula_dependencies() -> TestResult {
    for self_closing in [false, true] {
        let first = fixture::blank_results(&fixture::batch("5")?, self_closing)?;
        let second = fixture::blank_results(&fixture::batch("101")?, self_closing)?;
        let mixed = fixture::two_sections(&first, &second)?;
        let next = output(&mixed, 4, 4, 2)?;
        assert_current(
            &next,
            &[
                FormulaDecimal::new(7, 0),
                FormulaDecimal::new(6, 0),
                FormulaDecimal::new(103, 0),
                FormulaDecimal::new(102, 0),
            ],
        )?;
    }
    Ok(())
}
#[test]
fn invalid_numeric_dependency_in_second_section_denies_evaluation_of_whole_source() -> TestResult {
    let empty =
        forms_fixture::package("<hp:p id='1'><hp:run><hp:t>NO-FIELDS</hp:t></hp:run></hp:p>")?;
    let forms = forms_fixture::forms(&empty, "formula-batch")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    let evaluated = ImportedSourceFormulaEvaluation::import(&meanings)?;
    assert!(matches!(
        evaluated.lower_results(&empty, WriterLimits::default()),
        Err(FormulaResultOutputError::NoTargets)
    ));
    let healthy = fixture::batch("5")?;
    let invalid = fixture::batch("NON-NUMERIC")?;
    let mixed = fixture::two_sections(&healthy, &invalid)?;
    let before = mixed.clone();
    let forms = forms_fixture::forms(&mixed, "formula-batch")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    assert!(ImportedSourceFormulaEvaluation::import(&meanings).is_err());
    assert_eq!(mixed, before);
    Ok(())
}
