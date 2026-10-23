//! Original strict product envelope -> actual stored source -> original full form compiler.
//! No public artifact/path/approval input; no signed route, idempotency claim or publication.
use super::{MAX_ENVELOPE_BYTES, MAX_INPUT_BYTES, Request, bounded, digest, scope_digest};
use crate::form_stored_provider::{
    PreparedStoredForm, StoredFormError, StoredFormInputs, StoredFormProvider, StoredFormReceipt,
};
use artifact_service::{ArtifactMetadataRepository, ArtifactScanner, EncryptedBlobStore};
use domain_ir::form_input::FormInputAccessPolicy;
use hwpx_package::{NativeFormPackageMap, NativeFormPackagePolicy};
use revision_service::{RevisionHead, RevisionRepository};
use serde::Serialize;
use std::fmt;
use thiserror::Error;

pub const STORED_PRODUCT_FORM_PROFILE: &str = "hwpx-agent.product-stored-form-request/v1";

/// Provider-owned bindings. The strict public envelope cannot select these or authorize a route.
pub struct StoredProductFormBindings<'a> {
    pub map: &'a NativeFormPackageMap,
    pub policies: &'a [NativeFormPackagePolicy],
    pub access: &'a FormInputAccessPolicy,
}
impl fmt::Debug for StoredProductFormBindings<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("StoredProductFormBindings(<redacted>)")
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct StoredProductFormReceipt {
    pub profile: &'static str,
    pub raw_request_sha256: String,
    pub canonical_request_sha256: String,
    /// Original project/document/key/request digest, NOT a claimed key or global execution identity.
    pub scoped_request_sha256: String,
    pub stored: StoredFormReceipt,
}

/// Private original strict request bound to the actual sealed stored source and whole candidate.
pub struct PreparedStoredProductForm {
    request: Request,
    stored: PreparedStoredForm,
    receipt: StoredProductFormReceipt,
}
impl fmt::Debug for PreparedStoredProductForm {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("PreparedStoredProductForm(<redacted>)")
    }
}
impl PreparedStoredProductForm {
    #[must_use]
    pub const fn receipt(&self) -> &StoredProductFormReceipt {
        &self.receipt
    }

    /// Memory candidate only, never a published or authorized artifact.
    #[must_use]
    pub fn candidate_bytes(&self) -> &[u8] {
        self.stored.candidate_bytes()
    }

    /// Fresh real head/node/tenant/scope/ACL/AEAD/source and original whole compiler checks.
    /// # Errors
    /// Rejects stale source, substituted provider/bindings or changed access. Reads emit audit events.
    pub fn verify<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        bindings: &StoredProductFormBindings<'_>,
        now: u64,
    ) -> Result<StoredProductFormReceipt, StoredProductFormError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        check_binding(&self.request, provider, now)?;
        let stored = self.stored.verify(
            provider,
            bindings.map,
            bindings.policies,
            bindings.access,
            now,
        )?;
        check_binding(&self.request, provider, now)?;
        if self.receipt.profile != STORED_PRODUCT_FORM_PROFILE
            || stored != self.receipt.stored
            || stored.source_sha256 != self.request.expected_source_package_sha256
            || stored.head_generation != self.request.expected_head_generation
            || self.receipt.canonical_request_sha256
                != digest(&bounded(&self.request, MAX_ENVELOPE_BYTES)?)
            || self.receipt.scoped_request_sha256 != scope_digest(&self.request)?
        {
            return Err(StoredProductFormError::Receipt);
        }
        Ok(self.receipt.clone())
    }

    /// Consults unchanged real route authority only after the complete fresh stored-request check.
    /// # Errors
    /// Current form scope is denied; no manifest, key claim, ingest, commit or publication.
    pub fn require_current_product_route<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        bindings: &StoredProductFormBindings<'_>,
        now: u64,
    ) -> Result<(), StoredProductFormError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.verify(provider, bindings, now)?;
        self.stored.require_current_product_route(
            provider,
            bindings.map,
            bindings.policies,
            bindings.access,
            now,
        )?;
        Ok(())
    }
}

#[derive(Debug)]
pub struct StoredProductFormRequest;
impl StoredProductFormRequest {
    /// Reuses the ORIGINAL duplicate-free bounded strict envelope; source comes ONLY from the provider.
    /// # Errors
    /// Rejects malformed/stale/substituted envelopes and service/compiler failures. No stream mutation.
    pub fn prepare_json<R, B, S, V>(
        provider: &StoredFormProvider<'_, R, B, S, V>,
        raw: &[u8],
        bindings: &StoredProductFormBindings<'_>,
        now: u64,
    ) -> Result<PreparedStoredProductForm, StoredProductFormError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        let request = Request::parse(raw)?;
        check_binding(&request, provider, now)?;
        let input = bounded(&request.form_input, MAX_INPUT_BYTES)?;
        let stored = provider.prepare_json(
            StoredFormInputs {
                expected_head: head(&request)?,
                plan_id: request.plan_id.clone(),
                form_input_json: &input,
                map: bindings.map,
                policies: bindings.policies,
                access: bindings.access,
            },
            now,
        )?;
        let receipt = StoredProductFormReceipt {
            profile: STORED_PRODUCT_FORM_PROFILE,
            raw_request_sha256: digest(raw),
            canonical_request_sha256: digest(&bounded(&request, MAX_ENVELOPE_BYTES)?),
            scoped_request_sha256: scope_digest(&request)?,
            stored: stored.receipt().clone(),
        };
        let prepared = PreparedStoredProductForm {
            request,
            stored,
            receipt,
        };
        prepared.verify(provider, bindings, now)?;
        Ok(prepared)
    }
}
pub(super) fn head(request: &Request) -> Result<RevisionHead, StoredProductFormError> {
    let revision = revision_service::RevisionId::parse(request.base_revision.as_str())
        .map_err(|_| StoredProductFormError::Head)?;
    RevisionHead::new(Some(revision), request.expected_head_generation)
        .map_err(|_| StoredProductFormError::Head)
}
pub(super) fn check_binding<R, B, S, V>(
    request: &Request,
    provider: &StoredFormProvider<'_, R, B, S, V>,
    now: u64,
) -> Result<(), StoredProductFormError>
where
    R: ArtifactMetadataRepository,
    B: EncryptedBlobStore,
    S: ArtifactScanner,
    V: RevisionRepository,
{
    provider.check_product_binding(
        &request.project_id,
        &request.document_id,
        head(request)?,
        &request.expected_source_package_sha256,
        now,
    )?;
    Ok(())
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum StoredProductFormError {
    #[error("stored_product_form_request_rejected")]
    Request(#[from] super::FormProductRequestError),
    #[error("stored_product_form_service_rejected")]
    Stored(#[from] StoredFormError),
    #[error("stored_product_form_revision_identity_rejected")]
    Head,
    #[error("stored_product_form_receipt_changed")]
    Receipt,
}
