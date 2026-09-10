//! Exact local-bare-Git effect boundary for durable mirror push recovery.
//!
//! Planning writes only unreachable Git objects. Publishing is one `update-ref` compare-and-swap.
//! A stored plan can therefore be observed after a process crash without blindly repeating the
//! external effect. Network transports and production repository custody are intentionally absent.

use std::ffi::OsStr;
use std::fmt;
use std::fs;
use std::io::{Read as _, Write as _};
use std::path::{Path, PathBuf};
use std::process::{Command, ExitStatus, Stdio};

use revision_service::{BranchId, ProjectId, RevisionId};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use tempfile::TempDir;
use thiserror::Error;

const STATE_SCHEMA: &str = "hwpx-agent.git-mirror-state/v1";
const PLAN_SCHEMA: &str = "hwpx-agent.git-mirror-push-plan/v1";
const RECEIPT_SCHEMA: &str = "hwpx-agent.git-mirror-push-receipt/v1";
const STATE_PATH: &str = "mirror-state.json";
const MAX_GIT_OUTPUT_BYTES: usize = 16_384;
const MAX_PLAN_BYTES: usize = 4_096;

#[derive(Clone, Eq, PartialEq)]
pub struct GitMirrorPushInput {
    project_id: String,
    branch_id: String,
    expected_revision_id: Option<String>,
    expected_generation: u64,
    expected_snapshot_sha256: Option<String>,
    result_revision_id: String,
    result_snapshot_sha256: String,
    operation_plan_sha256: String,
    request_sha256: String,
}

impl GitMirrorPushInput {
    /// Constructs one fully bound next-generation Git mirror state.
    ///
    /// # Errors
    ///
    /// Rejects noncanonical identifiers/digests, inconsistent empty heads, generation overflow,
    /// or reuse of the expected revision identity.
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        project_id: String,
        branch_id: String,
        expected_revision_id: Option<String>,
        expected_generation: u64,
        expected_snapshot_sha256: Option<String>,
        result_revision_id: String,
        result_snapshot_sha256: String,
        operation_plan_sha256: String,
        request_sha256: String,
    ) -> Result<Self, GitMirrorEffectError> {
        ProjectId::parse(&project_id).map_err(|_| GitMirrorEffectError::RequestRejected)?;
        BranchId::parse(&branch_id).map_err(|_| GitMirrorEffectError::RequestRejected)?;
        let result = RevisionId::parse(&result_revision_id)
            .map_err(|_| GitMirrorEffectError::RequestRejected)?;
        let expected = expected_revision_id
            .as_deref()
            .map(RevisionId::parse)
            .transpose()
            .map_err(|_| GitMirrorEffectError::RequestRejected)?;
        if expected_revision_id.is_none() != (expected_generation == 0)
            || expected_snapshot_sha256.is_none() != (expected_generation == 0)
            || expected == Some(result)
            || expected_generation.checked_add(1).is_none()
            || expected_snapshot_sha256
                .as_deref()
                .is_some_and(|value| !valid_digest(value))
            || !valid_digest(&result_snapshot_sha256)
            || !valid_digest(&operation_plan_sha256)
            || !valid_digest(&request_sha256)
        {
            return Err(GitMirrorEffectError::RequestRejected);
        }
        Ok(Self {
            project_id,
            branch_id,
            expected_revision_id,
            expected_generation,
            expected_snapshot_sha256,
            result_revision_id,
            result_snapshot_sha256,
            operation_plan_sha256,
            request_sha256,
        })
    }

    #[must_use]
    pub const fn expected_generation(&self) -> u64 {
        self.expected_generation
    }

    #[must_use]
    pub const fn result_generation(&self) -> u64 {
        self.expected_generation + 1
    }

    #[must_use]
    pub fn result_revision_id(&self) -> &str {
        &self.result_revision_id
    }

    #[must_use]
    pub fn result_snapshot_sha256(&self) -> &str {
        &self.result_snapshot_sha256
    }
}

