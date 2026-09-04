use std::path::{Path, PathBuf};

use artifact_service::TenantId;
use auth_middleware::{AuthMiddleware, AuthRegistryLimits, AuthScope, PrincipalGrant, TenantRole};
use base64::Engine as _;
use base64::engine::general_purpose::URL_SAFE_NO_PAD;
use hmac::{Hmac, Mac as _};
use mcp_control_plane::{
    AsyncJobError, AuthorizedToolCall, DurableAsyncJobGateway, DurableJobStore, GatewayError,
    InMemoryProjectPolicy, JobLocator, JobProgressStage, McpControlPlane, McpToolRequest,
    ProjectAccess, ProjectPolicyLimits, ToolServiceGateway, ToolServiceOutput,
};
use serde::Serialize;
use serde_json::{Value, json};
use sha2::Sha256;
use tempfile::TempDir;
use uuid::Uuid;

type HmacSha256 = Hmac<Sha256>;
type TestControl =
    McpControlPlane<InMemoryProjectPolicy, DurableAsyncJobGateway<RejectingDelegate>>;

const RESOURCE: &str = "https://mcp.hwpx-agent.example";
const METADATA: &str = "https://mcp.hwpx-agent.example/.well-known/oauth-protected-resource";
const ISSUER: &str = "https://identity.hwpx-agent.example";
const KEY_ID: &str = "local-key-01";
const SECRET: &[u8] = b"0123456789abcdef0123456789abcdef";
const NOW: u64 = 2_100_000_000;
const PROJECT_ID: &str = "prj_asyncjob01";
const SOURCE_REVISION: &str = "rev_asyncsource01";

const ALL_SCOPES: [AuthScope; 8] = [
    AuthScope::ArtifactRead,
    AuthScope::ArtifactWrite,
    AuthScope::JobCancel,
    AuthScope::JobSubmit,
    AuthScope::MirrorSync,
    AuthScope::ProjectRead,
    AuthScope::ProjectWrite,
    AuthScope::RetentionManage,
];

#[derive(Debug)]
struct RejectingDelegate;

impl ToolServiceGateway for RejectingDelegate {
    fn dispatch(&mut self, _call: AuthorizedToolCall) -> Result<ToolServiceOutput, GatewayError> {
        Err(GatewayError::Rejected)
    }
}

#[derive(Serialize)]
struct Claims {
    iss: String,
    sub: String,
    aud: String,
    exp: u64,
    nbf: u64,
    iat: u64,
    jti: String,
    scope: String,
    token_kind: String,
    tenant_id: TenantId,
    #[serde(skip_serializing_if = "Option::is_none")]
    service_id: Option<String>,
}

struct Fixture {
    _temporary: TempDir,
    root: PathBuf,
    control: TestControl,
    store: DurableJobStore,
    bearer: String,
    tenant_id: TenantId,
}

impl Fixture {
    fn new() -> Self {
        let temporary = tempfile::tempdir().unwrap_or_else(|error| panic!("tempdir: {error}"));
        let root = temporary.path().join("durable-jobs");
        let store =
            DurableJobStore::open(&root).unwrap_or_else(|error| panic!("durable store: {error}"));
        let (control, bearer, tenant_id) = control_for(store.clone());
        Self {
            _temporary: temporary,
            root,
            control,
            store,
            bearer,
            tenant_id,
        }
    }

    fn call(
        &mut self,
        tool: &str,
        arguments: &Value,
        now: u64,
    ) -> mcp_control_plane::McpToolResult {
        self.control.handle(McpToolRequest::new(
            tool,
            self.bearer.clone(),
            serde_json::to_vec(arguments)
                .unwrap_or_else(|error| panic!("serialize request: {error}")),
            now,
        ))
    }

    fn submit_render(&mut self, request_id: &str, idempotency_key: &str) -> String {
        let result = self.call(
            "document_render",
            &render_input(request_id, idempotency_key),
            NOW,
        );
        assert!(!result.is_error(), "{:?}", result.error_code());
        assert_eq!(result.structured_content()["outcome"], "accepted");
        result.structured_content()["job_id"]
            .as_str()
            .unwrap_or_else(|| panic!("missing job id"))
            .to_owned()
    }

