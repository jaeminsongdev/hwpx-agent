use std::fmt;

use local_sync::{
    CheckpointRequest, CheckpointServiceContext, Connectivity, LocalMirror, PullRequest,
    PushRequest, RemoteFailure, RemoteHead, RemoteSyncPort, SyncError,
    decode_checkpoint_to_service, map_checkpoint_to_service,
};
use serde_json::Value;
use sha2::{Digest as _, Sha256};

type TestResult = Result<(), Box<dyn std::error::Error>>;

#[derive(Default)]
struct CapturePort {
    checkpoint: Option<CheckpointRequest>,
}

impl fmt::Debug for CapturePort {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CapturePort")
            .field("has_checkpoint", &self.checkpoint.is_some())
            .finish()
    }
}

impl RemoteSyncPort for CapturePort {
    fn pull(
        &mut self,
        _request: &PullRequest,
    ) -> Result<local_sync::RemoteSnapshot, RemoteFailure> {
        Err(RemoteFailure::Unavailable)
    }

    fn push(
        &mut self,
        _request: &PushRequest,
    ) -> Result<local_sync::RemotePushReceipt, RemoteFailure> {
        Err(RemoteFailure::Unavailable)
    }

    fn checkpoint(
        &mut self,
        request: &CheckpointRequest,
    ) -> Result<local_sync::RemoteCheckpointReceipt, RemoteFailure> {
        self.checkpoint = Some(request.clone());
        Err(RemoteFailure::Unavailable)
    }
}

fn digest(byte: u8) -> String {
    hex::encode(Sha256::digest([byte]))
}

fn request(note: Option<&str>) -> Result<CheckpointRequest, SyncError> {
    request_for("mir_mirror001", note)
}

fn request_for(mirror_id: &str, note: Option<&str>) -> Result<CheckpointRequest, SyncError> {
    let mut mirror = LocalMirror::new(
        "prj_project01".to_owned(),
        "brn_branch001".to_owned(),
        mirror_id.to_owned(),
        RemoteHead::new(Some("rev_revision01".to_owned()), 7)?,
        digest(1),
        Connectivity::Online,
    )?;
    let mut port = CapturePort::default();
    assert_eq!(
        mirror.checkpoint(
            &mut port,
            "checkpoint-key-0001".to_owned(),
            "Reviewed baseline".to_owned(),
            note.map(str::to_owned),
        ),
        Err(SyncError::RemoteUnavailable)
    );
    port.checkpoint.ok_or(SyncError::InvalidState)
}

fn public_checkpoint_schema() -> Result<Value, Box<dyn std::error::Error>> {
    let path = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../../protocol/mcp/p15-public-tools-v1.json");
    let catalog: Value = serde_json::from_slice(&std::fs::read(path)?)?;
    catalog["tools"]
        .as_array()
        .and_then(|tools| {
            tools
                .iter()
                .find(|tool| tool["name"] == "project_checkpoint")
        })
        .and_then(|tool| tool.get("inputSchema"))
        .cloned()
        .ok_or_else(|| "project_checkpoint schema missing".into())
}

#[test]
fn exact_mapping_matches_p15_schema_and_retains_private_binding() -> TestResult {
    let request = request(Some("Local operator note"))?;
    let context = CheckpointServiceContext::new("req_checkpoint01".to_owned(), "ko-KR".to_owned())?;
    let binding = map_checkpoint_to_service(&request, &context)?;
    let arguments: Value = serde_json::from_slice(&binding.arguments().encoded()?)?;
    let validator = jsonschema::validator_for(&public_checkpoint_schema()?)?;

    assert!(validator.is_valid(&arguments));
    assert_eq!(arguments["client_surface"], "codex_local");
    assert_eq!(arguments["locale"], "ko-KR");
    assert_eq!(arguments["request_id"], "req_checkpoint01");
    assert_eq!(arguments["project_id"], "prj_project01");
    assert_eq!(arguments["expected_revision"], "rev_revision01");
    assert_eq!(arguments["revision_id"], "rev_revision01");
    assert_eq!(arguments["label"], "Reviewed baseline");
    assert_eq!(arguments["note"], "Local operator note");
    assert_eq!(binding.branch_id(), "brn_branch001");
    assert_eq!(binding.mirror_id(), "mir_mirror001");
    assert_eq!(binding.expected_generation(), 7);
    assert_eq!(binding.private_request_sha256().len(), 64);
    assert_eq!(binding.service_intent_sha256().len(), 64);
    assert_eq!(binding.service_arguments_sha256().len(), 64);
    assert_eq!(
        binding.service_arguments_sha256(),
        hex::encode(Sha256::digest(binding.arguments().encoded()?))
    );
    Ok(())
}

