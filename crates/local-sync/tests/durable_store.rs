use std::error::Error;
use std::fs;

use local_sync::{
    Connectivity, DurableMirrorStore, LocalMirror, MirrorPhase, RemoteHead, StoreError, SyncError,
};
use tempfile::tempdir;

type TestResult = Result<(), Box<dyn Error>>;

fn digest(character: char) -> String {
    character.to_string().repeat(64)
}

fn mirror(connectivity: Connectivity) -> Result<LocalMirror, SyncError> {
    LocalMirror::new(
        "prj_project01".to_owned(),
        "brn_branch001".to_owned(),
        "mir_mirror001".to_owned(),
        RemoteHead::new(Some("rev_00000001".to_owned()), 1)?,
        digest('a'),
        connectivity,
    )
}

#[test]
fn create_new_journal_round_trips_offline_and_online_transitions() -> TestResult {
    let temporary = tempdir()?;
    let store = DurableMirrorStore::open(temporary.path())?;
    let first = store.initialize(&mirror(Connectivity::Offline)?)?;
    assert_eq!(first.sequence(), 1);

    let (second, ()) = store.update(&first, |state| {
        state.queue_local_change(digest('b'), digest('c'))
    })?;
    assert_eq!(second.sequence(), 2);
    let (third, ()) = store.update(&second, |state| {
        state.set_connectivity(Connectivity::Online);
        Ok(())
    })?;
    assert_eq!(third.sequence(), 3);

    let reopened = DurableMirrorStore::open(temporary.path())?;
    let loaded = reopened.load()?.ok_or("missing mirror")?;
    let snapshot = loaded.mirror().snapshot();
    assert_eq!(loaded.revision().sequence(), 3);
    assert_eq!(snapshot.connectivity, Connectivity::Online);
    assert_eq!(snapshot.phase, MirrorPhase::Ahead);
    assert_eq!(snapshot.snapshot_sha256, digest('b'));
    assert_eq!(snapshot.pending_plan_sha256, Some(digest('c')));
    Ok(())
}

#[test]
fn stale_writer_cannot_overwrite_a_newer_sequence() -> TestResult {
    let temporary = tempdir()?;
    let first_store = DurableMirrorStore::open(temporary.path())?;
    let initial = first_store.initialize(&mirror(Connectivity::Offline)?)?;
    let second_store = DurableMirrorStore::open(temporary.path())?;
    let stale = second_store
        .load()?
        .ok_or("missing mirror")?
        .revision()
        .clone();

    first_store.update(&initial, |state| {
        state.set_connectivity(Connectivity::Online);
        Ok(())
    })?;
    assert_eq!(
        second_store.update(&stale, |state| {
            state.set_connectivity(Connectivity::Online);
            Ok(())
        }),
        Err(StoreError::Conflict)
    );
    assert_eq!(
        first_store
            .load()?
            .ok_or("missing mirror")?
            .revision()
            .sequence(),
        2
    );
    Ok(())
}

#[test]
fn malformed_unknown_and_gapped_entries_fail_closed() -> TestResult {
    let temporary = tempdir()?;
    let store = DurableMirrorStore::open(temporary.path())?;
    store.initialize(&mirror(Connectivity::Offline)?)?;
    let entries = temporary.path().join("p17-local-sync-journal-v1");
    fs::write(entries.join("unexpected.txt"), b"not a journal entry")?;
    assert!(matches!(
        DurableMirrorStore::open(temporary.path()),
        Err(StoreError::Corrupt)
    ));

    let other = tempdir()?;
    let other_entries = other.path().join("p17-local-sync-journal-v1");
    fs::create_dir(&other_entries)?;
    fs::write(other_entries.join("00000000000000000002.json"), b"{}")?;
    assert!(matches!(
        DurableMirrorStore::open(other.path()),
        Err(StoreError::Corrupt)
    ));
    Ok(())
}

#[test]
fn tampering_is_detected_and_debug_output_redacts_paths_and_hashes() -> TestResult {
    let temporary = tempdir()?;
    let store = DurableMirrorStore::open(temporary.path())?;
    let revision = store.initialize(&mirror(Connectivity::Offline)?)?;
    let debug = format!("{store:?} {revision:?}");
    assert!(!debug.contains(&temporary.path().display().to_string()));

    let entry = temporary
        .path()
        .join("p17-local-sync-journal-v1")
        .join("00000000000000000001.json");
    let mut bytes = fs::read(&entry)?;
    let target = bytes
        .iter()
        .position(|byte| *byte == b'a')
        .ok_or("target")?;
    bytes[target] = b'b';
    fs::write(entry, bytes)?;
    assert!(matches!(store.load(), Err(StoreError::Corrupt)));
    Ok(())
}

#[test]
fn non_directory_roots_and_initialized_reuse_are_rejected() -> TestResult {
    let temporary = tempdir()?;
    let file = temporary.path().join("file-root");
    fs::write(&file, b"x")?;
    assert!(matches!(
        DurableMirrorStore::open(&file),
        Err(StoreError::Unavailable | StoreError::InvalidConfiguration)
    ));

    let store = DurableMirrorStore::open(temporary.path().join("store"))?;
    store.initialize(&mirror(Connectivity::Offline)?)?;
    assert_eq!(
        store.initialize(&mirror(Connectivity::Offline)?),
        Err(StoreError::Conflict)
    );
    Ok(())
}
