#![allow(clippy::expect_used)] // Fixtures keep failures local and readable.

use domain_ir::{
    CROSS_REFERENCE_SCHEMA_VERSION, CrossReferenceBuilder, CrossReferenceCache,
    CrossReferenceCacheStatus, CrossReferenceDisplayKind, CrossReferenceDocumentState,
    CrossReferenceDocumentStateDraft, CrossReferenceEntry, CrossReferenceError,
    CrossReferenceFieldType, CrossReferenceIdentity, CrossReferenceLimitConfig,
    CrossReferenceLimits, CrossReferenceNativeBeginTag, CrossReferenceNativeEndTag,
    CrossReferenceNativePair, CrossReferenceOperation, CrossReferenceRequest,
    CrossReferenceRequestDraft, CrossReferenceSectionState, CrossReferenceSemanticBinding,
    CrossReferenceTarget, CrossReferenceTargetIdentity, CrossReferenceTargetKind,
    CrossReferenceUpdatePolicy, LinkAnchor, LinkPoint, LogicalId, OpaqueLinkProperty,
};
use serde_json::Value;

const A: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const B: &str = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
const C: &str = "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc";
const D: &str = "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd";
const FLOW_A: &str = "1111111111111111111111111111111111111111111111111111111111111111";
const FLOW_B: &str = "2222222222222222222222222222222222222222222222222222222222222222";

fn limits() -> CrossReferenceLimits {
    CrossReferenceLimits::new(CrossReferenceLimitConfig::default()).expect("valid limits")
}

fn id(value: &str) -> LogicalId {
    LogicalId::parse(value).expect("valid id")
}

fn point(paragraph: u32, inline: u32) -> LinkPoint {
    LinkPoint {
        paragraph_ordinal: paragraph,
        run_ordinal: 0,
        inline_ordinal: inline,
    }
}

fn anchor(paragraph: u32, start: u32, end: u32) -> LinkAnchor {
    LinkAnchor {
        section_id: id("section-1"),
        start: point(paragraph, start),
        end: point(paragraph, end),
    }
}

fn section(locked: bool) -> CrossReferenceSectionState {
    CrossReferenceSectionState {
        section_id: id("section-1"),
        paragraph_count: 2,
        run_topology_sha256: A.to_owned(),
        inline_topology_sha256: B.to_owned(),
        opaque_section_state_sha256: C.to_owned(),
        locked,
    }
}

fn target(index: u32, kind: CrossReferenceTargetKind) -> CrossReferenceTarget {
    CrossReferenceTarget {
        identity: CrossReferenceTargetIdentity {
            logical_target_id: id(&format!("target-{index}")),
        },
        kind,
        anchor: anchor(0, index * 100, index * 100 + 80),
        semantic_name_sha256: A.to_owned(),
        source_text_sha256: B.to_owned(),
        label_sha256: (kind == CrossReferenceTargetKind::Caption).then(|| C.to_owned()),
        numbering_sha256: matches!(
            kind,
            CrossReferenceTargetKind::Heading
                | CrossReferenceTargetKind::NumberedParagraph
                | CrossReferenceTargetKind::Caption
                | CrossReferenceTargetKind::Footnote
                | CrossReferenceTargetKind::Endnote
        )
        .then(|| D.to_owned()),
        page_assignment_sha256: C.to_owned(),
        dependency_target_ids: Vec::new(),
        opaque_target_state_sha256: D.to_owned(),
        opaque_properties: vec![OpaqueLinkProperty {
            namespace: "hp".to_owned(),
            name: format!("target_{index}"),
            value_sha256: A.to_owned(),
        }],
        locked: false,
    }
}

fn native_pair(index: u32) -> CrossReferenceNativePair {
    CrossReferenceNativePair {
        begin_tag: CrossReferenceNativeBeginTag::FieldBegin,
        end_tag: CrossReferenceNativeEndTag::FieldEnd,
        field_type: CrossReferenceFieldType::Crossref,
        semantic_binding: CrossReferenceSemanticBinding::UnverifiedFieldParameters,
        end_begin_control_id_ref: 1000 + index,
        end_field_id: 2000 + index,
        field_name_sha256: Some(format!("{index:064x}")),
        editable: true,
        dirty: false,
        z_order: -1,
        parameters_sha256: B.to_owned(),
        sub_list_sha256: Some(C.to_owned()),
        meta_tag_sha256: None,
        opaque_begin_state_sha256: A.to_owned(),
        opaque_end_state_sha256: B.to_owned(),
    }
}

