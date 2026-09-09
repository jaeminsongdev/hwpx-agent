use domain_ir::{
    CellCoordinate, FormulaAst, FormulaAstDraft, FormulaCache, FormulaCachePolicy, FormulaCell,
    FormulaCellDraft, FormulaDecimal, FormulaGridDimensions, FormulaGridEdit, FormulaLimits,
    FormulaNumberFormat, FormulaValue, LogicalId, TABLE_FORMULA_SCHEMA_VERSION,
    TABLE_RULING_SCHEMA_VERSION, TABLE_STRUCTURE_SCHEMA_VERSION, TableCellSpan, TableGrid,
    TableGridLimits, TableRulingAxis, TableRulingCellDraft, TableRulingCellProperties,
    TableRulingEdge, TableRulingFrame, TableRulingLimits, TableRulingPayloadBlock,
    TableRulingState, TableRulingStateDraft, TableStructureBuilder, TableStructureError,
    TableStructureLimits, TableStructureOperation, TableStructureRequest,
    TableStructureRequestDraft,
};

type TestResult = Result<(), Box<dyn std::error::Error>>;

fn id(value: &str) -> Result<LogicalId, Box<dyn std::error::Error>> {
    Ok(LogicalId::parse(value)?)
}

fn digest(character: char) -> String {
    std::iter::repeat_n(character, 64).collect()
}

fn hex(bytes: impl AsRef<[u8]>) -> String {
    use std::fmt::Write as _;

    bytes
        .as_ref()
        .iter()
        .fold(String::new(), |mut output, byte| {
            let _ = write!(output, "{byte:02x}");
            output
        })
}

fn grid(rows: u32, columns: u32) -> Result<TableGrid, Box<dyn std::error::Error>> {
    let mut cells = Vec::new();
    for row in 0..rows {
        for column in 0..columns {
            cells.push(TableCellSpan {
                master_cell_id: id(&format!("cell-{row}-{column}"))?,
                row,
                column,
                row_span: 1,
                column_span: 1,
            });
        }
    }
    Ok(TableGrid::new(
        rows,
        columns,
        cells,
        TableGridLimits::default(),
    )?)
}

fn properties() -> TableRulingCellProperties {
    TableRulingCellProperties {
        non_ruling_properties_sha256: digest('a'),
        background_sha256: Some(digest('b')),
        slash_diagonal_sha256: None,
        back_slash_diagonal_sha256: None,
    }
}

fn all_edges(rows: u32, columns: u32, line: char) -> Vec<TableRulingEdge> {
    let mut edges = Vec::new();
    for boundary in 0..=rows {
        for offset in 0..columns {
            edges.push(TableRulingEdge {
                axis: TableRulingAxis::Horizontal,
                boundary,
                offset,
                line_sha256: Some(digest(line)),
            });
        }
    }
    for boundary in 0..=columns {
        for offset in 0..rows {
            edges.push(TableRulingEdge {
                axis: TableRulingAxis::Vertical,
                boundary,
                offset,
                line_sha256: Some(digest(line)),
            });
        }
    }
    edges
}

fn formula_draft(
    owner: CellCoordinate,
    source: &str,
) -> Result<FormulaCellDraft, Box<dyn std::error::Error>> {
    let ast = FormulaAst::parse(source, FormulaLimits::default())?;
    Ok(FormulaCellDraft {
        schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
        owner,
        ast: FormulaAstDraft {
            schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
            expression: ast.expression().clone(),
        },
        cache: FormulaCache::Unverified {
            value: FormulaValue::Decimal {
                value: FormulaDecimal::new(7, 0),
            },
        },
        number_format: FormulaNumberFormat::General,
    })
}

fn formula_as_draft(formula: &FormulaCell) -> FormulaCellDraft {
    FormulaCellDraft {
        schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
        owner: formula.owner(),
        ast: FormulaAstDraft {
            schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
            expression: formula.ast().expression().clone(),
        },
        cache: formula.cache().clone(),
        number_format: formula.number_format(),
    }
}

