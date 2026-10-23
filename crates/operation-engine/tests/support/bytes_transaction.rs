//! Real isolated filesystem staging/publication with synthetic manifest/validator/CAS, not P09 authority.
use super::*;

#[test]
fn bytes_source_matches_file_receipt_without_external_plaintext_source_and_calls_cas_once()->TestResult{
    let root=tempfile::tempdir()?;let source=SOURCE.to_vec();let original=source.clone();let manifest=fixture_manifest("tx-byte-equivalence",SOURCE)?;
    let byte_workspace=root.path().join("bytes-workspace");let mut bytes=WorkspaceTransaction::create(&byte_workspace,manifest.clone(),Default::default())?;
    let validated=Cell::new(0);let committed=Cell::new(0);
    let mut validator=|data:&[u8]|{validated.set(validated.get()+1);assert_eq!(data,OUTPUT);ValidationOutcome::Valid};
    let mut cas=|request:&RevisionCommitRequest|{committed.set(committed.get()+1);assert_eq!(request.transaction_id(),manifest.transaction_id());
        assert_eq!(request.base_revision(),manifest.base_revision());assert_eq!(request.result_sha256(),<[u8;32]>::from(Sha256::digest(OUTPUT)));
        assert_eq!(request.result_size(),OUTPUT.len()as u64);RevisionCasOutcome::Committed};
    let receipt=bytes.execute_bytes(&source,OUTPUT,&mut validator,&mut cas,&mut FaultPlan::none())?;
    assert_eq!((validated.get(),committed.get()),(1,1));assert_eq!(source,original);assert!(receipt.source_unchanged());assert!(!root.path().join("source.hwpx").exists());
    assert_eq!(file_count(&byte_workspace.join("staging"))?,0);assert_eq!(read_only_file(&byte_workspace.join("output"))?,OUTPUT);
    let path=write_source(root.path(),SOURCE)?;let mut file=WorkspaceTransaction::create(root.path().join("file-workspace"),manifest,Default::default())?;
    let other=execute_valid(&mut file,&path,OUTPUT,RevisionCasOutcome::Committed)?;assert_eq!(receipt.canonical_json()?,other.canonical_json()?);Ok(())
}
#[test]
fn bytes_wrong_sha_size_and_empty_source_fail_before_staging_validator_or_cas()->TestResult{
    for source in[vec![b'X';SOURCE.len()],SOURCE[..SOURCE.len()-1].to_vec(),vec![]]{let root=tempfile::tempdir()?;let workspace=root.path().join("workspace");
        let mut tx=WorkspaceTransaction::create(&workspace,fixture_manifest("tx-byte-identity",SOURCE)?,Default::default())?;
        let validator_called=Cell::new(false);let cas_called=Cell::new(false);let mut validator=|_:&[u8]|{validator_called.set(true);ValidationOutcome::Valid};
        let mut cas=|_:&RevisionCommitRequest|{cas_called.set(true);RevisionCasOutcome::Committed};
        let e=tx.execute_bytes(&source,OUTPUT,&mut validator,&mut cas,&mut FaultPlan::none()).expect_err("identity");
        assert_eq!(e.primary(),TransactionError::SourceIdentityMismatch);assert_eq!(e.receipt().state(),TransactionState::RolledBack);
        assert!(!validator_called.get()&&!cas_called.get());assert_eq!(file_count(&workspace.join("staging"))?,0);assert_eq!(file_count(&workspace.join("output"))?,0);
    }Ok(())
}
#[test]
fn bytes_limits_and_invalid_output_do_not_widen_source_or_publish_partial_bytes()->TestResult{
    for output in[vec![],vec![b'x';2]]{let root=tempfile::tempdir()?;let workspace=root.path().join("workspace");
        let mut tx=WorkspaceTransaction::create(&workspace,fixture_manifest("tx-byte-output-limit",SOURCE)?,TransactionLimits{max_output_bytes:1,..Default::default()})?;
        let called=Cell::new(false);let mut validator=|_:&[u8]|{called.set(true);ValidationOutcome::Valid};let mut cas=|_:&RevisionCommitRequest|{called.set(true);RevisionCasOutcome::Committed};
        let e=tx.execute_bytes(SOURCE,&output,&mut validator,&mut cas,&mut FaultPlan::none()).expect_err("output limit");assert_eq!(e.primary(),TransactionError::InvalidOutput);assert!(!called.get());assert_eq!(file_count(&workspace.join("output"))?,0);
    }
    let root=tempfile::tempdir()?;let workspace=root.path().join("source-limit");let mut tx=WorkspaceTransaction::create(&workspace,fixture_manifest("tx-byte-source-limit",SOURCE)?,
        TransactionLimits{max_source_bytes:SOURCE.len()as u64,..Default::default()})?;
    let mut input=SOURCE.to_vec();input.push(0);let mut validator=|_:&[u8]|ValidationOutcome::Valid;let mut cas=|_:&RevisionCommitRequest|RevisionCasOutcome::Committed;
    let e=tx.execute_bytes(&input,OUTPUT,&mut validator,&mut cas,&mut FaultPlan::none()).expect_err("source limit");assert_eq!(e.primary(),TransactionError::SourceIdentityMismatch);assert_eq!(file_count(&workspace.join("staging"))?,0);Ok(())
}
#[test]
fn bytes_validator_rejected_and_failed_roll_back_without_cas()->TestResult{
    for(outcome,expected)in[(ValidationOutcome::Rejected,TransactionError::ValidationRejected),(ValidationOutcome::Failed,TransactionError::ValidationFailed)]{
        let root=tempfile::tempdir()?;let workspace=root.path().join("workspace");let mut tx=WorkspaceTransaction::create(&workspace,fixture_manifest("tx-byte-validator",SOURCE)?,Default::default())?;
        let called=Cell::new(false);let mut validator=|_:&[u8]|outcome;let mut cas=|_:&RevisionCommitRequest|{called.set(true);RevisionCasOutcome::Committed};
        let e=tx.execute_bytes(SOURCE,OUTPUT,&mut validator,&mut cas,&mut FaultPlan::none()).expect_err("validator");assert_eq!(e.primary(),expected);assert_eq!(e.receipt().state(),TransactionState::RolledBack);
        assert!(e.receipt().source_unchanged());assert!(!called.get());assert_eq!(file_count(&workspace.join("staging"))?,0);assert_eq!(file_count(&workspace.join("output"))?,0);
    }Ok(())
}
#[test]
fn bytes_cas_conflict_and_failure_quarantine_complete_output()->TestResult{
    for(outcome,expected)in[(RevisionCasOutcome::Conflict,TransactionError::RevisionConflict),(RevisionCasOutcome::Failed,TransactionError::RevisionCasFailed)]{
        let root=tempfile::tempdir()?;let workspace=root.path().join("workspace");let mut tx=WorkspaceTransaction::create(&workspace,fixture_manifest("tx-byte-cas",SOURCE)?,Default::default())?;
        let mut validator=|_:&[u8]|ValidationOutcome::Valid;let mut cas=|_:&RevisionCommitRequest|outcome;
        let e=tx.execute_bytes(SOURCE,OUTPUT,&mut validator,&mut cas,&mut FaultPlan::none()).expect_err("cas");assert_eq!(e.primary(),expected);assert_eq!(e.receipt().state(),TransactionState::Quarantined);
        assert!(e.receipt().source_unchanged());assert_eq!(file_count(&workspace.join("output"))?,0);assert_eq!(read_only_file(&workspace.join("quarantine"))?,OUTPUT);
    }Ok(())
}
#[test]
fn bytes_every_normal_transition_fault_is_absent_quarantined_or_completed()->TestResult{
    for step in TransactionStep::NORMAL{for moment in[FaultMoment::Before,FaultMoment::After]{let root=tempfile::tempdir()?;let workspace=root.path().join("workspace");
        let mut tx=WorkspaceTransaction::create(&workspace,fixture_manifest(&format!("tx-byte-{step:?}-{moment:?}"),SOURCE)?,Default::default())?;
        let mut validator=|_:&[u8]|ValidationOutcome::Valid;let mut cas=|_:&RevisionCommitRequest|RevisionCasOutcome::Committed;
        let e=tx.execute_bytes(SOURCE,OUTPUT,&mut validator,&mut cas,&mut FaultPlan::at(FaultPoint::new(step,moment))).expect_err("injected");
        assert_eq!(e.primary(),TransactionError::InjectedFault);assert!(e.receipt().source_unchanged());let public=file_count(&workspace.join("output"))?;
        match e.receipt().state(){TransactionState::RolledBack=>{assert_eq!(public,0);assert_eq!(e.receipt().artifact_disposition(),ArtifactDisposition::Absent);},
            TransactionState::Quarantined=>{assert_eq!(public,0);assert_eq!(read_only_file(&workspace.join("quarantine"))?,OUTPUT);},
            TransactionState::RevisionCasCommitted|TransactionState::Completed=>{assert_eq!(public,1);assert_eq!(read_only_file(&workspace.join("output"))?,OUTPUT);},
            _=>return Err("unexpected byte fault state".into())}
    }}Ok(())
}
#[test]
fn bytes_rollback_and_quarantine_faults_preserve_explicit_recovery_failure()->TestResult{
    for step in[TransactionStep::Rollback,TransactionStep::Quarantine]{for moment in[FaultMoment::Before,FaultMoment::After]{
        let root=tempfile::tempdir()?;let workspace=root.path().join("workspace");let mut tx=WorkspaceTransaction::create(&workspace,fixture_manifest("tx-byte-recovery",SOURCE)?,Default::default())?;
        let rollback=step==TransactionStep::Rollback;let mut validator=|_:&[u8]|if rollback{ValidationOutcome::Rejected}else{ValidationOutcome::Valid};let mut cas=|_:&RevisionCommitRequest|RevisionCasOutcome::Conflict;
        let e=tx.execute_bytes(SOURCE,OUTPUT,&mut validator,&mut cas,&mut FaultPlan::at(FaultPoint::new(step,moment))).expect_err("recovery");
        assert_eq!(e.primary(),if rollback{TransactionError::ValidationRejected}else{TransactionError::RevisionConflict});assert_eq!(e.recovery(),Some(TransactionError::InjectedFault));assert!(e.receipt().source_unchanged());
        let public=file_count(&workspace.join("output"))?;if rollback{assert_eq!(public,0);}else{let quarantined=file_count(&workspace.join("quarantine"))?;assert_eq!(public+quarantined,1);
            assert_eq!(read_only_file(&workspace.join(if public==1{"output"}else{"quarantine"}))?,OUTPUT);}
    }}Ok(())
}
#[test]
fn bytes_and_file_entrypoints_share_single_use_state()->TestResult{
    for byte_first in[false,true]{let root=tempfile::tempdir()?;let source=write_source(root.path(),SOURCE)?;let workspace=root.path().join("workspace");
        let mut tx=WorkspaceTransaction::create(&workspace,fixture_manifest("tx-byte-single-use",SOURCE)?,Default::default())?;
        let mut validator=|_:&[u8]|ValidationOutcome::Valid;let mut cas=|_:&RevisionCommitRequest|RevisionCasOutcome::Committed;
        if byte_first{tx.execute_bytes(SOURCE,OUTPUT,&mut validator,&mut cas,&mut FaultPlan::none())?;}else{tx.execute(&source,OUTPUT,&mut validator,&mut cas,&mut FaultPlan::none())?;}
        let e=if byte_first{tx.execute(&source,OUTPUT,&mut validator,&mut cas,&mut FaultPlan::none())}else{tx.execute_bytes(SOURCE,OUTPUT,&mut validator,&mut cas,&mut FaultPlan::none())}.expect_err("single use");
        assert_eq!(e.primary(),TransactionError::InvalidState);assert_eq!(e.receipt().state(),TransactionState::Completed);assert_eq!(read_only_file(&workspace.join("output"))?,OUTPUT);assert_eq!(fs::read(source)?,SOURCE);
    }Ok(())
}
#[test]
fn bytes_no_overwrite_preserves_existing_result_and_never_calls_second_cas()->TestResult{
    let root=tempfile::tempdir()?;let workspace=root.path().join("workspace");let mut first=WorkspaceTransaction::create(&workspace,fixture_manifest("tx-byte-first",SOURCE)?,Default::default())?;
    let mut validator=|_:&[u8]|ValidationOutcome::Valid;let mut cas=|_:&RevisionCommitRequest|RevisionCasOutcome::Committed;
    first.execute_bytes(SOURCE,OUTPUT,&mut validator,&mut cas,&mut FaultPlan::none())?;
    let mut second=WorkspaceTransaction::create(&workspace,fixture_manifest("tx-byte-second",SOURCE)?,Default::default())?;let called=Cell::new(false);
    let mut second_cas=|_:&RevisionCommitRequest|{called.set(true);RevisionCasOutcome::Committed};
    let e=second.execute_bytes(SOURCE,OUTPUT,&mut validator,&mut second_cas,&mut FaultPlan::none()).expect_err("overwrite");
    assert_eq!(e.primary(),TransactionError::ArtifactExists);assert!(!called.get());assert_eq!(read_only_file(&workspace.join("output"))?,OUTPUT);Ok(())
}
#[test]
fn bytes_input_and_receipts_do_not_disclose_plaintext_or_external_paths()->TestResult{
    let source=b"PRIVATE-SOURCE-DATA";let root=tempfile::tempdir()?;let mut tx=WorkspaceTransaction::create(root.path().join("workspace"),fixture_manifest("private-byte-key",source)?,Default::default())?;
    let mut validator=|_:&[u8]|ValidationOutcome::Valid;let mut cas=|_:&RevisionCommitRequest|RevisionCasOutcome::Committed;
    let receipt=tx.execute_bytes(source,OUTPUT,&mut validator,&mut cas,&mut FaultPlan::none())?;
    for text in[format!("{tx:?}{receipt:?}"),String::from_utf8(receipt.canonical_json()?)?]{assert!(!text.contains("PRIVATE-SOURCE-DATA"));assert!(!text.contains(root.path().to_string_lossy().as_ref()));}
    Ok(())
}
#[test]
fn bytes_validator_cannot_publish_a_tampered_staged_output()->TestResult{
    let root=tempfile::tempdir()?;let workspace=root.path().join("workspace");let mut tx=WorkspaceTransaction::create(&workspace,fixture_manifest("tx-byte-staging-tamper",SOURCE)?,Default::default())?;
    let changed=Cell::new(false);let staging=workspace.join("staging");let mut validator=|_:&[u8]|{
        let mut pending=vec![staging.clone()];while let Some(path)=pending.pop(){if let Ok(entries)=fs::read_dir(path){for entry in entries.flatten(){let path=entry.path();if path.is_dir(){pending.push(path);}else if path.file_name().is_some_and(|n|n=="output.hwpx"){assert!(fs::write(path,b"TAMPERED").is_ok());changed.set(true);}}}}
        ValidationOutcome::Valid};
    let called=Cell::new(false);let mut cas=|_:&RevisionCommitRequest|{called.set(true);RevisionCasOutcome::Committed};
    let _failure=tx.execute_bytes(SOURCE,OUTPUT,&mut validator,&mut cas,&mut FaultPlan::none()).expect_err("staged tamper");
    assert!(changed.get());assert!(!called.get());assert_eq!(file_count(&workspace.join("output"))?,0);Ok(())
}
#[test]
fn bytes_source_does_not_resolve_or_modify_unrelated_external_source_filename()->TestResult{
    let root=tempfile::tempdir()?;let external=root.path().join("source.hwpx");fs::write(&external,b"UNRELATED-PRIVATE-DATA")?;
    let mut tx=WorkspaceTransaction::create(root.path().join("workspace"),fixture_manifest("tx-byte-unrelated",SOURCE)?,Default::default())?;
    let mut validator=|_:&[u8]|ValidationOutcome::Valid;let mut cas=|_:&RevisionCommitRequest|RevisionCasOutcome::Committed;
    tx.execute_bytes(SOURCE,OUTPUT,&mut validator,&mut cas,&mut FaultPlan::none())?;assert_eq!(fs::read(external)?,b"UNRELATED-PRIVATE-DATA");Ok(())
}
#[test]
fn file_validator_same_size_staging_tamper_also_fails_before_publication_or_cas()->TestResult{
    let root=tempfile::tempdir()?;let source=write_source(root.path(),SOURCE)?;let workspace=root.path().join("workspace");
    let mut tx=WorkspaceTransaction::create(&workspace,fixture_manifest("tx-file-staging-tamper",SOURCE)?,Default::default())?;
    let changed=Cell::new(false);let staging=workspace.join("staging");let mut validator=|_:&[u8]|{
        let mut pending=vec![staging.clone()];while let Some(path)=pending.pop(){if let Ok(entries)=fs::read_dir(path){for entry in entries.flatten(){let path=entry.path();if path.is_dir(){pending.push(path);}else if path.file_name().is_some_and(|n|n=="output.hwpx"){assert!(fs::write(path,vec![b'X';OUTPUT.len()]).is_ok());changed.set(true);}}}}
        ValidationOutcome::Valid};
    let called=Cell::new(false);let mut cas=|_:&RevisionCommitRequest|{called.set(true);RevisionCasOutcome::Committed};
    let e=tx.execute(&source,OUTPUT,&mut validator,&mut cas,&mut FaultPlan::none()).expect_err("same-size staged tamper");
    assert!(changed.get());assert_eq!(e.primary(),TransactionError::InvalidOutput);assert_eq!(e.receipt().state(),TransactionState::RolledBack);
    assert!(!called.get());assert_eq!(file_count(&workspace.join("output"))?,0);assert_eq!(fs::read(source)?,SOURCE);Ok(())
}
#[test]
fn bytes_post_cas_tamper_is_incomplete_and_never_reports_a_completed_revision()->TestResult{
    let root=tempfile::tempdir()?;let workspace=root.path().join("workspace");let mut tx=WorkspaceTransaction::create(&workspace,fixture_manifest("tx-byte-post-cas",SOURCE)?,Default::default())?;
    let mut validator=|_:&[u8]|ValidationOutcome::Valid;let called=Cell::new(0);let mut cas=|request:&RevisionCommitRequest|{
        called.set(called.get()+1);let path=workspace.join("output").join("artifacts").join(format!("{}.hwpx",hex::encode(request.result_sha256())));
        assert!(fs::write(path,vec![b'X';OUTPUT.len()]).is_ok());RevisionCasOutcome::Committed};
    let e=tx.execute_bytes(SOURCE,OUTPUT,&mut validator,&mut cas,&mut FaultPlan::none()).expect_err("post-CAS tamper");
    assert_eq!(called.get(),1);assert_eq!(e.primary(),TransactionError::InvalidOutput);assert_eq!(e.receipt().state(),TransactionState::Incomplete);
    assert_eq!(e.receipt().artifact_disposition(),ArtifactDisposition::CommittedOutcomeUncertain);assert!(e.receipt().source_unchanged());
    assert_eq!(file_count(&workspace.join("output"))?,1);assert!(e.recovery().is_none());Ok(())
}