    fn locator(&self, job_id: &str) -> JobLocator {
        JobLocator::new(self.tenant_id, PROJECT_ID, job_id)
            .unwrap_or_else(|error| panic!("locator: {error}"))
    }
}

fn tenant(value: u128) -> TenantId {
    TenantId::new(Uuid::from_u128(value)).unwrap_or_else(|error| panic!("tenant: {error}"))
}

fn control_for(store: DurableJobStore) -> (TestControl, String, TenantId) {
    let tenant_id = tenant(101);
    let mut middleware = AuthMiddleware::new(
        RESOURCE,
        METADATA,
        60,
        AuthRegistryLimits::product_maximums(),
    )
    .unwrap_or_else(|error| panic!("middleware: {error}"));
    middleware
        .register_local_hmac_key(ISSUER, KEY_ID, SECRET, NOW - 600, NOW + 7_200)
        .unwrap_or_else(|error| panic!("key: {error}"));
    let subject = middleware
        .register_user(
            ISSUER,
            "oidc-async-user",
            PrincipalGrant::new(
                tenant_id,
                TenantRole::Owner,
                ALL_SCOPES,
                NOW - 600,
                NOW + 7_200,
            )
            .unwrap_or_else(|error| panic!("grant: {error}")),
        )
        .unwrap_or_else(|error| panic!("user: {error}"));
    let claims = Claims {
        iss: ISSUER.to_owned(),
        sub: "oidc-async-user".to_owned(),
        aud: RESOURCE.to_owned(),
        exp: NOW + 600,
        nbf: NOW - 60,
        iat: NOW - 60,
        jti: "async-token-0001".to_owned(),
        scope: ALL_SCOPES
            .iter()
            .map(|scope| scope.as_str())
            .collect::<Vec<_>>()
            .join(" "),
        token_kind: "user".to_owned(),
        tenant_id,
        service_id: None,
    };
    let mut policy = InMemoryProjectPolicy::new(ProjectPolicyLimits::product_maximums());
    policy
        .register_project(PROJECT_ID, tenant_id)
        .unwrap_or_else(|error| panic!("project: {error}"));
    policy
        .register_membership(PROJECT_ID, subject, ProjectAccess::Owner)
        .unwrap_or_else(|error| panic!("membership: {error}"));
    let control = McpControlPlane::new(
        middleware,
        policy,
        DurableAsyncJobGateway::new(store, RejectingDelegate),
    )
    .unwrap_or_else(|error| panic!("control: {error}"));
    (control, format!("Bearer {}", sign(&claims)), tenant_id)
}

fn sign(claims: &Claims) -> String {
    let header = URL_SAFE_NO_PAD.encode(
        serde_json::to_vec(&json!({"alg": "HS256", "kid": KEY_ID, "typ": "at+jwt"}))
            .unwrap_or_else(|error| panic!("header: {error}")),
    );
    let body = URL_SAFE_NO_PAD
        .encode(serde_json::to_vec(claims).unwrap_or_else(|error| panic!("claims: {error}")));
    let signing_input = format!("{header}.{body}");
    let mut signer = <HmacSha256 as hmac::KeyInit>::new_from_slice(SECRET)
        .unwrap_or_else(|error| panic!("signer: {error}"));
    signer.update(signing_input.as_bytes());
    format!(
        "{signing_input}.{}",
        URL_SAFE_NO_PAD.encode(signer.finalize().into_bytes())
    )
}

fn render_input(request_id: &str, idempotency_key: &str) -> Value {
    json!({
        "client_surface": "codex_local",
        "locale": "ko-KR",
        "request_id": request_id,
        "project_id": PROJECT_ID,
        "target_profile": "hancom-hangul-2020-secondary",
        "idempotency_key": idempotency_key,
        "revision_id": SOURCE_REVISION,
        "pages": {"first": 1, "last": 3},
        "dpi": 144,
        "output": "png",
        "backend": "hancom_2020",
        "crop": "page"
    })
}

