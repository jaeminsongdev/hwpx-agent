use std::fmt;

use prost::Message;

use crate::foundation::v1::{ArtifactRef, ValidationState};
use crate::windows_bridge::v1::{
    AgentLeaseRequest, BridgeErrorCode, ExecutionState, LeaseAssignment, ResourceLimits,
    SecurityPolicy, StaCommandEnvelope, StaCommandReceipt, StaEventType, StagedArtifactRef,
    TargetProfileIdentity, sta_command_envelope,
};

pub const WINDOWS_BRIDGE_PROTOCOL_MAJOR: u32 = 1;
pub const WINDOWS_BRIDGE_PROTOCOL_MINOR: u32 = 0;
pub const MAX_WINDOWS_BRIDGE_FRAME_BYTES: usize = 1_048_576;

const MAX_ARTIFACT_BYTES: u64 = 1_073_741_824;
const MIN_MEMORY_BYTES: u64 = 67_108_864;
const MAX_MEMORY_BYTES: u64 = 17_179_869_184;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum WindowsBridgeValidationError {
    WireLimit,
    Decode,
    ProtocolVersion,
    MissingField,
    InvalidIdentifier,
    InvalidDigest,
    InvalidArtifact,
    UnsafeSandboxHandle,
    InvalidFencingToken,
    InvalidDeadline,
    InvalidLimit,
    MissingCommand,
    ForbiddenRawAutomation,
    InvalidState,
    InvalidEventSequence,
    UnsafeSuccessReceipt,
}

impl fmt::Display for WindowsBridgeValidationError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(match self {
            Self::WireLimit => "windows bridge wire limit exceeded",
            Self::Decode => "windows bridge protobuf rejected",
            Self::ProtocolVersion => "windows bridge protocol version rejected",
            Self::MissingField => "windows bridge required field missing",
            Self::InvalidIdentifier => "windows bridge identifier rejected",
            Self::InvalidDigest => "windows bridge digest rejected",
            Self::InvalidArtifact => "windows bridge artifact rejected",
            Self::UnsafeSandboxHandle => "windows bridge sandbox handle rejected",
            Self::InvalidFencingToken => "windows bridge fencing token rejected",
            Self::InvalidDeadline => "windows bridge deadline rejected",
            Self::InvalidLimit => "windows bridge resource limit rejected",
            Self::MissingCommand => "windows bridge command missing",
            Self::ForbiddenRawAutomation => "windows bridge raw automation rejected",
            Self::InvalidState => "windows bridge state rejected",
            Self::InvalidEventSequence => "windows bridge event sequence rejected",
            Self::UnsafeSuccessReceipt => "windows bridge success receipt rejected",
        })
    }
}

impl std::error::Error for WindowsBridgeValidationError {}

/// Decodes one bounded named-pipe frame and validates its complete typed envelope.
///
/// # Errors
///
/// Returns a stable validation category when the frame is oversized, malformed, unsupported, or
/// fails any authority, artifact, policy, or command invariant.
pub fn decode_and_validate_sta_command(
    bytes: &[u8],
) -> Result<StaCommandEnvelope, WindowsBridgeValidationError> {
    if bytes.len() > MAX_WINDOWS_BRIDGE_FRAME_BYTES {
        return Err(WindowsBridgeValidationError::WireLimit);
    }
    let envelope =
        StaCommandEnvelope::decode(bytes).map_err(|_| WindowsBridgeValidationError::Decode)?;
    validate_sta_command(&envelope)?;
    Ok(envelope)
}

/// Validates the outbound Windows Agent lease request before transport.
///
/// # Errors
///
/// Returns a stable validation category for an unsupported version, invalid identity/digest, absent
/// target profile, stale timestamp shape, or an out-of-range slot count.
pub fn validate_agent_lease_request(
    request: &AgentLeaseRequest,
) -> Result<(), WindowsBridgeValidationError> {
    validate_version(request.protocol_major, request.protocol_minor)?;
    require_uuid(&request.agent_instance_id)?;
    validate_target_profile(
        request
            .target_profile
            .as_ref()
            .ok_or(WindowsBridgeValidationError::MissingField)?,
    )?;
    require_digest(&request.capability_registry_sha256)?;
    if !(1..=16).contains(&request.available_job_slots) || request.observed_at_unix_ms == 0 {
        return Err(WindowsBridgeValidationError::InvalidLimit);
    }
    require_digest(&request.nonce_sha256)
}

