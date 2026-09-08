use domain_ir::{
    CellCoordinate, FormulaAst, FormulaAstDraft, FormulaCache, FormulaCellDraft, FormulaDecimal,
    FormulaLimits, FormulaNumberFormat, FormulaValue, LogicalId, TABLE_DRAW_CAPABILITY_ID,
    TABLE_ERASER_CAPABILITY_ID, TABLE_FORMULA_SCHEMA_VERSION, TABLE_GRID_SCHEMA_VERSION,
    TABLE_RULING_SCHEMA_VERSION, TableCellSpan, TableGrid, TableGridDraft, TableGridLimits,
    TableRulingAxis, TableRulingBuilder, TableRulingCellDraft, TableRulingCellProperties,
    TableRulingDiagonalDirection, TableRulingEdge, TableRulingError, TableRulingFormulaPolicy,
    TableRulingFrame, TableRulingLimitConfig, TableRulingLimits, TableRulingOperation,
    TableRulingPayloadBlock, TableRulingPlan, TableRulingRequest, TableRulingRequestDraft,
    TableRulingState, TableRulingStateDraft, TableRulingStroke,
};

type TestResult = Result<(), Box<dyn std::error::Error>>;

fn id(value: &str) -> Result<LogicalId, Box<dyn std::error::Error>> {
    Ok(LogicalId::parse(value)?)
}

fn digest(character: char) -> String {
    let value = match character {
        '0'..='9' | 'a'..='f' => character,
        'p' => '8',
        't' => '9',
        _ => '7',
    };
    std::iter::repeat_n(value, 64).collect()
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

fn frame() -> TableRulingFrame {
    TableRulingFrame {
        left_hwpunit: 1_000,
        top_hwpunit: 2_000,
        width_hwpunit: 100,
        height_hwpunit: 100,
    }
}

fn properties(character: char) -> TableRulingCellProperties {
    TableRulingCellProperties {
        non_ruling_properties_sha256: digest(character),
        background_sha256: Some(digest('b')),
        slash_diagonal_sha256: None,
        back_slash_diagonal_sha256: None,
    }
}

fn formula(
    source: &str,
    owner: CellCoordinate,
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
        number_format: FormulaNumberFormat::Number {
            decimal_places: 2,
            use_grouping: true,
        },
    })
}

fn unmerged_grid(rows: u32, columns: u32) -> Result<TableGrid, Box<dyn std::error::Error>> {
    let mut master_cells = Vec::new();
    for row in 0..rows {
        for column in 0..columns {
            master_cells.push(TableCellSpan {
                master_cell_id: id(&format!("cell-{row}-{column}"))?,
                row,
                column,
                row_span: 1,
                column_span: 1,
            });
        }
    }
    Ok(TableGrid::from_draft(
        TableGridDraft {
            schema_version: TABLE_GRID_SCHEMA_VERSION.to_owned(),
            rows,
            columns,
            master_cells,
        },
        TableGridLimits::default(),
    )?)
}

fn all_edges(rows: u32, columns: u32, line: Option<&str>) -> Vec<TableRulingEdge> {
    let mut edges = Vec::new();
    for boundary in 0..=rows {
        for offset in 0..columns {
            edges.push(TableRulingEdge {
                axis: TableRulingAxis::Horizontal,
                boundary,
                offset,
                line_sha256: line.map(str::to_owned),
            });
        }
    }
    for boundary in 0..=columns {
        for offset in 0..rows {
            edges.push(TableRulingEdge {
                axis: TableRulingAxis::Vertical,
                boundary,
                offset,
                line_sha256: line.map(str::to_owned),
            });
        }
    }
    edges
}

fn state_draft(
    grid: &TableGrid,
    row_boundaries: Vec<u32>,
    column_boundaries: Vec<u32>,
    property_characters: &[char],
    formulas: &[(CellCoordinate, &str)],
    line: char,
) -> Result<TableRulingStateDraft, Box<dyn std::error::Error>> {
    let mut cells = Vec::new();
    for (index, span) in grid.master_cells().iter().enumerate() {
        let coordinate = CellCoordinate {
            row: span.row,
            column: span.column,
        };
        let formula = formulas
            .iter()
            .find(|(owner, _)| *owner == coordinate)
            .map(|(_, source)| formula(source, coordinate))
            .transpose()?;
        cells.push(TableRulingCellDraft {
            master_cell_id: span.master_cell_id.clone(),
            coordinate,
            payload: vec![TableRulingPayloadBlock {
                block_id: id(&format!("payload-{index}"))?,
                payload_sha256: digest(if index % 2 == 0 { 'a' } else { 'c' }),
            }],
            properties: properties(property_characters[index]),
            formula,
        });
    }
    Ok(TableRulingStateDraft {
        schema_version: TABLE_RULING_SCHEMA_VERSION.to_owned(),
        table_id: id("table-private-secret")?,
        frame: frame(),
        grid_sha256: hex(grid.canonical_sha256()?),
        table_properties_sha256: digest('t'),
        row_boundaries_hwpunit: row_boundaries,
        column_boundaries_hwpunit: column_boundaries,
        edges: all_edges(grid.rows(), grid.columns(), Some(&digest(line))),
        cells,
    })
}

