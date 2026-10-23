//! Actual stored revision result -> tenant/scope/ACL/AEAD checked source -> form compiler.
//! Content/head reads emit the artifact service's normal access audit; no content publication.
//! Two head reads are not atomic CAS; contexts are provider-authenticated inputs, not an issuer.
pub mod actual_import;
pub mod comments;
pub mod full_document;
use crate::form_value_operation::{
    FormOperationContext, FormOperationIdentity, FormOperationPreparation, FormOperationReceipt,
    PreparedFormOperation,
};
use artifact_service::{
    ArtifactId, ArtifactKind, ArtifactMetadataRepository, ArtifactScanner, ArtifactService,
    AuthScope, ContentDigest, EncryptedBlobStore, RequestContext, StorageState, SubjectDigest,
    TenantId, ValidationState,
};
use domain_ir::{DocumentId, PlanId, RevisionId, form_input::FormInputAccessPolicy};
use hwpx_package::{NativeFormPackageMap, NativeFormPackagePolicy};
use revision_service::{
    BranchId, ProjectId, RevisionHead, RevisionRepository, RevisionRequestContext, RevisionService,
};
use serde::Serialize;
use std::fmt;
use thiserror::Error;

pub const STORED_FORM_SOURCE_PROFILE: &str = "hwpx-agent.product-stored-form-source/v1";
const MAX_SOURCE_BYTES: usize = 32 * 1024 * 1024;

#[derive(Clone, Eq, PartialEq)]
struct Scope {
    tenant: TenantId,
    subject: SubjectDigest,
    project: ProjectId,
    branch: BranchId,
    document: DocumentId,
}

/// Services and identities are owned by the authenticated provider, not public JSON.
/// No caller-selected artifact ID, path, key, scanner verdict or approval bit is accepted.
pub struct StoredFormProvider<'a, R, B, S, V> {
    artifacts: &'a ArtifactService<R, B, S>,
    revisions: &'a RevisionService<V>,
    artifact_context: &'a RequestContext,
    revision_context: &'a RevisionRequestContext,
    scope: Scope,
}
impl<R, B, S, V> fmt::Debug for StoredFormProvider<'_, R, B, S, V> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("StoredFormProvider(<redacted>)")
    }
}

/// Bounded form request and provider-owned native bindings. No route authorization.
pub struct StoredFormInputs<'a> {
    pub expected_head: RevisionHead,
    pub plan_id: PlanId,
    pub form_input_json: &'a [u8],
    pub map: &'a NativeFormPackageMap,
    pub policies: &'a [NativeFormPackagePolicy],
    pub access: &'a FormInputAccessPolicy,
}
impl fmt::Debug for StoredFormInputs<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("StoredFormInputs(<redacted>)")
    }
}

struct SourceSnapshot {
    scope: Scope,
    head: RevisionHead,
    artifact: ArtifactId,
    digest: ContentDigest,
    bytes: Vec<u8>,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct StoredFormReceipt {
    pub profile: &'static str,
    pub source_sha256: String,
    pub source_bytes: usize,
    pub head_generation: u64,
    pub operation: FormOperationReceipt,
    pub qualification: StoredFormQualification,
}
#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum StoredFormQualification {
    ActualServiceSourcePreflightOnlyIssuerFullImportAtomicCasIdempotencyRoutePublicationNativeAndGateUnqualified,
}

/// Private, non-deserializable actual stored source and original complete preparation.
pub struct PreparedStoredForm {
    source: SourceSnapshot,
    operation: PreparedFormOperation,
    receipt: StoredFormReceipt,
}
impl fmt::Debug for PreparedStoredForm {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("PreparedStoredForm(<redacted>)")
    }
}

