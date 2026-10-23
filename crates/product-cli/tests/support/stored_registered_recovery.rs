use super::*;
fn manager(f:&StoredFixture)->RequestContext{RequestContext::new(f.reader.tenant_id(),f.reader.subject(),[AuthScope::DocumentRead,AuthScope::DocumentWrite,AuthScope::ArtifactShare,AuthScope::SecurityModify])}
fn lookup(f:&StoredFixture)->Result<StoredCommitIntentLookup,RevisionError>{let l=lease()?.identity();StoredCommitIntentLookup::new(f.project,l.idempotency_key,l.job_id,l.attempt_no)}
fn ready(mode:u8)->Result<(StoredFixture,ExecutionManifest,RevisionService<Jobs>),Box<dyn Error>>{
    let f=fixture()?;let c=writer(&f);let m=manifest_fixture::manifest(&f,"registered-read-recovery")?;let revisions=Jobs::service(&f,0,mode)?;
    let mut cas=StoredResultRevisionCas::bind_registered(&f.artifacts,&revisions,&c,&f.revision_context,binding(&f,&m,OUTPUT),lease()?,||10)?;
    let root=tempfile::tempdir()?;let outcome=execute(&root.path().join("workspace"),m.clone(),OUTPUT,&mut cas);
    assert_eq!(outcome.is_err(),mode!=0);drop(cas);Ok((f,m,revisions))
}
fn observe(f:&StoredFixture,m:&ExecutionManifest,r:&RevisionService<Jobs>)->Result<RegisteredStoredCommitRecoveryOutcome,StoredCommitError>{
    reconcile_registered_stored_commit(&f.artifacts,r,&writer(f),&f.revision_context,lookup(f).map_err(|_|StoredCommitError::Binding)?,m,||20)
}
#[test]fn committed_recovery_needs_no_saved_request_and_never_reexecutes()->TestResult{
    let(f,m,r)=ready(0)?;let before=r.repository().inner.calls.load(Ordering::SeqCst);
    assert!(matches!(observe(&f,&m,&r)?,RegisteredStoredCommitRecoveryOutcome::Registered(StoredCommitRecoveryOutcome::Committed{result:RecoveredResult::VerifiedAvailable(_),..})));
    assert_eq!(r.repository().inner.calls.load(Ordering::SeqCst),before);assert_eq!(r.repository().registered.load(Ordering::SeqCst),1);Ok(())
}
#[test]fn before_and_after_cas_unknown_have_distinct_observations_not_retry_permissions()->TestResult{
    for mode in[2,3]{let(f,m,r)=ready(mode)?;let out=observe(&f,&m,&r)?;
        assert_eq!(matches!(out,RegisteredStoredCommitRecoveryOutcome::Registered(StoredCommitRecoveryOutcome::NotObserved)),mode==2);
        assert_eq!(matches!(out,RegisteredStoredCommitRecoveryOutcome::Registered(StoredCommitRecoveryOutcome::Committed{..})),mode==3);
        assert_eq!(r.repository().inner.calls.load(Ordering::SeqCst),1);}Ok(())
}
#[test]fn missing_registration_is_distinct_from_missing_commit_and_has_no_side_effect()->TestResult{
    let f=fixture()?;let m=manifest_fixture::manifest(&f,"no-registration")?;let r=Jobs::service(&f,0,0)?;
    assert_eq!(observe(&f,&m,&r)?,RegisteredStoredCommitRecoveryOutcome::RegistrationNotObserved);
    assert_eq!(r.repository().inner.calls.load(Ordering::SeqCst),0);assert_eq!(r.repository().registered.load(Ordering::SeqCst),0);Ok(())
}
#[test]fn read_scope_and_foreign_context_are_rejected_before_registered_lookup()->TestResult{
    let(f,m,r)=ready(0)?;let no_read=RequestContext::new(f.reader.tenant_id(),f.reader.subject(),[AuthScope::DocumentWrite]);
    assert_eq!(reconcile_registered_stored_commit(&f.artifacts,&r,&no_read,&f.revision_context,lookup(&f)?,&m,||20).expect_err("scope"),StoredCommitError::Scope);
    let foreign=RevisionRequestContext::new(f.reader.tenant_id(),SubjectDigest::from_authenticated_subject("other recovery caller")?);
    assert_eq!(reconcile_registered_stored_commit(&f.artifacts,&r,&writer(&f),&foreign,lookup(&f)?,&m,||20).expect_err("context"),StoredCommitError::Scope);Ok(())
}
#[test]fn foreign_returned_locator_and_drifted_manifest_are_rejected()->TestResult{
    let(f,m,r)=ready(0)?;let l=lease()?.identity();let record=r.repository().read_commit_intent(&f.revision_context,lookup(&f)?)?.ok_or("row")?;
    let bad=Uuid::from_u128(9909);r.repository().records.lock().map_err(|_|"records")?.insert((f.project,l.idempotency_key,bad,1),record);
    assert_eq!(reconcile_registered_stored_commit(&f.artifacts,&r,&writer(&f),&f.revision_context,StoredCommitIntentLookup::new(f.project,l.idempotency_key,bad,1)?,&m,||20).expect_err("lookup"),StoredCommitError::Binding);
    let other=manifest_fixture::manifest(&f,"different-manifest")?;assert_eq!(observe(&f,&other,&r).expect_err("manifest"),StoredCommitError::Binding);Ok(())
}
#[test]fn both_receipt_acls_are_fresh_and_regrant_restores_observation()->TestResult{
    for precommit in[false,true]{let(f,m,r)=ready(0)?;let row=r.repository().read_commit_intent(&f.revision_context,lookup(&f)?)?.ok_or("row")?;
        let target=if precommit{row.precommit_artifact_id()}else{row.intent_artifact_id()};
        f.artifacts.set_permissions(&manager(&f),target,f.reader.subject(),BTreeSet::from([ArtifactPermission::Manage]),20)?;
        assert_eq!(observe(&f,&m,&r).expect_err("revoked"),StoredCommitError::Artifact);
        f.artifacts.set_permissions(&manager(&f),target,f.reader.subject(),BTreeSet::from([ArtifactPermission::Read,ArtifactPermission::Manage]),21)?;
        assert!(matches!(observe(&f,&m,&r)?,RegisteredStoredCommitRecoveryOutcome::Registered(StoredCommitRecoveryOutcome::Committed{..})));}Ok(())
}
#[test]fn quarantined_precommit_is_not_accepted_as_an_authenticated_receipt()->TestResult{
    let(f,m,r)=ready(0)?;let row=r.repository().read_commit_intent(&f.revision_context,lookup(&f)?)?.ok_or("row")?;
    f.artifacts.quarantine(&manager(&f),row.precommit_artifact_id(),QuarantineReason::parse("RECOVERY_FIXTURE")?,20)?;
    assert_eq!(observe(&f,&m,&r).expect_err("quarantine"),StoredCommitError::Artifact);Ok(())
}
#[test]fn result_availability_remains_independent_of_committed_observation()->TestResult{
    let(f,m,r)=ready(0)?;let head=r.head(&f.revision_context,f.project,f.branch)?;let result=r.node(&f.revision_context,f.project,head.revision_id().ok_or("head")?)?.result_artifact_id();
    f.artifacts.quarantine(&manager(&f),result,QuarantineReason::parse("RECOVERY_FIXTURE")?,20)?;
    assert!(matches!(observe(&f,&m,&r)?,RegisteredStoredCommitRecoveryOutcome::Registered(StoredCommitRecoveryOutcome::Committed{result:RecoveredResult::Unavailable,..})));Ok(())
}
#[test]fn ciphertext_tamper_is_denied_without_a_second_commit()->TestResult{
    let(f,m,r)=ready(0)?;f.blobs.tamper.store(true,Ordering::SeqCst);
    assert_eq!(observe(&f,&m,&r).expect_err("ciphertext"),StoredCommitError::Artifact);
    f.blobs.tamper.store(false,Ordering::SeqCst);assert!(matches!(observe(&f,&m,&r)?,RegisteredStoredCommitRecoveryOutcome::Registered(StoredCommitRecoveryOutcome::Committed{..})));
    assert_eq!(r.repository().inner.calls.load(Ordering::SeqCst),1);Ok(())
}
#[test]fn authenticated_but_duplicate_or_unknown_receipt_fields_are_rejected()->TestResult{
    for extra in[",\"unrecognized\":1}",",\"schema_version\":\"duplicate\"}"]{
        let(f,m,r)=ready(0)?;let c=writer(&f);let original=r.repository().read_commit_intent(&f.revision_context,lookup(&f)?)?.ok_or("row")?;
        let bytes=f.artifacts.download(&c,original.intent_artifact_id(),20)?;let v:serde_json::Value=serde_json::from_slice(&bytes)?;
        let request:RevisionCommitRequest=serde_json::from_value(v["request"].clone())?;
        let mut malformed=String::from_utf8(bytes)?;assert_eq!(malformed.pop(),Some('}'));malformed.push_str(extra);
        let intent=f.artifacts.ingest(&c,IngestRequest{bytes:malformed.into_bytes(),kind:ArtifactKind::Receipt,media_type:MediaType::parse("application/json")?,file_name:FileName::parse("malformed-recovery.json")?},20)?;
        let result=f.artifacts.get_descriptor(&c,request.result_artifact_id(),20)?;let precommit=f.artifacts.get_descriptor(&c,original.precommit_artifact_id(),20)?;
        let registration=StoredCommitRegistration::new(lease()?,request,&result,&intent,&precommit)?;
        let record=StoredCommitIntentRecord::expected(&f.revision_context,&registration)?;let l=lease()?.identity();
        r.repository().records.lock().map_err(|_|"records")?.insert((f.project,l.idempotency_key,l.job_id,1),record);
        assert_eq!(observe(&f,&m,&r).expect_err("strict JSON"),StoredCommitError::Binding);
    }Ok(())
}
