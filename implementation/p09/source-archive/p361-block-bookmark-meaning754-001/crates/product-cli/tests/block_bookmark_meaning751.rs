//! Common field meanings for admitted source BOOKMARK ranges, never Native evaluation.
#![allow(dead_code)]
#[path="bookmark_results728.rs"]mod prior;
#[path="reference_field_semantics_product.rs"]mod legacy;
#[path="../../hwpx-package/tests/support/block_bookmark679_fixture.rs"]mod native;
#[path="../../hwpx-package/tests/support/document_import_field_fixture.rs"]mod base;
use domain_ir::{DocumentId,DocumentGraph,DocumentGraphLimits,ReferenceAuxiliaryLimits,ReferenceAuxiliaryLimitConfig};
use hwpx_agent_cli::reference_validation_product::{ReferenceValidationProductOperation as Product,
    source_field_semantics::ReferenceSourceMeaningKind as Kind,source::ReferenceSourceStatus};
use hwpx_package::{WriterLimits,cross_reference_sdk::SdkCrossReferenceDisplay as D,document_import::{ImportedSourcePackage,SourceImportLimits,
    forms::ImportedDocumentForms,fields::{ImportedDocumentFields,block_bookmarks::ImportedBlockBookmarks,
        bookmark_insertion::SourceBookmarkInsertion,cached_source::FieldCacheSnapshot,
        bookmark_crossref::SourceBookmarkResolution,semantics::{ImportedFieldMeaning as M,ImportedDocumentFieldSemantics,
            block749,source_index::SourceFieldMeaningIndex}}}};
