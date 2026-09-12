#![allow(clippy::expect_used, clippy::too_many_lines)] // Exact fixtures keep failures local.

use domain_ir::{
    LogicalId, NOTE_ENGINE_SCHEMA_VERSION, NoteAnchor, NoteAutoNumberFormat, NoteBuilder,
    NoteDocumentState, NoteDocumentStateDraft, NoteEntry, NoteKind, NoteLimitConfig, NoteLimits,
    NoteLineStyle, NoteLineType, NoteLineWidth, NoteMarkerProperties, NoteNativeTag,
    NoteNumberFormat, NoteNumberingRestart, NoteOperation, NotePlacement, NoteRequest,
    NoteRequestDraft, NoteSectionState, NoteSpacing, NoteStyle,
};
use hwpx_package::{
    NOTE_HWPX_PROFILE_ID, NoteHwpxBuilder, NoteHwpxError, NoteHwpxLimitConfig, NoteHwpxLimits,
    NoteHwpxLowerer, NoteHwpxReader,
};

const A: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const B: &str = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
const FLOW_SOURCE: &str = "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc";
const FLOW_TARGET: &str = "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd";
const EMPTY_SHA256: &str = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";
const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";

fn state_limits() -> NoteLimits {
    NoteLimits::new(NoteLimitConfig::default()).expect("valid state limits")
}

fn hwpx_limits() -> NoteHwpxLimits {
    NoteHwpxLimits::new(NoteHwpxLimitConfig::default()).expect("valid HWPX limits")
}

fn id(value: &str) -> LogicalId {
    LogicalId::parse(value).expect("valid logical id")
}

fn style(kind: NoteKind) -> NoteStyle {
    NoteStyle {
        kind,
        auto_number_format: NoteAutoNumberFormat {
            format: NoteNumberFormat::Digit,
            user_character: String::new(),
            prefix_character: String::new(),
            suffix_character: ")".to_owned(),
            superscript: false,
        },
        note_line: NoteLineStyle {
            length_hwp_units: -1,
            line_type: NoteLineType::Solid,
            width: NoteLineWidth::Mm0_12,
            color_rgb: 0,
        },
        spacing: NoteSpacing {
            between_notes_hwp_units: 283,
            below_line_hwp_units: 567,
            above_line_hwp_units: 850,
        },
        numbering_restart: NoteNumberingRestart::Continuous,
        new_number: 1,
        placement: match kind {
            NoteKind::Footnote => NotePlacement::EachColumn,
            NoteKind::Endnote => NotePlacement::EndOfDocument,
        },
        beneath_text: false,
        opaque_style_sha256: A.to_owned(),
        locked: false,
    }
}

fn section() -> NoteSectionState {
    NoteSectionState {
        section_id: id("section-main"),
        footnote_style: style(NoteKind::Footnote),
        endnote_style: style(NoteKind::Endnote),
        opaque_section_state_sha256: B.to_owned(),
        locked: false,
    }
}

fn state(notes: Vec<NoteEntry>) -> NoteDocumentState {
    NoteDocumentState::from_draft(
        NoteDocumentStateDraft {
            schema_version: NOTE_ENGINE_SCHEMA_VERSION.to_owned(),
            sections: vec![section()],
            notes,
            non_note_content_sha256: A.to_owned(),
            style_catalog_sha256: B.to_owned(),
            numbering_inventory_sha256: A.to_owned(),
            reference_inventory_sha256: B.to_owned(),
            resource_inventory_sha256: A.to_owned(),
            document_protection_sha256: B.to_owned(),
            opaque_document_state_sha256: A.to_owned(),
            document_locked: false,
        },
        state_limits(),
    )
    .expect("valid state")
}

fn paragraph_ids() -> Vec<LogicalId> {
    vec![id("paragraph-one"), id("paragraph-two")]
}

