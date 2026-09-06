#![forbid(unsafe_code)]

use std::ffi::OsStr;
use std::fs::{self, File, OpenOptions};
use std::io::{Read as _, Write as _};
use std::path::{Path, PathBuf};
use std::process::{Command, ExitStatus, Stdio};

use approval_policy::{
    ApprovalError, ApprovalReceipt, ApprovalScope, AuthorizedEffect, EffectKind, EffectRequest,
};
use local_workflow::{GitCommitPlan, LocalWorkflow, MAX_WORKFLOW_FILE_BYTES};
use sha2::{Digest as _, Sha256};
use tempfile::TempDir;
use thiserror::Error;

const APPROVAL_RECEIPT_SCHEMA: &str = "hwpx-agent.approval-receipt/v1";
const MAX_OPERATION_ID_BYTES: usize = 120;
const MAX_GIT_OUTPUT_BYTES: usize = 256;
const COPY_BUFFER_BYTES: usize = 64 * 1024;

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct GitCommitEffectInput {
    operation_id: String,
    output_name: String,
    expected_output_sha256: [u8; 32],
    message: String,
}

impl GitCommitEffectInput {
    /// Creates one semantic Git commit request without accepting a command string.
    ///
    /// # Errors
    ///
    /// Rejects malformed operation IDs. Output and message validation is repeated by the workflow.
    pub fn new(
        operation_id: String,
        output_name: String,
        expected_output_sha256: [u8; 32],
        message: String,
    ) -> Result<Self, GitEffectError> {
        if !(12..=MAX_OPERATION_ID_BYTES).contains(&operation_id.len())
            || !operation_id.starts_with("op_")
            || !operation_id
                .bytes()
                .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'_' | b'-'))
            || expected_output_sha256 == [0; 32]
        {
            return Err(GitEffectError::RequestRejected);
        }
        Ok(Self {
            operation_id,
            output_name,
            expected_output_sha256,
            message,
        })
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct GitCommitEffectReceipt {
    pub schema_version: &'static str,
    pub commit_oid: String,
    pub previous_head: String,
    pub updated_reference: Option<String>,
    pub output_sha256: String,
    pub target_sha256: String,
    pub plan_sha256: String,
    pub approval: ApprovalReceipt,
    pub index_synchronized: bool,
}

impl std::fmt::Debug for GitCommitEffectReceipt {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("GitCommitEffectReceipt")
            .field("schema_version", &self.schema_version)
            .field("commit_oid", &self.commit_oid)
            .field("updated_reference", &self.updated_reference)
            .field("index_synchronized", &self.index_synchronized)
            .finish_non_exhaustive()
    }
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum GitEffectError {
    #[error("Git effect configuration rejected")]
    ConfigurationRejected,
    #[error("Git effect request rejected")]
    RequestRejected,
    #[error("Git effect authorization rejected")]
    AuthorizationRejected,
    #[error("Git effect authorization is stale")]
    AuthorizationStale,
    #[error("Git workflow state rejected")]
    WorkflowRejected,
    #[error("Git process unavailable")]
    GitUnavailable,
    #[error("Git repository state rejected")]
    GitStateRejected,
    #[error("Git reference changed concurrently")]
    ReferenceConflict,
    #[error("Git commit completed but index synchronization failed")]
    IndexSynchronizationFailed,
}

impl From<ApprovalError> for GitEffectError {
    fn from(_: ApprovalError) -> Self {
        Self::RequestRejected
    }
}

#[derive(Clone)]
pub struct GitEffectHost {
    root: PathBuf,
    git_program: PathBuf,
    max_file_bytes: u64,
    max_execution_delay_seconds: u64,
}

impl std::fmt::Debug for GitEffectHost {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("GitEffectHost")
            .field("root", &"<redacted>")
            .field("git_program", &"<redacted>")
            .field("max_file_bytes", &self.max_file_bytes)
            .field(
                "max_execution_delay_seconds",
                &self.max_execution_delay_seconds,
            )
            .finish()
    }
}