/// Validates a complete lease assignment before any artifact is staged or worker is spawned.
///
/// # Errors
///
/// Returns a stable validation category when authority, fencing, expiry, artifacts, limits, or
/// security policy are missing or invalid.
pub fn validate_lease_assignment(
    assignment: &LeaseAssignment,
) -> Result<(), WindowsBridgeValidationError> {
    for value in [
        &assignment.lease_id,
        &assignment.request_id,
        &assignment.job_id,
        &assignment.trace_id,
        &assignment.execution_id,
    ] {
        require_uuid(value)?;
    }
    if assignment.fencing_token == 0 {
        return Err(WindowsBridgeValidationError::InvalidFencingToken);
    }
    if assignment.expires_at_unix_ms == 0 {
        return Err(WindowsBridgeValidationError::InvalidDeadline);
    }
    require_token(&assignment.target_profile_id, 3, 127)?;
    for artifact in [
        assignment.input.as_ref(),
        assignment.operation_plan.as_ref(),
        assignment.validation_contract.as_ref(),
    ] {
        let artifact = artifact.ok_or(WindowsBridgeValidationError::MissingField)?;
        validate_staged_artifact(artifact)?;
        if !artifact.read_only {
            return Err(WindowsBridgeValidationError::InvalidArtifact);
        }
    }
    validate_resource_limits(
        assignment
            .resource_limits
            .as_ref()
            .ok_or(WindowsBridgeValidationError::MissingField)?,
    )?;
    validate_security_policy(
        assignment
            .security_policy
            .as_ref()
            .ok_or(WindowsBridgeValidationError::MissingField)?,
    )
}

/// Validates one already-decoded Agent-to-STA command envelope.
///
/// # Errors
///
/// Returns a stable validation category when the command is not the exact v1 typed union or contains
/// invalid authority, path-like handles, raw automation names, or incomplete command data.
pub fn validate_sta_command(
    envelope: &StaCommandEnvelope,
) -> Result<(), WindowsBridgeValidationError> {
    validate_version(envelope.protocol_major, envelope.protocol_minor)?;
    require_uuid(&envelope.session_id)?;
    require_uuid(&envelope.command_id)?;
    require_uuid(&envelope.trace_id)?;
    if envelope.fencing_token == 0 {
        return Err(WindowsBridgeValidationError::InvalidFencingToken);
    }
    if envelope.deadline_unix_ms == 0 {
        return Err(WindowsBridgeValidationError::InvalidDeadline);
    }

    match envelope
        .command
        .as_ref()
        .ok_or(WindowsBridgeValidationError::MissingCommand)?
    {
        sta_command_envelope::Command::StartSession(command) => {
            validate_target_profile(
                command
                    .target_profile
                    .as_ref()
                    .ok_or(WindowsBridgeValidationError::MissingField)?,
            )?;
            require_digest(&command.capability_registry_sha256)?;
            validate_security_policy(
                command
                    .security_policy
                    .as_ref()
                    .ok_or(WindowsBridgeValidationError::MissingField)?,
            )
        }
        sta_command_envelope::Command::OpenDocument(command) => {
            let input = command
                .input
                .as_ref()
                .ok_or(WindowsBridgeValidationError::MissingField)?;
            validate_staged_artifact(input)?;
            if !input.read_only {
                return Err(WindowsBridgeValidationError::InvalidArtifact);
            }
            require_semantic_id(&command.open_policy_id)
        }
        sta_command_envelope::Command::ExecutePlan(command) => {
            let plan = command
                .operation_plan
                .as_ref()
                .ok_or(WindowsBridgeValidationError::MissingField)?;
            validate_staged_artifact(plan)?;
            if !plan.read_only {
                return Err(WindowsBridgeValidationError::InvalidArtifact);
            }
            require_no_raw_automation(&command.binding_bundle_id)?;
            require_semantic_id(&command.binding_bundle_id)?;
            require_digest(&command.binding_bundle_sha256)
        }
        sta_command_envelope::Command::SaveDocument(command) => {
            require_handle(&command.output_slot)?;
            require_semantic_id(&command.format_id)
        }
        sta_command_envelope::Command::RenderDocument(command) => {
            require_handle(&command.output_slot)?;
            require_semantic_id(&command.render_profile_id)
        }
        sta_command_envelope::Command::CloseSession(command) => {
            if !command.discard_unsaved_changes {
                return Err(WindowsBridgeValidationError::UnsafeSuccessReceipt);
            }
            Ok(())
        }
        sta_command_envelope::Command::Cancel(command) => require_uuid(&command.target_command_id),
    }
}

