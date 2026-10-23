//! Exact synthetic catalog-match masks, not personal data, Native matching or package anonymization.
use super::*;
use hwpx_package::document_import::search::{personal_info::catalog::{SourcePersonalInfoCatalog as Catalog,
    PersonalInfoCatalogFamily as Family,PersonalInfoCatalogError as CatalogError},replacement::atoms::personal_info::catalog::{
    SourcePersonalInfoCatalogMaskCandidate as CatalogCandidate,SourcePersonalInfoCatalogMaskError as CM}};
const SECTIONS:[&str;11]=["TELEPHONE","RESIDENT","FOREIGNER","EMAIL","ACCOUNT","LICENSE","PASSPORT","CREDIT","IPADDRESS","BIRTHDAY","USERDEF"];
fn config(patterns:&[&str])->Result<Catalog,Box<dyn Error>>{
    let text=SECTIONS.iter().enumerate().map(|(i,name)|format!("[{name}]\r\n{}",if i==0{
        patterns.iter().enumerate().map(|(n,p)|format!("pattern{n}={p}\r\n")).collect::<String>()
    }else if i==10{String::new()}else{format!("pattern0=UNMATCHED-{i}\r\n")})).collect::<String>();
    let mut raw=vec![0xff,0xfe];for unit in text.encode_utf16(){raw.extend_from_slice(&unit.to_le_bytes());}
    Ok(Catalog::parse_utf16le(&raw,Sha256::digest(&raw).into())?)
}
fn candidate(raw:&[u8],patterns:&[&str],policy:Mask)->Result<CatalogCandidate,Box<dyn Error>>{
    Ok(forms(raw)?.lower_personal_info_catalog_mask_candidate(raw,&config(patterns)?,&[Family::Telephone],Scope::Document,all(),policy,Default::default(),Default::default())?)
}
fn bytes(raw:&[u8],c:&CatalogCandidate)->Result<Vec<u8>,Box<dyn Error>>{
    let value=c.with_verified_bytes(<[u8]>::to_vec)?;let r=c.receipt();
    assert_eq!(r.source_package_sha256,<[u8;32]>::from(Sha256::digest(raw)));assert_eq!(r.output_package_sha256,<[u8;32]>::from(Sha256::digest(&value)));
    assert!(r.exact_original_match_selections_verified&&r.original_run_shells_styles_controls_and_references_preserved&&r.output_spans_and_outside_slots_verified);
    assert!(!r.whole_package_personal_data_removed&&!r.native_catalog_mask_semantics_or_service_execution_qualified);Ok(value)
}
fn exact_mask(raw:&[u8],c:&CatalogCandidate,old:&str,new:&str)->R{assert_eq!(section(&bytes(raw,c)?)?,section(raw)?.replace(old,new));Ok(())}

