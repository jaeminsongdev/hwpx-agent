use std::collections::VecDeque;
use std::error::Error;
use std::fmt;

use local_sync::{
    AuthenticatedRemoteSyncAdapter, AuthorizationHeader, Connectivity, CredentialFailure,
    LocalMirror, RemoteCredentialProvider, RemoteHead, RemoteTransport, SyncError,
    TransportFailure,
};
use serde_json::{Value, json};
use sha2::{Digest as _, Sha256};

type TestResult = Result<(), Box<dyn Error>>;

struct FakeCredentials {
    headers: VecDeque<Result<String, CredentialFailure>>,
    calls: usize,
}

impl fmt::Debug for FakeCredentials {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("FakeCredentials")
            .field("remaining", &self.headers.len())
            .field("calls", &self.calls)
            .finish()
    }
}

impl RemoteCredentialProvider for FakeCredentials {
    fn authorization_header(&mut self) -> Result<AuthorizationHeader, CredentialFailure> {
        self.calls += 1;
        let value = self
            .headers
            .pop_front()
            .unwrap_or(Err(CredentialFailure::Unavailable))?;
        AuthorizationHeader::new(value)
    }
}

enum ResponsePlan {
    PullSuccess {
        revision: String,
        snapshot: String,
    },
    PushSuccess {
        revision: String,
        generation: u64,
    },
    CheckpointSuccess {
        checkpoint: String,
        revision: String,
    },
    Conflict {
        revision: String,
        generation: u64,
    },
    Rejected,
    WrongBinding,
    UnknownField,
    InvalidHead,
    Oversized,
    Transport(TransportFailure),
}

struct FakeTransport {
    plans: VecDeque<ResponsePlan>,
    requests: Vec<Value>,
    request_sha256s: Vec<String>,
    authorizations: Vec<String>,
}

impl fmt::Debug for FakeTransport {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("FakeTransport")
            .field("remaining", &self.plans.len())
            .field("request_count", &self.requests.len())
            .field("request_digest_count", &self.request_sha256s.len())
            .field("authorization_count", &self.authorizations.len())
            .finish()
    }
}

impl RemoteTransport for FakeTransport {
    fn exchange(
        &mut self,
        authorization_header: &str,
        request: &[u8],
    ) -> Result<Vec<u8>, TransportFailure> {
        let value: Value =
            serde_json::from_slice(request).map_err(|_| TransportFailure::Rejected)?;
        self.requests.push(value.clone());
        self.request_sha256s
            .push(hex::encode(Sha256::digest(request)));
        self.authorizations.push(authorization_header.to_owned());
        let plan = self
            .plans
            .pop_front()
            .unwrap_or(ResponsePlan::Transport(TransportFailure::Unavailable));
        match &plan {
            ResponsePlan::Transport(error) => return Err(*error),
            ResponsePlan::Oversized => return Ok(vec![b'x'; 65_537]),
            _ => {}
        }
        let wrong_binding = matches!(&plan, ResponsePlan::WrongBinding);
        let request_sha256 = hex::encode(Sha256::digest(request));
        let result = match plan {
            ResponsePlan::PullSuccess { revision, snapshot } => json!({
                "outcome":"succeeded",
                "head":{"revision_id":revision,"generation":2},
                "snapshot_sha256":snapshot
            }),
            ResponsePlan::PushSuccess {
                revision,
                generation,
            } => json!({
                "outcome":"succeeded",
                "head":{"revision_id":revision,"generation":generation},
                "snapshot_sha256":value["snapshot_sha256"]
            }),
            ResponsePlan::CheckpointSuccess {
                checkpoint,
                revision,
            } => json!({
                "outcome":"succeeded",
                "checkpoint_id":checkpoint,
                "revision_id":revision,
                "replayed":false
            }),
            ResponsePlan::Conflict {
                revision,
                generation,
            } => json!({
                "outcome":"conflict",
                "head":{"revision_id":revision,"generation":generation}
            }),
            ResponsePlan::Rejected | ResponsePlan::WrongBinding => {
                json!({"outcome":"rejected"})
            }
            ResponsePlan::UnknownField => json!({"outcome":"rejected","extra":true}),
            ResponsePlan::InvalidHead => json!({
                "outcome":"succeeded",
                "head":{"revision_id":"bad","generation":2},
                "snapshot_sha256":digest('b')
            }),
            ResponsePlan::Oversized | ResponsePlan::Transport(_) => unreachable!(),
        };
        let binding = if wrong_binding {
            "f".repeat(64)
        } else {
            request_sha256
        };
        serde_json::to_vec(&json!({
            "schema_version":"hwpx-agent.remote-sync-response/v1",
            "request_sha256":binding,
            "result":result
        }))
        .map_err(|_| TransportFailure::Rejected)
    }
}

