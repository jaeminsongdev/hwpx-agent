#![forbid(unsafe_code)]

pub mod bookmark_preview722;

use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::path::{Component, Path, PathBuf};
use std::sync::{Arc, Mutex};
use std::time::{SystemTime, UNIX_EPOCH};

use approval_policy::{
    ApprovalEvaluator, ApprovalPolicy, ApprovalScope, ConfirmationToken, DurableReplayLedger,
    EffectKind,
};
use base64::Engine as _;
use base64::engine::general_purpose::URL_SAFE_NO_PAD;
use git_effect_host::{GitCommitEffectInput, GitEffectHost};
use local_workflow::{LocalWorkflow, MaterializeSlot};
use serde::{Deserialize, Serialize};
use serde_json::{Value, json};
use sha2::{Digest as _, Sha256};
use thiserror::Error;
use zeroize::Zeroizing;

pub const PROTOCOL_VERSION: &str = "hwpx-agent.local-companion-private/v1";
pub const WORKFLOW_PROTOCOL_VERSION: &str = "hwpx-agent.local-companion-private/v2";
pub const APPROVAL_PROTOCOL_VERSION: &str = "hwpx-agent.local-companion-private/v3";
pub const EFFECT_PROTOCOL_VERSION: &str = "hwpx-agent.local-companion-private/v4";
pub const CONFIG_VERSION: &str = "hwpx-agent.local-companion-config/v1";
pub const TARGET_PROFILE: &str = "hancom-2020-x86-11.0.0.9136";
pub const SESSION_TOKEN_ENV: &str = "HWPX_AGENT_LOCAL_SESSION_TOKEN";
pub const APPROVAL_SECRET_ENV: &str = "HWPX_AGENT_APPROVAL_SECRET";
pub const APPROVAL_STATE_ROOT_ENV: &str = "HWPX_AGENT_APPROVAL_STATE_ROOT";
pub const GIT_PROGRAM_ENV: &str = "HWPX_AGENT_GIT_PROGRAM";
pub const MAX_CONFIG_BYTES: u64 = 65_536;
pub const MAX_REQUEST_BYTES: usize = 16_384;
const MAX_WORKSPACES: usize = 8;
const MAX_RELATIVE_PATH_BYTES: usize = 1_024;
const MAX_PATH_COMPONENTS: usize = 32;
const MAX_FILE_BYTES_LIMIT: u64 = 1_073_741_824;
const APPROVAL_MAX_TTL_SECONDS: u64 = 120;
const APPROVAL_MAX_CONSUMED_TOKENS: usize = 4_096;
const EFFECT_MAX_EXECUTION_DELAY_SECONDS: u64 = 30;

#[derive(Debug, Error)]
pub enum DaemonError {
    #[error("configuration rejected")]
    Configuration,
    #[error("request rejected")]
    Request,
    #[error("workspace boundary rejected")]
    Workspace,
    #[error("local I/O rejected")]
    Io,
    #[error("side effect rejected")]
    Effect,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct ConfigDocument {
    schema_version: String,
    target_profile: String,
    automation_mode: AutomationMode,
    network_mode: NetworkMode,
    max_file_bytes: u64,
    workspaces: Vec<WorkspaceDocument>,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq)]
#[serde(rename_all = "snake_case")]
enum AutomationMode {
    Disabled,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq)]
#[serde(rename_all = "snake_case")]
enum NetworkMode {
    Disabled,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct WorkspaceDocument {
    id: String,
    root: PathBuf,
}

#[derive(Clone, Debug)]
struct Workspace {
    root: PathBuf,
}

#[derive(Clone)]
pub struct LocalCompanionConfig {
    max_file_bytes: u64,
    workspaces: BTreeMap<String, Workspace>,
    digest: String,
}

impl std::fmt::Debug for LocalCompanionConfig {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("LocalCompanionConfig")
            .field("max_file_bytes", &self.max_file_bytes)
            .field("workspace_count", &self.workspaces.len())
            .field("digest", &self.digest)
            .finish()
    }
}

