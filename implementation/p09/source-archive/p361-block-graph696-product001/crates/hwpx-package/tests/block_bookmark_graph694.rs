//! Same-source block edges; unknown meanings, ambiguity and partial state remain.
use domain_ir::{DocumentGraph,DocumentGraphLimits,ReferenceAuxiliaryLimits};
use hwpx_package::document_import::fields::{ImportedDocumentFields,
    bookmark_crossref::{SourceBookmarkResolution,SourceBookmarkCrossReferenceBindings},
    semantics::ImportedDocumentFieldSemantics};
use std::error::Error;
#[path="support/document_import_field_fixture.rs"]
#[allow(dead_code)]mod fixture;
#[path="support/document_import_bookmark_fixture.rs"]
#[allow(dead_code)]mod point;
type Result<T=()>=std::result::Result<T,Box<dyn Error>>;
fn block(id:u32,name:&str)->String{format!("<hp:ctrl><hp:fieldBegin id='{id}' type='BOOKMARK' name='{name}' fieldid='999'><hp:parameters cnt='1' name=''><hp:integerParam name='Prop'>2</hp:integerParam></hp:parameters></hp:fieldBegin></hp:ctrl><hp:t>selected</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='{id}' fieldid='999'/></hp:ctrl>")}
fn xref(name:&str,display:u8,link:bool)->String{format!("<hp:ctrl><hp:fieldBegin id='50' type='CROSSREF'><hp:parameters cnt='1'><hp:stringParam name='Command'>?{name};6;{display};{};0</hp:stringParam></hp:parameters></hp:fieldBegin></hp:ctrl><hp:t>unverified cache</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='50'/></hp:ctrl>",u8::from(link))}
fn check(body:&str,expected_bound:bool)->Result{
    let raw=fixture::package(&format!("<hp:p id='1'><hp:run>{body}</hp:run></hp:p>"))?;
    let forms=fixture::forms(&raw,"block-graph694")?;let fields=ImportedDocumentFields::import(&forms)?;
    let limits=ReferenceAuxiliaryLimits::new(Default::default())?;
    let bindings=SourceBookmarkCrossReferenceBindings::import(&fields,limits)?;assert_eq!(bindings.bindings().len(),1);
    let binding=&bindings.bindings()[0];let semantics=ImportedDocumentFieldSemantics::import(&fields)?;
    let bytes=semantics.graph().canonical_json()?;let graph:serde_json::Value=serde_json::from_slice(&bytes)?;
    let id=serde_json::to_value(&binding.field_reference_id)?;
    let rows:Vec<_>=graph["references"].as_array().ok_or("references")?.iter().filter(|v|v["reference_id"]==id).collect();assert_eq!(rows.len(),1);
    if expected_bound{
        let SourceBookmarkResolution::Bound{logical_target_id,..}=&binding.target else{return Err("missing Bound".into())};
        let target=fields.fields().iter().find(|v|&v.reference_id==logical_target_id&&v.native_kind=="BOOKMARK").ok_or("target")?;
        assert_eq!(rows[0]["target_node_id"],serde_json::to_value(&target.begin_node_id)?);
        assert_ne!(rows[0]["target_node_id"],serde_json::to_value(&target.end_node_id)?);
        assert_eq!(semantics.receipt().bound_bookmark_edges,1);
    }else{assert!(rows[0]["target_node_id"].is_null());assert_eq!(semantics.receipt().bound_bookmark_edges,0);}
    assert_eq!(semantics.verify_source(&raw)?,*semantics.receipt());
    assert_eq!(DocumentGraph::from_json(&bytes,DocumentGraphLimits::default())?,*semantics.graph());
    assert_eq!(semantics.observations().len(),fields.fields().len());
    Ok(())
}
#[test]fn actual_block_begin_is_target_for_all_four_displays_and_both_link_options()->Result{
    for d in 0..4{for link in[false,true]{check(&(block(1,"b")+&xref("b",d,link)),true)?;}}Ok(())
}
#[test]fn missing_name_never_binds_unrelated_bookmark()->Result{check(&(block(1,"b")+&xref("missing",2,false)),false)}
#[test]fn duplicate_block_names_do_not_choose_first_field()->Result{check(&(block(1,"b")+&block(2,"b")+&xref("b",2,false)),false)}
#[test]fn cross_family_name_collision_does_not_choose_point_or_block()->Result{check(&(point::marker("b")+&block(1,"b")+&xref("b",2,false)),false)}
#[test]fn later_same_paragraph_block_does_not_replace_selected_target()->Result{check(&(block(1,"chosen")+&block(2,"other")+&xref("chosen",2,true)),true)}
#[test]fn opaque_bookmark_kind_without_prop2_cannot_become_bound_target()->Result{
    let text=block(1,"b").replace(">2</hp:integerParam>",">1</hp:integerParam>")+&xref("b",2,false);
    let raw=fixture::package(&format!("<hp:p id='1'><hp:run>{text}</hp:run></hp:p>"))?;
    let forms=fixture::forms(&raw,"invalid-block694")?;let fields=ImportedDocumentFields::import(&forms)?;
    assert!(ImportedDocumentFieldSemantics::import(&fields).is_err());Ok(())
}