impl fmt::Debug for GitMirrorPushInput {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("GitMirrorPushInput")
            .field("project_id", &"<redacted>")
            .field("branch_id", &"<redacted>")
            .field("expected_generation", &self.expected_generation)
            .field("result_generation", &self.result_generation())
            .field("digests", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct GitMirrorPushPlan {
    schema_version: String,
    input_sha256: String,
    target_reference: String,
    expected_oid: Option<String>,
    result_oid: String,
    state_sha256: String,
}

impl GitMirrorPushPlan {
    /// Encodes the plan in its only accepted durable representation.
    ///
    /// # Errors
    ///
    /// Returns unavailable only if bounded serialization unexpectedly fails.
    pub fn encode(&self) -> Result<Vec<u8>, GitMirrorEffectError> {
        serde_json::to_vec(&PushPlanWire::from(self))
            .map_err(|_| GitMirrorEffectError::GitUnavailable)
    }

    /// Decodes an exact canonical plan suitable for later crash observation.
    ///
    /// # Errors
    ///
    /// Rejects whitespace, extra fields, malformed digests/OIDs/references and noncanonical bytes.
    pub fn decode(bytes: &[u8]) -> Result<Self, GitMirrorEffectError> {
        if bytes.is_empty() || bytes.len() > MAX_PLAN_BYTES {
            return Err(GitMirrorEffectError::PlanRejected);
        }
        let wire: PushPlanWire =
            serde_json::from_slice(bytes).map_err(|_| GitMirrorEffectError::PlanRejected)?;
        let plan = Self::from(wire);
        plan.validate()?;
        if plan.encode()?.as_slice() != bytes {
            return Err(GitMirrorEffectError::PlanRejected);
        }
        Ok(plan)
    }

    #[must_use]
    pub fn expected_oid(&self) -> Option<&str> {
        self.expected_oid.as_deref()
    }

    #[must_use]
    pub fn result_oid(&self) -> &str {
        &self.result_oid
    }

    #[must_use]
    pub fn state_sha256(&self) -> &str {
        &self.state_sha256
    }

    fn validate(&self) -> Result<(), GitMirrorEffectError> {
        if self.schema_version != PLAN_SCHEMA
            || !valid_digest(&self.input_sha256)
            || !valid_reference(&self.target_reference)
            || self
                .expected_oid
                .as_deref()
                .is_some_and(|oid| !valid_oid(oid) || oid.len() != self.result_oid.len())
            || !valid_oid(&self.result_oid)
            || !valid_digest(&self.state_sha256)
            || self.expected_oid.as_deref() == Some(self.result_oid.as_str())
        {
            return Err(GitMirrorEffectError::PlanRejected);
        }
        Ok(())
    }
}

impl fmt::Debug for GitMirrorPushPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("GitMirrorPushPlan")
            .field("schema_version", &self.schema_version)
            .field("has_expected_oid", &self.expected_oid.is_some())
            .field("identities", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum GitMirrorEffectObservation {
    NoEffect,
    Committed,
    Diverged,
}

#[derive(Clone, Eq, PartialEq)]
pub struct GitMirrorPushReceipt {
    pub schema_version: &'static str,
    pub result_oid: String,
    pub state_sha256: String,
    pub replayed: bool,
}

#[derive(Clone, Eq, PartialEq)]
pub struct GitMirrorSnapshot {
    revision_id: String,
    generation: u64,
    snapshot_sha256: String,
    commit_oid: String,
    state_sha256: String,
}

impl GitMirrorSnapshot {
    #[must_use]
    pub fn revision_id(&self) -> &str {
        &self.revision_id
    }

    #[must_use]
    pub const fn generation(&self) -> u64 {
        self.generation
    }

    #[must_use]
    pub fn snapshot_sha256(&self) -> &str {
        &self.snapshot_sha256
    }

    #[must_use]
    pub fn commit_oid(&self) -> &str {
        &self.commit_oid
    }

    #[must_use]
    pub fn state_sha256(&self) -> &str {
        &self.state_sha256
    }
}

impl fmt::Debug for GitMirrorSnapshot {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("GitMirrorSnapshot")
            .field("generation", &self.generation)
            .field("identities", &"<redacted>")
            .finish_non_exhaustive()
    }
}

impl fmt::Debug for GitMirrorPushReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("GitMirrorPushReceipt")
            .field("schema_version", &self.schema_version)
            .field("replayed", &self.replayed)
            .field("identities", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Error, Eq, PartialEq)]
pub enum GitMirrorEffectError {
    #[error("Git mirror effect configuration rejected")]
    ConfigurationRejected,
    #[error("Git mirror effect request rejected")]
    RequestRejected,
    #[error("Git mirror effect durable plan rejected")]
    PlanRejected,
    #[error("Git mirror repository state rejected")]
    GitStateRejected,
    #[error("Git mirror reference changed concurrently")]
    ReferenceConflict,
    #[error("Git mirror process outcome is unavailable")]
    GitUnavailable,
}

#[derive(Clone)]
pub struct GitMirrorEffectHost {
    bare_repository: PathBuf,
    git_program: PathBuf,
    object_oid_bytes: usize,
}

impl fmt::Debug for GitMirrorEffectHost {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("GitMirrorEffectHost")
            .field("bare_repository", &"<redacted>")
            .field("git_program", &"<redacted>")
            .field("object_oid_bytes", &self.object_oid_bytes)
            .finish()
    }
}