impl LocalCompanionConfig {
    /// Loads and validates a bounded local-only configuration file.
    ///
    /// # Errors
    ///
    /// Rejects non-regular/link files, malformed or non-canonical workspace roots, duplicate
    /// identities, unsupported target profiles, enabled automation/network modes and unsafe limits.
    pub fn load(path: &Path) -> Result<Self, DaemonError> {
        if !path.is_absolute() {
            return Err(DaemonError::Configuration);
        }
        let metadata = fs::symlink_metadata(path).map_err(|_| DaemonError::Io)?;
        if !metadata.is_file()
            || is_link_or_reparse(&metadata)
            || metadata.len() == 0
            || metadata.len() > MAX_CONFIG_BYTES
        {
            return Err(DaemonError::Configuration);
        }
        let bytes = fs::read(path).map_err(|_| DaemonError::Io)?;
        let document: ConfigDocument =
            serde_json::from_slice(&bytes).map_err(|_| DaemonError::Configuration)?;
        if document.schema_version != CONFIG_VERSION
            || document.target_profile != TARGET_PROFILE
            || document.automation_mode != AutomationMode::Disabled
            || document.network_mode != NetworkMode::Disabled
            || !(1..=MAX_FILE_BYTES_LIMIT).contains(&document.max_file_bytes)
            || document.workspaces.is_empty()
            || document.workspaces.len() > MAX_WORKSPACES
        {
            return Err(DaemonError::Configuration);
        }
        let mut workspaces = BTreeMap::new();
        let mut roots = BTreeSet::new();
        for candidate in document.workspaces {
            if !valid_identifier(&candidate.id) || !candidate.root.is_absolute() {
                return Err(DaemonError::Configuration);
            }
            let requested =
                fs::symlink_metadata(&candidate.root).map_err(|_| DaemonError::Configuration)?;
            if !requested.is_dir() || is_link_or_reparse(&requested) {
                return Err(DaemonError::Configuration);
            }
            let root = candidate
                .root
                .canonicalize()
                .map_err(|_| DaemonError::Configuration)?;
            if root.parent().is_none() || !is_directory_without_link(&root) {
                return Err(DaemonError::Configuration);
            }
            let root_key = path_identity(&root)?;
            if !roots.insert(root_key)
                || workspaces
                    .insert(candidate.id, Workspace { root })
                    .is_some()
            {
                return Err(DaemonError::Configuration);
            }
        }
        Ok(Self {
            max_file_bytes: document.max_file_bytes,
            workspaces,
            digest: hex_digest(&bytes),
        })
    }

    #[must_use]
    pub fn workspace_count(&self) -> usize {
        self.workspaces.len()
    }

    #[must_use]
    pub fn digest(&self) -> &str {
        &self.digest
    }

    fn workflow(&self, workspace_id: &str) -> Result<LocalWorkflow, DaemonError> {
        if !valid_identifier(workspace_id) {
            return Err(DaemonError::Workspace);
        }
        let workspace = self
            .workspaces
            .get(workspace_id)
            .ok_or(DaemonError::Workspace)?;
        LocalWorkflow::open(&workspace.root, self.max_file_bytes)
            .map_err(|_| DaemonError::Workspace)
    }
}

struct ApprovalRuntimeState {
    evaluator: ApprovalEvaluator,
    hosts: BTreeMap<String, GitEffectHost>,
}

#[derive(Clone)]
pub struct ApprovalRuntime {
    state: Arc<Mutex<ApprovalRuntimeState>>,
}

impl std::fmt::Debug for ApprovalRuntime {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("ApprovalRuntime")
            .field("state", &"<redacted>")
            .finish()
    }
}

impl ApprovalRuntime {
    /// Builds the opt-in Git approval runtime without exposing a confirmation minting API.
    ///
    /// # Errors
    ///
    /// Rejects unsafe state/Git paths, invalid keys, ledger failures and unsupported workspaces.
    pub fn new(
        config: &LocalCompanionConfig,
        git_program: &Path,
        state_root: &Path,
        secret: &[u8],
    ) -> Result<Self, DaemonError> {
        if !state_root.is_absolute() {
            return Err(DaemonError::Configuration);
        }
        let ledger =
            DurableReplayLedger::open(state_root).map_err(|_| DaemonError::Configuration)?;
        let policy = ApprovalPolicy::new(
            [EffectKind::GitCommit],
            APPROVAL_MAX_TTL_SECONDS,
            APPROVAL_MAX_CONSUMED_TOKENS,
        )
        .map_err(|_| DaemonError::Configuration)?;
        let evaluator = ApprovalEvaluator::with_replay_ledger(policy, secret, Box::new(ledger))
            .map_err(|_| DaemonError::Configuration)?;
        let mut hosts = BTreeMap::new();
        for (workspace_id, workspace) in &config.workspaces {
            let host = GitEffectHost::open(
                &workspace.root,
                git_program,
                config.max_file_bytes,
                EFFECT_MAX_EXECUTION_DELAY_SECONDS,
            )
            .map_err(|_| DaemonError::Configuration)?;
            hosts.insert(workspace_id.clone(), host);
        }
        Ok(Self {
            state: Arc::new(Mutex::new(ApprovalRuntimeState { evaluator, hosts })),
        })
    }

