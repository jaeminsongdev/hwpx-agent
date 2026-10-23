//! Strict existing-CROSSREF command request -> owned original candidate/compiler.
//! Request/plan hashes and scoped observations are never claims or write grants.
use super::super::{UniqueJson, bounded, digest};
use super::compiled_search::request_lookup::{
    PreparedSearchRequestLookup, SearchRequestLookupError,
};
use super::{PreparedStoredProductOperation, StoredProductRequest};
use crate::form_stored_provider::{
    StoredFormProvider,
    actual_import::{
        StoredActualFormImportError,
        bookmark_command_output::{
            StoredBookmarkCommandError,
            compiled::{
                BookmarkCommandCompileError, CompiledBookmarkCommandReceipt,
                PreparedCompiledBookmarkCommandCandidate,
            },
        },
        source_search::StoredSourceSearchError,
    },
};
use artifact_service::{
    ArtifactMetadataRepository, ArtifactScanner, ContentDigest, EncryptedBlobStore,
};
use domain_ir::{
    CompiledOperationPlan, DocumentId, IdempotencyKey, LogicalId, PlanId, ProjectId,
    ReferenceAuxiliaryLimits, RevisionId,
};
use hwpx_package::{
    WriterLimits, cross_reference_sdk::SdkCrossReferenceDisplay,
    document_import::fields::semantics::source_index::bookmark_updates::SourceBookmarkCommandChange,
};
use revision_service::{
    RevisionHead, RevisionRepository,
    postgres::source_formula_policy::issuer_registry::stored_revision_jobs::{
        lifecycle::StoredJobObservation,
        request_lookup::{StoredRequestLookupRepository, StoredRequestObservation},
    },
};
use serde::{Deserialize, Serialize};
use std::{collections::BTreeSet, fmt};
use thiserror::Error;

pub const BOOKMARK_COMMAND_PRODUCT_REQUEST_SCHEMA: &str =
    "hwpx-agent.product-bookmark-command-request/v1";