fn state(
    grid: &TableGrid,
    row_boundaries: Vec<u32>,
    column_boundaries: Vec<u32>,
) -> Result<TableRulingState, Box<dyn std::error::Error>> {
    let properties = vec!['a'; grid.master_cell_count()];
    Ok(TableRulingState::from_draft(
        state_draft(
            grid,
            row_boundaries,
            column_boundaries,
            &properties,
            &[],
            '1',
        )?,
        grid,
        FormulaLimits::default(),
        TableRulingLimits::default(),
    )?)
}

fn existing_request(
    state: &TableRulingState,
    grid: &TableGrid,
    operation: TableRulingOperation,
) -> Result<TableRulingRequest, Box<dyn std::error::Error>> {
    Ok(TableRulingRequest::from_draft(
        TableRulingRequestDraft {
            schema_version: TABLE_RULING_SCHEMA_VERSION.to_owned(),
            table_id: state.table_id().clone(),
            expected_state_sha256: Some(hex(state.canonical_sha256(TableRulingLimits::default())?)),
            expected_grid_sha256: Some(hex(grid.canonical_sha256()?)),
            expected_document_flow_sha256: digest('f'),
            operation,
        },
        Some(state),
        Some(grid),
        &digest('f'),
        TableRulingLimits::default(),
    )?)
}

fn build_existing(
    request: &TableRulingRequest,
    state: &TableRulingState,
    grid: &TableGrid,
) -> Result<TableRulingPlan, TableRulingError> {
    TableRulingBuilder::build(
        request,
        Some(state),
        Some(grid),
        &digest('f'),
        TableGridLimits::default(),
        FormulaLimits::default(),
        TableRulingLimits::default(),
    )
}

fn grid_from_plan(plan: &TableRulingPlan) -> Result<TableGrid, Box<dyn std::error::Error>> {
    Ok(TableGrid::new(
        plan.after_grid().rows(),
        plan.after_grid().columns(),
        plan.after_grid().master_cells().to_vec(),
        TableGridLimits::default(),
    )?)
}

fn outer_plan() -> Result<TableRulingPlan, Box<dyn std::error::Error>> {
    let request = TableRulingRequest::from_draft(
        TableRulingRequestDraft {
            schema_version: TABLE_RULING_SCHEMA_VERSION.to_owned(),
            table_id: id("table-created")?,
            expected_state_sha256: None,
            expected_grid_sha256: None,
            expected_document_flow_sha256: digest('f'),
            operation: TableRulingOperation::DrawOuterRectangle {
                frame: frame(),
                initial_master_cell_id: id("cell-origin")?,
                table_properties_sha256: digest('t'),
                initial_cell_properties: properties('a'),
                line_sha256: digest('1'),
                insertion_context_sha256: digest('e'),
            },
        },
        None,
        None,
        &digest('f'),
        TableRulingLimits::default(),
    )?;
    Ok(TableRulingBuilder::build(
        &request,
        None,
        None,
        &digest('f'),
        TableGridLimits::default(),
        FormulaLimits::default(),
        TableRulingLimits::default(),
    )?)
}

#[test]
fn outer_rectangle_creates_exact_one_cell_table_and_visible_frame() -> TestResult {
    let plan = outer_plan()?;
    assert_eq!(plan.capability_id(), TABLE_DRAW_CAPABILITY_ID);
    assert_eq!(plan.after_grid().rows(), 1);
    assert_eq!(plan.after_grid().columns(), 1);
    assert_eq!(plan.after_grid().master_cells().len(), 1);
    assert_eq!(plan.after_state().frame(), frame());
    assert_eq!(plan.after_state().edges().len(), 4);
    assert!(
        plan.after_state()
            .edges()
            .iter()
            .all(|edge| edge.line_sha256 == Some(digest('1')))
    );
    assert!(plan.after_state().cells()[0].payload().is_empty());
    assert!(plan.after_state().cells()[0].formula().is_none());
    assert!(plan.receipt().topology_changed());
    assert_eq!(plan.receipt().created_master_cell_count(), 1);
    assert_eq!(
        plan.receipt().insertion_context_sha256(),
        Some(digest('e').as_str())
    );
    Ok(())
}

