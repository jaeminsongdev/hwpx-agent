#![forbid(unsafe_code)]

mod service;
mod store;
mod types;

pub use service::JobService;
pub use store::{InMemoryJobRepository, JobRepository, QualifiedArtifactKind};
pub use types::{
    AgentInstanceId, ExecutionId, JobError, JobId, JobRecord, JobRequestContext, JobSpec, JobStage,
    JobState, LeaseGrant, ProjectRole, RequestId, TargetProfileId, TerminalErrorCode,
};
