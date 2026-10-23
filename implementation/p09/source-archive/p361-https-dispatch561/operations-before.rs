//! Common strict candidate API: original Form/Formula plus closed search mutation schemas.
//! No command-line/server transport, issuer, idempotency claim or publication is added.
pub mod formula;
pub mod policy;
pub mod search_mutations;
pub mod search_preview;
pub mod compiled_search;
pub mod https_targets;
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

/// All variants preserve their original authentication and route guards.
#[derive(Debug)]
pub enum PreparedStoredProductOperation {
    Form(Box<PreparedStoredProductForm>),
    TableFormulas(Box<PreparedStoredProductFormula>),
    SearchMutation(Box<search_mutations::PreparedStoredSearchMutation>),
    SearchPreview(Box<search_preview::PreparedStoredSearchPreview>),
    NamedStylePreview(Box<super::stored_literal_replacement::named_styles::PreparedStoredNamedStylePreviewProduct>),
    NamedStyleOptionsPreview(Box<super::stored_literal_replacement::named_styles::options::PreparedStoredNamedStyleOptionsPreviewProduct>),
    PersonalInfoMaskPreview(Box<super::stored_literal_replacement::personal_info::PreparedStoredPersonalInfoMaskPreviewProduct>),
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
            Self::SearchMutation(candidate) => {
                if bindings.is_some() {
                    return Err(StoredProductOperationError::Bindings);
                }
                Ok(candidate.with_verified_bytes(provider, now, consume)?)
            }
            Self::SearchPreview(_) | Self::NamedStylePreview(_) | Self::NamedStyleOptionsPreview(_) | Self::PersonalInfoMaskPreview(_) => {
                if bindings.is_some(){return Err(StoredProductOperationError::Bindings);}
                Err(StoredProductOperationError::PreviewOnly)
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
            Self::SearchMutation(candidate) => {
                if bindings.is_some() {
                    return Err(StoredProductOperationError::Bindings);
                }
                Ok(candidate.require_current_product_route(provider, now)?)
            }
            Self::SearchPreview(preview) => {
                if bindings.is_some(){return Err(StoredProductOperationError::Bindings);}
                Ok(preview.require_current_product_route(provider,now)?)
            }
            Self::NamedStylePreview(preview) => {
                if bindings.is_some(){return Err(StoredProductOperationError::Bindings);}
                Ok(preview.require_current_product_route(provider,now)?)
            }
            Self::NamedStyleOptionsPreview(preview) => {
                if bindings.is_some(){return Err(StoredProductOperationError::Bindings);}
                Ok(preview.require_current_product_route(provider,now)?)
            }
            Self::PersonalInfoMaskPreview(preview) => {
                if bindings.is_some(){return Err(StoredProductOperationError::Bindings);}
                Ok(preview.require_current_product_route(provider,now)?)
            }
        }
    }
}
impl PreparedStoredProductOperation {
    /// # Errors
    /// Only a real nonmutating preview can deliver this JSON. No candidate bytes or fake plan.
    pub fn with_verified_preview_json<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,bindings:Option<&StoredProductFormBindings<'_>>,
        now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,StoredProductOperationError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        if bindings.is_some(){return Err(StoredProductOperationError::Bindings);}
        match self{Self::SearchPreview(p)=>Ok(p.with_verified_json(provider,now,consume)?),Self::NamedStylePreview(p)=>Ok(p.with_verified_json(provider,now,consume)?),Self::NamedStyleOptionsPreview(p)=>Ok(p.with_verified_json(provider,now,consume)?),Self::PersonalInfoMaskPreview(p)=>Ok(p.with_verified_json(provider,now,consume)?),_=>Err(StoredProductOperationError::PreviewKind)}
    }
}
#[derive(Debug)]
pub struct StoredProductRequest;
impl StoredProductRequest {
    /// Dispatches the bounded duplicate-free original product request family.
    /// # Errors
    /// Rejects an unknown schema/operation before artifact reads. v1 requires original form
    /// bindings; formulas and search mutations reject them and derive results from actual source.
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
        Self::prepare_json_with_search_limits(provider, raw, bindings, search_mutations::SearchMutationLimits::standard()?, now)
    }
    /// Dispatches the same closed schemas with server-owned validated search/writer budgets.
    /// # Errors
    /// Original Form/Formula behavior is unchanged; search candidates reject legacy bindings.
    pub fn prepare_json_with_search_limits<R, B, S, V>(
        provider: &StoredFormProvider<'_, R, B, S, V>,
        raw: &[u8],
        bindings: Option<&StoredProductFormBindings<'_>>,
        limits: search_mutations::SearchMutationLimits,
        now: u64,
    ) -> Result<PreparedStoredProductOperation, StoredProductOperationError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        match request::classify(raw)? {
            request::Kind::HttpsTargets => Err(StoredProductOperationError::PolicyRepositoryRequired),
            request::Kind::Form => {
                let bindings = bindings.ok_or(StoredProductOperationError::Bindings)?;
                Ok(PreparedStoredProductOperation::Form(Box::new(
                    StoredProductFormRequest::prepare_json(provider, raw, bindings, now)?,
                )))
            }
            request::Kind::TableFormulas(request) => {
                if bindings.is_some() {
                    return Err(StoredProductOperationError::Bindings);
                }
                Ok(PreparedStoredProductOperation::TableFormulas(Box::new(
                    formula::prepare(provider, request, raw, now)?,
                )))
            }
            request::Kind::SearchMutation(family) => {
                if bindings.is_some() {
                    return Err(StoredProductOperationError::Bindings);
                }
                Ok(PreparedStoredProductOperation::SearchMutation(Box::new(
                    search_mutations::prepare(family, provider, raw, limits, now)?,
                )))
            }
            request::Kind::FontPreview => {
                if bindings.is_some(){return Err(StoredProductOperationError::Bindings);}
                Ok(PreparedStoredProductOperation::SearchPreview(Box::new(search_preview::prepare(provider,raw,limits,now)?)))
            }
            request::Kind::NamedStylePreview => {
                if bindings.is_some(){return Err(StoredProductOperationError::Bindings);}
                Ok(PreparedStoredProductOperation::NamedStylePreview(Box::new(super::stored_literal_replacement::named_styles::StoredNamedStyleProductRequest::prepare_preview_json(provider,raw,limits.search,limits.writer,now)?)))
            }
            request::Kind::NamedStyleOptionsPreview => {
                if bindings.is_some(){return Err(StoredProductOperationError::Bindings);}
                Ok(PreparedStoredProductOperation::NamedStyleOptionsPreview(Box::new(super::stored_literal_replacement::named_styles::options::StoredNamedStyleOptionsProductRequest::prepare_preview_json(provider,raw,limits.search,limits.writer,now)?)))
            }
            request::Kind::PersonalInfoMaskPreview => {
                if bindings.is_some(){return Err(StoredProductOperationError::Bindings);}
                Ok(PreparedStoredProductOperation::PersonalInfoMaskPreview(Box::new(super::stored_literal_replacement::personal_info::StoredPersonalInfoMaskProductRequest::prepare_preview_json(provider,raw,limits.search,limits.writer,now)?)))
            }
        }
    }
}
#[derive(Debug, Error)]
pub enum StoredProductOperationError {
    #[error("product_operation_https_current_policy_repository_required")]
    PolicyRepositoryRequired,
    #[error("product_operation_personal_info_mask_rejected")]
    PersonalInfoMask(#[from]super::stored_literal_replacement::personal_info::PersonalInfoMaskProductError),
    #[error("product_operation_named_style_rejected")]
    NamedStyle(#[from]super::stored_literal_replacement::named_styles::NamedStyleProductError),
    #[error("product_operation_font_options_rejected")]
    FontOptions(#[from]super::stored_literal_replacement::fonts::options::FontOptionsProductError),
    #[error("product_operation_preview_has_no_output")]
    PreviewOnly,
    #[error("product_operation_preview_kind_rejected")]
    PreviewKind,
    #[error("product_operation_search_mutation_rejected")]
    SearchMutation(#[from] search_mutations::SearchMutationError),
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