impl GitEffectHost {
    /// Opens a workspace-bound host around one explicit Git executable.
    ///
    /// # Errors
    ///
    /// Rejects relative/link executables, unsafe limits and invalid workspaces.
    pub fn open(
        root: &Path,
        git_program: &Path,
        max_file_bytes: u64,
        max_execution_delay_seconds: u64,
    ) -> Result<Self, GitEffectError> {
        if !git_program.is_absolute()
            || !(1..=MAX_WORKFLOW_FILE_BYTES).contains(&max_file_bytes)
            || !(1..=60).contains(&max_execution_delay_seconds)
        {
            return Err(GitEffectError::ConfigurationRejected);
        }
        let git_metadata =
            fs::symlink_metadata(git_program).map_err(|_| GitEffectError::ConfigurationRejected)?;
        if !git_metadata.is_file() || is_link_or_reparse(&git_metadata) {
            return Err(GitEffectError::ConfigurationRejected);
        }
        let git_program = git_program
            .canonicalize()
            .map_err(|_| GitEffectError::ConfigurationRejected)?;
        let workflow = LocalWorkflow::open(root, max_file_bytes)
            .map_err(|_| GitEffectError::ConfigurationRejected)?;
        let root = root
            .canonicalize()
            .map_err(|_| GitEffectError::ConfigurationRejected)?;
        let host = Self {
            root,
            git_program,
            max_file_bytes,
            max_execution_delay_seconds,
        };
        let temporary = tempfile::tempdir().map_err(|_| GitEffectError::GitUnavailable)?;
        let version = host.run_git(&[OsStr::new("--version")], None, None, &temporary)?;
        if !version.status.success() || !version.stdout.starts_with(b"git version ") {
            return Err(GitEffectError::ConfigurationRejected);
        }
        let _ = workflow;
        Ok(host)
    }

    /// Rebuilds current Git state and creates the only approval request this host will execute.
    ///
    /// # Errors
    ///
    /// Rejects malformed identities and any output, digest, message, repository or path drift.
    pub fn prepare_approval_request(
        &self,
        input: &GitCommitEffectInput,
        actor_sha256: String,
        tenant_sha256: String,
        requested_at_unix_seconds: u64,
    ) -> Result<EffectRequest, GitEffectError> {
        let workflow = LocalWorkflow::open(&self.root, self.max_file_bytes)
            .map_err(|_| GitEffectError::WorkflowRejected)?;
        let plan = workflow
            .prepare_git_commit(
                &input.output_name,
                &input.expected_output_sha256,
                &input.message,
            )
            .map_err(|_| GitEffectError::WorkflowRejected)?;
        let target_sha256 = workflow
            .git_approval_target_sha256()
            .map_err(|_| GitEffectError::WorkflowRejected)?;
        EffectRequest::new(
            input.operation_id.clone(),
            actor_sha256,
            tenant_sha256,
            EffectKind::GitCommit,
            target_sha256,
            plan.approval_plan_sha256(),
            requested_at_unix_seconds,
        )
        .map_err(Into::into)
    }

    /// Executes exactly one approved output-file commit through Git plumbing and a ref CAS.
    ///
    /// # Errors
    ///
    /// Fails closed for stale/mismatched approval, workspace drift, staged target changes, Git
    /// failures, reference races and post-commit index synchronization failure.
    pub fn execute_git_commit(
        &self,
        input: &GitCommitEffectInput,
        authorization: AuthorizedEffect,
        now_unix_seconds: u64,
    ) -> Result<GitCommitEffectReceipt, GitEffectError> {
        let workflow = LocalWorkflow::open(&self.root, self.max_file_bytes)
            .map_err(|_| GitEffectError::WorkflowRejected)?;
        let plan = workflow
            .prepare_git_commit(
                &input.output_name,
                &input.expected_output_sha256,
                &input.message,
            )
            .map_err(|_| GitEffectError::WorkflowRejected)?;
        let target_sha256 = workflow
            .git_approval_target_sha256()
            .map_err(|_| GitEffectError::WorkflowRejected)?;
        let plan_sha256 = plan.approval_plan_sha256();
        validate_authorization(
            input,
            &authorization,
            &target_sha256,
            &plan_sha256,
            now_unix_seconds,
            self.max_execution_delay_seconds,
        )?;
        let approval = authorization.into_receipt();
        let temporary = tempfile::tempdir().map_err(|_| GitEffectError::GitUnavailable)?;
        let objects = build_commit_objects(self, &workflow, input, &plan, &temporary)?;
        publish_commit(self, &workflow, input, &plan, &objects, &temporary)?;

        Ok(GitCommitEffectReceipt {
            schema_version: "hwpx-agent.git-commit-effect-receipt/v1",
            commit_oid: objects.commit_oid,
            previous_head: plan.expected_head,
            updated_reference: plan.expected_head_reference,
            output_sha256: hex::encode(input.expected_output_sha256),
            target_sha256,
            plan_sha256,
            approval,
            index_synchronized: true,
        })
    }

