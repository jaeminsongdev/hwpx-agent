use std::collections::BTreeSet;
use std::fmt;

use serde::de::Error as _;
use serde::{Deserialize, Deserializer, Serialize, Serializer};
use sha2::{Digest, Sha256};
use thiserror::Error;
use unicode_normalization::UnicodeNormalization as _;
use uuid::Uuid;

pub const SHA256_BYTES: usize = 32;

#[derive(Debug, Error, Clone, Eq, PartialEq)]
pub enum ArtifactError {
    #[error("artifact identifier is invalid")]
    InvalidArtifactId,
    #[error("tenant identifier is invalid")]
    InvalidTenantId,
    #[error("subject identifier is invalid")]
    InvalidSubject,
    #[error("SHA-256 digest is invalid")]
    InvalidDigest,
    #[error("media type is invalid")]
    InvalidMediaType,
    #[error("file name is invalid")]
    InvalidFileName,
    #[error("key reference is invalid")]
    InvalidKeyReference,
    #[error("scanner reference or signature version is invalid")]
    InvalidScannerReference,
    #[error("quarantine reason is invalid")]
    InvalidQuarantineReason,
    #[error("object key is invalid")]
    InvalidObjectKey,
    #[error("signed URL is invalid")]
    InvalidSignedUrl,
    #[error("signed URL has expired or has an invalid lifetime")]
    InvalidSignedUrlLifetime,
    #[error("payload exceeds the configured limit of {limit_bytes} bytes")]
    PayloadTooLarge { limit_bytes: u64 },
    #[error("access denied")]
    AccessDenied,
    #[error("artifact was not found")]
    NotFound,
    #[error("artifact is quarantined")]
    Quarantined,
    #[error("artifact state transition is invalid")]
    InvalidState,
    #[error("artifact integrity verification failed")]
    IntegrityMismatch,
    #[error("cryptographic operation failed")]
    CryptoFailure,
    #[error("storage operation failed")]
    StorageFailure,
    #[error("metadata operation conflicted")]
    Conflict,
    #[error("required scanner did not produce a clean verdict")]
    ScanNotClean,
}

impl ArtifactError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidArtifactId => "ARTIFACT_ID_INVALID",
            Self::InvalidTenantId => "TENANT_ID_INVALID",
            Self::InvalidSubject => "SUBJECT_INVALID",
            Self::InvalidDigest => "DIGEST_INVALID",
            Self::InvalidMediaType => "MEDIA_TYPE_INVALID",
            Self::InvalidFileName => "FILE_NAME_INVALID",
            Self::InvalidKeyReference => "KEY_REFERENCE_INVALID",
            Self::InvalidScannerReference => "SCANNER_REFERENCE_INVALID",
            Self::InvalidQuarantineReason => "QUARANTINE_REASON_INVALID",
            Self::InvalidObjectKey => "OBJECT_KEY_INVALID",
            Self::InvalidSignedUrl => "SIGNED_URL_INVALID",
            Self::InvalidSignedUrlLifetime => "SIGNED_URL_LIFETIME_INVALID",
            Self::PayloadTooLarge { .. } => "PAYLOAD_TOO_LARGE",
            Self::AccessDenied => "ACCESS_DENIED",
            Self::NotFound => "ARTIFACT_NOT_FOUND",
            Self::Quarantined => "ARTIFACT_QUARANTINED",
            Self::InvalidState => "ARTIFACT_STATE_INVALID",
            Self::IntegrityMismatch => "ARTIFACT_INTEGRITY_MISMATCH",
            Self::CryptoFailure => "CRYPTO_FAILURE",
            Self::StorageFailure => "STORAGE_FAILURE",
            Self::Conflict => "METADATA_CONFLICT",
            Self::ScanNotClean => "SCAN_NOT_CLEAN",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub struct TenantId(Uuid);

