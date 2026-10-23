//! Actual sealed result -> unchanged ACL/AEAD read -> source-backed partial import.
//! Fresh reads are not atomic CAS, durable importer persistence or issuer authority.
pub mod field_ranges;
pub mod review;
pub mod source_policy;
pub mod caption_text_output;
pub mod caption_text_batch_output;
pub mod caption_edit_batch_output;
pub mod caption_content_output;
pub mod note_conversion_output;
pub mod note_style_output;
pub mod note_export_output;
pub mod source_search;
pub mod literal_search_output;
pub mod named_style_declarations;
pub mod https_target_output;

use super::{SourceSnapshot, StoredFormError, StoredFormProvider};
use artifact_service::{
    ArtifactId, ArtifactMetadataRepository, ArtifactScanner, EncryptedBlobStore,
};
use domain_ir::{DocumentGraph, FormDocumentState};
use hwpx_package::document_import::{
    ImportedSourcePackage, SourceImportLimits,
    forms::{
        FormImportError, FormImportReceipt, ImportedDocumentForms, VerifiedFormReconstruction,
        policies::{
            FormPolicyBindingError, FormPolicyBindingReceipt, FormPolicySourceBinding,
            PolicyBoundDocumentForms, SourceFormPolicy,
        },
    },
};
use revision_service::{RevisionHead, RevisionRepository};
use serde::Serialize;
use std::fmt;
use thiserror::Error;

const PROFILE: &str = "hwpx-agent.stored-actual-form-import/partial-v1";

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct StoredActualFormImportReceipt {
    pub profile: &'static str,
    pub source_artifact: ArtifactId,
    pub head_generation: u64,
    pub source_bytes: usize,
    pub imported: FormImportReceipt,
    pub qualification: StoredActualFormImportQualification,
}
#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum StoredActualFormImportQualification {
    ActualServiceReadAndPartialImportOnlyIssuerPolicyAuthorityPersistenceExecutionNativeGateUnqualified,
}

/// Immutable provider-scoped source + actual imported graph. No deserialization,
/// public artifact selector, caller graph/map or artifact write capability.
pub struct StoredImportedDocumentForms {
    source: SourceSnapshot,
    imported: ImportedDocumentForms,
    receipt: StoredActualFormImportReceipt,
}
impl fmt::Debug for StoredImportedDocumentForms {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("StoredImportedDocumentForms(<redacted>)")
    }
}

