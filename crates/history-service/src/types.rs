use std::collections::BTreeSet;
use std::fmt;

use artifact_service::{ArtifactId, ContentDigest, SubjectDigest, TenantId};
use revision_service::{BranchId, ProjectId, RevisionHead, RevisionId};
use serde::de::Error as _;
use serde::{Deserialize, Deserializer, Serialize, Serializer};
use thiserror::Error;
use unicode_normalization::UnicodeNormalization as _;
use uuid::Uuid;

pub const MAX_HISTORY_PAGE_SIZE: u16 = 100;
pub const MAX_HISTORY_NODES: usize = 10_000;
const MAX_BRANCH_NAME_BYTES: usize = 127;
const MAX_CHECKPOINT_LABEL_CHARS: usize = 120;
const MAX_CHECKPOINT_NOTE_CHARS: usize = 1_000;
const MAX_REVISION_PARENTS: usize = 32;

#[derive(Clone, Debug, Error, Eq, PartialEq)]
pub enum HistoryError {
    #[error("history identifier is invalid")]
    InvalidIdentifier,
    #[error("history request is invalid")]
    InvalidRequest,
    #[error("history cursor is invalid")]
    InvalidCursor,
    #[error("history cursor has expired")]
    CursorExpired,
    #[error("history item was not found")]
    NotFound,
    #[error("history mutation is forbidden")]
    AccessDenied,
    #[error("history graph is invalid")]
    InvalidGraph,
    #[error("history graph exceeds the bounded query limit")]
    GraphLimitExceeded,
    #[error("history identity already exists")]
    DuplicateIdentity,
    #[error("history idempotency key conflicts with its prior request")]
    IdempotencyConflict,
    #[error("history serialization failed")]
    Serialization,
    #[error("history cursor cryptography failed")]
    CryptoFailure,
    #[error("history repository failed")]
    RepositoryFailure,
}

impl HistoryError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidIdentifier => "HISTORY_IDENTIFIER_INVALID",
            Self::InvalidRequest => "HISTORY_REQUEST_INVALID",
            Self::InvalidCursor => "HISTORY_CURSOR_INVALID",
            Self::CursorExpired => "HISTORY_CURSOR_EXPIRED",
            Self::NotFound => "HISTORY_NOT_FOUND",
            Self::AccessDenied => "HISTORY_ACCESS_DENIED",
            Self::InvalidGraph => "HISTORY_GRAPH_INVALID",
            Self::GraphLimitExceeded => "HISTORY_GRAPH_LIMIT_EXCEEDED",
            Self::DuplicateIdentity => "HISTORY_IDENTITY_ALREADY_EXISTS",
            Self::IdempotencyConflict => "HISTORY_IDEMPOTENCY_CONFLICT",
            Self::Serialization => "HISTORY_SERIALIZATION_FAILED",
            Self::CryptoFailure => "HISTORY_CRYPTO_FAILURE",
            Self::RepositoryFailure => "HISTORY_REPOSITORY_FAILED",
        }
    }
}