#[test]
fn full_row_and_column_strokes_build_a_complete_two_by_two_topology() -> TestResult {
    let outer = outer_plan()?;
    let grid = grid_from_plan(&outer)?;
    let horizontal = existing_request(
        outer.after_state(),
        &grid,
        TableRulingOperation::DrawStroke {
            stroke: TableRulingStroke {
                axis: TableRulingAxis::Horizontal,
                fixed_hwpunit: 50,
                start_hwpunit: 0,
                end_hwpunit: 100,
            },
            line_sha256: digest('2'),
            new_master_cell_ids: vec![id("cell-bottom")?],
            formula_policy: TableRulingFormulaPolicy::RejectRebase,
        },
    )?;
    let two_rows = build_existing(&horizontal, outer.after_state(), &grid)?;
    assert_eq!(two_rows.after_grid().rows(), 2);
    assert_eq!(two_rows.after_grid().master_cells().len(), 2);
    assert_eq!(two_rows.receipt().created_master_cell_count(), 1);

    let two_row_grid = grid_from_plan(&two_rows)?;
    let vertical = existing_request(
        two_rows.after_state(),
        &two_row_grid,
        TableRulingOperation::DrawStroke {
            stroke: TableRulingStroke {
                axis: TableRulingAxis::Vertical,
                fixed_hwpunit: 50,
                start_hwpunit: 0,
                end_hwpunit: 100,
            },
            line_sha256: digest('3'),
            new_master_cell_ids: vec![id("cell-top-right")?, id("cell-bottom-right")?],
            formula_policy: TableRulingFormulaPolicy::RejectRebase,
        },
    )?;
    let four_cells = build_existing(&vertical, two_rows.after_state(), &two_row_grid)?;
    assert_eq!(four_cells.after_grid().rows(), 2);
    assert_eq!(four_cells.after_grid().columns(), 2);
    assert_eq!(four_cells.after_grid().master_cells().len(), 4);
    assert_eq!(four_cells.after_state().edges().len(), 12);
    assert_eq!(four_cells.receipt().created_master_cell_count(), 2);
    assert_eq!(four_cells.receipt().payload_block_preserved_count(), 0);
    Ok(())
}

#[test]
fn local_cell_split_refines_the_lattice_without_splitting_its_neighbor() -> TestResult {
    let grid = unmerged_grid(2, 2)?;
    let state = state(&grid, vec![0, 50, 100], vec![0, 50, 100])?;
    let request = existing_request(
        &state,
        &grid,
        TableRulingOperation::DrawStroke {
            stroke: TableRulingStroke {
                axis: TableRulingAxis::Horizontal,
                fixed_hwpunit: 25,
                start_hwpunit: 0,
                end_hwpunit: 50,
            },
            line_sha256: digest('2'),
            new_master_cell_ids: vec![id("cell-local-new")?],
            formula_policy: TableRulingFormulaPolicy::RejectRebase,
        },
    )?;
    let plan = build_existing(&request, &state, &grid)?;
    assert_eq!(plan.after_grid().rows(), 3);
    assert_eq!(plan.after_grid().columns(), 2);
    assert_eq!(plan.after_grid().master_cells().len(), 5);
    let top_right = plan
        .after_grid()
        .master_cells()
        .iter()
        .find(|span| span.master_cell_id.as_str() == "cell-0-1")
        .ok_or("missing top-right")?;
    assert_eq!(top_right.row_span, 2);
    assert_eq!(plan.receipt().payload_block_preserved_count(), 4);
    assert_eq!(
        plan.after_state()
            .cells()
            .iter()
            .map(|cell| cell.payload().len())
            .sum::<usize>(),
        4
    );
    Ok(())
}

#[test]
fn draw_and_erase_diagonals_are_nonstructural_and_directional() -> TestResult {
    let grid = unmerged_grid(1, 1)?;
    let state = state(&grid, vec![0, 100], vec![0, 100])?;
    let cell_id = grid.master_cells()[0].master_cell_id.clone();
    let draw = existing_request(
        &state,
        &grid,
        TableRulingOperation::DrawDiagonal {
            master_cell_id: cell_id.clone(),
            direction: TableRulingDiagonalDirection::Slash,
            line_sha256: digest('4'),
        },
    )?;
    let drawn = build_existing(&draw, &state, &grid)?;
    assert_eq!(drawn.capability_id(), TABLE_DRAW_CAPABILITY_ID);
    assert_eq!(drawn.receipt().diagonal_change_count(), 1);
    assert!(!drawn.receipt().topology_changed());
    assert_eq!(
        drawn.after_state().cells()[0]
            .properties()
            .slash_diagonal_sha256,
        Some(digest('4'))
    );
    assert!(
        drawn.after_state().cells()[0]
            .properties()
            .back_slash_diagonal_sha256
            .is_none()
    );

    let erase = existing_request(
        drawn.after_state(),
        &grid,
        TableRulingOperation::EraseDiagonal {
            master_cell_id: cell_id,
            direction: TableRulingDiagonalDirection::Slash,
        },
    )?;
    let erased = build_existing(&erase, drawn.after_state(), &grid)?;
    assert_eq!(erased.capability_id(), TABLE_ERASER_CAPABILITY_ID);
    assert!(
        erased.after_state().cells()[0]
            .properties()
            .slash_diagonal_sha256
            .is_none()
    );
    Ok(())
}

