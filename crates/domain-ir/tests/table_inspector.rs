use std::error::Error;

use domain_ir::{
    CellCoordinate, DocumentGraph, DocumentGraphDraft, DocumentGraphLimits, DocumentId,
    DrawingNode, Flow, Inline, LogicalId, Node, NodeCommon, NodeKind, Note, ParagraphNode,
    Properties, RevisionId, Section, StructuralPath, StructuralRoot, StructuralStep,
    TABLE_INSPECTION_SCHEMA_VERSION, TableCell, TableCellSelector, TableInspectionError,
    TableInspectionExpectation, TableInspectionLimitConfig, TableInspectionLimits,
    TableInspectionSnapshot, TableNode, TableSelector,
};

type TestResult = Result<(), Box<dyn Error>>;

#[test]
fn merged_coordinates_resolve_to_one_canonical_master() -> TestResult {
    let snapshot = snapshot(&fixture_graph(false, false)?, "rev-1")?;
    let root_id = id("table-root")?;

    let left_selector =
        snapshot.cell_selector_at(&root_id, CellCoordinate { row: 0, column: 0 })?;
    let covered_selector =
        snapshot.cell_selector_at(&root_id, CellCoordinate { row: 0, column: 1 })?;
    let left = snapshot.resolve_cell(&snapshot.expectation(), &left_selector)?;
    let covered = snapshot.resolve_cell(&snapshot.expectation(), &covered_selector)?;

    assert_eq!(left.master_cell_id().as_str(), "cell-merged");
    assert_eq!(covered.master_cell_id(), left.master_cell_id());
    assert_eq!(
        covered.master_coordinate(),
        CellCoordinate { row: 0, column: 0 }
    );
    assert_eq!(
        covered.requested_coordinate(),
        CellCoordinate { row: 0, column: 1 }
    );
    assert_eq!((covered.row_span(), covered.column_span()), (1, 2));
    assert_eq!(
        covered.master_cell_fingerprint_sha256(),
        left.master_cell_fingerprint_sha256()
    );
    Ok(())
}

#[test]
fn nested_tables_keep_parent_cell_paths_and_exact_id_selection() -> TestResult {
    let snapshot = snapshot(&fixture_graph(true, true)?, "rev-nested")?;
    assert_eq!(snapshot.table_count(), 3);
    assert_eq!(snapshot.master_cell_count(), 5);

    let root_selector = snapshot.table_selector_for(&id("table-root")?)?;
    let root = snapshot.resolve_table(&snapshot.expectation(), &root_selector)?;
    let nested_ids: Vec<&str> = root
        .direct_nested_table_ids()
        .iter()
        .map(LogicalId::as_str)
        .collect();
    assert_eq!(nested_ids, vec!["table-nested-a", "table-nested-b"]);

    for nested_id in ["table-nested-a", "table-nested-b"] {
        let selector = snapshot.table_selector_for(&id(nested_id)?)?;
        let steps = selector.structural_path().steps();
        assert!(matches!(
            steps,
            [
                StructuralStep::FlowChild {
                    expected_kind: NodeKind::Table,
                    ..
                },
                StructuralStep::TableCell { row: 0, column: 0 },
                StructuralStep::FlowChild {
                    expected_kind: NodeKind::Table,
                    ..
                }
            ]
        ));
        assert_eq!(
            snapshot
                .resolve_table(&snapshot.expectation(), &selector)?
                .table_id()
                .as_str(),
            nested_id
        );
    }
    Ok(())
}

#[test]
fn parent_cell_inspection_lists_only_direct_nested_tables() -> TestResult {
    let snapshot = snapshot(&fixture_graph(true, true)?, "rev-cell")?;
    let selector = snapshot.cell_selector_for(&id("table-root")?, &id("cell-merged")?)?;
    let cell = snapshot.resolve_cell(&snapshot.expectation(), &selector)?;
    let nested_ids: Vec<&str> = cell
        .direct_nested_table_ids()
        .iter()
        .map(LogicalId::as_str)
        .collect();
    assert_eq!(nested_ids, vec!["table-nested-a", "table-nested-b"]);

    let nested_selector =
        snapshot.cell_selector_for(&id("table-nested-a")?, &id("cell-nested-a")?)?;
    assert!(
        snapshot
            .resolve_cell(&snapshot.expectation(), &nested_selector)?
            .direct_nested_table_ids()
            .is_empty()
    );
    Ok(())
}

