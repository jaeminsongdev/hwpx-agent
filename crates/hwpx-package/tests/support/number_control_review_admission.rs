use super::*;
use hwpx_package::document_import::{structure::review::ImportedDocumentReviewBodies,
    reference_targets::{caption_source_state::ImportedCaptionSourceState,numbering::{ImportedCaptionNumbering,CaptionNumberingImportError as ImportError,NativeNumberControlKind as NumberKind}},
    structure::caption_numbering_sequence::*};
fn observed_body(tag:&str)->String{
    review::body().replace("<hp:t>BODY K K</hp:t>",&format!("<hp:t>BODY K K</hp:t>{}",control("autoNum",2)))
        .replace("<hp:t>HIDDEN K K<hp:lineBreak/></hp:t>",&format!("<hp:t>HIDDEN K K<hp:lineBreak/></hp:t>{}",control(tag,3)))
        .replace("<hp:t>MEMO K K</hp:t>",&format!("<hp:t>MEMO K K</hp:t>{}",control(tag,4)))
}
fn observed(tag:&str)->Result<Vec<u8>,Box<dyn Error>>{fixture::package(&observed_body(tag))}
#[test]
fn review_number_import_keeps_legacy_wire_unchanged_and_binds_actual_review_inventory()->TestResult{
    let raw=plain()?;let f=forms(&raw)?;let review=ImportedDocumentReviewBodies::import(&f)?;
    let old=ImportedCaptionNumbering::import(f.body_structure(),limits()?)?;let bound=ImportedCaptionNumbering::import_review_bound(&f,&review,limits()?)?;
    assert_eq!(old.controls(),bound.controls());assert_eq!(old.section_starts(),bound.section_starts());
    let a=serde_json::to_value(old.receipt())?;let mut b=serde_json::to_value(bound.receipt())?;
    assert!(a.get("review_body_inventory_sha256").is_none());assert_eq!(bound.receipt().review_body_inventory_sha256,Some(review.receipt().body_observations_sha256));
    assert_ne!(old.receipt().profile,bound.receipt().profile);b["profile"]=a["profile"].clone();b.as_object_mut().ok_or("object")?.remove("review_body_inventory_sha256");assert_eq!(a,b);Ok(())
}
#[test]
fn review_number_import_rejects_other_model_even_with_identical_source_bytes()->TestResult{
    let raw=observed("autoNum")?;let f=forms(&raw)?;let other=forms(&raw)?;let review=ImportedDocumentReviewBodies::import(&f)?;
    assert!(matches!(ImportedCaptionNumbering::import_review_bound(&other,&review,limits()?),Err(ImportError::Binding)));
    assert!(matches!(ImportedCaptionSourceState::import_review_bound(&other,&review,limits()?),Err(ImportError::Binding)));
    let bound=ImportedCaptionSourceState::import_review_bound(&f,&review,limits()?)?;assert_eq!(bound.numbering().controls().len(),3);
    assert!(!bound.receipt().sequence_interpretation_and_recalculation_qualified&&!bound.receipt().execution_publication_authority);Ok(())
}
#[test]
fn review_number_source_all_policy_combinations_preserve_excluded_values_and_complete_order()->TestResult{
    let raw=observed("autoNum")?;let f=forms(&raw)?;
    for hidden in[false,true]{for memo in[false,true]{let policy=Body{include_hidden_explanations:hidden,include_memo_bodies:memo};let count=1+usize::from(hidden)+usize::from(memo);
        let c=f.lower_review_selector_number_control_candidate(&raw,Scope::Document,policy,Kind::AutoNumber,count,9,Format::Preserve,Default::default(),limits()?,Default::default())?;
        assert_eq!(c.receipt().selected_controls,count);assert_eq!(c.receipt().stream.number_sequence.requested_events,3);
        let mut expected=section(&raw)?.replace("autoNum num='2'","autoNum num='9'");if hidden{expected=expected.replace("autoNum num='3'","autoNum num='9'");}if memo{expected=expected.replace("autoNum num='4'","autoNum num='9'");}
        assert_eq!(section(&output(&raw,&c)?)?,expected);
    }}Ok(())
}
#[test]
fn review_number_source_restart_format_is_bound_without_touching_body_auto_or_metadata()->TestResult{
    let raw=observed("newNum")?;let f=forms(&raw)?;let c=replace(&f,&raw,Scope::Document,body(),Kind::NewNumber,7,
        Format::Replace{format:NumberFormat::LatinSmall,user_character:"",prefix:"<private&",suffix:"suffix",superscript:true})?;
    let out=section(&output(&raw,&c)?)?;assert_eq!(c.receipt().selected_controls,2);assert!(out.contains(&control("autoNum",2)));
    assert_eq!(out.matches("newNum num='7'").count(),2);assert_eq!(out.matches("type='LATIN_SMALL'").count(),2);
    assert!(out.contains("PRIVATE-AUTHOR")&&out.contains("CACHE FROZEN"));assert!(!serde_json::to_string(c.receipt())?.contains("private&"));Ok(())
}
#[test]
fn review_number_source_memo_cache_never_inherits_the_actual_payload_exception()->TestResult{
    let body_text=observed_body("newNum").replace("<hp:t>CACHE FROZEN</hp:t>",&format!("<hp:t>CACHE FROZEN</hp:t>{}",control("newNum",8)));
    let raw=fixture::package(&body_text)?;let f=forms(&raw)?;assert!(matches!(replace(&f,&raw,Scope::Document,body(),Kind::NewNumber,8,Format::Preserve),Err(C::Output(E::FieldContent))));Ok(())
}
#[test]
fn review_number_source_selected_locked_memo_noop_rejects_but_excluded_control_stays_exact()->TestResult{
    let body_text=observed_body("autoNum").replace(&control("autoNum",4),&control("autoNum",4).replace("<hp:autoNum ","<hp:autoNum lock='1' "));
    let raw=fixture::package(&body_text)?;let f=forms(&raw)?;
    assert!(matches!(replace(&f,&raw,Scope::Document,body(),Kind::AutoNumber,4,Format::Preserve),Err(C::Output(E::Protection))));
    let c=replace(&f,&raw,Scope::Document,Body{include_hidden_explanations:false,include_memo_bodies:false},Kind::AutoNumber,9,Format::Preserve)?;
    exact(&raw,&c,"autoNum num='2'","autoNum num='9'")?;Ok(())
}
#[test]
fn review_number_import_header_control_still_rejects_full_coverage_in_both_modes()->TestResult{
    let header=fixture::header()?.replace("</hh:head>",&format!("{}</hh:head>",p(55,&control("autoNum",8))));
    let raw=fixture::package_with_header(&p(1,&format!("<hp:t>A</hp:t>{}",control("autoNum",2))),&header)?;let f=forms(&raw)?;let review=ImportedDocumentReviewBodies::import(&f)?;
    assert!(matches!(ImportedCaptionNumbering::import(f.body_structure(),limits()?),Err(ImportError::Coverage)));
    assert!(matches!(ImportedCaptionNumbering::import_review_bound(&f,&review,limits()?),Err(ImportError::Coverage)));Ok(())
}
#[test]
fn review_number_import_additional_paragraphs_obey_finite_limits()->TestResult{
    let raw=observed("autoNum")?;let f=forms(&raw)?;let review=ImportedDocumentReviewBodies::import(&f)?;
    let tight=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig{items_per_kind:1,..Default::default()})?;
    assert!(matches!(ImportedCaptionNumbering::import_review_bound(&f,&review,tight),Err(ImportError::Limit)));
    assert!(ImportedCaptionNumbering::import_review_bound(&f,&review,limits()?).is_ok());Ok(())
}
#[test]
fn review_number_legacy_sequence_output_uses_original_body_branch_and_omits_review_wire_field()->TestResult{
    let raw=plain()?;let f=forms(&raw)?;let state=ImportedCaptionSourceState::import(f.body_structure(),limits()?)?;
    let events:Vec<_>=state.context().ordered_controls().iter().map(|o|{let c=state.numbering().controls().iter().find(|n|n.logical_control_id==o.logical_control_id).ok_or("control")?;
        let values=match c.kind{NumberKind::AutoNumber=>NativeNumberEventValues::AutoNumber{category:c.category,stored_number:9,format:Format::Preserve},
            NumberKind::Restart=>NativeNumberEventValues::Restart{category:c.category,stored_number:c.stored_number,format:Format::Preserve}};
        Ok::<_,Box<dyn Error>>(NativeNumberEventReplacement{source_control_id:&c.logical_control_id,source_fingerprint_sha256:c.source_fingerprint_sha256,values})}).collect::<Result<_,_>>()?;
    let begin=state.context().document_start().map(|c|NativeDocumentStartReplacement{source_control_id:&c.logical_control_id,source_fingerprint_sha256:c.source_fingerprint_sha256,
        values:NativeDocumentStartValues{page:c.page,footnote:c.footnote,endnote:c.endnote,picture:c.picture,table:c.table,equation:c.equation}});
    let request=NativeNumberSequenceReplacement{expected_joined_state_sha256:state.receipt().joined_state_sha256,document_start:begin,events:&events};
    let c=state.lower_sequence_batch_candidate(&raw,&[],&[],&[],&request,limits()?,Default::default())?;
    assert!(c.receipt().content.output.output_review_import.is_none());assert!(serde_json::to_value(&c.receipt().content.output)?.get("output_review_import").is_none());
    let out=c.with_verified_bytes(<[u8]>::to_vec)?;assert_eq!(section(&out)?,section(&raw)?.replace("autoNum num='2'","autoNum num='9'"));Ok(())
}
#[test]
fn review_number_source_reuses_output_form_field_review_admission_and_exact_sha()->TestResult{
    let raw=observed("autoNum")?;let f=forms(&raw)?;let c=replace(&f,&raw,Scope::Document,body(),Kind::AutoNumber,9,Format::Preserve)?;
    let r=c.receipt();let shared=r.stream.content.output.output_review_import.as_ref().ok_or("shared review")?;
    assert_eq!(shared,&r.output_review_import);assert_eq!(shared.source_package_sha256,r.stream.content.output.output_package_sha256);
    assert_eq!((shared.hidden_explanations,shared.memo_fields),(1,1));
    assert!(r.stream.content.source_state.numbering.review_body_inventory_sha256.is_some());assert!(!r.stream.number_sequence.native_counter_interpretation_and_recalculation_qualified);
    output(&raw,&c)?;Ok(())
}
