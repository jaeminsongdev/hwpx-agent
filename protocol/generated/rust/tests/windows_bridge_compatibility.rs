use hwpx_agent_protocol::foundation::v1::{ArtifactRef, ValidationState};
use hwpx_agent_protocol::windows_bridge::v1::{
    AgentLeaseRequest, ExecutionState, SecurityPolicy, StaCommandEnvelope, StaCommandReceipt,
    StaEventRecord, StaEventType, StaExecutePlanCommand, StaOpenDocumentCommand, StagedArtifactRef,
    TargetProfileIdentity, sta_command_envelope,
};
use hwpx_agent_protocol::windows_bridge_validation::{
    MAX_WINDOWS_BRIDGE_FRAME_BYTES, WindowsBridgeValidationError, decode_and_validate_sta_command,
    validate_agent_lease_request, validate_sta_command, validate_sta_receipt,
};
use prost::Message;
use prost_types::FileDescriptorSet;
use sha2::{Digest, Sha256};

const FOUNDATION_DESCRIPTOR_SHA256: &str =
    "174f4c25fd24bdb323c29658b10939365964acffc8cbf4a7d236d1d6842a666e";
const OPEN_COMMAND_VECTOR_HEX: &str = "08011a2430303030303030302d303030302d343030302d383030302d303030303030303030303031222430303030303030302d303030302d343030302d383030302d30303030303030303030303228073080a0f1c2b1343a2430303030303030302d303030302d343030302d383030302d303030303030303030303033aa01770a640a540a0d666978747572652d696e70757412406363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636318d23e120a696e7075745f303030311801120f66696c652e6c6f63616c5f72656164";

fn digest(character: char) -> String {
    std::iter::repeat_n(character, 64).collect()
}

fn target_profile() -> TargetProfileIdentity {
    TargetProfileIdentity {
        profile_id: "hancom-hangul-2020-secondary".to_owned(),
        product_build: "11.0.0.9136".to_owned(),
        locale: "ko-KR".to_owned(),
        process_architecture: "x86".to_owned(),
        executable_sha256: digest('a'),
        environment_digest: digest('b'),
    }
}

fn staged_input() -> StagedArtifactRef {
    StagedArtifactRef {
        artifact: Some(ArtifactRef {
            artifact_id: "fixture-input".to_owned(),
            sha256: digest('c'),
            size_bytes: 8_018,
        }),
        sandbox_handle: "input_0001".to_owned(),
        read_only: true,
    }
}

fn open_envelope() -> StaCommandEnvelope {
    StaCommandEnvelope {
        protocol_major: 1,
        protocol_minor: 0,
        session_id: "00000000-0000-4000-8000-000000000001".to_owned(),
        command_id: "00000000-0000-4000-8000-000000000002".to_owned(),
        fencing_token: 7,
        deadline_unix_ms: 1_800_000_000_000,
        trace_id: "00000000-0000-4000-8000-000000000003".to_owned(),
        command: Some(sta_command_envelope::Command::OpenDocument(
            StaOpenDocumentCommand {
                input: Some(staged_input()),
                open_policy_id: "file.local_read".to_owned(),
            },
        )),
    }
}

#[test]
fn foundation_v1_descriptor_remains_byte_locked() {
    let bytes = include_bytes!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../descriptor/hwpx-agent-foundation.pb"
    ));
    assert_eq!(
        hex::encode(Sha256::digest(bytes)),
        FOUNDATION_DESCRIPTOR_SHA256
    );
}

#[test]
fn descriptor_declares_exact_outbound_service_and_local_envelopes() {
    let bytes = include_bytes!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../descriptor/hwpx-agent-windows-bridge.pb"
    ));
    let descriptors = FileDescriptorSet::decode(bytes.as_slice())
        .unwrap_or_else(|error| panic!("bridge descriptor must decode: {error}"));
    let bridge = descriptors
        .file
        .iter()
        .find(|file| file.package.as_deref() == Some("hwpx_agent.windows_bridge.v1"))
        .unwrap_or_else(|| panic!("bridge package descriptor missing"));
    assert_eq!(
        bridge.dependency,
        ["hwpx_agent/foundation/v1/foundation.proto"]
    );
    let service = bridge
        .service
        .iter()
        .find(|service| service.name.as_deref() == Some("WindowsAgentControl"))
        .unwrap_or_else(|| panic!("WindowsAgentControl descriptor missing"));
    let methods = service
        .method
        .iter()
        .filter_map(|method| method.name.as_deref())
        .collect::<Vec<_>>();
    assert_eq!(
        methods,
        [
            "AcquireLease",
            "Heartbeat",
            "CommitExecution",
            "ReportProbe"
        ]
    );
    for message in [
        "StaCommandEnvelope",
        "StaCommandReceipt",
        "StagedArtifactRef",
    ] {
        assert!(
            bridge
                .message_type
                .iter()
                .any(|descriptor| descriptor.name.as_deref() == Some(message)),
            "missing {message}"
        );
    }
}

#[test]
fn fixed_open_command_has_stable_wire_bytes_and_roundtrips() {
    let envelope = open_envelope();
    validate_sta_command(&envelope).unwrap_or_else(|error| panic!("valid command: {error}"));
    let bytes = envelope.encode_to_vec();
    assert_eq!(hex::encode(&bytes), OPEN_COMMAND_VECTOR_HEX);
    let decoded = decode_and_validate_sta_command(&bytes)
        .unwrap_or_else(|error| panic!("fixed vector must decode: {error}"));
    assert_eq!(decoded, envelope);
}

