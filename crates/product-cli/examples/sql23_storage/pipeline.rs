use super::*;
fn prepared<'a>(m:&'a ExecutionManifest)->Result<PreparedStoredJob<'a>>{Ok(PreparedStoredJob::prepare(StoredCommitBinding{
    manifest:m,output:OUTPUT,project:project()?,branch:branch()?,expected_head:RevisionHead::new(Some(revision(20)?),1)?,
    commit:commit(201)?,new_revision:revision(200)?,validation_summary:ContentDigest::of(b"synthetic-validator-not-P09")},StoredJobOptions{
    key:id(101),job:id(102),request:id(103),request_sha:ContentDigest::of(b"canonical-storage-request"),capability_sha:ContentDigest::of(b"storage-capability"),
    max_attempts:3,base_delay_seconds:1,max_delay_seconds:4,ttl_seconds:600},Default::default())?)}
fn manifest(s:&Value)->Result<ExecutionManifest>{manifest_fixture::manifest(&StoredFixture{head:RevisionHead::new(Some(revision(20)?),1)?,result:read_id(s,"source")?},"sql23-storage-transaction")}
fn retained_path()->Result<PathBuf>{Ok(owned_root()?.join("completed-handles.json"))}
fn completed()->Result<Value>{let path=retained_path()?;let m=fs::symlink_metadata(&path)?;check(m.is_file()&&!m.file_type().is_symlink()&&m.len()<=16384,"STORAGE_COMPLETED_BOUND")?;
    Ok(serde_json::from_slice(&fs::read(path)?)?)}
pub fn execute()->Result<Value>{let s=state()?;let a=artifacts()?;let ctx=actor()?;let rc=context()?;let revisions=RevisionService::new(repository()?);
    let m=manifest(&s)?;let prepared=prepared(&m)?;
    let mut c=raw("p09_revision_284",&value("P09_SQL23_REVISION_PASSWORD")?)?;scoped(&mut c)?;setup::register(&mut c,130,prepared.claim().input().capability_sha)?;
    let report=prepared.run_once(&a,&revisions,&ctx,&rc,id(130),id(120),120,ContentDigest::of(b"storage-event"),&owned_root()?.join("workspace"),SOURCE,
        &mut |bytes:&[u8]|if bytes==OUTPUT{ValidationOutcome::Valid}else{ValidationOutcome::Rejected},||10);
    // Preserve structured closed failure observations without backend values or credentials.
    if report.stage!=StoredJobRunStage::Completed{return Ok(json!({"state":"FAILED_ACTUAL_STORAGE_COORDINATOR","stage":format!("{:?}",report.stage),
        "repository_error":report.repository_error.as_ref().map(revision_service::RevisionError::code),"binding_error":report.binding_error.map(|e|format!("{e:?}")),
        "workspace_error":report.workspace_error.map(|e|format!("{e:?}")),"cas_error":report.cas_error.map(|e|format!("{e:?}")),
        "result_retained":report.result.is_some(),"intent_retained":report.intent.is_some(),"precommit_retained":report.precommit.is_some(),"registration_retained":report.registered_intent.is_some()}));}
    check(report.transaction.as_ref().ok_or("STORAGE_NO_TRANSACTION")?.as_ref().map(|r|r.state()).ok()==Some(TransactionState::Completed)
        &&report.repository_error.is_none()&&report.cas_error.is_none(),"STORAGE_COMPLETED_REPORT")?;
    let result=report.result.as_ref().ok_or("STORAGE_NO_RESULT")?;let intent=report.intent.as_ref().ok_or("STORAGE_NO_INTENT")?;let precommit=report.precommit.as_ref().ok_or("STORAGE_NO_PRECOMMIT")?;
    let request=report.request.as_ref().ok_or("STORAGE_NO_REQUEST")?;let registered=report.registered_intent.as_ref().ok_or("STORAGE_NO_REGISTERED_INTENT")?;
    check(request.transaction_receipt_sha256()==precommit.sha256&&precommit.sha256!=intent.sha256
        &&registered.intent_artifact_id()==intent.artifact_id&&registered.precommit_artifact_id()==precommit.artifact_id,"STORAGE_DISTINCT_RECEIPT_BINDINGS")?;
    check(a.download(&ctx,result.artifact_id,11)?==OUTPUT&&a.download(&ctx,read_id(&s,"source")?,11)?==SOURCE,"STORAGE_FINAL_AND_SOURCE_READBACK")?;
    let precommit_bytes=a.download(&ctx,precommit.artifact_id,11)?;let intent_bytes=a.download(&ctx,intent.artifact_id,11)?;
    check(ContentDigest::of(&precommit_bytes)==precommit.sha256&&ContentDigest::of(&intent_bytes)==intent.sha256,"STORAGE_RECEIPTS_AEAD_READBACK")?;
    let from_db=revisions.repository().read_commit_intent(&rc,StoredCommitIntentLookup::new(project()?,id(101),id(102),1)?)?.ok_or("STORAGE_NO_DB_INTENT")?;
    check(from_db==*registered&&revisions.head(&rc,project()?,branch()?)?==RevisionHead::new(Some(revision(200)?),2)?,"STORAGE_REGISTERED_ROW_AND_HEAD")?;
    check(report.completion.as_ref().ok_or("STORAGE_NO_COMPLETION")?.receipt_artifact_id()==Some(precommit.artifact_id),"STORAGE_COMPLETION_USES_PRECOMMIT")?;
    let retained=json!({"schema":"p09.storage-completed-handles/v1","result":result.artifact_id.public_id(),"intent":intent.artifact_id.public_id(),
        "precommit":precommit.artifact_id.public_id(),"intent_sha":intent.sha256.hex(),"request":request});
    {use std::io::Write;let bytes=serde_json::to_vec(&retained)?;check(bytes.len()<=16384,"STORAGE_COMPLETED_BOUND")?;
        let mut f=fs::OpenOptions::new().write(true).create_new(true).open(retained_path()?)?;f.write_all(&bytes)?;f.sync_all()?;}
    Ok(json!({"state":"PASS_REAL_AEAD_SQL23_REGISTERED_CAS_AND_COMPLETION_NOT_P09_ROUTE", "registered_intent":true,"success_completion":true,
        "three_receipts_and_source_readback":true,"actual_product_execution":false,"synthetic_route_scanner_validator_and_bytes":true}))}