fn get_input(request_id: &str, job_id: &str, cursor: Option<&str>, limit: u64) -> Value {
    let mut value = json!({
        "client_surface": "codex_local",
        "locale": "ko-KR",
        "request_id": request_id,
        "project_id": PROJECT_ID,
        "job_id": job_id,
        "include_events": true,
        "event_limit": limit
    });
    if let Some(cursor) = cursor {
        value
            .as_object_mut()
            .unwrap_or_else(|| panic!("job get input object"))
            .insert("event_cursor".to_owned(), Value::String(cursor.to_owned()));
    }
    value
}

fn cancel_input(request_id: &str, job_id: &str, idempotency_key: &str) -> Value {
    json!({
        "client_surface": "codex_local",
        "locale": "ko-KR",
        "request_id": request_id,
        "project_id": PROJECT_ID,
        "expected_revision": SOURCE_REVISION,
        "idempotency_key": idempotency_key,
        "job_id": job_id,
        "reason": "User requested cancellation."
    })
}

fn common_mutation_input(request_id: &str, idempotency_key: &str) -> Value {
    json!({
        "client_surface": "codex_local",
        "locale": "ko-KR",
        "request_id": request_id,
        "project_id": PROJECT_ID,
        "target_profile": "hancom-hangul-2020-secondary",
        "expected_revision": SOURCE_REVISION,
        "idempotency_key": idempotency_key
    })
}

fn event_sequences(result: &mcp_control_plane::McpToolResult) -> Vec<u64> {
    result.meta()["hwpx/jobEvents"]
        .as_array()
        .unwrap_or_else(|| panic!("missing job events"))
        .iter()
        .map(|event| {
            event["sequence"]
                .as_u64()
                .unwrap_or_else(|| panic!("event sequence"))
        })
        .collect()
}

fn terminal_event_count(result: &mcp_control_plane::McpToolResult) -> usize {
    result.meta()["hwpx/jobEvents"]
        .as_array()
        .unwrap_or_else(|| panic!("missing job events"))
        .iter()
        .filter(|event| event["kind"] == "terminal")
        .count()
}

