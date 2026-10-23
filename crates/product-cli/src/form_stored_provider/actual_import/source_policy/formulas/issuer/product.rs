//! Mandatory issuer signature wrapper around unchanged P116 product/source/math/protection checks.
use super::super::FormulaPolicyRepository;
use super::{
    FormulaApprovalRepository, FormulaIssuerClock, FormulaIssuerError, FormulaIssuerReceipt,
    FormulaIssuerTrustRepository, provider::SignedRepository,
};
use crate::{
    form_product_request::stored_operations::{
        StoredProductRequest,
        policy::{
            PolicyFormulaProductError, PolicyFormulaProductReceipt, PreparedPolicyFormulaProduct,
        },
    },
    form_stored_provider::StoredFormProvider,
};
use artifact_service::{ArtifactMetadataRepository, ArtifactScanner, EncryptedBlobStore};
use revision_service::RevisionRepository;
use serde::Serialize;
use std::fmt;

/// Explicit server dependencies; no default issuer, clock timestamp, public key or approval in request JSON.
pub struct FormulaIssuerDependencies<'a, P, A, T, C> {
    pub(super) policies: &'a P,
    pub(super) approvals: &'a A,
    pub(super) trust: &'a T,
    pub(super) clock: &'a C,
}
impl<'a, P, A, T, C> FormulaIssuerDependencies<'a, P, A, T, C> {
    #[must_use]
    pub const fn new(policies: &'a P, approvals: &'a A, trust: &'a T, clock: &'a C) -> Self {
        Self {
            policies,
            approvals,
            trust,
            clock,
        }
    }
}
impl<P, A, T, C> fmt::Debug for FormulaIssuerDependencies<'_, P, A, T, C> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("FormulaIssuerDependencies(<redacted>)")
    }
}
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct IssuerFormulaProductReceipt {
    pub issuer: FormulaIssuerReceipt,
    pub product: PolicyFormulaProductReceipt,
    pub qualification: &'static str,
}
pub struct PreparedIssuerFormulaProduct {
    product: PreparedPolicyFormulaProduct,
    receipt: IssuerFormulaProductReceipt,
}
impl fmt::Debug for PreparedIssuerFormulaProduct {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("PreparedIssuerFormulaProduct(<redacted>)")
    }
}
impl StoredProductRequest {
    /// Requires fresh signed approval under live trusted server keys BEFORE original formula math/output.
    /// # Errors
    /// Rejects original strict envelope/source/policy/protection, signature/key/time/approval drift. No endpoint is installed.
    pub fn prepare_formula_with_issuer<R, B, S, V, P, A, T, C>(
        provider: &StoredFormProvider<'_, R, B, S, V>,
        deps: &FormulaIssuerDependencies<'_, P, A, T, C>,
        raw: &[u8],
    ) -> Result<PreparedIssuerFormulaProduct, IssuerFormulaProductError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
        P: FormulaPolicyRepository,
        A: FormulaApprovalRepository,
        T: FormulaIssuerTrustRepository,
        C: FormulaIssuerClock,
    {
        let now = deps.clock.now()?;
        let repository = SignedRepository::new(provider, deps);
        let product = Self::prepare_formula_with_policy(provider, &repository, raw, now)?;
        let issuer = repository.receipt()?;
        let receipt = IssuerFormulaProductReceipt {
            issuer,
            product: product.receipt().clone(),
            qualification: "mandatory_live_ed25519_formula_approval_and_original_product_component_NOT_configured_production_issuer_signed_registry_actual_SQL_transport_atomic_execution_native_or_Gate",
        };
        Ok(PreparedIssuerFormulaProduct { product, receipt })
    }
}
impl PreparedIssuerFormulaProduct {
    #[must_use]
    pub const fn receipt(&self) -> &IssuerFormulaProductReceipt {
        &self.receipt
    }
    /// Rebuilds live signature/source/policy checks with the supplied current provider, never cached keys.
    /// # Errors
    /// Rejects trust/key/proof/version/ACL/AEAD/time or original whole product drift.
    pub fn verify<R, B, S, V, P, A, T, C>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        deps: &FormulaIssuerDependencies<'_, P, A, T, C>,
    ) -> Result<IssuerFormulaProductReceipt, IssuerFormulaProductError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
        P: FormulaPolicyRepository,
        A: FormulaApprovalRepository,
        T: FormulaIssuerTrustRepository,
        C: FormulaIssuerClock,
    {
        let repository = SignedRepository::new(provider, deps);
        let product = self
            .product
            .verify(provider, &repository, deps.clock.now()?)?;
        if product != self.receipt.product || repository.receipt()? != self.receipt.issuer {
            return Err(IssuerFormulaProductError::Drift);
        }
        Ok(self.receipt.clone())
    }
    /// Rechecks all live dependencies inside the original fresh candidate callback boundary.
    /// # Errors
    /// Denies before caller callback on signature/source/whole product drift. No lease/publication is asserted.
    pub fn with_verified_bytes<R, B, S, V, P, A, T, C, O>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        deps: &FormulaIssuerDependencies<'_, P, A, T, C>,
        consume: impl FnOnce(&[u8]) -> O,
    ) -> Result<O, IssuerFormulaProductError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
        P: FormulaPolicyRepository,
        A: FormulaApprovalRepository,
        T: FormulaIssuerTrustRepository,
        C: FormulaIssuerClock,
    {
        self.verify(provider, deps)?;
        let repository = SignedRepository::new(provider, deps);
        self.product
            .with_verified_bytes(provider, &repository, deps.clock.now()?, |bytes| {
                if repository.receipt()? != self.receipt.issuer {
                    return Err(IssuerFormulaProductError::Drift);
                }
                Ok(consume(bytes))
            })?
    }
    /// Retains original native/atomic/product route denial even with a valid component signature.
    /// # Errors
    /// Signature evidence does not override current native/full-product qualification.
    pub fn require_current_product_route<R, B, S, V, P, A, T, C>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        deps: &FormulaIssuerDependencies<'_, P, A, T, C>,
    ) -> Result<(), IssuerFormulaProductError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
        P: FormulaPolicyRepository,
        A: FormulaApprovalRepository,
        T: FormulaIssuerTrustRepository,
        C: FormulaIssuerClock,
    {
        self.verify(provider, deps)?;
        let repository = SignedRepository::new(provider, deps);
        self.product
            .require_current_product_route(provider, &repository, deps.clock.now()?)?;
        if repository.receipt()? != self.receipt.issuer {
            return Err(IssuerFormulaProductError::Drift);
        }
        Ok(())
    }
}
#[derive(Debug, thiserror::Error)]
pub enum IssuerFormulaProductError {
    #[error("issuer_formula_product_original_component_denied")]
    Product(#[from] PolicyFormulaProductError),
    #[error("issuer_formula_product_signature_component_denied")]
    Issuer(#[from] FormulaIssuerError),
    #[error("issuer_formula_product_exact_approval_changed")]
    Drift,
}
