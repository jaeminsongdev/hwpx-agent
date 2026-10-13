//! Sealed revision-selected document IR -> actual ACL/AEAD download -> full-graph preparation.
//! An available verified artifact is storage/scanner evidence, never native import provenance.
use super::{
    MAX_SOURCE_BYTES, PreparedStoredForm, SourceSnapshot, StoredFormInputs, StoredFormProvider,
    StoredFormReceipt,
};
use crate::form_value_operation::{
    FormOperationContext,
    full_document::{
        FullDocumentFormContext, FullDocumentFormPreparation, FullDocumentFormReceipt,
        PreparedFullDocumentForms,
    },
};
use artifact_service::{
    ArtifactKind, ArtifactMetadataRepository, ArtifactScanner, ContentDigest, EncryptedBlobStore,
    StorageState, ValidationState,
};
use domain_ir::{
    CompiledOperationPlan, DocumentGraph, DocumentGraphLimits, RevisionId,
    form_input::FormInputAccessPolicy,
};
use hwpx_package::{NativeFormPackageMap, NativeFormPackagePolicy};
use revision_service::{FullDocumentIrBinding, RevisionRepository};
use serde::Serialize;
use std::fmt;
use thiserror::Error;

pub const DOCUMENT_IR_MEDIA_TYPE: &str = "application/vnd.hwpx-agent.document-graph+json";
const PROFILE: &str = "hwpx-agent.product-stored-full-document-form/v1";

struct IrSnapshot {
    binding: FullDocumentIrBinding,
    graph: DocumentGraph,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct StoredFullDocumentFormReceipt {
    pub profile: &'static str,
    pub stored: StoredFormReceipt,
    pub full_document: FullDocumentFormReceipt,
    pub ir_artifact_sha256: String,
    pub qualification: StoredFullDocumentFormQualification,
}
#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum StoredFullDocumentFormQualification {
    ActualServicesStoredSnapshotOnlyDurableIrLinkImportRoutePublicationNativeAndGateUnqualified,
}

/// Owns exact immutable IR/package/compiled-plan snapshots. No artifact write or CAS capability.
pub struct PreparedStoredFullDocumentForm {
    stored: PreparedStoredForm,
    snapshot: IrSnapshot,
    full: PreparedFullDocumentForms,
    receipt: StoredFullDocumentFormReceipt,
}
impl fmt::Debug for PreparedStoredFullDocumentForm {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("PreparedStoredFullDocumentForm(<redacted>)")
    }
}

