use std::collections::{BTreeMap, BTreeSet};
use std::error::Error;
use std::fmt::Write as _;

use domain_ir::{
    ArtifactRef, BreakKind, BreakNode, ChangeCategory, ChangeKind, ChartNode, DocumentGraph,
    DocumentGraphDraft, DocumentGraphError, DocumentGraphLimits, DocumentId, DrawingNode,
    EmbeddedObjectNode, EmbeddedObjectType, EntityKind, EquationNode, EquationSource, FieldNode,
    Flow, FormControlNode, Inline, LogicalId, Node, NodeCommon, Note, OpaqueExtension,
    OpaquePreservation, ParagraphNode, Properties, PropertyValue, Reference, Resource,
    ResourceKind, ReviewEntry, RevisionId, Section, SemanticDiff, SemanticDiffError,
    SemanticDiffLimits, SemanticDiffSnapshot, SemanticSummaryKind, Style, TableCell, TableNode,
};

type TestResult = Result<(), Box<dyn Error>>;

#[test]
fn full_typed_graph_projects_all_eight_review_categories_without_losing_records() -> TestResult {
    let mut after_draft = base_draft(false)?;
    let mut before_draft = after_draft.clone();
    before_draft.sections[0].body.children.clear();
    before_draft.resources.clear();
    before_draft.styles.clear();
    before_draft.notes.clear();
    before_draft.references.clear();
    before_draft.review.clear();
    before_draft.opaque_preservation_bag.clear();
    after_draft.sections[0]
        .properties
        .insert("review-test", PropertyValue::Integer(1));
    let before = graph(before_draft)?;
    let after = graph(after_draft)?;
    let difference = diff(
        &before,
        &RevisionId::parse("before")?,
        &after,
        &RevisionId::parse("after")?,
        SemanticDiffLimits::default(),
    )?;
    let summary = domain_ir::SemanticDiffSummary::from_diff(
        &difference,
        &before,
        &after,
        domain_ir::SemanticSummaryLimits::default(),
    )?;
    assert_eq!(
        summary
            .categories()
            .iter()
            .map(domain_ir::SemanticSummaryCategory::kind)
            .collect::<Vec<_>>(),
        vec![
            SemanticSummaryKind::Paragraph,
            SemanticSummaryKind::Table,
            SemanticSummaryKind::Style,
            SemanticSummaryKind::Image,
            SemanticSummaryKind::Field,
            SemanticSummaryKind::Section,
            SemanticSummaryKind::Metadata,
            SemanticSummaryKind::Other,
        ]
    );
    assert_eq!(
        usize::try_from(summary.added() + summary.modified() + summary.removed())?,
        difference.changes().len()
    );
    assert_eq!(
        summary
            .categories()
            .iter()
            .map(domain_ir::SemanticSummaryCategory::count)
            .sum::<u32>(),
        summary.added() + summary.modified() + summary.removed()
    );
    Ok(())
}

#[test]
fn identical_graph_has_empty_deterministic_diff() -> TestResult {
    let graph = graph(base_draft(false)?)?;
    let revision = RevisionId::parse("revision-1")?;
    let digest = graph.canonical_sha256()?;
    let first = SemanticDiff::between(
        SemanticDiffSnapshot::new(&revision, digest, &graph)?,
        SemanticDiffSnapshot::new(&revision, digest, &graph)?,
        SemanticDiffLimits::default(),
    )?;
    let second = SemanticDiff::between(
        SemanticDiffSnapshot::new(&revision, digest, &graph)?,
        SemanticDiffSnapshot::new(&revision, digest, &graph)?,
        SemanticDiffLimits::default(),
    )?;
    assert!(first.is_empty());
    assert_eq!(first.canonical_json()?, second.canonical_json()?);
    Ok(())
}

