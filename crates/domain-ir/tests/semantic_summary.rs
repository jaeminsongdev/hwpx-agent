use std::error::Error;

use domain_ir::{
    BreakKind, BreakNode, DocumentGraph, DocumentGraphDraft, DocumentGraphLimits, DocumentId,
    DrawingNode, Flow, Inline, LogicalId, Node, NodeCommon, Note, ParagraphNode, Properties,
    Resource, ResourceKind, RevisionId, Section, SemanticDiff, SemanticDiffLimits,
    SemanticDiffSnapshot, SemanticDiffSummary, SemanticSummaryError, SemanticSummaryLimits,
};
use serde_json::json;

type TestResult = Result<(), Box<dyn Error>>;

fn paragraph(id: &str, text: &str) -> Result<Node, Box<dyn Error>> {
    Ok(Node::Paragraph(ParagraphNode {
        common: NodeCommon::new(LogicalId::parse(id)?),
        inlines: vec![Inline::Text {
            text: text.to_owned(),
        }],
        paragraph_properties: Properties::new(),
    }))
}

fn draft() -> Result<DocumentGraphDraft, Box<dyn Error>> {
    Ok(DocumentGraphDraft::new(
        DocumentId::parse("private-document")?,
        vec![Section {
            section_id: LogicalId::parse("private-section")?,
            properties: Properties::new(),
            master_pages: vec![],
            headers_footers: vec![],
            body: Flow {
                children: vec![paragraph("private-first", "PRIVATE BEFORE")?],
            },
        }],
    ))
}

fn graph(draft: DocumentGraphDraft) -> Result<DocumentGraph, Box<dyn Error>> {
    Ok(DocumentGraph::from_draft(
        draft,
        DocumentGraphLimits::default(),
    )?)
}

fn diff(before: &DocumentGraph, after: &DocumentGraph) -> Result<SemanticDiff, Box<dyn Error>> {
    Ok(SemanticDiff::between(
        SemanticDiffSnapshot::new(
            &RevisionId::parse("private-revision-before")?,
            before.canonical_sha256()?,
            before,
        )?,
        SemanticDiffSnapshot::new(
            &RevisionId::parse("private-revision-after")?,
            after.canonical_sha256()?,
            after,
        )?,
        SemanticDiffLimits::default(),
    )?)
}

#[test]
fn real_graph_changes_project_exact_private_free_widget_counts() -> TestResult {
    let before = graph(draft()?)?;
    let mut changed = draft()?;
    changed.sections[0].body.children[0] = paragraph("private-first", "PRIVATE AFTER")?;
    changed.sections[0]
        .body
        .children
        .push(paragraph("private-added", "PRIVATE INSERTED")?);
    let after = graph(changed)?;
    let difference = diff(&before, &after)?;
    let summary = SemanticDiffSummary::from_diff(
        &difference,
        &before,
        &after,
        SemanticSummaryLimits::default(),
    )?;
    assert_eq!(
        serde_json::to_value(&summary)?,
        json!({
            "added": 1, "modified": 1, "removed": 0,
            "categories": [{"kind": "paragraph", "count": 2}]
        })
    );
    assert_eq!(summary.source_diff_sha256(), difference.canonical_sha256()?);
    assert_eq!(summary.before_graph_sha256(), before.canonical_sha256()?);
    assert_eq!(summary.after_graph_sha256(), after.canonical_sha256()?);
    let serialized = serde_json::to_string(&summary)?;
    assert!(!serialized.contains("private"));
    assert!(!serialized.contains("PRIVATE"));
    assert!(!format!("{summary:?}").contains("PRIVATE"));
    Ok(())
}

#[test]
fn graph_mismatch_is_not_projected_into_an_unrelated_review() -> TestResult {
    let before = graph(draft()?)?;
    let mut changed = draft()?;
    changed.sections[0]
        .body
        .children
        .push(paragraph("private-added", "new")?);
    let after = graph(changed)?;
    let difference = diff(&before, &after)?;
    assert_eq!(
        SemanticDiffSummary::from_diff(
            &difference,
            &after,
            &before,
            SemanticSummaryLimits::default()
        ),
        Err(SemanticSummaryError::GraphMismatch)
    );
    Ok(())
}

#[test]
fn empty_diff_is_empty_and_change_limit_is_never_silently_clamped() -> TestResult {
    let before = graph(draft()?)?;
    let empty = SemanticDiffSummary::from_diff(
        &diff(&before, &before)?,
        &before,
        &before,
        SemanticSummaryLimits::default(),
    )?;
    assert_eq!(
        serde_json::to_value(&empty)?,
        json!({"added":0,"modified":0,"removed":0,"categories":[]})
    );
    let mut changed = draft()?;
    changed.sections[0]
        .body
        .children
        .push(paragraph("private-added", "new")?);
    changed.sections[0]
        .body
        .children
        .push(paragraph("private-added-two", "new")?);
    let after = graph(changed)?;
    let difference = diff(&before, &after)?;
    let limits = SemanticSummaryLimits {
        max_changes: 1,
        ..SemanticSummaryLimits::default()
    };
    assert_eq!(
        SemanticDiffSummary::from_diff(&difference, &before, &after, limits),
        Err(SemanticSummaryError::LimitExceeded)
    );
    Ok(())
}

