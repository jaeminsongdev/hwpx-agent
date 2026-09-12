#![allow(clippy::expect_used)] // Fixtures keep failures local and readable.

use domain_ir::{
    LogicalId, NOTE_ENGINE_SCHEMA_VERSION, NoteAnchor, NoteAutoNumberFormat, NoteBuilder,
    NoteDocumentState, NoteDocumentStateDraft, NoteEntry, NoteError, NoteExportFormat,
    NoteExportSelection, NoteIdentity, NoteKind, NoteLimitConfig, NoteLimits, NoteLineStyle,
    NoteLineType, NoteLineWidth, NoteMarkerProperties, NoteNativeTag, NoteNumberFormat,
    NoteNumberingRestart, NoteOperation, NotePlacement, NoteRequest, NoteRequestDraft,
    NoteSectionState, NoteSpacing, NoteStyle, OpaqueNoteProperty,
};

const FLOW_A: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const FLOW_B: &str = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";

fn limits() -> NoteLimits {
    NoteLimits::new(NoteLimitConfig::default()).expect("valid limits")
}

fn id(value: &str) -> LogicalId {
    LogicalId::parse(value).expect("valid logical id")
}

fn identity(index: u32) -> NoteIdentity {
    NoteIdentity {
        logical_note_id: id(&format!("note-{index}")),
        native_instance_id: index,
    }
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
        opaque_style_sha256: FLOW_A.to_owned(),
        locked: false,
    }
}

fn section(index: u32) -> NoteSectionState {
    NoteSectionState {
        section_id: id(&format!("section-{index}")),
        footnote_style: style(NoteKind::Footnote),
        endnote_style: style(NoteKind::Endnote),
        opaque_section_state_sha256: FLOW_B.to_owned(),
        locked: false,
    }
}

fn note(index: u32, section_index: u32, kind: NoteKind) -> NoteEntry {
    NoteEntry {
        identity: identity(index),
        anchor: NoteAnchor {
            section_id: id(&format!("section-{section_index}")),
            paragraph_id: id(&format!("paragraph-{index}")),
            run_ordinal: index,
            inline_ordinal: 0,
        },
        kind,
        native_tag: match kind {
            NoteKind::Footnote => NoteNativeTag::FootNote,
            NoteKind::Endnote => NoteNativeTag::EndNote,
        },
        marker: NoteMarkerProperties {
            flags: index,
            number: u16::try_from(index).expect("small fixture"),
            user_character: None,
            prefix_character: None,
            suffix_character: Some(")".to_owned()),
        },
        body_graph_sha256: FLOW_A.to_owned(),
        plain_text_sha256: Some(FLOW_B.to_owned()),
        marker_style_sha256: FLOW_A.to_owned(),
        body_style_sha256: FLOW_B.to_owned(),
        opaque_native_payload_sha256: FLOW_A.to_owned(),
        opaque_properties: vec![OpaqueNoteProperty {
            namespace: "private.note".to_owned(),
            name: format!("property-{index}"),
            value_sha256: FLOW_B.to_owned(),
        }],
        locked: false,
    }
}

fn state_with(
    sections: Vec<NoteSectionState>,
    notes: Vec<NoteEntry>,
    document_locked: bool,
) -> Result<NoteDocumentState, NoteError> {
    NoteDocumentState::from_draft(
        NoteDocumentStateDraft {
            schema_version: NOTE_ENGINE_SCHEMA_VERSION.to_owned(),
            sections,
            notes,
            non_note_content_sha256: FLOW_A.to_owned(),
            style_catalog_sha256: FLOW_B.to_owned(),
            numbering_inventory_sha256: FLOW_A.to_owned(),
            reference_inventory_sha256: FLOW_B.to_owned(),
            resource_inventory_sha256: FLOW_A.to_owned(),
            document_protection_sha256: FLOW_B.to_owned(),
            opaque_document_state_sha256: FLOW_A.to_owned(),
            document_locked,
        },
        limits(),
    )
}

fn state(notes: Vec<NoteEntry>) -> NoteDocumentState {
    state_with(vec![section(1), section(2)], notes, false).expect("valid state")
}

