use hwpx_package::{BoundedZipReader,WriterLimits,WriterLimitConfig,NumberFormat,
    document_import::{ImportedSourcePackage,forms::ImportedDocumentForms,search::{SourceSearchLimits,SourceSearchLimitConfig,
        selector::{SourceIndexScopeSelector as Scope,SourceIndexBoundary as Boundary},reviews::SourceReviewTextPolicy as Body,
        inspection::SourceControlKind as Kind,replacement::{SourceLiteralReplacementError as E,atoms::number_controls::{SourceNumberControlCandidate as Candidate,SourceNumberControlError as C,SOURCE_NUMBER_CONTROL_PROFILE}}},
        structure::{caption_numbering_sequence::NativeNumberFormatReplacement as Format,caption_text::CaptionTextOutputError as Stream}}};
use domain_ir::{DocumentId,ReferenceAuxiliaryLimits,ReferenceAuxiliaryLimitConfig};
use sha2::{Digest as _,Sha256};
use std::{error::Error,io::{Cursor,Write}};
use zip::{ZipWriter,CompressionMethod,write::SimpleFileOptions};
#[allow(dead_code)] #[path="support/search_definition_fixture.rs"] mod fixture;
#[allow(dead_code)] #[path="support/review_scope_fixture.rs"] mod review;
#[allow(dead_code)] #[path="support/document_import_review_assembly_fixture.rs"] mod assembly;
type TestResult=Result<(),Box<dyn Error>>;
const STYLE:&str="<hp:autoNumFormat type='DIGIT' userChar='' prefixChar='' suffixChar='' supscript='0'/>";
fn control(tag:&str,n:i32)->String{format!("<hp:ctrl><hp:{tag} num='{n}' numType='PICTURE'>{STYLE}</hp:{tag}></hp:ctrl>")}
fn p(id:u32,body:&str)->String{format!("<hp:p id='{id}' paraPrIDRef='0' styleIDRef='0'><hp:run charPrIDRef='0'>{body}</hp:run></hp:p>")}
fn body()->Body{Body{include_hidden_explanations:true,include_memo_bodies:true}}
fn limits()->Result<ReferenceAuxiliaryLimits,Box<dyn Error>>{Ok(ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig::default())?)}
fn forms(raw:&[u8])->Result<ImportedDocumentForms,Box<dyn Error>>{Ok(ImportedDocumentForms::import(ImportedSourcePackage::import(raw,DocumentId::parse("number-control")?,Sha256::digest(raw).into(),Default::default())?)?)}
fn replace(f:&ImportedDocumentForms,raw:&[u8],scope:Scope<'_>,policy:Body,kind:Kind,n:i32,format:Format<'_>)->Result<Candidate,C>{
    f.lower_review_selector_number_control_candidate(raw,scope,policy,kind,4096,n,format,Default::default(),limits().map_err(|_|C::Output(E::Limit))?,Default::default())}
fn parts(raw:&[u8])->Result<Vec<(String,Vec<u8>)>,Box<dyn Error>>{let mut r=BoundedZipReader::open(Cursor::new(raw),Default::default())?;let mut out=Vec::new();
    for i in 0..r.entries().len(){out.push((r.entries()[i].path.as_str().to_owned(),r.read_entry(i)?));}Ok(out)}
fn section(raw:&[u8])->Result<String,Box<dyn Error>>{Ok(String::from_utf8(parts(raw)?.into_iter().find(|(p,_)|p=="Contents/section0.xml").ok_or("section")?.1)?)}
fn output(raw:&[u8],c:&Candidate)->Result<Vec<u8>,Box<dyn Error>>{let out=c.with_verified_bytes(<[u8]>::to_vec)?;let r=c.receipt();
    assert_eq!(r.profile,SOURCE_NUMBER_CONTROL_PROFILE);assert!(r.whole_original_control_ranges_verified&&r.all_unselected_control_values_and_reference_bytes_preserved);
    assert!(!r.native_recalculation_full_search_service_or_execution_authority&&!r.stream.execution_publication_authority);
    assert!(r.stream.content.output.outside_selected_edits_exact&&r.stream.number_sequence.complete_original_control_order_checked&&r.stream.number_sequence.all_requested_values_read_back);
    let before=parts(raw)?;let after=parts(&out)?;assert_eq!(before.len(),after.len());for((path,a),(other,b))in before.iter().zip(&after){assert_eq!(path,other);if !path.starts_with("Contents/section"){assert_eq!(a,b);}}
    assert_eq!(r.changed_controls,r.changes.len());Ok(out)}
