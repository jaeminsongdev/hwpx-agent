use std::collections::BTreeSet;
use std::fmt;

use artifact_service::{ArtifactId, ContentDigest, SubjectDigest, TenantId};
use serde::de::Error as _;
use serde::{Deserialize, Deserializer, Serialize, Serializer};
use thiserror::Error;
use uuid::Uuid;

pub const REVISION_COMMIT_RECEIPT_SCHEMA_VERSION: &str = "hwpx-agent.revision-commit-receipt/v1";
const MAX_PARENTS: usize = 32;

#[derive(Debug, Error, Clone, Eq, PartialEq)]
pub enum RevisionError {
    #[error("revision service identifier is invalid")]
    InvalidIdentifier,
    #[error("revision commit request is invalid")]
    InvalidRequest,
    #[error("revision head is invalid")]
    InvalidHead,
    #[error("revision stream was not found")]
    NotFound,
    #[error("revision stream already exists")]
    DuplicateStream,
    #[error("revision already exists")]
    DuplicateRevision,
    #[error("revision commit already exists")]
    DuplicateCommit,
    #[error("revision parent is absent or not sealed")]
    ParentUnavailable,
    #[error("revision graph would contain a cycle")]
    GraphCycle,
    #[error("revision serialization failed")]
    Serialization,
    #[error("revision repository failed")]
    RepositoryFailure,
}

impl RevisionError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidIdentifier => "REVISION_IDENTIFIER_INVALID",
            Self::InvalidRequest => "REVISION_REQUEST_INVALID",
            Self::InvalidHead => "REVISION_HEAD_INVALID",
            Self::NotFound => "REVISION_STREAM_NOT_FOUND",
            Self::DuplicateStream => "REVISION_STREAM_ALREADY_EXISTS",
            Self::DuplicateRevision => "REVISION_ALREADY_EXISTS",
            Self::DuplicateCommit => "REVISION_COMMIT_ALREADY_EXISTS",
            Self::ParentUnavailable => "REVISION_PARENT_UNAVAILABLE",
            Self::GraphCycle => "REVISION_GRAPH_CYCLE",
            Self::Serialization => "REVISION_SERIALIZATION_FAILED",
            Self::RepositoryFailure => "REVISION_REPOSITORY_FAILED",
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
            /// Returns [`RevisionError::InvalidIdentifier`] for a noncanonical or nil UUID.
            pub fn parse(value: &str) -> Result<Self, RevisionError> {
                let encoded = value
                    .strip_prefix($prefix)
                    .ok_or(RevisionError::InvalidIdentifier)?;
                if encoded.len() != 32
                    || !encoded
                        .as_bytes()
                        .iter()
                        .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(byte))
                {
                    return Err(RevisionError::InvalidIdentifier);
                }
                let value =
                    Uuid::parse_str(encoded).map_err(|_| RevisionError::InvalidIdentifier)?;
                if value.is_nil() {
                    return Err(RevisionError::InvalidIdentifier);
                }
                Ok(Self(value))
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

