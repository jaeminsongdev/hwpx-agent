use super::*;

#[test]
fn unknown_commit_preserves_file_and_byte_output_without_quarantine_or_rollback() -> TestResult {
    for bytes in [false, true] {
        let root = tempfile::tempdir()?;
        let source = write_source(root.path(), SOURCE)?;
        let workspace = root.path().join("workspace");
        let mut tx = WorkspaceTransaction::create(&workspace, fixture_manifest("unknown-cas", SOURCE)?, Default::default())?;
        let calls = Cell::new(0);
        let mut validator = |_: &[u8]| ValidationOutcome::Valid;
        let mut cas = |request: &RevisionCommitRequest| {
            calls.set(calls.get() + 1);
            assert_eq!(request.source_artifact_id().as_str(), "source-artifact");
            assert_ne!(request.manifest_sha256(), [0; 32]);
            RevisionCasOutcome::Unknown
        };
        let failure = if bytes { tx.execute_bytes(SOURCE, OUTPUT, &mut validator, &mut cas, &mut FaultPlan::none()) }
            else { tx.execute(&source, OUTPUT, &mut validator, &mut cas, &mut FaultPlan::none()) }.expect_err("unknown outcome");
        assert_eq!(failure.primary(), TransactionError::RevisionOutcomeUnknown);
        assert_eq!(failure.primary().code(), "workspace_transaction_revision_outcome_unknown");
        assert_eq!(failure.receipt().state(), TransactionState::Incomplete);
        assert_eq!(failure.receipt().artifact_disposition(), ArtifactDisposition::CommittedOutcomeUncertain);
        assert!(failure.receipt().source_unchanged());
        assert!(failure.recovery().is_none());
        assert_eq!(calls.get(), 1);
        assert_eq!(read_only_file(&workspace.join("output"))?, OUTPUT);
        assert_eq!(file_count(&workspace.join("quarantine"))?, 0);
        assert_eq!(fs::read(&source)?, SOURCE);
    }
    Ok(())
}

#[test]
fn unknown_commit_does_not_invoke_recovery_even_when_recovery_fault_is_armed() -> TestResult {
    for step in [TransactionStep::Rollback, TransactionStep::Quarantine] {
        let root = tempfile::tempdir()?;
        let workspace = root.path().join("workspace");
        let mut tx = WorkspaceTransaction::create(&workspace, fixture_manifest("unknown-recovery", SOURCE)?, Default::default())?;
        let mut validator = |_: &[u8]| ValidationOutcome::Valid;
        let mut cas = |_: &RevisionCommitRequest| RevisionCasOutcome::Unknown;
        let failure = tx.execute_bytes(SOURCE, OUTPUT, &mut validator, &mut cas,
            &mut FaultPlan::at(FaultPoint::new(step, FaultMoment::Before))).expect_err("unknown");
        assert_eq!(failure.primary(), TransactionError::RevisionOutcomeUnknown);
        assert!(failure.recovery().is_none());
        assert_eq!(read_only_file(&workspace.join("output"))?, OUTPUT);
    }
    Ok(())
}

#[test]
fn unknown_transaction_cannot_be_reexecuted_and_receipt_does_not_disclose_plaintext() -> TestResult {
    let root = tempfile::tempdir()?;
    let mut tx = WorkspaceTransaction::create(root.path().join("workspace"), fixture_manifest("unknown-single-use", SOURCE)?, Default::default())?;
    let calls = Cell::new(0);
    let mut validator = |_: &[u8]| ValidationOutcome::Valid;
    let mut cas = |_: &RevisionCommitRequest| { calls.set(calls.get() + 1); RevisionCasOutcome::Unknown };
    let first = tx.execute_bytes(SOURCE, OUTPUT, &mut validator, &mut cas, &mut FaultPlan::none()).expect_err("unknown");
    let second = tx.execute_bytes(SOURCE, OUTPUT, &mut validator, &mut cas, &mut FaultPlan::none()).expect_err("no retry");
    assert_eq!(second.primary(), TransactionError::InvalidState);
    assert_eq!(second.receipt().state(), TransactionState::Incomplete);
    assert_eq!(second.receipt().artifact_disposition(), ArtifactDisposition::CommittedOutcomeUncertain);
    assert_eq!(calls.get(), 1);
    assert_eq!(first.receipt().canonical_json()?, second.receipt().canonical_json()?);
    let rendered = format!("{first:?}{second:?}{}", String::from_utf8(first.receipt().canonical_json()?)?);
    assert!(!rendered.contains(std::str::from_utf8(SOURCE)?));
    assert!(!rendered.contains(root.path().to_string_lossy().as_ref()));
    Ok(())
}