impl GitMirrorEffectHost {
    /// Opens one exact plain local bare repository and explicit plain Git executable.
    ///
    /// # Errors
    ///
    /// Rejects relative, linked/reparse, non-bare or unsupported-object-format configurations.
    pub fn open(bare_repository: &Path, git_program: &Path) -> Result<Self, GitMirrorEffectError> {
        if !bare_repository.is_absolute() || !git_program.is_absolute() {
            return Err(GitMirrorEffectError::ConfigurationRejected);
        }
        let repository_metadata = fs::symlink_metadata(bare_repository)
            .map_err(|_| GitMirrorEffectError::ConfigurationRejected)?;
        let git_metadata = fs::symlink_metadata(git_program)
            .map_err(|_| GitMirrorEffectError::ConfigurationRejected)?;
        if !repository_metadata.is_dir()
            || is_link_or_reparse(&repository_metadata)
            || !git_metadata.is_file()
            || is_link_or_reparse(&git_metadata)
        {
            return Err(GitMirrorEffectError::ConfigurationRejected);
        }
        let mut host = Self {
            bare_repository: bare_repository
                .canonicalize()
                .map_err(|_| GitMirrorEffectError::ConfigurationRejected)?,
            git_program: git_program
                .canonicalize()
                .map_err(|_| GitMirrorEffectError::ConfigurationRejected)?,
            object_oid_bytes: 0,
        };
        let temporary = tempfile::tempdir().map_err(|_| GitMirrorEffectError::GitUnavailable)?;
        if host.git_line(&["rev-parse", "--is-bare-repository"], &temporary)? != "true" {
            return Err(GitMirrorEffectError::ConfigurationRejected);
        }
        host.object_oid_bytes = match host
            .git_line(&["rev-parse", "--show-object-format"], &temporary)?
            .as_str()
        {
            "sha1" => 40,
            "sha256" => 64,
            _ => return Err(GitMirrorEffectError::ConfigurationRejected),
        };
        Ok(host)
    }

    /// Materializes deterministic unreachable objects and returns the exact durable CAS plan.
    ///
    /// # Errors
    ///
    /// Rejects any mismatch between the expected semantic head and current Git reference state.
    pub fn prepare_push(
        &self,
        input: &GitMirrorPushInput,
    ) -> Result<GitMirrorPushPlan, GitMirrorEffectError> {
        let temporary = tempfile::tempdir().map_err(|_| GitMirrorEffectError::GitUnavailable)?;
        let target_reference = target_reference(&input.branch_id);
        let expected_oid = self.read_reference(&target_reference, &temporary)?;
        self.require_expected_state(input, expected_oid.as_deref(), &temporary)?;
        let state_bytes = state_bytes(input)?;
        let state_sha256 = digest(&state_bytes);
        let blob_oid =
            self.git_line_with_input(&["hash-object", "-w", "--stdin"], &state_bytes, &temporary)?;
        self.require_oid(&blob_oid)?;
        let tree_line = format!("100644 blob {blob_oid}\t{STATE_PATH}\n");
        let tree_oid = self.git_line_with_input(&["mktree"], tree_line.as_bytes(), &temporary)?;
        self.require_oid(&tree_oid)?;
        let mut arguments = vec!["commit-tree", tree_oid.as_str()];
        if let Some(parent) = expected_oid.as_deref() {
            arguments.extend(["-p", parent]);
        }
        let message = format!(
            "hwpx-agent mirror generation {}\n\nrequest-sha256: {}\n",
            input.result_generation(),
            input.request_sha256
        );
        let result_oid = self.git_line_with_input(&arguments, message.as_bytes(), &temporary)?;
        self.require_oid(&result_oid)?;
        let plan = GitMirrorPushPlan {
            schema_version: PLAN_SCHEMA.to_owned(),
            input_sha256: input_digest(input)?,
            target_reference,
            expected_oid,
            result_oid,
            state_sha256,
        };
        plan.validate()?;
        Ok(plan)
    }