#[test]
fn erasing_a_shared_edge_merges_cells_and_concatenates_payload_in_row_major_order() -> TestResult {
    let grid = unmerged_grid(1, 2)?;
    let state = state(&grid, vec![0, 100], vec![0, 50, 100])?;
    let request = existing_request(
        &state,
        &grid,
        TableRulingOperation::EraseStroke {
            stroke: TableRulingStroke {
                axis: TableRulingAxis::Vertical,
                fixed_hwpunit: 50,
                start_hwpunit: 0,
                end_hwpunit: 100,
            },
            formula_policy: TableRulingFormulaPolicy::RejectRebase,
        },
    )?;
    let plan = build_existing(&request, &state, &grid)?;
    assert_eq!(plan.capability_id(), TABLE_ERASER_CAPABILITY_ID);
    assert_eq!(plan.after_grid().master_cells().len(), 1);
    assert_eq!(plan.after_grid().master_cells()[0].column_span, 2);
    assert_eq!(plan.after_state().cells()[0].payload().len(), 2);
    assert_eq!(
        plan.after_state().cells()[0].payload()[0].block_id.as_str(),
        "payload-0"
    );
    assert_eq!(
        plan.after_state().cells()[0].payload()[1].block_id.as_str(),
        "payload-1"
    );
    assert_eq!(plan.receipt().retired_master_cell_count(), 1);
    assert_eq!(plan.receipt().structural_merge_count(), 1);
    assert_eq!(plan.receipt().payload_block_preserved_count(), 2);
    Ok(())
}

#[test]
fn erasing_outer_or_already_nonstructural_edges_uses_explicit_transparent_lines() -> TestResult {
    let grid = unmerged_grid(1, 2)?;
    let state = state(&grid, vec![0, 100], vec![0, 50, 100])?;
    let request = existing_request(
        &state,
        &grid,
        TableRulingOperation::EraseStroke {
            stroke: TableRulingStroke {
                axis: TableRulingAxis::Horizontal,
                fixed_hwpunit: 0,
                start_hwpunit: 0,
                end_hwpunit: 100,
            },
            formula_policy: TableRulingFormulaPolicy::RejectRebase,
        },
    )?;
    let plan = build_existing(&request, &state, &grid)?;
    assert_eq!(plan.after_grid().master_cells().len(), 2);
    assert!(!plan.receipt().topology_changed());
    assert_eq!(plan.receipt().nonstructural_transparent_edge_count(), 2);
    assert_eq!(plan.receipt().edge_change_count(), 2);
    assert!(
        plan.after_state()
            .edge(TableRulingAxis::Horizontal, 0, 0)
            .ok_or("missing edge")?
            .line_sha256
            .is_none()
    );
    Ok(())
}

#[test]
fn erasing_an_internal_edge_of_one_merged_cell_is_transparent_not_a_merge() -> TestResult {
    let grid = TableGrid::new(
        1,
        2,
        vec![TableCellSpan {
            master_cell_id: id("merged-cell")?,
            row: 0,
            column: 0,
            row_span: 1,
            column_span: 2,
        }],
        TableGridLimits::default(),
    )?;
    let state = state(&grid, vec![0, 100], vec![0, 50, 100])?;
    let request = existing_request(
        &state,
        &grid,
        TableRulingOperation::EraseStroke {
            stroke: TableRulingStroke {
                axis: TableRulingAxis::Vertical,
                fixed_hwpunit: 50,
                start_hwpunit: 0,
                end_hwpunit: 100,
            },
            formula_policy: TableRulingFormulaPolicy::RejectRebase,
        },
    )?;
    let plan = build_existing(&request, &state, &grid)?;
    assert_eq!(plan.after_grid().master_cells().len(), 1);
    assert_eq!(plan.receipt().structural_merge_count(), 0);
    assert_eq!(plan.receipt().nonstructural_transparent_edge_count(), 1);
    assert!(
        plan.after_state()
            .edge(TableRulingAxis::Vertical, 1, 0)
            .ok_or("missing internal edge")?
            .line_sha256
            .is_none()
    );
    Ok(())
}

