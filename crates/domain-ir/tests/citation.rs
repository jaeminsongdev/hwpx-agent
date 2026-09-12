#![allow(clippy::expect_used)]

use domain_ir::{
    BibliographyCatalogState, BibliographyFormatBinding, BibliographyManifestId,
    BibliographyMediaType, BibliographyPartPath, CITATION_SCHEMA_VERSION, CitationBuilder,
    CitationCache, CitationCacheStatus, CitationDisplayOptions, CitationDocumentState,
    CitationDocumentStateDraft, CitationError, CitationFieldType, CitationLimitConfig,
    CitationLimits, CitationLocator, CitationLocatorKind, CitationNativeBeginTag,
    CitationNativeEndTag, CitationNativePair, CitationNode, CitationOperation, CitationRequest,
    CitationRequestDraft, CitationSectionState, CitationSemanticBinding, CitationSource,
    LinkAnchor, LinkPoint, LogicalId,
};

const A: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const B: &str = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
const C: &str = "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc";
const D: &str = "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd";
const FLOW_A: &str = "1111111111111111111111111111111111111111111111111111111111111111";
const FLOW_B: &str = "2222222222222222222222222222222222222222222222222222222222222222";

fn limits() -> CitationLimits {
    CitationLimits::new(CitationLimitConfig::default()).expect("limits")
}

fn id(value: &str) -> LogicalId {
    LogicalId::parse(value).expect("id")
}

fn anchor(paragraph: u32) -> LinkAnchor {
    LinkAnchor {
        section_id: id("section-1"),
        start: LinkPoint {
            paragraph_ordinal: paragraph,
            run_ordinal: 0,
            inline_ordinal: 2,
        },
        end: LinkPoint {
            paragraph_ordinal: paragraph,
            run_ordinal: 0,
            inline_ordinal: 3,
        },
    }
}

fn source(index: u32, key: &str) -> CitationSource {
    CitationSource {
        logical_source_id: id(&format!("source-{index}")),
        provider_record_key_sha256: key.to_owned(),
        semantic_record_sha256: A.to_owned(),
        display_record_sha256: B.to_owned(),
        opaque_record_sha256: C.to_owned(),
        opaque_properties: Vec::new(),
        locked: false,
    }
}

fn catalog() -> BibliographyCatalogState {
    BibliographyCatalogState {
        logical_catalog_id: id("catalog-1"),
        part_path: BibliographyPartPath::CustomBibliographyXml,
        manifest_id: BibliographyManifestId::Bibliography,
        media_type: BibliographyMediaType::ApplicationXml,
        format_binding: BibliographyFormatBinding::UnverifiedOpaquePart,
        part_sha256: D.to_owned(),
        provider_id_sha256: A.to_owned(),
        provider_version_sha256: B.to_owned(),
        locale: "ko-KR".to_owned(),
        citation_style_sha256: C.to_owned(),
        sources: vec![source(1, A), source(2, B)],
        opaque_properties: Vec::new(),
        locked: false,
    }
}

fn options() -> CitationDisplayOptions {
    CitationDisplayOptions {
        locator: Some(CitationLocator {
            kind: CitationLocatorKind::Page,
            value_sha256: A.to_owned(),
        }),
        prefix_sha256: Some(B.to_owned()),
        suffix_sha256: Some(C.to_owned()),
        suppress_author: false,
        opaque_formatting_sha256: D.to_owned(),
    }
}

fn citation(
    catalog: &BibliographyCatalogState,
    index: u32,
    source_ids: Vec<LogicalId>,
) -> CitationNode {
    let display_options = options();
    CitationNode {
        logical_citation_id: id(&format!("citation-{index}")),
        begin_control_id: 1000 + index,
        field_id: 2000 + index,
        anchor: anchor(index - 1),
        cache: CitationCache {
            source_projection_sha256: CitationNode::projection_sha256(
                catalog,
                &source_ids,
                &display_options,
                limits(),
            )
            .expect("projection"),
            displayed_text_sha256: A.to_owned(),
            status: CitationCacheStatus::Current,
        },
        source_ids,
        display_options,
        native_pair: CitationNativePair {
            begin_tag: CitationNativeBeginTag::FieldBegin,
            end_tag: CitationNativeEndTag::FieldEnd,
            field_type: CitationFieldType::Citation,
            semantic_binding: CitationSemanticBinding::UnverifiedFieldParameters,
            end_begin_control_id_ref: 1000 + index,
            end_field_id: 2000 + index,
            field_name_sha256: Some(format!("{index:064x}")),
            editable: true,
            dirty: false,
            z_order: -1,
            parameters_sha256: B.to_owned(),
            sub_list_sha256: Some(C.to_owned()),
            meta_tag_sha256: None,
            opaque_begin_state_sha256: C.to_owned(),
            opaque_end_state_sha256: D.to_owned(),
        },
        opaque_citation_state_sha256: D.to_owned(),
        opaque_properties: Vec::new(),
        locked: false,
    }
}