impl<R, B, S, V> StoredFormProvider<'_, R, B, S, V>
where
    R: ArtifactMetadataRepository,
    B: EncryptedBlobStore,
    S: ArtifactScanner,
    V: RevisionRepository,
{
    /// Selects only this authenticated provider's sealed current Result, reusing
    /// the unchanged head/node/descriptor/tenant/ACL/quarantine/AEAD/digest checks.
    /// Source kind is not silently changed to Result or accepted by an old guard.
    /// # Errors
    /// Rejects source/head/access/security failures and any actual importer failure.
    pub fn import_actual_forms(
        &self,
        expected_head: RevisionHead,
        now: u64,
    ) -> Result<StoredImportedDocumentForms, StoredActualFormImportError> {
        let source = self.source(expected_head, now)?;
        let imported = ImportedDocumentForms::import(
            ImportedSourcePackage::import(
                &source.bytes,
                self.scope.document.clone(),
                *source.digest.as_bytes(),
                SourceImportLimits::default(),
            )
            .map_err(FormImportError::from)?,
        )?;
        // Preserve the original two-read discipline without claiming a held lock.
        self.check_head(expected_head)?;
        let receipt = StoredActualFormImportReceipt {
            profile: PROFILE, source_artifact: source.artifact,
            head_generation: source.head.generation(), source_bytes: source.bytes.len(),
            imported: imported.receipt().clone(),
            qualification: StoredActualFormImportQualification::ActualServiceReadAndPartialImportOnlyIssuerPolicyAuthorityPersistenceExecutionNativeGateUnqualified,
        };
        Ok(StoredImportedDocumentForms {
            source,
            imported,
            receipt,
        })
    }
}
impl StoredImportedDocumentForms {
    // Operation-local source borrowing for the storage bridge. No second copy,
    // retained reconstruction, caller artifact selector or service authority.
    pub(crate) fn with_verified_compiler_source<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64,
        consume:impl FnOnce(&[u8],revision_service::ProjectId,revision_service::BranchId,RevisionHead)->T)
        ->Result<T,StoredActualFormImportError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let fresh=self.fresh_source(provider,now)?;self.check_compiler_head(provider)?;
        Ok(consume(&fresh.bytes,fresh.scope.project,fresh.scope.branch,fresh.head))
    }
    pub(crate) const fn compiler_head(&self) -> RevisionHead { self.source.head }
    pub(crate) fn check_compiler_head<R, B, S, V>(&self, provider: &StoredFormProvider<'_, R, B, S, V>) -> Result<(), StoredActualFormImportError>
    where R: ArtifactMetadataRepository, B: EncryptedBlobStore, S: ArtifactScanner, V: RevisionRepository {
        provider.check_head(self.source.head).map_err(Into::into)
    }
    #[must_use]
    pub const fn imported(&self) -> &ImportedDocumentForms {
        &self.imported
    }

    #[must_use]
    pub fn notes(
        &self,
    ) -> &[hwpx_package::document_import::structure::notes::ImportedNoteObservation] {
        self.imported.notes()
    }

    #[must_use]
    pub fn bookmarks(
        &self,
    ) -> &[hwpx_package::document_import::structure::bookmarks::ImportedBookmarkObservation] {
        self.imported.bookmarks()
    }

    /// Fresh original service authorization before raw source-name selection.
    /// # Errors
    /// Rejects revoked/head/scope/source drift and absent/ambiguous names.
    pub fn observed_bookmark_by_name<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        name: &str,
        now: u64,
    ) -> Result<
        &hwpx_package::document_import::structure::bookmarks::ImportedBookmarkObservation,
        StoredActualFormImportError,
    >
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.fresh_source(provider, now)?;
        Ok(self.imported.observed_bookmark_by_name(name)?)
    }
    #[must_use]
    pub const fn receipt(&self) -> &StoredActualFormImportReceipt {
        &self.receipt
    }

    fn fresh_source<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<SourceSnapshot, StoredActualFormImportError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        let (fresh, _) = self.fresh_source_reconstructed(provider, now)?;
        Ok(fresh)
    }

    // Private and operation-local: every call keeps the original fresh service
    // read and head/byte/receipt checks. Never stores reconstruction or authority.
    fn fresh_source_reconstructed<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<(SourceSnapshot, VerifiedFormReconstruction<'_>), StoredActualFormImportError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        if self.source.scope != provider.scope {
            return Err(StoredActualFormImportError::Binding);
        }
        let fresh = provider.source(self.source.head, now)?;
        if fresh.scope != self.source.scope
            || fresh.head != self.source.head
            || fresh.artifact != self.source.artifact
            || fresh.digest != self.source.digest
            || fresh.bytes != self.source.bytes
        {
            return Err(StoredActualFormImportError::Binding);
        }
        let reconstruction = self
            .imported
            .reconstruct_source_for_verification(&fresh.bytes)?;
        provider.check_head(fresh.head)?;
        if self.receipt.profile != PROFILE
            || self.receipt.source_artifact != fresh.artifact
            || self.receipt.head_generation != fresh.head.generation()
            || self.receipt.source_bytes != fresh.bytes.len()
            || &self.receipt.imported != reconstruction.receipt()
        {
            return Err(StoredActualFormImportError::Binding);
        }
        Ok((fresh, reconstruction))
    }
    /// Rechecks current authenticated service access before whole actual-source reconstruction.
    /// # Errors
    /// Rejects scope/head/ACL/quarantine/AEAD/descriptor/source/graph drift.
    pub fn verify<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<StoredActualFormImportReceipt, StoredActualFormImportError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.fresh_source(provider, now)?;
        Ok(self.receipt.clone())
    }
    /// Only explicit policy fields are accepted after FRESH service/head authorization.
    /// Caller policy choices remain unqualified as an authoritative persisted policy provider.
    /// # Errors
    /// Rejects revoked/current service access or the original source-bound policy validations.
    pub fn bind_policies<'a, R, B, S, V>(
        &'a self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        binding: &FormPolicySourceBinding,
        policies: &[SourceFormPolicy],
        now: u64,
    ) -> Result<StoredBoundFormPolicies<'a>, StoredActualFormImportError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.fresh_source(provider, now)?;
        let bound = PolicyBoundDocumentForms::bind(&self.imported, binding, policies)?;
        provider.check_head(self.source.head)?;
        let receipt = StoredActualFormPolicyReceipt {
            imported: self.receipt.clone(),
            policy: bound.receipt().clone(),
            qualification: "actual_authenticated_source_with_explicit_caller_policy_not_policy_issuer_persistence_or_execution",
        };
        Ok(StoredBoundFormPolicies {
            imported: self,
            bound,
            receipt,
        })
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct StoredActualFormPolicyReceipt {
    pub imported: StoredActualFormImportReceipt,
    pub policy: FormPolicyBindingReceipt,
    pub qualification: &'static str,
}
pub struct StoredBoundFormPolicies<'a> {
    imported: &'a StoredImportedDocumentForms,
    bound: PolicyBoundDocumentForms<'a>,
    receipt: StoredActualFormPolicyReceipt,
}
impl fmt::Debug for StoredBoundFormPolicies<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("StoredBoundFormPolicies(<redacted>)")
    }
}
impl StoredBoundFormPolicies<'_> {
    #[must_use]
    pub const fn graph(&self) -> &DocumentGraph {
        self.bound.graph()
    }
    #[must_use]
    pub const fn state(&self) -> &FormDocumentState {
        self.bound.state()
    }
    #[must_use]
    pub const fn receipt(&self) -> &StoredActualFormPolicyReceipt {
        &self.receipt
    }
    /// Fresh ACL/AEAD/whole source/policy/state/graph verification. Read audits
    /// are the only service write; no ingest, seal, CAS, manifest or publication.
    /// # Errors
    /// Rejects any revoked service access, stale head/source or complete policy drift.
    pub fn verify<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        binding: &FormPolicySourceBinding,
        policies: &[SourceFormPolicy],
        now: u64,
    ) -> Result<StoredActualFormPolicyReceipt, StoredActualFormImportError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        let fresh = self.imported.fresh_source(provider, now)?;
        let policy = self.bound.verify_source(&fresh.bytes, binding, policies)?;
        provider.check_head(fresh.head)?;
        if self.receipt.imported != self.imported.receipt || self.receipt.policy != policy {
            return Err(StoredActualFormImportError::Binding);
        }
        Ok(self.receipt.clone())
    }
}