#[test]
fn nonrectangular_draw_or_shared_edge_merge_fails_closed() -> TestResult {
    let grid = unmerged_grid(1, 1)?;
    let base_state = state(&grid, vec![0, 100], vec![0, 100])?;
    let partial = existing_request(
        &base_state,
        &grid,
        TableRulingOperation::DrawStroke {
            stroke: TableRulingStroke {
                axis: TableRulingAxis::Horizontal,
                fixed_hwpunit: 50,
                start_hwpunit: 0,
                end_hwpunit: 50,
            },
            line_sha256: digest('2'),
            new_master_cell_ids: Vec::new(),
            formula_policy: TableRulingFormulaPolicy::RejectRebase,
        },
    )?;
    assert_eq!(
        build_existing(&partial, &base_state, &grid),
        Err(TableRulingError::NonRectangularSplit)
    );

    let l_grid = TableGrid::new(
        2,
        2,
        vec![
            TableCellSpan {
                master_cell_id: id("left")?,
                row: 0,
                column: 0,
                row_span: 2,
                column_span: 1,
            },
            TableCellSpan {
                master_cell_id: id("right-top")?,
                row: 0,
                column: 1,
                row_span: 1,
                column_span: 1,
            },
            TableCellSpan {
                master_cell_id: id("right-bottom")?,
                row: 1,
                column: 1,
                row_span: 1,
                column_span: 1,
            },
        ],
        TableGridLimits::default(),
    )?;
    let l_state = state(&l_grid, vec![0, 50, 100], vec![0, 50, 100])?;
    let l_merge = existing_request(
        &l_state,
        &l_grid,
        TableRulingOperation::EraseStroke {
            stroke: TableRulingStroke {
                axis: TableRulingAxis::Vertical,
                fixed_hwpunit: 50,
                start_hwpunit: 0,
                end_hwpunit: 50,
            },
            formula_policy: TableRulingFormulaPolicy::RejectRebase,
        },
    )?;
    assert_eq!(
        build_existing(&l_merge, &l_state, &l_grid),
        Err(TableRulingError::NonRectangularMerge)
    );
    Ok(())
}

#[test]
fn split_and_merge_reject_unpreservable_diagonal_or_property_state() -> TestResult {
    let grid = unmerged_grid(1, 1)?;
    let mut draft = state_draft(&grid, vec![0, 100], vec![0, 100], &['a'], &[], '1')?;
    draft.cells[0].properties.slash_diagonal_sha256 = Some(digest('4'));
    let diagonal_state = TableRulingState::from_draft(
        draft,
        &grid,
        FormulaLimits::default(),
        TableRulingLimits::default(),
    )?;
    let split = existing_request(
        &diagonal_state,
        &grid,
        TableRulingOperation::DrawStroke {
            stroke: TableRulingStroke {
                axis: TableRulingAxis::Horizontal,
                fixed_hwpunit: 50,
                start_hwpunit: 0,
                end_hwpunit: 100,
            },
            line_sha256: digest('2'),
            new_master_cell_ids: vec![id("new-cell")?],
            formula_policy: TableRulingFormulaPolicy::RejectRebase,
        },
    )?;
    assert_eq!(
        build_existing(&split, &diagonal_state, &grid),
        Err(TableRulingError::DiagonalSplitConflict)
    );

    let merge_grid = unmerged_grid(1, 2)?;
    let merge_state = TableRulingState::from_draft(
        state_draft(
            &merge_grid,
            vec![0, 100],
            vec![0, 50, 100],
            &['a', 'c'],
            &[],
            '1',
        )?,
        &merge_grid,
        FormulaLimits::default(),
        TableRulingLimits::default(),
    )?;
    let merge = existing_request(
        &merge_state,
        &merge_grid,
        TableRulingOperation::EraseStroke {
            stroke: TableRulingStroke {
                axis: TableRulingAxis::Vertical,
                fixed_hwpunit: 50,
                start_hwpunit: 0,
                end_hwpunit: 100,
            },
            formula_policy: TableRulingFormulaPolicy::RejectRebase,
        },
    )?;
    assert_eq!(
        build_existing(&merge, &merge_state, &merge_grid),
        Err(TableRulingError::CellPropertiesConflict)
    );
    Ok(())
}

#[test]
fn formula_rebase_is_explicit_and_only_changed_caches_are_cleared() -> TestResult {
    let grid = unmerged_grid(1, 2)?;
    let state = TableRulingState::from_draft(
        state_draft(
            &grid,
            vec![0, 100],
            vec![0, 50, 100],
            &['a', 'a'],
            &[(CellCoordinate { row: 0, column: 0 }, "B1")],
            '1',
        )?,
        &grid,
        FormulaLimits::default(),
        TableRulingLimits::default(),
    )?;
    let new_cell_id = id("cell-left-new")?;
    let operation = |policy| TableRulingOperation::DrawStroke {
        stroke: TableRulingStroke {
            axis: TableRulingAxis::Vertical,
            fixed_hwpunit: 25,
            start_hwpunit: 0,
            end_hwpunit: 100,
        },
        line_sha256: digest('2'),
        new_master_cell_ids: vec![new_cell_id.clone()],
        formula_policy: policy,
    };
    let rejecting = existing_request(
        &state,
        &grid,
        operation(TableRulingFormulaPolicy::RejectRebase),
    )?;
    assert_eq!(
        build_existing(&rejecting, &state, &grid),
        Err(TableRulingError::FormulaRebaseRequired)
    );

    let clearing = existing_request(
        &state,
        &grid,
        operation(TableRulingFormulaPolicy::RebaseAndClearTopologyStaleCache),
    )?;
    let plan = build_existing(&clearing, &state, &grid)?;
    assert_eq!(plan.receipt().formula_preserved_count(), 1);
    assert_eq!(plan.receipt().formula_rebased_count(), 1);
    assert_eq!(plan.receipt().formula_cache_cleared_count(), 1);
    let formula = plan.after_state().cells()[0]
        .formula()
        .ok_or("formula missing")?;
    assert_eq!(
        formula.ast().canonical_formula(FormulaLimits::default())?,
        "C1"
    );
    assert!(matches!(formula.cache(), FormulaCache::Absent));
    Ok(())
}

