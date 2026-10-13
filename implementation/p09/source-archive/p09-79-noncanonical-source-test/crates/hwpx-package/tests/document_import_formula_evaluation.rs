use domain_ir::formula_evaluation::EvaluationError;
use domain_ir::{FormulaCache, FormulaValue};
use hwpx_package::document_import::fields::{
    ImportedDocumentFields,
    semantics::{
        ImportedDocumentFieldSemantics, ImportedFieldMeaning,
        evaluation::{ImportedSourceFormulaEvaluation, SourceFormulaEvaluationError},
    },
};
#[path = "support/document_import_formula_evaluation_fixture.rs"]
mod fixture;
#[path = "support/document_import_field_fixture.rs"]
mod forms_fixture;
type TestResult = Result<(), Box<dyn std::error::Error>>;

#[test]
fn all_actual_inputs_evaluate_source_values_and_preserve_whole_graph_and_caches() -> TestResult {
    let mut counts = (0, 0, 0, 0, 0);
    for bytes in fixture::inputs::actual_corpus()? {
        let forms = forms_fixture::forms(&bytes, "source-evaluation-test")?;
        let fields = ImportedDocumentFields::import(&forms)?;
        let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
        let before = meanings.graph().clone();
        let observations = meanings.observations().to_vec();
        let evaluated = ImportedSourceFormulaEvaluation::import(&meanings)?;
        assert_eq!(evaluated.verify_source(&bytes)?, *evaluated.receipt());
        assert_eq!(meanings.graph(), &before);
        assert_eq!(meanings.observations(), observations);
        let receipt = evaluated.receipt();
        counts.0 += 1;
        counts.1 += receipt.formula_targets;
        counts.2 += receipt.canonical_numeric_cells;
        counts.3 += receipt.source_cell_bindings;
        for binding in evaluated.source_bindings() {
            forms.source().resolve_anchor(&binding.source_anchor)?;
        }
        for value in evaluated.values() {
            forms.source().resolve_anchor(&value.begin_anchor)?;
            let source = meanings
                .observations()
                .iter()
                .find(|m| m.reference_id == value.reference_id)
                .ok_or("meaning")?;
            let ImportedFieldMeaning::TableFormula { formula, .. } = &source.meaning else {
                return Err("formula".into());
            };
            let FormulaCache::Unverified {
                value: FormulaValue::Decimal { value: cached },
            } = formula.cache()
            else {
                return Err("unverified source cache".into());
            };
            assert_eq!(cached, &value.value); // comparison only, not native qualification
            counts.4 += 1;
        }
    }
    assert_eq!(counts, (36, 16, 112, 128, 16));
    Ok(())
}

#[test]
fn actual_layout_metadata_is_preserved_not_flattened_or_taken_as_numeric_text() -> TestResult {
    let bytes = fixture::inputs::actual_corpus()?.remove(0);
    let forms = forms_fixture::forms(&bytes, "source-evaluation-test")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    assert!(
        meanings
            .graph()
            .clone()
            .into_draft()
            .sections
            .iter()
            .any(|s| !s.body.children.is_empty())
    );
    let evaluated = ImportedSourceFormulaEvaluation::import(&meanings)?;
    assert_eq!(
        (
            evaluated.receipt().formula_targets,
            evaluated.receipt().canonical_numeric_cells
        ),
        (1, 7)
    );
    let without_layout = fixture::mutate_first_cell(&bytes, |cell| {
        let start = cell.find("<hp:linesegarray>").ok_or("layout start")?;
        let end = cell.find("</hp:linesegarray>").ok_or("layout end")? + "</hp:linesegarray>".len();
        let mut out = cell.to_owned();
        out.replace_range(start..end, "");
        Ok(out)
    })?;
    assert!(evaluated.verify_source(&without_layout).is_err());
    let forms = forms_fixture::forms(&without_layout, "source-evaluation-test")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    let no_layout = ImportedSourceFormulaEvaluation::import(&meanings)?;
    assert_eq!(evaluated.values()[0].value, no_layout.values()[0].value);
    assert_ne!(
        evaluated.receipt().source_package_sha256,
        no_layout.receipt().source_package_sha256
    );
    Ok(())
}

