use hwpx_package::document_import::{ImportedSourcePackage,forms::ImportedDocumentForms,search::{SourceSearchQuery as Query,SourceSearchMode as Mode,
    selector::SourceIndexScopeSelector as Scope,scope::SourceSearchScope,reviews::{SourceReviewTextPolicy as Policy,selector::resolved_styles::SourceResolvedStyleSearchError as RE},
    inspection::definitions::{SourceDefinitionStyleFilter as Explicit,resolved::SourceResolvedStyleFilter as Filter,tab_details::SourceTabDefinitionFilter}}};
use hwpx_package::{TabDefinitionCatalogReader,TabDefinitionCatalogWriter,TabStop,TabItem,TabPositionUnit,TabStopAlignment,LineType2};
use domain_ir::DocumentId;
use sha2::{Digest as _,Sha256};
use serde_json::{json,Value};
#[path="tab_definition_fixture.rs"] mod fixture;
type TestResult=Result<(),Box<dyn std::error::Error>>;
fn forms(raw:&[u8])->Result<ImportedDocumentForms,Box<dyn std::error::Error>> {Ok(ImportedDocumentForms::import(ImportedSourcePackage::import(raw,DocumentId::parse("tab-definition")?,Sha256::digest(raw).into(),Default::default())?)?)}
fn q(query:&str)->Query<'_> {Query {query,mode:Mode::Literal,case_sensitive:true,whole_word:false,max_results:100}}
fn filter(value:Value)->Result<Filter,serde_json::Error> {serde_json::from_value(json!({"tab_details":value}))}
#[test]
fn all16_tab_conditions_match_the_referenced_definition_without_source_rewrites()->TestResult {
    let raw=fixture::package(&fixture::p(1,"K",0))?;let original=raw.clone();let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;
    assert_eq!(fixture::predicates().len(),16);
    for(yes,no)in fixture::predicates(){for(value,total)in[(yes,1),(no,0)] {
        let result=index.find_resolved_style(q("K"),Scope::Document,Policy::default(),filter(value)?)?;
        assert_eq!(result.search().result().matches().len(),total);assert!(result.coverage().requested_axes_complete());
    }}assert_eq!(raw,original);Ok(())
}
#[test]
fn tabs_follow_explicit_direct_and_named_paragraph_axes_never_any_matching_catalog_row()->TestResult {
    let raw=fixture::package(&fixture::p(1,"K",1))?;let f=forms(&raw)?;let text=f.body_structure().source_text_index(&raw,Default::default())?;
    let inspect=text.inspection()?;let defs=inspect.resolve_style_definitions()?;
    for(axis,count)in[("direct_property",0),("named_style",1)] {
        let filter:Explicit=serde_json::from_value(json!({"paragraph_source":axis,"tab_details":{"auto_tab_left":true}}))?;
        assert_eq!(defs.find(q("K"),SourceSearchScope::MappedDocument,filter)?.matches().matches().len(),count);
    }
    let index=f.source_review_scope_index(&raw,Default::default())?;
    assert_eq!(index.find_resolved_style(q("K"),Scope::Document,Policy::default(),filter(json!({"stop_count":0}))?)?.search().result().matches().len(),1);
    let raw=fixture::package(&fixture::p(1,"K",0).replace("paraPrIDRef='0'",""))?;let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;
    assert!(matches!(index.find_resolved_style(q("ABSENT"),Scope::Document,Policy::default(),filter(json!({"auto_tab_left":true}))?),Err(RE::Unresolved(_))));Ok(())
}
#[test]
fn indexed_stops_are_ordered_conjunctive_and_branches_never_choose_an_effective_fallback()->TestResult {
    let raw=fixture::package(&fixture::p(1,"K",0))?;let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;
    let a=fixture::direct(0,json!({"position":0}))["stops"][0].clone();
    let b=fixture::branch("current",json!({"position":100}))["stops"][0].clone();
    for (value,count) in[(json!({"auto_tab_left":true,"auto_tab_right":false,"stop_count":3,"stops":[a.clone(),b.clone()]}),1),
        (fixture::direct(1,json!({"position":201})),0),(fixture::branch("current",json!({"position":201})),0),
        (fixture::indexed(0,json!({"kind":"hwp_unit_char","fallback":{"position":0}})),0),
        (json!({"stops":[a,b],"auto_tab_right":true}),0),(fixture::direct(7,json!({"position":300})),0)] {
        assert_eq!(index.find_resolved_style(q("K"),Scope::Document,Policy::default(),filter(value)?)?.search().result().matches().len(),count);
    }Ok(())
}
#[test]
fn malformed_nested_conditions_and_wrong_axes_are_denied_without_default_coercion()->TestResult {
    for value in[json!({}),json!({"stops":[]}),json!({"stop_count":262145}),fixture::direct(0,json!({})),fixture::direct(0,json!({"position":-1})),
        fixture::direct(0,json!({"alignment":"justify"})),fixture::direct(0,json!({"leader":"unknown"})),
        fixture::direct(0,json!({"unit":{"kind":"absent","unit":"hwp_unit"}})),fixture::indexed(0,json!({"kind":"hwp_unit_char"})),
        fixture::indexed(0,json!({"kind":"hwp_unit_char","current":{}})),fixture::direct(262144,json!({"position":0})),
        json!({"stop_count":0,"stops":[{"index":0,"stop":{"kind":"direct","item":{"position":0}}}]}),
        json!({"stops":[{"index":1,"stop":{"kind":"direct","item":{"position":0}}},{"index":0,"stop":{"kind":"direct","item":{"position":0}}}]}),
        json!({"stops":[{"index":0,"stop":{"kind":"direct","item":{"position":0}}},{"index":0,"stop":{"kind":"direct","item":{"position":0}}}]})] {
        assert!(serde_json::from_value::<SourceTabDefinitionFilter>(value).map_or(true,|f|f.validate().is_err()));
    }
    for value in[json!({"tab_details":{"stop_count":0}}),json!({"character_source":"run_property","tab_details":{"stop_count":0}})] {
        assert!(serde_json::from_value::<Explicit>(value)?.validate().is_err());
    }
    let old:Filter=serde_json::from_value(json!({"bold":false}))?;assert!(!serde_json::to_string(&old)?.contains("tab_details"));Ok(())
}
#[test]
fn source_tab_corruption_is_a_definition_error_not_a_false_or_inferred_match()->TestResult {
    let header=fixture::header()?;let damaged=header.replacen("pos=\"0\"","pos=\"-1\"",1);assert_ne!(header,damaged);
    let raw=fixture::definition::package_with_header(&fixture::p(1,"K",0),&damaged)?;let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;
    // No new predicate keeps the existing reader contract; requested tab semantics fail closed.
    assert_eq!(index.find_resolved_style(q("K"),Scope::Document,Policy::default(),serde_json::from_value(json!({"bold":false}))?)?.search().result().matches().len(),1);
    assert!(index.find_resolved_style(q("ABSENT"),Scope::Document,Policy::default(),filter(json!({"auto_tab_left":true}))?).is_err());Ok(())
}
#[test]
fn explicit_character_unit_is_not_an_absent_default_hwp_unit()->TestResult {
    let mut catalog=TabDefinitionCatalogReader::read(fixture::header()?.as_bytes(),Default::default())?;
    catalog.definitions[0].stops=vec![TabStop::Direct(TabItem {position:0,alignment:TabStopAlignment::Left,leader:LineType2::None,unit:Some(TabPositionUnit::Character)})];
    // The original tab writer independently checks this declaration, then the source fixture patches only its tab block.
    let lowered=String::from_utf8(TabDefinitionCatalogWriter::lower(&catalog,Default::default())?)?;
    let header=fixture::header()?;let start=header.find("<hh:tabProperties").ok_or("start")?;let end=header.find("</hh:tabProperties>").ok_or("end")?+"</hh:tabProperties>".len();
    let a=lowered.find("<hh:tabProperties").ok_or("start")?;let b=lowered.find("</hh:tabProperties>").ok_or("end")?+"</hh:tabProperties>".len();
    let mut changed=header;changed.replace_range(start..end,&lowered[a..b]);let raw=fixture::definition::package_with_header(&fixture::p(1,"K",0),&changed)?;
    let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;
    for(unit,count)in[(json!({"kind":"present","unit":"character"}),1),(json!({"kind":"present","unit":"hwp_unit"}),0),(json!({"kind":"absent"}),0)] {
        assert_eq!(index.find_resolved_style(q("K"),Scope::Document,Policy::default(),filter(fixture::direct(0,json!({"unit":unit})))?)?.search().result().matches().len(),count);
    }Ok(())
}
#[test]
fn combined_font_privacy_projection_keeps_tab_conditions_and_distinct_request_identity()->TestResult {
    let header=fixture::header()?;let font_name=fixture::font_name()?;let raw=fixture::definition::package_with_header(&fixture::p(1,"K",0),&header)?;
    let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;
    let value=json!({"font_details":{"hangul":{"face":{"query":font_name,"regex":false,"case_sensitive":true,"whole_word":false}}},"tab_details":{"auto_tab_left":true}});
    let out=index.find_resolved_style(q("K"),Scope::Document,Policy::default(),serde_json::from_value(value.clone())?)?;
    let serialized=serde_json::to_value(&out)?;assert_eq!(out.search().result().matches().len(),1);
    let text=serde_json::to_string(&serialized)?;assert!(!text.contains(&font_name));assert!(text.contains("tab_details"));
    let mut other=value;other["tab_details"]=json!({"stop_count":3});
    let second=index.find_resolved_style(q("K"),Scope::Document,Policy::default(),serde_json::from_value(other)?)?;
    assert_ne!(out.search().request_sha256(),second.search().request_sha256());Ok(())
}
#[test]
fn tab_filtered_real_case_candidate_reimports_only_matching_paragraph_and_retains_original()->TestResult {
    use hwpx_package::document_import::search::{reviews::selector::styles::SourceReviewStyleFilter as ReviewFilter,
        replacement::atoms::case::{SourceCaseMode,SourceCasePolicy}};
    let raw=fixture::package(&(fixture::p(1,"K",0)+&fixture::p(2,"K",1)))?;let original=raw.clone();let f=forms(&raw)?;
    let filter:ReviewFilter=serde_json::from_value(json!({"kind":"definition","filter":{"paragraph_source":"direct_property","tab_details":{"auto_tab_left":true}}}))?;
    let candidate=f.lower_review_selector_case_candidate(&raw,q("K"),Scope::Document,Policy::default(),Some(filter),SourceCaseMode::Lowercase,
        SourceCasePolicy::UnicodeDefaultEachMatchedTextGroup,Default::default(),Default::default())?;
    assert!(serde_json::to_string(candidate.receipt())?.contains("tab_details"));let after=candidate.with_verified_bytes(<[u8]>::to_vec)?;
    let parsed=forms(&after)?;let index=parsed.source_review_scope_index(&after,Default::default())?;
    assert_eq!(index.find_resolved_style(q("k"),Scope::Document,Policy::default(),filter_from(json!({"auto_tab_left":true}))?)?.search().result().matches().len(),1);
    assert_eq!(index.find_resolved_style(q("K"),Scope::Document,Policy::default(),filter_from(json!({"auto_tab_left":false}))?)?.search().result().matches().len(),1);
    assert_eq!(raw,original);assert_ne!(after,original);Ok(())
}
fn filter_from(value:Value)->Result<Filter,serde_json::Error> {filter(value)}