    fn run_git(
        &self,
        arguments: &[&OsStr],
        input: Option<&[u8]>,
        index: Option<&Path>,
        temporary: &TempDir,
    ) -> Result<GitOutput, GitEffectError> {
        let hooks = temporary.path().join("empty-hooks");
        fs::create_dir_all(&hooks).map_err(|_| GitEffectError::GitUnavailable)?;
        let hooks_config = format!("core.hooksPath={}", hooks.display());
        let mut command = Command::new(&self.git_program);
        command
            .arg("-C")
            .arg(&self.root)
            .arg("-c")
            .arg(&hooks_config)
            .arg("-c")
            .arg("core.fsmonitor=false")
            .args(arguments)
            .env_clear()
            .env("GIT_CONFIG_NOSYSTEM", "1")
            .env("GIT_CONFIG_GLOBAL", null_device())
            .env("GIT_NO_REPLACE_OBJECTS", "1")
            .env("GIT_TERMINAL_PROMPT", "0")
            .env("GCM_INTERACTIVE", "Never")
            .env("LC_ALL", "C")
            .env("TEMP", temporary.path())
            .env("TMP", temporary.path())
            .stdin(if input.is_some() {
                Stdio::piped()
            } else {
                Stdio::null()
            })
            .stdout(Stdio::piped())
            .stderr(Stdio::null());
        if let Some(index) = index {
            command.env("GIT_INDEX_FILE", index);
        }
        for name in ["SystemRoot", "WINDIR"] {
            if let Some(value) = std::env::var_os(name) {
                command.env(name, value);
            }
        }
        let mut child = command
            .spawn()
            .map_err(|_| GitEffectError::GitUnavailable)?;
        if let Some(input) = input {
            let Some(mut stdin) = child.stdin.take() else {
                terminate_child(&mut child);
                return Err(GitEffectError::GitUnavailable);
            };
            if stdin.write_all(input).is_err() {
                terminate_child(&mut child);
                return Err(GitEffectError::GitUnavailable);
            }
        }
        let Some(stdout) = child.stdout.take() else {
            terminate_child(&mut child);
            return Err(GitEffectError::GitUnavailable);
        };
        let output_limit =
            u64::try_from(MAX_GIT_OUTPUT_BYTES).map_err(|_| GitEffectError::GitUnavailable)? + 1;
        let mut stdout = stdout.take(output_limit);
        let mut bytes = Vec::new();
        if stdout.read_to_end(&mut bytes).is_err() || bytes.len() > MAX_GIT_OUTPUT_BYTES {
            terminate_child(&mut child);
            return Err(GitEffectError::GitUnavailable);
        }
        let status = child.wait().map_err(|_| GitEffectError::GitUnavailable)?;
        Ok(GitOutput {
            status,
            stdout: bytes,
        })
    }
}

struct GitOutput {
    status: ExitStatus,
    stdout: Vec<u8>,
}

fn terminate_child(child: &mut std::process::Child) {
    let _ = child.kill();
    let _ = child.wait();
}

struct GitObjectSet {
    blob_oid: String,
    commit_oid: String,
}