#[test]
fn drawing_nested_and_note_root_tables_keep_typed_paths() -> TestResult {
    let drawing = Node::Drawing(DrawingNode {
        common: NodeCommon::new(id("drawing-container")?),
        resource_id: None,
        children: Flow {
            children: vec![single_cell_table(
                "table-drawing",
                "cell-drawing",
                Flow::default(),
            )?],
        },
        properties: Properties::new(),
    });
    let graph = graph_with_merged_body(Flow {
        children: vec![drawing],
    })?;
    let mut draft = graph.into_draft();
    draft.notes.push(Note {
        note_id: id("note-root")?,
        body: Flow {
            children: vec![single_cell_table(
                "table-note",
                "cell-note",
                Flow::default(),
            )?],
        },
        properties: Properties::new(),
    });
    let graph = DocumentGraph::from_draft(draft, DocumentGraphLimits::default())?;
    let snapshot = snapshot(&graph, "rev-drawing-note")?;

    let drawing_selector = snapshot.table_selector_for(&id("table-drawing")?)?;
    assert!(matches!(
        drawing_selector.structural_path().steps(),
        [
            StructuralStep::FlowChild {
                expected_kind: NodeKind::Table,
                ..
            },
            StructuralStep::TableCell { row: 0, column: 0 },
            StructuralStep::FlowChild {
                expected_kind: NodeKind::Drawing,
                ..
            },
            StructuralStep::FlowChild {
                expected_kind: NodeKind::Table,
                ..
            }
        ]
    ));
    let parent = snapshot.cell_selector_for(&id("table-root")?, &id("cell-merged")?)?;
    assert_eq!(
        snapshot
            .resolve_cell(&snapshot.expectation(), &parent)?
            .direct_nested_table_ids()[0]
            .as_str(),
        "table-drawing"
    );

    let note_selector = snapshot.table_selector_for(&id("table-note")?)?;
    assert_eq!(
        note_selector.structural_path().root(),
        StructuralRoot::Note { index: 0 }
    );
    Ok(())
}

#[test]
fn revision_graph_table_and_cell_anchor_drift_fail_closed() -> TestResult {
    let original = fixture_graph(true, false)?;
    let original_snapshot = snapshot(&original, "rev-1")?;
    let selector = original_snapshot
        .cell_selector_at(&id("table-root")?, CellCoordinate { row: 0, column: 1 })?;

    let wrong_revision = TableInspectionExpectation::new(RevisionId::parse("rev-2")?, [0; 32]);
    assert_eq!(
        original_snapshot
            .resolve_cell(&wrong_revision, &selector)
            .map_err(TableInspectionError::code),
        Err("table_inspection_stale")
    );

    let changed = fixture_graph_with_text("changed private cell body")?;
    let changed_snapshot = snapshot(&changed, "rev-2")?;
    assert_eq!(
        changed_snapshot
            .resolve_cell(&changed_snapshot.expectation(), &selector)
            .map_err(TableInspectionError::code),
        Err("table_inspection_stale")
    );

    let table = original_snapshot.table_selector_for(&id("table-root")?)?;
    let wrong_master = TableCellSelector::restore(
        table,
        CellCoordinate { row: 0, column: 1 },
        id("cell-bottom-left")?,
        selector.master_cell_fingerprint_sha256(),
    )?;
    assert_eq!(
        original_snapshot
            .resolve_cell(&original_snapshot.expectation(), &wrong_master)
            .map_err(TableInspectionError::code),
        Err("table_inspection_stale")
    );
    Ok(())
}

#[test]
fn table_selector_requires_exact_path_and_fingerprint() -> TestResult {
    let snapshot = snapshot(&fixture_graph(false, false)?, "rev-table")?;
    let selector = snapshot.table_selector_for(&id("table-root")?)?;
    let wrong_fingerprint = TableSelector::restore(
        id("table-root")?,
        selector.structural_path().clone(),
        [7; 32],
    )?;
    assert_eq!(
        snapshot
            .resolve_table(&snapshot.expectation(), &wrong_fingerprint)
            .map_err(TableInspectionError::code),
        Err("table_inspection_stale")
    );

    let paragraph_path = StructuralPath::new(
        0,
        vec![StructuralStep::FlowChild {
            index: 0,
            expected_kind: NodeKind::Paragraph,
        }],
    )?;
    assert_eq!(
        TableSelector::restore(id("table-root")?, paragraph_path, [1; 32])
            .map_err(TableInspectionError::code),
        Err("table_inspection_invalid_selector")
    );
    assert_eq!(
        TableSelector::restore(
            id("table-root")?,
            selector.structural_path().clone(),
            [0; 32]
        )
        .map_err(TableInspectionError::code),
        Err("table_inspection_invalid_selector")
    );
    let malformed_path = StructuralPath::new(
        0,
        vec![
            StructuralStep::FlowChild {
                index: 0,
                expected_kind: NodeKind::Paragraph,
            },
            StructuralStep::FlowChild {
                index: 0,
                expected_kind: NodeKind::Table,
            },
        ],
    )?;
    assert_eq!(
        TableSelector::restore(id("table-root")?, malformed_path, [1; 32])
            .map_err(TableInspectionError::code),
        Err("table_inspection_invalid_selector")
    );
    Ok(())
}

