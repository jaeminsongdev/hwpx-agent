//! Read-only cursor resolution, distinct from moving a Native window or accepting render output.
#![allow(dead_code)]
#[path="bookmark_results728.rs"]mod prior;
#[path="../../hwpx-package/tests/support/document_import_field_fixture.rs"]mod base;
#[path="../../hwpx-package/tests/support/document_import_bookmark_fixture.rs"]mod point;
#[path="../../hwpx-package/tests/support/block_bookmark679_fixture.rs"]mod fixture;
use domain_ir::{DocumentId,LogicalId,ReferenceAuxiliaryLimits,ReferenceAuxiliaryLimitConfig};
use hwpx_agent_cli::reference_validation_product::{ReferenceValidationProductOperation as Product,
    source_crossref::bookmark_navigation744::{BookmarkNavigationError as E,BookmarkNavigationStatus as S,PreparedBookmarkNavigation}};
use hwpx_package::{WriterLimits,cross_reference_sdk::SdkCrossReferenceDisplay as D,document_import::{ImportedSourcePackage,
    SourceImportLimits,forms::ImportedDocumentForms,fields::{ImportedDocumentFields,bookmark_insertion::SourceBookmarkInsertion,
        bookmark_authoring_targets::SourceBookmarkFamily as Family}}};