fn build_commit_objects(
    host: &GitEffectHost,
    workflow: &LocalWorkflow,
    input: &GitCommitEffectInput,
    plan: &GitCommitPlan,
    temporary: &TempDir,
) -> Result<GitObjectSet, GitEffectError> {
    if !target_index_is_clean(host, plan, temporary)? {
        return Err(GitEffectError::GitStateRejected);
    }
    let snapshot = temporary.path().join("approved-output.snapshot");
    snapshot_output(
        &host.root,
        &plan.output_pathspec,
        &snapshot,
        &input.expected_output_sha256,
        host.max_file_bytes,
    )?;
    require_same_plan(workflow, input, plan)?;
    let blob_oid = parse_oid(
        &host.run_git(
            &[
                OsStr::new("hash-object"),
                OsStr::new("-w"),
                OsStr::new("--no-filters"),
                OsStr::new("--"),
                snapshot.as_os_str(),
            ],
            None,
            None,
            temporary,
        )?,
        plan.expected_head.len(),
    )?;
    let temporary_index = temporary.path().join("approval.index");
    let read_tree = host.run_git(
        &[OsStr::new("read-tree"), OsStr::new(&plan.expected_head)],
        None,
        Some(&temporary_index),
        temporary,
    )?;
    require_success(&read_tree)?;
    update_index_entry(
        host,
        &blob_oid,
        &plan.output_pathspec,
        Some(&temporary_index),
        temporary,
    )?;
    let tree_oid = parse_oid(
        &host.run_git(
            &[OsStr::new("write-tree")],
            None,
            Some(&temporary_index),
            temporary,
        )?,
        plan.expected_head.len(),
    )?;
    let parent_tree_expression = format!("{}^{{tree}}", plan.expected_head);
    let parent_tree_oid = parse_oid(
        &host.run_git(
            &[OsStr::new("rev-parse"), OsStr::new(&parent_tree_expression)],
            None,
            None,
            temporary,
        )?,
        plan.expected_head.len(),
    )?;
    if tree_oid == parent_tree_oid {
        return Err(GitEffectError::GitStateRejected);
    }
    let mut message = input.message.as_bytes().to_vec();
    message.push(b'\n');
    let commit_oid = parse_oid(
        &host.run_git(
            &[
                OsStr::new("commit-tree"),
                OsStr::new(&tree_oid),
                OsStr::new("-p"),
                OsStr::new(&plan.expected_head),
            ],
            Some(&message),
            None,
            temporary,
        )?,
        plan.expected_head.len(),
    )?;
    Ok(GitObjectSet {
        blob_oid,
        commit_oid,
    })
}

fn publish_commit(
    host: &GitEffectHost,
    workflow: &LocalWorkflow,
    input: &GitCommitEffectInput,
    plan: &GitCommitPlan,
    objects: &GitObjectSet,
    temporary: &TempDir,
) -> Result<(), GitEffectError> {
    if !target_index_is_clean(host, plan, temporary)? {
        return Err(GitEffectError::GitStateRejected);
    }
    require_same_plan(workflow, input, plan)?;
    update_reference_transaction(host, plan, &objects.commit_oid, temporary)?;
    update_index_entry(
        host,
        &objects.blob_oid,
        &plan.output_pathspec,
        None,
        temporary,
    )
    .map_err(|_| GitEffectError::IndexSynchronizationFailed)?;
    verify_updated_state(
        host,
        plan,
        &objects.commit_oid,
        &objects.blob_oid,
        temporary,
    )
    .map_err(|_| GitEffectError::IndexSynchronizationFailed)
}

fn require_same_plan(
    workflow: &LocalWorkflow,
    input: &GitCommitEffectInput,
    expected: &GitCommitPlan,
) -> Result<(), GitEffectError> {
    let observed = workflow
        .prepare_git_commit(
            &input.output_name,
            &input.expected_output_sha256,
            &input.message,
        )
        .map_err(|_| GitEffectError::WorkflowRejected)?;
    if &observed == expected {
        Ok(())
    } else {
        Err(GitEffectError::GitStateRejected)
    }
}