impl<'a, R, B, S, V> StoredFormProvider<'a, R, B, S, V>
where
    R: ArtifactMetadataRepository,
    B: EncryptedBlobStore,
    S: ArtifactScanner,
    V: RevisionRepository,
{
    /// Binds trusted provider scopes; independently checks both service identities and read scope.
    /// # Errors
    /// Rejects mismatched tenant/subject, absent read scope or oversized document identity.
    pub fn bind(
        artifacts: &'a ArtifactService<R, B, S>,
        revisions: &'a RevisionService<V>,
        artifact_context: &'a RequestContext,
        revision_context: &'a RevisionRequestContext,
        project: ProjectId,
        branch: BranchId,
        document: DocumentId,
    ) -> Result<Self, StoredFormError> {
        if artifact_context.tenant_id() != revision_context.tenant_id()
            || artifact_context.subject() != revision_context.subject()
            || !artifact_context.has_scope(AuthScope::DocumentRead)
            || document.as_str().len() > 1024
        {
            return Err(StoredFormError::Scope);
        }
        Ok(Self {
            artifacts,
            revisions,
            artifact_context,
            revision_context,
            scope: Scope {
                tenant: artifact_context.tenant_id(),
                subject: artifact_context.subject(),
                project,
                branch,
                document,
            },
        })
    }
    fn check_head(&self, expected: RevisionHead) -> Result<(), StoredFormError> {
        if expected.revision_id().is_none()
            || expected.generation() == 0
            || self
                .revisions
                .head(self.revision_context, self.scope.project, self.scope.branch)
                .map_err(|_| StoredFormError::Head)?
                != expected
        {
            return Err(StoredFormError::Head);
        }
        Ok(())
    }
    /// Internal strict product-envelope binding. Uses the real source before compiling input.
    pub(crate) fn check_product_binding(
        &self,
        project: &domain_ir::ProjectId,
        document: &DocumentId,
        head: RevisionHead,
        source_sha256: &str,
        now: u64,
    ) -> Result<(), StoredFormError> {
        if project.as_str() != self.scope.project.public_id() || document != &self.scope.document {
            return Err(StoredFormError::Scope);
        }
        if self.source(head, now)?.digest.hex() != source_sha256 {
            return Err(StoredFormError::Drift);
        }
        Ok(())
    }

    fn source(&self, head: RevisionHead, now: u64) -> Result<SourceSnapshot, StoredFormError> {
        self.check_head(head)?;
        let revision = head.revision_id().ok_or(StoredFormError::Head)?;
        let node = self
            .revisions
            .node(self.revision_context, self.scope.project, revision)
            .map_err(|_| StoredFormError::Head)?;
        if !node.sealed()
            || node.project_id() != self.scope.project
            || node.revision_id() != revision
            || node.committed_generation() != head.generation()
        {
            return Err(StoredFormError::Head);
        }
        let artifact = node.result_artifact_id();
        let descriptor = self
            .artifacts
            .get_descriptor(self.artifact_context, artifact, now)
            .map_err(|_| StoredFormError::Artifact)?;
        if descriptor.artifact_id != artifact
            || descriptor.kind != ArtifactKind::Result
            || descriptor.storage_state != StorageState::Available
            || descriptor.validation_state != ValidationState::Verified
            || descriptor.quarantine_reason.is_some()
            || descriptor.size_bytes == 0
            || descriptor.size_bytes > MAX_SOURCE_BYTES as u64
        {
            return Err(StoredFormError::Artifact);
        }
        // Actual service rechecks ACL/state, decrypts AEAD and checks complete content digest.
        // Repository size/content identity is immutable; this is not an attacker-supplied downloader.
        let bytes = self
            .artifacts
            .download(self.artifact_context, artifact, now)
            .map_err(|_| StoredFormError::Artifact)?;
        if bytes.is_empty()
            || bytes.len() > MAX_SOURCE_BYTES
            || bytes.len() as u64 != descriptor.size_bytes
            || ContentDigest::of(&bytes) != descriptor.sha256
        {
            return Err(StoredFormError::Artifact);
        }
        self.check_head(head)?;
        Ok(SourceSnapshot {
            scope: self.scope.clone(),
            head,
            artifact,
            digest: descriptor.sha256,
            bytes,
        })
    }
    /// Loads ONLY the real sealed head's committed result and runs the unchanged form compiler.
    /// # Errors
    /// Rejects stale/empty streams, tenant/ACL/quarantine/AEAD/source or original form failure.
    /// Does not provision a stream, claim idempotency, ingest a result, commit or publish.
    pub fn prepare_json(
        &self,
        inputs: StoredFormInputs<'_>,
        now: u64,
    ) -> Result<PreparedStoredForm, StoredFormError> {
        let source = self.source(inputs.expected_head, now)?;
        let identity = FormOperationIdentity::new(
            self.scope.document.clone(),
            RevisionId::parse(
                inputs
                    .expected_head
                    .revision_id()
                    .ok_or(StoredFormError::Head)?
                    .public_id(),
            )
            .map_err(|_| StoredFormError::Preparation)?,
            inputs.plan_id,
        )
        .map_err(|_| StoredFormError::Preparation)?;
        let context = FormOperationContext::bind(&source.bytes, inputs.map, inputs.policies)
            .map_err(|_| StoredFormError::Preparation)?;
        let operation = FormOperationPreparation::prepare_json(
            &context,
            identity,
            inputs.form_input_json,
            inputs.access,
        )
        .map_err(|_| StoredFormError::Preparation)?;
        self.check_head(source.head)?;
        let receipt=StoredFormReceipt{profile:STORED_FORM_SOURCE_PROFILE,source_sha256:source.digest.hex(),
            source_bytes:source.bytes.len(),head_generation:source.head.generation(),operation:operation.receipt().clone(),
            qualification:StoredFormQualification::ActualServiceSourcePreflightOnlyIssuerFullImportAtomicCasIdempotencyRoutePublicationNativeAndGateUnqualified};
        let prepared = PreparedStoredForm {
            source,
            operation,
            receipt,
        };
        prepared.verify(self, inputs.map, inputs.policies, inputs.access, now)?;
        Ok(prepared)
    }
}