use serde_json::{Value,json};
use sha2::{Digest as _,Sha256};
use std::{error::Error,io::{Cursor,Read}};
type Result<T=()> = std::result::Result<T,Box<dyn Error>>;
const INPUT:&str=include_str!("../../../implementation/p09/evidence/p09-361-bookmark-navigation743-inputs.v1.json");
fn require(ok:bool)->Result{if ok{Ok(())}else{Err("P746_NAVIGATION_CHECK_FAILED".into())}}
fn doc()->Result<DocumentId>{Ok(DocumentId::parse("navigation745")?)}
fn limits()->Result<ReferenceAuxiliaryLimits>{Ok(ReferenceAuxiliaryLimits::new(Default::default())?)}
fn forms(b:&[u8])->Result<ImportedDocumentForms>{Ok(ImportedDocumentForms::import(ImportedSourcePackage::import(b,doc()?,Sha256::digest(b).into(),SourceImportLimits::default())?)?)}
fn ids(b:&[u8])->Result<Vec<LogicalId>>{let f=forms(b)?;Ok(ImportedDocumentFields::import(&f)?.fields().iter().filter(|v|v.native_kind=="CROSSREF").map(|v|v.reference_id.clone()).collect())}
fn prepare(b:&[u8])->Result<PreparedBookmarkNavigation>{Ok(Product::prepare_source_bookmark_navigation(b,doc()?,Sha256::digest(b).into(),SourceImportLimits::default(),limits()?,&ids(b)?)?)}
fn sample(index:usize,stage:&str)->Result<Vec<u8>>{let v:Value=serde_json::from_str(INPUT)?;prior::read_result_pin728(&v["cases"][index-1][stage])}
fn status(b:&[u8])->Result<S>{let p=prepare(b)?;Ok(p.with_current_results(b,|r|r[0].receipt().status)?)}
fn point_source()->Result<Vec<u8>>{
    let marker=point::marker("p09_point745");let raw=base::package(&format!("<hp:p id='1'><hp:run>{marker}</hp:run></hp:p><hp:p id='2'><hp:run><hp:t>POINT745</hp:t></hp:run></hp:p>"))?;
    let f=forms(&raw)?;let fields=ImportedDocumentFields::import(&f)?;let target=&f.body_structure().bookmarks()[0].reference_id;
    let mut zip=zip::ZipArchive::new(Cursor::new(&raw))?;let mut run=None;
    for part in f.source().parts(){if let Some(xml)=part.xml(){let mut bytes=Vec::new();zip.by_name(part.path().as_str())?.read_to_end(&mut bytes)?;
        require(<[u8;32]>::from(Sha256::digest(&bytes))==xml.original_sha256())?;
        for(i,n)in xml.elements().iter().enumerate(){if n.name().local_name()!="run"{continue;}
            if n.first_child().and_then(|i|xml.elements().get(i)).and_then(|n|n.content_span()).is_some_and(|s|bytes.get(s.start()..s.end())==Some(b"POINT745")){
                run=part.element_anchor(i).cloned();}
        }
    }}
    let proof=f.reconstruct_source_for_verification(&raw)?;
    Ok(fields.create_bookmark_reference(&proof,SourceBookmarkInsertion{run:&run.ok_or("run")?,target_id:target,display:D::BookmarkName,hyperlink:true},limits()?,WriterLimits::default())?.with_verified_bytes(|b|b.to_vec())?)
}
fn destination(b:&[u8],name:&str)->Result<(usize,Option<usize>)>{
    let p=prepare(b)?;let f=forms(b)?;
    p.with_current_results(b,|rows|->Result<_>{require(rows.len()==1)?;let r=&rows[0];require(r.receipt().status==S::SourceDestinationResolved)?;
        let target=r.destination().ok_or("destination")?;let start=f.source().resolve_anchor(target.start())?;
        let n=start.element().ok_or("element")?;let mut zip=zip::ZipArchive::new(Cursor::new(b))?;let mut raw=Vec::new();
        zip.by_name(start.part().path().as_str())?.read_to_end(&mut raw)?;
        require(<[u8;32]>::from(Sha256::digest(&raw))==start.part().xml().ok_or("xml")?.original_sha256())?;
        let a=n.attributes().iter().find(|a|a.name().namespace().is_none()&&a.name().local_name()=="name").ok_or("name")?.value_span();
        require(quick_xml::escape::unescape(std::str::from_utf8(raw.get(a.start()..a.end()).ok_or("span")?)?)?.as_ref()==name)?;
        let end=target.end().map(|a|f.source().resolve_anchor(a)).transpose()?;
        if target.family()==Family::Block{require(n.name().local_name()=="fieldBegin"&&end.as_ref().and_then(|v|v.element()).is_some_and(|n|n.name().local_name()=="fieldEnd"))?;}
        else{require(n.name().local_name()=="bookmark"&&end.is_none())?;}
        Ok((start.element_index().ok_or("start")?,end.and_then(|e|e.element_index())))
    })?
}
pub fn observation()->Result<Value>{
    let v:Value=serde_json::from_str(INPUT)?;let mut rows=Vec::new();let(mut resolved,mut disabled)=(0,0);
    for c in v["cases"].as_array().ok_or("cases")?{let index=c["case_index"].as_u64().ok_or("index")?;
        for stage in["original","renamed"]{let bytes=prior::read_result_pin728(&c[stage])?;let p=prepare(&bytes)?;
            let s=p.with_current_results(&bytes,|r|r[0].receipt().status)?;let enabled=index%2==0;
            require(s==if enabled{S::SourceDestinationResolved}else{S::HyperlinkDisabled})?;
            let position=if enabled{resolved+=1;Some(destination(&bytes,if stage=="original"{"p09_block643_01"}else{"p09_renamed737"})?)}else{disabled+=1;
                require(p.with_current_results(&bytes,|r|r[0].destination().is_none())?)?;None};
            let metadata=p.canonical_receipts_json()?;require(prior::read_result_pin728(&c[stage])?==bytes)?;
            rows.push(json!({"case_index":index,"stage":stage,"source":c[stage],"status":s,"source_position":position,"receipt_sha256":hex::encode(Sha256::digest(metadata)),"source_unchanged":true}));
        }
    }
    require(resolved==8&&disabled==8)?;
    Ok(json!({"state":"QUALIFIED746_ORIGINAL_AND_RENAMED16_CURRENT_SOURCE_NAVIGATION8_DISABLED8_NOT_NATIVE_CURSOR_OR_F11",
        "cases":rows,"resolved":resolved,"disabled":disabled,"Native_started":false,"native_cursor_moved":false,"full_F11_or_P09_qualified":false}))
}
#[test]
fn enabled_native_block_crossref_resolves_exact_begin_and_end_not_opaque_fieldid()->Result{let b=sample(4,"original")?;let(a,z)=destination(&b,"p09_block643_01")?;require(z.is_some_and(|z|a<z))}
#[test]
fn disabled_link_never_yields_a_cursor_even_with_a_bound_target()->Result{let b=sample(3,"original")?;let p=prepare(&b)?;
    require(p.with_current_results(&b,|r|r[0].receipt().status==S::HyperlinkDisabled&&r[0].destination().is_none())?)}
#[test]
fn point_marker_is_a_single_source_destination_without_block_promotion()->Result{require(destination(&point_source()?,"p09_point745")?.1.is_none())}
#[test]
fn renamed_target_resolves_new_source_name_without_consuming_old_display_cache()->Result{let b=sample(4,"renamed")?;destination(&b,"p09_renamed737")?;let p=prepare(&b)?;
    require(p.with_current_results(&b,|r|!r[0].receipt().cached_display_used_for_destination&&!r[0].receipt().native_cursor_or_execution_authority)?)}
