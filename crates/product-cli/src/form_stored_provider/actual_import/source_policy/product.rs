//! Repository-selected source policy -> unchanged strict stored product request and compiler.
//! No caller map/policy selector, partial-to-full import promotion, signed route or publication.
use super::{
    SourcePolicyRepository, StoredSourceFormPolicies, StoredSourcePolicyError,
    StoredSourcePolicyReceipt,
};
use crate::{
    form_product_request::stored::{
        PreparedStoredProductForm, StoredProductFormBindings, StoredProductFormError,
        StoredProductFormReceipt, StoredProductFormRequest,
    },
    form_stored_provider::StoredFormProvider,
};
use artifact_service::{ArtifactMetadataRepository, ArtifactScanner, EncryptedBlobStore};
use domain_ir::form_input::FormInputAccessPolicy;
use revision_service::RevisionRepository;
use serde::Serialize;
use std::fmt;
use thiserror::Error;

const PROFILE: &str = "hwpx-agent.stored-source-policy-product-preparation/partial-v1";

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct StoredPolicyProductReceipt {
    pub profile: &'static str,
    pub policy: StoredSourcePolicyReceipt,
    pub product: StoredProductFormReceipt,
    pub qualification: &'static str,
}

/// Immutable in-memory candidate. Cached bytes or receipts never authorize execution.
pub struct PreparedStoredPolicyProduct<'a, 'source> {
    policy: &'a StoredSourceFormPolicies<'source>,
    product: PreparedStoredProductForm,
    receipt: StoredPolicyProductReceipt,
}
impl fmt::Debug for PreparedStoredPolicyProduct<'_, '_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("PreparedStoredPolicyProduct(<redacted>)")
    }
}
impl<'source> StoredSourceFormPolicies<'source> {
    /// Uses only the original strict product envelope and retained original source bindings.
    /// `access` is a trusted server input, not a caller approval or route capability.
    /// # Errors
    /// Rejects stale/revoked policy, source/ACL/AEAD drift, malformed request and compiler failure.
    pub fn prepare_product_json<'a, R, B, S, V, P>(
        &'a self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        repository: &P,
        raw: &[u8],
        access: &FormInputAccessPolicy,
        now: u64,
    ) -> Result<PreparedStoredPolicyProduct<'a, 'source>, StoredPolicyProductError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
        P: SourcePolicyRepository,
    {
        let policy = self.verify(provider, repository, now)?;
        let native = self.bound.native_binding();
        let bindings = StoredProductFormBindings {
            map: native.map(),
            policies: native.policies(),
            access,
        };
        let product = StoredProductFormRequest::prepare_json(provider, raw, &bindings, now)?;
        let receipt = StoredPolicyProductReceipt {
            profile: PROFILE,
            policy,
            product: product.receipt().clone(),
            qualification: "repository_selected_source_bound_original_form_inventory_compiler_memory_candidate_not_atomic_policy_lease_external_issuer_full_document_execution_native_or_gate",
        };
        let prepared = PreparedStoredPolicyProduct {
            policy: self,
            product,
            receipt,
        };
        prepared.verify(provider, repository, access, now)?;
        Ok(prepared)
    }
}
impl PreparedStoredPolicyProduct<'_, '_> {
    #[must_use]
    pub const fn receipt(&self) -> &StoredPolicyProductReceipt {
        &self.receipt
    }

    /// Memory candidate only, not an authorized or published artifact.
    #[must_use]
    pub fn candidate_bytes(&self) -> &[u8] {
        self.product.candidate_bytes()
    }

    /// Re-reads and reconstructs the whole current source/policy and original compiler result.
    /// Before/after authorization bounds observations but is not an atomic policy lease.
    /// # Errors
    /// Rejects any latest/revocation/source/provider/access or whole receipt/candidate drift.
    pub fn verify<R, B, S, V, P>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        repository: &P,
        access: &FormInputAccessPolicy,
        now: u64,
    ) -> Result<StoredPolicyProductReceipt, StoredPolicyProductError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
        P: SourcePolicyRepository,
    {
        let before = self.policy.verify(provider, repository, now)?;
        let native = self.policy.bound.native_binding();
        let product = self.product.verify(
            provider,
            &StoredProductFormBindings {
                map: native.map(),
                policies: native.policies(),
                access,
            },
            now,
        )?;
        let after = self.policy.verify(provider, repository, now)?;
        if self.receipt.profile != PROFILE
            || before != self.receipt.policy
            || after != before
            || product != self.receipt.product
        {
            return Err(StoredPolicyProductError::Receipt);
        }
        Ok(self.receipt.clone())
    }

    /// Consults the unchanged original route guard only after fresh policy/product verification.
    /// # Errors
    /// Current form execution remains denied. No head write, ingest, key claim or publication.
    pub fn require_current_product_route<R, B, S, V, P>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        repository: &P,
        access: &FormInputAccessPolicy,
        now: u64,
    ) -> Result<(), StoredPolicyProductError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
        P: SourcePolicyRepository,
    {
        self.verify(provider, repository, access, now)?;
        let native = self.policy.bound.native_binding();
        self.product.require_current_product_route(
            provider,
            &StoredProductFormBindings {
                map: native.map(),
                policies: native.policies(),
                access,
            },
            now,
        )?;
        // Relevant if the original route becomes supported in a later qualified phase.
        self.policy.verify(provider, repository, now)?;
        Ok(())
    }
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum StoredPolicyProductError {
    #[error("stored_policy_product_policy_denied")]
    Policy(#[from] StoredSourcePolicyError),
    #[error("stored_policy_product_original_product_denied")]
    Product(#[from] StoredProductFormError),
    #[error("stored_policy_product_receipt_changed")]
    Receipt,
}
