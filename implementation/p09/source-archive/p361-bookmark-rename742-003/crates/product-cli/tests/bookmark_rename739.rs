//! Atomic source rename candidate and exact linked-leaf preservation; never Native refresh.
#![allow(dead_code)]
#[path="bookmark_results728.rs"]mod prior;
#[path="../../hwpx-package/tests/support/document_import_field_fixture.rs"]#[allow(dead_code)]mod base;
#[path="../../hwpx-package/tests/support/document_import_bookmark_fixture.rs"]#[allow(dead_code)]mod point;
#[path="../../hwpx-package/tests/support/block_bookmark679_fixture.rs"]mod native;
use domain_ir::{DocumentId,LogicalId,ReferenceAuxiliaryLimits,SourceAnchorHandle};
use hwpx_agent_cli::reference_validation_product::{ReferenceValidationProductOperation as Product,
    source_crossref::bookmark_rename738::{BookmarkRenameRequest,BookmarkRenameError as E,SourceBookmarkRenameCandidate}};
use hwpx_package::{WriterLimits,cross_reference_sdk::SdkCrossReferenceDisplay as D,
    document_import::{ImportedSourcePackage,SourceImportLimits,forms::ImportedDocumentForms,
        fields::{ImportedDocumentFields,block_bookmarks::ImportedBlockBookmarks,bookmark_insertion::SourceBookmarkInsertion}}};