impl TenantId {
    /// Creates a non-nil tenant identifier.
    ///
    /// # Errors
    ///
    /// Returns [`ArtifactError::InvalidTenantId`] for the nil UUID.
    pub fn new(value: Uuid) -> Result<Self, ArtifactError> {
        if value.is_nil() {
            Err(ArtifactError::InvalidTenantId)
        } else {
            Ok(Self(value))
        }
    }

    #[must_use]
    pub const fn as_uuid(self) -> Uuid {
        self.0
    }

    #[must_use]
    pub fn canonical(self) -> String {
        self.0.simple().to_string()
    }
}

#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub struct ArtifactId(Uuid);

impl ArtifactId {
    #[must_use]
    pub fn generate() -> Self {
        Self(Uuid::new_v4())
    }

    /// Parses the canonical `art_` plus 32 lowercase hexadecimal UUID form.
    ///
    /// # Errors
    ///
    /// Returns [`ArtifactError::InvalidArtifactId`] for any noncanonical or nil identifier.
    pub fn parse(value: &str) -> Result<Self, ArtifactError> {
        let encoded = value
            .strip_prefix("art_")
            .ok_or(ArtifactError::InvalidArtifactId)?;
        if encoded.len() != 32 || !is_lower_hex(encoded) {
            return Err(ArtifactError::InvalidArtifactId);
        }
        let uuid = Uuid::parse_str(encoded).map_err(|_| ArtifactError::InvalidArtifactId)?;
        if uuid.is_nil() {
            return Err(ArtifactError::InvalidArtifactId);
        }
        Ok(Self(uuid))
    }

    #[must_use]
    pub const fn as_uuid(self) -> Uuid {
        self.0
    }

    #[must_use]
    pub fn public_id(self) -> String {
        format!("art_{}", self.0.simple())
    }
}

impl fmt::Display for ArtifactId {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(&self.public_id())
    }
}

#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub struct ContentDigest([u8; SHA256_BYTES]);

impl ContentDigest {
    #[must_use]
    pub fn of(bytes: &[u8]) -> Self {
        Self(Sha256::digest(bytes).into())
    }

    /// Parses exactly 64 lowercase hexadecimal SHA-256 characters.
    ///
    /// # Errors
    ///
    /// Returns [`ArtifactError::InvalidDigest`] for noncanonical input.
    pub fn parse(value: &str) -> Result<Self, ArtifactError> {
        parse_digest(value).map(Self)
    }

    #[must_use]
    pub const fn as_bytes(&self) -> &[u8; SHA256_BYTES] {
        &self.0
    }

    #[must_use]
    pub fn hex(self) -> String {
        hex::encode(self.0)
    }
}

impl fmt::Display for ContentDigest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(&hex::encode(self.0))
    }
}

#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub struct SubjectDigest([u8; SHA256_BYTES]);

impl SubjectDigest {
    /// Hashes one bounded authenticated subject identifier without retaining the raw value.
    ///
    /// # Errors
    ///
    /// Returns [`ArtifactError::InvalidSubject`] for empty, control-containing or oversized input.
    pub fn from_authenticated_subject(value: &str) -> Result<Self, ArtifactError> {
        if value.is_empty() || value.len() > 512 || value.chars().any(char::is_control) {
            return Err(ArtifactError::InvalidSubject);
        }
        Ok(Self(Sha256::digest(value.as_bytes()).into()))
    }

    /// Parses exactly 64 lowercase hexadecimal SHA-256 characters.
    ///
    /// # Errors
    ///
    /// Returns [`ArtifactError::InvalidDigest`] for noncanonical input.
    pub fn parse(value: &str) -> Result<Self, ArtifactError> {
        parse_digest(value).map(Self)
    }

    #[must_use]
    pub const fn as_bytes(&self) -> &[u8; SHA256_BYTES] {
        &self.0
    }

    #[must_use]
    pub fn hex(self) -> String {
        hex::encode(self.0)
    }
}

#[derive(Clone, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub struct MediaType(String);