pub fn restart()->Result<Value>{let s=state()?;let h=completed()?;let a=artifacts()?;let ctx=actor()?;let rc=context()?;let revisions=RevisionService::new(repository()?);let m=manifest(&s)?;
    check(a.download(&ctx,read_id(&h,"result")?,20)?==OUTPUT&&a.download(&ctx,read_id(&s,"source")?,20)?==SOURCE,"STORAGE_RESTART_AEAD_READBACK")?;
    let precommit=a.download(&ctx,read_id(&h,"precommit")?,20)?;let intent_sha=ContentDigest::parse(h["intent_sha"].as_str().ok_or("STORAGE_INTENT_SHA")?)?;
    let request:RevisionCommitRequest=serde_json::from_value(h["request"].clone())?;
    check(ContentDigest::of(&precommit)==request.transaction_receipt_sha256(),"STORAGE_RESTART_PRECOMMIT")?;
    let row=revisions.repository().read_commit_intent(&rc,StoredCommitIntentLookup::new(project()?,id(101),id(102),1)?)?.ok_or("STORAGE_RESTART_INTENT")?;
    check(row.intent_artifact_id()==read_id(&h,"intent")?&&row.precommit_artifact_id()==read_id(&h,"precommit")?&&row.request_sha256()==request.canonical_sha256()?,"STORAGE_RESTART_DB_INTENT_BINDING")?;
    let binding=StoredCommitRecoveryBinding{intent:read_id(&h,"intent")?,intent_sha256:intent_sha,manifest:&m,request:&request,result_sha256:ContentDigest::of(OUTPUT),result_size:OUTPUT.len()as u64};
    check(matches!(reconcile_stored_commit(&a,&revisions,&ctx,&rc,&binding,||20)?,StoredCommitRecoveryOutcome::Committed{result:RecoveredResult::VerifiedAvailable(_),..}),"STORAGE_RESTART_READONLY_RECONCILIATION")?;
    let observed=revisions.repository().claim_job(&rc,prepared(&m)?.claim(),ContentDigest::of(b"read-only-restart-replay"))?;
    check(observed.outcome()==StoredJobOutcome::Replay&&observed.state()==StoredJobState::TerminalSuccess&&observed.attempt_no()==1
        &&observed.result_revision_id()==Some(revision(200)?)&&observed.receipt_artifact_id()==Some(read_id(&h,"precommit")?),"STORAGE_RESTART_SUCCESS_REPLAY")?;
    Ok(json!({"state":"PASS_RESTART_REAL_AEAD_REGISTERED_INTENT_AND_COMMITTED_RECOVERY_NO_REEXECUTION", "execution_retried":false,"parent_retained_ephemeral_test_keys":true}))}
