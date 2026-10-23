use hwpx_package::document_import::{ImportedSourcePackage,forms::ImportedDocumentForms,search::{SourceSearchQuery as Query,SourceSearchMode as Mode,
    SourceSearchError as E,SourceSearchLimits,SourceSearchLimitConfig as Config,selector::{SourceIndexScopeSelector as Scope,SourceIndexBoundary as Boundary},
    reviews::SourceReviewTextPolicy as Policy,navigation::{SourceSearchNavigationRequest as Next,SourceSearchDirection as Direction,SourceSearchCursor as Cursor,
        SourceSearchNavigationSelection as Selection}}};
use domain_ir::DocumentId;
use sha2::{Digest as _,Sha256};
#[path="support/review_scope_fixture.rs"] mod fixture;
type TestResult=Result<(),Box<dyn std::error::Error>>;
fn forms(raw:&[u8])->Result<ImportedDocumentForms,Box<dyn std::error::Error>>{Ok(ImportedDocumentForms::import(ImportedSourcePackage::import(raw,DocumentId::parse("selector-navigation")?,Sha256::digest(raw).into(),Default::default())?)?)}
fn query(q:&str)->Query<'_>{Query{query:q,mode:Mode::Literal,case_sensitive:true,whole_word:false,max_results:100}}
fn all()->Policy{Policy{include_hidden_explanations:true,include_memo_bodies:true}}
fn next(direction:Direction,wrap:bool,cursor:Option<&Cursor>)->Next{Next{direction,wrap,cursor:cursor.cloned()}}
#[test]
fn selector_navigation_all_four_scopes_retain_source_selection_order_and_explicit_wrap()->TestResult{
    let raw=fixture::package()?;let f=forms(&raw)?;let index=f.body_structure().source_text_index(&raw,Default::default())?;let inv=index.scope_inventory()?;
    let b=&inv.blocks[0];let start=Boundary{paragraph_handle:b.paragraph_handle.clone(),block_index:b.block_index,normalized_scalar:7};let end=Boundary{normalized_scalar:8,..start.clone()};
    let id=inv.nodes.iter().find(|n|n.source_handle==b.paragraph_handle).ok_or("node")?.node_id.clone();let nodes=[id];
    for(scope,count)in[(Scope::Document,2),(Scope::Section(&inv.section_ids),2),(Scope::NodeSet(&nodes),2),(Scope::Selection{index_sha256:inv.index.index_sha256,start:&start,end:&end},1)]{
        let found=index.find_selector(query("K"),scope)?;let mut cursor=None;
        for n in 0..count{let value=found.navigate(&next(Direction::Forward,false,cursor.as_ref()),[3;32])?;assert_eq!(value.match_index(),Some(n));
            let Some(Selection::Text(selected))=value.selection()else{return Err("text".into())};assert_eq!(selected,&found.result().matches()[n]);cursor=value.cursor().cloned();}
        let exhausted=found.navigate(&next(Direction::Forward,false,cursor.as_ref()),[3;32])?;assert!(exhausted.exhausted());assert_eq!(exhausted.cursor(),cursor.as_ref());
        let wrapped=found.navigate(&next(Direction::Forward,true,cursor.as_ref()),[3;32])?;assert!(wrapped.wrapped());assert_eq!(wrapped.match_index(),Some(0));
        let last=found.navigate(&next(Direction::Backward,true,wrapped.cursor()),[3;32])?;assert_eq!(last.match_index(),Some(count-1));assert!(last.wrapped());}
    Ok(())
}
#[test]
fn selector_navigation_review_policy_regions_and_partial_windows_are_retained()->TestResult{
    let raw=fixture::package()?;let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;let inv=index.scope_inventory()?;
    let found=index.find(query("K"),Scope::Document,all())?;let mut cursor=None;
    for n in 0..6{let value=found.navigate(&next(Direction::Forward,false,cursor.as_ref()),[3;32])?;let v=serde_json::to_value(&value)?;
        assert_eq!(v["region"],["body_and_notes","hidden_explanation","memo_body"][n/2]);
        let Some(Selection::Text(selected))=value.selection()else{return Err("text".into())};assert_eq!(selected,&found.result().matches()[n]);cursor=value.cursor().cloned();}
    let i=inv.block_regions.iter().position(|r|serde_json::to_value(r).is_ok_and(|v|v=="memo_body")).ok_or("memo")?;let b=&inv.inventory.blocks[i];
    let start=Boundary{paragraph_handle:b.paragraph_handle.clone(),block_index:b.block_index,normalized_scalar:7};let end=Boundary{normalized_scalar:8,..start.clone()};
    let selected=index.find(Query{query:"^K$",mode:Mode::Regex,max_results:1,..query("K")},Scope::Selection{index_sha256:inv.inventory.index.index_sha256,start:&start,end:&end},all())?;
    let value=selected.navigate(&next(Direction::Forward,false,None),[3;32])?;let Some(Selection::Text(m))=value.selection()else{return Err("text".into())};
    assert_eq!(m.start_normalized_scalar,7);assert_eq!(serde_json::to_value(&value)?["region"],"memo_body");Ok(())
}
#[test]
fn selector_navigation_cursor_binds_scope_policy_query_options_context_and_legacy_result_kind()->TestResult{
    let raw=fixture::package()?;let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;let inv=index.scope_inventory()?;
    let found=index.find(query("K"),Scope::Document,all())?;let first=found.navigate(&next(Direction::Forward,false,None),[3;32])?;let request=next(Direction::Forward,false,first.cursor());
    assert!(matches!(found.navigate(&request,[4;32]),Err(E::Cursor)));
    for q in[Query{case_sensitive:false,..query("K")},Query{mode:Mode::Regex,..query("K")},Query{whole_word:true,..query("K")},Query{max_results:99,..query("K")}]{assert!(matches!(index.find(q,Scope::Document,all())?.navigate(&request,[3;32]),Err(E::Cursor)));}
    assert!(matches!(index.find(query("K"),Scope::Document,Default::default())?.navigate(&request,[3;32]),Err(E::Cursor)));
    assert!(matches!(index.find(query("K"),Scope::Section(&inv.inventory.section_ids),all())?.navigate(&request,[3;32]),Err(E::Cursor)));
    let plain=f.body_structure().source_text_index(&raw,Default::default())?;assert!(matches!(plain.find_selector(query("K"),Scope::Document)?.navigate(&request,[3;32]),Err(E::Cursor)));
    assert!(matches!(plain.find(query("K"))?.navigate(&request,[3;32]),Err(E::Cursor)));Ok(())
}
#[test]
fn selector_navigation_zero_width_and_empty_windows_advance_without_search_or_edit_authority()->TestResult{
    let raw=fixture::package()?;let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;let inv=index.scope_inventory()?;let b=&inv.inventory.blocks[0];
    let start=Boundary{paragraph_handle:b.paragraph_handle.clone(),block_index:b.block_index,normalized_scalar:7};let end=Boundary{normalized_scalar:8,..start.clone()};
    let scope=Scope::Selection{index_sha256:inv.inventory.index.index_sha256,start:&start,end:&end};let found=index.find(Query{query:"^|$",mode:Mode::Regex,..query("K")},scope,all())?;
    let mut cursor=None;for n in 0..2{let value=found.navigate(&next(Direction::Forward,false,cursor.as_ref()),[0;32])?;assert_eq!(value.match_index(),Some(n));
        let Some(Selection::Text(m))=value.selection()else{return Err("text".into())};assert!(m.zero_width&&m.pieces.is_empty());cursor=value.cursor().cloned();}
    assert!(found.navigate(&next(Direction::Forward,false,cursor.as_ref()),[0;32])?.exhausted());
    let empty=index.find(query("absent"),scope,all())?;for direction in[Direction::Forward,Direction::Backward]{let value=empty.navigate(&next(direction,true,None),[0;32])?;assert!(value.exhausted()&&!value.wrapped()&&value.cursor().is_none());}
    assert!(matches!(empty.navigate(&next(Direction::Forward,true,cursor.as_ref()),[0;32]),Err(E::Cursor)));Ok(())
}
#[test]
fn selector_navigation_tampered_cursor_profile_binding_ordinal_and_occurrence_are_rejected()->TestResult{
    let raw=fixture::package()?;let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;let found=index.find(query("K"),Scope::Document,all())?;
    let first=found.navigate(&next(Direction::Forward,false,None),[0;32])?;let original=serde_json::to_value(first.cursor())?;
    for(key,value)in[("profile",serde_json::json!("other")),("binding_sha256",serde_json::json!(vec![1u8;32])),("match_index",serde_json::json!(1)),("match_index",serde_json::json!(9999)),("occurrence_sha256",serde_json::json!(vec![0u8;32]))]{
        let mut v=original.clone();v[key]=value;let cursor:Cursor=serde_json::from_value(v)?;assert!(matches!(found.navigate(&next(Direction::Forward,false,Some(&cursor)),[0;32]),Err(E::Cursor)));}
    Ok(())
}
#[test]
fn selector_navigation_nfc_original_pieces_and_bounded_private_response_are_preserved()->TestResult{
    let body=fixture::body().replace("<hp:t>MEMO K K</hp:t>","<hp:t>Xᄀ</hp:t></hp:run><hp:run><hp:t>ᅡ</hp:t></hp:run><hp:run><hp:t>ᆨY</hp:t>");
    let raw=fixture::with_body(&body)?;let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;let found=index.find(query("각"),Scope::Document,all())?;
    let first=found.navigate(&next(Direction::Forward,false,None),[0;32])?;let Some(Selection::Text(m))=first.selection()else{return Err("text".into())};
    assert_eq!(m,&found.result().matches()[0]);assert_eq!(m.pieces.len(),3);let bytes=first.canonical_json()?;assert!(!String::from_utf8(bytes)?.contains("각"));
    assert!(!format!("{first:?}").contains("각"));let maximum=found.canonical_json()?.len();
    let bounded=f.source_review_scope_index(&raw,SourceSearchLimits::new(Config{result_bytes:maximum,..Default::default()})?)?;
    assert_eq!(bounded.find(query("각"),Scope::Document,all())?.navigate(&next(Direction::Forward,false,None),[0;32])?.canonical_json()?,first.canonical_json()?);Ok(())
}
