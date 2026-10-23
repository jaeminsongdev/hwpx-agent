#![allow(clippy::expect_used)]
mod sequence_program {include!("support/caption_sequence_program.rs");}

use std::fmt::Write as _;

use domain_ir::{
    AuxiliaryCacheStatus, AuxiliarySectionState, BrokenReferenceKind, CaptionBinding,
    CaptionNativeEnvelope, CaptionNativeSemanticBinding, CaptionNumberFormat, CaptionObjectKind,
    CaptionObjectTarget, CaptionRestartPolicy, CaptionSequenceCache, CaptionSequenceDefinition,
    CorrectionMarkKind, CorrectionMarkNode, DataLinkArtifactProtection, DataLinkAvailability,
    DataLinkInheritance, DataLinkState, DateTimeCalendar, DateTimeFieldCache, DateTimeFieldNode,
    DateTimeFormatDefinition, FileNameLiteralNode, LinkAnchor, LinkPoint, LogicalId,
    NativeCaptionSide, NativeDateFieldType, REFERENCE_AUXILIARY_SCHEMA_VERSION,
    ReferenceAuxiliaryBuilder, ReferenceAuxiliaryDocumentState,
    ReferenceAuxiliaryDocumentStateDraft, ReferenceAuxiliaryError, ReferenceAuxiliaryLimitConfig,
    ReferenceAuxiliaryLimits, ReferenceAuxiliaryOperation, ReferenceAuxiliaryRequest,
    ReferenceAuxiliaryRequestDraft, ReferenceTargetKind, ValidationReferenceEdge, ValidationTarget,
};
use sha2::{Digest as _, Sha256};

const D: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const FLOW_A: &str = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
const FLOW_B: &str = "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc";

fn id(value: &str) -> LogicalId {
    LogicalId::parse(value).expect("logical id")
}

fn sha(value: &str) -> String {
    let bytes: [u8; 32] = Sha256::digest(value.as_bytes()).into();
    let mut output = String::with_capacity(64);
    for byte in bytes {
        write!(&mut output, "{byte:02x}").expect("string write");
    }
    output
}

fn limits() -> ReferenceAuxiliaryLimits {
    ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig::default()).expect("limits")
}

fn anchor(section: &str, paragraph: u32) -> LinkAnchor {
    LinkAnchor {
        section_id: id(section),
        start: LinkPoint {
            paragraph_ordinal: paragraph,
            run_ordinal: 0,
            inline_ordinal: 0,
        },
        end: LinkPoint {
            paragraph_ordinal: paragraph,
            run_ordinal: 0,
            inline_ordinal: 0,
        },
    }
}

fn sequence(
    name: &str,
    object_kind: CaptionObjectKind,
    restart_policy: CaptionRestartPolicy,
    start_at: u32,
) -> CaptionSequenceDefinition {
    CaptionSequenceDefinition {
        logical_sequence_id: id(name),
        object_kind,
        label: format!("label-{name}"),
        separator: " ".to_owned(),
        number_format: CaptionNumberFormat::Decimal,
        restart_policy,
        start_at,
        number_style_sha256: sha(&format!("style-{name}")),
        opaque_properties: Vec::new(),
        locked: false,
    }
}

fn object(name: &str, kind: CaptionObjectKind, section: &str) -> CaptionObjectTarget {
    CaptionObjectTarget {
        logical_object_id: id(name),
        object_kind: kind,
        section_id: id(section),
        object_state_sha256: sha(&format!("object-{name}")),
        locked: false,
    }
}

fn caption(
    name: &str,
    target: &CaptionObjectTarget,
    sequence: &CaptionSequenceDefinition,
    document_order: u64,
    resolved_number: u32,
) -> CaptionBinding {
    let mut binding = CaptionBinding {
        logical_caption_id: id(name),
        logical_object_id: target.logical_object_id.clone(),
        logical_sequence_id: sequence.logical_sequence_id.clone(),
        document_order,
        caption_content_sha256: sha(&format!("content-{name}")),
        cache: CaptionSequenceCache {
            sequence_projection_sha256: D.to_owned(),
            rendered_number_sha256: sha(&resolved_number.to_string()),
            resolved_number,
            status: AuxiliaryCacheStatus::Stale,
        },
        native_envelope: CaptionNativeEnvelope {
            side: NativeCaptionSide::Bottom,
            full_size: false,
            width_hwpunit: -1,
            gap_hwpunit: 850,
            last_width_hwpunit: 0,
            sub_list_sha256: sha(&format!("sublist-{name}")),
            opaque_native_state_sha256: sha(&format!("native-{name}")),
            semantic_binding: CaptionNativeSemanticBinding::UnverifiedSubListNumbering,
        },
        opaque_properties: Vec::new(),
        locked: false,
    };
    binding.cache.sequence_projection_sha256 =
        CaptionBinding::projection_sha256(sequence, target, &binding, resolved_number, limits())
            .expect("caption projection");
    binding.cache.status = AuxiliaryCacheStatus::Current;
    binding
}