pub fn wrong_key()->Result<Value>{let h=completed()?;let a=artifacts()?;
    check(matches!(a.download(&actor()?,read_id(&h,"result")?,20),Err(ArtifactError::CryptoFailure)),"STORAGE_WRONG_AES_KEY_NOT_REJECTED")?;
    Ok(json!({"state":"PASS_REAL_DISK_AES_GCM_WRONG_KEY_REJECTED","raw_values":false,"actual_product_execution":false}))}
pub fn restart_registered()->Result<Value>{
    let original=retained_path()?;let preserved=owned_root()?.join("completed-handles.preserved.json");
    let metadata=fs::symlink_metadata(&original)?;check(metadata.is_file()&&!metadata.file_type().is_symlink()&&metadata.len()<=16384&&!preserved.exists(),"STORAGE_PRESERVE_REQUEST_FIXTURE_BOUND")?;
    // Keep the original fixture recoverable, but make its normal request path unavailable.
    fs::rename(&original,&preserved)?;check(!original.exists()&&preserved.is_file(),"STORAGE_REQUEST_FIXTURE_NOT_REMOVED_FROM_RECOVERY_PATH")?;
    let s=state()?;let a=artifacts()?;let ctx=actor()?;let rc=context()?;let revisions=RevisionService::new(repository()?);let m=manifest(&s)?;
    let lookup=StoredCommitIntentLookup::new(project()?,id(101),id(102),1)?;
    let recovered=reconcile_registered_stored_commit(&a,&revisions,&ctx,&rc,lookup,&m,||20)?;
    match recovered{RegisteredStoredCommitRecoveryOutcome::Registered(StoredCommitRecoveryOutcome::Committed{receipt,result:RecoveredResult::VerifiedAvailable(result)})=>{
        check(receipt.committed_head()==RevisionHead::new(Some(revision(200)?),2)?&&a.download(&ctx,result.artifact_id,20)?==OUTPUT,"STORAGE_REGISTERED_RECOVERY_EXACT_RESULT")?;
    },_=>return Err("STORAGE_REGISTERED_RECOVERY_NOT_COMMITTED".into())}
    let missing=StoredCommitIntentLookup::new(project()?,id(101),id(9909),1)?;
    check(reconcile_registered_stored_commit(&a,&revisions,&ctx,&rc,missing,&m,||20)?==RegisteredStoredCommitRecoveryOutcome::RegistrationNotObserved,"STORAGE_REGISTERED_RECOVERY_MISSING_NOT_DISTINCT")?;
    let drifted=manifest_fixture::manifest(&StoredFixture{head:RevisionHead::new(Some(revision(20)?),1)?,result:read_id(&s,"source")?},"wrong-recovery-manifest")?;
    check(matches!(reconcile_registered_stored_commit(&a,&revisions,&ctx,&rc,lookup,&drifted,||20),Err(StoredCommitError::Binding)),"STORAGE_REGISTERED_RECOVERY_MANIFEST_NOT_DENIED")?;
    check(!original.exists()&&preserved.is_file(),"STORAGE_REGISTERED_RECOVERY_DID_NOT_RECREATE_REQUEST")?;
    Ok(json!({"state":"PASS_REAL_REGISTERED_RECOVERY_WITHOUT_SAVED_REQUEST_NO_DOMAIN_MUTATIONS","registered_recovery_checks":3,
        "request_fixture_preserved":true,"retained_request_file_used":false,"execution_retried":false,"actual_product_execution":false}))
}
