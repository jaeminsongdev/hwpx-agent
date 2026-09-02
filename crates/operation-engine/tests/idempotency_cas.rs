use std::error::Error;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::{Arc, Barrier};
use std::thread;

use domain_ir::{ArtifactId, DocumentId, IdempotencyKey, ProjectId, RevisionId, TransactionId};
use operation_engine::{
    ClaimLease, ClaimOutcome, IdempotencyBinding, IdempotencyError, IdempotencyLimits,
    IdempotencyService, IdempotencyState, IdempotencyStore, OwnerToken, ReconcileObservation,
    RevisionCommit, RevisionStreamKey, TerminalFailure,
};

type TestResult = Result<(), Box<dyn Error>>;

#[test]
fn identical_terminal_retry_replays_byte_exactly_without_second_revision() -> TestResult {
    let service = IdempotencyService::new(IdempotencyLimits::default())?;
    let stream = stream("document-main")?;
    let revision_one = revision("revision-1")?;
    service.initialize_stream(stream.clone(), revision_one.clone())?;
    let binding = binding("key-main", stream.clone(), revision_one, 1, 1)?;
    let lease = acquired(service.claim(binding.clone(), &owner(1)?)?)?;
    assert_eq!(service.heartbeat(&lease)?, 1);
    service.start(&lease)?;
    assert_eq!(service.heartbeat(&lease)?, 2);
    let commit = commit("revision-2", 2, IdempotencyLimits::default())?;
    let receipt = service.commit_success(&lease, &commit)?;
    assert_eq!(receipt.state(), IdempotencyState::Succeeded);
    assert_eq!(service.head(&stream)?.generation(), 2);

    let replay = service.claim(binding, &owner(2)?)?;
    let ClaimOutcome::Replayed(replayed) = replay else {
        return Err("expected terminal replay".into());
    };
    assert_eq!(receipt.canonical_json()?, replayed.canonical_json()?);
    assert_eq!(service.head(&stream)?.generation(), 2);
    assert_eq!(service.start(&lease), Err(IdempotencyError::InvalidState));
    Ok(())
}

#[test]
fn key_reuse_with_any_binding_drift_is_conflict_without_mutation() -> TestResult {
    let service = IdempotencyService::new(IdempotencyLimits::default())?;
    let stream = stream("document-main")?;
    let revision_one = revision("revision-1")?;
    service.initialize_stream(stream.clone(), revision_one.clone())?;
    let original = binding("same-key", stream.clone(), revision_one.clone(), 1, 1)?;
    let _lease = acquired(service.claim(original, &owner(1)?)?)?;
    let drifted = binding("same-key", stream.clone(), revision_one, 1, 9)?;
    assert_eq!(
        service.claim(drifted, &owner(2)?),
        Err(IdempotencyError::KeyReuseConflict)
    );
    assert_eq!(service.record_count()?, 1);
    assert_eq!(service.head(&stream)?.generation(), 1);
    Ok(())
}

#[test]
fn missing_and_stale_head_claims_create_no_record() -> TestResult {
    let service = IdempotencyService::new(IdempotencyLimits::default())?;
    let missing_stream = stream("missing-document")?;
    let revision_one = revision("revision-1")?;
    let missing = binding("missing-key", missing_stream, revision_one.clone(), 1, 1)?;
    assert_eq!(
        service.claim(missing, &owner(1)?),
        Err(IdempotencyError::RevisionStreamMissing)
    );
    assert_eq!(service.record_count()?, 0);

    let live_stream = stream("live-document")?;
    service.initialize_stream(live_stream.clone(), revision_one)?;
    let stale = binding(
        "stale-key",
        live_stream.clone(),
        revision("wrong-revision")?,
        1,
        2,
    )?;
    assert_eq!(
        service.claim(stale, &owner(2)?),
        Err(IdempotencyError::RevisionConflict)
    );
    assert_eq!(service.record_count()?, 0);
    assert_eq!(service.head(&live_stream)?.generation(), 1);
    Ok(())
}