fn exact(raw:&[u8],c:&Candidate,old:&str,new:&str)->TestResult{assert_eq!(section(&output(raw,c)?)?,section(raw)?.replace(old,new));Ok(())}
fn plain()->Result<Vec<u8>,Box<dyn Error>>{fixture::package(&p(1,&format!("<hp:t>A&#38;</hp:t>{}<hp:t>B</hp:t>{}<hp:t>C</hp:t>",control("autoNum",2),control("newNum",3))))}
fn inventory(f:&ImportedDocumentForms,raw:&[u8])->Result<hwpx_package::document_import::search::reviews::selector::SourceReviewScopeInventory,Box<dyn Error>>{
    Ok(f.source_review_scope_index(raw,Default::default())?.scope_inventory()?)
}
#[test]
fn number_control_source_auto_values_preserve_restart_text_entities_style_and_package_parts()->TestResult{
    let raw=plain()?;let f=forms(&raw)?;let c=replace(&f,&raw,Scope::Document,body(),Kind::AutoNumber,9,Format::Preserve)?;
    exact(&raw,&c,"autoNum num='2'","autoNum num='9'")?;assert_eq!((c.receipt().selected_controls,c.receipt().changed_controls),(1,1));Ok(())
}
#[test]
fn number_control_source_restart_values_preserve_auto_and_categories()->TestResult{
    let raw=plain()?;let f=forms(&raw)?;let c=replace(&f,&raw,Scope::Document,body(),Kind::NewNumber,17,Format::Preserve)?;
    exact(&raw,&c,"newNum num='3'","newNum num='17'")?;assert_eq!(c.receipt().changes[0].changed_attributes,1);Ok(())
}
#[test]
fn number_control_source_typed_format_escaped_affixes_and_unsigned_boolean_read_back()->TestResult{
    let raw=plain()?;let f=forms(&raw)?;let c=replace(&f,&raw,Scope::Document,body(),Kind::AutoNumber,5,
        Format::Replace{format:NumberFormat::RomanCapital,user_character:"",prefix:"private<&'😀",suffix:"&tail",superscript:true})?;
    let out=section(&output(&raw,&c)?)?;assert!(out.contains("type='ROMAN_CAPITAL'")&&out.contains("prefixChar='private&lt;&amp;&apos;😀'")&&out.contains("supscript='1'"));
    assert!(out.contains(&control("newNum",3)));assert_eq!(c.receipt().changes[0].changed_attributes,5);Ok(())
}
#[test]
fn number_control_source_document_section_node_and_selection_are_exact()->TestResult{
    let raw=fixture::package(&(p(1,&format!("<hp:t>A</hp:t>{}<hp:t>B</hp:t>",control("autoNum",2)))+&p(2,&format!("<hp:t>C</hp:t>{}<hp:t>D</hp:t>",control("autoNum",3)))))?;
    let f=forms(&raw)?;let inv=inventory(&f,&raw)?;let b=&inv.inventory.blocks[0];let node=inv.inventory.nodes.iter().find(|n|n.source_handle==b.paragraph_handle).ok_or("node")?.node_id.clone();
    let start=Boundary{paragraph_handle:b.paragraph_handle.clone(),block_index:0,normalized_scalar:0};
    let last=inv.inventory.blocks.iter().filter(|n|n.paragraph_handle==b.paragraph_handle).last().ok_or("last original block")?;
    let end=Boundary{paragraph_handle:last.paragraph_handle.clone(),block_index:last.block_index,normalized_scalar:last.normalized_scalars};
    for(scope,count)in[(Scope::Document,2),(Scope::Section(&inv.inventory.section_ids),2),(Scope::NodeSet(&[node][..]),1),
        (Scope::Selection{index_sha256:inv.inventory.index.index_sha256,start:&start,end:&end},1)]{
        let c=replace(&f,&raw,scope,body(),Kind::AutoNumber,9,Format::Preserve)?;assert_eq!(c.receipt().selected_controls,count);let out=section(&output(&raw,&c)?)?;
        assert!(out.contains("autoNum num='9'"));assert_eq!(out.contains("autoNum num='3'"),count==1);
    }Ok(())
}
#[test]
fn number_control_source_empty_and_neighbor_only_selection_do_not_widen()->TestResult{
    let raw=plain()?;let f=forms(&raw)?;let inv=inventory(&f,&raw)?;let b=&inv.inventory.blocks[0];
    for(a,z)in[(0,1),(1,1)]{let start=Boundary{paragraph_handle:b.paragraph_handle.clone(),block_index:0,normalized_scalar:a};let end=Boundary{normalized_scalar:z,..start.clone()};
        assert!(matches!(replace(&f,&raw,Scope::Selection{index_sha256:inv.inventory.index.index_sha256,start:&start,end:&end},body(),Kind::AutoNumber,9,Format::Preserve),Err(C::Output(E::NoMatches))));}Ok(())
}
#[test]
fn number_control_source_noop_subset_keeps_original_lexemes_and_source_order()->TestResult{
    let a=control("autoNum",9).replace("num='9'","num='009'");let b=control("autoNum",2);let raw=fixture::package(&p(1,&format!("<hp:t>A</hp:t>{a}<hp:t>B</hp:t>{b}<hp:t>C</hp:t>")))?;
    let f=forms(&raw)?;let c=replace(&f,&raw,Scope::Document,body(),Kind::AutoNumber,9,Format::Preserve)?;exact(&raw,&c,"autoNum num='2'","autoNum num='9'")?;
    assert_eq!((c.receipt().selected_controls,c.receipt().changed_controls),(2,1));let search=&c.receipt().search;assert_eq!(c.receipt().changes[0].source_control_anchor,search.controls()[1].control_anchor);Ok(())
}
#[test]
fn number_control_source_all_noop_is_not_a_successful_empty_change()->TestResult{
    let raw=plain()?;let f=forms(&raw)?;assert!(matches!(replace(&f,&raw,Scope::Document,body(),Kind::AutoNumber,2,Format::Preserve),Err(C::Stream(Stream::NoChange))));Ok(())
}
#[test]
fn number_control_source_other_kinds_reject_before_whole_source_reconstruction()->TestResult{
    let raw=plain()?;let f=forms(&raw)?;for kind in[Kind::Tab,Kind::LineBreak,Kind::FieldBegin,Kind::Footnote,Kind::Bookmark,Kind::Table,Kind::SectionProperties]{
        assert!(matches!(replace(&f,b"invalid source",Scope::Document,body(),kind,9,Format::Preserve),Err(C::UnsupportedKind)));}Ok(())
}
#[test]
fn number_control_source_bad_output_values_reject_before_source_access()->TestResult{
    let raw=plain()?;let f=forms(&raw)?;for text in["bad\u{0}","bad\u{1}"]{assert!(matches!(replace(&f,b"invalid source",Scope::Document,body(),Kind::AutoNumber,9,
        Format::Replace{format:NumberFormat::Digit,user_character:"",prefix:text,suffix:"",superscript:false}),Err(C::Output(E::Value))));}Ok(())
}
#[test]
fn number_control_source_fresh_bytes_and_foreign_model_proof_cannot_be_reused()->TestResult{
    let raw=plain()?;let f=forms(&raw)?;let other=forms(&raw)?;let proof=f.reconstruct_source_for_verification(&raw)?;
    assert!(matches!(replace(&f,b"changed source",Scope::Document,body(),Kind::AutoNumber,9,Format::Preserve),Err(C::Output(E::Source))));
    assert!(matches!(proof.lower_review_selector_number_control_candidate(&other,Scope::Document,body(),Kind::AutoNumber,10,9,Format::Preserve,Default::default(),limits()?,Default::default()),Err(C::Output(E::Source))));Ok(())
}
#[test]
fn number_control_source_stale_index_and_foreign_selector_reject()->TestResult{
    let raw=plain()?;let f=forms(&raw)?;let inv=inventory(&f,&raw)?;let b=&inv.inventory.blocks[0];let start=Boundary{paragraph_handle:b.paragraph_handle.clone(),block_index:0,normalized_scalar:0};let end=Boundary{normalized_scalar:2,..start.clone()};
    assert!(replace(&f,&raw,Scope::Selection{index_sha256:[0;32],start:&start,end:&end},body(),Kind::AutoNumber,9,Format::Preserve).is_err());
    let bad=[domain_ir::LogicalId::parse("foreign-node")?];assert!(replace(&f,&raw,Scope::NodeSet(&bad),body(),Kind::AutoNumber,9,Format::Preserve).is_err());Ok(())
}
#[test]
fn number_control_source_lock_and_tracking_reject_even_semantic_noop()->TestResult{
    for body_text in[p(1,&format!("<hp:t>A</hp:t>{}<hp:t>B</hp:t>",control("autoNum",2))).replace("<hp:run ","<hp:run charTcId='7' "),
        p(1,&format!("<hp:t>A</hp:t>{}<hp:t>B</hp:t>",control("autoNum",2).replace("<hp:autoNum ","<hp:autoNum lock='1' ")))]{
        let raw=fixture::package(&body_text)?;let f=forms(&raw)?;assert!(matches!(replace(&f,&raw,Scope::Document,body(),Kind::AutoNumber,2,Format::Preserve),Err(C::Output(E::Protection))));}Ok(())
}
#[test]
fn number_control_source_cached_field_control_rejects_before_noop_elimination()->TestResult{
    let field=format!("<hp:ctrl><hp:fieldBegin id='17' type='HYPERLINK' editable='1'><hp:parameters cnt='0'/></hp:fieldBegin></hp:ctrl><hp:t>A</hp:t>{}<hp:t>B</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='17'/></hp:ctrl>",control("autoNum",2));
    let raw=fixture::package(&p(1,&field))?;let f=forms(&raw)?;assert!(matches!(replace(&f,&raw,Scope::Document,body(),Kind::AutoNumber,2,Format::Preserve),Err(C::Output(E::FieldContent))));Ok(())
}
#[test]
fn number_control_source_review_exclusion_precedes_match_limit()->TestResult{
    let body_text=review::body().replace("<hp:t>BODY K K</hp:t>",&format!("<hp:t>BODY K K</hp:t>{}",control("autoNum",2)))
        .replace("<hp:t>HIDDEN K K<hp:lineBreak/></hp:t>",&format!("<hp:t>HIDDEN K K<hp:lineBreak/></hp:t>{}",control("autoNum",3)));
    let raw=fixture::package(&body_text)?;let f=forms(&raw)?;let c=f.lower_review_selector_number_control_candidate(&raw,Scope::Document,Body{include_hidden_explanations:false,include_memo_bodies:false},Kind::AutoNumber,1,9,Format::Preserve,Default::default(),limits()?,Default::default())?;
    assert_eq!(c.receipt().selected_controls,1);let out=section(&output(&raw,&c)?)?;assert!(out.contains("autoNum num='9'")&&out.contains("autoNum num='3'"));Ok(())
}
#[test]
fn number_control_source_missing_format_is_preserved_but_cannot_be_fabricated()->TestResult{
    let raw=fixture::package(&p(1,"<hp:t>A</hp:t><hp:ctrl><hp:newNum num='3' numType='PICTURE'/></hp:ctrl><hp:t>B</hp:t>"))?;let f=forms(&raw)?;
    exact(&raw,&replace(&f,&raw,Scope::Document,body(),Kind::NewNumber,9,Format::Preserve)?,"newNum num='3'","newNum num='9'")?;
    assert!(matches!(replace(&f,&raw,Scope::Document,body(),Kind::NewNumber,9,Format::Replace{format:NumberFormat::Digit,user_character:"",prefix:"",suffix:"",superscript:false}),Err(C::Stream(Stream::Selection))));Ok(())
}
#[test]
fn number_control_source_original_zero_negative_and_full_i32_values_are_not_recalculated()->TestResult{
    let raw=plain()?;let f=forms(&raw)?;for n in[0,-1,i32::MIN,i32::MAX]{let c=replace(&f,&raw,Scope::Document,body(),Kind::AutoNumber,n,Format::Preserve)?;
        exact(&raw,&c,"autoNum num='2'",&format!("autoNum num='{n}'"))?;}Ok(())
}
#[test]
fn number_control_source_namespace_alias_and_default_preserve_exact_original_spelling()->TestResult{
    let raw=plain()?;for default in[false,true]{let mut w=ZipWriter::new(Cursor::new(Vec::new()));for(name,data)in parts(&raw)?{w.start_file(&name,SimpleFileOptions::default().compression_method(CompressionMethod::Stored))?;
        let data=if name=="Contents/section0.xml"{let s=String::from_utf8(data)?;if default{s.replace("xmlns:hp=","xmlns=").replace("hp:","")}else{s.replace("xmlns:hp=","xmlns:q=").replace("hp:","q:")}.into_bytes()}else{data};w.write_all(&data)?;}
        let input=w.finish()?.into_inner();let f=forms(&input)?;let c=replace(&f,&input,Scope::Document,body(),Kind::AutoNumber,9,Format::Preserve)?;exact(&input,&c,"autoNum num='2'","autoNum num='9'")?;}Ok(())
}
#[test]
fn number_control_source_match_response_format_and_writer_limits_do_not_return_partial_output()->TestResult{
    let raw=plain()?;let f=forms(&raw)?;
    assert!(f.lower_review_selector_number_control_candidate(&raw,Scope::Document,body(),Kind::AutoNumber,0,9,Format::Preserve,Default::default(),limits()?,Default::default()).is_err());
    let small=SourceSearchLimits::new(SourceSearchLimitConfig{result_bytes:1,..Default::default()})?;
    assert!(f.lower_review_selector_number_control_candidate(&raw,Scope::Document,body(),Kind::AutoNumber,2,9,Format::Preserve,small,limits()?,Default::default()).is_err());
    let tight=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig{text_bytes:1,..Default::default()})?;
    assert!(matches!(f.lower_review_selector_number_control_candidate(b"invalid",Scope::Document,body(),Kind::AutoNumber,2,9,Format::Replace{format:NumberFormat::Digit,user_character:"",prefix:"too long",suffix:"",superscript:false},Default::default(),tight,Default::default()),Err(C::Output(E::Limit))));
    let writer=WriterLimits::new(WriterLimitConfig{max_output_bytes:1,..Default::default()})?;
    assert!(f.lower_review_selector_number_control_candidate(&raw,Scope::Document,body(),Kind::AutoNumber,2,9,Format::Preserve,Default::default(),limits()?,writer).is_err());Ok(())
}
#[test]
fn number_control_source_many_controls_share_one_part_guard_and_complete_order()->TestResult{
    let mut run=String::from("<hp:t>A</hp:t>");for _ in 0..256{run.push_str(&control("autoNum",2));}run.push_str("<hp:t>B</hp:t>");
    let raw=fixture::package(&p(1,&run))?;let f=forms(&raw)?;let c=replace(&f,&raw,Scope::Document,body(),Kind::AutoNumber,9,Format::Preserve)?;
    assert_eq!((c.receipt().selected_controls,c.receipt().changed_controls,c.receipt().observed_protection_parts),(256,256,1));
    let xml=f.source().parts().iter().find(|p|p.path().as_str()=="Contents/section0.xml").and_then(|p|p.xml()).ok_or("xml")?;
    assert_eq!(c.receipt().observed_protection_element_visits,xml.elements().len()*4);exact(&raw,&c,"autoNum num='2'","autoNum num='9'")?;Ok(())
}
#[test]
fn number_control_source_fingerprints_bind_kind_value_format_scope_and_hide_plaintext()->TestResult{
    let raw=plain()?;let f=forms(&raw)?;let a=replace(&f,&raw,Scope::Document,body(),Kind::AutoNumber,9,Format::Preserve)?;
    let b=replace(&f,&raw,Scope::Document,body(),Kind::AutoNumber,10,Format::Preserve)?;let c=replace(&f,&raw,Scope::Document,body(),Kind::NewNumber,9,Format::Preserve)?;
    let d=replace(&f,&raw,Scope::Document,body(),Kind::AutoNumber,9,Format::Replace{format:NumberFormat::Digit,user_character:"",prefix:"private-prefix",suffix:"",superscript:false})?;
    for other in[&b,&c,&d]{assert_ne!(a.receipt().request_sha256,other.receipt().request_sha256);}
    assert!(!format!("{d:?}{}",serde_json::to_string(d.receipt())?).contains("private-prefix"));assert_eq!(f.reconstruct_source_for_verification(&raw)?.receipt(),f.receipt());Ok(())
}
#[test]
fn number_control_source_review_failure_is_numbering_coverage_not_policy_or_resource_stop()->TestResult{
    use hwpx_package::document_import::reference_targets::{caption_source_state::ImportedCaptionSourceState,numbering::CaptionNumberingImportError};
    let base=review::body().replace("<hp:t>BODY K K</hp:t>",&format!("<hp:t>BODY K K</hp:t>{}",control("autoNum",2)));
    let raw=fixture::package(&base)?;let f=forms(&raw)?;
    assert!(ImportedCaptionSourceState::import(f.body_structure(),limits()?).is_ok());
    let hidden=base.replace("<hp:t>HIDDEN K K<hp:lineBreak/></hp:t>",&format!("<hp:t>HIDDEN K K<hp:lineBreak/></hp:t>{}",control("autoNum",3)));
    let raw=fixture::package(&hidden)?;let f=forms(&raw)?;let index=f.source_review_scope_index(&raw,Default::default())?;
    let selected=index.find_control(Scope::Document,Body{include_hidden_explanations:false,include_memo_bodies:false},Kind::AutoNumber,1)?;
    assert_eq!(selected.controls().len(),1);
    assert!(matches!(ImportedCaptionSourceState::import(f.body_structure(),limits()?),Err(CaptionNumberingImportError::Coverage)));
    // The original positive review test remains required and failing until the source/backend
    // join admits these exact observed paragraphs. This diagnosis never replaces that test.
    Ok(())
}
#[path="support/number_control_review_admission.rs"] mod review_admission;
