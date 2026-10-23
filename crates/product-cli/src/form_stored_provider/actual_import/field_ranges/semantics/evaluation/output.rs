//! Fresh authenticated evaluator -> original preserving formula result candidate.
pub mod compiler;
pub mod outcome;
use super::StoredSourceFormulaEvaluation;
use crate::form_stored_provider::StoredFormProvider;
use artifact_service::{ArtifactMetadataRepository, ArtifactScanner, EncryptedBlobStore};
use hwpx_package::{
    WriterLimits,
    document_import::fields::semantics::evaluation::output::{
        FormulaResultOutput, FormulaResultOutputReceipt,
    },
};
use revision_service::RevisionRepository;
use std::fmt;
use thiserror::Error;

pub struct PreparedStoredFormulaResults<'a, 'meanings, 'fields, 'source> {
    evaluation: &'a StoredSourceFormulaEvaluation<'meanings, 'fields, 'source>,
    limits: WriterLimits,
    output: FormulaResultOutput,
}
impl fmt::Debug for PreparedStoredFormulaResults<'_, '_, '_, '_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("PreparedStoredFormulaResults(<redacted>)")
    }
}
impl<'meanings, 'fields, 'source> StoredSourceFormulaEvaluation<'meanings, 'fields, 'source> {
    /// Source-selected computed results only. No caller result/cache/AST/artifact override.
    /// # Errors
    /// Rejects fresh source/evaluation authorization and original lowering/readback failures.
    pub fn prepare_results<'a, R, B, S, V>(
        &'a self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        limits: WriterLimits,
        now: u64,
    ) -> Result<
        PreparedStoredFormulaResults<'a, 'meanings, 'fields, 'source>,
        StoredFormulaOutputError,
    >
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.verify(provider, now)
            .map_err(|_| StoredFormulaOutputError::Source)?;
        let (_fresh, reconstruction) = self
            .meanings
            .ranges
            .source
            .fresh_source_reconstructed(provider, now)
            .map_err(|_| StoredFormulaOutputError::Source)?;
        let output = self
            .evaluated
            .lower_results_reconstruction(&reconstruction, limits)
            .map_err(|_| StoredFormulaOutputError::Output)?;
        self.verify(provider, now)
            .map_err(|_| StoredFormulaOutputError::Source)?;
        Ok(PreparedStoredFormulaResults {
            evaluation: self,
            limits,
            output,
        })
    }
}
impl PreparedStoredFormulaResults<'_, '_, '_, '_> {
    #[must_use]
    pub const fn receipt(&self) -> &FormulaResultOutputReceipt {
        self.output.receipt()
    }
    /// Replays original source ACL/AEAD/scope/head and complete evaluator/output binding.
    /// Repeated reads are not a held lease or atomic publication capability.
    /// # Errors
    /// Rejects fresh access/source/math/output/receipt drift.
    pub fn verify<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<FormulaResultOutputReceipt, StoredFormulaOutputError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.evaluation
            .verify(provider, now)
            .map_err(|_| StoredFormulaOutputError::Source)?;
        let (_fresh, reconstruction) = self
            .evaluation
            .meanings
            .ranges
            .source
            .fresh_source_reconstructed(provider, now)
            .map_err(|_| StoredFormulaOutputError::Source)?;
        let output = self
            .evaluation
            .evaluated
            .lower_results_reconstruction(&reconstruction, self.limits)
            .map_err(|_| StoredFormulaOutputError::Output)?;
        self.evaluation
            .verify(provider, now)
            .map_err(|_| StoredFormulaOutputError::Source)?;
        if output.receipt() != self.output.receipt() {
            return Err(StoredFormulaOutputError::Binding);
        }
        self.output
            .with_verified_bytes(|_| ())
            .map_err(|_| StoredFormulaOutputError::Output)?;
        Ok(self.output.receipt().clone())
    }
    /// Never invokes the callback after a failed fresh service check; no ingest or head write.
    /// # Errors
    /// Rejects source/output failures. Candidate bytes are not execution authorization.
    pub fn with_verified_bytes<R, B, S, V, T>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
        consume: impl FnOnce(&[u8]) -> T,
    ) -> Result<T, StoredFormulaOutputError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.verify(provider, now)?;
        self.output
            .with_verified_bytes(consume)
            .map_err(|_| StoredFormulaOutputError::Output)
    }
    /// A mathematical candidate does not establish native policy/issuer/atomic execution.
    /// # Errors
    /// Always denies after original fresh verification, or returns that earlier failure.
    pub fn require_current_product_route<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<(), StoredFormulaOutputError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.verify(provider, now)?;
        Err(StoredFormulaOutputError::RouteUnqualified)
    }
}
#[derive(Debug, Error, Eq, PartialEq)]
pub enum StoredFormulaOutputError {
    #[error("stored_formula_result_original_source_rejected")]
    Source,
    #[error("stored_formula_result_output_rejected")]
    Output,
    #[error("stored_formula_result_binding_rejected")]
    Binding,
    #[error("stored_formula_result_route_unqualified")]
    RouteUnqualified,
}