#[test]
fn comprehensive_typed_changes_have_stable_golden_digest() -> TestResult {
    let before = graph(base_draft(false)?)?;
    let after = graph(comprehensive_mutation(base_draft(false)?)?)?;
    let before_revision = RevisionId::parse("revision-before")?;
    let after_revision = RevisionId::parse("revision-after")?;
    let diff = diff(
        &before,
        &before_revision,
        &after,
        &after_revision,
        SemanticDiffLimits::default(),
    )?;
    let categories = diff
        .changes()
        .iter()
        .map(domain_ir::SemanticChange::category)
        .collect::<BTreeSet<_>>();
    assert_eq!(
        categories,
        BTreeSet::from([
            ChangeCategory::Document,
            ChangeCategory::Node,
            ChangeCategory::Style,
            ChangeCategory::Resource,
            ChangeCategory::Table,
            ChangeCategory::Equation,
            ChangeCategory::Object,
            ChangeCategory::Reference,
            ChangeCategory::Opaque,
        ])
    );
    assert!(diff.changes().iter().any(|change| {
        change.entity_kind() == EntityKind::Node
            && change.change_kind() == ChangeKind::ModifiedAndMoved
    }));
    assert!(diff.changes().iter().any(|change| {
        change.entity_kind() == EntityKind::Style
            && change
                .before_reference_count()
                .is_some_and(|count| count > 0)
            && change
                .after_reference_count()
                .is_some_and(|count| count > 0)
    }));
    assert_eq!(
        hex(&diff.canonical_sha256()?),
        "b12f8a542b42286470f981daff8de67ed352c5715742eec1c2fce4d892749f7e"
    );
    Ok(())
}

#[test]
fn add_remove_and_move_are_not_guessed_as_renames_and_inverse_exactly() -> TestResult {
    let before = graph(base_draft(false)?)?;
    let mut after_draft = base_draft(false)?;
    let removed = after_draft.sections[0].body.children.remove(8);
    assert!(matches!(removed, Node::EmbeddedObject(_)));
    after_draft.sections[0]
        .body
        .children
        .insert(0, paragraph("node-added", "new private text")?);
    after_draft.sections[0].body.children.swap(2, 3);
    let after = graph(after_draft)?;
    let revision_a = RevisionId::parse("revision-a")?;
    let revision_b = RevisionId::parse("revision-b")?;
    let forward = diff(
        &before,
        &revision_a,
        &after,
        &revision_b,
        SemanticDiffLimits::default(),
    )?;
    let reverse = diff(
        &after,
        &revision_b,
        &before,
        &revision_a,
        SemanticDiffLimits::default(),
    )?;

    let forward_by_subject = by_subject(&forward);
    let reverse_by_subject = by_subject(&reverse);
    assert_eq!(forward_by_subject.len(), reverse_by_subject.len());
    for (key, kind) in forward_by_subject {
        let reverse_kind = reverse_by_subject
            .get(&key)
            .ok_or("missing inverse change")?;
        assert_eq!(*reverse_kind, inverse(kind));
    }
    assert!(
        forward
            .changes()
            .iter()
            .any(|change| change.change_kind() == ChangeKind::Added)
    );
    assert!(
        forward
            .changes()
            .iter()
            .any(|change| change.change_kind() == ChangeKind::Removed)
    );
    assert!(
        forward
            .changes()
            .iter()
            .any(|change| change.change_kind() == ChangeKind::Moved)
    );
    Ok(())
}

#[test]
fn insertion_shift_does_not_over_report_unchanged_siblings_as_moved() -> TestResult {
    let before = graph(base_draft(false)?)?;
    let mut after_draft = base_draft(false)?;
    after_draft.sections[0]
        .body
        .children
        .insert(0, paragraph("node-inserted", "inserted private text")?);
    let after = graph(after_draft)?;
    let revision_a = RevisionId::parse("revision-shift-a")?;
    let revision_b = RevisionId::parse("revision-shift-b")?;
    let diff = diff(
        &before,
        &revision_a,
        &after,
        &revision_b,
        SemanticDiffLimits::default(),
    )?;
    assert_eq!(diff.changes().len(), 1);
    assert_eq!(diff.changes()[0].entity_kind(), EntityKind::Node);
    assert_eq!(diff.changes()[0].change_kind(), ChangeKind::Added);
    Ok(())
}