fn validate_authorization(
    input: &GitCommitEffectInput,
    authorization: &AuthorizedEffect,
    target_sha256: &str,
    plan_sha256: &str,
    now_unix_seconds: u64,
    max_execution_delay_seconds: u64,
) -> Result<(), GitEffectError> {
    let receipt = authorization.receipt();
    if authorization.effect() != EffectKind::GitCommit
        || receipt.schema_version != APPROVAL_RECEIPT_SCHEMA
        || receipt.effect != EffectKind::GitCommit
        || receipt.required_scope != ApprovalScope::WorkstationControl
        || receipt.operation_sha256 != digest(input.operation_id.as_bytes())
        || receipt.target_sha256 != target_sha256
        || receipt.plan_sha256 != plan_sha256
    {
        return Err(GitEffectError::AuthorizationRejected);
    }
    if receipt.approved_at_unix_seconds > now_unix_seconds
        || now_unix_seconds - receipt.approved_at_unix_seconds > max_execution_delay_seconds
    {
        return Err(GitEffectError::AuthorizationStale);
    }
    Ok(())
}

fn target_index_is_clean(
    host: &GitEffectHost,
    plan: &GitCommitPlan,
    temporary: &TempDir,
) -> Result<bool, GitEffectError> {
    let output = host.run_git(
        &[
            OsStr::new("diff-index"),
            OsStr::new("--cached"),
            OsStr::new("--quiet"),
            OsStr::new("--no-ext-diff"),
            OsStr::new("--ignore-submodules=all"),
            OsStr::new(&plan.expected_head),
            OsStr::new("--"),
            OsStr::new(&plan.output_pathspec),
        ],
        None,
        None,
        temporary,
    )?;
    match output.status.code() {
        Some(0) => Ok(true),
        Some(1) => Ok(false),
        _ => Err(GitEffectError::GitUnavailable),
    }
}

fn snapshot_output(
    root: &Path,
    pathspec: &str,
    destination: &Path,
    expected_sha256: &[u8; 32],
    max_file_bytes: u64,
) -> Result<(), GitEffectError> {
    let source_path = root.join(pathspec);
    let source_metadata =
        fs::symlink_metadata(&source_path).map_err(|_| GitEffectError::WorkflowRejected)?;
    if !source_metadata.is_file()
        || is_link_or_reparse(&source_metadata)
        || source_metadata.len() == 0
        || source_metadata.len() > max_file_bytes
    {
        return Err(GitEffectError::WorkflowRejected);
    }
    let resolved = source_path
        .canonicalize()
        .map_err(|_| GitEffectError::WorkflowRejected)?;
    if !resolved.starts_with(root) {
        return Err(GitEffectError::WorkflowRejected);
    }
    let mut source = File::open(resolved).map_err(|_| GitEffectError::WorkflowRejected)?;
    let mut target = OpenOptions::new()
        .create_new(true)
        .write(true)
        .open(destination)
        .map_err(|_| GitEffectError::GitUnavailable)?;
    let mut hasher = Sha256::new();
    let mut size = 0_u64;
    let mut buffer = vec![0_u8; COPY_BUFFER_BYTES].into_boxed_slice();
    loop {
        let count = source
            .read(&mut buffer)
            .map_err(|_| GitEffectError::WorkflowRejected)?;
        if count == 0 {
            break;
        }
        size = size
            .checked_add(u64::try_from(count).map_err(|_| GitEffectError::WorkflowRejected)?)
            .ok_or(GitEffectError::WorkflowRejected)?;
        if size > max_file_bytes {
            return Err(GitEffectError::WorkflowRejected);
        }
        hasher.update(&buffer[..count]);
        target
            .write_all(&buffer[..count])
            .map_err(|_| GitEffectError::GitUnavailable)?;
    }
    target
        .sync_all()
        .map_err(|_| GitEffectError::GitUnavailable)?;
    let observed: [u8; 32] = hasher.finalize().into();
    if size == 0 || &observed != expected_sha256 {
        return Err(GitEffectError::WorkflowRejected);
    }
    Ok(())
}