impl PreparedStoredForm {
    #[must_use]
    pub const fn receipt(&self) -> &StoredFormReceipt {
        &self.receipt
    }
    /// Memory candidate only; not a published or route-authorized artifact.
    #[must_use]
    pub fn candidate_bytes(&self) -> &[u8] {
        self.operation.candidate_bytes()
    }
    /// Fresh service head/node/ACL/quarantine/AEAD/raw source plus whole compiler/output check.
    /// # Errors
    /// Rejects any provider/head/content/access/map/policy drift; normal service audits are emitted.
    pub fn verify<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        map: &NativeFormPackageMap,
        policies: &[NativeFormPackagePolicy],
        access: &FormInputAccessPolicy,
        now: u64,
    ) -> Result<StoredFormReceipt, StoredFormError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        if self.source.scope != provider.scope {
            return Err(StoredFormError::Scope);
        }
        let fresh = provider.source(self.source.head, now)?;
        if fresh.artifact != self.source.artifact
            || fresh.digest != self.source.digest
            || fresh.bytes != self.source.bytes
        {
            return Err(StoredFormError::Drift);
        }
        let context = FormOperationContext::bind(&fresh.bytes, map, policies)
            .map_err(|_| StoredFormError::Drift)?;
        let operation = self
            .operation
            .verify(&context, access)
            .map_err(|_| StoredFormError::Drift)?;
        provider.check_head(fresh.head)?;
        if self.receipt.profile != STORED_FORM_SOURCE_PROFILE
            || self.receipt.source_sha256 != fresh.digest.hex()
            || self.receipt.source_bytes != fresh.bytes.len()
            || self.receipt.head_generation != fresh.head.generation()
            || operation != self.receipt.operation
        {
            return Err(StoredFormError::Drift);
        }
        Ok(self.receipt.clone())
    }
    /// Full fresh actual-service validation before consulting the unchanged current signed scope.
    /// # Errors
    /// Current form scope is always denied; no result ingest, manifest, key claim or commit.
    pub fn require_current_product_route<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        map: &NativeFormPackageMap,
        policies: &[NativeFormPackagePolicy],
        access: &FormInputAccessPolicy,
        now: u64,
    ) -> Result<(), StoredFormError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.verify(provider, map, policies, access, now)?;
        let context = FormOperationContext::bind(&self.source.bytes, map, policies)
            .map_err(|_| StoredFormError::Drift)?;
        self.operation
            .require_current_product_route(&context, access)
            .map_err(|_| StoredFormError::RouteUnqualified)
    }
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum StoredFormError {
    #[error("stored_form_provider_scope_invalid")]
    Scope,
    #[error("stored_form_provider_head_invalid")]
    Head,
    #[error("stored_form_provider_artifact_unavailable")]
    Artifact,
    #[error("stored_form_provider_preparation_invalid")]
    Preparation,
    #[error("stored_form_provider_fresh_state_changed")]
    Drift,
    #[error("stored_form_provider_route_unqualified")]
    RouteUnqualified,
}

