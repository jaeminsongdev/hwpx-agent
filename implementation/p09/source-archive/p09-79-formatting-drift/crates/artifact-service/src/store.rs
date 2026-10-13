use std::collections::{BTreeMap, BTreeSet};
use std::fmt;
use std::io::{self, Read as _};
use std::path::{Path, PathBuf};
use std::sync::{Arc, Mutex, MutexGuard};

use hwpx_agent_foundation::workdir::{SecureWorkspace, WorkspaceError};
use serde::Serialize;
use uuid::Uuid;

use crate::crypto::EncryptionMetadata;
use crate::types::{
    ArtifactAuditEvent, ArtifactDescriptor, ArtifactError, ArtifactId, ArtifactKind,
    ArtifactPermission, ContentDigest, FileName, MediaType, QuarantineReason, ScannerReference,
    ScannerSignatureVersion, StorageState, SubjectDigest, TenantId, ValidationState,
};

pub mod postgres_repository;

#[derive(Clone, Debug, Eq, Hash, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(transparent)]
pub struct ObjectKey(String);

impl ObjectKey {
    /// Parses a bounded relative object key containing only safe lowercase segments.
    ///
    /// # Errors
    ///
    /// Returns [`ArtifactError::InvalidObjectKey`] for absolute, traversing or malformed keys.
    pub fn parse(value: impl Into<String>) -> Result<Self, ArtifactError> {
        let value = value.into();
        let segments = value.split('/').collect::<Vec<_>>();
        let digest = segments
            .get(5)
            .and_then(|segment| segment.strip_suffix(".aes256gcm"))
            .unwrap_or_default();
        let kind_valid = segments.get(3).is_some_and(|kind| {
            matches!(
                *kind,
                "source"
                    | "result"
                    | "document_ir"
                    | "preview"
                    | "evidence"
                    | "trace"
                    | "diff"
                    | "receipt"
            )
        });
        let state_valid = segments
            .get(4)
            .is_some_and(|state| matches!(*state, "available" | "quarantined"));
        let tenant_valid = segments.get(2).is_some_and(|tenant| {
            Uuid::parse_str(tenant)
                .is_ok_and(|uuid| !uuid.is_nil() && uuid.simple().to_string().as_str() == *tenant)
        });
        if value.len() > 512
            || segments.len() != 6
            || segments[0] != "artifacts"
            || segments[1] != "v1"
            || !tenant_valid
            || !kind_valid
            || !state_valid
            || digest.len() != 64
            || !is_lower_hex(digest)
        {
            return Err(ArtifactError::InvalidObjectKey);
        }
        Ok(Self(value))
    }

    /// Derives the canonical tenant/kind/state/content-addressed encrypted object key.
    ///
    /// # Errors
    ///
    /// Returns an error if the derived key violates the object-key contract.
    pub fn for_artifact(
        tenant_id: TenantId,
        kind: ArtifactKind,
        state: StorageState,
        digest: ContentDigest,
    ) -> Result<Self, ArtifactError> {
        Self::parse(format!(
            "artifacts/v1/{}/{}/{}/{}.aes256gcm",
            tenant_id.canonical(),
            kind.as_str(),
            state.as_str(),
            digest.hex()
        ))
    }

    #[must_use]
    pub fn as_str(&self) -> &str {
        &self.0
    }

    fn state(&self) -> StorageState {
        if self.0.contains("/quarantined/") {
            StorageState::Quarantined
        } else {
            StorageState::Available
        }
    }

    fn with_state(&self, state: StorageState) -> Result<Self, ArtifactError> {
        let current = self.state().as_str();
        Self::parse(
            self.0
                .replace(&format!("/{current}/"), &format!("/{}/", state.as_str())),
        )
    }