fn update_index_entry(
    host: &GitEffectHost,
    blob_oid: &str,
    pathspec: &str,
    index: Option<&Path>,
    temporary: &TempDir,
) -> Result<(), GitEffectError> {
    let mut record = format!("100644 {blob_oid}\t{pathspec}").into_bytes();
    record.push(0);
    let output = host.run_git(
        &[
            OsStr::new("update-index"),
            OsStr::new("-z"),
            OsStr::new("--index-info"),
        ],
        Some(&record),
        index,
        temporary,
    )?;
    require_success(&output)
}

fn update_reference_transaction(
    host: &GitEffectHost,
    plan: &GitCommitPlan,
    commit_oid: &str,
    temporary: &TempDir,
) -> Result<(), GitEffectError> {
    let transaction = if let Some(reference) = plan.expected_head_reference.as_deref() {
        format!(
            "start\nupdate {reference} {commit_oid} {}\nprepare\ncommit\n",
            plan.expected_head
        )
    } else {
        format!(
            "start\noption no-deref\nupdate HEAD {commit_oid} {}\nprepare\ncommit\n",
            plan.expected_head
        )
    };
    let output = host.run_git(
        &[OsStr::new("update-ref"), OsStr::new("--stdin")],
        Some(transaction.as_bytes()),
        None,
        temporary,
    )?;
    if output.status.success() {
        Ok(())
    } else {
        Err(GitEffectError::ReferenceConflict)
    }
}

fn verify_updated_state(
    host: &GitEffectHost,
    plan: &GitCommitPlan,
    commit_oid: &str,
    blob_oid: &str,
    temporary: &TempDir,
) -> Result<(), GitEffectError> {
    let reference = plan.expected_head_reference.as_deref().unwrap_or("HEAD");
    let observed_commit = parse_oid(
        &host.run_git(
            &[OsStr::new("rev-parse"), OsStr::new(reference)],
            None,
            None,
            temporary,
        )?,
        plan.expected_head.len(),
    )?;
    if observed_commit != commit_oid {
        return Err(GitEffectError::GitStateRejected);
    }
    let output = host.run_git(
        &[
            OsStr::new("ls-files"),
            OsStr::new("--stage"),
            OsStr::new("--"),
            OsStr::new(&plan.output_pathspec),
        ],
        None,
        None,
        temporary,
    )?;
    require_success(&output)?;
    let line = bounded_line(&output.stdout)?;
    let expected = format!("100644 {blob_oid} 0\t{}", plan.output_pathspec);
    if line != expected {
        return Err(GitEffectError::GitStateRejected);
    }
    Ok(())
}

fn require_success(output: &GitOutput) -> Result<(), GitEffectError> {
    if output.status.success() {
        Ok(())
    } else {
        Err(GitEffectError::GitUnavailable)
    }
}

fn parse_oid(output: &GitOutput, expected_length: usize) -> Result<String, GitEffectError> {
    if !output.status.success() {
        return Err(GitEffectError::GitUnavailable);
    }
    let value = bounded_line(&output.stdout)?;
    if value.len() != expected_length
        || !matches!(value.len(), 40 | 64)
        || !value.bytes().all(|byte| byte.is_ascii_hexdigit())
        || value.bytes().all(|byte| byte == b'0')
    {
        return Err(GitEffectError::GitUnavailable);
    }
    Ok(value.to_ascii_lowercase())
}

fn bounded_line(bytes: &[u8]) -> Result<String, GitEffectError> {
    let value = std::str::from_utf8(bytes).map_err(|_| GitEffectError::GitUnavailable)?;
    let value = value.strip_suffix('\n').unwrap_or(value);
    let value = value.strip_suffix('\r').unwrap_or(value);
    if value.is_empty() || value.contains(['\r', '\n', '\0']) {
        return Err(GitEffectError::GitUnavailable);
    }
    Ok(value.to_owned())
}

fn digest(value: &[u8]) -> String {
    hex::encode(Sha256::digest(value))
}

fn null_device() -> &'static OsStr {
    #[cfg(windows)]
    {
        OsStr::new("NUL")
    }
    #[cfg(not(windows))]
    {
        OsStr::new("/dev/null")
    }
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
