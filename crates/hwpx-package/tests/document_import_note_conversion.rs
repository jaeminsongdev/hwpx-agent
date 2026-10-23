use domain_ir::NoteKind;
use hwpx_package::{
    BoundedZipReader, IdIndexLimits, IdRuleProfile, NoteHwpxLimitConfig, NoteHwpxLimits,
    PackageGraph, PackageGraphLimits, PackageLimits, PatchIntent, PatchLimits,
    PreservationRuleProfile, PreservingPatchEngine, PreservingXmlDocument,
    WriterLimitConfig, WriterLimits, XmlElementSelector,
    document_import::structure::note_conversion::{NoteKindConversion, NoteKindConversionError as E},
};
use std::{collections::BTreeMap, error::Error, io::Cursor};
#[path = "support/document_import_field_fixture.rs"] mod fixture;
#[path = "support/document_import_note_fixture.rs"] mod notes;
type TestResult = Result<(), Box<dyn Error>>;
fn limits() -> NoteHwpxLimits { NoteHwpxLimits::new(NoteHwpxLimitConfig::default()).expect("default limits") }
fn note(kind: &str, ordinal: u32, prefix: &str) -> String {
    let q = if prefix.is_empty() { String::new() } else { format!("{prefix}:") };
    let namespace = if prefix.is_empty() { "xmlns".to_owned() } else { format!("xmlns:{prefix}") };
    format!("<{q}ctrl {namespace}='http://www.hancom.co.kr/hwpml/2011/paragraph'><{q}{kind} instId='101' flag='0' number='7' userChar='0' prefixChar='40' suffixChar='41' ><{q}subList><{q}p id='{ordinal}'><{q}run><{q}t>PRIVATE-NOTE &amp; body</{q}t></{q}run></{q}p></{q}subList></{q}{kind} ></{q}ctrl>")
}
fn bytes(body: &str) -> Result<Vec<u8>, Box<dyn Error>> {
    fixture::package(&format!("<hp:p id='1'><hp:run><hp:t>UNCHANGED</hp:t>{body}<hp:t>TAIL</hp:t></hp:run></hp:p>"))
}
fn expanded(bytes: &[u8]) -> Result<BTreeMap<String, Vec<u8>>, Box<dyn Error>> {
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    (0..reader.entries().len()).map(|i| Ok((reader.entries()[i].path.as_str().to_owned(), reader.read_entry(i)?))).collect()
}
#[test]
fn mixed_batch_preserves_exact_prefixes_tags_attributes_body_and_all_other_parts() -> TestResult {
    let source = bytes(&(note("footNote", 10, "x") + &note("endNote", 11, "") + &note("footNote", 12, "hp")))?;
    let before = expanded(&source)?;
    let forms = fixture::forms(&source, "note-conversion")?;
    let requests = [NoteKindConversion { note_id: &forms.notes()[0].note_id, source_note_sha256: forms.notes()[0].source_anchor.fingerprint_sha256, target_kind: NoteKind::Endnote },
        NoteKindConversion { note_id: &forms.notes()[1].note_id, source_note_sha256: forms.notes()[1].source_anchor.fingerprint_sha256, target_kind: NoteKind::Footnote }];
    let candidate = forms.body_structure().lower_note_kind_batch_candidate(&source, &requests, limits(), WriterLimits::default())?;
    let output = candidate.with_verified_bytes(<[u8]>::to_vec)?;
    let mut expected = before;
    let section = expected.get_mut("Contents/section0.xml").ok_or("section")?;
    let text = String::from_utf8(section.clone())?.replace("x:footNote", "x:endNote").replace("<endNote ", "<footNote ").replace("</endNote ", "</footNote ");
    *section = text.into_bytes();
    assert_eq!(expanded(&output)?, expected);
    assert_eq!(forms.verify_source(&source)?, *forms.receipt());
    let receipt = candidate.receipt();
    assert_eq!((receipt.converted_notes, receipt.total_notes_read_back, receipt.changed_parts), (2, 3, 1));
    assert!(receipt.only_selected_note_names_changed && receipt.body_marker_attributes_and_other_parts_preserved);
    assert!(!receipt.complete_protection_qualified && !receipt.native_number_recalculation_qualified && !receipt.execution_publication_authority);
    for debug in [format!("{candidate:?}"), format!("{:?}", requests[0])] { assert!(!debug.contains("PRIVATE-NOTE") && !debug.contains(forms.notes()[0].note_id.as_str())); }
    Ok(())
}
#[test]
fn foreign_stale_duplicate_empty_and_mixed_noop_requests_fail_atomically() -> TestResult {
    let source = bytes(&(note("footNote", 10, "hp") + &note("endNote", 11, "hp")))?;
    let forms = fixture::forms(&source, "note-conversion")?;
    let foreign = fixture::forms(&source, "foreign-document")?;
    let a = &forms.notes()[0]; let b = &forms.notes()[1];
    let request = || NoteKindConversion { note_id: &a.note_id, source_note_sha256: a.source_anchor.fingerprint_sha256, target_kind: NoteKind::Endnote };
    let lower = |items: &[NoteKindConversion<'_>]| forms.body_structure().lower_note_kind_batch_candidate(&source, items, limits(), WriterLimits::default());
    assert!(matches!(lower(&[]), Err(E::Selection)));
    assert!(matches!(lower(&[request(), request()]), Err(E::Selection)));
    assert!(matches!(lower(&[NoteKindConversion { note_id: &foreign.notes()[0].note_id, ..request() }]), Err(E::Selection)));
    assert!(matches!(lower(&[NoteKindConversion { source_note_sha256: [0; 32], ..request() }]), Err(E::Selection)));
    assert!(matches!(lower(&[request(), NoteKindConversion { note_id: &b.note_id, source_note_sha256: b.source_anchor.fingerprint_sha256, target_kind: NoteKind::Endnote }]), Err(E::NoChange)));
    assert_eq!(forms.verify_source(&source)?, *forms.receipt());
    Ok(())
}
#[test]
fn original_proof_is_operation_local_and_rejects_foreign_model_or_fresh_byte_drift() -> TestResult {
    let source = bytes(&note("footNote", 10, "hp"))?;
    let forms = fixture::forms(&source, "note-conversion")?;
    let foreign = fixture::forms(&source, "foreign-document")?;
    let proof = forms.reconstruct_source_for_verification(&source)?;
    let selected = &forms.notes()[0];
    let requests = [NoteKindConversion { note_id: &selected.note_id, source_note_sha256: selected.source_anchor.fingerprint_sha256, target_kind: NoteKind::Endnote }];
    let result = proof.lower_note_kind_batch_candidate(&forms, &source, &requests, limits(), WriterLimits::default())?;
    let direct = forms.body_structure().lower_note_kind_batch_candidate(&source, &requests, limits(), WriterLimits::default())?;
    assert_eq!(result.receipt(), direct.receipt());
    assert_eq!(result.with_verified_bytes(<[u8]>::to_vec)?, direct.with_verified_bytes(<[u8]>::to_vec)?);
    assert!(matches!(proof.lower_note_kind_batch_candidate(&foreign, &source, &requests, limits(), WriterLimits::default()), Err(E::Source)));
    let changed = bytes(&note("footNote", 12, "hp"))?;
    assert!(matches!(proof.lower_note_kind_batch_candidate(&forms, &changed, &requests, limits(), WriterLimits::default()), Err(E::Source)));
    assert!(matches!(forms.body_structure().lower_note_kind_batch_candidate(&changed, &requests, limits(), WriterLimits::default()), Err(E::Source)));
    Ok(())
}
#[test]
fn observed_ancestor_locks_are_not_converted_into_permission() -> TestResult {
    let mut guard_rejections = 0;
    for lock in ["true", "1", "unknown"] {
        let table = format!(r#"<hp:tbl id="9" zOrder="0" numberingType="TABLE" textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="{lock}" dropcapstyle="None" pageBreak="CELL" repeatHeader="0" rowCnt="1" colCnt="1" cellSpacing="0" borderFillIDRef="1" noAdjust="0"><hp:sz width="2000" widthRelTo="ABSOLUTE" height="1000" heightRelTo="ABSOLUTE" protect="0"/><hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP" horzAlign="LEFT" vertOffset="0" horzOffset="0"/><hp:outMargin left="0" right="0" top="0" bottom="0"/><hp:inMargin left="0" right="0" top="0" bottom="0"/><hp:tr><hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="0" borderFillIDRef="1"><hp:cellAddr colAddr="0" rowAddr="0"/><hp:cellSpan colSpan="1" rowSpan="1"/><hp:cellSz width="1000" height="500"/><hp:cellMargin left="0" right="0" top="0" bottom="0"/><hp:subList><hp:p id="2"><hp:run>{}</hp:run></hp:p></hp:subList></hp:tc></hp:tr></hp:tbl>"#, note("footNote", 10, "hp"));
        let source = bytes(&table)?;
        // Malformed native boolean values can be rejected by the importer
        // before the conversion guard; neither stage grants permission.
        let Ok(forms) = fixture::forms(&source, "note-conversion") else { continue };
        let selected = &forms.notes()[0];
        let request = NoteKindConversion { note_id: &selected.note_id, source_note_sha256: selected.source_anchor.fingerprint_sha256, target_kind: NoteKind::Endnote };
        assert!(matches!(forms.body_structure().lower_note_kind_batch_candidate(&source, &[request], limits(), WriterLimits::default()), Err(E::Protection)));
        guard_rejections += 1;
    }
    assert!(guard_rejections > 0, "at least one admitted locked table must reach the original guard");
    Ok(())
}
#[test]
fn finite_selection_section_output_and_writer_limits_are_retained() -> TestResult {
    let source = bytes(&(note("footNote", 10, "hp") + &note("footNote", 11, "hp")))?;
    let forms = fixture::forms(&source, "note-conversion")?;
    let requests: Vec<_> = forms.notes().iter().map(|n| NoteKindConversion { note_id: &n.note_id, source_note_sha256: n.source_anchor.fingerprint_sha256, target_kind: NoteKind::Endnote }).collect();
    for config in [NoteHwpxLimitConfig { notes: 1, ..NoteHwpxLimitConfig::default() },
        NoteHwpxLimitConfig { section_bytes: 1, ..NoteHwpxLimitConfig::default() },
        NoteHwpxLimitConfig { section_bytes: 1, payload_bytes: 1, output_bytes: 1, ..NoteHwpxLimitConfig::default() }] {
        assert!(matches!(forms.body_structure().lower_note_kind_batch_candidate(&source, &requests, NoteHwpxLimits::new(config)?, WriterLimits::default()), Err(E::Limit)));
    }
    assert!(matches!(forms.body_structure().lower_note_kind_batch_candidate(&source, &requests, limits(), WriterLimits::new(WriterLimitConfig { max_output_bytes: 1 })?), Err(E::Writer)));
    Ok(())
}
#[test]
fn one_protection_scan_per_part_and_complete_readback_for_large_partial_batch() -> TestResult {
    let body: String = (0..64).map(|i| note("footNote", 10 + i, "hp")).collect();
    let source = bytes(&body)?;
    let forms = fixture::forms(&source, "note-conversion")?;
    let selected: Vec<_> = forms.notes().iter().step_by(2).map(|n| NoteKindConversion { note_id: &n.note_id, source_note_sha256: n.source_anchor.fingerprint_sha256, target_kind: NoteKind::Endnote }).collect();
    let output = forms.body_structure().lower_note_kind_batch_candidate(&source, &selected, limits(), WriterLimits::default())?;
    let section = expanded(&source)?.remove("Contents/section0.xml").ok_or("section")?;
    let xml = PreservingXmlDocument::parse(&section)?;
    assert_eq!(output.receipt().protection_element_visits, xml.elements().len() * 2);
    assert_eq!(output.receipt().converted_notes, 32);
    let next = output.with_verified_bytes(|b| fixture::forms(b, "note-conversion"))??;
    assert_eq!(next.notes().len(), 64);
    for (i, note) in next.notes().iter().enumerate() { assert_eq!(note.native_kind, if i % 2 == 0 { "endNote" } else { "footNote" }); }
    Ok(())
}
#[test]
fn nine_locked_note_sources_convert_six_and_reject_three_original_id_collisions() -> TestResult {
    let mut lanes = [0usize; 3];
    let (mut converted, mut rejected) = (0usize, 0usize);
    for input in notes::actual_inputs()? {
        let forms = fixture::forms(&input.bytes, "note-conversion")?;
        assert_eq!(forms.notes().len(), input.expected_notes);
        let requests: Vec<_> = forms.notes().iter().map(|n| NoteKindConversion { note_id: &n.note_id, source_note_sha256: n.source_anchor.fingerprint_sha256,
            target_kind: if n.native_kind == "footNote" { NoteKind::Endnote } else { NoteKind::Footnote } }).collect();
        // The old positive expectation was wrong for the mixed-case inputs:
        // the original generator reused IDs 101/102, and native save kept them.
        // Independently require that exact SOURCE rejection, never waive it.
        let mut reader = BoundedZipReader::open(Cursor::new(&input.bytes), PackageLimits::default())?;
        let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
        let original_ids = hwpx_package::IdIndex::build_with_graph_limits(&mut reader, &graph,
            PackageGraphLimits::default(), IdRuleProfile::hwpml_2011_shape_v6(), IdIndexLimits::default());
        let output = forms.body_structure().lower_note_kind_batch_candidate(&input.bytes, &requests, limits(), WriterLimits::default());
        if input.expected_notes == 2 {
            let error = original_ids.err().ok_or("expected original mixed-input ID rejection")?;
            let issues = error.validation().ok_or("expected ID validation report")?.issues();
            assert_eq!(issues.len(), 2);
            assert!(issues.iter().all(|i| i.code() == "id_index_duplicate_declaration"
                && i.expected_kind() == Some(hwpx_package::IdKind::Paragraph)));
            assert!(matches!(output, Err(E::Patch("id_index_duplicate_declaration"))));
            rejected += 1;
        } else {
            original_ids?;
            let candidate = output?;
            assert_eq!(candidate.receipt().converted_notes, input.expected_notes);
            assert!(!candidate.receipt().native_number_recalculation_qualified);
            converted += 1;
        }
        assert_eq!(forms.verify_source(&input.bytes)?, *forms.receipt());
        lanes[match input.lane { "generated" => 0, "saved" => 1, "reopened" => 2, _ => return Err("lane".into()) }] += 1;
    }
    assert_eq!(lanes, [3, 3, 3]);
    assert_eq!((converted, rejected), (6, 3));
    Ok(())
}
#[test]
fn raw_patch_intent_cannot_rename_non_note_unknown_namespace_or_noop_tags() -> TestResult {
    for (body, name, kind) in [("<hp:t>PRIVATE-NOTE</hp:t>".to_owned(), "t", NoteKind::Endnote),
        ("<u:footNote instId='101'><u:subList/></u:footNote>".to_owned(), "footNote", NoteKind::Endnote),
        (note("footNote", 10, "hp"), "footNote", NoteKind::Footnote)] {
        let source = bytes(&body)?;
        let mut reader = BoundedZipReader::open(Cursor::new(source), PackageLimits::default())?;
        let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
        let part_index = reader.entries().iter().position(|p| p.path.as_str() == "Contents/section0.xml").ok_or("section")?;
        let path = reader.entries()[part_index].path.clone();
        let xml = PreservingXmlDocument::parse(&reader.read_entry(part_index)?)?;
        let index = xml.elements().iter().position(|n| n.name().local_name() == name).ok_or("element")?;
        let intent = PatchIntent::ConvertNoteKind { target: XmlElementSelector::bind(&path, &xml, index)?, kind };
        assert!(!format!("{intent:?}").contains("PRIVATE-NOTE"));
        assert!(PreservingPatchEngine::apply_with_limits_and_preservation_profile(&mut reader, &graph, PackageGraphLimits::default(), IdRuleProfile::hwpml_2011_shape_v6(), IdIndexLimits::default(), PatchLimits::default(), PreservationRuleProfile::Hangul2020PreviewTextV2, &[intent]).is_err());
    }
    Ok(())
}
#[test]
fn locked_note_source_id_diagnostic_does_not_execute_conversion() -> TestResult {
    // Independently inspect the ORIGINAL nine archives, never normalize IDs or
    // turn this diagnostic pass into conversion/native acceptance.
    let mut result = Vec::new();
    for input in notes::actual_inputs()? {
        let mut reader = BoundedZipReader::open(Cursor::new(&input.bytes), PackageLimits::default())?;
        let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
        let check = hwpx_package::IdIndex::build_with_graph_limits(&mut reader, &graph,
            PackageGraphLimits::default(), IdRuleProfile::hwpml_2011_shape_v6(), IdIndexLimits::default());
        let mut observed = Vec::new();
        let mut counts = BTreeMap::new();
        if let Err(error) = check {
            let report = error.validation().ok_or("original ID index failed without validation report")?;
            for issue in report.issues() {
                *counts.entry(issue.code()).or_insert(0usize) += 1;
                if observed.len() >= 8 { continue; }
                let mut positions = Vec::new();
                for location in [Some(issue.source()), issue.related()].into_iter().flatten() {
                    let part = reader.entries().iter().position(|p| &p.path == location.part()).ok_or("issue part")?;
                    let xml = PreservingXmlDocument::parse(&reader.read_entry(part)?)?;
                    let mut index = Some(location.element_index());
                    let mut tags = Vec::new();
                    while let Some(i) = index {
                        let node = &xml.elements()[i];
                        tags.push(node.name().local_name().to_owned()); index = node.parent();
                    }
                    tags.reverse();
                    positions.push(tags);
                }
                observed.push(serde_json::json!({"code": issue.code(), "expected_kind": format!("{:?}", issue.expected_kind()), "source_and_related_ancestry": positions}));
            }
        }
        result.push(serde_json::json!({"lane": input.lane, "expected_notes": input.expected_notes, "original_source_issue_counts": counts, "sample": observed}));
    }
    assert_eq!(result.len(), 9);
    println!("NOTE_SOURCE_ID_DIAGNOSTIC {}", serde_json::to_string(&result)?);
    Ok(())
}