fn source_xml() -> Vec<u8> {
    format!(
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?><hs:sec xmlns:hs=\"http://www.hancom.co.kr/hwpml/2011/section\" xmlns:hp=\"{PARAGRAPH_NS}\"><!--PRESERVE-OUTSIDE--><hp:p id=\"1\" paraPrIDRef=\"0\" styleIDRef=\"0\" pageBreak=\"0\" columnBreak=\"0\" merged=\"0\"><hp:run charPrIDRef=\"7\"><hp:t>A</hp:t><!--PRESERVE-IN-RUN--><hp:t>B</hp:t></hp:run></hp:p><hp:p id=\"2\" paraPrIDRef=\"0\" styleIDRef=\"0\" pageBreak=\"0\" columnBreak=\"0\" merged=\"0\"><hp:run charPrIDRef=\"9\"><hp:t>TAIL</hp:t></hp:run></hp:p></hs:sec>"
    )
    .into_bytes()
}

fn payload(text: &str) -> Vec<u8> {
    format!(
        "<hp:subList xmlns:hp=\"{PARAGRAPH_NS}\" id=\"\" textDirection=\"HORIZONTAL\" lineWrap=\"BREAK\" vertAlign=\"TOP\" linkListIDRef=\"0\" linkListNextIDRef=\"0\" textWidth=\"0\" textHeight=\"0\" hasTextRef=\"0\" hasNumRef=\"0\"><hp:p id=\"101\" paraPrIDRef=\"2\" styleIDRef=\"3\" pageBreak=\"0\" columnBreak=\"0\" merged=\"0\"><hp:run charPrIDRef=\"4\"><hp:t>{text}</hp:t></hp:run><hp:run charPrIDRef=\"5\"><hp:t charStyleIDRef=\"6\">SECOND</hp:t></hp:run></hp:p><hp:p id=\"102\" paraPrIDRef=\"7\" styleIDRef=\"8\" pageBreak=\"0\" columnBreak=\"0\" merged=\"0\"><hp:run charPrIDRef=\"9\"><hp:t>THIRD</hp:t></hp:run></hp:p></hp:subList>"
    )
    .into_bytes()
}

fn note_for(
    source: &[u8],
    body: &[u8],
    kind: NoteKind,
    paragraph: usize,
    run: u32,
    inline: u32,
    native_id: u32,
) -> NoteEntry {
    let digests = NoteHwpxReader::inspect_payload(body, hwpx_limits()).expect("payload digests");
    NoteEntry {
        identity: domain_ir::NoteIdentity {
            logical_note_id: id(&format!("note-{native_id}")),
            native_instance_id: native_id,
        },
        anchor: NoteAnchor {
            section_id: id("section-main"),
            paragraph_id: paragraph_ids()[paragraph].clone(),
            run_ordinal: run,
            inline_ordinal: inline,
        },
        kind,
        native_tag: match kind {
            NoteKind::Footnote => NoteNativeTag::FootNote,
            NoteKind::Endnote => NoteNativeTag::EndNote,
        },
        marker: NoteMarkerProperties {
            flags: 17,
            number: 3,
            user_character: Some("※".to_owned()),
            prefix_character: Some("&".to_owned()),
            suffix_character: Some(")".to_owned()),
        },
        body_graph_sha256: digests.body_graph_sha256,
        plain_text_sha256: digests.plain_text_sha256,
        marker_style_sha256: NoteHwpxReader::marker_style_sha256_at(
            source,
            u32::try_from(paragraph).expect("small paragraph"),
            run,
            hwpx_limits(),
        )
        .expect("marker style"),
        body_style_sha256: digests.body_style_sha256,
        opaque_native_payload_sha256: EMPTY_SHA256.to_owned(),
        opaque_properties: Vec::new(),
        locked: false,
    }
}

fn domain_plan(source: &NoteDocumentState, note: NoteEntry) -> domain_ir::NotePlan {
    let request = NoteRequest::from_draft(
        NoteRequestDraft {
            schema_version: NOTE_ENGINE_SCHEMA_VERSION.to_owned(),
            request_id: id("request-insert"),
            expected_source_state_sha256: source
                .canonical_sha256(state_limits())
                .expect("source digest"),
            expected_document_flow_sha256: FLOW_SOURCE.to_owned(),
            target_document_flow_sha256: FLOW_TARGET.to_owned(),
            operation: NoteOperation::Insert {
                insertion_index: source.notes().len(),
                note,
            },
        },
        source,
        FLOW_SOURCE,
        state_limits(),
    )
    .expect("request");
    NoteBuilder::plan(source, &request, FLOW_SOURCE, state_limits()).expect("domain plan")
}

