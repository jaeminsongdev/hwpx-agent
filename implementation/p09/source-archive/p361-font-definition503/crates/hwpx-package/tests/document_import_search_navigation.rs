use hwpx_package::document_import::{ImportedSourcePackage,SourceImportLimits,structure::ImportedDocumentStructure,forms::ImportedDocumentForms,
    search::{SourceSearchLimits,SourceSearchLimitConfig,SourceSearchQuery as Query,SourceSearchMode as Mode,SourceSearchError as E,
        scope::SourceSearchScope as Scope,navigation::{SourceSearchNavigationRequest as Request,SourceSearchDirection as Direction,
            SourceSearchCursor,SourceSearchNavigationSelection as Selection},inspection::{SourceDeclaredStyleFilter,SourceControlKind,
            definitions::{SourceDefinitionStyleFilter,CharacterDefinitionSource}},reviews::SourceReviewTextPolicy}};
use domain_ir::DocumentId;
use sha2::{Digest as _,Sha256};
#[path="support/search_review_fixture.rs"] mod review;
#[path="support/search_definition_fixture.rs"] mod definition;
type TestResult=Result<(),Box<dyn std::error::Error>>;
fn query(s:&str)->Query<'_> {Query {query:s,mode:Mode::Literal,case_sensitive:true,whole_word:false,max_results:100}}
fn source(b:&[u8],id:&str)->Result<ImportedSourcePackage,Box<dyn std::error::Error>> {
    Ok(ImportedSourcePackage::import(b,DocumentId::parse(id)?,Sha256::digest(b).into(),SourceImportLimits::default())?)}
