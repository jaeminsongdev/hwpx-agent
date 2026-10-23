#![forbid(unsafe_code)]

mod crypto;
pub mod key_custody;
mod service;
mod signed_url;
mod store;
mod types;

pub use crypto::{Aes256GcmKeyring, EncryptionMetadata};
pub use service::{
    ArtifactScanner, ArtifactService, ArtifactServiceConfig, FailClosedScanner, ScanRequest,
};
pub use signed_url::{DownloadClaims, DownloadSigner};
pub use store::postgres_repository::{
    LocalPostgresConfig, LocalPostgresMetadataRepository, PostgresConnectFailure,
    PostgresConnectStage,
};
pub use store::{
    ArtifactMetadataRepository, ArtifactRecord, EncryptedBlobStore, InMemoryBlobStore,
    InMemoryMetadataRepository, LocalEncryptedBlobStore, ObjectKey,
};
pub use types::{
    ArtifactAuditEvent, ArtifactAuditOutcome, ArtifactDescriptor, ArtifactError, ArtifactId,
    ArtifactKind, ArtifactPermission, AuthScope, ContentDigest, FileName, IngestRequest,
    KeyReference, MediaType, QuarantineReason, RequestContext, ScanEvidence, ScanVerdict,
    ScannerReference, ScannerSignatureVersion, SignedDownloadUrl, StorageState, SubjectDigest,
    TenantId, ValidationState,
};
