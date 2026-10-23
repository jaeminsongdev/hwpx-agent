//! Original strict product request -> sealed revision-selected package AND complete document IR.
//! Preparation emits normal artifact-read audits, not an ingest, CAS, key claim or publication.
use super::{
    MAX_ENVELOPE_BYTES, MAX_INPUT_BYTES, Request, bounded, digest, scope_digest,
    stored::{StoredProductFormBindings, StoredProductFormError, check_binding, head},
};
use crate::form_stored_provider::{
    StoredFormInputs, StoredFormProvider,
    full_document::{
        PreparedStoredFullDocumentForm, StoredFullDocumentFormError, StoredFullDocumentFormReceipt,
    },
};
use artifact_service::{ArtifactMetadataRepository, ArtifactScanner, EncryptedBlobStore};
use domain_ir::{CompiledOperationPlan, DocumentGraph};
use revision_service::RevisionRepository;
use serde::Serialize;
use std::fmt;
use thiserror::Error;

pub const STORED_FULL_DOCUMENT_PRODUCT_FORM_PROFILE: &str =
    "hwpx-agent.product-stored-full-document-form-request/v1";

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct StoredFullDocumentProductFormReceipt {
    pub profile: &'static str,
    pub raw_request_sha256: String,
    pub canonical_request_sha256: String,
    /// Request identity only; NOT a claimed key or proof of exactly-once execution.
    pub scoped_request_sha256: String,
    pub full_document: StoredFullDocumentFormReceipt,
    pub qualification: StoredFullDocumentProductFormQualification,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum StoredFullDocumentProductFormQualification {
    ServiceHeadBoundPreparationOnlyImportIssuerAtomicCasIdempotencyPublicationNativeAndGateUnqualified,
}

/// Non-deserializable request and complete package/IR/plan snapshots. No write capability.
pub struct PreparedStoredFullDocumentProductForm {
    request: Request,
    full_document: PreparedStoredFullDocumentForm,
    receipt: StoredFullDocumentProductFormReceipt,
}
impl fmt::Debug for PreparedStoredFullDocumentProductForm {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("PreparedStoredFullDocumentProductForm(<redacted>)")
    }
}

impl PreparedStoredFullDocumentProductForm {
    #[must_use]
    pub const fn receipt(&self) -> &StoredFullDocumentProductFormReceipt {
        &self.receipt
    }

    /// Memory candidate only, never a published or authorized result artifact.
    #[must_use]
    pub fn candidate_bytes(&self) -> &[u8] {
        self.full_document.candidate_bytes()
    }

    /// Complete stored graph with only the validated form-control states changed.
    #[must_use]
    pub const fn target_graph(&self) -> &DocumentGraph {
        self.full_document.target_graph()
    }

    /// Selectors and base digest refer to the whole graph, never an inventory projection.
    #[must_use]
    pub const fn compiled_plan(&self) -> &CompiledOperationPlan {
        self.full_document.compiled_plan()
    }

    /// Rechecks original request scope/head/source and independently downloads package AND IR.
    /// # Errors
    /// Rejects fresh scope/head/ACL/AEAD/state/map/policy/access/graph/plan drift. Read audits append.
    /// Multiple fresh head reads are not a lock or an atomic CAS authorization.
    pub fn verify<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        bindings: &StoredProductFormBindings<'_>,
        now: u64,
    ) -> Result<StoredFullDocumentProductFormReceipt, StoredFullDocumentProductFormError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        check_binding(&self.request, provider, now)?;
        let full_document = self.full_document.verify(
            provider,
            bindings.map,
            bindings.policies,
            bindings.access,
            now,
        )?;
        check_binding(&self.request, provider, now)?;
        if self.receipt.profile != STORED_FULL_DOCUMENT_PRODUCT_FORM_PROFILE
            || full_document != self.receipt.full_document
            || full_document.stored.source_sha256 != self.request.expected_source_package_sha256
            || full_document.stored.head_generation != self.request.expected_head_generation
            || self.compiled_plan().plan_id() != &self.request.plan_id
            || self.compiled_plan().base_revision() != &self.request.base_revision
            || self.target_graph().document_id() != &self.request.document_id
            || self.receipt.canonical_request_sha256
                != digest(&bounded(&self.request, MAX_ENVELOPE_BYTES)?)
            || self.receipt.scoped_request_sha256 != scope_digest(&self.request)?
            || self.receipt.qualification
                != StoredFullDocumentProductFormQualification::ServiceHeadBoundPreparationOnlyImportIssuerAtomicCasIdempotencyPublicationNativeAndGateUnqualified
        {
            return Err(StoredFullDocumentProductFormError::Receipt);
        }
        Ok(self.receipt.clone())
    }

    /// Consults the actual existing route authority only after complete fresh request verification.
    /// # Errors
    /// Current full-document form scope remains denied. No VS0 authority substitution is possible.
    pub fn require_current_product_route<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        bindings: &StoredProductFormBindings<'_>,
        now: u64,
    ) -> Result<(), StoredFullDocumentProductFormError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.verify(provider, bindings, now)?;
        self.full_document.require_current_product_route(
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
pub struct StoredFullDocumentProductFormRequest;
impl StoredFullDocumentProductFormRequest {
    /// Original bounded duplicate-free envelope -> current stored result AND sealed-node IR.
    /// # Errors
    /// Rejects malformed requests before service reads and rejects every absent or invalid IR.
    /// Never falls back to inventory-only preparation, initializes a stream or claims a retry key.
    pub fn prepare_json<R, B, S, V>(
        provider: &StoredFormProvider<'_, R, B, S, V>,
        raw: &[u8],
        bindings: &StoredProductFormBindings<'_>,
        now: u64,
    ) -> Result<PreparedStoredFullDocumentProductForm, StoredFullDocumentProductFormError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        let request = Request::parse(raw)?;
        check_binding(&request, provider, now)?;
        let input = bounded(&request.form_input, MAX_INPUT_BYTES)?;
        let full_document = provider.prepare_full_document_json(
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
        let receipt = StoredFullDocumentProductFormReceipt {
            profile: STORED_FULL_DOCUMENT_PRODUCT_FORM_PROFILE,
            raw_request_sha256: digest(raw),
            canonical_request_sha256: digest(&bounded(&request, MAX_ENVELOPE_BYTES)?),
            scoped_request_sha256: scope_digest(&request)?,
            full_document: full_document.receipt().clone(),
            qualification: StoredFullDocumentProductFormQualification::ServiceHeadBoundPreparationOnlyImportIssuerAtomicCasIdempotencyPublicationNativeAndGateUnqualified,
        };
        let prepared = PreparedStoredFullDocumentProductForm {
            request,
            full_document,
            receipt,
        };
        prepared.verify(provider, bindings, now)?;
        Ok(prepared)
    }
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum StoredFullDocumentProductFormError {
    #[error("stored_full_document_product_form_request_rejected")]
    Request(#[from] super::FormProductRequestError),
    #[error("stored_full_document_product_form_provider_rejected")]
    Provider(#[from] StoredProductFormError),
    #[error("stored_full_document_product_form_ir_rejected")]
    FullDocument(#[from] StoredFullDocumentFormError),
    #[error("stored_full_document_product_form_receipt_changed")]
    Receipt,
}