    /// Loads an all-or-none opt-in runtime from private host environment values.
    ///
    /// # Errors
    ///
    /// Rejects partial, malformed, non-canonical or unsafe configuration.
    pub fn from_environment(config: &LocalCompanionConfig) -> Result<Option<Self>, DaemonError> {
        let git_program = std::env::var_os(GIT_PROGRAM_ENV);
        let state_root = std::env::var_os(APPROVAL_STATE_ROOT_ENV);
        let encoded_secret = std::env::var_os(APPROVAL_SECRET_ENV);
        if git_program.is_none() && state_root.is_none() && encoded_secret.is_none() {
            return Ok(None);
        }
        let git_program = PathBuf::from(git_program.ok_or(DaemonError::Configuration)?);
        let state_root = PathBuf::from(state_root.ok_or(DaemonError::Configuration)?);
        let encoded_secret = encoded_secret
            .and_then(|value| value.into_string().ok())
            .ok_or(DaemonError::Configuration)?;
        if !(43..=171).contains(&encoded_secret.len())
            || encoded_secret.contains('=')
            || !encoded_secret
                .bytes()
                .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'_'))
        {
            return Err(DaemonError::Configuration);
        }
        let secret = Zeroizing::new(
            URL_SAFE_NO_PAD
                .decode(encoded_secret.as_bytes())
                .map_err(|_| DaemonError::Configuration)?,
        );
        if !(32..=128).contains(&secret.len())
            || URL_SAFE_NO_PAD.encode(secret.as_slice()) != encoded_secret
        {
            return Err(DaemonError::Configuration);
        }
        Self::new(config, &git_program, &state_root, &secret).map(Some)
    }

    fn execute_git_commit(
        &self,
        mut params: ExecuteGitCommitParams,
        now_unix_seconds: u64,
    ) -> Result<Value, DaemonError> {
        if !valid_identifier(&params.workspace_id)
            || !valid_identifier(&params.operation_id)
            || !valid_identifier(&params.output_id)
        {
            return Err(DaemonError::Effect);
        }
        let expected_sha256 = parse_digest(&params.expected_sha256)?;
        let input = GitCommitEffectInput::new(
            params.operation_id.clone(),
            format!("{}.hwpx", params.output_id),
            expected_sha256,
            params.message.clone(),
        )
        .map_err(|_| DaemonError::Effect)?;
        let confirmation = ConfirmationToken::parse(std::mem::take(&mut params.confirmation_token))
            .map_err(|_| DaemonError::Effect)?;
        let mut state = self.state.lock().map_err(|_| DaemonError::Effect)?;
        let host = state
            .hosts
            .get(&params.workspace_id)
            .cloned()
            .ok_or(DaemonError::Effect)?;
        let request = host
            .prepare_approval_request(
                &input,
                params.actor_sha256.clone(),
                params.tenant_sha256.clone(),
                params.requested_at_unix_seconds,
            )
            .map_err(|_| DaemonError::Effect)?;
        let scopes = BTreeSet::from([ApprovalScope::WorkstationControl]);
        let authorization = state
            .evaluator
            .authorize(&request, &scopes, Some(&confirmation), now_unix_seconds)
            .map_err(|_| DaemonError::Effect)?;
        let receipt = host
            .execute_git_commit(&input, authorization, now_unix_seconds)
            .map_err(|_| DaemonError::Effect)?;
        Ok(json!({
            "workspace_id": params.workspace_id,
            "operation_id": params.operation_id,
            "output_id": params.output_id,
            "commit_oid": receipt.commit_oid,
            "previous_head": receipt.previous_head,
            "updated_reference": receipt.updated_reference,
            "output_sha256": receipt.output_sha256,
            "target_sha256": receipt.target_sha256,
            "plan_sha256": receipt.plan_sha256,
            "approved_at_unix_seconds": receipt.approval.approved_at_unix_seconds,
            "index_synchronized": receipt.index_synchronized,
            "executed": true,
        }))
    }
}

pub struct SessionToken(Zeroizing<String>);

impl std::fmt::Debug for SessionToken {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter.write_str("SessionToken([REDACTED])")
    }
}

