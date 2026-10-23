use super::*;
use hwpx_package::document_import::reference_targets::caption_source_state::{ImportedCaptionSourceState,CaptionNumberingSourceEventKind as Event};
fn joined_package()->Result<Vec<u8>,Box<dyn Error>> {source_caption_context_package(&source_frame_body(),&format!("{}{}",source_caption_context_begin(),source_frame_styles()))}
#[test]
fn source_caption_join_product_exposes_exact_original_receipt_links_and_xml_events_without_authority() -> TestResult {
    let bytes=joined_package()?;let original=bytes.clone();let forms=fixture::forms(&bytes,"reference-product")?;let state=ImportedCaptionSourceState::import(forms.body_structure(),limits()?)?;let report=assess(&bytes)?;
    assert_eq!(report.caption_source_state_receipt(),state.receipt());assert_eq!(report.caption_owner_links(),state.owner_links());assert_eq!(report.caption_source_events(),state.source_events());
    let r=report.caption_source_state_receipt();assert_eq!((&r.numbering,&r.context,&r.frames,&r.object_states),(report.numbering_receipt(),report.numbering_context_receipt(),report.caption_frame_receipt(),report.caption_object_state_receipt()));
    assert_eq!((r.owner_links,r.caption_links,r.source_events),(1,1,4));let link=&report.caption_owner_links()[0];assert_eq!((link.owner_index,link.object_state_index),(0,0));let cap=link.caption.ok_or("caption")?;
    assert_eq!(report.caption_frames()[cap.frame_index].logical_object_id,report.numbering_owners()[link.owner_index].logical_object_id);assert_eq!(report.caption_envelopes()[cap.envelope_index].logical_caption_id(),&report.caption_frames()[cap.frame_index].logical_caption_id);
    assert!(report.caption_source_events().windows(2).all(|w|w[0].source_position<w[1].source_position));
    assert!(report.caption_source_events().iter().any(|e|matches!(e.event,Event::AutoNumber {control_index:1,owner_index:Some(0)})));
    assert!(!r.sequence_interpretation_and_recalculation_qualified&&!r.complete_auxiliary_state_and_protection_qualified&&!r.execution_publication_authority);assert_eq!(bytes,original);assert_eq!(report.status(),ReferenceSourceStatus::Incomplete);assert!(report.validation_report().is_none());Ok(())
}
#[test]
fn source_caption_join_actual_cli_v10_exposes_request_bindings_without_private_values_or_complete_pass() -> TestResult {
    let bytes=joined_package()?;let report=assess(&bytes)?;let temp=tempfile::tempdir()?;let path=temp.path().join("joined-source.hwpx");fs::write(&path,&bytes)?;
    let sha=hex::encode(Sha256::digest(&bytes));let output=cli([OsStr::new("reference-source"),OsStr::new("reference-product"),OsStr::new(&sha),path.as_os_str()])?;
    assert_eq!(output.status.code(),Some(3));assert!(output.stderr.is_empty());let value:Value=serde_json::from_slice(&output.stdout)?;
    assert_eq!(value,serde_json::from_slice::<Value>(&report.canonical_json(limits()?)?)?);assert_eq!(value["schema_version"],"hwpx-agent.product.reference-source-assessment/v14");
    assert_eq!(value["caption_source_state_import"]["joined_state_sha256"],serde_json::to_value(report.caption_source_state_receipt().joined_state_sha256)?);
    assert_eq!(value["caption_owner_links"],serde_json::to_value(report.caption_owner_links())?);assert_eq!(value["caption_source_events"],serde_json::to_value(report.caption_source_events())?);
    assert_eq!(value["unresolved"].as_array().ok_or("unresolved")?.len(),4);assert!(value["validation_report"].is_null());assert_eq!(value["status"],"incomplete");
    assert_eq!(value["caption_source_state_import"]["execution_publication_authority"],false);assert_eq!(fs::read(path)?,bytes);
    let safe=format!("{report:?}{}",String::from_utf8(output.stdout)?);for private in ["private caption label","private prefix","private frame style","private frame style name"]{assert!(!safe.contains(private));}Ok(())
}
#[test]
fn source_caption_join_two_parts_keep_same_local_ids_separate_and_link_every_owner_and_control() -> TestResult {
    use std::io::{Cursor,Read,Write};
    let bytes=bookmark_fixture::two_sections()?;let mut input=zip::ZipArchive::new(Cursor::new(bytes))?;let mut output=zip::ZipWriter::new(Cursor::new(Vec::new()));
    for i in 0..input.len(){let mut entry=input.by_index(i)?;let name=entry.name().to_owned();let mut data=Vec::new();entry.read_to_end(&mut data)?;
        if name.starts_with("Contents/section"){data=String::from_utf8(data)?.replace("<hp:ctrl><hp:bookmark name='same-across-sections'/></hp:ctrl>",&source_frame_body()).into_bytes();}
        if name=="Contents/header.xml"{data=format!("<hh:head xmlns:hh='http://www.hancom.co.kr/hwpml/2011/head'>{}{}</hh:head>",source_caption_context_begin(),source_frame_styles()).into_bytes();}
        output.start_file(name,zip::write::SimpleFileOptions::default().compression_method(zip::CompressionMethod::Stored))?;output.write_all(&data)?;}
    let bytes=output.finish()?.into_inner();let report=assess(&bytes)?;let forms=fixture::forms(&bytes,"reference-product")?;let state=ImportedCaptionSourceState::import(forms.body_structure(),limits()?)?;
    assert_eq!((report.caption_owner_links().len(),report.caption_source_events().len(),report.caption_frames().len()),(2,8,2));assert_eq!(report.caption_source_state_receipt(),state.receipt());
    assert_eq!(report.caption_owner_links(),state.owner_links());assert_eq!(report.caption_source_events(),state.source_events());assert_ne!(report.numbering_owners()[0].logical_object_id,report.numbering_owners()[1].logical_object_id);
    let mut seen=std::collections::BTreeSet::new();for link in report.caption_owner_links(){let cap=link.caption.ok_or("caption")?;assert!(seen.insert(cap.frame_index));
        assert_eq!(report.caption_frames()[cap.frame_index].logical_object_id,report.numbering_owners()[link.owner_index].logical_object_id);assert_eq!(report.caption_object_states()[link.object_state_index].logical_object_id,report.numbering_owners()[link.owner_index].logical_object_id);}
    let mut controls=std::collections::BTreeSet::new();let mut starts=std::collections::BTreeSet::new();for event in report.caption_source_events(){match event.event {
        Event::AutoNumber {control_index,owner_index}|Event::Restart {control_index,owner_index}=>{assert!(controls.insert(control_index));assert_eq!(report.numbering_controls()[control_index].section_id,event.section_id);if let Some(owner)=owner_index{assert_eq!(report.numbering_owners()[owner].section_id,event.section_id);}},
        Event::SectionStart {section_start_index}=>{assert!(starts.insert(section_start_index));assert_eq!(report.numbering_section_starts()[section_start_index].section_id,event.section_id);},Event::Owner {owner_index}=>assert_eq!(report.numbering_owners()[owner_index].section_id,event.section_id),
    }}assert_eq!(controls.len(),report.numbering_controls().len());assert_eq!(starts.len(),report.numbering_section_starts().len());Ok(())
}
#[test]
fn source_caption_join_empty_and_bare_owners_preserve_absence_and_do_not_manufacture_native_defaults() -> TestResult {
    for (body,owners) in [("<hp:t>private empty body</hp:t>",0),("<hp:arc id='7'/><hp:connectLine id='8'/>",2)] {
        let bytes=package(body)?;let report=assess(&bytes)?;let forms=fixture::forms(&bytes,"reference-product")?;let state=ImportedCaptionSourceState::import(forms.body_structure(),limits()?)?;
        assert_eq!(report.caption_source_state_receipt(),state.receipt());assert_eq!(report.caption_owner_links().len(),owners);assert!(report.caption_owner_links().iter().all(|l|l.caption.is_none()));
        assert_eq!(report.caption_source_events().len(),owners);assert!(report.document_numbering_start().is_none());assert!(report.caption_frames().is_empty());assert!(report.numbering_controls().is_empty());assert!(report.validation_report().is_none());
        let value:Value=serde_json::from_slice(&report.canonical_json(limits()?)?)?;assert_eq!(value["unresolved"].as_array().ok_or("unresolved")?.len(),4);assert_eq!(value["caption_source_state_import"]["complete_auxiliary_state_and_protection_qualified"],false);
    }Ok(())
}
#[test]
fn source_caption_join_whole_source_document_binding_and_exact_response_limits_are_not_cached_authority() -> TestResult {
    let bytes=joined_package()?;let report=assess(&bytes)?;let foreign=ReferenceValidationProductOperation::assess_package_source(&bytes,DocumentId::parse("foreign-reference-product")?,Sha256::digest(&bytes).into(),SourceImportLimits::default(),limits()?)?;
    assert_ne!(report.caption_source_state_receipt().joined_state_sha256,foreign.caption_source_state_receipt().joined_state_sha256);
    let changed=source_caption_context_package(&source_frame_body(),&format!("{}{}<u:future value='private opaque state'/>",source_caption_context_begin(),source_frame_styles()))?;
    let after=assess(&changed)?;assert_ne!(report.caption_source_state_receipt().joined_state_sha256,after.caption_source_state_receipt().joined_state_sha256);
    assert_eq!(ReferenceValidationProductOperation::assess_package_source(&changed,DocumentId::parse("reference-product")?,Sha256::digest(&bytes).into(),SourceImportLimits::default(),limits()?),Err(ReferenceSourceError::Binding));
    let n=report.canonical_json(limits()?)?.len();let exact=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {input_bytes:n,output_bytes:n,..Default::default()})?;
    let short=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {input_bytes:n-1,output_bytes:n-1,..Default::default()})?;assert_eq!(report.canonical_json(exact)?.len(),n);assert_eq!(report.canonical_json(short),Err(ReferenceSourceError::Output));
    assert!(!String::from_utf8(after.canonical_json(limits()?)?)?.contains("private opaque state"));Ok(())
}
