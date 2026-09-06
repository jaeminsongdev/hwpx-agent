use std::collections::BTreeSet;
use std::fmt;
use std::fs::{self, File, OpenOptions};
use std::io::{Read, Write};
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};

use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};

use crate::{ApprovalError, ConfirmationReplayLedger, valid_digest};

const ENTRY_SCHEMA: &str = "hwpx-agent.approval-replay-entry/v1";
const ENTRY_DIRECTORY: &str = "p17-approval-replay-v1";
const STAGING_DIRECTORY: &str = "p17-approval-replay-staging-v1";
const HARD_MAX_ENTRIES: usize = 65_536;
const MAX_ENTRY_BYTES: u64 = 2_048;
const MAX_LEDGER_BYTES: u64 = 64 * 1_024 * 1_024;
const MAX_STAGE_ATTEMPTS: usize = 32;

static NEXT_STAGE_ID: AtomicU64 = AtomicU64::new(1);

#[derive(Clone)]
pub struct DurableReplayLedger {
    entries: PathBuf,
    staging: PathBuf,
}

impl fmt::Debug for DurableReplayLedger {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("DurableReplayLedger")
            .field("entries", &"<redacted>")
            .field("staging", &"<redacted>")
            .finish()
    }
}

impl DurableReplayLedger {
    /// Opens or creates a bounded immutable-entry confirmation replay ledger.
    ///
    /// # Errors
    ///
    /// Fails closed for unsafe paths, links, corruption, capacity and I/O errors.
    pub fn open(root: impl AsRef<Path>) -> Result<Self, ApprovalError> {
        let requested = root.as_ref();
        if requested.as_os_str().is_empty() {
            return Err(ApprovalError::InvalidConfiguration);
        }
        fs::create_dir_all(requested).map_err(|_| ApprovalError::LedgerUnavailable)?;
        require_directory(requested)?;
        let root = requested
            .canonicalize()
            .map_err(|_| ApprovalError::LedgerUnavailable)?;
        require_directory(&root)?;
        let entries = root.join(ENTRY_DIRECTORY);
        match fs::create_dir(&entries) {
            Ok(()) => {}
            Err(error) if error.kind() == std::io::ErrorKind::AlreadyExists => {}
            Err(_) => return Err(ApprovalError::LedgerUnavailable),
        }
        require_directory(&entries)?;
        let staging = root.join(STAGING_DIRECTORY);
        match fs::create_dir(&staging) {
            Ok(()) => {}
            Err(error) if error.kind() == std::io::ErrorKind::AlreadyExists => {}
            Err(_) => return Err(ApprovalError::LedgerUnavailable),
        }
        require_directory(&staging)?;
        let ledger = Self { entries, staging };
        let _ = replay(&ledger.entries)?;
        Ok(ledger)
    }
}

