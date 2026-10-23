//! Source-only direct outline declarations and whole-package coverage; no installed application or Native state.
use super::*;
use hwpx_package::document_import::reference_targets::headings::ImportedReferenceHeadingTargets as Headings;
#[allow(dead_code)]#[path="document_import_catalog_fixture.rs"]mod archive;
const OUTLINE:&str="<hh:heading type='OUTLINE' idRef='7' level='2'/>";
fn para(id:u32,reference:&str,text:&str)->String{format!("<hp:p id='{id}' {reference}><hp:run><hp:t>{text}</hp:t></hp:run></hp:p>")}
fn header(declaration:&str)->String{format!("<hh:head xmlns:hh='http://www.hancom.co.kr/hwpml/2011/head' xmlns:hp='http://www.hancom.co.kr/hwpml/2011/paragraph' xmlns:u='urn:future'><hh:refList><hh:paraProperties><hh:paraPr id='0'>{declaration}</hh:paraPr><hh:paraPr id='1'><hh:heading type='NONE' idRef='0' level='0'/></hh:paraPr></hh:paraProperties></hh:refList></hh:head>")}
fn package(body:&str,head:&str)->Result<Vec<u8>,Box<dyn Error>>{archive::mutate_part(&base::package(body)?,"Contents/header.xml",|_|Ok(head.to_owned()))}
fn standard()->Result<Vec<u8>,Box<dyn Error>>{package(&para(1,"paraPrIDRef='0'","PRIVATE-HEADING-TEXT"),&header(OUTLINE))}
fn imported(bytes:&[u8])->Result<ImportedDocumentStructure,Box<dyn Error>>{structure(bytes,"source-heading")}
fn append(bytes:&[u8],path:&str,body:&str,spine:bool)->Result<Vec<u8>,Box<dyn Error>>{
    use std::io::{Cursor,Read,Write};
    let mut input=zip::ZipArchive::new(Cursor::new(bytes))?;let mut output=zip::ZipWriter::new(Cursor::new(Vec::new()));
    assert!(input.len()<16);for i in 0..input.len(){let mut part=input.by_index(i)?;let name=part.name().to_owned();let mut data=Vec::new();part.read_to_end(&mut data)?;
        if name=="Contents/content.hpf"{let text=String::from_utf8(data)?;let mut text=text.replace("</o:manifest>",&format!("<o:item id='extra' href='{path}' media-type='application/xml'/></o:manifest>"));
            if spine{text=text.replace("</o:spine>","<o:itemref idref='extra'/></o:spine>");}data=text.into_bytes();}
        output.start_file(name,zip::write::SimpleFileOptions::default().compression_method(zip::CompressionMethod::Stored))?;output.write_all(&data)?;}
    output.start_file(path,zip::write::SimpleFileOptions::default().compression_method(zip::CompressionMethod::Stored))?;output.write_all(body.as_bytes())?;Ok(output.finish()?.into_inner())
}
#[test]
fn exact_source_outline_declaration_binds_one_paragraph_without_native_flow_or_number()->TestResult{
    let bytes=standard()?;let source=imported(&bytes)?;let found=Headings::import(&source,limits()?)?;assert_eq!(found.targets().len(),1);let r=found.receipt();
    assert_eq!(r.paragraph_definitions,2);assert_eq!(r.outline_definitions,1);assert_eq!(r.represented_paragraphs,1);assert_eq!(r.heading_targets,1);
    assert!(!r.effective_style_cascade_qualified&&!r.native_number_or_navigation_qualified&&!r.complete_reference_state_qualified);
    let target=&found.targets()[0];assert_eq!(target.target_kind,ReferenceTargetKind::Heading);assert!(target.active&&target.anchor.is_none());assert_eq!(target.target_state_sha256.len(),64);
    let row=&found.observations()[0];assert_eq!(target.logical_target_id,row.paragraph_id);assert_eq!(row.paragraph_property_id,0);assert_eq!(row.source_numbering_id_ref,7);assert_eq!(row.raw_source_level,2);
    assert_eq!(found.verify_source(&bytes)?,*r);Ok(())
}
#[test]
fn none_number_and_bullet_are_not_relabelled_as_heading_targets()->TestResult{
    for kind in ["NONE","NUMBER","BULLET"]{let head=header(&OUTLINE.replace("OUTLINE",kind));let bytes=package(&para(1,"paraPrIDRef='0'","body"),&head)?;
        let source=imported(&bytes)?;let found=Headings::import(&source,limits()?)?;assert!(found.targets().is_empty());assert_eq!(found.receipt().represented_paragraphs,1);}Ok(())
}
#[test]
fn no_direct_reference_or_no_heading_declaration_never_infers_a_named_style_cascade()->TestResult{
    for(reference,declaration,missing)in [("styleIDRef='0'",OUTLINE,1),("paraPrIDRef='0'","",0)]{let bytes=package(&para(1,reference,"body"),&header(declaration))?;
        let source=imported(&bytes)?;let found=Headings::import(&source,limits()?)?;assert!(found.targets().is_empty());assert_eq!(found.receipt().paragraphs_without_direct_property_reference,missing);
        assert!(!found.receipt().effective_style_cascade_qualified);}Ok(())
}
#[test]
fn missing_type_idref_or_level_is_not_defaulted_from_cpp_constructor_values()->TestResult{
    for removed in [" type='OUTLINE'"," idRef='7'"," level='2'"]{let head=header(&OUTLINE.replace(removed,""));let bytes=package(&para(1,"paraPrIDRef='0'","body"),&head)?;
        let source=imported(&bytes)?;assert!(matches!(Headings::import(&source,limits()?),Err(ReferenceTargetImportError::Binding)));}Ok(())
}
#[test]
fn unknown_type_or_invalid_unsigned_declaration_values_fail_closed()->TestResult{
    for(tag,value)in [("OUTLINE","outline"),("OUTLINE","FUTURE"),("idRef='7'","idRef='-1'"),("idRef='7'","idRef='4294967296'"),
        ("level='2'","level='+2'"),("level='2'","level=' 2'"),("level='2'","level=''"),("level='2'","level='4294967296'")]{
        let bytes=package(&para(1,"paraPrIDRef='0'","body"),&header(&OUTLINE.replace(tag,value)))?;let source=imported(&bytes)?;assert!(Headings::import(&source,limits()?).is_err());}Ok(())
}
#[test]
fn raw_uint_level_is_retained_without_claiming_a_native_level_range_or_computed_label()->TestResult{
    let head=header(&OUTLINE.replace("level='2'","level='4294967295'"));let bytes=package(&para(1,"paraPrIDRef='0'","body"),&head)?;
    let source=imported(&bytes)?;let found=Headings::import(&source,limits()?)?;assert_eq!(found.observations()[0].raw_source_level,u32::MAX);assert!(!found.receipt().native_number_or_navigation_qualified);Ok(())
}
#[test]
fn duplicate_decimal_property_ids_and_multiple_heading_children_reject()->TestResult{
    for head in [header(OUTLINE).replace("id='1'","id='00'"),header(&(OUTLINE.to_owned()+OUTLINE))]{let bytes=package(&para(1,"paraPrIDRef='0'","body"),&head)?;
        let source=imported(&bytes)?;assert!(matches!(Headings::import(&source,limits()?),Err(ReferenceTargetImportError::Binding)));}Ok(())
}
#[test]
fn wrong_header_root_or_duplicate_property_containers_reject()->TestResult{
    let good=header(OUTLINE);for head in [good.replace("hh:head","hh:notHead"),good.replace("</hh:refList>","<hh:paraProperties/></hh:refList>")]{
        let bytes=package(&para(1,"paraPrIDRef='0'","body"),&head)?;let source=imported(&bytes)?;assert!(Headings::import(&source,limits()?).is_err());}Ok(())
}
#[test]
fn headings_and_properties_outside_the_official_parent_chain_are_not_partially_collected()->TestResult{
    let good=header(OUTLINE);for head in [good.replace("</hh:head>",&format!("{OUTLINE}</hh:head>")),good.replace("</hh:head>","<hh:paraPr id='8'/></hh:head>")]{
        let bytes=package(&para(1,"paraPrIDRef='0'","body"),&head)?;let source=imported(&bytes)?;assert!(matches!(Headings::import(&source,limits()?),Err(ReferenceTargetImportError::Coverage)));}Ok(())
}
#[test]
fn unknown_attributes_nested_children_comments_or_text_in_heading_reject()->TestResult{
    for declaration in [OUTLINE.replace("/>"," extra='1'/>"),OUTLINE.replace("/>","><u:extension/></hh:heading>"),
        OUTLINE.replace("/>",">TEXT</hh:heading>"),OUTLINE.replace("/>","><!--future--></hh:heading>")]{let bytes=package(&para(1,"paraPrIDRef='0'","body"),&header(&declaration))?;
        let source=imported(&bytes)?;assert!(Headings::import(&source,limits()?).is_err());}Ok(())
}
#[test]
fn whitespace_only_explicit_heading_content_and_xml_namespace_declarations_are_allowed()->TestResult{
    let declaration=OUTLINE.replace("/>"," xmlns:x='urn:future'> \n\t </hh:heading>");let bytes=package(&para(1,"paraPrIDRef='0'","body"),&header(&declaration))?;
    let source=imported(&bytes)?;assert_eq!(Headings::import(&source,limits()?)?.targets().len(),1);Ok(())
}
#[test]
fn foreign_namespace_heading_and_reference_attributes_do_not_become_native_declarations()->TestResult{
    let bytes=package(&para(1,"paraPrIDRef='0'","body"),&header(&OUTLINE.replace("hh:heading","u:heading")))?;
    let source=imported(&bytes)?;assert!(Headings::import(&source,limits()?)?.targets().is_empty());
    let bytes=package(&para(1,"u:paraPrIDRef='0'","body"),&header(OUTLINE))?;
    let error=imported(&bytes).err().ok_or("original paragraph parser must reject foreign reference attribute")?;
    assert!(matches!(error.downcast_ref::<hwpx_package::document_import::structure::StructureImportError>(),Some(hwpx_package::document_import::structure::StructureImportError::Paragraph{..})));Ok(())
}
#[test]
fn dangling_invalid_or_overflowing_paragraph_property_reference_rejects()->TestResult{
    let bytes=package(&para(1,"paraPrIDRef='8'","body"),&header(OUTLINE))?;let source=imported(&bytes)?;
    assert!(matches!(Headings::import(&source,limits()?),Err(ReferenceTargetImportError::Binding)));
    for id in ["-1","+0","4294967296"]{let bytes=package(&para(1,&format!("paraPrIDRef='{id}'"),"body"),&header(OUTLINE))?;
        match imported(&bytes){Ok(source)=>assert!(matches!(Headings::import(&source,limits()?),Err(ReferenceTargetImportError::Binding))),
            Err(error)=>assert!(matches!(error.downcast_ref::<hwpx_package::document_import::structure::StructureImportError>(),Some(hwpx_package::document_import::structure::StructureImportError::Paragraph{..}))),}
    }Ok(())
}
#[test]
fn header_and_opaque_body_outline_paragraphs_cannot_hide_outside_the_represented_graph()->TestResult{
    let p=para(1,"paraPrIDRef='0'","hidden title");let body=para(2,"paraPrIDRef='1'","body");
    for(bytes,_)in [(package(&body,&header(OUTLINE).replace("</hh:head>",&format!("{p}</hh:head>")))?,0),
        (package(&format!("<u:opaque>{p}</u:opaque>{body}"),&header(OUTLINE))?,1)]{let source=imported(&bytes)?;
        assert!(matches!(Headings::import(&source,limits()?),Err(ReferenceTargetImportError::Coverage)));}Ok(())
}
#[test]
fn nonspine_outline_paragraph_and_declaration_are_not_silently_ignored()->TestResult{
    let bytes=standard()?;
    for extra in [format!("<hs:sec xmlns:hs='http://www.hancom.co.kr/hwpml/2011/section' xmlns:hp='http://www.hancom.co.kr/hwpml/2011/paragraph'>{}</hs:sec>",para(9,"paraPrIDRef='0'","title")),header(OUTLINE)]{
        let extended=append(&bytes,"Contents/extra.xml",&extra,false)?;let source=imported(&extended)?;assert!(matches!(Headings::import(&source,limits()?),Err(ReferenceTargetImportError::Coverage)));}Ok(())
}
#[test]
fn identical_local_paragraph_ids_in_two_spine_parts_keep_distinct_source_targets()->TestResult{
    let bytes=standard()?;let extra=format!("<hs:sec xmlns:hs='http://www.hancom.co.kr/hwpml/2011/section' xmlns:hp='http://www.hancom.co.kr/hwpml/2011/paragraph'>{}</hs:sec>",para(1,"paraPrIDRef='0'","title"));
    let bytes=append(&bytes,"Contents/section1.xml",&extra,true)?;let source=imported(&bytes)?;let found=Headings::import(&source,limits()?)?;
    assert_eq!(found.targets().len(),2);assert_ne!(found.targets()[0].logical_target_id,found.targets()[1].logical_target_id);assert_ne!(found.observations()[0].paragraph_anchor_sha256,found.observations()[1].paragraph_anchor_sha256);Ok(())
}
#[test]
fn source_document_and_changed_package_cannot_rebind_a_retained_heading_inventory()->TestResult{
    let bytes=standard()?;let source=imported(&bytes)?;let found=Headings::import(&source,limits()?)?;let other=structure(&bytes,"foreign-document")?;let foreign=Headings::import(&other,limits()?)?;
    assert_ne!(found.targets()[0].logical_target_id,foreign.targets()[0].logical_target_id);assert_ne!(found.receipt().inventory_sha256,foreign.receipt().inventory_sha256);
    let changed=package(&para(1,"paraPrIDRef='0'","changed"),&header(OUTLINE))?;assert!(matches!(found.verify_source(&changed),Err(ReferenceTargetImportError::Binding)));Ok(())
}
#[test]
fn heading_level_and_definition_changes_are_bound_to_target_state_not_just_paragraph_id()->TestResult{
    let a=standard()?;let b=package(&para(1,"paraPrIDRef='0'","PRIVATE-HEADING-TEXT"),&header(&OUTLINE.replace("level='2'","level='3'")))?;
    let sa=imported(&a)?;let sb=imported(&b)?;let a=Headings::import(&sa,limits()?)?;let b=Headings::import(&sb,limits()?)?;
    assert_ne!(a.targets()[0].target_state_sha256,b.targets()[0].target_state_sha256);assert_ne!(a.observations()[0].heading_declaration_sha256,b.observations()[0].heading_declaration_sha256);Ok(())
}
#[test]
fn metadata_and_debug_never_contain_private_title_text_or_raw_xml()->TestResult{
    let bytes=standard()?;let source=imported(&bytes)?;let found=Headings::import(&source,limits()?)?;
    for text in [format!("{found:?}"),String::from_utf8(found.canonical_json()?)?]{assert!(!text.contains("PRIVATE-")&&!text.contains("<hp:")&&!text.contains("<hh:"));}Ok(())
}
#[test]
fn header_definition_and_represented_paragraph_counts_respect_caller_limits()->TestResult{
    let bytes=standard()?;let source=imported(&bytes)?;let limit=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig{items_per_kind:1,..Default::default()})?;
    assert!(matches!(Headings::import(&source,limit),Err(ReferenceTargetImportError::Limit)));
    let head=header(OUTLINE).replace("<hh:paraPr id='1'><hh:heading type='NONE' idRef='0' level='0'/></hh:paraPr>","");
    let bytes=package(&(para(1,"paraPrIDRef='0'","one")+&para(2,"paraPrIDRef='0'","two")),&head)?;let source=imported(&bytes)?;
    assert!(matches!(Headings::import(&source,limit),Err(ReferenceTargetImportError::Limit)));Ok(())
}
#[test]
fn entire_metadata_envelope_byte_limit_is_exact_and_never_truncated()->TestResult{
    let bytes=standard()?;let source=imported(&bytes)?;let found=Headings::import(&source,limits()?)?;let n=found.canonical_json()?.len();
    let exact=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig{input_bytes:1,output_bytes:n,..Default::default()})?;
    assert_eq!(Headings::import(&source,exact)?.canonical_json()?.len(),n);
    let short=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig{input_bytes:1,output_bytes:n-1,..Default::default()})?;assert!(matches!(Headings::import(&source,short),Err(ReferenceTargetImportError::Limit)));Ok(())
}
#[test]
fn larger_outline_inventory_shares_one_definition_and_preserves_source()->TestResult{
    let body=(0..128).map(|i|para(i,"paraPrIDRef='0'","title")).collect::<String>();let bytes=package(&body,&header(OUTLINE))?;let original=Sha256::digest(&bytes);
    let source=imported(&bytes)?;let found=Headings::import(&source,limits()?)?;assert_eq!(found.targets().len(),128);assert_eq!(found.receipt().represented_paragraphs,128);
    assert_eq!(found.receipt().outline_definitions,1);assert_eq!(Sha256::digest(&bytes),original);found.verify_source(&bytes)?;Ok(())
}