#[test]
fn inserts_exact_footnote_and_endnote_with_full_body_and_marker_state() {
    for (kind, tag) in [
        (NoteKind::Footnote, "footNote"),
        (NoteKind::Endnote, "endNote"),
    ] {
        let source = source_xml();
        let body = payload("BODY &amp; PRIVATE");
        let source_state = state(Vec::new());
        let note = note_for(&source, &body, kind, 0, 0, 1, 41);
        let domain = domain_plan(&source_state, note.clone());
        let plan = NoteHwpxBuilder::plan(
            &source,
            &source_state,
            &domain,
            FLOW_SOURCE,
            &paragraph_ids(),
            &body,
            state_limits(),
            hwpx_limits(),
        )
        .expect("adapter plan");
        let (output, receipt) = NoteHwpxLowerer::lower_section_with_receipt(
            &source,
            &body,
            &plan,
            &source_state,
            FLOW_SOURCE,
            state_limits(),
            hwpx_limits(),
        )
        .expect("lowering");
        let output_text = String::from_utf8(output.clone()).expect("UTF-8 output");
        assert!(output_text.contains(&format!("<hp:{tag} flag=\"17\" number=\"3\" userChar=\"※\" prefixChar=\"&amp;\" suffixChar=\")\" instId=\"41\">")));
        assert!(output_text.contains("BODY &amp; PRIVATE"));
        assert!(output_text.contains("<!--PRESERVE-OUTSIDE-->"));
        assert!(output_text.contains("<!--PRESERVE-IN-RUN-->"));
        assert_eq!(receipt.profile_id, NOTE_HWPX_PROFILE_ID);
        assert_eq!(receipt.capability_id, kind.insert_capability_id());
        assert_eq!(receipt.inserted_notes, 1);
        assert_eq!(receipt.payload_bytes, body.len());
        let target = NoteBuilder::build(&domain, &source_state, FLOW_SOURCE, state_limits())
            .expect("domain result")
            .state;
        let readback = NoteHwpxReader::read_section(
            &output,
            &target,
            &paragraph_ids(),
            state_limits(),
            hwpx_limits(),
        )
        .expect("exact readback");
        assert_eq!(readback.note_count, 1);
        assert_eq!(readback.state.notes()[0], note);
    }
}

#[test]
fn inserts_at_exact_second_paragraph_boundary_and_preserves_every_other_byte() {
    let source = source_xml();
    let body = payload("SECOND-PARAGRAPH");
    let source_state = state(Vec::new());
    let note = note_for(&source, &body, NoteKind::Footnote, 1, 0, 0, 52);
    let domain = domain_plan(&source_state, note);
    let plan = NoteHwpxBuilder::plan(
        &source,
        &source_state,
        &domain,
        FLOW_SOURCE,
        &paragraph_ids(),
        &body,
        state_limits(),
        hwpx_limits(),
    )
    .expect("plan");
    let output = NoteHwpxLowerer::lower_section(
        &source,
        &body,
        &plan,
        &source_state,
        FLOW_SOURCE,
        state_limits(),
        hwpx_limits(),
    )
    .expect("lowering");
    let source_text = String::from_utf8(source).expect("source UTF-8");
    let output_text = String::from_utf8(output).expect("output UTF-8");
    let marker = "<hp:run charPrIDRef=\"9\">";
    let source_run = source_text.find(marker).expect("second run");
    let output_run = output_text.find(marker).expect("second run");
    assert_eq!(&source_text[..source_run], &output_text[..output_run]);
    assert!(output_text[output_run..].starts_with(marker));
    assert!(output_text.contains("instId=\"52\"><hp:subList"));
    assert!(output_text.contains("</hp:ctrl><hp:t>TAIL</hp:t>"));
}

