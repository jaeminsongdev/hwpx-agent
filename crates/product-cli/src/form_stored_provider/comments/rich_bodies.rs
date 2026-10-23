//! Revision-selected persisted caller-complete review Flows -> original rich comment compiler.
//! Native source import, metadata, SQL durability and atomic publication remain unqualified.
use super::{StoredCommentError, StoredCommentInputs, context, stored_state};
use crate::{
    comment_operation::rich_bodies::{
        COMMENT_RICH_BODIES_PROPERTY, CommentRichBody, CommentRichContext, CommentRichReceipt,
        PreparedRichCommentOperation, RichCommentOperationPreparation, bodies_json,
    },
    form_stored_provider::{SourceSnapshot, StoredFormProvider, full_document::IrSnapshot},
};
use artifact_service::{ArtifactMetadataRepository, ArtifactScanner, EncryptedBlobStore};
use domain_ir::{
    CommentDocumentState, CompiledOperationPlan, DocumentGraph, Flow, LogicalId, PropertyValue,
};
use revision_service::RevisionRepository;
use serde::{Deserialize, Serialize};
use std::fmt;

const MAX_BODY_BYTES: usize = 8 * 1024 * 1024;
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct StoredBodyDraft {
    review_id: LogicalId,
    body: Flow,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct StoredRichCommentReceipt {
    pub qualification: &'static str,
    pub source_sha256: String,
    pub source_bytes: usize,
    pub head_generation: u64,
    pub ir_artifact_sha256: String,
    pub operation: CommentRichReceipt,
}
pub struct PreparedStoredRichComment {
    source: SourceSnapshot,
    snapshot: IrSnapshot,
    state: CommentDocumentState,
    operation: PreparedRichCommentOperation,
    receipt: StoredRichCommentReceipt,
}
impl fmt::Debug for PreparedStoredRichComment {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("PreparedStoredRichComment(<redacted>)")
    }
}
impl<R, B, S, V> StoredFormProvider<'_, R, B, S, V>
where
    R: ArtifactMetadataRepository,
    B: EncryptedBlobStore,
    S: ArtifactScanner,
    V: RevisionRepository,
{
    /// Loads every EXISTING body from the original revision-selected authenticated IR artifact.
    /// Only a NEW insertion body is supplied by the caller, under the original logical request.
    /// No public source/IR selector, persisted body override, ingest, commit or authority claim.
    /// # Errors
    /// Rejects original independent source/IR admission, stale scope/head, noncanonical/incomplete
    /// body inventories and every original full document/rich compiler failure.
    pub fn prepare_rich_comment_json(
        &self,
        inputs: StoredCommentInputs<'_>,
        inserted_body: Option<CommentRichBody>,
        now: u64,
    ) -> Result<PreparedStoredRichComment, StoredCommentError> {
        let source = self.source(inputs.expected_head, now)?;
        let snapshot = self.full_document_ir(&source, now)?;
        if snapshot.graph.document_id() != &self.scope.document {
            return Err(StoredCommentError::Scope);
        }
        let state = stored_state(&snapshot.graph)?;
        let base = context(&source, &snapshot, &state)?;
        let rich = CommentRichContext::bind(&base, stored_bodies(&snapshot.graph)?)
            .map_err(|_| StoredCommentError::Preparation)?;
        let operation = RichCommentOperationPreparation::prepare_json(
            &rich,
            inputs.plan_id,
            inputs.request_json,
            inputs.insertion,
            inserted_body,
        )
        .map_err(|_| StoredCommentError::Preparation)?;
        self.check_head(source.head)?;
        let receipt = receipt(&source, &snapshot, operation.receipt());
        let prepared = PreparedStoredRichComment {
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
// This private deserializer reads only the downloaded graph's exact root property. It cannot
// deserialize a prepared body/receipt or bypass original canonical artifact/state admission.
fn stored_bodies(graph: &DocumentGraph) -> Result<Vec<CommentRichBody>, StoredCommentError> {
    let json = graph
        .metadata()
        .iter()
        .find_map(|(key, value)| {
            if key == COMMENT_RICH_BODIES_PROPERTY
                && let PropertyValue::Text(json) = value
            {
                Some(json.as_bytes())
            } else {
                None
            }
        })
        .ok_or(StoredCommentError::State)?;
    if json.is_empty() || json.len() > MAX_BODY_BYTES {
        return Err(StoredCommentError::State);
    }
    let raw: Vec<StoredBodyDraft> =
        serde_json::from_slice(json).map_err(|_| StoredCommentError::State)?;
    let bodies = raw
        .into_iter()
        .map(|raw| CommentRichBody {
            review_id: raw.review_id,
            body: raw.body,
        })
        .collect::<Vec<_>>();
    // Whole inner-string canonical equality rejects duplicates, unknown keys, trailing lexical
    // aliases and missing typed fields. A canonical outer graph cannot vouch for its JSON string.
    if bodies_json(&bodies)
        .map_err(|_| StoredCommentError::State)?
        .as_bytes()
        != json
    {
        return Err(StoredCommentError::State);
    }
    Ok(bodies)
}
fn receipt(
    source: &SourceSnapshot,
    snapshot: &IrSnapshot,
    operation: &CommentRichReceipt,
) -> StoredRichCommentReceipt {
    StoredRichCommentReceipt {
        qualification: "original_authenticated_revision_selected_IR_rich_body_final_compiler_binding_NOT_native_source_import_SQL_issuer_atomic_execution_publication_or_Gate",
        source_sha256: source.digest.hex(),
        source_bytes: source.bytes.len(),
        head_generation: source.head.generation(),
        ir_artifact_sha256: snapshot.binding.artifact_sha256.hex(),
        operation: operation.clone(),
    }
}
impl PreparedStoredRichComment {
    #[must_use]
    pub const fn receipt(&self) -> &StoredRichCommentReceipt {
        &self.receipt
    }
    #[must_use]
    pub const fn target_graph(&self) -> &DocumentGraph {
        self.operation.target_graph()
    }
    #[must_use]
    pub const fn compiled_plan(&self) -> &CompiledOperationPlan {
        self.operation.compiled()
    }
    #[must_use]
    pub fn target_bodies(&self) -> &[CommentRichBody] {
        self.operation.target_bodies()
    }
    /// Re-download original sealed source/IR with independent ACL/AEAD/admission and replay.
    /// Repeated reads audit access but do NOT supply an atomic lease or publication authority.
    /// # Errors
    /// Rejects any fresh actor/scope/head/package/IR/state/body/compiled plan or receipt drift.
    pub fn verify<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<StoredRichCommentReceipt, StoredCommentError>
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
        let base = context(&fresh, &snapshot, &state)?;
        let rich = CommentRichContext::bind(&base, stored_bodies(&snapshot.graph)?)
            .map_err(|_| StoredCommentError::Drift)?;
        let operation = self
            .operation
            .verify(&rich)
            .map_err(|_| StoredCommentError::Drift)?;
        provider.check_head(fresh.head)?;
        let checked = receipt(&fresh, &snapshot, &operation);
        if checked != self.receipt {
            return Err(StoredCommentError::Drift);
        }
        Ok(checked)
    }
    /// Fresh failures precede the original unqualified route; no execution capability is added.
    /// # Errors
    /// Always rejects after full source/IR/body/compiler replay, or reports its fresh failure.
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