#[test]
fn submit_progress_poll_terminal_and_restart_is_end_to_end() {
    let mut fixture = Fixture::new();
    let idempotency_key = "123e4567-e89b-42d3-a456-426614174001";
    let job_id = fixture.submit_render("req_renderjob01", idempotency_key);
    let replay = fixture.call(
        "document_render",
        &render_input("req_renderretry01", idempotency_key),
        NOW + 1,
    );
    assert!(!replay.is_error(), "{:?}", replay.error_code());
    assert_eq!(replay.structured_content()["job_id"], job_id);
    let mut changed = render_input("req_renderretry02", idempotency_key);
    changed
        .as_object_mut()
        .unwrap_or_else(|| panic!("render retry input"))
        .insert("dpi".to_owned(), json!(300));
    let conflict = fixture.call("document_render", &changed, NOW + 1);
    assert!(conflict.is_error());
    assert_eq!(conflict.error_code(), Some("REQUEST_CONFLICT"));
    let locator = fixture.locator(&job_id);
    for (time, stage, completed, total) in [
        (NOW + 1, JobProgressStage::Preflight, 0, Some(3)),
        (NOW + 2, JobProgressStage::Render, 2, Some(3)),
        (NOW + 3, JobProgressStage::Validate, 3, Some(3)),
        (NOW + 4, JobProgressStage::Commit, 3, Some(3)),
    ] {
        fixture
            .store
            .record_progress(&locator, time, stage, completed, total)
            .unwrap_or_else(|error| panic!("progress: {error}"));
    }

    let first = fixture.call(
        "job_get",
        &get_input("req_pollpage01", &job_id, None, 2),
        NOW + 5,
    );
    assert!(!first.is_error(), "{:?}", first.error_code());
    assert_eq!(first.structured_content()["state"], "committing");
    assert_eq!(event_sequences(&first), vec![1, 2]);
    let cursor = first.structured_content()["next_event_cursor"]
        .as_str()
        .unwrap_or_else(|| panic!("event cursor"))
        .to_owned();

    let second = fixture.call(
        "job_get",
        &get_input("req_pollpage02", &job_id, Some(&cursor), 200),
        NOW + 5,
    );
    assert_eq!(event_sequences(&second), vec![3, 4, 5]);
    let terminal_cursor = second.structured_content()["next_event_cursor"]
        .as_str()
        .unwrap_or_else(|| panic!("second cursor"))
        .to_owned();

    let receipt = fixture
        .store
        .complete_success(&locator, NOW + 6, ["art_renderout01".to_owned()])
        .unwrap_or_else(|error| panic!("complete: {error}"));
    assert!(receipt.starts_with("rcp_"));
    assert_eq!(
        fixture
            .store
            .complete_success(&locator, NOW + 7, Vec::<String>::new()),
        Err(AsyncJobError::InvalidTransition)
    );

    let terminal = fixture.call(
        "job_get",
        &get_input("req_pollterminal01", &job_id, Some(&terminal_cursor), 200),
        NOW + 7,
    );
    assert_eq!(terminal.structured_content()["state"], "succeeded");
    assert_eq!(
        terminal.structured_content()["result_artifact_ids"],
        json!(["art_renderout01"])
    );
    assert_eq!(event_sequences(&terminal), vec![6]);
    assert_eq!(terminal_event_count(&terminal), 1);
    assert_eq!(terminal.meta()["hwpx/jobEvents"][0]["receipt_id"], receipt);

    let reopened = DurableJobStore::open(&fixture.root)
        .unwrap_or_else(|error| panic!("reopen durable store: {error}"));
    let (mut restarted_control, restarted_bearer, _) = control_for(reopened);
    let restarted = restarted_control.handle(McpToolRequest::new(
        "job_get",
        restarted_bearer,
        serde_json::to_vec(&get_input("req_restartpoll01", &job_id, None, 200))
            .unwrap_or_else(|error| panic!("restart request: {error}")),
        NOW + 8,
    ));
    assert_eq!(restarted.structured_content()["state"], "succeeded");
    assert_eq!(event_sequences(&restarted), vec![1, 2, 3, 4, 5, 6]);

    let journal = std::fs::read_to_string(fixture.root.join("p15-job-journal-v1.jsonl"))
        .unwrap_or_else(|error| panic!("journal: {error}"));
    assert!(!journal.contains(SOURCE_REVISION));
    assert!(!journal.contains("Bearer "));
}

#[test]
fn queued_cancel_is_immediate_terminal_and_idempotent() {
    let mut fixture = Fixture::new();
    let job_id = fixture.submit_render("req_queuedjob01", "123e4567-e89b-42d3-a456-426614174002");
    let cancel_key = "123e4567-e89b-42d3-a456-426614174102";
    let first = fixture.call(
        "job_cancel",
        &cancel_input("req_cancelqueued01", &job_id, cancel_key),
        NOW + 1,
    );
    assert_eq!(first.structured_content()["cancel_state"], "cancelled");
    assert_eq!(first.structured_content()["replayed"], false);
    let receipt = first.structured_content()["receipt_id"].clone();

    let replay = fixture.call(
        "job_cancel",
        &cancel_input("req_cancelqueued02", &job_id, cancel_key),
        NOW + 2,
    );
    assert_eq!(replay.structured_content()["cancel_state"], "cancelled");
    assert_eq!(replay.structured_content()["receipt_id"], receipt);
    assert_eq!(replay.structured_content()["replayed"], true);

    let poll = fixture.call(
        "job_get",
        &get_input("req_cancelledpoll01", &job_id, None, 200),
        NOW + 3,
    );
    assert_eq!(poll.structured_content()["state"], "cancelled");
    assert_eq!(terminal_event_count(&poll), 1);
    assert_eq!(
        fixture
            .store
            .acknowledge_cancellation(&fixture.locator(&job_id), NOW + 4),
        Err(AsyncJobError::InvalidTransition)
    );
}

