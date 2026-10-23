//! Synthetic selected-body masking, not real personal data, package sanitization or Native qualification.
#[path="support/personal_info_detection.rs"]mod detection;
#[path="support/personal_info_catalog.rs"]mod catalog;
#[path="support/personal_info_catalog_mask.rs"]mod catalog_mask;
use hwpx_package::{PreservingXmlDocument,WriterLimits,WriterLimitConfig,document_import::{ImportedSourcePackage,forms::ImportedDocumentForms,
    search::{SourceSearchLimits,SourceSearchLimitConfig as Config,selector::{SourceIndexScopeSelector as Scope,SourceIndexBoundary as Boundary},
        reviews::{SourceReviewTextPolicy as Policy,SourceTextRegion},replacement::{SourceLiteralReplacementError as E,
            atoms::personal_info::{SourcePersonalInfoMaskPolicy as Mask,SourcePersonalInfoMaskCandidate as Candidate}}}}};
use domain_ir::{DocumentId,LogicalId};
use sha2::{Digest as _,Sha256};
use std::error::Error;
#[allow(dead_code)]#[path="support/search_definition_fixture.rs"]mod fixture;
#[allow(dead_code)]#[path="support/review_scope_fixture.rs"]mod review;
#[allow(dead_code)]#[path="support/document_import_catalog_fixture.rs"]mod archive;
#[allow(dead_code)]#[path="support/document_import_review_assembly_fixture.rs"]mod assembly;
#[allow(dead_code)]#[path="support/review_cell_output_fixture.rs"]mod table;
type R=Result<(),Box<dyn Error>>;
fn forms(raw:&[u8])->Result<ImportedDocumentForms,Box<dyn Error>>{Ok(ImportedDocumentForms::import(ImportedSourcePackage::import(raw,
    DocumentId::parse("personal-info-mask-source")?,Sha256::digest(raw).into(),Default::default())?)?)}