fn reference_at(
    index: u32,
    target: &CrossReferenceTarget,
    display_kind: CrossReferenceDisplayKind,
    reference_anchor: &LinkAnchor,
    containing_target_id: Option<LogicalId>,
) -> CrossReferenceEntry {
    CrossReferenceEntry {
        identity: CrossReferenceIdentity {
            logical_cross_reference_id: id(&format!("crossref-{index}")),
            begin_control_id: 1000 + index,
            field_id: 2000 + index,
        },
        anchor: reference_anchor.clone(),
        containing_target_id,
        target_id: target.identity.logical_target_id.clone(),
        display_kind,
        update_policy: CrossReferenceUpdatePolicy::PreserveCached,
        cache: CrossReferenceCache {
            target_projection_sha256: target
                .projection_sha256(display_kind, reference_anchor, limits())
                .expect("projection"),
            display_value_sha256: D.to_owned(),
            status: CrossReferenceCacheStatus::Current,
        },
        native_pair: native_pair(index),
        opaque_native_payload_sha256: C.to_owned(),
        opaque_properties: vec![OpaqueLinkProperty {
            namespace: "hp".to_owned(),
            name: format!("crossref_{index}"),
            value_sha256: B.to_owned(),
        }],
        locked: false,
    }
}

fn reference(
    index: u32,
    target: &CrossReferenceTarget,
    display_kind: CrossReferenceDisplayKind,
) -> CrossReferenceEntry {
    let reference_anchor = anchor(1, index * 2, index * 2 + 1);
    reference_at(index, target, display_kind, &reference_anchor, None)
}

fn state(
    targets: Vec<CrossReferenceTarget>,
    cross_references: Vec<CrossReferenceEntry>,
    occupied_begin_ids: Vec<u32>,
    occupied_field_ids: Vec<u32>,
) -> Result<CrossReferenceDocumentState, CrossReferenceError> {
    CrossReferenceDocumentState::from_draft(
        state_draft(
            targets,
            cross_references,
            occupied_begin_ids,
            occupied_field_ids,
        ),
        limits(),
    )
}

fn state_draft(
    targets: Vec<CrossReferenceTarget>,
    cross_references: Vec<CrossReferenceEntry>,
    occupied_begin_ids: Vec<u32>,
    occupied_field_ids: Vec<u32>,
) -> CrossReferenceDocumentStateDraft {
    CrossReferenceDocumentStateDraft {
        schema_version: CROSS_REFERENCE_SCHEMA_VERSION.to_owned(),
        sections: vec![section(false)],
        targets,
        cross_references,
        occupied_non_cross_reference_begin_control_ids: occupied_begin_ids,
        occupied_non_cross_reference_field_ids: occupied_field_ids,
        occupied_non_cross_reference_field_name_sha256: Vec::new(),
        non_cross_reference_content_sha256: A.to_owned(),
        unrelated_field_inventory_sha256: B.to_owned(),
        bookmark_inventory_sha256: C.to_owned(),
        note_inventory_sha256: D.to_owned(),
        object_inventory_sha256: A.to_owned(),
        numbering_inventory_sha256: B.to_owned(),
        style_catalog_sha256: C.to_owned(),
        relationship_inventory_sha256: D.to_owned(),
        resource_inventory_sha256: A.to_owned(),
        document_protection_sha256: B.to_owned(),
        opaque_document_state_sha256: C.to_owned(),
        document_locked: false,
    }
}

fn request(
    source: &CrossReferenceDocumentState,
    cross_reference: CrossReferenceEntry,
) -> Result<CrossReferenceRequest, CrossReferenceError> {
    CrossReferenceRequest::from_draft(
        CrossReferenceRequestDraft {
            schema_version: CROSS_REFERENCE_SCHEMA_VERSION.to_owned(),
            request_id: id("request-1"),
            expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
            expected_document_flow_sha256: FLOW_A.to_owned(),
            target_document_flow_sha256: FLOW_B.to_owned(),
            operation: CrossReferenceOperation::Insert {
                insertion_index: source.cross_references().len(),
                cross_reference: Box::new(cross_reference),
            },
        },
        source,
        FLOW_A,
        limits(),
    )
}

fn execute(
    source: &CrossReferenceDocumentState,
    cross_reference: CrossReferenceEntry,
) -> Result<CrossReferenceDocumentState, CrossReferenceError> {
    let request = request(source, cross_reference)?;
    let plan = CrossReferenceBuilder::plan(source, &request, FLOW_A, limits())?;
    Ok(CrossReferenceBuilder::build(&plan, source, FLOW_A, limits())?.state)
}