#[test]
fn catalog_input_order_is_irrelevant_but_document_order_is_semantic() -> TestResult {
    let normal = graph(base_draft(false)?)?;
    let reversed_catalogs = graph(base_draft(true)?)?;
    assert_eq!(
        normal.canonical_sha256()?,
        reversed_catalogs.canonical_sha256()?
    );

    let revision_a = RevisionId::parse("revision-a")?;
    let revision_b = RevisionId::parse("revision-b")?;
    assert!(
        diff(
            &normal,
            &revision_a,
            &reversed_catalogs,
            &revision_b,
            SemanticDiffLimits::default(),
        )?
        .is_empty()
    );

    let mut reordered = base_draft(false)?;
    reordered.sections[0].body.children.swap(0, 1);
    let reordered = graph(reordered)?;
    let ordered_diff = diff(
        &normal,
        &revision_a,
        &reordered,
        &revision_b,
        SemanticDiffLimits::default(),
    )?;
    assert!(
        ordered_diff
            .changes()
            .iter()
            .any(|change| change.change_kind() == ChangeKind::Moved)
    );
    Ok(())
}

#[test]
fn document_and_snapshot_identity_fail_closed() -> TestResult {
    let first = graph(base_draft(false)?)?;
    let mut other_draft = base_draft(false)?;
    other_draft.document_id = DocumentId::parse("other-document")?;
    let other = graph(other_draft)?;
    let revision_a = RevisionId::parse("revision-a")?;
    let revision_b = RevisionId::parse("revision-b")?;
    assert_eq!(
        diff(
            &first,
            &revision_a,
            &other,
            &revision_b,
            SemanticDiffLimits::default()
        ),
        Err(SemanticDiffError::DocumentMismatch)
    );

    let digest = first.canonical_sha256()?;
    assert_eq!(
        SemanticDiff::between(
            SemanticDiffSnapshot::new(&revision_a, [9; 32], &first)?,
            SemanticDiffSnapshot::new(&revision_b, digest, &first)?,
            SemanticDiffLimits::default(),
        ),
        Err(SemanticDiffError::SnapshotDigestMismatch)
    );
    assert!(matches!(
        SemanticDiffSnapshot::new(&revision_a, [0; 32], &first),
        Err(SemanticDiffError::InvalidSnapshot)
    ));
    Ok(())
}

#[test]
fn one_revision_cannot_name_two_graphs() -> TestResult {
    let before = graph(base_draft(false)?)?;
    let after = graph(comprehensive_mutation(base_draft(false)?)?)?;
    let revision = RevisionId::parse("same-revision")?;
    assert_eq!(
        diff(
            &before,
            &revision,
            &after,
            &revision,
            SemanticDiffLimits::default()
        ),
        Err(SemanticDiffError::RevisionDigestConflict)
    );
    Ok(())
}

#[test]
fn entity_change_depth_and_serialized_limits_are_finite() -> TestResult {
    let before = graph(base_draft(false)?)?;
    let after = graph(comprehensive_mutation(base_draft(false)?)?)?;
    let revision_a = RevisionId::parse("revision-a")?;
    let revision_b = RevisionId::parse("revision-b")?;

    for limits in [
        SemanticDiffLimits {
            max_entities: 1,
            ..SemanticDiffLimits::default()
        },
        SemanticDiffLimits {
            max_changes: 1,
            ..SemanticDiffLimits::default()
        },
        SemanticDiffLimits {
            max_depth: 1,
            ..SemanticDiffLimits::default()
        },
        SemanticDiffLimits {
            max_serialized_bytes: 1,
            ..SemanticDiffLimits::default()
        },
    ] {
        assert_eq!(
            diff(&before, &revision_a, &after, &revision_b, limits),
            Err(SemanticDiffError::LimitExceeded)
        );
    }
    assert_eq!(
        diff(
            &before,
            &revision_a,
            &after,
            &revision_b,
            SemanticDiffLimits {
                max_entities: 0,
                ..SemanticDiffLimits::default()
            }
        ),
        Err(SemanticDiffError::InvalidLimit)
    );
    Ok(())
}

