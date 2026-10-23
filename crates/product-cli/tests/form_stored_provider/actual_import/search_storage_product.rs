//! Actual candidate/engine/scanner/AEAD/CAS; in-memory stores and synthetic routes, never Native qualification.
#[path="search_request_lookup_product.rs"] mod request_lookup;
use super::*;
use hwpx_agent_cli::{form_product_request::stored_operations::{StoredProductRequest as Dispatch,search_mutations::{SearchMutationLimits as Limits,SEARCH_MUTATION_REQUEST_SCHEMAS as SCHEMAS},
    compiled_search::routing::PreparedSearchExecutionManifest as Manifest},stored_revision_commit::{StoredResultRevisionCas,StoredCommitError,StoredPrecommitGuard,job::identity::StoredJobPolicy}};
use domain_ir::{Architecture,BackendHealth,BackendHealthState,BackendId,BackendKind,CapabilityId,CapabilityRouteCatalog,ExactTargetProfile,
    PolicyScope,PreservationImpact,PreservationRequirement,ProtectionState,RegistryTrustState,RouteBinding,RouteContext,SignatureImpact,SupportState,TargetProfileId,TransactionId};
use operation_engine::{OutputValidator,ValidationOutcome,WorkspaceTransaction,FaultPlan};
#[path="search_storage_fixture.rs"] mod cases;
fn routing(cap:&str,now:u64,mode:u8)->Result<(RouteContext,CapabilityRouteCatalog),Box<dyn Error>> {
    let backend=BackendId::parse("synthetic-storage-direct")?;
    let target=ExactTargetProfile::new(TargetProfileId::parse("synthetic-storage-target")?,if mode==1{"11.0.0.9999"}else{"11.0.0.9136"},Architecture::X86)?;
    let digest=if mode==2{[8;32]}else{[7;32]};let generation=if mode==3{2}else{1};
    let context=RouteContext::new(target.clone(),digest,1,RegistryTrustState::SignatureVerified,PolicyScope::CurrentPcPersonalLocalDevelopment,
        PreservationRequirement::Exact,ProtectionState::Unprotected,now*1000,
        vec![BackendHealth::new(backend.clone(),BackendHealthState::Healthy,generation,now*1000,10_000)])?;
    let binding=RouteBinding::new(CapabilityId::parse(cap)?,backend,BackendKind::DirectHwpx,SupportState::Verified,target,digest,1,10,1,PreservationImpact::Exact,SignatureImpact::Preserved);
    Ok((context,CapabilityRouteCatalog::from_bindings(vec![binding])?))
}
fn manifest(p:&Provider<'_>,v:&Value)->Result<Manifest,Box<dyn Error>> {
    let out=Dispatch::prepare_compiled_search_json(p,&wire(v)?,Limits::standard()?,4)?;
    let(c,r)=routing(out.receipt().capability_id,6,0)?;Ok(out.prepare_execution_manifest(p,&c,&r,TransactionId::parse("search-storage-transaction")?,6)?)
}
fn exercise_family(i:usize)->TestResult {
    assert_eq!(SCHEMAS.len(),23);
        let bytes=cases::source(i)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);
        let out=manifest(&p,&cases::request(i,&s,&bytes)?)?;assert_eq!(out.compiled_receipt().request_schema,SCHEMAS[i]);
        let(c,r)=routing(out.compiled_receipt().capability_id,6,0)?;assert!(out.require_current_product_route(&p,&c,&r,6).is_err());
        let root=tempfile::tempdir()?;
        out.with_verified_storage_preparation(&p,&c,&r,6,|input|->TestResult {
            assert_eq!(input.source_bytes(),bytes);assert_ne!(input.output_bytes(),bytes);assert_eq!(input.manifest(),out.manifest());
            assert_eq!(input.receipt().request_schema,SCHEMAS[i]);assert!(!input.receipt().validation_executed&&!input.receipt().execution_or_native_authority);
            assert_eq!(ContentDigest::of(input.output_bytes()).as_bytes(),&input.receipt().output_package_sha256);
            let revision=rev::RevisionId::generate();let job=input.prepare_bound_job(StoredJobPolicy::default(),rev::CommitId::generate(),revision,Default::default())?;
            assert!(!format!("{job:?}{input:?}").contains("PRIVATE"));
            let cap=out.compiled_receipt().capability_id;let calls=Cell::new(0);
            let mut cas=StoredResultRevisionCas::bind(&s.artifacts,&s.revisions,&actor,&s.revision_context,input.commit_binding(rev::CommitId::generate(),revision)?,||7)?;
            cas.require_precommit_guard(Box::new(out.current_commit_guard(&p,||{calls.set(calls.get()+1);let(c,r)=routing(cap,7,0).map_err(|_|())?;Ok((c,r,7))})))?;
            let mut validator=input.output_validator();let mut tx=WorkspaceTransaction::create(root.path().join("source-owned"),input.manifest().clone(),Default::default())?;
            assert!(tx.execute_bytes(input.source_bytes(),input.output_bytes(),&mut validator,&mut cas,&mut FaultPlan::none()).is_ok(),"family {i}");
            assert_eq!(calls.get(),2);assert!(cas.error().is_none());let saved=cas.retained_result().ok_or("saved")?;
            assert_eq!(s.artifacts.download(&actor,saved.artifact_id,8)?,input.output_bytes());
            assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?.revision_id(),Some(revision));
            assert_eq!(validator.validate(input.output_bytes()),ValidationOutcome::Failed);Ok(())
        })??;
        assert_eq!(s.artifacts.download(&s.reader,s.result,8)?,bytes);
    Ok(())
}
#[test]fn family_00_literal()->TestResult {exercise_family(0)}
#[test]fn family_01_atoms()->TestResult {exercise_family(1)}
#[test]fn family_02_review()->TestResult {exercise_family(2)}
#[test]fn family_03_selector()->TestResult {exercise_family(3)}
#[test]fn family_04_regex()->TestResult {exercise_family(4)}
#[test]fn family_05_insertion()->TestResult {exercise_family(5)}
#[test]fn family_06_character()->TestResult {exercise_family(6)}
#[test]fn family_07_text_style()->TestResult {exercise_family(7)}
#[test]fn family_08_paragraph()->TestResult {exercise_family(8)}
#[test]fn family_09_unicode_scope()->TestResult {exercise_family(9)}
#[test]fn family_10_unicode_match()->TestResult {exercise_family(10)}
#[test]fn family_11_case()->TestResult {exercise_family(11)}
#[test]fn family_12_width()->TestResult {exercise_family(12)}
#[test]fn family_13_whitespace()->TestResult {exercise_family(13)}
#[test]fn family_14_text_control()->TestResult {exercise_family(14)}
#[test]fn family_15_number_control()->TestResult {exercise_family(15)}
#[test]fn family_16_sort()->TestResult {exercise_family(16)}
#[test]fn family_17_sort_groups()->TestResult {exercise_family(17)}
#[test]fn family_18_fonts()->TestResult {exercise_family(18)}
#[test]fn family_19_font_options()->TestResult {exercise_family(19)}
#[test]fn family_20_named_styles()->TestResult {exercise_family(20)}
#[test]fn family_21_named_options()->TestResult {exercise_family(21)}
#[test]fn family_22_personal_mask()->TestResult {exercise_family(22)}
#[test]
fn corrupt_truncated_source_and_other_candidate_bytes_fail_once_without_validator_replay()->TestResult {
    let bytes=cases::source(0)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let out=manifest(&p,&cases::request(0,&s,&bytes)?)?;
    let(c,r)=routing(out.compiled_receipt().capability_id,6,0)?;
    out.with_verified_storage_preparation(&p,&c,&r,6,|input|{
        let mut corrupt=input.output_bytes().to_vec();corrupt[10]^=1;
        for proposed in[&[][..],input.source_bytes(),&corrupt,input.output_bytes().get(..10).unwrap_or_default()] {
            let mut validator=input.output_validator();assert_eq!(validator.validate(proposed),ValidationOutcome::Rejected);
            assert_eq!(validator.validate(input.output_bytes()),ValidationOutcome::Failed);
        }
        assert!(!input.receipt().validation_executed);
    })?;assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);Ok(())
}
#[test]
fn same_public_key_keeps_server_job_ids_across_changed_schema_content_and_plan()->TestResult {
    let bytes=cases::source(11)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);
    let mut ids=Vec::new();
    for i in[11,12] {let mut v=cases::request(i,&s,&bytes)?;v["plan_id"]=json!(format!("different-{i}"));let out=manifest(&p,&v)?;
        let(c,r)=routing(out.compiled_receipt().capability_id,6,0)?;
        ids.push(out.with_verified_storage_preparation(&p,&c,&r,6,|input|input.job_identity().clone())?);
    }
    assert_eq!((ids[0].key(),ids[0].job(),ids[0].request()),(ids[1].key(),ids[1].job(),ids[1].request()));assert_ne!(ids[0],ids[1]);Ok(())
}
#[test]
fn bound_jobs_reject_old_revision_and_invalid_retry_policy_without_claim_or_ingest()->TestResult {
    let bytes=cases::source(0)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let out=manifest(&p,&cases::request(0,&s,&bytes)?)?;
    let before=s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count();let(c,r)=routing(out.compiled_receipt().capability_id,6,0)?;
    out.with_verified_storage_preparation(&p,&c,&r,6,|input|->TestResult {
        assert!(input.commit_binding(rev::CommitId::generate(),s.head.revision_id().ok_or("head")?).is_err());
        for p in[StoredJobPolicy{max_attempts:0,..Default::default()},StoredJobPolicy{base_delay_seconds:-1,..Default::default()},StoredJobPolicy{ttl_seconds:0,..Default::default()}] {
            assert!(input.prepare_bound_job(p,rev::CommitId::generate(),rev::RevisionId::generate(),Default::default()).is_err());
        }Ok(())
    })??;assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),before);assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);Ok(())
}
#[test]
fn stale_clock_target_registry_or_health_never_reaches_storage_callback()->TestResult {
    let bytes=cases::source(0)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let out=manifest(&p,&cases::request(0,&s,&bytes)?)?;
    for mode in 0..=3 {let(c,r)=routing(out.compiled_receipt().capability_id,6,mode)?;let called=Cell::new(false);
        assert!(out.with_verified_storage_preparation(&p,&c,&r,if mode==0{7}else{6},|_|called.set(true)).is_err());assert!(!called.get());
    }Ok(())
}
#[test]
fn current_commit_guard_refreshes_and_latches_missing_clock_and_route_failures()->TestResult {
    let bytes=cases::source(0)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let out=manifest(&p,&cases::request(0,&s,&bytes)?)?;let cap=out.compiled_receipt().capability_id;
    for mode in 0..=4 {let calls=Cell::new(0);let mut guard=out.current_commit_guard(&p,||{
        let n=calls.get()+1;calls.set(n);if n==2&&mode==0{return Err(());}
        let(c,r)=routing(cap,7,if n==2&&mode<=3{mode}else{0}).map_err(|_|())?;Ok((c,r,if n==2&&mode==4{8}else{7}))
    });guard.check()?;assert_eq!(guard.check(),Err(StoredCommitError::CurrentGuard));assert_eq!(guard.check(),Err(StoredCommitError::CurrentGuard));assert_eq!(calls.get(),2);}
    Ok(())
}
#[test]
fn current_acl_quarantine_and_aead_denials_block_storage_and_latch_guard()->TestResult {
    for mode in 0..3 {let bytes=cases::source(0)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let out=manifest(&p,&cases::request(0,&s,&bytes)?)?;
        let cap=out.compiled_receipt().capability_id;let mut guard=out.current_commit_guard(&p,||{let(c,r)=routing(cap,7,0).map_err(|_|())?;Ok((c,r,7))});guard.check()?;
        match mode{0=>{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),7)?;},1=>{s.artifacts.quarantine(&s.owner,s.result,QuarantineReason::parse("CURRENT_STORAGE")?,7)?;},_=>s.blobs.tamper.store(true,Ordering::SeqCst)}
        assert_eq!(guard.check(),Err(StoredCommitError::CurrentGuard));let(c,r)=routing(cap,7,0)?;let called=Cell::new(false);
        assert!(out.with_verified_storage_preparation(&p,&c,&r,7,|_|called.set(true)).is_err());assert!(!called.get());
    }Ok(())
}
fn stopped_commit(boundary:u8)->TestResult {
    let bytes=cases::source(0)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let out=manifest(&p,&cases::request(0,&s,&bytes)?)?;
    let(c,r)=routing(out.compiled_receipt().capability_id,6,0)?;let root=tempfile::tempdir()?;
    out.with_verified_storage_preparation(&p,&c,&r,6,|input|->TestResult {
        let calls=Cell::new(0);let cap=out.compiled_receipt().capability_id;
        let mut cas=StoredResultRevisionCas::bind(&s.artifacts,&s.revisions,&actor,&s.revision_context,input.commit_binding(rev::CommitId::generate(),rev::RevisionId::generate())?,||7)?;
        cas.require_precommit_guard(Box::new(out.current_commit_guard(&p,||{let n=calls.get()+1;calls.set(n);if n==boundary{return Err(());}let(c,r)=routing(cap,7,0).map_err(|_|())?;Ok((c,r,7))})))?;
        assert_eq!(cas.require_precommit_guard(Box::new(||Ok(()))),Err(StoredCommitError::CurrentGuard));
        let mut validator=input.output_validator();let mut tx=WorkspaceTransaction::create(root.path().join("stopped"),input.manifest().clone(),Default::default())?;
        assert!(tx.execute_bytes(input.source_bytes(),input.output_bytes(),&mut validator,&mut cas,&mut FaultPlan::none()).is_err());
        assert_eq!(cas.error(),Some(StoredCommitError::CurrentGuard));assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);
        if boundary==1{assert!(cas.retained_result().is_none()&&cas.retained_intent().is_none());}
        else{for saved in[cas.retained_result(),cas.retained_intent(),cas.retained_precommit()]{let saved=saved.ok_or("recovery")?;assert!(!s.artifacts.download(&actor,saved.artifact_id,8)?.is_empty());}}
        assert_eq!(cas.require_precommit_guard(Box::new(||Ok(()))),Err(StoredCommitError::CurrentGuard));Ok(())
    })??;assert_eq!(s.artifacts.download(&s.reader,s.result,8)?,bytes);Ok(())
}
#[test]fn pre_ingest_denial_keeps_original_and_does_not_store_a_result()->TestResult {stopped_commit(1)}
#[test]fn final_cas_denial_keeps_head_and_retains_recovery_artifacts()->TestResult {stopped_commit(2)}
