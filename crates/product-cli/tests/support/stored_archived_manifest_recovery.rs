use super::*;
use hwpx_agent_cli::stored_revision_commit::{ArchivedRegisteredStoredCommitRecoveryOutcome as O,reconcile_archived_registered_stored_commit as cold};
fn lookup(f:&StoredFixture)->Result<StoredCommitIntentLookup,RevisionError>{let id=lease()?.identity();StoredCommitIntentLookup::new(f.project,id.idempotency_key,id.job_id,id.attempt_no)}
fn manager(f:&StoredFixture)->RequestContext{RequestContext::new(f.reader.tenant_id(),f.reader.subject(),[AuthScope::DocumentRead,AuthScope::DocumentWrite,AuthScope::ArtifactShare,AuthScope::SecurityModify])}
fn ready(cas_mode:u8,archived:bool)->Result<(StoredFixture,RevisionService<Jobs>),Box<dyn Error>>{
    let f=fixture()?;let c=writer(&f);let m=manifest_fixture::manifest(&f,"archived-cold-recovery")?;let r=Jobs::service(&f,0,cas_mode)?;
    let clock:fn()->u64=||10;
    let mut cas=if archived{StoredResultRevisionCas::bind_registered_archived(&f.artifacts,&r,&c,&f.revision_context,binding(&f,&m,OUTPUT),lease()?,clock)?}
        else{StoredResultRevisionCas::bind_registered(&f.artifacts,&r,&c,&f.revision_context,binding(&f,&m,OUTPUT),lease()?,clock)?};
    let root=tempfile::tempdir()?;let result=execute(&root.path().join("workspace"),m.clone(),OUTPUT,&mut cas);
    assert_eq!(result.is_ok(),cas_mode==0);drop(cas);drop(m);Ok((f,r))
}
fn observe(f:&StoredFixture,r:&RevisionService<Jobs>)->Result<O,StoredCommitError>{cold(&f.artifacts,r,&writer(f),&f.revision_context,lookup(f).map_err(|_|StoredCommitError::Binding)?,||20)}
fn row(f:&StoredFixture,r:&RevisionService<Jobs>)->Result<StoredCommitIntentRecord,Box<dyn Error>>{r.repository().read_commit_intent(&f.revision_context,lookup(f)?)?.ok_or_else(||"registered row missing".into())}
fn saved_wire(f:&StoredFixture,r:&RevisionService<Jobs>)->Result<serde_json::Value,Box<dyn Error>>{Ok(serde_json::from_slice(&f.artifacts.download(&writer(f),row(f,r)?.intent_artifact_id(),20)?)?)}
fn replace_wire(f:&StoredFixture,r:&RevisionService<Jobs>,bytes:Vec<u8>)->TestResult{
    replace_wire_with_precommit(f,r,bytes,None)
}
fn replace_wire_with_precommit(f:&StoredFixture,r:&RevisionService<Jobs>,bytes:Vec<u8>,replacement:Option<artifact_service::ArtifactDescriptor>)->TestResult{
    let c=writer(f);let original=row(f,r)?;let value:serde_json::Value=serde_json::from_slice(&bytes)?;
    let request:RevisionCommitRequest=serde_json::from_value(value["commit_intent"]["request"].clone())?;
    let intent=f.artifacts.ingest(&c,IngestRequest{bytes,kind:ArtifactKind::Receipt,media_type:MediaType::parse("application/json")?,file_name:FileName::parse("archived-negative.json")?},20)?;
    let result=f.artifacts.get_descriptor(&c,request.result_artifact_id(),20)?;let precommit=if let Some(replacement)=replacement{replacement}else{f.artifacts.get_descriptor(&c,original.precommit_artifact_id(),20)?};
    let registration=StoredCommitRegistration::new(lease()?,request,&result,&intent,&precommit)?;let record=StoredCommitIntentRecord::expected(&f.revision_context,&registration)?;
    let id=lease()?.identity();r.repository().records.lock().map_err(|_|"records")?.insert((f.project,id.idempotency_key,id.job_id,1),record);Ok(())
}
#[test]fn committed_observation_needs_no_manifest_or_request_and_never_reexecutes()->TestResult{
    let(f,r)=ready(0,true)?;let calls=r.repository().inner.calls.load(Ordering::SeqCst);let registered=r.repository().registered.load(Ordering::SeqCst);
    assert!(matches!(observe(&f,&r)?,O::Registered(StoredCommitRecoveryOutcome::Committed{result:RecoveredResult::VerifiedAvailable(_),..})));
    assert_eq!(r.repository().inner.calls.load(Ordering::SeqCst),calls);assert_eq!(r.repository().registered.load(Ordering::SeqCst),registered);Ok(())
}
#[test]fn legacy_intent_requests_original_manifest_without_claiming_no_effect()->TestResult{
    let(f,r)=ready(0,false)?;assert_eq!(observe(&f,&r)?,O::LegacyManifestRequired);assert_eq!(r.repository().inner.calls.load(Ordering::SeqCst),1);Ok(())
}
#[test]fn before_and_after_cas_unknown_remain_distinct_read_only_observations()->TestResult{
    for mode in[2,3]{let(f,r)=ready(mode,true)?;let out=observe(&f,&r)?;
        assert_eq!(matches!(out,O::Registered(StoredCommitRecoveryOutcome::NotObserved)),mode==2);
        assert_eq!(matches!(out,O::Registered(StoredCommitRecoveryOutcome::Committed{..})),mode==3);assert_eq!(r.repository().inner.calls.load(Ordering::SeqCst),1);}Ok(())
}
#[test]fn missing_registration_is_distinct_and_does_not_start_any_write()->TestResult{
    let f=fixture()?;let r=Jobs::service(&f,0,0)?;assert_eq!(observe(&f,&r)?,O::RegistrationNotObserved);
    assert_eq!(r.repository().inner.calls.load(Ordering::SeqCst),0);assert_eq!(r.repository().registered.load(Ordering::SeqCst),0);Ok(())
}
#[test]fn scope_and_foreign_context_fail_before_registered_lookup()->TestResult{
    let(f,r)=ready(0,true)?;let before=r.repository().events.lock().map_err(|_|"events")?.len();
    let no_read=RequestContext::new(f.reader.tenant_id(),f.reader.subject(),[AuthScope::DocumentWrite]);
    assert_eq!(cold(&f.artifacts,&r,&no_read,&f.revision_context,lookup(&f)?,||20).expect_err("scope"),StoredCommitError::Scope);
    let other=RevisionRequestContext::new(f.reader.tenant_id(),SubjectDigest::from_authenticated_subject("different reader")?);
    assert_eq!(cold(&f.artifacts,&r,&writer(&f),&other,lookup(&f)?,||20).expect_err("context"),StoredCommitError::Scope);
    assert_eq!(r.repository().events.lock().map_err(|_|"events")?.len(),before);Ok(())
}
#[test]fn both_receipt_acl_checks_are_fresh_and_regrant_restores_observation()->TestResult{
    for precommit in[false,true]{let(f,r)=ready(0,true)?;let row=row(&f,&r)?;let id=if precommit{row.precommit_artifact_id()}else{row.intent_artifact_id()};
        f.artifacts.set_permissions(&manager(&f),id,f.reader.subject(),BTreeSet::from([ArtifactPermission::Manage]),20)?;
        assert_eq!(observe(&f,&r).expect_err("revoked"),StoredCommitError::Artifact);
        f.artifacts.set_permissions(&manager(&f),id,f.reader.subject(),BTreeSet::from([ArtifactPermission::Read,ArtifactPermission::Manage]),21)?;
        assert!(matches!(observe(&f,&r)?,O::Registered(StoredCommitRecoveryOutcome::Committed{..})));}Ok(())
}
#[test]fn quarantined_precommit_and_ciphertext_tamper_are_rejected_without_cas()->TestResult{
    let(f,r)=ready(0,true)?;f.blobs.tamper.store(true,Ordering::SeqCst);assert_eq!(observe(&f,&r).expect_err("tamper"),StoredCommitError::Artifact);
    f.blobs.tamper.store(false,Ordering::SeqCst);f.artifacts.quarantine(&manager(&f),row(&f,&r)?.precommit_artifact_id(),QuarantineReason::parse("ARCHIVE_FIXTURE")?,20)?;
    assert_eq!(observe(&f,&r).expect_err("quarantined"),StoredCommitError::Artifact);assert_eq!(r.repository().inner.calls.load(Ordering::SeqCst),1);Ok(())
}
#[test]fn unavailable_result_does_not_erase_committed_history()->TestResult{
    let(f,r)=ready(0,true)?;let head=r.head(&f.revision_context,f.project,f.branch)?;let result=r.node(&f.revision_context,f.project,head.revision_id().ok_or("head")?)?.result_artifact_id();
    f.artifacts.quarantine(&manager(&f),result,QuarantineReason::parse("ARCHIVE_FIXTURE")?,20)?;
    assert!(matches!(observe(&f,&r)?,O::Registered(StoredCommitRecoveryOutcome::Committed{result:RecoveredResult::Unavailable,..})));Ok(())
}
#[test]fn unknown_versions_fields_and_manifest_hash_drift_fail_closed()->TestResult{
    for mode in 0..5{let(f,r)=ready(0,true)?;let mut value=saved_wire(&f,&r)?;
        match mode{0=>value["schema_version"]=serde_json::json!("future/v3"),1=>value["extra"]=serde_json::json!(true),
            2=>value["commit_intent"]["schema_version"]=serde_json::json!("future/v2"),3=>value["commit_intent"]["extra"]=serde_json::json!(true),
            _=>value["manifest_canonical_json"]=serde_json::json!([0,1,2])}
        replace_wire(&f,&r,serde_json::to_vec(&value)?)?;assert_eq!(observe(&f,&r).expect_err("strict archive"),StoredCommitError::Binding);
        assert_eq!(r.repository().inner.calls.load(Ordering::SeqCst),1);}Ok(())
}
#[test]fn canonical_but_substituted_archive_cannot_match_original_engine_precommit()->TestResult{
    for key in["transaction_id","registry_sequence","route_count"]{let(f,r)=ready(0,true)?;let mut value=saved_wire(&f,&r)?;
        let bytes:Vec<u8>=serde_json::from_value(value["manifest_canonical_json"].clone())?;let raw=String::from_utf8(bytes)?;
        let parsed:serde_json::Value=serde_json::from_str(&raw)?;let replacement=if key=="transaction_id"{serde_json::json!("different-valid-archive")}else{serde_json::json!(parsed[key].as_u64().ok_or("counter")?+1)};
        let changed=raw.replace(&format!("\"{key}\":{}",parsed[key]),&format!("\"{key}\":{replacement}"));assert_ne!(changed,raw);
        value["manifest_canonical_json"]=serde_json::json!(changed.as_bytes());value["commit_intent"]["manifest_sha256"]=serde_json::json!(hex::encode(Sha256::digest(changed.as_bytes())));
        replace_wire(&f,&r,serde_json::to_vec(&value)?)?;assert_eq!(observe(&f,&r).expect_err("original precommit"),StoredCommitError::Binding);
        assert_eq!(r.repository().inner.calls.load(Ordering::SeqCst),1);}Ok(())
}
#[test]fn foreign_registered_locator_is_not_used_as_a_recovery_handle()->TestResult{
    let(f,r)=ready(0,true)?;let record=row(&f,&r)?;let id=lease()?.identity();let foreign=Uuid::from_u128(9911);
    r.repository().records.lock().map_err(|_|"records")?.insert((f.project,id.idempotency_key,foreign,1),record);
    assert_eq!(cold(&f.artifacts,&r,&writer(&f),&f.revision_context,StoredCommitIntentLookup::new(f.project,id.idempotency_key,foreign,1)?,||20).expect_err("locator"),StoredCommitError::Binding);Ok(())
}
#[test]fn original_manifest_api_accepts_v2_only_with_the_exact_original_manifest()->TestResult{
    let f=fixture()?;let c=writer(&f);let m=manifest_fixture::manifest(&f,"v2-original-api")?;let r=Jobs::service(&f,0,0)?;
    let mut cas=StoredResultRevisionCas::bind_registered_archived(&f.artifacts,&r,&c,&f.revision_context,binding(&f,&m,OUTPUT),lease()?,||10)?;
    let root=tempfile::tempdir()?;execute(&root.path().join("workspace"),m.clone(),OUTPUT,&mut cas)?;drop(cas);
    assert!(matches!(reconcile_registered_stored_commit(&f.artifacts,&r,&c,&f.revision_context,lookup(&f)?,&m,||20)?,RegisteredStoredCommitRecoveryOutcome::Registered(StoredCommitRecoveryOutcome::Committed{..})));
    let other=manifest_fixture::manifest(&f,"different-v2-original-api")?;
    assert_eq!(reconcile_registered_stored_commit(&f.artifacts,&r,&c,&f.revision_context,lookup(&f)?,&other,||20).expect_err("manifest"),StoredCommitError::Binding);Ok(())
}
#[test]fn outer_nested_and_manifest_duplicate_keys_are_not_silently_deduplicated()->TestResult{
    for mode in 0..3{let(f,r)=ready(0,true)?;let mut value=saved_wire(&f,&r)?;
        let bytes=if mode<2{let text=String::from_utf8(serde_json::to_vec(&value)?)?;
            if mode==0{text.replacen('{',"{\"schema_version\":\"hwpx-agent.stored-revision-commit-intent/v2\",",1).into_bytes()}
            else{text.replacen("\"commit_intent\":{","\"commit_intent\":{\"schema_version\":\"hwpx-agent.stored-revision-commit-intent/v1\",",1).into_bytes()}
        }else{let raw:Vec<u8>=serde_json::from_value(value["manifest_canonical_json"].clone())?;let raw=String::from_utf8(raw)?.replacen('{',"{\"schema_version\":\"hwpx-agent.execution-manifest/v1\",",1);
            value["manifest_canonical_json"]=serde_json::json!(raw.as_bytes());value["commit_intent"]["manifest_sha256"]=serde_json::json!(hex::encode(Sha256::digest(raw.as_bytes())));serde_json::to_vec(&value)?};
        replace_wire(&f,&r,bytes)?;assert_eq!(observe(&f,&r).expect_err("duplicate"),StoredCommitError::Binding);
    }Ok(())
}
#[test]fn authenticated_but_non_engine_precommit_shape_is_rejected_before_commit_observation()->TestResult{
    let(f,r)=ready(0,true)?;let c=writer(&f);let original=row(&f,&r)?;let raw=f.artifacts.download(&c,original.precommit_artifact_id(),20)?;
    let raw=String::from_utf8(raw)?.replacen('{',"{\"unexpected\":true,",1).into_bytes();
    let precommit=f.artifacts.ingest(&c,IngestRequest{bytes:raw,kind:ArtifactKind::Receipt,media_type:MediaType::parse("application/json")?,file_name:FileName::parse("non-engine-precommit.json")?},20)?;
    let mut value=saved_wire(&f,&r)?;let old:RevisionCommitRequest=serde_json::from_value(value["commit_intent"]["request"].clone())?;
    let changed=RevisionCommitRequest::new(old.commit_id(),old.project_id(),old.branch_id(),old.expected_head(),old.new_revision_id(),old.parents().to_vec(),
        old.source_artifact_id(),old.result_artifact_id(),old.semantic_diff_artifact_id(),old.operation_plan_sha256(),RevisionValidationState::Verified,
        old.validation_summary_sha256(),precommit.sha256)?;
    value["commit_intent"]["request"]=serde_json::to_value(changed)?;replace_wire_with_precommit(&f,&r,serde_json::to_vec(&value)?,Some(precommit))?;
    assert_eq!(observe(&f,&r).expect_err("engine precommit shape"),StoredCommitError::Binding);assert_eq!(r.repository().inner.calls.load(Ordering::SeqCst),1);Ok(())
}
