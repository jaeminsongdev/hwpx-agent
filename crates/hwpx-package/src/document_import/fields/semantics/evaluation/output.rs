//! Original computed source values -> complete preserving HWPX result candidate.
//! Not native recalculation, full field policy, issuer, atomic commit or publication authority.
mod readback;
use super::ImportedSourceFormulaEvaluation;
use crate::document_import::forms::VerifiedFormReconstruction;
use crate::document_import::structure::review::cell_body_output::require_no_observed_mutation_protection;
use crate::{
    BoundedZipReader, IdIndexLimits, IdRuleProfile, PackageArtifact, PackageGraphLimits,
    PatchIntent, PatchLimits, PatchText, PreservationRuleProfile, PreservingPatchEngine,
    PreservingWriter, WriterError, WriterLimits, XmlElementSelector,
};
use domain_ir::{FormulaCache, FormulaValue};
use serde::Serialize;
use std::{collections::BTreeSet, fmt, io::Cursor};
use thiserror::Error;

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum FormulaResultAuthority {
    Unqualified,
}
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct FormulaResultOutputReceipt {
    pub qualification: &'static str,
    pub source_package_sha256: [u8; 32],
    pub output_package_sha256: [u8; 32],
    pub evaluated_values_sha256: [u8; 32],
    pub formula_targets: usize,
    pub changed_formula_results: usize,
    pub changed_parts: usize,
    pub changed_leaves: usize,
    pub outside_result_leaf_edits_exact: bool,
    pub formula_ast_and_numeric_inputs_preserved: bool,
    pub native_recalculation_verified: bool,
    pub execution_publication_authority: FormulaResultAuthority,
}
pub struct FormulaResultOutput {
    artifact: PackageArtifact,
    receipt: FormulaResultOutputReceipt,
}
impl fmt::Debug for FormulaResultOutput {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("FormulaResultOutput(<redacted>)")
    }
}
impl FormulaResultOutput {
    #[must_use]
    pub const fn receipt(&self) -> &FormulaResultOutputReceipt {
        &self.receipt
    }
    /// Integrity only, never original service access or execution permission.
    /// # Errors
    /// Rejects artifact integrity failure before invoking the callback.
    pub fn with_verified_bytes<T>(
        &self,
        consume: impl FnOnce(&[u8]) -> T,
    ) -> Result<T, WriterError> {
        self.artifact.with_verified_bytes(consume)
    }
}
pub(super) struct LeafEdit {
    pub part: String,
    pub start: usize,
    pub end: usize,
    pub value: String,
    pub empty_name: Option<String>,
}
impl ImportedSourceFormulaEvaluation<'_, '_, '_> {
    /// Update ALL admitted source formula results from the original evaluator, not caller values.
    /// Command/LastResult/visible text change together; ASTs, inputs and all other bytes stay exact.
    /// Original caches remain unverified data, including the output's computed cache.
    /// # Errors
    /// Rejects stale source, observed protection, no-op/empty targets, original profile/budgets,
    /// patch/writer failure or whole package/re-import/evaluation readback mismatch.
    pub fn lower_results(
        &self,
        fresh: &[u8],
        limits: WriterLimits,
    ) -> Result<FormulaResultOutput, FormulaResultOutputError> {
        let reconstruction = self
            .meanings
            .fields
            .forms
            .reconstruct_source_for_verification(fresh)
            .map_err(|_| FormulaResultOutputError::Source)?;
        self.lower_results_reconstruction(&reconstruction, limits)
    }

    /// Uses only the exact original-bound reconstruction's immutable source bytes.
    /// No separate caller bytes, values, graph or cross-operation authorization.
    /// Full before/after meanings/math checks, protection, patch/writer and entire
    /// candidate readback remain mandatory; source/forms parsing is shared only.
    /// # Errors
    /// Rejects foreign source and every original lowering/protection/readback error.
    pub fn lower_results_reconstruction(
        &self,
        reconstruction: &VerifiedFormReconstruction<'_>,
        limits: WriterLimits,
    ) -> Result<FormulaResultOutput, FormulaResultOutputError> {
        #[cfg(test)]
        let mut timer = stage_profile::Timer::new();
        let forms = reconstruction
            .for_original(self.meanings.fields.forms)
            .map_err(|_| FormulaResultOutputError::Source)?;
        let fresh = forms.source().original.as_ref();
        self.verify_reconstruction(reconstruction)
            .map_err(|_| FormulaResultOutputError::Source)?;
        #[cfg(test)]
        timer.record("bind_and_pre_verify");
        if self.values.is_empty() {
            return Err(FormulaResultOutputError::NoTargets);
        }
        if self
            .values
            .len()
            .checked_mul(3)
            .is_none_or(|n| n > PatchLimits::default().config().max_intents)
        {
            return Err(FormulaResultOutputError::Limit);
        }
        let (intents, edits, changed) = self.result_edits()?;
        #[cfg(test)]
        timer.record("edits_and_protection");
        if changed == 0 {
            return Err(FormulaResultOutputError::NoChange);
        }
        let source = self.meanings.fields.forms.source();
        let zip = source
            .limits
            .zip()
            .map_err(|_| FormulaResultOutputError::Source)?;
        let mut reader = BoundedZipReader::open(Cursor::new(fresh), zip)
            .map_err(|_| FormulaResultOutputError::Source)?;
        let patch = PreservingPatchEngine::apply_with_limits_and_preservation_profile(
            &mut reader,
            &source.graph,
            PackageGraphLimits::default(),
            IdRuleProfile::current_hancom_2020_formula_v3(),
            IdIndexLimits::default(),
            PatchLimits::default(),
            PreservationRuleProfile::Hangul2020PreviewTextV2,
            &intents,
        )
        .map_err(|_| FormulaResultOutputError::Patch)?;
        #[cfg(test)]
        timer.record("preserving_patch");
        let parts: BTreeSet<_> = edits.iter().map(|e| &e.part).collect();
        if patch.changed_parts() != parts.len()
            || patch.added_parts() != 0
            || patch.parts().iter().any(|p| {
                !parts.contains(&p.path().as_str().to_owned())
                    && p.source_sha256() != Some(p.output_sha256())
            })
        {
            return Err(FormulaResultOutputError::Preservation);
        }
        #[cfg(test)]
        timer.record("patch_preservation_checks");
        let artifact = PreservingWriter::build(
            &patch,
            zip,
            PackageGraphLimits::default(),
            IdIndexLimits::default(),
            limits,
        )
        .map_err(|_| FormulaResultOutputError::Writer)?;
        #[cfg(test)]
        timer.record("preserving_writer_build");
        artifact
            .with_verified_bytes(|bytes| readback::verify(self, bytes, &edits))
            .map_err(|_| FormulaResultOutputError::Writer)??;
        #[cfg(test)]
        timer.record("artifact_verify_and_full_candidate_readback");
        self.verify_reconstruction(reconstruction)
            .map_err(|_| FormulaResultOutputError::Source)?;
        #[cfg(test)]
        timer.record("post_source_verify");
        Ok(FormulaResultOutput {
            receipt: FormulaResultOutputReceipt {
                qualification: "original_source_math_all_admitted_formula_result_candidate_NOT_native_recalculation_full_field_policy_issuer_atomic_commit_execution_publication_or_Gate",
                source_package_sha256: self.receipt.source_package_sha256,
                output_package_sha256: artifact.sha256(),
                evaluated_values_sha256: self.receipt.values_and_source_bindings_sha256,
                formula_targets: self.values.len(),
                changed_formula_results: changed,
                changed_parts: parts.len(),
                changed_leaves: edits.len(),
                outside_result_leaf_edits_exact: true,
                formula_ast_and_numeric_inputs_preserved: true,
                native_recalculation_verified: false,
                execution_publication_authority: FormulaResultAuthority::Unqualified,
            },
            artifact,
        })
    }
    fn result_edits(
        &self,
    ) -> Result<(Vec<PatchIntent>, Vec<LeafEdit>, usize), FormulaResultOutputError> {
        let source = self.meanings.fields.forms.source();
        let mut intents = Vec::new();
        let mut edits = Vec::new();
        let mut changed = 0;
        for value in &self.values {
            let resolved = source
                .resolve_anchor(&value.begin_anchor)
                .map_err(|_| FormulaResultOutputError::Selection)?;
            let xml = resolved
                .part()
                .xml()
                .ok_or(FormulaResultOutputError::Selection)?;
            let index = resolved
                .element_index()
                .ok_or(FormulaResultOutputError::Selection)?;
            // Reuse the original whole ancestor guard; absent flags are NOT inferred permission.
            require_no_observed_mutation_protection(xml, index)
                .map_err(|_| FormulaResultOutputError::Protection)?;
            let (_, original) = crate::table_formula::read_imported_field(xml, index)
                .map_err(|_| FormulaResultOutputError::Selection)?;
            if matches!(original.cache(), FormulaCache::Unverified { value: FormulaValue::Decimal { value: cached } } if cached == &value.value)
            {
                continue;
            }
            let targets = crate::table_formula::result_output::targets(xml, index, value.value)
                .map_err(|_| FormulaResultOutputError::Selection)?;
            for (index, value) in targets.indices.into_iter().zip(targets.values) {
                let node = &xml.elements()[index];
                let span = node
                    .content_span()
                    .ok_or(FormulaResultOutputError::Selection)?;
                let (start, end, empty_name) = if node.is_empty() {
                    let tag = node.start_tag_span();
                    let name = node.start_name_span();
                    (
                        tag.end() - 2,
                        tag.end(),
                        Some(
                            xml.with_source_bytes(|raw| {
                                String::from_utf8(raw[name.start()..name.end()].to_vec())
                            })
                            .map_err(|_| FormulaResultOutputError::Selection)?,
                        ),
                    )
                } else {
                    (span.start(), span.end(), None)
                };
                edits.push(LeafEdit {
                    part: resolved.part().path().as_str().into(),
                    start,
                    end,
                    value: value.clone(),
                    empty_name,
                });
                intents.push(PatchIntent::ReplaceLeafText {
                    target: XmlElementSelector::bind(resolved.part().path(), xml, index)
                        .map_err(|_| FormulaResultOutputError::Selection)?,
                    value: PatchText::new(&value).map_err(|_| FormulaResultOutputError::Limit)?,
                });
            }
            changed += 1;
        }
        Ok((intents, edits, changed))
    }
}