    /// Reads one exact semantic branch snapshot without changing repository state.
    ///
    /// # Errors
    ///
    /// Rejects malformed identifiers, noncanonical state, extra tree entries and identity drift.
    pub fn read_branch(
        &self,
        project_id: &str,
        branch_id: &str,
    ) -> Result<Option<GitMirrorSnapshot>, GitMirrorEffectError> {
        ProjectId::parse(project_id).map_err(|_| GitMirrorEffectError::RequestRejected)?;
        BranchId::parse(branch_id).map_err(|_| GitMirrorEffectError::RequestRejected)?;
        let reference = target_reference(branch_id);
        let temporary = tempfile::tempdir().map_err(|_| GitMirrorEffectError::GitUnavailable)?;
        let Some(commit_oid) = self.read_reference(&reference, &temporary)? else {
            return Ok(None);
        };
        let bytes = self.read_state(&commit_oid, &temporary)?;
        let state: MirrorState =
            serde_json::from_slice(&bytes).map_err(|_| GitMirrorEffectError::GitStateRejected)?;
        if !state.valid()
            || state.schema_version != STATE_SCHEMA
            || state.project_id != project_id
            || state.branch_id != branch_id
            || serde_json::to_vec(&state).map_err(|_| GitMirrorEffectError::GitUnavailable)?
                != bytes
        {
            return Err(GitMirrorEffectError::GitStateRejected);
        }
        self.require_exact_tree(&commit_oid, &bytes, &temporary)?;
        let revision_id = state
            .revision_id
            .ok_or(GitMirrorEffectError::GitStateRejected)?;
        Ok(Some(GitMirrorSnapshot {
            revision_id,
            generation: state.generation,
            snapshot_sha256: state.snapshot_sha256,
            commit_oid,
            state_sha256: digest(&bytes),
        }))
    }

    /// Publishes once by ref CAS or returns an exact replay receipt if already committed.
    ///
    /// # Errors
    ///
    /// Rejects plan/input drift and any current ref other than the exact old or result OID.
    pub fn execute_push(
        &self,
        input: &GitMirrorPushInput,
        plan: &GitMirrorPushPlan,
    ) -> Result<GitMirrorPushReceipt, GitMirrorEffectError> {
        self.require_plan_input(input, plan)?;
        match self.observe_push(input, plan)? {
            GitMirrorEffectObservation::Committed => return Ok(receipt(plan, true)),
            GitMirrorEffectObservation::Diverged => {
                return Err(GitMirrorEffectError::ReferenceConflict);
            }
            GitMirrorEffectObservation::NoEffect => {}
        }
        let rebuilt = self.prepare_push(input)?;
        if &rebuilt != plan {
            return Err(GitMirrorEffectError::PlanRejected);
        }
        let temporary = tempfile::tempdir().map_err(|_| GitMirrorEffectError::GitUnavailable)?;
        let old = plan
            .expected_oid
            .clone()
            .unwrap_or_else(|| "0".repeat(self.object_oid_bytes));
        let outcome = self.run_git(
            &[
                OsStr::new("update-ref"),
                OsStr::new(&plan.target_reference),
                OsStr::new(&plan.result_oid),
                OsStr::new(&old),
            ],
            None,
            &temporary,
        )?;
        if !outcome.status.success() {
            return match self.observe_push(input, plan)? {
                GitMirrorEffectObservation::Committed => Ok(receipt(plan, true)),
                GitMirrorEffectObservation::NoEffect | GitMirrorEffectObservation::Diverged => {
                    Err(GitMirrorEffectError::ReferenceConflict)
                }
            };
        }
        if self.observe_push(input, plan)? != GitMirrorEffectObservation::Committed {
            return Err(GitMirrorEffectError::GitUnavailable);
        }
        Ok(receipt(plan, false))
    }

