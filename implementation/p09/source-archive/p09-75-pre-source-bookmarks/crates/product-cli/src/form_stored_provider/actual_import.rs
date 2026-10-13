//! Actual sealed result -> unchanged ACL/AEAD read -> source-backed partial import.
//! Fresh reads are not atomic CAS, durable importer persistence or issuer authority.
pub mod field_ranges;

use super::{SourceSnapshot, StoredFormError, StoredFormProvider};
use artifact_service::{
    ArtifactId, ArtifactMetadataRepository, ArtifactScanner, EncryptedBlobStore,
};
use domain_ir::{DocumentGraph, FormDocumentState};
use hwpx_package::document_import::{
    ImportedSourcePackage, SourceImportLimits,
    forms::{
        FormImportError, FormImportReceipt, ImportedDocumentForms,
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
        let receipt = self.imported.verify_source(&fresh.bytes)?;
        provider.check_head(fresh.head)?;
        if self.receipt.profile != PROFILE
            || self.receipt.source_artifact != fresh.artifact
            || self.receipt.head_generation != fresh.head.generation()
            || self.receipt.source_bytes != fresh.bytes.len()
            || self.receipt.imported != receipt
        {
            return Err(StoredActualFormImportError::Binding);
        }
        Ok(fresh)
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
