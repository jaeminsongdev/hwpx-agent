//! Field-policy DATA gating around the original strict product API; not issuer/execution authority.
use super::{StoredProductOperationError, StoredProductRequest, formula, request};
use crate::form_stored_provider::{
    StoredFormProvider,
    actual_import::source_policy::formulas::{
        FormulaPolicyRepository, StoredFormulaPolicy, StoredFormulaPolicyError,
        StoredFormulaPolicyReceipt,
    },
};
use artifact_service::{ArtifactMetadataRepository, ArtifactScanner, EncryptedBlobStore};
use revision_service::RevisionRepository;
use serde::Serialize;
use std::fmt;
use thiserror::Error;
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct PolicyFormulaProductReceipt {
    pub policy: StoredFormulaPolicyReceipt,
    pub product: formula::StoredProductFormulaReceipt,
    pub qualification: &'static str,
}
pub struct PreparedPolicyFormulaProduct {
    policy: StoredFormulaPolicy,
    product: formula::PreparedStoredProductFormula,
    receipt: PolicyFormulaProductReceipt,
}
impl fmt::Debug for PreparedPolicyFormulaProduct {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("PreparedPolicyFormulaProduct(<redacted>)")
    }
}
impl StoredProductRequest {
    /// Validates the original v2 envelope, then fresh repository-selected policy before any math/output.
    /// # Errors
    /// Rejects a v1/wrong operation, source/policy denial, absent/denied targets or original compiler failure.
    pub fn prepare_formula_with_policy<R, B, S, V, P>(
        provider: &StoredFormProvider<'_, R, B, S, V>,
        repository: &P,
        raw: &[u8],
        now: u64,
    ) -> Result<PreparedPolicyFormulaProduct, PolicyFormulaProductError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
        P: FormulaPolicyRepository,
    {
        let request::Kind::TableFormulas(request) = request::classify(raw)? else {
            return Err(PolicyFormulaProductError::Kind);
        };
        request.check(provider, now)?;
        let source = provider
            .import_actual_forms(request.head()?, now)
            .map_err(StoredProductOperationError::from)?;
        let policy = source.bind_stored_formula_policy(provider, repository, now)?;
        policy.require_recalculation_data_permission()?;
        let product = formula::prepare_from_source(provider, request, raw, source, now)?;
        policy.verify(product.source(), provider, repository, now)?;
        policy.require_recalculation_data_permission()?;
        let receipt = PolicyFormulaProductReceipt {
            policy: policy.receipt().clone(),
            product: product.receipt().clone(),
            qualification: "fresh_repository_selected_exact_source_formula_policy_data_and_original_product_NOT_trusted_issuer_full_import_SQL_transport_atomic_execution_native_or_Gate",
        };
        Ok(PreparedPolicyFormulaProduct {
            policy,
            product,
            receipt,
        })
    }
}
impl PreparedPolicyFormulaProduct {
    #[must_use]
    pub const fn receipt(&self) -> &PolicyFormulaProductReceipt {
        &self.receipt
    }
    /// Fresh policy before and after original source/math/compiler/candidate checks.
    /// # Errors
    /// Rejects latest/revocation/ACL/AEAD/head/scope/whole policy-product drift; no held lease.
    pub fn verify<R, B, S, V, P>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        repository: &P,
        now: u64,
    ) -> Result<PolicyFormulaProductReceipt, PolicyFormulaProductError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
        P: FormulaPolicyRepository,
    {
        let before = self
            .policy
            .verify(self.product.source(), provider, repository, now)?;
        self.policy.require_recalculation_data_permission()?;
        let product = self.product.verify(provider, now)?;
        let after = self
            .policy
            .verify(self.product.source(), provider, repository, now)?;
        if before != self.receipt.policy || after != before || product != self.receipt.product {
            return Err(PolicyFormulaProductError::Drift);
        }
        Ok(self.receipt.clone())
    }
    /// Rechecks policy immediately before the caller consumes original freshly verified candidate bytes.
    /// # Errors
    /// Rejects changes before callback; no ingest/head write/idempotency claim/file publication occurs.
    pub fn with_verified_bytes<R, B, S, V, P, T>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        repository: &P,
        now: u64,
        consume: impl FnOnce(&[u8]) -> T,
    ) -> Result<T, PolicyFormulaProductError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
        P: FormulaPolicyRepository,
    {
        self.verify(provider, repository, now)?;
        self.product.with_verified_bytes(provider, now, |bytes| {
            self.policy
                .verify(self.product.source(), provider, repository, now)?;
            self.policy.require_recalculation_data_permission()?;
            Ok(consume(bytes))
        })?
    }
    /// Preserves the unchanged product route denial after fresh policy/product verification.
    /// # Errors
    /// Current native/issuer/atomic execution remains unqualified.
    pub fn require_current_product_route<R, B, S, V, P>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        repository: &P,
        now: u64,
    ) -> Result<(), PolicyFormulaProductError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
        P: FormulaPolicyRepository,
    {
        self.verify(provider, repository, now)?;
        self.product.require_current_product_route(provider, now)?;
        self.policy
            .verify(self.product.source(), provider, repository, now)?;
        Ok(())
    }
}
#[derive(Debug, Error)]
pub enum PolicyFormulaProductError {
    #[error("policy_formula_product_original_request_rejected")]
    Product(#[from] StoredProductOperationError),
    #[error("policy_formula_product_current_policy_denied")]
    Policy(#[from] StoredFormulaPolicyError),
    #[error("policy_formula_product_request_kind_rejected")]
    Kind,
    #[error("policy_formula_product_whole_binding_changed")]
    Drift,
}