    fn as_relative_path(&self) -> &Path {
        Path::new(&self.0)
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ArtifactRecord {
    tenant_id: TenantId,
    artifact_id: ArtifactId,
    content_sha256: ContentDigest,
    size_bytes: u64,
    media_type: MediaType,
    file_name: FileName,
    kind: ArtifactKind,
    storage_state: StorageState,
    validation_state: ValidationState,
    quarantine_reason: Option<QuarantineReason>,
    scanner_engine: ScannerReference,
    scanner_signature_version: ScannerSignatureVersion,
    encryption: EncryptionMetadata,
    object_key: ObjectKey,
    acl_version: u64,
    acl: BTreeMap<SubjectDigest, BTreeSet<ArtifactPermission>>,
    created_at_unix_seconds: u64,
}

impl ArtifactRecord {
    #[allow(clippy::too_many_arguments)]
    pub(crate) fn new(
        tenant_id: TenantId,
        artifact_id: ArtifactId,
        content_sha256: ContentDigest,
        size_bytes: u64,
        media_type: MediaType,
        file_name: FileName,
        kind: ArtifactKind,
        storage_state: StorageState,
        validation_state: ValidationState,
        quarantine_reason: Option<QuarantineReason>,
        scanner_engine: ScannerReference,
        scanner_signature_version: ScannerSignatureVersion,
        encryption: EncryptionMetadata,
        object_key: ObjectKey,
        owner: SubjectDigest,
        created_at_unix_seconds: u64,
    ) -> Self {
        let owner_permissions = BTreeSet::from([
            ArtifactPermission::Read,
            ArtifactPermission::Manage,
            ArtifactPermission::QuarantineRead,
        ]);
        Self {
            tenant_id,
            artifact_id,
            content_sha256,
            size_bytes,
            media_type,
            file_name,
            kind,
            storage_state,
            validation_state,
            quarantine_reason,
            scanner_engine,
            scanner_signature_version,
            encryption,
            object_key,
            acl_version: 1,
            acl: BTreeMap::from([(owner, owner_permissions)]),
            created_at_unix_seconds,
        }
    }

    #[must_use]
    pub fn descriptor(&self) -> ArtifactDescriptor {
        ArtifactDescriptor {
            artifact_id: self.artifact_id,
            sha256: self.content_sha256,
            size_bytes: self.size_bytes,
            media_type: self.media_type.clone(),
            file_name: self.file_name.clone(),
            kind: self.kind,
            storage_state: self.storage_state,
            validation_state: self.validation_state,
            quarantine_reason: self.quarantine_reason.clone(),
            scanner_engine: self.scanner_engine.clone(),
            scanner_signature_version: self.scanner_signature_version.clone(),
            created_at_unix_seconds: self.created_at_unix_seconds,
        }
    }

    #[must_use]
    pub const fn tenant_id(&self) -> TenantId {
        self.tenant_id
    }

    #[must_use]
    pub const fn artifact_id(&self) -> ArtifactId {
        self.artifact_id
    }

    #[must_use]
    pub const fn content_sha256(&self) -> ContentDigest {
        self.content_sha256
    }

    #[must_use]
    pub const fn size_bytes(&self) -> u64 {
        self.size_bytes
    }

    #[must_use]
    pub fn media_type(&self) -> &MediaType {
        &self.media_type
    }

    #[must_use]
    pub const fn kind(&self) -> ArtifactKind {
        self.kind
    }

    #[must_use]
    pub const fn storage_state(&self) -> StorageState {
        self.storage_state
    }

    #[must_use]
    pub fn encryption(&self) -> &EncryptionMetadata {
        &self.encryption
    }

    #[must_use]
    pub fn object_key(&self) -> &ObjectKey {
        &self.object_key
    }

    #[must_use]
    pub const fn acl_version(&self) -> u64 {
        self.acl_version
    }

    #[must_use]
    pub fn has_permission(&self, subject: SubjectDigest, permission: ArtifactPermission) -> bool {
        self.acl
            .get(&subject)
            .is_some_and(|permissions| permissions.contains(&permission))
    }

    #[must_use]
    pub fn permissions_for(&self, subject: SubjectDigest) -> BTreeSet<ArtifactPermission> {
        self.acl.get(&subject).cloned().unwrap_or_default()
    }

    fn validate(&self) -> Result<(), ArtifactError> {
        let security_state_consistent = match self.storage_state {
            StorageState::Available => {
                self.validation_state == ValidationState::Verified
                    && self.quarantine_reason.is_none()
            }
            StorageState::Quarantined => {
                matches!(
                    self.validation_state,
                    ValidationState::Unverified
                        | ValidationState::Failed
                        | ValidationState::Quarantined
                ) && self.quarantine_reason.is_some()
            }
            StorageState::Staged | StorageState::Orphaned | StorageState::Purging => false,
        };
        let expected_key = ObjectKey::for_artifact(
            self.tenant_id,
            self.kind,
            self.storage_state,
            self.content_sha256,
        )?;
        let has_manager = self
            .acl
            .values()
            .any(|permissions| permissions.contains(&ArtifactPermission::Manage));
        if !security_state_consistent
            || expected_key != self.object_key
            || self.acl_version == 0
            || !has_manager
        {
            return Err(ArtifactError::InvalidState);
        }
        Ok(())
    }
}

pub trait ArtifactMetadataRepository: fmt::Debug + Send + Sync {
    /// Finds one artifact strictly inside the supplied tenant boundary.
    ///
    /// # Errors
    ///
    /// Returns an error when the repository cannot perform a trustworthy lookup.
    fn find(
        &self,
        tenant_id: TenantId,
        artifact_id: ArtifactId,
    ) -> Result<Option<ArtifactRecord>, ArtifactError>;

    /// Finds the tenant-local identity for immutable content.
    ///
    /// # Errors
    ///
    /// Returns an error when the repository cannot perform a trustworthy lookup.
    fn find_by_content(
        &self,
        tenant_id: TenantId,
        digest: ContentDigest,
    ) -> Result<Option<ArtifactRecord>, ArtifactError>;

    /// Inserts a fully validated record without replacing either identity.
    ///
    /// # Errors
    ///
    /// Returns an error for invalid state, duplicate identity or repository failure.
    fn insert(&self, record: ArtifactRecord) -> Result<(), ArtifactError>;

    /// Performs an expected-state transition and increments the authorization generation.
    ///
    /// # Errors
    ///
    /// Returns an error for missing identity, state conflict or an invalid resulting record.
    #[allow(clippy::too_many_arguments)]
    fn transition_state(
        &self,
        tenant_id: TenantId,
        artifact_id: ArtifactId,
        expected_acl_version: u64,
        expected_state: StorageState,
        new_state: StorageState,
        validation_state: ValidationState,
        quarantine_reason: Option<QuarantineReason>,
        object_key: ObjectKey,
    ) -> Result<ArtifactRecord, ArtifactError>;

    /// Replaces a subject ACL entry while preserving at least one manager.
    ///
    /// # Errors
    ///
    /// Returns an error for missing identity, generation overflow or an invalid resulting ACL.
    fn set_permissions(
        &self,
        tenant_id: TenantId,
        artifact_id: ArtifactId,
        expected_acl_version: u64,
        subject: SubjectDigest,
        permissions: BTreeSet<ArtifactPermission>,
    ) -> Result<ArtifactRecord, ArtifactError>;

    /// Appends one structurally safe audit event.
    ///
    /// # Errors
    ///
    /// Returns an error when durable audit publication fails.
    fn append_audit(&self, event: ArtifactAuditEvent) -> Result<(), ArtifactError>;

    /// Reads audit events for verification and an eventual durable adapter.
    ///
    /// # Errors
    ///
    /// Returns an error when audit storage cannot be read safely.
    fn audit_events(&self) -> Result<Vec<ArtifactAuditEvent>, ArtifactError>;
}

pub trait EncryptedBlobStore: fmt::Debug + Send + Sync {
    /// Publishes ciphertext under a create-new object key.
    ///
    /// # Errors
    ///
    /// Returns an error if the object exists or publication fails.
    fn put_if_absent(&self, key: &ObjectKey, ciphertext: &[u8]) -> Result<(), ArtifactError>;

    /// Reads ciphertext without exposing a filesystem or provider path.
    ///
    /// # Errors
    ///
    /// Returns an error when object storage cannot be read safely.
    fn get(&self, key: &ObjectKey) -> Result<Option<Vec<u8>>, ArtifactError>;

    /// Moves one complete ciphertext object to an absent target key.
    ///
    /// # Errors
    ///
    /// Returns an error for a missing source, existing target or non-atomic failure.
    fn relocate_if_absent(
        &self,
        source: &ObjectKey,
        target: &ObjectKey,
    ) -> Result<(), ArtifactError>;
}

#[derive(Clone, Debug, Default)]
pub struct InMemoryMetadataRepository {
    state: Arc<Mutex<MetadataState>>,
}

#[derive(Debug, Default)]
struct MetadataState {
    records: BTreeMap<(TenantId, ArtifactId), ArtifactRecord>,
    by_content: BTreeMap<(TenantId, ContentDigest), ArtifactId>,
    audit_events: Vec<ArtifactAuditEvent>,
}

impl ArtifactMetadataRepository for InMemoryMetadataRepository {
    fn find(
        &self,
        tenant_id: TenantId,
        artifact_id: ArtifactId,
    ) -> Result<Option<ArtifactRecord>, ArtifactError> {
        Ok(lock(&self.state)?
            .records
            .get(&(tenant_id, artifact_id))
            .cloned())
    }

    fn find_by_content(
        &self,
        tenant_id: TenantId,
        digest: ContentDigest,
    ) -> Result<Option<ArtifactRecord>, ArtifactError> {
        let state = lock(&self.state)?;
        Ok(state
            .by_content
            .get(&(tenant_id, digest))
            .and_then(|artifact_id| state.records.get(&(tenant_id, *artifact_id)))
            .cloned())
    }

    fn insert(&self, record: ArtifactRecord) -> Result<(), ArtifactError> {
        record.validate()?;
        let mut state = lock(&self.state)?;
        let identity = (record.tenant_id, record.artifact_id);
        let content_identity = (record.tenant_id, record.content_sha256);
        if state.records.contains_key(&identity) || state.by_content.contains_key(&content_identity)
        {
            return Err(ArtifactError::Conflict);
        }
        state
            .by_content
            .insert(content_identity, record.artifact_id);
        state.records.insert(identity, record);
        Ok(())
    }

    fn transition_state(
        &self,
        tenant_id: TenantId,
        artifact_id: ArtifactId,
        expected_acl_version: u64,
        expected_state: StorageState,
        new_state: StorageState,
        validation_state: ValidationState,
        quarantine_reason: Option<QuarantineReason>,
        object_key: ObjectKey,
    ) -> Result<ArtifactRecord, ArtifactError> {
        let mut state = lock(&self.state)?;
        let current = state
            .records
            .get(&(tenant_id, artifact_id))
            .ok_or(ArtifactError::NotFound)?;
        if current.storage_state != expected_state || current.acl_version != expected_acl_version {
            return Err(ArtifactError::Conflict);
        }
        let mut changed = current.clone();
        changed.storage_state = new_state;
        changed.validation_state = validation_state;
        changed.quarantine_reason = quarantine_reason;
        changed.object_key = object_key;
        changed.acl_version = changed
            .acl_version
            .checked_add(1)
            .ok_or(ArtifactError::Conflict)?;
        changed.validate()?;
        state
            .records
            .insert((tenant_id, artifact_id), changed.clone());
        Ok(changed)
    }

    fn set_permissions(
        &self,
        tenant_id: TenantId,
        artifact_id: ArtifactId,
        expected_acl_version: u64,
        subject: SubjectDigest,
        permissions: BTreeSet<ArtifactPermission>,
    ) -> Result<ArtifactRecord, ArtifactError> {
        let mut state = lock(&self.state)?;
        let current = state
            .records
            .get(&(tenant_id, artifact_id))
            .ok_or(ArtifactError::NotFound)?;
        if current.acl_version != expected_acl_version {
            return Err(ArtifactError::Conflict);
        }
        let mut changed = current.clone();
        if permissions.is_empty() {
            changed.acl.remove(&subject);
        } else {
            changed.acl.insert(subject, permissions);
        }
        changed.acl_version = changed
            .acl_version
            .checked_add(1)
            .ok_or(ArtifactError::Conflict)?;
        changed.validate()?;
        state
            .records
            .insert((tenant_id, artifact_id), changed.clone());
        Ok(changed)
    }

    fn append_audit(&self, event: ArtifactAuditEvent) -> Result<(), ArtifactError> {
        lock(&self.state)?.audit_events.push(event);
        Ok(())
    }

    fn audit_events(&self) -> Result<Vec<ArtifactAuditEvent>, ArtifactError> {
        Ok(lock(&self.state)?.audit_events.clone())
    }
}

#[derive(Clone, Debug, Default)]
pub struct InMemoryBlobStore {
    objects: Arc<Mutex<BTreeMap<ObjectKey, Vec<u8>>>>,
}

impl EncryptedBlobStore for InMemoryBlobStore {
    fn put_if_absent(&self, key: &ObjectKey, ciphertext: &[u8]) -> Result<(), ArtifactError> {
        let mut objects = lock(&self.objects)?;
        if objects.contains_key(key) {
            return Err(ArtifactError::Conflict);
        }
        objects.insert(key.clone(), ciphertext.to_vec());
        Ok(())
    }

    fn get(&self, key: &ObjectKey) -> Result<Option<Vec<u8>>, ArtifactError> {
        Ok(lock(&self.objects)?.get(key).cloned())
    }

    fn relocate_if_absent(
        &self,
        source: &ObjectKey,
        target: &ObjectKey,
    ) -> Result<(), ArtifactError> {
        let mut objects = lock(&self.objects)?;
        if objects.contains_key(target) {
            return Err(ArtifactError::Conflict);
        }
        let ciphertext = objects
            .get(source)
            .cloned()
            .ok_or(ArtifactError::StorageFailure)?;
        objects.insert(target.clone(), ciphertext);
        objects.remove(source);
        Ok(())
    }
}

#[derive(Clone, Debug)]
pub struct LocalEncryptedBlobStore {
    workspace: SecureWorkspace,
    max_ciphertext_bytes: u64,
}

impl LocalEncryptedBlobStore {
    /// Creates or safely reopens a bounded local encrypted-object workspace.
    ///
    /// # Errors
    ///
    /// Returns an error if the root is unsafe or the ciphertext bound cannot hold an AEAD tag.
    pub fn create(
        root: impl AsRef<Path>,
        max_ciphertext_bytes: u64,
    ) -> Result<Self, ArtifactError> {
        if !(16..=1_099_511_627_792).contains(&max_ciphertext_bytes) {
            return Err(ArtifactError::PayloadTooLarge {
                limit_bytes: 1_099_511_627_792,
            });
        }
        let workspace =
            SecureWorkspace::create(root).map_err(|error| map_workspace_error(&error))?;
        Ok(Self {
            workspace,
            max_ciphertext_bytes,
        })
    }

    fn open(&self, key: &ObjectKey) -> Result<Option<Vec<u8>>, ArtifactError> {
        let reader = match key.state() {
            StorageState::Available => self.workspace.open_output(key.as_relative_path()),
            StorageState::Quarantined => self.workspace.open_quarantined(key.as_relative_path()),
            _ => return Err(ArtifactError::InvalidState),
        };
        let mut reader = match reader {
            Ok(reader) => reader,
            Err(WorkspaceError::Io(error)) if error.kind() == io::ErrorKind::NotFound => {
                return Ok(None);
            }
            Err(error) => return Err(map_workspace_error(&error)),
        };
        let read_limit = self
            .max_ciphertext_bytes
            .checked_add(1)
            .ok_or(ArtifactError::StorageFailure)?;
        let mut ciphertext = Vec::new();
        reader
            .by_ref()
            .take(read_limit)
            .read_to_end(&mut ciphertext)
            .map_err(|_| ArtifactError::StorageFailure)?;
        if u64::try_from(ciphertext.len()).map_err(|_| ArtifactError::StorageFailure)?
            > self.max_ciphertext_bytes
        {
            return Err(ArtifactError::StorageFailure);
        }
        Ok(Some(ciphertext))
    }
}

impl EncryptedBlobStore for LocalEncryptedBlobStore {
    fn put_if_absent(&self, key: &ObjectKey, ciphertext: &[u8]) -> Result<(), ArtifactError> {
        if u64::try_from(ciphertext.len()).map_err(|_| ArtifactError::StorageFailure)?
            > self.max_ciphertext_bytes
        {
            return Err(ArtifactError::PayloadTooLarge {
                limit_bytes: self.max_ciphertext_bytes,
            });
        }
        let staging_relative = PathBuf::from(format!(
            "artifact-write/{}.ciphertext",
            Uuid::new_v4().simple()
        ));
        let staged = self
            .workspace
            .stage_bytes(&staging_relative, ciphertext)
            .map_err(|error| map_workspace_error(&error))?;
        let publication = match key.state() {
            StorageState::Available => self.workspace.publish(&staged, key.as_relative_path()),
            StorageState::Quarantined => self.workspace.quarantine(&staged, key.as_relative_path()),
            _ => return Err(ArtifactError::InvalidState),
        };
        if let Err(error) = publication {
            if self.workspace.open_staged(&staged).is_ok()
                && self.workspace.discard_staged(&staged).is_err()
            {
                return Err(ArtifactError::StorageFailure);
            }
            return Err(map_workspace_error(&error));
        }
        Ok(())
    }

    fn get(&self, key: &ObjectKey) -> Result<Option<Vec<u8>>, ArtifactError> {
        self.open(key)
    }

    fn relocate_if_absent(
        &self,
        source: &ObjectKey,
        target: &ObjectKey,
    ) -> Result<(), ArtifactError> {
        if source.state() == target.state()
            || source.with_state(target.state()).as_ref() != Ok(target)
        {
            return Err(ArtifactError::InvalidState);
        }
        match (source.state(), target.state()) {
            (StorageState::Available, StorageState::Quarantined) => self
                .workspace
                .quarantine_published(source.as_relative_path(), target.as_relative_path()),
            (StorageState::Quarantined, StorageState::Available) => self
                .workspace
                .restore_quarantined(source.as_relative_path(), target.as_relative_path()),
            _ => return Err(ArtifactError::InvalidState),
        }
        .map_err(|error| map_workspace_error(&error))
    }
}

fn map_workspace_error(error: &WorkspaceError) -> ArtifactError {
    match error {
        WorkspaceError::ArtifactExists => ArtifactError::Conflict,
        WorkspaceError::ArtifactDigestMismatch => ArtifactError::IntegrityMismatch,
        WorkspaceError::InvalidRelativePath | WorkspaceError::EscapesWorkspace => {
            ArtifactError::InvalidObjectKey
        }
        WorkspaceError::LinkNotAllowed
        | WorkspaceError::ArtifactPublishedIncomplete
        | WorkspaceError::Io(_) => ArtifactError::StorageFailure,
    }
}

fn is_lower_hex(value: &str) -> bool {
    value
        .bytes()
        .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

fn lock<T>(mutex: &Mutex<T>) -> Result<MutexGuard<'_, T>, ArtifactError> {
    mutex.lock().map_err(|_| ArtifactError::StorageFailure)
}

#[cfg(test)]
mod tests {
    use std::collections::BTreeSet;

    use super::{
        ArtifactMetadataRepository, ArtifactRecord, EncryptedBlobStore, InMemoryBlobStore,
        InMemoryMetadataRepository, LocalEncryptedBlobStore, ObjectKey,
    };
    use crate::crypto::Aes256GcmKeyring;
    use crate::types::{
        ArtifactError, ArtifactId, ArtifactKind, ArtifactPermission, ContentDigest, FileName,
        KeyReference, MediaType, QuarantineReason, ScannerReference, ScannerSignatureVersion,
        StorageState, SubjectDigest, TenantId, ValidationState,
    };
    use uuid::Uuid;

    fn fixture_record() -> ArtifactRecord {
        let tenant =
            TenantId::new(Uuid::new_v4()).unwrap_or_else(|error| panic!("tenant: {error}"));
        let subject = SubjectDigest::from_authenticated_subject("owner")
            .unwrap_or_else(|error| panic!("subject: {error}"));
        let media =
            MediaType::parse("application/pdf").unwrap_or_else(|error| panic!("media: {error}"));
        let key_ref = KeyReference::parse("kms.artifact-v1")
            .unwrap_or_else(|error| panic!("key ref: {error}"));
        let keyring = Aes256GcmKeyring::new(key_ref.clone(), [(key_ref, [9_u8; 32])])
            .unwrap_or_else(|error| panic!("keyring: {error}"));
        let digest = ContentDigest::of(b"payload");
        let encrypted = keyring
            .encrypt(tenant, digest, 7, &media, ArtifactKind::Result, b"payload")
            .unwrap_or_else(|error| panic!("encrypt: {error}"));
        let key = ObjectKey::for_artifact(
            tenant,
            ArtifactKind::Result,
            StorageState::Available,
            digest,
        )
        .unwrap_or_else(|error| panic!("object key: {error}"));
        ArtifactRecord::new(
            tenant,
            ArtifactId::generate(),
            digest,
            7,
            media,
            FileName::parse("result.pdf").unwrap_or_else(|error| panic!("filename: {error}")),
            ArtifactKind::Result,
            StorageState::Available,
            ValidationState::Verified,
            None,
            ScannerReference::parse("scanner.test")
                .unwrap_or_else(|error| panic!("scanner: {error}")),
            ScannerSignatureVersion::parse("test-v1")
                .unwrap_or_else(|error| panic!("scanner version: {error}")),
            encrypted.metadata,
            key,
            subject,
            100,
        )
    }

    #[test]
    fn repository_scopes_identity_by_tenant_and_preserves_manager() {
        let repository = InMemoryMetadataRepository::default();
        let record = fixture_record();
        repository
            .insert(record.clone())
            .unwrap_or_else(|error| panic!("insert: {error}"));
        let other_tenant =
            TenantId::new(Uuid::new_v4()).unwrap_or_else(|error| panic!("other tenant: {error}"));
        assert_eq!(
            repository
                .find(other_tenant, record.artifact_id())
                .unwrap_or_else(|error| panic!("find: {error}")),
            None
        );
        assert!(matches!(
            repository.insert(record.clone()),
            Err(ArtifactError::Conflict)
        ));

        let owner = record
            .acl
            .iter()
            .find_map(|(subject, permissions)| {
                permissions
                    .contains(&ArtifactPermission::Manage)
                    .then_some(*subject)
            })
            .unwrap_or_else(|| panic!("owner missing"));
        assert!(matches!(
            repository.set_permissions(
                record.tenant_id(),
                record.artifact_id(),
                record.acl_version(),
                owner,
                BTreeSet::new(),
            ),
            Err(ArtifactError::InvalidState)
        ));
        let preserved = repository
            .find(record.tenant_id(), record.artifact_id())
            .unwrap_or_else(|error| panic!("find preserved: {error}"))
            .unwrap_or_else(|| panic!("preserved record missing"));
        assert!(preserved.has_permission(owner, ArtifactPermission::Manage));
        assert_eq!(preserved.acl_version(), 1);
    }

    #[test]
    fn repository_rejects_inconsistent_security_state() {
        let repository = InMemoryMetadataRepository::default();
        let record = fixture_record();
        repository
            .insert(record.clone())
            .unwrap_or_else(|error| panic!("insert: {error}"));
        let quarantine_key = ObjectKey::for_artifact(
            record.tenant_id(),
            record.kind(),
            StorageState::Quarantined,
            record.content_sha256(),
        )
        .unwrap_or_else(|error| panic!("quarantine key: {error}"));
        let result = repository.transition_state(
            record.tenant_id(),
            record.artifact_id(),
            record.acl_version(),
            StorageState::Available,
            StorageState::Quarantined,
            ValidationState::Verified,
            Some(
                QuarantineReason::parse("MANUAL_REVIEW")
                    .unwrap_or_else(|error| panic!("reason: {error}")),
            ),
            quarantine_key,
        );
        assert!(matches!(result, Err(ArtifactError::InvalidState)));
        let preserved = repository
            .find(record.tenant_id(), record.artifact_id())
            .unwrap_or_else(|error| panic!("find: {error}"))
            .unwrap_or_else(|| panic!("record missing"));
        assert_eq!(preserved.storage_state(), StorageState::Available);
        assert_eq!(preserved.acl_version(), 1);
    }

    #[test]
    fn stale_acl_authority_cannot_mutate_permissions_or_storage() {
        let repository = InMemoryMetadataRepository::default();
        let record = fixture_record();
        repository
            .insert(record.clone())
            .unwrap_or_else(|error| panic!("fixture insert: {error}"));
        let subject = SubjectDigest::from_authenticated_subject("another-manager")
            .unwrap_or_else(|error| panic!("fixture subject: {error}"));
        let changed = repository
            .set_permissions(
                record.tenant_id(),
                record.artifact_id(),
                1,
                subject,
                BTreeSet::from([ArtifactPermission::Manage]),
            )
            .unwrap_or_else(|error| panic!("fixture grant: {error}"));
        assert_eq!(changed.acl_version(), 2);
        assert_eq!(
            repository.set_permissions(
                record.tenant_id(),
                record.artifact_id(),
                1,
                subject,
                BTreeSet::new()
            ),
            Err(ArtifactError::Conflict)
        );
        let target = ObjectKey::for_artifact(
            record.tenant_id(),
            record.kind(),
            StorageState::Quarantined,
            record.content_sha256(),
        )
        .unwrap_or_else(|error| panic!("fixture key: {error}"));
        assert_eq!(
            repository.transition_state(
                record.tenant_id(),
                record.artifact_id(),
                1,
                StorageState::Available,
                StorageState::Quarantined,
                ValidationState::Quarantined,
                Some(
                    QuarantineReason::parse("MANUAL_REVIEW")
                        .unwrap_or_else(|error| panic!("reason: {error}"))
                ),
                target
            ),
            Err(ArtifactError::Conflict)
        );
        assert_eq!(
            repository
                .find(record.tenant_id(), record.artifact_id())
                .unwrap_or_else(|error| panic!("find: {error}")),
            Some(changed)
        );
    }

    #[test]
    fn blob_store_never_overwrites_and_relocates_atomically() {
        let store = InMemoryBlobStore::default();
        let tenant =
            TenantId::new(Uuid::new_v4()).unwrap_or_else(|error| panic!("tenant: {error}"));
        let digest = ContentDigest::of(b"ciphertext");
        let source = ObjectKey::for_artifact(
            tenant,
            ArtifactKind::Source,
            StorageState::Available,
            digest,
        )
        .unwrap_or_else(|error| panic!("source: {error}"));
        let target = ObjectKey::for_artifact(
            tenant,
            ArtifactKind::Source,
            StorageState::Quarantined,
            digest,
        )
        .unwrap_or_else(|error| panic!("target: {error}"));
        store
            .put_if_absent(&source, b"ciphertext")
            .unwrap_or_else(|error| panic!("put: {error}"));
        assert!(matches!(
            store.put_if_absent(&source, b"replacement"),
            Err(ArtifactError::Conflict)
        ));
        store
            .relocate_if_absent(&source, &target)
            .unwrap_or_else(|error| panic!("relocate: {error}"));
        assert_eq!(
            store
                .get(&source)
                .unwrap_or_else(|error| panic!("get: {error}")),
            None
        );
        assert_eq!(
            store
                .get(&target)
                .unwrap_or_else(|error| panic!("get: {error}")),
            Some(b"ciphertext".to_vec())
        );
    }

    #[test]
    fn local_store_uses_create_new_and_separate_quarantine_namespace() {
        let temporary = tempfile::tempdir().unwrap_or_else(|error| panic!("tempdir: {error}"));
        let store = LocalEncryptedBlobStore::create(temporary.path().join("objects"), 1_024)
            .unwrap_or_else(|error| panic!("local store: {error}"));
        let tenant =
            TenantId::new(Uuid::new_v4()).unwrap_or_else(|error| panic!("tenant: {error}"));
        let digest = ContentDigest::of(b"encrypted bytes");
        let available = ObjectKey::for_artifact(
            tenant,
            ArtifactKind::Evidence,
            StorageState::Available,
            digest,
        )
        .unwrap_or_else(|error| panic!("available key: {error}"));
        let quarantined = ObjectKey::for_artifact(
            tenant,
            ArtifactKind::Evidence,
            StorageState::Quarantined,
            digest,
        )
        .unwrap_or_else(|error| panic!("quarantine key: {error}"));

        store
            .put_if_absent(&available, b"encrypted bytes")
            .unwrap_or_else(|error| panic!("put: {error}"));
        assert!(matches!(
            store.put_if_absent(&available, b"replacement"),
            Err(ArtifactError::Conflict)
        ));
        assert_eq!(
            store
                .get(&available)
                .unwrap_or_else(|error| panic!("get available: {error}")),
            Some(b"encrypted bytes".to_vec())
        );
        store
            .relocate_if_absent(&available, &quarantined)
            .unwrap_or_else(|error| panic!("quarantine: {error}"));
        assert_eq!(
            store
                .get(&available)
                .unwrap_or_else(|error| panic!("get old: {error}")),
            None
        );
        assert_eq!(
            store
                .get(&quarantined)
                .unwrap_or_else(|error| panic!("get quarantine: {error}")),
            Some(b"encrypted bytes".to_vec())
        );
        store
            .relocate_if_absent(&quarantined, &available)
            .unwrap_or_else(|error| panic!("restore: {error}"));
        assert_eq!(
            store
                .get(&available)
                .unwrap_or_else(|error| panic!("get restored: {error}")),
            Some(b"encrypted bytes".to_vec())
        );
    }

    #[test]
    fn object_keys_reject_noncanonical_paths() {
        for invalid in [
            "",
            "../escape",
            "artifacts/v1/a/source/available/a.aes256gcm",
            "artifacts/v1/00000000000000000000000000000000/source/available/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.aes256gcm",
            "artifacts/v1/00000000000000000000000000000000/source/staged/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.aes256gcm",
            "artifacts/v1/00000000000000000000000000000000/unknown/available/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.aes256gcm",
        ] {
            assert!(ObjectKey::parse(invalid).is_err(), "accepted {invalid}");
        }
    }
}