fn digest(character: char) -> String {
    character.to_string().repeat(64)
}

fn head(number: u64, generation: u64) -> Result<RemoteHead, SyncError> {
    RemoteHead::new(Some(format!("rev_{number:08}")), generation)
}

fn mirror() -> Result<LocalMirror, SyncError> {
    LocalMirror::new(
        "prj_project01".to_owned(),
        "brn_branch001".to_owned(),
        "mir_mirror001".to_owned(),
        head(1, 1)?,
        digest('a'),
        Connectivity::Online,
    )
}

fn adapter(
    plans: impl IntoIterator<Item = ResponsePlan>,
) -> AuthenticatedRemoteSyncAdapter<FakeCredentials, FakeTransport> {
    AuthenticatedRemoteSyncAdapter::new(
        FakeCredentials {
            headers: [
                Ok("Bearer aaa.bbb.ccc".to_owned()),
                Ok("Bearer ddd.eee.fff".to_owned()),
                Ok("Bearer ggg.hhh.iii".to_owned()),
            ]
            .into(),
            calls: 0,
        },
        FakeTransport {
            plans: plans.into_iter().collect(),
            requests: Vec::new(),
            request_sha256s: Vec::new(),
            authorizations: Vec::new(),
        },
    )
}

#[test]
fn authenticated_adapter_maps_exact_pull_push_and_checkpoint_exchanges() -> TestResult {
    let mut mirror = mirror()?;
    let mut adapter = adapter([
        ResponsePlan::PullSuccess {
            revision: "rev_00000002".to_owned(),
            snapshot: digest('b'),
        },
        ResponsePlan::PushSuccess {
            revision: "rev_00000003".to_owned(),
            generation: 3,
        },
        ResponsePlan::CheckpointSuccess {
            checkpoint: "chk_checkpoint01".to_owned(),
            revision: "rev_00000003".to_owned(),
        },
    ]);

    mirror.pull(&mut adapter)?;
    mirror.queue_local_change(digest('c'), digest('d'))?;
    mirror.push(&mut adapter, "push-key-0001".to_owned())?;
    mirror.checkpoint(
        &mut adapter,
        "checkpoint-key-0001".to_owned(),
        "Milestone 1".to_owned(),
        Some("Operator note".to_owned()),
    )?;

    let (credentials, transport) = adapter.into_parts();
    assert_eq!(credentials.calls, 3);
    assert_eq!(
        transport.authorizations,
        [
            "Bearer aaa.bbb.ccc",
            "Bearer ddd.eee.fff",
            "Bearer ggg.hhh.iii"
        ]
    );
    assert_eq!(
        transport
            .requests
            .iter()
            .map(|value| value["operation"].as_str())
            .collect::<Vec<_>>(),
        [Some("pull"), Some("push"), Some("checkpoint")]
    );
    let push = &transport.requests[1];
    assert_eq!(push["project_id"], "prj_project01");
    assert_eq!(push["branch_id"], "brn_branch001");
    assert_eq!(push["mirror_id"], "mir_mirror001");
    assert_eq!(push["expected_head"]["generation"], 2);
    assert_eq!(push["snapshot_sha256"], digest('c'));
    assert_eq!(push["operation_plan_sha256"], digest('d'));
    let encoded = serde_json::to_string(&transport.requests)?;
    assert!(!encoded.contains("Bearer "));
    for request in &transport.requests {
        assert_eq!(
            request["schema_version"],
            "hwpx-agent.remote-sync-request/v3"
        );
        assert_eq!(request["mirror_id"], "mir_mirror001");
    }
    let checkpoint = &transport.requests[2];
    assert_eq!(checkpoint["label"], "Milestone 1");
    assert_eq!(checkpoint["note"], "Operator note");
    Ok(())
}