    /// Classifies post-crash Git state without mutating the reference.
    ///
    /// # Errors
    ///
    /// Rejects a mismatched plan/input and treats malformed committed state as rejected Git state.
    pub fn observe_push(
        &self,
        input: &GitMirrorPushInput,
        plan: &GitMirrorPushPlan,
    ) -> Result<GitMirrorEffectObservation, GitMirrorEffectError> {
        self.require_plan_input(input, plan)?;
        let temporary = tempfile::tempdir().map_err(|_| GitMirrorEffectError::GitUnavailable)?;
        let current = self.read_reference(&plan.target_reference, &temporary)?;
        if current.as_deref() == Some(plan.result_oid.as_str()) {
            let observed = self.read_state(&plan.result_oid, &temporary)?;
            if observed != state_bytes(input)? || digest(&observed) != plan.state_sha256 {
                return Err(GitMirrorEffectError::GitStateRejected);
            }
            self.require_exact_tree(&plan.result_oid, &observed, &temporary)?;
            return Ok(GitMirrorEffectObservation::Committed);
        }
        if current == plan.expected_oid {
            return Ok(GitMirrorEffectObservation::NoEffect);
        }
        Ok(GitMirrorEffectObservation::Diverged)
    }

    fn require_plan_input(
        &self,
        input: &GitMirrorPushInput,
        plan: &GitMirrorPushPlan,
    ) -> Result<(), GitMirrorEffectError> {
        plan.validate()?;
        if plan.input_sha256 != input_digest(input)?
            || plan.target_reference != target_reference(&input.branch_id)
            || plan.result_oid.len() != self.object_oid_bytes
        {
            return Err(GitMirrorEffectError::PlanRejected);
        }
        Ok(())
    }

    fn require_expected_state(
        &self,
        input: &GitMirrorPushInput,
        expected_oid: Option<&str>,
        temporary: &TempDir,
    ) -> Result<(), GitMirrorEffectError> {
        if input.expected_generation == 0 {
            return if expected_oid.is_none() {
                Ok(())
            } else {
                Err(GitMirrorEffectError::GitStateRejected)
            };
        }
        let oid = expected_oid.ok_or(GitMirrorEffectError::GitStateRejected)?;
        let bytes = self.read_state(oid, temporary)?;
        let state: MirrorState =
            serde_json::from_slice(&bytes).map_err(|_| GitMirrorEffectError::GitStateRejected)?;
        if state.schema_version != STATE_SCHEMA
            || state.project_id != input.project_id
            || state.branch_id != input.branch_id
            || state.revision_id.as_deref() != input.expected_revision_id.as_deref()
            || state.generation != input.expected_generation
            || Some(state.snapshot_sha256.as_str()) != input.expected_snapshot_sha256.as_deref()
            || !state.valid()
            || serde_json::to_vec(&state).map_err(|_| GitMirrorEffectError::GitUnavailable)?
                != bytes
        {
            return Err(GitMirrorEffectError::GitStateRejected);
        }
        self.require_exact_tree(oid, &bytes, temporary)?;
        Ok(())
    }

    fn read_reference(
        &self,
        reference: &str,
        temporary: &TempDir,
    ) -> Result<Option<String>, GitMirrorEffectError> {
        let output = self.run_git(
            &[
                OsStr::new("rev-parse"),
                OsStr::new("--verify"),
                OsStr::new("--quiet"),
                OsStr::new(&format!("{reference}^{{commit}}")),
            ],
            None,
            temporary,
        )?;
        match output.status.code() {
            Some(0) => {
                let oid = parse_line(&output.stdout)?;
                self.require_oid(&oid)?;
                Ok(Some(oid))
            }
            Some(1) => Ok(None),
            _ => Err(GitMirrorEffectError::GitUnavailable),
        }
    }

    fn read_state(&self, oid: &str, temporary: &TempDir) -> Result<Vec<u8>, GitMirrorEffectError> {
        self.require_oid(oid)?;
        let specification = format!("{oid}:{STATE_PATH}");
        let output = self.run_git(
            &[OsStr::new("show"), OsStr::new(&specification)],
            None,
            temporary,
        )?;
        if !output.status.success() || output.stdout.is_empty() {
            return Err(GitMirrorEffectError::GitStateRejected);
        }
        Ok(output.stdout)
    }

