use std::fmt;

use artifact_service::{ArtifactId, ContentDigest, SubjectDigest, TenantId};
use revision_service::{ProjectId, RevisionId};
use serde::de::Error as _;
use serde::{Deserialize, Deserializer, Serialize, Serializer};
use thiserror::Error;
use uuid::Uuid;

const MAX_LEASE_SECONDS: u64 = 3_600;

#[derive(Clone, Debug, Error, Eq, PartialEq)]
pub enum JobError {
    #[error("job identifier is invalid")]
    InvalidIdentifier,
    #[error("job request is invalid")]
    InvalidRequest,
    #[error("job was not found")]
    NotFound,
    #[error("job action is forbidden")]
    AccessDenied,
    #[error("job identity already exists")]
    DuplicateIdentity,
    #[error("job transition is invalid")]
    InvalidTransition,
    #[error("job lease binding is stale or mismatched")]
    LeaseMismatch,
    #[error("job artifact is not qualified")]
    ArtifactNotQualified,
    #[error("job revision is not qualified")]
    RevisionNotQualified,
    #[error("job repository failed")]
    RepositoryFailure,
}

impl JobError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidIdentifier => "JOB_IDENTIFIER_INVALID",
            Self::InvalidRequest => "JOB_REQUEST_INVALID",
            Self::NotFound => "JOB_NOT_FOUND",
            Self::AccessDenied => "JOB_ACCESS_DENIED",
            Self::DuplicateIdentity => "JOB_IDENTITY_ALREADY_EXISTS",
            Self::InvalidTransition => "JOB_TRANSITION_INVALID",
            Self::LeaseMismatch => "JOB_LEASE_MISMATCH",
            Self::ArtifactNotQualified => "JOB_ARTIFACT_NOT_QUALIFIED",
            Self::RevisionNotQualified => "JOB_REVISION_NOT_QUALIFIED",
            Self::RepositoryFailure => "JOB_REPOSITORY_FAILED",
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

            /// Parses one exact lowercase public identifier.
            ///
            /// # Errors
            ///
            /// Rejects malformed, noncanonical or nil UUIDs.
            pub fn parse(value: &str) -> Result<Self, JobError> {
                let encoded = value
                    .strip_prefix($prefix)
                    .ok_or(JobError::InvalidIdentifier)?;
                if encoded.len() != 32
                    || !encoded
                        .bytes()
                        .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
                {
                    return Err(JobError::InvalidIdentifier);
                }
                let uuid = Uuid::parse_str(encoded).map_err(|_| JobError::InvalidIdentifier)?;
                if uuid.is_nil() {
                    return Err(JobError::InvalidIdentifier);
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

prefixed_uuid!(JobId, "job_");
prefixed_uuid!(RequestId, "req_");
prefixed_uuid!(AgentInstanceId, "agt_");
prefixed_uuid!(ExecutionId, "exe_");

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
pub struct TargetProfileId(String);

impl TargetProfileId {
    /// Parses the exact database-compatible target profile form.
    ///
    /// # Errors
    ///
    /// Rejects values outside the 2-127 byte ASCII contract.
    pub fn parse(value: impl Into<String>) -> Result<Self, JobError> {
        let value = value.into();
        let bytes = value.as_bytes();
        if !(2..=127).contains(&bytes.len())
            || !bytes[0].is_ascii_alphanumeric()
            || !bytes[1..]
                .iter()
                .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'.' | b'_' | b'-'))
        {
            return Err(JobError::InvalidRequest);
        }
        Ok(Self(value))
    }

    #[must_use]
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl fmt::Debug for TargetProfileId {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(&self.0)
    }
}

impl<'de> Deserialize<'de> for TargetProfileId {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        Self::parse(String::deserialize(deserializer)?).map_err(D::Error::custom)
    }
}

#[derive(Clone, Eq, Hash, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(transparent)]
pub struct TerminalErrorCode(String);