impl MediaType {
    /// Parses a bounded lowercase type/subtype media identifier.
    ///
    /// # Errors
    ///
    /// Returns [`ArtifactError::InvalidMediaType`] for malformed or oversized values.
    pub fn parse(value: impl Into<String>) -> Result<Self, ArtifactError> {
        let value = value.into();
        let mut parts = value.split('/');
        let left = parts.next().unwrap_or_default();
        let right = parts.next().unwrap_or_default();
        if value.len() > 127
            || parts.next().is_some()
            || !valid_media_token(left)
            || !valid_media_token(right)
        {
            return Err(ArtifactError::InvalidMediaType);
        }
        Ok(Self(value))
    }

    #[must_use]
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

#[derive(Clone, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub struct FileName(String);

impl FileName {
    /// Normalizes and validates one metadata-only file name without path components.
    ///
    /// # Errors
    ///
    /// Returns [`ArtifactError::InvalidFileName`] for empty, unsafe or oversized values.
    pub fn parse(value: impl Into<String>) -> Result<Self, ArtifactError> {
        let normalized = value.into().nfc().collect::<String>();
        if normalized.is_empty()
            || normalized.len() > 255
            || normalized == "."
            || normalized == ".."
            || normalized.starts_with(char::is_whitespace)
            || normalized.ends_with(char::is_whitespace)
            || normalized
                .chars()
                .any(|character| character.is_control() || matches!(character, '/' | '\\'))
        {
            return Err(ArtifactError::InvalidFileName);
        }
        Ok(Self(normalized))
    }

    #[must_use]
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

#[derive(Clone, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub struct KeyReference(String);

impl KeyReference {
    /// Parses a bounded dotted key-vault reference; raw key material is never accepted here.
    ///
    /// # Errors
    ///
    /// Returns [`ArtifactError::InvalidKeyReference`] for malformed identifiers.
    pub fn parse(value: impl Into<String>) -> Result<Self, ArtifactError> {
        let value = value.into();
        let mut segments = value.split('.');
        let first = segments.next().unwrap_or_default();
        let rest = segments.collect::<Vec<_>>();
        if value.len() > 128
            || rest.is_empty()
            || !valid_key_segment(first, true)
            || rest
                .iter()
                .any(|segment| !valid_key_segment(segment, false))
        {
            return Err(ArtifactError::InvalidKeyReference);
        }
        Ok(Self(value))
    }

    #[must_use]
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

#[derive(Clone, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub struct ScannerReference(String);

impl ScannerReference {
    /// Parses a bounded dotted scanner implementation reference.
    ///
    /// # Errors
    ///
    /// Returns [`ArtifactError::InvalidScannerReference`] for malformed identifiers.
    pub fn parse(value: impl Into<String>) -> Result<Self, ArtifactError> {
        KeyReference::parse(value)
            .map(|reference| Self(reference.0))
            .map_err(|_| ArtifactError::InvalidScannerReference)
    }

    #[must_use]
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

#[derive(Clone, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub struct ScannerSignatureVersion(String);

impl ScannerSignatureVersion {
    /// Parses a bounded scanner engine/signature version without free-form diagnostics.
    ///
    /// # Errors
    ///
    /// Returns [`ArtifactError::InvalidScannerReference`] for malformed version identifiers.
    pub fn parse(value: impl Into<String>) -> Result<Self, ArtifactError> {
        let value = value.into();
        if value.is_empty()
            || value.len() > 128
            || !value
                .bytes()
                .all(|byte| byte.is_ascii_alphanumeric() || b"._-".contains(&byte))
        {
            return Err(ArtifactError::InvalidScannerReference);
        }
        Ok(Self(value))
    }

    #[must_use]
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

#[derive(Clone, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub struct QuarantineReason(String);

impl QuarantineReason {
    /// Parses an allowlisted-shape uppercase machine-readable reason code.
    ///
    /// # Errors
    ///
    /// Returns [`ArtifactError::InvalidQuarantineReason`] for malformed codes.
    pub fn parse(value: impl Into<String>) -> Result<Self, ArtifactError> {
        let value = value.into();
        if !(3..=64).contains(&value.len())
            || !value.as_bytes().first().is_some_and(u8::is_ascii_uppercase)
            || !value
                .bytes()
                .all(|byte| byte.is_ascii_uppercase() || byte.is_ascii_digit() || byte == b'_')
        {
            return Err(ArtifactError::InvalidQuarantineReason);
        }
        Ok(Self(value))
    }