#[test]
fn changed_actual_numeric_input_changes_value_without_using_or_mutating_original_cache()
-> TestResult {
    let bytes = fixture::inputs::actual_corpus()?.remove(0);
    let forms = forms_fixture::forms(&bytes, "source-evaluation-test")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    let evaluated = ImportedSourceFormulaEvaluation::import(&meanings)?;
    let changed =
        fixture::mutate_first_cell(&bytes, |cell| fixture::replace_first_text(cell, "900001"))?;
    assert!(evaluated.verify_source(&changed).is_err());
    let forms = forms_fixture::forms(&changed, "source-evaluation-test")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let changed_meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    let before = changed_meanings.graph().clone();
    let changed_value = ImportedSourceFormulaEvaluation::import(&changed_meanings)?;
    assert_ne!(changed_value.values()[0].value, evaluated.values()[0].value);
    assert_ne!(
        changed_value.receipt().values_and_source_bindings_sha256,
        evaluated.receipt().values_and_source_bindings_sha256
    );
    assert_eq!(
        meanings.observations()[0].meaning,
        changed_meanings.observations()[0].meaning
    );
    assert_eq!(changed_meanings.graph(), &before);
    Ok(())
}

#[test]
fn noncanonical_blank_locale_unicode_and_nonnumeric_source_never_default_or_coerce() -> TestResult {
    let original = fixture::inputs::actual_corpus()?.remove(0);
    for replacement in ["", " ", "01", "-0", "1,5", "１", "text", "1&lt;hp:t/&gt;"] {
        let bytes = fixture::mutate_first_cell(&original, |cell| {
            fixture::replace_first_text(cell, replacement)
        })?;
        let forms = forms_fixture::forms(&bytes, "source-evaluation-test")?;
        let fields = ImportedDocumentFields::import(&forms)?;
        let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
        assert!(matches!(
            ImportedSourceFormulaEvaluation::import(&meanings),
            Err(SourceFormulaEvaluationError::Math(
                EvaluationError::MissingValue
            ))
        ));
    }
    Ok(())
}

#[test]
fn opaque_layout_with_hidden_text_or_foreign_children_is_not_ignored() -> TestResult {
    let original = fixture::inputs::actual_corpus()?.remove(0);
    for hidden in [
        "<hp:t>9</hp:t>",
        "<hp:ctrl/>",
        "<u:lineseg xmlns:u='urn:future'/>",
    ] {
        let bytes = fixture::mutate_first_cell(&original, |cell| {
            assert!(cell.contains("</hp:linesegarray>"));
            Ok(cell.replacen(
                "</hp:linesegarray>",
                &format!("{hidden}</hp:linesegarray>"),
                1,
            ))
        })?;
        let forms = forms_fixture::forms(&bytes, "source-evaluation-test")?;
        let fields = ImportedDocumentFields::import(&forms)?;
        let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
        assert!(matches!(
            ImportedSourceFormulaEvaluation::import(&meanings),
            Err(SourceFormulaEvaluationError::Math(
                EvaluationError::MissingValue
            ))
        ));
    }
    Ok(())
}

#[test]
fn tabs_breaks_and_extra_paragraphs_are_not_plain_numeric_source() -> TestResult {
    let original = fixture::inputs::actual_corpus()?.remove(0);
    for replacement in [
        "1<hp:lineBreak/>",
        "1<hp:tab width='0' leader='0' type='0'/>",
    ] {
        let bytes = fixture::mutate_first_cell(&original, |cell| {
            fixture::replace_first_text(cell, replacement)
        })?;
        let forms = forms_fixture::forms(&bytes, "source-evaluation-test")?;
        let fields = ImportedDocumentFields::import(&forms)?;
        let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
        assert!(matches!(
            ImportedSourceFormulaEvaluation::import(&meanings),
            Err(SourceFormulaEvaluationError::Math(
                EvaluationError::MissingValue
            ))
        ));
    }
    let bytes = fixture::mutate_first_cell(&original, |cell| {
        assert!(cell.contains("</hp:subList>"));
        Ok(cell.replacen(
            "</hp:subList>",
            "<hp:p id='99999'><hp:run><hp:t>2</hp:t></hp:run></hp:p></hp:subList>",
            1,
        ))
    })?;
    let forms = forms_fixture::forms(&bytes, "source-evaluation-test")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    assert!(matches!(
        ImportedSourceFormulaEvaluation::import(&meanings),
        Err(SourceFormulaEvaluationError::Math(
            EvaluationError::MissingValue
        ))
    ));
    Ok(())
}

