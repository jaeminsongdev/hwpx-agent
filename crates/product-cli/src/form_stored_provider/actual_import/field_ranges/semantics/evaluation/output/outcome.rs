//! Exact original no-change outcome is a mathematical no-op, not an empty compiler plan.
use super::{
    PreparedStoredFormulaResults, StoredFormulaOutputError as Error, StoredSourceFormulaEvaluation,
};
use crate::form_stored_provider::StoredFormProvider;
use artifact_service::{ArtifactMetadataRepository, ArtifactScanner, EncryptedBlobStore};
use hwpx_package::{
    WriterLimits, document_import::fields::semantics::evaluation::output::FormulaResultOutputError,
};
use revision_service::RevisionRepository;
use serde::Serialize;

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct UnchangedFormulaReceipt {
    pub source_package_sha256: [u8; 32],
    pub evaluated_values_sha256: [u8; 32],
    pub formula_targets: usize,
    pub original_lowerer_no_change_and_protection_checks_verified: bool,
    pub native_recalculation_verified: bool,
    pub execution_publication_authority: &'static str,
}
#[derive(Debug)]
pub enum StoredFormulaOutcome<'a, 'meanings, 'fields, 'source> {
    Changed(Box<PreparedStoredFormulaResults<'a, 'meanings, 'fields, 'source>>),
    Unchanged(PreparedUnchangedFormulaResults<'a, 'meanings, 'fields, 'source>),
}
pub struct PreparedUnchangedFormulaResults<'a, 'meanings, 'fields, 'source> {
    evaluation: &'a StoredSourceFormulaEvaluation<'meanings, 'fields, 'source>,
    limits: WriterLimits,
    receipt: UnchangedFormulaReceipt,
}
impl std::fmt::Debug for PreparedUnchangedFormulaResults<'_, '_, '_, '_> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str("PreparedUnchangedFormulaResults(<redacted>)")
    }
}
impl<'meanings, 'fields, 'source> StoredSourceFormulaEvaluation<'meanings, 'fields, 'source> {
    /// Distinguishes only the original lowerer's exact no-change outcome after all protection checks.
    /// # Errors
    /// Rejects every other lowering failure; no empty targets/invalid numeric/protected source becomes a no-op.
    pub fn prepare_results_outcome<'a, R, B, S, V>(
        &'a self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        limits: WriterLimits,
        now: u64,
    ) -> Result<StoredFormulaOutcome<'a, 'meanings, 'fields, 'source>, Error>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.verify(provider, now).map_err(|_| Error::Source)?;
        let (_fresh, reconstruction) = self
            .meanings
            .ranges
            .source
            .fresh_source_reconstructed(provider, now)
            .map_err(|_| Error::Source)?;
        let output = self
            .evaluated
            .lower_results_reconstruction(&reconstruction, limits);
        self.verify(provider, now).map_err(|_| Error::Source)?;
        match output {
            Ok(output) => Ok(StoredFormulaOutcome::Changed(Box::new(
                PreparedStoredFormulaResults {
                    evaluation: self,
                    limits,
                    output,
                },
            ))),
            Err(FormulaResultOutputError::NoChange) => Ok(StoredFormulaOutcome::Unchanged(
                PreparedUnchangedFormulaResults {
                    evaluation: self,
                    limits,
                    receipt: unchanged_receipt(self),
                },
            )),
            Err(_) => Err(Error::Output),
        }
    }
}
fn unchanged_receipt(
    evaluation: &StoredSourceFormulaEvaluation<'_, '_, '_>,
) -> UnchangedFormulaReceipt {
    UnchangedFormulaReceipt {
        source_package_sha256: evaluation.receipt().evaluation.source_package_sha256,
        evaluated_values_sha256: evaluation
            .receipt()
            .evaluation
            .values_and_source_bindings_sha256,
        formula_targets: evaluation.values().len(),
        original_lowerer_no_change_and_protection_checks_verified: true,
        native_recalculation_verified: false,
        execution_publication_authority: "unqualified",
    }
}
impl PreparedUnchangedFormulaResults<'_, '_, '_, '_> {
    #[must_use]
    pub const fn receipt(&self) -> &UnchangedFormulaReceipt {
        &self.receipt
    }
    /// Fresh original source/math/protection revalidation before exposing unchanged whole source bytes.
    /// # Errors
    /// Rejects scope/ACL/AEAD/head/protection/math drift before callback; never bypasses an output error.
    pub fn with_verified_bytes<R, B, S, V, T>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
        consume: impl FnOnce(&[u8]) -> T,
    ) -> Result<T, Error>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.evaluation
            .verify(provider, now)
            .map_err(|_| Error::Source)?;
        let (fresh, reconstruction) = self
            .evaluation
            .meanings
            .ranges
            .source
            .fresh_source_reconstructed(provider, now)
            .map_err(|_| Error::Source)?;
        if !matches!(
            self.evaluation
                .evaluated
                .lower_results_reconstruction(&reconstruction, self.limits),
            Err(FormulaResultOutputError::NoChange)
        ) {
            return Err(Error::Binding);
        }
        self.evaluation
            .verify(provider, now)
            .map_err(|_| Error::Source)?;
        if unchanged_receipt(self.evaluation) != self.receipt {
            return Err(Error::Binding);
        }
        Ok(consume(&fresh.bytes))
    }
}
