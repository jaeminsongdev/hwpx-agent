use super::*;
use domain_ir::NoteKind;
use std::collections::BTreeSet;

fn style(kind: &str, placement: &str) -> String {
    format!("<hp:{kind} u:future='PRIVATE-STYLE-OPAQUE'><hp:autoNumFormat type='USER_CHAR' userChar='☆' prefixChar='※' suffixChar='☃' supscript='0'/><hp:noteLine length='-1' type='SOLID' width='0.12 mm' color='#000000'/><hp:noteSpacing betweenNotes='283' belowLine='567' aboveLine='850'/><hp:numbering type='CONTINUOUS' newNum='1'/><hp:placement place='{placement}' beneathText='0'/><u:extension value='PRIVATE-EXTENSION'/></hp:{kind}>")
}
fn style_body() -> String {
    format!("<hp:secPr>{}{}</hp:secPr><hp:t>PRIVATE-STYLE-MAIN</hp:t>",style("footNotePr","EACH_COLUMN"),style("endNotePr","END_OF_DOCUMENT"))
}
fn source() -> Result<Vec<u8>,Box<dyn Error>> { package(&style_body()) }
fn assessment(bytes: &[u8],document: &str,limits: ReferenceAuxiliaryLimits)
    -> Result<hwpx_agent_cli::reference_validation_product::source::ReferenceSourceAssessment,ReferenceSourceError> {
    ReferenceValidationProductOperation::assess_package_source(bytes,DocumentId::parse(document).expect("fixed document"),Sha256::digest(bytes).into(),SourceImportLimits::default(),limits)
}
#[test]
fn source_note_style_selectors_match_original_observations_and_hide_values_text_and_opaque_xml() -> TestResult {
    let bytes=source()?;let original=bytes.clone();let report=assess(&bytes)?;
    let forms=fixture::forms(&bytes,"reference-product")?;
    let actual=forms.body_structure().import_note_styles(hwpx_package::NoteHwpxLimits::new(Default::default())?)?;
    let values:Value=serde_json::from_slice(&report.canonical_json(limits()?)?)?;
    assert_eq!(values["schema_version"],"hwpx-agent.product.reference-source-assessment/v13");
    let selections=values["note_style_selections"].as_array().ok_or("style selectors")?;
    assert_eq!(selections.len(),2);assert_eq!(report.note_style_selections().len(),actual.len());
    for ((entry,selector),direct) in selections.iter().zip(report.note_style_selections()).zip(&actual) {
        assert_eq!(entry.as_object().ok_or("selector")?.keys().map(String::as_str).collect::<BTreeSet<_>>(),BTreeSet::from(["kind","source_style_sha256","style_id"]));
        assert_eq!(selector.style_id(),direct.style_id());assert_eq!(selector.source_style_sha256(),direct.source_anchor().fingerprint_sha256);assert_eq!(selector.kind(),direct.kind());
        assert_eq!(entry["style_id"],selector.style_id().as_str());assert_eq!(entry["source_style_sha256"],serde_json::to_value(selector.source_style_sha256())?);
    }
    assert_eq!(report.note_style_selections()[0].kind(),NoteKind::Footnote);assert_eq!(report.note_style_selections()[1].kind(),NoteKind::Endnote);
    assert!(report.note_selections().is_empty());
    let json=String::from_utf8(report.canonical_json(limits()?)?)?;let debug=format!("{report:?}");
    for private in ["PRIVATE-STYLE-MAIN","PRIVATE-STYLE-OPAQUE","PRIVATE-EXTENSION","☆","※","☃","user_character","prefix_character","opaque_style_sha256"] {
        assert!(!json.contains(private) && !debug.contains(private));
    }
    assert_eq!(report.status(),ReferenceSourceStatus::Incomplete);assert!(report.validation_report().is_none());
    assert_eq!(values["unresolved"].as_array().ok_or("unresolved")?.len(),4);assert_eq!(bytes,original);
    Ok(())
}
#[test]
fn source_note_style_actual_v12_cli_is_read_only_and_preserves_incomplete_exit_three() -> TestResult {
    let bytes=source()?;let dir=tempfile::tempdir()?;let path=dir.path().join("source-note-styles.hwpx");fs::write(&path,&bytes)?;
    let digest=hex::encode(Sha256::digest(&bytes));
    let result=cli([OsStr::new("reference-source"),OsStr::new("reference-product"),OsStr::new(&digest),path.as_os_str()])?;
    assert_eq!(result.status.code(),Some(3));assert!(result.stderr.is_empty());
    let value:Value=serde_json::from_slice(&result.stdout)?;
    assert_eq!(value,serde_json::from_slice::<Value>(&assess(&bytes)?.canonical_json(limits()?)?)?);
    assert_eq!(value["note_style_selections"].as_array().ok_or("selectors")?.len(),2);
    assert_eq!(value["status"],"incomplete");assert!(value["validation_report"].is_null());
    assert!(!String::from_utf8_lossy(&result.stdout).contains("PRIVATE"));assert_eq!(fs::read(path)?,bytes);
    Ok(())
}
#[test]
fn source_note_style_selectors_bind_document_whole_package_and_original_style_fingerprint() -> TestResult {
    let bytes=source()?;let old=assess(&bytes)?;let foreign=assessment(&bytes,"other-document",limits()?)?;
    let drift=package(&style_body().replace("PRIVATE-STYLE-MAIN","DIFFERENT-PRIVATE-MAIN"))?;let changed=assess(&drift)?;
    for ((a,b),c) in old.note_style_selections().iter().zip(foreign.note_style_selections()).zip(changed.note_style_selections()) {
        assert_ne!(a.style_id(),b.style_id());assert_ne!(a.style_id(),c.style_id());
        assert_eq!(a.source_style_sha256(),b.source_style_sha256());assert_eq!(a.source_style_sha256(),c.source_style_sha256());
    }
    let style_drift=package(&style_body().replacen("newNum='1'","newNum='2'",1))?;let after=assess(&style_drift)?;
    assert_ne!(old.note_style_selections()[0].source_style_sha256(),after.note_style_selections()[0].source_style_sha256());
    assert_eq!(ReferenceValidationProductOperation::assess_package_source(&drift,DocumentId::parse("reference-product")?,Sha256::digest(&bytes).into(),SourceImportLimits::default(),limits()?),Err(ReferenceSourceError::Binding));
    Ok(())
}
#[test]
fn absent_styles_stay_absent_while_malformed_hidden_duplicate_or_incompatible_styles_fail_explicitly() -> TestResult {
    let absent=assess(&package("<hp:t>NO STYLE</hp:t>")?)?;assert!(absent.note_style_selections().is_empty());
    let value:Value=serde_json::from_slice(&absent.canonical_json(limits()?)?)?;assert_eq!(value["note_style_selections"],serde_json::json!([]));
    assert_eq!(value["status"],"incomplete");assert!(value["validation_report"].is_null());
    let valid=style_body();
    for body in [valid.replace(" newNum='1'",""),valid.replace("width='0.12 mm'","width='UNSUPPORTED'"),
        valid.replace("<hp:placement","<hp:numbering type='CONTINUOUS' newNum='1'/><hp:placement"),
        valid.replace("<hp:secPr>","<hp:secPr><u:hidden>").replace("</hp:secPr>","</u:hidden></hp:secPr>"),
        valid.replace("</hp:secPr>","</hp:secPr><hp:secPr/>"),
        valid.replace("place='END_OF_DOCUMENT'","place='EACH_COLUMN'"),
        valid.replace("<hp:secPr>","").replace("</hp:secPr>","")] {
        let bytes=package(&body)?;
        assert_eq!(assessment(&bytes,"reference-product",limits()?),Err(ReferenceSourceError::NoteStyles));
    }
    Ok(())
}
#[test]
fn source_note_style_count_text_and_exact_response_limits_are_retained_without_truncation() -> TestResult {
    let bytes=source()?;
    for config in [ReferenceAuxiliaryLimitConfig {items_per_kind:1,..Default::default()},ReferenceAuxiliaryLimitConfig {text_bytes:1,..Default::default()}] {
        assert_eq!(assessment(&bytes,"reference-product",ReferenceAuxiliaryLimits::new(config)?),Err(ReferenceSourceError::InputLimit));
    }
    let report=assess(&bytes)?;let size=report.canonical_json(limits()?)?.len();
    let exact=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {input_bytes:size,output_bytes:size,..Default::default()})?;
    let short=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {input_bytes:size-1,output_bytes:size-1,..Default::default()})?;
    assert_eq!(report.canonical_json(exact)?.len(),size);assert_eq!(report.canonical_json(short),Err(ReferenceSourceError::Output));
    Ok(())
}
#[test]
fn two_body_spine_parts_keep_same_style_subtrees_distinct_in_xml_order_and_enforce_section_limit() -> TestResult {
    use std::io::{Cursor,Read as _,Write as _};
    let seed=bookmark_fixture::two_sections()?;let mut archive=zip::ZipArchive::new(Cursor::new(seed))?;
    let mut output=zip::ZipWriter::new(Cursor::new(Vec::new()));
    for i in 0..archive.len() {
        let mut entry=archive.by_index(i)?;let name=entry.name().to_owned();let mut bytes=Vec::new();entry.read_to_end(&mut bytes)?;
        if matches!(name.as_str(),"Contents/section0.xml"|"Contents/section1.xml") {
            bytes=format!("<hs:sec xmlns:hs='http://www.hancom.co.kr/hwpml/2011/section' xmlns:hp='http://www.hancom.co.kr/hwpml/2011/paragraph' xmlns:u='urn:future'><hp:p id='1'><hp:run>{}</hp:run></hp:p></hs:sec>",style_body()).into_bytes();
        }
        output.start_file(name,zip::write::SimpleFileOptions::default().compression_method(zip::CompressionMethod::Stored))?;output.write_all(&bytes)?;
    }
    let bytes=output.finish()?.into_inner();let report=assess(&bytes)?;let selected=report.note_style_selections();assert_eq!(selected.len(),4);
    assert_eq!(selected.iter().map(|s|s.kind()).collect::<Vec<_>>(),vec![NoteKind::Footnote,NoteKind::Endnote,NoteKind::Footnote,NoteKind::Endnote]);
    assert_ne!(selected[0].style_id(),selected[2].style_id());assert_eq!(selected[0].source_style_sha256(),selected[2].source_style_sha256());
    let tight=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {sections:1,..Default::default()})?;
    assert_eq!(assessment(&bytes,"reference-product",tight),Err(ReferenceSourceError::InputLimit));
    Ok(())
}