#[test]
fn only_actual_matches_are_masked_not_all_text_in_the_selected_scope()->R{
    let raw=fixture::package(&para(1,"before MARK middle MARK after"))?;let original=raw.clone();
    let c=candidate(&raw,&["MARK"],Mask::PerOriginalScalarPreserveSlots)?;
    exact_mask(&raw,&c,"before MARK middle MARK after","before **** middle **** after")?;
    assert_eq!(c.receipt().matched_formats,2);assert_eq!(c.receipt().matched_original_scalars,8);assert_eq!(raw,original);Ok(())
}
#[test]
fn fixed_policy_masks_each_actual_format_match_without_masking_its_neighbors()->R{
    let raw=fixture::package(&para(1,"x A y LONGER z"))?;let c=candidate(&raw,&["A","LONGER"],Mask::ThreeAsterisksPerTextGroup)?;
    exact_mask(&raw,&c,"x A y LONGER z","x *** y *** z")?;assert_eq!(c.receipt().matched_formats,2);assert_eq!(c.receipt().matched_text_groups,2);Ok(())
}
#[test]
fn adjacent_matches_remain_separate_fixed_mask_groups()->R{
    let raw=fixture::package(&para(1,"ABAB"))?;let c=candidate(&raw,&["AB"],Mask::ThreeAsterisksPerTextGroup)?;
    exact_mask(&raw,&c,"ABAB","******")?;assert_eq!(c.receipt().matched_text_groups,2);Ok(())
}
#[test]
fn match_crosses_runs_but_scalar_mask_preserves_all_original_slots_and_styles()->R{
    let body="<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>pre MA</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t charStyleIDRef='1'>RK post</hp:t></hp:run></hp:p>";
    let raw=fixture::package(body)?;let c=candidate(&raw,&["MARK"],Mask::PerOriginalScalarPreserveSlots)?;
    exact_mask(&raw,&c,body,&body.replace("pre MA","pre **").replace("RK post","** post"))?;Ok(())
}
#[test]
fn fixed_match_group_crosses_runs_once_and_preserves_unmatched_prefix_and_suffix()->R{
    let body="<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>pre MA</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t>RK post</hp:t></hp:run></hp:p>";
    let raw=fixture::package(body)?;let c=candidate(&raw,&["MARK"],Mask::ThreeAsterisksPerTextGroup)?;
    exact_mask(&raw,&c,body,&body.replace("pre MA","pre ***").replace("RK post"," post"))?;assert_eq!(c.receipt().matched_text_groups,1);Ok(())
}
#[test]
fn decoded_entities_and_non_bmp_scalars_mask_original_scalars_not_xml_or_utf16_bytes()->R{
    let text="before A&amp;😀각 after";let raw=fixture::package(&para(1,text))?;let c=candidate(&raw,&["A&😀각"],Mask::PerOriginalScalarPreserveSlots)?;
    exact_mask(&raw,&c,text,"before **** after")?;assert_eq!(c.receipt().matched_original_scalars,4);Ok(())
}
#[test]
fn composed_hangul_match_masks_all_original_decomposed_contributors_in_their_own_runs()->R{
    let body="<hp:p id='1'><hp:run><hp:t>ᄀ</hp:t></hp:run><hp:run><hp:t>ᅡᆨ</hp:t></hp:run></hp:p>";
    let raw=fixture::package(body)?;let c=candidate(&raw,&["각"],Mask::PerOriginalScalarPreserveSlots)?;
    exact_mask(&raw,&c,body,&body.replace(">ᄀ<",">*<").replace(">ᅡᆨ<",">**<"))?;assert_eq!(c.receipt().matched_original_scalars,3);Ok(())
}
#[test]
fn inexact_canonically_reordered_partial_match_is_rejected_not_widened_or_skipped()->R{
    let raw=fixture::package(&para(1,"a\u{315}\u{300}Z"))?;let f=forms(&raw)?;
    assert!(matches!(f.lower_personal_info_catalog_mask_candidate(&raw,&config(&["à"])?,&[Family::Telephone],Scope::Document,all(),Mask::PerOriginalScalarPreserveSlots,Default::default(),Default::default()),Err(CM::Replacement(E::Selection))));Ok(())
}
#[test]
fn complete_reordered_match_masks_all_contributors_and_keeps_the_unmatched_tail()->R{
    let text="a\u{315}\u{300}Z";let raw=fixture::package(&para(1,text))?;let c=candidate(&raw,&["à\u{315}"],Mask::PerOriginalScalarPreserveSlots)?;
    exact_mask(&raw,&c,text,"***Z")?;Ok(())
}
#[test]
fn tabs_linebreaks_and_paragraph_boundaries_are_not_removed_to_create_a_format_match()->R{
    let raw=fixture::package(&(para(1,"MA<hp:tab width='1' leader='0' type='0'/>RK MA<hp:lineBreak/>RK")+&para(2,"MA")+&para(3,"RK")))?;
    let f=forms(&raw)?;assert!(matches!(f.lower_personal_info_catalog_mask_candidate(&raw,&config(&["MARK"])?,&[Family::Telephone],Scope::Document,all(),Mask::ThreeAsterisksPerTextGroup,Default::default(),Default::default()),Err(CM::Replacement(E::NoMatches))));Ok(())
}
#[test]
fn independent_matches_around_control_atoms_keep_original_control_bytes()->R{
    let text="MA<hp:tab width='1' leader='0' type='0'> </hp:tab>RK<hp:lineBreak> </hp:lineBreak>MA";
    let raw=fixture::package(&para(1,text))?;let c=candidate(&raw,&["MA","RK"],Mask::ThreeAsterisksPerTextGroup)?;
    exact_mask(&raw,&c,text,&text.replace("MA","***").replace("RK","***"))?;assert_eq!(c.receipt().matched_formats,3);Ok(())
}
#[test]
fn no_match_is_not_a_fabricated_unchanged_successful_candidate()->R{
    let raw=fixture::package(&para(1,"unmatched text"))?;let f=forms(&raw)?;
    assert!(matches!(f.lower_personal_info_catalog_mask_candidate(&raw,&config(&["MARK"])?,&[Family::Telephone],Scope::Document,all(),Mask::ThreeAsterisksPerTextGroup,Default::default(),Default::default()),Err(CM::Replacement(E::NoMatches))));Ok(())
}
#[test]
fn already_masked_match_is_no_change_not_an_executed_privacy_operation()->R{
    let raw=fixture::package(&para(1,"***"))?;let f=forms(&raw)?;
    assert!(matches!(f.lower_personal_info_catalog_mask_candidate(&raw,&config(&[r"\*+"])?,&[Family::Telephone],Scope::Document,all(),Mask::ThreeAsterisksPerTextGroup,Default::default(),Default::default()),Err(CM::Replacement(E::NoChange))));Ok(())
}
#[test]
fn fresh_whole_source_mismatch_is_rejected_before_catalog_masking()->R{
    let raw=fixture::package(&para(1,"MARK"))?;let changed=fixture::package(&para(1,"DIFFERENT-MARK"))?;let f=forms(&raw)?;
    assert!(matches!(f.lower_personal_info_catalog_mask_candidate(&changed,&config(&["MARK"])?,&[Family::Telephone],Scope::Document,all(),Mask::ThreeAsterisksPerTextGroup,Default::default(),Default::default()),Err(CM::Replacement(E::Source))));Ok(())
}
#[test]
fn missing_duplicate_or_empty_family_selection_is_not_replaced_by_default_formats()->R{
    let raw=fixture::package(&para(1,"MARK"))?;let f=forms(&raw)?;let c=config(&["MARK"])?;
    for families in [&[][..],&[Family::Telephone,Family::Telephone][..]]{
        assert!(matches!(f.lower_personal_info_catalog_mask_candidate(&raw,&c,families,Scope::Document,all(),Mask::ThreeAsterisksPerTextGroup,Default::default(),Default::default()),Err(CM::Catalog(CatalogError::Selection))));}
    assert!(matches!(f.lower_personal_info_catalog_mask_candidate(&raw,&c,&[Family::UserDefined],Scope::Document,all(),Mask::ThreeAsterisksPerTextGroup,Default::default(),Default::default()),Err(CM::Replacement(E::NoMatches))));Ok(())
}
#[test]
fn entire_selected_catalog_is_used_beyond_the_legacy_first_sixteen_patterns()->R{
    let patterns:Vec<_>=(0..32).map(|n|format!("TOKEN{n:02}")).collect();let refs:Vec<_>=patterns.iter().map(String::as_str).collect();
    let raw=fixture::package(&para(1,"before TOKEN31 after"))?;let c=candidate(&raw,&refs,Mask::ThreeAsterisksPerTextGroup)?;
    exact_mask(&raw,&c,"before TOKEN31 after","before *** after")?;assert_eq!(c.receipt().selected_patterns,32);Ok(())
}
#[test]
fn unsupported_and_zero_width_catalog_patterns_fail_without_partial_edits_or_fallback()->R{
    let raw=fixture::package(&para(1,"MARK"))?;let f=forms(&raw)?;
    for pattern in ["(?=MARK)MARK","a*"]{assert!(matches!(f.lower_personal_info_catalog_mask_candidate(&raw,&config(&[pattern])?,&[Family::Telephone],Scope::Document,all(),Mask::ThreeAsterisksPerTextGroup,Default::default(),Default::default()),Err(CM::Catalog(CatalogError::Pattern))));}Ok(())
}
#[test]
fn source_pattern_order_and_selected_mask_policy_are_bound_even_when_output_is_equal()->R{
    let raw=fixture::package(&para(1,"ABC"))?;let a=candidate(&raw,&["ABC","UNUSED"],Mask::ThreeAsterisksPerTextGroup)?;
    let b=candidate(&raw,&["UNUSED","ABC"],Mask::ThreeAsterisksPerTextGroup)?;let c=candidate(&raw,&["ABC","UNUSED"],Mask::PerOriginalScalarPreserveSlots)?;
    assert_eq!(a.receipt().output_package_sha256,b.receipt().output_package_sha256);assert_eq!(a.receipt().output_package_sha256,c.receipt().output_package_sha256);
    assert_ne!(a.receipt().request_sha256,b.receipt().request_sha256);assert_ne!(a.receipt().detection_result_sha256,b.receipt().detection_result_sha256);
    assert_ne!(a.receipt().request_sha256,c.receipt().request_sha256);Ok(())
}
#[test]
fn document_section_node_and_exact_selection_keep_the_original_scope_identity()->R{
    let raw=fixture::package(&(para(1,"MARK")+&para(2,"MARK")))?;let f=forms(&raw)?;let inv=f.source_review_scope_index(&raw,Default::default())?.scope_inventory()?;
    let block=&inv.inventory.blocks[0];let id=inv.inventory.nodes.iter().find(|n|n.source_handle==block.paragraph_handle).ok_or("node")?.node_id.clone();
    let ids=[id];let a=boundary(block,0);let b=boundary(block,4);
    for(scope,n)in [(Scope::Document,2),(Scope::Section(&inv.inventory.section_ids),2),(Scope::NodeSet(&ids),1),(Scope::Selection{index_sha256:inv.inventory.index.index_sha256,start:&a,end:&b},1)]{
        let c=f.lower_personal_info_catalog_mask_candidate(&raw,&config(&["MARK"])?,&[Family::Telephone],scope,all(),Mask::ThreeAsterisksPerTextGroup,Default::default(),Default::default())?;
        assert_eq!(c.receipt().matched_formats,n);assert_eq!(section(&bytes(&raw,&c)?)?.matches(">***<").count(),n);}Ok(())
}
#[test]
fn a_foreign_selection_digest_cannot_be_rebound_to_the_current_document()->R{
    let raw=fixture::package(&para(1,"MARK"))?;let foreign=fixture::package(&para(1,"MARK DIFFERENT"))?;let f=forms(&raw)?;
    let inv=forms(&foreign)?.source_review_scope_index(&foreign,Default::default())?.scope_inventory()?;let a=boundary(&inv.inventory.blocks[0],0);let b=boundary(&inv.inventory.blocks[0],4);
    assert!(f.lower_personal_info_catalog_mask_candidate(&raw,&config(&["MARK"])?,&[Family::Telephone],Scope::Selection{index_sha256:inv.inventory.index.index_sha256,start:&a,end:&b},all(),Mask::ThreeAsterisksPerTextGroup,Default::default(),Default::default()).is_err());Ok(())
}
#[test]
fn hidden_and_memo_policy_excludes_regions_before_matching_and_preserves_cached_text()->R{
    let raw=review::package()?;let f=forms(&raw)?;
    for(hidden,memo,n)in [(true,true,6),(false,true,4),(true,false,4),(false,false,2)]{
        let c=f.lower_personal_info_catalog_mask_candidate(&raw,&config(&[r"\bK\b"])?,&[Family::Telephone],Scope::Document,Policy{include_hidden_explanations:hidden,include_memo_bodies:memo},Mask::PerOriginalScalarPreserveSlots,Default::default(),Default::default())?;
        assert_eq!(c.receipt().matched_formats,n);let text=section(&bytes(&raw,&c)?)?;assert!(text.contains("CACHE FROZEN")&&text.contains("PRIVATE-AUTHOR"));
        assert_eq!(c.receipt().excluded_hidden_paragraphs,usize::from(!hidden));assert_eq!(c.receipt().excluded_memo_paragraphs,usize::from(!memo));}Ok(())
}
#[test]
fn matched_generic_field_cache_rejects_the_whole_operation_not_only_that_occurrence()->R{
    let body="<hp:p id='1'><hp:run><hp:t>MARK outside</hp:t><hp:ctrl><hp:fieldBegin id='7' type='DATE'/></hp:ctrl><hp:t>MARK</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='7'/></hp:ctrl></hp:run></hp:p>";
    let raw=fixture::package(body)?;let f=forms(&raw)?;
    assert!(matches!(f.lower_personal_info_catalog_mask_candidate(&raw,&config(&["MARK"])?,&[Family::Telephone],Scope::Document,all(),Mask::ThreeAsterisksPerTextGroup,Default::default(),Default::default()),Err(CM::Replacement(E::FieldContent))));Ok(())
}
#[test]
fn selected_tracked_content_rejects_without_using_a_partial_candidate()->R{
    let body="<hp:p id='1'><hp:run charTcId='0'><hp:t>MARK</hp:t></hp:run></hp:p>";let raw=fixture::package(body)?;let f=forms(&raw)?;
    assert!(matches!(f.lower_personal_info_catalog_mask_candidate(&raw,&config(&["MARK"])?,&[Family::Telephone],Scope::Document,all(),Mask::ThreeAsterisksPerTextGroup,Default::default(),Default::default()),Err(CM::Replacement(E::Protection))));Ok(())
}
#[test]
fn header_document_protection_blocks_even_an_unrelated_body_match()->R{
    let raw=archive::mutate_part(&fixture::package(&para(1,"MARK"))?,"Contents/header.xml",|t|Ok(t.replacen("<hh:head ","<hh:head protect='0' ",1)))?;let f=forms(&raw)?;
    assert_eq!(f.source().observe_protection_signals()?.counts().document_signal_parts,1);
    assert!(matches!(f.lower_personal_info_catalog_mask_candidate(&raw,&config(&["MARK"])?,&[Family::Telephone],Scope::Document,all(),Mask::ThreeAsterisksPerTextGroup,Default::default(),Default::default()),Err(CM::Replacement(E::Protection))));Ok(())
}
#[test]
fn unselected_tracked_text_is_preserved_not_widened_into_the_mask()->R{
    let body=para(1,"MARK")+"<hp:p id='2'><hp:run charTcId='0'><hp:t>MARK</hp:t></hp:run></hp:p>";let raw=fixture::package(&body)?;let f=forms(&raw)?;
    let inv=f.source_review_scope_index(&raw,Default::default())?.scope_inventory()?;let a=boundary(&inv.inventory.blocks[0],0);let b=boundary(&inv.inventory.blocks[0],4);
    let c=f.lower_personal_info_catalog_mask_candidate(&raw,&config(&["MARK"])?,&[Family::Telephone],Scope::Selection{index_sha256:inv.inventory.index.index_sha256,start:&a,end:&b},all(),Mask::ThreeAsterisksPerTextGroup,Default::default(),Default::default())?;
    assert_eq!(section(&bytes(&raw,&c)?)?,section(&raw)?.replacen(">MARK<",">***<",1));Ok(())
}
#[test]
fn header_metadata_and_nonselected_members_remain_exact_not_reported_as_anonymized()->R{
    let raw=fixture::package(&para(1,"MARK private-unmatched"))?;let c=candidate(&raw,&["MARK"],Mask::ThreeAsterisksPerTextGroup)?;let out=bytes(&raw,&c)?;
    for part in ["Contents/header.xml","Contents/content.hpf"]{assert_eq!(archive::read_part(&raw,part)?,archive::read_part(&out,part)?);}
    assert!(section(&out)?.contains("private-unmatched"));assert!(!c.receipt().whole_package_personal_data_removed);Ok(())
}
#[test]
fn public_metadata_and_debug_omit_pattern_bodies_source_values_and_per_value_hashes()->R{
    let raw=fixture::package(&para(1,"PRIVATE-SYNTHETIC-MARKER"))?;let c=candidate(&raw,&["PRIVATE-SYNTHETIC-MARKER"],Mask::ThreeAsterisksPerTextGroup)?;
    for text in [String::from_utf8(c.canonical_json()?)?,format!("{c:?}{:?}{:?}",c.receipt(),c.edit_inventory())]{
        for private in ["PRIVATE-","source_span_sha256","source_text_sha256","pattern0=","<hp:"]{assert!(!text.contains(private));}}Ok(())
}
#[test]
fn match_work_metadata_and_writer_limits_fail_without_a_partial_artifact()->R{
    let raw=fixture::package(&para(1,"MARK MARK"))?;let f=forms(&raw)?;let c=config(&["MARK"])?;
    for limits in [Config{matches:1,..Default::default()},Config{result_bytes:1,..Default::default()},Config{decomposed_scalars:2,..Default::default()}]{
        assert!(f.lower_personal_info_catalog_mask_candidate(&raw,&c,&[Family::Telephone],Scope::Document,all(),Mask::PerOriginalScalarPreserveSlots,SourceSearchLimits::new(limits)?,Default::default()).is_err());}
    assert!(matches!(f.lower_personal_info_catalog_mask_candidate(&raw,&c,&[Family::Telephone],Scope::Document,all(),Mask::ThreeAsterisksPerTextGroup,Default::default(),WriterLimits::new(WriterLimitConfig{max_output_bytes:1})?),Err(CM::Replacement(E::Writer))));Ok(())
}
#[test]
fn edit_inventory_binds_current_source_output_receipt_and_every_changed_text_anchor()->R{
    let body="<hp:p id='1'><hp:run><hp:t>MARK</hp:t><hp:t>MARK</hp:t></hp:run></hp:p>";let raw=fixture::package(body)?;let c=candidate(&raw,&["MARK"],Mask::PerOriginalScalarPreserveSlots)?;let inventory=c.edit_inventory();
    assert_eq!(inventory.anchors().len(),2);assert_eq!(inventory.source_package_sha256(),c.receipt().source_package_sha256);assert_eq!(inventory.output_package_sha256(),c.receipt().output_package_sha256);
    assert_eq!(inventory.receipt_sha256(),<[u8;32]>::from(Sha256::digest(serde_json::to_vec(c.receipt())?)));assert_ne!(inventory.canonical_sha256(),[0;32]);Ok(())
}
#[test]
fn borrowed_verified_form_proof_and_public_entry_produce_identical_bound_candidates()->R{
    let raw=fixture::package(&para(1,"before MARK after"))?;let f=forms(&raw)?;let c=config(&["MARK"])?;
    let direct=f.lower_personal_info_catalog_mask_candidate(&raw,&c,&[Family::Telephone],Scope::Document,all(),Mask::PerOriginalScalarPreserveSlots,Default::default(),Default::default())?;
    let proof=f.reconstruct_source_for_verification(&raw)?;let shared=proof.lower_personal_info_catalog_mask_candidate(&f,&c,&[Family::Telephone],Scope::Document,all(),Mask::PerOriginalScalarPreserveSlots,Default::default(),Default::default())?;
    assert_eq!(direct.receipt(),shared.receipt());assert_eq!(bytes(&raw,&direct)?,bytes(&raw,&shared)?);Ok(())
}
