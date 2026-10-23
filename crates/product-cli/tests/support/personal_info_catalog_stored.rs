//! Complete synthetic configuration -> current stored document. No installed/private configuration or Native required.
use super::*;
use std::cell::RefCell;
use hwpx_agent_cli::form_stored_provider::actual_import::source_search::personal_info_catalog::{CurrentPersonalInfoCatalogSource as CatalogSource,
    PersonalInfoCatalogSourceError as ReadError,StoredPersonalInfoCatalogError as CE,PreparedStoredPersonalInfoCatalog as Found};
use hwpx_package::document_import::search::{personal_info::catalog::{SourcePersonalInfoCatalog as Catalog,PersonalInfoCatalogFamily as F},
    navigation::{SourceSearchNavigationRequest as Next,SourceSearchDirection as Direction}};
const NAMES:[&str;11]=["TELEPHONE","RESIDENT","FOREIGNER","EMAIL","ACCOUNT","LICENSE","PASSPORT","CREDIT","IPADDRESS","BIRTHDAY","USERDEF"];
const FAMILIES:[F;11]=[F::Telephone,F::ResidentRegistration,F::ForeignRegistration,F::Email,F::Account,F::DriverLicense,F::Passport,F::CreditCard,F::IpAddress,F::BirthDate,F::UserDefined];
struct Feed{raw:RefCell<Vec<u8>>,reads:Cell<usize>,replace_at:Cell<usize>,replacement:RefCell<Vec<u8>>,fail:Cell<bool>}
impl CatalogSource for Feed{
    fn read_current_catalog(&self)->Result<Vec<u8>,ReadError>{
        let n=self.reads.get()+1;self.reads.set(n);if self.fail.get(){return Err(ReadError);}
        Ok(if n==self.replace_at.get(){self.replacement.borrow().clone()}else{self.raw.borrow().clone()})
    }
}
fn encoded(text:&str)->Vec<u8>{let mut out=vec![0xff,0xfe];for u in text.encode_utf16(){out.extend_from_slice(&u.to_le_bytes());}out}
fn feed(pattern:&str)->Feed{
    let counts=[8,1,1,6,35,1,2,1,1,8,0];let text=NAMES.iter().enumerate().map(|(i,n)|{
        let rows=(0..counts[i]).map(|j|format!("pattern{j}={}\r\n",if i==0&&j==0{pattern.to_owned()}else{format!("NEVERF{i}P{j}END")})).collect::<String>();
        format!("[{n}]\r\n{rows}")}).collect::<String>();
    Feed{raw:RefCell::new(encoded(&text)),reads:Cell::new(0),replace_at:Cell::new(usize::MAX),replacement:RefCell::new(vec![0]),fail:Cell::new(false)}
}
fn sha(feed:&Feed)->[u8;32]{*ContentDigest::of(&feed.raw.borrow()).as_bytes()}
fn nav()->Next{Next{direction:Direction::Forward,wrap:false,cursor:None}}
macro_rules! detect{($p:expr,$s:expr,$f:expr)=>{$p.import_actual_forms($s.head,4)?.into_personal_info_catalog($p,$f,sha($f),&FAMILIES,Scope::Document,policy(),Default::default(),4)}}
fn value(found:&Found,p:&Provider<'_>,f:&Feed)->Result<Value,Box<dyn Error>>{Ok(found.with_verified_json(p,f,5,|b|serde_json::from_slice(b))??)}
#[test]
fn complete_sixty_four_patterns_and_full_source_provenance_are_not_truncated_to_legacy_sixteen()->R{
    let bytes=raw("KEEP MARK MARK END")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let found=detect!(&p,&s,&f)?;
    assert_eq!(f.reads.get(),2);let r=found.receipt();assert_eq!(r.catalog.total_patterns,64);assert_eq!(r.selected_patterns,64);assert_eq!(r.catalog.source_section_order.len(),11);
    assert_eq!(r.catalog.source_sha256,sha(&f));assert_eq!(r.matched_formats,2);assert_eq!(r.index.source_package_sha256,*ContentDigest::of(&bytes).as_bytes());
    assert!(!r.catalog.installed_vendor_authenticity_or_native_semantics_qualified&&!r.native_format_identity_or_execution_qualified&&!r.whole_package_personal_data_removed);
    assert_eq!(value(&found,&p,&f)?["result"]["selected_patterns"],64);Ok(())
}
#[test]
fn stored_and_source_share_the_same_catalog_result_and_matching_policy()->R{
    let bytes=raw("MARK MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let found=detect!(&p,&s,&f)?;
    let imported=p.import_actual_forms(s.head,4)?;let proof=imported.imported().reconstruct_source_for_verification(&bytes)?;
    let catalog=Catalog::parse_utf16le(&f.raw.borrow(),sha(&f))?;let policy=catalog.prepare(&FAMILIES,Default::default())?;
    let direct=proof.source_review_scope_index(imported.imported(),Default::default())?.find_personal_info_catalog(&policy,Scope::Document,super::policy())?;
    assert_eq!(value(&found,&p,&f)?["result"],serde_json::from_slice::<Value>(&direct.canonical_json()?)?);Ok(())
}
#[test]
fn changed_catalog_blocks_verify_metadata_navigation_and_selection_without_callbacks()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let found=detect!(&p,&s,&f)?;
    let original=f.raw.borrow().clone();f.raw.borrow_mut()[8]^=1;let called=Cell::new(false);
    assert!(matches!(found.verify(&p,&f,5),Err(CE::Binding)));assert!(found.with_verified_json(&p,&f,5,|_|called.set(true)).is_err());
    assert!(found.with_navigation_verified_json(&p,&f,&nav(),[1;32],5,|_|called.set(true)).is_err());
    assert!(found.with_selection_verified_json(&p,&f,0,5,|_|called.set(true)).is_err());assert!(!called.get());
    *f.raw.borrow_mut()=original;found.verify(&p,&f,6)?;Ok(())
}
#[test]
fn preparation_final_catalog_race_rejects_after_scan()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");f.replace_at.set(2);
    assert!(detect!(&p,&s,&f).is_err());assert_eq!(f.reads.get(),2);Ok(())
}
#[test]
fn metadata_navigation_and_selection_final_catalog_races_never_call_consumer()->R{
    for mode in 0..3{let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let found=detect!(&p,&s,&f)?;
        f.replace_at.set(f.reads.get()+2);let called=Cell::new(false);let error=match mode{0=>found.with_verified_json(&p,&f,5,|_|called.set(true)),
            1=>found.with_navigation_verified_json(&p,&f,&nav(),[1;32],5,|_|called.set(true)),_=>found.with_selection_verified_json(&p,&f,0,5,|_|called.set(true))};
        assert!(error.is_err());assert!(!called.get());}Ok(())
}
#[test]
fn source_read_errors_and_empty_or_oversize_catalogs_are_not_cached_success()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let found=detect!(&p,&s,&f)?;
    f.fail.set(true);assert!(matches!(found.verify(&p,&f,5),Err(CE::CurrentCatalog(_))));f.fail.set(false);
    for content in [Vec::new(),vec![0;64*1024+1]]{*f.raw.borrow_mut()=content;assert!(matches!(found.verify(&p,&f,5),Err(CE::Limit)));assert!(detect!(&p,&s,&f).is_err());}Ok(())
}
#[test]
fn document_write_is_required_before_initial_or_retained_catalog_reads()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let found=detect!(&p,&s,&f)?;let reader=s.provider()?;
    let before=f.reads.get();let called=Cell::new(false);assert!(matches!(detect!(&reader,&s,&f),Err(CE::Permission)));assert!(matches!(found.verify(&reader,&f,5),Err(CE::Permission)));
    assert!(found.with_verified_json(&reader,&f,5,|_|called.set(true)).is_err());assert!(found.with_selection_verified_json(&reader,&f,0,5,|_|called.set(true)).is_err());
    assert_eq!(f.reads.get(),before);assert!(!called.get());Ok(())
}
#[test]
fn current_acl_revocation_and_regrant_apply_to_all_retained_deliveries()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let found=detect!(&p,&s,&f)?;
    s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;let called=Cell::new(false);
    assert!(found.verify(&p,&f,6).is_err());assert!(found.with_verified_json(&p,&f,6,|_|called.set(true)).is_err());
    assert!(found.with_navigation_verified_json(&p,&f,&nav(),[1;32],6,|_|called.set(true)).is_err());assert!(found.with_selection_verified_json(&p,&f,0,6,|_|called.set(true)).is_err());assert!(!called.get());
    s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),7)?;found.verify(&p,&f,8)?;Ok(())
}
#[test]
fn foreign_tenant_subject_project_branch_or_document_cannot_deliver_positions()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let found=detect!(&p,&s,&f)?;
    let called=Cell::new(false);for mode in 0..5{let tenant=if mode==4{TenantId::new(Uuid::from_u128(993))?}else{s.reader.tenant_id()};
        let subject=if mode==3{SubjectDigest::from_authenticated_subject("foreign-catalog")?}else{s.reader.subject()};let actor=RequestContext::new(tenant,subject,[AuthScope::DocumentRead,AuthScope::DocumentWrite]);
        let context=rev::RevisionRequestContext::new(tenant,subject);let project=if mode==2{rev::ProjectId::parse("prj_70000000000000000000000000000003")?}else{s.project};
        let branch=if mode==1{rev::BranchId::parse("brn_70000000000000000000000000000003")?}else{s.branch};
        let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&context,project,branch,DocumentId::parse(if mode==0{"foreign-document"}else{"actual-form-document"})?)?;
        assert!(found.verify(&other,&f,5).is_err());assert!(found.with_selection_verified_json(&other,&f,0,5,|_|called.set(true)).is_err());}assert!(!called.get());Ok(())
}
#[test]
fn quarantine_and_aead_integrity_failures_block_retained_catalog_positions()->R{
    for tamper in [false,true]{let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let found=detect!(&p,&s,&f)?;
        if tamper{s.blobs.tamper.store(true,Ordering::SeqCst);}else{s.artifacts.quarantine(&s.owner,s.result,QuarantineReason::parse("CATALOG_TEST")?,5)?;}
        let called=Cell::new(false);assert!(found.verify(&p,&f,6).is_err());assert!(found.with_selection_verified_json(&p,&f,0,6,|_|called.set(true)).is_err());assert!(!called.get());}Ok(())
}
#[test]
fn retained_navigation_uses_current_config_and_preserves_cursor_binding()->R{
    let bytes=raw("MARK MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let found=detect!(&p,&s,&f)?;
    let a=found.with_navigation_verified_json(&p,&f,&nav(),[1;32],5,|b|serde_json::from_slice::<Value>(b))??;assert_eq!(a["result"]["match_index"],0);
    let next:Next=serde_json::from_value(json!({"direction":"forward","wrap":false,"cursor":a["result"]["cursor"]}))?;
    let b=found.with_navigation_verified_json(&p,&f,&next,[1;32],5,|b|serde_json::from_slice::<Value>(b))??;assert_eq!(b["result"]["match_index"],1);
    assert!(found.with_navigation_verified_json(&p,&f,&next,[2;32],5,|_|()).is_err());Ok(())
}
#[test]
fn exact_original_selection_feeds_existing_mask_with_no_implicit_mutation()->R{
    let bytes=raw("KEEP MARK TAIL")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let found=detect!(&p,&s,&f)?;
    let v=found.with_selection_verified_json(&p,&f,0,5,|b|serde_json::from_slice::<Value>(b))??;let c=&v["result"];let sha:[u8;32]=serde_json::from_value(c["index_sha256"].clone())?;
    let mut req=request(&s,&bytes,false)?;req["selector"]["scope"]=json!("selection");req["selector"]["range"]=json!({"coordinate_space":"index_nfc_unicode_scalars","index_sha256":hex::encode(sha),"start":c["start"],"end":c["end"]});
    let masked=Product::prepare_json(&p,&wire(&req)?,Default::default(),Default::default(),5)?;assert!(masked.with_verified_bytes(&p,6,section)??.contains("KEEP **** TAIL"));
    assert_eq!(s.artifacts.download(&s.reader,s.result,6)?,bytes);assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);Ok(())
}
#[test]
fn empty_user_defined_selection_is_empty_and_never_a_zero_width_regex()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");
    let found=p.import_actual_forms(s.head,4)?.into_personal_info_catalog(&p,&f,sha(&f),&[F::UserDefined],Scope::Document,policy(),Default::default(),4)?;
    assert_eq!(found.receipt().matched_formats,0);assert_eq!(found.receipt().selected_patterns,0);assert!(found.with_selection_verified_json(&p,&f,0,5,|_|()).is_err());Ok(())
}
#[test]
fn whole_metadata_exact_byte_limit_and_one_less_are_enforced()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let found=detect!(&p,&s,&f)?;let n=found.with_verified_json(&p,&f,5,<[u8]>::len)?;
    let exact=p.import_actual_forms(s.head,4)?.into_personal_info_catalog(&p,&f,sha(&f),&FAMILIES,Scope::Document,policy(),SourceSearchLimits::new(Config{result_bytes:n,..Default::default()})?,4)?;
    assert_eq!(exact.with_verified_json(&p,&f,5,<[u8]>::len)?,n);assert!(p.import_actual_forms(s.head,4)?.into_personal_info_catalog(&p,&f,sha(&f),&FAMILIES,Scope::Document,policy(),SourceSearchLimits::new(Config{result_bytes:n-1,..Default::default()})?,4).is_err());Ok(())
}
#[test]
fn metadata_and_debug_never_disclose_pattern_body_or_matched_text()->R{
    let bytes=raw("PRIVATE-CATALOG-MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("PRIVATE-CATALOG-MARK");let found=detect!(&p,&s,&f)?;
    for text in [format!("{found:?}{:?}",found.receipt()),found.with_verified_json(&p,&f,5,|b|String::from_utf8_lossy(b).into_owned())?,
        found.with_selection_verified_json(&p,&f,0,5,|b|String::from_utf8_lossy(b).into_owned())?]{assert!(!text.contains("PRIVATE-")&&!text.contains("NEVERF")&&!text.contains("pattern0=")&&!text.contains("matched_value_sha256"));}Ok(())
}
#[test]
fn invalid_catalog_selection_wrong_digest_and_server_caps_fail_closed()->R{
    let bytes=raw("MARK MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");
    assert!(p.import_actual_forms(s.head,4)?.into_personal_info_catalog(&p,&f,[0;32],&FAMILIES,Scope::Document,policy(),Default::default(),4).is_err());
    for families in [vec![],vec![F::Telephone,F::Telephone]]{assert!(p.import_actual_forms(s.head,4)?.into_personal_info_catalog(&p,&f,sha(&f),&families,Scope::Document,policy(),Default::default(),4).is_err());}
    for config in [Config{matches:1,..Default::default()},Config{pattern_bytes:1,..Default::default()},Config{result_bytes:1,..Default::default()}]{
        assert!(p.import_actual_forms(s.head,4)?.into_personal_info_catalog(&p,&f,sha(&f),&FAMILIES,Scope::Document,policy(),SourceSearchLimits::new(config)?,4).is_err());}Ok(())
}
#[test]
fn source_kind_and_unverified_scanner_do_not_become_current_catalog_results()->R{
    let bytes=raw("MARK")?;for(kind,unverified)in [(ArtifactKind::Source,false),(ArtifactKind::Result,true)]{let s=StoredFixture::new(&bytes,kind,unverified)?;writer!(s,actor,p);let f=feed("MARK");
        let result=p.import_actual_forms(s.head,4).map_err(CE::from).and_then(|source|source.into_personal_info_catalog(&p,&f,sha(&f),&FAMILIES,Scope::Document,policy(),Default::default(),4));
        assert!(result.is_err());}Ok(())
}
#[test]
fn readonly_result_keeps_original_source_head_ingest_count_and_unqualified_route()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let found=detect!(&p,&s,&f)?;
    assert!(matches!(found.require_current_product_route(&p,&f,5),Err(CE::RouteUnqualified)));assert_eq!(s.artifacts.download(&s.reader,s.result,5)?,bytes);
    assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);Ok(())
}
fn race(stage:usize)->R{
    let bytes=raw("MARK MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let f=feed("MARK");let found=detect!(&p,&s,&f)?;
    let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,
        ContentDigest::of(b"catalog-head-race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation fixture"),ContentDigest::of(b"transaction fixture"))?;
    let repo=rev::RevisionService::new(BoundaryRepo{inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});
    let bound=StoredFormProvider::bind(&s.artifacts,&repo,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
    match stage{0=>{detect!(&bound,&s,&f)?;},1=>{found.verify(&bound,&f,5)?;},2=>{found.with_verified_json(&bound,&f,5,|_|())?;},
        3=>{found.with_navigation_verified_json(&bound,&f,&nav(),[1;32],5,|_|())?;},_=>{found.with_selection_verified_json(&bound,&f,0,5,|_|())?;}}
    let count=repo.repository().calls.load(Ordering::SeqCst);assert!(count>=4);repo.repository().calls.store(0,Ordering::SeqCst);repo.repository().trigger.store(count,Ordering::SeqCst);let called=Cell::new(false);
    match stage{0=>assert!(detect!(&bound,&s,&f).is_err()),1=>assert!(found.verify(&bound,&f,6).is_err()),2=>assert!(found.with_verified_json(&bound,&f,6,|_|called.set(true)).is_err()),
        3=>assert!(found.with_navigation_verified_json(&bound,&f,&nav(),[1;32],6,|_|called.set(true)).is_err()),_=>assert!(found.with_selection_verified_json(&bound,&f,0,6,|_|called.set(true)).is_err())}
    assert!(!called.get());assert_eq!(repo.repository().calls.load(Ordering::SeqCst),count);Ok(())
}
#[test]fn prepare_consumer_final_head_race_rejects()->R{race(0)}
#[test]fn verify_consumer_final_head_race_rejects()->R{race(1)}
#[test]fn metadata_consumer_final_head_race_rejects()->R{race(2)}
#[test]fn navigation_consumer_final_head_race_rejects()->R{race(3)}
#[test]fn selection_consumer_final_head_race_rejects()->R{race(4)}

mod product{include!("personal_info_catalog_product.rs");}
mod mask{include!("personal_info_catalog_mask_stored.rs");}
