//! Required-axis coverage must reject unknown formatting, not convert it into zero matches.
use hwpx_package::{CharacterStyleCatalogReader,ParagraphStyleCatalogReader,BinaryProperty,HorizontalAlignment,
    document_import::{ImportedSourcePackage,forms::ImportedDocumentForms,search::{SourceSearchQuery as Query,SourceSearchMode as Mode,
    SourceSearchLimits,SourceSearchLimitConfig as Config,SourceSearchError as E,selector::{SourceIndexScopeSelector as Scope,SourceIndexBoundary as Boundary},
    reviews::{SourceReviewTextPolicy as Policy,selector::resolved_styles::SourceResolvedStyleSearchError as RE},
    inspection::definitions::{DefinitionAlignment as Align,resolved::SourceResolvedStyleFilter as Filter},
    navigation::{SourceSearchNavigationRequest as Next,SourceSearchDirection as Direction}}}};
use domain_ir::DocumentId;
use sha2::{Digest as _,Sha256};
#[allow(dead_code)] #[path="support/search_definition_fixture.rs"] mod fixture;
#[allow(dead_code)] #[path="support/review_scope_fixture.rs"] mod review;
type TestResult=Result<(),Box<dyn std::error::Error>>;
fn forms(raw:&[u8])->Result<ImportedDocumentForms,Box<dyn std::error::Error>> {Ok(ImportedDocumentForms::import(ImportedSourcePackage::import(raw,DocumentId::parse("resolved-style")?,Sha256::digest(raw).into(),Default::default())?)?)}
fn q(text:&str)->Query<'_> {Query {query:text,mode:Mode::Literal,case_sensitive:true,whole_word:false,max_results:100}}
fn bold()->Filter {Filter {bold:Some(true),..Default::default()}}
fn p(id:u32,text:&str)->String {format!("<hp:p id='{id}' paraPrIDRef='1' styleIDRef='0'><hp:run charPrIDRef='1'><hp:t>{text}</hp:t></hp:run></hp:p>")}
fn all()->Policy {Policy {include_hidden_explanations:true,include_memo_bodies:true}}
fn review_body()->String {review::body().replace("<hp:p id='1'>","<hp:p id='1' paraPrIDRef='1' styleIDRef='0'>")
    .replace("<hp:p id='11'>","<hp:p id='11' paraPrIDRef='1' styleIDRef='0'>").replace("<hp:p id='12'>","<hp:p id='12' paraPrIDRef='1' styleIDRef='0'>")
    .replace("<hp:run>","<hp:run charPrIDRef='1'>")}

