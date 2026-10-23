use super::*;
fn prepared<'a>(m:&'a ExecutionManifest)->Result<PreparedStoredJob<'a>>{Ok(PreparedStoredJob::prepare(StoredCommitBinding{
    manifest:m,output:OUTPUT,project:project()?,branch:branch()?,expected_head:RevisionHead::new(Some(revision(20)?),1)?,
    commit:commit(201)?,new_revision:revision(200)?,validation_summary:ContentDigest::of(b"synthetic-validator-not-P09")},StoredJobOptions{
    key:id(101),job:id(102),request:id(103),request_sha:ContentDigest::of(b"canonical-storage-request"),capability_sha:ContentDigest::of(b"storage-capability"),
    max_attempts:3,base_delay_seconds:1,max_delay_seconds:4,ttl_seconds:600},Default::default())?)}
fn manifest(s:&Value)->Result<ExecutionManifest>{manifest_fixture::manifest(&StoredFixture{head:RevisionHead::new(Some(revision(20)?),1)?,result:read_id(s,"source")?},"sql23-ack-transaction")}
fn path()->Result<PathBuf>{Ok(owned_root()?.join("ack-loss-handles.json"))}
fn saved()->Result<Value>{let p=path()?;let m=fs::symlink_metadata(&p)?;check(m.is_file()&&!m.file_type().is_symlink()&&m.len()<=16384,"ACK_RETAINED_BOUND")?;Ok(serde_json::from_slice(&fs::read(p)?)?)}
pub fn execute()->Result<Value>{let s=state()?;let a=artifacts()?;let ctx=actor()?;let rc=context()?;let mode=case()?;
    let faulty=fault_repository::AckRepository::new(repository()?,mode.clone());let revisions=RevisionService::new(faulty.clone());
    let m=manifest(&s)?;let prepared=prepared(&m)?;let mut c=raw("p09_revision_284",&value("P09_SQL23_REVISION_PASSWORD")?)?;scoped(&mut c)?;
    setup::register(&mut c,130,prepared.claim().input().capability_sha)?;
    let r=prepared.run_once(&a,&revisions,&ctx,&rc,id(130),id(120),120,ContentDigest::of(b"ack-loss-event"),&owned_root()?.join("workspace"),SOURCE,
        &mut |bytes:&[u8]|if bytes==OUTPUT{ValidationOutcome::Valid}else{ValidationOutcome::Rejected},||10);
    let completion=mode=="complete_after";
    check(r.binding_error.is_none()&&r.workspace_error.is_none()&&r.completion.is_none(),"ACK_NO_FALSE_COMPLETION")?;
    if completion{check(r.stage==StoredJobRunStage::Completion&&r.repository_error==Some(RevisionError::CommitOutcomeUnknown)&&r.cas_error.is_none()
        &&r.unknown.is_none()&&r.transaction.as_ref().ok_or("ACK_NO_TRANSACTION")?.as_ref().map(|v|v.state()).ok()==Some(TransactionState::Completed),"ACK_COMPLETION_BOUNDARY")?;
    }else{let failure=r.transaction.as_ref().ok_or("ACK_NO_TRANSACTION")?.as_ref().err().ok_or("ACK_MISSING_ORIGINAL_FAILURE")?;
        check(r.stage==StoredJobRunStage::UnknownObservation&&r.cas_error==Some(StoredCommitError::Unknown)&&r.repository_error.is_none()&&r.unknown.is_some()
            &&failure.receipt().state()==TransactionState::Incomplete&&failure.receipt().artifact_disposition()==ArtifactDisposition::CommittedOutcomeUncertain,"ACK_UNKNOWN_BOUNDARY")?;}
    let counts=faulty.counts();let expected=json!({"injected":true,"cas_calls":if mode=="register_after"{0}else{1},"register_calls":1,
        "complete_calls":if completion{1}else{0},"unknown_calls":if completion{0}else{1}});
    check(counts==expected,"ACK_EXACT_ONCE_BOUNDARY_CALLS")?;
    let result=r.result.as_ref().ok_or("ACK_NO_RESULT")?;let intent=r.intent.as_ref().ok_or("ACK_NO_INTENT")?;let precommit=r.precommit.as_ref().ok_or("ACK_NO_PRECOMMIT")?;
    let request=r.request.as_ref().ok_or("ACK_NO_REQUEST")?;
    check(request.transaction_receipt_sha256()==precommit.sha256&&intent.sha256!=precommit.sha256&&a.download(&ctx,result.artifact_id,11)?==OUTPUT
        &&a.download(&ctx,read_id(&s,"source")?,11)?==SOURCE&&ContentDigest::of(&a.download(&ctx,precommit.artifact_id,11)?)==precommit.sha256
        &&ContentDigest::of(&a.download(&ctx,intent.artifact_id,11)?)==intent.sha256,"ACK_RETAINED_REAL_AEAD_AND_SEPARATE_RECEIPTS")?;
    check(r.registered_intent.is_some()==(mode!="register_after"),"ACK_REGISTRATION_ACK_NOT_INVENTED")?;
    let h=json!({"case":mode,"result":result.artifact_id.public_id(),"intent":intent.artifact_id.public_id(),"precommit":precommit.artifact_id.public_id(),
        "intent_sha":intent.sha256.hex(),"request":request,"counts":counts});
    {use std::io::Write;let bytes=serde_json::to_vec(&h)?;check(bytes.len()<=16384,"ACK_RETAINED_BOUND")?;
        let mut f=fs::OpenOptions::new().write(true).create_new(true).open(path()?)?;f.write_all(&bytes)?;f.sync_all()?;}
    Ok(json!({"state":"PASS_REAL_DB_EFFECTS_WITH_SYNTHETIC_APPLICATION_ACK_LOSS","case":mode,"counts":counts,
        "original_failure_and_artifacts_retained":true,"actual_network_fault":false,"actual_product_execution":false}))}