fn request(source: &NoteDocumentState, operation: NoteOperation) -> Result<NoteRequest, NoteError> {
    let target_flow = if matches!(operation, NoteOperation::PrepareExport { .. }) {
        FLOW_A
    } else {
        FLOW_B
    };
    NoteRequest::from_draft(
        NoteRequestDraft {
            schema_version: NOTE_ENGINE_SCHEMA_VERSION.to_owned(),
            request_id: id("request-1"),
            expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
            expected_document_flow_sha256: FLOW_A.to_owned(),
            target_document_flow_sha256: target_flow.to_owned(),
            operation,
        },
        source,
        FLOW_A,
        limits(),
    )
}

fn build(source: &NoteDocumentState, operation: NoteOperation) -> domain_ir::NoteResult {
    let request = request(source, operation).expect("valid request");
    let plan = NoteBuilder::plan(source, &request, FLOW_A, limits()).expect("valid plan");
    NoteBuilder::build(&plan, source, FLOW_A, limits()).expect("valid result")
}

#[test]
fn inserts_footnote_and_endnote_with_exact_capability_and_native_tag() {
    let mut current = state(Vec::new());
    for (index, kind, expected) in [
        (1, NoteKind::Footnote, "ref.footnote_insert"),
        (2, NoteKind::Endnote, "ref.endnote_insert"),
    ] {
        let operation = NoteOperation::Insert {
            insertion_index: current.notes().len(),
            note: note(index, 1, kind),
        };
        assert_eq!(operation.capability_id(), expected);
        current = build(&current, operation).state;
    }
    assert_eq!(current.notes().len(), 2);
    assert_eq!(current.notes()[0].native_tag, NoteNativeTag::FootNote);
    assert_eq!(current.notes()[1].native_tag, NoteNativeTag::EndNote);

    let duplicate = NoteOperation::Insert {
        insertion_index: 2,
        note: note(1, 2, NoteKind::Footnote),
    };
    assert_eq!(
        request(&current, duplicate),
        Err(NoteError::InvalidIdentity)
    );
}

#[test]
fn replaces_only_the_selected_sections_exact_note_style() {
    let source = state(Vec::new());
    let before: serde_json::Value =
        serde_json::from_slice(&source.canonical_json(limits()).expect("json")).expect("value");
    let mut replacement = style(NoteKind::Footnote);
    replacement.numbering_restart = NoteNumberingRestart::PerPage;
    replacement.new_number = 7;
    replacement.placement = NotePlacement::RightMostColumn;
    replacement.note_line.color_rgb = 0x00ab_cdef;
    let result = build(
        &source,
        NoteOperation::ReplaceStyle {
            section_id: id("section-2"),
            note_kind: NoteKind::Footnote,
            style: replacement,
        },
    );
    let after: serde_json::Value =
        serde_json::from_slice(&result.state.canonical_json(limits()).expect("json"))
            .expect("value");
    assert_eq!(before["sections"][0], after["sections"][0]);
    assert_eq!(
        before["sections"][1]["endnote_style"],
        after["sections"][1]["endnote_style"]
    );
    assert_eq!(after["sections"][1]["footnote_style"]["new_number"], 7);
    assert_eq!(
        after["sections"][1]["footnote_style"]["numbering_restart"],
        "per_page"
    );
}

#[test]
fn converts_kind_and_native_tag_while_preserving_identity_anchor_content_and_marker() {
    let source = state(vec![note(1, 1, NoteKind::Footnote)]);
    let before: serde_json::Value =
        serde_json::from_slice(&source.canonical_json(limits()).expect("json")).expect("value");
    let result = build(
        &source,
        NoteOperation::Convert {
            target: identity(1),
            target_kind: NoteKind::Endnote,
        },
    );
    let after: serde_json::Value =
        serde_json::from_slice(&result.state.canonical_json(limits()).expect("json"))
            .expect("value");
    assert_eq!(after["notes"][0]["kind"], "endnote");
    assert_eq!(after["notes"][0]["native_tag"], "end_note");
    for field in [
        "identity",
        "anchor",
        "marker",
        "body_graph_sha256",
        "plain_text_sha256",
        "marker_style_sha256",
        "body_style_sha256",
        "opaque_native_payload_sha256",
        "opaque_properties",
        "locked",
    ] {
        assert_eq!(before["notes"][0][field], after["notes"][0][field]);
    }
}

