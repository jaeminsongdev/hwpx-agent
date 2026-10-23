//! Operation-local memoization, real source matching, and directly affected existing paths only.
#[path="../src/document_import/search/inspection/definitions/last_predicate.rs"] mod last_predicate;
#[path="document_import_search_definitions.rs"] mod explicit;
#[path="document_import_resolved_style_search.rs"] mod resolved;
#[path="document_import_selector_styles.rs"] mod selector;
#[path="document_import_border_definition_search.rs"] mod border;
#[path="document_import_scoped_fonts.rs"] mod fonts;
#[path="document_import_paragraph_style_replacement.rs"] mod paragraphs;
#[path="support/font_definition_contract.rs"] mod font_definitions;
#[path="support/tab_definition_contract.rs"] mod tab_definitions;
#[allow(dead_code)] #[path="support/detail_axes_fixture.rs"] mod fixture;
use hwpx_package::document_import::{ImportedSourcePackage,forms::ImportedDocumentForms,
    search::{SourceSearchQuery as Query,SourceSearchMode as Mode,scope::SourceSearchScope,selector::SourceIndexScopeSelector as Scope,
        inspection::definitions::SourceDefinitionStyleFilter as Filter}};
use domain_ir::DocumentId;
use sha2::{Digest as _,Sha256};
use serde_json::json;
use std::cell::Cell;
type TestResult=Result<(),Box<dyn std::error::Error>>;
type Key=(Option<usize>,Option<usize>);
fn q(text:&str,mode:Mode)->Query<'_> {Query {query:text,mode,case_sensitive:true,whole_word:false,max_results:100}}
fn forms(raw:&[u8])->Result<ImportedDocumentForms,Box<dyn std::error::Error>> {Ok(ImportedDocumentForms::import(ImportedSourcePackage::import(raw,DocumentId::parse("predicate-local")?,Sha256::digest(raw).into(),Default::default())?)?)}
#[test]
fn last_predicate_repeated_true_and_false_need_two_evaluations_not_twenty_thousand() {
    let cache=last_predicate::LastPredicate::<Key>::default();let evaluated=Cell::new(0);
    for expected in[true,false] {for _ in 0..10_000 {
        let key=(Some(usize::from(expected)),Some(0));assert_eq!(cache.test(key,||{evaluated.set(evaluated.get()+1);expected}),expected);
    }}assert_eq!(evaluated.get(),2);
    assert!(std::mem::size_of_val(&cache)<=80); // One fixed-size pair, never a per-document collection.
}
#[test]
fn cache_key_distinguishes_absent_zero_both_axes_and_adversarial_alternation() {
    let cache=last_predicate::LastPredicate::<Key>::default();let count=Cell::new(0);
    let keys=[(None,Some(0)),(Some(0),Some(0)),(Some(0),None),(Some(0),Some(1)),(Some(1),Some(0))];
    for index in 0..10_000 {let key=keys[index%keys.len()];let expected=index%2==0;
        assert_eq!(cache.test(key,||{count.set(count.get()+1);expected}),expected);
    }assert_eq!(count.get(),10_000);
}
#[test]
fn cache_instances_never_share_another_predicate_or_source_value() {
    let first=last_predicate::LastPredicate::<Key>::default();let second=last_predicate::LastPredicate::<Key>::default();
    let third=last_predicate::LastPredicate::<Key>::default();let key=(Some(1),Some(1));
    assert!(first.test(key,||true));assert!(!second.test(key,||false));assert!(!third.test(key,||false));assert!(first.test(key,||panic!("repeat evaluated")));
}
fn details()->Result<Filter,serde_json::Error> {
    let mut characters=serde_json::Map::new();let mut paragraphs=serde_json::Map::new();
    for(yes,_)in fixture::characters::predicates(){characters.extend(yes.as_object().expect("character predicate").clone());}
    for(yes,_)in fixture::paragraphs::predicates(){paragraphs.extend(yes.as_object().expect("paragraph predicate").clone());}
    serde_json::from_value(json!({"character_source":"run_property","paragraph_source":"direct_property","character_details":characters,"paragraph_details":paragraphs}))
}
#[test]
fn many_same_definitions_and_a_changed_run_keep_all51_conjunctive_conditions()->TestResult {
    for(mixed,total)in[(false,1),(true,0)] {
        let mut runs=String::new();for index in 0..24 {let style=if mixed&&index==12{0}else{1};
            runs.push_str(&format!("<hp:run charPrIDRef='{style}'><hp:t>{}</hp:t></hp:run>","K".repeat(32)));}
        let body=format!("<hp:p id='1' paraPrIDRef='1' styleIDRef='0'>{runs}</hp:p>");let raw=fixture::package(&body)?;let original=raw.clone();
        let f=forms(&raw)?;let text=f.body_structure().source_text_index(&raw,Default::default())?;let inspection=text.inspection()?;let definitions=inspection.resolve_style_definitions()?;
        let filter=details()?;let a=definitions.find(q("K+",Mode::Regex),SourceSearchScope::MappedDocument,filter.clone())?;
        assert_eq!(a.matches().matches().len(),total);let b=definitions.find(q("K+",Mode::Regex),SourceSearchScope::MappedDocument,filter)?;
        assert_eq!(a.canonical_json()?,b.canonical_json()?);assert_eq!(raw,original);
    }Ok(())
}
#[test]
fn same_source_pair_with_new_predicate_and_new_source_does_not_reuse_old_acceptance()->TestResult {
    let body=fixture::p(1,"K");let raw=fixture::package(&body)?;let f=forms(&raw)?;
    let index=f.source_review_scope_index(&raw,Default::default())?;
    for(value,total)in[(true,1),(false,0),(true,1)] {
        let filter=serde_json::from_value(json!({"character_details":{"emboss":value}}))?;
        assert_eq!(index.find_resolved_style(q("K",Mode::Literal),Scope::Document,Default::default(),filter)?.search().result().matches().len(),total);
    }
    let mut header=fixture::characters::header()?;assert_eq!(header.matches("<hh:emboss/>").count(),1);header=header.replace("<hh:emboss/>","");
    let raw=fixture::paragraphs::definition::package_with_header(&body,&header)?;let f=forms(&raw)?;let other=f.source_review_scope_index(&raw,Default::default())?;
    let filter=serde_json::from_value::<hwpx_package::document_import::search::inspection::definitions::resolved::SourceResolvedStyleFilter>(json!({"character_details":{"emboss":true}}))?;
    assert_eq!(other.find_resolved_style(q("K",Mode::Literal),Scope::Document,Default::default(),filter)?.search().result().matches().len(),0);Ok(())
}
