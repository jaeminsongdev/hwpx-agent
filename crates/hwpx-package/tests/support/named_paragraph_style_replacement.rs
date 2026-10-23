//! Original named definitions and real paragraph attribute output, not prepared text expectations.
#[path="filtered_named_paragraph_style.rs"]mod filtered;
use super::*;
use hwpx_package::document_import::search::replacement::atoms::styles::paragraphs::named::{SourceNamedParagraphStyleQuery as NameQuery,
    SourceStyleNameAxis as NameAxis,SourceNamedParagraphStyleError as N,SourceNamedParagraphStyleCandidate as Named};
fn package(body:&str)->Result<Vec<u8>,Box<dyn Error>>{
    archive::mutate_part(&fixture::package(body)?,"Contents/header.xml",|text|{
        let xml=PreservingXmlDocument::parse(text.as_bytes())?;let mut edits=Vec::new();
        for n in xml.elements().iter().filter(|n|n.name().local_name()=="style"){
            let id=n.attributes().iter().find(|a|a.name().local_name()=="id").map(|a|&text[a.value_span().start()..a.value_span().end()]);
            let pair=match id{Some("0")=>Some(("원본 문단 A","SRC First")),Some("1")=>Some(("원본 문단 B","SRC Second")),Some("2")=>Some(("대상 문단","DST")),_=>None};
            if let Some((native,english))=pair{for a in n.attributes(){let v=match a.name().local_name(){"name"=>Some(native),"engName"=>Some(english),_=>None};
                if let Some(v)=v{edits.push((a.value_span().start(),a.value_span().end(),v));}}}
        }
        edits.sort_by_key(|e|e.0);let mut out=text.to_owned();for(a,b,v)in edits.into_iter().rev(){out.replace_range(a..b,v);}Ok(out)
    })
}
fn para(id:u32,style:u32,text:&str)->String{format!("<hp:p id='{id}' paraPrIDRef='0' styleIDRef='{style}'><hp:run charPrIDRef='0'><hp:t>{text}</hp:t></hp:run></hp:p>")}
fn q()->NameQuery<'static>{NameQuery{query:"SRC",replacement:"DST",regex:false,case_sensitive:true,whole_word:false,name_axis:NameAxis::EnglishName}}
fn lower(bytes:&[u8],query:NameQuery<'_>,scope:Scope<'_>)->Result<Named,N>{forms(bytes).map_err(|_|N::Source)?.lower_named_paragraph_style_candidate(bytes,query,scope,all(),Default::default(),Default::default())}
fn output(bytes:&[u8],out:&Named)->Result<Vec<u8>,Box<dyn Error>>{
    let result=out.with_verified_bytes(<[u8]>::to_vec)?;let mut a=BoundedZipReader::open(Cursor::new(bytes),Default::default())?;let mut b=BoundedZipReader::open(Cursor::new(&result),Default::default())?;
    assert_eq!(a.entries().len(),b.entries().len());for i in 0..a.entries().len(){let path=a.entries()[i].path.clone();if path.as_str()=="Contents/section0.xml"{continue;}
        let j=b.entries().iter().position(|e|e.path==path).ok_or("part")?;assert_eq!(a.read_entry(i)?,b.read_entry(j)?);}
    assert!(out.receipt().original_declarations_and_nonselected_references_preserved&&out.receipt().original_text_controls_run_and_text_references_preserved);
    assert!(!out.receipt().full_style_filter_character_style_native_or_execution_qualified);Ok(result)
}
#[test]
fn two_original_named_styles_replace_simultaneously_without_editing_definitions_or_other_references()->TestResult{
    let bytes=package(&(para(1,0,"A&amp;B")+&para(2,1,"각")+&para(3,2,"KEEP")))?;let out=lower(&bytes,q(),Scope::Document)?;
    let after=output(&bytes,&out)?;assert_eq!(references(&after)?,vec![(1,Some(0),Some(2)),(2,Some(0),Some(2)),(3,Some(0),Some(2))]);
    assert_eq!(out.receipt().from_style_ids,vec![0,1]);assert_eq!(out.receipt().target_style_id,2);assert_eq!(out.receipt().matched_paragraphs,2);assert_eq!(out.receipt().changes.len(),2);
    let expected=section(&bytes)?.replace("styleIDRef='0'","styleIDRef='2'").replace("styleIDRef='1'","styleIDRef='2'");assert_eq!(section(&after)?,expected);Ok(())
}
#[test]
fn admitted_empty_run_paragraphs_change_and_runless_source_stays_rejected()->TestResult{
    let runless=package("<hp:p id='1' paraPrIDRef='0' styleIDRef='0'/>")?;
    assert!(matches!(lower(&runless,q(),Scope::Document),Err(N::Source)));
    let bytes=package("<hp:p id='1' paraPrIDRef='0' styleIDRef='0'><hp:run charPrIDRef='0'/></hp:p><hp:p id='2' paraPrIDRef='0' styleIDRef='1'><hp:run charPrIDRef='0'><hp:t></hp:t></hp:run></hp:p><hp:p id='3' paraPrIDRef='0' styleIDRef='0'><hp:run charPrIDRef='0'><hp:t/></hp:run></hp:p>")?;
    let out=lower(&bytes,q(),Scope::Document)?;let after=output(&bytes,&out)?;assert_eq!(out.receipt().matched_paragraphs,3);
    assert_eq!(references(&after)?,vec![(1,Some(0),Some(2)),(2,Some(0),Some(2)),(3,Some(0),Some(2))]);Ok(())
}
#[test]
fn native_and_english_name_axes_are_explicit_and_not_implicit_alias_fallback()->TestResult{
    let bytes=package(&para(1,0,"A"))?;let query=NameQuery{query:"원본 문단 A",replacement:"대상 문단",name_axis:NameAxis::NativeName,..q()};
    let out=lower(&bytes,query,Scope::Document)?;assert_eq!(references(&output(&bytes,&out)?)?[0].2,Some(2));
    assert!(matches!(lower(&bytes,NameQuery{name_axis:NameAxis::EnglishName,..query},Scope::Document),Err(N::NoMatches)));Ok(())
}
#[test]
fn literal_regex_case_and_whole_word_name_matching_remain_bounded_and_distinct()->TestResult{
    let bytes=package(&(para(1,0,"A")+&para(2,1,"B")))?;
    for query in [NameQuery{query:"src",case_sensitive:false,..q()},NameQuery{query:r"^SRC (First|Second)$",regex:true,..q()},NameQuery{query:"SRC",whole_word:true,..q()}]{
        assert_eq!(lower(&bytes,query,Scope::Document)?.receipt().changes.len(),2);}
    assert!(matches!(lower(&bytes,NameQuery{query:"SR",whole_word:true,..q()},Scope::Document),Err(N::NoMatches)));
    assert!(matches!(lower(&bytes,NameQuery{query:"src",..q()},Scope::Document),Err(N::NoMatches)));Ok(())
}
#[test]
fn target_is_exact_unique_existing_paragraph_style_not_character_style_or_substring()->TestResult{
    let bytes=package(&para(1,0,"A"))?;
    for target in ["DS","Page Number","NOT DECLARED"]{assert!(matches!(lower(&bytes,NameQuery{replacement:target,..q()},Scope::Document),Err(N::MissingTarget)));}
    let duplicate=archive::mutate_part(&bytes,"Contents/header.xml",|t|Ok(t.replace("SRC Second","DST")))?;
    assert!(matches!(lower(&duplicate,q(),Scope::Document),Err(N::AmbiguousTarget)));Ok(())
}
#[test]
fn source_names_are_decoded_once_and_replacement_is_not_a_template_or_new_definition()->TestResult{
    let bytes=archive::mutate_part(&package(&para(1,0,"A"))?,"Contents/header.xml",|t|Ok(t.replace("SRC First","SRC &amp; One").replace("engName=\"DST\"","engName=\"DST &amp; Two\"")))?;
    let query=NameQuery{query:"SRC & One",replacement:"DST & Two",..q()};let out=lower(&bytes,query,Scope::Document)?;
    assert_eq!(references(&output(&bytes,&out)?)?[0].2,Some(2));Ok(())
}
#[test]
fn four_scope_kinds_limit_actual_paragraphs_and_partial_selection_never_widens()->TestResult{
    let bytes=package(&(para(1,0,"ABC")+&para(2,1,"DEF")))?;let f=forms(&bytes)?;let inv=f.source_review_scope_index(&bytes,Default::default())?.scope_inventory()?;
    let b=&inv.inventory.blocks[0];let a=Boundary{paragraph_handle:b.paragraph_handle.clone(),block_index:b.block_index,normalized_scalar:0};let end=Boundary{normalized_scalar:3,..a.clone()};
    let ids=[inv.inventory.nodes.iter().find(|n|n.source_handle==b.paragraph_handle).ok_or("node")?.node_id.clone()];
    for(scope,count)in [(Scope::Document,2),(Scope::Section(&inv.inventory.section_ids),2),(Scope::NodeSet(&ids),1),(Scope::Selection{index_sha256:inv.inventory.index.index_sha256,start:&a,end:&end},1)]{
        let out=lower(&bytes,q(),scope)?;assert_eq!(out.receipt().changes.len(),count);output(&bytes,&out)?;}
    let start=Boundary{normalized_scalar:1,..a};assert!(matches!(lower(&bytes,q(),Scope::Selection{index_sha256:inv.inventory.index.index_sha256,start:&start,end:&end}),Err(N::Paragraph(E::IncompleteParagraphScope))));Ok(())
}
#[test]
fn empty_selection_is_not_authority_to_change_empty_paragraph_style()->TestResult{
    let bytes=package("<hp:p id='1' paraPrIDRef='0' styleIDRef='0'><hp:run charPrIDRef='0'/></hp:p>")?;let f=forms(&bytes)?;let inv=f.source_review_scope_index(&bytes,Default::default())?.scope_inventory()?;
    let b=&inv.inventory.blocks[0];let a=Boundary{paragraph_handle:b.paragraph_handle.clone(),block_index:b.block_index,normalized_scalar:0};
    assert!(matches!(lower(&bytes,q(),Scope::Selection{index_sha256:inv.inventory.index.index_sha256,start:&a,end:&a}),Err(N::Paragraph(E::IncompleteParagraphScope))));Ok(())
}
#[test]
fn controls_and_all_blocks_must_fit_scope_before_whole_paragraph_edit()->TestResult{
    let bytes=package(&para(1,0,&format!("ABC{TAB}</hp:t><hp:ctrl><hp:bookmark name='BOOK'/></hp:ctrl><hp:t>DEF")))?;let f=forms(&bytes)?;let inv=f.source_review_scope_index(&bytes,Default::default())?.scope_inventory()?;let b=&inv.inventory.blocks[0];
    let a=Boundary{paragraph_handle:b.paragraph_handle.clone(),block_index:b.block_index,normalized_scalar:0};let end=Boundary{normalized_scalar:b.normalized_scalars,..a.clone()};
    assert!(matches!(lower(&bytes,q(),Scope::Selection{index_sha256:inv.inventory.index.index_sha256,start:&a,end:&end}),Err(N::Paragraph(E::IncompleteParagraphScope))));
    let out=lower(&bytes,q(),Scope::Document)?;let after=output(&bytes,&out)?;assert!(section(&after)?.contains(TAB));Ok(())
}
#[test]
fn missing_original_style_reference_is_not_default_zero_or_body_name_match()->TestResult{
    let bytes=package("<hp:p id='1' paraPrIDRef='0'><hp:run charPrIDRef='0'><hp:t>SRC First</hp:t></hp:run></hp:p>")?;
    assert!(matches!(lower(&bytes,q(),Scope::Document),Err(N::NoMatches)));Ok(())
}
#[test]
fn review_policy_selects_hidden_and_memo_without_editing_outer_cached_paragraph()->TestResult{
    let body=review::body().replace("<hp:p id='1'>","<hp:p id='1' paraPrIDRef='0' styleIDRef='2'>")
        .replace("<hp:p id='11'>","<hp:p id='11' paraPrIDRef='0' styleIDRef='0'>").replace("<hp:p id='12'>","<hp:p id='12' paraPrIDRef='0' styleIDRef='1'>");let bytes=package(&body)?;let f=forms(&bytes)?;
    for(h,m,total)in [(false,false,0),(true,false,1),(false,true,1),(true,true,2)]{
        let result=f.lower_named_paragraph_style_candidate(&bytes,q(),Scope::Document,Policy{include_hidden_explanations:h,include_memo_bodies:m},Default::default(),Default::default());
        if total==0{assert!(matches!(result,Err(N::NoMatches)));continue;}let out=result?;assert_eq!(out.receipt().changes.len(),total);let after=output(&bytes,&out)?;
        assert_eq!(references(&after)?[0].2,Some(2));assert!(section(&after)?.contains("CACHE FROZEN")&&section(&after)?.contains("PRIVATE-AUTHOR"));}Ok(())
}
#[test]
fn field_cache_anywhere_in_changed_paragraph_blocks_the_whole_batch()->TestResult{
    let bytes=package(&para(1,0,"A</hp:t><hp:ctrl><hp:fieldBegin id='17' type='DATE'/></hp:ctrl><hp:t>CACHE</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='17'/></hp:ctrl><hp:t>TAIL"))?;
    assert!(matches!(lower(&bytes,q(),Scope::Document),Err(N::Paragraph(E::Compile(Compile::FieldContent)))));Ok(())
}
#[test]
fn ancestor_or_descendant_tracking_and_locked_table_block_without_partial_candidate()->TestResult{
    let text=para(1,0,"A");let locked=table::table(300).replace("lock='0'","lock='1'");
    for body in [text.replace("id='1'","id='1' paraTcId='0'"),text.replace("charPrIDRef='0'","charPrIDRef='0' charTcId='0'"),para(1,0,&format!("A</hp:t>{locked}<hp:t>TAIL"))]{
        let bytes=package(&(para(2,1,"FIRST")+&body))?;assert!(matches!(lower(&bytes,q(),Scope::Document),Err(N::Paragraph(E::Compile(Compile::Protection)))));}
    Ok(())
}
#[test]
fn no_match_no_change_and_unused_declaration_do_not_return_successful_artifacts()->TestResult{
    let bytes=package(&para(1,2,"A"))?;assert!(matches!(lower(&bytes,q(),Scope::Document),Err(N::NoMatches)));
    assert!(matches!(lower(&bytes,NameQuery{query:"NOT THERE",..q()},Scope::Document),Err(N::NoMatches)));
    assert!(matches!(lower(&bytes,NameQuery{query:"DST",..q()},Scope::Document),Err(N::NoChange)));Ok(())
}
#[test]
fn malformed_zero_width_and_over_budget_patterns_reject_without_partial_outputs()->TestResult{
    let bytes=package(&para(1,0,"A"))?;
    for pattern in ["[","^",r"SRC|^$"]{let result=lower(&bytes,NameQuery{query:pattern,regex:true,..q()},Scope::Document);
        if pattern==r"SRC|^$"{result?;}else{assert!(matches!(result,Err(N::Pattern)));}}
    let f=forms(&bytes)?;assert!(matches!(f.lower_named_paragraph_style_candidate(&[],NameQuery{query:"",..q()},Scope::Document,all(),Default::default(),Default::default()),Err(N::Pattern)));
    let limits=SourceSearchLimits::new(Config{pattern_bytes:1,..Default::default()})?;
    assert!(matches!(f.lower_named_paragraph_style_candidate(&bytes,NameQuery{query:"(?:A|B){1000}",regex:true,..q()},Scope::Document,all(),limits,Default::default()),Err(N::Pattern)));Ok(())
}
#[test]
fn paragraph_request_server_writer_and_output_limits_never_return_partial_success()->TestResult{
    let bytes=package(&(para(1,0,"A")+&para(2,1,"B")))?;let f=forms(&bytes)?;
    let limits=SourceSearchLimits::new(Config{matches:1,..Default::default()})?;assert!(matches!(f.lower_named_paragraph_style_candidate(&bytes,q(),Scope::Document,all(),limits,Default::default()),Err(N::Limit)));
    let limits=SourceSearchLimits::new(Config{query_bytes:1,..Default::default()})?;assert!(matches!(f.lower_named_paragraph_style_candidate(&[],q(),Scope::Document,all(),limits,Default::default()),Err(N::Limit)));
    let writer=WriterLimits::new(WriterLimitConfig{max_output_bytes:1})?;assert!(matches!(f.lower_named_paragraph_style_candidate(&bytes,q(),Scope::Document,all(),Default::default(),writer),Err(N::Compile(Compile::Writer))));Ok(())
}
#[test]
fn stale_source_foreign_proof_and_selector_never_rebind_name_query()->TestResult{
    let bytes=package(&para(1,0,"A"))?;let other=package(&para(1,0,"B"))?;let f=forms(&bytes)?;
    assert!(matches!(f.lower_named_paragraph_style_candidate(&other,q(),Scope::Document,all(),Default::default(),Default::default()),Err(N::Source)));
    let second=forms(&bytes)?;let proof=f.reconstruct_source_for_verification(&bytes)?;assert!(matches!(proof.lower_named_paragraph_style_candidate(&second,q(),Scope::Document,all(),Default::default(),Default::default()),Err(N::Source)));
    let inv=f.source_review_scope_index(&bytes,Default::default())?.scope_inventory()?;let b=&inv.inventory.blocks[0];let start=Boundary{paragraph_handle:b.paragraph_handle.clone(),block_index:b.block_index,normalized_scalar:0};let end=Boundary{normalized_scalar:1,..start.clone()};
    assert!(matches!(lower(&bytes,q(),Scope::Selection{index_sha256:[0;32],start:&start,end:&end}),Err(N::Search(Search::Scope))));Ok(())
}
#[test]
fn receipts_bind_names_axis_scope_and_keep_names_and_private_text_redacted()->TestResult{
    let bytes=package(&para(1,0,"PRIVATE-NAMED-TEXT"))?;let first=lower(&bytes,q(),Scope::Document)?;
    let second=lower(&bytes,NameQuery{query:"SRC First",..q()},Scope::Document)?;assert_eq!(first.receipt().output_package_sha256,second.receipt().output_package_sha256);
    assert_ne!(first.receipt().query_sha256,second.receipt().query_sha256);assert_ne!(first.receipt().request_sha256,second.receipt().request_sha256);
    for text in [format!("{:?}{first:?}{:?}",q(),first.receipt()),serde_json::to_string(first.receipt())?]{assert!(!text.contains("SRC First")&&!text.contains("DST")&&!text.contains("PRIVATE-NAMED-TEXT"));}Ok(())
}
#[test]
fn many_paragraphs_reuse_one_part_guard_and_preserve_original_header()->TestResult{
    let mut body=String::new();for id in 1..=64{body.push_str(&para(id,id%2,"A"));}let bytes=package(&body)?;let out=lower(&bytes,q(),Scope::Document)?;
    assert_eq!(out.receipt().changes.len(),64);assert_eq!(out.receipt().observed_protection_parts,1);
    let xml=PreservingXmlDocument::parse(section(&bytes)?.as_bytes())?;assert_eq!(out.receipt().observed_protection_element_visits,xml.elements().len()*3);output(&bytes,&out)?;Ok(())
}
