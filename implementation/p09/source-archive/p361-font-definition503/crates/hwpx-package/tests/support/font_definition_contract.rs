//! Intended product-path contracts. NOT_RUN until font_details is integrated after external003.
//! This support file is not an auto-discovered test target and changes no current runtime input.
use hwpx_package::document_import::{ImportedSourcePackage,forms::ImportedDocumentForms,
    search::{SourceSearchQuery as Query,SourceSearchMode as Mode,SourceSearchError as E,
        selector::SourceIndexScopeSelector as Scope,scope::SourceSearchScope,
        reviews::{SourceReviewTextPolicy as Policy,selector::resolved_styles::SourceResolvedStyleSearchError as RE},
        inspection::definitions::{SourceDefinitionStyleFilter as Explicit,resolved::SourceResolvedStyleFilter as Filter,
            font_details::SourceFontDetailsFilter}}};
use domain_ir::DocumentId;
use sha2::{Digest as _,Sha256};
use serde_json::{json,Value};
#[path="font_definition_fixture.rs"] mod fixture;
type TestResult=Result<(),Box<dyn std::error::Error>>;
fn forms(raw:&[u8])->Result<ImportedDocumentForms,Box<dyn std::error::Error>> {Ok(ImportedDocumentForms::import(ImportedSourcePackage::import(raw,DocumentId::parse("font-definition")?,Sha256::digest(raw).into(),Default::default())?)?)}
fn q(text:&str)->Query<'_> {Query {query:text,mode:Mode::Literal,case_sensitive:true,whole_word:false,max_results:100}}
fn filter(value:Value)->Result<Filter,serde_json::Error> {serde_json::from_value(json!({"font_details":value}))}
fn name(query:&str,regex:bool,case_sensitive:bool,whole_word:bool)->Value {json!({"query":query,"regex":regex,"case_sensitive":case_sensitive,"whole_word":whole_word})}
#[test]
fn font_definition_all19_properties_and_seven_language_axes_match_original_referenced_font()->TestResult {
    let raw=fixture::package(&fixture::p(1,"K",0))?;let before=raw.clone();let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;
    for(language,native)in[("hangul","Hangul"),("latin","Latin"),("hanja","Hanja"),("japanese","Japanese"),("other","Other"),("symbol","Symbol"),("user","User")] {
        let predicates=fixture::predicates(native);assert_eq!(predicates.len(),19);
        for(yes,no)in predicates {for(value,total)in[(yes,1),(no,0)] {
            let out=i.find_resolved_style(q("K"),Scope::Document,Policy::default(),filter(json!({language:value}))?)?;
            assert_eq!(out.search().result().matches().len(),total,"{language}");assert!(out.coverage().requested_axes_complete());
        }}
    }assert_eq!(raw,before);Ok(())
}
#[test]
fn font_languages_are_conjunctive_and_same_numeric_id_never_crosses_groups()->TestResult {
    let raw=fixture::package(&fixture::p(1,"K",0))?;let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;
    for(value,total)in[(json!({"hangul":{"face":name("P09.Hangul.Font",false,true,false)},"latin":{"face":name("P09.Latin.Font",false,true,false)}}),1),
        (json!({"hangul":{"face":name("P09.Hangul.Font",false,true,false)},"latin":{"face":name("P09.Hangul.Font",false,true,false)}}),0)] {
        assert_eq!(i.find_resolved_style(q("K"),Scope::Document,Policy::default(),filter(value)?)?.search().result().matches().len(),total);
    }Ok(())
}
#[test]
fn font_declared_run_text_and_named_axes_are_not_effective_font_fallback()->TestResult {
    let raw=fixture::package(&fixture::p(1,"K",1).replace("<hp:t>","<hp:t charStyleIDRef='0'>"))?;let f=forms(&raw)?;
    let text=f.body_structure().source_text_index(&raw,Default::default())?;let inspection=text.inspection()?;let defs=inspection.resolve_style_definitions()?;
    for(axis,total)in[("run_property",0),("text_style",1),("named_style",1)] {
        let query:Explicit=serde_json::from_value(json!({"character_source":axis,"font_details":{"hangul":{"face":name("P09.Hangul.Font",false,true,false)}}}))?;
        assert_eq!(defs.find(q("K"),SourceSearchScope::MappedDocument,query)?.matches().matches().len(),total);
    }
    let i=f.source_review_scope_index(&raw,Default::default())?;
    assert!(matches!(i.find_resolved_style(q("ABSENT"),Scope::Document,Policy::default(),filter(json!({"hangul":{"is_embedded":true}}))?),Err(RE::Unresolved(_))));Ok(())
}
#[test]
fn font_names_use_literal_regex_unicode_case_and_word_policy_without_rewriting_source_names()->TestResult {
    let raw=fixture::package(&fixture::p(1,"K",0))?;let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;
    for(query,total)in[(name("P09.*Font",false,true,false),0),(name("P09.*Font",true,true,false),1),
        (name("p09.hangul.font",false,false,false),1),(name("p09.hangul.font",false,true,false),0),
        (name("Hangul",false,true,true),1),(name("angu",false,true,true),0)] {
        assert_eq!(i.find_resolved_style(q("K"),Scope::Document,Policy::default(),filter(json!({"hangul":{"face":query}}))?)?.search().result().matches().len(),total);
    }Ok(())
}
#[test]
fn font_absent_optional_declarations_are_not_empty_or_zero_defaults()->TestResult {
    for(style,total)in[(0,0),(1,1)] {
        let raw=fixture::package(&fixture::p(1,"K",style))?;let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;
        let value=json!({"hangul":{"is_embedded":false,"binary_item_id_ref":{"kind":"absent"},"substitute":{"kind":"absent"},"type_info":{"kind":"absent"}}});
        assert_eq!(i.find_resolved_style(q("K"),Scope::Document,Policy::default(),filter(value)?)?.search().result().matches().len(),total);
    }Ok(())
}
#[test]
fn font_empty_unknown_enum_overflow_and_zero_width_patterns_are_closed_before_reads()->TestResult {
    for value in[json!({}),json!({"hangul":{}}),json!({"hangul":{"substitute":{"kind":"present","filter":{}}}}),
        json!({"hangul":{"type_info":{"kind":"present","filter":{}}}}),json!({"hangul":{"face":name("[",true,true,false)}}),
        json!({"hangul":{"face":name(".*",true,true,false)}}),json!({"hangul":{"face":name("",false,true,false)}}),
        json!({"hangul":{"binary_item_id_ref":{"kind":"present","value":""}}})] {
        assert!(serde_json::from_value::<SourceFontDetailsFilter>(value)?.validate().is_err());
    }
    for value in[json!({"invalid":{"is_embedded":true}}),json!({"hangul":{"font_type":"TTF"}}),
        json!({"hangul":{"substitute":{"kind":"absent","filter":{"font_type":"true_type"}}}}),
        json!({"hangul":{"type_info":{"kind":"present","filter":{"weight":2147483648_i64}}}}),
        json!({"hangul":{"face":{"query":"P09"}}})] {assert!(serde_json::from_value::<SourceFontDetailsFilter>(value).is_err());}
    let raw=fixture::package(&fixture::p(1,"K",0))?;let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;
    assert!(matches!(i.find_resolved_style(q("ABSENT"),Scope::Document,Policy::default(),filter(json!({"hangul":{"face":name(r"\b",true,true,false)}}))?),Err(RE::Search(E::Filter))));Ok(())
}
#[test]
fn font_original_id_and_declared_font_predicates_are_both_required()->TestResult {
    let raw=fixture::package(&fixture::p(1,"K",0))?;let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;
    for(id,total)in[(0,1),(1,0)] {
        let filter:Filter=serde_json::from_value(json!({"character_details":{"font_refs":{"hangul":id}},"font_details":{"hangul":{"is_embedded":true}}}))?;
        assert_eq!(i.find_resolved_style(q("K"),Scope::Document,Policy::default(),filter)?.search().result().matches().len(),total);
    }Ok(())
}
#[test]
fn font_name_and_binary_query_texts_are_redacted_in_debug_and_result_but_bound_to_identity()->TestResult {
    let raw=fixture::package(&fixture::p(1,"K",0))?;let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;
    let a=filter(json!({"hangul":{"face":name("P09.Hangul.Font",false,true,false)}}))?;
    let debug=format!("{a:?}");assert!(!debug.contains("P09.Hangul.Font"));
    let one=i.find_resolved_style(q("K"),Scope::Document,Policy::default(),a)?;
    let two=i.find_resolved_style(q("K"),Scope::Document,Policy::default(),filter(json!({"hangul":{"is_embedded":true}}))?)?;
    assert_eq!(one.search().result().matches(),two.search().result().matches());assert_ne!(one.search().request_sha256(),two.search().request_sha256());
    let bytes=String::from_utf8(one.canonical_json()?)?;assert!(!bytes.contains("P09.Hangul.Font"));assert!(!bytes.contains("declared-font-Hangul"));Ok(())
}