    fn require_exact_tree(
        &self,
        commit_oid: &str,
        state: &[u8],
        temporary: &TempDir,
    ) -> Result<(), GitMirrorEffectError> {
        let blob_oid =
            self.git_line_with_input(&["hash-object", "-w", "--stdin"], state, temporary)?;
        self.require_oid(&blob_oid)?;
        let tree_line = format!("100644 blob {blob_oid}\t{STATE_PATH}\n");
        let expected_tree =
            self.git_line_with_input(&["mktree"], tree_line.as_bytes(), temporary)?;
        self.require_oid(&expected_tree)?;
        let tree_expression = format!("{commit_oid}^{{tree}}");
        let observed_tree = self.git_line(&["rev-parse", &tree_expression], temporary)?;
        self.require_oid(&observed_tree)?;
        if observed_tree != expected_tree {
            return Err(GitMirrorEffectError::GitStateRejected);
        }
        Ok(())
    }

    fn require_oid(&self, oid: &str) -> Result<(), GitMirrorEffectError> {
        if oid.len() == self.object_oid_bytes && valid_oid(oid) {
            Ok(())
        } else {
            Err(GitMirrorEffectError::GitStateRejected)
        }
    }

    fn git_line(
        &self,
        arguments: &[&str],
        temporary: &TempDir,
    ) -> Result<String, GitMirrorEffectError> {
        let arguments = arguments.iter().map(OsStr::new).collect::<Vec<_>>();
        let output = self.run_git(&arguments, None, temporary)?;
        if !output.status.success() {
            return Err(GitMirrorEffectError::GitUnavailable);
        }
        parse_line(&output.stdout)
    }

    fn git_line_with_input(
        &self,
        arguments: &[&str],
        input: &[u8],
        temporary: &TempDir,
    ) -> Result<String, GitMirrorEffectError> {
        let arguments = arguments.iter().map(OsStr::new).collect::<Vec<_>>();
        let output = self.run_git(&arguments, Some(input), temporary)?;
        if !output.status.success() {
            return Err(GitMirrorEffectError::GitUnavailable);
        }
        parse_line(&output.stdout)
    }

    fn run_git(
        &self,
        arguments: &[&OsStr],
        input: Option<&[u8]>,
        temporary: &TempDir,
    ) -> Result<GitOutput, GitMirrorEffectError> {
        self.require_configuration_stable()?;
        let hooks = temporary.path().join("empty-hooks");
        fs::create_dir_all(&hooks).map_err(|_| GitMirrorEffectError::GitUnavailable)?;
        let mut command = Command::new(&self.git_program);
        command
            .arg("-C")
            .arg(&self.bare_repository)
            .arg("-c")
            .arg(format!("core.hooksPath={}", hooks.display()))
            .args(arguments)
            .env_clear()
            .env("GIT_CONFIG_NOSYSTEM", "1")
            .env("GIT_CONFIG_GLOBAL", null_device())
            .env("GIT_NO_REPLACE_OBJECTS", "1")
            .env("GIT_TERMINAL_PROMPT", "0")
            .env("GCM_INTERACTIVE", "Never")
            .env("LC_ALL", "C")
            .env("GIT_AUTHOR_NAME", "hwpx-agent mirror")
            .env("GIT_AUTHOR_EMAIL", "mirror@invalid")
            .env("GIT_COMMITTER_NAME", "hwpx-agent mirror")
            .env("GIT_COMMITTER_EMAIL", "mirror@invalid")
            .env("GIT_AUTHOR_DATE", "@1 +0000")
            .env("GIT_COMMITTER_DATE", "@1 +0000")
            .env("TEMP", temporary.path())
            .env("TMP", temporary.path())
            .stdin(if input.is_some() {
                Stdio::piped()
            } else {
                Stdio::null()
            })
            .stdout(Stdio::piped())
            .stderr(Stdio::null());
        for name in ["SystemRoot", "WINDIR"] {
            if let Some(value) = std::env::var_os(name) {
                command.env(name, value);
            }
        }
        let mut child = command
            .spawn()
            .map_err(|_| GitMirrorEffectError::GitUnavailable)?;
        if let Some(input) = input {
            let Some(mut stdin) = child.stdin.take() else {
                terminate_child(&mut child);
                return Err(GitMirrorEffectError::GitUnavailable);
            };
            if stdin.write_all(input).is_err() {
                terminate_child(&mut child);
                return Err(GitMirrorEffectError::GitUnavailable);
            }
        }
        let Some(stdout) = child.stdout.take() else {
            terminate_child(&mut child);
            return Err(GitMirrorEffectError::GitUnavailable);
        };
        let mut stdout = stdout.take(
            u64::try_from(MAX_GIT_OUTPUT_BYTES)
                .map_err(|_| GitMirrorEffectError::GitUnavailable)?
                + 1,
        );
        let mut bytes = Vec::new();
        if stdout.read_to_end(&mut bytes).is_err() || bytes.len() > MAX_GIT_OUTPUT_BYTES {
            terminate_child(&mut child);
            return Err(GitMirrorEffectError::GitUnavailable);
        }
        let status = child
            .wait()
            .map_err(|_| GitMirrorEffectError::GitUnavailable)?;
        Ok(GitOutput {
            status,
            stdout: bytes,
        })
    }