fn date_field() -> DateTimeFieldNode {
    let mut field = DateTimeFieldNode {
        logical_field_id: id("date-field"),
        anchor: anchor("section-a", 0),
        begin_control_id: 101,
        field_id: 201,
        end_begin_control_id_ref: 101,
        end_field_id: 201,
        native_field_type: NativeDateFieldType::DocDate,
        format: DateTimeFormatDefinition {
            pattern: "yyyy-MM-dd".to_owned(),
            locale: "ko-KR".to_owned(),
            timezone_offset_minutes: 540,
            calendar: DateTimeCalendar::Gregorian,
        },
        cache: DateTimeFieldCache {
            format_projection_sha256: D.to_owned(),
            display_text_sha256: sha("display-date"),
            status: AuxiliaryCacheStatus::Stale,
        },
        native_parameters_sha256: sha("date-parameters"),
        opaque_field_state_sha256: sha("date-opaque"),
        opaque_properties: Vec::new(),
        locked: false,
    };
    field.cache.format_projection_sha256 = field
        .format_projection_sha256(limits())
        .expect("date projection");
    field.cache.status = AuxiliaryCacheStatus::Current;
    field
}

fn file_literal(name: &str, section: &str) -> FileNameLiteralNode {
    FileNameLiteralNode {
        logical_literal_id: id(&format!("literal-{section}")),
        anchor: anchor(section, 0),
        literal: name.to_owned(),
        source_leaf_name_sha256: sha(name),
        source_revision_sha256: sha("source-revision"),
        include_extension: true,
        character_style_sha256: sha("character-style"),
        paragraph_style_sha256: sha("paragraph-style"),
        opaque_text_state_sha256: sha("literal-opaque"),
        opaque_properties: Vec::new(),
        locked: false,
    }
}

fn correction(name: &str, kind: CorrectionMarkKind, native: u32) -> CorrectionMarkNode {
    CorrectionMarkNode {
        logical_mark_id: id(name),
        anchor: anchor("section-a", 0),
        kind,
        begin_control_id: native,
        field_id: native + 1000,
        end_begin_control_id_ref: native,
        end_field_id: native + 1000,
        author_identity_sha256: sha("author"),
        created_at_epoch_millis: 1_788_796_800_000,
        mark_content_sha256: sha(name),
        native_parameters_sha256: sha(&format!("params-{name}")),
        opaque_field_state_sha256: sha(&format!("opaque-{name}")),
        opaque_properties: Vec::new(),
        locked: false,
    }
}

fn data_link(availability: DataLinkAvailability) -> DataLinkState {
    DataLinkState {
        logical_link_id: id("data-link"),
        logical_artifact_id: id("data-artifact"),
        encrypted_artifact_sha256: sha("encrypted-artifact"),
        encryption_envelope_sha256: sha("encryption-envelope"),
        allowlisted_location_sha256: sha("allowlisted-location"),
        source_revision_sha256: sha("linked-revision"),
        relationship_state_sha256: sha("relationship"),
        inheritance: DataLinkInheritance::Page,
        availability,
        artifact_protection: DataLinkArtifactProtection::Encrypted,
        opaque_native_state_sha256: sha("native-link"),
        opaque_properties: Vec::new(),
        locked: false,
    }
}

fn validation_target(name: &str, kind: ReferenceTargetKind, active: bool) -> ValidationTarget {
    ValidationTarget {
        logical_target_id: id(name),
        target_kind: kind,
        anchor: Some(anchor("section-a", 0)),
        active,
        target_state_sha256: sha(&format!("target-{name}")),
    }
}

