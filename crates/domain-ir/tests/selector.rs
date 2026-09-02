use std::error::Error;

use domain_ir::{
    DocumentGraph, DocumentGraphDraft, DocumentGraphLimits, DocumentId, FieldNode, Flow, Inline,
    LogicalId, NamedSelectorKind, Node, NodeCommon, NodeKind, Note, ParagraphNode, Properties,
    PropertyValue, Reference, RevisionId, Section, Selector, SelectorError, SelectorExpectation,
    SelectorLimits, SelectorSnapshot, StructuralRoot, TableCell, TableNode, TextContextAnchor,
};

type TestResult = Result<(), Box<dyn Error>>;

#[test]
fn logical_id_and_note_nodes_resolve_exactly_once() -> TestResult {
    let graph = graph_from_draft(fixture_draft("alpha target omega", "other", false)?)?;
    let snapshot = build_snapshot(&graph, "rev-1", SelectorLimits::default())?;
    let expectation = snapshot.expectation();

    let target = snapshot.resolve_one(&expectation, &Selector::by_logical_id(id("p-slot")?))?;
    assert_eq!(target.node_id().as_str(), "p-slot");
    assert_eq!(target.node_kind(), NodeKind::Paragraph);

    let note = snapshot.resolve_one(&expectation, &Selector::by_logical_id(id("p-note")?))?;
    assert_eq!(
        note.structural_path().root(),
        StructuralRoot::Note { index: 0 }
    );
    assert_eq!(
        snapshot
            .resolve_one(&expectation, &Selector::by_logical_id(id("missing")?))
            .map_err(SelectorError::code),
        Err("selector_not_found")
    );
    Ok(())
}

#[test]
fn slot_field_and_bookmark_names_resolve_without_backend_ids() -> TestResult {
    let graph = graph_from_draft(fixture_draft("alpha target omega", "other", false)?)?;
    let snapshot = build_snapshot(&graph, "rev-1", SelectorLimits::default())?;
    let expectation = snapshot.expectation();

    let cases = [
        (NamedSelectorKind::Slot, "answer", "p-slot"),
        (NamedSelectorKind::Field, "student_name", "field-1"),
        (NamedSelectorKind::Bookmark, "document_title", "p-title"),
    ];
    for (kind, name, expected_id) in cases {
        let selector = Selector::by_name(kind, name)?;
        let target = snapshot.resolve_one(&expectation, &selector)?;
        assert_eq!(target.node_id().as_str(), expected_id);
    }
    Ok(())
}

#[test]
fn named_collisions_are_ambiguous_and_never_choose_the_first_node() -> TestResult {
    let graph = graph_from_draft(fixture_draft("alpha target omega", "other", true)?)?;
    let snapshot = build_snapshot(&graph, "rev-1", SelectorLimits::default())?;
    let selector = Selector::by_name(NamedSelectorKind::Slot, "answer")?;
    assert_eq!(
        snapshot
            .resolve_one(&snapshot.expectation(), &selector)
            .map_err(SelectorError::code),
        Err("selector_ambiguous")
    );
    Ok(())
}

#[test]
fn revision_and_graph_digest_mismatch_fail_before_lookup() -> TestResult {
    let graph = graph_from_draft(fixture_draft("alpha target omega", "other", false)?)?;
    let snapshot = build_snapshot(&graph, "rev-1", SelectorLimits::default())?;
    let selector = Selector::by_logical_id(id("p-slot")?);

    let wrong_revision = SelectorExpectation::new(RevisionId::parse("rev-2")?, [0; 32]);
    assert_eq!(
        snapshot
            .resolve_one(&wrong_revision, &selector)
            .map_err(SelectorError::code),
        Err("selector_stale")
    );
    let wrong_digest = SelectorExpectation::new(RevisionId::parse("rev-1")?, [0; 32]);
    assert_eq!(
        snapshot
            .resolve_one(&wrong_digest, &selector)
            .map_err(SelectorError::code),
        Err("selector_stale")
    );
    Ok(())
}

