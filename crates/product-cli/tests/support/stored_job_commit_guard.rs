// Original job/lease/intent/commit coordinator. Repository/scanner/validator here are synthetic.
use super::*;
fn run_guarded(stop:u8,mode:u8)->TestResult{
    let f=fixture()?;let m=manifest_fixture::manifest(&f,"guarded-job")?;let revisions=LifecycleJobs::service(&f,mode);let c=writer(&f);let root=tempfile::tempdir()?;let path=root.path().join("workspace");let calls=Cell::new(0);
    let mut prepared=PreparedStoredJob::prepare(binding(&f,&m,OUTPUT),options(),Default::default())?;
    prepared.require_precommit_guard(Box::new(||{calls.set(calls.get()+1);let n=calls.get();
        let events=revisions.repository().events().map_err(|_|StoredCommitError::CurrentGuard)?;
        match n{1=>assert!(events.is_empty()),2=>assert_eq!(events.last(),Some(&"validating")),3=>assert_eq!(events.last(),Some(&"register")),_=>panic!("unexpected repeated guard")}
        if n==usize::from(stop){Err(StoredCommitError::CurrentGuard)}else{Ok(())}}))?;
    assert_eq!(prepared.require_precommit_guard(Box::new(||Ok(()))),Err(StoredCommitError::CurrentGuard));
    let r=prepared.run_once(&f.artifacts,&revisions,&c,&f.revision_context,Uuid::from_u128(9201),Uuid::from_u128(9202),30,
        ContentDigest::of(b"server transition event"),&path,SOURCE,&mut |_:&[u8]|ValidationOutcome::Valid,||10);
    if mode==1{assert_eq!(calls.get(),1);assert_eq!(r.stage,StoredJobRunStage::Replay);assert_eq!(revisions.repository().events()?,["claim"]);assert!(!path.exists());}
    else if stop==0{assert_eq!(calls.get(),3);assert_eq!(r.stage,StoredJobRunStage::Completed);assert!(r.completion.is_some());assert_eq!(revisions.repository().inner.calls.load(Ordering::SeqCst),1);}
    else{assert_eq!(calls.get(),usize::from(stop));assert!(r.completion.is_none()&&r.revision_receipt.is_none()&&r.unknown.is_none());
        assert_eq!(revisions.head(&f.revision_context,f.project,f.branch)?,f.head);assert_eq!(revisions.repository().inner.calls.load(Ordering::SeqCst),0);
        if stop==1{assert_eq!(r.binding_error,Some(StoredCommitError::CurrentGuard));assert!(r.claim.is_none());assert!(!path.exists());assert!(revisions.repository().events()?.is_empty());}
        else{assert_eq!(r.cas_error,Some(StoredCommitError::CurrentGuard));assert!(r.transaction.as_ref().ok_or("transaction")?.is_err());
            if stop==2{assert!(r.result.is_none()&&r.registered_intent.is_none());}
            else{assert!(r.registered_intent.is_some()&&r.registration_response.is_some());for retained in [&r.result,&r.intent,&r.precommit]{let d=retained.as_ref().ok_or("retained recovery artifact")?;assert!(!f.artifacts.download(&c,d.artifact_id,11)?.is_empty());}
                assert_eq!(revisions.repository().events()?,["claim","lease","staged","executing","validating","register"]);}}}
    assert_eq!(f.artifacts.download(&f.reader,f.result,11)?,SOURCE);Ok(())
}
#[test]fn healthy_job_refreshes_before_claim_ingest_and_final_cas()->TestResult{run_guarded(0,0)}
#[test]fn failed_preclaim_guard_creates_no_claim_or_workspace()->TestResult{run_guarded(1,0)}
#[test]fn failed_preingest_guard_creates_no_result_or_intent()->TestResult{run_guarded(2,0)}
#[test]fn failed_postregistration_guard_preserves_recovery_without_commit_or_unknown_claim()->TestResult{run_guarded(3,0)}
#[test]fn replay_observation_never_reenters_ingest_or_final_guards()->TestResult{run_guarded(0,1)}