impl<R, B, S, V> StoredFormProvider<'_, R, B, S, V>
where
    R: ArtifactMetadataRepository,
    B: EncryptedBlobStore,
    S: ArtifactScanner,
    V: RevisionRepository,
{
    fn full_document_ir(
        &self,
        source: &SourceSnapshot,
        now: u64,
    ) -> Result<IrSnapshot, StoredFullDocumentFormError> {
        self.check_head(source.head)
            .map_err(|_| StoredFullDocumentFormError::Head)?;
        let revision = source
            .head
            .revision_id()
            .ok_or(StoredFullDocumentFormError::Head)?;
        let node = self
            .revisions
            .node(self.revision_context, self.scope.project, revision)
            .map_err(|_| StoredFullDocumentFormError::Head)?;
        if !node.sealed()
            || node.project_id() != self.scope.project
            || node.revision_id() != revision
            || node.committed_generation() != source.head.generation()
            || node.result_artifact_id() != source.artifact
        {
            return Err(StoredFullDocumentFormError::Head);
        }
        let binding = node
            .full_document_ir()
            .ok_or(StoredFullDocumentFormError::MissingIr)?;
        if binding.result_package_sha256 != source.digest {
            return Err(StoredFullDocumentFormError::Binding);
        }
        let descriptor = self
            .artifacts
            .get_descriptor(self.artifact_context, binding.artifact_id, now)
            .map_err(|_| StoredFullDocumentFormError::Artifact)?;
        if descriptor.artifact_id != binding.artifact_id
            || descriptor.kind != ArtifactKind::DocumentIr
            || descriptor.media_type.as_str() != DOCUMENT_IR_MEDIA_TYPE
            || descriptor.storage_state != StorageState::Available
            || descriptor.validation_state != ValidationState::Verified
            || descriptor.quarantine_reason.is_some()
            || descriptor.size_bytes == 0
            || descriptor.size_bytes > MAX_SOURCE_BYTES as u64
            || descriptor.sha256 != binding.artifact_sha256
        {
            return Err(StoredFullDocumentFormError::Artifact);
        }
        let bytes = self
            .artifacts
            .download(self.artifact_context, binding.artifact_id, now)
            .map_err(|_| StoredFullDocumentFormError::Artifact)?;
        if bytes.is_empty()
            || bytes.len() > MAX_SOURCE_BYTES
            || bytes.len() as u64 != descriptor.size_bytes
            || ContentDigest::of(&bytes) != binding.artifact_sha256
        {
            return Err(StoredFullDocumentFormError::Artifact);
        }
        let graph = DocumentGraph::from_json(&bytes, DocumentGraphLimits::default())
            .map_err(|_| StoredFullDocumentFormError::Graph)?;
        // Exact canonical bytes are required. Duplicate keys, lexical aliases and hidden trailing
        // properties cannot be admitted merely because deserialization selected a value.
        if graph
            .canonical_json()
            .map_err(|_| StoredFullDocumentFormError::Graph)?
            != bytes
            || graph
                .canonical_sha256()
                .map_err(|_| StoredFullDocumentFormError::Graph)?
                != *binding.canonical_graph_sha256.as_bytes()
        {
            return Err(StoredFullDocumentFormError::Graph);
        }
        self.check_head(source.head)
            .map_err(|_| StoredFullDocumentFormError::Head)?;
        Ok(IrSnapshot { binding, graph })
    }

    /// Reads only the sealed current revision's IR and actual result; no public artifact selector.
    /// # Errors
    /// Rejects absent/stale IR/head, independent ACL/state/media/digest/AEAD/canonical/schema
    /// failures and all original/full-document form preparation failures. No result/IR is ingested.
    pub fn prepare_full_document_json(
        &self,
        inputs: StoredFormInputs<'_>,
        now: u64,
    ) -> Result<PreparedStoredFullDocumentForm, StoredFullDocumentFormError> {
        let (map, policies, access) = (inputs.map, inputs.policies, inputs.access);
        let stored = self
            .prepare_json(inputs, now)
            .map_err(|_| StoredFullDocumentFormError::Source)?;
        let snapshot = self.full_document_ir(&stored.source, now)?;
        let context = ir_context(&snapshot, &stored)?;
        let native = FormOperationContext::bind(&stored.source.bytes, map, policies)
            .map_err(|_| StoredFullDocumentFormError::Preparation)?;
        let full =
            FullDocumentFormPreparation::prepare(&context, &stored.operation, &native, access)
                .map_err(|_| StoredFullDocumentFormError::Preparation)?;
        let receipt = StoredFullDocumentFormReceipt {
            profile: PROFILE, stored: stored.receipt().clone(), full_document: full.receipt().clone(),
            ir_artifact_sha256: snapshot.binding.artifact_sha256.hex(),
            qualification: StoredFullDocumentFormQualification::ActualServicesStoredSnapshotOnlyDurableIrLinkImportRoutePublicationNativeAndGateUnqualified,
        };
        let prepared = PreparedStoredFullDocumentForm {
            stored,
            snapshot,
            full,
            receipt,
        };
        prepared.verify(self, map, policies, access, now)?;
        Ok(prepared)
    }
}

fn ir_context<'a>(
    snapshot: &'a IrSnapshot,
    stored: &PreparedStoredForm,
) -> Result<FullDocumentFormContext<'a>, StoredFullDocumentFormError> {
    let revision = RevisionId::parse(
        stored
            .source
            .head
            .revision_id()
            .ok_or(StoredFullDocumentFormError::Head)?
            .public_id(),
    )
    .map_err(|_| StoredFullDocumentFormError::Binding)?;
    FullDocumentFormContext::bind(
        &snapshot.graph,
        *snapshot.binding.canonical_graph_sha256.as_bytes(),
        *snapshot.binding.result_package_sha256.as_bytes(),
        revision,
    )
    .map_err(|_| StoredFullDocumentFormError::Preparation)
}