impl TerminalErrorCode {
    /// Parses one stable public error code.
    ///
    /// # Errors
    ///
    /// Rejects lowercase, control, whitespace and oversized values.
    pub fn parse(value: impl Into<String>) -> Result<Self, JobError> {
        let value = value.into();
        let bytes = value.as_bytes();
        if !(3..=64).contains(&bytes.len())
            || !bytes[0].is_ascii_uppercase()
            || !bytes[1..]
                .iter()
                .all(|byte| byte.is_ascii_uppercase() || byte.is_ascii_digit() || *byte == b'_')
        {
            return Err(JobError::InvalidRequest);
        }
        Ok(Self(value))
    }

    #[must_use]
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl fmt::Debug for TerminalErrorCode {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(&self.0)
    }
}

impl<'de> Deserialize<'de> for TerminalErrorCode {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        Self::parse(String::deserialize(deserializer)?).map_err(D::Error::custom)
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum JobState {
    Queued,
    Leased,
    Staged,
    Executing,
    Validating,
    Succeeded,
    Failed,
    Cancelled,
    UnknownOutcome,
}

impl JobState {
    #[must_use]
    pub const fn is_terminal(self) -> bool {
        matches!(
            self,
            Self::Succeeded | Self::Failed | Self::Cancelled | Self::UnknownOutcome
        )
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum JobStage {
    Staged,
    Executing,
    Validating,
}

impl JobStage {
    #[must_use]
    pub const fn state(self) -> JobState {
        match self {
            Self::Staged => JobState::Staged,
            Self::Executing => JobState::Executing,
            Self::Validating => JobState::Validating,
        }
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct JobSpec {
    project_id: ProjectId,
    job_id: JobId,
    request_id: RequestId,
    input_artifact_id: ArtifactId,
    expected_revision_id: Option<RevisionId>,
    operation_plan_sha256: ContentDigest,
    required_target_profile_id: TargetProfileId,
    required_capability_set_sha256: ContentDigest,
}

impl fmt::Debug for JobSpec {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("JobSpec")
            .field("project_id", &self.project_id)
            .field("job_id", &self.job_id)
            .field("request_id", &self.request_id)
            .field("input_artifact_id", &self.input_artifact_id)
            .field("expected_revision_id", &self.expected_revision_id)
            .field("operation_plan_sha256", &"<redacted>")
            .field(
                "required_target_profile_id",
                &self.required_target_profile_id,
            )
            .field("required_capability_set_sha256", &"<redacted>")
            .finish()
    }
}

impl JobSpec {
    #[must_use]
    #[allow(clippy::too_many_arguments)]
    pub const fn new(
        project_id: ProjectId,
        job_id: JobId,
        request_id: RequestId,
        input_artifact_id: ArtifactId,
        expected_revision_id: Option<RevisionId>,
        operation_plan_sha256: ContentDigest,
        required_target_profile_id: TargetProfileId,
        required_capability_set_sha256: ContentDigest,
    ) -> Self {
        Self {
            project_id,
            job_id,
            request_id,
            input_artifact_id,
            expected_revision_id,
            operation_plan_sha256,
            required_target_profile_id,
            required_capability_set_sha256,
        }
    }

    #[must_use]
    pub const fn project_id(&self) -> ProjectId {
        self.project_id
    }

    #[must_use]
    pub const fn job_id(&self) -> JobId {
        self.job_id
    }

    #[must_use]
    pub const fn request_id(&self) -> RequestId {
        self.request_id
    }

    #[must_use]
    pub const fn input_artifact_id(&self) -> ArtifactId {
        self.input_artifact_id
    }

    #[must_use]
    pub const fn expected_revision_id(&self) -> Option<RevisionId> {
        self.expected_revision_id
    }

    #[must_use]
    pub const fn operation_plan_sha256(&self) -> ContentDigest {
        self.operation_plan_sha256
    }

    #[must_use]
    pub const fn required_target_profile_id(&self) -> &TargetProfileId {
        &self.required_target_profile_id
    }

    #[must_use]
    pub const fn required_capability_set_sha256(&self) -> ContentDigest {
        self.required_capability_set_sha256
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct JobRequestContext {
    tenant_id: TenantId,
    subject: SubjectDigest,
    now_unix_seconds: u64,
}

impl JobRequestContext {
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

impl fmt::Debug for JobRequestContext {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("JobRequestContext")
            .field("tenant_id", &self.tenant_id)
            .field("subject", &"<redacted>")
            .field("now_unix_seconds", &self.now_unix_seconds)
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct LeaseGrant {
    agent_instance_id: AgentInstanceId,
    execution_id: ExecutionId,
    attempt_no: u16,
    fencing_token: u64,
    issued_at_unix_seconds: u64,
    expires_at_unix_seconds: u64,
}

impl fmt::Debug for LeaseGrant {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("LeaseGrant")
            .field("agent_instance_id", &"<redacted>")
            .field("execution_id", &"<redacted>")
            .field("attempt_no", &self.attempt_no)
            .field("fencing_token", &self.fencing_token)
            .field("issued_at_unix_seconds", &self.issued_at_unix_seconds)
            .field("expires_at_unix_seconds", &self.expires_at_unix_seconds)
            .finish()
    }
}

impl LeaseGrant {
    /// Creates a bounded structural lease for the P14-05 state machine.
    ///
    /// # Errors
    ///
    /// Rejects zero fields, backward time and lifetimes above one hour.
    pub fn new(
        agent_instance_id: AgentInstanceId,
        execution_id: ExecutionId,
        attempt_no: u16,
        fencing_token: u64,
        issued_at_unix_seconds: u64,
        expires_at_unix_seconds: u64,
    ) -> Result<Self, JobError> {
        let lifetime = expires_at_unix_seconds
            .checked_sub(issued_at_unix_seconds)
            .ok_or(JobError::InvalidRequest)?;
        if !(1..=100).contains(&attempt_no)
            || fencing_token == 0
            || !(1..=MAX_LEASE_SECONDS).contains(&lifetime)
        {
            return Err(JobError::InvalidRequest);
        }
        Ok(Self {
            agent_instance_id,
            execution_id,
            attempt_no,
            fencing_token,
            issued_at_unix_seconds,
            expires_at_unix_seconds,
        })
    }

    #[must_use]
    pub const fn agent_instance_id(&self) -> AgentInstanceId {
        self.agent_instance_id
    }

    #[must_use]
    pub const fn execution_id(&self) -> ExecutionId {
        self.execution_id
    }

    #[must_use]
    pub const fn attempt_no(&self) -> u16 {
        self.attempt_no
    }

    #[must_use]
    pub const fn fencing_token(&self) -> u64 {
        self.fencing_token
    }

    #[must_use]
    pub const fn expires_at_unix_seconds(&self) -> u64 {
        self.expires_at_unix_seconds
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct JobRecord {
    spec: JobSpec,
    state: JobState,
    attempt_count: u16,
    active_lease: Option<LeaseGrant>,
    result_revision_id: Option<RevisionId>,
    terminal_receipt_artifact_id: Option<ArtifactId>,
    terminal_error_code: Option<TerminalErrorCode>,
    created_at_unix_seconds: u64,
    updated_at_unix_seconds: u64,
    completed_at_unix_seconds: Option<u64>,
}

impl fmt::Debug for JobRecord {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("JobRecord")
            .field("spec", &self.spec)
            .field("state", &self.state)
            .field("attempt_count", &self.attempt_count)
            .field("active_lease", &self.active_lease)
            .field("result_revision_id", &self.result_revision_id)
            .field(
                "terminal_receipt_artifact_id",
                &self.terminal_receipt_artifact_id,
            )
            .field("terminal_error_code", &self.terminal_error_code)
            .field("created_at_unix_seconds", &self.created_at_unix_seconds)
            .field("updated_at_unix_seconds", &self.updated_at_unix_seconds)
            .field("completed_at_unix_seconds", &self.completed_at_unix_seconds)
            .finish()
    }
}

impl JobRecord {
    pub(crate) const fn queued(spec: JobSpec, now: u64) -> Self {
        Self {
            spec,
            state: JobState::Queued,
            attempt_count: 0,
            active_lease: None,
            result_revision_id: None,
            terminal_receipt_artifact_id: None,
            terminal_error_code: None,
            created_at_unix_seconds: now,
            updated_at_unix_seconds: now,
            completed_at_unix_seconds: None,
        }
    }

    #[must_use]
    pub const fn spec(&self) -> &JobSpec {
        &self.spec
    }

    #[must_use]
    pub const fn state(&self) -> JobState {
        self.state
    }

    #[must_use]
    pub const fn attempt_count(&self) -> u16 {
        self.attempt_count
    }

    #[must_use]
    pub const fn active_lease(&self) -> Option<&LeaseGrant> {
        self.active_lease.as_ref()
    }

    #[must_use]
    pub const fn result_revision_id(&self) -> Option<RevisionId> {
        self.result_revision_id
    }

    #[must_use]
    pub const fn terminal_receipt_artifact_id(&self) -> Option<ArtifactId> {
        self.terminal_receipt_artifact_id
    }

    #[must_use]
    pub const fn terminal_error_code(&self) -> Option<&TerminalErrorCode> {
        self.terminal_error_code.as_ref()
    }

    #[must_use]
    pub const fn completed_at_unix_seconds(&self) -> Option<u64> {
        self.completed_at_unix_seconds
    }

    pub(crate) fn lease(&mut self, lease: LeaseGrant, now: u64) -> Result<(), JobError> {
        self.require_time(now)?;
        if self.state != JobState::Queued
            || self.attempt_count != 0
            || lease.attempt_no() != 1
            || lease.fencing_token() != 1
            || lease.issued_at_unix_seconds != now
        {
            return Err(JobError::InvalidTransition);
        }
        self.state = JobState::Leased;
        self.attempt_count = 1;
        self.active_lease = Some(lease);
        self.updated_at_unix_seconds = now;
        Ok(())
    }

    pub(crate) fn advance(
        &mut self,
        lease: &LeaseGrant,
        next: JobStage,
        now: u64,
    ) -> Result<(), JobError> {
        self.require_time(now)?;
        let valid = matches!(
            (self.state, next),
            (JobState::Leased, JobStage::Staged)
                | (JobState::Staged, JobStage::Executing)
                | (JobState::Executing, JobStage::Validating)
        );
        if !valid {
            return Err(JobError::InvalidTransition);
        }
        self.require_lease(lease)?;
        self.state = next.state();
        self.updated_at_unix_seconds = now;
        Ok(())
    }

    pub(crate) fn succeed(
        &mut self,
        lease: &LeaseGrant,
        revision_id: RevisionId,
        receipt_artifact_id: ArtifactId,
        now: u64,
    ) -> Result<(), JobError> {
        self.require_time(now)?;
        if self.state != JobState::Validating {
            return Err(JobError::InvalidTransition);
        }
        self.require_lease(lease)?;
        self.state = JobState::Succeeded;
        self.active_lease = None;
        self.result_revision_id = Some(revision_id);
        self.terminal_receipt_artifact_id = Some(receipt_artifact_id);
        self.updated_at_unix_seconds = now;
        self.completed_at_unix_seconds = Some(now);
        Ok(())
    }

    pub(crate) fn fail(
        &mut self,
        lease: &LeaseGrant,
        error_code: TerminalErrorCode,
        receipt_artifact_id: ArtifactId,
        now: u64,
    ) -> Result<(), JobError> {
        self.require_time(now)?;
        if !matches!(
            self.state,
            JobState::Leased | JobState::Staged | JobState::Executing | JobState::Validating
        ) {
            return Err(JobError::InvalidTransition);
        }
        self.require_lease(lease)?;
        self.state = JobState::Failed;
        self.active_lease = None;
        self.terminal_receipt_artifact_id = Some(receipt_artifact_id);
        self.terminal_error_code = Some(error_code);
        self.updated_at_unix_seconds = now;
        self.completed_at_unix_seconds = Some(now);
        Ok(())
    }

    fn require_lease(&self, lease: &LeaseGrant) -> Result<(), JobError> {
        if self.active_lease.as_ref() == Some(lease) {
            Ok(())
        } else {
            Err(JobError::LeaseMismatch)
        }
    }

    fn require_time(&self, now: u64) -> Result<(), JobError> {
        if now >= self.updated_at_unix_seconds {
            Ok(())
        } else {
            Err(JobError::InvalidRequest)
        }
    }
}