fn source_state(
    grid: &TableGrid,
    row_boundaries: Vec<u32>,
    column_boundaries: Vec<u32>,
    formula: Option<(CellCoordinate, &str)>,
) -> Result<TableRulingState, Box<dyn std::error::Error>> {
    let mut cells = Vec::new();
    for (index, span) in grid.master_cells().iter().enumerate() {
        let coordinate = CellCoordinate {
            row: span.row,
            column: span.column,
        };
        cells.push(TableRulingCellDraft {
            master_cell_id: span.master_cell_id.clone(),
            coordinate,
            payload: vec![TableRulingPayloadBlock {
                block_id: id(&format!("payload-{index}"))?,
                payload_sha256: digest(if index % 2 == 0 { 'c' } else { 'd' }),
            }],
            properties: properties(),
            formula: formula
                .filter(|(owner, _)| *owner == coordinate)
                .map(|(owner, value)| formula_draft(owner, value))
                .transpose()?,
        });
    }
    let width = *column_boundaries.last().ok_or("missing column boundary")?;
    let height = *row_boundaries.last().ok_or("missing row boundary")?;
    Ok(TableRulingState::from_draft(
        TableRulingStateDraft {
            schema_version: TABLE_RULING_SCHEMA_VERSION.to_owned(),
            table_id: id("secret-table-id")?,
            frame: TableRulingFrame {
                left_hwpunit: 10,
                top_hwpunit: 20,
                width_hwpunit: width,
                height_hwpunit: height,
            },
            grid_sha256: hex(grid.canonical_sha256()?),
            table_properties_sha256: digest('e'),
            row_boundaries_hwpunit: row_boundaries,
            column_boundaries_hwpunit: column_boundaries,
            edges: all_edges(grid.rows(), grid.columns(), '1'),
            cells,
        },
        grid,
        FormulaLimits::default(),
        TableRulingLimits::default(),
    )?)
}

fn formula_edit(
    operation: TableStructureOperation,
    source: &TableGrid,
    index: u32,
    count: u32,
) -> FormulaGridEdit {
    let before = FormulaGridDimensions {
        rows: source.rows(),
        columns: source.columns(),
    };
    match operation {
        TableStructureOperation::InsertRows => FormulaGridEdit::InsertRows {
            before,
            index,
            count,
        },
        TableStructureOperation::InsertColumns => FormulaGridEdit::InsertColumns {
            before,
            index,
            count,
        },
        TableStructureOperation::DeleteRows => FormulaGridEdit::DeleteRows {
            before,
            index,
            count,
        },
        TableStructureOperation::DeleteColumns => FormulaGridEdit::DeleteColumns {
            before,
            index,
            count,
        },
    }
}

#[allow(clippy::too_many_arguments)]
fn target_draft(
    source_grid: &TableGrid,
    source_state: &TableRulingState,
    target_grid: &TableGrid,
    operation: TableStructureOperation,
    index: u32,
    count: u32,
    row_boundaries: Vec<u32>,
    column_boundaries: Vec<u32>,
) -> Result<TableRulingStateDraft, Box<dyn std::error::Error>> {
    let edit = formula_edit(operation, source_grid, index, count);
    let mut cells = Vec::new();
    for span in target_grid.master_cells() {
        let coordinate = CellCoordinate {
            row: span.row,
            column: span.column,
        };
        if let Some(source) = source_state.cell(&span.master_cell_id) {
            let formula = source
                .formula()
                .map(|formula| {
                    formula.apply_grid_edit(
                        edit,
                        FormulaCachePolicy::Update,
                        Some(formula.cache().clone()),
                        FormulaLimits::default(),
                    )
                })
                .transpose()?
                .as_ref()
                .map(formula_as_draft);
            cells.push(TableRulingCellDraft {
                master_cell_id: span.master_cell_id.clone(),
                coordinate,
                payload: source.payload().to_vec(),
                properties: source.properties().clone(),
                formula,
            });
        } else {
            cells.push(TableRulingCellDraft {
                master_cell_id: span.master_cell_id.clone(),
                coordinate,
                payload: Vec::new(),
                properties: properties(),
                formula: None,
            });
        }
    }
    Ok(TableRulingStateDraft {
        schema_version: TABLE_RULING_SCHEMA_VERSION.to_owned(),
        table_id: source_state.table_id().clone(),
        frame: TableRulingFrame {
            left_hwpunit: source_state.frame().left_hwpunit,
            top_hwpunit: source_state.frame().top_hwpunit,
            width_hwpunit: *column_boundaries.last().ok_or("missing column boundary")?,
            height_hwpunit: *row_boundaries.last().ok_or("missing row boundary")?,
        },
        grid_sha256: hex(target_grid.canonical_sha256()?),
        table_properties_sha256: source_state.table_properties_sha256().to_owned(),
        row_boundaries_hwpunit: row_boundaries,
        column_boundaries_hwpunit: column_boundaries,
        edges: all_edges(target_grid.rows(), target_grid.columns(), '1'),
        cells,
    })
}