#[test]
fn inverse_add_remove_and_moves_preserve_record_totals() -> TestResult {
    let mut initial = draft()?;
    initial.sections[0]
        .body
        .children
        .push(paragraph("second", "second")?);
    initial.sections[0]
        .body
        .children
        .push(paragraph("third", "third")?);
    let before = graph(initial.clone())?;
    initial.sections[0].body.children.swap(0, 2);
    initial.sections[0].body.children[2] = paragraph("private-first", "edited and moved")?;
    let after = graph(initial)?;
    let forward_diff = diff(&before, &after)?;
    assert!(
        forward_diff
            .changes()
            .iter()
            .any(|c| c.change_kind() == domain_ir::ChangeKind::ModifiedAndMoved)
    );
    let forward = SemanticDiffSummary::from_diff(
        &forward_diff,
        &before,
        &after,
        SemanticSummaryLimits::default(),
    )?;
    assert_eq!(
        usize::try_from(forward.modified())?,
        forward_diff.changes().len()
    );
    let reverse = SemanticDiffSummary::from_diff(
        &diff(&after, &before)?,
        &after,
        &before,
        SemanticSummaryLimits::default(),
    )?;
    assert_eq!(forward.modified(), reverse.modified());
    let mut added = after.clone().into_draft();
    added.sections[0]
        .body
        .children
        .push(paragraph("fourth", "fourth")?);
    let added = graph(added)?;
    let removed = SemanticDiffSummary::from_diff(
        &diff(&added, &after)?,
        &added,
        &after,
        SemanticSummaryLimits::default(),
    )?;
    assert_eq!(
        serde_json::to_value(&removed)?,
        json!({"added":0,"modified":0,"removed":1,"categories":[{"kind":"paragraph","count":1}]})
    );
    Ok(())
}

#[test]
fn node_type_changes_and_vector_drawings_are_not_guessed_as_paragraphs_or_images() -> TestResult {
    let before = graph(draft()?)?;
    let mut changed = draft()?;
    changed.sections[0].body.children[0] = Node::Drawing(DrawingNode {
        common: NodeCommon::new(LogicalId::parse("private-first")?),
        resource_id: None,
        children: Flow::default(),
        properties: Properties::new(),
    });
    let after = graph(changed)?;
    let summary = SemanticDiffSummary::from_diff(
        &diff(&before, &after)?,
        &before,
        &after,
        SemanticSummaryLimits::default(),
    )?;
    assert_eq!(
        serde_json::to_value(summary)?,
        json!({"added":1,"modified":1,"removed":0,"categories":[{"kind":"other","count":2}]})
    );
    Ok(())
}

#[test]
fn image_resource_kind_not_filename_or_drawing_presence_drives_classification() -> TestResult {
    let before = graph(draft()?)?;
    let mut changed = draft()?;
    changed.resources = vec![
        Resource {
            resource_id: LogicalId::parse("font-named-picture.png")?,
            kind: ResourceKind::Font,
            artifact: None,
            metadata: Properties::new(),
        },
        Resource {
            resource_id: LogicalId::parse("image-named-secret-font")?,
            kind: ResourceKind::Image,
            artifact: None,
            metadata: Properties::new(),
        },
    ];
    for (id, resource) in [
        ("font-drawing", "font-named-picture.png"),
        ("image-drawing", "image-named-secret-font"),
    ] {
        changed.sections[0]
            .body
            .children
            .push(Node::Drawing(DrawingNode {
                common: NodeCommon::new(LogicalId::parse(id)?),
                resource_id: Some(LogicalId::parse(resource)?),
                children: Flow::default(),
                properties: Properties::new(),
            }));
    }
    let after = graph(changed)?;
    let summary = SemanticDiffSummary::from_diff(
        &diff(&before, &after)?,
        &before,
        &after,
        SemanticSummaryLimits::default(),
    )?;
    assert_eq!(
        serde_json::to_value(summary)?,
        json!({"added":6,"modified":0,"removed":0,"categories":[{"kind":"image","count":3},{"kind":"other","count":3}]})
    );
    Ok(())
}

#[test]
fn note_paragraphs_and_section_breaks_use_their_actual_structure() -> TestResult {
    let before = graph(draft()?)?;
    let mut changed = draft()?;
    changed.notes.push(Note {
        note_id: LogicalId::parse("note")?,
        body: Flow {
            children: vec![paragraph("note-paragraph", "private note")?],
        },
        properties: Properties::new(),
    });
    changed.sections[0]
        .body
        .children
        .push(Node::Break(BreakNode {
            common: NodeCommon::new(LogicalId::parse("section-break")?),
            break_kind: BreakKind::Section,
        }));
    let after = graph(changed)?;
    let summary = SemanticDiffSummary::from_diff(
        &diff(&before, &after)?,
        &before,
        &after,
        SemanticSummaryLimits::default(),
    )?;
    assert_eq!(
        serde_json::to_value(summary)?,
        json!({"added":4,"modified":0,"removed":0,"categories":[{"kind":"paragraph","count":1},{"kind":"section","count":2},{"kind":"metadata","count":1}]})
    );
    Ok(())
}