#[test]
fn concurrent_claim_and_commit_have_exactly_one_owner_and_effect() -> TestResult {
    let service = Arc::new(IdempotencyService::new(IdempotencyLimits::default())?);
    let stream = stream("document-concurrent")?;
    let revision_one = revision("revision-1")?;
    service.initialize_stream(stream.clone(), revision_one.clone())?;
    let binding = binding("concurrent-key", stream.clone(), revision_one, 1, 1)?;
    let barrier = Arc::new(Barrier::new(32));
    let effect_count = Arc::new(AtomicUsize::new(0));
    let mut handles = Vec::new();
    for index in 0..32_u8 {
        let service = Arc::clone(&service);
        let binding = binding.clone();
        let barrier = Arc::clone(&barrier);
        let effect_count = Arc::clone(&effect_count);
        handles.push(thread::spawn(move || {
            barrier.wait();
            let outcome =
                owner(index.saturating_add(1)).and_then(|token| service.claim(binding, &token))?;
            if matches!(outcome, ClaimOutcome::Acquired(_)) {
                let _ = effect_count.fetch_add(1, Ordering::SeqCst);
            }
            Ok::<_, IdempotencyError>(outcome)
        }));
    }
    let mut acquired_leases = Vec::new();
    let mut duplicates = 0;
    for handle in handles {
        match handle.join().map_err(|_| "claim thread panicked")?? {
            ClaimOutcome::Acquired(lease) => acquired_leases.push(lease),
            ClaimOutcome::Duplicate(IdempotencyState::Claimed) => duplicates += 1,
            other => return Err(format!("unexpected claim outcome: {other:?}").into()),
        }
    }
    assert_eq!(acquired_leases.len(), 1);
    assert_eq!(duplicates, 31);
    assert_eq!(effect_count.load(Ordering::SeqCst), 1);
    let lease = acquired_leases.pop().ok_or("missing owner lease")?;
    service.start(&lease)?;

    let commit_barrier = Arc::new(Barrier::new(16));
    let mut commit_handles = Vec::new();
    for _ in 0..16 {
        let service = Arc::clone(&service);
        let lease = lease.clone();
        let commit = commit("revision-2", 2, IdempotencyLimits::default())?;
        let barrier = Arc::clone(&commit_barrier);
        commit_handles.push(thread::spawn(move || {
            barrier.wait();
            service.commit_success(&lease, &commit)
        }));
    }
    let mut committed = 0;
    let mut rejected = 0;
    for handle in commit_handles {
        match handle.join().map_err(|_| "commit thread panicked")? {
            Ok(_) => committed += 1,
            Err(IdempotencyError::InvalidState) => rejected += 1,
            other => return Err(format!("unexpected commit result: {other:?}").into()),
        }
    }
    assert_eq!(committed, 1);
    assert_eq!(rejected, 15);
    assert_eq!(service.head(&stream)?.generation(), 2);
    Ok(())
}

#[test]
fn terminal_retry_storm_only_replays_and_never_recommits() -> TestResult {
    let service = Arc::new(IdempotencyService::new(IdempotencyLimits::default())?);
    let stream = stream("document-replay")?;
    let revision_one = revision("revision-1")?;
    service.initialize_stream(stream.clone(), revision_one.clone())?;
    let binding = binding("replay-key", stream.clone(), revision_one, 1, 1)?;
    let lease = acquired(service.claim(binding.clone(), &owner(1)?)?)?;
    service.start(&lease)?;
    let replay_commit = commit("revision-2", 2, IdempotencyLimits::default())?;
    let receipt = service.commit_success(&lease, &replay_commit)?;
    let expected = receipt.canonical_sha256()?;

    let barrier = Arc::new(Barrier::new(32));
    let mut handles = Vec::new();
    for index in 0..32_u8 {
        let service = Arc::clone(&service);
        let binding = binding.clone();
        let barrier = Arc::clone(&barrier);
        handles.push(thread::spawn(move || {
            barrier.wait();
            owner(index.saturating_add(33)).and_then(|token| service.claim(binding, &token))
        }));
    }
    for handle in handles {
        let ClaimOutcome::Replayed(replay) =
            handle.join().map_err(|_| "replay thread panicked")??
        else {
            return Err("retry was not replayed".into());
        };
        assert_eq!(replay.canonical_sha256()?, expected);
    }
    assert_eq!(service.head(&stream)?.generation(), 2);
    Ok(())
}

