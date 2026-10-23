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
use std::{
    collections::BTreeMap,
    error::Error,
    time::{Duration, Instant},
};
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
#[derive(Default, Serialize)]
struct StageTiming {
    calls: usize,
    total_us: u128,
    min_us: u128,
    max_us: u128,
}
impl StageTiming {
    fn record(&mut self, duration: Duration) {
        let micros = duration.as_micros();
        self.min_us = if self.calls == 0 {
            micros
        } else {
            self.min_us.min(micros)
        };
        self.max_us = self.max_us.max(micros);
        self.calls += 1;
        self.total_us += micros;
    }
}
fn main() -> Result<(), Box<dyn Error>> {
    let args: Vec<_> = std::env::args_os().skip(1).collect();
    if matches!(args.as_slice(), [argument] if argument == "--reconstruction-timing-only") {
        return reconstruction_timing_probe();
    }
    let timing_only = match args.as_slice() {
        [] => false,
        [argument] if argument == "--timing-only" => true,
        _ => return Err("closed diagnostic argument scope".into()),
    };
    let mut stages: BTreeMap<&'static str, StageTiming> = BTreeMap::new();
    let mut evidence = Evidence {
        profile: "hwpx-agent.actual-source-formula-evaluation-consumer/partial-v1",
        ..Evidence::default()
    };
    for bytes in inputs::actual_corpus()? {
        let tick = Instant::now();
        let source = ImportedSourcePackage::import(
            &bytes,
            DocumentId::parse("source-formula-consumer")?,
            Sha256::digest(&bytes).into(),
            SourceImportLimits::default(),
        )?;
        stages
            .entry("source_import")
            .or_default()
            .record(tick.elapsed());
        let tick = Instant::now();
        let forms = ImportedDocumentForms::import(source)?;
        stages
            .entry("forms_import")
            .or_default()
            .record(tick.elapsed());
        let tick = Instant::now();
        let fields = ImportedDocumentFields::import(&forms)?;
        stages
            .entry("field_ranges_import")
            .or_default()
            .record(tick.elapsed());
        let tick = Instant::now();
        let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
        stages
            .entry("field_semantics_import")
            .or_default()
            .record(tick.elapsed());
        if timing_only {
            let tick = Instant::now();
            let digest = meanings.graph().canonical_sha256()?;
            stages
                .entry("meaning_graph_canonical_sha256")
                .or_default()
                .record(tick.elapsed());
            if digest != meanings.receipt().graph_sha256 {
                return Err("diagnostic canonical graph receipt drift".into());
            }
        }
        let tick = Instant::now();
        let before = meanings.graph().clone();
        stages
            .entry("meaning_graph_clone")
            .or_default()
            .record(tick.elapsed());
        let tick = Instant::now();
        let evaluated = ImportedSourceFormulaEvaluation::import(&meanings)?;
        stages
            .entry("source_formula_evaluation")
            .or_default()
            .record(tick.elapsed());
        let tick = Instant::now();
        let verified = evaluated.verify_source(&bytes)?;
        stages
            .entry("fresh_source_verify")
            .or_default()
            .record(tick.elapsed());
        if verified != *evaluated.receipt() || &before != meanings.graph() {
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
    if timing_only {
        if stages.len() != 8 || stages.values().any(|stage| stage.calls != 36) {
            return Err("diagnostic complete stage coverage drift".into());
        }
        // Numeric aggregate observations only. No raw values, graphs, anchors,
        // paths, per-input identity, cache contents or complete receipt output.
        println!(
            "{}",
            serde_json::json!({
                "schema_version": "hwpx-agent.p09-source-stage-timing/v1",
                "qualification": "PROFILE_ONLY_NOT_SIGNED_SERVICE_SQL_NATIVE_OR_GATE",
                "actual_historical_inputs": evidence.actual_historical_inputs,
                "unchanged_whole_meaning_graphs": evidence.unchanged_whole_meaning_graphs,
                "inputs_with_formula_targets": evidence.inputs_with_formula_targets,
                "formula_targets": evidence.formula_targets,
                "source_cell_bindings": evidence.source_cell_bindings,
                "stages": stages,
                "native_or_SQL_qualified": false,
                "product_complete": false,
                "P09_gate": "OPEN"
            })
        );
    } else {
        println!("{}", serde_json::to_string(&evidence)?);
    }
    Ok(())
}

// Pure importer diagnostic only. Every iteration freshly imports the full bytes;
// no authority result, reconstruction or input acceptance is cached across calls.
fn reconstruction_timing_probe() -> Result<(), Box<dyn Error>> {
    let corpus = inputs::actual_corpus()?;
    if corpus.len() != 36 {
        return Err("reconstruction whole corpus coverage drift".into());
    }
    let mut stages: BTreeMap<&'static str, StageTiming> = BTreeMap::new();
    let mut full_equal = 0;
    let mut tamper_denied = 0;
    let mut targets = 0;
    let mut bindings = 0;
    for bytes in &corpus {
        let tick = Instant::now();
        let source = ImportedSourcePackage::import(
            bytes, DocumentId::parse("source-formula-consumer")?,
            Sha256::digest(bytes).into(), SourceImportLimits::default(),
        )?;
        stages.entry("source_import").or_default().record(tick.elapsed());
        let tick = Instant::now();
        let forms = ImportedDocumentForms::import(source)?;
        stages.entry("forms_import").or_default().record(tick.elapsed());
        let before_graph = forms.graph().clone();
        let before_receipt = forms.receipt().clone();
        let tick = Instant::now();
        let reconstructed = forms.reconstruct_source_for_verification(bytes)?;
        stages.entry("fresh_complete_reconstruction").or_default().record(tick.elapsed());
        if reconstructed.receipt() != &before_receipt || forms.graph() != &before_graph {
            return Err("reconstruction whole graph or receipt drift".into());
        }
        full_equal += 1;
        let tick = Instant::now();
        if forms.graph().canonical_sha256()? != forms.receipt().graph_sha256 {
            return Err("reconstruction canonical graph receipt drift".into());
        }
        stages.entry("forms_graph_canonical_sha256").or_default().record(tick.elapsed());
        let mut tampered = bytes.clone();
        let first = tampered.first_mut().ok_or("empty reconstruction input")?;
        *first ^= 1;
        if forms.reconstruct_source_for_verification(&tampered).is_ok() {
            return Err("reconstruction changed input accepted".into());
        }
        tamper_denied += 1;
        let fields = ImportedDocumentFields::import(&forms)?;
        let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
        let evaluated = ImportedSourceFormulaEvaluation::import(&meanings)?;
        targets += evaluated.values().len();
        bindings += evaluated.source_bindings().len();
    }
    if full_equal != 36 || tamper_denied != 36 || targets != 16 || bindings != 128
        || stages.len() != 4 || stages.values().any(|stage| stage.calls != 36)
        || inputs::actual_corpus()? != corpus
    {
        return Err("reconstruction complete coverage or frozen corpus drift".into());
    }
    // Numeric aggregates only; never original bytes, identifiers, keys or graphs.
    println!("{}", serde_json::json!({
        "schema_version":"hwpx-agent.p09-reconstruction-stage-timing/v1",
        "qualification":"PURE_COMPLETE36_RECONSTRUCTION_NOT_SIGNED_SQL_NATIVE_OR_GATE",
        "originals":36,"whole_graph_receipts_equal":full_equal,"tamper_denied":tamper_denied,
        "formula_targets":targets,"source_cell_bindings":bindings,"stages":stages,
        "runtime_signed_consumer_qualified":false,"product_complete":false,"P09_gate":"OPEN"
    }));
    Ok(())
}