macro_rules! prefixed_uuid {
    ($name:ident, $prefix:literal) => {
        #[derive(Clone, Copy, Eq, Hash, Ord, PartialEq, PartialOrd)]
        pub struct $name(Uuid);

        impl $name {
            #[must_use]
            pub fn generate() -> Self {
                Self(Uuid::new_v4())
            }

            /// Parses the exact lowercase public identifier form.
            ///
            /// # Errors
            ///
            /// Rejects noncanonical, malformed or nil UUIDs.
            pub fn parse(value: &str) -> Result<Self, HistoryError> {
                let encoded = value
                    .strip_prefix($prefix)
                    .ok_or(HistoryError::InvalidIdentifier)?;
                if encoded.len() != 32
                    || !encoded
                        .bytes()
                        .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
                {
                    return Err(HistoryError::InvalidIdentifier);
                }
                let uuid = Uuid::parse_str(encoded).map_err(|_| HistoryError::InvalidIdentifier)?;
                if uuid.is_nil() {
                    return Err(HistoryError::InvalidIdentifier);
                }
                Ok(Self(uuid))
            }

            #[must_use]
            pub const fn as_uuid(self) -> Uuid {
                self.0
            }

            #[must_use]
            pub fn public_id(self) -> String {
                format!("{}{}", $prefix, self.0.simple())
            }
        }

        impl fmt::Display for $name {
            fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
                formatter.write_str(&self.public_id())
            }
        }

        impl fmt::Debug for $name {
            fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
                formatter.write_str(&self.public_id())
            }
        }

        impl Serialize for $name {
            fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
            where
                S: Serializer,
            {
                serializer.serialize_str(&self.public_id())
            }
        }

        impl<'de> Deserialize<'de> for $name {
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

prefixed_uuid!(CheckpointId, "chk_");
prefixed_uuid!(RequestId, "req_");

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ProjectRole {
    Reader,
    Editor,
    Owner,
}

impl ProjectRole {
    #[must_use]
    pub const fn can_mutate(self) -> bool {
        matches!(self, Self::Editor | Self::Owner)
    }
}

#[derive(Clone, Eq, Hash, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(transparent)]
pub struct BranchName(String);

impl BranchName {
    /// Validates the branch-name contract used by the metadata schema.
    ///
    /// # Errors
    ///
    /// Rejects unsafe path segments, repeated separators and non-ASCII names.
    pub fn parse(value: impl Into<String>) -> Result<Self, HistoryError> {
        let value = value.into();
        let bytes = value.as_bytes();
        let valid_shape = !bytes.is_empty()
            && bytes.len() <= MAX_BRANCH_NAME_BYTES
            && bytes[0].is_ascii_alphanumeric()
            && bytes.iter().all(|byte| {
                byte.is_ascii_alphanumeric() || matches!(byte, b'.' | b'_' | b'/' | b'-')
            });
        if !valid_shape
            || value.contains("//")
            || value
                .split('/')
                .any(|segment| matches!(segment, "." | ".."))
        {
            return Err(HistoryError::InvalidRequest);
        }
        Ok(Self(value))
    }

    #[must_use]
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl fmt::Debug for BranchName {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(&self.0)
    }
}

impl<'de> Deserialize<'de> for BranchName {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        Self::parse(String::deserialize(deserializer)?).map_err(D::Error::custom)
    }
}

#[derive(Clone, Eq, Hash, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(transparent)]
pub struct CheckpointLabel(String);

impl CheckpointLabel {
    /// NFC-normalizes and validates a human-readable immutable label.
    ///
    /// # Errors
    ///
    /// Rejects empty, untrimmed, control-containing or oversized labels.
    pub fn parse(value: impl Into<String>) -> Result<Self, HistoryError> {
        let value = value.into().nfc().collect::<String>();
        let char_count = value.chars().count();
        if !(1..=MAX_CHECKPOINT_LABEL_CHARS).contains(&char_count)
            || value.trim() != value
            || value.chars().any(char::is_control)
        {
            return Err(HistoryError::InvalidRequest);
        }
        Ok(Self(value))
    }

    #[must_use]
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl fmt::Debug for CheckpointLabel {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(&self.0)
    }
}

impl<'de> Deserialize<'de> for CheckpointLabel {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        Self::parse(String::deserialize(deserializer)?).map_err(D::Error::custom)
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(transparent)]
pub struct CheckpointNote(String);

impl CheckpointNote {
    /// Validates an optional immutable P15 checkpoint note without changing its text.
    ///
    /// # Errors
    ///
    /// Rejects an empty or oversized note.
    pub fn parse(value: impl Into<String>) -> Result<Self, HistoryError> {
        let value = value.into();
        if !(1..=MAX_CHECKPOINT_NOTE_CHARS).contains(&value.chars().count()) {
            return Err(HistoryError::InvalidRequest);
        }
        Ok(Self(value))
    }

    #[must_use]
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl fmt::Debug for CheckpointNote {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("<redacted>")
    }
}