fn deny_reconcile(repo:&LocalPostgresStoredRevisionJobsRepository,receipt:ArtifactId)->Result<()>{
    let rc=context()?;let lookup=StoredCommitIntentLookup::new(project()?,id(101),id(102),1)?;
    check(matches!(repo.reconcile_job_committed(&rc,lookup,revision(200)?,receipt,ContentDigest::of(b"denied-reconcile")),Err(RevisionError::RepositoryFailure)),"ACK_ORACLE_NOT_DENIED")?;
    let mut c=raw("p09_revision_284",&value("P09_SQL23_REVISION_PASSWORD")?)?;scoped(&mut c)?;
    let denied=c.query_one("SELECT * FROM hwpx_agent.reconcile_stored_revision_job_v1($1,$2,$3::character(64),$4,$5,'committed',$6,$7,$8::character(64))",
        &[&id(1),&id(2),&subject()?.hex(),&id(101),&id(102),&revision(200)?.as_uuid(),&receipt.as_uuid(),&ContentDigest::of(b"denied-reconcile").hex()]);
    check(denied.as_ref().err().and_then(|e|e.code()).is_some_and(|c|c.code()=="55000"),"ACK_EXACT_ORACLE_SQLSTATE_REQUIRED")}
pub fn recover()->Result<Value>{let s=state()?;let h=saved()?;let mode=case()?;check(h["case"].as_str()==Some(mode.as_str()),"ACK_RETAINED_CASE")?;
    let a=artifacts()?;let ctx=actor()?;let rc=context()?;let revisions=RevisionService::new(repository()?);let m=manifest(&s)?;
    let request:RevisionCommitRequest=serde_json::from_value(h["request"].clone())?;let precommit=read_id(&h,"precommit")?;
    check(a.download(&ctx,read_id(&h,"result")?,20)?==OUTPUT&&a.download(&ctx,read_id(&s,"source")?,20)?==SOURCE
        &&ContentDigest::of(&a.download(&ctx,precommit,20)?)==request.transaction_receipt_sha256(),"ACK_RESTART_AEAD_READBACK")?;
    let row=revisions.repository().read_commit_intent(&rc,StoredCommitIntentLookup::new(project()?,id(101),id(102),1)?)?.ok_or("ACK_RESTART_REGISTERED_INTENT")?;
    check(row.intent_artifact_id()==read_id(&h,"intent")?&&row.precommit_artifact_id()==precommit&&row.request_sha256()==request.canonical_sha256()?,"ACK_RESTART_ACTUAL_REGISTERED_ROW")?;
    let binding=StoredCommitRecoveryBinding{intent:read_id(&h,"intent")?,intent_sha256:ContentDigest::parse(h["intent_sha"].as_str().ok_or("ACK_INTENT_SHA")?)?,
        manifest:&m,request:&request,result_sha256:ContentDigest::of(OUTPUT),result_size:OUTPUT.len()as u64};
    let observed=reconcile_stored_commit(&a,&revisions,&ctx,&rc,&binding,||20)?;
    let committed=matches!(mode.as_str(),"cas_after"|"complete_after");
    check(if committed{matches!(observed,StoredCommitRecoveryOutcome::Committed{result:RecoveredResult::VerifiedAvailable(_),..})}
        else{matches!(observed,StoredCommitRecoveryOutcome::NotObserved)},"ACK_NO_EFFECT_NOT_INFERRED_FROM_MISSING_COMMIT")?;
    let mut reconciled=false;let mut oracle_denied=false;
    if mode=="cas_after"{deny_reconcile(revisions.repository(),read_id(&h,"intent")?)?;oracle_denied=true;
        let r=revisions.repository().reconcile_job_committed(&rc,StoredCommitIntentLookup::new(project()?,id(101),id(102),1)?,revision(200)?,precommit,ContentDigest::of(b"committed-recovery"))?;
        check(r.state()==StoredJobState::TerminalSuccess&&r.outcome()==StoredJobOutcome::Committed&&r.attempt_no()==1,"ACK_COMMITTED_RECOVERY")?;reconciled=true;
    }else if !committed{deny_reconcile(revisions.repository(),precommit)?;oracle_denied=true;}
    let replay=revisions.repository().claim_job(&rc,prepared(&m)?.claim(),ContentDigest::of(b"ack-recovery-observe"))?;
    check(replay.outcome()==StoredJobOutcome::Replay&&replay.attempt_no()==1&&replay.fencing_token()==1
        &&replay.state()==if committed{StoredJobState::TerminalSuccess}else{StoredJobState::OutcomeUnknown},"ACK_RECOVERY_REPLAY_NO_SECOND_ATTEMPT")?;
    check(revisions.head(&rc,project()?,branch()?)?.generation()==if committed{2}else{1},"ACK_RECOVERY_HEAD")?;
    Ok(json!({"state":"PASS_REAL_DB_ACK_RECOVERY_WITHOUT_EXECUTION_RETRY","case":mode,"committed_observed":committed,
        "job_reconciled_committed":reconciled,"oracle_negative_SQLSTATE55000":oracle_denied,"left_unknown_without_no_effect_or_retry":!committed,
        "execution_retried":false,"actual_network_fault":false,"parent_retained_ephemeral_test_keys":true}))}
