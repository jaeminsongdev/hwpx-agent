//! Actual immutable source evaluation and cache comparison, never native acceptance.
use domain_ir::{DocumentId, FormulaCache, FormulaValue};
use hwpx_package::document_import::{
    ImportedSourcePackage, SourceImportLimits,
    fields::{
        ImportedDocumentFields,
        semantics::{
            ImportedDocumentFieldSemantics, ImportedFieldMeaning,
            evaluation::{ImportedSourceFormulaEvaluation, SourceFormulaEvaluationReceipt},
        },
    },
    forms::ImportedDocumentForms,
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use std::error::Error;
#[path = "../tests/support/document_import_settings_inputs.rs"]
mod inputs;
#[derive(Default, Serialize)]
struct Evidence {
    profile: &'static str,
    actual_historical_inputs: usize,
    inputs_with_formula_targets: usize,
    formula_targets: usize,
    evaluated_tables: usize,
    source_cell_bindings: usize,
    canonical_numeric_cells: usize,
    unavailable_cells: usize,
    resolved_source_anchors: usize,
    unchanged_whole_meaning_graphs: usize,
    observed_unverified_decimal_cache_comparisons: usize,
    observed_cache_matches: usize,
    observed_cache_mismatches: usize,
    receipts: Vec<SourceFormulaEvaluationReceipt>,
}
fn main() -> Result<(), Box<dyn Error>> {
    let mut evidence = Evidence {
        profile: "hwpx-agent.actual-source-formula-evaluation-consumer/partial-v1",
        ..Evidence::default()
    };
    for bytes in inputs::actual_corpus()? {
        let source = ImportedSourcePackage::import(
            &bytes,
            DocumentId::parse("source-formula-consumer")?,
            Sha256::digest(&bytes).into(),
            SourceImportLimits::default(),
        )?;
        let forms = ImportedDocumentForms::import(source)?;
        let fields = ImportedDocumentFields::import(&forms)?;
        let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
        let before = meanings.graph().clone();
        let evaluated = ImportedSourceFormulaEvaluation::import(&meanings)?;
        if evaluated.verify_source(&bytes)? != *evaluated.receipt() || &before != meanings.graph() {
            return Err("source evaluation fresh receipt or whole original graph drift".into());
        }
        for binding in evaluated.source_bindings() {
            forms.source().resolve_anchor(&binding.source_anchor)?;
            evidence.resolved_source_anchors += 1;
        }
        for value in evaluated.values() {
            forms.source().resolve_anchor(&value.begin_anchor)?;
            evidence.resolved_source_anchors += 1;
            let meaning = meanings
                .observations()
                .iter()
                .find(|m| m.reference_id == value.reference_id)
                .ok_or("source reference not bound")?;
            let ImportedFieldMeaning::TableFormula { formula, .. } = &meaning.meaning else {
                return Err("source formula meaning missing".into());
            };
            if let FormulaCache::Unverified {
                value: FormulaValue::Decimal { value: cached },
            } = formula.cache()
            {
                evidence.observed_unverified_decimal_cache_comparisons += 1;
                if cached == &value.value {
                    evidence.observed_cache_matches += 1;
                } else {
                    evidence.observed_cache_mismatches += 1;
                }
            }
        }
        let r = evaluated.receipt();
        evidence.actual_historical_inputs += 1;
        evidence.unchanged_whole_meaning_graphs += 1;
        evidence.inputs_with_formula_targets += usize::from(r.formula_targets > 0);
        evidence.formula_targets += r.formula_targets;
        evidence.evaluated_tables += r.evaluated_tables;
        evidence.source_cell_bindings += r.source_cell_bindings;
        evidence.canonical_numeric_cells += r.canonical_numeric_cells;
        evidence.unavailable_cells += r.unavailable_cells;
        evidence.receipts.push(r.clone());
    }
    if evidence.actual_historical_inputs != 36 || evidence.unchanged_whole_meaning_graphs != 36 {
        return Err("whole actual input coverage drift".into());
    }
    println!("{}", serde_json::to_string(&evidence)?);
    Ok(())
}