impl SessionToken {
    /// Admits exactly one 32-byte base64url token without padding.
    ///
    /// # Errors
    ///
    /// Returns `Configuration` when the token shape is not canonical.
    pub fn new(value: String) -> Result<Self, DaemonError> {
        if value.len() != 43
            || !value
                .bytes()
                .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'_'))
        {
            return Err(DaemonError::Configuration);
        }
        let decoded = Zeroizing::new(
            URL_SAFE_NO_PAD
                .decode(value.as_bytes())
                .map_err(|_| DaemonError::Configuration)?,
        );
        if decoded.len() != 32 || URL_SAFE_NO_PAD.encode(decoded.as_slice()) != value {
            return Err(DaemonError::Configuration);
        }
        Ok(Self(Zeroizing::new(value)))
    }

    /// Reads the process-scoped token supplied by the local MCP bridge.
    ///
    /// # Errors
    ///
    /// Returns `Configuration` when the environment value is absent or malformed.
    pub fn from_environment() -> Result<Self, DaemonError> {
        let value = std::env::var(SESSION_TOKEN_ENV).map_err(|_| DaemonError::Configuration)?;
        Self::new(value)
    }

    fn matches(&self, candidate: &[u8]) -> bool {
        let expected = self.0.as_bytes();
        if expected.len() != candidate.len() {
            return false;
        }
        expected
            .iter()
            .zip(candidate)
            .fold(0_u8, |difference, (left, right)| {
                difference | (left ^ right)
            })
            == 0
    }
}

#[derive(Clone, Debug)]
pub struct LocalCompanionDaemon {
    config: LocalCompanionConfig,
    approval: Option<ApprovalRuntime>,
}

