#![forbid(unsafe_code)]

use std::fs::{self, File, OpenOptions};
use std::io::{Read as _, Write as _};
use std::path::{Component, Path, PathBuf};

use sha2::{Digest as _, Sha256};
use thiserror::Error;

pub const MAX_WORKFLOW_FILE_BYTES: u64 = 1_073_741_824;
pub const GIT_APPROVAL_TARGET_SCHEMA: &str = "hwpx-agent.git-approval-target/v1";
pub const GIT_COMMIT_PLAN_SCHEMA: &str = "hwpx-agent.git-commit-plan/v1";
const MAX_RELATIVE_PATH_BYTES: usize = 1_024;
const MAX_PATH_COMPONENTS: usize = 32;
const MAX_COMMIT_MESSAGE_BYTES: usize = 128;
const COPY_BUFFER_BYTES: usize = 64 * 1024;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum MaterializeSlot {
    Source,
    Candidate,
}

impl MaterializeSlot {
    const fn file_name(self) -> &'static str {
        match self {
            Self::Source => "source.hwpx",
            Self::Candidate => "candidate.hwpx",
        }
    }
}

#[derive(Debug, Error)]
pub enum WorkflowError {
    #[error("workflow configuration rejected")]
    Configuration,
    #[error("workflow path rejected")]
    Path,
    #[error("workflow file rejected")]
    File,
    #[error("workflow digest rejected")]
    Digest,
    #[error("workflow output already exists")]
    OutputExists,
    #[error("workflow publication incomplete")]
    PublicationIncomplete,
    #[error("git repository state rejected")]
    GitState,
    #[error("local workflow I/O rejected")]
    Io,
}

#[derive(Clone)]
pub struct LocalWorkflow {
    root: PathBuf,
    work: PathBuf,
    max_file_bytes: u64,
}