#[test]
fn two_valid_claims_racing_on_one_head_make_stale_cas_side_effect_free() -> TestResult {
    let service = IdempotencyService::new(IdempotencyLimits::default())?;
    let stream = stream("document-stale")?;
    let revision_one = revision("revision-1")?;
    service.initialize_stream(stream.clone(), revision_one.clone())?;
    let first_binding = binding("key-first", stream.clone(), revision_one.clone(), 1, 1)?;
    let second_binding = binding("key-second", stream.clone(), revision_one, 1, 2)?;
    let first = acquired(service.claim(first_binding, &owner(1)?)?)?;
    let second = acquired(service.claim(second_binding.clone(), &owner(2)?)?)?;
    service.start(&first)?;
    service.start(&second)?;
    let first_commit = commit("revision-2", 2, IdempotencyLimits::default())?;
    service.commit_success(&first, &first_commit)?;
    let stale_commit = commit("revision-3", 3, IdempotencyLimits::default())?;
    assert_eq!(
        service.commit_success(&second, &stale_commit),
        Err(IdempotencyError::RevisionConflict)
    );
    assert_eq!(
        service.head(&stream)?.revision_id(),
        &revision("revision-2")?
    );
    assert_eq!(service.head(&stream)?.generation(), 2);
    let failed = service.fail_terminal(&second, TerminalFailure::RevisionConflict)?;
    assert_eq!(failed.failure(), Some(TerminalFailure::RevisionConflict));
    assert!(matches!(
        service.claim(second_binding, &owner(3)?)?,
        ClaimOutcome::Replayed(_)
    ));
    Ok(())
}

#[test]
fn committed_unknown_requires_exact_observation_then_replays() -> TestResult {
    let service = IdempotencyService::new(IdempotencyLimits::default())?;
    let stream = stream("document-unknown-commit")?;
    let revision_one = revision("revision-1")?;
    service.initialize_stream(stream.clone(), revision_one.clone())?;
    let binding = binding("unknown-commit-key", stream.clone(), revision_one, 1, 1)?;
    let lease = acquired(service.claim(binding.clone(), &owner(1)?)?)?;
    service.start(&lease)?;
    let exact = commit("revision-2", 2, IdempotencyLimits::default())?;
    service.commit_outcome_unknown(&lease, &exact)?;
    assert_eq!(service.head(&stream)?.generation(), 2);
    assert!(matches!(
        service.claim(binding.clone(), &owner(2)?)?,
        ClaimOutcome::Duplicate(IdempotencyState::OutcomeUnknown)
    ));
    assert_eq!(
        service.reconcile_unknown(
            &lease,
            ReconcileObservation::Committed(commit(
                "revision-wrong",
                9,
                IdempotencyLimits::default()
            )?)
        ),
        Err(IdempotencyError::ReconciliationMismatch)
    );
    let receipt = service.reconcile_unknown(&lease, ReconcileObservation::Committed(exact))?;
    assert_eq!(receipt.state(), IdempotencyState::Succeeded);
    assert_eq!(service.head(&stream)?.generation(), 2);
    assert!(matches!(
        service.claim(binding, &owner(3)?)?,
        ClaimOutcome::Replayed(_)
    ));
    Ok(())
}

#[test]
fn no_effect_unknown_reconciles_to_terminal_failure_without_retry_effect() -> TestResult {
    let service = IdempotencyService::new(IdempotencyLimits::default())?;
    let stream = stream("document-unknown-none")?;
    let revision_one = revision("revision-1")?;
    service.initialize_stream(stream.clone(), revision_one.clone())?;
    let binding = binding("unknown-none-key", stream.clone(), revision_one, 1, 1)?;
    let lease = acquired(service.claim(binding.clone(), &owner(1)?)?)?;
    service.start(&lease)?;
    service.mark_outcome_unknown(&lease)?;
    let receipt = service.reconcile_unknown(&lease, ReconcileObservation::NoEffect)?;
    assert_eq!(receipt.state(), IdempotencyState::FailedTerminal);
    assert_eq!(
        receipt.failure(),
        Some(TerminalFailure::OutcomeNotCommitted)
    );
    assert_eq!(service.head(&stream)?.generation(), 1);
    assert!(matches!(
        service.claim(binding, &owner(2)?)?,
        ClaimOutcome::Replayed(_)
    ));
    let forbidden_commit = commit("revision-2", 2, IdempotencyLimits::default())?;
    assert_eq!(
        service.commit_success(&lease, &forbidden_commit),
        Err(IdempotencyError::InvalidState)
    );
    Ok(())
}

#[test]
fn explicit_terminal_failure_is_immutable_and_replayed() -> TestResult {
    let service = IdempotencyService::new(IdempotencyLimits::default())?;
    let stream = stream("document-failed")?;
    let revision_one = revision("revision-1")?;
    service.initialize_stream(stream.clone(), revision_one.clone())?;
    let binding = binding("failed-key", stream.clone(), revision_one, 1, 1)?;
    let lease = acquired(service.claim(binding.clone(), &owner(1)?)?)?;
    service.start(&lease)?;
    let failed = service.fail_terminal(&lease, TerminalFailure::OperationFailed)?;
    assert_eq!(failed.failure(), Some(TerminalFailure::OperationFailed));
    let ClaimOutcome::Replayed(replay) = service.claim(binding, &owner(2)?)? else {
        return Err("failure was not replayed".into());
    };
    assert_eq!(failed.canonical_json()?, replay.canonical_json()?);
    assert_eq!(service.head(&stream)?.generation(), 1);
    Ok(())
}