    #[must_use]
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ArtifactKind {
    Source,
    Result,
    /// Canonical complete document IR snapshot, not a HWPX result or semantic diff.
    DocumentIr,
    Preview,
    Evidence,
    Trace,
    Diff,
    Receipt,
}

impl ArtifactKind {
    #[must_use]
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Source => "source",
            Self::Result => "result",
            Self::DocumentIr => "document_ir",
            Self::Preview => "preview",
            Self::Evidence => "evidence",
            Self::Trace => "trace",
            Self::Diff => "diff",
            Self::Receipt => "receipt",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum StorageState {
    Staged,
    Available,
    Quarantined,
    Orphaned,
    Purging,
}

impl StorageState {
    #[must_use]
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Staged => "staged",
            Self::Available => "available",
            Self::Quarantined => "quarantined",
            Self::Orphaned => "orphaned",
            Self::Purging => "purging",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ValidationState {
    Unverified,
    Verified,
    Failed,
    Quarantined,
}

#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub enum AuthScope {
    DocumentRead,
    DocumentWrite,
    SecurityInspect,
    SecurityModify,
    ArtifactShare,
}

#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub enum ArtifactPermission {
    Read,
    Manage,
    QuarantineRead,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RequestContext {
    tenant_id: TenantId,
    subject: SubjectDigest,
    scopes: BTreeSet<AuthScope>,
}

impl RequestContext {
    #[must_use]
    pub fn new(
        tenant_id: TenantId,
        subject: SubjectDigest,
        scopes: impl IntoIterator<Item = AuthScope>,
    ) -> Self {
        Self {
            tenant_id,
            subject,
            scopes: scopes.into_iter().collect(),
        }
    }

    #[must_use]
    pub const fn tenant_id(&self) -> TenantId {
        self.tenant_id
    }

    #[must_use]
    pub const fn subject(&self) -> SubjectDigest {
        self.subject
    }