fn request(
    source_grid: &TableGrid,
    source_state: &TableRulingState,
    operation: TableStructureOperation,
    index: u32,
    count: u32,
    new_master_cell_ids: Vec<LogicalId>,
    target_state: TableRulingStateDraft,
) -> Result<TableStructureRequest, TableStructureError> {
    TableStructureRequest::from_draft(
        TableStructureRequestDraft {
            schema_version: TABLE_STRUCTURE_SCHEMA_VERSION.to_owned(),
            operation,
            index,
            count,
            new_master_cell_ids,
            expected_source_state_sha256: hex(
                source_state.canonical_sha256(TableRulingLimits::default())?
            ),
            expected_source_grid_sha256: hex(source_grid.canonical_sha256()?),
            expected_document_flow_sha256: digest('2'),
            target_document_flow_sha256: digest('3'),
            target_state,
        },
        source_state,
        source_grid,
        &digest('2'),
        TableStructureLimits::default(),
    )
}

#[test]
fn insert_rows_preserves_complete_state_and_rebases_formula() -> TestResult {
    let source_grid = grid(2, 3)?;
    let source = source_state(
        &source_grid,
        vec![0, 40, 100],
        vec![0, 30, 70, 100],
        Some((CellCoordinate { row: 1, column: 2 }, "SUM(A2:B2)")),
    )?;
    let new_ids = vec![id("new-r0")?, id("new-r1")?, id("new-r2")?];
    let target_grid = source_grid
        .insert_rows(0, 1, new_ids.clone(), TableGridLimits::default())?
        .into_parts()
        .0;
    let target = target_draft(
        &source_grid,
        &source,
        &target_grid,
        TableStructureOperation::InsertRows,
        0,
        1,
        vec![0, 10, 50, 110],
        vec![0, 30, 70, 100],
    )?;
    let request = request(
        &source_grid,
        &source,
        TableStructureOperation::InsertRows,
        0,
        1,
        new_ids,
        target,
    )?;
    let plan = TableStructureBuilder::build(
        &request,
        &source,
        &source_grid,
        &digest('2'),
        TableStructureLimits::default(),
    )?;
    assert_eq!(plan.after_grid().rows(), 3);
    assert_eq!(plan.after_grid().columns(), 3);
    assert_eq!(plan.receipt().preserved_master_cell_count(), 6);
    assert_eq!(plan.receipt().inserted_master_cell_count(), 3);
    assert_eq!(plan.receipt().formula_rebased_count(), 1);
    assert_eq!(plan.receipt().formula_cache_updated_count(), 1);
    assert_eq!(plan.receipt().formula_cache_cleared_count(), 0);
    assert_eq!(
        plan.after_state()
            .cell(&id("cell-1-2")?)
            .and_then(|cell| cell.formula())
            .map(FormulaCell::owner),
        Some(CellCoordinate { row: 2, column: 2 })
    );
    Ok(())
}

#[test]
fn insert_columns_preserves_track_geometry_and_formula_identity() -> TestResult {
    let source_grid = grid(2, 3)?;
    let source = source_state(
        &source_grid,
        vec![0, 40, 100],
        vec![0, 30, 70, 100],
        Some((CellCoordinate { row: 1, column: 2 }, "SUM(A2:B2)")),
    )?;
    let new_ids = vec![id("new-c0")?, id("new-c1")?];
    let target_grid = source_grid
        .insert_columns(1, 1, new_ids.clone(), TableGridLimits::default())?
        .into_parts()
        .0;
    let target = target_draft(
        &source_grid,
        &source,
        &target_grid,
        TableStructureOperation::InsertColumns,
        1,
        1,
        vec![0, 40, 100],
        vec![0, 30, 40, 80, 110],
    )?;
    let request = request(
        &source_grid,
        &source,
        TableStructureOperation::InsertColumns,
        1,
        1,
        new_ids,
        target,
    )?;
    let plan = TableStructureBuilder::build(
        &request,
        &source,
        &source_grid,
        &digest('2'),
        TableStructureLimits::default(),
    )?;
    let formula = plan
        .after_state()
        .cell(&id("cell-1-2")?)
        .and_then(|cell| cell.formula())
        .ok_or("missing formula")?;
    assert_eq!(formula.owner(), CellCoordinate { row: 1, column: 3 });
    assert_eq!(
        formula.ast().canonical_formula(FormulaLimits::default())?,
        "SUM(A2:C2)"
    );
    assert_eq!(plan.receipt().introduced_edge_count(), 3);
    Ok(())
}

