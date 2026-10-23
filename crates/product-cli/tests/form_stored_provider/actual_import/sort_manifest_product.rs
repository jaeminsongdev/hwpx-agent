//! New sort manifest data path with synthetic route fixtures only; never actual target/registry/Native qualification.
use super::*;
#[allow(dead_code)]#[path="../../../../hwpx-package/tests/support/source_protection_fixture.rs"]mod security;
fn source()->Result<Vec<u8>,Box<dyn Error>>{definition::package(&(para(1,"Z-PRIVATE")+&para(2,"B")+&para(3,"A")))}
fn request(s:&StoredFixture,bytes:&[u8])->Result<Value,Box<dyn Error>>{let mut v=super::super::super::request(s,bytes)?;
    v["schema_version"]=json!(hwpx_agent_cli::form_product_request::stored_literal_replacement::sort::PARAGRAPH_SORT_PRODUCT_REQUEST_SCHEMA);
    v["operation"]=json!({"kind":"sort_sibling_paragraphs","sort_spec":{"direction":"ascending","comparison":"nfc_unicode_scalar_lexicographic","max_comparison_bytes":1048576},"review_policy":policy(false,false)});Ok(v)}
#[test]
fn manifest_sort_uses_actual_compiled_plan_source_routes_and_original_denial()->TestResult{
    let bytes=source()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=request(&s,&bytes)?;
    let compiled=Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,Limits::standard()?,4)?;
    assert_eq!(compiled.compiled().operations().len(),2);assert_manifest(&s,&p,&bytes,compiled)
}
#[test]
fn manifest_sort_held_routes_still_require_current_support_policy_protection_and_health()->TestResult{
    let bytes=source()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=request(&s,&bytes)?;
    let compiled=Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,Limits::standard()?,4)?;let cap=compiled.receipt().capability_id;
    let(context,catalog)=routing(cap,5,0)?;let out=compiled.prepare_execution_manifest(&p,&context,&catalog,transaction("sort-held")?,5)?;
    for mode in[1,4,5,6,9,10]{let(context,catalog)=routing(cap,6,mode)?;let called=Cell::new(false);
        assert!(matches!(out.with_verified_bytes(&p,&context,&catalog,6,|_|called.set(true)),Err(E::Route(_))));assert!(!called.get());}
    let(context,catalog)=routing(cap,6,0)?;out.verify(&p,&context,&catalog,6)?;Ok(())
}
#[test]
fn manifest_sort_document_protection_signal_cannot_be_overridden_by_unprotected_context()->TestResult{
    use hwpx_package::document_import::protection::SourceProtectionObservationError as PE;
    let bytes=security::header_signal(&source()?,"protect","0")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=request(&s,&bytes)?;
    let compiled=Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,Limits::standard()?,4)?;let(context,catalog)=routing(compiled.receipt().capability_id,5,0)?;
    assert!(matches!(compiled.prepare_execution_manifest(&p,&context,&catalog,transaction("sort-protection")?,5),Err(E::SourceProtection(PE::ObservedDocumentSignal))));
    assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);Ok(())
}
#[test]
fn manifest_sort_last_current_head_races_block_verify_and_byte_consumer()->TestResult{
    for delivery in [false,true]{let bytes=source()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=request(&s,&bytes)?;
        let compiled=Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,Limits::standard()?,4)?;let cap=compiled.receipt().capability_id;
        let(context,catalog)=routing(cap,5,0)?;let out=compiled.prepare_execution_manifest(&p,&context,&catalog,transaction("sort-head")?,5)?;
        let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,
            ContentDigest::of(b"sort manifest race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation"),ContentDigest::of(b"transaction"))?;
        let b=rev::RevisionService::new(BoundaryRepo{inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});
        let bound=StoredFormProvider::bind(&s.artifacts,&b,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
        let(context,catalog)=routing(cap,6,0)?;
        if delivery{out.with_verified_bytes(&bound,&context,&catalog,6,|_|())?;}else{out.verify(&bound,&context,&catalog,6)?;}
        let count=b.repository().calls.load(Ordering::SeqCst);assert!(count>=4);b.repository().calls.store(0,Ordering::SeqCst);b.repository().trigger.store(count,Ordering::SeqCst);let called=Cell::new(false);
        if delivery{assert!(out.with_verified_bytes(&bound,&context,&catalog,6,|_|called.set(true)).is_err());}else{assert!(out.verify(&bound,&context,&catalog,6).is_err());}
        assert!(!called.get());assert_eq!(b.repository().calls.load(Ordering::SeqCst),count);
    }Ok(())
}
#[path="sort_groups_manifest_product.rs"]mod groups_v1;