#[test]
fn checkpoint_without_note_omits_the_optional_wire_field() -> TestResult {
    let mut mirror = mirror()?;
    let mut adapter = adapter([ResponsePlan::CheckpointSuccess {
        checkpoint: "chk_checkpoint01".to_owned(),
        revision: "rev_00000001".to_owned(),
    }]);
    mirror.checkpoint(
        &mut adapter,
        "checkpoint-key-0001".to_owned(),
        "Milestone 1".to_owned(),
        None,
    )?;
    let (_, transport) = adapter.into_parts();
    let request = transport.requests.first().ok_or("missing request")?;
    assert_eq!(
        request["schema_version"],
        "hwpx-agent.remote-sync-request/v3"
    );
    assert_eq!(request["operation"], "checkpoint");
    assert_eq!(request["label"], "Milestone 1");
    assert!(request.get("note").is_none());
    Ok(())
}

#[test]
fn pending_checkpoint_digest_matches_the_exact_transmitted_request() -> TestResult {
    let mut mirror = mirror()?;
    let mut adapter = adapter([ResponsePlan::Transport(TransportFailure::Unavailable)]);
    assert_eq!(
        mirror.checkpoint(
            &mut adapter,
            "checkpoint-key-0001".to_owned(),
            "Milestone 1".to_owned(),
            Some("Operator note".to_owned()),
        ),
        Err(SyncError::RemoteUnavailable)
    );
    let pending_sha256 = mirror
        .snapshot()
        .pending_checkpoint_request_sha256
        .ok_or("missing pending request digest")?;
    let (_, transport) = adapter.into_parts();
    assert_eq!(transport.request_sha256s, [pending_sha256]);
    Ok(())
}

#[test]
fn adapter_rejects_wrong_binding_unknown_fields_invalid_heads_and_oversize() -> TestResult {
    for plan in [
        ResponsePlan::WrongBinding,
        ResponsePlan::UnknownField,
        ResponsePlan::InvalidHead,
        ResponsePlan::Oversized,
    ] {
        let mut adapter = adapter([plan]);
        let result = mirror()?.pull(&mut adapter);
        assert_eq!(result, Err(SyncError::InvalidResponse));
    }
    Ok(())
}

#[test]
fn credential_and_transport_failures_are_typed_and_debug_is_redacted() -> TestResult {
    assert!(AuthorizationHeader::new("bearer aaa.bbb.ccc".to_owned()).is_err());
    assert!(AuthorizationHeader::new("Bearer aaa.bbb".to_owned()).is_err());
    assert!(AuthorizationHeader::new("Bearer aaa.bbb.ccc.ddd".to_owned()).is_err());
    let header = AuthorizationHeader::new("Bearer secret.header.value".to_owned())?;
    assert!(!format!("{header:?}").contains("secret"));

    let mut unavailable = adapter([ResponsePlan::Transport(TransportFailure::Unavailable)]);
    assert_eq!(
        mirror()?.pull(&mut unavailable),
        Err(SyncError::RemoteUnavailable)
    );
    let mut rejected = adapter([ResponsePlan::Transport(TransportFailure::Rejected)]);
    assert_eq!(
        mirror()?.pull(&mut rejected),
        Err(SyncError::RemoteRejected)
    );
    let debug = format!("{rejected:?}");
    assert!(!debug.contains("Bearer"));
    assert!(!debug.contains("prj_project01"));
    Ok(())
}

#[test]
fn adapter_maps_typed_remote_rejection_and_conflict() -> TestResult {
    let mut rejected = adapter([ResponsePlan::Rejected]);
    assert_eq!(
        mirror()?.pull(&mut rejected),
        Err(SyncError::RemoteRejected)
    );

    let mut conflicted = adapter([ResponsePlan::Conflict {
        revision: "rev_00000009".to_owned(),
        generation: 9,
    }]);
    assert_eq!(mirror()?.pull(&mut conflicted), Err(SyncError::Conflict));
    Ok(())
}
