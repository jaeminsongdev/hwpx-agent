//! Original computed source values -> complete preserving HWPX result candidate.
//! Not native recalculation, full field policy, issuer, atomic commit or publication authority.
mod readback;
use super::ImportedSourceFormulaEvaluation;
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
    pub execution_publication_authority: bool,
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
        self.verify_source(fresh)
            .map_err(|_| FormulaResultOutputError::Source)?;
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
        let artifact = PreservingWriter::build(
            &patch,
            zip,
            PackageGraphLimits::default(),
            IdIndexLimits::default(),
            limits,
        )
        .map_err(|_| FormulaResultOutputError::Writer)?;
        artifact
            .with_verified_bytes(|bytes| readback::verify(self, bytes, &edits))
            .map_err(|_| FormulaResultOutputError::Writer)??;
        self.verify_source(fresh)
            .map_err(|_| FormulaResultOutputError::Source)?;
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
                execution_publication_authority: false,
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