#[test]
fn bounds_cover_index_depth_serialization_and_invalid_configurations() -> TestResult {
    let before = graph(draft()?)?;
    let mut changed = draft()?;
    changed.sections[0]
        .body
        .children
        .push(Node::Drawing(DrawingNode {
            common: NodeCommon::new(LogicalId::parse("drawing")?),
            resource_id: None,
            children: Flow {
                children: vec![paragraph("nested", "nested")?],
            },
            properties: Properties::new(),
        }));
    let after = graph(changed)?;
    let difference = diff(&before, &after)?;
    for limits in [
        SemanticSummaryLimits {
            max_index_entries: 1,
            ..SemanticSummaryLimits::default()
        },
        SemanticSummaryLimits {
            max_depth: 1,
            ..SemanticSummaryLimits::default()
        },
        SemanticSummaryLimits {
            max_serialized_bytes: 1,
            ..SemanticSummaryLimits::default()
        },
    ] {
        assert_eq!(
            SemanticDiffSummary::from_diff(&difference, &before, &after, limits),
            Err(SemanticSummaryError::LimitExceeded)
        );
    }
    for limits in [
        SemanticSummaryLimits {
            max_changes: 0,
            ..SemanticSummaryLimits::default()
        },
        SemanticSummaryLimits {
            max_changes: 100_001,
            ..SemanticSummaryLimits::default()
        },
        SemanticSummaryLimits {
            max_index_entries: usize::MAX,
            ..SemanticSummaryLimits::default()
        },
        SemanticSummaryLimits {
            max_depth: 129,
            ..SemanticSummaryLimits::default()
        },
        SemanticSummaryLimits {
            max_serialized_bytes: usize::MAX,
            ..SemanticSummaryLimits::default()
        },
    ] {
        assert_eq!(
            SemanticDiffSummary::from_diff(&difference, &before, &after, limits),
            Err(SemanticSummaryError::InvalidLimit)
        );
    }
    Ok(())
}

#[test]
fn repeat_projection_is_deterministic_and_sources_remain_immutable() -> TestResult {
    let before = graph(draft()?)?;
    let mut changed = draft()?;
    changed.sections[0]
        .body
        .children
        .push(paragraph("added", "private")?);
    let after = graph(changed)?;
    let before_bytes = before.canonical_json()?;
    let after_bytes = after.canonical_json()?;
    let difference = diff(&before, &after)?;
    let first = SemanticDiffSummary::from_diff(
        &difference,
        &before,
        &after,
        SemanticSummaryLimits::default(),
    )?;
    let second = SemanticDiffSummary::from_diff(
        &difference,
        &before,
        &after,
        SemanticSummaryLimits::default(),
    )?;
    assert_eq!(first, second);
    assert_eq!(serde_json::to_vec(&first)?, serde_json::to_vec(&second)?);
    assert_eq!(before.canonical_json()?, before_bytes);
    assert_eq!(after.canonical_json()?, after_bytes);
    Ok(())
}

#[test]
fn authenticated_projection_restore_is_exact_and_fail_closed() -> TestResult {
    use domain_ir::SemanticSummaryKind;

    let restored = SemanticDiffSummary::from_authenticated_projection(
        1,
        2,
        0,
        vec![
            (SemanticSummaryKind::Paragraph, 2),
            (SemanticSummaryKind::Table, 1),
        ],
        [1; 32],
        [2; 32],
        [3; 32],
        SemanticSummaryLimits::default(),
    )?;
    assert_eq!(restored.added(), 1);
    assert_eq!(restored.modified(), 2);
    assert_eq!(restored.source_diff_sha256(), [1; 32]);
    assert_eq!(
        SemanticDiffSummary::from_authenticated_projection(
            1,
            2,
            0,
            vec![
                (SemanticSummaryKind::Table, 1),
                (SemanticSummaryKind::Paragraph, 2)
            ],
            [1; 32],
            [2; 32],
            [3; 32],
            SemanticSummaryLimits::default(),
        ),
        Err(SemanticSummaryError::InvalidProjection)
    );
    assert_eq!(
        SemanticDiffSummary::from_authenticated_projection(
            1,
            2,
            0,
            vec![(SemanticSummaryKind::Paragraph, 2)],
            [1; 32],
            [2; 32],
            [3; 32],
            SemanticSummaryLimits::default(),
        ),
        Err(SemanticSummaryError::InvalidProjection)
    );
    Ok(())
}