fn validation_edge(
    reference: &str,
    source: &str,
    target: &str,
    kind: ReferenceTargetKind,
    cache_status: AuxiliaryCacheStatus,
) -> ValidationReferenceEdge {
    ValidationReferenceEdge {
        logical_reference_id: id(reference),
        source_node_id: id(source),
        expected_target_id: id(target),
        expected_target_kind: kind,
        source_anchor: anchor("section-a", 0),
        cached_display_sha256: sha(&format!("display-{reference}")),
        cache_status,
        edge_state_sha256: sha(&format!("edge-{reference}")),
    }
}

#[allow(clippy::too_many_lines)]
fn draft() -> ReferenceAuxiliaryDocumentStateDraft {
    let picture_a = object("picture-a", CaptionObjectKind::Picture, "section-a");
    let picture_b = object("picture-b", CaptionObjectKind::Picture, "section-b");
    let picture_sequence = sequence(
        "picture-sequence",
        CaptionObjectKind::Picture,
        CaptionRestartPolicy::Continuous,
        1,
    );
    ReferenceAuxiliaryDocumentStateDraft {
        schema_version: REFERENCE_AUXILIARY_SCHEMA_VERSION.to_owned(),
        sections: vec![
            AuxiliarySectionState {
                section_id: id("section-a"),
                paragraph_count: 2,
                run_topology_sha256: sha("runs-a"),
                inline_topology_sha256: sha("inline-a"),
                page_assignment_sha256: sha("pages-a"),
                opaque_section_state_sha256: sha("section-opaque-a"),
                locked: false,
            },
            AuxiliarySectionState {
                section_id: id("section-b"),
                paragraph_count: 2,
                run_topology_sha256: sha("runs-b"),
                inline_topology_sha256: sha("inline-b"),
                page_assignment_sha256: sha("pages-b"),
                opaque_section_state_sha256: sha("section-opaque-b"),
                locked: false,
            },
        ],
        caption_objects: vec![picture_a.clone(), picture_b.clone()],
        caption_sequences: vec![picture_sequence.clone()],
        captions: vec![
            caption("caption-a", &picture_a, &picture_sequence, 10, 1),
            caption("caption-b", &picture_b, &picture_sequence, 20, 2),
        ],
        date_time_fields: vec![date_field()],
        file_name_literals: Vec::new(),
        correction_marks: Vec::new(),
        data_link: None,
        validation_targets: vec![
            validation_target("target-a", ReferenceTargetKind::Bookmark, true),
            validation_target("target-inactive", ReferenceTargetKind::Bookmark, false),
            validation_target("cycle-a", ReferenceTargetKind::Bookmark, true),
            validation_target("cycle-b", ReferenceTargetKind::Bookmark, true),
            validation_target("external", ReferenceTargetKind::ExternalData, true),
        ],
        validation_edges: vec![
            validation_edge(
                "ref-valid",
                "node-valid",
                "target-a",
                ReferenceTargetKind::Bookmark,
                AuxiliaryCacheStatus::Current,
            ),
            validation_edge(
                "ref-missing",
                "node-missing",
                "missing",
                ReferenceTargetKind::Bookmark,
                AuxiliaryCacheStatus::Current,
            ),
            validation_edge(
                "ref-inactive",
                "node-inactive",
                "target-inactive",
                ReferenceTargetKind::Bookmark,
                AuxiliaryCacheStatus::Current,
            ),
            validation_edge(
                "ref-kind",
                "node-kind",
                "target-a",
                ReferenceTargetKind::Caption,
                AuxiliaryCacheStatus::Current,
            ),
            validation_edge(
                "ref-stale",
                "node-stale",
                "target-a",
                ReferenceTargetKind::Bookmark,
                AuxiliaryCacheStatus::Stale,
            ),
            validation_edge(
                "ref-cycle-a",
                "cycle-a",
                "cycle-b",
                ReferenceTargetKind::Bookmark,
                AuxiliaryCacheStatus::Current,
            ),
            validation_edge(
                "ref-cycle-b",
                "cycle-b",
                "cycle-a",
                ReferenceTargetKind::Bookmark,
                AuxiliaryCacheStatus::Current,
            ),
            validation_edge(
                "ref-external",
                "node-external",
                "external",
                ReferenceTargetKind::ExternalData,
                AuxiliaryCacheStatus::Current,
            ),
        ],
        occupied_non_aux_control_ids: vec![1, 2],
        occupied_non_aux_field_ids: vec![3, 4],
        non_auxiliary_content_sha256: sha("non-aux-content"),
        field_inventory_sha256: sha("fields"),
        form_inventory_sha256: sha("forms"),
        note_inventory_sha256: sha("notes"),
        comment_inventory_sha256: sha("comments"),
        link_inventory_sha256: sha("links"),
        cross_reference_inventory_sha256: sha("crossrefs"),
        toc_index_inventory_sha256: sha("toc-index"),
        citation_inventory_sha256: sha("citations"),
        mail_merge_inventory_sha256: sha("mail-merge"),
        object_inventory_sha256: sha("objects"),
        numbering_inventory_sha256: sha("numbering"),
        style_catalog_sha256: sha("styles"),
        relationship_inventory_sha256: sha("relationships"),
        resource_inventory_sha256: sha("resources"),
        document_protection_sha256: sha("protection"),
        opaque_document_state_sha256: sha("document-opaque"),
        document_locked: false,
    }
}

