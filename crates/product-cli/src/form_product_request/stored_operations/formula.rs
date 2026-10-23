//! Owned source/request/compiled snapshot, not a self-referential graph or execution permit.
use super::super::{MAX_ENVELOPE_BYTES, bounded, digest};
use super::{StoredProductOperationError as Error, request::FormulaRequest};
use crate::form_stored_provider::{
    StoredFormProvider, actual_import::StoredImportedDocumentForms,
    actual_import::field_ranges::semantics::evaluation::output::compiler::StoredFormulaCompilerReceipt,
};
use artifact_service::{ArtifactMetadataRepository, ArtifactScanner, EncryptedBlobStore};
use domain_ir::CompiledOperationPlan;
use hwpx_package::WriterLimits;
use revision_service::RevisionRepository;
use serde::Serialize;
use std::fmt;
use crate::form_stored_provider::actual_import::field_ranges::semantics::evaluation::output::outcome::{StoredFormulaOutcome, UnchangedFormulaReceipt};
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
#[serde(tag = "outcome", rename_all = "snake_case")]
pub enum FormulaPreparationReceipt {
    Changed {
        compiler: StoredFormulaCompilerReceipt,
    },
    Unchanged {
        source: UnchangedFormulaReceipt,
    },
}
pub const STORED_PRODUCT_FORMULA_PROFILE: &str =
    "hwpx-agent.product-stored-source-table-formulas/v1";
pub const PRODUCT_OPERATION_REQUEST_SCHEMA: &str = super::request::PRODUCT_OPERATION_REQUEST_SCHEMA;
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct StoredProductFormulaReceipt {
    pub profile: &'static str,
    pub raw_request_sha256: String,
    pub canonical_request_sha256: String,
    /// Request identity only: not tenant-global execution identity or a claimed idempotency key.
    pub request_identity_sha256: String,
    pub formula: FormulaPreparationReceipt,
    pub qualification: &'static str,
}
pub struct PreparedStoredProductFormula {
    request: FormulaRequest,
    source: StoredImportedDocumentForms,
    plan: Option<CompiledOperationPlan>,
    candidate: Vec<u8>,
    receipt: StoredProductFormulaReceipt,
}
impl fmt::Debug for PreparedStoredProductFormula {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("PreparedStoredProductFormula(<redacted>)")
    }
}
impl PreparedStoredProductFormula {
    pub(super) const fn source(&self) -> &StoredImportedDocumentForms {
        &self.source
    }
    #[must_use]
    pub const fn receipt(&self) -> &StoredProductFormulaReceipt {
        &self.receipt
    }
    /// Compiler data only; no execution manifest/issuer authority is conferred.
    #[must_use]
    pub const fn compiled(&self) -> Option<&CompiledOperationPlan> {
        self.plan.as_ref()
    }
    /// Rebuilds source-derived meanings/math/candidate/compiler through fresh original service checks.
    /// # Errors
    /// Rejects substituted provider/head/access/bytes/request identity or entire plan/candidate drift.
    pub fn verify<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<StoredProductFormulaReceipt, Error>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.request.check(provider, now)?;
        let (plan, candidate, receipt) = build(provider, &self.source, &self.request, now)?;
        self.request.check(provider, now)?;
        if plan != self.plan
            || candidate != self.candidate
            || receipt != self.receipt.formula
            || self.receipt.profile != STORED_PRODUCT_FORMULA_PROFILE
            || self.receipt.canonical_request_sha256
                != digest(&bounded(&self.request, MAX_ENVELOPE_BYTES)?)
            || self.receipt.request_identity_sha256 != identity(&self.request)?
        {
            return Err(Error::Receipt);
        }
        Ok(self.receipt.clone())
    }
    /// Fresh verification before releasing the complete candidate; no path/file/artifact is written.
    /// # Errors
    /// Rejects source/request/compiler drift before invoking the consumer.
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
        self.verify(provider, now)?;
        Ok(consume(&self.candidate))
    }
    /// Preserves the original field-result route denial after full fresh verification.
    /// # Errors
    /// Never authorizes the current unqualified field/issuer/durable/native route.
    pub fn require_current_product_route<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<(), Error>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.verify(provider, now)?;
        if self.plan.is_none() {
            return Err(Error::RouteUnqualified);
        }
        let fields = self
            .source
            .import_field_ranges(provider, now)
            .map_err(|_| Error::Preparation)?;
        let meanings = fields
            .import_semantics(provider, now)
            .map_err(|_| Error::Preparation)?;
        let evaluation = meanings
            .evaluate_table_formulas(provider, now)
            .map_err(|_| Error::Preparation)?;
        let results = evaluation
            .prepare_results(provider, WriterLimits::default(), now)
            .map_err(|_| Error::Preparation)?;
        let plan = results.compile(provider, self.request.plan_id.clone(), now)?;
        Ok(plan.require_current_product_route(provider, now)?)
    }
}
pub(super) fn prepare<R, B, S, V>(
    provider: &StoredFormProvider<'_, R, B, S, V>,
    request: FormulaRequest,
    raw: &[u8],
    now: u64,
) -> Result<PreparedStoredProductFormula, Error>
where
    R: ArtifactMetadataRepository,
    B: EncryptedBlobStore,
    S: ArtifactScanner,
    V: RevisionRepository,
{
    request.check(provider, now)?;
    let source = provider.import_actual_forms(request.head()?, now)?;
    prepare_from_source(provider, request, raw, source, now)
}
pub(super) fn prepare_from_source<R, B, S, V>(
    provider: &StoredFormProvider<'_, R, B, S, V>,
    request: FormulaRequest,
    raw: &[u8],
    source: StoredImportedDocumentForms,
    now: u64,
) -> Result<PreparedStoredProductFormula, Error>
where
    R: ArtifactMetadataRepository,
    B: EncryptedBlobStore,
    S: ArtifactScanner,
    V: RevisionRepository,
{
    request.check(provider, now)?;
    source.verify(provider, now)?;
    let (plan, candidate, formula) = build(provider, &source, &request, now)?;
    request.check(provider, now)?;
    let receipt = StoredProductFormulaReceipt {
        profile: STORED_PRODUCT_FORMULA_PROFILE,
        raw_request_sha256: digest(raw),
        canonical_request_sha256: digest(&bounded(&request, MAX_ENVELOPE_BYTES)?),
        request_identity_sha256: identity(&request)?,
        formula,
        qualification: "strict_product_API_source_only_recalculation_preparation_NOT_full_import_field_policy_registry_issuer_atomic_CAS_idempotency_publication_transport_native_SQL_or_Gate",
    };
    Ok(PreparedStoredProductFormula {
        request,
        source,
        plan,
        candidate,
        receipt,
    })
}
fn build<R, B, S, V>(
    provider: &StoredFormProvider<'_, R, B, S, V>,
    source: &StoredImportedDocumentForms,
    request: &FormulaRequest,
    now: u64,
) -> Result<
    (
        Option<CompiledOperationPlan>,
        Vec<u8>,
        FormulaPreparationReceipt,
    ),
    Error,