#[test]
fn shared_edge_merge_rebases_the_single_formula_and_clears_only_its_stale_cache() -> TestResult {
    let grid = unmerged_grid(1, 2)?;
    let state = TableRulingState::from_draft(
        state_draft(
            &grid,
            vec![0, 100],
            vec![0, 50, 100],
            &['a', 'a'],
            &[(CellCoordinate { row: 0, column: 1 }, "B1")],
            '1',
        )?,
        &grid,
        FormulaLimits::default(),
        TableRulingLimits::default(),
    )?;
    let operation = |policy| TableRulingOperation::EraseStroke {
        stroke: TableRulingStroke {
            axis: TableRulingAxis::Vertical,
            fixed_hwpunit: 50,
            start_hwpunit: 0,
            end_hwpunit: 100,
        },
        formula_policy: policy,
    };
    let rejecting = existing_request(
        &state,
        &grid,
        operation(TableRulingFormulaPolicy::RejectRebase),
    )?;
    assert_eq!(
        build_existing(&rejecting, &state, &grid),
        Err(TableRulingError::FormulaRebaseRequired)
    );
    let clearing = existing_request(
        &state,
        &grid,
        operation(TableRulingFormulaPolicy::RebaseAndClearTopologyStaleCache),
    )?;
    let plan = build_existing(&clearing, &state, &grid)?;
    assert_eq!(plan.receipt().formula_preserved_count(), 1);
    assert_eq!(plan.receipt().formula_rebased_count(), 1);
    assert_eq!(plan.receipt().formula_cache_cleared_count(), 1);
    let formula = plan.after_state().cells()[0]
        .formula()
        .ok_or("merged formula missing")?;
    assert_eq!(formula.owner(), CellCoordinate { row: 0, column: 0 });
    assert_eq!(
        formula.ast().canonical_formula(FormulaLimits::default())?,
        "A1"
    );
    assert!(matches!(formula.cache(), FormulaCache::Absent));
    Ok(())
}

#[test]
fn shared_edge_merge_clears_external_formula_caches_only_under_explicit_policy() -> TestResult {
    let grid = unmerged_grid(1, 3)?;
    let state = TableRulingState::from_draft(
        state_draft(
            &grid,
            vec![0, 100],
            vec![0, 30, 60, 100],
            &['a', 'a', 'a'],
            &[(CellCoordinate { row: 0, column: 2 }, "C1")],
            '1',
        )?,
        &grid,
        FormulaLimits::default(),
        TableRulingLimits::default(),
    )?;
    let operation = |formula_policy| TableRulingOperation::EraseStroke {
        stroke: TableRulingStroke {
            axis: TableRulingAxis::Vertical,
            fixed_hwpunit: 30,
            start_hwpunit: 0,
            end_hwpunit: 100,
        },
        formula_policy,
    };
    let rejecting = existing_request(
        &state,
        &grid,
        operation(TableRulingFormulaPolicy::RejectRebase),
    )?;
    assert_eq!(
        build_existing(&rejecting, &state, &grid),
        Err(TableRulingError::FormulaRebaseRequired)
    );

    let clearing = existing_request(
        &state,
        &grid,
        operation(TableRulingFormulaPolicy::RebaseAndClearTopologyStaleCache),
    )?;
    let plan = build_existing(&clearing, &state, &grid)?;
    assert_eq!(plan.receipt().formula_preserved_count(), 1);
    assert_eq!(plan.receipt().formula_rebased_count(), 0);
    assert_eq!(plan.receipt().formula_cache_cleared_count(), 1);
    let formula = plan
        .after_state()
        .cells()
        .iter()
        .find_map(|cell| cell.formula())
        .ok_or("formula missing")?;
    assert_eq!(formula.owner(), CellCoordinate { row: 0, column: 2 });
    assert_eq!(
        formula.ast().canonical_formula(FormulaLimits::default())?,
        "C1"
    );
    assert!(matches!(formula.cache(), FormulaCache::Absent));
    Ok(())
}