#[test]
fn absent_note_is_omitted_and_private_key_maps_stably() -> TestResult {
    let request = request(None)?;
    let first = map_checkpoint_to_service(
        &request,
        &CheckpointServiceContext::new("req_checkpoint01".to_owned(), "ko-KR".to_owned())?,
    )?;
    let second = map_checkpoint_to_service(
        &request,
        &CheckpointServiceContext::new("req_checkpoint02".to_owned(), "en-US".to_owned())?,
    )?;
    let value: Value = serde_json::from_slice(&first.arguments().encoded()?)?;

    assert!(value.get("note").is_none());
    assert_eq!(
        first.arguments().idempotency_key(),
        second.arguments().idempotency_key()
    );
    assert_eq!(
        first.service_intent_sha256(),
        second.service_intent_sha256()
    );
    assert_ne!(
        first.service_arguments_sha256(),
        second.service_arguments_sha256()
    );
    let other_mirror = request_for("mir_mirror002", None)?;
    let other = map_checkpoint_to_service(
        &other_mirror,
        &CheckpointServiceContext::new("req_checkpoint03".to_owned(), "ko-KR".to_owned())?,
    )?;
    assert_ne!(
        first.arguments().idempotency_key(),
        other.arguments().idempotency_key()
    );
    Ok(())
}

#[test]
fn mapping_debug_and_validation_fail_closed() -> TestResult {
    let request = request(Some("SECRET CHECKPOINT NOTE"))?;
    let context = CheckpointServiceContext::new("req_checkpoint01".to_owned(), "ko-KR".to_owned())?;
    let binding = map_checkpoint_to_service(&request, &context)?;
    let debug = format!("{binding:?} {context:?}");

    for secret in [
        "SECRET CHECKPOINT NOTE",
        "Reviewed baseline",
        "prj_project01",
        "brn_branch001",
        "mir_mirror001",
        "checkpoint-key-0001",
        binding.private_request_sha256(),
        binding.service_intent_sha256(),
        binding.service_arguments_sha256(),
    ] {
        assert!(!debug.contains(secret));
    }
    for (request_id, locale) in [
        ("req_short", "ko-KR"),
        ("req_checkpoint01", "KO-kr"),
        ("req_checkpoint01", "ko-KR-extra"),
        ("req_checkpoint01", "ko-한국"),
    ] {
        assert_eq!(
            CheckpointServiceContext::new(request_id.to_owned(), locale.to_owned()),
            Err(SyncError::InvalidRequest)
        );
    }
    Ok(())
}

#[test]
fn exact_private_decoder_rejects_alternate_or_ambiguous_json() -> TestResult {
    let context = CheckpointServiceContext::new("req_checkpoint01".to_owned(), "ko-KR".to_owned())?;
    let exact = br#"{"schema_version":"hwpx-agent.remote-sync-request/v3","operation":"checkpoint","project_id":"prj_project01","branch_id":"brn_branch001","mirror_id":"mir_mirror001","expected_head":{"revision_id":"rev_revision01","generation":7},"idempotency_key":"checkpoint-key-0001","label":"Reviewed baseline"}"#;
    let binding = decode_checkpoint_to_service(exact, &context)?;
    assert_eq!(binding.expected_generation(), 7);
    assert_eq!(binding.arguments().label(), "Reviewed baseline");

    let candidates: &[&[u8]] = &[
        b"",
        br#"{"schema_version":"hwpx-agent.remote-sync-request/v2","operation":"checkpoint","project_id":"prj_project01","branch_id":"brn_branch001","mirror_id":"mir_mirror001","expected_head":{"revision_id":"rev_revision01","generation":7},"idempotency_key":"checkpoint-key-0001","label":"Reviewed baseline"}"#,
        br#"{"schema_version":"hwpx-agent.remote-sync-request/v3","operation":"pull","project_id":"prj_project01","branch_id":"brn_branch001","mirror_id":"mir_mirror001","expected_head":{"revision_id":"rev_revision01","generation":7},"idempotency_key":"checkpoint-key-0001","label":"Reviewed baseline"}"#,
        br#"{"schema_version":"hwpx-agent.remote-sync-request/v3","operation":"checkpoint","project_id":"prj_project01","project_id":"prj_project02","branch_id":"brn_branch001","mirror_id":"mir_mirror001","expected_head":{"revision_id":"rev_revision01","generation":7},"idempotency_key":"checkpoint-key-0001","label":"Reviewed baseline"}"#,
        br#"{"schema_version":"hwpx-agent.remote-sync-request/v3","operation":"checkpoint","project_id":"prj_project01","branch_id":"brn_branch001","mirror_id":"mir_mirror001","expected_head":{"revision_id":"rev_revision01","generation":7},"idempotency_key":"checkpoint-key-0001","label":"Reviewed baseline","extra":true}"#,
        br#" {"schema_version":"hwpx-agent.remote-sync-request/v3","operation":"checkpoint","project_id":"prj_project01","branch_id":"brn_branch001","mirror_id":"mir_mirror001","expected_head":{"revision_id":"rev_revision01","generation":7},"idempotency_key":"checkpoint-key-0001","label":"Reviewed baseline"}"#,
        br#"{"operation":"checkpoint","schema_version":"hwpx-agent.remote-sync-request/v3","project_id":"prj_project01","branch_id":"brn_branch001","mirror_id":"mir_mirror001","expected_head":{"revision_id":"rev_revision01","generation":7},"idempotency_key":"checkpoint-key-0001","label":"Reviewed baseline"}"#,
    ];
    for candidate in candidates {
        assert_eq!(
            decode_checkpoint_to_service(candidate, &context),
            Err(SyncError::InvalidRequest)
        );
    }
    assert_eq!(
        decode_checkpoint_to_service(&vec![b' '; 16_385], &context),
        Err(SyncError::InvalidRequest)
    );
    Ok(())
}
