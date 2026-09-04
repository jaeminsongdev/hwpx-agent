#![forbid(unsafe_code)]

mod cursor;
mod service;
mod store;
mod types;

pub use cursor::CursorCodec;
pub use service::HistoryService;
pub use store::{HistoryRepository, InMemoryHistoryRepository};
pub use types::{
    BranchCreateRequest, BranchName, BranchRecord, CheckpointId, CheckpointLabel,
    CheckpointOutcome, CheckpointRecord, CheckpointRequest, CommittedRevisionProjection,
    HistoryEntry, HistoryError, HistoryPage, HistoryQuery, HistoryRequestContext, HistorySnapshot,
    ProjectRole, RequestId, SemanticDiffReference,
};