#[test]
fn limits_and_public_debug_are_finite_and_redacted() -> TestResult {
    assert!(matches!(
        IdempotencyService::new(IdempotencyLimits {
            max_records: 0,
            ..IdempotencyLimits::default()
        }),
        Err(IdempotencyError::InvalidLimit)
    ));
    assert_eq!(
        OwnerToken::new([0; 32]),
        Err(IdempotencyError::InvalidOwnerToken)
    );
    assert_eq!(
        RevisionCommit::new(
            revision("revision-mismatched-artifact")?,
            ArtifactId::parse("sha256-deadbeef")?,
            [7; 32],
            7,
            [8; 32],
            IdempotencyLimits::default(),
        ),
        Err(IdempotencyError::InvalidCommit)
    );

    let limits = IdempotencyLimits {
        max_records: 1,
        max_streams: 1,
        max_receipt_bytes: 1,
        max_artifact_bytes: 64,
    };
    let service = IdempotencyService::new(limits)?;
    let storage_boundary: &dyn IdempotencyStore = &service;
    assert_eq!(storage_boundary.record_count()?, 0);
    let secret = "private-document-and-key-sentinel";
    let current_stream = stream(secret)?;
    let revision_one = revision("revision-1")?;
    service.initialize_stream(current_stream.clone(), revision_one.clone())?;
    assert_eq!(
        service.initialize_stream(stream("second-document")?, revision("revision-x")?),
        Err(IdempotencyError::StreamLimitExceeded)
    );
    let binding = binding(secret, current_stream.clone(), revision_one, 1, 1)?;
    let lease = acquired(service.claim(binding.clone(), &owner(1)?)?)?;
    service.start(&lease)?;
    let oversized_receipt_commit = commit("revision-2", 2, limits)?;
    assert_eq!(
        service.commit_success(&lease, &oversized_receipt_commit),
        Err(IdempotencyError::InvalidCommit)
    );
    assert_eq!(service.head(&current_stream)?.generation(), 1);
    assert!(!format!("{service:?} {binding:?} {lease:?}").contains(secret));
    assert!(!format!("{}", IdempotencyError::KeyReuseConflict).contains(secret));
    Ok(())
}

fn acquired(outcome: ClaimOutcome) -> Result<ClaimLease, Box<dyn Error>> {
    let ClaimOutcome::Acquired(lease) = outcome else {
        return Err("expected acquired lease".into());
    };
    Ok(lease)
}

fn binding(
    key: &str,
    stream: RevisionStreamKey,
    expected_revision: RevisionId,
    generation: u64,
    seed: u8,
) -> Result<IdempotencyBinding, IdempotencyError> {
    IdempotencyBinding::new(
        IdempotencyKey::parse(key).map_err(|_| IdempotencyError::InvalidBinding)?,
        [seed; 32],
        [seed.saturating_add(32); 32],
        stream,
        expected_revision,
        generation,
        TransactionId::parse(format!("transaction-{seed}"))
            .map_err(|_| IdempotencyError::InvalidBinding)?,
    )
}

fn commit(
    revision_id: &str,
    seed: u8,
    limits: IdempotencyLimits,
) -> Result<RevisionCommit, IdempotencyError> {
    RevisionCommit::new(
        revision(revision_id).map_err(|_| IdempotencyError::InvalidCommit)?,
        ArtifactId::parse(format!("sha256-{}", hex::encode([seed; 32])))
            .map_err(|_| IdempotencyError::InvalidCommit)?,
        [seed; 32],
        u64::from(seed),
        [seed.saturating_add(64); 32],
        limits,
    )
}

fn owner(seed: u8) -> Result<OwnerToken, IdempotencyError> {
    OwnerToken::new([seed; 32])
}

fn stream(document: &str) -> Result<RevisionStreamKey, Box<dyn Error>> {
    Ok(RevisionStreamKey::new(
        ProjectId::parse("project-main")?,
        DocumentId::parse(document)?,
    ))
}

fn revision(value: &str) -> Result<RevisionId, Box<dyn Error>> {
    Ok(RevisionId::parse(value)?)
}