#[test]
fn structural_paths_require_both_shape_and_node_fingerprint() -> TestResult {
    let graph = graph_from_draft(fixture_draft("alpha target omega", "other", false)?)?;
    let snapshot = build_snapshot(&graph, "rev-1", SelectorLimits::default())?;
    let cell_id = id("p-cell")?;
    let path = snapshot.structural_path_for(&cell_id)?;
    let fingerprint = snapshot.fingerprint_for(&cell_id)?;
    let selector = Selector::by_structural_path(path.clone(), fingerprint);
    let target = snapshot.resolve_one(&snapshot.expectation(), &selector)?;
    assert_eq!(target.node_id(), &cell_id);

    let wrong_fingerprint = Selector::by_structural_path(path.clone(), [7; 32]);
    assert_eq!(
        snapshot
            .resolve_one(&snapshot.expectation(), &wrong_fingerprint)
            .map_err(SelectorError::code),
        Err("selector_stale")
    );

    let mut shifted = fixture_draft("alpha target omega", "other", false)?;
    shifted.sections[0].body.children.insert(
        0,
        paragraph("p-inserted", vec![Inline::Text { text: "new".into() }])?,
    );
    let shifted_graph = graph_from_draft(shifted)?;
    let shifted_snapshot = build_snapshot(&shifted_graph, "rev-2", SelectorLimits::default())?;
    assert_eq!(
        shifted_snapshot
            .resolve_one(&shifted_snapshot.expectation(), &selector)
            .map_err(SelectorError::code),
        Err("selector_stale")
    );
    Ok(())
}

#[test]
fn text_context_survives_offset_drift_but_rejects_context_drift() -> TestResult {
    let before = TextContextAnchor::from_text("alpha ")?;
    let after = TextContextAnchor::from_text(" omega")?;
    let selector = Selector::by_text_context("target", Some(before), Some(after))?;

    let graph = graph_from_draft(fixture_draft("alpha target omega", "other", false)?)?;
    let snapshot = build_snapshot(&graph, "rev-1", SelectorLimits::default())?;
    let target = snapshot.resolve_one(&snapshot.expectation(), &selector)?;
    let range = target.text_range().ok_or("missing text range")?;
    assert_eq!((range.start_scalar(), range.end_scalar()), (6, 12));

    let shifted = graph_from_draft(fixture_draft("prefix alpha target omega", "other", false)?)?;
    let shifted_snapshot = build_snapshot(&shifted, "rev-2", SelectorLimits::default())?;
    let shifted_target =
        shifted_snapshot.resolve_one(&shifted_snapshot.expectation(), &selector)?;
    assert_eq!(
        shifted_target
            .text_range()
            .ok_or("missing shifted range")?
            .start_scalar(),
        13
    );

    let changed = graph_from_draft(fixture_draft("alpha changed target omega", "other", false)?)?;
    let changed_snapshot = build_snapshot(&changed, "rev-3", SelectorLimits::default())?;
    assert_eq!(
        changed_snapshot
            .resolve_one(&changed_snapshot.expectation(), &selector)
            .map_err(SelectorError::code),
        Err("selector_stale")
    );

    let missing = Selector::by_text_context(
        "absent",
        Some(TextContextAnchor::from_text("alpha ")?),
        None,
    )?;
    assert_eq!(
        snapshot
            .resolve_one(&snapshot.expectation(), &missing)
            .map_err(SelectorError::code),
        Err("selector_not_found")
    );
    Ok(())
}

#[test]
fn repeated_text_and_candidate_limits_fail_closed() -> TestResult {
    let graph = graph_from_draft(fixture_draft(
        "alpha target omega",
        "alpha target omega",
        false,
    )?)?;
    let selector = Selector::by_text_context(
        "target",
        Some(TextContextAnchor::from_text("alpha ")?),
        Some(TextContextAnchor::from_text(" omega")?),
    )?;
    let snapshot = build_snapshot(&graph, "rev-1", SelectorLimits::default())?;
    assert_eq!(
        snapshot
            .resolve_one(&snapshot.expectation(), &selector)
            .map_err(SelectorError::code),
        Err("selector_ambiguous")
    );

    let limited = SelectorLimits {
        max_candidates: 1,
        ..SelectorLimits::default()
    };
    let limited_snapshot = build_snapshot(&graph, "rev-1", limited)?;
    assert_eq!(
        limited_snapshot
            .resolve_one(&limited_snapshot.expectation(), &selector)
            .map_err(SelectorError::code),
        Err("selector_limit_exceeded")
    );
    Ok(())
}