#[test]
fn opaque_and_unknown_property_changes_are_visible_without_raw_values() -> TestResult {
    let sentinel = "private-body-and-path-sentinel";
    let before = graph(base_draft(false)?)?;
    let mut after_draft = base_draft(false)?;
    after_draft
        .metadata
        .insert("unknown-private", PropertyValue::Text(sentinel.to_owned()));
    after_draft.opaque_preservation_bag[0].sha256 = [8; 32];
    let Node::Paragraph(paragraph) = &mut after_draft.sections[0].body.children[0] else {
        return Err("expected paragraph".into());
    };
    paragraph.inlines[0] = Inline::Text {
        text: sentinel.to_owned(),
    };
    let after = graph(after_draft)?;
    let revision_a = RevisionId::parse("revision-private-a")?;
    let revision_b = RevisionId::parse("revision-private-b")?;
    let diff = diff(
        &before,
        &revision_a,
        &after,
        &revision_b,
        SemanticDiffLimits::default(),
    )?;
    assert!(
        diff.changes()
            .iter()
            .any(|change| change.category() == ChangeCategory::Opaque)
    );
    assert!(
        diff.changes()
            .iter()
            .any(|change| change.category() == ChangeCategory::Document)
    );
    let json = String::from_utf8(diff.canonical_json()?)?;
    let debug = format!("{diff:?} {:?}", diff.changes());
    assert!(!json.contains(sentinel));
    assert!(!debug.contains(sentinel));
    assert!(!format!("{}", SemanticDiffError::SnapshotDigestMismatch).contains(sentinel));
    Ok(())
}

#[test]
fn nested_table_drawing_and_note_nodes_keep_distinct_typed_paths() -> TestResult {
    let before = graph(base_draft(false)?)?;
    let mut after_draft = base_draft(false)?;
    let Node::Table(table) = &mut after_draft.sections[0].body.children[1] else {
        return Err("expected table".into());
    };
    table.cells[0]
        .body
        .children
        .push(paragraph("node-cell-added", "nested table private text")?);
    let Node::Drawing(drawing) = &mut after_draft.sections[0].body.children[3] else {
        return Err("expected drawing".into());
    };
    drawing.children.children.push(paragraph(
        "node-drawing-added",
        "nested drawing private text",
    )?);
    after_draft.notes[0]
        .body
        .children
        .push(paragraph("node-note-added", "nested note private text")?);
    let after = graph(after_draft)?;
    let revision_a = RevisionId::parse("revision-nested-a")?;
    let revision_b = RevisionId::parse("revision-nested-b")?;
    let diff = diff(
        &before,
        &revision_a,
        &after,
        &revision_b,
        SemanticDiffLimits::default(),
    )?;
    let added = diff
        .changes()
        .iter()
        .filter(|change| {
            change.entity_kind() == EntityKind::Node && change.change_kind() == ChangeKind::Added
        })
        .collect::<Vec<_>>();
    assert_eq!(added.len(), 3);
    let paths = added
        .iter()
        .filter_map(|change| change.after_path())
        .map(|path| format!("{path:?}"))
        .collect::<BTreeSet<_>>();
    assert_eq!(paths.len(), 3);
    Ok(())
}

fn diff(
    before: &DocumentGraph,
    before_revision: &RevisionId,
    after: &DocumentGraph,
    after_revision: &RevisionId,
    limits: SemanticDiffLimits,
) -> Result<SemanticDiff, SemanticDiffError> {
    let before_digest = before
        .canonical_sha256()
        .map_err(|_| SemanticDiffError::SerializationFailed)?;
    let after_digest = after
        .canonical_sha256()
        .map_err(|_| SemanticDiffError::SerializationFailed)?;
    SemanticDiff::between(
        SemanticDiffSnapshot::new(before_revision, before_digest, before)?,
        SemanticDiffSnapshot::new(after_revision, after_digest, after)?,
        limits,
    )
}

fn by_subject(diff: &SemanticDiff) -> BTreeMap<(EntityKind, [u8; 32]), ChangeKind> {
    diff.changes()
        .iter()
        .map(|change| {
            (
                (change.entity_kind(), change.subject_ref_sha256()),
                change.change_kind(),
            )
        })
        .collect()
}

const fn inverse(kind: ChangeKind) -> ChangeKind {
    match kind {
        ChangeKind::Added => ChangeKind::Removed,
        ChangeKind::Removed => ChangeKind::Added,
        ChangeKind::Modified => ChangeKind::Modified,
        ChangeKind::Moved => ChangeKind::Moved,
        ChangeKind::ModifiedAndMoved => ChangeKind::ModifiedAndMoved,
    }
}

