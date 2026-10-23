//! Revision-selected stored comment preparation on the ORIGINAL source/IR readers and compiler.
//! Storage authentication does not establish native comment semantics or execution authority.
pub mod rich_bodies;
use super::{SourceSnapshot, StoredFormError, StoredFormProvider, full_document::IrSnapshot};
use crate::comment_operation::{
    COMMENT_STATE_PROPERTY, CommentInsertionTarget, CommentOperationContext,
    CommentOperationPreparation, CommentOperationReceipt, PreparedCommentOperation,
};
use artifact_service::{ArtifactMetadataRepository, ArtifactScanner, EncryptedBlobStore};
use domain_ir::{
    CommentDocumentState, CommentDocumentStateDraft, CommentLimitConfig, CommentLimits,
    CompiledOperationPlan, DocumentGraph, PlanId, PropertyValue, RevisionId,
};
use revision_service::{RevisionHead, RevisionRepository};
use serde::Serialize;
use std::fmt;
use thiserror::Error;

pub const STORED_COMMENT_PROFILE: &str = "hwpx-agent.product-stored-comment-preparation/v1";

/// Request/anchor only. Source, IR, complete state and hashes are selected by the sealed revision.
/// The insertion binding remains a logical caller input, NOT a qualified native coordinate map.
pub struct StoredCommentInputs<'a> {
    pub expected_head: RevisionHead,
    pub plan_id: PlanId,
    pub request_json: &'a [u8],
    pub insertion: Option<CommentInsertionTarget>,
}
impl fmt::Debug for StoredCommentInputs<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("StoredCommentInputs(<redacted>)")
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct StoredCommentReceipt {
    pub profile: &'static str,
    pub source_sha256: String,
    pub source_bytes: usize,
    pub head_generation: u64,
    pub ir_artifact_sha256: String,
    pub operation: CommentOperationReceipt,
    pub qualification: StoredCommentQualification,
}
#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum StoredCommentQualification {
    ActualServiceSnapshotOnlyNativeImportLoweringIssuerAtomicExecutionPublicationAndGateUnqualified,
}

/// Immutable, non-deserializable preparation. No artifact writer, revision commit or key claim.
pub struct PreparedStoredComment {
    source: SourceSnapshot,
    snapshot: IrSnapshot,
    state: CommentDocumentState,
    operation: PreparedCommentOperation,
    receipt: StoredCommentReceipt,
}
impl fmt::Debug for PreparedStoredComment {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("PreparedStoredComment(<redacted>)")
    }
}

impl<R, B, S, V> StoredFormProvider<'_, R, B, S, V>
where
    R: ArtifactMetadataRepository,
    B: EncryptedBlobStore,
    S: ArtifactScanner,
    V: RevisionRepository,
{
    /// Uses the original sealed result and committed IR loaders, never caller artifact IDs/state.
    /// # Errors
    /// Rejects stale head, independent ACL/state/AEAD failures, noncanonical/partial IR,
    /// wrong document, absent complete comment state or any original compiler failure.
    pub fn prepare_comment_json(
        &self,
        inputs: StoredCommentInputs<'_>,
        now: u64,
    ) -> Result<PreparedStoredComment, StoredCommentError> {
        let source = self.source(inputs.expected_head, now)?;
        let snapshot = self.full_document_ir(&source, now)?;
        if snapshot.graph.document_id() != &self.scope.document {
            return Err(StoredCommentError::Scope);
        }
        let state = stored_state(&snapshot.graph)?;
        let context = context(&source, &snapshot, &state)?;
        let operation = CommentOperationPreparation::prepare_json(
            &context,
            inputs.plan_id,
            inputs.request_json,
            inputs.insertion,
        )
        .map_err(|_| StoredCommentError::Preparation)?;
        self.check_head(source.head)?;
        let receipt = receipt(&source, &snapshot, operation.receipt());
        let prepared = PreparedStoredComment {
            source,
            snapshot,
            state,
            operation,
            receipt,
        };
        prepared.verify(self, now)?;
        Ok(prepared)
    }
}

fn stored_state(graph: &DocumentGraph) -> Result<CommentDocumentState, StoredCommentError> {
    let json = graph
        .metadata()
        .iter()
        .find_map(|(key, value)| {
            if key == COMMENT_STATE_PROPERTY
                && let PropertyValue::Text(json) = value
            {
                return Some(json.as_bytes());
            }
            None
        })
        .ok_or(StoredCommentError::State)?;
    let config = CommentLimitConfig::default();
    if json.is_empty() || json.len() > config.input_bytes {
        return Err(StoredCommentError::State);
    }
    let limits = CommentLimits::new(config).map_err(|_| StoredCommentError::State)?;
    let raw: CommentDocumentStateDraft =
        serde_json::from_slice(json).map_err(|_| StoredCommentError::State)?;
    let state =
        CommentDocumentState::from_draft(raw, limits).map_err(|_| StoredCommentError::State)?;
    // Reject duplicate/unknown/lexical aliases and missing data. No author/time/style defaults.
    if state
        .canonical_json(limits)
        .map_err(|_| StoredCommentError::State)?
        != json
    {
        return Err(StoredCommentError::State);
    }
    Ok(state)
}