impl ConfirmationReplayLedger for DurableReplayLedger {
    fn consume(
        &mut self,
        token_id_sha256: &str,
        expires_at_unix_seconds: u64,
        now_unix_seconds: u64,
        capacity: usize,
    ) -> Result<(), ApprovalError> {
        if !valid_digest(token_id_sha256)
            || expires_at_unix_seconds <= now_unix_seconds
            || !(1..=HARD_MAX_ENTRIES).contains(&capacity)
        {
            return Err(ApprovalError::InvalidRequest);
        }
        let current = replay(&self.entries)?;
        if current.consumed.contains(token_id_sha256) {
            return Err(ApprovalError::ConfirmationReplay);
        }
        if current.consumed.len() >= capacity
            || usize::try_from(current.sequence).map_or(true, |value| value >= HARD_MAX_ENTRIES)
        {
            return Err(ApprovalError::CapacityExceeded);
        }
        let sequence = current
            .sequence
            .checked_add(1)
            .ok_or(ApprovalError::CapacityExceeded)?;
        let previous_checksum_sha256 = current.checksum_sha256;
        let checksum_sha256 = checksum(
            sequence,
            previous_checksum_sha256.as_deref(),
            token_id_sha256,
            expires_at_unix_seconds,
            now_unix_seconds,
        )?;
        let entry = ReplayEntry {
            schema_version: ENTRY_SCHEMA.to_owned(),
            sequence,
            previous_checksum_sha256,
            token_id_sha256: token_id_sha256.to_owned(),
            expires_at_unix_seconds,
            consumed_at_unix_seconds: now_unix_seconds,
            checksum_sha256,
        };
        let mut encoded = serde_json::to_vec(&entry).map_err(|_| ApprovalError::LedgerCorrupt)?;
        encoded.push(b'\n');
        if u64::try_from(encoded.len()).map_or(true, |length| length > MAX_ENTRY_BYTES) {
            return Err(ApprovalError::CapacityExceeded);
        }
        let (staged_path, mut stream) = create_staged_entry(&self.staging, token_id_sha256)?;
        let write_result = stream
            .write_all(&encoded)
            .and_then(|()| stream.sync_all())
            .map_err(|_| ApprovalError::LedgerUnavailable);
        if let Err(error) = write_result {
            drop(stream);
            let _ = fs::remove_file(&staged_path);
            return Err(error);
        }
        drop(stream);

        let published_path = self.entries.join(entry_name(sequence));
        match fs::hard_link(&staged_path, published_path) {
            Ok(()) => {
                let sync_result = sync_directory(&self.entries);
                let _ = fs::remove_file(&staged_path);
                let _ = sync_directory(&self.staging);
                sync_result
            }
            Err(error) if error.kind() == std::io::ErrorKind::AlreadyExists => {
                let _ = fs::remove_file(&staged_path);
                let concurrent = replay(&self.entries)?;
                if concurrent.consumed.contains(token_id_sha256) {
                    Err(ApprovalError::ConfirmationReplay)
                } else {
                    Err(ApprovalError::LedgerConflict)
                }
            }
            Err(_) => {
                let _ = fs::remove_file(&staged_path);
                Err(ApprovalError::LedgerUnavailable)
            }
        }
    }
}

fn create_staged_entry(
    staging: &Path,
    token_id_sha256: &str,
) -> Result<(PathBuf, File), ApprovalError> {
    require_directory(staging)?;
    for _ in 0..MAX_STAGE_ATTEMPTS {
        let stage_id = NEXT_STAGE_ID.fetch_add(1, Ordering::Relaxed);
        let name_seed = format!("{}:{stage_id}:{token_id_sha256}", std::process::id());
        let name = format!("{}.pending", hex::encode(Sha256::digest(name_seed)));
        let path = staging.join(name);
        match OpenOptions::new().create_new(true).write(true).open(&path) {
            Ok(stream) => return Ok((path, stream)),
            Err(error) if error.kind() == std::io::ErrorKind::AlreadyExists => {}
            Err(_) => return Err(ApprovalError::LedgerUnavailable),
        }
    }
    Err(ApprovalError::LedgerUnavailable)
}

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct ReplayEntry {
    schema_version: String,
    sequence: u64,
    previous_checksum_sha256: Option<String>,
    token_id_sha256: String,
    expires_at_unix_seconds: u64,
    consumed_at_unix_seconds: u64,
    checksum_sha256: String,
}

#[derive(Serialize)]
struct ChecksumPayload<'a> {
    schema_version: &'static str,
    sequence: u64,
    previous_checksum_sha256: Option<&'a str>,
    token_id_sha256: &'a str,
    expires_at_unix_seconds: u64,
    consumed_at_unix_seconds: u64,
}

struct ReplayState {
    sequence: u64,
    checksum_sha256: Option<String>,
    consumed: BTreeSet<String>,
}

