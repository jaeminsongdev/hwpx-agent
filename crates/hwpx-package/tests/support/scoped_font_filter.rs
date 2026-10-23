//! Real in-memory original packages; style selection is independent of the font-name matcher.
use super::*;
use hwpx_package::document_import::search::{SourceSearchError,inspection::{SourceDeclaredStyleFilter as Declared,
    definitions::{SourceDefinitionStyleFilter as Definition,CharacterDefinitionSource as Character}},
    reviews::selector::styles::SourceReviewStyleFilter as Filter,replacement::atoms::styles::fonts::filtered::{
        SourceFontFilteredReplacementCandidate as Filtered,FILTERED_FONT_REPLACEMENT_PROFILE}};

fn run(id:u32)->Filter{Filter::Declared(Declared{run_character_property:Some(id),..Default::default()})}
fn apply(raw:&[u8],axis:Axis,filter:Filter,name_id:u32)->Result<Filtered,Box<dyn Error>>{
    let forms=original::forms(raw,"scoped-font")?;
    Ok(forms.lower_scoped_font_filtered_candidate(raw,query(&style_name(raw,name_id)?),Scope::Document,policy(),axis,filter,Default::default(),Default::default())?)
}
fn output(out:&Filtered)->Result<Vec<u8>,Box<dyn Error>>{Ok(out.with_verified_bytes(<[u8]>::to_vec)?)}
fn two()->Result<Vec<u8>,Box<dyn Error>>{package("<hp:p id='1' paraPrIDRef='0' styleIDRef='0'><hp:run charPrIDRef='0'><hp:t>A</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t>B</hp:t></hp:run></hp:p>")}

