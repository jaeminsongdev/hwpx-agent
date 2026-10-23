// Actual versioned source API/CLI integration; source presence only, not Native headings or completed validation.
use super::*;
use hwpx_package::document_import::reference_targets::headings::ImportedReferenceHeadingTargets as Headings;
const OUTLINE:&str="<hh:heading type='OUTLINE' idRef='0' level='2'/>";
fn paragraph(id:u32,reference:&str,text:&str)->String{format!("<hp:p id='{id}' {reference}><hp:run>{text}</hp:run></hp:p>")}
fn head(kind:&str)->String{format!("<hh:head xmlns:hh='http://www.hancom.co.kr/hwpml/2011/head' xmlns:hp='http://www.hancom.co.kr/hwpml/2011/paragraph' xmlns:u='urn:future'><hh:refList><hh:paraProperties><hh:paraPr id='0'>{kind}</hh:paraPr></hh:paraProperties></hh:refList></hh:head>")}
fn rewrite(bytes:&[u8],header:&str,reference_sections:bool)->Result<Vec<u8>,Box<dyn Error>>{
    use std::io::{Cursor,Read,Write};let mut input=zip::ZipArchive::new(Cursor::new(bytes))?;let mut output=zip::ZipWriter::new(Cursor::new(Vec::new()));
    for i in 0..input.len(){let mut part=input.by_index(i)?;let name=part.name().to_owned();let mut data=Vec::new();part.read_to_end(&mut data)?;
        if name=="Contents/header.xml"{data=header.as_bytes().to_vec();}
        if reference_sections&&name.starts_with("Contents/section"){data=String::from_utf8(data)?.replace("<hp:p ","<hp:p paraPrIDRef='0' ").into_bytes();}
        output.start_file(name,zip::write::SimpleFileOptions::default().compression_method(zip::CompressionMethod::Stored))?;output.write_all(&data)?;}
    Ok(output.finish()?.into_inner())
}
fn bundle(body:&str,header:&str)->Result<Vec<u8>,Box<dyn Error>>{rewrite(&fixture::package(body)?,header,false)}
fn heading_package()->Result<Vec<u8>,Box<dyn Error>>{bundle(&paragraph(1,"paraPrIDRef='0'","<hp:t>PRIVATE-OUTLINE-TITLE</hp:t>"),&head(OUTLINE))}
#[test]
fn v13_api_joins_exact_original_heading_receipt_and_targets_without_native_authority()->TestResult{
    let bytes=heading_package()?;let forms=fixture::forms(&bytes,"reference-product")?;let direct=Headings::import(forms.body_structure(),limits()?)?;let result=assess(&bytes)?;
    assert_eq!(result.heading_target_receipt(),Some(direct.receipt()));assert_eq!(result.targets(),direct.targets());assert_eq!(result.heading_target_receipt().ok_or("heading")?.heading_targets,1);
    assert_eq!(result.status(),ReferenceSourceStatus::Incomplete);assert!(result.validation_report().is_none());let value:Value=serde_json::from_slice(&result.canonical_json(limits()?)?)?;
    assert_eq!(value["schema_version"],"hwpx-agent.product.reference-source-assessment/v14");assert_eq!(value["unresolved"].as_array().ok_or("unresolved")?.len(),4);
    assert_eq!(value["heading_target_import"]["native_number_or_navigation_qualified"],false);assert_eq!(value["heading_target_import"]["effective_style_cascade_qualified"],false);Ok(())
}
#[test]
fn v13_cli_matches_actual_heading_api_and_exit3_preserving_original_bytes()->TestResult{
    let bytes=heading_package()?;let report=assess(&bytes)?;let temp=tempfile::tempdir()?;let path=temp.path().join("source-headings.hwpx");fs::write(&path,&bytes)?;let sha=hex::encode(Sha256::digest(&bytes));
    let output=cli([OsStr::new("reference-source"),OsStr::new("reference-product"),OsStr::new(&sha),path.as_os_str()])?;assert_eq!(output.status.code(),Some(3));assert!(output.stderr.is_empty());
    let value:Value=serde_json::from_slice(&output.stdout)?;assert_eq!(value,serde_json::from_slice::<Value>(&report.canonical_json(limits()?)?)?);
    assert_eq!(value["heading_target_import"]["heading_targets"],1);assert!(value["validation_report"].is_null());assert_eq!(fs::read(path)?,bytes);Ok(())
}
#[test]
fn legacy_partial_header_reports_unavailable_not_a_fabricated_empty_heading_receipt()->TestResult{
    let bytes=package("<hp:t>private legacy body</hp:t>")?;let report=assess(&bytes)?;assert!(report.heading_target_receipt().is_none());
    let value:Value=serde_json::from_slice(&report.canonical_json(limits()?)?)?;assert!(value.as_object().ok_or("object")?.contains_key("heading_target_import"));assert!(value["heading_target_import"].is_null());
    assert_eq!(value["status"],"incomplete");assert_eq!(value["unresolved"].as_array().ok_or("unresolved")?.len(),4);assert!(value["validation_report"].is_null());Ok(())
}
#[test]
fn explicit_none_declaration_has_a_real_zero_count_receipt_not_unavailable()->TestResult{
    let bytes=bundle(&paragraph(1,"paraPrIDRef='0'","<hp:t>body</hp:t>"),&head(&OUTLINE.replace("OUTLINE","NONE")))?;
    let report=assess(&bytes)?;assert_eq!(report.heading_target_receipt().ok_or("observed NONE")?.heading_targets,0);assert!(report.targets().is_empty());
    assert!(!report.heading_target_receipt().ok_or("observed NONE")?.complete_reference_state_qualified);Ok(())
}
#[test]
fn malformed_observed_heading_is_not_suppressed_as_unavailable()->TestResult{
    for declaration in [OUTLINE.replace(" level='2'",""),OUTLINE.replace("OUTLINE","FUTURE"),OUTLINE.replace("idRef='0'","idRef='-1'")]{
        let bytes=bundle(&paragraph(1,"paraPrIDRef='0'","<hp:t>body</hp:t>"),&head(&declaration))?;
        assert_eq!(ReferenceValidationProductOperation::assess_package_source(&bytes,DocumentId::parse("reference-product")?,Sha256::digest(&bytes).into(),SourceImportLimits::default(),limits()?),Err(ReferenceSourceError::Binding));}Ok(())
}
#[test]
fn observed_heading_marker_in_unsupported_legacy_header_never_becomes_a_null_success()->TestResult{
    let body=format!("<u:extension xmlns:hh='http://www.hancom.co.kr/hwpml/2011/head'>{OUTLINE}</u:extension>");let bytes=fixture::package(&body)?;
    assert!(assess(&bytes).is_err());Ok(())
}
#[test]
fn whole_source_opaque_and_header_heading_coverage_errors_remain_fatal()->TestResult{
    let p=paragraph(1,"paraPrIDRef='0'","<hp:t>private hidden title</hp:t>");
    for bytes in [bundle(&format!("<u:opaque>{p}</u:opaque>"),&head(OUTLINE))?,bundle(&paragraph(2,"","<hp:t>body</hp:t>"),&head(OUTLINE).replace("</hh:head>",&format!("{p}</hh:head>")))?]{
        assert_eq!(ReferenceValidationProductOperation::assess_package_source(&bytes,DocumentId::parse("reference-product")?,Sha256::digest(&bytes).into(),SourceImportLimits::default(),limits()?),Err(ReferenceSourceError::Coverage));}Ok(())
}
#[test]
fn invalid_heading_cli_has_exit2_no_partial_json_and_unchanged_original()->TestResult{
    let bytes=bundle(&paragraph(1,"paraPrIDRef='0'","<hp:t>body</hp:t>"),&head(&OUTLINE.replace(" level='2'","")))?;
    let temp=tempfile::tempdir()?;let path=temp.path().join("invalid-heading.hwpx");fs::write(&path,&bytes)?;let sha=hex::encode(Sha256::digest(&bytes));
    let output=cli([OsStr::new("reference-source"),OsStr::new("reference-product"),OsStr::new(&sha),path.as_os_str()])?;
    assert_eq!(output.status.code(),Some(2));assert!(output.stdout.is_empty());assert_eq!(String::from_utf8(output.stderr)?.trim(),"REFERENCE_SOURCE_BINDING_REJECTED");assert_eq!(fs::read(path)?,bytes);Ok(())
}
#[test]
fn bookmark_targets_and_new_heading_targets_are_combined_without_changing_existing_kind()->TestResult{
    let bytes=bundle(&paragraph(1,"paraPrIDRef='0'",&format!("{}<hp:t>title</hp:t>",marker("PRIVATE-BOOKMARK"))),&head(OUTLINE))?;
    let report=assess(&bytes)?;assert_eq!(report.targets().len(),2);assert_eq!(report.targets()[0].target_kind,domain_ir::ReferenceTargetKind::Bookmark);
    assert_eq!(report.targets()[1].target_kind,domain_ir::ReferenceTargetKind::Heading);assert!(report.targets().iter().all(|t|t.active&&t.anchor.is_none()));assert!(report.validation_report().is_none());Ok(())
}
#[test]
fn two_source_parts_with_same_local_paragraph_ids_produce_distinct_heading_targets()->TestResult{
    let bytes=rewrite(&bookmark_fixture::two_sections()?,&head(OUTLINE),true)?;let report=assess(&bytes)?;
    let headings:Vec<_>=report.targets().iter().filter(|t|t.target_kind==domain_ir::ReferenceTargetKind::Heading).collect();assert_eq!(headings.len(),2);
    assert_ne!(headings[0].logical_target_id,headings[1].logical_target_id);assert_eq!(report.heading_target_receipt().ok_or("headings")?.heading_targets,2);Ok(())
}
#[test]
fn foreign_document_and_source_changes_change_heading_binding_without_caller_state()->TestResult{
    let bytes=heading_package()?;let local=assess(&bytes)?;let foreign=ReferenceValidationProductOperation::assess_package_source(&bytes,DocumentId::parse("foreign-heading-source")?,Sha256::digest(&bytes).into(),SourceImportLimits::default(),limits()?)?;
    assert_ne!(local.targets()[0].logical_target_id,foreign.targets()[0].logical_target_id);assert_ne!(local.heading_target_receipt().ok_or("local")?.inventory_sha256,foreign.heading_target_receipt().ok_or("foreign")?.inventory_sha256);
    let changed=bundle(&paragraph(1,"paraPrIDRef='0'","<hp:t>different title</hp:t>"),&head(OUTLINE))?;assert_ne!(assess(&changed)?.targets()[0].target_state_sha256,local.targets()[0].target_state_sha256);Ok(())
}
#[test]
fn expanded_response_limit_and_heading_item_limits_remain_fail_closed()->TestResult{
    let bytes=heading_package()?;let report=assess(&bytes)?;let n=report.canonical_json(limits()?)?.len();
    let exact=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig{input_bytes:n,output_bytes:n,..Default::default()})?;
    let short=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig{input_bytes:n-1,output_bytes:n-1,..Default::default()})?;
    assert_eq!(report.canonical_json(exact)?.len(),n);assert_eq!(report.canonical_json(short),Err(ReferenceSourceError::Output));
    let body=paragraph(1,"paraPrIDRef='0'","<hp:t>A</hp:t>")+&paragraph(2,"paraPrIDRef='0'","<hp:t>B</hp:t>");let bytes=bundle(&body,&head(OUTLINE))?;
    let bounded=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig{items_per_kind:1,..Default::default()})?;
    assert_eq!(ReferenceValidationProductOperation::assess_package_source(&bytes,DocumentId::parse("reference-product")?,Sha256::digest(&bytes).into(),SourceImportLimits::default(),bounded),Err(ReferenceSourceError::InputLimit));Ok(())
}
#[test]
fn api_and_cli_metadata_never_disclose_title_text_or_header_parameter_values()->TestResult{
    let bytes=heading_package()?;let report=assess(&bytes)?;let output=report.canonical_json(limits()?)?;let value:Value=serde_json::from_slice(&output)?;
    for key in ["source_numbering_id_ref","raw_source_level","paragraph_property_id","observations"]{assert!(value["heading_target_import"].get(key).is_none());}
    for text in [String::from_utf8(output)?,format!("{report:?}")]{assert!(!text.contains("PRIVATE-")&&!text.contains("<hh:")&&!text.contains("<hp:"));}Ok(())
}
