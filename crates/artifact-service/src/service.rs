use std::collections::BTreeSet;
use std::fmt;

use crate::crypto::Aes256GcmKeyring;
use crate::signed_url::{DownloadClaims, DownloadSigner};
use crate::store::{ArtifactMetadataRepository, ArtifactRecord, EncryptedBlobStore, ObjectKey};
use crate::types::{
    ArtifactAuditEvent, ArtifactAuditOutcome, ArtifactDescriptor, ArtifactError, ArtifactId,
    ArtifactKind, ArtifactPermission, AuthScope, ContentDigest, FileName, IngestRequest, MediaType,
    QuarantineReason, RequestContext, ScanEvidence, ScanVerdict, ScannerReference,
    ScannerSignatureVersion, SignedDownloadUrl, StorageState, ValidationState,
};

const DATABASE_MAX_ARTIFACT_BYTES: u64 = 1_099_511_627_776;

#[derive(Clone, Copy, Debug)]
pub struct ScanRequest<'a> {
    pub bytes: &'a [u8],
    pub media_type: &'a MediaType,
    pub file_name: &'a FileName,
    pub kind: ArtifactKind,
}

pub trait ArtifactScanner: fmt::Debug + Send + Sync {
    /// Classifies an untrusted payload without mutating it.
    ///
    /// # Errors
    ///
    /// Returns an error when the scanner cannot safely classify the request. Callers must not
    /// promote such a failure to a clean verdict.
    fn scan(&self, request: ScanRequest<'_>) -> Result<ScanEvidence, ArtifactError>;
}

#[derive(Clone, Copy, Debug, Default)]
pub struct FailClosedScanner;

impl ArtifactScanner for FailClosedScanner {
    fn scan(&self, _request: ScanRequest<'_>) -> Result<ScanEvidence, ArtifactError> {
        Ok(ScanEvidence {
            engine: ScannerReference::parse("scanner.unavailable")?,
            signature_version: ScannerSignatureVersion::parse("none")?,
            verdict: ScanVerdict::Unverified(QuarantineReason::parse("SCANNER_UNAVAILABLE")?),
        })
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ArtifactServiceConfig {
    pub max_payload_bytes: u64,
    pub signed_url_ttl_seconds: u64,
}

impl ArtifactServiceConfig {
    /// Creates bounded storage and signed-URL limits.
    ///
    /// # Errors
    ///
    /// Returns an error when either limit is zero or exceeds its persisted security boundary.
    pub fn new(max_payload_bytes: u64, signed_url_ttl_seconds: u64) -> Result<Self, ArtifactError> {
        if !(1..=DATABASE_MAX_ARTIFACT_BYTES).contains(&max_payload_bytes) {
            return Err(ArtifactError::PayloadTooLarge {
                limit_bytes: DATABASE_MAX_ARTIFACT_BYTES,
            });
        }
        if !(1..=300).contains(&signed_url_ttl_seconds) {
            return Err(ArtifactError::InvalidSignedUrlLifetime);
        }
        Ok(Self {
            max_payload_bytes,
            signed_url_ttl_seconds,
        })
    }
}

#[derive(Debug)]
pub struct ArtifactService<R, B, S> {
    metadata: R,
    blobs: B,
    scanner: S,
    keyring: Aes256GcmKeyring,
    signer: DownloadSigner,
    config: ArtifactServiceConfig,
}

impl<R, B, S> ArtifactService<R, B, S>
where
    R: ArtifactMetadataRepository,
    B: EncryptedBlobStore,
    S: ArtifactScanner,
{
    #[must_use]
    pub fn new(
        metadata: R,
        blobs: B,
        scanner: S,
        keyring: Aes256GcmKeyring,
        signer: DownloadSigner,
        config: ArtifactServiceConfig,
    ) -> Self {
        Self {
            metadata,
            blobs,
            scanner,
            keyring,
            signer,
            config,
        }
    }

    /// Scans, encrypts and create-new stores one content-addressed artifact.
    ///
    /// # Errors
    ///
    /// Returns an error for invalid authorization, size, scan, crypto, metadata or blob state.
    pub fn ingest(
        &self,
        context: &RequestContext,
        request: IngestRequest,
        now_unix_seconds: u64,
    ) -> Result<ArtifactDescriptor, ArtifactError> {
        require_scope(context, AuthScope::DocumentWrite)?;
        let size_bytes =
            u64::try_from(request.bytes.len()).map_err(|_| ArtifactError::PayloadTooLarge {
                limit_bytes: self.config.max_payload_bytes,
            })?;
        if size_bytes > self.config.max_payload_bytes {
            return Err(ArtifactError::PayloadTooLarge {
                limit_bytes: self.config.max_payload_bytes,
            });
        }
        let digest = ContentDigest::of(&request.bytes);
        if let Some(existing) = self.metadata.find_by_content(context.tenant_id(), digest)? {
            return self.resolve_existing_ingest(context, &request, &existing, now_unix_seconds);
        }

        let scan = self.scanner.scan(ScanRequest {
            bytes: &request.bytes,
            media_type: &request.media_type,
            file_name: &request.file_name,
            kind: request.kind,
        })?;
        let (storage_state, validation_state, quarantine_reason, audit_outcome) = match scan.verdict
        {
            ScanVerdict::Clean => (
                StorageState::Available,
                ValidationState::Verified,
                None,
                ArtifactAuditOutcome::Allowed,
            ),
            ScanVerdict::Suspicious(reason) => (
                StorageState::Quarantined,
                ValidationState::Quarantined,
                Some(reason),
                ArtifactAuditOutcome::Quarantined,
            ),
            ScanVerdict::Unverified(reason) => (
                StorageState::Quarantined,
                ValidationState::Unverified,
                Some(reason),
                ArtifactAuditOutcome::Quarantined,
            ),
        };
        let encrypted = self.keyring.encrypt(
            context.tenant_id(),
            digest,
            size_bytes,
            &request.media_type,
            request.kind,
            &request.bytes,
        )?;
        let object_key =
            ObjectKey::for_artifact(context.tenant_id(), request.kind, storage_state, digest)?;
        self.blobs
            .put_if_absent(&object_key, &encrypted.ciphertext)?;
        let record = ArtifactRecord::new(
            context.tenant_id(),
            ArtifactId::generate(),
            digest,
            size_bytes,
            request.media_type,
            request.file_name,
            request.kind,
            storage_state,
            validation_state,
            quarantine_reason,
            scan.engine,
            scan.signature_version,
            encrypted.metadata,
            object_key,
            context.subject(),
            now_unix_seconds,
        );
        self.metadata.insert(record.clone())?;
        self.audit(
            "artifact.ingested",
            context,
            &record,
            audit_outcome,
            now_unix_seconds,
        )?;
        Ok(record.descriptor())
    }

    /// Reads tenant-scoped metadata after scope and artifact ACL checks.
    ///
    /// # Errors
    ///
    /// Returns not-found for a different tenant and access-denied for an ungranted local subject.
    pub fn get_descriptor(
        &self,
        context: &RequestContext,
        artifact_id: ArtifactId,
        now_unix_seconds: u64,
    ) -> Result<ArtifactDescriptor, ArtifactError> {
        require_scope(context, AuthScope::DocumentRead)?;
        let record = self.find_scoped(context, artifact_id)?;
        self.require_permission(
            context,
            &record,
            ArtifactPermission::Read,
            "artifact.metadata.read",
            now_unix_seconds,
        )?;
        self.audit(
            "artifact.metadata.read",
            context,
            &record,
            ArtifactAuditOutcome::Allowed,
            now_unix_seconds,
        )?;
        Ok(record.descriptor())
    }

    /// Decrypts a verified artifact after tenant, scope, ACL and quarantine checks.
    ///
    /// # Errors
    ///
    /// Returns an error for authorization, state, storage, AEAD or digest verification failure.
    pub fn download(
        &self,
        context: &RequestContext,
        artifact_id: ArtifactId,
        now_unix_seconds: u64,
    ) -> Result<Vec<u8>, ArtifactError> {
        require_scope(context, AuthScope::DocumentRead)?;
        let record = self.find_scoped(context, artifact_id)?;
        self.authorize_download(context, &record, "artifact.download", now_unix_seconds)?;
        let payload = match self.decrypt_record(&record) {
            Ok(payload) => payload,
            Err(error) => {
                self.audit(
                    "artifact.download",
                    context,
                    &record,
                    ArtifactAuditOutcome::Denied,
                    now_unix_seconds,
                )?;
                return Err(error);
            }
        };
        self.audit(
            "artifact.download",
            context,
            &record,
            ArtifactAuditOutcome::Allowed,
            now_unix_seconds,
        )?;
        Ok(payload)
    }

    /// Issues a short-lived subject- and ACL-generation-bound HTTPS download URL.
    ///
    /// # Errors
    ///
    /// Returns an error for authorization, non-available state or signing failure.
    pub fn issue_download_url(
        &self,
        context: &RequestContext,
        artifact_id: ArtifactId,
        now_unix_seconds: u64,
    ) -> Result<SignedDownloadUrl, ArtifactError> {
        require_scope(context, AuthScope::DocumentRead)?;
        let record = self.find_scoped(context, artifact_id)?;
        if record.storage_state() == StorageState::Quarantined {
            return Err(ArtifactError::Quarantined);
        }
        if record.storage_state() != StorageState::Available {
            return Err(ArtifactError::InvalidState);
        }
        self.require_permission(
            context,
            &record,
            ArtifactPermission::Read,
            "artifact.signed_url.issued",
            now_unix_seconds,
        )?;
        let expires_at_unix_seconds = now_unix_seconds
            .checked_add(self.config.signed_url_ttl_seconds)
            .ok_or(ArtifactError::InvalidSignedUrlLifetime)?;
        let signed_url = self.signer.issue(DownloadClaims {
            tenant_id: record.tenant_id(),
            artifact_id: record.artifact_id(),
            subject_sha256: context.subject(),
            content_sha256: record.content_sha256(),
            acl_version: record.acl_version(),
            issued_at_unix_seconds: now_unix_seconds,
            expires_at_unix_seconds,
        })?;
        self.audit(
            "artifact.signed_url.issued",
            context,
            &record,
            ArtifactAuditOutcome::Allowed,
            now_unix_seconds,
        )?;
        Ok(signed_url)
    }

    /// Verifies and redeems a signed URL against current tenant, subject, state and ACL metadata.
    ///
    /// # Errors
    ///
    /// Returns an error for invalid or expired signatures, stale ACLs, authorization or integrity.
    pub fn redeem_download_url(
        &self,
        context: &RequestContext,
        signed_url: &SignedDownloadUrl,
        now_unix_seconds: u64,
    ) -> Result<Vec<u8>, ArtifactError> {
        require_scope(context, AuthScope::DocumentRead)?;
        let claims = self.signer.verify(signed_url, now_unix_seconds)?;
        if claims.tenant_id != context.tenant_id() {
            return Err(ArtifactError::NotFound);
        }
        if claims.subject_sha256 != context.subject() {
            return Err(ArtifactError::AccessDenied);
        }
        let record = self.find_scoped(context, claims.artifact_id)?;
        if record.storage_state() != StorageState::Available
            || record.content_sha256() != claims.content_sha256
            || record.acl_version() != claims.acl_version
            || !record.has_permission(context.subject(), ArtifactPermission::Read)
        {
            self.audit(
                "artifact.signed_url.redeemed",
                context,
                &record,
                ArtifactAuditOutcome::Denied,
                now_unix_seconds,
            )?;
            return Err(ArtifactError::AccessDenied);
        }
        let payload = self.decrypt_record(&record)?;
        self.audit(
            "artifact.signed_url.redeemed",
            context,
            &record,
            ArtifactAuditOutcome::Allowed,
            now_unix_seconds,
        )?;
        Ok(payload)
    }

    /// Replaces one subject's artifact permissions and invalidates older signed URLs.
    ///
    /// # Errors
    ///
    /// Returns an error unless the actor can share and manage the artifact, or if the change would
    /// remove the final manager.
    pub fn set_permissions(
        &self,
        context: &RequestContext,
        artifact_id: ArtifactId,
        subject: crate::types::SubjectDigest,
        permissions: BTreeSet<ArtifactPermission>,
        now_unix_seconds: u64,
    ) -> Result<u64, ArtifactError> {
        require_scope(context, AuthScope::ArtifactShare)?;
        let record = self.find_scoped(context, artifact_id)?;
        self.require_permission(
            context,
            &record,
            ArtifactPermission::Manage,
            "artifact.acl.changed",
            now_unix_seconds,
        )?;
        let changed = self.metadata.set_permissions(
            context.tenant_id(),
            artifact_id,
            subject,
            permissions,
        )?;
        self.audit(
            "artifact.acl.changed",
            context,
            &changed,
            ArtifactAuditOutcome::Allowed,
            now_unix_seconds,
        )?;
        Ok(changed.acl_version())
    }

    /// Atomically relocates an available encrypted object to its quarantine namespace.
    ///
    /// # Errors
    ///
    /// Returns an error for missing security authority, invalid state, collision or failed rollback.
    pub fn quarantine(
        &self,
        context: &RequestContext,
        artifact_id: ArtifactId,
        reason: QuarantineReason,
        now_unix_seconds: u64,
    ) -> Result<ArtifactDescriptor, ArtifactError> {
        require_scope(context, AuthScope::SecurityModify)?;
        let record = self.find_scoped(context, artifact_id)?;
        self.require_permission(
            context,
            &record,
            ArtifactPermission::Manage,
            "artifact.quarantined",
            now_unix_seconds,
        )?;
        if record.storage_state() == StorageState::Quarantined {
            return Ok(record.descriptor());
        }
        if record.storage_state() != StorageState::Available {
            return Err(ArtifactError::InvalidState);
        }
        let target = ObjectKey::for_artifact(
            record.tenant_id(),
            record.kind(),
            StorageState::Quarantined,
            record.content_sha256(),
        )?;
        self.blobs
            .relocate_if_absent(record.object_key(), &target)?;
        let changed = match self.metadata.transition_state(
            record.tenant_id(),
            record.artifact_id(),
            StorageState::Available,
            StorageState::Quarantined,
            ValidationState::Quarantined,
            Some(reason),
            target.clone(),
        ) {
            Ok(changed) => changed,
            Err(error) => {
                if self
                    .blobs
                    .relocate_if_absent(&target, record.object_key())
                    .is_err()
                {
                    return Err(ArtifactError::StorageFailure);
                }
                return Err(error);
            }
        };
        self.audit(
            "artifact.quarantined",
            context,
            &changed,
            ArtifactAuditOutcome::Quarantined,
            now_unix_seconds,
        )?;
        Ok(changed.descriptor())
    }

    fn resolve_existing_ingest(
        &self,
        context: &RequestContext,
        request: &IngestRequest,
        existing: &ArtifactRecord,
        now_unix_seconds: u64,
    ) -> Result<ArtifactDescriptor, ArtifactError> {
        self.require_permission(
            context,
            existing,
            ArtifactPermission::Read,
            "artifact.ingest.deduplicated",
            now_unix_seconds,
        )?;
        let descriptor = existing.descriptor();
        if descriptor.size_bytes != u64::try_from(request.bytes.len()).unwrap_or(u64::MAX)
            || descriptor.media_type != request.media_type
            || descriptor.file_name != request.file_name
            || descriptor.kind != request.kind
        {
            return Err(ArtifactError::Conflict);
        }
        self.audit(
            "artifact.ingest.deduplicated",
            context,
            existing,
            ArtifactAuditOutcome::Allowed,
            now_unix_seconds,
        )?;
        Ok(descriptor)
    }

    fn find_scoped(
        &self,
        context: &RequestContext,
        artifact_id: ArtifactId,
    ) -> Result<ArtifactRecord, ArtifactError> {
        self.metadata
            .find(context.tenant_id(), artifact_id)?
            .ok_or(ArtifactError::NotFound)
    }

    fn authorize_download(
        &self,
        context: &RequestContext,
        record: &ArtifactRecord,
        event: &'static str,
        now_unix_seconds: u64,
    ) -> Result<(), ArtifactError> {
        match record.storage_state() {
            StorageState::Available => self.require_permission(
                context,
                record,
                ArtifactPermission::Read,
                event,
                now_unix_seconds,
            ),
            StorageState::Quarantined => {
                if !context.has_scope(AuthScope::SecurityInspect) {
                    self.audit(
                        event,
                        context,
                        record,
                        ArtifactAuditOutcome::Denied,
                        now_unix_seconds,
                    )?;
                    return Err(ArtifactError::Quarantined);
                }
                self.require_permission(
                    context,
                    record,
                    ArtifactPermission::QuarantineRead,
                    event,
                    now_unix_seconds,
                )
            }
            _ => Err(ArtifactError::InvalidState),
        }
    }

    fn require_permission(
        &self,
        context: &RequestContext,
        record: &ArtifactRecord,
        permission: ArtifactPermission,
        event: &'static str,
        now_unix_seconds: u64,
    ) -> Result<(), ArtifactError> {
        if record.has_permission(context.subject(), permission) {
            return Ok(());
        }
        self.audit(
            event,
            context,
            record,
            ArtifactAuditOutcome::Denied,
            now_unix_seconds,
        )?;
        Err(ArtifactError::AccessDenied)
    }

    fn decrypt_record(&self, record: &ArtifactRecord) -> Result<Vec<u8>, ArtifactError> {
        let ciphertext = self
            .blobs
            .get(record.object_key())?
            .ok_or(ArtifactError::StorageFailure)?;
        self.keyring.decrypt(
            record.tenant_id(),
            record.content_sha256(),
            record.size_bytes(),
            record.media_type(),
            record.kind(),
            record.encryption(),
            &ciphertext,
        )
    }

    fn audit(
        &self,
        event: &'static str,
        context: &RequestContext,
        record: &ArtifactRecord,
        outcome: ArtifactAuditOutcome,
        now_unix_seconds: u64,
    ) -> Result<(), ArtifactError> {
        self.metadata.append_audit(ArtifactAuditEvent {
            event,
            tenant_id: record.tenant_id(),
            artifact_id: record.artifact_id(),
            subject_sha256: context.subject(),
            content_sha256: record.content_sha256(),
            outcome,
            recorded_at_unix_seconds: now_unix_seconds,
        })
    }
}

fn require_scope(context: &RequestContext, scope: AuthScope) -> Result<(), ArtifactError> {
    if context.has_scope(scope) {
        Ok(())
    } else {
        Err(ArtifactError::AccessDenied)
    }
}

#[cfg(test)]
mod tests {
    use std::collections::BTreeSet;

    use super::{
        ArtifactScanner, ArtifactService, ArtifactServiceConfig, FailClosedScanner, ScanRequest,
    };
    use crate::crypto::Aes256GcmKeyring;
    use crate::signed_url::DownloadSigner;
    use crate::store::{
        ArtifactMetadataRepository, EncryptedBlobStore, InMemoryBlobStore,
        InMemoryMetadataRepository, LocalEncryptedBlobStore,
    };
    use crate::types::{
        ArtifactError, ArtifactKind, ArtifactPermission, AuthScope, FileName, IngestRequest,
        KeyReference, MediaType, QuarantineReason, RequestContext, ScanEvidence, ScanVerdict,
        ScannerReference, ScannerSignatureVersion, StorageState, SubjectDigest, TenantId,
    };
    use uuid::Uuid;

    #[derive(Clone, Copy, Debug)]
    struct CleanScanner;

    impl ArtifactScanner for CleanScanner {
        fn scan(&self, request: ScanRequest<'_>) -> Result<ScanEvidence, ArtifactError> {
            let verdict = if request.bytes.starts_with(b"MALWARE") {
                ScanVerdict::Suspicious(QuarantineReason::parse("SIGNATURE_MATCH")?)
            } else {
                ScanVerdict::Clean
            };
            Ok(ScanEvidence {
                engine: ScannerReference::parse("scanner.test")?,
                signature_version: ScannerSignatureVersion::parse("fixture-v1")?,
                verdict,
            })
        }
    }

    fn tenant() -> TenantId {
        TenantId::new(Uuid::new_v4()).unwrap_or_else(|error| panic!("tenant: {error}"))
    }

    fn subject(value: &str) -> SubjectDigest {
        SubjectDigest::from_authenticated_subject(value)
            .unwrap_or_else(|error| panic!("subject: {error}"))
    }

    fn context(
        tenant_id: TenantId,
        subject: SubjectDigest,
        scopes: impl IntoIterator<Item = AuthScope>,
    ) -> RequestContext {
        RequestContext::new(tenant_id, subject, scopes)
    }

    fn request(bytes: &[u8]) -> IngestRequest {
        IngestRequest {
            bytes: bytes.to_vec(),
            media_type: MediaType::parse("application/vnd.hancom.hwpx+zip")
                .unwrap_or_else(|error| panic!("media: {error}")),
            file_name: FileName::parse("fixture.hwpx")
                .unwrap_or_else(|error| panic!("filename: {error}")),
            kind: ArtifactKind::Source,
        }
    }

    fn service<S: ArtifactScanner>(
        scanner: S,
    ) -> (
        ArtifactService<InMemoryMetadataRepository, InMemoryBlobStore, S>,
        InMemoryMetadataRepository,
        InMemoryBlobStore,
    ) {
        let metadata = InMemoryMetadataRepository::default();
        let blobs = InMemoryBlobStore::default();
        let encryption_ref = KeyReference::parse("kms.artifact-v1")
            .unwrap_or_else(|error| panic!("encryption ref: {error}"));
        let keyring =
            Aes256GcmKeyring::new(encryption_ref.clone(), [(encryption_ref, [31_u8; 32])])
                .unwrap_or_else(|error| panic!("keyring: {error}"));
        let signer = DownloadSigner::new(
            "https://artifacts.example.test/v1/download",
            KeyReference::parse("hmac.download-v1")
                .unwrap_or_else(|error| panic!("signing ref: {error}")),
            &[41_u8; 32],
            300,
        )
        .unwrap_or_else(|error| panic!("signer: {error}"));
        let config =
            ArtifactServiceConfig::new(1_024, 60).unwrap_or_else(|error| panic!("config: {error}"));
        (
            ArtifactService::new(
                metadata.clone(),
                blobs.clone(),
                scanner,
                keyring,
                signer,
                config,
            ),
            metadata,
            blobs,
        )
    }

    #[test]
    fn ingest_encrypts_and_same_tenant_acl_controls_download() {
        let (service, metadata, blobs) = service(CleanScanner);
        let tenant_id = tenant();
        let owner_subject = subject("owner");
        let reader_subject = subject("reader");
        let owner = context(
            tenant_id,
            owner_subject,
            [
                AuthScope::DocumentRead,
                AuthScope::DocumentWrite,
                AuthScope::ArtifactShare,
            ],
        );
        let reader = context(tenant_id, reader_subject, [AuthScope::DocumentRead]);
        let payload = b"private fixture bytes";
        let descriptor = service
            .ingest(&owner, request(payload), 1_000)
            .unwrap_or_else(|error| panic!("ingest: {error}"));
        let record = metadata
            .find(tenant_id, descriptor.artifact_id)
            .unwrap_or_else(|error| panic!("find: {error}"))
            .unwrap_or_else(|| panic!("record missing"));
        let ciphertext = blobs
            .get(record.object_key())
            .unwrap_or_else(|error| panic!("blob get: {error}"))
            .unwrap_or_else(|| panic!("blob missing"));
        assert_ne!(ciphertext, payload);
        assert!(
            !ciphertext
                .windows(payload.len())
                .any(|window| window == payload)
        );
        assert!(matches!(
            service.download(&reader, descriptor.artifact_id, 1_001),
            Err(ArtifactError::AccessDenied)
        ));

        service
            .set_permissions(
                &owner,
                descriptor.artifact_id,
                reader_subject,
                BTreeSet::from([ArtifactPermission::Read]),
                1_002,
            )
            .unwrap_or_else(|error| panic!("grant: {error}"));
        assert_eq!(
            service
                .download(&reader, descriptor.artifact_id, 1_003)
                .unwrap_or_else(|error| panic!("download: {error}")),
            payload
        );
    }

    #[test]
    fn cross_tenant_access_is_indistinguishable_from_missing() {
        let (service, _metadata, _blobs) = service(CleanScanner);
        let tenant_a = tenant();
        let tenant_b = tenant();
        let actor = subject("actor");
        let owner = context(
            tenant_a,
            actor,
            [AuthScope::DocumentRead, AuthScope::DocumentWrite],
        );
        let attacker = context(
            tenant_b,
            actor,
            [AuthScope::DocumentRead, AuthScope::DocumentWrite],
        );
        let descriptor = service
            .ingest(&owner, request(b"tenant isolated"), 2_000)
            .unwrap_or_else(|error| panic!("ingest: {error}"));
        assert!(matches!(
            service.get_descriptor(&attacker, descriptor.artifact_id, 2_001),
            Err(ArtifactError::NotFound)
        ));
        assert!(matches!(
            service.download(&attacker, descriptor.artifact_id, 2_001),
            Err(ArtifactError::NotFound)
        ));
        assert!(matches!(
            service.issue_download_url(&attacker, descriptor.artifact_id, 2_001),
            Err(ArtifactError::NotFound)
        ));
    }

    #[test]
    fn signed_url_is_subject_bound_and_acl_revocation_invalidates_it() {
        let (service, _metadata, _blobs) = service(CleanScanner);
        let tenant_id = tenant();
        let owner_subject = subject("owner");
        let reader_subject = subject("reader");
        let other_subject = subject("other");
        let owner = context(
            tenant_id,
            owner_subject,
            [
                AuthScope::DocumentRead,
                AuthScope::DocumentWrite,
                AuthScope::ArtifactShare,
            ],
        );
        let reader = context(tenant_id, reader_subject, [AuthScope::DocumentRead]);
        let other = context(tenant_id, other_subject, [AuthScope::DocumentRead]);
        let descriptor = service
            .ingest(&owner, request(b"signed payload"), 3_000)
            .unwrap_or_else(|error| panic!("ingest: {error}"));
        service
            .set_permissions(
                &owner,
                descriptor.artifact_id,
                reader_subject,
                BTreeSet::from([ArtifactPermission::Read]),
                3_001,
            )
            .unwrap_or_else(|error| panic!("grant: {error}"));
        let url = service
            .issue_download_url(&reader, descriptor.artifact_id, 3_002)
            .unwrap_or_else(|error| panic!("issue: {error}"));
        assert_eq!(
            service
                .redeem_download_url(&reader, &url, 3_010)
                .unwrap_or_else(|error| panic!("redeem: {error}")),
            b"signed payload"
        );
        assert!(matches!(
            service.redeem_download_url(&other, &url, 3_010),
            Err(ArtifactError::AccessDenied)
        ));
        service
            .set_permissions(
                &owner,
                descriptor.artifact_id,
                reader_subject,
                BTreeSet::new(),
                3_011,
            )
            .unwrap_or_else(|error| panic!("revoke: {error}"));
        assert!(matches!(
            service.redeem_download_url(&reader, &url, 3_012),
            Err(ArtifactError::AccessDenied)
        ));
    }

    #[test]
    fn quarantine_requires_security_scope_and_blocks_normal_urls() {
        let (service, _metadata, _blobs) = service(CleanScanner);
        let tenant_id = tenant();
        let owner_subject = subject("owner");
        let ordinary = context(
            tenant_id,
            owner_subject,
            [AuthScope::DocumentRead, AuthScope::DocumentWrite],
        );
        let security = context(
            tenant_id,
            owner_subject,
            [
                AuthScope::DocumentRead,
                AuthScope::DocumentWrite,
                AuthScope::SecurityInspect,
                AuthScope::SecurityModify,
            ],
        );
        let descriptor = service
            .ingest(&ordinary, request(b"payload"), 4_000)
            .unwrap_or_else(|error| panic!("ingest: {error}"));
        assert!(matches!(
            service.quarantine(
                &ordinary,
                descriptor.artifact_id,
                QuarantineReason::parse("MANUAL_REVIEW")
                    .unwrap_or_else(|error| panic!("reason: {error}")),
                4_001,
            ),
            Err(ArtifactError::AccessDenied)
        ));
        let quarantined = service
            .quarantine(
                &security,
                descriptor.artifact_id,
                QuarantineReason::parse("MANUAL_REVIEW")
                    .unwrap_or_else(|error| panic!("reason: {error}")),
                4_002,
            )
            .unwrap_or_else(|error| panic!("quarantine: {error}"));
        assert_eq!(quarantined.storage_state, StorageState::Quarantined);
        assert!(matches!(
            service.download(&ordinary, descriptor.artifact_id, 4_003),
            Err(ArtifactError::Quarantined)
        ));
        assert!(matches!(
            service.issue_download_url(&security, descriptor.artifact_id, 4_003),
            Err(ArtifactError::Quarantined)
        ));
        assert_eq!(
            service
                .download(&security, descriptor.artifact_id, 4_004)
                .unwrap_or_else(|error| panic!("security download: {error}")),
            b"payload"
        );
    }

    #[test]
    fn suspicious_and_unverified_scans_are_quarantined_fail_closed() {
        let tenant_id = tenant();
        let actor = subject("owner");
        let context = context(
            tenant_id,
            actor,
            [AuthScope::DocumentRead, AuthScope::DocumentWrite],
        );
        let (clean_service, _metadata, _blobs) = service(CleanScanner);
        let suspicious = clean_service
            .ingest(&context, request(b"MALWARE fixture"), 5_000)
            .unwrap_or_else(|error| panic!("suspicious ingest: {error}"));
        assert_eq!(suspicious.storage_state, StorageState::Quarantined);

        let (fail_closed_service, _metadata, _blobs) = service(FailClosedScanner);
        let unverified = fail_closed_service
            .ingest(&context, request(b"unscanned fixture"), 5_001)
            .unwrap_or_else(|error| panic!("unverified ingest: {error}"));
        assert_eq!(unverified.storage_state, StorageState::Quarantined);
    }

    #[test]
    fn oversized_payload_is_rejected_before_scanning_or_storage() {
        let (service, metadata, _blobs) = service(CleanScanner);
        let context = context(tenant(), subject("owner"), [AuthScope::DocumentWrite]);
        assert!(matches!(
            service.ingest(&context, request(&vec![0_u8; 1_025]), 6_000),
            Err(ArtifactError::PayloadTooLarge { limit_bytes: 1_024 })
        ));
        assert!(
            metadata
                .audit_events()
                .unwrap_or_else(|error| panic!("audits: {error}"))
                .is_empty()
        );
    }

    #[test]
    fn audit_events_never_contain_body_or_signed_url() {
        let (service, metadata, _blobs) = service(CleanScanner);
        let context = context(
            tenant(),
            subject("owner"),
            [AuthScope::DocumentRead, AuthScope::DocumentWrite],
        );
        let secret_body = b"TOP_SECRET_DOCUMENT_BODY";
        let descriptor = service
            .ingest(&context, request(secret_body), 7_000)
            .unwrap_or_else(|error| panic!("ingest: {error}"));
        let url = service
            .issue_download_url(&context, descriptor.artifact_id, 7_001)
            .unwrap_or_else(|error| panic!("issue: {error}"));
        let serialized = serde_json::to_string(
            &metadata
                .audit_events()
                .unwrap_or_else(|error| panic!("audits: {error}")),
        )
        .unwrap_or_else(|error| panic!("serialize: {error}"));
        assert!(!serialized.contains("TOP_SECRET"));
        assert!(!serialized.contains("sig="));
        assert!(!serialized.contains(url.expose()));
    }

    #[test]
    fn service_round_trip_uses_local_encrypted_blob_adapter() {
        let temporary = tempfile::tempdir().unwrap_or_else(|error| panic!("tempdir: {error}"));
        let metadata = InMemoryMetadataRepository::default();
        let blobs = LocalEncryptedBlobStore::create(temporary.path().join("objects"), 2_048)
            .unwrap_or_else(|error| panic!("local blobs: {error}"));
        let encryption_ref = KeyReference::parse("kms.artifact-v1")
            .unwrap_or_else(|error| panic!("encryption ref: {error}"));
        let keyring =
            Aes256GcmKeyring::new(encryption_ref.clone(), [(encryption_ref, [51_u8; 32])])
                .unwrap_or_else(|error| panic!("keyring: {error}"));
        let signer = DownloadSigner::new(
            "https://artifacts.example.test/v1/download",
            KeyReference::parse("hmac.download-v1")
                .unwrap_or_else(|error| panic!("signing ref: {error}")),
            &[61_u8; 32],
            60,
        )
        .unwrap_or_else(|error| panic!("signer: {error}"));
        let service = ArtifactService::new(
            metadata,
            blobs,
            CleanScanner,
            keyring,
            signer,
            ArtifactServiceConfig::new(1_024, 30).unwrap_or_else(|error| panic!("config: {error}")),
        );
        let actor = context(
            tenant(),
            subject("local-owner"),
            [
                AuthScope::DocumentRead,
                AuthScope::DocumentWrite,
                AuthScope::SecurityInspect,
                AuthScope::SecurityModify,
            ],
        );
        let descriptor = service
            .ingest(&actor, request(b"local encrypted payload"), 8_000)
            .unwrap_or_else(|error| panic!("ingest: {error}"));
        assert_eq!(
            service
                .download(&actor, descriptor.artifact_id, 8_001)
                .unwrap_or_else(|error| panic!("download: {error}")),
            b"local encrypted payload"
        );
        service
            .quarantine(
                &actor,
                descriptor.artifact_id,
                QuarantineReason::parse("LOCAL_REVIEW")
                    .unwrap_or_else(|error| panic!("reason: {error}")),
                8_002,
            )
            .unwrap_or_else(|error| panic!("quarantine: {error}"));
        assert_eq!(
            service
                .download(&actor, descriptor.artifact_id, 8_003)
                .unwrap_or_else(|error| panic!("quarantine download: {error}")),
            b"local encrypted payload"
        );
    }
}