// Private test-only observation. No product API, callback, receipt change or cache.
#[cfg(test)]
#[path = "../../../../../tests/support/document_import_settings_inputs.rs"]
mod output_profile_inputs;

#[cfg(test)]
mod stage_profile {
    use super::*;
    use crate::document_import::fields::{
        ImportedDocumentFields, semantics::ImportedDocumentFieldSemantics,
    };
    use crate::document_import::forms::ImportedDocumentForms;
    use crate::document_import::{ImportedSourcePackage, SourceImportLimits};
    use domain_ir::DocumentId;
    use sha2::{Digest as _, Sha256};
    use std::{cell::RefCell, collections::BTreeMap, error::Error, io::Write, time::Instant};
    use zip::{CompressionMethod, ZipWriter, write::SimpleFileOptions};

    #[derive(Default, serde::Serialize)]
    struct Timing {
        calls: usize,
        total_us: u128,
        min_us: u128,
        max_us: u128,
    }
    impl Timing {
        fn record(&mut self, micros: u128) {
            self.min_us = if self.calls == 0 {
                micros
            } else {
                self.min_us.min(micros)
            };
            self.max_us = self.max_us.max(micros);
            self.total_us += micros;
            self.calls += 1;
        }
    }
    thread_local! {
        static COLLECTION: RefCell<Option<BTreeMap<&'static str, Timing>>> = const { RefCell::new(None) };
    }
    struct Capture;
    impl Capture {
        fn new() -> Self {
            COLLECTION.with(|cell| assert!(cell.replace(Some(BTreeMap::new())).is_none()));
            Self
        }
        fn finish(self) -> BTreeMap<&'static str, Timing> {
            COLLECTION.with(|cell| cell.borrow_mut().take().unwrap())
        }
    }
    impl Drop for Capture {
        fn drop(&mut self) {
            COLLECTION.with(|cell| {
                cell.borrow_mut().take();
            });
        }
    }
    pub(super) struct Timer {
        tick: Option<Instant>,
    }
    impl Timer {
        pub(super) fn new() -> Self {
            Self {
                tick: COLLECTION.with(|cell| cell.borrow().is_some().then(Instant::now)),
            }
        }
        pub(super) fn record(&mut self, stage: &'static str) {
            if let Some(tick) = self.tick {
                record(stage, tick.elapsed().as_micros());
                self.tick = Some(Instant::now());
            }
        }
    }
    fn record(stage: &'static str, micros: u128) {
        COLLECTION.with(|cell| {
            cell.borrow_mut()
                .as_mut()
                .unwrap()
                .entry(stage)
                .or_default()
                .record(micros);
        });
    }
    fn forms(bytes: &[u8]) -> Result<ImportedDocumentForms, Box<dyn Error>> {
        Ok(ImportedDocumentForms::import(
            ImportedSourcePackage::import(
                bytes,
                DocumentId::parse("output-stage-diagnostic")?,
                Sha256::digest(bytes).into(),
                SourceImportLimits::default(),
            )?,
        )?)
    }
    fn changed_first_numeric_cell(bytes: &[u8]) -> Result<Vec<u8>, Box<dyn Error>> {
        let mut reader =
            BoundedZipReader::open(Cursor::new(bytes), crate::PackageLimits::default())?;
        let paths: Vec<_> = reader
            .entries()
            .iter()
            .map(|e| e.path.as_str().to_owned())
            .collect();
        let section = paths
            .iter()
            .position(|p| p == "Contents/section0.xml")
            .ok_or("section")?;
        let raw = reader.read_entry(section)?;
        let text = std::str::from_utf8(&raw)?;
        let xml = crate::PreservingXmlDocument::parse(&raw)?;
        let cell = xml
            .elements()
            .iter()
            .find(|e| {
                e.name().local_name() == "tc"
                    && e.name().namespace() == Some("http://www.hancom.co.kr/hwpml/2011/paragraph")
            })
            .ok_or("source cell")?
            .outer_span()
            .ok_or("cell span")?;
        let original = &text[cell.start()..cell.end()];
        let begin = original.find("<hp:t>").ok_or("numeric leaf")? + "<hp:t>".len();
        let end = begin
            + original[begin..]
                .find("</hp:t>")
                .ok_or("numeric leaf end")?;
        let mut next = text.to_owned();
        next.replace_range(cell.start() + begin..cell.start() + end, "900001");
        if next == text {
            return Err("numeric derivative unchanged".into());
        }
        let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
        for (index, path) in paths.iter().enumerate() {
            let old = reader.read_entry(index)?;
            writer.start_file(
                path,
                SimpleFileOptions::default().compression_method(CompressionMethod::Stored),
            )?;
            writer.write_all(if index == section {
                next.as_bytes()
            } else {
                &old
            })?;
        }
        Ok(writer.finish()?.into_inner())
    }

    #[test]
    fn actual36_and_changed16_profile_complete_original_lowering_stages()
    -> Result<(), Box<dyn Error>> {
        let mut counts = (0, 0, 0, 0, 0);
        let mut outputs = (0, 0);
        let mut aggregate: BTreeMap<&'static str, Timing> = BTreeMap::new();
        for original in super::output_profile_inputs::actual_corpus()? {
            let original_sha = Sha256::digest(&original);
            let original_forms = forms(&original)?;
            let fields = ImportedDocumentFields::import(&original_forms)?;
            let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
            let before = meanings.graph().clone();
            let evaluated = ImportedSourceFormulaEvaluation::import(&meanings)?;
            let absent = evaluated.values().is_empty();
            let result = evaluated.lower_results(&original, WriterLimits::default());
            assert!(matches!(
                (&result, absent),
                (Err(FormulaResultOutputError::NoTargets), true)
                    | (Err(FormulaResultOutputError::NoChange), false)
            ));
            assert_eq!(&before, meanings.graph());
            counts.0 += 1;
            if absent {
                counts.1 += 1;
                continue;
            }
            let changed = changed_first_numeric_cell(&original)?;
            assert_ne!(Sha256::digest(&changed), original_sha);
            let changed_forms = forms(&changed)?;
            let fields = ImportedDocumentFields::import(&changed_forms)?;
            let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
            let before = meanings.graph().clone();
            let evaluated = ImportedSourceFormulaEvaluation::import(&meanings)?;
            let values = evaluated.values().to_vec();
            let bindings = evaluated.source_bindings().to_vec();
            let capture = Capture::new();
            let tick = Instant::now();
            let reconstructed = changed_forms.reconstruct_source_for_verification(&changed)?;
            record("fresh_source_reconstruction", tick.elapsed().as_micros());
            let result =
                evaluated.lower_results_reconstruction(&reconstructed, WriterLimits::default());
            let expected_stages = match result {
                Ok(output) => {
                    let tick = Instant::now();
                    let candidate = output.with_verified_bytes(<[u8]>::to_vec)?;
                    record("export_verified_candidate", tick.elapsed().as_micros());
                    let receipt = output.receipt();
                    assert_eq!(receipt.formula_targets, values.len());
                    assert_eq!(receipt.changed_formula_results, values.len());
                    assert_eq!(receipt.changed_leaves, values.len() * 3);
                    assert!(
                        receipt.outside_result_leaf_edits_exact
                            && receipt.formula_ast_and_numeric_inputs_preserved
                    );
                    assert!(!receipt.native_recalculation_verified);
                    assert_eq!(
                        receipt.execution_publication_authority,
                        FormulaResultAuthority::Unqualified
                    );
                    assert_eq!(
                        <[u8; 32]>::from(Sha256::digest(&candidate)),
                        receipt.output_package_sha256
                    );
                    assert_ne!(candidate, changed);
                    outputs.0 += 1;
                    9
                }
                Err(FormulaResultOutputError::NoChange) => {
                    // A changed numeric leaf can be outside the formula dependency.
                    // Keep the original no-op denial and prove exact caches; never
                    // force another mutation merely to manufacture a candidate.
                    for value in &values {
                        let meaning = meanings
                            .observations()
                            .iter()
                            .find(|m| m.reference_id == value.reference_id)
                            .ok_or("meaning")?;
                        let crate::document_import::fields::semantics::ImportedFieldMeaning::TableFormula { formula, .. } = &meaning.meaning else { return Err("formula".into()); };
                        assert!(
                            matches!(formula.cache(), FormulaCache::Unverified { value: FormulaValue::Decimal { value: cached } } if cached == &value.value)
                        );
                    }
                    let tick = Instant::now();
                    assert_eq!(evaluated.verify_source(&changed)?, *evaluated.receipt());
                    record("noop_fresh_source_verify", tick.elapsed().as_micros());
                    outputs.1 += 1;
                    4
                }
                Err(error) => return Err(error.into()),
            };
            let timings = capture.finish();
            assert_eq!(timings.len(), expected_stages);
            for (name, timing) in timings {
                assert_eq!(timing.calls, 1);
                aggregate.entry(name).or_default().record(timing.total_us);
            }
            assert_eq!(&before, meanings.graph());
            assert_eq!(evaluated.values(), values);
            assert_eq!(evaluated.source_bindings(), bindings);
            assert_eq!(Sha256::digest(&original), original_sha);
            counts.2 += 1;
            counts.3 += values.len();
            counts.4 += bindings.len();
        }
        assert_eq!(counts, (36, 20, 16, 16, 128));
        assert_eq!(outputs.0 + outputs.1, 16);
        assert!(outputs.0 > 0 && outputs.1 > 0);
        assert_eq!(aggregate.len(), 10);
        for (name, timing) in &aggregate {
            let expected = match *name {
                "fresh_source_reconstruction" | "bind_and_pre_verify" | "edits_and_protection" => {
                    16
                }
                "noop_fresh_source_verify" => outputs.1,
                _ => outputs.0,
            };
            assert_eq!(timing.calls, expected);
        }
        assert!(COLLECTION.with(|cell| cell.borrow().is_none()));
        println!(
            "P149_OUTPUT_STAGE_PROFILE={}",
            serde_json::json!({
                "schema_version": "hwpx-agent.p09-output-stage-timing/v1",
                "qualification": "TEST_ONLY_PURE_OUTPUT_PROFILE_NOT_SIGNED_SQL_NATIVE_OR_GATE",
                "original_inputs": 36, "original_no_targets": 20, "original_no_changes": 16,
                "changed_inputs": 16, "formula_targets": 16, "source_cell_bindings": 128,
                "lowered_candidates": outputs.0, "mathematically_unchanged": outputs.1,
                "unchanged_original_graphs": 36, "unchanged_changed_source_graphs": 16,
                "stages": aggregate, "native_or_SQL_qualified": false,
                "product_complete": false, "P09_gate": "OPEN"
            })
        );
        Ok(())
    }
}
#[derive(Debug, Error, Eq, PartialEq)]
pub enum FormulaResultOutputError {
    #[error("formula_result_original_source_rejected")]
    Source,
    #[error("formula_result_original_selection_rejected")]
    Selection,
    #[error("formula_result_observed_protection_rejected")]
    Protection,
    #[error("formula_result_no_targets")]
    NoTargets,
    #[error("formula_result_no_change")]
    NoChange,
    #[error("formula_result_limit")]
    Limit,
    #[error("formula_result_patch_rejected")]
    Patch,
    #[error("formula_result_writer_rejected")]
    Writer,
    #[error("formula_result_preservation_rejected")]
    Preservation,
    #[error("formula_result_readback_rejected")]
    Readback,
}