#[test]
fn unknown_table_cell_and_coordinate_are_distinct_failures() -> TestResult {
    let snapshot = snapshot(&fixture_graph(false, false)?, "rev-missing")?;
    assert_eq!(
        snapshot
            .table_selector_for(&id("missing-table")?)
            .map_err(TableInspectionError::code),
        Err("table_inspection_table_not_found")
    );
    assert_eq!(
        snapshot
            .cell_selector_for(&id("table-root")?, &id("missing-cell")?)
            .map_err(TableInspectionError::code),
        Err("table_inspection_cell_not_found")
    );
    assert_eq!(
        snapshot
            .cell_selector_at(&id("table-root")?, CellCoordinate { row: 2, column: 0 })
            .map_err(TableInspectionError::code),
        Err("table_inspection_coordinate_out_of_bounds")
    );
    Ok(())
}

#[test]
fn table_cell_depth_path_and_output_limits_are_finite() -> TestResult {
    let graph = fixture_graph(true, false)?;
    let cases = [
        TableInspectionLimitConfig {
            tables: 1,
            ..TableInspectionLimitConfig::default()
        },
        TableInspectionLimitConfig {
            master_cells: 3,
            ..TableInspectionLimitConfig::default()
        },
        TableInspectionLimitConfig {
            nested_depth: 1,
            ..TableInspectionLimitConfig::default()
        },
        TableInspectionLimitConfig {
            path_steps: 2,
            ..TableInspectionLimitConfig::default()
        },
        TableInspectionLimitConfig {
            serialized_bytes: 32,
            ..TableInspectionLimitConfig::default()
        },
    ];
    for config in cases {
        let limits = TableInspectionLimits::new(config)?;
        assert_eq!(
            TableInspectionSnapshot::build(&graph, RevisionId::parse("rev-limited")?, limits)
                .err()
                .map(TableInspectionError::code),
            Some("table_inspection_limit_exceeded")
        );
    }
    assert_eq!(
        TableInspectionLimits::new(TableInspectionLimitConfig {
            tables: 0,
            ..TableInspectionLimitConfig::default()
        })
        .map_err(TableInspectionError::code),
        Err("table_inspection_invalid_limit")
    );
    Ok(())
}

#[test]
fn canonical_snapshot_is_deterministic_metadata_only_and_versioned() -> TestResult {
    let graph = fixture_graph_with_text("highly private cell body")?;
    let first = snapshot(&graph, "rev-canonical")?;
    let second = snapshot(&graph, "rev-canonical")?;
    let first_json = first.canonical_json()?;

    assert_eq!(first_json, second.canonical_json()?);
    assert_eq!(first.canonical_sha256()?, second.canonical_sha256()?);
    assert!(!String::from_utf8(first_json.clone())?.contains("highly private cell body"));
    let value: serde_json::Value = serde_json::from_slice(&first_json)?;
    assert_eq!(value["schema_version"], TABLE_INSPECTION_SCHEMA_VERSION);
    assert_eq!(value["tables"].as_array().map(Vec::len), Some(1));
    Ok(())
}

#[test]
fn debug_surfaces_do_not_disclose_logical_ids_or_cell_content() -> TestResult {
    let graph = fixture_graph_with_text("do not print this")?;
    let snapshot = snapshot(&graph, "rev-debug")?;
    let selector = snapshot.cell_selector_for(&id("table-root")?, &id("cell-merged")?)?;
    let cell = snapshot.resolve_cell(&snapshot.expectation(), &selector)?;
    let output = format!("{snapshot:?} {selector:?} {cell:?}");
    assert!(!output.contains("table-root"));
    assert!(!output.contains("cell-merged"));
    assert!(!output.contains("do not print this"));
    Ok(())
}

