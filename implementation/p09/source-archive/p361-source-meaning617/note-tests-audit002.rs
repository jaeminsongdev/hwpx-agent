use super::*;
use domain_ir::NoteKind;
use std::collections::BTreeSet;

fn note(kind: &str, paragraph: u32) -> String {
    format!("<hp:ctrl><hp:{kind} instId='101' userChar='☆' prefixChar='※' suffixChar='☃'><hp:subList><hp:p id='{paragraph}'><hp:run><hp:t>PRIVATE-NOTE-SELECTION-BODY &amp; 한글</hp:t></hp:run></hp:p></hp:subList></hp:{kind}></hp:ctrl>")
}
fn mixed() -> Result<Vec<u8>, Box<dyn Error>> {
    package(&format!("{}{}<hp:t>PRIVATE-MAIN-SELECTION</hp:t>", note("footNote", 11), note("endNote", 12)))
}
#[test]
fn source_note_selectors_reuse_actual_observations_and_emit_only_id_fingerprint_and_kind() -> TestResult {
    let bytes = mixed()?; let original = bytes.clone();
    let direct = fixture::forms(&bytes, "reference-product")?; let report = assess(&bytes)?;
    assert_eq!(report.note_selections().len(), 2);
    for (selection, actual) in report.note_selections().iter().zip(direct.notes()) {
        assert_eq!(selection.note_id(), &actual.note_id);
        assert_eq!(selection.source_note_sha256(), actual.source_anchor.fingerprint_sha256);
        assert_eq!(selection.kind(), if actual.native_kind == "footNote" { NoteKind::Footnote } else { NoteKind::Endnote });
    }
    assert_ne!(report.note_selections()[0].note_id(), report.note_selections()[1].note_id());
    assert_eq!(direct.notes()[0].native_instance_id, direct.notes()[1].native_instance_id);
    let output = report.canonical_json(limits()?)?; let value: Value = serde_json::from_slice(&output)?;
    assert_eq!(value["schema_version"], "hwpx-agent.product.reference-source-assessment/v14");
    let selections = value["note_selections"].as_array().ok_or("selections")?;
    assert_eq!(selections.len(), 2);
    for (i, entry) in selections.iter().enumerate() {
        assert_eq!(entry.as_object().ok_or("entry")?.keys().map(String::as_str).collect::<BTreeSet<_>>(), BTreeSet::from(["kind", "note_id", "source_note_sha256"]));
        assert_eq!(entry["note_id"], report.note_selections()[i].note_id().as_str());
        assert_eq!(entry["source_note_sha256"], serde_json::to_value(report.note_selections()[i].source_note_sha256())?);
        assert_eq!(entry["kind"], if i == 0 { "footnote" } else { "endnote" });
    }
    let debug = format!("{report:?}"); let encoded = String::from_utf8(output)?;
    for private in ["PRIVATE-NOTE-SELECTION-BODY", "PRIVATE-MAIN-SELECTION", "☆", "※", "☃", "native_attributes", "native_instance_id"] {
        assert!(!debug.contains(private)); assert!(!encoded.contains(private));
    }
    assert_eq!(report.status(), ReferenceSourceStatus::Incomplete); assert!(report.validation_report().is_none());
    assert_eq!(value["unresolved"].as_array().ok_or("unresolved")?.len(), 4);
    assert_eq!(bytes, original);
    Ok(())
}
#[test]
fn source_note_selector_actual_cli_is_v12_read_only_and_still_exits_incomplete() -> TestResult {
    let bytes = mixed()?; let dir = tempfile::tempdir()?; let path = dir.path().join("original-note-selection.hwpx");
    fs::write(&path, &bytes)?; let digest = hex::encode(Sha256::digest(&bytes));
    let output = cli([OsStr::new("reference-source"), OsStr::new("reference-product"), OsStr::new(&digest), path.as_os_str()])?;
    assert_eq!(output.status.code(), Some(3)); assert!(output.stderr.is_empty());
    let value: Value = serde_json::from_slice(&output.stdout)?;
    assert_eq!(value, serde_json::from_slice::<Value>(&assess(&bytes)?.canonical_json(limits()?)?)?);
    assert_eq!(value["schema_version"], "hwpx-agent.product.reference-source-assessment/v13");
    assert_eq!(value["note_selections"].as_array().ok_or("selectors")?.len(), 2);
    assert_eq!(value["status"], "incomplete"); assert!(value["validation_report"].is_null());
    assert!(!String::from_utf8_lossy(&output.stdout).contains("PRIVATE")); assert_eq!(fs::read(path)?, bytes);
    Ok(())
}
#[test]
fn source_note_selectors_bind_whole_package_and_document_without_inventing_native_identity() -> TestResult {
    let bytes = mixed()?; let report = assess(&bytes)?;
    let foreign = ReferenceValidationProductOperation::assess_package_source(&bytes, DocumentId::parse("foreign-note-document")?, Sha256::digest(&bytes).into(), SourceImportLimits::default(), limits()?)?;
    let changed = package(&format!("{}{}<hp:t>DIFFERENT-PRIVATE-MAIN</hp:t>", note("footNote", 11), note("endNote", 12)))?;
    let current = assess(&changed)?;
    for ((a, b), c) in report.note_selections().iter().zip(foreign.note_selections()).zip(current.note_selections()) {
        assert_ne!(a.note_id(), b.note_id()); assert_ne!(a.note_id(), c.note_id());
        assert_eq!(a.source_note_sha256(), b.source_note_sha256()); assert_eq!(a.source_note_sha256(), c.source_note_sha256());
    }
    assert_eq!(ReferenceValidationProductOperation::assess_package_source(&changed, DocumentId::parse("reference-product")?, Sha256::digest(&bytes).into(), SourceImportLimits::default(), limits()?), Err(ReferenceSourceError::Binding));
    Ok(())
}
#[test]
fn source_note_selection_absence_hidden_note_coverage_and_exact_finite_response_limits_are_preserved() -> TestResult {
    let absent = assess(&package("<hp:t>private no-note body</hp:t>")?)?;
    assert!(absent.note_selections().is_empty()); assert!(absent.validation_report().is_none());
    let value: Value = serde_json::from_slice(&absent.canonical_json(limits()?)?)?;
    assert_eq!(value["note_selections"], serde_json::json!([])); assert_eq!(value["status"], "incomplete");
    let hidden = package(&format!("<u:hidden>{}</u:hidden>", note("footNote", 11)))?;
    assert_eq!(assess(&hidden).err().and_then(|e| e.downcast::<ReferenceSourceError>().ok()).map(|e| *e), Some(ReferenceSourceError::Structure));
    let bytes = mixed()?; let tight = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig { items_per_kind: 1, ..Default::default() })?;
    assert_eq!(ReferenceValidationProductOperation::assess_package_source(&bytes, DocumentId::parse("reference-product")?, Sha256::digest(&bytes).into(), SourceImportLimits::default(), tight), Err(ReferenceSourceError::InputLimit));
    let report = assess(&bytes)?; let n = report.canonical_json(limits()?)?.len();
    let exact = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig { input_bytes: n, output_bytes: n, ..Default::default() })?;
    let short = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig { input_bytes: n-1, output_bytes: n-1, ..Default::default() })?;
    assert_eq!(report.canonical_json(exact)?.len(), n); assert_eq!(report.canonical_json(short), Err(ReferenceSourceError::Output));
    Ok(())
}
#[test]
fn source_note_selector_order_keeps_same_local_ids_separate_across_two_source_parts() -> TestResult {
    use std::io::{Cursor, Read as _, Write as _};
    let seed = bookmark_fixture::two_sections()?; let mut input = zip::ZipArchive::new(Cursor::new(seed))?;
    let mut output = zip::ZipWriter::new(Cursor::new(Vec::new()));
    for i in 0..input.len() {
        let mut entry = input.by_index(i)?; let name = entry.name().to_owned(); let mut bytes = Vec::new(); entry.read_to_end(&mut bytes)?;
        if matches!(name.as_str(), "Contents/section0.xml" | "Contents/section1.xml") {
            bytes = format!("<hs:sec xmlns:hs='http://www.hancom.co.kr/hwpml/2011/section' xmlns:hp='http://www.hancom.co.kr/hwpml/2011/paragraph'><hp:p id='1'><hp:run>{}</hp:run></hp:p></hs:sec>", note("footNote", 11)).into_bytes();
        }
        output.start_file(name, zip::write::SimpleFileOptions::default().compression_method(zip::CompressionMethod::Stored))?; output.write_all(&bytes)?;
    }
    let bytes = output.finish()?.into_inner(); let report = assess(&bytes)?; let direct = fixture::forms(&bytes, "reference-product")?;
    assert_eq!(report.note_selections().len(), 2); assert_eq!(direct.notes().len(), 2);
    for (selected, original) in report.note_selections().iter().zip(direct.notes()) { assert_eq!(selected.note_id(), &original.note_id); }
    assert_ne!(report.note_selections()[0].note_id(), report.note_selections()[1].note_id());
    assert_eq!(report.note_selections()[0].source_note_sha256(), report.note_selections()[1].source_note_sha256());
    Ok(())
}