fn state() -> ReferenceAuxiliaryDocumentState {
    ReferenceAuxiliaryDocumentState::from_draft(draft(), limits()).expect("state")
}

fn request(
    source: &ReferenceAuxiliaryDocumentState,
    operation: ReferenceAuxiliaryOperation,
) -> Result<ReferenceAuxiliaryRequest, ReferenceAuxiliaryError> {
    ReferenceAuxiliaryRequest::from_draft(
        ReferenceAuxiliaryRequestDraft {
            schema_version: REFERENCE_AUXILIARY_SCHEMA_VERSION.to_owned(),
            request_id: id("request"),
            expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
            expected_document_flow_sha256: FLOW_A.to_owned(),
            target_document_flow_sha256: FLOW_B.to_owned(),
            operation,
        },
        source,
        FLOW_A,
        limits(),
    )
}

fn build(
    source: &ReferenceAuxiliaryDocumentState,
    operation: ReferenceAuxiliaryOperation,
) -> Result<domain_ir::ReferenceAuxiliaryResult, ReferenceAuxiliaryError> {
    let request = request(source, operation)?;
    let plan = ReferenceAuxiliaryBuilder::plan(source, &request, FLOW_A, limits())?;
    ReferenceAuxiliaryBuilder::build(&plan, source, FLOW_A, limits())
}

#[test]
fn exposes_exact_six_capabilities_and_no_generation_action() {
    let source = state();
    let operations = [
        ReferenceAuxiliaryOperation::SetCaptionState {
            caption_sequences: Vec::new(),
            captions: Vec::new(),
        },
        ReferenceAuxiliaryOperation::SetDateTimeFormat {
            logical_field_id: id("date-field"),
            format: DateTimeFormatDefinition {
                pattern: "yyyy".to_owned(),
                locale: "ko-KR".to_owned(),
                timezone_offset_minutes: 540,
                calendar: DateTimeCalendar::Gregorian,
            },
        },
        ReferenceAuxiliaryOperation::InsertFileNameLiteral {
            insertion_index: 0,
            literal: Box::new(file_literal("document.hwpx", "section-a")),
        },
        ReferenceAuxiliaryOperation::InsertCorrectionMark {
            insertion_index: 0,
            mark: Box::new(correction("mark", CorrectionMarkKind::Change, 300)),
        },
        ReferenceAuxiliaryOperation::SetDataLink {
            data_link: Some(Box::new(data_link(DataLinkAvailability::Available))),
        },
        ReferenceAuxiliaryOperation::ValidateReferences {
            expected_report_sha256: source
                .validate_references(limits())
                .expect("report")
                .canonical_sha256(limits())
                .expect("digest"),
        },
    ];
    assert_eq!(
        operations
            .iter()
            .map(ReferenceAuxiliaryOperation::capability_id)
            .collect::<Vec<_>>(),
        vec![
            "ref.caption_sequence",
            "ref.date_time_format",
            "ref.file_name_literal",
            "ref.correction_mark",
            "ref.data_link",
            "ref.reference_validate",
        ]
    );
    let json = serde_json::to_string(&operations).expect("json");
    for denied in [
        "crossref_update",
        "field_update",
        "desktop_automation",
        "lowerer",
    ] {
        assert!(!json.contains(denied));
    }
}

