//! Original review fixture, explicit font references, cached fields and ancestor protection.
use super::*;
#[path="../../../hwpx-package/tests/support/review_scope_fixture.rs"]#[allow(dead_code)]mod fixture;
#[path="../../../hwpx-package/tests/support/document_import_review_assembly_fixture.rs"]#[allow(dead_code)]mod assembly;
#[path="../../../hwpx-package/tests/support/review_cell_output_fixture.rs"]#[allow(dead_code)]mod table;
use hwpx_agent_cli::form_product_request::stored_operations::{StoredProductRequest as Dispatch,search_mutations::SearchMutationLimits as Limits};
fn body()->String{fixture::body().replace("<hp:run>","<hp:run charPrIDRef='0'>")}
fn rich()->Result<Vec<u8>,Box<dyn Error>>{package(&body())}
fn all()->Policy{Policy{include_hidden_explanations:true,include_memo_bodies:true}}
fn section(bytes:&[u8])->Result<String,Box<dyn Error>>{Ok(String::from_utf8(archive::read_part(bytes,"Contents/section0.xml")?)?)}
fn region_value(inv:&Value,region:&str,a:usize,b:usize)->Result<Value,Box<dyn Error>>{
    let i=inv["block_regions"].as_array().ok_or("regions")?.iter().enumerate().find(|(i,r)|r.as_str()==Some(region)
        &&inv["inventory"]["blocks"][*i]["normalized_scalars"].as_u64().is_some_and(|n|n>=b as u64)).map(|(i,_)|i).ok_or("nonempty region")?;
    at_block(inv,i,a,b)
}
fn at_block(inv:&Value,i:usize,a:usize,b:usize)->Result<Value,Box<dyn Error>>{
    let block=&inv["inventory"]["blocks"][i];let hash:[u8;32]=serde_json::from_value(inv["inventory"]["index"]["index_sha256"].clone())?;
    Ok(json!({"coordinate_space":"index_nfc_unicode_scalars","index_sha256":hex::encode(hash),
        "start":{"paragraph_handle":block["paragraph_handle"],"block_index":block["block_index"],"normalized_scalar":a},
        "end":{"paragraph_handle":block["paragraph_handle"],"block_index":block["block_index"],"normalized_scalar":b}}))
}
fn select(p:&Provider<'_>,v:&mut Value,region:&str,policy:Policy)->R{
    let inv=inventory(p,v)?;v["selector"]["scope"]=json!("selection");v["selector"]["range"]=region_value(&inv,region,0,1)?;v["operation"]["review_policy"]=json!(policy);Ok(())
}
fn expect_protection(bytes:&[u8],region:&str)->R{
    let s=StoredFixture::new(bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut v=request(&s,bytes)?;select(&p,&mut v,region,all())?;
    let result=prepare!(&p,&v);assert!(!result.is_ok(),"FONT_TRACKING_UNEXPECTED_ACCEPTANCE");assert!(matches!(&result,Err(E::Stored(Stored::Output(SourceError::Compile(Compile::Protection))))),"{result:?}");Ok(())
}
fn positive(region:&str)->R{
    let bytes=rich()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut v=request(&s,&bytes)?;select(&p,&mut v,region,all())?;let out=prepare!(&p,&v)?;
    out.verify(&p,5)?;let output=out.with_verified_bytes(&p,5,<[u8]>::to_vec)?;let text=section(&output)?;
    assert!(text.contains("CACHE FROZEN")&&text.contains("PRIVATE-AUTHOR")&&text.contains("<hp:lineBreak/>")&&text.contains("editable='0'"));
    assert_eq!(out.receipt().stored.output.changed_source_scalars,1);let inv=out.with_verified_edit_inventory(&p,5,Clone::clone)?;assert_eq!(inv.header_effects().count(),2);assert_eq!(inv.body_splices().count(),1);
    assert!(refs(&output)?.iter().filter(|(text,_,_)|text.contains("CACHE FROZEN")||text.contains("TAIL")).all(|(_,style,_)|*style==0));
    assert!(refs(&output)?.iter().any(|(_,style,_)|*style!=0));assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);Ok(())
}
#[test]fn included_hidden_font_selection_preserves_cache_metadata_and_controls()->R{positive("hidden_explanation")}
#[test]fn included_read_only_memo_payload_is_not_mistaken_for_cached_result()->R{positive("memo_body")}
#[test]
fn excluded_hidden_selection_is_no_matches_not_an_implicit_body_fallback()->R{
    let bytes=rich()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut v=request(&s,&bytes)?;select(&p,&mut v,"hidden_explanation",Policy{include_hidden_explanations:false,include_memo_bodies:true})?;
    assert!(matches!(prepare!(&p,&v),Err(E::Stored(Stored::Output(SourceError::Compile(Compile::NoMatches))))));Ok(())
}
#[test]
fn excluded_memo_selection_is_no_matches_not_a_cached_result_target()->R{
    let bytes=rich()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut v=request(&s,&bytes)?;select(&p,&mut v,"memo_body",Policy{include_hidden_explanations:true,include_memo_bodies:false})?;
    assert!(matches!(prepare!(&p,&v),Err(E::Stored(Stored::Output(SourceError::Compile(Compile::NoMatches))))));Ok(())
}
#[test]
fn ordinary_prefix_outside_field_cache_can_change_without_restyling_cached_text()->R{
    let bytes=rich()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut v=request(&s,&bytes)?;select(&p,&mut v,"body_and_notes",policy())?;
    let out=prepare!(&p,&v)?;let values=out.with_verified_bytes(&p,5,refs)??;assert!(values.iter().any(|(_,style,_)|*style!=0));assert!(values.iter().filter(|(text,_,_)|text.contains("CACHE FROZEN")).all(|(_,style,_)|*style==0));Ok(())
}
#[test]
fn whole_document_does_not_silently_skip_or_restyle_cached_field_results()->R{
    let bytes=rich()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut v=request(&s,&bytes)?;v["operation"]["review_policy"]=json!(all());
    assert!(matches!(prepare!(&p,&v),Err(E::Stored(Stored::Output(SourceError::Compile(Compile::FieldContent))))));Ok(())
}
#[test]
fn nested_date_inside_memo_is_rejected_by_existing_source_admission()->R{
    let text=body().replace("<hp:t>MEMO K K</hp:t>","<hp:ctrl><hp:fieldBegin id='18' type='DATE'/></hp:ctrl><hp:t>MEMO K K</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='18'/></hp:ctrl>");
    let bytes=package(&text)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);
    assert!(matches!(p.import_actual_forms(s.head,4),Err(hwpx_agent_cli::form_stored_provider::actual_import::StoredActualFormImportError::Import(hwpx_package::document_import::forms::FormImportError::Body(_)))));Ok(())
}
#[test]
fn outer_date_field_still_protects_an_inner_memo_payload()->R{
    let content=body().replacen("<hp:run charPrIDRef='0'>","<hp:run charPrIDRef='0'><hp:ctrl><hp:fieldBegin id='19' type='DOC_DATE'/></hp:ctrl>",1);
    let text=content.replace("<hp:t>TAIL</hp:t>","<hp:t>TAIL</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='19'/></hp:ctrl>");let bytes=package(&text)?;
    let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut v=request(&s,&bytes)?;select(&p,&mut v,"memo_body",all())?;
    assert!(matches!(prepare!(&p,&v),Err(E::Stored(Stored::Output(SourceError::Compile(Compile::FieldContent))))));Ok(())
}
#[test]
fn invalid_paragraph_lock_attributes_reject_before_hidden_selection()->R{reject_invalid_lock(&package(&body().replacen("<hp:p id='1'>","<hp:p id='1' lock='1'>",1))?,true)}
#[test]
fn invalid_memo_paragraph_lock_attributes_reject_at_import()->R{reject_invalid_lock(&package(&body().replace("<hp:p id='12'>","<hp:p id='12' lock='1'>"))?,false)}
#[test]
fn unselected_invalid_paragraph_lock_is_still_source_import_error()->R{
    let bytes=package(&body().replace("<hp:p id='11'>","<hp:p id='11' lock='1'>"))?;
    reject_invalid_lock(&bytes,false)
}
#[test]
fn direct_run_tracking_marker_is_rejected_for_both_zero_and_nonzero_identifiers()->R{
    for id in ["0","1"]{expect_protection(&package(&body().replace("<hp:p id='11'><hp:run charPrIDRef='0'>",&format!("<hp:p id='11'><hp:run charPrIDRef='0' charTcId='{id}'>")))?,"hidden_explanation")?;}Ok(())
}
#[test]
fn ancestor_run_tracking_marker_cannot_be_bypassed_by_selecting_hidden_payload()->R{
    for id in ["0","1"]{expect_protection(&package(&body().replacen("<hp:run charPrIDRef='0'>",&format!("<hp:run charPrIDRef='0' charTcId='{id}'>"),1))?,"hidden_explanation")?;}Ok(())
}
#[test]
fn paragraph_tracking_marker_protects_selected_ordinary_text()->R{
    for id in ["0","1"]{expect_protection(&package(&body().replace("<hp:p id='1'>",&format!("<hp:p id='1' paraTcId='{id}'>")))?,"body_and_notes")?;}Ok(())
}
#[test]
fn ancestor_paragraph_tracking_marker_protects_selected_memo_payload()->R{
    for id in ["0","1"]{expect_protection(&package(&body().replace("<hp:p id='1'>",&format!("<hp:p id='1' paraTcId='{id}'>")))?,"memo_body")?;}Ok(())
}
#[test]
fn review_font_common_compiler_uses_actual_graph_owner_and_keeps_storage_unchanged()->R{
    let bytes=rich()?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut v=request(&s,&bytes)?;select(&p,&mut v,"memo_body",all())?;
    let out=Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,Limits::standard()?,4)?;let source=p.import_actual_forms(s.head,4)?;
    let snapshot=domain_ir::SelectorSnapshot::build(source.imported().graph(),domain_ir::RevisionId::parse(s.head.revision_id().ok_or("head")?.public_id())?,Default::default())?;
    for op in out.compiled().operations(){let target=snapshot.resolve_one(&snapshot.expectation(),&domain_ir::Selector::by_logical_id(op.target().node_id().clone()))?;assert_eq!(&target,op.target());}
    out.verify(&p,5)?;assert!(out.require_current_product_route(&p,5).is_err());assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);Ok(())
}
// Valid native table protection fixtures and exact source-import rejection begin.
fn reject_invalid_lock(bytes:&[u8],root:bool)->R{
    use hwpx_agent_cli::form_stored_provider::actual_import::StoredActualFormImportError as Import;
    let s=StoredFixture::new(bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let v=request(&s,bytes)?;
    let result=prepare!(&p,&v);
    if root{assert!(matches!(result,Err(E::Import(Import::Import(hwpx_package::document_import::forms::FormImportError::Body(_))))));}
    else{assert!(matches!(&result,Err(E::Stored(Stored::Output(SourceError::Source)))),"{result:?}");}Ok(())
}
fn table_body()->String{body().replace("<hp:t>MEMO K K</hp:t>",&format!("<hp:t>MEMO K K</hp:t>{}",table::table(300)))}
fn select_cell(p:&Provider<'_>,v:&mut Value)->R{
    let source=p.import_actual_forms(rev::RevisionHead::new(Some(rev::RevisionId::parse(v["base_revision"].as_str().ok_or("revision")?)?),v["expected_head_generation"].as_u64().ok_or("generation")?)?,4)?;
    let part=source.imported().source().parts().iter().find(|p|p.path().as_str()=="Contents/section0.xml").ok_or("part")?;let xml=part.xml().ok_or("xml")?;
    let(first,cell)=xml.elements().iter().enumerate().find(|(_,n)|n.name().local_name()=="tc").ok_or("cell")?;let stop=cell.outer_span().ok_or("span")?.end();
    let i=xml.elements().iter().enumerate().skip(first+1).find(|(_,n)|n.name().local_name()=="p"&&n.start_tag_span().start()<stop).ok_or("cell paragraph")?.0;
    let anchor=&part.element_anchor(i).ok_or("anchor")?.opaque_handle;let inv=inventory(p,v)?;
    let block=inv["inventory"]["blocks"].as_array().ok_or("blocks")?.iter().position(|b|b["paragraph_handle"].as_str()==Some(anchor.as_str())&&b["normalized_scalars"].as_u64().is_some_and(|n|n>0)).ok_or("cell block")?;
    v["selector"]["scope"]=json!("selection");v["selector"]["range"]=at_block(&inv,block,0,1)?;v["operation"]["review_policy"]=json!(all());Ok(())
}
fn blocked_cell(mode:usize)->R{
    let text=match mode{0=>table_body().replace("lock='0'","lock='1'"),1=>table_body().replace("hasMargin='0' protect='0'","hasMargin='0' protect='1'"),_=>table_body().replace("heightRelTo='ABSOLUTE' protect='0'","heightRelTo='ABSOLUTE' protect='1'")};
    let bytes=package(&text)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut v=request(&s,&bytes)?;select_cell(&p,&mut v)?;
    let result=prepare!(&p,&v);assert!(matches!(&result,Err(E::Stored(Stored::Output(SourceError::Compile(Compile::Protection))))),"{result:?}");Ok(())
}
#[test]fn native_table_lock_protects_selected_memo_cell()->R{blocked_cell(0)}
#[test]fn native_cell_protect_flag_protects_selected_memo_cell()->R{blocked_cell(1)}
#[test]fn native_table_size_protect_flag_protects_selected_memo_cell()->R{blocked_cell(2)}
#[test]
fn unselected_native_locked_table_preserves_flags_and_all_cell_text()->R{
    let bytes=package(&table_body().replace("lock='0'","lock='1'"))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut v=request(&s,&bytes)?;select(&p,&mut v,"body_and_notes",policy())?;
    let out=prepare!(&p,&v)?;let text=out.with_verified_bytes(&p,5,section)??;assert!(text.contains("lock='1'")&&text.contains("CELL-OLD")&&text.contains("OTHER-CELL"));Ok(())
}
// Valid native table protection fixtures and exact source-import rejection end.
// Ancestor tracking on the explicit text axis and common compiler begin.
fn text_tracking(region:&str,paragraph:bool)->R{
    for id in ["0","1"]{let text=body().replace("<hp:t>","<hp:t charStyleIDRef='1'>");let text=if paragraph{text.replace("<hp:p id='1'>",&format!("<hp:p id='1' paraTcId='{id}'>"))}
        else{text.replacen("<hp:run charPrIDRef='0'>",&format!("<hp:run charPrIDRef='0' charTcId='{id}'>"),1)};
        let bytes=package(&text)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut v=request(&s,&bytes)?;select(&p,&mut v,region,all())?;
        v["operation"]["axis"]=json!("text_style");v["operation"]["query"]=json!(name(&bytes,1)?);
        assert!(matches!(prepare!(&p,&v),Err(E::Stored(Stored::Output(SourceError::Compile(Compile::Protection))))));}Ok(())
}
#[test]fn text_axis_inherits_tracking_from_outer_run_in_hidden_body()->R{text_tracking("hidden_explanation",false)}
#[test]fn text_axis_inherits_tracking_from_outer_paragraph_in_memo_body()->R{text_tracking("memo_body",true)}
#[test]fn text_axis_inherits_tracking_for_ordinary_paragraph_text()->R{text_tracking("body_and_notes",true)}
#[test]
fn common_font_compiler_rejects_tracked_review_ancestor_before_plan()->R{
    use hwpx_agent_cli::form_product_request::stored_operations::{StoredProductOperationError as OperationError,search_mutations::SearchMutationError as MutationError,
        compiled_search::CompiledSearchError as PlanError};
    let bytes=package(&body().replacen("<hp:run charPrIDRef='0'>","<hp:run charPrIDRef='0' charTcId='0'>",1))?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;writer!(s,actor,p);let mut v=request(&s,&bytes)?;select(&p,&mut v,"hidden_explanation",all())?;
    let result=Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,Limits::standard()?,4);
    assert!(matches!(result,Err(PlanError::Request(OperationError::SearchMutation(MutationError::Font(E::Stored(Stored::Output(SourceError::Compile(Compile::Protection)))))))));
    assert_eq!(s.revisions.head(&s.revision_context,s.project,s.branch)?,s.head);assert_eq!(s.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),2);Ok(())
}
// Ancestor tracking on the explicit text axis and common compiler end.
