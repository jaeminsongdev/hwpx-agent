//! Exact final patch inventory through the actual shared product entry and current stored guards.
use super::*;
use std::collections::BTreeMap;
use hwpx_package::document_import::{ImportedSourcePackage,search::replacement::atoms::styles::intents::{SourceStyleSpliceInventory as Inventory,StyleSpliceAxis as Axis}};
fn style_source(axis:usize,text:&str)->Result<Vec<u8>,Box<dyn Error>> {
    let p=para(1,text);definition::package(&if axis==6{p.replace(" charStyleIDRef='0'","")}else{p})
}
fn take<R,B,S,V,T>(out:&Operation,p:&StoredFormProvider<'_,R,B,S,V>,now:u64,consume:impl FnOnce(&Inventory)->T)->Result<T,Box<dyn Error>>
where R:artifact_service::ArtifactMetadataRepository,B:artifact_service::EncryptedBlobStore,S:artifact_service::ArtifactScanner,V:rev::RevisionRepository {
    let Operation::SearchMutation(candidate)=out else{return Err("not mutation".into())};
    match &**candidate {
        base_candidate::CharacterStyle(c)=>Ok(c.with_verified_splice_inventory(p,now,consume)?),
        base_candidate::TextStyle(c)=>Ok(c.with_verified_splice_inventory(p,now,consume)?),
        _=>Err("not style".into()),
    }
}
use hwpx_agent_cli::form_product_request::stored_operations::search_mutations::PreparedStoredSearchMutation as base_candidate;
struct OldReceipt { value:Value, sha:[u8;32] }
impl std::ops::Deref for OldReceipt {type Target=Value;fn deref(&self)->&Value{&self.value}}
fn legacy(receipt:&impl serde::Serialize)->Result<OldReceipt,Box<dyn Error>> {
    let bytes=serde_json::to_vec(receipt)?;Ok(OldReceipt{value:serde_json::from_slice(&bytes)?,sha:*ContentDigest::of(&bytes).as_bytes()})
}
fn old_receipt(out:&Operation)->Result<OldReceipt,Box<dyn Error>> {
    let Operation::SearchMutation(candidate)=out else{return Err("kind".into())};
    match candidate.receipt(){Receipt::CharacterStyle(r)=>legacy(&r.stored.output),Receipt::TextStyle(r)=>legacy(&r.stored.output),_=>Err("style".into())}
}
fn exact_inventory(bytes:&[u8],after:&[u8],inventory:&Inventory,receipt:&OldReceipt)->TestResult {
    assert_eq!(inventory.source_package_sha256(),*ContentDigest::of(bytes).as_bytes());
    assert_eq!(inventory.output_package_sha256(),*ContentDigest::of(after).as_bytes());
    assert_eq!(inventory.legacy_receipt_sha256(),receipt.sha);
    assert_eq!(inventory.canonical_sha256(),*ContentDigest::of(&serde_json::to_vec(inventory)?).as_bytes());
    let source=ImportedSourcePackage::import(bytes,DocumentId::parse("actual-form-document")?,*ContentDigest::of(bytes).as_bytes(),Default::default())?;
    let mut groups:BTreeMap<String,Vec<_>>=BTreeMap::new();
    for splice in inventory.splices(){let at=source.resolve_anchor(splice.source_anchor())?;let e=at.element().ok_or("element")?.outer_span().ok_or("outer")?;
        assert_eq!((e.start(),e.end()),(splice.source_start(),splice.source_end()));assert!(splice.fragments()>0);
        groups.entry(at.part().path().as_str().to_owned()).or_default().push(splice);
    }
    assert_eq!(groups.len(),receipt["changed_parts"].as_u64().ok_or("parts")? as usize);
    let mut zip=hwpx_package::BoundedZipReader::open(Cursor::new(after),Default::default())?;
    let mut old_zip=hwpx_package::BoundedZipReader::open(Cursor::new(bytes),Default::default())?;
    for(path,splices)in groups {let part=source.parts().iter().find(|p|p.path().as_str()==path).ok_or("part")?;
        let index=zip.entries().iter().position(|e|e.path.as_str()==path).ok_or("output part")?;let new=zip.read_entry(index)?;
        let old_index=old_zip.entries().iter().position(|e|e.path.as_str()==path).ok_or("source part")?;let old=old_zip.read_entry(old_index)?;
        let _xml=part.xml().ok_or("xml")?;let(mut a,mut b)=(0,0);
            for s in splices {assert!(s.source_start()>=a);let unchanged=s.source_start()-a;
                assert_eq!(old.get(a..s.source_start()),new.get(b..b+unchanged));b+=unchanged;
                let replacement=new.get(b..b+s.replacement_bytes()).ok_or("replacement")?;
                assert_eq!(s.replacement_sha256(),*ContentDigest::of(replacement).as_bytes());b+=s.replacement_bytes();a=s.source_end();
            }assert_eq!(old.get(a..),new.get(b..));
    }Ok(())
}
#[test]
fn style_inventory_both_axes_bind_actual_partial_subtree_bytes_and_unchanged_legacy_receipts()->TestResult {
    for axis in [6,7]{let bytes=style_source(axis,"AXB")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);
        let mut v=req(axis,&s,&bytes)?;v["operation"]["query"]=json!("X");let out=Dispatch::prepare_json(&p,&wire(&v)?,None,4)?;drop(v);
        let inventory=take(&out,&p,5,Clone::clone)?;assert_eq!(inventory.splices().len(),1);assert_eq!(inventory.splices()[0].fragments(),3);
        assert_eq!(inventory.axis(),if axis==6{Axis::RunCharacterProperty}else{Axis::TextCharacterStyle});
        exact_inventory(&bytes,&out.with_verified_bytes(&p,None,5,<[u8]>::to_vec)?,&inventory,&old_receipt(&out)?)?;
        assert!(out.require_current_product_route(&p,None,5).is_err());
    }Ok(())
}
#[test]
fn style_inventory_discontiguous_matches_are_one_final_splice_not_guessed_match_count()->TestResult {
    for axis in [6,7]{let bytes=style_source(axis,"AXBYXC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=req(axis,&s,&bytes)?;v["operation"]["query"]=json!("X");
        let out=Dispatch::prepare_json(&p,&wire(&v)?,None,4)?;let inventory=take(&out,&p,5,Clone::clone)?;assert_eq!(old_receipt(&out)?["matched_occurrences"],2);
        assert_eq!(inventory.splices().len(),1);assert_eq!(inventory.splices()[0].fragments(),5);exact_inventory(&bytes,&out.with_verified_bytes(&p,None,5,<[u8]>::to_vec)?,&inventory,&old_receipt(&out)?)?;
    }Ok(())
}
#[test]
fn style_inventory_nested_review_overlay_records_only_actual_nonoverlapping_final_splices()->TestResult {
    for axis in [6,7]{let mut body=fixture::body().replace("<hp:run>","<hp:run charPrIDRef='0'>");if axis==7{body=body.replace("<hp:t>","<hp:t charStyleIDRef='0'>");}
        let bytes=definition::package(&body)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=req(axis,&s,&bytes)?;
        let out=Dispatch::prepare_json(&p,&wire(&v)?,None,4)?;let inventory=take(&out,&p,5,Clone::clone)?;
        assert_eq!(inventory.splices().len(),if axis==6{1}else{3});exact_inventory(&bytes,&out.with_verified_bytes(&p,None,5,<[u8]>::to_vec)?,&inventory,&old_receipt(&out)?)?;
    }Ok(())
}
#[test]
fn style_inventory_skips_actual_noop_targets_without_erasing_original_guard_semantics()->TestResult {
    for axis in [6,7]{let first=para(1,"K");let second=para(2,"K");let body=if axis==6{(first+&second.replace("charPrIDRef='0'","charPrIDRef='1'")).replace(" charStyleIDRef='0'","")}else{first+&second.replace("charStyleIDRef='0'","charStyleIDRef='1'")};
        let bytes=definition::package(&body)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=req(axis,&s,&bytes)?;
        v["operation"]["style_filter"]=json!({"kind":"declared","filter":{"paragraph_property":0}});let out=Dispatch::prepare_json(&p,&wire(&v)?,None,4)?;
        let inventory=take(&out,&p,5,Clone::clone)?;assert_eq!(inventory.splices().len(),1);assert_eq!(old_receipt(&out)?["matched_occurrences"],2);
        exact_inventory(&bytes,&out.with_verified_bytes(&p,None,5,<[u8]>::to_vec)?,&inventory,&old_receipt(&out)?)?;
    }Ok(())
}
#[test]
fn style_inventory_review_policy_is_bound_even_when_final_patch_owner_is_shared()->TestResult {
    let bytes=definition::package(&fixture::body().replace("<hp:run>","<hp:run charPrIDRef='0'>"))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut hashes=BTreeSet::new();
    for h in [false,true]{for m in [false,true]{let mut v=req(6,&s,&bytes)?;v["operation"]["review_policy"]=policy(h,m);let out=Dispatch::prepare_json(&p,&wire(&v)?,None,4)?;
        let inventory=take(&out,&p,5,Clone::clone)?;hashes.insert(inventory.canonical_sha256());assert_eq!(inventory.splices().len(),1);
        exact_inventory(&bytes,&out.with_verified_bytes(&p,None,5,<[u8]>::to_vec)?,&inventory,&old_receipt(&out)?)?;
    }}assert_eq!(hashes.len(),4);Ok(())
}
#[test]
fn style_inventory_is_semantic_metadata_not_a_key_claim_and_exposes_no_fragment_xml()->TestResult {
    for axis in [6,7]{let bytes=style_source(axis,"PRIVATE K")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let v=req(axis,&s,&bytes)?;
        let out=Dispatch::prepare_json(&p,&wire(&v)?,None,4)?;let inventory=take(&out,&p,5,Clone::clone)?;let mut other=v;other["idempotency_key"]=json!("OTHER-PRIVATE-KEY");other["plan_id"]=json!("other-plan");
        let again=Dispatch::prepare_json(&p,&wire(&other)?,None,4)?;assert_eq!(inventory,take(&again,&p,5,Clone::clone)?);
        let text=serde_json::to_string(&inventory)?;assert!(!text.contains("PRIVATE")&&!text.contains("<hp:")&&!text.contains("idempotency"));
        assert_eq!(serde_json::to_value(&inventory)?.as_object().ok_or("wire")?.len(),6);assert!(!format!("{inventory:?}{:?}",inventory.splices()).contains("src-"));
        assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);
    }Ok(())
}
#[test]
fn style_inventory_current_write_permission_is_required_before_metadata_consumer()->TestResult {
    for axis in [6,7]{let bytes=style_source(axis,"K")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);
        let out=Dispatch::prepare_json(&p,&wire(&req(axis,&s,&bytes)?)?,None,4)?;let reader=s.provider()?;let called=Cell::new(false);
        assert!(take(&out,&reader,5,|_|called.set(true)).is_err());assert!(!called.get());
    }Ok(())
}
#[test]
fn style_inventory_five_foreign_scopes_cannot_use_retained_metadata()->TestResult {
    for axis in [6,7]{let bytes=style_source(axis,"K")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let out=Dispatch::prepare_json(&p,&wire(&req(axis,&s,&bytes)?)?,None,4)?;let called=Cell::new(false);
        for n in 0..5{let tenant=if n==4{TenantId::new(Uuid::from_u128(1211))?}else{s.reader.tenant_id()};let subject=if n==3{SubjectDigest::from_authenticated_subject("foreign-style-inventory")?}else{s.reader.subject()};
            let actor=RequestContext::new(tenant,subject,[AuthScope::DocumentRead,AuthScope::DocumentWrite]);let context=rev::RevisionRequestContext::new(tenant,subject);
            let project=if n==2{rev::ProjectId::parse("prj_70000000000000000000000000000002")?}else{s.project};let branch=if n==1{rev::BranchId::parse("brn_70000000000000000000000000000002")?}else{s.branch};
            let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&context,project,branch,DocumentId::parse(if n==0{"foreign-document"}else{"actual-form-document"})?)?;
            assert!(take(&out,&other,5,|_|called.set(true)).is_err());
        }assert!(!called.get());
    }Ok(())
}
#[test]
fn style_inventory_acl_revocation_quarantine_and_aead_prevent_retained_delivery()->TestResult {
    for axis in [6,7]{for mode in 0..3{let bytes=style_source(axis,"K")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let out=Dispatch::prepare_json(&p,&wire(&req(axis,&s,&bytes)?)?,None,4)?;
        match mode{0=>{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;},1=>{s.artifacts.quarantine(&s.owner,s.result,QuarantineReason::parse("STYLE_INVENTORY")?,5)?;},_=>s.blobs.tamper.store(true,Ordering::SeqCst)}
        let called=Cell::new(false);assert!(take(&out,&p,6,|_|called.set(true)).is_err());assert!(!called.get());
        if mode==0{s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),7)?;take(&out,&p,8,|_|())?;}
    }}Ok(())
}
#[test]
fn style_inventory_original_consumer_final_head_race_blocks_new_metadata_callback()->TestResult {
    for axis in [6,7]{let bytes=style_source(axis,"K")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let out=Dispatch::prepare_json(&p,&wire(&req(axis,&s,&bytes)?)?,None,4)?;
        let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,ContentDigest::of(b"inventory race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation"),ContentDigest::of(b"transaction"))?;
        let repo=rev::RevisionService::new(BoundaryRepo{inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});let bound=StoredFormProvider::bind(&s.artifacts,&repo,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
        take(&out,&bound,5,|_|())?;let calls=repo.repository().calls.load(Ordering::SeqCst);assert!(calls>=4);repo.repository().calls.store(0,Ordering::SeqCst);repo.repository().trigger.store(calls,Ordering::SeqCst);
        let called=Cell::new(false);assert!(take(&out,&bound,6,|_|called.set(true)).is_err());assert!(!called.get());assert_eq!(repo.repository().calls.load(Ordering::SeqCst),calls);
    }Ok(())
}
#[test]
fn style_inventory_many_actual_targets_keep_one_streamed_inventory_without_raw_fragments()->TestResult {
    for axis in [6,7]{let mut body=String::new();for n in 1..=128{body.push_str(&para(n,"K"));}if axis==6{body=body.replace(" charStyleIDRef='0'","");}
        let bytes=definition::package(&body)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=req(axis,&s,&bytes)?;v["operation"]["max_replacements"]=json!(128);
        let out=Dispatch::prepare_json(&p,&wire(&v)?,None,4)?;let inventory=take(&out,&p,5,Clone::clone)?;assert_eq!(inventory.splices().len(),128);
        assert_eq!(inventory.splices().iter().map(|e|&e.source_anchor().opaque_handle).collect::<BTreeSet<_>>().len(),128);
        exact_inventory(&bytes,&out.with_verified_bytes(&p,None,5,<[u8]>::to_vec)?,&inventory,&old_receipt(&out)?)?;
    }Ok(())
}
#[test]
fn style_inventory_clipped_review_selection_never_becomes_whole_body_edit_permission()->TestResult {
    let bytes=definition::package(&fixture::body().replace("<hp:run>","<hp:run charPrIDRef='0'>"))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,p);let mut v=req(6,&s,&bytes)?;let inv=inventory(&p,&v)?;
    v["selector"]["scope"]=json!("selection");v["selector"]["range"]=window(&inv,"memo_body",7,8)?;let out=Dispatch::prepare_json(&p,&wire(&v)?,None,4)?;
    let targets=take(&out,&p,5,Clone::clone)?;assert_eq!(targets.splices().len(),1);assert_eq!(old_receipt(&out)?["matched_occurrences"],1);
    exact_inventory(&bytes,&out.with_verified_bytes(&p,None,5,<[u8]>::to_vec)?,&targets,&old_receipt(&out)?)?;Ok(())
}
