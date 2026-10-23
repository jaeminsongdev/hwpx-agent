#![forbid(unsafe_code)]

mod service;
mod store;
mod types;
mod reconciliation;
pub use reconciliation::CommitObservation;
pub mod postgres;

pub use service::RevisionService;
pub use store::{InMemoryRevisionRepository, RevisionRepository};
pub use types::{
    BranchId, CommitId, CommitOutcome, ProjectId, RevisionCommitRequest, RevisionConflict,
    RevisionError, RevisionHead, RevisionId, RevisionNode, RevisionReceipt, RevisionRequestContext,
    RevisionValidationState, FullDocumentIrBinding,
};
