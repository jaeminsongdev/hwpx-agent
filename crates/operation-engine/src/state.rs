use std::fmt;

use serde::Serialize;
use thiserror::Error;

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TransactionState {
    Received,
    Planned,
    PreconditionsVerified,
    WorkspacePrepared,
    Executing,
    Readback,
    Validating,
    ArtifactCommitted,
    RevisionCasCommitted,
    Completed,
    RolledBack,
    Quarantined,
    Incomplete,
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum TransactionStep {
    Plan,
    VerifyPreconditions,
    PrepareWorkspace,
    Execute,
    Readback,
    Validate,
    CommitArtifact,
    CommitRevision,
    Complete,
    Rollback,
    Quarantine,
}

impl TransactionStep {
    pub const NORMAL: [Self; 9] = [
        Self::Plan,
        Self::VerifyPreconditions,
        Self::PrepareWorkspace,
        Self::Execute,
        Self::Readback,
        Self::Validate,
        Self::CommitArtifact,
        Self::CommitRevision,
        Self::Complete,
    ];
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum FaultMoment {
    Before,
    After,
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub struct FaultPoint {
    step: TransactionStep,
    moment: FaultMoment,
}

impl FaultPoint {
    #[must_use]
    pub const fn new(step: TransactionStep, moment: FaultMoment) -> Self {
        Self { step, moment }
    }

    #[must_use]
    pub const fn step(self) -> TransactionStep {
        self.step
    }

    #[must_use]
    pub const fn moment(self) -> FaultMoment {
        self.moment
    }
}

#[derive(Clone, Debug, Default)]
pub struct FaultPlan {
    fail_at: Option<FaultPoint>,
    fired: bool,
}

impl FaultPlan {
    #[must_use]
    pub const fn none() -> Self {
        Self {
            fail_at: None,
            fired: false,
        }
    }

    #[must_use]
    pub const fn at(point: FaultPoint) -> Self {
        Self {
            fail_at: Some(point),
            fired: false,
        }
    }

    pub(crate) fn check(&mut self, point: FaultPoint) -> bool {
        if !self.fired && self.fail_at == Some(point) {
            self.fired = true;
            true
        } else {
            false
        }
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TransactionStateMachine {
    state: TransactionState,
}

impl Default for TransactionStateMachine {
    fn default() -> Self {
        Self {
            state: TransactionState::Received,
        }
    }
}

impl TransactionStateMachine {
    #[must_use]
    pub const fn state(&self) -> TransactionState {
        self.state
    }

    /// Advances exactly one legal success transition.
    ///
    /// # Errors
    ///
    /// Rejects skips, repeats, backward movement and all transitions out of terminal states.
    pub fn advance(&mut self, next: TransactionState) -> Result<(), StateMachineError> {
        let expected = match self.state {
            TransactionState::Received => TransactionState::Planned,
            TransactionState::Planned => TransactionState::PreconditionsVerified,
            TransactionState::PreconditionsVerified => TransactionState::WorkspacePrepared,
            TransactionState::WorkspacePrepared => TransactionState::Executing,
            TransactionState::Executing => TransactionState::Readback,
            TransactionState::Readback => TransactionState::Validating,
            TransactionState::Validating => TransactionState::ArtifactCommitted,
            TransactionState::ArtifactCommitted => TransactionState::RevisionCasCommitted,
            TransactionState::RevisionCasCommitted => TransactionState::Completed,
            TransactionState::Completed
            | TransactionState::RolledBack
            | TransactionState::Quarantined
            | TransactionState::Incomplete => return Err(StateMachineError::Terminal),
        };
        if next != expected {
            return Err(StateMachineError::InvalidTransition);
        }
        self.state = next;
        Ok(())
    }

    pub(crate) const fn mark_recovery(&mut self, state: TransactionState) {
        self.state = state;
    }
}

impl fmt::Debug for TransactionStateMachine {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TransactionStateMachine")
            .field("state", &self.state)
            .finish()
    }
}

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum StateMachineError {
    #[error("transaction state transition is invalid")]
    InvalidTransition,
    #[error("transaction state is terminal")]
    Terminal,
}

impl StateMachineError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::InvalidTransition => "workspace_transaction_invalid_transition",
            Self::Terminal => "workspace_transaction_terminal_state",
        }
    }
}
