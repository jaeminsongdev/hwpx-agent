#![allow(clippy::expect_used)]

use domain_ir::{
    GeneratedCache, GeneratedCacheStatus, IndexGeneratedBinding, IndexGeneratedBlock, IndexMark,
    IndexMarkNativeTag, IndexSettings, LinkAnchor, LinkPoint, LogicalId, TOC_INDEX_SCHEMA_VERSION,
    TocFieldType, TocGeneratedBlock, TocIndexBuilder, TocIndexDocumentState,
    TocIndexDocumentStateDraft, TocIndexError, TocIndexLimitConfig, TocIndexLimits,
    TocIndexOperation, TocIndexRequest, TocIndexRequestDraft, TocIndexSectionState, TocLeaderKind,
    TocMark, TocMarkNativeTag, TocNativeBeginTag, TocNativeEndTag, TocNativePair,
    TocSemanticBinding, TocSettings, TocSource,
};

const A: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const B: &str = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
const C: &str = "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc";
const D: &str = "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd";
const FLOW_A: &str = "1111111111111111111111111111111111111111111111111111111111111111";
const FLOW_B: &str = "2222222222222222222222222222222222222222222222222222222222222222";

fn limits() -> TocIndexLimits {
    TocIndexLimits::new(TocIndexLimitConfig::default()).expect("limits")
}

fn id(value: &str) -> LogicalId {
    LogicalId::parse(value).expect("id")
}

fn anchor(paragraph: u32, start: u32, end: u32) -> LinkAnchor {
    LinkAnchor {
        section_id: id("section-1"),
        start: LinkPoint {
            paragraph_ordinal: paragraph,
            run_ordinal: 0,
            inline_ordinal: start,
        },
        end: LinkPoint {
            paragraph_ordinal: paragraph,
            run_ordinal: 0,
            inline_ordinal: end,
        },
    }
}

fn source(index: u32, level: u8, paragraph: u32) -> TocSource {
    TocSource {
        logical_source_id: id(&format!("source-{index}")),
        anchor: anchor(paragraph, 0, 20),
        level,
        text_sha256: A.to_owned(),
        numbering_linkage_sha256: B.to_owned(),
        style_sha256: C.to_owned(),
        page_assignment_sha256: D.to_owned(),
        opaque_source_state_sha256: A.to_owned(),
        opaque_properties: Vec::new(),
        locked: false,
    }
}

fn toc_mark(index: u32, source_index: u32, paragraph: u32) -> TocMark {
    TocMark {
        logical_mark_id: id(&format!("toc-mark-{index}")),
        source_id: id(&format!("source-{source_index}")),
        anchor: anchor(paragraph, 0, 20),
        native_tag: TocMarkNativeTag::TitleMark,
        ignore: false,
        opaque_native_payload_sha256: B.to_owned(),
        opaque_properties: Vec::new(),
        locked: false,
    }
}

fn index_mark(index: u32, paragraph: u32) -> IndexMark {
    IndexMark {
        logical_mark_id: id(&format!("index-mark-{index}")),
        control_id: 3000 + index,
        anchor: anchor(paragraph, 30, 40),
        native_tag: IndexMarkNativeTag::Indexmark,
        first_key_sha256: A.to_owned(),
        second_key_sha256: index.is_multiple_of(2).then(|| B.to_owned()),
        first_sort_key_sha256: C.to_owned(),
        second_sort_key_sha256: index.is_multiple_of(2).then(|| D.to_owned()),
        page_assignment_sha256: B.to_owned(),
        opaque_native_payload_sha256: C.to_owned(),
        opaque_properties: Vec::new(),
        locked: false,
    }
}

fn toc_settings() -> TocSettings {
    TocSettings {
        minimum_level: 1,
        maximum_level: 3,
        include_page_numbers: true,
        right_align_page_numbers: true,
        hyperlink_entries: true,
        leader: TocLeaderKind::Dot,
        level_style_sha256: vec![A.to_owned(), B.to_owned(), C.to_owned()],
        page_number_format_sha256: D.to_owned(),
        numbering_render_policy_sha256: A.to_owned(),
    }
}