/// Validates a bounded STA receipt before it can be correlated with a lease or committed.
///
/// # Errors
///
/// Returns a stable validation category for invalid authority/state, artifacts, event ordering,
/// diagnostics, or a success claim that reports an unsafe side effect.
pub fn validate_sta_receipt(
    receipt: &StaCommandReceipt,
) -> Result<(), WindowsBridgeValidationError> {
    validate_version(receipt.protocol_major, receipt.protocol_minor)?;
    require_uuid(&receipt.session_id)?;
    require_uuid(&receipt.command_id)?;
    if receipt.fencing_token == 0 {
        return Err(WindowsBridgeValidationError::InvalidFencingToken);
    }
    let state = ExecutionState::try_from(receipt.state)
        .map_err(|_| WindowsBridgeValidationError::InvalidState)?;
    if matches!(
        state,
        ExecutionState::Unspecified | ExecutionState::Accepted
    ) {
        return Err(WindowsBridgeValidationError::InvalidState);
    }
    if receipt.outputs.len() > 64 || receipt.events.len() > 1_024 {
        return Err(WindowsBridgeValidationError::InvalidLimit);
    }
    for output in &receipt.outputs {
        validate_staged_artifact(output)?;
        if output.read_only {
            return Err(WindowsBridgeValidationError::InvalidArtifact);
        }
    }
    let validation_state = ValidationState::try_from(receipt.validation_state)
        .map_err(|_| WindowsBridgeValidationError::InvalidState)?;
    if validation_state == ValidationState::Unspecified {
        return Err(WindowsBridgeValidationError::InvalidState);
    }
    for (index, event) in receipt.events.iter().enumerate() {
        let expected = u32::try_from(index + 1)
            .map_err(|_| WindowsBridgeValidationError::InvalidEventSequence)?;
        if event.sequence != expected || event.recorded_at_unix_ms == 0 {
            return Err(WindowsBridgeValidationError::InvalidEventSequence);
        }
        let event_type = StaEventType::try_from(event.event_type)
            .map_err(|_| WindowsBridgeValidationError::InvalidState)?;
        if event_type == StaEventType::Unspecified {
            return Err(WindowsBridgeValidationError::InvalidState);
        }
        if event.safe_metadata_sha256.is_empty() {
            continue;
        }
        require_digest(&event.safe_metadata_sha256)?;
    }
    if let Some(diagnostic) = &receipt.diagnostic {
        let error_code = BridgeErrorCode::try_from(diagnostic.error_code)
            .map_err(|_| WindowsBridgeValidationError::InvalidState)?;
        if error_code == BridgeErrorCode::Unspecified {
            return Err(WindowsBridgeValidationError::InvalidState);
        }
        require_digest(&diagnostic.safe_detail_sha256)?;
    }
    if state == ExecutionState::Succeeded
        && (receipt.diagnostic.is_some()
            || validation_state != ValidationState::Passed
            || !receipt.input_unchanged
            || receipt.raw_document_content_logged
            || receipt.external_network_invoked
            || receipt.registry_or_system_setting_changed)
    {
        return Err(WindowsBridgeValidationError::UnsafeSuccessReceipt);
    }
    Ok(())
}

fn validate_version(major: u32, minor: u32) -> Result<(), WindowsBridgeValidationError> {
    if major == WINDOWS_BRIDGE_PROTOCOL_MAJOR && minor == WINDOWS_BRIDGE_PROTOCOL_MINOR {
        Ok(())
    } else {
        Err(WindowsBridgeValidationError::ProtocolVersion)
    }
}

fn validate_target_profile(
    target: &TargetProfileIdentity,
) -> Result<(), WindowsBridgeValidationError> {
    require_token(&target.profile_id, 3, 127)?;
    require_token(&target.product_build, 3, 63)?;
    require_token(&target.locale, 2, 31)?;
    require_token(&target.process_architecture, 2, 31)?;
    require_digest(&target.executable_sha256)?;
    require_digest(&target.environment_digest)
}

fn validate_resource_limits(limits: &ResourceLimits) -> Result<(), WindowsBridgeValidationError> {
    if !(1..=900).contains(&limits.command_timeout_seconds)
        || limits.job_timeout_seconds < limits.command_timeout_seconds
        || limits.job_timeout_seconds > 3_600
        || !(MIN_MEMORY_BYTES..=MAX_MEMORY_BYTES).contains(&limits.memory_limit_bytes)
        || limits.max_output_bytes == 0
        || limits.max_output_bytes > MAX_ARTIFACT_BYTES
        || !(1..=10_000).contains(&limits.max_event_count)
    {
        return Err(WindowsBridgeValidationError::InvalidLimit);
    }
    Ok(())
}

