use hwpx_package::{WriterLimits, WriterLimitConfig, document_import::fields::{ImportedDocumentFields, semantics::{ImportedDocumentFieldSemantics, evaluation::{ImportedSourceFormulaEvaluation, output::FormulaResultOutputError}}}};
use domain_ir::{FormulaCache, FormulaValue, FormulaDecimal};
#[path = "support/document_import_formula_evaluation_fixture.rs"] mod fixture;
#[path = "support/document_import_field_fixture.rs"] mod forms_fixture;
#[path = "support/document_import_formula_output_fixture.rs"] mod output_fixture;
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
    let mut cases = (0, 0, 0);
    for original in fixture::inputs::actual_corpus()? {
        let forms = forms_fixture::forms(&original, "formula-output")?;
        let fields = ImportedDocumentFields::import(&forms)?;
        let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
        if ImportedSourceFormulaEvaluation::import(&meanings)?.values().is_empty() { continue; }
        let changed = fixture::mutate_first_cell(&original, |cell| fixture::replace_first_text(cell, "900001"))?;
        let forms = forms_fixture::forms(&changed, "formula-output")?;
        let fields = ImportedDocumentFields::import(&forms)?;
        let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
        let before = meanings.graph().clone();
        let evaluated = ImportedSourceFormulaEvaluation::import(&meanings)?;
        let output = match evaluated.lower_results(&changed, WriterLimits::default()) {
            Ok(output) => output,
            Err(FormulaResultOutputError::NoChange) => {
                for value in evaluated.values() {
                    let source = meanings.observations().iter().find(|m| m.reference_id == value.reference_id).ok_or("meaning")?;
                    let hwpx_package::document_import::fields::semantics::ImportedFieldMeaning::TableFormula { formula, .. } = &source.meaning else { return Err("formula".into()); };
                    assert!(matches!(formula.cache(), FormulaCache::Unverified { value: FormulaValue::Decimal { value: cached } } if cached == &value.value));
                }
                cases.0 += 1; cases.2 += 1; continue;
            }
            Err(error) => return Err(error.into()),
        };
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
        cases.0 += 1;
        cases.1 += 1;
    }
    assert_eq!(cases.0, 16);
    assert_eq!(cases.1 + cases.2, 16);
    assert!(cases.1 > 0);
    eprintln!("P112 numeric derivatives: total={}, changed={}, unchanged_mathematically={}", cases.0, cases.1, cases.2);
    Ok(())
}
#[test]
fn canonical_non_absolute_negative_fraction_and_absolute_results_use_the_original_decoder() -> TestResult {
    let original = fixture::inputs::actual_corpus()?.remove(0);
    for (formula, expected) in [("=1/8", FormulaDecimal::new(125,3)), ("=-2.5", FormulaDecimal::new(-25,1)), ("=0*$A$1+3", FormulaDecimal::new(3,0))] {
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
    let captured = forms_fixture::captured()?;
    forms_fixture::forms(&captured, "formula-output")?;
    let no_field = forms_fixture::package("<hp:p id='1'><hp:run><hp:t>NO-FIELD</hp:t></hp:run></hp:p>")?;
    let no_forms = forms_fixture::forms(&no_field, "formula-output")?;
    let no_fields = ImportedDocumentFields::import(&no_forms)?;
    let no_meanings = ImportedDocumentFieldSemantics::import(&no_fields)?;
    assert!(matches!(ImportedSourceFormulaEvaluation::import(&no_meanings)?.lower_results(&no_field, WriterLimits::default()), Err(FormulaResultOutputError::NoTargets)));
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
    for original in [&bytes, &changed] {
        let protected = output_fixture::section(original, |text| {
            let xml = hwpx_package::PreservingXmlDocument::parse(text.as_bytes())?;
            let begin = xml.elements().iter().position(|e| e.name().local_name() == "fieldBegin").ok_or("begin")?;
            let mut parent = xml.elements()[begin].parent();
            let cell = loop {
                let i = parent.ok_or("cell")?;
                if xml.elements()[i].name().local_name() == "tc" { break &xml.elements()[i]; }
                parent = xml.elements()[i].parent();
            };
            let attr = cell.attributes().iter().find(|a| a.name().local_name() == "protect").ok_or("protect")?;
            let mut result = text.to_owned();
            result.replace_range(attr.value_span().start()..attr.value_span().end(), "1");
            Ok(result)
        })?;
        let forms = forms_fixture::forms(&protected, "formula-output")?;
        let fields = ImportedDocumentFields::import(&forms)?;
        let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
        assert!(matches!(ImportedSourceFormulaEvaluation::import(&meanings)?.lower_results(&protected, tiny), Err(FormulaResultOutputError::Protection)));
    }
    Ok(())
}
#[test]
fn empty_canonical_cache_result_leaves_are_updated_without_inventing_native_verification() -> TestResult {
    let canonical = fixture::replace_formula(&fixture::inputs::actual_corpus()?.remove(0), "=1/8")?;
    for empty in [false, true] {
        let bytes = output_fixture::blank_results(&canonical, empty)?;
        let forms = forms_fixture::forms(&bytes, "formula-output")?;
        let fields = ImportedDocumentFields::import(&forms)?;
        let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
        let evaluated = ImportedSourceFormulaEvaluation::import(&meanings)?;
        let output = evaluated.lower_results(&bytes, WriterLimits::default())?;
        assert_eq!(output.receipt().changed_leaves, 3);
        assert!(!output.receipt().native_recalculation_verified);
    }
    Ok(())
}