const PROFILE: &str = "hwpx-agent.product-bookmark-command-preparation/v1";
const MAX_REQUEST_BYTES: usize = 2 * 1024 * 1024;
const MAX_CHANGES: usize = 4096;
#[derive(Clone, Copy, Debug)]
pub struct BookmarkCommandProductLimits {
    pub auxiliary: ReferenceAuxiliaryLimits,
    pub writer: WriterLimits,
}
impl BookmarkCommandProductLimits {
    /// # Errors
    /// Finite server budgets, not request-selected trust, policy or output data.
    pub fn standard() -> Result<Self, BookmarkCommandProductError> {
        Ok(Self {
            auxiliary: ReferenceAuxiliaryLimits::new(Default::default()).map_err(|_| E::Limit)?,
            writer: WriterLimits::default(),
        })
    }
}
#[derive(Deserialize, Serialize)]
#[serde(rename_all = "snake_case")]
enum Kind {
    ChangeBookmarkCrossrefCommands,
}
#[derive(Deserialize, Serialize)]
#[serde(rename_all = "snake_case")]
enum Display {
    Page,
    BookmarkName,
    Content,
    RelativePosition,
}
impl Display {
    fn sdk(&self) -> SdkCrossReferenceDisplay {
        match self {
            Self::Page => SdkCrossReferenceDisplay::Page,
            Self::BookmarkName => SdkCrossReferenceDisplay::BookmarkName,
            Self::Content => SdkCrossReferenceDisplay::Content,
            Self::RelativePosition => SdkCrossReferenceDisplay::RelativePosition,
        }
    }
}
#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct Change {
    reference_id: LogicalId,
    expected_source_field_sha256: String,
    expected_meaning_sha256: String,
    target_id: LogicalId,
    display: Display,
    hyperlink: bool,
}
#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct Operation {
    kind: Kind,
    changes: Vec<Change>,
}
#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub(super) struct ParsedBookmarkCommandRequest {
    schema_version: String,
    idempotency_key: IdempotencyKey,
    project_id: ProjectId,
    document_id: DocumentId,
    base_revision: RevisionId,
    expected_head_generation: u64,
    expected_source_package_sha256: String,
    plan_id: PlanId,
    operation: Operation,
}
fn valid_sha(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|v| v.is_ascii_digit() || (b'a'..=b'f').contains(&v))
}
impl ParsedBookmarkCommandRequest {
    pub(super) fn parse(raw: &[u8], limits: BookmarkCommandProductLimits) -> Result<Self, E> {
        if raw.is_empty() || raw.len() > MAX_REQUEST_BYTES {
            return Err(E::Limit);
        }
        let mut parser = serde_json::Deserializer::from_slice(raw);
        UniqueJson::deserialize(&mut parser).map_err(|_| E::Request)?;
        parser.end().map_err(|_| E::Request)?;
        let value: serde_json::Value = serde_json::from_slice(raw).map_err(|_| E::Request)?;
        if !value.is_object()
            || !value
                .get("operation")
                .is_some_and(serde_json::Value::is_object)
        {
            return Err(E::Request);
        }
        let changes = value["operation"]["changes"].as_array().ok_or(E::Request)?;
        if changes.is_empty()
            || changes.len() > MAX_CHANGES
            || changes.len() > limits.auxiliary.config().items_per_kind
        {
            return Err(E::Limit);
        }
        if changes.iter().any(|v| !v.is_object()) {
            return Err(E::Request);
        }
        let request: Self = serde_json::from_value(value).map_err(|_| E::Request)?;
        if request.schema_version != BOOKMARK_COMMAND_PRODUCT_REQUEST_SCHEMA
            || request.expected_head_generation == 0
            || request.expected_head_generation > i64::MAX as u64
            || request.document_id.as_str().len() > 1024
            || !valid_sha(&request.expected_source_package_sha256)
        {
            return Err(E::Request);
        }
        let mut seen = BTreeSet::new();
        for change in &request.operation.changes {
            if !seen.insert(&change.reference_id)
                || !valid_sha(&change.expected_source_field_sha256)
                || !valid_sha(&change.expected_meaning_sha256)
            {
                return Err(E::Request);
            }
        }
        request.head()?;
        Ok(request)
    }
    fn head(&self) -> Result<RevisionHead, E> {
        RevisionHead::new(
            Some(
                revision_service::RevisionId::parse(self.base_revision.as_str())
                    .map_err(|_| E::Request)?,
            ),
            self.expected_head_generation,
        )
        .map_err(|_| E::Request)
    }
    fn canonical(&self) -> Result<String, E> {
        Ok(digest(
            &bounded(self, MAX_REQUEST_BYTES).map_err(|_| E::Limit)?,
        ))
    }
    fn scoped(&self, scope: [u8; 32], canonical: &str) -> Result<String, E> {
        Ok(digest(
            &bounded(
                &(BOOKMARK_COMMAND_PRODUCT_REQUEST_SCHEMA, scope, canonical),
                MAX_REQUEST_BYTES,
            )
            .map_err(|_| E::Limit)?,
        ))
    }
    fn lookup<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
    ) -> Result<PreparedBookmarkCommandLookup, E>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        let scope = provider.source_search_product_scope(&self.project_id, &self.document_id)?;
        let canonical = self.canonical()?;
        let scoped = self.scoped(scope, &canonical)?;
        Ok(PreparedBookmarkCommandLookup {
            shared: PreparedSearchRequestLookup::bind(
                provider,
                &self.project_id,
                &self.document_id,
                &self.idempotency_key,
                &canonical,
                &scoped,
                ContentDigest::parse(&self.expected_source_package_sha256)
                    .map_err(|_| E::Request)?,
                self.head()?,
                scope,
            )?,
        })
    }
}
#[derive(Debug, Error)]
pub enum BookmarkCommandProductError {
    #[error("BOOKMARK_COMMAND_PRODUCT_REQUEST_REJECTED")]
    Request,
    #[error("BOOKMARK_COMMAND_PRODUCT_LIMIT")]
    Limit,
    #[error("BOOKMARK_COMMAND_PRODUCT_SCOPE_REJECTED")]
    Scope(#[from] StoredSourceSearchError),
    #[error("BOOKMARK_COMMAND_PRODUCT_SOURCE_REJECTED")]
    Source(#[from] StoredActualFormImportError),
    #[error("BOOKMARK_COMMAND_PRODUCT_CANDIDATE_REJECTED")]
    Stored(#[from] StoredBookmarkCommandError),
    #[error("BOOKMARK_COMMAND_PRODUCT_COMPILER_REJECTED")]
    Compiler(#[from] BookmarkCommandCompileError),
    #[error("BOOKMARK_COMMAND_PRODUCT_LOOKUP_REJECTED")]
    Lookup(#[from] SearchRequestLookupError),
    #[error("BOOKMARK_COMMAND_PRODUCT_BINDING_REJECTED")]
    Binding,
}
type E = BookmarkCommandProductError;
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct BookmarkCommandProductReceipt {
    pub profile: &'static str,
    pub request_schema: &'static str,
    pub raw_request_sha256: String,
    pub canonical_request_sha256: String,
    pub scoped_request_sha256: String,
    pub compiled: CompiledBookmarkCommandReceipt,
    pub idempotency_key_claimed: bool,
    pub execution_or_publication_authority: bool,
}
pub struct PreparedBookmarkCommandProduct {
    request: ParsedBookmarkCommandRequest,
    candidate: PreparedCompiledBookmarkCommandCandidate<'static>,
    receipt: BookmarkCommandProductReceipt,
}
impl fmt::Debug for PreparedBookmarkCommandProduct {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(
            "PreparedBookmarkCommandProduct(<redacted>; no_claim_CAS_or_execution_authority)",
        )
    }
}
pub struct PreparedBookmarkCommandLookup {
    shared: PreparedSearchRequestLookup,
}
impl fmt::Debug for PreparedBookmarkCommandLookup {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("PreparedBookmarkCommandLookup(<redacted>; observation_only)")
    }
}
impl PreparedBookmarkCommandLookup {
    #[must_use]
    pub fn canonical_request_sha256(&self) -> [u8; 32] {
        self.shared.canonical_request_sha256()
    }
    #[must_use]
    pub fn scoped_request_sha256(&self) -> [u8; 32] {
        self.shared.scoped_request_sha256()
    }
    /// # Errors
    /// Original current scoped observer; no source/head/compiler/claim fallback.
    pub fn observe<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
    ) -> Result<StoredRequestObservation, E>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: StoredRequestLookupRepository,
    {
        Ok(self.shared.observe(provider)?)
    }
    /// # Errors
    /// Explicit registered-effect readback with current ACL/AEAD and a second
    /// observation. A mere status is not independent effect proof or a retry grant.
    pub fn recover_registered<R, B, S, V, F>(&self, provider: &StoredFormProvider<'_, R, B, S, V>, clock: F)
        -> Result<crate::form_stored_provider::actual_import::source_search::request_recovery::StoredRequestRecoveryObservation, E>
    where R: ArtifactMetadataRepository, B: EncryptedBlobStore, S: ArtifactScanner,
        V: StoredRequestLookupRepository + revision_service::postgres::source_formula_policy::issuer_registry::stored_revision_jobs::StoredRevisionJobRepository,
    F: FnMut() -> u64{
        Ok(self.shared.recover_registered(provider, clock)?)
    }
}
pub enum BookmarkCommandRequestEntry {
    Existing(StoredJobObservation),
    Prepared(Box<PreparedBookmarkCommandProduct>),
}
impl fmt::Debug for BookmarkCommandRequestEntry {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(match self {
            Self::Existing(_) => {
                "BookmarkCommandRequestEntry::Existing(<redacted>; no_retry_grant)"
            }
            Self::Prepared(_) => {
                "BookmarkCommandRequestEntry::Prepared(<redacted>; route_unqualified)"
            }
        })
    }
}
impl StoredProductRequest {
    /// # Errors
    /// Strict typed request before source access; no raw commands/maps/results.
    pub fn prepare_bookmark_commands_json<R, B, S, V>(
        provider: &StoredFormProvider<'_, R, B, S, V>,
        raw: &[u8],
        limits: BookmarkCommandProductLimits,
        now: u64,
    ) -> Result<PreparedBookmarkCommandProduct, E>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        prepare(
            provider,
            ParsedBookmarkCommandRequest::parse(raw, limits)?,
            raw,
            limits,
            now,
        )
    }
    /// # Errors
    /// Pure request/scope binding, no head/source reads or key claim.
    pub fn prepare_bookmark_commands_lookup_json<R, B, S, V>(
        provider: &StoredFormProvider<'_, R, B, S, V>,
        raw: &[u8],
        limits: BookmarkCommandProductLimits,
    ) -> Result<PreparedBookmarkCommandLookup, E>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        ParsedBookmarkCommandRequest::parse(raw, limits)?.lookup(provider)
    }
    /// # Errors
    /// Existing or lookup errors never fall back to new source/compiler work.
    /// NotObserved permits only preparation, never an absence lease or execution.
    pub fn prepare_bookmark_commands_or_observe_json<R, B, S, V>(
        provider: &StoredFormProvider<'_, R, B, S, V>,
        raw: &[u8],
        limits: BookmarkCommandProductLimits,
        now: u64,
    ) -> Result<BookmarkCommandRequestEntry, E>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: StoredRequestLookupRepository,
    {
        let request = ParsedBookmarkCommandRequest::parse(raw, limits)?;
        match request.lookup(provider)?.observe(provider)? {
            StoredRequestObservation::Existing(job) => {
                Ok(BookmarkCommandRequestEntry::Existing(job))
            }
            StoredRequestObservation::NotObserved => Ok(BookmarkCommandRequestEntry::Prepared(
                Box::new(prepare(provider, request, raw, limits, now)?),
            )),
        }
    }
}
pub(super) fn prepare<R, B, S, V>(
    provider: &StoredFormProvider<'_, R, B, S, V>,
    request: ParsedBookmarkCommandRequest,
    raw: &[u8],
    limits: BookmarkCommandProductLimits,
    now: u64,
) -> Result<PreparedBookmarkCommandProduct, E>
where
    R: ArtifactMetadataRepository,
    B: EncryptedBlobStore,
    S: ArtifactScanner,
    V: RevisionRepository,
{
    let scope = provider.source_search_product_scope(&request.project_id, &request.document_id)?;
    let canonical = request.canonical()?;
    let scoped = request.scoped(scope, &canonical)?;
    let source = provider.import_actual_forms(request.head()?, now)?;
    if hex::encode(source.receipt().imported.source_package_sha256)
        != request.expected_source_package_sha256
    {
        return Err(E::Binding);
    }
    let mut changes = Vec::new();
    changes
        .try_reserve_exact(request.operation.changes.len())
        .map_err(|_| E::Limit)?;
    for change in &request.operation.changes {
        changes.push(SourceBookmarkCommandChange {
            reference_id: &change.reference_id,
            expected_source_field_sha256: *ContentDigest::parse(
                &change.expected_source_field_sha256,
            )
            .map_err(|_| E::Request)?
            .as_bytes(),
            expected_meaning_sha256: *ContentDigest::parse(&change.expected_meaning_sha256)
                .map_err(|_| E::Request)?
                .as_bytes(),
            target_id: &change.target_id,
            display: change.display.sdk(),
            hyperlink: change.hyperlink,
        });
    }
    let candidate = source.into_bookmark_command_candidate(
        provider,
        &changes,
        limits.auxiliary,
        limits.writer,
        now,
    )?;
    drop(changes);
    let candidate = candidate.compile(provider, request.plan_id.clone(), now)?;
    let receipt = BookmarkCommandProductReceipt {
        profile: PROFILE,
        request_schema: BOOKMARK_COMMAND_PRODUCT_REQUEST_SCHEMA,
        raw_request_sha256: digest(raw),
        canonical_request_sha256: canonical,
        scoped_request_sha256: scoped,
        compiled: candidate.receipt().clone(),
        idempotency_key_claimed: false,
        execution_or_publication_authority: false,
    };
    let product = PreparedBookmarkCommandProduct {
        request,
        candidate,
        receipt,
    };
    product.check(provider)?;
    Ok(product)
}
impl PreparedBookmarkCommandProduct {
    #[must_use]
    pub const fn receipt(&self) -> &BookmarkCommandProductReceipt {
        &self.receipt
    }
    #[must_use]
    pub const fn compiled(&self) -> &CompiledOperationPlan {
        self.candidate.compiled()
    }
    fn check<R, B, S, V>(&self, provider: &StoredFormProvider<'_, R, B, S, V>) -> Result<(), E>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        let request = &self.request;
        let scope =
            provider.source_search_product_scope(&request.project_id, &request.document_id)?;
        let canonical = request.canonical()?;
        if self.receipt.profile != PROFILE
            || self.receipt.request_schema != BOOKMARK_COMMAND_PRODUCT_REQUEST_SCHEMA
            || self.receipt.canonical_request_sha256 != canonical
            || self.receipt.scoped_request_sha256 != request.scoped(scope, &canonical)?
            || &self.receipt.compiled != self.candidate.receipt()
            || self.compiled().plan_id() != &request.plan_id
            || self.compiled().base_revision() != &request.base_revision
            || self.receipt.compiled.head_generation != request.expected_head_generation
            || hex::encode(self.receipt.compiled.source_package_sha256)
                != request.expected_source_package_sha256
            || self.compiled().operations().len() != request.operation.changes.len()
            || self.receipt.idempotency_key_claimed
            || self.receipt.execution_or_publication_authority
        {
            return Err(E::Binding);
        }
        Ok(())
    }
    /// # Errors
    /// Request/plan binding plus original current source authorization only.
    pub fn verify<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<&BookmarkCommandProductReceipt, E>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.check(provider)?;
        self.candidate.verify(provider, now)?;
        Ok(&self.receipt)
    }
    /// # Errors
    /// Original final ACL/AEAD/head and writer callback remains the sole delivery.
    pub fn with_verified_bytes<R, B, S, V, T>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
        consume: impl FnOnce(&[u8]) -> T,
    ) -> Result<T, E>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.check(provider)?;
        Ok(self.candidate.with_verified_bytes(provider, now, consume)?)
    }
    /// # Errors
    /// A product request is not a registered route, durable job or write grant.
    pub fn require_current_product_route<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<(), E>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.check(provider)?;
        Ok(self
            .candidate
            .require_current_product_route(provider, now)?)
    }
}
impl PreparedStoredProductOperation {
    #[must_use]
    pub fn as_bookmark_commands(&self) -> Option<&PreparedBookmarkCommandProduct> {
        match self {
            Self::BookmarkCommands(v) => Some(v),
            _ => None,
        }
    }
}