fn value(state: &CrossReferenceDocumentState) -> Value {
    serde_json::from_slice(&state.canonical_json(limits()).expect("json")).expect("value")
}

#[test]
fn schema_capability_native_shape_and_projection_are_exact() {
    let target = target(1, CrossReferenceTargetKind::Heading);
    let reference = reference(1, &target, CrossReferenceDisplayKind::TargetText);
    let operation = CrossReferenceOperation::Insert {
        insertion_index: 0,
        cross_reference: Box::new(reference.clone()),
    };
    assert_eq!(operation.capability_id(), "ref.crossref_insert");
    assert_eq!(
        reference.native_pair.field_type,
        CrossReferenceFieldType::Crossref
    );
    assert_eq!(
        reference.cache.target_projection_sha256,
        target
            .projection_sha256(
                CrossReferenceDisplayKind::TargetText,
                &reference.anchor,
                limits(),
            )
            .expect("projection")
    );
}

#[test]
fn all_target_and_display_families_insert_with_exact_current_cache() {
    let targets = vec![
        target(1, CrossReferenceTargetKind::Bookmark),
        target(2, CrossReferenceTargetKind::Heading),
        target(3, CrossReferenceTargetKind::NumberedParagraph),
        target(4, CrossReferenceTargetKind::Caption),
        target(5, CrossReferenceTargetKind::Footnote),
        target(6, CrossReferenceTargetKind::Endnote),
    ];
    let displays = [
        CrossReferenceDisplayKind::TargetName,
        CrossReferenceDisplayKind::TargetText,
        CrossReferenceDisplayKind::NumberOnly,
        CrossReferenceDisplayKind::LabelAndNumber,
        CrossReferenceDisplayKind::PageNumber,
        CrossReferenceDisplayKind::RelativePosition,
    ];
    let mut current = state(targets.clone(), Vec::new(), Vec::new(), Vec::new()).expect("state");
    for (offset, (target, display)) in targets.iter().zip(displays).enumerate() {
        current = execute(
            &current,
            reference(
                u32::try_from(offset + 1).expect("small fixture"),
                target,
                display,
            ),
        )
        .expect("insert");
    }
    assert_eq!(current.cross_references().len(), 6);
}

#[test]
fn insertion_changes_only_cross_reference_inventory() {
    let target = target(1, CrossReferenceTargetKind::Heading);
    let source = state(vec![target.clone()], Vec::new(), vec![900], vec![901]).expect("state");
    let after = execute(
        &source,
        reference(1, &target, CrossReferenceDisplayKind::TargetText),
    )
    .expect("insert");
    let before = value(&source);
    let after_value = value(&after);
    for key in before.as_object().expect("object").keys() {
        if key != "cross_references" {
            assert_eq!(before[key], after_value[key], "preserved {key}");
        }
    }
}

#[test]
fn target_rename_and_cache_update_state_are_classified_exactly() {
    let original = target(1, CrossReferenceTargetKind::Heading);
    let mut cached = reference(1, &original, CrossReferenceDisplayKind::TargetName);
    let mut renamed = original.clone();
    renamed.semantic_name_sha256 = B.to_owned();

    assert_eq!(
        state(
            vec![renamed.clone()],
            vec![cached.clone()],
            Vec::new(),
            Vec::new(),
        ),
        Err(CrossReferenceError::InvalidCache)
    );
    cached.cache.status = CrossReferenceCacheStatus::Stale;
    state(
        vec![renamed.clone()],
        vec![cached.clone()],
        Vec::new(),
        Vec::new(),
    )
    .expect("stale state");

    cached.cache.target_projection_sha256 = renamed
        .projection_sha256(
            CrossReferenceDisplayKind::TargetName,
            &cached.anchor,
            limits(),
        )
        .expect("renamed projection");
    cached.cache.display_value_sha256 = A.to_owned();
    cached.cache.status = CrossReferenceCacheStatus::Current;
    state(vec![renamed], vec![cached], Vec::new(), Vec::new()).expect("refreshed state");
}

