//! Synthetic route fixtures exercise real multi-part plan-to-manifest data, not trust qualification.
use super::*;
#[path="sort_groups_plan_fixture.rs"]mod multigroup;
use multigroup::{source,request};
#[test]
fn manifest_groups_uses_all_actual_multi_part_routes_source_and_original_denial()->TestResult{
    let bytes=source()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=request(&s,&bytes)?;
    let compiled=Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,Limits::standard()?,4)?;
    assert_eq!(compiled.compiled().operations().len(),4);assert_manifest(&s,&p,&bytes,compiled)
}
#[test]
fn manifest_groups_current_support_policy_protection_health_remain_required()->TestResult{
    let bytes=source()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=request(&s,&bytes)?;
    let compiled=Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,Limits::standard()?,4)?;let cap=compiled.receipt().capability_id;
    let(context,catalog)=routing(cap,5,0)?;let out=compiled.prepare_execution_manifest(&p,&context,&catalog,transaction("groups-held")?,5)?;
    for mode in[1,4,5,6,9,10]{let(context,catalog)=routing(cap,6,mode)?;let called=Cell::new(false);
        assert!(matches!(out.with_verified_bytes(&p,&context,&catalog,6,|_|called.set(true)),Err(E::Route(_))));assert!(!called.get());}
    let(context,catalog)=routing(cap,6,0)?;out.verify(&p,&context,&catalog,6)?;Ok(())
}
#[test]
fn manifest_groups_observed_document_signal_cannot_be_overridden_by_route_fixture()->TestResult{
    use hwpx_package::document_import::protection::SourceProtectionObservationError as PE;
    let bytes=security::header_signal(&source()?,"protect","0")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=request(&s,&bytes)?;
    let compiled=Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,Limits::standard()?,4)?;let(context,catalog)=routing(compiled.receipt().capability_id,5,0)?;
    assert!(matches!(compiled.prepare_execution_manifest(&p,&context,&catalog,transaction("groups-protection")?,5),Err(E::SourceProtection(PE::ObservedDocumentSignal))));
    assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);Ok(())
}
#[test]
fn manifest_groups_last_head_races_block_verify_and_byte_delivery()->TestResult{
    for delivery in[false,true]{let bytes=source()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=request(&s,&bytes)?;
        let compiled=Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,Limits::standard()?,4)?;let cap=compiled.receipt().capability_id;
        let(context,catalog)=routing(cap,5,0)?;let out=compiled.prepare_execution_manifest(&p,&context,&catalog,transaction("groups-head")?,5)?;
        let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,
            ContentDigest::of(b"group manifest race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation"),ContentDigest::of(b"transaction"))?;
        let b=rev::RevisionService::new(BoundaryRepo{inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});
        let bound=StoredFormProvider::bind(&s.artifacts,&b,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;let(context,catalog)=routing(cap,6,0)?;
        if delivery{out.with_verified_bytes(&bound,&context,&catalog,6,|_|())?;}else{out.verify(&bound,&context,&catalog,6)?;}
        let count=b.repository().calls.load(Ordering::SeqCst);assert!(count>=4);b.repository().calls.store(0,Ordering::SeqCst);b.repository().trigger.store(count,Ordering::SeqCst);let called=Cell::new(false);
        if delivery{assert!(out.with_verified_bytes(&bound,&context,&catalog,6,|_|called.set(true)).is_err());}else{assert!(out.verify(&bound,&context,&catalog,6).is_err());}
        assert!(!called.get());assert_eq!(b.repository().calls.load(Ordering::SeqCst),count);
    }Ok(())
}