#[test]
fn cached_field_text_inside_numeric_dependency_is_not_a_plain_value() -> TestResult {
    let original = fixture::inputs::actual_corpus()?.remove(0);
    let bytes = fixture::mutate_first_cell(&original, |cell| {
        assert!(cell.contains("<hp:t>") && cell.contains("</hp:t>"));
        Ok(cell
            .replacen(
                "<hp:t>",
                "<hp:ctrl><hp:fieldBegin id='90001' type='DATE'/></hp:ctrl><hp:t>",
                1,
            )
            .replacen(
                "</hp:t>",
                "</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='90001'/></hp:ctrl>",
                1,
            ))
    })?;
    let forms = forms_fixture::forms(&bytes, "source-evaluation-test")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    assert_eq!(meanings.receipt().unsupported_meanings, 1);
    assert!(matches!(
        ImportedSourceFormulaEvaluation::import(&meanings),
        Err(SourceFormulaEvaluationError::Math(
            EvaluationError::MissingValue
        ))
    ));
    Ok(())
}

#[test]
fn actual_formula_dependencies_follow_source_ast_not_old_cache_including_cycles() -> TestResult {
    let original = fixture::inputs::actual_corpus()?.remove(0);
    for (expression, expected) in [
        ("=SUM(D2:D2)", EvaluationError::Cycle),
        ("=1/0", EvaluationError::DivisionByZero),
    ] {
        let bytes = fixture::replace_formula(&original, expression)?;
        let forms = forms_fixture::forms(&bytes, "source-evaluation-test")?;
        let fields = ImportedDocumentFields::import(&forms)?;
        let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
        let before = meanings.graph().clone();
        assert!(
            matches!(ImportedSourceFormulaEvaluation::import(&meanings), Err(SourceFormulaEvaluationError::Math(e)) if e == expected)
        );
        assert_eq!(meanings.graph(), &before);
    }
    Ok(())
}

#[test]
fn nonformula_meanings_are_explicitly_not_evaluated_including_captured_https() -> TestResult {
    for bytes in [
        forms_fixture::captured()?,
        forms_fixture::package(
            "<hp:p id='1'><hp:run><hp:ctrl><hp:fieldBegin id='1' type='DATE'/></hp:ctrl><hp:t>123</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='1'/></hp:ctrl></hp:run></hp:p>",
        )?,
    ] {
        let forms = forms_fixture::forms(&bytes, "source-evaluation-test")?;
        let fields = ImportedDocumentFields::import(&forms)?;
        let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
        let evaluated = ImportedSourceFormulaEvaluation::import(&meanings)?;
        assert_eq!(
            (
                evaluated.receipt().formula_targets,
                evaluated.receipt().non_formula_meanings_not_evaluated
            ),
            (0, 1)
        );
        assert!(evaluated.values().is_empty() && evaluated.source_bindings().is_empty());
        assert_eq!(evaluated.verify_source(&bytes)?, *evaluated.receipt());
    }
    Ok(())
}

#[test]
fn debug_and_receipts_are_hashes_counts_not_document_values_or_source_xml() -> TestResult {
    let bytes = fixture::inputs::actual_corpus()?.remove(0);
    let forms = forms_fixture::forms(&bytes, "source-evaluation-test")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    let evaluated = ImportedSourceFormulaEvaluation::import(&meanings)?;
    assert_eq!(
        format!("{evaluated:?}"),
        "ImportedSourceFormulaEvaluation(<redacted>)"
    );
    assert_eq!(
        format!("{:?}", evaluated.values()[0]),
        "SourceFormulaValue(<redacted>)"
    );
    let receipt = serde_json::to_value(evaluated.receipt())?;
    assert!(receipt.get("values").is_none() && receipt.get("bindings").is_none());
    assert!(!serde_json::to_string(evaluated.receipt())?.contains("<hp:"));
    Ok(())
}