#[test]
fn running_cancel_waits_for_safe_point_and_blocks_progress() {
    let mut fixture = Fixture::new();
    let job_id = fixture.submit_render("req_runningjob01", "123e4567-e89b-42d3-a456-426614174003");
    let locator = fixture.locator(&job_id);
    fixture
        .store
        .record_progress(&locator, NOW + 1, JobProgressStage::Render, 1, Some(3))
        .unwrap_or_else(|error| panic!("progress: {error}"));
    let cancel = fixture.call(
        "job_cancel",
        &cancel_input(
            "req_cancelrunning01",
            &job_id,
            "123e4567-e89b-42d3-a456-426614174103",
        ),
        NOW + 2,
    );
    assert_eq!(cancel.structured_content()["cancel_state"], "requested");
    let receipt = cancel.structured_content()["receipt_id"]
        .as_str()
        .unwrap_or_else(|| panic!("cancel receipt"))
        .to_owned();
    assert_eq!(
        fixture
            .store
            .record_progress(&locator, NOW + 3, JobProgressStage::Render, 2, Some(3)),
        Err(AsyncJobError::CancellationPending)
    );
    assert_eq!(
        fixture
            .store
            .acknowledge_cancellation(&locator, NOW + 3)
            .unwrap_or_else(|error| panic!("acknowledge: {error}")),
        receipt
    );
    let poll = fixture.call(
        "job_get",
        &get_input("req_runningcancelpoll01", &job_id, None, 200),
        NOW + 4,
    );
    assert_eq!(poll.structured_content()["state"], "cancelled");
    assert_eq!(event_sequences(&poll), vec![1, 2, 3, 4]);
    assert_eq!(terminal_event_count(&poll), 1);
}

#[test]
fn committing_job_rejects_cancel_but_can_finish_once() {
    let mut fixture = Fixture::new();
    let job_id = fixture.submit_render("req_commitjob01", "123e4567-e89b-42d3-a456-426614174004");
    let locator = fixture.locator(&job_id);
    fixture
        .store
        .record_progress(&locator, NOW + 1, JobProgressStage::Commit, 3, Some(3))
        .unwrap_or_else(|error| panic!("commit stage: {error}"));
    let cancel = fixture.call(
        "job_cancel",
        &cancel_input(
            "req_cancelcommit01",
            &job_id,
            "123e4567-e89b-42d3-a456-426614174104",
        ),
        NOW + 2,
    );
    assert_eq!(
        cancel.structured_content()["cancel_state"],
        "not_cancellable"
    );
    fixture
        .store
        .complete_success(&locator, NOW + 3, ["art_commitout01".to_owned()])
        .unwrap_or_else(|error| panic!("complete: {error}"));
    let poll = fixture.call(
        "job_get",
        &get_input("req_commitpoll01", &job_id, None, 200),
        NOW + 4,
    );
    assert_eq!(poll.structured_content()["state"], "succeeded");
    assert_eq!(terminal_event_count(&poll), 1);
}