impl PreparedStoredFullDocumentForm {
    #[must_use]
    pub const fn receipt(&self) -> &StoredFullDocumentFormReceipt {
        &self.receipt
    }
    #[must_use]
    pub fn candidate_bytes(&self) -> &[u8] {
        self.stored.candidate_bytes()
    }
    #[must_use]
    pub const fn target_graph(&self) -> &DocumentGraph {
        self.full.target_graph()
    }
    #[must_use]
    pub const fn compiled_plan(&self) -> &CompiledOperationPlan {
        self.full.compiled_plan()
    }
    /// Independently re-downloads the revision-selected IR and verifies the entire old source.
    /// # Errors
    /// Rejects fresh scope/head/ACL/artifact/state/content/schema/map/policy/access drift.
    pub fn verify<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        map: &NativeFormPackageMap,
        policies: &[NativeFormPackagePolicy],
        access: &FormInputAccessPolicy,
        now: u64,
    ) -> Result<StoredFullDocumentFormReceipt, StoredFullDocumentFormError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        let stored_receipt = self
            .stored
            .verify(provider, map, policies, access, now)
            .map_err(|_| StoredFullDocumentFormError::Source)?;
        let fresh = provider.full_document_ir(&self.stored.source, now)?;
        if fresh.binding != self.snapshot.binding || fresh.graph != self.snapshot.graph {
            return Err(StoredFullDocumentFormError::Binding);
        }
        let native = FormOperationContext::bind(&self.stored.source.bytes, map, policies)
            .map_err(|_| StoredFullDocumentFormError::Preparation)?;
        let full_receipt = self
            .full
            .verify(
                &ir_context(&fresh, &self.stored)?,
                &self.stored.operation,
                &native,
                access,
            )
            .map_err(|_| StoredFullDocumentFormError::Preparation)?;
        provider
            .check_head(self.stored.source.head)
            .map_err(|_| StoredFullDocumentFormError::Head)?;
        if self.receipt.profile != PROFILE
            || self.receipt.stored != stored_receipt
            || self.receipt.full_document != full_receipt
            || self.receipt.ir_artifact_sha256 != fresh.binding.artifact_sha256.hex()
        {
            return Err(StoredFullDocumentFormError::Binding);
        }
        Ok(self.receipt.clone())
    }
    /// Consultation of the real existing signed scope never grants this unqualified route.
    /// # Errors
    /// First rejects all fresh source/IR drift, then denies unsupported form publication.
    pub fn require_current_product_route<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        map: &NativeFormPackageMap,
        policies: &[NativeFormPackagePolicy],
        access: &FormInputAccessPolicy,
        now: u64,
    ) -> Result<(), StoredFullDocumentFormError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.verify(provider, map, policies, access, now)?;
        self.stored
            .require_current_product_route(provider, map, policies, access, now)
            .map_err(|_| StoredFullDocumentFormError::RouteUnqualified)?;
        // Even future operation-level scope is not full importer/durable IR/product acceptance.
        Err(StoredFullDocumentFormError::RouteUnqualified)
    }
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum StoredFullDocumentFormError {
    #[error("stored_full_document_form_source_rejected")]
    Source,
    #[error("stored_full_document_form_head_rejected")]
    Head,
    #[error("stored_full_document_form_ir_missing")]
    MissingIr,
    #[error("stored_full_document_form_ir_artifact_rejected")]
    Artifact,
    #[error("stored_full_document_form_ir_graph_rejected")]
    Graph,
    #[error("stored_full_document_form_ir_binding_drift")]
    Binding,
    #[error("stored_full_document_form_preparation_rejected")]
    Preparation,
    #[error("stored_full_document_form_signed_route_unqualified")]
    RouteUnqualified,
}