#[test]
fn splitting_an_existing_merged_lattice_with_formula_state_fails_closed() -> TestResult {
    let grid = TableGrid::new(
        1,
        2,
        vec![TableCellSpan {
            master_cell_id: id("merged")?,
            row: 0,
            column: 0,
            row_span: 1,
            column_span: 2,
        }],
        TableGridLimits::default(),
    )?;
    let state = TableRulingState::from_draft(
        state_draft(
            &grid,
            vec![0, 100],
            vec![0, 50, 100],
            &['a'],
            &[(CellCoordinate { row: 0, column: 0 }, "A1")],
            '1',
        )?,
        &grid,
        FormulaLimits::default(),
        TableRulingLimits::default(),
    )?;
    let request = existing_request(
        &state,
        &grid,
        TableRulingOperation::DrawStroke {
            stroke: TableRulingStroke {
                axis: TableRulingAxis::Vertical,
                fixed_hwpunit: 50,
                start_hwpunit: 0,
                end_hwpunit: 100,
            },
            line_sha256: digest('2'),
            new_master_cell_ids: vec![id("split-new")?],
            formula_policy: TableRulingFormulaPolicy::RebaseAndClearTopologyStaleCache,
        },
    )?;
    assert_eq!(
        build_existing(&request, &state, &grid),
        Err(TableRulingError::FormulaTopologyAmbiguous)
    );
    Ok(())
}

#[test]
fn split_requires_the_exact_deterministic_new_master_identity_count() -> TestResult {
    let grid = unmerged_grid(1, 1)?;
    let state = state(&grid, vec![0, 100], vec![0, 100])?;
    for new_master_cell_ids in [Vec::new(), vec![id("new-a")?, id("new-b")?]] {
        let request = existing_request(
            &state,
            &grid,
            TableRulingOperation::DrawStroke {
                stroke: TableRulingStroke {
                    axis: TableRulingAxis::Horizontal,
                    fixed_hwpunit: 50,
                    start_hwpunit: 0,
                    end_hwpunit: 100,
                },
                line_sha256: digest('2'),
                new_master_cell_ids,
                formula_policy: TableRulingFormulaPolicy::RejectRebase,
            },
        )?;
        assert_eq!(
            build_existing(&request, &state, &grid),
            Err(TableRulingError::NewMasterCellCountMismatch)
        );
    }
    Ok(())
}

#[test]
fn request_and_builder_both_reject_state_grid_or_flow_drift() -> TestResult {
    let grid = unmerged_grid(1, 2)?;
    let state = state(&grid, vec![0, 100], vec![0, 50, 100])?;
    let operation = TableRulingOperation::EraseStroke {
        stroke: TableRulingStroke {
            axis: TableRulingAxis::Horizontal,
            fixed_hwpunit: 0,
            start_hwpunit: 0,
            end_hwpunit: 100,
        },
        formula_policy: TableRulingFormulaPolicy::RejectRebase,
    };
    let mut bad_draft = TableRulingRequestDraft {
        schema_version: TABLE_RULING_SCHEMA_VERSION.to_owned(),
        table_id: state.table_id().clone(),
        expected_state_sha256: Some(digest('0')),
        expected_grid_sha256: Some(hex(grid.canonical_sha256()?)),
        expected_document_flow_sha256: digest('f'),
        operation: operation.clone(),
    };
    assert_eq!(
        TableRulingRequest::from_draft(
            bad_draft.clone(),
            Some(&state),
            Some(&grid),
            &digest('f'),
            TableRulingLimits::default(),
        ),
        Err(TableRulingError::StateBindingMismatch)
    );
    bad_draft.expected_state_sha256 =
        Some(hex(state.canonical_sha256(TableRulingLimits::default())?));
    bad_draft.expected_grid_sha256 = Some(digest('0'));
    assert_eq!(
        TableRulingRequest::from_draft(
            bad_draft.clone(),
            Some(&state),
            Some(&grid),
            &digest('f'),
            TableRulingLimits::default(),
        ),
        Err(TableRulingError::StateBindingMismatch)
    );
    bad_draft.expected_grid_sha256 = Some(hex(grid.canonical_sha256()?));
    assert_eq!(
        TableRulingRequest::from_draft(
            bad_draft,
            Some(&state),
            Some(&grid),
            &digest('e'),
            TableRulingLimits::default(),
        ),
        Err(TableRulingError::FlowBindingMismatch)
    );

    let request = existing_request(&state, &grid, operation)?;
    let drifted_state = TableRulingState::from_draft(
        state_draft(&grid, vec![0, 100], vec![0, 50, 100], &['a', 'a'], &[], '2')?,
        &grid,
        FormulaLimits::default(),
        TableRulingLimits::default(),
    )?;
    assert_eq!(
        build_existing(&request, &drifted_state, &grid),
        Err(TableRulingError::StateBindingMismatch)
    );
    let drifted_grid = unmerged_grid(2, 1)?;
    assert_eq!(
        TableRulingBuilder::build(
            &request,
            Some(&state),
            Some(&drifted_grid),
            &digest('f'),
            TableGridLimits::default(),
            FormulaLimits::default(),
            TableRulingLimits::default(),
        ),
        Err(TableRulingError::StateBindingMismatch)
    );
    assert_eq!(
        TableRulingBuilder::build(
            &request,
            Some(&state),
            Some(&grid),
            &digest('e'),
            TableGridLimits::default(),
            FormulaLimits::default(),
            TableRulingLimits::default(),
        ),
        Err(TableRulingError::FlowBindingMismatch)
    );
    Ok(())
}