#[test]
fn normalization_limits_and_reserved_metadata_are_validated() -> TestResult {
    let graph = graph_from_draft(fixture_draft("go Cafe\u{301} now", "other", false)?)?;
    let snapshot = build_snapshot(&graph, "rev-1", SelectorLimits::default())?;
    let selector = Selector::by_text_context(
        "Café",
        Some(TextContextAnchor::from_text("go ")?),
        Some(TextContextAnchor::from_text(" now")?),
    )?;
    assert_eq!(
        snapshot
            .resolve_one(&snapshot.expectation(), &selector)?
            .node_id()
            .as_str(),
        "p-slot"
    );

    let invalid_limits = SelectorLimits {
        max_path_steps: 0,
        ..SelectorLimits::default()
    };
    assert_eq!(
        snapshot_with_result(&graph, "rev-1", invalid_limits)
            .err()
            .map(SelectorError::code),
        Some("selector_invalid_limit")
    );
    let node_limited = SelectorLimits {
        max_indexed_nodes: 1,
        ..SelectorLimits::default()
    };
    assert_eq!(
        snapshot_with_result(&graph, "rev-1", node_limited)
            .err()
            .map(SelectorError::code),
        Some("selector_limit_exceeded")
    );

    let mut bad_metadata = fixture_draft("alpha target omega", "other", false)?;
    let Node::Paragraph(slot) = &mut bad_metadata.sections[0].body.children[1] else {
        return Err("expected slot paragraph".into());
    };
    slot.common
        .semantics
        .insert("slot_name", PropertyValue::Integer(7));
    let bad_graph = graph_from_draft(bad_metadata)?;
    assert_eq!(
        snapshot_with_result(&bad_graph, "rev-1", SelectorLimits::default())
            .err()
            .map(SelectorError::code),
        Some("selector_invalid_graph_metadata")
    );
    Ok(())
}

#[test]
fn public_debug_and_serialization_do_not_disclose_selector_values() -> TestResult {
    let secret = "secret-selector-value";
    let selector = Selector::by_name(NamedSelectorKind::Slot, secret)?;
    let anchor = TextContextAnchor::from_text(secret)?;
    let graph = graph_from_draft(fixture_draft("alpha target omega", "other", false)?)?;
    let snapshot = build_snapshot(&graph, secret, SelectorLimits::default())?;
    let target = snapshot.resolve_one(
        &snapshot.expectation(),
        &Selector::by_logical_id(id("p-slot")?),
    )?;

    for rendered in [
        format!("{selector:?}"),
        format!("{anchor:?}"),
        format!("{snapshot:?}"),
        format!("{:?}", snapshot.expectation()),
        format!("{target:?}"),
    ] {
        assert!(!rendered.contains(secret));
        assert!(!rendered.contains("p-slot"));
    }
    let first = serde_json::to_vec(&selector)?;
    let second = serde_json::to_vec(&selector)?;
    assert_eq!(first, second);
    Ok(())
}

fn build_snapshot(
    graph: &DocumentGraph,
    revision: &str,
    limits: SelectorLimits,
) -> Result<SelectorSnapshot, Box<dyn Error>> {
    Ok(snapshot_with_result(graph, revision, limits)?)
}

fn snapshot_with_result(
    graph: &DocumentGraph,
    revision: &str,
    limits: SelectorLimits,
) -> Result<SelectorSnapshot, SelectorError> {
    let revision = RevisionId::parse(revision).map_err(|_| SelectorError::InvalidSelector)?;
    SelectorSnapshot::build(graph, revision, limits)
}

