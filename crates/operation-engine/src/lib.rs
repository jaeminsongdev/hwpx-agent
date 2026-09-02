#![forbid(unsafe_code)]

mod idempotency;
mod manifest;
mod state;
mod transaction;

pub use idempotency::{
    ClaimLease, ClaimOutcome, CommittedResult, IDEMPOTENCY_RECEIPT_SCHEMA_VERSION,
    IdempotencyBinding, IdempotencyError, IdempotencyLimits, IdempotencyReceipt,
    IdempotencyService, IdempotencyState, IdempotencyStore, OwnerToken, ReconcileObservation,
    RevisionCommit, RevisionHead, RevisionStreamKey, TerminalFailure,
};
pub use manifest::{ExecutionManifest, ExecutionManifestError};
pub use state::{
    FaultMoment, FaultPlan, FaultPoint, StateMachineError, TransactionState,
    TransactionStateMachine, TransactionStep,
};
pub use transaction::{
    ArtifactDisposition, OutputValidator, RevisionCas, RevisionCasOutcome, RevisionCommitRequest,
    TransactionError, TransactionFailure, TransactionLimits, TransactionReceipt, ValidationOutcome,
    WORKSPACE_TRANSACTION_RECEIPT_SCHEMA_VERSION, WorkspaceTransaction,
};