fn draft() -> CitationDocumentStateDraft {
    CitationDocumentStateDraft {
        schema_version: CITATION_SCHEMA_VERSION.to_owned(),
        sections: vec![CitationSectionState {
            section_id: id("section-1"),
            paragraph_count: 8,
            run_topology_sha256: A.to_owned(),
            inline_topology_sha256: B.to_owned(),
            page_assignment_sha256: C.to_owned(),
            opaque_section_state_sha256: D.to_owned(),
            locked: false,
        }],
        bibliography: Some(catalog()),
        citations: Vec::new(),
        occupied_non_citation_control_ids: vec![50],
        occupied_non_citation_field_ids: vec![60],
        occupied_non_citation_field_name_sha256: vec![D.to_owned()],
        non_citation_content_sha256: A.to_owned(),
        unrelated_field_inventory_sha256: B.to_owned(),
        reference_inventory_sha256: C.to_owned(),
        note_inventory_sha256: D.to_owned(),
        toc_index_inventory_sha256: A.to_owned(),
        object_inventory_sha256: B.to_owned(),
        numbering_inventory_sha256: C.to_owned(),
        style_catalog_sha256: D.to_owned(),
        relationship_inventory_sha256: A.to_owned(),
        resource_inventory_sha256: B.to_owned(),
        document_protection_sha256: C.to_owned(),
        opaque_document_state_sha256: D.to_owned(),
        document_locked: false,
    }
}

fn state() -> CitationDocumentState {
    CitationDocumentState::from_draft(draft(), limits()).expect("state")
}