#[test]
fn digest_manifest_export_is_deterministic_document_ordered_and_state_preserving() {
    let source = state(vec![
        note(1, 1, NoteKind::Footnote),
        note(2, 1, NoteKind::Endnote),
        note(3, 2, NoteKind::Footnote),
    ]);
    let operation = NoteOperation::PrepareExport {
        selection: NoteExportSelection::Exact {
            notes: vec![identity(3), identity(1)],
        },
        format: NoteExportFormat::DigestManifestV1,
    };
    let request = request(&source, operation).expect("request");
    assert_eq!(request.operation().capability_id(), "ref.note_export");
    let first = NoteBuilder::plan(&source, &request, FLOW_A, limits()).expect("plan");
    let second = NoteBuilder::plan(&source, &request, FLOW_A, limits()).expect("plan");
    assert_eq!(first.plan_sha256(), second.plan_sha256());
    assert_eq!(first.target_state(), &source);
    let result = NoteBuilder::build(&first, &source, FLOW_A, limits()).expect("result");
    assert_eq!(result.state, source);
    let manifest = result.export_manifest.expect("manifest");
    assert_eq!(manifest.entries().len(), 2);
    let value: serde_json::Value =
        serde_json::from_slice(&manifest.canonical_json(limits()).expect("json")).expect("value");
    assert_eq!(value["entries"][0]["document_ordinal"], 0);
    assert_eq!(value["entries"][1]["document_ordinal"], 2);
}

#[test]
fn marker_native_style_and_identity_boundaries_fail_closed() {
    let mut wrong_tag = note(1, 1, NoteKind::Footnote);
    wrong_tag.native_tag = NoteNativeTag::EndNote;
    assert_eq!(
        state_with(vec![section(1)], vec![wrong_tag], false),
        Err(NoteError::InvalidNativeTag)
    );

    let mut bad_marker = note(1, 1, NoteKind::Footnote);
    bad_marker.marker.user_character = Some("ab".to_owned());
    assert_eq!(
        state_with(vec![section(1)], vec![bad_marker], false),
        Err(NoteError::InvalidNote)
    );

    let mut invalid_section = section(1);
    invalid_section.endnote_style.numbering_restart = NoteNumberingRestart::PerPage;
    assert_eq!(
        state_with(vec![invalid_section], Vec::new(), false),
        Err(NoteError::InvalidStyle)
    );

    let mut invalid_section = section(1);
    invalid_section.footnote_style.placement = NotePlacement::EndOfDocument;
    assert_eq!(
        state_with(vec![invalid_section], Vec::new(), false),
        Err(NoteError::InvalidStyle)
    );

    let mut invalid_section = section(1);
    invalid_section.footnote_style.auto_number_format.format = NoteNumberFormat::UserChar;
    assert_eq!(
        state_with(vec![invalid_section], Vec::new(), false),
        Err(NoteError::InvalidStyle)
    );

    let mut duplicate_anchor = note(2, 1, NoteKind::Endnote);
    duplicate_anchor.anchor = note(1, 1, NoteKind::Footnote).anchor;
    assert_eq!(
        state_with(
            vec![section(1)],
            vec![note(1, 1, NoteKind::Footnote), duplicate_anchor],
            false,
        ),
        Err(NoteError::InvalidIdentity)
    );
}

#[test]
fn protection_noop_and_export_selection_fail_without_partial_state() {
    let locked_document = state_with(vec![section(1)], Vec::new(), true).expect("locked document");
    assert_eq!(
        request(
            &locked_document,
            NoteOperation::Insert {
                insertion_index: 0,
                note: note(1, 1, NoteKind::Footnote),
            },
        ),
        Err(NoteError::Protected)
    );

    let mut locked_note = note(1, 1, NoteKind::Footnote);
    locked_note.locked = true;
    let locked = state(vec![locked_note]);
    assert_eq!(
        request(
            &locked,
            NoteOperation::Convert {
                target: identity(1),
                target_kind: NoteKind::Endnote,
            },
        ),
        Err(NoteError::Protected)
    );

    let source = state(vec![note(1, 1, NoteKind::Footnote)]);
    assert_eq!(
        request(
            &source,
            NoteOperation::Convert {
                target: identity(1),
                target_kind: NoteKind::Footnote,
            },
        ),
        Err(NoteError::Noop)
    );
    assert_eq!(
        request(
            &source,
            NoteOperation::PrepareExport {
                selection: NoteExportSelection::Exact {
                    notes: vec![identity(2)],
                },
                format: NoteExportFormat::DigestManifestV1,
            },
        ),
        Err(NoteError::InvalidExportSelection)
    );
}

