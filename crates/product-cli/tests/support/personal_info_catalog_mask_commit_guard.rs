// Real candidate/manifest and HWPX validator; synthetic route/repository are not production qualification.
use super::*;
use hwpx_agent_cli::stored_revision_commit::{StoredCommitError,StoredPrecommitGuard};

#[test]
fn fresh_server_snapshot_is_required_at_every_check_without_remasking()->R{
    let bytes=raw("KEEP MARK END")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let out=manifest(&p,&f,&req(&s,&bytes,&f,false)?)?;
    let calls=Cell::new(0);let mut guard=out.current_commit_guard(&p,&f,||{calls.set(calls.get()+1);let(c,r)=route(7,0).map_err(|_|())?;Ok((c,r,7))});
    for _ in 0..3{guard.check()?;}assert_eq!(calls.get(),3);
    let(c,r)=route(7,0)?;assert!(out.with_verified_bytes(&p,&f,&c,&r,7,section)??.contains("KEEP **** END"));Ok(())
}
#[test]
fn all_current_router_denials_and_changed_identity_stop_the_guard()->R{
    for mode in 1..=11{let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let out=manifest(&p,&f,&req(&s,&bytes,&f,false)?)?;
        let mut guard=out.current_commit_guard(&p,&f,||{let(c,r)=route(7,mode).map_err(|_|())?;Ok((c,r,7))});
        assert_eq!(guard.check(),Err(StoredCommitError::CurrentGuard));}Ok(())
}
#[test]
fn missing_snapshot_and_stale_clock_fail_closed_and_latch()->R{
    for mode in 0..2{let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let out=manifest(&p,&f,&req(&s,&bytes,&f,false)?)?;
        let calls=Cell::new(0);let mut guard=out.current_commit_guard(&p,&f,||{calls.set(calls.get()+1);if mode==0{return Err(());}
            let(c,r)=route(6,0).map_err(|_|())?;Ok((c,r,7))});
        assert_eq!(guard.check(),Err(StoredCommitError::CurrentGuard));assert_eq!(guard.check(),Err(StoredCommitError::CurrentGuard));assert_eq!(calls.get(),1);}Ok(())
}
#[test]
fn current_catalog_change_and_read_failure_cannot_be_restored_into_same_attempt()->R{
    for fail in [false,true]{let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let out=manifest(&p,&f,&req(&s,&bytes,&f,false)?)?;
        let saved=f.raw.borrow().clone();let mut guard=out.current_commit_guard(&p,&f,||{let(c,r)=route(7,0).map_err(|_|())?;Ok((c,r,7))});guard.check()?;
        if fail{f.fail.set(true);}else{f.raw.borrow_mut()[2]^=1;}
        assert_eq!(guard.check(),Err(StoredCommitError::CurrentGuard));f.fail.set(false);*f.raw.borrow_mut()=saved;
        assert_eq!(guard.check(),Err(StoredCommitError::CurrentGuard));}Ok(())
}
#[test]
fn original_acl_quarantine_and_aead_checks_remain_mandatory_at_commit_guard()->R{
    for mode in 0..3{let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let out=manifest(&p,&f,&req(&s,&bytes,&f,false)?)?;
        let mut guard=out.current_commit_guard(&p,&f,||{let(c,r)=route(7,0).map_err(|_|())?;Ok((c,r,7))});guard.check()?;
        match mode{0=>{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),7)?;},1=>{s.artifacts.quarantine(&s.owner,s.result,QuarantineReason::parse("FINAL_GUARD")?,7)?;},_=>s.blobs.tamper.store(true,Ordering::SeqCst)}
        assert_eq!(guard.check(),Err(StoredCommitError::CurrentGuard));}Ok(())
}
fn commit_case(mode:u8)->R{
    let bytes=raw("KEEP MARK END")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let out=manifest(&p,&f,&req(&s,&bytes,&f,false)?)?;
    let(c,r)=route(6,0)?;let root=tempfile::tempdir()?;let calls=Cell::new(0);
    out.with_verified_storage_preparation(&p,&f,&c,&r,6,|input|->R{
        let revision=rev::RevisionId::generate();let mut cas=StoredResultRevisionCas::bind(&s.artifacts,&s.revisions,&actor,&s.revision_context,
            input.commit_binding(rev::CommitId::generate(),revision)?,||7)?;
        cas.require_precommit_guard(Box::new(out.current_commit_guard(&p,&f,||{let call=calls.get()+1;calls.set(call);
            if mode==1&&call==1{return Err(());}if mode==2&&call==2{f.raw.borrow_mut()[2]^=1;}
            let(c,r)=route(7,if mode==3&&call==2{11}else{0}).map_err(|_|())?;Ok((c,r,7))})))?;
        // A second installation must not replace the first guard or erase retained evidence.
        assert_eq!(cas.require_precommit_guard(Box::new(||Ok(()))),Err(StoredCommitError::CurrentGuard));
        let mut validator=input.output_validator();let mut tx=WorkspaceTransaction::create(root.path().join("guarded"),input.manifest().clone(),Default::default())?;
        let result=tx.execute_bytes(input.source_bytes(),input.output_bytes(),&mut validator,&mut cas,&mut FaultPlan::none());
        if mode==0{assert!(result.is_ok());assert_eq!(calls.get(),2);assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?.revision_id(),Some(revision));}
        else{assert!(result.is_err());assert_eq!(cas.error(),Some(StoredCommitError::CurrentGuard));assert!(cas.service_receipt().is_none());
            assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);
            if mode==1{assert_eq!(calls.get(),1);assert!(cas.retained_result().is_none());assert!(cas.retained_intent().is_none());}
            else{assert_eq!(calls.get(),2);for retained in [cas.retained_result(),cas.retained_intent(),cas.retained_precommit()]{
                let descriptor=retained.ok_or("original recovery artifact")?;assert!(!s.artifacts.download(&actor,descriptor.artifact_id,8)?.is_empty());}}}
        assert_eq!(cas.require_precommit_guard(Box::new(||Ok(()))),Err(StoredCommitError::CurrentGuard));Ok(())
    })??;assert_eq!(s.artifacts.download(&s.reader,s.result,8)?,bytes);Ok(())
}
#[test]fn original_hwpx_transaction_commits_only_after_both_fresh_checks()->R{commit_case(0)}
#[test]fn pre_ingest_guard_rejection_keeps_head_and_skips_result_storage()->R{commit_case(1)}
#[test]fn final_catalog_drift_retains_recovery_artifacts_without_head_commit()->R{commit_case(2)}
#[test]fn final_registry_change_retains_recovery_artifacts_without_head_commit()->R{commit_case(3)}
#[test]
fn passing_guard_still_cannot_open_the_unqualified_product_route()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let out=manifest(&p,&f,&req(&s,&bytes,&f,false)?)?;
    let mut guard=out.current_commit_guard(&p,&f,||{let(c,r)=route(7,0).map_err(|_|())?;Ok((c,r,7))});guard.check()?;
    let(c,r)=route(7,0)?;assert!(out.require_current_product_route(&p,&f,&c,&r,7).is_err());Ok(())
}