#[test]
fn public_error_codes_are_stable() {
    let cases = [
        (
            TableInspectionError::InvalidLimit,
            "table_inspection_invalid_limit",
        ),
        (
            TableInspectionError::LimitExceeded,
            "table_inspection_limit_exceeded",
        ),
        (
            TableInspectionError::InvalidGraph,
            "table_inspection_invalid_graph",
        ),
        (
            TableInspectionError::SerializationFailed,
            "table_inspection_serialization_failed",
        ),
        (
            TableInspectionError::AllocationFailed,
            "table_inspection_allocation_failed",
        ),
        (
            TableInspectionError::InvalidSelector,
            "table_inspection_invalid_selector",
        ),
        (TableInspectionError::Stale, "table_inspection_stale"),
        (
            TableInspectionError::TableNotFound,
            "table_inspection_table_not_found",
        ),
        (
            TableInspectionError::CellNotFound,
            "table_inspection_cell_not_found",
        ),
        (
            TableInspectionError::CoordinateOutOfBounds,
            "table_inspection_coordinate_out_of_bounds",
        ),
    ];
    for (error, expected) in cases {
        assert_eq!(error.code(), expected);
    }
}

fn snapshot(
    graph: &DocumentGraph,
    revision: &str,
) -> Result<TableInspectionSnapshot, Box<dyn Error>> {
    Ok(TableInspectionSnapshot::build(
        graph,
        RevisionId::parse(revision)?,
        TableInspectionLimits::default(),
    )?)
}

fn fixture_graph(
    include_nested_a: bool,
    include_nested_b: bool,
) -> Result<DocumentGraph, Box<dyn Error>> {
    let mut nested = Vec::new();
    if include_nested_a {
        nested.push(single_cell_table(
            "table-nested-a",
            "cell-nested-a",
            Flow::default(),
        )?);
    }
    if include_nested_b {
        nested.push(single_cell_table(
            "table-nested-b",
            "cell-nested-b",
            Flow::default(),
        )?);
    }
    graph_with_merged_body(Flow { children: nested })
}

fn fixture_graph_with_text(text: &str) -> Result<DocumentGraph, Box<dyn Error>> {
    graph_with_merged_body(Flow {
        children: vec![Node::Paragraph(ParagraphNode {
            common: NodeCommon::new(id("paragraph-private")?),
            inlines: vec![Inline::Text { text: text.into() }],
            paragraph_properties: Properties::new(),
        })],
    })
}

fn graph_with_merged_body(merged_body: Flow) -> Result<DocumentGraph, Box<dyn Error>> {
    let root = Node::Table(TableNode {
        common: NodeCommon::new(id("table-root")?),
        rows: 2,
        columns: 2,
        cells: vec![
            TableCell {
                cell_id: id("cell-bottom-right")?,
                row: 1,
                column: 1,
                row_span: 1,
                column_span: 1,
                body: Flow::default(),
                properties: Properties::new(),
            },
            TableCell {
                cell_id: id("cell-merged")?,
                row: 0,
                column: 0,
                row_span: 1,
                column_span: 2,
                body: merged_body,
                properties: Properties::new(),
            },
            TableCell {
                cell_id: id("cell-bottom-left")?,
                row: 1,
                column: 0,
                row_span: 1,
                column_span: 1,
                body: Flow::default(),
                properties: Properties::new(),
            },
        ],
        properties: Properties::new(),
    });
    let draft = DocumentGraphDraft::new(
        DocumentId::parse("document-table-inspection")?,
        vec![Section {
            section_id: id("section-root")?,
            properties: Properties::new(),
            master_pages: Vec::new(),
            headers_footers: Vec::new(),
            body: Flow {
                children: vec![root],
            },
        }],
    );
    Ok(DocumentGraph::from_draft(
        draft,
        DocumentGraphLimits::default(),
    )?)
}

fn single_cell_table(table_id: &str, cell_id: &str, body: Flow) -> Result<Node, Box<dyn Error>> {
    Ok(Node::Table(TableNode {
        common: NodeCommon::new(id(table_id)?),
        rows: 1,
        columns: 1,
        cells: vec![TableCell {
            cell_id: id(cell_id)?,
            row: 0,
            column: 0,
            row_span: 1,
            column_span: 1,
            body,
            properties: Properties::new(),
        }],
        properties: Properties::new(),
    }))
}

fn id(value: &str) -> Result<LogicalId, domain_ir::DocumentGraphError> {
    LogicalId::parse(value)
}
