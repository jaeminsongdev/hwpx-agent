use std::fmt;
use std::fs::{self, File, OpenOptions};
use std::io::{Read, Write};
use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use thiserror::Error;

use crate::{
    CheckpointOutcome, LocalMirror, MirrorSnapshot, PullOutcome, PushOutcome, RemoteSyncPort,
    SyncError,
};

const ENTRY_SCHEMA_VERSION: &str = "hwpx-agent.local-sync-journal-entry/v1";
const ENTRY_DIRECTORY_NAME: &str = "p17-local-sync-journal-v1";
const MAX_ENTRIES: usize = 4_096;
const MAX_ENTRY_BYTES: u64 = 65_536;
const MAX_JOURNAL_BYTES: u64 = 64 * 1_024 * 1_024;

#[derive(Clone, Debug, Error, Eq, PartialEq)]
pub enum StoreError {
    #[error("local sync store configuration is invalid")]
    InvalidConfiguration,
    #[error("local sync store is unavailable")]
    Unavailable,
    #[error("local sync journal is corrupt")]
    Corrupt,
    #[error("local sync journal reached its capacity")]
    CapacityExceeded,
    #[error("local sync store revision conflicts with another writer")]
    Conflict,
    #[error("local sync state transition was rejected")]
    TransitionRejected,
}

#[derive(Clone, Debug, Error, Eq, PartialEq)]
pub enum DurableSyncError {
    #[error("local sync durable store rejected the operation")]
    Store(#[from] StoreError),
    #[error("local sync state or remote operation was rejected")]
    Sync(#[from] SyncError),
}

#[derive(Clone, Eq, PartialEq)]
pub struct StoreRevision {
    sequence: u64,
    checksum_sha256: String,
}

impl fmt::Debug for StoreRevision {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("StoreRevision")
            .field("sequence", &self.sequence)
            .field("checksum_sha256", &"<redacted>")
            .finish()
    }
}

impl StoreRevision {
    #[must_use]
    pub const fn sequence(&self) -> u64 {
        self.sequence
    }
}

#[derive(Clone)]
pub struct LoadedMirror {
    revision: StoreRevision,
    mirror: LocalMirror,
}

impl fmt::Debug for LoadedMirror {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("LoadedMirror")
            .field("revision", &self.revision)
            .field("mirror", &self.mirror)
            .finish()
    }
}

impl LoadedMirror {
    #[must_use]
    pub const fn revision(&self) -> &StoreRevision {
        &self.revision
    }

    #[must_use]
    pub const fn mirror(&self) -> &LocalMirror {
        &self.mirror
    }
}

#[derive(Clone)]
pub struct DurableMirrorStore {
    entries: PathBuf,
}

impl fmt::Debug for DurableMirrorStore {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("DurableMirrorStore")
            .field("entries", &"<redacted>")
            .finish()
    }
}

impl DurableMirrorStore {
    /// Opens or creates one create-new, immutable-entry local mirror journal.
    ///
    /// # Errors
    ///
    /// Fails closed on links/reparse points, malformed history, capacity or I/O failure.
    pub fn open(root: impl AsRef<Path>) -> Result<Self, StoreError> {
        let requested = root.as_ref();
        if requested.as_os_str().is_empty() {
            return Err(StoreError::InvalidConfiguration);
        }
        fs::create_dir_all(requested).map_err(|_| StoreError::Unavailable)?;
        require_plain_directory(requested)?;
        let root = requested
            .canonicalize()
            .map_err(|_| StoreError::Unavailable)?;
        require_plain_directory(&root)?;
        let entries = root.join(ENTRY_DIRECTORY_NAME);
        match fs::create_dir(&entries) {
            Ok(()) => {}
            Err(error) if error.kind() == std::io::ErrorKind::AlreadyExists => {}
            Err(_) => return Err(StoreError::Unavailable),
        }
        require_plain_directory(&entries)?;
        let store = Self { entries };
        let _ = store.load()?;
        Ok(store)
    }

    /// Opens an already-created journal without creating a missing path.
    ///
    /// # Errors
    ///
    /// Fails closed when the root/journal is absent, linked, malformed or unavailable.
    pub fn open_existing(root: impl AsRef<Path>) -> Result<Self, StoreError> {
        let requested = root.as_ref();
        if requested.as_os_str().is_empty() {
            return Err(StoreError::InvalidConfiguration);
        }
        require_plain_directory(requested)?;
        let root = requested
            .canonicalize()
            .map_err(|_| StoreError::Unavailable)?;
        require_plain_directory(&root)?;
        let entries = root.join(ENTRY_DIRECTORY_NAME);
        require_plain_directory(&entries)?;
        let store = Self { entries };
        let _ = store.load()?;
        Ok(store)
    }