fn validate_security_policy(policy: &SecurityPolicy) -> Result<(), WindowsBridgeValidationError> {
    require_semantic_id(&policy.file_access_policy_id)?;
    require_semantic_id(&policy.modal_policy_id)
}

fn validate_staged_artifact(
    staged: &StagedArtifactRef,
) -> Result<(), WindowsBridgeValidationError> {
    validate_artifact(
        staged
            .artifact
            .as_ref()
            .ok_or(WindowsBridgeValidationError::MissingField)?,
    )?;
    require_handle(&staged.sandbox_handle)
}

fn validate_artifact(artifact: &ArtifactRef) -> Result<(), WindowsBridgeValidationError> {
    if !is_artifact_id(&artifact.artifact_id)
        || !is_digest(&artifact.sha256)
        || artifact.size_bytes == 0
        || artifact.size_bytes > MAX_ARTIFACT_BYTES
    {
        return Err(WindowsBridgeValidationError::InvalidArtifact);
    }
    Ok(())
}

fn require_uuid(value: &str) -> Result<(), WindowsBridgeValidationError> {
    let bytes = value.as_bytes();
    let valid = bytes.len() == 36
        && [8, 13, 18, 23].iter().all(|index| bytes[*index] == b'-')
        && bytes.iter().enumerate().all(|(index, byte)| {
            [8, 13, 18, 23].contains(&index)
                || byte.is_ascii_digit()
                || (b'a'..=b'f').contains(byte)
        });
    if valid {
        Ok(())
    } else {
        Err(WindowsBridgeValidationError::InvalidIdentifier)
    }
}

fn require_digest(value: &str) -> Result<(), WindowsBridgeValidationError> {
    if is_digest(value) {
        Ok(())
    } else {
        Err(WindowsBridgeValidationError::InvalidDigest)
    }
}

fn require_handle(value: &str) -> Result<(), WindowsBridgeValidationError> {
    let valid = (3..=64).contains(&value.len())
        && value
            .bytes()
            .next()
            .is_some_and(|byte| byte.is_ascii_lowercase())
        && value.bytes().all(|byte| {
            byte.is_ascii_lowercase() || byte.is_ascii_digit() || matches!(byte, b'_' | b'-')
        });
    if valid {
        Ok(())
    } else {
        Err(WindowsBridgeValidationError::UnsafeSandboxHandle)
    }
}

fn require_semantic_id(value: &str) -> Result<(), WindowsBridgeValidationError> {
    require_no_raw_automation(value)?;
    let mut segments = value.split('.');
    let first = segments.next().is_some_and(is_identifier_segment);
    let mut count = 0usize;
    let remaining = segments.all(|segment| {
        count += 1;
        is_identifier_segment(segment)
    });
    if first && remaining && count > 0 && value.len() <= 127 {
        Ok(())
    } else {
        Err(WindowsBridgeValidationError::InvalidIdentifier)
    }
}

fn require_no_raw_automation(value: &str) -> Result<(), WindowsBridgeValidationError> {
    if value.contains("haction") || value.contains("parameterset") {
        Err(WindowsBridgeValidationError::ForbiddenRawAutomation)
    } else {
        Ok(())
    }
}

fn require_token(
    value: &str,
    minimum: usize,
    maximum: usize,
) -> Result<(), WindowsBridgeValidationError> {
    let valid = (minimum..=maximum).contains(&value.len())
        && value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'.' | b'_' | b'-'));
    if valid {
        Ok(())
    } else {
        Err(WindowsBridgeValidationError::InvalidIdentifier)
    }
}

fn is_identifier_segment(value: &str) -> bool {
    value
        .bytes()
        .next()
        .is_some_and(|byte| byte.is_ascii_lowercase())
        && value.bytes().all(|byte| {
            byte.is_ascii_lowercase() || byte.is_ascii_digit() || matches!(byte, b'_' | b'-')
        })
}

fn is_artifact_id(value: &str) -> bool {
    (3..=128).contains(&value.len())
        && value
            .bytes()
            .next()
            .is_some_and(|byte| byte.is_ascii_lowercase() || byte.is_ascii_digit())
        && value.bytes().all(|byte| {
            byte.is_ascii_lowercase() || byte.is_ascii_digit() || matches!(byte, b'.' | b'_' | b'-')
        })
}

fn is_digest(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}