fn graph(draft: DocumentGraphDraft) -> Result<DocumentGraph, DocumentGraphError> {
    DocumentGraph::from_draft(draft, DocumentGraphLimits::default())
}

#[allow(clippy::too_many_lines)]
fn base_draft(reverse_catalogs: bool) -> Result<DocumentGraphDraft, DocumentGraphError> {
    let resources = vec![
        Resource {
            resource_id: id("resource-image")?,
            kind: ResourceKind::Image,
            artifact: Some(ArtifactRef {
                sha256: [1; 32],
                byte_length: 128,
                media_type: "image/png".to_owned(),
            }),
            metadata: Properties::new(),
        },
        Resource {
            resource_id: id("resource-chart")?,
            kind: ResourceKind::ChartData,
            artifact: Some(ArtifactRef {
                sha256: [2; 32],
                byte_length: 64,
                media_type: "application/json".to_owned(),
            }),
            metadata: Properties::new(),
        },
        Resource {
            resource_id: id("resource-ole")?,
            kind: ResourceKind::Ole,
            artifact: None,
            metadata: Properties::new(),
        },
    ];
    let styles = vec![
        Style {
            style_id: id("style-base")?,
            based_on: None,
            properties: Properties::new(),
        },
        Style {
            style_id: id("style-body")?,
            based_on: Some(id("style-base")?),
            properties: Properties::new(),
        },
    ];

    let mut paragraph_node = paragraph("node-paragraph", "synthetic paragraph")?;
    let Node::Paragraph(value) = &mut paragraph_node else {
        return Err(DocumentGraphError::InvalidValue);
    };
    value.common.style_refs = vec![id("style-body")?];
    value.common.resource_refs = vec![id("resource-image")?];
    value.inlines.push(Inline::FieldRef {
        reference_id: id("reference-main")?,
    });
    value.inlines.push(Inline::ControlRef {
        node_id: id("node-form")?,
    });
    let table = Node::Table(TableNode {
        common: common("node-table")?,
        rows: 1,
        columns: 1,
        cells: vec![TableCell {
            cell_id: id("cell-main")?,
            row: 0,
            column: 0,
            row_span: 1,
            column_span: 1,
            body: Flow {
                children: vec![paragraph("node-cell-paragraph", "cell text")?],
            },
            properties: Properties::new(),
        }],
        properties: Properties::new(),
    });
    let equation = Node::Equation(EquationNode {
        common: common("node-equation")?,
        source: EquationSource::Formula("x + y".to_owned()),
        display: true,
        properties: Properties::new(),
    });
    let drawing = Node::Drawing(DrawingNode {
        common: common_with_resource("node-drawing", "resource-image")?,
        resource_id: Some(id("resource-image")?),
        children: Flow {
            children: vec![Node::Break(BreakNode {
                common: common("node-drawing-break")?,
                break_kind: BreakKind::Column,
            })],
        },
        properties: Properties::new(),
    });
    let chart = Node::Chart(ChartNode {
        common: common_with_resource("node-chart", "resource-chart")?,
        data_resource_id: id("resource-chart")?,
        properties: Properties::new(),
    });
    let field = Node::Field(FieldNode {
        common: common("node-field")?,
        reference_id: id("reference-main")?,
        properties: Properties::new(),
    });
    let form = Node::FormControl(FormControlNode {
        common: common("node-form")?,
        control_kind: "button".to_owned(),
        properties: Properties::new(),
    });
    let page_break = Node::Break(BreakNode {
        common: common("node-break")?,
        break_kind: BreakKind::Page,
    });
    let embedded = Node::EmbeddedObject(EmbeddedObjectNode {
        common: common_with_resource("node-embedded", "resource-ole")?,
        object_type: EmbeddedObjectType::Ole,
        resource_id: id("resource-ole")?,
        properties: Properties::new(),
    });

    let section = Section {
        section_id: id("section-main")?,
        properties: Properties::new(),
        master_pages: Vec::new(),
        headers_footers: Vec::new(),
        body: Flow {
            children: vec![
                paragraph_node,
                table,
                equation,
                drawing,
                chart,
                field,
                form,
                page_break,
                embedded,
            ],
        },
    };
    let mut draft = DocumentGraphDraft::new(DocumentId::parse("document-main")?, vec![section]);
    draft.source_profile = Some(id("profile-current-2020")?);
    draft.resources = resources;
    draft.styles = styles;
    draft.notes = vec![Note {
        note_id: id("note-main")?,
        body: Flow {
            children: vec![paragraph("node-note-paragraph", "note text")?],
        },
        properties: Properties::new(),
    }];
    draft.references = vec![Reference {
        reference_id: id("reference-main")?,
        target_node_id: Some(id("node-paragraph")?),
        properties: Properties::new(),
    }];
    draft.review = vec![ReviewEntry {
        review_id: id("review-main")?,
        target_node_id: id("node-paragraph")?,
        properties: Properties::new(),
    }];
    draft.opaque_preservation_bag = vec![OpaqueExtension {
        handle: id("opaque-main")?,
        sha256: [3; 32],
        byte_length: 32,
        preservation: OpaquePreservation::PreserveExact,
    }];
    if reverse_catalogs {
        draft.resources.reverse();
        draft.styles.reverse();
        draft.notes.reverse();
        draft.references.reverse();
        draft.review.reverse();
        draft.opaque_preservation_bag.reverse();
    }
    Ok(draft)
}

