//! Fresh authenticated actual numeric source evaluation, no cache mutation or execution capability.
use super::{
    StoredFieldSemanticImportError, StoredFieldSemanticImportReceipt, StoredImportedFieldSemantics,
};
use crate::form_stored_provider::{StoredFormProvider, actual_import::StoredActualFormImportError};
use artifact_service::{ArtifactMetadataRepository, ArtifactScanner, EncryptedBlobStore};
use hwpx_package::document_import::fields::semantics::evaluation::{
    ImportedSourceFormulaEvaluation, SourceFormulaCellBinding, SourceFormulaEvaluationError,
    SourceFormulaEvaluationReceipt, SourceFormulaValue,
};
use revision_service::RevisionRepository;
use serde::Serialize;
use std::fmt;
use thiserror::Error;
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct StoredFormulaEvaluationReceipt {
    pub source: StoredFieldSemanticImportReceipt,
    pub evaluation: SourceFormulaEvaluationReceipt,
    pub qualification: &'static str,
}
pub struct StoredSourceFormulaEvaluation<'a, 'fields, 'source> {
    meanings: &'a StoredImportedFieldSemantics<'fields, 'source>,
    evaluated: ImportedSourceFormulaEvaluation<'a, 'fields, 'source>,
    receipt: StoredFormulaEvaluationReceipt,
}
impl fmt::Debug for StoredSourceFormulaEvaluation<'_, '_, '_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("StoredSourceFormulaEvaluation(<redacted>)")
    }
}
impl<'fields, 'source> StoredImportedFieldSemantics<'fields, 'source> {
    /// Whole original source/meaning authorization before, exact original source checkpoint after.
    /// # Errors
    /// Rejects stale/revoked/AEAD/scope source, numeric binding/dependency/math failures.
    pub fn evaluate_table_formulas<'a, R, B, S, V>(
        &'a self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<StoredSourceFormulaEvaluation<'a, 'fields, 'source>, StoredFormulaEvaluationError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        let source = self.verify(provider, now)?;
        let evaluated = ImportedSourceFormulaEvaluation::import(&self.imported)?;
        self.ranges.source.verify(provider, now)?;
        let receipt = StoredFormulaEvaluationReceipt {
            source,
            evaluation: evaluated.receipt().clone(),
            qualification: "fresh_authenticated_actual_numeric_source_exact_math_not_native_cache_policy_issuer_persistence_publication_or_execution",
        };
        Ok(StoredSourceFormulaEvaluation {
            meanings: self,
            evaluated,
            receipt,
        })
    }
}
impl StoredSourceFormulaEvaluation<'_, '_, '_> {
    #[must_use]
    pub fn values(&self) -> &[SourceFormulaValue] {
        self.evaluated.values()
    }
    #[must_use]
    pub fn source_bindings(&self) -> &[SourceFormulaCellBinding] {
        self.evaluated.source_bindings()
    }
    #[must_use]
    pub const fn receipt(&self) -> &StoredFormulaEvaluationReceipt {
        &self.receipt
    }
    /// Fresh full original authorization and deterministic WHOLE source/value/receipt equality.
    /// # Errors
    /// Rejects access/scope/head/source/numeric/receipt drift before cached values are accepted.
    pub fn verify<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<StoredFormulaEvaluationReceipt, StoredFormulaEvaluationError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        let source = self.meanings.verify(provider, now)?;
        let evaluated = ImportedSourceFormulaEvaluation::import(&self.meanings.imported)?;
        self.meanings.ranges.source.verify(provider, now)?;
        if self.receipt.source != source
            || self.receipt.evaluation != *evaluated.receipt()
            || self.evaluated.values() != evaluated.values()
            || self.evaluated.source_bindings() != evaluated.source_bindings()
        {
            return Err(StoredFormulaEvaluationError::Binding);
        }
        Ok(self.receipt.clone())
    }
}
#[derive(Debug, Error)]
pub enum StoredFormulaEvaluationError {
    #[error("stored evaluation original fresh meanings authorization rejected")]
    Source(#[from] StoredFieldSemanticImportError),
    #[error("stored evaluation original final authenticated source checkpoint rejected")]
    Checkpoint(#[from] StoredActualFormImportError),
    #[error("stored evaluation exact source/numeric mathematical evaluation rejected")]
    Evaluation(#[from] SourceFormulaEvaluationError),
    #[error("stored evaluation whole source/value/receipt drift rejected")]
    Binding,
}