fn replay(entries: &Path) -> Result<ReplayState, ApprovalError> {
    require_directory(entries)?;
    let mut paths = Vec::new();
    let mut total_bytes = 0_u64;
    for candidate in fs::read_dir(entries).map_err(|_| ApprovalError::LedgerUnavailable)? {
        let candidate = candidate.map_err(|_| ApprovalError::LedgerUnavailable)?;
        if paths.len() >= HARD_MAX_ENTRIES {
            return Err(ApprovalError::CapacityExceeded);
        }
        let name = candidate.file_name();
        let name = name.to_str().ok_or(ApprovalError::LedgerCorrupt)?;
        let sequence = parse_entry_name(name).ok_or(ApprovalError::LedgerCorrupt)?;
        let metadata =
            fs::symlink_metadata(candidate.path()).map_err(|_| ApprovalError::LedgerUnavailable)?;
        if !metadata.is_file() || is_link_or_reparse(&metadata) {
            return Err(ApprovalError::LedgerCorrupt);
        }
        if metadata.len() > MAX_ENTRY_BYTES {
            return Err(ApprovalError::CapacityExceeded);
        }
        total_bytes = total_bytes
            .checked_add(metadata.len())
            .ok_or(ApprovalError::CapacityExceeded)?;
        if total_bytes > MAX_LEDGER_BYTES {
            return Err(ApprovalError::CapacityExceeded);
        }
        paths.push((sequence, candidate.path(), metadata.len()));
    }
    paths.sort_unstable_by_key(|(sequence, _, _)| *sequence);

    let mut state = ReplayState {
        sequence: 0,
        checksum_sha256: None,
        consumed: BTreeSet::new(),
    };
    for (index, (sequence, path, expected_length)) in paths.into_iter().enumerate() {
        let expected_sequence = u64::try_from(index)
            .ok()
            .and_then(|value| value.checked_add(1))
            .ok_or(ApprovalError::CapacityExceeded)?;
        if sequence != expected_sequence {
            return Err(ApprovalError::LedgerCorrupt);
        }
        let stream = File::open(path).map_err(|_| ApprovalError::LedgerUnavailable)?;
        let mut bytes = Vec::new();
        stream
            .take(MAX_ENTRY_BYTES + 1)
            .read_to_end(&mut bytes)
            .map_err(|_| ApprovalError::LedgerUnavailable)?;
        if u64::try_from(bytes.len()).ok() != Some(expected_length)
            || u64::try_from(bytes.len()).map_or(true, |length| length > MAX_ENTRY_BYTES)
        {
            return Err(ApprovalError::LedgerCorrupt);
        }
        let entry: ReplayEntry =
            serde_json::from_slice(&bytes).map_err(|_| ApprovalError::LedgerCorrupt)?;
        let expected_checksum = checksum(
            sequence,
            state.checksum_sha256.as_deref(),
            &entry.token_id_sha256,
            entry.expires_at_unix_seconds,
            entry.consumed_at_unix_seconds,
        )?;
        if entry.schema_version != ENTRY_SCHEMA
            || entry.sequence != sequence
            || entry.previous_checksum_sha256 != state.checksum_sha256
            || entry.checksum_sha256 != expected_checksum
            || !valid_digest(&entry.token_id_sha256)
            || entry.expires_at_unix_seconds <= entry.consumed_at_unix_seconds
            || !state.consumed.insert(entry.token_id_sha256)
        {
            return Err(ApprovalError::LedgerCorrupt);
        }
        state.sequence = sequence;
        state.checksum_sha256 = Some(expected_checksum);
    }
    Ok(state)
}

fn checksum(
    sequence: u64,
    previous_checksum_sha256: Option<&str>,
    token_id_sha256: &str,
    expires_at_unix_seconds: u64,
    consumed_at_unix_seconds: u64,
) -> Result<String, ApprovalError> {
    let payload = ChecksumPayload {
        schema_version: ENTRY_SCHEMA,
        sequence,
        previous_checksum_sha256,
        token_id_sha256,
        expires_at_unix_seconds,
        consumed_at_unix_seconds,
    };
    let encoded = serde_json::to_vec(&payload).map_err(|_| ApprovalError::LedgerCorrupt)?;
    Ok(hex::encode(Sha256::digest(encoded)))
}

fn entry_name(sequence: u64) -> String {
    format!("{sequence:020}.json")
}

fn parse_entry_name(name: &str) -> Option<u64> {
    let digits = name.strip_suffix(".json")?;
    if digits.len() != 20 || !digits.bytes().all(|byte| byte.is_ascii_digit()) {
        return None;
    }
    let sequence = digits.parse().ok()?;
    (sequence > 0).then_some(sequence)
}

fn require_directory(path: &Path) -> Result<(), ApprovalError> {
    let metadata = fs::symlink_metadata(path).map_err(|_| ApprovalError::LedgerUnavailable)?;
    if metadata.is_dir() && !is_link_or_reparse(&metadata) {
        Ok(())
    } else {
        Err(ApprovalError::InvalidConfiguration)
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
fn sync_directory(path: &Path) -> Result<(), ApprovalError> {
    File::open(path)
        .and_then(|directory| directory.sync_all())
        .map_err(|_| ApprovalError::LedgerUnavailable)
}

#[cfg(windows)]
#[allow(clippy::unnecessary_wraps)]
fn sync_directory(_path: &Path) -> Result<(), ApprovalError> {
    Ok(())
}