    fn require_configuration_stable(&self) -> Result<(), GitMirrorEffectError> {
        let repository = fs::symlink_metadata(&self.bare_repository)
            .map_err(|_| GitMirrorEffectError::ConfigurationRejected)?;
        let program = fs::symlink_metadata(&self.git_program)
            .map_err(|_| GitMirrorEffectError::ConfigurationRejected)?;
        if !repository.is_dir()
            || is_link_or_reparse(&repository)
            || !program.is_file()
            || is_link_or_reparse(&program)
            || self
                .bare_repository
                .canonicalize()
                .map_err(|_| GitMirrorEffectError::ConfigurationRejected)?
                != self.bare_repository
            || self
                .git_program
                .canonicalize()
                .map_err(|_| GitMirrorEffectError::ConfigurationRejected)?
                != self.git_program
        {
            return Err(GitMirrorEffectError::ConfigurationRejected);
        }
        Ok(())
    }
}

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct MirrorState {
    schema_version: String,
    project_id: String,
    branch_id: String,
    revision_id: Option<String>,
    generation: u64,
    snapshot_sha256: String,
    operation_plan_sha256: String,
    request_sha256: String,
}

impl MirrorState {
    fn valid(&self) -> bool {
        ProjectId::parse(&self.project_id).is_ok()
            && BranchId::parse(&self.branch_id).is_ok()
            && self
                .revision_id
                .as_deref()
                .is_some_and(|value| RevisionId::parse(value).is_ok())
            && self.generation > 0
            && valid_digest(&self.snapshot_sha256)
            && valid_digest(&self.operation_plan_sha256)
            && valid_digest(&self.request_sha256)
    }
}

struct GitOutput {
    status: ExitStatus,
    stdout: Vec<u8>,
}

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct PushPlanWire {
    schema_version: String,
    input_sha256: String,
    target_reference: String,
    expected_oid: Option<String>,
    result_oid: String,
    state_sha256: String,
}

impl From<&GitMirrorPushPlan> for PushPlanWire {
    fn from(value: &GitMirrorPushPlan) -> Self {
        Self {
            schema_version: value.schema_version.clone(),
            input_sha256: value.input_sha256.clone(),
            target_reference: value.target_reference.clone(),
            expected_oid: value.expected_oid.clone(),
            result_oid: value.result_oid.clone(),
            state_sha256: value.state_sha256.clone(),
        }
    }
}

impl From<PushPlanWire> for GitMirrorPushPlan {
    fn from(value: PushPlanWire) -> Self {
        Self {
            schema_version: value.schema_version,
            input_sha256: value.input_sha256,
            target_reference: value.target_reference,
            expected_oid: value.expected_oid,
            result_oid: value.result_oid,
            state_sha256: value.state_sha256,
        }
    }
}