    /// Loads and verifies the complete bounded journal.
    ///
    /// # Errors
    ///
    /// Fails closed if any entry, checksum, sequence or mirror invariant is invalid.
    pub fn load(&self) -> Result<Option<LoadedMirror>, StoreError> {
        replay(&self.entries)
    }

    /// Writes the first durable mirror state using create-new publication.
    ///
    /// # Errors
    ///
    /// Rejects an initialized store, invalid mirror state, capacity and storage failures.
    pub fn initialize(&self, mirror: &LocalMirror) -> Result<StoreRevision, StoreError> {
        if self.load()?.is_some() {
            return Err(StoreError::Conflict);
        }
        self.append(None, mirror)
    }

    /// Applies one pure local transition to the exact expected durable revision.
    ///
    /// This method is intentionally for local-only mutations. Remote operations must use the
    /// dedicated methods below, which persist effect intent before push/checkpoint I/O.
    ///
    /// # Errors
    ///
    /// Rejects stale revisions, invalid transitions, capacity and storage failures.
    pub fn update<T>(
        &self,
        expected: &StoreRevision,
        operation: impl FnOnce(&mut LocalMirror) -> Result<T, SyncError>,
    ) -> Result<(StoreRevision, T), StoreError> {
        let current = self.load()?.ok_or(StoreError::Conflict)?;
        if current.revision != *expected {
            return Err(StoreError::Conflict);
        }
        let mut mirror = current.mirror;
        let output = operation(&mut mirror).map_err(|_| StoreError::TransitionRejected)?;
        let revision = self.append(Some(expected), &mirror)?;
        Ok((revision, output))
    }

    /// Executes a read-only remote pull and persists any accepted update or conflict transition.
    ///
    /// # Errors
    ///
    /// Fails before remote I/O for invalid/offline/stale state. Remote conflict state is durably
    /// recorded before the semantic conflict is returned.
    pub fn pull_remote(
        &self,
        port: &mut impl RemoteSyncPort,
    ) -> Result<(StoreRevision, PullOutcome), DurableSyncError> {
        let current = self.load()?.ok_or(StoreError::Conflict)?;
        let expected = current.revision;
        let mut mirror = current.mirror;
        let before = mirror.snapshot();
        let outcome = mirror.pull(port);
        let revision = if mirror.snapshot() == before {
            expected
        } else {
            self.append_exact(&expected, &mirror)?
        };
        outcome
            .map(|value| (revision, value))
            .map_err(DurableSyncError::Sync)
    }

    /// Persists a push idempotency intent, performs one injected remote exchange, then persists the
    /// terminal response using an exact journal CAS.
    ///
    /// # Errors
    ///
    /// Unavailable or malformed outcomes leave the first idempotency key durably pending. A later
    /// retry must use the same key. Stale writers fail before or after I/O without overwriting.
    pub fn push_remote(
        &self,
        port: &mut impl RemoteSyncPort,
        idempotency_key: String,
    ) -> Result<(StoreRevision, PushOutcome), DurableSyncError> {
        let current = self.load()?.ok_or(StoreError::Conflict)?;
        let mut mirror = current.mirror;
        let (request, intent_changed) = mirror.prepare_push(idempotency_key)?;
        let intent_revision = if intent_changed {
            self.append_exact(&current.revision, &mirror)?
        } else {
            current.revision
        };
        let pending = mirror.snapshot();
        let response = port.push(&request);
        let outcome = mirror.apply_push_result(&request, response);
        let revision = if mirror.snapshot() == pending {
            intent_revision
        } else {
            self.append_exact(&intent_revision, &mirror)?
        };
        outcome
            .map(|value| (revision, value))
            .map_err(DurableSyncError::Sync)
    }