#[test]
fn command_boundary_rejects_paths_raw_actions_versions_and_missing_authority() {
    let mut candidate = open_envelope();
    candidate.protocol_major = 2;
    assert_eq!(
        validate_sta_command(&candidate),
        Err(WindowsBridgeValidationError::ProtocolVersion)
    );

    let mut candidate = open_envelope();
    candidate.fencing_token = 0;
    assert_eq!(
        validate_sta_command(&candidate),
        Err(WindowsBridgeValidationError::InvalidFencingToken)
    );

    let mut candidate = open_envelope();
    candidate.session_id = "AAAAAAAA-AAAA-4AAA-8AAA-AAAAAAAAAAAA".to_owned();
    assert_eq!(
        validate_sta_command(&candidate),
        Err(WindowsBridgeValidationError::InvalidIdentifier)
    );

    let mut candidate = open_envelope();
    candidate.command = None;
    assert_eq!(
        validate_sta_command(&candidate),
        Err(WindowsBridgeValidationError::MissingCommand)
    );

    let mut candidate = open_envelope();
    if let Some(sta_command_envelope::Command::OpenDocument(command)) = &mut candidate.command {
        command
            .input
            .as_mut()
            .unwrap_or_else(|| panic!("fixture input missing"))
            .sandbox_handle = "../user-document.hwpx".to_owned();
    }
    assert_eq!(
        validate_sta_command(&candidate),
        Err(WindowsBridgeValidationError::UnsafeSandboxHandle)
    );

    let mut candidate = open_envelope();
    candidate.command = Some(sta_command_envelope::Command::ExecutePlan(
        StaExecutePlanCommand {
            operation_plan: Some(staged_input()),
            binding_bundle_id: "haction.run".to_owned(),
            binding_bundle_sha256: digest('d'),
        },
    ));
    assert_eq!(
        validate_sta_command(&candidate),
        Err(WindowsBridgeValidationError::ForbiddenRawAutomation)
    );

    assert_eq!(
        decode_and_validate_sta_command(&vec![0; MAX_WINDOWS_BRIDGE_FRAME_BYTES + 1]),
        Err(WindowsBridgeValidationError::WireLimit)
    );
}

#[test]
fn lease_and_success_receipt_require_bounded_private_shapes() {
    let request = AgentLeaseRequest {
        protocol_major: 1,
        protocol_minor: 0,
        agent_instance_id: "00000000-0000-4000-8000-000000000004".to_owned(),
        target_profile: Some(target_profile()),
        capability_registry_sha256: digest('e'),
        available_job_slots: 1,
        observed_at_unix_ms: 1_800_000_000_000,
        nonce_sha256: digest('f'),
    };
    validate_agent_lease_request(&request)
        .unwrap_or_else(|error| panic!("valid lease request: {error}"));

    let mut unsafe_request = request;
    unsafe_request.available_job_slots = 17;
    assert_eq!(
        validate_agent_lease_request(&unsafe_request),
        Err(WindowsBridgeValidationError::InvalidLimit)
    );

    let receipt = StaCommandReceipt {
        protocol_major: 1,
        protocol_minor: 0,
        session_id: "00000000-0000-4000-8000-000000000001".to_owned(),
        command_id: "00000000-0000-4000-8000-000000000002".to_owned(),
        fencing_token: 7,
        state: ExecutionState::Succeeded.into(),
        outputs: vec![StagedArtifactRef {
            artifact: Some(ArtifactRef {
                artifact_id: "fixture-output".to_owned(),
                sha256: digest('1'),
                size_bytes: 8_100,
            }),
            sandbox_handle: "output_0001".to_owned(),
            read_only: false,
        }],
        validation_state: ValidationState::Passed.into(),
        events: vec![StaEventRecord {
            sequence: 1,
            event_type: StaEventType::CleanupCompleted.into(),
            recorded_at_unix_ms: 1_800_000_000_001,
            safe_metadata_sha256: digest('2'),
        }],
        diagnostic: None,
        input_unchanged: true,
        raw_document_content_logged: false,
        external_network_invoked: false,
        registry_or_system_setting_changed: false,
        cleanup_required: false,
    };
    validate_sta_receipt(&receipt).unwrap_or_else(|error| panic!("valid receipt: {error}"));

    let mut unsafe_receipt = receipt;
    unsafe_receipt.raw_document_content_logged = true;
    assert_eq!(
        validate_sta_receipt(&unsafe_receipt),
        Err(WindowsBridgeValidationError::UnsafeSuccessReceipt)
    );

    let mut unknown_event_receipt = unsafe_receipt;
    unknown_event_receipt.raw_document_content_logged = false;
    unknown_event_receipt.events[0].event_type = 99;
    assert_eq!(
        validate_sta_receipt(&unknown_event_receipt),
        Err(WindowsBridgeValidationError::InvalidState)
    );
}

#[test]
fn security_policy_is_typed_and_contains_no_generic_action_field() {
    let policy = SecurityPolicy {
        allow_external_network: false,
        allow_clipboard: false,
        allow_macros: false,
        allow_ole_activation: false,
        file_access_policy_id: "file.local_read".to_owned(),
        modal_policy_id: "modal.fail_closed".to_owned(),
    };
    assert!(!policy.allow_external_network);

    let descriptor_text = include_str!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../proto/hwpx_agent/windows_bridge/v1/windows_bridge.proto"
    ));
    assert!(!descriptor_text.contains("string action"));
    assert!(!descriptor_text.contains("map<string"));
    assert!(!descriptor_text.contains("bytes payload"));
}