fn three()->Result<Vec<u8>,Box<dyn std::error::Error>> {review::with_body("<hp:p id='1'><hp:run><hp:t>K K</hp:t></hp:run></hp:p><hp:p id='2'><hp:run><hp:t>K</hp:t></hp:run></hp:p>")}
fn step(direction:Direction,wrap:bool,cursor:Option<&SourceSearchCursor>)->Request {Request {direction,wrap,cursor:cursor.cloned()}}
#[test]
fn navigation_forward_backward_exhaustion_preserves_position_for_direction_reversal()->TestResult {
    let b=three()?;let s=ImportedDocumentStructure::import(source(&b,"navigate")?)?;let index=s.source_text_index(&b,Default::default())?;
    let found=index.find_scoped(query("K"),Scope::MappedDocument)?;let mut cursor=None;
    for expected in 0..3 {let n=found.navigate(&step(Direction::Forward,false,cursor.as_ref()),[0;32])?;assert_eq!(n.match_index(),Some(expected));cursor=n.cursor().cloned();}
    let end=found.navigate(&step(Direction::Forward,false,cursor.as_ref()),[0;32])?;assert!(end.exhausted());assert!(!end.wrapped());assert_eq!(end.cursor(),cursor.as_ref());
    let back=found.navigate(&step(Direction::Backward,false,end.cursor()),[0;32])?;assert_eq!(back.match_index(),Some(1));
    let last=found.navigate(&step(Direction::Backward,false,None),[0;32])?;assert_eq!(last.match_index(),Some(2));Ok(())
}
#[test]
fn navigation_wrap_is_explicit_in_both_directions_and_single_occurrence()->TestResult {
    let b=three()?;let s=ImportedDocumentStructure::import(source(&b,"wrap")?)?;let index=s.source_text_index(&b,Default::default())?;let all=index.find(query("K"))?;
    let first=all.navigate(&step(Direction::Forward,false,None),[0;32])?;
    assert!(all.navigate(&step(Direction::Backward,false,first.cursor()),[0;32])?.exhausted());
    let last=all.navigate(&step(Direction::Backward,true,first.cursor()),[0;32])?;assert_eq!(last.match_index(),Some(2));assert!(last.wrapped());
    let looped=all.navigate(&step(Direction::Forward,true,last.cursor()),[0;32])?;assert_eq!(looped.match_index(),Some(0));assert!(looped.wrapped());
    let one=index.find(query("K K"))?;let start=one.navigate(&step(Direction::Forward,false,None),[0;32])?;
    assert!(one.navigate(&step(Direction::Forward,false,start.cursor()),[0;32])?.exhausted());
    assert!(one.navigate(&step(Direction::Forward,true,start.cursor()),[0;32])?.wrapped());Ok(())
}
#[test]
fn navigation_zero_width_occurrences_advance_by_ordinal_without_rescanning()->TestResult {
    let b=three()?;let s=ImportedDocumentStructure::import(source(&b,"zero")?)?;let index=s.source_text_index(&b,Default::default())?;
    let found=index.find(Query {mode:Mode::Regex,..query("^|$")})?;assert_eq!(found.matches().len(),4);let mut cursor=None;
    for expected in 0..4 {let n=found.navigate(&step(Direction::Forward,false,cursor.as_ref()),[0;32])?;assert_eq!(n.match_index(),Some(expected));
        let Some(Selection::Text(m))=n.selection()else{return Err("text occurrence".into())};assert!(m.zero_width&&m.pieces.is_empty());cursor=n.cursor().cloned();}
    assert!(found.navigate(&step(Direction::Forward,false,cursor.as_ref()),[0;32])?.exhausted());Ok(())
}
#[test]
fn navigation_empty_sets_have_no_cursor_and_never_accept_another_result_cursor()->TestResult {
    let b=three()?;let s=ImportedDocumentStructure::import(source(&b,"empty")?)?;let index=s.source_text_index(&b,Default::default())?;
    let empty=index.find(query("absent"))?;let all=index.find(query("K"))?;let previous=all.navigate(&step(Direction::Forward,false,None),[0;32])?;
    for direction in [Direction::Forward,Direction::Backward] {let n=empty.navigate(&step(direction,true,None),[0;32])?;assert!(n.exhausted());assert!(!n.wrapped());assert!(n.cursor().is_none());}
    assert!(matches!(empty.navigate(&step(Direction::Forward,true,previous.cursor()),[0;32]),Err(E::Cursor)));Ok(())
}
#[test]
fn navigation_cursor_binds_original_document_source_query_options_scope_and_context()->TestResult {
    let b=three()?;let s=ImportedDocumentStructure::import(source(&b,"binding")?)?;let index=s.source_text_index(&b,Default::default())?;
    let found=index.find_scoped(query("K"),Scope::MappedDocument)?;let first=found.navigate(&step(Direction::Forward,false,None),[0;32])?;
    let request=step(Direction::Forward,false,first.cursor());
    assert!(matches!(found.navigate(&request,[1;32]),Err(E::Cursor)));
    for q in [query("K K"),Query {case_sensitive:false,..query("K")},Query {whole_word:true,..query("K")},Query {max_results:99,..query("K")},Query {mode:Mode::Regex,..query("K")}] {
        assert!(matches!(index.find_scoped(q,Scope::MappedDocument)?.navigate(&request,[0;32]),Err(E::Cursor)));}
    let id=found.result().matches()[0].paragraph_anchor.opaque_handle.clone();
    assert!(matches!(index.find_scoped(query("K"),Scope::Paragraphs(&[id]))?.navigate(&request,[0;32]),Err(E::Cursor)));
    for (bytes,id) in [(b.clone(),"foreign"),(review::with_body("<hp:p id='1'><hp:run><hp:t>K changed</hp:t></hp:run></hp:p>")?,"binding")] {
        let other=ImportedDocumentStructure::import(source(&bytes,id)?)?;let other_index=other.source_text_index(&bytes,Default::default())?;
        assert!(matches!(other_index.find_scoped(query("K"),Scope::MappedDocument)?.navigate(&request,[0;32]),Err(E::Cursor)));}
    Ok(())
}
#[test]
fn navigation_tampered_profile_binding_position_and_occurrence_fingerprint_are_rejected()->TestResult {
    let b=three()?;let s=ImportedDocumentStructure::import(source(&b,"tamper")?)?;let index=s.source_text_index(&b,Default::default())?;let found=index.find(query("K"))?;
    let first=found.navigate(&step(Direction::Forward,false,None),[0;32])?;let original=serde_json::to_value(first.cursor())?;
    for (key,value) in [("profile",serde_json::json!("other")),("binding_sha256",serde_json::json!(vec![1u8;32])),
        ("match_index",serde_json::json!(3)),("match_index",serde_json::json!(1)),("occurrence_sha256",serde_json::json!(vec![0u8;32]))] {
        let mut v=original.clone();v[key]=value;let cursor:SourceSearchCursor=serde_json::from_value(v)?;
        assert!(matches!(found.navigate(&step(Direction::Forward,false,Some(&cursor)),[0;32]),Err(E::Cursor)));}Ok(())
}
#[test]
fn navigation_selected_match_keeps_nfc_source_pieces_and_never_discloses_query_or_text()->TestResult {
    let b=review::with_body("<hp:p id='1'><hp:run><hp:t>ᄀ</hp:t></hp:run><hp:run><hp:t>ᅡᆨ</hp:t></hp:run></hp:p>")?;
    let s=ImportedDocumentStructure::import(source(&b,"nfc")?)?;let index=s.source_text_index(&b,Default::default())?;let found=index.find(query("각"))?;
    let n=found.navigate(&step(Direction::Forward,false,None),[0;32])?;let Some(Selection::Text(m))=n.selection()else{return Err("text".into())};
    assert_eq!(m,&found.matches()[0]);assert_eq!(m.pieces.len(),2);
    assert!(!String::from_utf8(n.canonical_json()?)?.contains("각"));assert!(!format!("{n:?}").contains("각"));Ok(())
}
#[test]
fn navigation_declared_style_and_control_results_preserve_filter_and_occurrence_kind()->TestResult {
    let b=review::with_body("<hp:p id='1'><hp:run charPrIDRef='1'><hp:t>K</hp:t><hp:ctrl><hp:bookmark name='PRIVATE-NAME'/></hp:ctrl><hp:t>K</hp:t></hp:run></hp:p>")?;
    let s=ImportedDocumentStructure::import(source(&b,"inspect")?)?;let index=s.source_text_index(&b,Default::default())?;let inspection=index.inspection()?;
    let found=inspection.find_style(query("K"),Scope::MappedDocument,SourceDeclaredStyleFilter {run_character_property:Some(1),..Default::default()})?;
    let first=found.navigate(&step(Direction::Forward,false,None),[0;32])?;assert!(matches!(first.selection(),Some(Selection::Text(_))));
    let controls=inspection.find_control(Scope::MappedDocument,SourceControlKind::Bookmark,10)?;
    let n=controls.navigate(&step(Direction::Forward,false,None),[0;32])?;assert!(matches!(n.selection(),Some(Selection::Control(_))));
    assert!(matches!(controls.navigate(&step(Direction::Forward,false,first.cursor()),[0;32]),Err(E::Cursor)));Ok(())
}
#[test]
fn navigation_definition_and_review_policies_are_bound_without_losing_region_annotations()->TestResult {
    let b=definition::package("<hp:p id='1'><hp:run charPrIDRef='1'><hp:t>K</hp:t></hp:run></hp:p>")?;
    let s=ImportedDocumentStructure::import(source(&b,"definitions")?)?;let index=s.source_text_index(&b,Default::default())?;let inspection=index.inspection()?;
    let definitions=inspection.resolve_style_definitions()?;let found=definitions.find(query("K"),Scope::MappedDocument,
        SourceDefinitionStyleFilter {character_source:Some(CharacterDefinitionSource::RunProperty),bold:Some(true),..Default::default()})?;
    assert!(matches!(found.navigate(&step(Direction::Forward,false,None),[0;32])?.selection(),Some(Selection::Text(_))));
    let b=review::package()?;let forms=ImportedDocumentForms::import(source(&b,"reviews")?)?;let index=forms.source_review_text_index(&b,Default::default())?;
    let found=index.find(query("K"),Scope::MappedDocument,SourceReviewTextPolicy {include_hidden_explanations:true,include_memo_bodies:true})?;
    let first=found.navigate(&step(Direction::Forward,false,None),[0;32])?;let second=found.navigate(&step(Direction::Forward,false,first.cursor()),[0;32])?;
    assert_eq!(serde_json::to_value(&second)?["region"],"hidden_explanation");
    let excluded=index.find(query("K"),Scope::MappedDocument,Default::default())?;
    assert!(matches!(excluded.navigate(&step(Direction::Forward,false,first.cursor()),[0;32]),Err(E::Cursor)));Ok(())
}
#[test]
fn navigation_request_types_are_strict_and_selected_response_is_bounded_without_truncation()->TestResult {
    for v in [serde_json::json!({"direction":"all","wrap":false}),serde_json::json!({"direction":"forward","wrap":0}),
        serde_json::json!({"direction":"forward"}),serde_json::json!({"direction":"forward","wrap":false,"approved":true})] {
        assert!(serde_json::from_value::<Request>(v).is_err());}
    let b=review::with_body("<hp:p id='1'><hp:run><hp:t>K</hp:t></hp:run></hp:p>")?;let s=ImportedDocumentStructure::import(source(&b,"bounds")?)?;
    let index=s.source_text_index(&b,Default::default())?;let found=index.find(query("K"))?;let original_len=found.canonical_json()?.len();
    let nav=found.navigate(&step(Direction::Forward,false,None),[0;32])?;let expected=nav.canonical_json()?;
    assert!(expected.len()<=original_len);
    let bounded=s.source_text_index(&b,SourceSearchLimits::new(SourceSearchLimitConfig {result_bytes:original_len,..Default::default()})?)?;
    let found=bounded.find(query("K"))?;assert_eq!(found.navigate(&step(Direction::Forward,false,None),[0;32])?.canonical_json()?,expected);
    let too_small=s.source_text_index(&b,SourceSearchLimits::new(SourceSearchLimitConfig {result_bytes:original_len-1,..Default::default()})?)?;
    assert!(matches!(too_small.find(query("K")),Err(E::Output)));Ok(())
}
