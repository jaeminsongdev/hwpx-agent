use super::*;

#[derive(serde::Serialize)]
struct IndependentPrecommit<'a>{transaction_id:&'a TransactionId,base_revision:&'a RevisionId,source_artifact_id:&'a ArtifactId,
    result_artifact_id:ArtifactId,manifest_sha256:[u8;32],result_sha256:[u8;32],result_size:u64}

#[test]
fn pure_expected_identity_matches_executed_request_and_independent_original_json()->TestResult{
    let root=tempfile::tempdir()?;let manifest=fixture_manifest("planned-real-callback",SOURCE)?;
    let planned:operation_engine::PreparedPrecommitIdentity=manifest.prepare_precommit(OUTPUT,Default::default())?;
    assert_eq!(fs::read_dir(root.path())?.count(),0);
    let digest:[u8;32]=Sha256::digest(OUTPUT).into();
    let independent=serde_json::to_vec(&IndependentPrecommit{transaction_id:manifest.transaction_id(),base_revision:manifest.base_revision(),
        source_artifact_id:manifest.source_artifact_id(),result_artifact_id:ArtifactId::parse(format!("sha256-{}",hex::encode(digest)))?,
        manifest_sha256:manifest.canonical_sha256()?,result_sha256:digest,result_size:OUTPUT.len()as u64})?;
    assert_eq!(planned.expected_result_sha256(),digest);assert_eq!(planned.expected_result_size(),OUTPUT.len()as u64);
    assert_eq!(planned.expected_precommit_sha256()?,<[u8;32]>::from(Sha256::digest(&independent)));
    let mut tx=WorkspaceTransaction::create(root.path().join("workspace"),manifest,Default::default())?;
    let called=Cell::new(0);let mut cas=|actual:&RevisionCommitRequest|{
        called.set(called.get()+1);assert!(planned.matches_executed(actual));
        assert_eq!(actual.canonical_json().unwrap_or_else(|_|panic!("synthetic receipt serialization")),independent);
        assert_eq!(actual.canonical_sha256().unwrap_or_else(|_|panic!("synthetic receipt digest")),planned.expected_precommit_sha256().unwrap_or_else(|_|panic!("synthetic expected digest")));
        RevisionCasOutcome::Committed};
    tx.execute_bytes(SOURCE,OUTPUT,&mut|_:&[u8]|ValidationOutcome::Valid,&mut cas,&mut FaultPlan::none())?;
    assert_eq!(called.get(),1);Ok(())
}

#[test]
fn actual_file_and_byte_callbacks_share_one_prepared_identity()->TestResult{
    let manifest=fixture_manifest("planned-file-bytes",SOURCE)?;let planned=manifest.prepare_precommit(OUTPUT,Default::default())?;
    let mut receipts=Vec::new();
    for bytes in[false,true]{let root=tempfile::tempdir()?;let source=write_source(root.path(),SOURCE)?;
        let mut tx=WorkspaceTransaction::create(root.path().join("workspace"),manifest.clone(),Default::default())?;
        let mut validator=|_:&[u8]|ValidationOutcome::Valid;let mut cas=|actual:&RevisionCommitRequest|{assert!(planned.matches_executed(actual));RevisionCasOutcome::Committed};
        let receipt=if bytes{tx.execute_bytes(SOURCE,OUTPUT,&mut validator,&mut cas,&mut FaultPlan::none())?}else{tx.execute(&source,OUTPUT,&mut validator,&mut cas,&mut FaultPlan::none())?};
        receipts.push(receipt.canonical_json()?);assert_eq!(fs::read(source)?,SOURCE);
    }assert_eq!(receipts[0],receipts[1]);Ok(())
}

#[test]
fn different_manifest_identity_cannot_match_the_prepared_request()->TestResult{
    let original=fixture_manifest("planned-original",SOURCE)?;let other=fixture_manifest("planned-other",SOURCE)?;
    let planned=original.prepare_precommit(OUTPUT,Default::default())?;let foreign=other.prepare_precommit(OUTPUT,Default::default())?;
    assert_ne!(planned.expected_precommit_sha256()?,foreign.expected_precommit_sha256()?);
    let root=tempfile::tempdir()?;let mut tx=WorkspaceTransaction::create(root.path().join("workspace"),other,Default::default())?;
    let mut cas=|actual:&RevisionCommitRequest|{assert!(!planned.matches_executed(actual));RevisionCasOutcome::Failed};
    let failure=tx.execute_bytes(SOURCE,OUTPUT,&mut|_:&[u8]|ValidationOutcome::Valid,&mut cas,&mut FaultPlan::none()).expect_err("foreign expected request");
    assert_eq!(failure.primary(),TransactionError::RevisionCasFailed);assert_eq!(failure.receipt().state(),TransactionState::Quarantined);Ok(())
}

