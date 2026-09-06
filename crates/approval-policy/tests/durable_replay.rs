use std::collections::BTreeSet;
use std::error::Error;
use std::fs;
use std::sync::{Arc, Barrier};
use std::thread;

use approval_policy::{
    ApprovalError, ApprovalEvaluator, ApprovalPolicy, ApprovalScope, ConfirmationAuthority,
    DurableReplayLedger, EffectKind, EffectRequest,
};
use tempfile::tempdir;

type TestResult = Result<(), Box<dyn Error>>;

const SECRET: &[u8] = b"approval-durable-test-secret-key-01";
const NOW: u64 = 2_000_000_000;

fn digest(character: char) -> String {
    character.to_string().repeat(64)
}

fn request(suffix: &str) -> Result<EffectRequest, ApprovalError> {
    EffectRequest::new(
        format!("op_operation{suffix}"),
        digest('a'),
        digest('b'),
        EffectKind::GitCommit,
        digest('c'),
        digest('d'),
        NOW,
    )
}

fn policy(capacity: usize) -> Result<ApprovalPolicy, ApprovalError> {
    ApprovalPolicy::new([EffectKind::GitCommit], 120, capacity)
}

#[test]
fn consumed_confirmation_remains_rejected_after_reopen() -> TestResult {
    let temporary = tempdir()?;
    let first_request = request("0001")?;
    let authority = ConfirmationAuthority::new(SECRET)?;
    let token = authority.mint(
        "cnf_confirm0001".to_owned(),
        &first_request,
        true,
        NOW,
        NOW + 60,
    )?;
    let scopes = BTreeSet::from([ApprovalScope::WorkstationControl]);
    let ledger = DurableReplayLedger::open(temporary.path())?;
    let mut first = ApprovalEvaluator::with_replay_ledger(policy(8)?, SECRET, Box::new(ledger))?;
    first.authorize(&first_request, &scopes, Some(&token), NOW + 1)?;
    drop(first);

    let reopened = DurableReplayLedger::open(temporary.path())?;
    let mut second = ApprovalEvaluator::with_replay_ledger(policy(8)?, SECRET, Box::new(reopened))?;
    assert_eq!(
        second.authorize(&first_request, &scopes, Some(&token), NOW + 2),
        Err(ApprovalError::ConfirmationReplay)
    );
    Ok(())
}

#[test]
fn concurrent_consumers_have_exactly_one_authorized_result() -> TestResult {
    let temporary = tempdir()?;
    let request = request("0001")?;
    let authority = ConfirmationAuthority::new(SECRET)?;
    let token = authority.mint("cnf_confirm0001".to_owned(), &request, true, NOW, NOW + 60)?;
    let barrier = Arc::new(Barrier::new(2));
    let mut handles = Vec::new();
    for _ in 0..2 {
        let ledger = DurableReplayLedger::open(temporary.path())?;
        let request = request.clone();
        let token = token.clone();
        let barrier = Arc::clone(&barrier);
        handles.push(thread::spawn(move || {
            let scopes = BTreeSet::from([ApprovalScope::WorkstationControl]);
            let mut evaluator =
                ApprovalEvaluator::with_replay_ledger(policy(8)?, SECRET, Box::new(ledger))?;
            barrier.wait();
            evaluator
                .authorize(&request, &scopes, Some(&token), NOW + 1)
                .map(|_| ())
        }));
    }
    let results = handles
        .into_iter()
        .map(|handle| handle.join().map_err(|_| "thread panic"))
        .collect::<Result<Vec<_>, _>>()?;
    assert_eq!(results.iter().filter(|result| result.is_ok()).count(), 1);
    assert_eq!(
        results
            .iter()
            .filter(|result| matches!(result, Err(ApprovalError::ConfirmationReplay)))
            .count(),
        1
    );
    Ok(())
}

#[test]
fn durable_ledger_stores_only_token_hash_and_redacts_its_path() -> TestResult {
    let temporary = tempdir()?;
    let root_text = temporary.path().display().to_string();
    let request = request("0001")?;
    let authority = ConfirmationAuthority::new(SECRET)?;
    let token = authority.mint("cnf_confirm0001".to_owned(), &request, true, NOW, NOW + 60)?;
    let ledger = DurableReplayLedger::open(temporary.path())?;
    let debug = format!("{ledger:?}");
    assert!(!debug.contains(&root_text));
    let scopes = BTreeSet::from([ApprovalScope::WorkstationControl]);
    let mut evaluator =
        ApprovalEvaluator::with_replay_ledger(policy(8)?, SECRET, Box::new(ledger))?;
    evaluator.authorize(&request, &scopes, Some(&token), NOW + 1)?;

    let entry = temporary
        .path()
        .join("p17-approval-replay-v1")
        .join("00000000000000000001.json");
    let stored = fs::read_to_string(entry)?;
    assert!(!stored.contains("cnf_confirm0001"));
    assert!(!stored.contains(token.encoded()));
    assert!(!stored.contains("approval-durable-test-secret"));
    assert!(!stored.contains("op_operation0001"));
    Ok(())
}