#[derive(Debug, Error)]
pub enum StoredActualFormImportError {
    #[error("stored actual form source service rejected")]
    Source(#[from] StoredFormError),
    #[error("stored actual form source importer rejected")]
    Import(#[from] FormImportError),
    #[error("stored actual form explicit policy rejected")]
    Policy(#[from] FormPolicyBindingError),
    #[error("stored actual form scope/source/graph binding rejected")]
    Binding,
}

/// Source caption observations only; no numbering, issuer or executable route.
pub mod reference_captions {
    use super::*;
    use domain_ir::{ReferenceAuxiliaryLimits, ValidationTarget};
    use hwpx_package::document_import::reference_targets::captions::{
        ImportedReferenceCaptionEnvelope, ImportedReferenceCaptions,
        ReferenceCaptionImportError, ReferenceCaptionImportReceipt,
    };

    #[derive(Clone, Debug, Eq, PartialEq, Serialize)]
    pub struct StoredReferenceCaptionImportReceipt {
        pub source: StoredActualFormImportReceipt,
        pub captions: ReferenceCaptionImportReceipt,
        pub qualification: &'static str,
    }
    pub struct StoredImportedReferenceCaptions<'a> {
        source: &'a StoredImportedDocumentForms,
        imported: ImportedReferenceCaptions<'a>,
        limits: ReferenceAuxiliaryLimits,
        receipt: StoredReferenceCaptionImportReceipt,
    }
    impl fmt::Debug for StoredImportedReferenceCaptions<'_> {
        fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
            f.write_str("StoredImportedReferenceCaptions(<redacted>; envelope_only)")
        }
    }
    #[derive(Debug, Error)]
    pub enum StoredReferenceCaptionError {
        #[error("stored caption source access rejected")] Source(#[from] StoredActualFormImportError),
        #[error("stored caption model rejected")] Model(#[from] ReferenceCaptionImportError),
        #[error("stored caption source binding rejected")] Binding,
        #[error("stored caption product route unqualified")] RouteUnqualified,
    }
    impl StoredImportedDocumentForms {
        /// # Errors
        /// Requires fresh authenticated source access and complete caption coverage.
        pub fn import_reference_captions<R,B,S,V>(
            &self, provider:&StoredFormProvider<'_,R,B,S,V>,
            limits:ReferenceAuxiliaryLimits, now:u64,
        )->Result<StoredImportedReferenceCaptions<'_>,StoredReferenceCaptionError>
        where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
            let fresh=self.fresh_source(provider,now)?;
            let imported=ImportedReferenceCaptions::import(self.imported.body_structure(),limits)?;
            if imported.receipt().source_package_sha256!=*fresh.digest.as_bytes() {return Err(StoredReferenceCaptionError::Binding);}
            provider.check_head(fresh.head).map_err(StoredActualFormImportError::from)?;
            let receipt=StoredReferenceCaptionImportReceipt {source:self.receipt.clone(),captions:imported.receipt().clone(),
                qualification:"fresh_service_source_caption_envelopes_only_numbering_full_state_issuer_execution_native_unqualified"};
            Ok(StoredImportedReferenceCaptions {source:self,imported,limits,receipt})
        }
    }
    impl StoredImportedReferenceCaptions<'_> {
        #[must_use] pub const fn receipt(&self)->&StoredReferenceCaptionImportReceipt {&self.receipt}
        /// # Errors
        /// Fresh scope/head/ACL/quarantine/AEAD checks plus whole reconstruction.
        pub fn verify<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)
            ->Result<StoredReferenceCaptionImportReceipt,StoredReferenceCaptionError>
        where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
            let (fresh,proof)=self.source.fresh_source_reconstructed(provider,now)?;
            let captions=self.imported.verify_reconstructed(&self.source.imported,&proof,self.limits)?;
            if self.receipt.source!=self.source.receipt||self.receipt.captions!=captions {return Err(StoredReferenceCaptionError::Binding);}
            provider.check_head(fresh.head).map_err(StoredActualFormImportError::from)?;
            Ok(self.receipt.clone())
        }
        /// Each call reauthorizes; retaining this model never retains access.
        /// Read audits only. Multiple head checks do not claim atomic CAS.
        /// # Errors
        /// No callback after stale/revoked/quarantined/tampered/foreign access.
        pub fn with_source_captions<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64,
            consume:impl FnOnce(&[ImportedReferenceCaptionEnvelope],&[ValidationTarget])->T)
            ->Result<T,StoredReferenceCaptionError>
        where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
            self.verify(provider,now)?;
            provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;
            Ok(consume(self.imported.envelopes(),self.imported.targets()))
        }
        /// # Errors
        /// Always denies executable routes even after successful fresh verification.
        pub fn require_current_product_route<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)
            ->Result<(),StoredReferenceCaptionError>
        where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
            self.verify(provider,now)?; Err(StoredReferenceCaptionError::RouteUnqualified)
        }
    }
}