#[test]
fn caption_sequence_restarts_per_section_and_preserves_every_other_inventory() {
    let source = state();
    let mut source_draft: ReferenceAuxiliaryDocumentStateDraft = source.clone().into();
    let replacement = sequence(
        "picture-sequence",
        CaptionObjectKind::Picture,
        CaptionRestartPolicy::PerSection,
        7,
    );
    let object_a = source_draft.caption_objects[0].clone();
    let object_b = source_draft.caption_objects[1].clone();
    let captions = vec![
        caption("caption-a", &object_a, &replacement, 10, 7),
        caption("caption-b", &object_b, &replacement, 20, 7),
    ];
    let result = build(
        &source,
        ReferenceAuxiliaryOperation::SetCaptionState {
            caption_sequences: vec![replacement],
            captions,
        },
    )
    .expect("build");
    assert_eq!(
        result
            .state
            .captions()
            .iter()
            .map(|caption| caption.cache.resolved_number)
            .collect::<Vec<_>>(),
        vec![7, 7]
    );
    let target: ReferenceAuxiliaryDocumentStateDraft = result.state.into();
    assert_eq!(
        target.field_inventory_sha256,
        source_draft.field_inventory_sha256
    );
    assert_eq!(target.validation_edges, source_draft.validation_edges);
    assert_eq!(target.data_link, source_draft.data_link);
    source_draft.caption_sequences = target.caption_sequences;
}

#[test]
fn caption_state_rejects_kind_number_projection_duplicate_and_protected_drift() {
    let source = state();
    let mut draft: ReferenceAuxiliaryDocumentStateDraft = source.clone().into();
    draft.caption_sequences[0].object_kind = CaptionObjectKind::Table;
    assert_eq!(
        ReferenceAuxiliaryDocumentState::from_draft(draft, limits()),
        Err(ReferenceAuxiliaryError::InvalidCaption)
    );

    let mut draft: ReferenceAuxiliaryDocumentStateDraft = source.clone().into();
    draft.captions[0].cache.resolved_number = 99;
    assert_eq!(
        ReferenceAuxiliaryDocumentState::from_draft(draft, limits()),
        Err(ReferenceAuxiliaryError::InvalidCaption)
    );

    let mut draft: ReferenceAuxiliaryDocumentStateDraft = source.clone().into();
    draft.captions[1].logical_object_id = draft.captions[0].logical_object_id.clone();
    assert_eq!(
        ReferenceAuxiliaryDocumentState::from_draft(draft, limits()),
        Err(ReferenceAuxiliaryError::InvalidCaption)
    );

    let mut locked: ReferenceAuxiliaryDocumentStateDraft = source.into();
    locked.captions[0].locked = true;
    let locked = ReferenceAuxiliaryDocumentState::from_draft(locked, limits()).expect("locked");
    assert_eq!(
        build(
            &locked,
            ReferenceAuxiliaryOperation::SetCaptionState {
                caption_sequences: Vec::new(),
                captions: Vec::new(),
            }
        ),
        Err(ReferenceAuxiliaryError::Protected)
    );
}

#[test]
fn date_time_format_change_is_exact_and_intentionally_marks_display_cache_stale() {
    let source = state();
    let old_display = source.date_time_fields()[0]
        .cache
        .display_text_sha256
        .clone();
    let result = build(
        &source,
        ReferenceAuxiliaryOperation::SetDateTimeFormat {
            logical_field_id: id("date-field"),
            format: DateTimeFormatDefinition {
                pattern: "yyyy년 M월 d일 HH:mm".to_owned(),
                locale: "ko-KR".to_owned(),
                timezone_offset_minutes: 540,
                calendar: DateTimeCalendar::LocaleDefault,
            },
        },
    )
    .expect("build");
    let field = &result.state.date_time_fields()[0];
    assert_eq!(field.cache.status, AuxiliaryCacheStatus::Stale);
    assert_eq!(field.cache.display_text_sha256, old_display);
    assert_eq!(field.native_field_type, NativeDateFieldType::DocDate);
    assert_eq!(result.receipt.capability_id, "ref.date_time_format");
}