#[test]
fn moving_point_marker_requires_fresh_resolution_and_cannot_reuse_old_position()->Result{
    let b=point_source()?;let old=destination(&b,"p09_point745")?;let prepared=prepare(&b)?;let marker=point::marker("p09_point745");
    let moved=fixture::map_section(&b,|xml|{require(xml.matches(&marker).count()==1)?;let without=xml.replacen(&marker,"",1);let at=without.rfind("</hs:sec>").ok_or("section")?;
        Ok(format!("{}<hp:p id='3'><hp:run>{marker}</hp:run></hp:p>{}",&without[..at],&without[at..]))})?;
    require(matches!(prepared.with_current_results(&moved,|_|()),Err(E::Source)))?;
    let current=destination(&moved,"p09_point745")?;require(current.0>old.0&&current.1.is_none())
}
#[test]
fn missing_and_ambiguous_targets_are_diagnostics_with_no_destination()->Result{
    let missing=fixture::map_section(&sample(4,"original")?,|xml|{require(xml.matches("?p09_block643_01;").count()==2)?;Ok(xml.replace("?p09_block643_01;","?missing745;"))})?;
    require(status(&missing)?==S::MissingTarget)?;
    let ambiguous=fixture::map_section(&sample(4,"original")?,|xml|{let old="name=\"p09_block643_02\"";require(xml.matches(old).count()==1)?;
        Ok(xml.replacen(old,"name=\"p09_block643_01\"",1))})?;
    require(status(&ambiguous)?==S::AmbiguousTarget)
}
#[test]
fn inconsistent_or_duplicate_refpath_cannot_authorize_navigation()->Result{
    for duplicate in[false,true]{let b=fixture::map_section(&sample(4,"original")?,|xml|{
        let i=xml.find("name=\"RefPath\"").ok_or("refpath")?;let a=i+xml[i..].find('>').ok_or("start")?+1;let z=a+xml[a..].find("</hp:stringParam>").ok_or("end")?;
        if duplicate{let start=xml[..i].rfind("<hp:stringParam").ok_or("start")?;let end=z+"</hp:stringParam>".len();
            let parameters=xml[..i].rfind("<hp:parameters ").ok_or("parameters")?;
            let a=parameters+xml[parameters..].find("cnt=\"").ok_or("count")?+5;let z=a+xml[a..].find('"').ok_or("count")?;
            let count=xml[a..z].parse::<usize>()?.checked_add(1).ok_or("count")?;
            let mut output=format!("{}{}{}",&xml[..end],&xml[start..end],&xml[end..]);output.replace_range(a..z,&count.to_string());Ok(output)}
        else{Ok(format!("{}?wrong745;{}",&xml[..a],&xml[z..]))}})?;
        let ids=ids(&b)?;require(matches!(Product::prepare_source_bookmark_navigation(&b,doc()?,Sha256::digest(&b).into(),SourceImportLimits::default(),limits()?,&ids),Err(E::Parameters)))?;
    }Ok(())
}
#[test]
fn stale_source_duplicate_unknown_empty_and_tiny_output_are_rejected()->Result{
    let b=sample(4,"original")?;let selection=ids(&b)?;
    require(matches!(Product::prepare_source_bookmark_navigation(&b,doc()?,[7;32],SourceImportLimits::default(),limits()?,&selection),Err(E::Source)))?;
    for bad in[Vec::new(),vec![selection[0].clone(),selection[0].clone()],vec![LogicalId::parse("not_a_field745")?]]{
        require(Product::prepare_source_bookmark_navigation(&b,doc()?,Sha256::digest(&b).into(),SourceImportLimits::default(),limits()?,&bad).is_err())?;
    }
    let tiny=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig{input_bytes:1,output_bytes:1,..Default::default()})?;
    require(Product::prepare_source_bookmark_navigation(&b,doc()?,Sha256::digest(&b).into(),SourceImportLimits::default(),tiny,&selection).is_err())
}
#[test]
fn receipt_and_debug_hide_names_commands_contents_and_native_permission()->Result{
    let b=sample(4,"original")?;let p=prepare(&b)?;let metadata=String::from_utf8(p.canonical_receipts_json()?)?;
    require(!metadata.contains("p09_block643")&&!metadata.contains("B643_ALPHA")&&!metadata.contains("#?")
        &&metadata.contains("\"native_cursor_moved\":false")&&!format!("{p:?}").contains("p09_block643"))
}
