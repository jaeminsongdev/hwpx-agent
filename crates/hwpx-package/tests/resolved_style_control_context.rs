//! Enclosing control styles cannot silently become resolved direct character formatting.
use super::*;
fn hidden(id:u32)->String {review_body().replace("<hp:ctrl><hp:hiddenComment>",&format!("<hp:ctrl charStyleIDRef='{id}'><hp:hiddenComment>"))}
fn memo(id:u32)->String {review_body().replace("<hp:ctrl><hp:fieldBegin",&format!("<hp:ctrl charStyleIDRef='{id}'><hp:fieldBegin"))}
#[test]
fn control_style_hidden_body_requires_resolution_even_with_direct_run_properties()->TestResult {
    for id in[0,1] {let raw=fixture::package(&hidden(id))?;let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;
        for query in["K","ABSENT"] {match i.find_resolved_style(q(query),Scope::Document,all(),bold()) {Err(RE::Unresolved(c))=>{
            assert_eq!(c.unresolved_text_style_segments,1);assert_eq!(c.missing_run_segments,0);assert_eq!(c.resolved_character_segments+1,c.selected_text_segments);
        },_=>panic!("enclosing control style cannot be assumed overridden")}}
    }Ok(())
}
#[test]
fn control_style_memo_retains_original_admission_rejection_and_hidden_paragraph_axis_is_independent()->TestResult {
    for id in[0,1] {let raw=fixture::package(&memo(id))?;let original=Sha256::digest(&raw);
        let error=forms(&raw).expect_err("MEMO control style is outside original admission");
        assert!(matches!(error.downcast_ref::<hwpx_package::document_import::forms::FormImportError>(),Some(hwpx_package::document_import::forms::FormImportError::Body(_))));
        assert_eq!(Sha256::digest(&raw),original);
    }
    let raw=fixture::package(&hidden(1))?;let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;
    let found=i.find_resolved_style(q("K"),Scope::Document,all(),Filter {alignment:Some(Align::Right),..Default::default()})?;
    assert_eq!(found.search().result().matches().len(),6);assert_eq!(found.coverage().unresolved_text_style_segments,1);assert!(found.coverage().requested_axes_complete());Ok(())
}
#[test]
fn control_style_policy_excludes_context_before_resolution_without_leaking_into_siblings()->TestResult {
    for body in[hidden(0),hidden(1)] {let raw=fixture::package(&body)?;let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;
        let found=i.find_resolved_style(q("K"),Scope::Document,Policy::default(),bold())?;assert_eq!(found.search().result().matches().len(),2);
        assert_eq!(found.coverage().unresolved_text_style_segments,0);assert_eq!(found.coverage().resolved_character_segments,found.coverage().selected_text_segments);
    }Ok(())
}
#[test]
fn control_style_exact_selected_main_body_does_not_include_descendant_control_context()->TestResult {
    let raw=fixture::package(&hidden(1))?;let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;let inv=i.scope_inventory()?;let b=&inv.inventory.blocks[0];
    let start=Boundary {paragraph_handle:b.paragraph_handle.clone(),block_index:b.block_index,normalized_scalar:0};let end=Boundary {normalized_scalar:8,..start.clone()};
    let found=i.find_resolved_style(q("K"),Scope::Selection {index_sha256:inv.inventory.index.index_sha256,start:&start,end:&end},all(),bold())?;
    assert_eq!(found.search().result().matches().len(),2);assert_eq!(found.coverage().unresolved_text_style_segments,0);Ok(())
}
#[test]
fn control_style_text_and_control_references_count_uncertain_segments_once()->TestResult {
    let body=hidden(0).replace("<hp:t>HIDDEN","<hp:t charStyleIDRef='0'>HIDDEN");let raw=fixture::package(&body)?;let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;
    match i.find_resolved_style(q("ABSENT"),Scope::Document,all(),bold()) {Err(RE::Unresolved(c))=>assert_eq!(c.unresolved_text_style_segments,1),_=>panic!("one unresolved segment expected")};Ok(())
}
#[test]
fn control_style_namespace_alias_is_recognized_but_foreign_attribute_is_not_reinterpreted()->TestResult {
    let alias=hidden(1).replace("<hp:ctrl charStyleIDRef='1'><hp:hiddenComment>","<z:ctrl xmlns:z='http://www.hancom.co.kr/hwpml/2011/paragraph' charStyleIDRef='1'><hp:hiddenComment>")
        .replace("</hp:hiddenComment></hp:ctrl>","</hp:hiddenComment></z:ctrl>");
    let raw=fixture::package(&alias)?;let f=forms(&raw)?;assert!(matches!(f.source_review_scope_index(&raw,Default::default())?.find_resolved_style(q("K"),Scope::Document,all(),bold()),Err(RE::Unresolved(_))));
    let foreign=review_body().replace("<hp:ctrl><hp:hiddenComment>","<hp:ctrl xmlns:x='urn:foreign-style' x:charStyleIDRef='1'><hp:hiddenComment>");
    let raw=fixture::package(&foreign)?;let f=forms(&raw)?;assert_eq!(f.source_review_scope_index(&raw,Default::default())?.find_resolved_style(q("K"),Scope::Document,all(),bold())?.search().result().matches().len(),6);Ok(())
}
#[test]
fn control_style_many_descendant_runs_share_context_and_do_not_hide_unknowns_from_absent_query()->TestResult {
    let runs=(0..128).map(|_|"<hp:run charPrIDRef='1'><hp:t>K</hp:t></hp:run>").collect::<String>();let body=hidden(1)
        .replace("<hp:run charPrIDRef='1'><hp:t>HIDDEN K K<hp:lineBreak/></hp:t></hp:run>",&runs);
    let raw=fixture::package(&body)?;let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;
    match i.find_resolved_style(q("ABSENT"),Scope::Document,all(),bold()) {Err(RE::Unresolved(c))=>{assert_eq!(c.unresolved_text_style_segments,128);assert_eq!(c.observed_segment_visits,c.selected_text_segments);},_=>panic!("all contextual segments must remain unresolved")};Ok(())
}
#[test]
fn control_style_empty_selection_inside_uncertain_body_does_not_invent_contributing_segments()->TestResult {
    let raw=fixture::package(&hidden(1))?;let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;let inv=i.scope_inventory()?;
    let n=inv.block_regions.iter().position(|r|*r==hwpx_package::document_import::search::reviews::SourceTextRegion::HiddenExplanation).ok_or("hidden")?;let b=&inv.inventory.blocks[n];
    let cut=Boundary {paragraph_handle:b.paragraph_handle.clone(),block_index:b.block_index,normalized_scalar:0};let found=i.find_resolved_style(q("K"),
        Scope::Selection {index_sha256:inv.inventory.index.index_sha256,start:&cut,end:&cut},all(),bold())?;
    assert_eq!(found.coverage().selected_text_segments,0);assert_eq!(found.coverage().unresolved_text_style_segments,0);assert!(found.search().result().matches().is_empty());Ok(())
}