fn comprehensive_mutation(
    mut draft: DocumentGraphDraft,
) -> Result<DocumentGraphDraft, DocumentGraphError> {
    draft
        .settings
        .insert("layout-mode", PropertyValue::Text("changed".to_owned()));
    draft.styles[1]
        .properties
        .insert("weight", PropertyValue::Integer(700));
    draft.resources[0].artifact = Some(ArtifactRef {
        sha256: [7; 32],
        byte_length: 129,
        media_type: "image/png".to_owned(),
    });
    draft.sections[0].body.children.swap(0, 1);
    let Node::Paragraph(paragraph) = &mut draft.sections[0].body.children[1] else {
        return Err(DocumentGraphError::InvalidValue);
    };
    paragraph.inlines[0] = Inline::Text {
        text: "changed private paragraph".to_owned(),
    };
    let Node::Table(table) = &mut draft.sections[0].body.children[0] else {
        return Err(DocumentGraphError::InvalidValue);
    };
    table
        .properties
        .insert("grid", PropertyValue::Text("changed".to_owned()));
    table.cells[0]
        .properties
        .insert("fill", PropertyValue::Boolean(true));
    let Node::Equation(equation) = &mut draft.sections[0].body.children[2] else {
        return Err(DocumentGraphError::InvalidValue);
    };
    equation.source = EquationSource::Formula("x - y".to_owned());
    let Node::Drawing(drawing) = &mut draft.sections[0].body.children[3] else {
        return Err(DocumentGraphError::InvalidValue);
    };
    drawing
        .properties
        .insert("geometry", PropertyValue::Decimal("10.5".to_owned()));
    draft.references[0].target_node_id = Some(id("node-equation")?);
    draft.opaque_preservation_bag[0].sha256 = [8; 32];
    Ok(draft)
}

fn paragraph(node_id: &str, text: &str) -> Result<Node, DocumentGraphError> {
    Ok(Node::Paragraph(ParagraphNode {
        common: common(node_id)?,
        inlines: vec![Inline::Text {
            text: text.to_owned(),
        }],
        paragraph_properties: Properties::new(),
    }))
}

fn common(value: &str) -> Result<NodeCommon, DocumentGraphError> {
    Ok(NodeCommon::new(id(value)?))
}

fn common_with_resource(value: &str, resource: &str) -> Result<NodeCommon, DocumentGraphError> {
    let mut value = common(value)?;
    value.resource_refs = vec![id(resource)?];
    Ok(value)
}

fn id(value: &str) -> Result<LogicalId, DocumentGraphError> {
    LogicalId::parse(value)
}

fn hex(bytes: &[u8]) -> String {
    let mut output = String::with_capacity(bytes.len() * 2);
    for byte in bytes {
        let _ = write!(&mut output, "{byte:02x}");
    }
    output
}
