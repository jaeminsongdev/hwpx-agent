use hwpx_package::{CompatibleHeading,Heading,HeadingType,document_import::{ImportedSourcePackage,forms::ImportedDocumentForms,
    search::{SourceSearchQuery as Query,SourceSearchMode as Mode,SourceSearchError as E,selector::SourceIndexScopeSelector as Scope,
        reviews::{SourceReviewTextPolicy as Policy,selector::resolved_styles::SourceResolvedStyleSearchError as RE},
        inspection::definitions::{SourceDefinitionStyleFilter as Explicit,ParagraphDefinitionSource as Axis,
            paragraph_details::SourceParagraphDetailFilter as Details,resolved::SourceResolvedStyleFilter as Filter}}}};
use domain_ir::DocumentId;
use sha2::{Digest as _,Sha256};
use serde_json::{json,Value};
#[allow(dead_code)] #[path="support/paragraph_detail_fixture.rs"] mod fixture;
type TestResult=Result<(),Box<dyn std::error::Error>>;
fn forms(raw:&[u8])->Result<ImportedDocumentForms,Box<dyn std::error::Error>> {Ok(ImportedDocumentForms::import(ImportedSourcePackage::import(raw,DocumentId::parse("paragraph-detail")?,Sha256::digest(raw).into(),Default::default())?)?)}
fn q(text:&str)->Query<'_> {Query {query:text,mode:Mode::Literal,case_sensitive:true,whole_word:false,max_results:100}}
fn filter(details:Value)->Result<Filter,serde_json::Error> {serde_json::from_value(json!({"paragraph_details":details}))}
#[test]
fn paragraph_detail_all27_conditions_match_actual_typed_source_positive_and_negative()->TestResult {
    let raw=fixture::package(&fixture::p(1,"K"))?;let before=raw.clone();let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;
    assert_eq!(fixture::predicates().len(),27);
    for(yes,no)in fixture::predicates(){for(value,count)in[(yes,1),(no,0)] {
        let result=i.find_resolved_style(q("K"),Scope::Document,Policy::default(),filter(value)?)?;
        assert_eq!(result.search().result().matches().len(),count);assert!(result.coverage().requested_axes_complete());
    }}assert_eq!(raw,before);Ok(())
}
#[test]
fn paragraph_detail_layout_branches_units_all_margins_and_spacing_are_independent()->TestResult {
    let raw=fixture::package(&fixture::p(1,"K"))?;let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;
    for(branch,values)in[("current_layout",[-720,120,34,56,78]),("fallback_layout",[-1440,1500,68,112,156])] {
        for((name,value),position)in["indent","left","right","previous","next"].into_iter().zip(values).zip(0..) {
            let unit=if branch=="current_layout"&&position==0{"character"}else{"hwp_unit"};
            for(value,count)in[(value,1),(value+1,0)] {
                let result=i.find_resolved_style(q("K"),Scope::Document,Policy::default(),filter(json!({branch:{name:{"value":value,"unit":unit}}}))?)?;
                assert_eq!(result.search().result().matches().len(),count);
            }
        }
        let(value,unit,kind)=if branch=="current_layout"{(1200,"character","fixed")}else{(1600,"hwp_unit","at_least")};
        for(value,count)in[(value,1),(value+1,0)] {
            assert_eq!(i.find_resolved_style(q("K"),Scope::Document,Policy::default(),filter(json!({branch:{"line_spacing":{"spacing_type":kind,"value":value,"unit":unit}}}))?)?.search().result().matches().len(),count);
        }
    }Ok(())
}
#[test]
fn paragraph_detail_heading_kind_and_both_branches_do_not_infer_a_native_winner()->TestResult {
    let raw=fixture::package(&fixture::p(1,"K"))?;let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;
    for(details,count)in[(json!({"heading":{"kind":"meta_tag","fallback":{"heading_type":"none","id_ref":0,"level":0}}}),1),
        (json!({"heading":{"kind":"meta_tag","current":{"heading_type":"outline","id_ref":0,"level":4},"fallback":{"heading_type":"outline","id_ref":0,"level":4}}}),0)] {
        assert_eq!(i.find_resolved_style(q("K"),Scope::Document,Policy::default(),filter(details)?)?.search().result().matches().len(),count);
    }
    let heading=CompatibleHeading::Direct(Heading {heading_type:HeadingType::Outline,id_ref:0,level:4});
    let raw=fixture::definition::package_with_header(&fixture::p(1,"K"),&fixture::header_with_heading(heading)?)?;let f=forms(&raw)?;
    assert_eq!(f.source_review_scope_index(&raw,Default::default())?.find_resolved_style(q("K"),Scope::Document,Policy::default(),filter(json!({"heading":{"kind":"direct","heading":{"heading_type":"outline","id_ref":0,"level":4}}}))?)?.search().result().matches().len(),1);Ok(())
}
#[test]
fn paragraph_detail_empty_branches_impossible_values_unknown_keys_and_overflows_reject()->TestResult {
    for value in[json!({}),json!({"current_layout":{}}),json!({"checked":true,"fallback_layout":{}}),json!({"condense":76}),
        json!({"non_latin_word":"hyphenation"}),json!({"heading":{"kind":"meta_tag"}}),
        json!({"heading":{"kind":"direct","heading":{"heading_type":"none","id_ref":1,"level":0}}}),
        json!({"heading":{"kind":"direct","heading":{"heading_type":"outline","id_ref":0,"level":10}}}),
        json!({"current_layout":{"line_spacing":{"spacing_type":"percent","value":501,"unit":"hwp_unit"}}})] {
        assert!(matches!(filter(value)?.validate(),Err(E::Filter)));
    }
    for value in[json!({"unknown":true}),json!({"condense":256}),json!({"border_offset_left":2147483648_i64}),
        json!({"text_direction":"auto"}),json!({"current_layout":{"indent":{"value":1}}}),json!({"fallback_layout":{"indent":{"value":1,"unit":"auto"}}}),
        json!({"heading":{"kind":"direct","heading":{"heading_type":"none","id_ref":0,"level":0},"fallback":{}}})] {assert!(filter(value).is_err());}
    Ok(())
}
#[test]
fn paragraph_detail_legacy_bytes_unchanged_and_same_hits_still_bind_distinct_conditions()->TestResult {
    for legacy in[r#"{"bold":true,"italic":null,"height_hwpunit":null,"text_rgb":null,"alignment":null}"#,
        r#"{"bold":null,"italic":null,"height_hwpunit":null,"text_rgb":null,"alignment":null,"character_details":{"shade_color":null,"use_font_space":null,"use_kerning":null,"emphasis":null,"border_fill":null,"underline_position":null,"underline_shape":null,"underline_color":null,"strikeout_shape":null,"strikeout_color":null,"outline":null,"shadow_type":null,"shadow_color":null,"shadow_offset_x":null,"shadow_offset_y":null,"emboss":true,"engrave":null,"superscript":null,"subscript":null,"font_refs":null,"ratios":null,"spacing":null,"relative_sizes":null,"offsets":null}}"#] {
        assert_eq!(serde_json::to_string(&serde_json::from_str::<Filter>(legacy)?)?,legacy);
    }
    let raw=fixture::package(&fixture::p(1,"K"))?;let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;
    let a=i.find_resolved_style(q("K"),Scope::Document,Policy::default(),filter(json!({"condense":17}))?)?;
    let b=i.find_resolved_style(q("K"),Scope::Document,Policy::default(),filter(json!({"checked":true}))?)?;
    assert_eq!(a.search().result().matches(),b.search().result().matches());assert_ne!(a.search().request_sha256(),b.search().request_sha256());Ok(())
}
#[test]
fn paragraph_detail_explicit_direct_and_named_axes_remain_distinct_and_required()->TestResult {
    let raw=fixture::package(&fixture::p(1,"K"))?;let f=forms(&raw)?;let i=f.body_structure().source_text_index(&raw,Default::default())?;let inspection=i.inspection()?;let d=inspection.resolve_style_definitions()?;
    let details:Details=serde_json::from_value(json!({"condense":17}))?;
    assert!(matches!(Explicit {paragraph_details:Some(details),..Default::default()}.validate(),Err(E::Filter)));
    for(axis,count)in[(Axis::DirectProperty,1),(Axis::NamedStyle,0)] {
        assert_eq!(d.find(q("K"),hwpx_package::document_import::search::scope::SourceSearchScope::MappedDocument,
            Explicit {paragraph_source:Some(axis),paragraph_details:Some(details),..Default::default()})?.matches().matches().len(),count);
    }Ok(())
}
#[test]
fn paragraph_detail_missing_required_paragraph_rejects_before_absent_query_but_character_axis_is_optional()->TestResult {
    let raw=fixture::package(&fixture::p(1,"K").replace("paraPrIDRef='1'",""))?;let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;
    assert!(matches!(i.find_resolved_style(q("ABSENT"),Scope::Document,Policy::default(),filter(json!({"condense":17}))?),Err(RE::Unresolved(_))));
    let raw=fixture::package(&fixture::p(1,"K").replace("charPrIDRef='1'","").replace("<hp:t>","<hp:t charStyleIDRef='0'>"))?;let f=forms(&raw)?;
    assert_eq!(f.source_review_scope_index(&raw,Default::default())?.find_resolved_style(q("K"),Scope::Document,Policy::default(),filter(json!({"condense":17}))?)?.search().result().matches().len(),1);Ok(())
}
#[test]
fn paragraph_detail_combines_existing_character_and_alignment_without_mutating_source()->TestResult {
    let raw=fixture::package(&fixture::p(1,"K"))?;let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;
    for(value,count)in[(json!({"bold":true,"alignment":"right","paragraph_details":{"condense":17,"border_connect":true}}),1),
        (json!({"bold":false,"paragraph_details":{"condense":17}}),0),(json!({"alignment":"left","paragraph_details":{"condense":17}}),0)] {
        assert_eq!(i.find_resolved_style(q("K"),Scope::Document,Policy::default(),serde_json::from_value(value)?)?.search().result().matches().len(),count);
    }Ok(())
}