type HandleSuccess = (&'static str, String, Value);
type HandleFailure = (Option<&'static str>, Option<String>, DaemonError);

impl LocalCompanionDaemon {
    #[must_use]
    pub fn new(config: LocalCompanionConfig) -> Self {
        Self {
            config,
            approval: None,
        }
    }

    #[must_use]
    pub fn with_approval_runtime(config: LocalCompanionConfig, approval: ApprovalRuntime) -> Self {
        Self {
            config,
            approval: Some(approval),
        }
    }

    /// Handles one bounded private-protocol JSON value and returns a bounded response.
    ///
    /// Authentication and exact request-shape validation precede all filesystem inspection.
    #[must_use]
    pub fn handle(&self, bytes: &[u8], token: &SessionToken) -> Value {
        self.handle_optional_bookmark_runtime(bytes, token, None)
    }

    /// A trusted embedding host supplies its authenticated current-source runtime.
    /// The ordinary daemon has no runtime and fails closed for the new method.
    #[must_use]
    pub fn handle_with_bookmark_runtime(&self, bytes: &[u8], token: &SessionToken,
        runtime: &dyn bookmark_preview722::BookmarkPreviewRuntime) -> Value {
        self.handle_optional_bookmark_runtime(bytes, token, Some(runtime))
    }

    fn handle_optional_bookmark_runtime(&self, bytes: &[u8], token: &SessionToken,
        runtime: Option<&dyn bookmark_preview722::BookmarkPreviewRuntime>) -> Value {
        let parsed = self.handle_inner(bytes, token, runtime);
        match parsed {
            Ok((protocol, request_id, result)) => response_ok(protocol, &request_id, result),
            Err((protocol, request_id, _)) => response_error(
                protocol.unwrap_or(PROTOCOL_VERSION),
                request_id.as_deref().unwrap_or("invalid"),
            ),
        }
    }

    fn handle_inner(
        &self,
        bytes: &[u8],
        token: &SessionToken,
        runtime: Option<&dyn bookmark_preview722::BookmarkPreviewRuntime>,
    ) -> Result<HandleSuccess, HandleFailure> {
        if bytes.is_empty() || bytes.len() > MAX_REQUEST_BYTES {
            return Err((None, None, DaemonError::Request));
        }
        let mut request: PrivateRequest =
            serde_json::from_slice(bytes).map_err(|_| (None, None, DaemonError::Request))?;
        let request_id = if valid_identifier(&request.request_id) {
            request.request_id.clone()
        } else {
            return Err((None, None, DaemonError::Request));
        };
        let protocol = match request.protocol_version.as_str() {
            PROTOCOL_VERSION => PROTOCOL_VERSION,
            WORKFLOW_PROTOCOL_VERSION => WORKFLOW_PROTOCOL_VERSION,
            APPROVAL_PROTOCOL_VERSION => APPROVAL_PROTOCOL_VERSION,
            EFFECT_PROTOCOL_VERSION => EFFECT_PROTOCOL_VERSION,
            bookmark_preview722::BOOKMARK_PREVIEW_PROTOCOL => bookmark_preview722::BOOKMARK_PREVIEW_PROTOCOL,
            _ => return Err((None, Some(request_id), DaemonError::Request)),
        };
        let supplied = Zeroizing::new(std::mem::take(&mut request.session_token));
        if !token.matches(supplied.as_bytes()) {
            return Err((Some(protocol), Some(request_id), DaemonError::Request));
        }
        let result = match (protocol, request.method) {
            (bookmark_preview722::BOOKMARK_PREVIEW_PROTOCOL, PrivateMethod::StageBookmarkPreview) => {
                bookmark_preview722::unique_request(bytes)
                    .map_err(|error| (Some(protocol), Some(request_id.clone()), error))?;
                let params = parse_exact_params(request.params)
                    .map_err(|error| (Some(protocol), Some(request_id.clone()), error))?;
                self.config.stage_bookmark_preview(params, runtime)
                    .map_err(|error| (Some(protocol), Some(request_id.clone()), error))?
            }
            (_, PrivateMethod::Health) => {
                parse_exact_params::<EmptyParams>(request.params)
                    .map_err(|error| (Some(protocol), Some(request_id.clone()), error))?;
                json!({
                    "status": "ready",
                    "target_profile": TARGET_PROFILE,
                    "automation_enabled": false,
                    "network_enabled": false,
                    "workspace_count": self.config.workspace_count(),
                    "config_sha256": self.config.digest(),
                })
            }
            (PROTOCOL_VERSION, PrivateMethod::AuthorizePath) => {
                let params = parse_exact_params::<AuthorizePathParams>(request.params)
                    .map_err(|error| (Some(protocol), Some(request_id.clone()), error))?;
                self.authorize_path(&params)
                    .map_err(|error| (Some(protocol), Some(request_id.clone()), error))?
            }
            (WORKFLOW_PROTOCOL_VERSION, PrivateMethod::Materialize) => {
                let params = parse_exact_params(request.params)
                    .map_err(|error| (Some(protocol), Some(request_id.clone()), error))?;
                self.materialize(&params)
                    .map_err(|error| (Some(protocol), Some(request_id.clone()), error))?
            }
            (WORKFLOW_PROTOCOL_VERSION, PrivateMethod::Diff) => {
                let params = parse_exact_params(request.params)
                    .map_err(|error| (Some(protocol), Some(request_id.clone()), error))?;
                self.diff(&params)
                    .map_err(|error| (Some(protocol), Some(request_id.clone()), error))?
            }
            (WORKFLOW_PROTOCOL_VERSION, PrivateMethod::Publish) => {
                let params = parse_exact_params(request.params)
                    .map_err(|error| (Some(protocol), Some(request_id.clone()), error))?;
                self.publish(&params)
                    .map_err(|error| (Some(protocol), Some(request_id.clone()), error))?
            }
            (WORKFLOW_PROTOCOL_VERSION, PrivateMethod::PrepareGitCommit) => {
                let params = parse_exact_params(request.params)
                    .map_err(|error| (Some(protocol), Some(request_id.clone()), error))?;
                self.prepare_git_commit(&params)
                    .map_err(|error| (Some(protocol), Some(request_id.clone()), error))?
            }
            (APPROVAL_PROTOCOL_VERSION, PrivateMethod::PrepareGitCommitApproval) => {
                let params = parse_exact_params(request.params)
                    .map_err(|error| (Some(protocol), Some(request_id.clone()), error))?;
                self.prepare_git_commit_approval(&params)
                    .map_err(|error| (Some(protocol), Some(request_id.clone()), error))?
            }
            (EFFECT_PROTOCOL_VERSION, PrivateMethod::ExecuteGitCommit) => {
                let params = parse_exact_params(request.params)
                    .map_err(|error| (Some(protocol), Some(request_id.clone()), error))?;
                let now = current_unix_seconds()
                    .map_err(|error| (Some(protocol), Some(request_id.clone()), error))?;
                self.approval
                    .as_ref()
                    .ok_or_else(|| {
                        (
                            Some(protocol),
                            Some(request_id.clone()),
                            DaemonError::Effect,
                        )
                    })?
                    .execute_git_commit(params, now)
                    .map_err(|error| (Some(protocol), Some(request_id.clone()), error))?
            }
            _ => {
                return Err((Some(protocol), Some(request_id), DaemonError::Request));
            }
        };
        Ok((protocol, request_id, result))
    }

    fn authorize_path(&self, params: &AuthorizePathParams) -> Result<Value, DaemonError> {
        if !valid_identifier(&params.workspace_id) {
            return Err(DaemonError::Workspace);
        }
        let workspace = self
            .config
            .workspaces
            .get(&params.workspace_id)
            .ok_or(DaemonError::Workspace)?;
        let relative = validate_relative_path(&params.relative_path)?;
        match params.access {
            PathAccess::ReadExisting => {
                let path = resolve_existing(&workspace.root, &relative)?;
                let metadata = fs::metadata(path).map_err(|_| DaemonError::Io)?;
                if !metadata.is_file() || metadata.len() > self.config.max_file_bytes {
                    return Err(DaemonError::Workspace);
                }
                Ok(json!({
                    "authorized": true,
                    "workspace_id": params.workspace_id,
                    "access": "read_existing",
                    "path_kind": "existing_file",
                    "size_bytes": metadata.len(),
                }))
            }
            PathAccess::CreateOutput => {
                if relative.components().next().and_then(component_text) != Some("output") {
                    return Err(DaemonError::Workspace);
                }
                let candidate = workspace.root.join(&relative);
                if fs::symlink_metadata(&candidate).is_ok() {
                    return Err(DaemonError::Workspace);
                }
                let parent = candidate.parent().ok_or(DaemonError::Workspace)?;
                reject_links_between(&workspace.root, parent)?;
                let canonical_parent = parent.canonicalize().map_err(|_| DaemonError::Workspace)?;
                if !canonical_parent.starts_with(&workspace.root) {
                    return Err(DaemonError::Workspace);
                }
                Ok(json!({
                    "authorized": true,
                    "workspace_id": params.workspace_id,
                    "access": "create_output",
                    "path_kind": "creatable_output",
                }))
            }
        }
    }

    fn materialize(&self, params: &MaterializeParams) -> Result<Value, DaemonError> {
        if !valid_identifier(&params.fixture_id) || !valid_identifier(&params.operation_id) {
            return Err(DaemonError::Workspace);
        }
        let digest = parse_digest(&params.expected_sha256)?;
        let slot = match params.slot {
            WorkflowSlot::Source => MaterializeSlot::Source,
            WorkflowSlot::Candidate => MaterializeSlot::Candidate,
        };
        let input_relative = format!("input/{}.hwpx", params.fixture_id);
        let receipt = self
            .config
            .workflow(&params.workspace_id)?
            .materialize(&params.operation_id, slot, &input_relative, &digest)
            .map_err(|_| DaemonError::Workspace)?;
        Ok(json!({
            "workspace_id": params.workspace_id,
            "operation_id": receipt.operation_id,
            "slot": params.slot,
            "sha256": receipt.sha256,
            "size_bytes": receipt.size_bytes,
        }))
    }

    fn diff(&self, params: &DiffParams) -> Result<Value, DaemonError> {
        if !valid_identifier(&params.operation_id) {
            return Err(DaemonError::Workspace);
        }
        let receipt = self
            .config
            .workflow(&params.workspace_id)?
            .diff(&params.operation_id)
            .map_err(|_| DaemonError::Workspace)?;
        Ok(json!({
            "workspace_id": params.workspace_id,
            "operation_id": receipt.operation_id,
            "identical": receipt.identical,
            "source": {
                "sha256": receipt.source.sha256,
                "size_bytes": receipt.source.size_bytes,
            },
            "candidate": {
                "sha256": receipt.candidate.sha256,
                "size_bytes": receipt.candidate.size_bytes,
            },
        }))
    }

    fn publish(&self, params: &PublishParams) -> Result<Value, DaemonError> {
        if !valid_identifier(&params.operation_id) || !valid_identifier(&params.output_id) {
            return Err(DaemonError::Workspace);
        }
        let digest = parse_digest(&params.expected_sha256)?;
        let output_name = format!("{}.hwpx", params.output_id);
        let receipt = self
            .config
            .workflow(&params.workspace_id)?
            .publish(&params.operation_id, &output_name, &digest)
            .map_err(|_| DaemonError::Workspace)?;
        Ok(json!({
            "workspace_id": params.workspace_id,
            "operation_id": receipt.operation_id,
            "output_id": params.output_id,
            "sha256": receipt.sha256,
            "size_bytes": receipt.size_bytes,
        }))
    }

    fn prepare_git_commit(&self, params: &PrepareGitCommitParams) -> Result<Value, DaemonError> {
        if !valid_identifier(&params.output_id) {
            return Err(DaemonError::Workspace);
        }
        let digest = parse_digest(&params.expected_sha256)?;
        let output_name = format!("{}.hwpx", params.output_id);
        let plan = self
            .config
            .workflow(&params.workspace_id)?
            .prepare_git_commit(&output_name, &digest, &params.message)
            .map_err(|_| DaemonError::Workspace)?;
        Ok(json!({
            "workspace_id": params.workspace_id,
            "output_id": params.output_id,
            "output_pathspec": plan.output_pathspec,
            "expected_output_sha256": plan.expected_output_sha256,
            "expected_head": plan.expected_head,
            "message": plan.message,
            "executed": false,
        }))
    }

    fn prepare_git_commit_approval(
        &self,
        params: &PrepareGitCommitApprovalParams,
    ) -> Result<Value, DaemonError> {
        if !valid_identifier(&params.operation_id) || !valid_identifier(&params.output_id) {
            return Err(DaemonError::Workspace);
        }
        let digest = parse_digest(&params.expected_sha256)?;
        let output_name = format!("{}.hwpx", params.output_id);
        let workflow = self.config.workflow(&params.workspace_id)?;
        let plan = workflow
            .prepare_git_commit(&output_name, &digest, &params.message)
            .map_err(|_| DaemonError::Workspace)?;
        let target_sha256 = workflow
            .git_approval_target_sha256()
            .map_err(|_| DaemonError::Workspace)?;
        let plan_sha256 = plan.approval_plan_sha256();
        Ok(json!({
            "workspace_id": params.workspace_id,
            "operation_id": params.operation_id,
            "output_id": params.output_id,
            "output_pathspec": plan.output_pathspec,
            "expected_output_sha256": plan.expected_output_sha256,
            "expected_head": plan.expected_head,
            "expected_head_reference": plan.expected_head_reference,
            "message": plan.message,
            "approval": {
                "effect": "git_commit",
                "target_sha256": target_sha256,
                "plan_sha256": plan_sha256,
            },
            "executed": false,
        }))
    }
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct PrivateRequest {
    protocol_version: String,
    request_id: String,
    session_token: String,
    method: PrivateMethod,
    params: Value,
}

#[derive(Clone, Copy, Deserialize)]
#[serde(rename_all = "snake_case")]
enum PrivateMethod {
    Health,
    StageBookmarkPreview,
    AuthorizePath,
    Materialize,
    Diff,
    Publish,
    PrepareGitCommit,
    PrepareGitCommitApproval,
    ExecuteGitCommit,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct EmptyParams {}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct AuthorizePathParams {
    workspace_id: String,
    relative_path: String,
    access: PathAccess,
}

#[derive(Clone, Copy, Deserialize, Serialize)]
#[serde(rename_all = "snake_case")]
enum WorkflowSlot {
    Source,
    Candidate,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct MaterializeParams {
    workspace_id: String,
    operation_id: String,
    slot: WorkflowSlot,
    fixture_id: String,
    expected_sha256: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct DiffParams {
    workspace_id: String,
    operation_id: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct PublishParams {
    workspace_id: String,
    operation_id: String,
    output_id: String,
    expected_sha256: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct PrepareGitCommitParams {
    workspace_id: String,
    output_id: String,
    expected_sha256: String,
    message: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct PrepareGitCommitApprovalParams {
    workspace_id: String,
    operation_id: String,
    output_id: String,
    expected_sha256: String,
    message: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ExecuteGitCommitParams {
    workspace_id: String,
    operation_id: String,
    output_id: String,
    expected_sha256: String,
    message: String,
    actor_sha256: String,
    tenant_sha256: String,
    requested_at_unix_seconds: u64,
    confirmation_token: String,
}

#[derive(Clone, Copy, Deserialize)]
#[serde(rename_all = "snake_case")]
enum PathAccess {
    ReadExisting,
    CreateOutput,
}

fn parse_exact_params<T>(value: Value) -> Result<T, DaemonError>
where
    T: for<'de> Deserialize<'de>,
{
    serde_json::from_value(value).map_err(|_| DaemonError::Request)
}

#[derive(Serialize)]
struct PrivateResponse<'a> {
    protocol_version: &'a str,
    request_id: &'a str,
    ok: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    result: Option<Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<&'static str>,
}

fn response_ok<'a>(protocol_version: &'a str, request_id: &'a str, result: Value) -> Value {
    serde_json::to_value(PrivateResponse {
        protocol_version,
        request_id,
        ok: true,
        result: Some(result),
        error: None,
    })
    .unwrap_or_else(|_| response_error(PROTOCOL_VERSION, "invalid"))
}

fn response_error(protocol_version: &str, request_id: &str) -> Value {
    json!({
        "protocol_version": protocol_version,
        "request_id": request_id,
        "ok": false,
        "error": "request_rejected",
    })
}

fn parse_digest(value: &str) -> Result<[u8; 32], DaemonError> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || matches!(byte, b'a'..=b'f'))
    {
        return Err(DaemonError::Request);
    }
    let mut digest = [0_u8; 32];
    hex::decode_to_slice(value, &mut digest).map_err(|_| DaemonError::Request)?;
    if digest == [0; 32] {
        return Err(DaemonError::Request);
    }
    Ok(digest)
}

fn valid_identifier(value: &str) -> bool {
    (1..=64).contains(&value.len())
        && value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'_'))
}

fn validate_relative_path(value: &str) -> Result<PathBuf, DaemonError> {
    if value.is_empty() || value.len() > MAX_RELATIVE_PATH_BYTES || value.contains('\0') {
        return Err(DaemonError::Workspace);
    }
    let path = Path::new(value);
    if path.is_absolute() {
        return Err(DaemonError::Workspace);
    }
    let mut count = 0_usize;
    for component in path.components() {
        let Component::Normal(part) = component else {
            return Err(DaemonError::Workspace);
        };
        let text = part.to_str().ok_or(DaemonError::Workspace)?;
        if !valid_windows_component(text) {
            return Err(DaemonError::Workspace);
        }
        count += 1;
        if count > MAX_PATH_COMPONENTS {
            return Err(DaemonError::Workspace);
        }
    }
    if count == 0 {
        return Err(DaemonError::Workspace);
    }
    Ok(path.to_path_buf())
}

fn valid_windows_component(value: &str) -> bool {
    if value.is_empty()
        || value.ends_with([' ', '.'])
        || value
            .chars()
            .any(|character| character <= '\u{1f}' || "<>:\"/\\|?*".contains(character))
    {
        return false;
    }
    let stem = value
        .split('.')
        .next()
        .unwrap_or_default()
        .to_ascii_uppercase();
    !matches!(
        stem.as_str(),
        "CON"
            | "PRN"
            | "AUX"
            | "NUL"
            | "CLOCK$"
            | "CONIN$"
            | "CONOUT$"
            | "COM1"
            | "COM2"
            | "COM3"
            | "COM4"
            | "COM5"
            | "COM6"
            | "COM7"
            | "COM8"
            | "COM9"
            | "LPT1"
            | "LPT2"
            | "LPT3"
            | "LPT4"
            | "LPT5"
            | "LPT6"
            | "LPT7"
            | "LPT8"
            | "LPT9"
    )
}

fn resolve_existing(root: &Path, relative: &Path) -> Result<PathBuf, DaemonError> {
    let candidate = root.join(relative);
    reject_links_between(root, &candidate)?;
    let resolved = candidate
        .canonicalize()
        .map_err(|_| DaemonError::Workspace)?;
    if !resolved.starts_with(root) {
        return Err(DaemonError::Workspace);
    }
    Ok(resolved)
}

fn reject_links_between(root: &Path, candidate: &Path) -> Result<(), DaemonError> {
    let relative = candidate
        .strip_prefix(root)
        .map_err(|_| DaemonError::Workspace)?;
    let mut current = root.to_path_buf();
    if !is_directory_without_link(&current) {
        return Err(DaemonError::Workspace);
    }
    for component in relative.components() {
        let Component::Normal(part) = component else {
            return Err(DaemonError::Workspace);
        };
        current.push(part);
        match fs::symlink_metadata(&current) {
            Ok(metadata) if is_link_or_reparse(&metadata) => {
                return Err(DaemonError::Workspace);
            }
            Ok(_) => {}
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => break,
            Err(_) => return Err(DaemonError::Io),
        }
    }
    Ok(())
}

fn is_directory_without_link(path: &Path) -> bool {
    fs::symlink_metadata(path)
        .is_ok_and(|metadata| metadata.is_dir() && !is_link_or_reparse(&metadata))
}

fn is_link_or_reparse(metadata: &fs::Metadata) -> bool {
    if metadata.file_type().is_symlink() {
        return true;
    }
    #[cfg(windows)]
    {
        use std::os::windows::fs::MetadataExt as _;
        const FILE_ATTRIBUTE_REPARSE_POINT: u32 = 0x0400;
        metadata.file_attributes() & FILE_ATTRIBUTE_REPARSE_POINT != 0
    }
    #[cfg(not(windows))]
    {
        false
    }
}

fn component_text(component: Component<'_>) -> Option<&str> {
    match component {
        Component::Normal(value) => value.to_str(),
        _ => None,
    }
}

fn path_identity(path: &Path) -> Result<String, DaemonError> {
    let value = path.to_str().ok_or(DaemonError::Configuration)?;
    #[cfg(windows)]
    {
        Ok(value.replace('/', "\\").to_lowercase())
    }
    #[cfg(not(windows))]
    {
        Ok(value.to_owned())
    }
}

fn hex_digest(bytes: &[u8]) -> String {
    hex::encode(Sha256::digest(bytes))
}

fn current_unix_seconds() -> Result<u64, DaemonError> {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|duration| duration.as_secs())
        .map_err(|_| DaemonError::Effect)
}