#[test]
fn all_six_long_running_tools_return_schema_valid_durable_jobs() {
    let mut fixture = Fixture::new();
    let mut cases = Vec::new();

    let mut create =
        common_mutation_input("req_submitcreate01", "123e4567-e89b-42d3-a456-426614174011");
    create
        .as_object_mut()
        .unwrap_or_else(|| panic!("create input"))
        .extend([
            ("plan_id".to_owned(), json!("plan_asyncplan01")),
            ("mode".to_owned(), json!("normalized_authoring")),
        ]);
    cases.push(("document_create", create));

    let mut edit =
        common_mutation_input("req_submitedit001", "123e4567-e89b-42d3-a456-426614174012");
    edit.as_object_mut()
        .unwrap_or_else(|| panic!("edit input"))
        .extend([
            ("source_revision_id".to_owned(), json!(SOURCE_REVISION)),
            ("plan_id".to_owned(), json!("plan_asyncplan02")),
            ("dry_run".to_owned(), json!(false)),
            ("best_effort".to_owned(), json!(false)),
        ]);
    cases.push(("document_edit", edit));

    let mut transform = common_mutation_input(
        "req_submittransform01",
        "123e4567-e89b-42d3-a456-426614174013",
    );
    transform
        .as_object_mut()
        .unwrap_or_else(|| panic!("transform input"))
        .extend([
            ("source_revision_ids".to_owned(), json!([SOURCE_REVISION])),
            ("transform".to_owned(), json!("sanitize_metadata")),
            ("preview_diff".to_owned(), json!(true)),
        ]);
    cases.push(("document_transform", transform));

    let mut validate = common_mutation_input(
        "req_submitvalidate01",
        "123e4567-e89b-42d3-a456-426614174014",
    );
    validate
        .as_object_mut()
        .unwrap_or_else(|| panic!("validate input"))
        .remove("expected_revision");
    validate
        .as_object_mut()
        .unwrap_or_else(|| panic!("validate input"))
        .extend([
            ("revision_id".to_owned(), json!(SOURCE_REVISION)),
            ("levels".to_owned(), json!(["schema", "semantic"])),
            ("fail_on_unverified".to_owned(), json!(true)),
        ]);
    cases.push(("document_validate", validate));

    cases.push((
        "document_render",
        render_input("req_submitrender01", "123e4567-e89b-42d3-a456-426614174015"),
    ));

    let mut export =
        common_mutation_input("req_submitexport01", "123e4567-e89b-42d3-a456-426614174016");
    export
        .as_object_mut()
        .unwrap_or_else(|| panic!("export input"))
        .extend([
            ("source_revision_id".to_owned(), json!(SOURCE_REVISION)),
            ("format".to_owned(), json!("pdf")),
            ("profile".to_owned(), json!("print")),
            ("allow_lossy".to_owned(), json!(false)),
            ("include_loss_report".to_owned(), json!(true)),
        ]);
    cases.push(("document_export", export));

    let mut job_ids = std::collections::BTreeSet::new();
    for (tool, input) in cases {
        let result = fixture.call(tool, &input, NOW);
        assert!(!result.is_error(), "{tool}: {:?}", result.error_code());
        assert_eq!(result.structured_content()["outcome"], "accepted");
        let job_id = result.structured_content()["job_id"]
            .as_str()
            .unwrap_or_else(|| panic!("{tool} job id"));
        assert!(job_ids.insert(job_id.to_owned()));
    }
    assert_eq!(job_ids.len(), 6);
}

#[test]
fn cancel_after_success_returns_the_single_terminal_receipt() {
    let mut fixture = Fixture::new();
    let job_id = fixture.submit_render("req_terminaljob01", "123e4567-e89b-42d3-a456-426614174017");
    let locator = fixture.locator(&job_id);
    fixture
        .store
        .record_progress(&locator, NOW + 1, JobProgressStage::Commit, 3, Some(3))
        .unwrap_or_else(|error| panic!("commit: {error}"));
    let terminal_receipt = fixture
        .store
        .complete_success(&locator, NOW + 2, ["art_terminalout01".to_owned()])
        .unwrap_or_else(|error| panic!("complete: {error}"));
    let cancel = fixture.call(
        "job_cancel",
        &cancel_input(
            "req_cancelterminal01",
            &job_id,
            "123e4567-e89b-42d3-a456-426614174117",
        ),
        NOW + 3,
    );
    assert!(!cancel.is_error(), "{:?}", cancel.error_code());
    assert_eq!(
        cancel.structured_content()["cancel_state"],
        "already_terminal"
    );
    assert_eq!(cancel.structured_content()["receipt_id"], terminal_receipt);
    let poll = fixture.call(
        "job_get",
        &get_input("req_terminalpoll01", &job_id, None, 200),
        NOW + 4,
    );
    assert_eq!(terminal_event_count(&poll), 1);
}

#[test]
fn cursor_is_bound_to_one_job_and_event_order() {
    let mut fixture = Fixture::new();
    let first_job =
        fixture.submit_render("req_cursorjob01", "123e4567-e89b-42d3-a456-426614174005");
    let second_job =
        fixture.submit_render("req_cursorjob02", "123e4567-e89b-42d3-a456-426614174006");
    let first_page = fixture.call(
        "job_get",
        &get_input("req_cursorpoll01", &first_job, None, 1),
        NOW + 1,
    );
    let cursor = first_page.structured_content()["next_event_cursor"]
        .as_str()
        .unwrap_or_else(|| panic!("cursor"));
    let wrong_job = fixture.call(
        "job_get",
        &get_input("req_cursorpoll02", &second_job, Some(cursor), 1),
        NOW + 1,
    );
    assert!(wrong_job.is_error());
    assert_eq!(wrong_job.error_code(), Some("REQUEST_CONFLICT"));
}