#[test]
fn complete_existing_note_projection_detects_marker_body_style_and_anchor_drift() {
    let source = source_xml();
    let body = payload("EXISTING");
    let source_state = state(Vec::new());
    let note = note_for(&source, &body, NoteKind::Endnote, 0, 0, 1, 61);
    let domain = domain_plan(&source_state, note.clone());
    let plan = NoteHwpxBuilder::plan(
        &source,
        &source_state,
        &domain,
        FLOW_SOURCE,
        &paragraph_ids(),
        &body,
        state_limits(),
        hwpx_limits(),
    )
    .expect("plan");
    let output = NoteHwpxLowerer::lower_section(
        &source,
        &body,
        &plan,
        &source_state,
        FLOW_SOURCE,
        state_limits(),
        hwpx_limits(),
    )
    .expect("output");
    let target = NoteBuilder::build(&domain, &source_state, FLOW_SOURCE, state_limits())
        .expect("domain result")
        .state;
    assert!(
        NoteHwpxReader::read_section(
            &output,
            &target,
            &paragraph_ids(),
            state_limits(),
            hwpx_limits()
        )
        .is_ok()
    );

    let mut marker_drift = target.notes()[0].clone();
    marker_drift.marker.flags = 18;
    assert_eq!(
        NoteHwpxReader::read_section(
            &output,
            &state(vec![marker_drift]),
            &paragraph_ids(),
            state_limits(),
            hwpx_limits()
        ),
        Err(NoteHwpxError::ProjectionMismatch)
    );
    let mut body_drift = target.notes()[0].clone();
    body_drift.body_graph_sha256 = A.to_owned();
    assert_eq!(
        NoteHwpxReader::read_section(
            &output,
            &state(vec![body_drift]),
            &paragraph_ids(),
            state_limits(),
            hwpx_limits()
        ),
        Err(NoteHwpxError::ProjectionMismatch)
    );
    let wrong_map = vec![id("paragraph-two"), id("paragraph-one")];
    assert_eq!(
        NoteHwpxReader::read_section(&output, &target, &wrong_map, state_limits(), hwpx_limits()),
        Err(NoteHwpxError::ProjectionMismatch)
    );
}

#[test]
fn payload_profile_rejects_unknown_graph_missing_fields_and_astral_marker() {
    let body = payload("VALID");
    let unknown = String::from_utf8(body.clone())
        .expect("UTF-8")
        .replace("<hp:t>VALID</hp:t>", "<hp:tbl/>");
    assert_eq!(
        NoteHwpxReader::inspect_payload(unknown.as_bytes(), hwpx_limits()),
        Err(NoteHwpxError::InvalidPayload)
    );
    let missing = String::from_utf8(body.clone())
        .expect("UTF-8")
        .replace(" paraPrIDRef=\"2\"", "");
    assert_eq!(
        NoteHwpxReader::inspect_payload(missing.as_bytes(), hwpx_limits()),
        Err(NoteHwpxError::InvalidPayload)
    );
    let direct_text = String::from_utf8(body.clone())
        .expect("UTF-8")
        .replace("<hp:t>VALID</hp:t>", "STRAY<hp:t>VALID</hp:t>");
    assert_eq!(
        NoteHwpxReader::inspect_payload(direct_text.as_bytes(), hwpx_limits()),
        Err(NoteHwpxError::InvalidPayload)
    );
    let commented = String::from_utf8(body.clone())
        .expect("UTF-8")
        .replace("<hp:t>VALID</hp:t>", "<hp:t>VA<!-- hidden -->LID</hp:t>");
    assert_eq!(
        NoteHwpxReader::inspect_payload(commented.as_bytes(), hwpx_limits()),
        Err(NoteHwpxError::InvalidPayload)
    );

    let source = source_xml();
    let source_state = state(Vec::new());
    let mut note = note_for(&source, &body, NoteKind::Footnote, 0, 0, 1, 71);
    note.marker.user_character = Some("😀".to_owned());
    let domain = domain_plan(&source_state, note);
    assert_eq!(
        NoteHwpxBuilder::plan(
            &source,
            &source_state,
            &domain,
            FLOW_SOURCE,
            &paragraph_ids(),
            &body,
            state_limits(),
            hwpx_limits()
        )
        .expect_err("astral WCHAR must fail"),
        NoteHwpxError::NonRepresentable
    );
}

