use std::fmt;
use std::fs::{self, File};
use std::io::Read;
use std::path::{Path, PathBuf};

use domain_ir::{ArtifactId, RevisionId, TransactionId};
use hwpx_agent_foundation::workdir::{SecureWorkspace, StagedArtifact, WorkspaceError};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::{
    ExecutionManifest, FaultMoment, FaultPlan, FaultPoint, TransactionState,
    TransactionStateMachine, TransactionStep,
};

pub const WORKSPACE_TRANSACTION_RECEIPT_SCHEMA_VERSION: &str =
    "hwpx-agent.workspace-transaction-receipt/v1";

const HARD_MAX_ARTIFACT_BYTES: u64 = 4 * 1024 * 1024 * 1024;
const HARD_MAX_MANIFEST_BYTES: usize = 16 * 1024 * 1024;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TransactionLimits {
    pub max_source_bytes: u64,
    pub max_output_bytes: u64,
    pub max_manifest_bytes: usize,
}

impl Default for TransactionLimits {
    fn default() -> Self {
        Self {
            max_source_bytes: 512 * 1024 * 1024,
            max_output_bytes: 512 * 1024 * 1024,
            max_manifest_bytes: 4 * 1024 * 1024,
        }
    }
}

impl TransactionLimits {
    fn validate(self) -> Result<(), TransactionError> {
        if self.max_source_bytes == 0
            || self.max_source_bytes > HARD_MAX_ARTIFACT_BYTES
            || self.max_output_bytes == 0
            || self.max_output_bytes > HARD_MAX_ARTIFACT_BYTES
            || self.max_manifest_bytes == 0
            || self.max_manifest_bytes > HARD_MAX_MANIFEST_BYTES
        {
            return Err(TransactionError::InvalidLimit);
        }
        Ok(())
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ValidationOutcome {
    Valid,
    Rejected,
    Failed,
}

pub trait OutputValidator {
    fn validate(&mut self, bytes: &[u8]) -> ValidationOutcome;
}

impl<F> OutputValidator for F
where
    F: FnMut(&[u8]) -> ValidationOutcome,
{
    fn validate(&mut self, bytes: &[u8]) -> ValidationOutcome {
        self(bytes)
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum RevisionCasOutcome {
    Committed,
    Conflict,
    Failed,
}

pub trait RevisionCas {
    fn compare_and_swap(&mut self, request: &RevisionCommitRequest) -> RevisionCasOutcome;
}

impl<F> RevisionCas for F
where
    F: FnMut(&RevisionCommitRequest) -> RevisionCasOutcome,
{
    fn compare_and_swap(&mut self, request: &RevisionCommitRequest) -> RevisionCasOutcome {
        self(request)
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct RevisionCommitRequest {
    transaction_id: TransactionId,
    base_revision: RevisionId,
    source_artifact_id: ArtifactId,
    result_artifact_id: ArtifactId,
    manifest_sha256: [u8; 32],
    result_sha256: [u8; 32],
    result_size: u64,
}

impl RevisionCommitRequest {
    #[must_use]
    pub const fn transaction_id(&self) -> &TransactionId {
        &self.transaction_id
    }

    #[must_use]
    pub const fn base_revision(&self) -> &RevisionId {
        &self.base_revision
    }

    #[must_use]
    pub const fn result_artifact_id(&self) -> &ArtifactId {
        &self.result_artifact_id
    }

    #[must_use]
    pub const fn result_sha256(&self) -> [u8; 32] {
        self.result_sha256
    }

    #[must_use]
    pub const fn result_size(&self) -> u64 {
        self.result_size
    }

    /// Hashes the deterministic precommit receipt that is presented to revision CAS.
    ///
    /// # Errors
    ///
    /// Returns a stable serialization error.
    pub fn canonical_sha256(&self) -> Result<[u8; 32], TransactionError> {
        let bytes = serde_json::to_vec(self).map_err(|_| TransactionError::ReceiptSerialization)?;
        Ok(Sha256::digest(bytes).into())
    }
}

impl fmt::Debug for RevisionCommitRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("RevisionCommitRequest")
            .field("result_size", &self.result_size)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ArtifactDisposition {
    Absent,
    Committed,
    Quarantined,
    CommittedOutcomeUncertain,
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TransactionReceipt {
    schema_version: String,
    transaction_id: TransactionId,
    state: TransactionState,
    manifest_sha256: [u8; 32],
    source_sha256: [u8; 32],
    source_unchanged: bool,
    result_artifact_id: Option<ArtifactId>,
    result_sha256: Option<[u8; 32]>,
    result_size: Option<u64>,
    artifact_disposition: ArtifactDisposition,
}

impl TransactionReceipt {
    #[must_use]
    pub const fn state(&self) -> TransactionState {
        self.state
    }

    #[must_use]
    pub const fn source_unchanged(&self) -> bool {
        self.source_unchanged
    }

    #[must_use]
    pub const fn artifact_disposition(&self) -> ArtifactDisposition {
        self.artifact_disposition
    }

    #[must_use]
    pub const fn result_sha256(&self) -> Option<[u8; 32]> {
        self.result_sha256
    }

    /// Emits deterministic compact receipt bytes.
    ///
    /// # Errors
    ///
    /// Returns a stable serialization failure.
    pub fn canonical_json(&self) -> Result<Vec<u8>, TransactionError> {
        serde_json::to_vec(self).map_err(|_| TransactionError::ReceiptSerialization)
    }

    /// Hashes the deterministic transaction receipt.
    ///
    /// # Errors
    ///
    /// Propagates a stable serialization failure.
    pub fn canonical_sha256(&self) -> Result<[u8; 32], TransactionError> {
        Ok(Sha256::digest(self.canonical_json()?).into())
    }
}

impl fmt::Debug for TransactionReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TransactionReceipt")
            .field("state", &self.state)
            .field("source_unchanged", &self.source_unchanged)
            .field("artifact_disposition", &self.artifact_disposition)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TransactionFailure {
    primary: TransactionError,
    recovery: Option<TransactionError>,
    receipt: Box<TransactionReceipt>,
}

impl TransactionFailure {
    #[must_use]
    pub const fn primary(&self) -> TransactionError {
        self.primary
    }

    #[must_use]
    pub const fn recovery(&self) -> Option<TransactionError> {
        self.recovery
    }

    #[must_use]
    pub fn receipt(&self) -> &TransactionReceipt {
        self.receipt.as_ref()
    }
}

impl fmt::Debug for TransactionFailure {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TransactionFailure")
            .field("primary", &self.primary)
            .field("recovery", &self.recovery)
            .field("state", &self.receipt.state)
            .field("artifact_disposition", &self.receipt.artifact_disposition)
            .finish()
    }
}

impl fmt::Display for TransactionFailure {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(self.primary.code())
    }
}

impl std::error::Error for TransactionFailure {}

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum TransactionError {
    #[error("workspace transaction limit is invalid")]
    InvalidLimit,
    #[error("workspace transaction input exceeds its finite limit")]
    LimitExceeded,
    #[error("workspace transaction manifest is invalid")]
    InvalidManifest,
    #[error("workspace transaction source is invalid")]
    InvalidSource,
    #[error("workspace transaction source identity does not match")]
    SourceIdentityMismatch,
    #[error("workspace transaction source changed")]
    SourceMutationDetected,
    #[error("workspace transaction output is invalid")]
    InvalidOutput,
    #[error("workspace transaction output validation rejected")]
    ValidationRejected,
    #[error("workspace transaction output validation failed")]
    ValidationFailed,
    #[error("workspace transaction artifact already exists")]
    ArtifactExists,
    #[error("workspace transaction artifact outcome is incomplete")]
    ArtifactOutcomeIncomplete,
    #[error("workspace transaction revision compare-and-swap conflicted")]
    RevisionConflict,
    #[error("workspace transaction revision compare-and-swap failed")]
    RevisionCasFailed,
    #[error("workspace transaction fault was injected")]
    InjectedFault,
    #[error("workspace transaction recovery failed")]
    RecoveryFailed,
    #[error("workspace transaction filesystem boundary failed")]
    WorkspaceFailure,
    #[error("workspace transaction state transition failed")]
    InvalidState,
    #[error("workspace transaction receipt serialization failed")]
    ReceiptSerialization,
}

impl TransactionError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::InvalidLimit => "workspace_transaction_invalid_limit",
            Self::LimitExceeded => "workspace_transaction_limit_exceeded",
            Self::InvalidManifest => "workspace_transaction_invalid_manifest",
            Self::InvalidSource => "workspace_transaction_invalid_source",
            Self::SourceIdentityMismatch => "workspace_transaction_source_identity_mismatch",
            Self::SourceMutationDetected => "workspace_transaction_source_mutation_detected",
            Self::InvalidOutput => "workspace_transaction_invalid_output",
            Self::ValidationRejected => "workspace_transaction_validation_rejected",
            Self::ValidationFailed => "workspace_transaction_validation_failed",
            Self::ArtifactExists => "workspace_transaction_artifact_exists",
            Self::ArtifactOutcomeIncomplete => "workspace_transaction_artifact_outcome_incomplete",
            Self::RevisionConflict => "workspace_transaction_revision_conflict",
            Self::RevisionCasFailed => "workspace_transaction_revision_cas_failed",
            Self::InjectedFault => "workspace_transaction_injected_fault",
            Self::RecoveryFailed => "workspace_transaction_recovery_failed",
            Self::WorkspaceFailure => "workspace_transaction_workspace_failure",
            Self::InvalidState => "workspace_transaction_invalid_state",
            Self::ReceiptSerialization => "workspace_transaction_receipt_serialization",
        }
    }
}

pub struct WorkspaceTransaction {
    manifest: ExecutionManifest,
    manifest_sha256: [u8; 32],
    limits: TransactionLimits,
    machine: TransactionStateMachine,
    workspace: SecureWorkspace,
    workspace_root: PathBuf,
    job_relative: PathBuf,
    source_staged: Option<StagedArtifact>,
    output_staged: Option<StagedArtifact>,
    result_sha256: Option<[u8; 32]>,
    result_size: Option<u64>,
    output_relative: Option<PathBuf>,
    artifact_disposition: ArtifactDisposition,
}

#[derive(Clone, Eq, PartialEq)]
struct SourceObservation {
    canonical_path: PathBuf,
    sha256: [u8; 32],
    size: u64,
}

impl WorkspaceTransaction {
    /// Creates one isolated, single-use transaction workspace.
    ///
    /// # Errors
    ///
    /// Rejects invalid limits/manifests and workspace containment or creation failures.
    pub fn create(
        workspace_root: impl AsRef<Path>,
        manifest: ExecutionManifest,
        limits: TransactionLimits,
    ) -> Result<Self, TransactionError> {
        limits.validate()?;
        if manifest.expected_source_size() > limits.max_source_bytes {
            return Err(TransactionError::LimitExceeded);
        }
        let manifest_bytes = manifest
            .canonical_json()
            .map_err(|_| TransactionError::InvalidManifest)?;
        if manifest_bytes.len() > limits.max_manifest_bytes {
            return Err(TransactionError::LimitExceeded);
        }
        let manifest_sha256 = Sha256::digest(&manifest_bytes).into();
        let workspace = SecureWorkspace::create(workspace_root.as_ref()).map_err(map_workspace)?;
        let workspace_root = workspace_root
            .as_ref()
            .canonicalize()
            .map_err(|_| TransactionError::WorkspaceFailure)?;
        let job_digest = hex::encode(Sha256::digest(
            manifest.transaction_id().as_str().as_bytes(),
        ));
        Ok(Self {
            manifest,
            manifest_sha256,
            limits,
            machine: TransactionStateMachine::default(),
            workspace,
            workspace_root,
            job_relative: PathBuf::from("jobs").join(job_digest),
            source_staged: None,
            output_staged: None,
            result_sha256: None,
            result_size: None,
            output_relative: None,
            artifact_disposition: ArtifactDisposition::Absent,
        })
    }

    #[must_use]
    pub const fn state(&self) -> TransactionState {
        self.machine.state()
    }

    /// Executes a precomputed output through isolated staging, readback, validation, artifact
    /// publication and revision CAS. The source is opened read-only and never used as a destination.
    ///
    /// # Errors
    ///
    /// Returns a failure receipt after rollback, quarantine or explicit incomplete classification.
    pub fn execute<V, C>(
        &mut self,
        source_path: impl AsRef<Path>,
        proposed_output: &[u8],
        validator: &mut V,
        revision_cas: &mut C,
        faults: &mut FaultPlan,
    ) -> Result<TransactionReceipt, TransactionFailure>
    where
        V: OutputValidator,
        C: RevisionCas,
    {
        let source_path = source_path.as_ref();
        let initial_source = self.observe_source(source_path);
        let result = self.run(
            source_path,
            proposed_output,
            validator,
            revision_cas,
            faults,
        );
        match result {
            Ok(()) => {
                let source_unchanged = initial_source.as_ref().is_some_and(|before| {
                    self.observe_source(source_path).as_ref() == Some(before)
                });
                if !source_unchanged {
                    self.machine.mark_recovery(TransactionState::Incomplete);
                    return Err(self.failure(
                        TransactionError::SourceMutationDetected,
                        None,
                        false,
                    ));
                }
                let receipt = self.receipt(true);
                let receipt_is_valid = receipt
                    .canonical_json()
                    .is_ok_and(|bytes| bytes.len() <= self.limits.max_manifest_bytes);
                if !receipt_is_valid {
                    self.machine.mark_recovery(TransactionState::Incomplete);
                    return Err(self.failure(TransactionError::ReceiptSerialization, None, true));
                }
                Ok(receipt)
            }
            Err(primary) => {
                let recovery = self.recover(faults);
                let source_unchanged = initial_source.as_ref().is_some_and(|before| {
                    self.observe_source(source_path).as_ref() == Some(before)
                });
                let source_changed_during_transaction =
                    initial_source.is_some() && !source_unchanged;
                if source_changed_during_transaction {
                    self.machine.mark_recovery(TransactionState::Incomplete);
                }
                Err(self.failure(
                    if source_changed_during_transaction {
                        TransactionError::SourceMutationDetected
                    } else {
                        primary
                    },
                    recovery,
                    source_unchanged,
                ))
            }
        }
    }

    fn run<V, C>(
        &mut self,
        source_path: &Path,
        proposed_output: &[u8],
        validator: &mut V,
        revision_cas: &mut C,
        faults: &mut FaultPlan,
    ) -> Result<(), TransactionError>
    where
        V: OutputValidator,
        C: RevisionCas,
    {
        if self.machine.state() != TransactionState::Received {
            return Err(TransactionError::InvalidState);
        }
        if proposed_output.is_empty()
            || u64::try_from(proposed_output.len())
                .map_or(true, |size| size > self.limits.max_output_bytes)
        {
            return Err(TransactionError::InvalidOutput);
        }

        Self::begin(TransactionStep::Plan, faults)?;
        self.finish(TransactionStep::Plan, TransactionState::Planned, faults)?;

        Self::begin(TransactionStep::VerifyPreconditions, faults)?;
        let source = self.read_verified_source(source_path)?;
        self.finish(
            TransactionStep::VerifyPreconditions,
            TransactionState::PreconditionsVerified,
            faults,
        )?;

        let readback = self.prepare_and_readback(&source, proposed_output, faults)?;
        let result_sha256 = self.result_sha256.ok_or(TransactionError::InvalidState)?;

        Self::begin(TransactionStep::Validate, faults)?;
        match validator.validate(&readback) {
            ValidationOutcome::Valid => {}
            ValidationOutcome::Rejected => return Err(TransactionError::ValidationRejected),
            ValidationOutcome::Failed => return Err(TransactionError::ValidationFailed),
        }
        if !self.source_matches(source_path) {
            return Err(TransactionError::SourceMutationDetected);
        }
        self.finish(
            TransactionStep::Validate,
            TransactionState::Validating,
            faults,
        )?;

        Self::begin(TransactionStep::CommitArtifact, faults)?;
        let public_relative =
            PathBuf::from("artifacts").join(format!("{}.hwpx", hex::encode(result_sha256)));
        self.output_relative = Some(public_relative.clone());
        let staged = self
            .output_staged
            .as_ref()
            .ok_or(TransactionError::InvalidState)?;
        if let Err(error) = self.workspace.publish(staged, &public_relative) {
            if matches!(error, WorkspaceError::ArtifactPublishedIncomplete) {
                self.artifact_disposition = ArtifactDisposition::CommittedOutcomeUncertain;
            }
            return Err(map_workspace(error));
        }
        self.output_staged = None;
        self.artifact_disposition = ArtifactDisposition::Committed;
        self.finish(
            TransactionStep::CommitArtifact,
            TransactionState::ArtifactCommitted,
            faults,
        )?;

        Self::begin(TransactionStep::CommitRevision, faults)?;
        let request = self.commit_request()?;
        match revision_cas.compare_and_swap(&request) {
            RevisionCasOutcome::Committed => {}
            RevisionCasOutcome::Conflict => return Err(TransactionError::RevisionConflict),
            RevisionCasOutcome::Failed => return Err(TransactionError::RevisionCasFailed),
        }
        self.finish(
            TransactionStep::CommitRevision,
            TransactionState::RevisionCasCommitted,
            faults,
        )?;

        Self::begin(TransactionStep::Complete, faults)?;
        self.workspace
            .cleanup_staging(&self.job_relative)
            .map_err(map_workspace)?;
        self.source_staged = None;
        self.finish(
            TransactionStep::Complete,
            TransactionState::Completed,
            faults,
        )
    }

    fn begin(step: TransactionStep, faults: &mut FaultPlan) -> Result<(), TransactionError> {
        if faults.check(FaultPoint::new(step, FaultMoment::Before)) {
            return Err(TransactionError::InjectedFault);
        }
        Ok(())
    }

    fn prepare_and_readback(
        &mut self,
        source: &[u8],
        proposed_output: &[u8],
        faults: &mut FaultPlan,
    ) -> Result<Vec<u8>, TransactionError> {
        Self::begin(TransactionStep::PrepareWorkspace, faults)?;
        let source_relative = self.job_relative.join("source.hwpx");
        self.source_staged = Some(
            self.workspace
                .stage_bytes(&source_relative, source)
                .map_err(map_workspace)?,
        );
        self.finish(
            TransactionStep::PrepareWorkspace,
            TransactionState::WorkspacePrepared,
            faults,
        )?;

        Self::begin(TransactionStep::Execute, faults)?;
        let output_relative = self.job_relative.join("output.hwpx");
        self.output_staged = Some(
            self.workspace
                .stage_bytes(&output_relative, proposed_output)
                .map_err(map_workspace)?,
        );
        self.finish(
            TransactionStep::Execute,
            TransactionState::Executing,
            faults,
        )?;

        Self::begin(TransactionStep::Readback, faults)?;
        let readback = self.read_staged_output()?;
        self.result_sha256 = Some(Sha256::digest(&readback).into());
        self.result_size =
            Some(u64::try_from(readback.len()).map_err(|_| TransactionError::LimitExceeded)?);
        self.finish(
            TransactionStep::Readback,
            TransactionState::Readback,
            faults,
        )?;
        Ok(readback)
    }

    fn finish(
        &mut self,
        step: TransactionStep,
        next: TransactionState,
        faults: &mut FaultPlan,
    ) -> Result<(), TransactionError> {
        self.machine
            .advance(next)
            .map_err(|_| TransactionError::InvalidState)?;
        if faults.check(FaultPoint::new(step, FaultMoment::After)) {
            return Err(TransactionError::InjectedFault);
        }
        Ok(())
    }

    fn read_verified_source(&self, source_path: &Path) -> Result<Vec<u8>, TransactionError> {
        reject_source_link(source_path)?;
        let canonical = source_path
            .canonicalize()
            .map_err(|_| TransactionError::InvalidSource)?;
        if canonical.starts_with(&self.workspace_root) {
            return Err(TransactionError::InvalidSource);
        }
        self.read_source_identity(&canonical)
    }

    fn read_source_identity(&self, canonical: &Path) -> Result<Vec<u8>, TransactionError> {
        let file = File::open(canonical).map_err(|_| TransactionError::InvalidSource)?;
        let metadata = file
            .metadata()
            .map_err(|_| TransactionError::InvalidSource)?;
        if !metadata.is_file()
            || metadata.len() != self.manifest.expected_source_size()
            || metadata.len() > self.limits.max_source_bytes
        {
            return Err(TransactionError::SourceIdentityMismatch);
        }
        let capacity =
            usize::try_from(metadata.len()).map_err(|_| TransactionError::LimitExceeded)?;
        let mut bytes = Vec::with_capacity(capacity);
        file.take(self.limits.max_source_bytes.saturating_add(1))
            .read_to_end(&mut bytes)
            .map_err(|_| TransactionError::InvalidSource)?;
        if u64::try_from(bytes.len()).map_err(|_| TransactionError::LimitExceeded)?
            != metadata.len()
            || <[u8; 32]>::from(Sha256::digest(&bytes)) != self.manifest.expected_source_sha256()
        {
            return Err(TransactionError::SourceIdentityMismatch);
        }
        Ok(bytes)
    }

    fn source_matches(&self, source_path: &Path) -> bool {
        self.read_verified_source(source_path).is_ok()
    }

    fn observe_source(&self, source_path: &Path) -> Option<SourceObservation> {
        reject_source_link(source_path).ok()?;
        let canonical = source_path.canonicalize().ok()?;
        let file = File::open(&canonical).ok()?;
        let metadata = file.metadata().ok()?;
        if !metadata.is_file() || metadata.len() > self.limits.max_source_bytes {
            return None;
        }
        let mut bytes = Vec::with_capacity(usize::try_from(metadata.len()).ok()?);
        file.take(self.limits.max_source_bytes.saturating_add(1))
            .read_to_end(&mut bytes)
            .ok()?;
        let size = u64::try_from(bytes.len()).ok()?;
        (size == metadata.len()).then_some(SourceObservation {
            canonical_path: canonical,
            sha256: Sha256::digest(&bytes).into(),
            size,
        })
    }

    fn read_staged_output(&self) -> Result<Vec<u8>, TransactionError> {
        let staged = self
            .output_staged
            .as_ref()
            .ok_or(TransactionError::InvalidState)?;
        if staged.size_bytes == 0 || staged.size_bytes > self.limits.max_output_bytes {
            return Err(TransactionError::InvalidOutput);
        }
        let reader = self.workspace.open_staged(staged).map_err(map_workspace)?;
        let capacity =
            usize::try_from(staged.size_bytes).map_err(|_| TransactionError::LimitExceeded)?;
        let mut bytes = Vec::with_capacity(capacity);
        reader
            .take(self.limits.max_output_bytes.saturating_add(1))
            .read_to_end(&mut bytes)
            .map_err(|_| TransactionError::WorkspaceFailure)?;
        let size = u64::try_from(bytes.len()).map_err(|_| TransactionError::LimitExceeded)?;
        if size != staged.size_bytes
            || hex::encode(Sha256::digest(&bytes)) != staged.sha256
            || size > self.limits.max_output_bytes
        {
            return Err(TransactionError::InvalidOutput);
        }
        Ok(bytes)
    }

    fn commit_request(&self) -> Result<RevisionCommitRequest, TransactionError> {
        let result_sha256 = self.result_sha256.ok_or(TransactionError::InvalidState)?;
        let result_size = self.result_size.ok_or(TransactionError::InvalidState)?;
        let result_artifact_id = artifact_id(result_sha256)?;
        Ok(RevisionCommitRequest {
            transaction_id: self.manifest.transaction_id().clone(),
            base_revision: self.manifest.base_revision().clone(),
            source_artifact_id: self.manifest.source_artifact_id().clone(),
            result_artifact_id,
            manifest_sha256: self.manifest_sha256,
            result_sha256,
            result_size,
        })
    }

    fn recover(&mut self, faults: &mut FaultPlan) -> Option<TransactionError> {
        match self.machine.state() {
            TransactionState::ArtifactCommitted => self.quarantine(faults).err(),
            TransactionState::RevisionCasCommitted
            | TransactionState::Completed
            | TransactionState::Quarantined
            | TransactionState::RolledBack
            | TransactionState::Incomplete => None,
            TransactionState::Received
            | TransactionState::Planned
            | TransactionState::PreconditionsVerified
            | TransactionState::WorkspacePrepared
            | TransactionState::Executing
            | TransactionState::Readback
            | TransactionState::Validating => {
                if matches!(
                    self.artifact_disposition,
                    ArtifactDisposition::Committed | ArtifactDisposition::CommittedOutcomeUncertain
                ) {
                    self.quarantine(faults).err()
                } else {
                    self.rollback(faults).err()
                }
            }
        }
    }

    fn rollback(&mut self, faults: &mut FaultPlan) -> Result<(), TransactionError> {
        Self::begin(TransactionStep::Rollback, faults)
            .inspect_err(|_| self.machine.mark_recovery(TransactionState::Incomplete))?;
        if (self.source_staged.is_some() || self.output_staged.is_some())
            && self.workspace.cleanup_staging(&self.job_relative).is_err()
        {
            self.machine.mark_recovery(TransactionState::Incomplete);
            return Err(TransactionError::RecoveryFailed);
        }
        self.source_staged = None;
        self.output_staged = None;
        self.machine.mark_recovery(TransactionState::RolledBack);
        if faults.check(FaultPoint::new(
            TransactionStep::Rollback,
            FaultMoment::After,
        )) {
            return Err(TransactionError::InjectedFault);
        }
        Ok(())
    }

    fn quarantine(&mut self, faults: &mut FaultPlan) -> Result<(), TransactionError> {
        if let Err(error) = Self::begin(TransactionStep::Quarantine, faults) {
            self.machine.mark_recovery(TransactionState::Incomplete);
            self.artifact_disposition = ArtifactDisposition::CommittedOutcomeUncertain;
            return Err(error);
        }
        let output_relative = self
            .output_relative
            .as_ref()
            .ok_or(TransactionError::RecoveryFailed)?;
        let result_sha256 = self.result_sha256.ok_or(TransactionError::RecoveryFailed)?;
        let quarantine_relative = PathBuf::from("orphans").join(format!(
            "{}-{}.hwpx",
            hex::encode(self.manifest_sha256),
            hex::encode(result_sha256)
        ));
        if self
            .workspace
            .quarantine_published(output_relative, &quarantine_relative)
            .is_err()
        {
            self.machine.mark_recovery(TransactionState::Incomplete);
            self.artifact_disposition = ArtifactDisposition::CommittedOutcomeUncertain;
            return Err(TransactionError::RecoveryFailed);
        }
        if self.source_staged.is_some()
            && self.workspace.cleanup_staging(&self.job_relative).is_err()
        {
            self.machine.mark_recovery(TransactionState::Incomplete);
            self.artifact_disposition = ArtifactDisposition::Quarantined;
            return Err(TransactionError::RecoveryFailed);
        }
        self.source_staged = None;
        self.output_staged = None;
        self.artifact_disposition = ArtifactDisposition::Quarantined;
        self.machine.mark_recovery(TransactionState::Quarantined);
        if faults.check(FaultPoint::new(
            TransactionStep::Quarantine,
            FaultMoment::After,
        )) {
            return Err(TransactionError::InjectedFault);
        }
        Ok(())
    }

    fn receipt(&self, source_unchanged: bool) -> TransactionReceipt {
        TransactionReceipt {
            schema_version: WORKSPACE_TRANSACTION_RECEIPT_SCHEMA_VERSION.to_owned(),
            transaction_id: self.manifest.transaction_id().clone(),
            state: self.machine.state(),
            manifest_sha256: self.manifest_sha256,
            source_sha256: self.manifest.expected_source_sha256(),
            source_unchanged,
            result_artifact_id: self
                .result_sha256
                .and_then(|digest| artifact_id(digest).ok()),
            result_sha256: self.result_sha256,
            result_size: self.result_size,
            artifact_disposition: self.artifact_disposition,
        }
    }

    fn failure(
        &self,
        primary: TransactionError,
        recovery: Option<TransactionError>,
        source_unchanged: bool,
    ) -> TransactionFailure {
        TransactionFailure {
            primary,
            recovery,
            receipt: Box::new(self.receipt(source_unchanged)),
        }
    }
}

impl fmt::Debug for WorkspaceTransaction {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("WorkspaceTransaction")
            .field("state", &self.machine.state())
            .field("limits", &self.limits)
            .field("artifact_disposition", &self.artifact_disposition)
            .finish_non_exhaustive()
    }
}

fn artifact_id(digest: [u8; 32]) -> Result<ArtifactId, TransactionError> {
    ArtifactId::parse(format!("sha256-{}", hex::encode(digest)))
        .map_err(|_| TransactionError::ReceiptSerialization)
}

fn map_workspace(error: WorkspaceError) -> TransactionError {
    match error {
        WorkspaceError::ArtifactExists => TransactionError::ArtifactExists,
        WorkspaceError::ArtifactPublishedIncomplete => TransactionError::ArtifactOutcomeIncomplete,
        WorkspaceError::InvalidRelativePath
        | WorkspaceError::EscapesWorkspace
        | WorkspaceError::LinkNotAllowed => TransactionError::WorkspaceFailure,
        WorkspaceError::Io(inner) => {
            drop(inner);
            TransactionError::WorkspaceFailure
        }
    }
}

fn reject_source_link(path: &Path) -> Result<(), TransactionError> {
    let metadata = fs::symlink_metadata(path).map_err(|_| TransactionError::InvalidSource)?;
    if metadata.file_type().is_symlink() || has_windows_reparse_point(&metadata) {
        return Err(TransactionError::InvalidSource);
    }
    Ok(())
}

#[cfg(windows)]
fn has_windows_reparse_point(metadata: &fs::Metadata) -> bool {
    use std::os::windows::fs::MetadataExt as _;

    const FILE_ATTRIBUTE_REPARSE_POINT: u32 = 0x400;
    metadata.file_attributes() & FILE_ATTRIBUTE_REPARSE_POINT != 0
}

#[cfg(not(windows))]
const fn has_windows_reparse_point(_metadata: &fs::Metadata) -> bool {
    false
}