>
where
    R: ArtifactMetadataRepository,
    B: EncryptedBlobStore,
    S: ArtifactScanner,
    V: RevisionRepository,
{
    let fields = source
        .import_field_ranges(provider, now)
        .map_err(|_| Error::Preparation)?;
    let meanings = fields
        .import_semantics(provider, now)
        .map_err(|_| Error::Preparation)?;
    let evaluation = meanings
        .evaluate_table_formulas(provider, now)
        .map_err(|_| Error::Preparation)?;
    let outcome = evaluation
        .prepare_results_outcome(provider, WriterLimits::default(), now)
        .map_err(|_| Error::Preparation)?;
    match outcome {
        StoredFormulaOutcome::Changed(results) => {
            let plan = results.compile(provider, request.plan_id.clone(), now)?;
            let candidate = plan.with_verified_bytes(provider, now, <[u8]>::to_vec)?;
            Ok((
                Some(plan.compiled().clone()),
                candidate,
                FormulaPreparationReceipt::Changed {
                    compiler: plan.receipt().clone(),
                },
            ))
        }
        StoredFormulaOutcome::Unchanged(results) => {
            let candidate = results
                .with_verified_bytes(provider, now, <[u8]>::to_vec)
                .map_err(|_| Error::Preparation)?;
            Ok((
                None,
                candidate,
                FormulaPreparationReceipt::Unchanged {
                    source: results.receipt().clone(),
                },
            ))
        }
    }
}
fn identity(request: &FormulaRequest) -> Result<String, Error> {
    Ok(digest(&bounded(
        &(
            PRODUCT_OPERATION_REQUEST_SCHEMA,
            &request.project_id,
            &request.document_id,
            &request.idempotency_key,
            &request.base_revision,
            request.expected_head_generation,
            &request.expected_source_package_sha256,
            &request.plan_id,
            &request.operation,
        ),
        MAX_ENVELOPE_BYTES,
    )?))
}