fn index_settings() -> IndexSettings {
    IndexSettings {
        locale: "ko-KR".to_owned(),
        collation_profile_sha256: A.to_owned(),
        heading_style_sha256: B.to_owned(),
        entry_style_sha256: C.to_owned(),
        subentry_style_sha256: D.to_owned(),
        page_number_format_sha256: A.to_owned(),
        duplicate_page_policy_sha256: B.to_owned(),
        column_layout_sha256: C.to_owned(),
    }
}

fn native_pair(index: u32) -> TocNativePair {
    TocNativePair {
        begin_tag: TocNativeBeginTag::FieldBegin,
        end_tag: TocNativeEndTag::FieldEnd,
        field_type: TocFieldType::Tableofcontents,
        semantic_binding: TocSemanticBinding::UnverifiedFieldParameters,
        end_begin_control_id_ref: 1000 + index,
        end_field_id: 2000 + index,
        field_name_sha256: Some(format!("{index:064x}")),
        editable: true,
        dirty: false,
        z_order: -1,
        parameters_sha256: A.to_owned(),
        sub_list_sha256: Some(B.to_owned()),
        meta_tag_sha256: None,
        opaque_begin_state_sha256: C.to_owned(),
        opaque_end_state_sha256: D.to_owned(),
    }
}