/// Authenticated source access around an immutable, layout-only memory output.
/// Reading this candidate never grants ingest, revision commit or execution.
pub mod caption_layout_output {
    use super::*;
    use domain_ir::{LogicalId,ReferenceAuxiliaryLimits};
    use hwpx_package::{WriterLimits,document_import::structure::caption_layout::{
        CaptionLayout,CaptionLayoutOutputCandidate,CaptionLayoutOutputError,CaptionLayoutOutputReceipt,
    }};

    #[derive(Clone,Debug,Eq,PartialEq,Serialize)]
    pub struct StoredCaptionLayoutOutputReceipt {
        pub source:StoredActualFormImportReceipt,
        pub source_caption_id:LogicalId,
        pub requested_layout:CaptionLayout,
        pub output:CaptionLayoutOutputReceipt,
        pub qualification:&'static str,
        pub issuer_execution_publication_authority:bool,
    }
    pub struct PreparedStoredCaptionLayoutCandidate<'a> {
        source:&'a StoredImportedDocumentForms,
        output:CaptionLayoutOutputCandidate,
        receipt:StoredCaptionLayoutOutputReceipt,
    }
    impl fmt::Debug for PreparedStoredCaptionLayoutCandidate<'_> {
        fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("PreparedStoredCaptionLayoutCandidate(<redacted>; layout_only)")}
    }
    #[derive(Debug,Error)]
    pub enum StoredCaptionLayoutError {
        #[error("stored caption layout source access rejected")] Source(#[from] StoredActualFormImportError),
        #[error("stored caption layout output rejected")] Output(#[from] CaptionLayoutOutputError),
        #[error("stored caption layout artifact integrity rejected")] Integrity,
        #[error("stored caption layout source/output binding rejected")] Binding,
        #[error("stored caption layout product route unqualified")] RouteUnqualified,
    }
    impl StoredImportedDocumentForms {
        /// Fresh service read plus whole-source reconstruction precedes lowering.
        /// Reuses that original-bound proof rather than reimporting source again.
        /// The only service effect is its normal metadata/download read audit.
        /// # Errors
        /// Rejects stale/revoked/quarantined/tampered/foreign source and every
        /// original source selection, layout, protection, ID and writer failure.
        pub fn prepare_caption_layout_candidate<R,B,S,V>(&self,
            provider:&StoredFormProvider<'_,R,B,S,V>,caption_id:&LogicalId,
            layout:CaptionLayout,limits:ReferenceAuxiliaryLimits,writer_limits:WriterLimits,now:u64,
        )->Result<PreparedStoredCaptionLayoutCandidate<'_>,StoredCaptionLayoutError>
        where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
            let (fresh,proof)=self.fresh_source_reconstructed(provider,now)?;
            let output=proof.lower_caption_layout_candidate(&self.imported,&fresh.bytes,caption_id,layout,limits,writer_limits)?;
            if output.receipt().source_package_sha256!=*fresh.digest.as_bytes() {return Err(StoredCaptionLayoutError::Binding);}
            provider.check_head(fresh.head).map_err(StoredActualFormImportError::from)?;
            let receipt=StoredCaptionLayoutOutputReceipt {source:self.receipt.clone(),source_caption_id:caption_id.clone(),requested_layout:layout,
                output:output.receipt().clone(),qualification:"fresh_service_source_bound_layout_memory_candidate_not_complete_numbering_state_protection_issuer_CAS_execution_or_native",
                issuer_execution_publication_authority:false};
            Ok(PreparedStoredCaptionLayoutCandidate {source:self,output,receipt})
        }
    }
    impl PreparedStoredCaptionLayoutCandidate<'_> {
        #[must_use] pub const fn receipt(&self)->&StoredCaptionLayoutOutputReceipt {&self.receipt}
        fn fresh<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<(),StoredCaptionLayoutError>
        where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
            // No cached access: this rebuilds and compares the complete original
            // source/form model on every operation using current service bytes.
            let fresh=self.source.fresh_source(provider,now)?;
            if self.receipt.source!=self.source.receipt||&self.receipt.output!=self.output.receipt()
                ||self.receipt.output.source_package_sha256!=*fresh.digest.as_bytes()
                ||self.receipt.issuer_execution_publication_authority {return Err(StoredCaptionLayoutError::Binding);}
            Ok(())
        }
        /// # Errors
        /// Rechecks current service access and the unchanged writer artifact.
        pub fn verify<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)
            ->Result<StoredCaptionLayoutOutputReceipt,StoredCaptionLayoutError>
        where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
            self.fresh(provider,now)?;
            self.output.with_verified_bytes(|_|()).map_err(|_|StoredCaptionLayoutError::Integrity)?;
            provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;
            Ok(self.receipt.clone())
        }
        /// Each exposure gets fresh source access, artifact integrity and a head
        /// check immediately inside the writer callback. This is not atomic CAS.
        /// # Errors
        /// Never invokes the consumer after access, source or integrity rejection.
        pub fn with_verified_bytes<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64,
            consume:impl FnOnce(&[u8])->T)->Result<T,StoredCaptionLayoutError>
        where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
            self.fresh(provider,now)?;
            self.output.with_verified_bytes(|bytes| {
                provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;
                Ok(consume(bytes))
            }).map_err(|_|StoredCaptionLayoutError::Integrity)?
        }
        /// # Errors
        /// Always rejects the executable route even after fresh verification.
        pub fn require_current_product_route<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)
            ->Result<(),StoredCaptionLayoutError>
        where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
            self.verify(provider,now)?;Err(StoredCaptionLayoutError::RouteUnqualified)
        }
    }
}