#[test]
fn partial_assessment_legacy_header_is_unavailable_not_confirmed_empty()->TestResult{
    let bytes=base::package(&para(1,"","body"))?;let source=imported(&bytes)?;
    assert!(Headings::for_partial_source_assessment(&source,limits()?)?.is_none());
    assert!(matches!(Headings::import(&source,limits()?),Err(ReferenceTargetImportError::Binding)));Ok(())
}
#[test]
fn partial_assessment_keeps_unobserved_header_model_distinct_from_explicit_none()->TestResult{
    let bytes=package(&para(1,"paraPrIDRef='0'","body"),&header(""))?;let source=imported(&bytes)?;
    // The second property still has an explicit NONE heading declaration, so the model is observable.
    let observed=Headings::for_partial_source_assessment(&source,limits()?)?.ok_or("explicit NONE model")?;assert!(observed.targets().is_empty());
    let bytes=package(&para(1,"paraPrIDRef='0'","body"),&header("").replace("<hh:heading type='NONE' idRef='0' level='0'/>",""))?;let source=imported(&bytes)?;
    assert!(Headings::for_partial_source_assessment(&source,limits()?)?.is_none());Ok(())
}
#[test]
fn partial_assessment_observable_outline_uses_the_exact_strict_inventory()->TestResult{
    let bytes=standard()?;let source=imported(&bytes)?;let strict=Headings::import(&source,limits()?)?;
    let observed=Headings::for_partial_source_assessment(&source,limits()?)?.ok_or("outline model")?;
    assert_eq!(strict.receipt(),observed.receipt());assert_eq!(strict.targets(),observed.targets());Ok(())
}
#[test]
fn partial_assessment_never_swallows_invalid_explicit_heading_values()->TestResult{
    let bytes=package(&para(1,"paraPrIDRef='0'","body"),&header(&OUTLINE.replace(" level='2'","")))?;let source=imported(&bytes)?;
    assert!(matches!(Headings::for_partial_source_assessment(&source,limits()?),Err(ReferenceTargetImportError::Binding)));Ok(())
}
#[test]
fn partial_assessment_marker_outside_header_with_legacy_root_is_not_unavailable()->TestResult{
    let body=format!("<u:extension xmlns:hh='http://www.hancom.co.kr/hwpml/2011/head'>{OUTLINE}</u:extension>{}",para(1,"","body"));
    let bytes=base::package(&body)?;let source=imported(&bytes)?;assert!(Headings::for_partial_source_assessment(&source,limits()?).is_err());Ok(())
}
#[test]
fn partial_assessment_preserves_whole_source_heading_coverage_failure()->TestResult{
    let body=format!("<u:opaque>{}</u:opaque>",para(1,"paraPrIDRef='0'","hidden"));let bytes=package(&body,&header(OUTLINE))?;let source=imported(&bytes)?;
    assert!(matches!(Headings::for_partial_source_assessment(&source,limits()?),Err(ReferenceTargetImportError::Coverage)));Ok(())
}
#[test]
fn partial_assessment_keeps_caller_limits_and_does_not_reclassify_an_overflow_as_unavailable()->TestResult{
    let bytes=standard()?;let source=imported(&bytes)?;let bounded=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig{items_per_kind:1,..Default::default()})?;
    assert!(matches!(Headings::for_partial_source_assessment(&source,bounded),Err(ReferenceTargetImportError::Limit)));Ok(())
}
