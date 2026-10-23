use hwpx_package::document_import::{ImportedSourcePackage,forms::ImportedDocumentForms,
    search::{SourceSearchQuery as Query,SourceSearchMode as Mode,selector::SourceIndexScopeSelector as Scope,
        reviews::{SourceReviewTextPolicy as Policy,selector::resolved_styles::SourceResolvedStyleSearchError as RE},
        scope::SourceSearchScope,inspection::definitions::{SourceDefinitionStyleFilter as Explicit,resolved::SourceResolvedStyleFilter as Filter}}};
use domain_ir::DocumentId;
use sha2::{Digest as _,Sha256};
use serde_json::{json,Value};
#[allow(dead_code)] #[path="support/border_definition_fixture.rs"] mod fixture;
type TestResult=Result<(),Box<dyn std::error::Error>>;
fn forms(raw:&[u8])->Result<ImportedDocumentForms,Box<dyn std::error::Error>> {Ok(ImportedDocumentForms::import(ImportedSourcePackage::import(raw,DocumentId::parse("border-definition")?,Sha256::digest(raw).into(),Default::default())?)?)}
fn q(text:&str)->Query<'_> {Query {query:text,mode:Mode::Literal,case_sensitive:true,whole_word:false,max_results:100}}
fn filter(field:&str,value:Value)->Result<Filter,serde_json::Error> {serde_json::from_value(json!({field:{"border_definition":value}}))}
#[test]
fn every_border_resource_property_matches_both_typed_axes_positive_and_negative()->TestResult {
    let raw=fixture::package(&fixture::p(1,"K"))?;let original=raw.clone();let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;
    assert_eq!(fixture::predicates().len(),30);
    for field in["character_details","paragraph_details"] {for(yes,no)in fixture::predicates(){for(value,total)in[(yes,1),(no,0)] {
        let out=index.find_resolved_style(q("K"),Scope::Document,Policy::default(),filter(field,value)?)?;
        assert_eq!(out.search().result().matches().len(),total,"{field}");assert!(out.coverage().requested_axes_complete());
    }}}assert_eq!(raw,original);Ok(())
}
#[test]
fn character_and_paragraph_use_their_own_referenced_resource_not_matching_any_catalog_entry()->TestResult {
    // char0 references border1; char1 references border2; both paragraph properties reference border1.
    let raw=fixture::package(&fixture::p(1,"K").replace("charPrIDRef='0'","charPrIDRef='1'"))?;let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;
    assert_eq!(i.find_resolved_style(q("K"),Scope::Document,Policy::default(),filter("character_details",json!({"three_d":true}))?)?.search().result().matches().len(),0);
    assert_eq!(i.find_resolved_style(q("K"),Scope::Document,Policy::default(),filter("paragraph_details",json!({"three_d":true}))?)?.search().result().matches().len(),1);
    assert_eq!(i.find_resolved_style(q("K"),Scope::Document,Policy::default(),filter("character_details",json!({"fill_brush":{"kind":"absent"}}))?)?.search().result().matches().len(),1);Ok(())
}
#[test]
fn explicit_run_text_and_named_axes_remain_independent_with_shared_border_definitions()->TestResult {
    let raw=fixture::package(&fixture::p(1,"K").replace("charPrIDRef='0'","charPrIDRef='1'").replace("<hp:t>","<hp:t charStyleIDRef='0'>"))?;
    let f=forms(&raw)?;let text=f.body_structure().source_text_index(&raw,Default::default())?;let inspection=text.inspection()?;let defs=inspection.resolve_style_definitions()?;
    for(axis,total)in[("run_property",0),("text_style",1),("named_style",1)] {
        let query:Explicit=serde_json::from_value(json!({"character_source":axis,"character_details":{"border_definition":{"three_d":true}}}))?;
        assert_eq!(defs.find(q("K"),SourceSearchScope::MappedDocument,query)?.matches().matches().len(),total);
    }Ok(())
}
#[test]
fn border_definitions_do_not_resolve_missing_direct_axes_or_uninterpreted_text_styles()->TestResult {
    for body in[fixture::p(1,"K").replace("charPrIDRef='0'",""),fixture::p(1,"K").replace("<hp:t>","<hp:t charStyleIDRef='0'>")] {
        let raw=fixture::package(&body)?;let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;
        assert!(matches!(i.find_resolved_style(q("ABSENT"),Scope::Document,Policy::default(),filter("character_details",json!({"three_d":true}))?),Err(RE::Unresolved(_))));
    }Ok(())
}
#[test]
fn nested_predicates_are_conjunctive_and_all_normalization_contributors_must_match()->TestResult {
    for(style,total)in[(0,1),(1,0)] {
        let body=format!("<hp:p id='1' paraPrIDRef='0'><hp:run charPrIDRef='0'><hp:t>ᄀ</hp:t></hp:run><hp:run charPrIDRef='{style}'><hp:t>ᅡᆨ</hp:t></hp:run></hp:p>");
        let raw=fixture::package(&body)?;let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;
        assert_eq!(i.find_resolved_style(q("각"),Scope::Document,Policy::default(),filter("character_details",json!({"three_d":true,"left":{"line_type":"dash","rgb":[1,2,3]}}))?)?.search().result().matches().len(),total);
        assert_eq!(i.find_resolved_style(q("각"),Scope::Document,Policy::default(),filter("character_details",json!({"three_d":true,"left":{"rgb":[3,2,1]}}))?)?.search().result().matches().len(),0);
    }Ok(())
}
#[test]
fn empty_unknown_bad_enums_and_out_of_range_nested_predicates_reject()->TestResult {
    for value in[json!({}),json!({"left":{}}),json!({"slash":{}}),json!({"fill_brush":{"kind":"window","filter":{}}})] {
        assert!(filter("character_details",value)?.validate().is_err());
    }
    for value in[json!({"unknown":true}),json!({"left":{"width":"0.3 mm"}}),json!({"left":{"rgb":[256,0,0]}}),
        json!({"fill_brush":{"kind":"window","filter":{"alpha":256}}}),json!({"fill_brush":{"kind":"absent","filter":{"alpha":0}}}),
        json!({"fill_brush":{"kind":"gradient"}}),json!({"fill_brush":{"kind":"window","filter":{"hatch_color":{"kind":"absent","color":{"kind":"none"}}}}})] {
        assert!(filter("character_details",value).is_err());
    }Ok(())
}
#[test]
fn old_detail_serialization_stays_exact_and_equal_hits_keep_distinct_predicate_identity()->TestResult {
    for field in["character_details","paragraph_details"] {
        let old=if field=="character_details"{json!({"emboss":false})}else{json!({"condense":0})};
        let parsed:Value=serde_json::to_value(serde_json::from_value::<Filter>(json!({field:old}))?)?;
        assert!(parsed[field].get("border_definition").is_none());
    }
    let raw=fixture::package(&fixture::p(1,"K"))?;let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;
    let a=i.find_resolved_style(q("K"),Scope::Document,Policy::default(),filter("character_details",json!({"three_d":true}))?)?;
    let b=i.find_resolved_style(q("K"),Scope::Document,Policy::default(),filter("character_details",json!({"shadow":false}))?)?;
    assert_eq!(a.search().result().matches(),b.search().result().matches());assert_ne!(a.search().request_sha256(),b.search().request_sha256());Ok(())
}
#[test]
fn absent_border_brush_and_hatch_attributes_never_become_present_none_values()->TestResult {
    let header=fixture::header()?;
    // Both attributes occur exactly once in the new brush; a present `none` color was tested above.
    assert_eq!(header.matches(" hatchColor=\"none\"").count(),1);assert_eq!(header.matches(" hatchStyle=\"CROSS_DIAGONAL\"").count(),1);
    let absent=header.replace(" hatchColor=\"none\"","").replace(" hatchStyle=\"CROSS_DIAGONAL\"","");
    let raw=fixture::definition::package_with_header(&fixture::p(1,"K"),&absent)?;let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;
    for(value,total)in[(json!({"hatch_color":{"kind":"absent"},"hatch_style":{"kind":"absent"}}),1),
        (json!({"hatch_color":{"kind":"present","color":{"kind":"none"}}}),0)] {
        assert_eq!(i.find_resolved_style(q("K"),Scope::Document,Policy::default(),filter("character_details",json!({"fill_brush":{"kind":"window","filter":value}}))?)?.search().result().matches().len(),total);
    }
    let needle="symMark=\"NONE\" borderFillIDRef=\"1\"";assert_eq!(absent.matches(needle).count(),1);
    let absent=absent.replace(needle,"symMark=\"NONE\"");let raw=fixture::definition::package_with_header(&fixture::p(1,"K"),&absent)?;
    let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;
    assert_eq!(i.find_resolved_style(q("K"),Scope::Document,Policy::default(),filter("character_details",json!({"fill_brush":{"kind":"absent"}}))?)?.search().result().matches().len(),0);Ok(())
}