fn graph_from_draft(draft: DocumentGraphDraft) -> Result<DocumentGraph, Box<dyn Error>> {
    Ok(DocumentGraph::from_draft(
        draft,
        DocumentGraphLimits::default(),
    )?)
}

#[allow(clippy::too_many_lines)]
fn fixture_draft(
    first_text: &str,
    second_text: &str,
    duplicate_slot: bool,
) -> Result<DocumentGraphDraft, Box<dyn Error>> {
    let mut bookmark_properties = Properties::new();
    bookmark_properties.insert(
        "bookmark_name",
        PropertyValue::Text("document_title".into()),
    );
    let mut field_reference_properties = Properties::new();
    field_reference_properties.insert("field_name", PropertyValue::Text("student_name".into()));

    let title = paragraph(
        "p-title",
        vec![
            Inline::BookmarkAnchor {
                reference_id: id("ref-bookmark")?,
            },
            Inline::Text {
                text: "Document title".into(),
            },
        ],
    )?;
    let mut slot = paragraph(
        "p-slot",
        vec![Inline::Text {
            text: first_text.into(),
        }],
    )?;
    let Node::Paragraph(slot_node) = &mut slot else {
        return Err("expected paragraph".into());
    };
    slot_node
        .common
        .semantics
        .insert("slot_name", PropertyValue::Text("answer".into()));

    let mut second = paragraph(
        "p-second",
        vec![Inline::Text {
            text: second_text.into(),
        }],
    )?;
    if duplicate_slot {
        let Node::Paragraph(second_node) = &mut second else {
            return Err("expected paragraph".into());
        };
        second_node
            .common
            .semantics
            .insert("slot_name", PropertyValue::Text("answer".into()));
    }

    let mut field_properties = Properties::new();
    field_properties.insert("field_name", PropertyValue::Text("student_name".into()));
    let field = Node::Field(FieldNode {
        common: NodeCommon::new(id("field-1")?),
        reference_id: id("ref-field")?,
        properties: field_properties,
    });
    let table = Node::Table(TableNode {
        common: NodeCommon::new(id("table-1")?),
        rows: 1,
        columns: 1,
        cells: vec![TableCell {
            cell_id: id("cell-1")?,
            row: 0,
            column: 0,
            row_span: 1,
            column_span: 1,
            body: Flow {
                children: vec![paragraph(
                    "p-cell",
                    vec![Inline::Text {
                        text: "cell body".into(),
                    }],
                )?],
            },
            properties: Properties::new(),
        }],
        properties: Properties::new(),
    });

    let mut draft = DocumentGraphDraft::new(
        DocumentId::parse("doc-selector")?,
        vec![Section {
            section_id: id("section-1")?,
            properties: Properties::new(),
            master_pages: Vec::new(),
            headers_footers: Vec::new(),
            body: Flow {
                children: vec![title, slot, second, field, table],
            },
        }],
    );
    draft.notes.push(Note {
        note_id: id("note-1")?,
        body: Flow {
            children: vec![paragraph(
                "p-note",
                vec![Inline::Text {
                    text: "note body".into(),
                }],
            )?],
        },
        properties: Properties::new(),
    });
    draft.references = vec![
        Reference {
            reference_id: id("ref-bookmark")?,
            target_node_id: Some(id("p-title")?),
            properties: bookmark_properties,
        },
        Reference {
            reference_id: id("ref-field")?,
            target_node_id: Some(id("field-1")?),
            properties: field_reference_properties,
        },
    ];
    Ok(draft)
}

fn paragraph(node_id: &str, inlines: Vec<Inline>) -> Result<Node, Box<dyn Error>> {
    Ok(Node::Paragraph(ParagraphNode {
        common: NodeCommon::new(id(node_id)?),
        inlines,
        paragraph_properties: Properties::new(),
    }))
}

fn id(value: &str) -> Result<LogicalId, domain_ir::DocumentGraphError> {
    LogicalId::parse(value)
}