#[test]
fn date_time_missing_noop_invalid_locale_and_lock_fail_closed() {
    let source = state();
    assert_eq!(
        build(
            &source,
            ReferenceAuxiliaryOperation::SetDateTimeFormat {
                logical_field_id: id("missing"),
                format: source.date_time_fields()[0].format.clone(),
            }
        ),
        Err(ReferenceAuxiliaryError::DateTimeFieldMissing)
    );
    assert_eq!(
        build(
            &source,
            ReferenceAuxiliaryOperation::SetDateTimeFormat {
                logical_field_id: id("date-field"),
                format: source.date_time_fields()[0].format.clone(),
            }
        ),
        Err(ReferenceAuxiliaryError::NoChange)
    );
    let mut invalid = source.date_time_fields()[0].format.clone();
    invalid.locale = "ko KR".to_owned();
    assert_eq!(
        build(
            &source,
            ReferenceAuxiliaryOperation::SetDateTimeFormat {
                logical_field_id: id("date-field"),
                format: invalid,
            }
        ),
        Err(ReferenceAuxiliaryError::InvalidDateTime)
    );
    let mut locked: ReferenceAuxiliaryDocumentStateDraft = source.into();
    locked.date_time_fields[0].locked = true;
    let locked = ReferenceAuxiliaryDocumentState::from_draft(locked, limits()).expect("locked");
    let mut changed = locked.date_time_fields()[0].format.clone();
    changed.pattern = "yyyy".to_owned();
    assert_eq!(
        build(
            &locked,
            ReferenceAuxiliaryOperation::SetDateTimeFormat {
                logical_field_id: id("date-field"),
                format: changed,
            }
        ),
        Err(ReferenceAuxiliaryError::Protected)
    );
}

#[test]
fn file_name_literal_is_leaf_only_source_bound_and_preserves_nontext_state() {
    let source = state();
    let before: ReferenceAuxiliaryDocumentStateDraft = source.clone().into();
    let result = build(
        &source,
        ReferenceAuxiliaryOperation::InsertFileNameLiteral {
            insertion_index: 0,
            literal: Box::new(file_literal("수업자료.hwpx", "section-b")),
        },
    )
    .expect("build");
    assert_eq!(
        result.state.file_name_literals()[0].literal,
        "수업자료.hwpx"
    );
    let after: ReferenceAuxiliaryDocumentStateDraft = result.state.into();
    assert_eq!(after.captions, before.captions);
    assert_eq!(after.date_time_fields, before.date_time_fields);
    assert_eq!(
        after.relationship_inventory_sha256,
        before.relationship_inventory_sha256
    );

    let mut path = file_literal("document.hwpx", "section-a");
    path.literal = "folder/document.hwpx".to_owned();
    path.source_leaf_name_sha256 = sha(&path.literal);
    assert_eq!(
        build(
            &source,
            ReferenceAuxiliaryOperation::InsertFileNameLiteral {
                insertion_index: 0,
                literal: Box::new(path),
            }
        ),
        Err(ReferenceAuxiliaryError::InvalidFileNameLiteral)
    );
}

#[test]
fn correction_mark_covers_all_official_kinds_and_native_pairs() {
    let kinds = [
        CorrectionMarkKind::Change,
        CorrectionMarkKind::Sign,
        CorrectionMarkKind::Delete,
        CorrectionMarkKind::Attach,
        CorrectionMarkKind::Clipping,
        CorrectionMarkKind::Sawtooth,
        CorrectionMarkKind::Thinking,
        CorrectionMarkKind::Praise,
        CorrectionMarkKind::Line,
        CorrectionMarkKind::SimpleChange,
        CorrectionMarkKind::Hyperlink,
        CorrectionMarkKind::LineAttach,
        CorrectionMarkKind::LineLink,
        CorrectionMarkKind::LineTransfer,
        CorrectionMarkKind::RightMove,
        CorrectionMarkKind::LeftMove,
        CorrectionMarkKind::Transfer,
        CorrectionMarkKind::Split,
        CorrectionMarkKind::SimpleInsert,
    ];
    let encoded = kinds
        .iter()
        .map(|kind| serde_json::to_string(kind).expect("json"))
        .collect::<std::collections::BTreeSet<_>>();
    assert_eq!(encoded.len(), 19);

    let source = state();
    let result = build(
        &source,
        ReferenceAuxiliaryOperation::InsertCorrectionMark {
            insertion_index: 0,
            mark: Box::new(correction(
                "proofreading-mark",
                CorrectionMarkKind::SimpleInsert,
                300,
            )),
        },
    )
    .expect("build");
    assert_eq!(result.state.correction_marks().len(), 1);
    assert_eq!(result.receipt.capability_id, "ref.correction_mark");
}

#[test]
fn correction_mark_native_collision_timestamp_and_pair_drift_fail_closed() {
    let source = state();
    let mut colliding = correction("collision", CorrectionMarkKind::Delete, 101);
    colliding.field_id = 301;
    colliding.end_field_id = 301;
    assert_eq!(
        build(
            &source,
            ReferenceAuxiliaryOperation::InsertCorrectionMark {
                insertion_index: 0,
                mark: Box::new(colliding),
            }
        ),
        Err(ReferenceAuxiliaryError::InvalidCorrectionMark)
    );
    let mut invalid = correction("invalid", CorrectionMarkKind::Delete, 300);
    invalid.created_at_epoch_millis = -1;
    assert_eq!(
        build(
            &source,
            ReferenceAuxiliaryOperation::InsertCorrectionMark {
                insertion_index: 0,
                mark: Box::new(invalid),
            }
        ),
        Err(ReferenceAuxiliaryError::InvalidCorrectionMark)
    );
}