fn state_bytes(input: &GitMirrorPushInput) -> Result<Vec<u8>, GitMirrorEffectError> {
    serde_json::to_vec(&MirrorState {
        schema_version: STATE_SCHEMA.to_owned(),
        project_id: input.project_id.clone(),
        branch_id: input.branch_id.clone(),
        revision_id: Some(input.result_revision_id.clone()),
        generation: input.result_generation(),
        snapshot_sha256: input.result_snapshot_sha256.clone(),
        operation_plan_sha256: input.operation_plan_sha256.clone(),
        request_sha256: input.request_sha256.clone(),
    })
    .map_err(|_| GitMirrorEffectError::GitUnavailable)
}

fn input_digest(input: &GitMirrorPushInput) -> Result<String, GitMirrorEffectError> {
    #[derive(Serialize)]
    struct InputDigest<'a> {
        schema_version: &'static str,
        project_id: &'a str,
        branch_id: &'a str,
        expected_revision_id: Option<&'a str>,
        expected_generation: u64,
        expected_snapshot_sha256: Option<&'a str>,
        result_revision_id: &'a str,
        result_snapshot_sha256: &'a str,
        operation_plan_sha256: &'a str,
        request_sha256: &'a str,
    }
    let bytes = serde_json::to_vec(&InputDigest {
        schema_version: "hwpx-agent.git-mirror-push-input/v1",
        project_id: &input.project_id,
        branch_id: &input.branch_id,
        expected_revision_id: input.expected_revision_id.as_deref(),
        expected_generation: input.expected_generation,
        expected_snapshot_sha256: input.expected_snapshot_sha256.as_deref(),
        result_revision_id: &input.result_revision_id,
        result_snapshot_sha256: &input.result_snapshot_sha256,
        operation_plan_sha256: &input.operation_plan_sha256,
        request_sha256: &input.request_sha256,
    })
    .map_err(|_| GitMirrorEffectError::GitUnavailable)?;
    Ok(digest(&bytes))
}

fn receipt(plan: &GitMirrorPushPlan, replayed: bool) -> GitMirrorPushReceipt {
    GitMirrorPushReceipt {
        schema_version: RECEIPT_SCHEMA,
        result_oid: plan.result_oid.clone(),
        state_sha256: plan.state_sha256.clone(),
        replayed,
    }
}

fn target_reference(branch_id: &str) -> String {
    let suffix = branch_id.strip_prefix("brn_").unwrap_or_default();
    format!("refs/heads/hwpx-agent/{suffix}")
}

fn valid_reference(value: &str) -> bool {
    value
        .strip_prefix("refs/heads/hwpx-agent/")
        .is_some_and(|suffix| {
            suffix.len() == 32
                && suffix
                    .bytes()
                    .all(|byte| byte.is_ascii_digit() || matches!(byte, b'a'..=b'f'))
        })
}

fn valid_digest(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || matches!(byte, b'a'..=b'f'))
}

fn valid_oid(value: &str) -> bool {
    matches!(value.len(), 40 | 64)
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || matches!(byte, b'a'..=b'f'))
}

fn digest(bytes: &[u8]) -> String {
    hex::encode(Sha256::digest(bytes))
}

fn parse_line(bytes: &[u8]) -> Result<String, GitMirrorEffectError> {
    let raw = std::str::from_utf8(bytes).map_err(|_| GitMirrorEffectError::GitUnavailable)?;
    let value = raw
        .strip_suffix("\r\n")
        .or_else(|| raw.strip_suffix('\n'))
        .unwrap_or(raw);
    if value.is_empty() || value.contains('\n') || value.contains('\r') {
        return Err(GitMirrorEffectError::GitUnavailable);
    }
    Ok(value.to_owned())
}

fn terminate_child(child: &mut std::process::Child) {
    let _ = child.kill();
    let _ = child.wait();
}

#[cfg(windows)]
fn null_device() -> &'static str {
    "NUL"
}

#[cfg(not(windows))]
fn null_device() -> &'static str {
    "/dev/null"
}

#[cfg(windows)]
fn is_link_or_reparse(metadata: &fs::Metadata) -> bool {
    use std::os::windows::fs::MetadataExt as _;
    const FILE_ATTRIBUTE_REPARSE_POINT: u32 = 0x400;
    metadata.file_type().is_symlink()
        || metadata.file_attributes() & FILE_ATTRIBUTE_REPARSE_POINT != 0
}

#[cfg(not(windows))]
fn is_link_or_reparse(metadata: &fs::Metadata) -> bool {
    metadata.file_type().is_symlink()
}
