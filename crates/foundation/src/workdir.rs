#[cfg(not(windows))]
use std::fs::File;
use std::fs::{self, OpenOptions};
use std::io::{self, Write};
use std::path::{Component, Path, PathBuf};

use sha2::{Digest, Sha256};
use thiserror::Error;

#[derive(Debug, Error)]
pub enum WorkspaceError {
    #[error("path must contain only normal relative components")]
    InvalidRelativePath,
    #[error("path escapes the secure workspace")]
    EscapesWorkspace,
    #[error("symbolic links and reparse points are not allowed")]
    LinkNotAllowed,
    #[error("artifact already exists")]
    ArtifactExists,
    #[error("I/O error: {0}")]
    Io(#[from] io::Error),
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct StagedArtifact {
    path: PathBuf,
    pub sha256: String,
    pub size_bytes: u64,
}

#[derive(Clone, Debug)]
pub struct SecureWorkspace {
    root: PathBuf,
    staging: PathBuf,
    quarantine: PathBuf,
    output: PathBuf,
}

impl SecureWorkspace {
    /// staging/quarantine/output 경계가 있는 새 보안 작업공간을 만든다.
    ///
    /// # Errors
    ///
    /// root를 만들거나 canonicalize할 수 없거나 link 경계가 발견되면 실패한다.
    pub fn create(root: impl AsRef<Path>) -> Result<Self, WorkspaceError> {
        let requested = root.as_ref();
        fs::create_dir_all(requested)?;
        reject_link(requested)?;
        let root = requested.canonicalize()?;
        reject_link(&root)?;
        let workspace = Self {
            staging: root.join("staging"),
            quarantine: root.join("quarantine"),
            output: root.join("output"),
            root,
        };
        for directory in [&workspace.staging, &workspace.quarantine, &workspace.output] {
            fs::create_dir_all(directory)?;
            reject_link(directory)?;
        }
        Ok(workspace)
    }

    /// bytes를 create-new staging 파일에 쓰고 동기화한다.
    ///
    /// # Errors
    ///
    /// 상대경로가 안전하지 않거나 기존 파일/link와 충돌하거나 I/O가 실패하면 오류를 반환한다.
    pub fn stage_bytes(
        &self,
        relative: &Path,
        bytes: &[u8],
    ) -> Result<StagedArtifact, WorkspaceError> {
        let path = self.resolve_for_create(&self.staging, relative)?;
        create_parent_chain(
            &self.root,
            path.parent().ok_or(WorkspaceError::InvalidRelativePath)?,
        )?;
        let mut file = OpenOptions::new()
            .create_new(true)
            .write(true)
            .open(&path)?;
        file.write_all(bytes)?;
        file.sync_all()?;
        sync_parent(&path)?;
        Ok(StagedArtifact {
            path,
            sha256: hex::encode(Sha256::digest(bytes)),
            size_bytes: u64::try_from(bytes.len()).unwrap_or(u64::MAX),
        })
    }

    /// 동일 volume hard-link publication으로 no-overwrite와 atomic visibility를 동시에 보장한다.
    ///
    /// # Errors
    ///
    /// staging identity가 경계를 벗어나거나 목적지가 이미 존재하거나 I/O가 실패하면 오류를 반환한다.
    pub fn publish(
        &self,
        staged: &StagedArtifact,
        relative: &Path,
    ) -> Result<PathBuf, WorkspaceError> {
        self.ensure_existing_contained(&staged.path, &self.staging)?;
        let destination = self.resolve_for_create(&self.output, relative)?;
        create_parent_chain(
            &self.root,
            destination
                .parent()
                .ok_or(WorkspaceError::InvalidRelativePath)?,
        )?;
        match fs::hard_link(&staged.path, &destination) {
            Ok(()) => {}
            Err(error) if error.kind() == io::ErrorKind::AlreadyExists => {
                return Err(WorkspaceError::ArtifactExists);
            }
            Err(error) => return Err(WorkspaceError::Io(error)),
        }
        sync_parent(&destination)?;
        fs::remove_file(&staged.path)?;
        Ok(destination)
    }

    /// 게시할 수 없는 staged artifact를 격리 영역으로 이동한다.
    ///
    /// # Errors
    ///
    /// 경로 경계/link 검사 또는 원자 no-overwrite publication이 실패하면 오류를 반환한다.
    pub fn quarantine(
        &self,
        staged: &StagedArtifact,
        relative: &Path,
    ) -> Result<PathBuf, WorkspaceError> {
        self.ensure_existing_contained(&staged.path, &self.staging)?;
        let destination = self.resolve_for_create(&self.quarantine, relative)?;
        create_parent_chain(
            &self.root,
            destination
                .parent()
                .ok_or(WorkspaceError::InvalidRelativePath)?,
        )?;
        match fs::hard_link(&staged.path, &destination) {
            Ok(()) => {}
            Err(error) if error.kind() == io::ErrorKind::AlreadyExists => {
                return Err(WorkspaceError::ArtifactExists);
            }
            Err(error) => return Err(WorkspaceError::Io(error)),
        }
        sync_parent(&destination)?;
        fs::remove_file(&staged.path)?;
        Ok(destination)
    }

    /// 중단된 한 staging 하위 디렉터리만 제거한다.
    ///
    /// # Errors
    ///
    /// 대상이 staging 밖이거나 디렉터리가 아니거나 제거 I/O가 실패하면 오류를 반환한다.
    pub fn cleanup_staging(&self, relative_directory: &Path) -> Result<(), WorkspaceError> {
        let path = self.resolve_existing(&self.staging, relative_directory)?;
        if path.is_dir() {
            fs::remove_dir_all(path)?;
        } else {
            return Err(WorkspaceError::InvalidRelativePath);
        }
        Ok(())
    }

    fn resolve_for_create(&self, base: &Path, relative: &Path) -> Result<PathBuf, WorkspaceError> {
        validate_relative(relative)?;
        ensure_under_root(base, &self.root)?;
        let candidate = base.join(relative);
        reject_existing_links(&self.root, &candidate)?;
        Ok(candidate)
    }

    fn resolve_existing(&self, base: &Path, relative: &Path) -> Result<PathBuf, WorkspaceError> {
        let candidate = self.resolve_for_create(base, relative)?;
        let canonical = candidate.canonicalize()?;
        ensure_under_root(&canonical, base)?;
        reject_existing_links(&self.root, &candidate)?;
        Ok(canonical)
    }

    fn ensure_existing_contained(&self, path: &Path, base: &Path) -> Result<(), WorkspaceError> {
        let canonical = path.canonicalize()?;
        ensure_under_root(&canonical, base)?;
        reject_existing_links(&self.root, path)
    }
}

fn validate_relative(path: &Path) -> Result<(), WorkspaceError> {
    if path.as_os_str().is_empty() || path.is_absolute() {
        return Err(WorkspaceError::InvalidRelativePath);
    }
    if path
        .components()
        .all(|component| matches!(component, Component::Normal(_)))
    {
        Ok(())
    } else {
        Err(WorkspaceError::InvalidRelativePath)
    }
}

fn ensure_under_root(path: &Path, root: &Path) -> Result<(), WorkspaceError> {
    if path.starts_with(root) {
        Ok(())
    } else {
        Err(WorkspaceError::EscapesWorkspace)
    }
}

fn create_parent_chain(root: &Path, parent: &Path) -> Result<(), WorkspaceError> {
    ensure_under_root(parent, root)?;
    let relative = parent
        .strip_prefix(root)
        .map_err(|_| WorkspaceError::EscapesWorkspace)?;
    let mut current = root.to_path_buf();
    for component in relative.components() {
        let Component::Normal(segment) = component else {
            return Err(WorkspaceError::InvalidRelativePath);
        };
        current.push(segment);
        if current.exists() {
            reject_link(&current)?;
        } else {
            fs::create_dir(&current)?;
        }
    }
    Ok(())
}

fn reject_existing_links(root: &Path, path: &Path) -> Result<(), WorkspaceError> {
    ensure_under_root(path, root)?;
    let relative = path
        .strip_prefix(root)
        .map_err(|_| WorkspaceError::EscapesWorkspace)?;
    let mut current = root.to_path_buf();
    for component in relative.components() {
        let Component::Normal(segment) = component else {
            return Err(WorkspaceError::InvalidRelativePath);
        };
        current.push(segment);
        if current.exists() {
            reject_link(&current)?;
        }
    }
    Ok(())
}

fn reject_link(path: &Path) -> Result<(), WorkspaceError> {
    let metadata = fs::symlink_metadata(path)?;
    if metadata.file_type().is_symlink() {
        Err(WorkspaceError::LinkNotAllowed)
    } else {
        Ok(())
    }
}

#[cfg(not(windows))]
fn sync_parent(path: &Path) -> Result<(), WorkspaceError> {
    if let Some(parent) = path.parent() {
        File::open(parent)?.sync_all()?;
    }
    Ok(())
}

// std::fs는 Windows directory handle의 FILE_FLAG_BACKUP_SEMANTICS를 노출하지 않는다.
// 파일 자체는 sync_all하고 publication은 동일 volume hard-link로 원자화한다.
#[cfg(windows)]
#[allow(clippy::unnecessary_wraps)] // 플랫폼 공통 호출부가 Result contract를 유지한다.
fn sync_parent(_path: &Path) -> Result<(), WorkspaceError> {
    Ok(())
}

#[cfg(test)]
mod tests {
    use std::path::Path;

    use tempfile::tempdir;

    use super::{SecureWorkspace, WorkspaceError};

    #[cfg(unix)]
    fn create_directory_link(target: &Path, link: &Path) -> std::io::Result<()> {
        std::os::unix::fs::symlink(target, link)
    }

    #[cfg(windows)]
    fn create_directory_link(target: &Path, link: &Path) -> std::io::Result<()> {
        std::os::windows::fs::symlink_dir(target, link)
    }

    #[test]
    fn rejects_traversal_absolute_and_empty_paths() {
        let temporary = tempdir().unwrap_or_else(|error| panic!("tempdir: {error}"));
        let workspace = SecureWorkspace::create(temporary.path().join("work"))
            .unwrap_or_else(|error| panic!("workspace: {error}"));
        for invalid in [
            Path::new("../escape"),
            Path::new("a/../../escape"),
            Path::new(""),
        ] {
            assert!(matches!(
                workspace.stage_bytes(invalid, b"x"),
                Err(WorkspaceError::InvalidRelativePath)
            ));
        }
        let absolute = temporary.path().join("outside");
        assert!(matches!(
            workspace.stage_bytes(&absolute, b"x"),
            Err(WorkspaceError::InvalidRelativePath)
        ));
    }

    #[test]
    fn safely_reopens_an_existing_workspace_root() {
        let temporary = tempdir().unwrap_or_else(|error| panic!("tempdir: {error}"));
        let root = temporary.path().join("work");
        let _first = SecureWorkspace::create(&root)
            .unwrap_or_else(|error| panic!("first workspace: {error}"));
        let _second = SecureWorkspace::create(&root)
            .unwrap_or_else(|error| panic!("second workspace: {error}"));
    }

    #[test]
    fn rejects_a_link_inserted_below_staging() {
        let temporary = tempdir().unwrap_or_else(|error| panic!("tempdir: {error}"));
        let root = temporary.path().join("work");
        let outside = temporary.path().join("outside");
        std::fs::create_dir(&outside).unwrap_or_else(|error| panic!("create outside: {error}"));
        let workspace =
            SecureWorkspace::create(&root).unwrap_or_else(|error| panic!("workspace: {error}"));
        create_directory_link(&outside, &root.join("staging/link"))
            .unwrap_or_else(|error| panic!("create directory link: {error}"));
        assert!(matches!(
            workspace.stage_bytes(Path::new("link/escape.bin"), b"escape"),
            Err(WorkspaceError::LinkNotAllowed)
        ));
        assert!(!outside.join("escape.bin").exists());
    }

    #[test]
    fn atomically_publishes_without_overwrite() {
        let temporary = tempdir().unwrap_or_else(|error| panic!("tempdir: {error}"));
        let workspace = SecureWorkspace::create(temporary.path().join("work"))
            .unwrap_or_else(|error| panic!("workspace: {error}"));
        let first = workspace
            .stage_bytes(Path::new("job-1/a.bin"), b"first")
            .unwrap_or_else(|error| panic!("stage: {error}"));
        let published = workspace
            .publish(&first, Path::new("artifacts/a.bin"))
            .unwrap_or_else(|error| panic!("publish: {error}"));
        let first_bytes =
            std::fs::read(&published).unwrap_or_else(|error| panic!("read published: {error}"));
        assert_eq!(first_bytes, b"first");

        let second = workspace
            .stage_bytes(Path::new("job-2/a.bin"), b"second")
            .unwrap_or_else(|error| panic!("stage: {error}"));
        assert!(matches!(
            workspace.publish(&second, Path::new("artifacts/a.bin")),
            Err(WorkspaceError::ArtifactExists)
        ));
        let preserved =
            std::fs::read(&published).unwrap_or_else(|error| panic!("read preserved: {error}"));
        assert_eq!(preserved, b"first");
    }

    #[test]
    fn interruption_cleanup_never_removes_published_output() {
        let temporary = tempdir().unwrap_or_else(|error| panic!("tempdir: {error}"));
        let workspace = SecureWorkspace::create(temporary.path().join("work"))
            .unwrap_or_else(|error| panic!("workspace: {error}"));
        let complete = workspace
            .stage_bytes(Path::new("job-ok/a.bin"), b"complete")
            .unwrap_or_else(|error| panic!("stage: {error}"));
        let published = workspace
            .publish(&complete, Path::new("a.bin"))
            .unwrap_or_else(|error| panic!("publish: {error}"));
        let _interrupted = workspace
            .stage_bytes(Path::new("job-interrupted/a.bin"), b"partial")
            .unwrap_or_else(|error| panic!("stage: {error}"));
        workspace
            .cleanup_staging(Path::new("job-interrupted"))
            .unwrap_or_else(|error| panic!("cleanup: {error}"));
        let complete_bytes =
            std::fs::read(published).unwrap_or_else(|error| panic!("read complete: {error}"));
        assert_eq!(complete_bytes, b"complete");
    }

    #[test]
    fn quarantine_is_atomic_and_never_overwrites() {
        let temporary = tempdir().unwrap_or_else(|error| panic!("tempdir: {error}"));
        let workspace = SecureWorkspace::create(temporary.path().join("work"))
            .unwrap_or_else(|error| panic!("workspace: {error}"));
        let first = workspace
            .stage_bytes(Path::new("job-1/suspicious.bin"), b"first")
            .unwrap_or_else(|error| panic!("stage: {error}"));
        let quarantined = workspace
            .quarantine(&first, Path::new("malicious/suspicious.bin"))
            .unwrap_or_else(|error| panic!("quarantine: {error}"));
        let second = workspace
            .stage_bytes(Path::new("job-2/suspicious.bin"), b"second")
            .unwrap_or_else(|error| panic!("stage: {error}"));
        assert!(matches!(
            workspace.quarantine(&second, Path::new("malicious/suspicious.bin")),
            Err(WorkspaceError::ArtifactExists)
        ));
        let bytes =
            std::fs::read(quarantined).unwrap_or_else(|error| panic!("read quarantine: {error}"));
        assert_eq!(bytes, b"first");
    }
}