#[test]
fn request_plan_and_build_recheck_exact_state_and_document_flow() {
    let source = state(Vec::new());
    let operation = NoteOperation::Insert {
        insertion_index: 0,
        note: note(1, 1, NoteKind::Footnote),
    };
    let mut draft = NoteRequestDraft {
        schema_version: NOTE_ENGINE_SCHEMA_VERSION.to_owned(),
        request_id: id("request-1"),
        expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
        expected_document_flow_sha256: FLOW_A.to_owned(),
        target_document_flow_sha256: FLOW_B.to_owned(),
        operation: operation.clone(),
    };
    draft.expected_source_state_sha256 = FLOW_B.to_owned();
    assert_eq!(
        NoteRequest::from_draft(draft, &source, FLOW_A, limits()),
        Err(NoteError::SourceStateDrift)
    );

    let request = request(&source, operation).expect("request");
    assert_eq!(
        NoteBuilder::plan(&source, &request, FLOW_B, limits()),
        Err(NoteError::DocumentFlowDrift)
    );
    let plan = NoteBuilder::plan(&source, &request, FLOW_A, limits()).expect("plan");
    assert_eq!(
        NoteBuilder::build(&plan, &source, FLOW_B, limits()),
        Err(NoteError::DocumentFlowDrift)
    );

    let export_drift = NoteRequest::from_draft(
        NoteRequestDraft {
            schema_version: NOTE_ENGINE_SCHEMA_VERSION.to_owned(),
            request_id: id("request-export"),
            expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
            expected_document_flow_sha256: FLOW_A.to_owned(),
            target_document_flow_sha256: FLOW_B.to_owned(),
            operation: NoteOperation::PrepareExport {
                selection: NoteExportSelection::All,
                format: NoteExportFormat::DigestManifestV1,
            },
        },
        &source,
        FLOW_A,
        limits(),
    );
    assert_eq!(export_drift, Err(NoteError::DocumentFlowDrift));
}

#[test]
fn strict_json_limits_error_codes_and_debug_output_are_bounded_and_redacted() {
    let source = state(Vec::new());
    let draft = NoteRequestDraft {
        schema_version: NOTE_ENGINE_SCHEMA_VERSION.to_owned(),
        request_id: id("request-private"),
        expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
        expected_document_flow_sha256: FLOW_A.to_owned(),
        target_document_flow_sha256: FLOW_B.to_owned(),
        operation: NoteOperation::Insert {
            insertion_index: 0,
            note: note(1, 1, NoteKind::Footnote),
        },
    };
    let bytes = serde_json::to_vec(&draft).expect("json");
    assert!(NoteRequest::from_json(&bytes, &source, FLOW_A, limits()).is_ok());

    let duplicate = String::from_utf8(bytes.clone()).expect("utf8").replacen(
        "\"schema_version\":",
        "\"schema_version\":\"hwpx-agent.note-engine/v1\",\"schema_version\":",
        1,
    );
    assert_eq!(
        NoteRequest::from_json(duplicate.as_bytes(), &source, FLOW_A, limits()),
        Err(NoteError::InvalidJson)
    );
    let unknown = String::from_utf8(bytes)
        .expect("utf8")
        .replacen('{', "{\"unknown\":true,", 1);
    assert_eq!(
        NoteRequest::from_json(unknown.as_bytes(), &source, FLOW_A, limits()),
        Err(NoteError::InvalidJson)
    );

    let tiny = NoteLimits::new(NoteLimitConfig {
        input_bytes: 8,
        output_bytes: 8,
        ..NoteLimitConfig::default()
    })
    .expect("tiny limits");
    assert_eq!(
        NoteRequest::from_json(b"123456789", &source, FLOW_A, tiny),
        Err(NoteError::InputLimit)
    );
    assert_eq!(NoteError::Protected.code(), "note_protected");
    let debug = format!("{draft:?} {source:?}");
    assert!(!debug.contains("request-private"));
    assert!(!debug.contains("paragraph-1"));
    assert!(!debug.contains(FLOW_A));
}
