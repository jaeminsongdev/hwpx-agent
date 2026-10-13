//! All source-backed table-formula targets evaluated without replacing their native caches.
mod source;
use super::{FieldSemanticImportError, ImportedDocumentFieldSemantics, ImportedFieldMeaning};
use domain_ir::formula_evaluation::{EvaluationError, EvaluationReceipt};
use domain_ir::{CellCoordinate, FormulaDecimal, LogicalId, SourceAnchorHandle};
use serde::Serialize;
use std::fmt;
use thiserror::Error;

pub const SOURCE_FORMULA_EVALUATION_PROFILE: &str =
    "hwpx-agent.source-formula-evaluation/partial-v1";
pub const SOURCE_FORMULA_EVALUATION_SCOPE: &str = "actual_source_canonical_decimal_text_and_original_ast_exact_math_not_native_coercion_cache_approval_or_execution";

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct SourceFormulaValue {
    pub reference_id: LogicalId,
    pub table_id: LogicalId,
    pub cell_id: LogicalId,
    pub coordinate: CellCoordinate,
    pub begin_anchor: SourceAnchorHandle,
    pub value: FormulaDecimal,
}
impl fmt::Debug for SourceFormulaValue {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("SourceFormulaValue(<redacted>)")
    }
}
#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct SourceFormulaCellBinding {
    pub table_id: LogicalId,
    pub cell_id: LogicalId,
    pub coordinate: CellCoordinate,
    pub source_anchor: SourceAnchorHandle,
    pub interpretation: &'static str,
}
impl fmt::Debug for SourceFormulaCellBinding {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("SourceFormulaCellBinding(<redacted>)")
    }
}
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct SourceFormulaEvaluationReceipt {
    pub profile: &'static str,
    pub qualification: &'static str,
    pub source_package_sha256: [u8; 32],
    pub original_meaning_graph_sha256: [u8; 32],
    pub values_and_source_bindings_sha256: [u8; 32],
    pub formula_targets: usize,
    pub evaluated_tables: usize,
    pub source_cell_bindings: usize,
    pub canonical_numeric_cells: usize,
    pub unavailable_cells: usize,
    pub non_formula_meanings_not_evaluated: usize,
    pub tables: Vec<EvaluationReceipt>,
}
pub struct ImportedSourceFormulaEvaluation<'a, 'fields, 'source> {
    meanings: &'a ImportedDocumentFieldSemantics<'fields, 'source>,
    values: Vec<SourceFormulaValue>,
    bindings: Vec<SourceFormulaCellBinding>,
    receipt: SourceFormulaEvaluationReceipt,
}
impl fmt::Debug for ImportedSourceFormulaEvaluation<'_, '_, '_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ImportedSourceFormulaEvaluation(<redacted>)")
    }
}
impl<'a, 'fields, 'source> ImportedSourceFormulaEvaluation<'a, 'fields, 'source> {
    /// All actual source FORMULA meanings, original table/owner/AST and source-derived inputs.
    /// # Errors
    /// Rejects ambiguous source ownership, missing numeric dependencies or exact math/budget errors.
    pub fn import(
        meanings: &'a ImportedDocumentFieldSemantics<'fields, 'source>,
    ) -> Result<Self, SourceFormulaEvaluationError> {
        let (values, bindings, tables) = source::evaluate(meanings)?;
        let receipt = SourceFormulaEvaluationReceipt {
            profile: SOURCE_FORMULA_EVALUATION_PROFILE,
            qualification: SOURCE_FORMULA_EVALUATION_SCOPE,
            source_package_sha256: meanings.receipt().source_package_sha256,
            original_meaning_graph_sha256: meanings.receipt().graph_sha256,
            values_and_source_bindings_sha256: source::digest(&values, &bindings)?,
            formula_targets: values.len(),
            evaluated_tables: tables.len(),
            source_cell_bindings: bindings.len(),
            canonical_numeric_cells: bindings
                .iter()
                .filter(|b| b.interpretation == "observed_canonical_decimal_text")
                .count(),
            unavailable_cells: bindings
                .iter()
                .filter(|b| b.interpretation == "unavailable_not_defaulted")
                .count(),
            non_formula_meanings_not_evaluated: meanings
                .observations()
                .iter()
                .filter(|m| !matches!(m.meaning, ImportedFieldMeaning::TableFormula { .. }))
                .count(),
            tables,
        };
        Ok(Self {
            meanings,
            values,
            bindings,
            receipt,
        })
    }
    #[must_use]
    pub fn values(&self) -> &[SourceFormulaValue] {
        &self.values
    }
    #[must_use]
    pub fn source_bindings(&self) -> &[SourceFormulaCellBinding] {
        &self.bindings
    }
    #[must_use]
    pub const fn receipt(&self) -> &SourceFormulaEvaluationReceipt {
        &self.receipt
    }
    /// Original fresh whole-source/meaning checks, then deterministic source-value reconstruction.
    /// # Errors
    /// Rejects whole source/meaning/numeric binding/value/receipt drift; caches remain unchanged.
    pub fn verify_source(
        &self,
        fresh: &[u8],
    ) -> Result<SourceFormulaEvaluationReceipt, SourceFormulaEvaluationError> {
        self.meanings.verify_source(fresh)?;
        let rebuilt = Self::import(self.meanings)?;
        if self.values != rebuilt.values
            || self.bindings != rebuilt.bindings
            || self.receipt != rebuilt.receipt
        {
            return Err(SourceFormulaEvaluationError::Binding);
        }
        Ok(self.receipt.clone())
    }
}
#[derive(Debug, Error)]
pub enum SourceFormulaEvaluationError {
    #[error("source formula original fresh meanings rejected")]
    Meanings(#[from] FieldSemanticImportError),
    #[error("source formula original cell/text/grid/field binding rejected")]
    Binding,
    #[error("source formula whole source work/serialization budget exceeded")]
    Limit,
    #[error("source formula exact numeric evaluation rejected")]
    Math(#[from] EvaluationError),
}