#[test]
fn missing_incompatible_and_bad_containment_targets_fail_closed() {
    let target = target(1, CrossReferenceTargetKind::Bookmark);
    let mut missing = reference(1, &target, CrossReferenceDisplayKind::TargetText);
    missing.target_id = id("missing");
    assert_eq!(
        state(vec![target.clone()], vec![missing], Vec::new(), Vec::new()),
        Err(CrossReferenceError::InvalidTarget)
    );

    let mut incompatible = reference(1, &target, CrossReferenceDisplayKind::TargetText);
    incompatible.display_kind = CrossReferenceDisplayKind::LabelAndNumber;
    assert_eq!(
        state(
            vec![target.clone()],
            vec![incompatible],
            Vec::new(),
            Vec::new(),
        ),
        Err(CrossReferenceError::InvalidTarget)
    );

    let mut outside = reference(1, &target, CrossReferenceDisplayKind::TargetText);
    outside.containing_target_id = Some(target.identity.logical_target_id.clone());
    assert_eq!(
        state(vec![target], vec![outside], Vec::new(), Vec::new()),
        Err(CrossReferenceError::InvalidTarget)
    );
}

#[test]
fn target_dependencies_and_contained_reference_cycles_fail_closed() {
    let mut first = target(1, CrossReferenceTargetKind::Heading);
    let mut second = target(2, CrossReferenceTargetKind::Heading);
    first.dependency_target_ids = vec![second.identity.logical_target_id.clone()];
    second.dependency_target_ids = vec![first.identity.logical_target_id.clone()];
    assert_eq!(
        state(vec![first, second], Vec::new(), Vec::new(), Vec::new()),
        Err(CrossReferenceError::ReferenceCycle)
    );

    let owner = target(1, CrossReferenceTargetKind::Heading);
    let mut referenced = target(2, CrossReferenceTargetKind::Heading);
    referenced.dependency_target_ids = vec![owner.identity.logical_target_id.clone()];
    let contained_anchor = anchor(0, 110, 111);
    let contained = reference_at(
        1,
        &referenced,
        CrossReferenceDisplayKind::TargetText,
        &contained_anchor,
        Some(owner.identity.logical_target_id.clone()),
    );
    assert_eq!(
        state(
            vec![owner, referenced],
            vec![contained],
            Vec::new(),
            Vec::new(),
        ),
        Err(CrossReferenceError::ReferenceCycle)
    );
}

#[test]
fn native_pair_duplicates_and_global_occupied_ids_are_rejected() {
    let target = target(1, CrossReferenceTargetKind::Heading);
    let reference = reference(1, &target, CrossReferenceDisplayKind::TargetText);
    assert_eq!(
        state(
            vec![target.clone()],
            vec![reference.clone()],
            vec![1001],
            Vec::new(),
        ),
        Err(CrossReferenceError::InvalidIdentity)
    );
    assert_eq!(
        state(
            vec![target.clone()],
            vec![reference.clone()],
            Vec::new(),
            vec![2001],
        ),
        Err(CrossReferenceError::InvalidIdentity)
    );
    let collision_target = self::target(2, CrossReferenceTargetKind::Heading);
    let collision_reference =
        self::reference(2, &collision_target, CrossReferenceDisplayKind::TargetText);
    let mut name_collision = state_draft(
        vec![collision_target],
        vec![collision_reference],
        Vec::new(),
        Vec::new(),
    );
    name_collision.occupied_non_cross_reference_field_name_sha256 = vec![format!("{:064x}", 2)];
    assert_eq!(
        CrossReferenceDocumentState::from_draft(name_collision, limits()),
        Err(CrossReferenceError::FieldNameConflict)
    );
    let mut bad_native = reference;
    bad_native.native_pair.end_field_id += 1;
    assert_eq!(
        state(vec![target], vec![bad_native], Vec::new(), Vec::new()),
        Err(CrossReferenceError::InvalidNativeBinding)
    );
}

#[test]
fn protection_index_and_stale_insert_are_side_effect_free() {
    let target = target(1, CrossReferenceTargetKind::Heading);
    let source = state(vec![target.clone()], Vec::new(), Vec::new(), Vec::new()).expect("state");
    let mut stale = reference(1, &target, CrossReferenceDisplayKind::TargetText);
    stale.cache.target_projection_sha256 = A.to_owned();
    stale.cache.status = CrossReferenceCacheStatus::Stale;
    assert_eq!(
        request(&source, stale),
        Err(CrossReferenceError::InvalidCache)
    );

    let mut protected_draft = state_draft(vec![target.clone()], Vec::new(), Vec::new(), Vec::new());
    protected_draft.sections[0].locked = true;
    let protected_source =
        CrossReferenceDocumentState::from_draft(protected_draft, limits()).expect("protected");
    assert_eq!(
        request(
            &protected_source,
            reference(1, &target, CrossReferenceDisplayKind::TargetText)
        ),
        Err(CrossReferenceError::Protected)
    );

    let mut initially_locked = reference(1, &target, CrossReferenceDisplayKind::TargetText);
    initially_locked.locked = true;
    assert!(request(&source, initially_locked).is_ok());

    let valid = reference(1, &target, CrossReferenceDisplayKind::TargetText);
    let draft = CrossReferenceRequestDraft {
        schema_version: CROSS_REFERENCE_SCHEMA_VERSION.to_owned(),
        request_id: id("request-1"),
        expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
        expected_document_flow_sha256: FLOW_A.to_owned(),
        target_document_flow_sha256: FLOW_B.to_owned(),
        operation: CrossReferenceOperation::Insert {
            insertion_index: 1,
            cross_reference: Box::new(valid),
        },
    };
    assert_eq!(
        CrossReferenceRequest::from_draft(draft, &source, FLOW_A, limits()),
        Err(CrossReferenceError::InvalidInsertionIndex)
    );
}