#[test]
fn request_and_build_reject_section_payload_state_flow_and_map_drift() {
    let source = source_xml();
    let body = payload("BOUND");
    let source_state = state(Vec::new());
    let note = note_for(&source, &body, NoteKind::Footnote, 0, 0, 1, 81);
    let domain = domain_plan(&source_state, note);
    let plan = NoteHwpxBuilder::plan(
        &source,
        &source_state,
        &domain,
        FLOW_SOURCE,
        &paragraph_ids(),
        &body,
        state_limits(),
        hwpx_limits(),
    )
    .expect("plan");

    let mut section_drift = source.clone();
    section_drift.extend_from_slice(b" ");
    assert_eq!(
        NoteHwpxLowerer::lower_section(
            &section_drift,
            &body,
            &plan,
            &source_state,
            FLOW_SOURCE,
            state_limits(),
            hwpx_limits()
        ),
        Err(NoteHwpxError::SourceDrift)
    );
    let payload_drift = payload("CHANGED");
    assert_eq!(
        NoteHwpxLowerer::lower_section(
            &source,
            &payload_drift,
            &plan,
            &source_state,
            FLOW_SOURCE,
            state_limits(),
            hwpx_limits()
        ),
        Err(NoteHwpxError::SourceDrift)
    );
    assert_eq!(
        NoteHwpxLowerer::lower_section(
            &source,
            &body,
            &plan,
            &source_state,
            FLOW_TARGET,
            state_limits(),
            hwpx_limits()
        ),
        Err(NoteHwpxError::SourceDrift)
    );
    let wrong_map = vec![id("paragraph-other"), id("paragraph-two")];
    assert_eq!(
        NoteHwpxBuilder::plan(
            &source,
            &source_state,
            &domain,
            FLOW_SOURCE,
            &wrong_map,
            &body,
            state_limits(),
            hwpx_limits()
        )
        .expect_err("anchor map drift must fail"),
        NoteHwpxError::NonRepresentable
    );
}

#[test]
fn limits_error_codes_json_and_debug_are_bounded_and_redacted() {
    assert_eq!(
        NoteHwpxLimits::new(NoteHwpxLimitConfig {
            payload_bytes: 0,
            ..NoteHwpxLimitConfig::default()
        }),
        Err(NoteHwpxError::InvalidLimit)
    );
    let source = source_xml();
    let body = payload("PRIVATE-NOTE-TEXT");
    let source_state = state(Vec::new());
    let note = note_for(&source, &body, NoteKind::Endnote, 0, 0, 1, 91);
    let domain = domain_plan(&source_state, note);
    let plan = NoteHwpxBuilder::plan(
        &source,
        &source_state,
        &domain,
        FLOW_SOURCE,
        &paragraph_ids(),
        &body,
        state_limits(),
        hwpx_limits(),
    )
    .expect("plan");
    let json = plan.canonical_json(hwpx_limits()).expect("bounded JSON");
    let json_text = String::from_utf8(json).expect("UTF-8 JSON");
    assert!(!json_text.contains("PRIVATE-NOTE-TEXT"));
    let debug = format!("{plan:?}");
    assert!(!debug.contains("paragraph-one"));
    assert!(!debug.contains("PRIVATE-NOTE-TEXT"));
    assert!(!debug.contains(FLOW_SOURCE));
    assert_eq!(NoteHwpxError::SourceDrift.code(), "note_hwpx_source_drift");

    let tiny = NoteHwpxLimits::new(NoteHwpxLimitConfig {
        section_bytes: source.len(),
        payload_bytes: 8,
        output_bytes: source.len() + 8,
        ..NoteHwpxLimitConfig::default()
    })
    .expect("tiny valid limits");
    assert_eq!(
        NoteHwpxReader::inspect_payload(&body, tiny),
        Err(NoteHwpxError::InputLimit)
    );
}

#[test]
fn foreign_namespace_note_and_noncanonical_native_shape_fail_closed() {
    let source_state = state(Vec::new());
    let foreign = format!(
        "<hs:sec xmlns:hs=\"http://www.hancom.co.kr/hwpml/2011/section\" xmlns:hp=\"{PARAGRAPH_NS}\" xmlns:x=\"urn:foreign\"><hp:p><hp:run><hp:ctrl><x:footNote/></hp:ctrl></hp:run></hp:p><hp:p/></hs:sec>"
    );
    assert_eq!(
        NoteHwpxReader::read_section(
            foreign.as_bytes(),
            &source_state,
            &paragraph_ids(),
            state_limits(),
            hwpx_limits()
        ),
        Err(NoteHwpxError::InvalidNote)
    );
}