    #[must_use]
    pub fn has_scope(&self, scope: AuthScope) -> bool {
        self.scopes.contains(&scope)
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct IngestRequest {
    pub bytes: Vec<u8>,
    pub media_type: MediaType,
    pub file_name: FileName,
    pub kind: ArtifactKind,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct ArtifactDescriptor {
    pub artifact_id: ArtifactId,
    pub sha256: ContentDigest,
    pub size_bytes: u64,
    pub media_type: MediaType,
    pub file_name: FileName,
    pub kind: ArtifactKind,
    pub storage_state: StorageState,
    pub validation_state: ValidationState,
    pub quarantine_reason: Option<QuarantineReason>,
    pub scanner_engine: ScannerReference,
    pub scanner_signature_version: ScannerSignatureVersion,
    pub created_at_unix_seconds: u64,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum ScanVerdict {
    Clean,
    Suspicious(QuarantineReason),
    Unverified(QuarantineReason),
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ScanEvidence {
    pub engine: ScannerReference,
    pub signature_version: ScannerSignatureVersion,
    pub verdict: ScanVerdict,
}

#[derive(Clone, Eq, PartialEq)]
pub struct SignedDownloadUrl(String);

impl SignedDownloadUrl {
    pub(crate) fn new(value: String) -> Self {
        Self(value)
    }

    #[must_use]
    pub fn expose(&self) -> &str {
        &self.0
    }
}

impl fmt::Debug for SignedDownloadUrl {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("SignedDownloadUrl([REDACTED])")
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ArtifactAuditOutcome {
    Allowed,
    Denied,
    Quarantined,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct ArtifactAuditEvent {
    pub event: &'static str,
    pub tenant_id: TenantId,
    pub artifact_id: ArtifactId,
    pub subject_sha256: SubjectDigest,
    pub content_sha256: ContentDigest,
    pub outcome: ArtifactAuditOutcome,
    pub recorded_at_unix_seconds: u64,
}

impl Serialize for TenantId {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        serializer.serialize_str(&self.0.hyphenated().to_string())
    }
}

impl<'de> Deserialize<'de> for TenantId {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        let value = String::deserialize(deserializer)?;
        let uuid = Uuid::parse_str(&value).map_err(D::Error::custom)?;
        if uuid.hyphenated().to_string() != value {
            return Err(D::Error::custom(ArtifactError::InvalidTenantId));
        }
        Self::new(uuid).map_err(D::Error::custom)
    }
}

impl Serialize for ArtifactId {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        serializer.serialize_str(&self.public_id())
    }
}

impl<'de> Deserialize<'de> for ArtifactId {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        let value = String::deserialize(deserializer)?;
        Self::parse(&value).map_err(D::Error::custom)
    }
}

macro_rules! impl_digest_serde {
    ($type:ty) => {
        impl Serialize for $type {
            fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
            where
                S: Serializer,
            {
                serializer.serialize_str(&self.hex())
            }
        }

        impl<'de> Deserialize<'de> for $type {
            fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
            where
                D: Deserializer<'de>,
            {
                let value = String::deserialize(deserializer)?;
                Self::parse(&value).map_err(D::Error::custom)
            }
        }
    };
}

impl_digest_serde!(ContentDigest);
impl_digest_serde!(SubjectDigest);

macro_rules! impl_validated_string_serde {
    ($type:ty) => {
        impl Serialize for $type {
            fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
            where
                S: Serializer,
            {
                serializer.serialize_str(self.as_str())
            }
        }

        impl<'de> Deserialize<'de> for $type {
            fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
            where
                D: Deserializer<'de>,
            {
                let value = String::deserialize(deserializer)?;
                Self::parse(value).map_err(D::Error::custom)
            }
        }
    };
}

impl_validated_string_serde!(MediaType);
impl_validated_string_serde!(FileName);
impl_validated_string_serde!(KeyReference);
impl_validated_string_serde!(ScannerReference);
impl_validated_string_serde!(ScannerSignatureVersion);
impl_validated_string_serde!(QuarantineReason);

fn parse_digest(value: &str) -> Result<[u8; SHA256_BYTES], ArtifactError> {
    if value.len() != SHA256_BYTES * 2 || !is_lower_hex(value) {
        return Err(ArtifactError::InvalidDigest);
    }
    let mut bytes = [0_u8; SHA256_BYTES];
    hex::decode_to_slice(value, &mut bytes).map_err(|_| ArtifactError::InvalidDigest)?;
    Ok(bytes)
}

fn is_lower_hex(value: &str) -> bool {
    value
        .bytes()
        .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

fn valid_media_token(value: &str) -> bool {
    !value.is_empty()
        && value.as_bytes().first().is_some_and(u8::is_ascii_lowercase)
        && value.bytes().all(|byte| {
            byte.is_ascii_lowercase() || byte.is_ascii_digit() || b"!#$&^_.+-".contains(&byte)
        })
}

fn valid_key_segment(value: &str, first: bool) -> bool {
    !value.is_empty()
        && (!first || value.as_bytes().first().is_some_and(u8::is_ascii_lowercase))
        && value
            .bytes()
            .all(|byte| byte.is_ascii_lowercase() || byte.is_ascii_digit() || b"_-".contains(&byte))
}

#[cfg(test)]
mod tests {
    use super::{
        ArtifactError, ArtifactId, ContentDigest, FileName, KeyReference, MediaType,
        QuarantineReason, ScannerReference, ScannerSignatureVersion, SubjectDigest, TenantId,
    };
    use uuid::Uuid;

    #[test]
    fn identifiers_and_digests_are_canonical() {
        let tenant =
            TenantId::new(Uuid::new_v4()).unwrap_or_else(|error| panic!("tenant: {error}"));
        assert_eq!(tenant.canonical().len(), 32);
        assert!(matches!(
            TenantId::new(Uuid::nil()),
            Err(ArtifactError::InvalidTenantId)
        ));

        let id = ArtifactId::generate();
        assert_eq!(ArtifactId::parse(&id.public_id()), Ok(id));
        assert!(ArtifactId::parse("art_AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA").is_err());
        assert!(ArtifactId::parse("not-an-artifact").is_err());

        let digest = ContentDigest::of(b"payload");
        assert_eq!(ContentDigest::parse(&digest.hex()), Ok(digest));
        assert!(ContentDigest::parse(&"A".repeat(64)).is_err());

        let subject = SubjectDigest::from_authenticated_subject("oidc:user:42")
            .unwrap_or_else(|error| panic!("subject: {error}"));
        assert_eq!(SubjectDigest::parse(&subject.hex()), Ok(subject));
    }

    #[test]
    fn public_metadata_values_are_bounded() {
        assert!(MediaType::parse("application/vnd.hancom.hwpx+zip").is_ok());
        assert!(MediaType::parse("Application/PDF").is_err());
        assert!(MediaType::parse("application").is_err());

        let normalized =
            FileName::parse("e\u{301}.hwpx").unwrap_or_else(|error| panic!("filename: {error}"));
        assert_eq!(normalized.as_str(), "é.hwpx");
        for invalid in ["", ".", "../escape", "a\\b", " a.hwpx", "a.hwpx "] {
            assert!(FileName::parse(invalid).is_err(), "accepted {invalid:?}");
        }

        assert!(KeyReference::parse("kms.artifact-v1").is_ok());
        assert!(KeyReference::parse("single").is_err());
        assert!(KeyReference::parse("KMS.key").is_err());
        assert!(ScannerReference::parse("scanner.clamav").is_ok());
        assert!(ScannerSignatureVersion::parse("daily-27391.1").is_ok());
        assert!(ScannerSignatureVersion::parse("version with spaces").is_err());

        assert!(QuarantineReason::parse("OLE_SCRIPT_DETECTED").is_ok());
        assert!(QuarantineReason::parse("not_safe").is_err());
    }

    #[test]
    fn json_wire_forms_are_canonical_and_cannot_bypass_validation() {
        let tenant =
            TenantId::new(Uuid::new_v4()).unwrap_or_else(|error| panic!("tenant: {error}"));
        let artifact_id = ArtifactId::generate();
        let digest = ContentDigest::of(b"payload");
        let file_name =
            FileName::parse("fixture.hwpx").unwrap_or_else(|error| panic!("filename: {error}"));

        assert_eq!(
            serde_json::to_string(&tenant).unwrap_or_else(|error| panic!("tenant json: {error}")),
            format!("\"{}\"", tenant.as_uuid().hyphenated())
        );
        assert_eq!(
            serde_json::to_string(&artifact_id)
                .unwrap_or_else(|error| panic!("artifact json: {error}")),
            format!("\"{}\"", artifact_id.public_id())
        );
        assert_eq!(
            serde_json::to_string(&digest).unwrap_or_else(|error| panic!("digest json: {error}")),
            format!("\"{}\"", digest.hex())
        );
        assert_eq!(
            serde_json::to_string(&file_name)
                .unwrap_or_else(|error| panic!("filename json: {error}")),
            "\"fixture.hwpx\""
        );

        assert!(
            serde_json::from_str::<TenantId>("\"00000000-0000-0000-0000-000000000000\"").is_err()
        );
        assert!(serde_json::from_str::<TenantId>(&format!("\"{}\"", tenant.canonical())).is_err());
        assert!(
            serde_json::from_str::<ArtifactId>("\"00000000-0000-0000-0000-000000000001\"").is_err()
        );
        assert!(serde_json::from_str::<ContentDigest>(&format!("\"{}\"", "A".repeat(64))).is_err());
        assert!(serde_json::from_str::<FileName>("\"../escape.hwpx\"").is_err());
        assert!(serde_json::from_str::<MediaType>("\"Application/PDF\"").is_err());
    }
}