#[test]
fn resolved_styles_direct_values_use_original_typed_readers_not_named_defaults()->TestResult {
    let raw=fixture::package(&p(1,"K"))?;let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;
    let filter=Filter {italic:Some(true),height_hwpunit:Some(1000),text_rgb:Some([0,0,0]),alignment:Some(Align::Right),..bold()};
    let found=index.find_resolved_style(q("K"),Scope::Document,all(),filter)?;assert_eq!(found.search().result().matches().len(),1);
    let header=fixture::header()?;let chars=CharacterStyleCatalogReader::read(header.as_bytes(),Default::default())?;
    let paras=ParagraphStyleCatalogReader::read(header.as_bytes(),Default::default())?;
    assert_eq!(chars.styles[1].effects.bold,BinaryProperty::On);assert_eq!(paras.styles[1].horizontal_alignment,HorizontalAlignment::Right);
    assert_eq!(found.coverage().resolved_character_segments,1);assert_eq!(found.coverage().resolved_paragraph_segments,1);
    assert!(found.coverage().requested_axes_complete());assert!(!found.coverage().inferred_default_or_named_fallback);Ok(())
}
#[test]
fn resolved_styles_false_predicates_are_not_absent_and_both_axes_are_conjunctive()->TestResult {
    let body=p(1,"K")+&p(2,"K").replace("charPrIDRef='1'","charPrIDRef='0'").replace("paraPrIDRef='1'","paraPrIDRef='0'");
    let raw=fixture::package(&body)?;let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;
    for (filter,count) in[(Filter {bold:Some(false),italic:Some(false),alignment:Some(Align::Justify),..Default::default()},1),
        (Filter {alignment:Some(Align::Justify),..bold()},0),(Filter {alignment:Some(Align::Right),..bold()},1)] {
        assert_eq!(i.find_resolved_style(q("K"),Scope::Document,all(),filter)?.search().result().matches().len(),count);
    }Ok(())
}
#[test]
fn resolved_styles_missing_direct_references_reject_before_even_an_absent_query()->TestResult {
    let raw=fixture::package("<hp:p id='1' styleIDRef='0'><hp:run><hp:t>K</hp:t></hp:run></hp:p>")?;let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;
    for query in["K","ABSENT"] {match i.find_resolved_style(q(query),Scope::Document,all(),Filter {alignment:Some(Align::Right),..bold()}) {
        Err(RE::Unresolved(c))=>{assert_eq!(c.missing_run_segments,1);assert_eq!(c.missing_paragraph_segments,1);assert!(!c.requested_axes_complete());},_=>panic!("unresolved axes must reject")
    }}Ok(())
}
#[test]
fn resolved_styles_present_text_style_is_unresolved_even_when_its_value_agrees()->TestResult {
    for id in[0,1] {let raw=fixture::package(&p(1,"K").replace("<hp:t>",&format!("<hp:t charStyleIDRef='{id}'>")))?;let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;
        match i.find_resolved_style(q("ABSENT"),Scope::Document,all(),bold()) {Err(RE::Unresolved(c))=>{assert_eq!(c.unresolved_text_style_segments,1);assert_eq!(c.resolved_character_segments,0);assert_eq!(c.missing_run_segments,0);},_=>panic!("text precedence cannot be guessed")}
    }Ok(())
}
#[test]
fn resolved_styles_only_requested_axes_require_resolution()->TestResult {
    for (body,filter) in[(p(1,"K").replace("charPrIDRef='1'","").replace("<hp:t>","<hp:t charStyleIDRef='1'>"),Filter {alignment:Some(Align::Right),..Default::default()}),
        (p(1,"K").replace("paraPrIDRef='1'",""),bold())] {
        let raw=fixture::package(&body)?;let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;
        let found=i.find_resolved_style(q("K"),Scope::Document,all(),filter)?;assert_eq!(found.search().result().matches().len(),1);assert!(found.coverage().requested_axes_complete());
    }Ok(())
}
#[test]
fn resolved_styles_four_scopes_and_clipped_selection_assess_only_selected_segments()->TestResult {
    let raw=fixture::package(&p(1,"K K"))?;let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;let inv=i.scope_inventory()?;let b=&inv.inventory.blocks[0];
    let nodes=[inv.inventory.nodes.iter().find(|n|n.source_handle==b.paragraph_handle).ok_or("node")?.node_id.clone()];
    let start=Boundary {paragraph_handle:b.paragraph_handle.clone(),block_index:b.block_index,normalized_scalar:2};let end=Boundary {normalized_scalar:3,..start.clone()};
    for (scope,count) in[(Scope::Document,2),(Scope::Section(&inv.inventory.section_ids),2),(Scope::NodeSet(&nodes),2),
        (Scope::Selection {index_sha256:inv.inventory.index.index_sha256,start:&start,end:&end},1)] {
        let found=i.find_resolved_style(q("K"),scope,all(),bold())?;assert_eq!(found.search().result().matches().len(),count);assert_eq!(found.coverage().selected_text_segments,1);
    }
    let raw=fixture::package(&(p(1,"K")+&p(2,"BAD").replace("charPrIDRef='1'","")))?;let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;let inv=i.scope_inventory()?;let b=&inv.inventory.blocks[0];
    let nodes=[inv.inventory.nodes.iter().find(|n|n.source_handle==b.paragraph_handle).ok_or("node")?.node_id.clone()];
    assert_eq!(i.find_resolved_style(q("K"),Scope::NodeSet(&nodes),all(),bold())?.coverage().selected_text_segments,1);
    assert!(matches!(i.find_resolved_style(q("K"),Scope::Document,all(),bold()),Err(RE::Unresolved(_))));Ok(())
}
#[test]
fn resolved_styles_hidden_and_memo_exclusions_precede_resolution_and_result_caps()->TestResult {
    let body=review_body().replace("<hp:t>HIDDEN","<hp:t charStyleIDRef='1'>HIDDEN").replace("<hp:t>MEMO","<hp:t charStyleIDRef='1'>MEMO");
    let raw=fixture::package(&body)?;let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;
    let found=i.find_resolved_style(Query {max_results:2,..q("K")},Scope::Document,Policy::default(),bold())?;assert_eq!(found.search().result().matches().len(),2);
    assert_eq!(found.coverage().unresolved_text_style_segments,0);
    for policy in[Policy {include_hidden_explanations:true,include_memo_bodies:false},Policy {include_hidden_explanations:false,include_memo_bodies:true},all()] {
        assert!(matches!(i.find_resolved_style(q("ABSENT"),Scope::Document,policy,bold()),Err(RE::Unresolved(_))));
    }Ok(())
}
#[test]
fn resolved_styles_all_original_nfc_contributors_must_match_not_just_the_first()->TestResult {
    for mixed in[false,true] {let body=format!("<hp:p id='1' paraPrIDRef='1' styleIDRef='0'><hp:run charPrIDRef='1'><hp:t>Xᄀ</hp:t></hp:run><hp:run charPrIDRef='{}'><hp:t>ᅡᆨY</hp:t></hp:run></hp:p>",if mixed{0}else{1});
        let raw=fixture::package(&body)?;let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;let found=i.find_resolved_style(q("각"),Scope::Document,all(),bold())?;
        assert_eq!(found.search().result().matches().len(),usize::from(!mixed));assert_eq!(found.coverage().observed_segment_visits,2);
        if !mixed{assert_eq!(found.search().result().matches()[0].pieces.len(),2);}
    }Ok(())
}
#[test]
fn resolved_styles_regex_clipped_window_and_zero_width_retain_original_matching_rules()->TestResult {
    let raw=fixture::package(&p(1,"A K Z"))?;let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;let inv=i.scope_inventory()?;let b=&inv.inventory.blocks[0];
    let start=Boundary {paragraph_handle:b.paragraph_handle.clone(),block_index:b.block_index,normalized_scalar:2};let end=Boundary {normalized_scalar:3,..start.clone()};
    let scope=Scope::Selection {index_sha256:inv.inventory.index.index_sha256,start:&start,end:&end};
    let found=i.find_resolved_style(Query {query:"^k$",mode:Mode::Regex,case_sensitive:false,whole_word:true,..q("K")},scope,all(),bold())?;
    assert_eq!(found.search().result().matches().len(),1);assert_eq!(found.search().result().matches()[0].start_normalized_scalar,2);
    assert!(i.find_resolved_style(Query {query:"^|$",mode:Mode::Regex,..q("K")},scope,all(),bold())?.search().result().matches().is_empty());Ok(())
}
#[test]
fn resolved_styles_dangling_excluded_references_and_bad_headers_still_fail_original_admission()->TestResult {
    let body=review_body().replace("<hp:t>HIDDEN","<hp:t charStyleIDRef='999'>HIDDEN");let raw=fixture::package(&body)?;let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;
    assert!(matches!(i.find_resolved_style(q("ABSENT"),Scope::Document,Policy::default(),bold()),Err(RE::Search(E::Definition))));
    let header=fixture::header()?.replacen("charProperties itemCnt=\"7\"","charProperties itemCnt=\"8\"",1);let raw=fixture::package_with_header(&p(1,"K"),&header)?;let f=forms(&raw)?;
    assert!(matches!(f.source_review_scope_index(&raw,Default::default())?.find_resolved_style(q("K"),Scope::Document,all(),bold()),Err(RE::Search(E::Definition))));Ok(())
}
#[test]
fn resolved_styles_filter_is_closed_nonempty_and_rejects_old_axis_and_bad_value_shapes()->TestResult {
    assert!(matches!(Filter::default().validate(),Err(E::Filter)));
    for value in[serde_json::json!({"character_source":"run_property","bold":true}),serde_json::json!({"bold":1}),serde_json::json!({"height_hwpunit":-1}),
        serde_json::json!({"text_rgb":[256,0,0]}),serde_json::json!({"alignment":"unknown"}),serde_json::json!({"approved":true}),serde_json::json!([])] {assert!(serde_json::from_value::<Filter>(value).is_err());}
    Filter {bold:Some(false),..Default::default()}.validate()?;Ok(())
}
#[test]
fn resolved_styles_invalid_scope_and_stale_source_never_return_empty_success()->TestResult {
    let raw=fixture::package(&p(1,"K"))?;let changed=fixture::package(&p(1,"CHANGED"))?;let f=forms(&raw)?;
    assert!(f.source_review_scope_index(&changed,Default::default()).is_err());let i=f.source_review_scope_index(&raw,Default::default())?;let inv=i.scope_inventory()?;let b=&inv.inventory.blocks[0];
    let cut=Boundary {paragraph_handle:b.paragraph_handle.clone(),block_index:b.block_index,normalized_scalar:0};
    assert!(matches!(i.find_resolved_style(q("ABSENT"),Scope::Selection {index_sha256:[0;32],start:&cut,end:&cut},all(),bold()),Err(RE::Search(E::Scope))));
    assert!(matches!(i.find_resolved_style(q("ABSENT"),Scope::NodeSet(&[]),all(),bold()),Err(RE::Search(E::Scope))));Ok(())
}
#[test]
fn resolved_styles_predicate_scope_policy_and_query_bind_retained_navigation()->TestResult {
    let raw=fixture::package(&review_body())?;let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;
    let found=i.find_resolved_style(q("K"),Scope::Document,all(),bold())?;let first=found.navigate(&Next {direction:Direction::Forward,wrap:false,cursor:None},[3;32])?;
    let next=Next {direction:Direction::Forward,wrap:false,cursor:first.cursor().cloned()};assert_eq!(found.navigate(&next,[3;32])?.match_index(),Some(1));
    for other in[i.find_resolved_style(q("K"),Scope::Document,Policy::default(),bold())?,i.find_resolved_style(q("K"),Scope::Document,all(),Filter {italic:Some(true),..Default::default()})?,
        i.find_resolved_style(Query {case_sensitive:false,..q("K")},Scope::Document,all(),bold())?] {
        assert_ne!(found.search().request_sha256(),other.search().request_sha256());assert!(matches!(other.navigate(&next,[3;32]),Err(E::Cursor)));
    }assert!(matches!(found.navigate(&next,[4;32]),Err(E::Cursor)));Ok(())
}
#[test]
fn resolved_styles_exact_response_budget_includes_coverage_and_is_atomic()->TestResult {
    let raw=fixture::package(&p(1,"K"))?;let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;
    let found=i.find_resolved_style(q("K"),Scope::Document,all(),bold())?;let bytes=found.canonical_json()?;
    let i=f.source_review_scope_index(&raw,SourceSearchLimits::new(Config {result_bytes:bytes.len(),..Default::default()})?)?;
    assert_eq!(i.find_resolved_style(q("K"),Scope::Document,all(),bold())?.canonical_json()?,bytes);
    let i=f.source_review_scope_index(&raw,SourceSearchLimits::new(Config {result_bytes:bytes.len()-1,..Default::default()})?)?;
    assert!(matches!(i.find_resolved_style(q("K"),Scope::Document,all(),bold()),Err(RE::Search(E::Output))));Ok(())
}
#[test]
fn resolved_styles_query_match_and_pattern_limits_remain_fail_closed()->TestResult {
    let raw=fixture::package(&p(1,"K K"))?;let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;
    assert!(matches!(i.find_resolved_style(Query {max_results:1,..q("K")},Scope::Document,all(),bold()),Err(RE::Search(E::Limit))));
    assert!(matches!(i.find_resolved_style(Query {mode:Mode::Regex,..q("(")},Scope::Document,all(),bold()),Err(RE::Search(E::Pattern))));
    assert!(matches!(i.find_resolved_style(q(""),Scope::Document,all(),bold()),Err(RE::Search(E::Limit))));Ok(())
}
#[test]
fn resolved_styles_many_matches_assess_each_source_segment_once()->TestResult {
    let text=(0..128).map(|_|"<hp:run charPrIDRef='1'><hp:t>K</hp:t></hp:run>").collect::<String>();
    let raw=fixture::package(&format!("<hp:p id='1' paraPrIDRef='1' styleIDRef='0'>{text}</hp:p>"))?;let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;
    let found=i.find_resolved_style(Query {max_results:128,..q("K")},Scope::Document,all(),bold())?;
    assert_eq!(found.search().result().matches().len(),128);assert_eq!(found.coverage().selected_text_segments,128);assert_eq!(found.coverage().observed_segment_visits,128);Ok(())
}
#[test]
fn resolved_styles_output_preserves_source_and_never_exposes_query_body_author_or_authority()->TestResult {
    let raw=fixture::package(&review_body())?;let original=Sha256::digest(&raw);let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;
    let found=i.find_resolved_style(q("PRIVATE-QUERY"),Scope::Document,all(),bold())?;let bytes=found.canonical_json()?;let text=String::from_utf8(bytes.clone())?;
    for value in["PRIVATE-QUERY","PRIVATE-AUTHOR","CACHE FROZEN"] {assert!(!text.contains(value));assert!(!format!("{found:?}").contains(value));}
    let value:serde_json::Value=serde_json::from_slice(&bytes)?;assert_eq!(value["native_cascade_visibility_or_execution_authority"],false);
    assert!(!found.coverage().native_effective_visibility_or_execution_authority);assert_eq!(Sha256::digest(&raw),original);Ok(())
}
#[test]
fn resolved_styles_empty_selection_has_no_invented_formatting_or_zero_width_match()->TestResult {
    let raw=fixture::package(&p(1,"K"))?;let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;let inv=i.scope_inventory()?;let b=&inv.inventory.blocks[0];
    let cut=Boundary {paragraph_handle:b.paragraph_handle.clone(),block_index:b.block_index,normalized_scalar:1};
    let found=i.find_resolved_style(Query {mode:Mode::Regex,..q("^|$")},Scope::Selection {index_sha256:inv.inventory.index.index_sha256,start:&cut,end:&cut},all(),bold())?;
    assert_eq!(found.coverage().selected_text_segments,0);assert!(found.search().result().matches().is_empty());Ok(())
}
#[path="resolved_style_control_context.rs"] mod control_context;