fn context<'a>(
    source: &SourceSnapshot,
    snapshot: &'a IrSnapshot,
    state: &'a CommentDocumentState,
) -> Result<CommentOperationContext<'a>, StoredCommentError> {
    let revision = RevisionId::parse(
        source
            .head
            .revision_id()
            .ok_or(StoredCommentError::Drift)?
            .public_id(),
    )
    .map_err(|_| StoredCommentError::Drift)?;
    CommentOperationContext::bind(
        &snapshot.graph,
        state,
        *snapshot.binding.canonical_graph_sha256.as_bytes(),
        *snapshot.binding.result_package_sha256.as_bytes(),
        revision,
    )
    .map_err(|_| StoredCommentError::Preparation)
}

fn receipt(
    source: &SourceSnapshot,
    snapshot: &IrSnapshot,
    operation: &CommentOperationReceipt,
) -> StoredCommentReceipt {
    StoredCommentReceipt {
        profile: STORED_COMMENT_PROFILE,
        source_sha256: source.digest.hex(),
        source_bytes: source.bytes.len(),
        head_generation: source.head.generation(),
        ir_artifact_sha256: snapshot.binding.artifact_sha256.hex(),
        operation: operation.clone(),
        qualification: StoredCommentQualification::ActualServiceSnapshotOnlyNativeImportLoweringIssuerAtomicExecutionPublicationAndGateUnqualified,
    }
}

impl PreparedStoredComment {
    #[must_use]
    pub const fn receipt(&self) -> &StoredCommentReceipt {
        &self.receipt
    }
    /// Memory candidate only; not lowered HWPX, a result artifact or an authorized route.
    #[must_use]
    pub const fn target_graph(&self) -> &DocumentGraph {
        self.operation.target_graph()
    }
    #[must_use]
    pub const fn compiled_plan(&self) -> &CompiledOperationPlan {
        self.operation.compiled()
    }
    /// Fresh original service head/node/ACL/state/AEAD/whole-byte checks and full compiler replay.
    /// # Errors
    /// Rejects a different provider actor/scope or any result, IR, complete state or plan drift.
    /// These reads emit normal access audits, but do NOT provide atomic CAS or publication.
    pub fn verify<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<StoredCommentReceipt, StoredCommentError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        if self.source.scope != provider.scope {
            return Err(StoredCommentError::Scope);
        }
        let fresh = provider.source(self.source.head, now)?;
        if fresh.artifact != self.source.artifact
            || fresh.digest != self.source.digest
            || fresh.bytes != self.source.bytes
        {
            return Err(StoredCommentError::Drift);
        }
        let snapshot = provider.full_document_ir(&fresh, now)?;
        if snapshot.binding != self.snapshot.binding || snapshot.graph != self.snapshot.graph {
            return Err(StoredCommentError::Drift);
        }
        let state = stored_state(&snapshot.graph)?;
        if state != self.state {
            return Err(StoredCommentError::Drift);
        }
        let context = context(&fresh, &snapshot, &state)?;
        let operation = self
            .operation
            .verify(&context)
            .map_err(|_| StoredCommentError::Drift)?;
        provider.check_head(fresh.head)?;
        let checked = receipt(&fresh, &snapshot, &operation);
        if checked != self.receipt {
            return Err(StoredCommentError::Drift);
        }
        Ok(checked)
    }
    /// Always denies the current unqualified product route AFTER fresh complete verification.
    /// # Errors
    /// Any source/permission drift is reported first; otherwise `RouteUnqualified`.
    pub fn require_current_product_route<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<(), StoredCommentError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.verify(provider, now)?;
        Err(StoredCommentError::RouteUnqualified)
    }
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum StoredCommentError {
    #[error("stored_comment_scope_invalid")]
    Scope,
    #[error("stored_comment_source_invalid: {0}")]
    Source(#[from] StoredFormError),
    #[error("stored_comment_ir_invalid: {0}")]
    Ir(#[from] super::full_document::StoredFullDocumentFormError),
    #[error("stored_comment_complete_state_invalid")]
    State,
    #[error("stored_comment_preparation_invalid")]
    Preparation,
    #[error("stored_comment_snapshot_drift")]
    Drift,
    #[error("stored_comment_route_unqualified")]
    RouteUnqualified,
}