#[test]
fn delete_rows_and_columns_preserve_survivors_and_exact_geometry() -> TestResult {
    let source_grid = grid(3, 3)?;
    let source = source_state(
        &source_grid,
        vec![0, 20, 50, 100],
        vec![0, 25, 65, 100],
        None,
    )?;
    let row_grid = source_grid
        .delete_rows(1, 1, TableGridLimits::default())?
        .into_parts()
        .0;
    let row_target = target_draft(
        &source_grid,
        &source,
        &row_grid,
        TableStructureOperation::DeleteRows,
        1,
        1,
        vec![0, 20, 70],
        vec![0, 25, 65, 100],
    )?;
    let row_request = request(
        &source_grid,
        &source,
        TableStructureOperation::DeleteRows,
        1,
        1,
        Vec::new(),
        row_target,
    )?;
    let row_plan = TableStructureBuilder::build(
        &row_request,
        &source,
        &source_grid,
        &digest('2'),
        TableStructureLimits::default(),
    )?;
    assert_eq!(row_plan.receipt().deleted_master_cell_count(), 3);
    assert_eq!(row_plan.receipt().removed_edge_count(), 4);

    let column_grid = source_grid
        .delete_columns(1, 1, TableGridLimits::default())?
        .into_parts()
        .0;
    let column_target = target_draft(
        &source_grid,
        &source,
        &column_grid,
        TableStructureOperation::DeleteColumns,
        1,
        1,
        vec![0, 20, 50, 100],
        vec![0, 25, 60],
    )?;
    let column_request = request(
        &source_grid,
        &source,
        TableStructureOperation::DeleteColumns,
        1,
        1,
        Vec::new(),
        column_target,
    )?;
    let column_plan = TableStructureBuilder::build(
        &column_request,
        &source,
        &source_grid,
        &digest('2'),
        TableStructureLimits::default(),
    )?;
    assert_eq!(column_plan.receipt().deleted_master_cell_count(), 3);
    assert_eq!(column_plan.after_grid().columns(), 2);
    Ok(())
}

#[test]
fn collapsed_survivor_edges_must_match_exactly() -> TestResult {
    let source_grid = grid(3, 2)?;
    let source = source_state(&source_grid, vec![0, 20, 50, 100], vec![0, 50, 100], None)?;
    let target_grid = source_grid
        .delete_rows(1, 1, TableGridLimits::default())?
        .into_parts()
        .0;
    let mut target = target_draft(
        &source_grid,
        &source,
        &target_grid,
        TableStructureOperation::DeleteRows,
        1,
        1,
        vec![0, 20, 70],
        vec![0, 50, 100],
    )?;
    target
        .edges
        .iter_mut()
        .find(|edge| {
            edge.axis == TableRulingAxis::Horizontal && edge.boundary == 1 && edge.offset == 0
        })
        .ok_or("missing target edge")?
        .line_sha256 = Some(digest('2'));
    assert!(matches!(
        request(
            &source_grid,
            &source,
            TableStructureOperation::DeleteRows,
            1,
            1,
            Vec::new(),
            target,
        ),
        Err(TableStructureError::EdgePreservationMismatch)
    ));
    Ok(())
}

#[test]
fn geometry_payload_property_and_inserted_cell_drift_fail_closed() -> TestResult {
    let source_grid = grid(2, 2)?;
    let source = source_state(&source_grid, vec![0, 50, 100], vec![0, 50, 100], None)?;
    let new_ids = vec![id("new-0")?, id("new-1")?];
    let target_grid = source_grid
        .insert_rows(1, 1, new_ids.clone(), TableGridLimits::default())?
        .into_parts()
        .0;
    let make_target = || {
        target_draft(
            &source_grid,
            &source,
            &target_grid,
            TableStructureOperation::InsertRows,
            1,
            1,
            vec![0, 50, 60, 110],
            vec![0, 50, 100],
        )
    };
    let mut geometry = make_target()?;
    geometry.row_boundaries_hwpunit = vec![0, 45, 55, 105];
    geometry.frame.height_hwpunit = 105;
    assert!(matches!(
        request(
            &source_grid,
            &source,
            TableStructureOperation::InsertRows,
            1,
            1,
            new_ids.clone(),
            geometry,
        ),
        Err(TableStructureError::GeometryMismatch)
    ));

    let mut payload = make_target()?;
    payload.cells[0].payload.clear();
    assert!(matches!(
        request(
            &source_grid,
            &source,
            TableStructureOperation::InsertRows,
            1,
            1,
            new_ids.clone(),
            payload,
        ),
        Err(TableStructureError::CellPreservationMismatch)
    ));

    let mut inserted = make_target()?;
    inserted
        .cells
        .iter_mut()
        .find(|cell| cell.master_cell_id == new_ids[0])
        .ok_or("missing inserted cell")?
        .payload
        .push(TableRulingPayloadBlock {
            block_id: id("forbidden-payload")?,
            payload_sha256: digest('f'),
        });
    assert!(matches!(
        request(
            &source_grid,
            &source,
            TableStructureOperation::InsertRows,
            1,
            1,
            new_ids,
            inserted,
        ),
        Err(TableStructureError::InsertedCellMismatch)
    ));
    Ok(())
}