#[test]
fn strict_json_complete_sets_and_finite_limits_fail_closed() -> TestResult {
    let grid = unmerged_grid(1, 1)?;
    let draft = state_draft(&grid, vec![0, 100], vec![0, 100], &['a'], &[], '1')?;
    let mut missing_edge = draft.clone();
    missing_edge.edges.pop();
    assert_eq!(
        TableRulingState::from_draft(
            missing_edge,
            &grid,
            FormulaLimits::default(),
            TableRulingLimits::default(),
        ),
        Err(TableRulingError::EdgeSetMismatch)
    );
    let state = TableRulingState::from_draft(
        draft,
        &grid,
        FormulaLimits::default(),
        TableRulingLimits::default(),
    )?;
    let mut json: serde_json::Value =
        serde_json::from_slice(&state.canonical_json(TableRulingLimits::default())?)?;
    json.as_object_mut()
        .ok_or("state is not object")?
        .insert("unknown".to_owned(), serde_json::Value::Bool(true));
    assert_eq!(
        TableRulingState::from_json(
            &serde_json::to_vec(&json)?,
            &grid,
            FormulaLimits::default(),
            TableRulingLimits::default(),
        ),
        Err(TableRulingError::InvalidJson)
    );
    let canonical = String::from_utf8(state.canonical_json(TableRulingLimits::default())?)?;
    let duplicate = canonical.replacen(
        '{',
        &format!("{{\"schema_version\":\"{TABLE_RULING_SCHEMA_VERSION}\","),
        1,
    );
    assert_eq!(
        TableRulingState::from_json(
            duplicate.as_bytes(),
            &grid,
            FormulaLimits::default(),
            TableRulingLimits::default(),
        ),
        Err(TableRulingError::InvalidJson)
    );
    assert_eq!(
        TableRulingState::from_json(
            b"",
            &grid,
            FormulaLimits::default(),
            TableRulingLimits::default(),
        ),
        Err(TableRulingError::InputLimitExceeded)
    );
    let tiny = TableRulingLimits::new(TableRulingLimitConfig {
        input_bytes: 64,
        serialized_bytes: 64,
        ..TableRulingLimitConfig::default()
    })?;
    assert_eq!(
        state.canonical_json(tiny),
        Err(TableRulingError::OutputLimitExceeded)
    );
    Ok(())
}

#[test]
fn debug_output_redacts_identifiers_payloads_properties_formulas_and_digests() -> TestResult {
    let grid = unmerged_grid(1, 1)?;
    let state = TableRulingState::from_draft(
        state_draft(
            &grid,
            vec![0, 100],
            vec![0, 100],
            &['a'],
            &[(CellCoordinate { row: 0, column: 0 }, "1+2")],
            '1',
        )?,
        &grid,
        FormulaLimits::default(),
        TableRulingLimits::default(),
    )?;
    let debug = format!("{state:?}");
    assert!(!debug.contains("table-private-secret"));
    assert!(!debug.contains("payload-0"));
    assert!(!debug.contains(&digest('a')));
    assert!(!debug.contains("1+2"));
    let request = existing_request(
        &state,
        &grid,
        TableRulingOperation::DrawDiagonal {
            master_cell_id: id("cell-0-0")?,
            direction: TableRulingDiagonalDirection::Slash,
            line_sha256: digest('4'),
        },
    )?;
    let request_debug = format!("{request:?}");
    assert!(!request_debug.contains("table-private-secret"));
    assert!(!request_debug.contains("cell-0-0"));
    assert!(!request_debug.contains(&digest('4')));
    assert!(!request_debug.contains(&digest('f')));

    let plan_debug = format!("{:?}", outer_plan()?);
    assert!(!plan_debug.contains("table-created"));
    assert!(!plan_debug.contains("cell-origin"));
    assert!(!plan_debug.contains(&digest('1')));
    assert!(!plan_debug.contains(&digest('e')));
    assert!(!plan_debug.contains(&digest('f')));
    Ok(())
}