prefixed_uuid!(ProjectId, "prj_");
prefixed_uuid!(BranchId, "brn_");
prefixed_uuid!(RevisionId, "rev_");
prefixed_uuid!(CommitId, "cmt_");

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum RevisionValidationState {
    Verified,
    Partial,
    Failed,
    Unverified,
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RevisionRequestContext {
    tenant_id: TenantId,
    subject: SubjectDigest,
}

impl RevisionRequestContext {
    #[must_use]
    pub const fn new(tenant_id: TenantId, subject: SubjectDigest) -> Self {
        Self { tenant_id, subject }
    }

    #[must_use]
    pub const fn tenant_id(&self) -> TenantId {
        self.tenant_id
    }

    #[must_use]
    pub const fn subject(&self) -> SubjectDigest {
        self.subject
    }
}

impl fmt::Debug for RevisionRequestContext {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("RevisionRequestContext")
            .field("tenant_id", &self.tenant_id)
            .field("subject", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct RevisionHead {
    revision_id: Option<RevisionId>,
    generation: u64,
}

impl<'de> Deserialize<'de> for RevisionHead {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        #[derive(Deserialize)]
        #[serde(deny_unknown_fields)]
        struct WireHead {
            revision_id: Option<RevisionId>,
            generation: u64,
        }

        let value = WireHead::deserialize(deserializer)?;
        Self::new(value.revision_id, value.generation).map_err(D::Error::custom)
    }
}

impl RevisionHead {
    /// Creates an internally consistent stream head.
    ///
    /// # Errors
    ///
    /// Rejects a zero generation with a revision or a nonzero generation without one.
    pub fn new(revision_id: Option<RevisionId>, generation: u64) -> Result<Self, RevisionError> {
        if revision_id.is_some() != (generation > 0) {
            return Err(RevisionError::InvalidHead);
        }
        Ok(Self {
            revision_id,
            generation,
        })
    }

    #[must_use]
    pub const fn empty() -> Self {
        Self {
            revision_id: None,
            generation: 0,
        }
    }

    #[must_use]
    pub const fn revision_id(self) -> Option<RevisionId> {
        self.revision_id
    }

    #[must_use]
    pub const fn generation(self) -> u64 {
        self.generation
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct RevisionCommitRequest {
    commit_id: CommitId,
    project_id: ProjectId,
    branch_id: BranchId,
    expected_head: RevisionHead,
    new_revision_id: RevisionId,
    parents: Vec<RevisionId>,
    source_artifact_id: ArtifactId,
    result_artifact_id: ArtifactId,
    semantic_diff_artifact_id: Option<ArtifactId>,
    operation_plan_sha256: ContentDigest,
    validation_state: RevisionValidationState,
    validation_summary_sha256: ContentDigest,
    transaction_receipt_sha256: ContentDigest,
}

impl<'de> Deserialize<'de> for RevisionCommitRequest {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        #[derive(Deserialize)]
        #[serde(deny_unknown_fields)]
        struct WireRequest {
            commit_id: CommitId,
            project_id: ProjectId,
            branch_id: BranchId,
            expected_head: RevisionHead,
            new_revision_id: RevisionId,
            parents: Vec<RevisionId>,
            source_artifact_id: ArtifactId,
            result_artifact_id: ArtifactId,
            semantic_diff_artifact_id: Option<ArtifactId>,
            operation_plan_sha256: ContentDigest,
            validation_state: RevisionValidationState,
            validation_summary_sha256: ContentDigest,
            transaction_receipt_sha256: ContentDigest,
        }

        let value = WireRequest::deserialize(deserializer)?;
        Self::new(
            value.commit_id,
            value.project_id,
            value.branch_id,
            value.expected_head,
            value.new_revision_id,
            value.parents,
            value.source_artifact_id,
            value.result_artifact_id,
            value.semantic_diff_artifact_id,
            value.operation_plan_sha256,
            value.validation_state,
            value.validation_summary_sha256,
            value.transaction_receipt_sha256,
        )
        .map_err(D::Error::custom)
    }
}

impl RevisionCommitRequest {
    /// Creates one bounded immutable-node CAS request.
    ///
    /// # Errors
    ///
    /// Rejects unverified output, malformed root/parent topology, duplicate parents or overflow.
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        commit_id: CommitId,
        project_id: ProjectId,
        branch_id: BranchId,
        expected_head: RevisionHead,
        new_revision_id: RevisionId,
        parents: Vec<RevisionId>,
        source_artifact_id: ArtifactId,
        result_artifact_id: ArtifactId,
        semantic_diff_artifact_id: Option<ArtifactId>,
        operation_plan_sha256: ContentDigest,
        validation_state: RevisionValidationState,
        validation_summary_sha256: ContentDigest,
        transaction_receipt_sha256: ContentDigest,
    ) -> Result<Self, RevisionError> {
        if validation_state != RevisionValidationState::Verified
            || parents.len() > MAX_PARENTS
            || parents.contains(&new_revision_id)
            || parents.iter().copied().collect::<BTreeSet<_>>().len() != parents.len()
            || source_artifact_id == result_artifact_id
            || semantic_diff_artifact_id.is_some_and(|artifact| {
                artifact == source_artifact_id || artifact == result_artifact_id
            })
        {
            return Err(RevisionError::InvalidRequest);
        }
        match expected_head.revision_id() {
            None if !parents.is_empty() || expected_head.generation() != 0 => {
                return Err(RevisionError::InvalidRequest);
            }
            Some(expected)
                if parents.first() != Some(&expected) || expected_head.generation() == 0 =>
            {
                return Err(RevisionError::InvalidRequest);
            }
            _ => {}
        }
        Ok(Self {
            commit_id,
            project_id,
            branch_id,
            expected_head,
            new_revision_id,
            parents,
            source_artifact_id,
            result_artifact_id,
            semantic_diff_artifact_id,
            operation_plan_sha256,
            validation_state,
            validation_summary_sha256,
            transaction_receipt_sha256,
        })
    }

    #[must_use]
    pub const fn commit_id(&self) -> CommitId {
        self.commit_id
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
    pub const fn expected_head(&self) -> RevisionHead {
        self.expected_head
    }

    #[must_use]
    pub const fn new_revision_id(&self) -> RevisionId {
        self.new_revision_id
    }

    #[must_use]
    pub fn parents(&self) -> &[RevisionId] {
        &self.parents
    }

    #[must_use]
    pub const fn source_artifact_id(&self) -> ArtifactId {
        self.source_artifact_id
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
    pub const fn operation_plan_sha256(&self) -> ContentDigest {
        self.operation_plan_sha256
    }

    #[must_use]
    pub const fn validation_summary_sha256(&self) -> ContentDigest {
        self.validation_summary_sha256
    }

    #[must_use]
    pub const fn transaction_receipt_sha256(&self) -> ContentDigest {
        self.transaction_receipt_sha256
    }

    /// Hashes the exact canonical request that participates in CAS.
    ///
    /// # Errors
    ///
    /// Returns a stable serialization failure.
    pub fn canonical_sha256(&self) -> Result<ContentDigest, RevisionError> {
        let bytes = serde_json::to_vec(self).map_err(|_| RevisionError::Serialization)?;
        Ok(ContentDigest::of(&bytes))
    }
}

impl fmt::Debug for RevisionCommitRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("RevisionCommitRequest")
            .field("project_id", &self.project_id)
            .field("branch_id", &self.branch_id)
            .field("expected_generation", &self.expected_head.generation)
            .field("parent_count", &self.parents.len())
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct RevisionNode {
    project_id: ProjectId,
    revision_id: RevisionId,
    parents: Vec<RevisionId>,
    source_artifact_id: ArtifactId,
    result_artifact_id: ArtifactId,
    semantic_diff_artifact_id: Option<ArtifactId>,
    operation_plan_sha256: ContentDigest,
    validation_summary_sha256: ContentDigest,
    transaction_receipt_sha256: ContentDigest,
    committed_generation: u64,
    commit_request_sha256: ContentDigest,
    commit_id: CommitId,
    created_by_subject_sha256: SubjectDigest,
    sealed: bool,
}

impl RevisionNode {
    #[allow(clippy::too_many_arguments)]
    pub(crate) fn sealed_from(
        request: &RevisionCommitRequest,
        generation: u64,
        request_sha256: ContentDigest,
        subject: SubjectDigest,
    ) -> Self {
        Self {
            project_id: request.project_id,
            revision_id: request.new_revision_id,
            parents: request.parents.clone(),
            source_artifact_id: request.source_artifact_id,
            result_artifact_id: request.result_artifact_id,
            semantic_diff_artifact_id: request.semantic_diff_artifact_id,
            operation_plan_sha256: request.operation_plan_sha256,
            validation_summary_sha256: request.validation_summary_sha256,
            transaction_receipt_sha256: request.transaction_receipt_sha256,
            committed_generation: generation,
            commit_request_sha256: request_sha256,
            commit_id: request.commit_id,
            created_by_subject_sha256: subject,
            sealed: true,
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
    pub const fn committed_generation(&self) -> u64 {
        self.committed_generation
    }

    #[must_use]
    pub const fn sealed(&self) -> bool {
        self.sealed
    }
}

impl fmt::Debug for RevisionNode {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("RevisionNode")
            .field("project_id", &self.project_id)
            .field("revision_id", &self.revision_id)
            .field("parent_count", &self.parents.len())
            .field("committed_generation", &self.committed_generation)
            .field("sealed", &self.sealed)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct RevisionReceipt {
    schema_version: String,
    commit_id: CommitId,
    project_id: ProjectId,
    branch_id: BranchId,
    previous_head: RevisionHead,
    committed_head: RevisionHead,
    request_sha256: ContentDigest,
    transaction_receipt_sha256: ContentDigest,
    subject_sha256: SubjectDigest,
    receipt_sha256: ContentDigest,
}

#[derive(Serialize)]
struct RevisionReceiptBody {
    schema_version: &'static str,
    commit_id: CommitId,
    project_id: ProjectId,
    branch_id: BranchId,
    previous_head: RevisionHead,
    committed_head: RevisionHead,
    request_sha256: ContentDigest,
    transaction_receipt_sha256: ContentDigest,
    subject_sha256: SubjectDigest,
}

impl RevisionReceipt {
    pub(crate) fn from_commit(
        request: &RevisionCommitRequest,
        previous_head: RevisionHead,
        committed_head: RevisionHead,
        request_sha256: ContentDigest,
        subject_sha256: SubjectDigest,
    ) -> Result<Self, RevisionError> {
        let body = RevisionReceiptBody {
            schema_version: REVISION_COMMIT_RECEIPT_SCHEMA_VERSION,
            commit_id: request.commit_id,
            project_id: request.project_id,
            branch_id: request.branch_id,
            previous_head,
            committed_head,
            request_sha256,
            transaction_receipt_sha256: request.transaction_receipt_sha256,
            subject_sha256,
        };
        let bytes = serde_json::to_vec(&body).map_err(|_| RevisionError::Serialization)?;
        Ok(Self {
            schema_version: REVISION_COMMIT_RECEIPT_SCHEMA_VERSION.to_owned(),
            commit_id: body.commit_id,
            project_id: body.project_id,
            branch_id: body.branch_id,
            previous_head: body.previous_head,
            committed_head: body.committed_head,
            request_sha256: body.request_sha256,
            transaction_receipt_sha256: body.transaction_receipt_sha256,
            subject_sha256: body.subject_sha256,
            receipt_sha256: ContentDigest::of(&bytes),
        })
    }

    #[must_use]
    pub const fn committed_head(&self) -> RevisionHead {
        self.committed_head
    }

    #[must_use]
    pub const fn request_sha256(&self) -> ContentDigest {
        self.request_sha256
    }

    #[must_use]
    pub const fn receipt_sha256(&self) -> ContentDigest {
        self.receipt_sha256
    }
}

impl fmt::Debug for RevisionReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("RevisionReceipt")
            .field("schema_version", &self.schema_version)
            .field("committed_generation", &self.committed_head.generation)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct RevisionConflict {
    project_id: ProjectId,
    branch_id: BranchId,
    expected_head: RevisionHead,
    observed_head: RevisionHead,
    request_sha256: ContentDigest,
}

impl RevisionConflict {
    pub(crate) fn new(
        request: &RevisionCommitRequest,
        observed_head: RevisionHead,
        request_sha256: ContentDigest,
    ) -> Self {
        Self {
            project_id: request.project_id,
            branch_id: request.branch_id,
            expected_head: request.expected_head,
            observed_head,
            request_sha256,
        }
    }

    #[must_use]
    pub const fn observed_head(&self) -> RevisionHead {
        self.observed_head
    }
}

impl fmt::Debug for RevisionConflict {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("RevisionConflict")
            .field("project_id", &self.project_id)
            .field("branch_id", &self.branch_id)
            .field("expected_generation", &self.expected_head.generation)
            .field("observed_generation", &self.observed_head.generation)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum CommitOutcome {
    Committed(RevisionReceipt),
    Conflict(RevisionConflict),
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn identifiers_are_exact_and_nil_is_rejected() {
        let project = ProjectId::parse("prj_10000000000000000000000000000001")
            .unwrap_or_else(|error| panic!("project: {error}"));
        assert_eq!(project.public_id(), "prj_10000000000000000000000000000001");
        assert!(ProjectId::parse("PRJ_10000000000000000000000000000001").is_err());
        assert!(ProjectId::parse("prj_00000000000000000000000000000000").is_err());
    }

    #[test]
    fn head_shape_is_closed() {
        let revision = RevisionId::parse("rev_10000000000000000000000000000001")
            .unwrap_or_else(|error| panic!("revision: {error}"));
        assert!(RevisionHead::new(None, 1).is_err());
        assert!(RevisionHead::new(Some(revision), 0).is_err());
        assert_eq!(RevisionHead::empty().generation(), 0);
    }
}