#[test]
fn same_size_changed_result_is_rejected_by_expected_identity_before_repository_commit()->TestResult{
    let manifest=fixture_manifest("planned-output-drift",SOURCE)?;let planned=manifest.prepare_precommit(OUTPUT,Default::default())?;
    let changed=vec![b'X';OUTPUT.len()];let root=tempfile::tempdir()?;let mut tx=WorkspaceTransaction::create(root.path().join("workspace"),manifest,Default::default())?;
    let mut cas=|actual:&RevisionCommitRequest|{assert!(!planned.matches_executed(actual));assert_eq!(actual.result_size(),planned.expected_result_size());RevisionCasOutcome::Failed};
    let failure=tx.execute_bytes(SOURCE,&changed,&mut|_:&[u8]|ValidationOutcome::Valid,&mut cas,&mut FaultPlan::none()).expect_err("changed output");
    assert_eq!(failure.primary(),TransactionError::RevisionCasFailed);Ok(())
}

#[test]
fn planning_applies_finite_source_manifest_output_and_invalid_limit_bounds()->TestResult{
    let manifest=fixture_manifest("planned-limits",SOURCE)?;
    for mode in 0..4{let mut limits=TransactionLimits::default();match mode{0=>limits.max_source_bytes=0,1=>limits.max_output_bytes=0,2=>limits.max_manifest_bytes=0,_=>limits.max_source_bytes=u64::MAX};
        assert_eq!(manifest.prepare_precommit(OUTPUT,limits).expect_err("invalid limits"),TransactionError::InvalidLimit);}
    let mut limits=TransactionLimits::default();limits.max_source_bytes=SOURCE.len()as u64-1;
    assert_eq!(manifest.prepare_precommit(OUTPUT,limits).expect_err("source cap"),TransactionError::LimitExceeded);
    let mut limits=TransactionLimits::default();limits.max_manifest_bytes=1;
    assert_eq!(manifest.prepare_precommit(OUTPUT,limits).expect_err("manifest cap"),TransactionError::LimitExceeded);
    let mut limits=TransactionLimits::default();limits.max_output_bytes=1;
    assert_eq!(manifest.prepare_precommit(OUTPUT,limits).expect_err("output cap"),TransactionError::InvalidOutput);
    assert_eq!(manifest.prepare_precommit(b"",Default::default()).expect_err("empty"),TransactionError::InvalidOutput);Ok(())
}

#[test]
fn preparation_is_not_validator_success_or_artifact_publication()->TestResult{
    let manifest=fixture_manifest("planned-no-validation",SOURCE)?;let planned=manifest.prepare_precommit(OUTPUT,Default::default())?;
    assert_ne!(planned.expected_precommit_sha256()?,[0;32]);let root=tempfile::tempdir()?;let workspace=root.path().join("workspace");
    let mut tx=WorkspaceTransaction::create(&workspace,manifest,Default::default())?;let called=Cell::new(false);
    let mut cas=|_:&RevisionCommitRequest|{called.set(true);RevisionCasOutcome::Committed};
    let failure=tx.execute_bytes(SOURCE,OUTPUT,&mut|_:&[u8]|ValidationOutcome::Rejected,&mut cas,&mut FaultPlan::none()).expect_err("validator rejected");
    assert_eq!(failure.receipt().state(),TransactionState::RolledBack);assert!(!called.get());assert_eq!(file_count(&workspace.join("output"))?,0);Ok(())
}

#[test]
fn preparation_does_not_admit_a_different_live_source()->TestResult{
    let manifest=fixture_manifest("planned-no-live-source",SOURCE)?;let _planned=manifest.prepare_precommit(OUTPUT,Default::default())?;
    let root=tempfile::tempdir()?;let mut tx=WorkspaceTransaction::create(root.path().join("workspace"),manifest,Default::default())?;
    let validated=Cell::new(false);let committed=Cell::new(false);let wrong=vec![b'X';SOURCE.len()];
    let mut validator=|_:&[u8]|{validated.set(true);ValidationOutcome::Valid};let mut cas=|_:&RevisionCommitRequest|{committed.set(true);RevisionCasOutcome::Committed};
    let failure=tx.execute_bytes(&wrong,OUTPUT,&mut validator,&mut cas,&mut FaultPlan::none()).expect_err("source mismatch");
    assert_eq!(failure.primary(),TransactionError::SourceIdentityMismatch);assert!(!validated.get());assert!(!committed.get());Ok(())
}

#[test]
fn prepared_identity_is_immutable_when_borrowed_candidate_bytes_change()->TestResult{
    let manifest=fixture_manifest("planned-candidate-borrow",SOURCE)?;let mut candidate=OUTPUT.to_vec();
    let planned=manifest.prepare_precommit(&candidate,Default::default())?;let old=planned.expected_precommit_sha256()?;
    candidate.push(b'X');let changed=manifest.prepare_precommit(&candidate,Default::default())?;
    assert_eq!(planned.expected_precommit_sha256()?,old);assert_eq!(planned.expected_result_size(),OUTPUT.len()as u64);
    assert_ne!(changed.expected_precommit_sha256()?,old);Ok(())
}

#[test]
fn prepared_identity_debug_does_not_disclose_source_output_or_private_identifiers()->TestResult{
    let manifest=fixture_manifest("private-planning-transaction",SOURCE)?;let planned=manifest.prepare_precommit(OUTPUT,Default::default())?;
    let debug=format!("{planned:?}");for value in["private-planning-transaction","source-artifact",std::str::from_utf8(SOURCE)?,std::str::from_utf8(OUTPUT)?]{assert!(!debug.contains(value));}
    assert_eq!(planned,planned.clone());Ok(())
}