#[test]
fn request_plan_and_build_recheck_exact_state_and_flow() {
    let target_entry = target(1, CrossReferenceTargetKind::Heading);
    let source = state(
        vec![target_entry.clone()],
        Vec::new(),
        Vec::new(),
        Vec::new(),
    )
    .expect("state");
    let reference = reference(1, &target_entry, CrossReferenceDisplayKind::TargetText);
    let request = request(&source, reference).expect("request");
    assert_eq!(
        CrossReferenceBuilder::plan(&source, &request, FLOW_B, limits()),
        Err(CrossReferenceError::DocumentFlowDrift)
    );
    let plan = CrossReferenceBuilder::plan(&source, &request, FLOW_A, limits()).expect("plan");
    let drifted = state(
        vec![target(2, CrossReferenceTargetKind::Heading)],
        Vec::new(),
        Vec::new(),
        Vec::new(),
    )
    .expect("drifted");
    assert_eq!(
        CrossReferenceBuilder::build(&plan, &drifted, FLOW_A, limits()),
        Err(CrossReferenceError::SourceStateDrift)
    );
    assert_eq!(
        CrossReferenceBuilder::build(&plan, &source, FLOW_B, limits()),
        Err(CrossReferenceError::DocumentFlowDrift)
    );
    assert_eq!(
        CrossReferenceBuilder::build(&plan, &source, FLOW_A, limits())
            .expect("build")
            .state
            .cross_references()
            .len(),
        1
    );
}

#[test]
fn strict_json_limits_errors_and_debug_are_bounded_and_redacted() {
    let target = target(1, CrossReferenceTargetKind::Heading);
    let source = state(vec![target.clone()], Vec::new(), Vec::new(), Vec::new()).expect("state");
    let draft = CrossReferenceRequestDraft {
        schema_version: CROSS_REFERENCE_SCHEMA_VERSION.to_owned(),
        request_id: id("secret-request"),
        expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
        expected_document_flow_sha256: FLOW_A.to_owned(),
        target_document_flow_sha256: FLOW_B.to_owned(),
        operation: CrossReferenceOperation::Insert {
            insertion_index: 0,
            cross_reference: Box::new(reference(1, &target, CrossReferenceDisplayKind::TargetText)),
        },
    };
    let bytes = serde_json::to_vec(&draft).expect("json");
    let duplicate = String::from_utf8(bytes.clone()).expect("utf8").replacen(
        "{\"schema_version\"",
        "{\"schema_version\":\"hwpx-agent.cross-reference/v1\",\"schema_version\"",
        1,
    );
    assert_eq!(
        CrossReferenceRequest::from_json(duplicate.as_bytes(), &source, FLOW_A, limits()),
        Err(CrossReferenceError::InvalidJson)
    );
    let tiny = CrossReferenceLimits::new(CrossReferenceLimitConfig {
        input_bytes: 32,
        ..CrossReferenceLimitConfig::default()
    })
    .expect("tiny");
    assert_eq!(
        CrossReferenceRequest::from_json(&bytes, &source, FLOW_A, tiny),
        Err(CrossReferenceError::InputLimit)
    );
    let valid =
        CrossReferenceRequest::from_json(&bytes, &source, FLOW_A, limits()).expect("valid request");
    let debug = format!("{valid:?} {source:?} {target:?}");
    for secret in ["secret-request", "target-1", A, B] {
        assert!(!debug.contains(secret));
    }
    assert!(debug.len() < 512);
    assert_eq!(
        CrossReferenceError::ReferenceCycle.code(),
        "cross_reference_cycle"
    );
}
