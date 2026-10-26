//! Conditional source declarations are observations, never chosen headings or execution authority.
use domain_ir::{DocumentId,ReferenceAuxiliaryLimitConfig,ReferenceAuxiliaryLimits,ReferenceTargetKind};
use hwpx_agent_cli::reference_validation_product::{ReferenceValidationProductOperation as Product,
    source::{ReferenceSourceAssessment,ReferenceSourceError,ReferenceSourceStatus}};
use hwpx_package::document_import::{SourceImportLimits,reference_targets::{ReferenceTargetImportError as E,
    headings::{ImportedReferenceHeadingTargets as Strict,declarations702::{SourceHeadingDeclarationInventory as Inventory,
        SourceHeadingDeclaration,SourceHeadingDeclarationType}}}};
use sha2::{Digest as _,Sha256};
use serde_json::Value;
use std::{error::Error,io::{Cursor,Read,Write}};
#[path="../../hwpx-package/tests/support/document_import_field_fixture.rs"]
#[allow(dead_code)] mod fixture;
type Result<T=()> = std::result::Result<T,Box<dyn Error>>;
const OUTLINE:&str="<hh:heading type='OUTLINE' idRef='0' level='8'/>";
const NONE:&str="<hh:heading type='NONE' idRef='0' level='0'/>";
const URI:&str="urn:PRIVATE-required-namespace";
fn limits()->Result<ReferenceAuxiliaryLimits>{Ok(ReferenceAuxiliaryLimits::new(Default::default())?)}
fn switch()->String{format!("<hp:switch><hp:case hp:required-namespace='{URI}'>{OUTLINE}</hp:case><hp:default>{NONE}</hp:default></hp:switch>")}
fn header(declaration:&str)->String{format!("<hh:head xmlns:hh='http://www.hancom.co.kr/hwpml/2011/head' xmlns:hp='http://www.hancom.co.kr/hwpml/2011/paragraph' xmlns:u='urn:future'><hh:refList><hh:paraProperties><hh:paraPr id='0'>{declaration}</hh:paraPr></hh:paraProperties></hh:refList></hh:head>")}
fn paragraph()->String{"<hp:p id='1' paraPrIDRef='0'><hp:run><hp:t>PRIVATE-title</hp:t></hp:run></hp:p>".into()}
fn replace(bytes:&[u8],name:&str,value:&str)->Result<Vec<u8>>{
    let mut input=zip::ZipArchive::new(Cursor::new(bytes))?;let mut out=zip::ZipWriter::new(Cursor::new(Vec::new()));
    for i in 0..input.len(){let mut part=input.by_index(i)?;let path=part.name().to_owned();let mut data=Vec::new();part.read_to_end(&mut data)?;
        if path==name{data=value.as_bytes().to_vec();}out.start_file(path,zip::write::SimpleFileOptions::default().compression_method(zip::CompressionMethod::Stored))?;out.write_all(&data)?;}
    Ok(out.finish()?.into_inner())
}
fn package(body:&str,head:&str)->Result<Vec<u8>>{replace(&fixture::package(body)?,"Contents/header.xml",head)}
fn assess_with(bytes:&[u8],bounds:ReferenceAuxiliaryLimits)->std::result::Result<ReferenceSourceAssessment,ReferenceSourceError>{
    Product::assess_package_source(bytes,DocumentId::parse("conditional702").expect("constant id"),Sha256::digest(bytes).into(),SourceImportLimits::default(),bounds)
}
fn assess(bytes:&[u8])->Result<ReferenceSourceAssessment>{Ok(assess_with(bytes,limits()?)?)}
fn cli(bytes:&[u8])->Result<(std::process::Output,Vec<u8>)>{
    let temp=tempfile::tempdir()?;let path=temp.path().join("input.hwpx");std::fs::write(&path,bytes)?;
    let mut command=std::process::Command::new(env!("CARGO_BIN_EXE_hwpx-agent-cli"));
    command.args(["reference-source","conditional702",&hex::encode(Sha256::digest(bytes))]).arg(&path);
    #[cfg(windows)]{use std::os::windows::process::CommandExt as _;command.creation_flags(0x0800_0000);}
    Ok((command.output()?,std::fs::read(path)?))
}
#[test]
fn alternatives_preserve_both_values_without_branch_selection_or_strict_target_fallback()->Result{
    let bytes=package(&paragraph(),&header(&switch()))?;let forms=fixture::forms(&bytes,"conditional702")?;
    let inventory=Inventory::observe_conditional(forms.body_structure(),limits()?)?.ok_or("observed")?;
    assert_eq!((inventory.receipt.paragraph_definitions,inventory.receipt.conditional_definitions,inventory.receipt.heading_elements,inventory.receipt.conditional_paragraphs),(1,1,2,1));
    let SourceHeadingDeclaration::Conditional{branches}=&inventory.definitions[0].declaration else{return Err("conditional".into())};
    assert_eq!(branches.len(),2);assert!(!branches[0].is_default);assert_eq!(branches[0].required_namespace_sha256,Some(Sha256::digest(URI.as_bytes()).into()));
    assert_eq!((branches[0].value.heading_type,branches[0].value.level),(SourceHeadingDeclarationType::Outline,8));
    assert!(branches[1].is_default);assert!(branches[1].required_namespace_sha256.is_none());assert_eq!(branches[1].value.heading_type,SourceHeadingDeclarationType::None);
    assert!(!inventory.receipt.selected_conditional_branch&&!inventory.receipt.effective_headings_qualified&&!inventory.receipt.native_or_complete_reference_state_qualified);
    inventory.verify_source(forms.body_structure(),&bytes,limits()?)?;
    assert!(matches!(Strict::for_partial_source_assessment(forms.body_structure(),limits()?),Err(E::Coverage)));Ok(())
}
#[test]
fn main_api_v16_exposes_unresolved_inventory_and_preserves_bookmarks_without_heading_targets()->Result{
    let body=paragraph().replace("<hp:t>","<hp:ctrl><hp:bookmark name='PRIVATE-name'/></hp:ctrl><hp:t>");
    let bytes=package(&body,&header(&switch()))?;let report=assess(&bytes)?;
    assert!(report.heading_target_receipt().is_none());assert!(report.conditional_heading_declarations().is_some());
    assert_eq!(report.targets().len(),1);assert_eq!(report.targets()[0].target_kind,ReferenceTargetKind::Bookmark);
    assert_eq!(report.status(),ReferenceSourceStatus::Incomplete);assert!(report.validation_report().is_none());
    let value:Value=serde_json::from_slice(&report.canonical_json(limits()?)?)?;
    assert_eq!(value["schema_version"],"hwpx-agent.product.reference-source-assessment/v16");assert!(value["heading_target_import"].is_null());
    assert!(value["unresolved"].as_array().ok_or("unresolved")?.contains(&Value::from("conditional_heading_declarations")));
    for raw in["PRIVATE-title","PRIVATE-name",URI,"<hh:","<hp:"]{assert!(!String::from_utf8(report.canonical_json(limits()?)?)?.contains(raw));assert!(!format!("{report:?}").contains(raw));}Ok(())
}
#[test]
fn actual_cli_v16_matches_api_exit3_and_preserves_source()->Result{
    let bytes=package(&paragraph(),&header(&switch()))?;let report=assess(&bytes)?;let(output,after)=cli(&bytes)?;
    assert_eq!(output.status.code(),Some(3));assert!(output.stderr.is_empty());assert_eq!(after,bytes);
    assert_eq!(serde_json::from_slice::<Value>(&output.stdout)?,serde_json::from_slice::<Value>(&report.canonical_json(limits()?)?)?);Ok(())
}
#[test]
fn malformed_alternatives_are_rejected_without_partial_output()->Result{
    let s=switch();let case=format!("<hp:case hp:required-namespace='{URI}'>{OUTLINE}</hp:case>");
    let variants=[s.replace(&format!("<hp:default>{NONE}</hp:default>"),""),s.replace("hp:required-namespace=","required-namespace="),
        s.replace(URI,""),s.replace(&case,&format!("{case}{case}")),s.replace(NONE,&format!("{NONE}{NONE}")),
        s.replace("level='8'","level='-1'"),s.replace("OUTLINE","UNKNOWN"),s.replace("<hp:default>","<hp:default extra='1'>"),
        s.replace("<hp:switch>","<hp:switch extra='1'>"),s.replace(OUTLINE,&format!("<u:opaque>{OUTLINE}</u:opaque>")),
        s.replace("</hp:case>","PRIVATE-text</hp:case>"),format!("{s}{OUTLINE}")];
    for declaration in variants{let bytes=package(&paragraph(),&header(&declaration))?;assert!(assess(&bytes).is_err());}
    let bytes=package(&paragraph(),&header(&s.replace("level='8'","level='-1'")))?;let(output,after)=cli(&bytes)?;
    assert_eq!(output.status.code(),Some(2));assert!(output.stdout.is_empty());assert_eq!(String::from_utf8(output.stderr)?.trim(),"REFERENCE_SOURCE_BINDING_REJECTED");assert_eq!(after,bytes);Ok(())
}
#[test]
fn opaque_header_and_nonspine_conditional_paragraphs_remain_coverage_errors()->Result{
    let p=paragraph();let h=header(&switch());
    let opaque=package(&format!("<u:opaque>{p}</u:opaque>"),&h)?;
    let hidden=package("<hp:p id='2'><hp:run><hp:t>body</hp:t></hp:run></hp:p>",&h.replace("</hh:head>",&format!("{p}</hh:head>")))?;
    let nonspine=replace(&package(&p,&h)?,"version.xml",&format!("<v xmlns:hp='http://www.hancom.co.kr/hwpml/2011/paragraph'>{p}</v>"))?;
    for bytes in[opaque,hidden,nonspine]{assert_eq!(assess_with(&bytes,limits()?),Err(ReferenceSourceError::Coverage));}Ok(())
}
#[test]
fn hidden_declarations_duplicate_ids_and_unknown_property_references_are_rejected()->Result{
    let h=header(&switch());let duplicate=h.replace("</hh:paraProperties>",&format!("<hh:paraPr id='0'>{NONE}</hh:paraPr></hh:paraProperties>"));
    let hidden=h.replace("</hh:head>",&format!("{OUTLINE}</hh:head>"));
    for(bytes,_)in[(package(&paragraph(),&duplicate)?,0),(package(&paragraph(),&hidden)?,0),
        (package(&paragraph().replace("paraPrIDRef='0'","paraPrIDRef='9'"),&h)?,0)]{assert!(assess(&bytes).is_err());}Ok(())
}
#[test]
fn source_drift_foreign_graph_and_caller_mutated_inventory_cannot_be_rebound()->Result{
    let bytes=package(&paragraph(),&header(&switch()))?;let forms=fixture::forms(&bytes,"conditional702")?;
    let inventory=Inventory::observe(forms.body_structure(),limits()?)?.ok_or("inventory")?;
    let changed=package(&paragraph().replace("PRIVATE-title","changed"),&header(&switch()))?;
    assert!(inventory.verify_source(forms.body_structure(),&changed,limits()?).is_err());
    let foreign=fixture::forms(&bytes,"foreign702")?;assert!(inventory.verify_source(foreign.body_structure(),&bytes,limits()?).is_err());
    let mut forged=inventory.clone();forged.receipt.selected_conditional_branch=true;
    assert!(forged.verify_source(forms.body_structure(),&bytes,limits()?).is_err());Ok(())
}
#[test]
fn item_text_and_output_limits_reject_instead_of_truncating_alternatives()->Result{
    let bytes=package(&paragraph(),&header(&switch()))?;
    for config in[ReferenceAuxiliaryLimitConfig{items_per_kind:1,..Default::default()},
        ReferenceAuxiliaryLimitConfig{text_bytes:1,..Default::default()},
        ReferenceAuxiliaryLimitConfig{input_bytes:128,output_bytes:128,..Default::default()}]{
        assert!(assess_with(&bytes,ReferenceAuxiliaryLimits::new(config)?).is_err());}
    let report=assess(&bytes)?;let n=report.canonical_json(limits()?)?.len();
    let short=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig{input_bytes:n-1,output_bytes:n-1,..Default::default()})?;
    assert_eq!(report.canonical_json(short),Err(ReferenceSourceError::Output));Ok(())
}
#[test]
fn absent_direct_and_multiple_distinct_cases_are_observed_without_effective_selection()->Result{
    let case=format!("<hp:case hp:required-namespace='urn:second'>{NONE}</hp:case>");
    let s=switch().replace("<hp:default>",&format!("{case}<hp:default>"));
    let h=header(&s).replace("</hh:paraProperties>",&format!("<hh:paraPr id='1'>{OUTLINE}</hh:paraPr><hh:paraPr id='2'/></hh:paraProperties>"));
    let bytes=package(&paragraph(),&h)?;let report=assess(&bytes)?;let inv=report.conditional_heading_declarations().ok_or("inventory")?;
    assert_eq!((inv.receipt.paragraph_definitions,inv.receipt.conditional_definitions,inv.receipt.direct_definitions),(3,1,1));
    assert!(matches!(inv.definitions[2].declaration,SourceHeadingDeclaration::Absent));
    assert!(report.targets().iter().all(|t|t.target_kind!=ReferenceTargetKind::Heading));Ok(())
}
