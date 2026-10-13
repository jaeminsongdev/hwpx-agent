//! Common strict product API: unchanged v1 form input or source-only v2 formula recalculation.
//! No command-line/server transport, issuer, idempotency claim or publication is added.
pub mod formula;
mod request;
use super::FormProductRequestError;
use super::stored::{
    PreparedStoredProductForm, StoredProductFormBindings, StoredProductFormError,
    StoredProductFormRequest,
};
use crate::form_stored_provider::{
    StoredFormError, StoredFormProvider, actual_import::StoredActualFormImportError,
};
use artifact_service::{ArtifactMetadataRepository, ArtifactScanner, EncryptedBlobStore};
use formula::PreparedStoredProductFormula;
use revision_service::RevisionRepository;
use thiserror::Error;

/// Both variants preserve their original authentication and route guards.
#[derive(Debug)]
pub enum PreparedStoredProductOperation {
    Form(PreparedStoredProductForm),
    TableFormulas(PreparedStoredProductFormula),
}
impl PreparedStoredProductOperation {
    /// Fresh verification before returning a whole in-memory candidate to a consumer.
    /// # Errors
    /// Rejects missing/foreign bindings, source/head/access failure or any receipt drift.
    pub fn with_verified_bytes<R, B, S, V, T>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        bindings: Option<&StoredProductFormBindings<'_>>,
        now: u64,
        consume: impl FnOnce(&[u8]) -> T,
    ) -> Result<T, StoredProductOperationError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        match self {
            Self::Form(form) => {
                form.verify(
                    provider,
                    bindings.ok_or(StoredProductOperationError::Bindings)?,
                    now,
                )?;
                Ok(consume(form.candidate_bytes()))
            }
            Self::TableFormulas(formula) => {
                if bindings.is_some() {
                    return Err(StoredProductOperationError::Bindings);
                }
                formula.with_verified_bytes(provider, now, consume)
            }
        }
    }
    /// Reuses the original route denial only after fresh authentication and verification.
    /// # Errors
    /// Current variants remain unqualified; never claims a key, ingests or commits.
    pub fn require_current_product_route<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        bindings: Option<&StoredProductFormBindings<'_>>,
        now: u64,
    ) -> Result<(), StoredProductOperationError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        match self {
            Self::Form(form) => Ok(form.require_current_product_route(
                provider,
                bindings.ok_or(StoredProductOperationError::Bindings)?,
                now,
            )?),
            Self::TableFormulas(formula) => {
                if bindings.is_some() {
                    return Err(StoredProductOperationError::Bindings);
                }
                formula.require_current_product_route(provider, now)
            }
        }
    }
}
#[derive(Debug)]
pub struct StoredProductRequest;
impl StoredProductRequest {
    /// Dispatches the bounded duplicate-free original product request family.
    /// # Errors
    /// Rejects an unknown schema/operation before artifact reads. v1 requires original form
    /// bindings; v2 formulas reject them and derive all targets/results from actual source.
    pub fn prepare_json<R, B, S, V>(
        provider: &StoredFormProvider<'_, R, B, S, V>,
        raw: &[u8],
        bindings: Option<&StoredProductFormBindings<'_>>,
        now: u64,
    ) -> Result<PreparedStoredProductOperation, StoredProductOperationError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        match request::classify(raw)? {
            request::Kind::Form => {
                let bindings = bindings.ok_or(StoredProductOperationError::Bindings)?;
                Ok(PreparedStoredProductOperation::Form(
                    StoredProductFormRequest::prepare_json(provider, raw, bindings, now)?,
                ))
            }
            request::Kind::TableFormulas(request) => {
                if bindings.is_some() {
                    return Err(StoredProductOperationError::Bindings);
                }
                Ok(PreparedStoredProductOperation::TableFormulas(
                    formula::prepare(provider, request, raw, now)?,
                ))
            }
        }
    }
}
#[derive(Debug, Error)]
pub enum StoredProductOperationError {
    #[error("product_operation_request_rejected")]
    Request(#[from] FormProductRequestError),
    #[error("product_operation_original_form_rejected")]
    Legacy(#[from] StoredProductFormError),
    #[error("product_operation_provider_rejected")]
    Provider(#[from] StoredFormError),
    #[error("product_operation_actual_source_rejected")]
    Source(#[from] StoredActualFormImportError),
    #[error("product_operation_formula_compiler_rejected")]
    Compiler(#[from] crate::form_stored_provider::actual_import::field_ranges::semantics::evaluation::output::compiler::StoredFormulaCompilerError),
    #[error("product_operation_formula_preparation_rejected")]
    Preparation,
    #[error("product_operation_binding_kind_rejected")]
    Bindings,
    #[error("product_operation_receipt_binding_rejected")]
    Receipt,
    #[error("product_operation_no_change_route_unqualified")]
    RouteUnqualified,
}