#[test]
fn backward_progress_and_terminal_failure_are_fail_closed() {
    let mut fixture = Fixture::new();
    let job_id = fixture.submit_render("req_failurejob01", "123e4567-e89b-42d3-a456-426614174007");
    let locator = fixture.locator(&job_id);
    fixture
        .store
        .record_progress(&locator, NOW + 1, JobProgressStage::Render, 1, Some(3))
        .unwrap_or_else(|error| panic!("render: {error}"));
    assert_eq!(
        fixture
            .store
            .record_progress(&locator, NOW + 2, JobProgressStage::Execute, 2, Some(3)),
        Err(AsyncJobError::InvalidTransition)
    );
    fixture
        .store
        .record_progress(&locator, NOW + 3, JobProgressStage::Validate, 2, Some(3))
        .unwrap_or_else(|error| panic!("validate: {error}"));
    let receipt = fixture
        .store
        .complete_failure(&locator, NOW + 4, "RENDER_FAILED")
        .unwrap_or_else(|error| panic!("failure: {error}"));
    assert!(receipt.starts_with("rcp_"));
    assert_eq!(
        fixture
            .store
            .complete_failure(&locator, NOW + 5, "RENDER_FAILED"),
        Err(AsyncJobError::InvalidTransition)
    );
    let poll = fixture.call(
        "job_get",
        &get_input("req_failurepoll01", &job_id, None, 200),
        NOW + 6,
    );
    assert_eq!(poll.structured_content()["state"], "failed");
    assert_eq!(terminal_event_count(&poll), 1);
}

#[test]
fn malformed_or_duplicate_journal_data_fails_reopen() {
    let root = tempfile::tempdir().unwrap_or_else(|error| panic!("tempdir: {error}"));
    let store =
        DurableJobStore::open(root.path()).unwrap_or_else(|error| panic!("initial store: {error}"));
    drop(store);
    std::fs::write(
        root.path().join("p15-job-journal-v1.jsonl"),
        b"{\"schema_version\":\"x\",\"schema_version\":\"y\"}\n",
    )
    .unwrap_or_else(|error| panic!("corrupt journal: {error}"));
    assert!(matches!(
        DurableJobStore::open(root.path()),
        Err(AsyncJobError::StoreCorrupt)
    ));
}

#[test]
fn store_debug_and_journal_do_not_expose_local_paths_or_cancel_reason() {
    let mut fixture = Fixture::new();
    let job_id = fixture.submit_render("req_redactedjob01", "123e4567-e89b-42d3-a456-426614174008");
    let debug = format!("{:?}", fixture.store);
    assert!(!debug.contains(&fixture.root.to_string_lossy().to_string()));
    let reason = "SENSITIVE LOCAL PATH D:/private/document.hwpx";
    let mut input = cancel_input(
        "req_redactedcancel01",
        &job_id,
        "123e4567-e89b-42d3-a456-426614174108",
    );
    input
        .as_object_mut()
        .unwrap_or_else(|| panic!("cancel input"))
        .insert("reason".to_owned(), Value::String(reason.to_owned()));
    let result = fixture.call("job_cancel", &input, NOW + 1);
    assert!(!result.is_error());
    let journal = std::fs::read_to_string(fixture.root.join("p15-job-journal-v1.jsonl"))
        .unwrap_or_else(|error| panic!("journal: {error}"));
    assert!(!journal.contains(reason));
    assert!(!journal.contains("document.hwpx"));
}

#[test]
fn journal_location_is_fixed_under_the_requested_root() {
    let temporary = tempfile::tempdir().unwrap_or_else(|error| panic!("tempdir: {error}"));
    let root = temporary.path().join("nested");
    let _store = DurableJobStore::open(&root).unwrap_or_else(|error| panic!("store: {error}"));
    assert!(Path::new(&root).is_dir());
    assert!(!temporary.path().join("p15-job-journal-v1.jsonl").exists());
}