    /// Persists an exact checkpoint-request intent before performing the injected remote exchange.
    ///
    /// # Errors
    ///
    /// Unavailable or malformed outcomes retain the pending key and request digest for safe replay.
    /// Definitive rejection, conflict and success are durably recorded with an exact journal CAS.
    pub fn checkpoint_remote(
        &self,
        port: &mut impl RemoteSyncPort,
        idempotency_key: String,
        label: String,
        note: Option<String>,
    ) -> Result<(StoreRevision, CheckpointOutcome), DurableSyncError> {
        let current = self.load()?.ok_or(StoreError::Conflict)?;
        let mut mirror = current.mirror;
        let (request, intent_changed) = mirror.prepare_checkpoint(idempotency_key, label, note)?;
        let intent_revision = if intent_changed {
            self.append_exact(&current.revision, &mirror)?
        } else {
            current.revision
        };
        let pending = mirror.snapshot();
        let response = port.checkpoint(&request);
        let outcome = mirror.apply_checkpoint_result(&request, response);
        let revision = if mirror.snapshot() == pending {
            intent_revision
        } else {
            self.append_exact(&intent_revision, &mirror)?
        };
        outcome
            .map(|value| (revision, value))
            .map_err(DurableSyncError::Sync)
    }

    fn append_exact(
        &self,
        expected: &StoreRevision,
        mirror: &LocalMirror,
    ) -> Result<StoreRevision, StoreError> {
        let current = self.load()?.ok_or(StoreError::Conflict)?;
        if current.revision != *expected {
            return Err(StoreError::Conflict);
        }
        self.append(Some(expected), mirror)
    }

    fn append(
        &self,
        previous: Option<&StoreRevision>,
        mirror: &LocalMirror,
    ) -> Result<StoreRevision, StoreError> {
        require_plain_directory(&self.entries)?;
        let sequence = match previous {
            Some(revision) => revision
                .sequence
                .checked_add(1)
                .ok_or(StoreError::CapacityExceeded)?,
            None => 1,
        };
        if usize::try_from(sequence).map_or(true, |value| value > MAX_ENTRIES) {
            return Err(StoreError::CapacityExceeded);
        }
        let snapshot = mirror.snapshot();
        LocalMirror::restore(snapshot.clone()).map_err(|_| StoreError::TransitionRejected)?;
        let previous_checksum_sha256 = previous.map(|revision| revision.checksum_sha256.clone());
        let checksum_sha256 = checksum(sequence, previous_checksum_sha256.as_deref(), &snapshot)?;
        let entry = JournalEntry {
            schema_version: ENTRY_SCHEMA_VERSION.to_owned(),
            sequence,
            previous_checksum_sha256,
            snapshot,
            checksum_sha256: checksum_sha256.clone(),
        };
        let mut encoded = serde_json::to_vec(&entry).map_err(|_| StoreError::Corrupt)?;
        encoded.push(b'\n');
        if u64::try_from(encoded.len()).map_or(true, |length| length > MAX_ENTRY_BYTES) {
            return Err(StoreError::CapacityExceeded);
        }
        let path = self.entries.join(entry_file_name(sequence));
        let mut stream = match OpenOptions::new().create_new(true).write(true).open(&path) {
            Ok(stream) => stream,
            Err(error) if error.kind() == std::io::ErrorKind::AlreadyExists => {
                return Err(StoreError::Conflict);
            }
            Err(_) => return Err(StoreError::Unavailable),
        };
        stream
            .write_all(&encoded)
            .and_then(|()| stream.sync_all())
            .map_err(|_| StoreError::Unavailable)?;
        sync_directory(&self.entries)?;
        Ok(StoreRevision {
            sequence,
            checksum_sha256,
        })
    }
}

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct JournalEntry {
    schema_version: String,
    sequence: u64,
    previous_checksum_sha256: Option<String>,
    snapshot: MirrorSnapshot,
    checksum_sha256: String,
}

#[derive(Serialize)]
struct ChecksumPayload<'a> {
    schema_version: &'static str,
    sequence: u64,
    previous_checksum_sha256: Option<&'a str>,
    snapshot: &'a MirrorSnapshot,
}

