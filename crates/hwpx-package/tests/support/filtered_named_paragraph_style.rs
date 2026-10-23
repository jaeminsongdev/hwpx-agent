//! Whole-paragraph source predicates, original writer bytes and preservation, no target execution.
use super::*;
use hwpx_package::document_import::search::{inspection::definitions::CharacterDefinitionSource as CharacterAxis,
    replacement::atoms::styles::paragraphs::named::filtered::{SourceFilteredNamedParagraphStyleCandidate as Filtered,FILTERED_NAMED_PARAGRAPH_STYLE_PROFILE as PROFILE}};
fn lower_filtered(bytes:&[u8],filter:Filter)->Result<Filtered,N>{forms(bytes).map_err(|_|N::Source)?.lower_filtered_named_paragraph_style_candidate(bytes,q(),Scope::Document,all(),filter,Default::default(),Default::default())}
fn output_filtered(bytes:&[u8],out:&Filtered)->Result<Vec<u8>,Box<dyn Error>>{
    let after=out.with_verified_bytes(<[u8]>::to_vec)?;let mut a=BoundedZipReader::open(Cursor::new(bytes),Default::default())?;let mut b=BoundedZipReader::open(Cursor::new(&after),Default::default())?;
    assert_eq!(a.entries().len(),b.entries().len());for i in 0..a.entries().len(){let path=a.entries()[i].path.clone();if path.as_str()=="Contents/section0.xml"{continue;}
        let j=b.entries().iter().position(|e|e.path==path).ok_or("part")?;assert_eq!(a.read_entry(i)?,b.read_entry(j)?);}
    assert_eq!(out.receipt().profile,PROFILE);assert!(!out.receipt().full_style_native_or_service_authority);assert!(!out.receipt().style_filter.effective_style_visibility_or_execution_authority);
    assert_eq!(out.receipt().source.output_package_sha256,<[u8;32]>::from(Sha256::digest(&after)));Ok(after)
}
fn declared(f:Declared)->Filter{Filter::Declared(f)}
#[test]
fn declared_paragraph_axes_select_only_original_matching_named_reference()->TestResult{
    let bytes=package(&(para(1,0,"A")+&para(2,1,"B")))?;let filter=declared(Declared{paragraph_property:Some(0),paragraph_style:Some(0),..Default::default()});
    let out=lower_filtered(&bytes,filter)?;assert_eq!(references(&output_filtered(&bytes,&out)?)?,vec![(1,Some(0),Some(2)),(2,Some(0),Some(1))]);
    assert_eq!(out.receipt().style_filter.selected_paragraphs,1);assert_eq!(out.receipt().style_filter.filtered_paragraphs,1);assert!(out.receipt().style_filter.definitions.is_none());Ok(())
}
#[test]
fn any_mismatching_run_excludes_the_entire_paragraph_not_only_that_run()->TestResult{
    let mixed=para(1,0,"A</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t>B");let bytes=package(&(mixed+&para(2,1,"C")))?;
    let out=lower_filtered(&bytes,declared(Declared{run_character_property:Some(0),..Default::default()}))?;
    assert_eq!(references(&output_filtered(&bytes,&out)?)?,vec![(1,Some(0),Some(0)),(2,Some(0),Some(2))]);assert_eq!(out.receipt().style_filter.examined_source_segments,3);Ok(())
}
#[test]
fn text_reference_axis_is_not_run_or_named_style_axis()->TestResult{
    let first=para(1,0,"A").replace("<hp:t>","<hp:t charStyleIDRef='1'>");let second=para(2,1,"B").replace("<hp:t>","<hp:t charStyleIDRef='0'>");let bytes=package(&(first+&second))?;
    let out=lower_filtered(&bytes,declared(Declared{text_character_style:Some(1),..Default::default()}))?;
    assert_eq!(references(&output_filtered(&bytes,&out)?)?,vec![(1,Some(0),Some(2)),(2,Some(0),Some(1))]);Ok(())
}
#[test]
fn definition_character_axis_uses_original_typed_properties_and_preserves_header()->TestResult{
    let first=para(1,0,"A").replace("charPrIDRef='0'","charPrIDRef='1'");let bytes=package(&(first+&para(2,1,"B")))?;
    let out=lower_filtered(&bytes,Filter::Definition(Definition{character_source:Some(CharacterAxis::RunProperty),bold:Some(true),..Default::default()}))?;
    assert_eq!(references(&output_filtered(&bytes,&out)?)?,vec![(1,Some(0),Some(2)),(2,Some(0),Some(1))]);assert!(out.receipt().style_filter.definitions.is_some());Ok(())
}
#[test]
fn definition_paragraph_axis_is_explicit_and_combines_with_character_axis()->TestResult{
    let first=para(1,0,"A").replace("paraPrIDRef='0'","paraPrIDRef='1'").replace("charPrIDRef='0'","charPrIDRef='1'");let bytes=package(&(first+&para(2,1,"B")))?;
    let filter=Filter::Definition(Definition{paragraph_source:Some(Axis::DirectProperty),alignment:Some(Alignment::Right),character_source:Some(CharacterAxis::RunProperty),italic:Some(true),..Default::default()});
    let out=lower_filtered(&bytes,filter)?;assert_eq!(references(&output_filtered(&bytes,&out)?)?,vec![(1,Some(1),Some(2)),(2,Some(0),Some(1))]);Ok(())
}
#[test]
fn combined_declared_axes_are_conjunctive_not_alternative()->TestResult{
    let first=para(1,0,"A").replace("charPrIDRef='0'","charPrIDRef='1'");let bytes=package(&(first+&para(2,1,"B")))?;
    assert!(matches!(lower_filtered(&bytes,declared(Declared{paragraph_style:Some(0),run_character_property:Some(0),..Default::default()})),Err(N::NoMatches)));Ok(())
}
#[test]
fn missing_reference_never_matches_implicit_zero_or_named_style_fallback()->TestResult{
    let bytes=package(&para(1,0,"A"))?;
    assert!(matches!(lower_filtered(&bytes,declared(Declared{text_character_style:Some(0),..Default::default()})),Err(N::NoMatches)));
    assert!(matches!(lower_filtered(&bytes,Filter::Definition(Definition{character_source:Some(CharacterAxis::TextStyle),bold:Some(false),..Default::default()})),Err(N::NoMatches)));Ok(())
}
#[test]
fn invalid_empty_or_axisless_filter_is_rejected_before_stale_source_check()->TestResult{
    let bytes=package(&para(1,0,"A"))?;let f=forms(&bytes)?;
    for filter in [declared(Declared::default()),Filter::Definition(Definition{bold:Some(true),..Default::default()}),Filter::Definition(Definition{paragraph_source:Some(Axis::DirectProperty),..Default::default()})]{
        assert!(matches!(f.lower_filtered_named_paragraph_style_candidate(&[],q(),Scope::Document,all(),filter,Default::default(),Default::default()),Err(N::Search(Search::Filter))));}Ok(())
}
#[test]
fn empty_run_open_empty_text_and_self_closing_text_are_not_vacuous_filter_matches()->TestResult{
    let empty="<hp:p id='1' paraPrIDRef='0' styleIDRef='0'><hp:run charPrIDRef='0'/></hp:p><hp:p id='2' paraPrIDRef='0' styleIDRef='0'><hp:run charPrIDRef='0'><hp:t></hp:t></hp:run></hp:p><hp:p id='3' paraPrIDRef='0' styleIDRef='0'><hp:run charPrIDRef='0'><hp:t/></hp:run></hp:p>";
    let bytes=package(&(empty.to_owned()+&para(4,1,"A")))?;let out=lower_filtered(&bytes,filter())?;
    assert_eq!(out.receipt().style_filter.empty_paragraphs,3);assert_eq!(out.receipt().source.changes.len(),1);assert_eq!(lower(&bytes,q(),Scope::Document)?.receipt().changes.len(),4);
    assert_eq!(references(&output_filtered(&bytes,&out)?)?,vec![(1,Some(0),Some(0)),(2,Some(0),Some(0)),(3,Some(0),Some(0)),(4,Some(0),Some(2))]);
    assert!(matches!(lower_filtered(&package(empty)?,filter()),Err(N::NoMatches)));Ok(())
}
#[test]
fn nfc_multi_run_contributors_must_all_match_before_whole_paragraph_change()->TestResult{
    let mixed=para(1,0,"ᄀ</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t>ᅡᆨ");let bytes=package(&(mixed+&para(2,1,"각")))?;
    let out=lower_filtered(&bytes,declared(Declared{run_character_property:Some(0),..Default::default()}))?;
    assert_eq!(references(&output_filtered(&bytes,&out)?)?,vec![(1,Some(0),Some(0)),(2,Some(0),Some(2))]);assert_eq!(out.receipt().style_filter.examined_normalized_units,2);Ok(())
}
#[test]
fn whole_scope_and_partial_selection_guards_apply_before_filter_can_widen()->TestResult{
    let bytes=package(&(para(1,0,"ABC")+&para(2,1,"DEF")))?;let f=forms(&bytes)?;let inv=f.source_review_scope_index(&bytes,Default::default())?.scope_inventory()?;
    let b=&inv.inventory.blocks[0];let start=Boundary{paragraph_handle:b.paragraph_handle.clone(),block_index:b.block_index,normalized_scalar:0};let end=Boundary{normalized_scalar:3,..start.clone()};
    let ids=[inv.inventory.nodes.iter().find(|n|n.source_handle==b.paragraph_handle).ok_or("node")?.node_id.clone()];
    for(scope,total)in [(Scope::Document,2),(Scope::Section(&inv.inventory.section_ids),2),(Scope::NodeSet(&ids),1),(Scope::Selection{index_sha256:inv.inventory.index.index_sha256,start:&start,end:&end},1)]{
        let out=f.lower_filtered_named_paragraph_style_candidate(&bytes,q(),scope,all(),filter(),Default::default(),Default::default())?;assert_eq!(out.receipt().source.changes.len(),total);output_filtered(&bytes,&out)?;}
    let clipped=Boundary{normalized_scalar:1,..start};assert!(matches!(f.lower_filtered_named_paragraph_style_candidate(&bytes,q(),Scope::Selection{index_sha256:inv.inventory.index.index_sha256,start:&clipped,end:&end},all(),filter(),Default::default(),Default::default()),Err(N::Paragraph(E::IncompleteParagraphScope))));Ok(())
}
#[test]
fn all_original_blocks_must_match_filter_without_ignoring_control_boundary()->TestResult{
    let first=para(1,0,"A</hp:t><hp:ctrl><hp:bookmark name='MARK'/></hp:ctrl><hp:t charStyleIDRef='1'>B");let second=para(2,1,"C").replace("<hp:t>","<hp:t charStyleIDRef='1'>");
    let bytes=package(&(first+&second))?;let out=lower_filtered(&bytes,declared(Declared{text_character_style:Some(1),..Default::default()}))?;
    assert_eq!(references(&output_filtered(&bytes,&out)?)?,vec![(1,Some(0),Some(0)),(2,Some(0),Some(2))]);Ok(())
}
#[test]
fn hidden_and_memo_policies_precede_filter_and_outer_field_cache_is_unchanged()->TestResult{
    let body=review::body().replace("<hp:p id='1'>","<hp:p id='1' paraPrIDRef='0' styleIDRef='2'>")
        .replace("<hp:p id='11'>","<hp:p id='11' paraPrIDRef='0' styleIDRef='0'>").replace("<hp:p id='12'>","<hp:p id='12' paraPrIDRef='0' styleIDRef='1'>");let bytes=package(&body)?;let f=forms(&bytes)?;
    for(h,m,total)in [(false,false,0),(true,false,1),(false,true,1),(true,true,2)]{let result=f.lower_filtered_named_paragraph_style_candidate(&bytes,q(),Scope::Document,Policy{include_hidden_explanations:h,include_memo_bodies:m},filter(),Default::default(),Default::default());
        if total==0{assert!(matches!(result,Err(N::NoMatches)));continue;}let out=result?;assert_eq!(out.receipt().source.changes.len(),total);let after=output_filtered(&bytes,&out)?;assert!(section(&after)?.contains("CACHE FROZEN"));assert_eq!(references(&after)?[0].2,Some(2));}Ok(())
}
#[test]
fn original_field_tracking_and_locked_descendant_guards_remain_in_force()->TestResult{
    let field=para(1,0,"A</hp:t><hp:ctrl><hp:fieldBegin id='17' type='DATE'/></hp:ctrl><hp:t>CACHE</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='17'/></hp:ctrl><hp:t>TAIL");
    assert!(matches!(lower_filtered(&package(&field)?,filter()),Err(N::Paragraph(E::Compile(Compile::FieldContent)))));
    let text=para(1,0,"A");let locked=table::table(300).replace("lock='0'","lock='1'");
    for body in [text.replace("id='1'","id='1' paraTcId='0'"),text.replace("charPrIDRef='0'","charPrIDRef='0' charTcId='0'"),para(1,0,&format!("A</hp:t>{locked}<hp:t>TAIL"))]{
        assert!(matches!(lower_filtered(&package(&(para(2,1,"FIRST")+&body))?,filter()),Err(N::Paragraph(E::Compile(Compile::Protection)))));}Ok(())
}
#[test]
fn different_filters_bind_different_receipts_even_with_same_output()->TestResult{
    let bytes=package(&para(1,0,"PRIVATE-FILTER-TEXT"))?;let a=lower_filtered(&bytes,filter())?;let b=lower_filtered(&bytes,declared(Declared{run_character_property:Some(0),..Default::default()}))?;
    assert_eq!(a.receipt().source,b.receipt().source);assert_ne!(a.receipt().request_sha256,b.receipt().request_sha256);assert_eq!(output_filtered(&bytes,&a)?,output_filtered(&bytes,&b)?);
    for text in [format!("{a:?}{:?}",a.receipt()),serde_json::to_string(a.receipt())?]{assert!(!text.contains("PRIVATE-")&&!text.contains("SRC")&&!text.contains("DST")&&!text.contains("<hp:"));}Ok(())
}
#[test]
fn stale_source_and_foreign_proof_do_not_rebind_filter_or_named_catalog()->TestResult{
    let bytes=package(&para(1,0,"A"))?;let other=package(&para(1,0,"B"))?;let f=forms(&bytes)?;
    assert!(matches!(f.lower_filtered_named_paragraph_style_candidate(&other,q(),Scope::Document,all(),filter(),Default::default(),Default::default()),Err(N::Source)));
    let second=forms(&bytes)?;let proof=f.reconstruct_source_for_verification(&bytes)?;
    assert!(matches!(proof.lower_filtered_named_paragraph_style_candidate(&second,q(),Scope::Document,all(),filter(),Default::default(),Default::default()),Err(N::Source)));Ok(())
}
#[test]
fn source_query_match_writer_and_whole_response_budgets_do_not_return_partial_success()->TestResult{
    let bytes=package(&(para(1,0,"A")+&para(2,1,"B")))?;let f=forms(&bytes)?;
    for limits in [SourceSearchLimits::new(Config{matches:1,..Default::default()})?,SourceSearchLimits::new(Config{query_bytes:1,..Default::default()})?,SourceSearchLimits::new(Config{result_bytes:1,..Default::default()})?]{
        assert!(f.lower_filtered_named_paragraph_style_candidate(&bytes,q(),Scope::Document,all(),filter(),limits,Default::default()).is_err());}
    let writer=WriterLimits::new(WriterLimitConfig{max_output_bytes:1})?;assert!(f.lower_filtered_named_paragraph_style_candidate(&bytes,q(),Scope::Document,all(),filter(),Default::default(),writer).is_err());Ok(())
}
#[test]
fn long_text_uses_one_predicate_per_segment_and_one_part_protection_map()->TestResult{
    let bytes=package(&para(1,0,&"A".repeat(4096)))?;let out=lower_filtered(&bytes,filter())?;
    assert_eq!(out.receipt().style_filter.examined_normalized_units,4096);assert_eq!(out.receipt().style_filter.examined_source_segments,1);
    assert_eq!(out.receipt().source.observed_protection_parts,1);let xml=PreservingXmlDocument::parse(section(&bytes)?.as_bytes())?;
    assert_eq!(out.receipt().source.observed_protection_element_visits,xml.elements().len()*3);output_filtered(&bytes,&out)?;Ok(())
}
