use hwpx_package::{WriterLimits, WriterLimitConfig, document_import::fields::{ImportedDocumentFields, semantics::{ImportedDocumentFieldSemantics, evaluation::{ImportedSourceFormulaEvaluation, output::FormulaResultOutputError}}}};
use domain_ir::{FormulaCache, FormulaValue, FormulaDecimal};
#[path = "support/document_import_formula_evaluation_fixture.rs"] mod fixture;
#[path = "support/document_import_field_fixture.rs"] mod forms_fixture;
type TestResult = Result<(), Box<dyn std::error::Error>>;

#[test]
fn actual36_sources_are_not_rewritten_when_results_are_current_or_fields_absent() -> TestResult {
    let mut counts = (0, 0);
    for bytes in fixture::inputs::actual_corpus()? {
        let forms = forms_fixture::forms(&bytes, "formula-output")?;
        let fields = ImportedDocumentFields::import(&forms)?;
        let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
        let evaluated = ImportedSourceFormulaEvaluation::import(&meanings)?;
        let result = evaluated.lower_results(&bytes, WriterLimits::default());
        if evaluated.values().is_empty() { assert!(matches!(result, Err(FormulaResultOutputError::NoTargets))); counts.0 += 1; }
        else { assert!(matches!(result, Err(FormulaResultOutputError::NoChange))); counts.1 += 1; }
    }
    assert_eq!(counts, (20, 16));
    Ok(())
}
#[test]
fn actual_source_numeric_changes_update_three_results_and_preserve_whole_original_ast_and_parts() -> TestResult {
    let mut cases = 0;
    for original in fixture::inputs::actual_corpus()?.into_iter().take(16) {
        let changed = fixture::mutate_first_cell(&original, |cell| fixture::replace_first_text(cell, "900001"))?;
        let forms = forms_fixture::forms(&changed, "formula-output")?;
        let fields = ImportedDocumentFields::import(&forms)?;
        let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
        let before = meanings.graph().clone();
        let evaluated = ImportedSourceFormulaEvaluation::import(&meanings)?;
        let output = evaluated.lower_results(&changed, WriterLimits::default())?;
        assert_eq!(output.receipt().changed_formula_results, 1);
        assert_eq!(output.receipt().changed_leaves, 3);
        assert_eq!(output.receipt().changed_parts, 1);
        assert!(!output.receipt().native_recalculation_verified);
        assert!(!output.receipt().execution_publication_authority);
        let next = output.with_verified_bytes(<[u8]>::to_vec)?;
        let next_forms = forms_fixture::forms(&next, "formula-output")?;
        let next_fields = ImportedDocumentFields::import(&next_forms)?;
        let next_meanings = ImportedDocumentFieldSemantics::import(&next_fields)?;
        let next_eval = ImportedSourceFormulaEvaluation::import(&next_meanings)?;
        assert_eq!(evaluated.values()[0].value, next_eval.values()[0].value);
        assert!(matches!(next_eval.lower_results(&next, WriterLimits::default()), Err(FormulaResultOutputError::NoChange)));
        assert_eq!(meanings.graph(), &before);
        assert_eq!(evaluated.verify_source(&changed)?, *evaluated.receipt());
        assert!(evaluated.verify_source(&original).is_err());
        cases += 1;
    }
    assert_eq!(cases, 16);
    Ok(())
}
#[test]
fn canonical_non_absolute_negative_fraction_and_absent_results_use_the_original_decoder() -> TestResult {
    let original = fixture::inputs::actual_corpus()?.remove(0);
    for (formula, expected) in [("=1/8", FormulaDecimal::new(125,3)), ("=-2.5", FormulaDecimal::new(-25,1)), ("=$A$1+2", FormulaDecimal::new(3,0))] {
        let bytes = fixture::replace_formula(&original, formula)?;
        let forms = forms_fixture::forms(&bytes, "formula-output")?;
        let fields = ImportedDocumentFields::import(&forms)?;
        let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
        let evaluated = ImportedSourceFormulaEvaluation::import(&meanings)?;
        assert_eq!(evaluated.values()[0].value, expected);
        let output = evaluated.lower_results(&bytes, WriterLimits::default())?;
        assert_eq!(output.receipt().changed_leaves, 3);
        output.with_verified_bytes(|b| -> TestResult {
            let forms = forms_fixture::forms(b, "formula-output")?;
            let fields = ImportedDocumentFields::import(&forms)?;
            let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
            let hwpx_package::document_import::fields::semantics::ImportedFieldMeaning::TableFormula { formula, .. } = &meanings.observations()[0].meaning else { return Err("formula".into()); };
            assert!(matches!(formula.cache(), FormulaCache::Unverified { value: FormulaValue::Decimal { value } } if *value == expected));
            Ok(())
        })??;
    }
    Ok(())
}
#[test]
fn stale_source_and_protected_targets_fail_before_noop_or_writer_limits() -> TestResult {
    let bytes = fixture::inputs::actual_corpus()?.remove(0);
    let forms = forms_fixture::forms(&bytes, "formula-output")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    let evaluated = ImportedSourceFormulaEvaluation::import(&meanings)?;
    let tiny = WriterLimits::new(WriterLimitConfig { max_output_bytes: 1 })?;
    assert!(matches!(evaluated.lower_results(b"stale", tiny), Err(FormulaResultOutputError::Source)));
    let changed = fixture::mutate_first_cell(&bytes, |cell| fixture::replace_first_text(cell, "900001"))?;
    let forms = forms_fixture::forms(&changed, "formula-output")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    assert!(matches!(ImportedSourceFormulaEvaluation::import(&meanings)?.lower_results(&changed, tiny), Err(FormulaResultOutputError::Writer)));
    Ok(())
}