use serde_json::{Value,json};
use sha2::{Digest as _,Sha256};
use std::{error::Error,path::PathBuf,io::{Cursor,Read as _,Write}};
type Result<T=()> = std::result::Result<T,Box<dyn Error>>;
const INPUT:&str=include_str!("../../../implementation/p09/evidence/p09-361-block-bookmark693-product-inputs.v1.json");
const OLD:&str="p09_block643_01";
const GENERATED:&str="implementation/p09/evidence/private/p09-361-bookmark-rename740-generated001";
fn require(ok:bool)->Result{if ok{Ok(())}else{Err("P740_ATOMIC_RENAME_CHECK_FAILED".into())}}
fn doc()->Result<DocumentId>{Ok(DocumentId::parse("rename739")?)}
fn limits()->Result<ReferenceAuxiliaryLimits>{Ok(ReferenceAuxiliaryLimits::new(Default::default())?)}
fn forms(bytes:&[u8])->Result<ImportedDocumentForms>{Ok(ImportedDocumentForms::import(ImportedSourcePackage::import(bytes,doc()?,Sha256::digest(bytes).into(),SourceImportLimits::default())?)?)}
fn select(bytes:&[u8],name:&str)->Result<LogicalId>{
    let forms=forms(bytes)?;let fields=ImportedDocumentFields::import(&forms)?;let blocks=ImportedBlockBookmarks::import(&fields,limits()?)?;
    if let Ok(row)=blocks.by_exact_source_name(name){return Ok(row.field_reference_id().clone());}
    Ok(forms.body_structure().bookmarks().iter().find(|b|b.name==name).ok_or("target")?.reference_id.clone())
}
fn rename(bytes:&[u8],name:&str,new:&str)->Result<SourceBookmarkRenameCandidate>{
    Ok(Product::prepare_source_bookmark_rename(bytes,doc()?,Sha256::digest(bytes).into(),SourceImportLimits::default(),limits()?,
        BookmarkRenameRequest{target_id:&select(bytes,name)?,expected_name_sha256:Sha256::digest(name.as_bytes()).into(),new_name:new},WriterLimits::default())?)
}
fn sample(stage:&str)->Result<Vec<u8>>{let v:Value=serde_json::from_str(INPUT)?;prior::read_result_pin728(&v["cases"][2]["stages"][stage]["pin"])}
fn plain_run(forms:&ImportedDocumentForms,raw:&[u8],text:&str)->Result<SourceAnchorHandle>{
    let mut zip=zip::ZipArchive::new(Cursor::new(raw))?;
    for part in forms.source().parts(){if let Some(xml)=part.xml(){let mut bytes=Vec::new();zip.by_name(part.path().as_str())?.read_to_end(&mut bytes)?;
        require(<[u8;32]>::from(Sha256::digest(&bytes))==xml.original_sha256())?;
        for(i,n)in xml.elements().iter().enumerate(){
        if n.name().local_name()!="run"{continue;}let Some(t)=n.first_child().and_then(|j|xml.elements().get(j))else{continue};
        if t.name().local_name()=="t"&&t.first_child().is_none()&&t.next_sibling().is_none()
            &&t.content_span().is_some_and(|s|bytes.get(s.start()..s.end())==Some(text.as_bytes())){return Ok(part.element_anchor(i).ok_or("run")?.clone());}
    }}}Err("run".into())
}
fn extra_reference(target:&str)->Result<Vec<u8>>{
    let raw=native::map_section(&sample("candidate")?,|xml|{let at=xml.rfind("</hs:sec>").ok_or("section")?;
        Ok(format!("{}<hp:p id=\"0\" paraPrIDRef=\"0\" styleIDRef=\"0\" pageBreak=\"0\" columnBreak=\"0\" merged=\"0\"><hp:run charPrIDRef=\"0\"><hp:t>SECOND737</hp:t></hp:run></hp:p>{}",&xml[..at],&xml[at..]))})?;
    let forms=forms(&raw)?;let fields=ImportedDocumentFields::import(&forms)?;let run=plain_run(&forms,&raw,"SECOND737")?;let target=select(&raw,target)?;
    let proof=forms.reconstruct_source_for_verification(&raw)?;
    Ok(fields.create_bookmark_reference(&proof,SourceBookmarkInsertion{run:&run,target_id:&target,display:D::Content,hyperlink:true},limits()?,WriterLimits::default())?
        .with_verified_bytes(|b|b.to_vec())?)
}
pub fn observation()->Result<Value>{
    let input:Value=serde_json::from_str(INPUT)?;
    let root=PathBuf::from(env!("CARGO_MANIFEST_DIR")).parent().and_then(std::path::Path::parent).ok_or("root")?.to_owned();
    let directory=root.join(GENERATED);require(!directory.exists())?;std::fs::create_dir(&directory)?;let mut rows=Vec::new();
    for case in input["cases"].as_array().ok_or("cases")?{
        let index=case["case_index"].as_u64().ok_or("index")?;let original=&case["stages"]["reopened"]["pin"];let bytes=prior::read_result_pin728(original)?;
        let candidate=rename(&bytes,OLD,"p09_renamed737")?;let r=candidate.receipt();
        require(r.changed_crossrefs==1&&r.changed_parts==1&&r.target_and_all_admitted_refs_rebound&&r.command_and_refpath_synchronized
            &&r.affected_fields_marked_dirty&&r.cache_bytes_preserved_not_refreshed&&r.outside_selected_values_exact
            &&!r.native_refresh_or_execution_publication_revision_authority)?;
        let output=candidate.with_verified_bytes(|v|v.to_vec())?;let relative=format!("{GENERATED}/case-{index:02}.hwpx");
        let mut file=std::fs::OpenOptions::new().write(true).create_new(true).open(root.join(&relative))?;file.write_all(&output)?;file.sync_all()?;drop(file);
        let pin=json!({"path":relative,"bytes":output.len(),"sha256":hex::encode(Sha256::digest(&output))});
        require(prior::read_result_pin728(&pin)?==output&&prior::read_result_pin728(original)?==bytes)?;
        rows.push(json!({"case_index":index,"source":original,"output":pin,"receipt":r,"source_unchanged":true,"output_readback_exact":true}));
    }
    Ok(json!({"state":"QUALIFIED740_ATOMIC_TARGET_RENAME_AND_ALL_BOUND_CROSSREFS_ACTUAL8_CACHE_PRESERVED_NOT_REFRESHED",
        "cases":rows,"Native_started":false,"reference_refresh_or_publication_qualified":false,"P09_complete":false}))
}
#[test]
fn block_name_command_refpath_and_dirty_change_atomically_with_xml_escaping()->Result{
    let bytes=sample("reopened")?;let candidate=rename(&bytes,OLD,"renamed&'雪")?;
    let r=candidate.receipt();require(r.changed_crossrefs==1&&r.target_and_all_admitted_refs_rebound&&r.command_and_refpath_synchronized
        &&r.affected_fields_marked_dirty&&r.cache_bytes_preserved_not_refreshed&&r.outside_selected_values_exact
        &&!r.native_refresh_or_execution_publication_revision_authority)?;
    let json=serde_json::to_string(r)?;require(!json.contains(OLD)&&!json.contains("renamed&"))?;
    let out=candidate.with_verified_bytes(|b|b.to_vec())?;
    let expectations=Product::prepare_source_bookmark_result_expectations(&out,doc()?,Sha256::digest(&out).into(),SourceImportLimits::default(),limits()?,
        &[hwpx_agent_cli::reference_validation_product::source_bookmark_results727::BookmarkResultSelection{target_id:select(&out,"renamed&'雪")?,display:D::BookmarkName,hyperlink:false}])?;
    let result=Product::assess_source_bookmark_result(&expectations[0],&out,&out,doc()?,Sha256::digest(&out).into(),SourceImportLimits::default())?;
    require(result.status==hwpx_agent_cli::reference_validation_product::source_bookmark_results727::BookmarkResultStatus::SourceTextMismatch)
}
#[test]
fn point_marker_rename_rebinds_its_generated_crossref_without_block_promotion()->Result{
    let raw=base::package(&format!("<hp:p id='1'><hp:run>{}</hp:run></hp:p><hp:p id='2'><hp:run><hp:t>POINT737</hp:t></hp:run></hp:p>",point::marker("p09_point737")))?;
    let forms=forms(&raw)?;let fields=ImportedDocumentFields::import(&forms)?;let run=plain_run(&forms,&raw,"POINT737")?;let target=select(&raw,"p09_point737")?;
    let proof=forms.reconstruct_source_for_verification(&raw)?;let created=fields.create_bookmark_reference(&proof,SourceBookmarkInsertion{
        run:&run,target_id:&target,display:D::BookmarkName,hyperlink:false},limits()?,WriterLimits::default())?.with_verified_bytes(|b|b.to_vec())?;
    let c=rename(&created,"p09_point737","p09_new_point737")?;require(c.receipt().changed_crossrefs==1
        &&c.receipt().family==hwpx_package::document_import::fields::bookmark_authoring_targets::SourceBookmarkFamily::Point)
}
#[test]
fn every_reference_to_selected_target_is_changed_in_one_output()->Result{
    let c=rename(&extra_reference(OLD)?,OLD,"p09_all_renamed737")?;require(c.receipt().changed_crossrefs==2&&c.receipt().cache_bytes_preserved_not_refreshed)
}
#[test]
fn unrelated_reference_is_preserved_while_selected_reference_changes()->Result{
    let c=rename(&extra_reference("p09_block643_02")?,OLD,"p09_one_renamed737")?;
    require(c.receipt().changed_crossrefs==1&&c.receipt().outside_selected_values_exact)
}
#[test]
fn collision_noop_and_unsafe_names_fail_without_a_partial_candidate()->Result{
    let bytes=sample("reopened")?;require(rename(&bytes,OLD,"p09_block643_02").is_err()&&rename(&bytes,OLD,OLD).is_err())?;
    for name in["","#bad","bad;name","bad/name","bad?name"]{require(rename(&bytes,OLD,name).is_err())?;}Ok(())
}
#[test]
fn stale_source_digest_and_wrong_expected_target_name_are_rejected()->Result{
    let bytes=sample("reopened")?;let target=select(&bytes,OLD)?;
    require(matches!(Product::prepare_source_bookmark_rename(&bytes,doc()?,[9;32],SourceImportLimits::default(),limits()?,
        BookmarkRenameRequest{target_id:&target,expected_name_sha256:Sha256::digest(OLD.as_bytes()).into(),new_name:"new737"},WriterLimits::default()),Err(E::Source)))?;
    require(matches!(Product::prepare_source_bookmark_rename(&bytes,doc()?,Sha256::digest(&bytes).into(),SourceImportLimits::default(),limits()?,
        BookmarkRenameRequest{target_id:&target,expected_name_sha256:[7;32],new_name:"new737"},WriterLimits::default()),Err(E::Target)))
}
#[test]
fn inconsistent_refpath_is_rejected_instead_of_changing_command_only()->Result{
    let bytes=native::map_section(&sample("reopened")?,|xml|{let i=xml.find("name=\"RefPath\"").ok_or("refpath")?;
        let a=i+xml[i..].find('>').ok_or("start")?+1;let b=a+xml[a..].find("</hp:stringParam>").ok_or("end")?;
        Ok(format!("{}?wrong737;{}",&xml[..a],&xml[b..]))})?;
    let target=select(&bytes,OLD)?;require(matches!(Product::prepare_source_bookmark_rename(&bytes,doc()?,Sha256::digest(&bytes).into(),SourceImportLimits::default(),limits()?,
        BookmarkRenameRequest{target_id:&target,expected_name_sha256:Sha256::digest(OLD.as_bytes()).into(),new_name:"new737"},WriterLimits::default()),Err(E::Parameters)))
}
#[test]
fn observed_lock_blocks_the_atomic_rename()->Result{
    let bytes=native::map_section(&sample("reopened")?,|xml|{require(xml.contains("<hp:fieldBegin "))?;Ok(xml.replacen("<hp:fieldBegin ","<hp:fieldBegin lock=\"1\" ",1))})?;
    let target=select(&bytes,OLD)?;require(matches!(Product::prepare_source_bookmark_rename(&bytes,doc()?,Sha256::digest(&bytes).into(),SourceImportLimits::default(),limits()?,
        BookmarkRenameRequest{target_id:&target,expected_name_sha256:Sha256::digest(OLD.as_bytes()).into(),new_name:"new737"},WriterLimits::default()),Err(E::Protection)))
}
#[test]
fn rename_cannot_silently_capture_an_unrelated_dangling_reference()->Result{
    let bytes=native::map_section(&extra_reference("p09_block643_02")?,|xml|{require(xml.matches("?p09_block643_02;").count()==2)?;
        Ok(xml.replace("?p09_block643_02;","?p09_future737;"))})?;
    let target=select(&bytes,OLD)?;require(matches!(Product::prepare_source_bookmark_rename(&bytes,doc()?,Sha256::digest(&bytes).into(),SourceImportLimits::default(),limits()?,
        BookmarkRenameRequest{target_id:&target,expected_name_sha256:Sha256::digest(OLD.as_bytes()).into(),new_name:"p09_future737"},WriterLimits::default()),Err(E::Collision)))
}
