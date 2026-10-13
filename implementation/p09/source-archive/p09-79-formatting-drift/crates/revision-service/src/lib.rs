#![forbid(unsafe_code)]

pub mod postgres;
mod service;
mod store;
mod types;

pub use service::RevisionService;
pub use store::{InMemoryRevisionRepository, RevisionRepository};
pub use types::{
    BranchId, CommitId, CommitOutcome, FullDocumentIrBinding, ProjectId, RevisionCommitRequest,
    RevisionConflict, RevisionError, RevisionHead, RevisionId, RevisionNode, RevisionReceipt,
    RevisionRequestContext, RevisionValidationState,
};