fn draft() -> TocIndexDocumentStateDraft {
    TocIndexDocumentStateDraft {
        schema_version: TOC_INDEX_SCHEMA_VERSION.to_owned(),
        sections: vec![TocIndexSectionState {
            section_id: id("section-1"),
            paragraph_count: 8,
            run_topology_sha256: A.to_owned(),
            inline_topology_sha256: B.to_owned(),
            page_assignment_sha256: C.to_owned(),
            opaque_section_state_sha256: D.to_owned(),
            locked: false,
        }],
        toc_sources: vec![source(1, 1, 0), source(2, 2, 1), source(3, 3, 2)],
        toc_marks: Vec::new(),
        index_marks: Vec::new(),
        toc_blocks: Vec::new(),
        index_blocks: Vec::new(),
        occupied_non_toc_index_control_ids: vec![50],
        occupied_non_toc_index_field_ids: vec![60],
        occupied_non_toc_index_field_name_sha256: vec![D.to_owned()],
        non_toc_index_content_sha256: A.to_owned(),
        unrelated_field_inventory_sha256: B.to_owned(),
        reference_inventory_sha256: C.to_owned(),
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

fn state() -> TocIndexDocumentState {
    TocIndexDocumentState::from_draft(draft(), limits()).expect("state")
}

fn execute(source: &TocIndexDocumentState, operation: TocIndexOperation) -> TocIndexDocumentState {
    let request = TocIndexRequest::from_draft(
        TocIndexRequestDraft {
            schema_version: TOC_INDEX_SCHEMA_VERSION.to_owned(),
            request_id: id("request-1"),
            expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
            expected_document_flow_sha256: FLOW_A.to_owned(),
            target_document_flow_sha256: FLOW_B.to_owned(),
            operation,
        },
        source,
        FLOW_A,
        limits(),
    )
    .expect("request");
    let plan = TocIndexBuilder::plan(source, &request, FLOW_A, limits()).expect("plan");
    TocIndexBuilder::build(&plan, source, FLOW_A, limits())
        .expect("build")
        .state
}

fn toc_block(state: &TocIndexDocumentState, index: u32) -> TocGeneratedBlock {
    let settings = toc_settings();
    TocGeneratedBlock {
        logical_block_id: id(&format!("toc-block-{index}")),
        begin_control_id: 1000 + index,
        field_id: 2000 + index,
        anchor: anchor(5, 0, 5),
        cache: GeneratedCache {
            source_projection_sha256: TocGeneratedBlock::projection_sha256(
                state.toc_sources(),
                state.toc_marks(),
                &settings,
                limits(),
            )
            .expect("projection"),
            generated_content_sha256: B.to_owned(),
            status: GeneratedCacheStatus::Current,
        },
        settings,
        native_pair: native_pair(index),
        opaque_generated_state_sha256: C.to_owned(),
        opaque_properties: Vec::new(),
        locked: false,
    }
}

fn index_block(state: &TocIndexDocumentState, index: u32) -> IndexGeneratedBlock {
    let settings = index_settings();
    IndexGeneratedBlock {
        logical_block_id: id(&format!("index-block-{index}")),
        anchor: anchor(6, 0, 5),
        semantic_binding: IndexGeneratedBinding::UnverifiedGeneratedRange,
        cache: GeneratedCache {
            source_projection_sha256: IndexGeneratedBlock::projection_sha256(
                state.index_marks(),
                &settings,
                limits(),
            )
            .expect("projection"),
            generated_content_sha256: C.to_owned(),
            status: GeneratedCacheStatus::Current,
        },
        settings,
        opaque_generated_state_sha256: D.to_owned(),
        opaque_properties: Vec::new(),
        locked: false,
    }
}

#[test]
fn all_p09_owned_capabilities_build_with_multilevel_state() {
    let initial = state();
    let marked = execute(
        &initial,
        TocIndexOperation::TocMarkInsert {
            insertion_index: 0,
            mark: toc_mark(1, 1, 0),
        },
    );
    let hidden = execute(
        &marked,
        TocIndexOperation::TocMarkHide {
            mark_id: id("toc-mark-1"),
        },
    );
    assert!(hidden.toc_marks()[0].ignore);
    let marked_again = execute(
        &hidden,
        TocIndexOperation::TocMarkInsert {
            insertion_index: 1,
            mark: toc_mark(2, 2, 1),
        },
    );
    let table = toc_block(&marked_again, 1);
    let with_toc = execute(
        &marked_again,
        TocIndexOperation::TocCreate {
            insertion_index: 0,
            block: Box::new(table),
        },
    );
    let with_index_mark = execute(
        &with_toc,
        TocIndexOperation::IndexMarkInsert {
            insertion_index: 0,
            mark: index_mark(2, 3),
        },
    );
    let index = index_block(&with_index_mark, 1);
    let complete = execute(
        &with_index_mark,
        TocIndexOperation::IndexCreate {
            insertion_index: 0,
            block: Box::new(index),
        },
    );
    assert_eq!(complete.toc_blocks().len(), 1);
    assert_eq!(complete.index_blocks().len(), 1);
    assert_eq!(complete.index_marks().len(), 1);
}

#[test]
fn toc_mark_insert_cannot_bypass_the_dedicated_hide_transition() {
    let source = state();
    let mut hidden_mark = toc_mark(1, 1, 0);
    hidden_mark.ignore = true;
    let error = TocIndexRequest::from_draft(
        TocIndexRequestDraft {
            schema_version: TOC_INDEX_SCHEMA_VERSION.to_owned(),
            request_id: id("request-1"),
            expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
            expected_document_flow_sha256: FLOW_A.to_owned(),
            target_document_flow_sha256: FLOW_B.to_owned(),
            operation: TocIndexOperation::TocMarkInsert {
                insertion_index: 0,
                mark: hidden_mark,
            },
        },
        &source,
        FLOW_A,
        limits(),
    )
    .expect_err("hidden insertion must use the dedicated hide transition");
    assert_eq!(error, TocIndexError::InvalidMark);
}

#[test]
fn source_or_index_mark_changes_make_generated_cache_stale() {
    let settings = toc_settings();
    let included_source = source(1, 1, 0);
    let included_mark = toc_mark(1, 1, 0);
    let baseline = TocGeneratedBlock::projection_sha256(
        std::slice::from_ref(&included_source),
        std::slice::from_ref(&included_mark),
        &settings,
        limits(),
    )
    .expect("baseline projection");
    let sources_with_unrelated = vec![included_source.clone(), source(4, 4, 3), source(2, 2, 1)];
    let marks_with_out_of_level = vec![included_mark.clone(), toc_mark(4, 4, 3)];
    assert_eq!(
        TocGeneratedBlock::projection_sha256(
            &sources_with_unrelated,
            &marks_with_out_of_level,
            &settings,
            limits(),
        )
        .expect("filtered projection"),
        baseline,
        "out-of-level and unmarked sources must not invalidate a TOC cache"
    );
    let mut changed_included_source = included_source;
    changed_included_source.text_sha256 = D.to_owned();
    assert_ne!(
        TocGeneratedBlock::projection_sha256(
            &[changed_included_source],
            &[included_mark],
            &settings,
            limits(),
        )
        .expect("changed projection"),
        baseline,
        "a marked source inside the selected level range must invalidate the cache"
    );

    let marked = execute(
        &state(),
        TocIndexOperation::TocMarkInsert {
            insertion_index: 0,
            mark: toc_mark(1, 1, 0),
        },
    );
    let block = toc_block(&marked, 1);
    let with_toc = execute(
        &marked,
        TocIndexOperation::TocCreate {
            insertion_index: 0,
            block: Box::new(block),
        },
    );
    let changed = execute(
        &with_toc,
        TocIndexOperation::TocMarkHide {
            mark_id: id("toc-mark-1"),
        },
    );
    assert_eq!(
        changed.toc_blocks()[0].cache.status,
        GeneratedCacheStatus::Stale
    );

    let first = execute(
        &state(),
        TocIndexOperation::IndexMarkInsert {
            insertion_index: 0,
            mark: index_mark(1, 3),
        },
    );
    let index = index_block(&first, 1);
    let generated = execute(
        &first,
        TocIndexOperation::IndexCreate {
            insertion_index: 0,
            block: Box::new(index),
        },
    );
    let changed = execute(
        &generated,
        TocIndexOperation::IndexMarkInsert {
            insertion_index: 1,
            mark: index_mark(2, 4),
        },
    );
    assert_eq!(
        changed.index_blocks()[0].cache.status,
        GeneratedCacheStatus::Stale
    );
}

#[test]
fn generated_create_rejects_stale_cache() {
    let source = state();
    let mut block = toc_block(&source, 1);
    block.cache.source_projection_sha256 = D.to_owned();
    block.cache.status = GeneratedCacheStatus::Stale;
    let error = TocIndexRequest::from_draft(
        TocIndexRequestDraft {
            schema_version: TOC_INDEX_SCHEMA_VERSION.to_owned(),
            request_id: id("request-1"),
            expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
            expected_document_flow_sha256: FLOW_A.to_owned(),
            target_document_flow_sha256: FLOW_B.to_owned(),
            operation: TocIndexOperation::TocCreate {
                insertion_index: 0,
                block: Box::new(block),
            },
        },
        &source,
        FLOW_A,
        limits(),
    )
    .expect_err("stale");
    assert_eq!(error, TocIndexError::InvalidGeneratedState);
}

#[test]
fn dangling_and_outside_toc_marks_fail_closed() {
    let source = state();
    let mut dangling = toc_mark(1, 99, 0);
    let operation = TocIndexOperation::TocMarkInsert {
        insertion_index: 0,
        mark: dangling.clone(),
    };
    let draft = TocIndexRequestDraft {
        schema_version: TOC_INDEX_SCHEMA_VERSION.to_owned(),
        request_id: id("request-1"),
        expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
        expected_document_flow_sha256: FLOW_A.to_owned(),
        target_document_flow_sha256: FLOW_B.to_owned(),
        operation,
    };
    assert_eq!(
        TocIndexRequest::from_draft(draft, &source, FLOW_A, limits()).expect_err("dangling"),
        TocIndexError::InvalidMark
    );
    dangling.source_id = id("source-1");
    dangling.anchor = anchor(1, 0, 20);
    let outside_draft = TocIndexRequestDraft {
        schema_version: TOC_INDEX_SCHEMA_VERSION.to_owned(),
        request_id: id("request-2"),
        expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
        expected_document_flow_sha256: FLOW_A.to_owned(),
        target_document_flow_sha256: FLOW_B.to_owned(),
        operation: TocIndexOperation::TocMarkInsert {
            insertion_index: 0,
            mark: dangling,
        },
    };
    assert_eq!(
        TocIndexRequest::from_draft(outside_draft, &source, FLOW_A, limits()).expect_err("outside"),
        TocIndexError::InvalidMark
    );
}

#[test]
fn native_id_and_field_name_collisions_are_rejected() {
    let mut collision = index_mark(1, 3);
    collision.control_id = 50;
    let mut draft_state = draft();
    draft_state.index_marks.push(collision);
    assert_eq!(
        TocIndexDocumentState::from_draft(draft_state, limits()).expect_err("control collision"),
        TocIndexError::InvalidIdentity
    );

    let source = state();
    let mut block = toc_block(&source, 1);
    block.native_pair.field_name_sha256 = Some(D.to_owned());
    let mut draft_state = draft();
    draft_state.toc_blocks.push(block);
    assert_eq!(
        TocIndexDocumentState::from_draft(draft_state, limits()).expect_err("name collision"),
        TocIndexError::FieldNameConflict
    );
}

#[test]
fn invalid_level_style_and_index_key_pairing_are_rejected() {
    let source = state();
    let mut block = toc_block(&source, 1);
    let _ = block.settings.level_style_sha256.pop();
    let mut draft_state = draft();
    draft_state.toc_blocks.push(block);
    assert_eq!(
        TocIndexDocumentState::from_draft(draft_state, limits()).expect_err("style count"),
        TocIndexError::InvalidGeneratedState
    );

    let mut mark = index_mark(2, 3);
    mark.second_sort_key_sha256 = None;
    let mut draft_state = draft();
    draft_state.index_marks.push(mark);
    assert_eq!(
        TocIndexDocumentState::from_draft(draft_state, limits()).expect_err("key pair"),
        TocIndexError::InvalidMark
    );
}

#[test]
fn protection_and_repeated_hide_are_rejected() {
    let marked = execute(
        &state(),
        TocIndexOperation::TocMarkInsert {
            insertion_index: 0,
            mark: toc_mark(1, 1, 0),
        },
    );
    let hidden = execute(
        &marked,
        TocIndexOperation::TocMarkHide {
            mark_id: id("toc-mark-1"),
        },
    );
    let hide_draft = TocIndexRequestDraft {
        schema_version: TOC_INDEX_SCHEMA_VERSION.to_owned(),
        request_id: id("request-2"),
        expected_source_state_sha256: hidden.canonical_sha256(limits()).expect("digest"),
        expected_document_flow_sha256: FLOW_A.to_owned(),
        target_document_flow_sha256: FLOW_B.to_owned(),
        operation: TocIndexOperation::TocMarkHide {
            mark_id: id("toc-mark-1"),
        },
    };
    assert_eq!(
        TocIndexRequest::from_draft(hide_draft, &hidden, FLOW_A, limits()).expect_err("repeat"),
        TocIndexError::InvalidMark
    );

    let mut protected = draft();
    protected.document_locked = true;
    let protected =
        TocIndexDocumentState::from_draft(protected, limits()).expect("protected state");
    let draft = TocIndexRequestDraft {
        schema_version: TOC_INDEX_SCHEMA_VERSION.to_owned(),
        request_id: id("request-3"),
        expected_source_state_sha256: protected.canonical_sha256(limits()).expect("digest"),
        expected_document_flow_sha256: FLOW_A.to_owned(),
        target_document_flow_sha256: FLOW_B.to_owned(),
        operation: TocIndexOperation::IndexMarkInsert {
            insertion_index: 0,
            mark: index_mark(1, 3),
        },
    };
    assert_eq!(
        TocIndexRequest::from_draft(draft, &protected, FLOW_A, limits()).expect_err("protected"),
        TocIndexError::Protected
    );
}

#[test]
fn request_and_build_recheck_state_and_flow_drift() {
    let source = state();
    let draft = TocIndexRequestDraft {
        schema_version: TOC_INDEX_SCHEMA_VERSION.to_owned(),
        request_id: id("request-1"),
        expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
        expected_document_flow_sha256: FLOW_A.to_owned(),
        target_document_flow_sha256: FLOW_B.to_owned(),
        operation: TocIndexOperation::IndexMarkInsert {
            insertion_index: 0,
            mark: index_mark(1, 3),
        },
    };
    assert_eq!(
        TocIndexRequest::from_draft(draft.clone(), &source, FLOW_B, limits())
            .expect_err("request flow"),
        TocIndexError::DocumentFlowDrift
    );
    let request = TocIndexRequest::from_draft(draft, &source, FLOW_A, limits()).expect("request");
    assert_eq!(
        TocIndexBuilder::plan(&source, &request, FLOW_B, limits()).expect_err("plan flow"),
        TocIndexError::DocumentFlowDrift
    );
    let plan = TocIndexBuilder::plan(&source, &request, FLOW_A, limits()).expect("plan");
    assert_eq!(
        TocIndexBuilder::build(&plan, &source, FLOW_B, limits()).expect_err("build flow"),
        TocIndexError::DocumentFlowDrift
    );
    let changed = execute(
        &source,
        TocIndexOperation::TocMarkInsert {
            insertion_index: 0,
            mark: toc_mark(1, 1, 0),
        },
    );
    assert_eq!(
        TocIndexBuilder::build(&plan, &changed, FLOW_A, limits()).expect_err("state drift"),
        TocIndexError::SourceStateDrift
    );
}

#[test]
fn strict_json_rejects_duplicate_and_unknown_keys() {
    let source = state();
    let duplicate = br#"{"schema_version":"hwpx-agent.toc-index/v1","schema_version":"hwpx-agent.toc-index/v1"}"#;
    assert_eq!(
        TocIndexRequest::from_json(duplicate, &source, FLOW_A, limits()).expect_err("duplicate"),
        TocIndexError::InvalidJson
    );
    let value = serde_json::to_value(TocIndexRequestDraft {
        schema_version: TOC_INDEX_SCHEMA_VERSION.to_owned(),
        request_id: id("request-1"),
        expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
        expected_document_flow_sha256: FLOW_A.to_owned(),
        target_document_flow_sha256: FLOW_B.to_owned(),
        operation: TocIndexOperation::IndexMarkInsert {
            insertion_index: 0,
            mark: index_mark(1, 3),
        },
    })
    .expect("json");
    let mut object = value.as_object().expect("object").clone();
    object.insert("unknown".to_owned(), serde_json::Value::Bool(true));
    let bytes = serde_json::to_vec(&object).expect("bytes");
    assert_eq!(
        TocIndexRequest::from_json(&bytes, &source, FLOW_A, limits()).expect_err("unknown"),
        TocIndexError::InvalidJson
    );
}

#[test]
fn bounded_input_output_and_limit_configuration_fail_closed() {
    let bad = TocIndexLimitConfig {
        input_bytes: 2,
        output_bytes: 1,
        ..TocIndexLimitConfig::default()
    };
    assert_eq!(
        TocIndexLimits::new(bad).expect_err("invalid"),
        TocIndexError::InvalidLimit
    );
    let tiny = TocIndexLimits::new(TocIndexLimitConfig {
        input_bytes: 1,
        output_bytes: 1,
        ..TocIndexLimitConfig::default()
    })
    .expect("tiny");
    let source = state();
    assert_eq!(
        TocIndexRequest::from_json(b"{}", &source, FLOW_A, tiny).expect_err("input"),
        TocIndexError::InputLimit
    );
    assert_eq!(
        source.canonical_json(tiny).expect_err("output"),
        TocIndexError::OutputLimit
    );
}

#[test]
fn unrelated_state_is_preserved_and_debug_is_redacted() {
    let source = state();
    let changed = execute(
        &source,
        TocIndexOperation::IndexMarkInsert {
            insertion_index: 0,
            mark: index_mark(1, 3),
        },
    );
    let before: serde_json::Value =
        serde_json::from_slice(&source.canonical_json(limits()).expect("json")).expect("value");
    let after: serde_json::Value =
        serde_json::from_slice(&changed.canonical_json(limits()).expect("json")).expect("value");
    for key in [
        "non_toc_index_content_sha256",
        "unrelated_field_inventory_sha256",
        "reference_inventory_sha256",
        "note_inventory_sha256",
        "object_inventory_sha256",
        "numbering_inventory_sha256",
        "style_catalog_sha256",
        "relationship_inventory_sha256",
        "resource_inventory_sha256",
        "opaque_document_state_sha256",
    ] {
        assert_eq!(before[key], after[key], "{key}");
    }
    let debug = format!("{changed:?}");
    assert!(debug.contains("<redacted>"));
    assert!(!debug.contains(A));
}

#[test]
fn canonical_state_is_deterministic_and_native_boundaries_are_explicit() {
    let source = state();
    assert_eq!(
        source.canonical_json(limits()).expect("one"),
        source.canonical_json(limits()).expect("two")
    );
    let block = toc_block(&source, 1);
    assert_eq!(
        block.native_pair.semantic_binding,
        TocSemanticBinding::UnverifiedFieldParameters
    );
    let index = index_block(&source, 1);
    assert_eq!(
        index.semantic_binding,
        IndexGeneratedBinding::UnverifiedGeneratedRange
    );
}
