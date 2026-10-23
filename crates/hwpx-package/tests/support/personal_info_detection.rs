//! Synthetic format markers only. The caller's rules are not Hancom defaults or validated identities.
use super::*;
use hwpx_package::document_import::search::{SourceSearchError as FindError,personal_info::{SourcePersonalInfoDetectionPolicy as Detection,
    SourcePersonalInfoRule as Rule,SourcePersonalInfoKind as Kind,SourcePersonalInfoDetectionResult as Found},
    reviews::selector::SourceReviewScopeIndex,navigation::{SourceSearchNavigationRequest as Next,SourceSearchDirection as Direction}};
fn rule(id:&str,kind:Kind,query:&str,regex:bool)->Rule{Rule{rule_id:id.into(),kind,query:query.into(),regex,case_sensitive:true,whole_word:false}}
fn policy(query:&str,regex:bool)->Result<Detection,FindError>{Detection::new(vec![rule("custom",Kind::Custom,query,regex)])}
fn detect(index:&SourceReviewScopeIndex<'_>,p:&Detection,scope:Scope<'_>)->Result<Found,FindError>{index.find_personal_info_candidates(p,scope,all())}
fn request(cursor:Option<hwpx_package::document_import::search::navigation::SourceSearchCursor>,direction:Direction,wrap:bool)->Next{Next{direction,wrap,cursor}}
#[test]
fn nine_documented_categories_and_custom_are_explicit_rule_labels_not_identity_assertions()->R{
    let kinds=[Kind::Telephone,Kind::ResidentRegistration,Kind::ForeignRegistration,Kind::Email,Kind::Account,Kind::CreditCard,Kind::IpAddress,Kind::BirthDate,Kind::Address,Kind::Custom];
    let rules:Vec<_>=kinds.iter().enumerate().map(|(i,k)|rule(&format!("format{i}"),*k,&format!("MARK{i:02}"),false)).collect();
    let text=rules.iter().map(|r|r.query.as_str()).collect::<Vec<_>>().join(" ");let raw=fixture::package(&para(1,&text))?;let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;
    let found=detect(&index,&Detection::new(rules)?,Scope::Document)?;assert_eq!(found.rule_matches().len(),10);
    for(i,m)in found.rule_matches().iter().enumerate(){assert_eq!(m.occurrence_index,i);assert_eq!(m.kind,kinds[i]);}
    let v:serde_json::Value=serde_json::from_slice(&found.canonical_json()?)?;assert_eq!(v["personal_identity_or_native_format_validated"],false);assert_eq!(v["mutation_or_execution_authority"],false);Ok(())
}
#[test]
fn cross_run_regex_and_entities_return_original_text_anchors_without_values()->R{
    let body="<hp:p id='1'><hp:run><hp:t>BEG</hp:t></hp:run><hp:run><hp:t>IN&amp;END</hp:t></hp:run></hp:p>";
    let raw=fixture::package(body)?;let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;let found=detect(&index,&policy("BEGIN.END",true)?,Scope::Document)?;
    let m=&found.search().result().matches()[0];assert_eq!(m.pieces.len(),2);assert!(m.source_scalar_selection_exact);assert_eq!(m.end_normalized_scalar,9);Ok(())
}
#[test]
fn retained_candidate_selection_masks_only_the_found_original_range()->R{
    let text="KEEP PRIVATE-MARK TAIL";let raw=fixture::package(&para(1,text))?;let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;
    let found=detect(&index,&policy("PRIVATE-MARK",false)?,Scope::Document)?;let selected=found.selection(0)?;
    assert_eq!(selected.request_sha256(),found.request_sha256());assert_eq!(selected.source_package_sha256(),<[u8;32]>::from(Sha256::digest(&raw)));
    let c=mask(&f,&raw,selected.scope(),all(),Mask::ThreeAsterisksPerTextGroup)?;exact(&raw,&c,text,"KEEP *** TAIL")?;
    assert_eq!(section(&raw)?,section(&fixture::package(&para(1,text))?)?);Ok(())
}
#[test]
fn literal_nfc_query_maps_decomposed_original_run_contributors()->R{
    let raw=fixture::package(&para(1,"각"))?;let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;
    let found=detect(&index,&policy("각",false)?,Scope::Document)?;assert_eq!(found.search().result().matches().len(),1);
    let selected=found.selection(0)?;let c=mask(&f,&raw,selected.scope(),all(),Mask::PerOriginalScalarPreserveSlots)?;exact(&raw,&c,"각","***")?;Ok(())
}
#[test]
fn partial_normalized_contribution_never_produces_an_edit_selection()->R{
    let raw=fixture::package(&para(1,"\u{344}"))?;let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;
    let found=detect(&index,&policy("\u{308}",true)?,Scope::Document)?;assert_eq!(found.rule_matches().len(),1);
    assert!(!found.search().result().matches()[0].source_scalar_selection_exact);assert!(matches!(found.selection(0),Err(FindError::Scope)));Ok(())
}
#[test]
fn control_and_paragraph_barriers_are_not_joined_into_private_candidates()->R{
    let text="BEG<hp:tab width='1' leader='0' type='0'> </hp:tab>IN BEG<hp:lineBreak/>IN";let raw=fixture::package(&(para(1,text)+&para(2,"BEG")+&para(3,"IN")))?;
    let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;assert!(detect(&index,&policy("BEGIN",false)?,Scope::Document)?.rule_matches().is_empty());Ok(())
}
#[test]
fn explicit_rule_order_resolves_equal_start_overlap_and_nonoverlapping_scan_is_stable()->R{
    let raw=fixture::package(&para(1,"AB AB"))?;let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;
    let a=rule("short",Kind::Custom,"A",false);let b=rule("long",Kind::Address,"AB",false);
    let first=detect(&index,&Detection::new(vec![a.clone(),b.clone()])?,Scope::Document)?;let second=detect(&index,&Detection::new(vec![b,a])?,Scope::Document)?;
    assert!(first.rule_matches().iter().all(|m|m.rule_id=="short"));assert!(second.rule_matches().iter().all(|m|m.rule_id=="long"));
    assert_eq!(first.search().result().matches()[0].end_normalized_scalar,1);assert_eq!(second.search().result().matches()[0].end_normalized_scalar,2);assert_ne!(first.request_sha256(),second.request_sha256());Ok(())
}
#[test]
fn per_rule_case_and_whole_word_flags_do_not_leak_between_alternatives()->R{
    let raw=fixture::package(&para(1,"ab AB XABX cd CD"))?;let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;
    let mut a=rule("first",Kind::Custom,"AB",false);a.case_sensitive=false;a.whole_word=true;let b=rule("second",Kind::Custom,"CD",false);
    let found=detect(&index,&Detection::new(vec![a,b])?,Scope::Document)?;assert_eq!(found.rule_matches().len(),3);assert_eq!(found.rule_matches()[2].rule_id,"second");Ok(())
}
#[test]
fn regex_inline_flags_are_scoped_and_inner_capture_groups_do_not_change_rule_identity()->R{
    let raw=fixture::package(&para(1,"ab CD cd"))?;let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;
    let p=Detection::new(vec![rule("one",Kind::Custom,"(?i)(a)(?P<inner>b)",true),rule("two",Kind::Email,"CD",false)])?;
    let found=detect(&index,&p,Scope::Document)?;assert_eq!(found.rule_matches().len(),2);assert_eq!(found.rule_matches()[1].kind,Kind::Email);Ok(())
}
#[test]
fn rule_regexes_are_validated_in_isolation_before_combination()->R{
    let raw=fixture::package(&para(1,"ABC"))?;let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;
    for q in ["(","x)|(?P<hijack>x)",r"(?P<p09pi0>X)",r"(?=X)"]{
        assert!(matches!(detect(&index,&policy(q,true)?,Scope::Document),Err(FindError::Pattern)));}Ok(())
}
#[test]
fn empty_and_observed_zero_width_rules_fail_instead_of_returning_maskable_positions()->R{
    let raw=fixture::package(&para(1,"ABC"))?;let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;
    assert!(policy("",false).is_err());for q in ["A*","^",r"\b"]{assert!(matches!(detect(&index,&policy(q,true)?,Scope::Document),Err(FindError::Pattern)));}Ok(())
}
#[test]
fn policy_rule_count_query_aggregate_identifiers_and_duplicates_have_finite_strict_limits()->R{
    assert!(Detection::new(vec![]).is_err());assert!(Detection::new((0..17).map(|i|rule(&format!("r{i}"),Kind::Custom,"A",false)).collect()).is_err());
    assert!(Detection::new(vec![rule("same",Kind::Custom,"A",false),rule("same",Kind::Custom,"B",false)]).is_err());
    for id in ["","private@example.invalid","한글","../outside"]{assert!(Detection::new(vec![rule(id,Kind::Custom,"A",false)]).is_err());}
    assert!(policy(&"x".repeat(4097),false).is_err());assert!(Detection::new(vec![rule("a",Kind::Custom,&"x".repeat(3000),false),rule("b",Kind::Custom,&"y".repeat(2000),false)]).is_err());Ok(())
}
#[test]
fn document_section_node_and_exact_selection_use_the_same_original_index()->R{
    let raw=fixture::package(&(para(1,"MARK MARK")+&para(2,"MARK")))?;let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;let inv=index.scope_inventory()?;
    let b=&inv.inventory.blocks[0];let id=inv.inventory.nodes.iter().find(|n|n.source_handle==b.paragraph_handle).ok_or("node")?.node_id.clone();let nodes=[id];let start=boundary(b,5);let end=boundary(b,9);let p=policy("MARK",false)?;
    for(scope,n)in [(Scope::Document,3),(Scope::Section(&inv.inventory.section_ids),3),(Scope::NodeSet(&nodes),2),(Scope::Selection{index_sha256:inv.inventory.index.index_sha256,start:&start,end:&end},1)]{
        assert_eq!(detect(&index,&p,scope)?.rule_matches().len(),n);}Ok(())
}
#[test]
fn invalid_scopes_and_stale_source_never_fall_back_to_whole_document()->R{
    let raw=fixture::package(&para(1,"MARK"))?;let f=forms(&raw)?;assert!(f.source_review_scope_index(&fixture::package(&para(1,"CHANGED"))?,Default::default()).is_err());
    let index=f.source_review_scope_index(&raw,Default::default())?;let inv=index.scope_inventory()?;let id=inv.inventory.nodes[0].node_id.clone();let p=policy("MARK",false)?;
    for nodes in [vec![],vec![id.clone(),id],vec![LogicalId::parse("foreign")?]]{assert!(detect(&index,&p,Scope::NodeSet(&nodes)).is_err());}
    let start=boundary(&inv.inventory.blocks[0],0);let end=boundary(&inv.inventory.blocks[0],1);assert!(detect(&index,&p,Scope::Selection{index_sha256:[0;32],start:&start,end:&end}).is_err());Ok(())
}
#[test]
fn hidden_and_memo_policy_is_applied_before_detection_and_binds_results()->R{
    let raw=fixture::package(&review::body())?;let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;let p=policy("K",false)?;let mut hashes=std::collections::BTreeSet::new();
    for(h,m,n)in [(false,false,2),(true,false,4),(false,true,4),(true,true,6)]{let found=index.find_personal_info_candidates(&p,Scope::Document,Policy{include_hidden_explanations:h,include_memo_bodies:m})?;
        assert_eq!(found.rule_matches().len(),n);hashes.insert(found.request_sha256());assert_eq!(found.search().match_regions().len(),n);}
    assert_eq!(hashes.len(),4);Ok(())
}
#[test]
fn supplemental_memo_node_can_be_selected_without_author_metadata_exposure()->R{
    let raw=fixture::package(&review::body())?;let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;let inv=index.scope_inventory()?;
    let b=inv.inventory.blocks.iter().zip(&inv.block_regions).find(|(_,r)|**r==SourceTextRegion::MemoBody).ok_or("memo")?.0;
    let node=inv.inventory.nodes.iter().find(|n|n.source_handle==b.paragraph_handle).ok_or("node")?.node_id.clone();
    let found=detect(&index,&policy("MEMO K K",false)?,Scope::NodeSet(&[node]))?;assert_eq!(found.rule_matches().len(),1);
    let text=String::from_utf8(found.canonical_json()?)?;assert!(!text.contains("PRIVATE-AUTHOR")&&!text.contains("MEMO K K"));Ok(())
}
#[test]
fn navigation_uses_retained_matches_and_rejects_another_policy_or_context_cursor()->R{
    let raw=fixture::package(&para(1,"MARK MARK"))?;let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;let found=detect(&index,&policy("MARK",false)?,Scope::Document)?;
    let a=found.navigate(&request(None,Direction::Forward,false),[1;32])?;assert_eq!(a.match_index(),Some(0));
    let b=found.navigate(&request(a.cursor().cloned(),Direction::Forward,false),[1;32])?;assert_eq!(b.match_index(),Some(1));
    let end=found.navigate(&request(b.cursor().cloned(),Direction::Forward,false),[1;32])?;assert!(end.exhausted());
    let wrap=found.navigate(&request(b.cursor().cloned(),Direction::Forward,true),[1;32])?;assert!(wrap.wrapped());assert_eq!(wrap.match_index(),Some(0));
    let backwards=found.navigate(&request(None,Direction::Backward,false),[1;32])?;assert_eq!(backwards.match_index(),Some(1));
    assert!(found.navigate(&request(a.cursor().cloned(),Direction::Forward,false),[2;32]).is_err());
    let other=detect(&index,&Detection::new(vec![rule("different",Kind::Email,"MARK",false)])?,Scope::Document)?;
    assert!(other.navigate(&request(a.cursor().cloned(),Direction::Forward,false),[1;32]).is_err());Ok(())
}
#[test]
fn no_matches_are_complete_empty_metadata_and_have_no_selection()->R{
    let raw=fixture::package(&para(1,"OTHER"))?;let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;let found=detect(&index,&policy("MARK",false)?,Scope::Document)?;
    assert!(found.rule_matches().is_empty());assert!(found.selection(0).is_err());assert!(found.navigate(&request(None,Direction::Forward,true),[0;32])?.exhausted());Ok(())
}
#[test]
fn public_json_debug_and_selection_contain_no_matched_value_query_or_per_value_hash()->R{
    let raw=fixture::package(&para(1,"PRIVATE-FORMAT-MARK"))?;let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;
    let r=rule("custom",Kind::Custom,"PRIVATE-FORMAT-MARK",false);let debug=format!("{r:?}");let p=Detection::new(vec![r])?;let found=detect(&index,&p,Scope::Document)?;let selected=found.selection(0)?;
    for text in [String::from_utf8(found.canonical_json()?)?,format!("{debug}{p:?}{found:?}{selected:?}"),serde_json::to_string(&selected)?]{
        assert!(!text.contains("PRIVATE-FORMAT-MARK")&&!text.contains("source_pieces_sha256")&&!text.contains("matched_value_sha256")&&!text.contains("\"query\":"));}Ok(())
}
#[test]
fn policy_kind_mode_case_order_and_scope_are_bound_even_when_positions_are_equal()->R{
    let raw=fixture::package(&para(1,"MARK"))?;let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;let mut hashes=std::collections::BTreeSet::new();
    for r in [rule("a",Kind::Custom,"MARK",false),rule("a",Kind::Email,"MARK",false),rule("b",Kind::Custom,"MARK",false),rule("a",Kind::Custom,"MARK",true),
        Rule{case_sensitive:false,..rule("a",Kind::Custom,"MARK",false)}]{let found=detect(&index,&Detection::new(vec![r])?,Scope::Document)?;assert_eq!(found.rule_matches().len(),1);hashes.insert(found.request_sha256());}
    assert_eq!(hashes.len(),5);Ok(())
}
#[test]
fn aggregate_matches_reported_points_query_and_regex_compilation_limits_are_not_silently_truncated()->R{
    let raw=fixture::package(&para(1,"A123 A456"))?;let f=forms(&raw)?;
    for config in [Config{matches:1,..Default::default()},Config{reported_points:1,..Default::default()},Config{query_bytes:3,..Default::default()},Config{pattern_bytes:1,..Default::default()}]{
        let index=f.source_review_scope_index(&raw,SourceSearchLimits::new(config)?)?;assert!(detect(&index,&policy("A[0-9]+",true)?,Scope::Document).is_err());}Ok(())
}
#[test]
fn exact_entire_detection_response_byte_limit_succeeds_and_one_byte_less_fails()->R{
    let raw=fixture::package(&para(1,"MARK"))?;let f=forms(&raw)?;let p=policy("MARK",false)?;let index=f.source_review_scope_index(&raw,Default::default())?;
    let expected=detect(&index,&p,Scope::Document)?.canonical_json()?;let n=expected.len();
    let exact=f.source_review_scope_index(&raw,SourceSearchLimits::new(Config{result_bytes:n,..Default::default()})?)?;
    assert_eq!(detect(&exact,&p,Scope::Document)?.canonical_json()?,expected);
    let short=f.source_review_scope_index(&raw,SourceSearchLimits::new(Config{result_bytes:n-1,..Default::default()})?)?;assert!(detect(&short,&p,Scope::Document).is_err());Ok(())
}
#[test]
fn malformed_rule_schema_and_unknown_kind_are_rejected_without_implicit_defaults()->R{
    let base=serde_json::to_value(rule("r",Kind::Email,"MARK",false))?;
    for change in ["unknown","missing","kind"]{let mut v=base.clone();match change{"unknown"=>v["replacement"]=serde_json::json!("***"),"missing"=>{v.as_object_mut().ok_or("object")?.remove("case_sensitive");},_=>v["kind"]=serde_json::json!("native_auto")};assert!(serde_json::from_value::<Rule>(v).is_err());}Ok(())
}
