// Current access/config and retained matched masks. Synthetic repositories only; no actual database or Native.
mod product{include!("personal_info_catalog_mask_product.rs");}
use super::*;
use hwpx_agent_cli::form_stored_provider::actual_import::source_search::personal_info_catalog::mask::{
    StoredPersonalInfoCatalogMaskError as ME,STORED_PERSONAL_INFO_CATALOG_MASK_PREVIEW_PROFILE};
use hwpx_package::document_import::search::replacement::atoms::personal_info::SourcePersonalInfoMaskPolicy as Mask;
macro_rules! mask_candidate{($p:expr,$s:expr,$f:expr)=>{$p.import_actual_forms($s.head,4)?.into_personal_info_catalog_mask_candidate(
    $p,$f,sha($f),&FAMILIES,Scope::Document,policy(),Mask::PerOriginalScalarPreserveSlots,Default::default(),Default::default(),4)}}

#[test]
fn all_sixty_four_patterns_bind_a_mask_that_preserves_nonmatching_text()->R{
    let bytes=raw("KEEP MARK MARK END")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let c=mask_candidate!(&p,&s,&f)?;
    assert_eq!(f.reads.get(),2);assert_eq!(c.receipt().output.catalog.total_patterns,64);assert_eq!(c.receipt().output.selected_patterns,64);assert_eq!(c.receipt().output.matched_formats,2);
    assert!(c.with_verified_bytes(&p,&f,5,section)??.contains("KEEP **** **** END"));assert_eq!(f.reads.get(),4);Ok(())
}
#[test]
fn current_stored_candidate_matches_the_original_public_source_lowerer()->R{
    let bytes=raw("KEEP MARK END")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");
    let source=p.import_actual_forms(s.head,4)?;let catalog=Catalog::parse_utf16le(&f.raw.borrow(),sha(&f))?;
    let direct=source.imported().lower_personal_info_catalog_mask_candidate(&bytes,&catalog,&FAMILIES,Scope::Document,policy(),Mask::PerOriginalScalarPreserveSlots,Default::default(),Default::default())?;
    let c=mask_candidate!(&p,&s,&f)?;assert_eq!(&c.receipt().output,direct.receipt());
    assert_eq!(c.with_verified_bytes(&p,&f,5,<[u8]>::to_vec)?,direct.with_verified_bytes(<[u8]>::to_vec)?);Ok(())
}
#[test]
fn configuration_change_during_preparation_rejects_before_returning_a_candidate()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");f.replace_at.set(2);
    assert!(mask_candidate!(&p,&s,&f).is_err());assert_eq!(f.reads.get(),2);Ok(())
}
#[test]
fn retained_candidate_rejects_changed_current_catalog_without_delivering_bytes()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let c=mask_candidate!(&p,&s,&f)?;
    f.raw.borrow_mut()[2]^=1;let called=Cell::new(false);assert!(c.with_verified_bytes(&p,&f,5,|_|called.set(true)).is_err());assert!(!called.get());Ok(())
}
#[test]
fn consumer_final_catalog_race_blocks_bytes_metadata_and_verify()->R{
    for mode in 0..3{let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let c=mask_candidate!(&p,&s,&f)?;
        f.replace_at.set(f.reads.get()+2);let called=Cell::new(false);let failed=match mode{
            0=>c.with_verified_bytes(&p,&f,5,|_|called.set(true)).is_err(),1=>c.with_verified_json(&p,&f,5,|_|called.set(true)).is_err(),_=>c.verify(&p,&f,5).is_err()};
        assert!(failed&&!called.get());}Ok(())
}
#[test]
fn failed_current_config_read_never_falls_back_to_retained_config_or_pattern_data()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let c=mask_candidate!(&p,&s,&f)?;
    f.fail.set(true);assert!(c.verify(&p,&f,5).is_err());assert!(mask_candidate!(&p,&s,&f).is_err());Ok(())
}
#[test]
fn document_write_is_required_before_any_initial_or_retained_catalog_read()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let c=mask_candidate!(&p,&s,&f)?;let reader=s.provider()?;
    let count=f.reads.get();assert!(matches!(mask_candidate!(&reader,&s,&f),Err(ME::Permission)));assert!(matches!(c.verify(&reader,&f,5),Err(ME::Permission)));assert_eq!(f.reads.get(),count);Ok(())
}
#[test]
fn current_acl_revocation_and_regrant_apply_to_retained_candidate_deliveries()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let c=mask_candidate!(&p,&s,&f)?;
    s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;let called=Cell::new(false);
    assert!(c.with_verified_bytes(&p,&f,6,|_|called.set(true)).is_err());assert!(c.with_verified_json(&p,&f,6,|_|called.set(true)).is_err());assert!(!called.get());
    s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),7)?;c.verify(&p,&f,8)?;Ok(())
}
#[test]
fn preview_current_acl_revocation_rejects_metadata_delivery()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let preview=mask_candidate!(&p,&s,&f)?.into_preview()?;
    s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;let called=Cell::new(false);
    assert!(preview.with_verified_json(&p,&f,6,|_|called.set(true)).is_err());assert!(!called.get());Ok(())
}
#[test]
fn foreign_document_branch_project_subject_or_tenant_cannot_deliver_retained_masks()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let c=mask_candidate!(&p,&s,&f)?;
    let called=Cell::new(false);for mode in 0..5{let tenant=if mode==4{TenantId::new(Uuid::from_u128(993))?}else{s.reader.tenant_id()};
        let subject=if mode==3{SubjectDigest::from_authenticated_subject("foreign-catalog-mask")?}else{s.reader.subject()};let actor=RequestContext::new(tenant,subject,[AuthScope::DocumentRead,AuthScope::DocumentWrite]);
        let context=rev::RevisionRequestContext::new(tenant,subject);let project=if mode==2{rev::ProjectId::parse("prj_70000000000000000000000000000003")?}else{s.project};
        let branch=if mode==1{rev::BranchId::parse("brn_70000000000000000000000000000003")?}else{s.branch};
        let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&context,project,branch,DocumentId::parse(if mode==0{"foreign-mask-document"}else{"actual-form-document"})?)?;
        assert!(c.with_verified_bytes(&other,&f,5,|_|called.set(true)).is_err());}assert!(!called.get());Ok(())
}
#[test]
fn quarantine_or_aead_tamper_blocks_both_candidate_and_preview()->R{
    for tamper in [false,true]{let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");
        let c=mask_candidate!(&p,&s,&f)?;let preview=mask_candidate!(&p,&s,&f)?.into_preview()?;
        if tamper{s.blobs.tamper.store(true,Ordering::SeqCst);}else{s.artifacts.quarantine(&s.owner,s.result,QuarantineReason::parse("CATALOG_MASK_TEST")?,5)?;}
        let called=Cell::new(false);assert!(c.with_verified_bytes(&p,&f,6,|_|called.set(true)).is_err());assert!(preview.with_verified_json(&p,&f,6,|_|called.set(true)).is_err());assert!(!called.get());}Ok(())
}
fn mask_head_race(stage:usize)->R{
    let bytes=raw("MARK MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");
    let c=mask_candidate!(&p,&s,&f)?;let preview=mask_candidate!(&p,&s,&f)?.into_preview()?;
    let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,
        ContentDigest::of(b"catalog-mask-head-race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation fixture"),ContentDigest::of(b"transaction fixture"))?;
    let repo=rev::RevisionService::new(BoundaryRepo{inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});
    let bound=StoredFormProvider::bind(&s.artifacts,&repo,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
    match stage{0=>{mask_candidate!(&bound,&s,&f)?;},1=>{c.with_verified_bytes(&bound,&f,5,|_|())?;},2=>{c.with_verified_json(&bound,&f,5,|_|())?;},_=>{preview.with_verified_json(&bound,&f,5,|_|())?;}}
    let count=repo.repository().calls.load(Ordering::SeqCst);assert!(count>=4);repo.repository().calls.store(0,Ordering::SeqCst);repo.repository().trigger.store(count,Ordering::SeqCst);let called=Cell::new(false);
    match stage{0=>assert!(mask_candidate!(&bound,&s,&f).is_err()),1=>assert!(c.with_verified_bytes(&bound,&f,6,|_|called.set(true)).is_err()),
        2=>assert!(c.with_verified_json(&bound,&f,6,|_|called.set(true)).is_err()),_=>assert!(preview.with_verified_json(&bound,&f,6,|_|called.set(true)).is_err())}
    assert!(!called.get());assert_eq!(repo.repository().calls.load(Ordering::SeqCst),count);Ok(())
}
#[test]fn preparation_final_head_race_rejects()->R{mask_head_race(0)}
#[test]fn retained_byte_consumer_final_head_race_rejects()->R{mask_head_race(1)}
#[test]fn retained_metadata_consumer_final_head_race_rejects()->R{mask_head_race(2)}
#[test]fn preview_metadata_consumer_final_head_race_rejects()->R{mask_head_race(3)}
#[test]
fn source_head_ingest_count_and_original_bytes_are_not_modified_by_mask_preparation()->R{
    let bytes=raw("KEEP MARK END")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let c=mask_candidate!(&p,&s,&f)?;
    c.verify(&p,&f,5)?;assert_eq!(s.artifacts.download(&s.reader,s.result,6)?,bytes);assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);
    assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);assert!(matches!(c.require_current_product_route(&p,&f,6),Err(ME::RouteUnqualified)));Ok(())
}
#[test]
fn metadata_and_debug_never_disclose_pattern_bodies_or_matched_private_text()->R{
    let bytes=raw("PRIVATE-CATALOG-MASK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("PRIVATE-CATALOG-MASK");let c=mask_candidate!(&p,&s,&f)?;
    for text in [format!("{c:?}{:?}",c.receipt()),c.with_verified_json(&p,&f,5,|b|String::from_utf8_lossy(b).into_owned())?]{
        for private in ["PRIVATE-","NEVERF","pattern0=","source_span_sha256","matched_value_sha256"]{assert!(!text.contains(private));}}Ok(())
}
#[test]
fn preview_retains_only_predicted_metadata_and_never_grants_an_execution_route()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let preview=mask_candidate!(&p,&s,&f)?.into_preview()?;
    assert_eq!(preview.receipt().profile,STORED_PERSONAL_INFO_CATALOG_MASK_PREVIEW_PROFILE);assert!(preview.receipt().preview_only);
    assert!(!preview.receipt().candidate_output_retained&&!preview.receipt().issuer_execution_publication_authority);
    let value:Value=preview.with_verified_json(&p,&f,5,|b|serde_json::from_slice(b))??;assert_eq!(value["preview_only"],true);
    assert!(matches!(preview.require_current_product_route(&p,&f,5),Err(ME::RouteUnqualified)));Ok(())
}
#[test]
fn wrong_catalog_digest_selection_and_server_caps_reject_without_prepared_bytes()->R{
    let bytes=raw("MARK MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");
    assert!(p.import_actual_forms(s.head,4)?.into_personal_info_catalog_mask_candidate(&p,&f,[0;32],&FAMILIES,Scope::Document,policy(),Mask::PerOriginalScalarPreserveSlots,Default::default(),Default::default(),4).is_err());
    for families in [vec![],vec![F::Telephone,F::Telephone],vec![F::UserDefined]]{
        assert!(p.import_actual_forms(s.head,4)?.into_personal_info_catalog_mask_candidate(&p,&f,sha(&f),&families,Scope::Document,policy(),Mask::PerOriginalScalarPreserveSlots,Default::default(),Default::default(),4).is_err());}
    for config in [Config{matches:1,..Default::default()},Config{pattern_bytes:1,..Default::default()},Config{result_bytes:1,..Default::default()}]{
        assert!(p.import_actual_forms(s.head,4)?.into_personal_info_catalog_mask_candidate(&p,&f,sha(&f),&FAMILIES,Scope::Document,policy(),Mask::PerOriginalScalarPreserveSlots,SourceSearchLimits::new(config)?,Default::default(),4).is_err());}Ok(())
}
#[test]
fn retained_deliveries_recheck_config_without_changing_candidate_receipt_or_output()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let c=mask_candidate!(&p,&s,&f)?;
    let original=c.receipt().clone();let before=f.reads.get();assert_eq!(c.verify(&p,&f,5)?,original);assert_eq!(f.reads.get(),before+2);
    let a=c.with_verified_bytes(&p,&f,5,<[u8]>::to_vec)?;let b=c.with_verified_bytes(&p,&f,6,<[u8]>::to_vec)?;assert_eq!(a,b);assert_eq!(c.receipt(),&original);Ok(())
}