#[test]
fn data_link_requires_encryption_and_uses_only_digest_location() {
    let source = state();
    let result = build(
        &source,
        ReferenceAuxiliaryOperation::SetDataLink {
            data_link: Some(Box::new(data_link(DataLinkAvailability::Available))),
        },
    )
    .expect("build");
    let link = result.state.data_link().expect("link");
    assert_eq!(
        link.artifact_protection,
        DataLinkArtifactProtection::Encrypted
    );
    assert_eq!(link.inheritance, DataLinkInheritance::Page);
    assert_eq!(result.receipt.capability_id, "ref.data_link");
    let json =
        String::from_utf8(result.state.canonical_json(limits()).expect("json")).expect("utf8");
    assert!(!json.contains("D:\\"));
    assert!(!json.contains("file://"));

    let mut invalid = data_link(DataLinkAvailability::Available);
    invalid.encrypted_artifact_sha256 = "not-a-digest".to_owned();
    assert_eq!(
        build(
            &source,
            ReferenceAuxiliaryOperation::SetDataLink {
                data_link: Some(Box::new(invalid)),
            }
        ),
        Err(ReferenceAuxiliaryError::InvalidDataLink)
    );
}

#[test]
fn reference_validator_reports_missing_inactive_kind_stale_cycle_and_data_link() {
    let source = state();
    let report = source.validate_references(limits()).expect("report");
    assert_eq!(report.checked_references, 8);
    assert_eq!(report.valid_references, 1);
    let kinds = report
        .issues
        .iter()
        .map(|issue| issue.kind)
        .collect::<std::collections::BTreeSet<_>>();
    assert_eq!(
        kinds,
        [
            BrokenReferenceKind::MissingTarget,
            BrokenReferenceKind::InactiveTarget,
            BrokenReferenceKind::TargetKindMismatch,
            BrokenReferenceKind::ReferenceCycle,
            BrokenReferenceKind::StaleCache,
            BrokenReferenceKind::DataLinkUnavailable,
        ]
        .into_iter()
        .collect()
    );
    assert_eq!(
        report.canonical_json(limits()).expect("json"),
        source
            .validate_references(limits())
            .expect("repeat")
            .canonical_json(limits())
            .expect("json")
    );
}

#[test]
fn reference_validate_is_read_only_report_bound_and_receipted() {
    let source = state();
    let expected = source
        .validate_references(limits())
        .expect("report")
        .canonical_sha256(limits())
        .expect("digest");
    let result = build(
        &source,
        ReferenceAuxiliaryOperation::ValidateReferences {
            expected_report_sha256: expected.clone(),
        },
    )
    .expect("build");
    assert_eq!(result.state, source);
    assert_eq!(result.receipt.validation_report_sha256, Some(expected));
    assert_eq!(result.receipt.capability_id, "ref.reference_validate");
    assert_eq!(
        build(
            &source,
            ReferenceAuxiliaryOperation::ValidateReferences {
                expected_report_sha256: D.to_owned(),
            }
        ),
        Err(ReferenceAuxiliaryError::ValidationReportDrift)
    );
}

