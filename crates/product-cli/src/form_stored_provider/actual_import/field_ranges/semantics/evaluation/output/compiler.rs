//! Stored source math candidate -> unchanged original operation compiler. Not route authority.
mod build;
use super::{PreparedStoredFormulaResults, StoredFormulaOutputError};
use crate::form_stored_provider::StoredFormProvider;
use artifact_service::{ArtifactMetadataRepository, ArtifactScanner, EncryptedBlobStore};
use domain_ir::{CompiledOperationPlan, PlanId};
use hwpx_package::document_import::fields::semantics::evaluation::output::FormulaResultOutputReceipt;
use revision_service::RevisionRepository;
use serde::Serialize;
use std::fmt;
use thiserror::Error;

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct StoredFormulaCompilerReceipt {
    pub qualification: &'static str,
    pub output: FormulaResultOutputReceipt,
    pub compiled_plan_sha256: [u8; 32],
    pub actual_meaning_graph_sha256: [u8; 32],
    pub head_generation: u64,
    pub changed_field_operations: usize,
}
pub struct PreparedStoredFormulaPlan<'a, 'evaluation, 'meanings, 'fields, 'source> {
    results: &'a PreparedStoredFormulaResults<'evaluation, 'meanings, 'fields, 'source>,
    plan: CompiledOperationPlan,
    receipt: StoredFormulaCompilerReceipt,
}
impl fmt::Debug for PreparedStoredFormulaPlan<'_, '_, '_, '_, '_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("PreparedStoredFormulaPlan(<redacted>)")
    }
}
impl<'evaluation, 'meanings, 'fields, 'source>
    PreparedStoredFormulaResults<'evaluation, 'meanings, 'fields, 'source>
{
    /// Uses only actual source fields/results/candidate and sealed current source revision.
    /// `plan_id` is an operation identity, never a supplied result, map, artifact or permission.
    /// # Errors
    /// Rejects fresh access/source/output failures, original compiler limits or binding drift.
    pub fn compile<'a, R, B, S, V>(
        &'a self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        plan_id: PlanId,
        now: u64,
    ) -> Result<
        PreparedStoredFormulaPlan<'a, 'evaluation, 'meanings, 'fields, 'source>,
        StoredFormulaCompilerError,
    >
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.verify(provider, now)?;
        let plan = build::compile(self, plan_id)?;
        let receipt = build::receipt(self, &plan)?;
        self.verify(provider, now)?;
        Ok(PreparedStoredFormulaPlan {
            results: self,
            plan,
            receipt,
        })
    }
}
impl PreparedStoredFormulaPlan<'_, '_, '_, '_, '_> {
    #[must_use]
    pub const fn compiled(&self) -> &CompiledOperationPlan {
        &self.plan
    }
    #[must_use]
    pub const fn receipt(&self) -> &StoredFormulaCompilerReceipt {
        &self.receipt
    }
    /// Reconstructs original compiler output after original ACL/AEAD/head/source/math checks.
    /// Not an atomic policy lease or durable publication.
    /// # Errors
    /// Rejects any source/compiler/receipt/whole plan drift.
    pub fn verify<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<StoredFormulaCompilerReceipt, StoredFormulaCompilerError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.results.verify(provider, now)?;
        let plan = build::compile(self.results, self.plan.plan_id().clone())?;
        let receipt = build::receipt(self.results, &plan)?;
        self.results.verify(provider, now)?;
        if plan != self.plan || receipt != self.receipt {
            return Err(StoredFormulaCompilerError::Binding);
        }
        Ok(receipt)
    }
    /// Fresh verification before releasing the original complete candidate to a consumer.
    /// # Errors
    /// Rejects all binding failures before callback; no ingest, commit or manifest is produced.
    pub fn with_verified_bytes<R, B, S, V, T>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
        consume: impl FnOnce(&[u8]) -> T,
    ) -> Result<T, StoredFormulaCompilerError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.verify(provider, now)?;
        Ok(self.results.with_verified_bytes(provider, now, consume)?)
    }
    /// Preserves the original source result route denial. Compilation is not issuer authority.
    /// # Errors
    /// Denies after fresh verification, or returns the earlier original service failure.
    pub fn require_current_product_route<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<(), StoredFormulaCompilerError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.verify(provider, now)?;
        Ok(self.results.require_current_product_route(provider, now)?)
    }
}
#[derive(Debug, Error, Eq, PartialEq)]
pub enum StoredFormulaCompilerError {
    #[error("stored_formula_compiler_source_rejected")]
    Source(#[from] StoredFormulaOutputError),
    #[error("stored_formula_original_compiler_rejected")]
    Compilation,
    #[error("stored_formula_compiler_binding_rejected")]
    Binding,
}
