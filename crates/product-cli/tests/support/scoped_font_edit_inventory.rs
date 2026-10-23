//! Independently compare every header effect/body splice to original anchors and actual output.
use super::*;
use sha2::{Digest as _,Sha256};
use hwpx_package::document_import::{ImportedSourcePackage,search::replacement::atoms::styles::fonts::inventory::{SourceFontEditInventory as Inventory,SourceFontEditKind as Kind,FONT_EDIT_INVENTORY_PROFILE}};
use hwpx_agent_cli::form_product_request::stored_literal_replacement::fonts::PreparedStoredFontProduct;

fn retained(out:&PreparedStoredFontProduct,p:&Provider<'_>)->Result<Inventory,Box<dyn Error>>{Ok(out.with_verified_edit_inventory(p,5,Clone::clone)?)}
fn compare(raw:&[u8],output:&[u8],inventory:&Inventory,receipt:&hwpx_package::document_import::search::replacement::atoms::styles::fonts::SourceFontReplacementReceipt)->R{
    let source=ImportedSourcePackage::import(raw,DocumentId::parse("actual-form-document")?,*ContentDigest::of(raw).as_bytes(),Default::default())?;
    assert_eq!(inventory.profile(),FONT_EDIT_INVENTORY_PROFILE);assert_eq!(inventory.axis(),receipt.axis);
    assert_eq!(inventory.source_package_sha256(),*ContentDigest::of(raw).as_bytes());assert_eq!(inventory.output_package_sha256(),*ContentDigest::of(output).as_bytes());
    assert_eq!(inventory.legacy_receipt_sha256(),<[u8;32]>::from(Sha256::digest(serde_json::to_vec(receipt)?)));
    assert_eq!(inventory.compiled_edits_sha256(),receipt.compiled_edits_sha256);
    assert_eq!(inventory.canonical_sha256(),<[u8;32]>::from(Sha256::digest(serde_json::to_vec(inventory)?)));
    let tuples:Vec<_>=inventory.edits().iter().map(|e|(e.source_part_path(),e.source_start(),e.source_end(),e.replacement_sha256())).collect();
    assert_eq!(inventory.compiled_edits_sha256(),<[u8;32]>::from(Sha256::digest(serde_json::to_vec(&tuples)?)));
    assert_eq!(inventory.header_effects().count(),2);assert!(inventory.body_splices().count()>0);
    let mut grouped=std::collections::BTreeMap::<_,Vec<_>>::new();let mut unique=BTreeSet::new();
    for e in inventory.edits(){assert!(unique.insert(e.source_anchor().opaque_handle.clone()));
        let at=source.resolve_anchor(e.source_anchor())?;assert_eq!(at.part().path().as_str(),e.source_part_path());let node=at.element().ok_or("edit element")?;
        let span=node.outer_span().ok_or("edit outer")?;
        match e.kind(){
            Kind::CharacterPropertyCount{attribute_index,original_items,output_items}=>{
                assert_eq!(e.source_part_path(),"Contents/header.xml");assert_eq!(node.name().local_name(),"charProperties");let a=&node.attributes()[attribute_index];
                assert_eq!(a.name().local_name(),"itemCnt");assert_eq!((a.value_span().start(),a.value_span().end()),(e.source_start(),e.source_end()));
                let original_part=archive::read_part(raw,e.source_part_path())?;
                assert_eq!(std::str::from_utf8(&original_part[e.source_start()..e.source_end()])?.parse::<usize>()?,original_items);assert_eq!(output_items-original_items,receipt.cloned_character_properties);assert_eq!(e.fragments(),0);
            },
            Kind::AppendCharacterProperties{appended_items}=>{assert_eq!(e.source_part_path(),"Contents/header.xml");assert_eq!(node.name().local_name(),"charPr");
                assert_eq!((e.source_start(),e.source_end()),(span.end(),span.end()));assert_eq!(appended_items,receipt.cloned_character_properties);assert_eq!(e.fragments(),appended_items);},
            Kind::RunSubtree|Kind::TextSubtree=>{assert_ne!(e.source_part_path(),"Contents/header.xml");assert_eq!((e.source_start(),e.source_end()),(span.start(),span.end()));
                assert_eq!(node.name().local_name(),if e.kind()==Kind::RunSubtree{"run"}else{"t"});assert!(e.fragments()>0);},
        }grouped.entry(e.source_part_path()).or_default().push(e);
    }
    assert_eq!(grouped.len(),receipt.changed_parts);
    for(path,edits)in grouped{let original=archive::read_part(raw,path)?;let changed=archive::read_part(output,path)?;let(mut left,mut right)=(0usize,0usize);
        for e in edits{assert!(e.source_start()>=left);let start=right+e.source_start()-left;assert!(original[left..e.source_start()]==changed[right..start]);let end=start+e.replacement_bytes();
            assert_eq!(<[u8;32]>::from(Sha256::digest(&changed[start..end])),e.replacement_sha256());
            if let Kind::CharacterPropertyCount{output_items,..}=e.kind(){assert!(changed[start..end]==*output_items.to_string().as_bytes());}
            left=e.source_end();right=end;
        }assert!(original[left..]==changed[right..]);
    }
    let before=CharacterStyleCatalogReader::read(&archive::read_part(raw,"Contents/header.xml")?,Default::default())?;
    let after=CharacterStyleCatalogReader::read(&archive::read_part(output,"Contents/header.xml")?,Default::default())?;
    assert_eq!(before.styles.as_slice(),&after.styles[..before.styles.len()]);assert_eq!(before.font_faces,after.font_faces);
    assert_eq!(after.styles.len()-before.styles.len(),receipt.cloned_character_properties);Ok(())
}
fn check(out:&PreparedStoredFontProduct,p:&Provider<'_>,bytes:&[u8])->Result<Inventory,Box<dyn Error>>{
    let inv=retained(out,p)?;let output=out.with_verified_bytes(p,5,<[u8]>::to_vec)?;compare(bytes,&output,&inv,&out.receipt().stored.output)?;Ok(inv)
}
#[test]
fn whole_candidate_has_two_exact_header_resources_and_one_body_splice()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let out=prepare!(&p,&request(&s,&bytes)?)?;
    let inv=check(&out,&p,&bytes)?;assert_eq!(inv.edits().len(),3);assert_eq!(inv.body_splices().count(),1);Ok(())
}
#[test]
fn partial_nfc_selection_keeps_raw_hangul_contributors_and_whole_final_run_splice()->R{
    let bytes=raw("X각Y")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut v=request(&s,&bytes)?;
    let inv=inventory(&p,&v)?;v["selector"]["scope"]=json!("selection");v["selector"]["range"]=selection(&inv,1,2)?;let out=prepare!(&p,&v)?;
    let inv=check(&out,&p,&bytes)?;assert_eq!(inv.body_splices().count(),1);assert_eq!(out.receipt().stored.output.changed_source_scalars,3);assert!(inv.body_splices().all(|e|e.fragments()==3));Ok(())
}
#[test]
fn text_axis_records_text_splices_not_an_inferred_run_or_header_owner()->R{
    let bytes=package("<hp:p id='1'><hp:run charPrIDRef='0'><hp:t charStyleIDRef='1'>ABCD</hp:t></hp:run></hp:p>")?;
    let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut v=request(&s,&bytes)?;v["operation"]["axis"]=json!("text_style");v["operation"]["query"]=json!(name(&bytes,1)?);
    let inv=inventory(&p,&v)?;v["selector"]["scope"]=json!("selection");v["selector"]["range"]=selection(&inv,1,3)?;let out=prepare!(&p,&v)?;
    assert!(check(&out,&p,&bytes)?.body_splices().all(|e|e.kind()==Kind::TextSubtree));Ok(())
}
#[test]
fn shared_style_batch_keeps_one_header_append_and_each_actual_body_splice()->R{
    let bytes=package("<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>ONE</hp:t></hp:run></hp:p><hp:p id='2'><hp:run charPrIDRef='0'><hp:t>TWO</hp:t></hp:run></hp:p>")?;
    let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let out=prepare!(&p,&request(&s,&bytes)?)?;let inv=check(&out,&p,&bytes)?;
    assert_eq!(inv.edits().len(),4);assert_eq!(out.receipt().stored.output.cloned_character_properties,1);Ok(())
}
#[test]
fn separate_original_properties_share_one_typed_append_with_exact_clone_count()->R{
    let bytes=package("<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>A</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t>B</hp:t></hp:run></hp:p>")?;
    let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut v=request(&s,&bytes)?;v["operation"]["regex"]=json!(true);v["operation"]["query"]=json!(".+");let out=prepare!(&p,&v)?;
    let inv=check(&out,&p,&bytes)?;assert_eq!(inv.body_splices().count(),2);assert_eq!(out.receipt().stored.output.cloned_character_properties,2);
    assert!(inv.header_effects().any(|e|e.kind()==Kind::AppendCharacterProperties{appended_items:2}));Ok(())
}
#[test]
fn raw_entities_and_multibyte_text_are_bound_by_original_byte_ranges()->R{
    let bytes=raw("A&#x1F600;B&amp;C")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut v=request(&s,&bytes)?;
    let inv=inventory(&p,&v)?;v["selector"]["scope"]=json!("selection");v["selector"]["range"]=selection(&inv,1,3)?;let out=prepare!(&p,&v)?;check(&out,&p,&bytes)?;Ok(())
}
#[test]
fn inventory_binds_source_output_axis_receipt_and_edits_without_xml_or_font_names()->R{
    let bytes=raw("PRIVATE-INVENTORY-TEXT")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let out=prepare!(&p,&request(&s,&bytes)?)?;let inv=check(&out,&p,&bytes)?;
    for text in [serde_json::to_string(&inv)?,format!("{inv:?}{:?}",inv.edits())]{assert!(!text.contains("PRIVATE-")&&!text.contains("<hp:")&&!text.contains("<hh:"));}
    let changed=raw("PRIVATE-INVENTORY-OTHER")?;let other=StoredFixture::new(&changed,ArtifactKind::Result,false)?;writer!(other,actor2,p2);let out2=prepare!(&p2,&request(&other,&changed)?)?;
    assert_ne!(inv.canonical_sha256(),retained(&out2,&p2)?.canonical_sha256());Ok(())
}
#[test]
fn core_borrowed_owned_and_product_inventory_are_identical_without_relowering()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let source=p.import_actual_forms(s.head,4)?;let n=name(&bytes,0)?;
    let borrowed=source.prepare_font_candidate(&p,query(&n),Scope::Document,policy(),Axis::RunProperty,Default::default(),Default::default(),4)?;
    let owned=p.import_actual_forms(s.head,4)?.into_font_candidate(&p,query(&n),Scope::Document,policy(),Axis::RunProperty,Default::default(),Default::default(),4)?;
    let out=prepare!(&p,&request(&s,&bytes)?)?;let inv=retained(&out,&p)?;
    assert_eq!(borrowed.with_verified_edit_inventory(&p,5,Clone::clone)?,inv);assert_eq!(owned.with_verified_edit_inventory(&p,5,Clone::clone)?,inv);
    let core=source.imported().lower_scoped_font_candidate(&bytes,query(&n),Scope::Document,policy(),Axis::RunProperty,Default::default(),Default::default())?;
    assert_eq!(core.edit_inventory(),&inv);Ok(())
}
#[test]
fn revoked_acl_blocks_inventory_consumer_and_regrant_rechecks_current_access()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let out=prepare!(&p,&request(&s,&bytes)?)?;let original=retained(&out,&p)?;
    s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::new(),5)?;let called=Cell::new(false);assert!(out.with_verified_edit_inventory(&p,6,|_|called.set(true)).is_err());assert!(!called.get());
    s.artifacts.set_permissions(&s.owner,s.result,s.reader.subject(),BTreeSet::from([ArtifactPermission::Read]),7)?;assert_eq!(out.with_verified_edit_inventory(&p,8,Clone::clone)?,original);Ok(())
}
#[test]
fn quarantine_and_ciphertext_tamper_block_inventory_without_consumer_calls()->R{
    for tamper in [false,true]{let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let out=prepare!(&p,&request(&s,&bytes)?)?;
        if tamper{s.blobs.tamper.store(true,Ordering::SeqCst);}else{s.artifacts.quarantine(&s.owner,s.result,QuarantineReason::parse("FONT_INVENTORY_TEST")?,5)?;}
        let called=Cell::new(false);assert!(out.with_verified_edit_inventory(&p,6,|_|called.set(true)).is_err());assert!(!called.get());}Ok(())
}
#[test]
fn inventory_final_head_race_denies_before_metadata_consumer()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let out=prepare!(&p,&request(&s,&bytes)?)?;
    let advance=rev::RevisionCommitRequest::new(rev::CommitId::generate(),s.project,s.branch,s.head,rev::RevisionId::generate(),s.head.revision_id().into_iter().collect(),artifact_service::ArtifactId::generate(),s.result,None,
        ContentDigest::of(b"font-inventory-race"),rev::RevisionValidationState::Verified,ContentDigest::of(b"validation fixture"),ContentDigest::of(b"transaction fixture"))?;
    let repo=rev::RevisionService::new(BoundaryRepo{inner:s.revisions.repository().clone(),calls:AtomicUsize::new(0),trigger:AtomicUsize::new(usize::MAX),context:s.revision_context.clone(),advance});
    let bound=StoredFormProvider::bind(&s.artifacts,&repo,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
    out.with_verified_edit_inventory(&bound,5,|_|())?;let calls=repo.repository().calls.load(Ordering::SeqCst);assert!(calls>=4);repo.repository().calls.store(0,Ordering::SeqCst);repo.repository().trigger.store(calls,Ordering::SeqCst);
    let called=Cell::new(false);assert!(out.with_verified_edit_inventory(&bound,6,|_|called.set(true)).is_err());assert!(!called.get());assert_eq!(repo.repository().calls.load(Ordering::SeqCst),calls);Ok(())
}
#[test]
fn read_only_and_foreign_provider_cannot_read_held_inventory()->R{
    let bytes=raw("ABC")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let out=prepare!(&p,&request(&s,&bytes)?)?;let called=Cell::new(false);
    assert!(out.with_verified_edit_inventory(&s.provider()?,5,|_|called.set(true)).is_err());
    let other=StoredFormProvider::bind(&s.artifacts,&s.revisions,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("foreign-inventory-document")?)?;
    assert!(out.with_verified_edit_inventory(&other,5,|_|called.set(true)).is_err());assert!(!called.get());Ok(())
}