impl std::fmt::Debug for LocalWorkflow {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("LocalWorkflow")
            .field("root", &"[REDACTED]")
            .field("work", &"[REDACTED]")
            .field("max_file_bytes", &self.max_file_bytes)
            .finish()
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct MaterializeReceipt {
    pub operation_id: String,
    pub slot: MaterializeSlot,
    pub sha256: String,
    pub size_bytes: u64,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct FileIdentity {
    pub sha256: String,
    pub size_bytes: u64,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct FileDiffReceipt {
    pub operation_id: String,
    pub identical: bool,
    pub source: FileIdentity,
    pub candidate: FileIdentity,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct PublishReceipt {
    pub operation_id: String,
    pub output_name: String,
    pub sha256: String,
    pub size_bytes: u64,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct GitCommitPlan {
    pub output_pathspec: String,
    pub expected_output_sha256: String,
    pub expected_head: String,
    pub expected_head_reference: Option<String>,
    pub message: String,
}

impl GitCommitPlan {
    /// Returns the domain-separated digest presented for exact-plan approval.
    #[must_use]
    pub fn approval_plan_sha256(&self) -> String {
        bound_digest(
            GIT_COMMIT_PLAN_SCHEMA,
            &[
                &self.output_pathspec,
                &self.expected_output_sha256,
                &self.expected_head,
                self.expected_head_reference
                    .as_deref()
                    .unwrap_or("detached"),
                &self.message,
            ],
        )
    }
}

impl LocalWorkflow {
    /// Opens one existing workspace and creates only its private work directory.
    ///
    /// # Errors
    ///
    /// Rejects non-absolute/link roots, missing `input`/`output` directories and unsafe limits.
    pub fn open(root: &Path, max_file_bytes: u64) -> Result<Self, WorkflowError> {
        if !root.is_absolute() || !(1..=MAX_WORKFLOW_FILE_BYTES).contains(&max_file_bytes) {
            return Err(WorkflowError::Configuration);
        }
        let requested = fs::symlink_metadata(root).map_err(|_| WorkflowError::Configuration)?;
        if !requested.is_dir() || is_link_or_reparse(&requested) {
            return Err(WorkflowError::Configuration);
        }
        let root = root
            .canonicalize()
            .map_err(|_| WorkflowError::Configuration)?;
        for required in [root.join("input"), root.join("output")] {
            let metadata =
                fs::symlink_metadata(&required).map_err(|_| WorkflowError::Configuration)?;
            if !metadata.is_dir() || is_link_or_reparse(&metadata) {
                return Err(WorkflowError::Configuration);
            }
        }
        let private = root.join(".hwpx-agent");
        let work = private.join("work");
        create_directory(&root, &private)?;
        create_directory(&root, &work)?;
        Ok(Self {
            root,
            work,
            max_file_bytes,
        })
    }

    /// Copies one checksum-bound `input/` HWPX into a create-new private operation slot.
    ///
    /// # Errors
    ///
    /// Rejects traversal, links, oversized files, digest drift and existing operation slots.
    pub fn materialize(
        &self,
        operation_id: &str,
        slot: MaterializeSlot,
        input_relative: &str,
        expected_sha256: &[u8; 32],
    ) -> Result<MaterializeReceipt, WorkflowError> {
        if !valid_identifier(operation_id) || expected_sha256 == &[0; 32] {
            return Err(WorkflowError::Path);
        }
        let relative = validate_relative(input_relative)?;
        if first_component(&relative) != Some("input") || !has_hwpx_extension(&relative) {
            return Err(WorkflowError::Path);
        }
        let source = resolve_existing(&self.root, &relative)?;
        let operation = self.work.join(operation_id);
        create_directory(&self.root, &operation)?;
        let destination = operation.join(slot.file_name());
        let identity =
            copy_new_verified(&source, &destination, expected_sha256, self.max_file_bytes)?;
        Ok(MaterializeReceipt {
            operation_id: operation_id.to_owned(),
            slot,
            sha256: identity.sha256,
            size_bytes: identity.size_bytes,
        })
    }

    /// Compares materialized source and candidate identities without returning their content.
    ///
    /// # Errors
    ///
    /// Rejects invalid operation IDs, links, missing files and configured size-limit violations.
    pub fn diff(&self, operation_id: &str) -> Result<FileDiffReceipt, WorkflowError> {
        let operation = self.operation_directory(operation_id)?;
        let source = identify_existing(
            &self.root,
            &operation.join(MaterializeSlot::Source.file_name()),
            self.max_file_bytes,
        )?;
        let candidate = identify_existing(
            &self.root,
            &operation.join(MaterializeSlot::Candidate.file_name()),
            self.max_file_bytes,
        )?;
        Ok(FileDiffReceipt {
            operation_id: operation_id.to_owned(),
            identical: source == candidate,
            source,
            candidate,
        })
    }

    /// Publishes a checksum-bound candidate to a create-new `output/` name and removes the slot.
    ///
    /// # Errors
    ///
    /// Rejects unsafe names, digest drift, overwrite, link insertion and incomplete publication.
    pub fn publish(
        &self,
        operation_id: &str,
        output_name: &str,
        expected_sha256: &[u8; 32],
    ) -> Result<PublishReceipt, WorkflowError> {
        if !valid_output_name(output_name) || expected_sha256 == &[0; 32] {
            return Err(WorkflowError::Path);
        }
        let operation = self.operation_directory(operation_id)?;
        let candidate = operation.join(MaterializeSlot::Candidate.file_name());
        let identity = identify_existing(&self.root, &candidate, self.max_file_bytes)?;
        if identity.sha256 != hex::encode(expected_sha256) {
            return Err(WorkflowError::Digest);
        }
        let output = self.root.join("output").join(output_name);
        reject_links_between(&self.root, &output)?;
        if fs::symlink_metadata(&output).is_ok() {
            return Err(WorkflowError::OutputExists);
        }
        let published =
            copy_new_verified(&candidate, &output, expected_sha256, self.max_file_bytes)?;
        if published != identity || fs::remove_file(&candidate).is_err() {
            return Err(WorkflowError::PublicationIncomplete);
        }
        Ok(PublishReceipt {
            operation_id: operation_id.to_owned(),
            output_name: output_name.to_owned(),
            sha256: identity.sha256,
            size_bytes: identity.size_bytes,
        })
    }

    /// Produces a head- and digest-bound Git commit plan without spawning Git or mutating its index.
    ///
    /// # Errors
    ///
    /// Rejects unsafe output names/messages, output drift and malformed or linked Git metadata.
    pub fn prepare_git_commit(
        &self,
        output_name: &str,
        expected_sha256: &[u8; 32],
        message: &str,
    ) -> Result<GitCommitPlan, WorkflowError> {
        if !valid_output_name(output_name)
            || expected_sha256 == &[0; 32]
            || message.is_empty()
            || message.len() > MAX_COMMIT_MESSAGE_BYTES
            || message.trim() != message
            || message.chars().any(char::is_control)
        {
            return Err(WorkflowError::GitState);
        }
        let output_path = self.root.join("output").join(output_name);
        let identity = identify_existing(&self.root, &output_path, self.max_file_bytes)?;
        if identity.sha256 != hex::encode(expected_sha256) {
            return Err(WorkflowError::Digest);
        }
        let expected_head = read_git_head(&self.root)?;
        Ok(GitCommitPlan {
            output_pathspec: format!("output/{output_name}"),
            expected_output_sha256: identity.sha256,
            expected_head: expected_head.object_id,
            expected_head_reference: expected_head.reference,
            message: message.to_owned(),
        })
    }

    /// Returns a domain-separated digest for this exact canonical workspace root.
    ///
    /// # Errors
    ///
    /// Rejects a root that cannot be represented without lossy path conversion.
    pub fn git_approval_target_sha256(&self) -> Result<String, WorkflowError> {
        let root = self.root.to_str().ok_or(WorkflowError::GitState)?;
        #[cfg(windows)]
        let root = root.replace('/', "\\").to_lowercase();
        #[cfg(not(windows))]
        let root = root.to_owned();
        Ok(bound_digest(GIT_APPROVAL_TARGET_SCHEMA, &[&root]))
    }

    fn operation_directory(&self, operation_id: &str) -> Result<PathBuf, WorkflowError> {
        if !valid_identifier(operation_id) {
            return Err(WorkflowError::Path);
        }
        let operation = self.work.join(operation_id);
        let metadata = fs::symlink_metadata(&operation).map_err(|_| WorkflowError::File)?;
        if !metadata.is_dir() || is_link_or_reparse(&metadata) {
            return Err(WorkflowError::Path);
        }
        reject_links_between(&self.root, &operation)?;
        Ok(operation)
    }
}

fn copy_new_verified(
    source: &Path,
    destination: &Path,
    expected_sha256: &[u8; 32],
    max_bytes: u64,
) -> Result<FileIdentity, WorkflowError> {
    let mut input = File::open(source).map_err(|_| WorkflowError::Io)?;
    let metadata = input.metadata().map_err(|_| WorkflowError::Io)?;
    if !metadata.is_file() || metadata.len() == 0 || metadata.len() > max_bytes {
        return Err(WorkflowError::File);
    }
    let mut output = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(destination)
        .map_err(|error| {
            if error.kind() == std::io::ErrorKind::AlreadyExists {
                WorkflowError::OutputExists
            } else {
                WorkflowError::Io
            }
        })?;
    let result = (|| {
        let mut hasher = Sha256::new();
        let mut size = 0_u64;
        let mut buffer = vec![0_u8; COPY_BUFFER_BYTES].into_boxed_slice();
        loop {
            let count = input.read(&mut buffer).map_err(|_| WorkflowError::Io)?;
            if count == 0 {
                break;
            }
            size = size
                .checked_add(u64::try_from(count).map_err(|_| WorkflowError::File)?)
                .ok_or(WorkflowError::File)?;
            if size > max_bytes {
                return Err(WorkflowError::File);
            }
            hasher.update(&buffer[..count]);
            output
                .write_all(&buffer[..count])
                .map_err(|_| WorkflowError::Io)?;
        }
        output.sync_all().map_err(|_| WorkflowError::Io)?;
        let observed: [u8; 32] = hasher.finalize().into();
        if &observed != expected_sha256 {
            return Err(WorkflowError::Digest);
        }
        Ok(FileIdentity {
            sha256: hex::encode(observed),
            size_bytes: size,
        })
    })();
    if result.is_err() {
        drop(output);
        let _ = fs::remove_file(destination);
    }
    result
}

fn identify_existing(
    root: &Path,
    path: &Path,
    max_bytes: u64,
) -> Result<FileIdentity, WorkflowError> {
    reject_links_between(root, path)?;
    let resolved = path.canonicalize().map_err(|_| WorkflowError::File)?;
    if !resolved.starts_with(root) {
        return Err(WorkflowError::Path);
    }
    let mut file = File::open(resolved).map_err(|_| WorkflowError::Io)?;
    let metadata = file.metadata().map_err(|_| WorkflowError::Io)?;
    if !metadata.is_file() || metadata.len() == 0 || metadata.len() > max_bytes {
        return Err(WorkflowError::File);
    }
    let mut hasher = Sha256::new();
    let mut size = 0_u64;
    let mut buffer = vec![0_u8; COPY_BUFFER_BYTES].into_boxed_slice();
    loop {
        let count = file.read(&mut buffer).map_err(|_| WorkflowError::Io)?;
        if count == 0 {
            break;
        }
        size = size
            .checked_add(u64::try_from(count).map_err(|_| WorkflowError::File)?)
            .ok_or(WorkflowError::File)?;
        if size > max_bytes {
            return Err(WorkflowError::File);
        }
        hasher.update(&buffer[..count]);
    }
    Ok(FileIdentity {
        sha256: hex::encode(hasher.finalize()),
        size_bytes: size,
    })
}

struct GitHeadState {
    object_id: String,
    reference: Option<String>,
}

fn read_git_head(root: &Path) -> Result<GitHeadState, WorkflowError> {
    let git = root.join(".git");
    let metadata = fs::symlink_metadata(&git).map_err(|_| WorkflowError::GitState)?;
    if !metadata.is_dir() || is_link_or_reparse(&metadata) {
        return Err(WorkflowError::GitState);
    }
    let head_path = git.join("HEAD");
    reject_links_between(root, &head_path)?;
    let head = read_bounded_text(&head_path, 256)?;
    if let Some(reference) = head.strip_prefix("ref: ") {
        let relative = validate_git_reference(reference)?;
        let reference_path = git.join(relative);
        reject_links_between(root, &reference_path)?;
        let value = read_bounded_text(&reference_path, 128)?;
        Ok(GitHeadState {
            object_id: validate_object_id(&value)?,
            reference: Some(reference.to_owned()),
        })
    } else {
        Ok(GitHeadState {
            object_id: validate_object_id(&head)?,
            reference: None,
        })
    }
}

fn bound_digest(domain: &str, fields: &[&str]) -> String {
    let mut hasher = Sha256::new();
    update_digest_field(&mut hasher, domain.as_bytes());
    for field in fields {
        update_digest_field(&mut hasher, field.as_bytes());
    }
    hex::encode(hasher.finalize())
}

fn update_digest_field(hasher: &mut Sha256, field: &[u8]) {
    let length = u64::try_from(field.len()).unwrap_or(u64::MAX);
    hasher.update(length.to_be_bytes());
    hasher.update(field);
}

fn read_bounded_text(path: &Path, max_bytes: u64) -> Result<String, WorkflowError> {
    let metadata = fs::metadata(path).map_err(|_| WorkflowError::GitState)?;
    if !metadata.is_file() || metadata.len() == 0 || metadata.len() > max_bytes {
        return Err(WorkflowError::GitState);
    }
    let value = fs::read_to_string(path).map_err(|_| WorkflowError::GitState)?;
    let trimmed = value.strip_suffix('\n').unwrap_or(&value);
    if trimmed.contains(['\r', '\n']) || trimmed.is_empty() {
        return Err(WorkflowError::GitState);
    }
    Ok(trimmed.to_owned())
}

fn validate_git_reference(value: &str) -> Result<PathBuf, WorkflowError> {
    if !value.starts_with("refs/heads/")
        || value.len() > 200
        || value.contains("..")
        || value.contains("@{")
        || value.ends_with(['/', '.'])
        || value
            .bytes()
            .any(|byte| !byte.is_ascii_alphanumeric() && !matches!(byte, b'/' | b'.' | b'_' | b'-'))
        || value.split('/').any(|component| {
            component.is_empty()
                || component.starts_with('.')
                || Path::new(component)
                    .extension()
                    .is_some_and(|extension| extension.eq_ignore_ascii_case("lock"))
        })
    {
        return Err(WorkflowError::GitState);
    }
    let relative = validate_relative(value).map_err(|_| WorkflowError::GitState)?;
    Ok(relative)
}

fn validate_object_id(value: &str) -> Result<String, WorkflowError> {
    if !matches!(value.len(), 40 | 64)
        || !value.bytes().all(|byte| byte.is_ascii_hexdigit())
        || value.bytes().all(|byte| byte == b'0')
    {
        return Err(WorkflowError::GitState);
    }
    Ok(value.to_ascii_lowercase())
}

fn validate_relative(value: &str) -> Result<PathBuf, WorkflowError> {
    if value.is_empty() || value.len() > MAX_RELATIVE_PATH_BYTES || value.contains('\0') {
        return Err(WorkflowError::Path);
    }
    let path = Path::new(value);
    if path.is_absolute() {
        return Err(WorkflowError::Path);
    }
    let mut count = 0_usize;
    for component in path.components() {
        let Component::Normal(part) = component else {
            return Err(WorkflowError::Path);
        };
        let text = part.to_str().ok_or(WorkflowError::Path)?;
        if !valid_windows_component(text) {
            return Err(WorkflowError::Path);
        }
        count += 1;
        if count > MAX_PATH_COMPONENTS {
            return Err(WorkflowError::Path);
        }
    }
    if count == 0 {
        return Err(WorkflowError::Path);
    }
    Ok(path.to_path_buf())
}

fn valid_identifier(value: &str) -> bool {
    (1..=64).contains(&value.len())
        && value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'_'))
}

fn valid_output_name(value: &str) -> bool {
    valid_windows_component(value)
        && value.len() <= 128
        && Path::new(value).components().count() == 1
        && Path::new(value)
            .extension()
            .and_then(|extension| extension.to_str())
            .is_some_and(|extension| extension.eq_ignore_ascii_case("hwpx"))
}

fn has_hwpx_extension(path: &Path) -> bool {
    path.extension()
        .and_then(|extension| extension.to_str())
        .is_some_and(|extension| extension.eq_ignore_ascii_case("hwpx"))
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

fn first_component(path: &Path) -> Option<&str> {
    path.components()
        .next()
        .and_then(|component| match component {
            Component::Normal(value) => value.to_str(),
            _ => None,
        })
}

fn resolve_existing(root: &Path, relative: &Path) -> Result<PathBuf, WorkflowError> {
    let candidate = root.join(relative);
    reject_links_between(root, &candidate)?;
    let resolved = candidate.canonicalize().map_err(|_| WorkflowError::File)?;
    if !resolved.starts_with(root) {
        return Err(WorkflowError::Path);
    }
    Ok(resolved)
}

fn create_directory(root: &Path, path: &Path) -> Result<(), WorkflowError> {
    if !path.starts_with(root) {
        return Err(WorkflowError::Path);
    }
    reject_links_between(root, path)?;
    match fs::create_dir(path) {
        Ok(()) => {}
        Err(error) if error.kind() == std::io::ErrorKind::AlreadyExists => {}
        Err(_) => return Err(WorkflowError::Io),
    }
    let metadata = fs::symlink_metadata(path).map_err(|_| WorkflowError::Io)?;
    if !metadata.is_dir() || is_link_or_reparse(&metadata) {
        return Err(WorkflowError::Path);
    }
    Ok(())
}

fn reject_links_between(root: &Path, candidate: &Path) -> Result<(), WorkflowError> {
    let relative = candidate
        .strip_prefix(root)
        .map_err(|_| WorkflowError::Path)?;
    let mut current = root.to_path_buf();
    for component in relative.components() {
        let Component::Normal(part) = component else {
            return Err(WorkflowError::Path);
        };
        current.push(part);
        match fs::symlink_metadata(&current) {
            Ok(metadata) if is_link_or_reparse(&metadata) => return Err(WorkflowError::Path),
            Ok(_) => {}
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => break,
            Err(_) => return Err(WorkflowError::Io),
        }
    }
    Ok(())
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