/// Provider-scoped filename descriptor checks; no CLI, issuer or publication route.
pub mod file_literal {
    use super::*;
    use crate::reference_validation_product::{ReferenceAuxiliaryProductContext,
        ReferenceAuxiliaryProductPreparation, ReferenceFileLiteralProductCandidate};
    use artifact_service::FileName;
    use domain_ir::{ReferenceAuxiliaryDocumentState, ReferenceAuxiliaryLimits,
        ReferenceAuxiliaryOperation, ReferenceAuxiliaryRequestDraft};
    use hwpx_package::{WriterLimits, document_import::{ImportedSourcePackage, SourceImportLimits,
        structure::ImportedDocumentStructure}};
    use sha2::{Digest as _, Sha256};

    pub struct StoredFileLiteralInputs<'a> {
        pub expected_head: RevisionHead,
        pub caller_state: &'a ReferenceAuxiliaryDocumentState,
        pub declared_flow_sha256: &'a str,
        pub request_json: &'a [u8],
        pub source_limits: SourceImportLimits,
        pub reference_limits: ReferenceAuxiliaryLimits,
        pub writer_limits: WriterLimits,
    }
    impl fmt::Debug for StoredFileLiteralInputs<'_> {
        fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result { f.write_str("StoredFileLiteralInputs(<redacted>; caller_state_unqualified)") }
    }
    #[derive(Clone, Debug, Eq, PartialEq, Serialize)]
    pub struct StoredFileLiteralCandidateReceipt {
        pub qualification: &'static str,
        pub source_package_sha256: String,
        pub output_package_sha256: [u8; 32],
        pub stored_leaf_name_sha256: [u8; 32],
        pub head_generation: u64,
        pub provider_scoped_filename_metadata_verified: bool,
        pub complete_auxiliary_state_verified: bool,
        pub issuer_execution_publication_authority: bool,
    }
    pub struct PreparedStoredFileLiteralCandidate {
        source: SourceSnapshot,
        filename: FileName,
        output: ReferenceFileLiteralProductCandidate,
        receipt: StoredFileLiteralCandidateReceipt,
    }
    impl fmt::Debug for PreparedStoredFileLiteralCandidate {
        fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result { f.write_str("PreparedStoredFileLiteralCandidate(<redacted>; route_unqualified)") }
    }
    #[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
    pub enum StoredFileLiteralError {
        #[error("STORED_FILE_LITERAL_SOURCE_REJECTED")] Source,
        #[error("STORED_FILE_LITERAL_METADATA_BINDING_REJECTED")] Binding,
        #[error("STORED_FILE_LITERAL_REQUEST_REJECTED")] Request,
        #[error("STORED_FILE_LITERAL_PROJECTION_NOT_QUALIFIED")] Projection,
        #[error("STORED_FILE_LITERAL_OUTPUT_REJECTED")] Output,
        #[error("STORED_FILE_LITERAL_ROUTE_UNQUALIFIED")] RouteUnqualified,
    }
    impl<R,B,S,V> StoredFormProvider<'_,R,B,S,V>
    where R: ArtifactMetadataRepository, B: EncryptedBlobStore, S: ArtifactScanner, V: RevisionRepository {
        // Original source performs sealed node/head/ACL/quarantine/AEAD/size/digest
        // checks. The second descriptor read must still describe that same result.
        fn file_literal_source(&self, head: RevisionHead, now: u64) -> Result<(SourceSnapshot, FileName), StoredFileLiteralError> {
            let source = self.source(head, now).map_err(|_| StoredFileLiteralError::Source)?;
            let metadata = self.artifacts.get_descriptor(self.artifact_context, source.artifact, now)
                .map_err(|_| StoredFileLiteralError::Source)?;
            if metadata.artifact_id != source.artifact || metadata.sha256 != source.digest
                || metadata.size_bytes != source.bytes.len() as u64 || metadata.kind != ArtifactKind::Result
                || metadata.storage_state != StorageState::Available || metadata.validation_state != ValidationState::Verified
                || metadata.quarantine_reason.is_some() {
                return Err(StoredFileLiteralError::Binding);
            }
            self.check_head(head).map_err(|_| StoredFileLiteralError::Source)?;
            Ok((source, metadata.file_name))
        }
        /// Uses the actual committed result descriptor, never a caller artifact/name selector.
        /// Normal service access audits occur; no result ingest, stream commit or publication.
        /// # Errors
        /// Rejects source access/head drift, a nonliteral or mismatched payload,
        /// unqualified no-extension projection and original candidate failures.
        pub fn prepare_file_literal_candidate(&self, inputs: StoredFileLiteralInputs<'_>, now: u64)
            -> Result<PreparedStoredFileLiteralCandidate, StoredFileLiteralError> {
            let (source, filename) = self.file_literal_source(inputs.expected_head, now)?;
            let revision = RevisionId::parse(source.head.revision_id().ok_or(StoredFileLiteralError::Source)?.public_id())
                .map_err(|_| StoredFileLiteralError::Source)?;
            let context = ReferenceAuxiliaryProductContext::new(inputs.caller_state, self.scope.document.clone(),
                revision, *source.digest.as_bytes(), inputs.declared_flow_sha256);
            let prepared = ReferenceAuxiliaryProductPreparation::prepare_json(&context, inputs.request_json, inputs.reference_limits)
                .map_err(|_| StoredFileLiteralError::Request)?;
            // Original strict parser has already rejected duplicate/unknown keys.
            let request: ReferenceAuxiliaryRequestDraft = serde_json::from_slice(inputs.request_json)
                .map_err(|_| StoredFileLiteralError::Request)?;
            let ReferenceAuxiliaryOperation::InsertFileNameLiteral { literal, .. } = request.operation else {
                return Err(StoredFileLiteralError::Request);
            };
            if !literal.include_extension { return Err(StoredFileLiteralError::Projection); }
            if literal.literal != filename.as_str()
                || literal.source_leaf_name_sha256 != hex::encode(Sha256::digest(filename.as_str().as_bytes())) {
                return Err(StoredFileLiteralError::Binding);
            }
            let package = ImportedSourcePackage::import(&source.bytes, self.scope.document.clone(), *source.digest.as_bytes(), inputs.source_limits)
                .map_err(|_| StoredFileLiteralError::Source)?;
            let imported = ImportedDocumentStructure::import(package).map_err(|_| StoredFileLiteralError::Source)?;
            let output = prepared.lower_file_name_literal_candidate(&context, &imported, &source.bytes,
                inputs.reference_limits, inputs.writer_limits).map_err(|_| StoredFileLiteralError::Output)?;
            let receipt = StoredFileLiteralCandidateReceipt {
                qualification: "provider_scoped_service_descriptor_exact_full_leaf_only_not_issuer_complete_state_atomic_CAS_publication_or_native",
                source_package_sha256: source.digest.hex(), output_package_sha256: output.output_receipt().output_package_sha256,
                stored_leaf_name_sha256: Sha256::digest(filename.as_str().as_bytes()).into(), head_generation: source.head.generation(),
                provider_scoped_filename_metadata_verified: true, complete_auxiliary_state_verified: false,
                issuer_execution_publication_authority: false,
            };
            let candidate = PreparedStoredFileLiteralCandidate { source, filename, output, receipt };
            candidate.verify(self, now)?;
            Ok(candidate)
        }
    }
    impl PreparedStoredFileLiteralCandidate {
        #[must_use]
        pub const fn receipt(&self) -> &StoredFileLiteralCandidateReceipt { &self.receipt }
        fn fresh<R,B,S,V>(&self, provider: &StoredFormProvider<'_,R,B,S,V>, now: u64) -> Result<(),StoredFileLiteralError>
        where R: ArtifactMetadataRepository, B: EncryptedBlobStore, S: ArtifactScanner, V: RevisionRepository {
            if provider.scope != self.source.scope { return Err(StoredFileLiteralError::Binding); }
            let (fresh, name) = provider.file_literal_source(self.source.head, now)?;
            if fresh.scope != self.source.scope || fresh.head != self.source.head || fresh.artifact != self.source.artifact
                || fresh.digest != self.source.digest || fresh.bytes != self.source.bytes || name != self.filename {
                return Err(StoredFileLiteralError::Binding);
            }
            Ok(())
        }
        /// Every verification rechecks original service authorization and complete source bytes.
        /// # Errors
        /// Rejects revocation, head/scope/metadata/AEAD drift and artifact integrity failure.
        pub fn verify<R,B,S,V>(&self, provider: &StoredFormProvider<'_,R,B,S,V>, now: u64)
            -> Result<StoredFileLiteralCandidateReceipt,StoredFileLiteralError>
        where R: ArtifactMetadataRepository, B: EncryptedBlobStore, S: ArtifactScanner, V: RevisionRepository {
            self.fresh(provider, now)?;
            self.output.with_verified_bytes(|_| ()).map_err(|_| StoredFileLiteralError::Output)?;
            provider.check_head(self.source.head).map_err(|_| StoredFileLiteralError::Source)?;
            Ok(self.receipt.clone())
        }
        /// No cached ACL capability: current access/head/filename precede each byte exposure.
        /// # Errors
        /// Never invokes the callback after service or integrity checks fail.
        pub fn with_verified_bytes<R,B,S,V,T>(&self, provider: &StoredFormProvider<'_,R,B,S,V>, now: u64,
            consume: impl FnOnce(&[u8])->T) -> Result<T,StoredFileLiteralError>
        where R: ArtifactMetadataRepository, B: EncryptedBlobStore, S: ArtifactScanner, V: RevisionRepository {
            self.fresh(provider, now)?;
            self.output.with_verified_bytes(|bytes| {
                provider.check_head(self.source.head).map_err(|_| StoredFileLiteralError::Source)?;
                Ok(consume(bytes))
            }).map_err(|_| StoredFileLiteralError::Output)?
        }
        /// # Errors
        /// Fresh checks never grant an execution/publication/Native route.
        pub fn require_current_product_route<R,B,S,V>(&self, provider: &StoredFormProvider<'_,R,B,S,V>, now: u64)
            -> Result<(),StoredFileLiteralError>
        where R: ArtifactMetadataRepository, B: EncryptedBlobStore, S: ArtifactScanner, V: RevisionRepository {
            self.verify(provider,now)?;
            Err(StoredFileLiteralError::RouteUnqualified)
        }
    }
}