#[test]
fn declared_run_filter_changes_only_original_matching_reference()->R{
    let raw=two()?;let out=apply(&raw,Axis::RunProperty,run(0),0)?;let values=scalar_styles(&output(&out)?)?;
    assert_ne!(values[0].1,Some(0));assert_eq!(values[1].1,Some(1));
    assert_eq!(out.receipt().style_filter.selected_normalized_units,1);assert_eq!(out.receipt().style_filter.filtered_normalized_units,1);
    assert_eq!(out.receipt().source.changed_source_scalars,1);assert!(out.receipt().style_filter.definitions.is_none());Ok(())
}
#[test]
fn definition_filter_resolves_original_bold_once_not_an_inferred_axis()->R{
    let raw=two()?;let filter=Filter::Definition(Definition{character_source:Some(Character::RunProperty),bold:Some(true),..Default::default()});
    let out=apply(&raw,Axis::RunProperty,filter.clone(),1)?;let values=scalar_styles(&output(&out)?)?;
    assert_eq!(values[0].1,Some(0));assert_ne!(values[1].1,Some(1));assert!(out.receipt().style_filter.definitions.is_some());
    assert_eq!(out.receipt().style_filter.filter,filter);Ok(())
}
#[test]
fn declared_paragraph_property_chooses_shared_font_users_without_changing_other_paragraph()->R{
    let raw=package("<hp:p id='1' paraPrIDRef='0'><hp:run charPrIDRef='0'><hp:t>A</hp:t></hp:run></hp:p><hp:p id='2' paraPrIDRef='1'><hp:run charPrIDRef='0'><hp:t>B</hp:t></hp:run></hp:p>")?;
    let out=apply(&raw,Axis::RunProperty,Filter::Declared(Declared{paragraph_property:Some(1),..Default::default()}),0)?;
    let values=scalar_styles(&output(&out)?)?;assert_eq!(values[0].1,Some(0));assert_ne!(values[1].1,Some(0));Ok(())
}
#[test]
fn declared_named_style_is_not_substituted_for_absent_paragraph_property()->R{
    let raw=package("<hp:p id='1' styleIDRef='0'><hp:run charPrIDRef='0'><hp:t>A</hp:t></hp:run></hp:p>")?;
    assert!(apply(&raw,Axis::RunProperty,Filter::Declared(Declared{paragraph_property:Some(0),..Default::default()}),0).is_err());
    let out=apply(&raw,Axis::RunProperty,Filter::Declared(Declared{paragraph_style:Some(0),..Default::default()}),0)?;
    assert_eq!(out.receipt().source.changed_source_scalars,1);Ok(())
}
#[test]
fn explicit_text_axis_uses_original_text_filter_and_preserves_run()->R{
    let raw=package("<hp:p id='1'><hp:run charPrIDRef='0'><hp:t charStyleIDRef='0'>A</hp:t><hp:t charStyleIDRef='1'>B</hp:t></hp:run></hp:p>")?;
    let filter=Filter::Declared(Declared{text_character_style:Some(1),..Default::default()});let out=apply(&raw,Axis::TextStyle,filter,1)?;
    let values=scalar_styles(&output(&out)?)?;assert_eq!(values[0],('A',Some(0),Some(0)));assert_eq!(values[1].1,Some(0));assert_ne!(values[1].2,Some(1));Ok(())
}
#[test]
fn filter_axes_are_conjunctive_not_alternative()->R{
    let raw=two()?;let filter=Filter::Declared(Declared{run_character_property:Some(0),paragraph_property:Some(1),..Default::default()});
    let forms=original::forms(&raw,"scoped-font")?;let name=style_name(&raw,0)?;
    assert!(matches!(forms.lower_scoped_font_filtered_candidate(&raw,query(&name),Scope::Document,policy(),Axis::RunProperty,filter,Default::default(),Default::default()),Err(E::Compile(Compile::NoMatches))));Ok(())
}
#[test]
fn empty_filter_rejected_before_fresh_source_reconstruction()->R{
    let raw=plain("A")?;let forms=original::forms(&raw,"scoped-font")?;
    assert!(matches!(forms.lower_scoped_font_filtered_candidate(b"not a package",query("font"),Scope::Document,policy(),Axis::RunProperty,
        Filter::Declared(Declared::default()),Default::default(),Default::default()),Err(E::Search(SourceSearchError::Filter))));Ok(())
}
#[test]
fn definition_without_explicit_axis_rejected_before_source()->R{
    let raw=plain("A")?;let forms=original::forms(&raw,"scoped-font")?;
    assert!(matches!(forms.lower_scoped_font_filtered_candidate(b"not a package",query("font"),Scope::Document,policy(),Axis::RunProperty,
        Filter::Definition(Definition{bold:Some(true),..Default::default()}),Default::default(),Default::default()),Err(E::Search(SourceSearchError::Filter))));Ok(())
}
#[test]
fn nfc_composed_unit_rejects_partial_filter_match_and_preserves_both_origins()->R{
    let raw=package("<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>Ae</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t>&#x301;</hp:t></hp:run></hp:p>")?;
    let out=apply(&raw,Axis::RunProperty,run(0),0)?;let values=scalar_styles(&output(&out)?)?;
    assert_ne!(values[0].1,Some(0));assert_eq!(values[1],('e',Some(0),None));assert_eq!(values[2],('\u{301}',Some(1),None));
    assert_eq!(out.receipt().source.changed_source_scalars,1);assert_eq!(out.receipt().style_filter.filtered_normalized_units,1);Ok(())
}
#[test]
fn nfc_composed_unit_with_same_style_changes_both_original_scalars()->R{
    let raw=plain("e&#x301;")?;let out=apply(&raw,Axis::RunProperty,run(0),0)?;let values=scalar_styles(&output(&out)?)?;
    assert_eq!(values.iter().map(|v|v.0).collect::<String>(),"e\u{301}");assert_eq!(values[0].1,values[1].1);assert_ne!(values[0].1,Some(0));
    assert_eq!(out.receipt().source.changed_source_scalars,2);assert_eq!(out.receipt().style_filter.selected_normalized_units,1);Ok(())
}
#[test]
fn shared_normalized_origin_cannot_be_both_accepted_and_rejected()->R{
    // U+0344 decomposes to two marks. In NFC, one composes with preceding 'a'.
    let raw=package("<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>a</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t>&#x344;</hp:t></hp:run></hp:p>")?;
    let forms=original::forms(&raw,"scoped-font")?;let name=style_name(&raw,1)?;
    assert!(matches!(forms.lower_scoped_font_filtered_candidate(&raw,query(&name),Scope::Document,policy(),Axis::RunProperty,run(1),Default::default(),Default::default()),Err(E::Compile(Compile::Selection))));Ok(())
}
#[test]
fn filter_metadata_binds_even_when_output_and_original_receipt_are_identical()->R{
    let raw=plain("AB")?;let a=apply(&raw,Axis::RunProperty,run(0),0)?;
    let b=apply(&raw,Axis::RunProperty,Filter::Declared(Declared{paragraph_property:Some(0),..Default::default()}),0)?;
    assert_eq!(a.receipt().source,b.receipt().source);assert_eq!(output(&a)?,output(&b)?);assert_ne!(a.receipt().request_sha256,b.receipt().request_sha256);
    assert_eq!(a.receipt().profile,FILTERED_FONT_REPLACEMENT_PROFILE);assert!(!a.receipt().service_execution_or_native_qualified);
    assert!(!a.receipt().style_filter.effective_style_visibility_or_execution_authority);Ok(())
}
#[test]
fn old_v1_receipt_has_no_new_filter_fields_and_same_source_output()->R{
    let raw=plain("AB")?;let forms=original::forms(&raw,"scoped-font")?;let old=lower(&forms,&raw,Scope::Document,Axis::RunProperty)?;
    let new=apply(&raw,Axis::RunProperty,run(0),0)?;assert_eq!(old.receipt(),&new.receipt().source);
    assert_eq!(serde_json::to_value(old.receipt())?.get("style_filter"),None);assert_eq!(bytes(&old)?,output(&new)?);
    assert_eq!(old.edit_inventory(),new.edit_inventory());Ok(())
}
#[test]
fn selector_window_still_limits_matching_style_changes()->R{
    let raw=plain("ABC")?;let forms=original::forms(&raw,"scoped-font")?;let(hash,a,b)=selection(&forms,&raw,0,1,2)?;let name=style_name(&raw,0)?;
    let out=forms.lower_scoped_font_filtered_candidate(&raw,query(&name),Scope::Selection{index_sha256:hash,start:&a,end:&b},policy(),Axis::RunProperty,run(0),Default::default(),Default::default())?;
    let values=scalar_styles(&output(&out)?)?;assert_eq!(values[0].1,Some(0));assert_ne!(values[1].1,Some(0));assert_eq!(values[2].1,Some(0));
    assert_eq!(out.receipt().style_filter.selected_normalized_units,1);assert_eq!(out.receipt().style_filter.filtered_normalized_units,0);Ok(())
}
#[test]
fn source_scalar_budget_still_counts_composed_origins_not_one_nfc_character()->R{
    let raw=plain("e&#x301;")?;let forms=original::forms(&raw,"scoped-font")?;let name=style_name(&raw,0)?;
    let limits=SourceSearchLimits::default().restrict_match_limit(1)?;
    assert!(matches!(forms.lower_scoped_font_filtered_candidate(&raw,query(&name),Scope::Document,policy(),Axis::RunProperty,run(0),limits,Default::default()),Err(E::Compile(Compile::Limit))));Ok(())
}
#[test]
fn filtered_tracking_marker_still_rejects_selected_matching_payload()->R{
    let raw=package("<hp:p id='1' paraTcId='0'><hp:run charPrIDRef='0'><hp:t>A</hp:t></hp:run></hp:p>")?;
    let forms=original::forms(&raw,"scoped-font")?;let name=style_name(&raw,0)?;
    assert!(matches!(forms.lower_scoped_font_filtered_candidate(&raw,query(&name),Scope::Document,policy(),Axis::RunProperty,run(0),Default::default(),Default::default()),Err(E::Compile(Compile::Protection))));Ok(())
}
#[test]
fn fresh_source_mismatch_is_not_hidden_by_filter()->R{
    let raw=plain("A")?;let other=plain("B")?;let forms=original::forms(&raw,"scoped-font")?;let name=style_name(&raw,0)?;
    assert!(matches!(forms.lower_scoped_font_filtered_candidate(&other,query(&name),Scope::Document,policy(),Axis::RunProperty,run(0),Default::default(),Default::default()),Err(E::Source)));Ok(())
}
#[test]
fn unknown_filter_axis_and_duplicate_fields_are_not_silently_accepted()->R{
    assert!(serde_json::from_str::<Filter>(r#"{"kind":"declared","filter":{"run_character_property":0,"fallback":true}}"#).is_err());
    assert!(serde_json::from_str::<Filter>(r#"{"kind":"declared","filter":{"run_character_property":0,"run_character_property":1}}"#).is_err());
    assert!(serde_json::from_str::<Filter>(r#"{"kind":"effective","filter":{}}"#).is_err());Ok(())
}