fn request(source: &CitationDocumentState, operation: CitationOperation) -> CitationRequest {
    CitationRequest::from_draft(
        CitationRequestDraft {
            schema_version: CITATION_SCHEMA_VERSION.to_owned(),
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
    .expect("request")
}

fn execute(source: &CitationDocumentState, operation: CitationOperation) -> CitationDocumentState {
    let request = request(source, operation);
    let plan = CitationBuilder::plan(source, &request, FLOW_A, limits()).expect("plan");
    CitationBuilder::build(&plan, source, FLOW_A, limits())
        .expect("build")
        .state
}

#[test]
fn inserts_single_and_clustered_citations_with_exact_capability() {
    let initial = state();
    let first = citation(
        initial.bibliography().expect("catalog"),
        1,
        vec![id("source-1")],
    );
    let operation = CitationOperation::CitationInsert {
        insertion_index: 0,
        citation: Box::new(first),
    };
    assert_eq!(operation.capability_id(), "ref.citation_insert");
    let once = execute(&initial, operation);
    let clustered = citation(
        once.bibliography().expect("catalog"),
        2,
        vec![id("source-2"), id("source-1")],
    );
    let complete = execute(
        &once,
        CitationOperation::CitationInsert {
            insertion_index: 1,
            citation: Box::new(clustered),
        },
    );
    assert_eq!(complete.citations().len(), 2);
    assert_eq!(complete.citations()[1].source_ids.len(), 2);
}

#[test]
fn projection_binds_only_selected_records_in_citation_order() {
    let base = catalog();
    let display = options();
    let ids = vec![id("source-1")];
    let baseline = CitationNode::projection_sha256(&base, &ids, &display, limits())
        .expect("baseline projection");

    let mut unrelated_changed = base.clone();
    unrelated_changed.part_sha256 = A.to_owned();
    unrelated_changed.sources[1].semantic_record_sha256 = D.to_owned();
    unrelated_changed.sources.push(source(3, C));
    assert_eq!(
        CitationNode::projection_sha256(&unrelated_changed, &ids, &display, limits())
            .expect("unrelated projection"),
        baseline
    );

    let mut selected_changed = base.clone();
    selected_changed.sources[0].semantic_record_sha256 = D.to_owned();
    assert_ne!(
        CitationNode::projection_sha256(&selected_changed, &ids, &display, limits())
            .expect("selected projection"),
        baseline
    );
    assert_ne!(
        CitationNode::projection_sha256(
            &base,
            &[id("source-1"), id("source-2")],
            &display,
            limits(),
        )
        .expect("ordered one"),
        CitationNode::projection_sha256(
            &base,
            &[id("source-2"), id("source-1")],
            &display,
            limits(),
        )
        .expect("ordered two")
    );
}

#[test]
fn missing_catalog_missing_source_and_duplicate_source_fail_closed() {
    let mut missing_catalog = draft();
    missing_catalog.bibliography = None;
    let missing_catalog =
        CitationDocumentState::from_draft(missing_catalog, limits()).expect("state");
    let candidate = citation(&catalog(), 1, vec![id("source-1")]);
    let request_draft = CitationRequestDraft {
        schema_version: CITATION_SCHEMA_VERSION.to_owned(),
        request_id: id("request-1"),
        expected_source_state_sha256: missing_catalog.canonical_sha256(limits()).expect("digest"),
        expected_document_flow_sha256: FLOW_A.to_owned(),
        target_document_flow_sha256: FLOW_B.to_owned(),
        operation: CitationOperation::CitationInsert {
            insertion_index: 0,
            citation: Box::new(candidate),
        },
    };
    assert_eq!(
        CitationRequest::from_draft(request_draft, &missing_catalog, FLOW_A, limits())
            .expect_err("catalog"),
        CitationError::InvalidCatalog
    );

    for source_ids in [
        vec![id("source-99")],
        vec![id("source-1"), id("source-1")],
        Vec::new(),
    ] {
        assert_eq!(
            CitationNode::projection_sha256(&catalog(), &source_ids, &options(), limits())
                .expect_err("source reference"),
            CitationError::SourceMissing
        );
    }
}

#[test]
fn stale_or_inconsistent_new_cache_is_rejected() {
    let source = state();
    let mut stale = citation(
        source.bibliography().expect("catalog"),
        1,
        vec![id("source-1")],
    );
    stale.cache.source_projection_sha256 = D.to_owned();
    stale.cache.status = CitationCacheStatus::Stale;
    let operation = CitationOperation::CitationInsert {
        insertion_index: 0,
        citation: Box::new(stale),
    };
    let request_draft = CitationRequestDraft {
        schema_version: CITATION_SCHEMA_VERSION.to_owned(),
        request_id: id("request-1"),
        expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
        expected_document_flow_sha256: FLOW_A.to_owned(),
        target_document_flow_sha256: FLOW_B.to_owned(),
        operation,
    };
    assert_eq!(
        CitationRequest::from_draft(request_draft, &source, FLOW_A, limits())
            .expect_err("stale insert"),
        CitationError::InvalidCitation
    );

    let mut inconsistent = citation(
        source.bibliography().expect("catalog"),
        1,
        vec![id("source-1")],
    );
    inconsistent.cache.source_projection_sha256 = D.to_owned();
    assert_eq!(
        CitationDocumentState::from_draft(
            CitationDocumentStateDraft {
                citations: vec![inconsistent],
                ..draft()
            },
            limits(),
        )
        .expect_err("inconsistent"),
        CitationError::InvalidCitation
    );
}

#[test]
fn native_identity_and_field_name_collisions_are_rejected() {
    let base = state();
    let mut control_collision = citation(
        base.bibliography().expect("catalog"),
        1,
        vec![id("source-1")],
    );
    control_collision.begin_control_id = 50;
    control_collision.native_pair.end_begin_control_id_ref = 50;
    let request = CitationRequestDraft {
        schema_version: CITATION_SCHEMA_VERSION.to_owned(),
        request_id: id("request-1"),
        expected_source_state_sha256: base.canonical_sha256(limits()).expect("digest"),
        expected_document_flow_sha256: FLOW_A.to_owned(),
        target_document_flow_sha256: FLOW_B.to_owned(),
        operation: CitationOperation::CitationInsert {
            insertion_index: 0,
            citation: Box::new(control_collision),
        },
    };
    assert_eq!(
        CitationRequest::from_draft(request, &base, FLOW_A, limits()).expect_err("control"),
        CitationError::InvalidIdentity
    );

    let mut name_collision = citation(
        base.bibliography().expect("catalog"),
        1,
        vec![id("source-1")],
    );
    name_collision.native_pair.field_name_sha256 = Some(D.to_owned());
    let request = CitationRequestDraft {
        schema_version: CITATION_SCHEMA_VERSION.to_owned(),
        request_id: id("request-2"),
        expected_source_state_sha256: base.canonical_sha256(limits()).expect("digest"),
        expected_document_flow_sha256: FLOW_A.to_owned(),
        target_document_flow_sha256: FLOW_B.to_owned(),
        operation: CitationOperation::CitationInsert {
            insertion_index: 0,
            citation: Box::new(name_collision),
        },
    };
    assert_eq!(
        CitationRequest::from_draft(request, &base, FLOW_A, limits()).expect_err("name"),
        CitationError::FieldNameConflict
    );
}

#[test]
fn catalog_source_identity_and_provider_key_duplicates_fail_closed() {
    let mut duplicate_id = draft();
    duplicate_id.bibliography.as_mut().expect("catalog").sources[1].logical_source_id =
        id("source-1");
    assert_eq!(
        CitationDocumentState::from_draft(duplicate_id, limits()).expect_err("source id"),
        CitationError::InvalidCatalog
    );

    let mut duplicate_key = draft();
    duplicate_key
        .bibliography
        .as_mut()
        .expect("catalog")
        .sources[1]
        .provider_record_key_sha256 = A.to_owned();
    assert_eq!(
        CitationDocumentState::from_draft(duplicate_key, limits()).expect_err("provider key"),
        CitationError::InvalidCatalog
    );

    let mut invalid_locale = draft();
    invalid_locale
        .bibliography
        .as_mut()
        .expect("catalog")
        .locale = "ko_KR".to_owned();
    assert_eq!(
        CitationDocumentState::from_draft(invalid_locale, limits()).expect_err("locale"),
        CitationError::InvalidCatalog
    );
}

#[test]
fn document_and_section_protection_fail_without_partial_state() {
    for lock_document in [false, true] {
        let mut draft = draft();
        draft.document_locked = lock_document;
        draft.sections[0].locked = !lock_document;
        let source = CitationDocumentState::from_draft(draft, limits()).expect("locked state");
        let candidate = citation(
            source.bibliography().expect("catalog"),
            1,
            vec![id("source-1")],
        );
        let request = CitationRequestDraft {
            schema_version: CITATION_SCHEMA_VERSION.to_owned(),
            request_id: id("request-1"),
            expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
            expected_document_flow_sha256: FLOW_A.to_owned(),
            target_document_flow_sha256: FLOW_B.to_owned(),
            operation: CitationOperation::CitationInsert {
                insertion_index: 0,
                citation: Box::new(candidate),
            },
        };
        assert_eq!(
            CitationRequest::from_draft(request, &source, FLOW_A, limits()).expect_err("protected"),
            CitationError::Protected
        );
        assert!(source.citations().is_empty());
    }
}

#[test]
fn request_plan_and_build_recheck_exact_state_and_flow() {
    let source = state();
    let operation = CitationOperation::CitationInsert {
        insertion_index: 0,
        citation: Box::new(citation(
            source.bibliography().expect("catalog"),
            1,
            vec![id("source-1")],
        )),
    };
    let draft = CitationRequestDraft {
        schema_version: CITATION_SCHEMA_VERSION.to_owned(),
        request_id: id("request-1"),
        expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
        expected_document_flow_sha256: FLOW_A.to_owned(),
        target_document_flow_sha256: FLOW_B.to_owned(),
        operation,
    };
    assert_eq!(
        CitationRequest::from_draft(draft.clone(), &source, FLOW_B, limits())
            .expect_err("request flow"),
        CitationError::DocumentFlowDrift
    );
    let request = CitationRequest::from_draft(draft, &source, FLOW_A, limits()).expect("request");
    assert_eq!(
        CitationBuilder::plan(&source, &request, FLOW_B, limits()).expect_err("plan flow"),
        CitationError::DocumentFlowDrift
    );
    let plan = CitationBuilder::plan(&source, &request, FLOW_A, limits()).expect("plan");
    assert_eq!(
        CitationBuilder::build(&plan, &source, FLOW_B, limits()).expect_err("build flow"),
        CitationError::DocumentFlowDrift
    );
    let changed = execute(
        &source,
        CitationOperation::CitationInsert {
            insertion_index: 0,
            citation: Box::new(citation(
                source.bibliography().expect("catalog"),
                2,
                vec![id("source-2")],
            )),
        },
    );
    assert_eq!(
        CitationBuilder::build(&plan, &changed, FLOW_A, limits()).expect_err("source drift"),
        CitationError::SourceStateDrift
    );
}

#[test]
fn strict_json_and_finite_input_output_limits_fail_closed() {
    let source = state();
    let duplicate =
        br#"{"schema_version":"hwpx-agent.citation/v1","schema_version":"hwpx-agent.citation/v1"}"#;
    assert_eq!(
        CitationRequest::from_json(duplicate, &source, FLOW_A, limits()).expect_err("duplicate"),
        CitationError::InvalidJson
    );
    let value = serde_json::to_value(CitationRequestDraft {
        schema_version: CITATION_SCHEMA_VERSION.to_owned(),
        request_id: id("request-1"),
        expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
        expected_document_flow_sha256: FLOW_A.to_owned(),
        target_document_flow_sha256: FLOW_B.to_owned(),
        operation: CitationOperation::CitationInsert {
            insertion_index: 0,
            citation: Box::new(citation(
                source.bibliography().expect("catalog"),
                1,
                vec![id("source-1")],
            )),
        },
    })
    .expect("json");
    let mut object = value.as_object().expect("object").clone();
    object.insert("unknown".to_owned(), serde_json::Value::Bool(true));
    let bytes = serde_json::to_vec(&object).expect("bytes");
    assert_eq!(
        CitationRequest::from_json(&bytes, &source, FLOW_A, limits()).expect_err("unknown"),
        CitationError::InvalidJson
    );

    let invalid = CitationLimitConfig {
        input_bytes: 2,
        output_bytes: 1,
        ..CitationLimitConfig::default()
    };
    assert_eq!(
        CitationLimits::new(invalid).expect_err("limit"),
        CitationError::InvalidLimit
    );
    let tiny = CitationLimits::new(CitationLimitConfig {
        input_bytes: 1,
        output_bytes: 1,
        ..CitationLimitConfig::default()
    })
    .expect("tiny");
    assert_eq!(
        CitationRequest::from_json(b"{}", &source, FLOW_A, tiny).expect_err("input"),
        CitationError::InputLimit
    );
    assert_eq!(
        source.canonical_json(tiny).expect_err("output"),
        CitationError::OutputLimit
    );
}

#[test]
fn insertion_preserves_catalog_and_all_unrelated_state_and_debug_is_redacted() {
    let source = state();
    let target = execute(
        &source,
        CitationOperation::CitationInsert {
            insertion_index: 0,
            citation: Box::new(citation(
                source.bibliography().expect("catalog"),
                1,
                vec![id("source-1")],
            )),
        },
    );
    let mut source_draft = CitationDocumentStateDraft::from(source.clone());
    let mut target_draft = CitationDocumentStateDraft::from(target.clone());
    source_draft.citations.clear();
    target_draft.citations.clear();
    assert_eq!(source_draft, target_draft);

    let debug = format!("{source:?} {:?} {:?}", target.citations()[0], options());
    for secret in ["section-1", "source-1", A, B, C, D] {
        assert!(!debug.contains(secret));
    }
    for error in [
        CitationError::InvalidCatalog,
        CitationError::SourceMissing,
        CitationError::PlanTampered,
    ] {
        assert!(error.code().starts_with("citation_"));
        assert!(!error.code().contains("source-1"));
    }
}

#[test]
fn canonical_state_is_deterministic_and_native_boundary_is_explicit() {
    let source = state();
    let bytes = source.canonical_json(limits()).expect("json");
    let decoded: CitationDocumentState = serde_json::from_slice(&bytes).expect("decode");
    assert_eq!(decoded, source);
    assert_eq!(
        decoded.canonical_sha256(limits()).expect("digest"),
        source.canonical_sha256(limits()).expect("digest")
    );
    let catalog = source.bibliography().expect("catalog");
    assert_eq!(
        catalog.format_binding,
        BibliographyFormatBinding::UnverifiedOpaquePart
    );
    let citation = citation(catalog, 1, vec![id("source-1")]);
    assert_eq!(
        citation.native_pair.semantic_binding,
        CitationSemanticBinding::UnverifiedFieldParameters
    );
}