#[test]
fn formula_reference_deletion_fails_but_owner_deletion_is_explicit() -> TestResult {
    let source_grid = grid(2, 3)?;
    let source = source_state(
        &source_grid,
        vec![0, 50, 100],
        vec![0, 30, 70, 100],
        Some((CellCoordinate { row: 1, column: 2 }, "SUM(A2:B2)")),
    )?;
    let reference_error = source_grid
        .delete_columns(0, 1, TableGridLimits::default())?
        .into_parts()
        .0;
    assert!(
        target_draft(
            &source_grid,
            &source,
            &reference_error,
            TableStructureOperation::DeleteColumns,
            0,
            1,
            vec![0, 50, 100],
            vec![0, 40, 70],
        )
        .is_err()
    );

    let owner_grid = source_grid
        .delete_rows(1, 1, TableGridLimits::default())?
        .into_parts()
        .0;
    let owner_target = target_draft(
        &source_grid,
        &source,
        &owner_grid,
        TableStructureOperation::DeleteRows,
        1,
        1,
        vec![0, 50],
        vec![0, 30, 70, 100],
    )?;
    let owner_request = request(
        &source_grid,
        &source,
        TableStructureOperation::DeleteRows,
        1,
        1,
        Vec::new(),
        owner_target,
    )?;
    let owner_plan = TableStructureBuilder::build(
        &owner_request,
        &source,
        &source_grid,
        &digest('2'),
        TableStructureLimits::default(),
    )?;
    assert_eq!(owner_plan.receipt().formula_deleted_count(), 1);
    Ok(())
}

#[test]
fn request_build_drift_json_bounds_and_debug_are_fail_closed() -> TestResult {
    let source_grid = grid(2, 2)?;
    let source = source_state(&source_grid, vec![0, 50, 100], vec![0, 50, 100], None)?;
    let ids = vec![id("new-a")?, id("new-b")?];
    let target_grid = source_grid
        .insert_rows(2, 1, ids.clone(), TableGridLimits::default())?
        .into_parts()
        .0;
    let target = target_draft(
        &source_grid,
        &source,
        &target_grid,
        TableStructureOperation::InsertRows,
        2,
        1,
        vec![0, 50, 100, 110],
        vec![0, 50, 100],
    )?;
    let request = request(
        &source_grid,
        &source,
        TableStructureOperation::InsertRows,
        2,
        1,
        ids,
        target,
    )?;
    assert!(matches!(
        TableStructureBuilder::build(
            &request,
            &source,
            &source_grid,
            &digest('4'),
            TableStructureLimits::default(),
        ),
        Err(TableStructureError::DocumentFlowMismatch)
    ));
    let json = request.canonical_json(TableStructureLimits::default())?;
    let duplicate = String::from_utf8(json.clone())?.replacen(
        '{',
        &format!("{{\"schema_version\":\"{TABLE_STRUCTURE_SCHEMA_VERSION}\","),
        1,
    );
    assert!(matches!(
        TableStructureRequest::from_json(
            duplicate.as_bytes(),
            &source,
            &source_grid,
            &digest('2'),
            TableStructureLimits::default(),
        ),
        Err(TableStructureError::InvalidJson)
    ));
    let unknown = String::from_utf8(json)?.replacen('{', "{\"unknown\":0,", 1);
    assert!(matches!(
        TableStructureRequest::from_json(
            unknown.as_bytes(),
            &source,
            &source_grid,
            &digest('2'),
            TableStructureLimits::default(),
        ),
        Err(TableStructureError::InvalidJson)
    ));
    let debug = format!("{request:?}");
    assert!(!debug.contains("secret-table-id"));
    assert!(!debug.contains(&digest('2')));
    assert!(!debug.contains("new-a"));
    Ok(())
}