#[test]
fn request_plan_and_build_recheck_complete_state_and_document_flow() {
    let source = state();
    let operation = ReferenceAuxiliaryOperation::InsertFileNameLiteral {
        insertion_index: 0,
        literal: Box::new(file_literal("document.hwpx", "section-a")),
    };
    let mut request_draft = ReferenceAuxiliaryRequestDraft {
        schema_version: REFERENCE_AUXILIARY_SCHEMA_VERSION.to_owned(),
        request_id: id("request"),
        expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
        expected_document_flow_sha256: FLOW_A.to_owned(),
        target_document_flow_sha256: FLOW_B.to_owned(),
        operation: operation.clone(),
    };
    request_draft.expected_source_state_sha256 = D.to_owned();
    assert_eq!(
        ReferenceAuxiliaryRequest::from_draft(request_draft, &source, FLOW_A, limits()),
        Err(ReferenceAuxiliaryError::SourceStateDrift)
    );
    assert_eq!(
        ReferenceAuxiliaryRequest::from_draft(
            ReferenceAuxiliaryRequestDraft {
                schema_version: REFERENCE_AUXILIARY_SCHEMA_VERSION.to_owned(),
                request_id: id("request"),
                expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
                expected_document_flow_sha256: FLOW_A.to_owned(),
                target_document_flow_sha256: FLOW_B.to_owned(),
                operation: operation.clone(),
            },
            &source,
            FLOW_B,
            limits(),
        ),
        Err(ReferenceAuxiliaryError::DocumentFlowDrift)
    );
    let request = request(&source, operation).expect("request");
    let plan = ReferenceAuxiliaryBuilder::plan(&source, &request, FLOW_A, limits()).expect("plan");
    assert_eq!(
        ReferenceAuxiliaryBuilder::build(&plan, &source, FLOW_B, limits()),
        Err(ReferenceAuxiliaryError::DocumentFlowDrift)
    );
    let mut drifted: ReferenceAuxiliaryDocumentStateDraft = source.clone().into();
    drifted.resource_inventory_sha256 = sha("drifted-resource");
    let drifted = ReferenceAuxiliaryDocumentState::from_draft(drifted, limits()).expect("drift");
    assert_eq!(
        ReferenceAuxiliaryBuilder::build(&plan, &drifted, FLOW_A, limits()),
        Err(ReferenceAuxiliaryError::SourceStateDrift)
    );
}

#[test]
fn strict_json_limits_and_redacted_debug_hold() {
    let source = state();
    let draft = ReferenceAuxiliaryRequestDraft {
        schema_version: REFERENCE_AUXILIARY_SCHEMA_VERSION.to_owned(),
        request_id: id("private-request-id"),
        expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
        expected_document_flow_sha256: FLOW_A.to_owned(),
        target_document_flow_sha256: FLOW_B.to_owned(),
        operation: ReferenceAuxiliaryOperation::InsertFileNameLiteral {
            insertion_index: 0,
            literal: Box::new(file_literal("private-name.hwpx", "section-a")),
        },
    };
    let mut value = serde_json::to_value(&draft).expect("json");
    value
        .as_object_mut()
        .expect("object")
        .insert("extra".to_owned(), serde_json::Value::Bool(true));
    assert_eq!(
        ReferenceAuxiliaryRequest::from_json(
            &serde_json::to_vec(&value).expect("bytes"),
            &source,
            FLOW_A,
            limits(),
        ),
        Err(ReferenceAuxiliaryError::InvalidJson)
    );
    let encoded = serde_json::to_string(&draft).expect("json");
    let duplicate = encoded.replacen(
        '{',
        &format!("{{\"schema_version\":\"{REFERENCE_AUXILIARY_SCHEMA_VERSION}\","),
        1,
    );
    assert_eq!(
        ReferenceAuxiliaryRequest::from_json(duplicate.as_bytes(), &source, FLOW_A, limits()),
        Err(ReferenceAuxiliaryError::InvalidJson)
    );
    let tiny = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {
        input_bytes: 16,
        output_bytes: 16,
        ..ReferenceAuxiliaryLimitConfig::default()
    })
    .expect("tiny");
    assert_eq!(
        ReferenceAuxiliaryRequest::from_json(encoded.as_bytes(), &source, FLOW_A, tiny),
        Err(ReferenceAuxiliaryError::InputLimit)
    );
    let debug = format!("{draft:?} {source:?}");
    for private in ["private-request-id", "private-name.hwpx", FLOW_A, FLOW_B] {
        assert!(!debug.contains(private));
    }
}

#[test]
fn state_json_is_canonical_and_error_codes_are_stable() {
    let source = state();
    let bytes = source.canonical_json(limits()).expect("json");
    let decoded: ReferenceAuxiliaryDocumentState = serde_json::from_slice(&bytes).expect("decode");
    assert_eq!(decoded, source);
    assert_eq!(
        decoded.canonical_sha256(limits()).expect("digest"),
        source.canonical_sha256(limits()).expect("digest")
    );
    assert_eq!(
        ReferenceAuxiliaryError::ValidationReportDrift.code(),
        "reference_auxiliary_validation_report_drift"
    );
    assert_eq!(
        ReferenceAuxiliaryError::InvalidDataLink.code(),
        "reference_auxiliary_invalid_data_link"
    );
}
