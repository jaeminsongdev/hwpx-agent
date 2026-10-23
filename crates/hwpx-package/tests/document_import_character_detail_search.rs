use hwpx_package::{document_import::{ImportedSourcePackage,forms::ImportedDocumentForms,
    search::{SourceSearchQuery as Query,SourceSearchMode as Mode,SourceSearchError as E,selector::SourceIndexScopeSelector as Scope,
        reviews::{SourceReviewTextPolicy as Policy,selector::resolved_styles::SourceResolvedStyleSearchError as RE},
        inspection::definitions::{SourceDefinitionStyleFilter as Explicit,CharacterDefinitionSource as Axis,
            details::SourceCharacterDetailFilter as Details,resolved::SourceResolvedStyleFilter as Filter}}}};
use domain_ir::DocumentId;
use sha2::{Digest as _,Sha256};
use serde_json::{json,Value};
#[allow(dead_code)] #[path="support/character_detail_fixture.rs"] mod fixture;
type TestResult=Result<(),Box<dyn std::error::Error>>;
fn forms(raw:&[u8])->Result<ImportedDocumentForms,Box<dyn std::error::Error>> {Ok(ImportedDocumentForms::import(ImportedSourcePackage::import(raw,DocumentId::parse("detail-search")?,Sha256::digest(raw).into(),Default::default())?)?)}
fn q(text:&str)->Query<'_> {Query {query:text,mode:Mode::Literal,case_sensitive:true,whole_word:false,max_results:100}}
fn filter(details:Value)->Result<Filter,serde_json::Error> {serde_json::from_value(json!({"character_details":details}))}

#[test]
fn detail_each_of_24_source_predicates_has_positive_and_negative_actual_search()->TestResult {
    let raw=fixture::package(&fixture::p(1,"K",1))?;let original=raw.clone();let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;
    assert_eq!(fixture::predicates().len(),24);
    for(positive,negative)in fixture::predicates() {
        for(value,expected)in[(positive,1),(negative,0)] {let found=index.find_resolved_style(q("K"),Scope::Document,Policy::default(),filter(value)?)?;
            assert_eq!(found.search().result().matches().len(),expected);assert!(found.coverage().requested_axes_complete());}
    }assert_eq!(raw,original);Ok(())
}
#[test]
fn detail_language_slots_are_separate_conjunctive_and_signed_zero_values_are_real()->TestResult {
    let raw=fixture::package(&fixture::p(1,"K",1))?;let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;
    for group in["font_refs","ratios","spacing","relative_sizes","offsets"] {
        for language in["hangul","latin","hanja","japanese","other","symbol","user"] {
            let value=match(group,language){("font_refs",_)=>0,("ratios","hangul")=>90,("relative_sizes","hangul")=>85,
                ("ratios"|"relative_sizes",_)=>100,("spacing","hangul")=>-4,("offsets","hangul")=>2,_=>0};
            for(v,n)in[(value,1),(value+1,0)] {let details=json!({group:{language:v}});let found=i.find_resolved_style(q("K"),Scope::Document,Policy::default(),filter(details)?)?;
                assert_eq!(found.search().result().matches().len(),n);}
        }
    }Ok(())
}
#[test]
fn detail_empty_nested_unknown_and_out_of_range_inputs_are_rejected()->TestResult {
    for value in[json!({}),json!({"font_refs":{}}),json!({"emboss":false,"spacing":{}}),json!({"ratios":{"hangul":null}})] {
        assert!(matches!(filter(value)?.validate(),Err(E::Filter)));
    }
    for value in[json!({"unknown":true}),json!({"underline_position":"bad"}),json!({"shadow_offset_x":32768}),json!({"spacing":{"latin":-32769}}),
        json!({"font_refs":{"other":-1}}),json!({"relative_sizes":{"user":65536}}),json!({"ratios":{"invalid":1}}),
        json!({"shade_color":{"kind":"none","rgb":[0,0,0]}}),json!({"shade_color":{"kind":"rgb","rgb":[256,0,0]}}),
        json!({"border_fill":{"kind":"absent","id":1}})] {assert!(filter(value).is_err());}
    Ok(())
}
#[test]
fn detail_legacy_filter_serialization_is_byte_exact_and_new_conditions_bind_hash()->TestResult {
    let legacy=r#"{"bold":true,"italic":null,"height_hwpunit":null,"text_rgb":null,"alignment":null}"#;
    let parsed:Filter=serde_json::from_str(legacy)?;assert_eq!(serde_json::to_string(&parsed)?,legacy);
    let explicit=r#"{"character_source":"run_property","bold":true,"italic":null,"height_hwpunit":null,"text_rgb":null,"paragraph_source":null,"alignment":null}"#;
    let parsed:Explicit=serde_json::from_str(explicit)?;assert_eq!(serde_json::to_string(&parsed)?,explicit);
    let raw=fixture::package(&fixture::p(1,"K",1))?;let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;
    let a=i.find_resolved_style(q("K"),Scope::Document,Policy::default(),filter(json!({"emboss":true}))?)?;
    let b=i.find_resolved_style(q("K"),Scope::Document,Policy::default(),filter(json!({"engrave":false}))?)?;
    assert_eq!(a.search().result().matches(),b.search().result().matches());assert_ne!(a.search().request_sha256(),b.search().request_sha256());Ok(())
}
#[test]
fn detail_explicit_axis_is_required_and_uses_the_original_definition_matcher()->TestResult {
    let raw=fixture::package(&fixture::p(1,"K",1))?;let f=forms(&raw)?;let i=f.body_structure().source_text_index(&raw,Default::default())?;let inspection=i.inspection()?;let definitions=inspection.resolve_style_definitions()?;
    let details:Details=serde_json::from_value(json!({"underline_position":"bottom"}))?;
    let bad=Explicit {character_details:Some(details),..Default::default()};assert!(matches!(bad.validate(),Err(E::Filter)));
    let good=Explicit {character_source:Some(Axis::RunProperty),..bad};let found=definitions.find(q("K"),hwpx_package::document_import::search::scope::SourceSearchScope::MappedDocument,good)?;
    assert_eq!(found.matches().matches().len(),1);Ok(())
}
#[test]
fn detail_unknown_direct_precedence_rejects_before_even_an_absent_query()->TestResult {
    for body in[fixture::p(1,"K",1).replace("charPrIDRef='1'",""),fixture::p(1,"K",1).replace("<hp:t>","<hp:t charStyleIDRef='0'>")] {
        let raw=fixture::package(&body)?;let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;
        assert!(matches!(i.find_resolved_style(q("ABSENT"),Scope::Document,Policy::default(),filter(json!({"emboss":true}))?),Err(RE::Unresolved(_))));
    }Ok(())
}
#[test]
fn detail_all_nfc_contributors_must_satisfy_the_predicate()->TestResult {
    for(style,count)in[(0,0),(1,1)] {let body=format!("<hp:p id='1' paraPrIDRef='1'><hp:run charPrIDRef='1'><hp:t>ᄀ</hp:t></hp:run><hp:run charPrIDRef='{style}'><hp:t>ᅡᆨ</hp:t></hp:run></hp:p>");
        let raw=fixture::package(&body)?;let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;
        assert_eq!(i.find_resolved_style(q("각"),Scope::Document,Policy::default(),filter(json!({"underline_position":"bottom"}))?)?.search().result().matches().len(),count);
    }Ok(())
}