#[test]
fn tampered_gapped_and_unknown_entries_fail_closed() -> TestResult {
    let temporary = tempdir()?;
    let first_request = request("0001")?;
    let authority = ConfirmationAuthority::new(SECRET)?;
    let token = authority.mint(
        "cnf_confirm0001".to_owned(),
        &first_request,
        true,
        NOW,
        NOW + 60,
    )?;
    let ledger = DurableReplayLedger::open(temporary.path())?;
    let scopes = BTreeSet::from([ApprovalScope::WorkstationControl]);
    let mut evaluator =
        ApprovalEvaluator::with_replay_ledger(policy(8)?, SECRET, Box::new(ledger))?;
    evaluator.authorize(&first_request, &scopes, Some(&token), NOW + 1)?;
    let entries = temporary.path().join("p17-approval-replay-v1");
    fs::write(entries.join("unexpected.txt"), b"x")?;
    assert!(matches!(
        DurableReplayLedger::open(temporary.path()),
        Err(ApprovalError::LedgerCorrupt)
    ));

    let other = tempdir()?;
    let other_entries = other.path().join("p17-approval-replay-v1");
    fs::create_dir(&other_entries)?;
    fs::write(other_entries.join("00000000000000000002.json"), b"{}")?;
    assert!(matches!(
        DurableReplayLedger::open(other.path()),
        Err(ApprovalError::LedgerCorrupt)
    ));

    let tampered = tempdir()?;
    let tampered_request = request("0003")?;
    let tampered_token = authority.mint(
        "cnf_confirm0003".to_owned(),
        &tampered_request,
        true,
        NOW,
        NOW + 60,
    )?;
    let ledger = DurableReplayLedger::open(tampered.path())?;
    let mut evaluator =
        ApprovalEvaluator::with_replay_ledger(policy(8)?, SECRET, Box::new(ledger))?;
    evaluator.authorize(&tampered_request, &scopes, Some(&tampered_token), NOW + 1)?;
    drop(evaluator);
    let entry = tampered
        .path()
        .join("p17-approval-replay-v1")
        .join("00000000000000000001.json");
    let mut value: serde_json::Value = serde_json::from_slice(&fs::read(&entry)?)?;
    value["token_id_sha256"] = serde_json::Value::String(digest('f'));
    fs::write(&entry, serde_json::to_vec(&value)?)?;
    assert!(matches!(
        DurableReplayLedger::open(tampered.path()),
        Err(ApprovalError::LedgerCorrupt)
    ));
    Ok(())
}

#[test]
fn durable_capacity_remains_enforced_after_restart() -> TestResult {
    let temporary = tempdir()?;
    let authority = ConfirmationAuthority::new(SECRET)?;
    let scopes = BTreeSet::from([ApprovalScope::WorkstationControl]);
    let first_request = request("0001")?;
    let first_token = authority.mint(
        "cnf_confirm0001".to_owned(),
        &first_request,
        true,
        NOW,
        NOW + 60,
    )?;
    let ledger = DurableReplayLedger::open(temporary.path())?;
    let mut first = ApprovalEvaluator::with_replay_ledger(policy(1)?, SECRET, Box::new(ledger))?;
    first.authorize(&first_request, &scopes, Some(&first_token), NOW + 1)?;
    drop(first);

    let second_request = request("0002")?;
    let second_token = authority.mint(
        "cnf_confirm0002".to_owned(),
        &second_request,
        true,
        NOW,
        NOW + 60,
    )?;
    let ledger = DurableReplayLedger::open(temporary.path())?;
    let mut second = ApprovalEvaluator::with_replay_ledger(policy(1)?, SECRET, Box::new(ledger))?;
    assert_eq!(
        second.authorize(&second_request, &scopes, Some(&second_token), NOW + 2),
        Err(ApprovalError::CapacityExceeded)
    );
    Ok(())
}