fn replay(entries: &Path) -> Result<Option<LoadedMirror>, StoreError> {
    require_plain_directory(entries)?;
    let mut paths = Vec::new();
    let mut total_bytes = 0_u64;
    for candidate in fs::read_dir(entries).map_err(|_| StoreError::Unavailable)? {
        let candidate = candidate.map_err(|_| StoreError::Unavailable)?;
        if paths.len() >= MAX_ENTRIES {
            return Err(StoreError::CapacityExceeded);
        }
        let name = candidate.file_name();
        let name = name.to_str().ok_or(StoreError::Corrupt)?;
        let sequence = parse_entry_file_name(name).ok_or(StoreError::Corrupt)?;
        let metadata =
            fs::symlink_metadata(candidate.path()).map_err(|_| StoreError::Unavailable)?;
        if !metadata.is_file() || is_link_or_reparse(&metadata) {
            return Err(StoreError::Corrupt);
        }
        if metadata.len() > MAX_ENTRY_BYTES {
            return Err(StoreError::CapacityExceeded);
        }
        total_bytes = total_bytes
            .checked_add(metadata.len())
            .ok_or(StoreError::CapacityExceeded)?;
        if total_bytes > MAX_JOURNAL_BYTES {
            return Err(StoreError::CapacityExceeded);
        }
        paths.push((sequence, candidate.path(), metadata.len()));
    }
    paths.sort_unstable_by_key(|(sequence, _, _)| *sequence);

    let mut previous_revision: Option<StoreRevision> = None;
    let mut previous_mirror: Option<LocalMirror> = None;
    for (index, (sequence, path, expected_length)) in paths.into_iter().enumerate() {
        let expected_sequence = u64::try_from(index)
            .ok()
            .and_then(|value| value.checked_add(1))
            .ok_or(StoreError::CapacityExceeded)?;
        if sequence != expected_sequence {
            return Err(StoreError::Corrupt);
        }
        let stream = File::open(path).map_err(|_| StoreError::Unavailable)?;
        let mut bytes = Vec::new();
        stream
            .take(MAX_ENTRY_BYTES + 1)
            .read_to_end(&mut bytes)
            .map_err(|_| StoreError::Unavailable)?;
        if u64::try_from(bytes.len()).ok() != Some(expected_length)
            || u64::try_from(bytes.len()).map_or(true, |length| length > MAX_ENTRY_BYTES)
        {
            return Err(StoreError::Corrupt);
        }
        let entry: JournalEntry =
            serde_json::from_slice(&bytes).map_err(|_| StoreError::Corrupt)?;
        let expected_previous = previous_revision
            .as_ref()
            .map(|revision| revision.checksum_sha256.as_str());
        let expected_checksum = checksum(sequence, expected_previous, &entry.snapshot)?;
        if entry.schema_version != ENTRY_SCHEMA_VERSION
            || entry.sequence != sequence
            || entry.previous_checksum_sha256.as_deref() != expected_previous
            || entry.checksum_sha256 != expected_checksum
        {
            return Err(StoreError::Corrupt);
        }
        let mirror = LocalMirror::restore(entry.snapshot).map_err(|_| StoreError::Corrupt)?;
        previous_revision = Some(StoreRevision {
            sequence,
            checksum_sha256: expected_checksum,
        });
        previous_mirror = Some(mirror);
    }
    Ok(previous_revision
        .zip(previous_mirror)
        .map(|(revision, mirror)| LoadedMirror { revision, mirror }))
}

fn checksum(
    sequence: u64,
    previous_checksum_sha256: Option<&str>,
    snapshot: &MirrorSnapshot,
) -> Result<String, StoreError> {
    let payload = ChecksumPayload {
        schema_version: ENTRY_SCHEMA_VERSION,
        sequence,
        previous_checksum_sha256,
        snapshot,
    };
    let encoded = serde_json::to_vec(&payload).map_err(|_| StoreError::Corrupt)?;
    Ok(hex::encode(Sha256::digest(encoded)))
}

fn entry_file_name(sequence: u64) -> String {
    format!("{sequence:020}.json")
}

fn parse_entry_file_name(name: &str) -> Option<u64> {
    let sequence = name.strip_suffix(".json")?;
    if sequence.len() != 20 || !sequence.bytes().all(|byte| byte.is_ascii_digit()) {
        return None;
    }
    let parsed = sequence.parse().ok()?;
    (parsed > 0).then_some(parsed)
}

fn require_plain_directory(path: &Path) -> Result<(), StoreError> {
    let metadata = fs::symlink_metadata(path).map_err(|_| StoreError::Unavailable)?;
    if metadata.is_dir() && !is_link_or_reparse(&metadata) {
        Ok(())
    } else {
        Err(StoreError::InvalidConfiguration)
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

#[cfg(not(windows))]
fn sync_directory(path: &Path) -> Result<(), StoreError> {
    File::open(path)
        .and_then(|directory| directory.sync_all())
        .map_err(|_| StoreError::Unavailable)
}

// Rust std does not expose FILE_FLAG_BACKUP_SEMANTICS for Windows directory handles. Each immutable
// entry itself is still sync_all'ed, and create_new supplies the cross-process sequence fence.
#[cfg(windows)]
#[allow(clippy::unnecessary_wraps)]
fn sync_directory(_path: &Path) -> Result<(), StoreError> {
    Ok(())
}