use serde_json::{Value,json};
use sha2::{Digest as _,Sha256};
use std::error::Error;
type Result<T=()> = std::result::Result<T,Box<dyn Error>>;
const INPUT:&str=include_str!("../../../implementation/p09/evidence/p09-361-block-bookmark693-product-inputs.v1.json");
const RENAMED:&str=include_str!("../../../implementation/p09/evidence/p09-361-bookmark-navigation743-inputs.v1.json");
fn require(ok:bool)->Result{if ok{Ok(())}else{Err("P752_BLOCK_MEANING_CHECK_FAILED".into())}}
fn doc()->Result<DocumentId>{Ok(DocumentId::parse("block-meaning751")?)}
fn limits()->Result<ReferenceAuxiliaryLimits>{Ok(ReferenceAuxiliaryLimits::new(Default::default())?)}
fn forms(b:&[u8])->Result<ImportedDocumentForms>{Ok(ImportedDocumentForms::import(ImportedSourcePackage::import(b,doc()?,Sha256::digest(b).into(),SourceImportLimits::default())?)?)}
fn source()->Result<Vec<u8>>{let v:Value=serde_json::from_str(INPUT)?;prior::read_result_pin728(&v["source"])}
fn sample(index:usize,stage:&str)->Result<Vec<u8>>{let v:Value=serde_json::from_str(INPUT)?;prior::read_result_pin728(&v["cases"][index-1]["stages"][stage]["pin"])}
fn readback(bytes:&[u8])->Result<Value>{
    let f=forms(bytes)?;let fields=ImportedDocumentFields::import(&f)?;let blocks=ImportedBlockBookmarks::import(&fields,limits()?)?;
    let index=SourceFieldMeaningIndex::import(&fields,limits()?)?;let graph=ImportedDocumentFieldSemantics::import(&fields)?;
    require(blocks.observations().len()==8&&index.receipt().block_bookmarks==8&&index.receipt().unsupported_meanings==0
        &&graph.receipt().block_bookmarks==8&&graph.receipt().unsupported_meanings==0&&index.observations()==graph.observations())?;
    require(index.receipt().profile==block749::INDEX_PROFILE&&graph.receipt().profile==block749::GRAPH_PROFILE)?;
    let mut selected=0usize;
    for b in blocks.observations(){let m=&index.observations().iter().find(|m|&m.reference_id==b.field_reference_id()).ok_or("block")?.meaning;
        let M::BlockBookmarkRange{bookmark}=m else{return Err("block meaning".into())};
        require(bookmark.name_sha256==<[u8;32]>::from(Sha256::digest(b.name().as_bytes()))&&bookmark.name_utf8_bytes==b.name().len()
            &&bookmark.begin_fingerprint_sha256==b.begin_anchor().fingerprint_sha256&&bookmark.end_fingerprint_sha256==b.end_anchor().fingerprint_sha256
            &&bookmark.selected_source==*b.selected_source()&&!bookmark.point_marker_equivalent&&!bookmark.native_evaluation_or_execution_authority)?;
        selected+=1;
    }
    let api=Product::assess_package_field_semantics(bytes,doc()?,Sha256::digest(bytes).into(),SourceImportLimits::default(),limits()?)?;
    require(api.receipt()==index.receipt()&&api.selections().iter().filter(|v|v.kind==Kind::BlockBookmarkRange).count()==8)?;
    let api_json:Value=serde_json::from_slice(&api.canonical_json(limits()?)?)?;
    require(api_json["schema_version"]=="hwpx-agent.product.reference-source-field-meanings/v3"
        &&api_json["status"]=="incomplete"&&api_json["reference_validation_or_external_approval"]==false)?;
    for (i,(range,m))in fields.fields().iter().zip(index.observations()).enumerate(){
        require(range.reference_id==m.reference_id&&api.selections()[i].meaning_sha256==index.meaning_sha256(i)?)?;
    }
    let raw=graph.graph().canonical_json()?;
    require(DocumentGraph::from_json(&raw,DocumentGraphLimits::default())?==*graph.graph()&&graph.verify_source(bytes)?==*graph.receipt())?;
    let proof=f.reconstruct_source_for_verification(bytes)?;require(index.verify_reconstruction(&proof)?==*index.receipt())?;
    let mut command_sha=None;let mut target_name_sha=None;
    for o in index.observations(){if let M::BookmarkCrossReference{command}=&o.meaning{
        command_sha=Some(hex::encode(command.command_sha256));
        let SourceBookmarkResolution::Bound{logical_target_id,..}=&command.target else{return Err("target".into())};
        let meaning=&index.observations().iter().find(|v|&v.reference_id==logical_target_id).ok_or("target")?.meaning;
        let M::BlockBookmarkRange{bookmark}=meaning else{return Err("target kind".into())};
        require(bookmark.name_sha256==command.exact_target_name_sha256)?;target_name_sha=Some(hex::encode(bookmark.name_sha256));
    }}
    Ok(json!({"block_meanings":selected,"unsupported":index.receipt().unsupported_meanings,
        "ranges":fields.fields().len(),"crossrefs":index.receipt().bookmark_crossrefs,"bound_edges":graph.receipt().bound_bookmark_edges,
        "command_sha256":command_sha,"target_name_sha256":target_name_sha,
        "graph_round_trip":true,"fresh_whole_reconstruction":true,"independent_field_API_parity":true,"raw_names_or_cache_exported":false}))
}
pub fn observation()->Result<Value>{
    let input:Value=serde_json::from_str(INPUT)?;let renamed:Value=serde_json::from_str(RENAMED)?;let mut observations=Vec::new();
    for c in input["cases"].as_array().ok_or("cases")?{let index=c["case_index"].as_u64().ok_or("index")?;
        for stage in["candidate","initial","saved","reopened","renamed"]{
            let pin=if stage=="renamed"{&renamed["cases"][(index-1)as usize]["renamed"]}else{&c["stages"][stage]["pin"]};
            let bytes=prior::read_result_pin728(pin)?;let summary=readback(&bytes)?;
            require(summary["ranges"]==9&&summary["crossrefs"]==1&&summary["bound_edges"]==1)?;
            if stage!="renamed"{require(summary["command_sha256"]==c["stages"][stage]["command_sha256"])?;}
            require(summary["target_name_sha256"]==if stage=="renamed"{json!(hex::encode(Sha256::digest(b"p09_renamed737")))}else{input["target_name_sha256"].clone()})?;
            let full=Product::assess_package_source(&bytes,doc()?,Sha256::digest(&bytes).into(),SourceImportLimits::default(),limits()?)?;
            require(full.validation_report().is_none()&&full.status()==ReferenceSourceStatus::Incomplete)?;
            let full:Value=serde_json::from_slice(&full.canonical_json(limits()?)?)?;
            let schema=if stage=="candidate"{"hwpx-agent.product.reference-source-assessment/v18"}else{"hwpx-agent.product.reference-source-assessment/v17"};
            require(full["schema_version"]==schema&&full["field_meanings"]["meaning_import"]["block_bookmarks"]==8
                &&full["field_meanings"]["meaning_import"]["unsupported_meanings"]==0
                &&full["unresolved"].as_array().is_some_and(|a|a.len()==if stage=="candidate"{5}else{4}))?;
            require(prior::read_result_pin728(pin)?==bytes)?;
            observations.push(json!({"case_index":index,"stage":stage,"source":pin,"readback_sha256":hex::encode(Sha256::digest(serde_json::to_vec(&summary)?)),
                "main_schema":schema,"source_unchanged":true}));
        }
    }
    require(observations.len()==40)?;
    Ok(json!({"state":"QUALIFIED752_BLOCK_BOOKMARK_MEANINGS_EXISTING40_COMMON_API_GRAPH_AND_SOURCE_STILL_INCOMPLETE",
        "observations":observations,"block_meanings_per_source":8,"unsupported_per_source":0,"crossrefs_per_source":1,
        "all_graph_round_trips_whole_reconstructions_and_independent_API_parity":true,
        "main_status":"incomplete","main_validation_report_present":false,
        "Native_started":false,"old_Native_or_249_tests_replayed":false,"full_F11_or_P09_qualified":false}))
}
#[test]
fn standalone_eight_block_ranges_are_typed_without_crossref_or_point_promotion()->Result{let b=source()?;let s=readback(&b)?;require(s["ranges"]==8&&s["crossrefs"]==0&&s["bound_edges"]==0)}
#[test]
fn source_and_field_API_versions_migrate_only_admitted_block_documents()->Result{
    for stage in["candidate","reopened"]{let b=sample(4,stage)?;let api=Product::assess_package_source(&b,doc()?,Sha256::digest(&b).into(),SourceImportLimits::default(),limits()?)?;
        require(api.validation_report().is_none()&&api.status()==ReferenceSourceStatus::Incomplete)?;let v:Value=serde_json::from_slice(&api.canonical_json(limits()?)?)?;
        require(v["schema_version"]==if stage=="candidate"{"hwpx-agent.product.reference-source-assessment/v18"}else{"hwpx-agent.product.reference-source-assessment/v17"})?;
    }Ok(())
}
#[test]
fn block_meaning_properties_and_crossref_edges_use_actual_existing_nodes()->Result{
    let b=sample(4,"reopened")?;let f=forms(&b)?;let fields=ImportedDocumentFields::import(&f)?;let g=ImportedDocumentFieldSemantics::import(&fields)?;
    let v:Value=serde_json::from_slice(&g.graph().canonical_json()?)?;
    for observation in g.observations(){if let M::BookmarkCrossReference{command}=&observation.meaning{
        let SourceBookmarkResolution::Bound{logical_target_id,..}=&command.target else{return Err("bound".into())};
        let target=fields.fields().iter().find(|r|&r.reference_id==logical_target_id).ok_or("target")?;
        let refs=v["references"].as_array().ok_or("references")?;let id=serde_json::to_value(&observation.reference_id)?;let node=serde_json::to_value(&target.begin_node_id)?;
        require(refs.iter().filter(|r|r["reference_id"]==id&&r["target_node_id"]==node).count()==1)?;
    }}require(g.receipt().block_bookmarks==8&&g.receipt().bound_bookmark_edges==1)
}
#[test]
fn changed_source_content_and_foreign_proofs_cannot_reuse_old_meaning_inventory()->Result{
    let b=source()?;let f=forms(&b)?;let fields=ImportedDocumentFields::import(&f)?;let old=SourceFieldMeaningIndex::import(&fields,limits()?)?;
    let foreign=forms(&b)?;let proof=foreign.reconstruct_source_for_verification(&b)?;require(old.verify_reconstruction(&proof).is_err())?;
    let changed=native::map_section(&b,|xml|{require(xml.contains("B643_ALPHA"))?;Ok(xml.replace("B643_ALPHA","CHANGED751"))})?;
    require(f.reconstruct_source_for_verification(&changed).is_err())?;let cf=forms(&changed)?;let fields=ImportedDocumentFields::import(&cf)?;
    let current=SourceFieldMeaningIndex::import(&fields,limits()?)?;require(current.receipt().meaning_inventory_sha256!=old.receipt().meaning_inventory_sha256)
}
#[test]
fn unknown_bookmark_prop_and_DATE_keep_legacy_profiles_and_explicit_unsupported()->Result{
    let body="<hp:p id='1'><hp:run><hp:ctrl><hp:fieldBegin id='1' type='BOOKMARK' name='UNKNOWN751'><hp:parameters cnt='1' name=''><hp:integerParam name='Prop'>3</hp:integerParam></hp:parameters></hp:fieldBegin></hp:ctrl><hp:t>PRIVATE751</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='1'/></hp:ctrl></hp:run></hp:p>";
    let date="<hp:p id='1'><hp:run><hp:ctrl><hp:fieldBegin id='1' type='DATE'/></hp:ctrl><hp:t>PRIVATE751</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='1'/></hp:ctrl></hp:run></hp:p>";
    for body in[body,date]{let b=base::package(body)?;let f=forms(&b)?;let fields=ImportedDocumentFields::import(&f)?;let index=SourceFieldMeaningIndex::import(&fields,limits()?)?;
        let graph=ImportedDocumentFieldSemantics::import(&fields)?;require(index.receipt().unsupported_meanings==1&&index.receipt().block_bookmarks==0
            &&graph.receipt().profile=="hwpx-agent.document-import-field-semantics/partial-v3"&&index.receipt().profile=="hwpx-agent.source-field-meaning-index/partial-v2")?;
        require(serde_json::to_value(index.receipt())?.get("block_bookmarks").is_none()&&serde_json::to_value(graph.receipt())?.get("block_bookmarks").is_none())?;
    }Ok(())
}
#[test]
fn malformed_boundaries_and_exhausted_budgets_never_become_typed_empty_bookmarks()->Result{
    let b=source()?;let f=forms(&b)?;let fields=ImportedDocumentFields::import(&f)?;
    let small=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig{input_bytes:1,output_bytes:1,..Default::default()})?;
    require(SourceFieldMeaningIndex::import(&fields,small).is_err())?;
    let broken=native::map_section(&b,|xml|{let i=xml.find("beginIDRef=\"").ok_or("end")?+12;let z=i+xml[i..].find('"').ok_or("end")?;
        Ok(format!("{}999999999{}",&xml[..i],&xml[z..]))})?;
    require(Product::assess_package_field_semantics(&broken,doc()?,Sha256::digest(&broken).into(),SourceImportLimits::default(),limits()?).is_err())
}
#[test]
fn duplicate_names_are_range_meanings_but_remain_ambiguous_crossref_targets()->Result{
    let b=native::map_section(&sample(4,"reopened")?,|xml|{let a="name=\"p09_block643_02\"";require(xml.matches(a).count()==1)?;Ok(xml.replacen(a,"name=\"p09_block643_01\"",1))})?;
    let f=forms(&b)?;let fields=ImportedDocumentFields::import(&f)?;let g=ImportedDocumentFieldSemantics::import(&fields)?;
    require(g.receipt().block_bookmarks==8&&g.receipt().bound_bookmark_edges==0&&g.observations().iter().any(|o|
        matches!(&o.meaning,M::BookmarkCrossReference{command}if matches!(command.target,SourceBookmarkResolution::Ambiguous))))
}
#[test]
fn newly_created_reference_keeps_exact_prior_candidate_bytes_with_new_meaning_readback()->Result{
    let v:Value=serde_json::from_str(INPUT)?;let b=source()?;let f=forms(&b)?;let fields=ImportedDocumentFields::import(&f)?;
    let(run,target)=native::select(&f,&b)?;let proof=f.reconstruct_source_for_verification(&b)?;
    let c=fields.create_bookmark_reference(&proof,SourceBookmarkInsertion{run:&run,target_id:&target,display:D::Content,hyperlink:true},limits()?,WriterLimits::default())?;
    require(c.receipt().original_selected_run_exact&&c.receipt().existing_display_text_is_not_evaluated_or_refreshed)?;
    let out=c.with_verified_bytes(|b|b.to_vec())?;require(out==prior::read_result_pin728(&v["cases"][5]["stages"]["candidate"]["pin"])?)?;
    let summary=readback(&out)?;require(summary["block_meanings"]==8&&summary["crossrefs"]==1)
}
#[test]
fn typed_metadata_never_exports_raw_names_content_or_native_authority()->Result{
    let b=sample(4,"reopened")?;let api=Product::assess_package_field_semantics(&b,doc()?,Sha256::digest(&b).into(),SourceImportLimits::default(),limits()?)?;
    let text=String::from_utf8(api.canonical_json(limits()?)?)?;require(!text.contains("p09_block643")&&!text.contains("B643_ALPHA")&&!text.contains("<hp:")
        &&text.contains("block_bookmark_range")&&text.contains("\"reference_validation_or_external_approval\":false"))?;
    let f=forms(&b)?;let fields=ImportedDocumentFields::import(&f)?;let g=ImportedDocumentFieldSemantics::import(&fields)?;
    for o in g.observations(){if let M::BlockBookmarkRange{bookmark}=&o.meaning{let encoded=serde_json::to_string(bookmark)?;
        require(matches!(bookmark.selected_source,FieldCacheSnapshot::DecodedTextNotEvaluated{..})&&!encoded.contains("B643_ALPHA")&&!encoded.contains("p09_block643"))?;
    }}Ok(())
}