impl<'de> Deserialize<'de> for CheckpointNote {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        Self::parse(String::deserialize(deserializer)?).map_err(D::Error::custom)
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct HistoryRequestContext {
    tenant_id: TenantId,
    subject: SubjectDigest,
    now_unix_seconds: u64,
}

impl HistoryRequestContext {
    #[must_use]
    pub const fn new(tenant_id: TenantId, subject: SubjectDigest, now_unix_seconds: u64) -> Self {
        Self {
            tenant_id,
            subject,
            now_unix_seconds,
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
    pub const fn now_unix_seconds(&self) -> u64 {
        self.now_unix_seconds
    }
}

impl fmt::Debug for HistoryRequestContext {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("HistoryRequestContext")
            .field("tenant_id", &self.tenant_id)
            .field("subject", &"<redacted>")
            .field("now_unix_seconds", &self.now_unix_seconds)
            .finish()
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct CommittedRevisionProjection {
    project_id: ProjectId,
    revision_id: RevisionId,
    parents: Vec<RevisionId>,
    result_artifact_id: ArtifactId,
    semantic_diff_artifact_id: Option<ArtifactId>,
    committed_generation: u64,
}

impl CommittedRevisionProjection {
    /// Creates a bounded projection of one already sealed `service_v1` revision.
    ///
    /// # Errors
    ///
    /// Rejects zero generation, duplicate/self parents and reused artifact identities.
    pub fn new(
        project_id: ProjectId,
        revision_id: RevisionId,
        parents: Vec<RevisionId>,
        result_artifact_id: ArtifactId,
        semantic_diff_artifact_id: Option<ArtifactId>,
        committed_generation: u64,
    ) -> Result<Self, HistoryError> {
        if committed_generation == 0
            || parents.len() > MAX_REVISION_PARENTS
            || parents.contains(&revision_id)
            || parents.iter().copied().collect::<BTreeSet<_>>().len() != parents.len()
            || semantic_diff_artifact_id == Some(result_artifact_id)
        {
            return Err(HistoryError::InvalidRequest);
        }
        Ok(Self {
            project_id,
            revision_id,
            parents,
            result_artifact_id,
            semantic_diff_artifact_id,
            committed_generation,
        })
    }

    #[must_use]
    pub const fn project_id(&self) -> ProjectId {
        self.project_id
    }

    #[must_use]
    pub const fn revision_id(&self) -> RevisionId {
        self.revision_id
    }

    #[must_use]
    pub fn parents(&self) -> &[RevisionId] {
        &self.parents
    }

    #[must_use]
    pub const fn result_artifact_id(&self) -> ArtifactId {
        self.result_artifact_id
    }

    #[must_use]
    pub const fn semantic_diff_artifact_id(&self) -> Option<ArtifactId> {
        self.semantic_diff_artifact_id
    }

    #[must_use]
    pub const fn committed_generation(&self) -> u64 {
        self.committed_generation
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct BranchRecord {
    project_id: ProjectId,
    branch_id: BranchId,
    name: BranchName,
    head: RevisionHead,
    is_default: bool,
}

impl BranchRecord {
    pub(crate) const fn new(
        project_id: ProjectId,
        branch_id: BranchId,
        name: BranchName,
        head: RevisionHead,
        is_default: bool,
    ) -> Self {
        Self {
            project_id,
            branch_id,
            name,
            head,
            is_default,
        }
    }

    #[must_use]
    pub const fn project_id(&self) -> ProjectId {
        self.project_id
    }

    #[must_use]
    pub const fn branch_id(&self) -> BranchId {
        self.branch_id
    }

    #[must_use]
    pub fn name(&self) -> &BranchName {
        &self.name
    }

    #[must_use]
    pub const fn head(&self) -> RevisionHead {
        self.head
    }

    #[must_use]
    pub const fn is_default(&self) -> bool {
        self.is_default
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CheckpointRecord {
    project_id: ProjectId,
    checkpoint_id: CheckpointId,
    revision_id: RevisionId,
    label: CheckpointLabel,
    #[serde(skip_serializing_if = "Option::is_none")]
    note: Option<CheckpointNote>,
    request_id: RequestId,
    request_sha256: ContentDigest,
}

impl CheckpointRecord {
    pub(crate) const fn new(
        project_id: ProjectId,
        checkpoint_id: CheckpointId,
        revision_id: RevisionId,
        label: CheckpointLabel,
        note: Option<CheckpointNote>,
        request_id: RequestId,
        request_sha256: ContentDigest,
    ) -> Self {
        Self {
            project_id,
            checkpoint_id,
            revision_id,
            label,
            note,
            request_id,
            request_sha256,
        }
    }

    #[must_use]
    pub const fn project_id(&self) -> ProjectId {
        self.project_id
    }

    #[must_use]
    pub const fn checkpoint_id(&self) -> CheckpointId {
        self.checkpoint_id
    }

    #[must_use]
    pub const fn revision_id(&self) -> RevisionId {
        self.revision_id
    }

    #[must_use]
    pub fn label(&self) -> &CheckpointLabel {
        &self.label
    }

    #[must_use]
    pub const fn note(&self) -> Option<&CheckpointNote> {
        self.note.as_ref()
    }

    #[must_use]
    pub const fn request_sha256(&self) -> ContentDigest {
        self.request_sha256
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum CheckpointOutcome {
    Created(CheckpointRecord),
    Replayed(CheckpointRecord),
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CheckpointRequest {
    request_id: RequestId,
    project_id: ProjectId,
    checkpoint_id: CheckpointId,
    revision_id: RevisionId,
    label: CheckpointLabel,
    #[serde(skip_serializing_if = "Option::is_none")]
    note: Option<CheckpointNote>,
}

impl CheckpointRequest {
    #[must_use]
    pub const fn new(
        request_id: RequestId,
        project_id: ProjectId,
        checkpoint_id: CheckpointId,
        revision_id: RevisionId,
        label: CheckpointLabel,
    ) -> Self {
        Self::new_with_note(
            request_id,
            project_id,
            checkpoint_id,
            revision_id,
            label,
            None,
        )
    }

    #[must_use]
    pub const fn new_with_note(
        request_id: RequestId,
        project_id: ProjectId,
        checkpoint_id: CheckpointId,
        revision_id: RevisionId,
        label: CheckpointLabel,
        note: Option<CheckpointNote>,
    ) -> Self {
        Self {
            request_id,
            project_id,
            checkpoint_id,
            revision_id,
            label,
            note,
        }
    }

    #[must_use]
    pub const fn request_id(&self) -> RequestId {
        self.request_id
    }

    #[must_use]
    pub const fn project_id(&self) -> ProjectId {
        self.project_id
    }

    #[must_use]
    pub const fn checkpoint_id(&self) -> CheckpointId {
        self.checkpoint_id
    }

    #[must_use]
    pub const fn revision_id(&self) -> RevisionId {
        self.revision_id
    }

    #[must_use]
    pub fn label(&self) -> &CheckpointLabel {
        &self.label
    }

    #[must_use]
    pub const fn note(&self) -> Option<&CheckpointNote> {
        self.note.as_ref()
    }

    /// Returns the digest used to bind this exact immutable checkpoint request.
    ///
    /// # Errors
    ///
    /// Returns [`HistoryError::Serialization`] if the closed request shape cannot be encoded.
    pub fn canonical_sha256(&self) -> Result<ContentDigest, HistoryError> {
        serde_json::to_vec(self)
            .map(|bytes| ContentDigest::of(&bytes))
            .map_err(|_| HistoryError::Serialization)
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct BranchCreateRequest {
    project_id: ProjectId,
    branch_id: BranchId,
    name: BranchName,
    from_revision_id: RevisionId,
}

impl BranchCreateRequest {
    #[must_use]
    pub const fn new(
        project_id: ProjectId,
        branch_id: BranchId,
        name: BranchName,
        from_revision_id: RevisionId,
    ) -> Self {
        Self {
            project_id,
            branch_id,
            name,
            from_revision_id,
        }
    }

    #[must_use]
    pub const fn project_id(&self) -> ProjectId {
        self.project_id
    }

    #[must_use]
    pub const fn branch_id(&self) -> BranchId {
        self.branch_id
    }

    #[must_use]
    pub fn name(&self) -> &BranchName {
        &self.name
    }

    #[must_use]
    pub const fn from_revision_id(&self) -> RevisionId {
        self.from_revision_id
    }
}

#[derive(Clone, Eq, PartialEq)]
pub enum HistoryQuery {
    First {
        project_id: ProjectId,
        branch_id: BranchId,
        page_size: u16,
    },
    Continue {
        cursor: String,
    },
}

impl fmt::Debug for HistoryQuery {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::First {
                project_id,
                branch_id,
                page_size,
            } => formatter
                .debug_struct("HistoryQuery::First")
                .field("project_id", project_id)
                .field("branch_id", branch_id)
                .field("page_size", page_size)
                .finish(),
            Self::Continue { .. } => formatter
                .debug_struct("HistoryQuery::Continue")
                .field("cursor", &"<redacted>")
                .finish(),
        }
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct HistoryEntry {
    revision_id: RevisionId,
    parents: Vec<RevisionId>,
    result_artifact_id: ArtifactId,
    committed_generation: u64,
    checkpoint_labels: Vec<CheckpointLabel>,
    semantic_diff_cursor: Option<String>,
}

impl fmt::Debug for HistoryEntry {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("HistoryEntry")
            .field("revision_id", &self.revision_id)
            .field("parents", &self.parents)
            .field("result_artifact_id", &self.result_artifact_id)
            .field("committed_generation", &self.committed_generation)
            .field("checkpoint_labels", &self.checkpoint_labels)
            .field(
                "semantic_diff_cursor",
                &self.semantic_diff_cursor.as_ref().map(|_| "<redacted>"),
            )
            .finish()
    }
}

impl HistoryEntry {
    pub(crate) fn new(
        revision: &CommittedRevisionProjection,
        checkpoint_labels: Vec<CheckpointLabel>,
        semantic_diff_cursor: Option<String>,
    ) -> Self {
        Self {
            revision_id: revision.revision_id,
            parents: revision.parents.clone(),
            result_artifact_id: revision.result_artifact_id,
            committed_generation: revision.committed_generation,
            checkpoint_labels,
            semantic_diff_cursor,
        }
    }

    #[must_use]
    pub const fn revision_id(&self) -> RevisionId {
        self.revision_id
    }

    #[must_use]
    pub fn parents(&self) -> &[RevisionId] {
        &self.parents
    }

    #[must_use]
    pub fn checkpoint_labels(&self) -> &[CheckpointLabel] {
        &self.checkpoint_labels
    }

    #[must_use]
    pub fn semantic_diff_cursor(&self) -> Option<&str> {
        self.semantic_diff_cursor.as_deref()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct HistoryPage {
    project_id: ProjectId,
    branch_id: BranchId,
    snapshot_head: RevisionHead,
    entries: Vec<HistoryEntry>,
    next_cursor: Option<String>,
}

impl fmt::Debug for HistoryPage {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("HistoryPage")
            .field("project_id", &self.project_id)
            .field("branch_id", &self.branch_id)
            .field("snapshot_head", &self.snapshot_head)
            .field("entries", &self.entries)
            .field(
                "next_cursor",
                &self.next_cursor.as_ref().map(|_| "<redacted>"),
            )
            .finish()
    }
}

impl HistoryPage {
    pub(crate) const fn new(
        project_id: ProjectId,
        branch_id: BranchId,
        snapshot_head: RevisionHead,
        entries: Vec<HistoryEntry>,
        next_cursor: Option<String>,
    ) -> Self {
        Self {
            project_id,
            branch_id,
            snapshot_head,
            entries,
            next_cursor,
        }
    }

    #[must_use]
    pub const fn snapshot_head(&self) -> RevisionHead {
        self.snapshot_head
    }

    #[must_use]
    pub fn entries(&self) -> &[HistoryEntry] {
        &self.entries
    }

    #[must_use]
    pub fn next_cursor(&self) -> Option<&str> {
        self.next_cursor.as_deref()
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
#[allow(clippy::struct_field_names)]
pub struct SemanticDiffReference {
    project_id: ProjectId,
    revision_id: RevisionId,
    artifact_id: ArtifactId,
}

impl SemanticDiffReference {
    pub(crate) const fn new(
        project_id: ProjectId,
        revision_id: RevisionId,
        artifact_id: ArtifactId,
    ) -> Self {
        Self {
            project_id,
            revision_id,
            artifact_id,
        }
    }

    #[must_use]
    pub const fn revision_id(&self) -> RevisionId {
        self.revision_id
    }

    #[must_use]
    pub const fn artifact_id(&self) -> ArtifactId {
        self.artifact_id
    }
}

#[derive(Clone, Debug)]
#[doc(hidden)]
pub struct HistorySnapshot {
    pub(crate) branch: BranchRecord,
    pub(crate) revisions: Vec<CommittedRevisionProjection>,
    pub(crate) checkpoints: Vec<CheckpointRecord>,
}

impl HistorySnapshot {
    #[doc(hidden)]
    #[must_use]
    pub const fn new(
        branch: BranchRecord,
        revisions: Vec<CommittedRevisionProjection>,
        checkpoints: Vec<CheckpointRecord>,
    ) -> Self {
        Self {
            branch,
            revisions,
            checkpoints,
        }
    }
}