fn para(id:u32,text:&str)->String{format!("<hp:p id='{id}'><hp:run charPrIDRef='0'><hp:t charStyleIDRef='0'>{text}</hp:t></hp:run></hp:p>")}
fn all()->Policy{Policy{include_hidden_explanations:true,include_memo_bodies:true}}
fn mask(f:&ImportedDocumentForms,raw:&[u8],scope:Scope<'_>,policy:Policy,m:Mask)->Result<Candidate,E>{f.lower_personal_info_mask_candidate(raw,scope,policy,m,Default::default(),Default::default())}
fn output(raw:&[u8],c:&Candidate)->Result<Vec<u8>,Box<dyn Error>>{let out=c.with_verified_bytes(<[u8]>::to_vec)?;let r=c.receipt();
    assert_eq!(r.source_package_sha256,<[u8;32]>::from(Sha256::digest(raw)));assert_eq!(r.output_package_sha256,<[u8;32]>::from(Sha256::digest(&out)));
    assert!(r.exact_original_selection_verified&&r.original_run_shells_styles_controls_and_references_preserved&&r.output_spans_and_outside_slots_verified);
    assert!(!r.whole_package_personal_data_removed&&!r.native_mask_semantics_or_service_execution_qualified);Ok(out)}
fn section(raw:&[u8])->Result<String,Box<dyn Error>>{Ok(String::from_utf8(archive::read_part(raw,"Contents/section0.xml")?)?)}
fn exact(raw:&[u8],c:&Candidate,old:&str,new:&str)->R{assert_eq!(section(&output(raw,c)?)?,section(raw)?.replace(old,new));Ok(())}
fn boundary(block:&hwpx_package::document_import::search::selector::inventory::SourceIndexBlockDescriptor,offset:usize)->Boundary{
    Boundary{paragraph_handle:block.paragraph_handle.clone(),block_index:block.block_index,normalized_scalar:offset}
}
#[test]
fn original_scalar_policy_counts_decoded_unicode_not_entity_bytes_or_utf16()->R{
    let text="A&amp;😀각";let raw=fixture::package(&para(1,text))?;let f=forms(&raw)?;let c=mask(&f,&raw,Scope::Document,all(),Mask::PerOriginalScalarPreserveSlots)?;
    exact(&raw,&c,text,"****")?;assert_eq!(c.receipt().selected_original_scalars,4);Ok(())
}
#[test]
fn fixed_policy_writes_three_stars_per_text_group_not_original_length()->R{
    let raw=fixture::package(&(para(1,"A")+&para(2,"LONGER-MARKER")))?;let f=forms(&raw)?;let c=mask(&f,&raw,Scope::Document,all(),Mask::ThreeAsterisksPerTextGroup)?;
    assert_eq!(section(&output(&raw,&c)?)?,section(&raw)?.replace(">A<",">***<").replace("LONGER-MARKER","***"));assert_eq!(c.receipt().selected_text_groups,2);Ok(())
}
#[test]
fn per_scalar_mask_retains_each_original_run_and_text_slot()->R{
    let body="<hp:p id='1'><hp:run charPrIDRef='0'><hp:t charStyleIDRef='0'>AB</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t charStyleIDRef='1'>CDE</hp:t><hp:t>F</hp:t></hp:run></hp:p>";
    let raw=fixture::package(body)?;let f=forms(&raw)?;let c=mask(&f,&raw,Scope::Document,all(),Mask::PerOriginalScalarPreserveSlots)?;
    exact(&raw,&c,body,&body.replace(">AB<",">**<").replace(">CDE<",">***<").replace(">F<",">*<"))?;Ok(())
}
#[test]
fn fixed_group_crosses_runs_once_but_retains_all_original_shells()->R{
    let body="<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>AB</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t>CD</hp:t></hp:run></hp:p>";
    let raw=fixture::package(body)?;let f=forms(&raw)?;let c=mask(&f,&raw,Scope::Document,all(),Mask::ThreeAsterisksPerTextGroup)?;
    exact(&raw,&c,body,&body.replace(">AB<",">***<").replace(">CD<","><"))?;assert_eq!(c.receipt().selected_text_groups,1);Ok(())
}
#[test]
fn decomposed_hangul_uses_all_original_contributors_without_normalizing_them_first()->R{
    let body="<hp:p id='1'><hp:run charPrIDRef='0'><hp:t>ᄀ</hp:t></hp:run><hp:run charPrIDRef='1'><hp:t>ᅡᆨ</hp:t></hp:run></hp:p>";
    let raw=fixture::package(body)?;let f=forms(&raw)?;let c=mask(&f,&raw,Scope::Document,all(),Mask::PerOriginalScalarPreserveSlots)?;
    exact(&raw,&c,body,&body.replace(">ᄀ<",">*<").replace(">ᅡᆨ<",">**<"))?;assert_eq!(c.receipt().selected_original_scalars,3);assert_eq!(c.receipt().selector.selected_normalized_scalars,1);Ok(())
}
#[test]
fn tab_and_paired_linebreak_bytes_survive_and_split_fixed_mask_groups()->R{
    let text="A<hp:tab width='1' leader='0' type='0'> </hp:tab>B<hp:lineBreak> </hp:lineBreak>C<hp:lineBreak/>D";
    let raw=fixture::package(&para(1,text))?;let f=forms(&raw)?;let c=mask(&f,&raw,Scope::Document,all(),Mask::ThreeAsterisksPerTextGroup)?;
    exact(&raw,&c,text,&text.replace("A<hp:tab","***<hp:tab").replace("</hp:tab>B","</hp:tab>***").replace("</hp:lineBreak>C","</hp:lineBreak>***").replace("<hp:lineBreak/>D","<hp:lineBreak/>***"))?;Ok(())
}
#[test]
fn exact_partial_selection_preserves_outside_entities_and_decomposed_text_byte_for_byte()->R{
    let text="A&amp;B à &#x65;&#x301;";let raw=fixture::package(&para(1,text))?;let f=forms(&raw)?;let inv=f.source_review_scope_index(&raw,Default::default())?.scope_inventory()?;
    let start=boundary(&inv.inventory.blocks[0],1);let end=boundary(&inv.inventory.blocks[0],2);
    let c=mask(&f,&raw,Scope::Selection{index_sha256:inv.inventory.index.index_sha256,start:&start,end:&end},all(),Mask::PerOriginalScalarPreserveSlots)?;exact(&raw,&c,text,"A*B à &#x65;&#x301;")?;Ok(())
}
#[test]
fn reordered_partial_nfc_selection_is_rejected_instead_of_widened()->R{
    let raw=fixture::package(&para(1,"a\u{315}\u{300}Z"))?;let f=forms(&raw)?;let inv=f.source_review_scope_index(&raw,Default::default())?.scope_inventory()?;
    let start=boundary(&inv.inventory.blocks[0],0);let end=boundary(&inv.inventory.blocks[0],1);
    assert!(matches!(mask(&f,&raw,Scope::Selection{index_sha256:inv.inventory.index.index_sha256,start:&start,end:&end},all(),Mask::PerOriginalScalarPreserveSlots),Err(E::Selection)));Ok(())
}
#[test]
fn document_section_node_and_exact_selection_use_original_scope_identities()->R{
    let raw=fixture::package(&(para(1,"ABC")+&para(2,"DEF")))?;let f=forms(&raw)?;let inv=f.source_review_scope_index(&raw,Default::default())?.scope_inventory()?;
    let block=&inv.inventory.blocks[0];let node=inv.inventory.nodes.iter().find(|n|n.source_handle==block.paragraph_handle).ok_or("node")?;let nodes=vec![node.node_id.clone()];
    let start=boundary(block,0);let end=boundary(block,3);
    for(scope,n)in [(Scope::Document,2),(Scope::Section(&inv.inventory.section_ids),2),(Scope::NodeSet(&nodes),1),(Scope::Selection{index_sha256:inv.inventory.index.index_sha256,start:&start,end:&end},1)]{
        let c=mask(&f,&raw,scope,all(),Mask::ThreeAsterisksPerTextGroup)?;assert_eq!(section(&output(&raw,&c)?)?.matches(">***<").count(),n);}Ok(())
}
#[test]
fn empty_duplicate_and_foreign_node_sets_never_fall_back_to_document_scope()->R{
    let raw=fixture::package(&para(1,"ABC"))?;let f=forms(&raw)?;let inv=f.source_review_scope_index(&raw,Default::default())?.scope_inventory()?;
    let id=inv.inventory.nodes[0].node_id.clone();for nodes in [vec![],vec![id.clone(),id],vec![LogicalId::parse("foreign-node")?]]{
        assert!(mask(&f,&raw,Scope::NodeSet(&nodes),all(),Mask::ThreeAsterisksPerTextGroup).is_err());}Ok(())
}
#[test]
fn foreign_original_proof_stale_index_and_changed_fresh_source_are_rejected()->R{
    let raw=fixture::package(&para(1,"ABC"))?;let f=forms(&raw)?;let other=forms(&raw)?;let proof=f.reconstruct_source_for_verification(&raw)?;
    assert!(matches!(proof.lower_personal_info_mask_candidate(&other,Scope::Document,all(),Mask::ThreeAsterisksPerTextGroup,Default::default(),Default::default()),Err(E::Source)));
    let inv=f.source_review_scope_index(&raw,Default::default())?.scope_inventory()?;let start=boundary(&inv.inventory.blocks[0],0);let end=boundary(&inv.inventory.blocks[0],1);
    assert!(mask(&f,&raw,Scope::Selection{index_sha256:[0;32],start:&start,end:&end},all(),Mask::PerOriginalScalarPreserveSlots).is_err());
    assert!(matches!(mask(&f,&fixture::package(&para(1,"DIFFERENT"))?,Scope::Document,all(),Mask::PerOriginalScalarPreserveSlots),Err(E::Source)));Ok(())
}
#[test]
fn review_policy_excludes_hidden_and_memo_before_mask_planning_without_editing_cache()->R{
    let raw=fixture::package(&(para(30,"PLAIN")+&review::body()))?;let f=forms(&raw)?;let inv=f.source_review_scope_index(&raw,Default::default())?.scope_inventory()?;
    let ids=inv.inventory.blocks.iter().zip(&inv.block_regions).filter(|(b,r)|b.block_index==0||**r!=SourceTextRegion::BodyAndNotes)
        .map(|(b,_)|inv.inventory.nodes.iter().find(|n|n.source_handle==b.paragraph_handle).map(|n|n.node_id.clone()).ok_or("node")).collect::<Result<Vec<_>,_>>()?;
    for(h,m,n)in [(false,false,1),(true,false,2),(false,true,2),(true,true,3)]{
        let c=mask(&f,&raw,Scope::NodeSet(&ids),Policy{include_hidden_explanations:h,include_memo_bodies:m},Mask::ThreeAsterisksPerTextGroup)?;let text=section(&output(&raw,&c)?)?;
        assert_eq!(text.matches(">***").count(),n);assert!(text.contains("CACHE FROZEN"));assert_eq!(c.receipt().excluded_hidden_paragraphs,usize::from(!h));assert_eq!(c.receipt().excluded_memo_paragraphs,usize::from(!m));}Ok(())
}
#[test]
fn memo_author_metadata_is_not_claimed_sanitized_by_payload_masking()->R{
    let raw=fixture::package(&review::body())?;let f=forms(&raw)?;let inv=f.source_review_scope_index(&raw,Default::default())?.scope_inventory()?;
    let b=inv.inventory.blocks.iter().zip(&inv.block_regions).find(|(_,r)|**r==SourceTextRegion::MemoBody).ok_or("memo")?.0;
    let id=inv.inventory.nodes.iter().find(|n|n.source_handle==b.paragraph_handle).ok_or("node")?.node_id.clone();
    let c=mask(&f,&raw,Scope::NodeSet(&[id]),all(),Mask::ThreeAsterisksPerTextGroup)?;let text=section(&output(&raw,&c)?)?;
    assert!(text.contains("PRIVATE-AUTHOR")&&!text.contains("MEMO K K"));assert!(!c.receipt().whole_package_personal_data_removed);Ok(())
}
#[test]
fn field_cached_content_is_rejected_even_if_already_three_stars()->R{
    let raw=fixture::package(&para(1,"</hp:t><hp:ctrl><hp:fieldBegin id='17' type='DATE'/></hp:ctrl><hp:t>***</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='17'/></hp:ctrl><hp:t>"))?;
    let f=forms(&raw)?;assert!(matches!(mask(&f,&raw,Scope::Document,all(),Mask::ThreeAsterisksPerTextGroup),Err(E::FieldContent)));Ok(())
}
#[test]
fn paragraph_and_character_tracking_zero_signals_are_checked_before_noop_elimination()->R{
    for body in [para(1,"***").replace("<hp:p ","<hp:p paraTcId='0' "),para(1,"***").replace("<hp:run ","<hp:run charTcId='0' ")]{
        let raw=fixture::package(&body)?;let f=forms(&raw)?;assert!(matches!(mask(&f,&raw,Scope::Document,all(),Mask::ThreeAsterisksPerTextGroup),Err(E::Protection)));}Ok(())
}
#[test]
fn locked_table_blocks_masking_without_silent_skips()->R{
    let body=format!("<hp:p id='1'><hp:run>{}</hp:run></hp:p>",table::table(300).replace("lock='0'","lock='1'"));
    let raw=fixture::package(&body)?;let f=forms(&raw)?;assert!(matches!(mask(&f,&raw,Scope::Document,all(),Mask::PerOriginalScalarPreserveSlots),Err(E::Protection)));Ok(())
}
#[test]
fn document_header_protection_signal_blocks_unrelated_selected_body()->R{
    let raw=archive::mutate_part(&fixture::package(&para(1,"ABC"))?,"Contents/header.xml",|t|Ok(t.replacen("<hh:head ","<hh:head protect='0' ",1)))?;
    let f=forms(&raw)?;assert_eq!(f.source().observe_protection_signals()?.counts().document_signal_parts,1);
    assert!(matches!(mask(&f,&raw,Scope::Document,all(),Mask::ThreeAsterisksPerTextGroup),Err(E::Protection)));Ok(())
}
#[test]
fn nonselected_text_beyond_bookmark_control_keeps_exact_original_xml()->R{
    let body="<hp:p id='1'><hp:run><hp:t>ABC</hp:t><hp:ctrl><hp:bookmark name='KEEP'/></hp:ctrl><hp:t>PRIVATE-TAIL</hp:t></hp:run></hp:p>";
    let raw=fixture::package(body)?;let f=forms(&raw)?;let inv=f.source_review_scope_index(&raw,Default::default())?.scope_inventory()?;
    let start=boundary(&inv.inventory.blocks[0],0);let end=boundary(&inv.inventory.blocks[0],3);
    let c=mask(&f,&raw,Scope::Selection{index_sha256:inv.inventory.index.index_sha256,start:&start,end:&end},all(),Mask::ThreeAsterisksPerTextGroup)?;
    exact(&raw,&c,body,&body.replace(">ABC<",">***<"))?;Ok(())
}
#[test]
fn header_metadata_and_other_parts_are_preserved_not_reported_anonymized()->R{
    let raw=archive::mutate_part(&fixture::package(&para(1,"PRIVATE-BODY"))?,"Contents/header.xml",|t|{
        let xml=PreservingXmlDocument::parse(t.as_bytes())?;let n=xml.elements().iter().find(|n|n.name().local_name()=="style").ok_or("style")?;
        let a=n.attributes().iter().find(|a|a.name().local_name()=="engName").ok_or("engName")?;let mut out=t.to_owned();out.replace_range(a.value_span().start()..a.value_span().end(),"PRIVATE-METADATA");Ok(out)})?;
    assert!(String::from_utf8(archive::read_part(&raw,"Contents/header.xml")?)?.contains("PRIVATE-METADATA"));
    let f=forms(&raw)?;let c=mask(&f,&raw,Scope::Document,all(),Mask::ThreeAsterisksPerTextGroup)?;let out=output(&raw,&c)?;
    assert_eq!(archive::read_part(&out,"Contents/header.xml")?,archive::read_part(&raw,"Contents/header.xml")?);assert!(!section(&out)?.contains("PRIVATE-BODY"));
    assert!(!c.receipt().whole_package_personal_data_removed);Ok(())
}
#[test]
fn public_metadata_has_no_original_text_pieces_or_per_value_source_hashes()->R{
    let raw=fixture::package(&para(1,"PRIVATE-SYNTHETIC-MARKER"))?;let f=forms(&raw)?;let c=mask(&f,&raw,Scope::Document,all(),Mask::ThreeAsterisksPerTextGroup)?;
    let value=String::from_utf8(c.canonical_json()?)?;assert!(!value.contains("PRIVATE-")&&!value.contains("source_span_sha256")&&!value.contains("source_text_sha256")&&!value.contains("pieces"));
    assert!(!format!("{c:?}{:?}",c.receipt()).contains("PRIVATE-"));Ok(())
}
#[test]
fn masking_policy_body_policy_and_scope_are_bound_to_distinct_receipts()->R{
    let raw=fixture::package(&para(1,"ABC"))?;let f=forms(&raw)?;let a=mask(&f,&raw,Scope::Document,all(),Mask::PerOriginalScalarPreserveSlots)?;
    let b=mask(&f,&raw,Scope::Document,all(),Mask::ThreeAsterisksPerTextGroup)?;let c=mask(&f,&raw,Scope::Document,Policy{include_hidden_explanations:false,include_memo_bodies:false},Mask::PerOriginalScalarPreserveSlots)?;
    assert_ne!(a.receipt().request_sha256,b.receipt().request_sha256);assert_ne!(a.receipt().request_sha256,c.receipt().request_sha256);assert_eq!(a.receipt().output_package_sha256,b.receipt().output_package_sha256);Ok(())
}
#[test]
fn server_component_work_output_and_writer_budgets_reject_without_partial_candidates()->R{
    let raw=fixture::package(&para(1,"A*B*C"))?;let f=forms(&raw)?;
    for config in [Config{matches:1,..Default::default()},Config{result_bytes:1,..Default::default()},Config{decomposed_scalars:2,..Default::default()}]{
        assert!(f.lower_personal_info_mask_candidate(&raw,Scope::Document,all(),Mask::PerOriginalScalarPreserveSlots,SourceSearchLimits::new(config)?,Default::default()).is_err());}
    assert!(matches!(f.lower_personal_info_mask_candidate(&raw,Scope::Document,all(),Mask::PerOriginalScalarPreserveSlots,Default::default(),WriterLimits::new(WriterLimitConfig{max_output_bytes:1})?),Err(E::Writer)));Ok(())
}
#[test]
fn exact_receipt_result_limit_is_enforced_independently_of_private_binding_hash()->R{
    let raw=fixture::package(&para(1,"ABC"))?;let f=forms(&raw)?;let c=mask(&f,&raw,Scope::Document,all(),Mask::ThreeAsterisksPerTextGroup)?;let n=c.canonical_json()?.len();
    let exact=f.lower_personal_info_mask_candidate(&raw,Scope::Document,all(),Mask::ThreeAsterisksPerTextGroup,SourceSearchLimits::new(Config{result_bytes:n,..Default::default()})?,Default::default())?;
    assert_eq!(exact.canonical_json()?.len(),n);assert!(matches!(f.lower_personal_info_mask_candidate(&raw,Scope::Document,all(),Mask::ThreeAsterisksPerTextGroup,SourceSearchLimits::new(Config{result_bytes:n-1,..Default::default()})?,Default::default()),Err(E::Limit)));Ok(())
}
#[test]
fn many_mask_components_share_original_part_guard_span_plan_and_source_preservation()->R{
    let raw=fixture::package(&para(1,&"A*".repeat(256)))?;let preserved=raw.clone();let f=forms(&raw)?;let c=mask(&f,&raw,Scope::Document,all(),Mask::PerOriginalScalarPreserveSlots)?;
    exact(&raw,&c,&"A*".repeat(256),&"**".repeat(256))?;assert_eq!(c.receipt().changed_components,256);assert_eq!(c.receipt().changed_parts,1);
    let part=section(&raw)?;let xml=PreservingXmlDocument::parse(part.as_bytes())?;let original=f.source().observe_protection_signals()?;
    assert_eq!(c.receipt().observed_protection_element_visits,original.counts().protection_element_visits+xml.elements().len()*3);assert_eq!(raw,preserved);Ok(())
}
#[test]
fn empty_selection_and_already_masked_text_never_create_a_successful_change()->R{
    let raw=fixture::package(&para(1,"***"))?;let f=forms(&raw)?;for policy in [Mask::PerOriginalScalarPreserveSlots,Mask::ThreeAsterisksPerTextGroup]{assert!(matches!(mask(&f,&raw,Scope::Document,all(),policy),Err(E::NoChange)));}
    let inv=f.source_review_scope_index(&raw,Default::default())?.scope_inventory()?;let at=boundary(&inv.inventory.blocks[0],1);
    assert!(matches!(mask(&f,&raw,Scope::Selection{index_sha256:inv.inventory.index.index_sha256,start:&at,end:&at},all(),Mask::ThreeAsterisksPerTextGroup),Err(E::NoChange)));Ok(())
}
