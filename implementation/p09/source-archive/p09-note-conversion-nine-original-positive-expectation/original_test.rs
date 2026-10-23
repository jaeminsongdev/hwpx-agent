// Historical original positive expectation, archived before correction.
// The original 003/004 failures remain authoritative; this is not a test target.
#[test]
fn nine_locked_generated_saved_reopened_packages_convert_without_relabelling_native_failures() -> TestResult {
    let mut lanes = [0usize; 3];
    for input in notes::actual_inputs()? {
        let forms = fixture::forms(&input.bytes, "note-conversion")?;
        assert_eq!(forms.notes().len(), input.expected_notes);
        let requests: Vec<_> = forms.notes().iter().map(|n| NoteKindConversion { note_id: &n.note_id, source_note_sha256: n.source_anchor.fingerprint_sha256,
            target_kind: if n.native_kind == "footNote" { NoteKind::Endnote } else { NoteKind::Footnote } }).collect();
        let candidate = forms.body_structure().lower_note_kind_batch_candidate(&input.bytes, &requests, limits(), WriterLimits::default())?;
        assert_eq!(candidate.receipt().converted_notes, input.expected_notes);
        assert!(!candidate.receipt().native_number_recalculation_qualified);
        assert_eq!(forms.verify_source(&input.bytes)?, *forms.receipt());
        lanes[match input.lane { "generated" => 0, "saved" => 1, "reopened" => 2, _ => return Err("lane".into()) }] += 1;
    }
    assert_eq!(lanes, [3, 3, 3]);
    Ok(())
}
