use domain_ir::{
    CellCoordinate, FormulaAst, FormulaAstDraft, FormulaCache, FormulaCellDraft, FormulaDecimal,
    FormulaLimitConfig, FormulaLimits, FormulaNumberFormat, FormulaValue, LogicalId,
    TABLE_FORMULA_SCHEMA_VERSION, TABLE_GRID_SCHEMA_VERSION, TABLE_JOIN_TABLE_CAPABILITY_ID,
    TABLE_PARTITION_SCHEMA_VERSION, TABLE_SPLIT_TABLE_CAPABILITY_ID, TableCellSpan, TableGrid,
    TableGridDraft, TableGridLimits, TableJoinSeparatorToken, TablePartitionBuilder,
    TablePartitionCellDraft, TablePartitionError, TablePartitionFormulaPolicy,
    TablePartitionLimitConfig, TablePartitionLimits, TablePartitionState, TablePartitionStateDraft,
    WholeTableJoinRequest, WholeTableJoinRequestDraft, WholeTableSplitRequest,
    WholeTableSplitRequestDraft,
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

fn formula_limits() -> Result<FormulaLimits, Box<dyn std::error::Error>> {
    Ok(FormulaLimits::new(FormulaLimitConfig {
        rows: 10_000,
        columns: 1_024,
        ..FormulaLimitConfig::default()
    })?)
}

fn formula_draft(
    source: &str,
    owner: CellCoordinate,
    cache: FormulaCache,
) -> Result<FormulaCellDraft, Box<dyn std::error::Error>> {
    let ast = FormulaAst::parse(source, formula_limits()?)?;
    Ok(FormulaCellDraft {
        schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
        owner,
        ast: FormulaAstDraft {
            schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
            expression: ast.expression().clone(),
        },
        cache,
        number_format: FormulaNumberFormat::Number {
            decimal_places: 2,
            use_grouping: true,
        },
    })
}

fn unverified_cache() -> FormulaCache {
    FormulaCache::Unverified {
        value: FormulaValue::Decimal {
            value: FormulaDecimal::new(7, 0),
        },
    }
}

fn unmerged_grid(
    prefix: &str,
    rows: u32,
    columns: u32,
) -> Result<TableGrid, Box<dyn std::error::Error>> {
    let mut master_cells = Vec::new();
    for row in 0..rows {
        for column in 0..columns {
            master_cells.push(TableCellSpan {
                master_cell_id: id(&format!("{prefix}-{row}-{column}"))?,
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

fn state(
    grid: &TableGrid,
    table_id: &str,
    column_widths: Vec<u32>,
    formulas: &[(CellCoordinate, &str)],
) -> Result<TablePartitionState, Box<dyn std::error::Error>> {
    state_with_table_properties(grid, table_id, column_widths, formulas, 'e')
}

fn state_with_table_properties(
    grid: &TableGrid,
    table_id: &str,
    column_widths: Vec<u32>,
    formulas: &[(CellCoordinate, &str)],
    table_properties_character: char,
) -> Result<TablePartitionState, Box<dyn std::error::Error>> {
    let width = column_widths.iter().copied().sum();
    let mut cells = Vec::new();
    for (index, span) in grid.master_cells().iter().enumerate() {
        let coordinate = CellCoordinate {
            row: span.row,
            column: span.column,
        };
        let formula = formulas
            .iter()
            .find(|(owner, _)| *owner == coordinate)
            .map(|(_, source)| formula_draft(source, coordinate, unverified_cache()))
            .transpose()?;
        cells.push(TablePartitionCellDraft {
            master_cell_id: span.master_cell_id.clone(),
            coordinate,
            payload_sha256: digest(if index % 2 == 0 { 'a' } else { 'b' }),
            cell_properties_sha256: digest(if index % 2 == 0 { 'c' } else { 'd' }),
            formula,
        });
    }
    Ok(TablePartitionState::from_draft(
        TablePartitionStateDraft {
            schema_version: TABLE_PARTITION_SCHEMA_VERSION.to_owned(),
            table_id: id(table_id)?,
            grid_sha256: hex(grid.canonical_sha256()?),
            table_properties_sha256: digest(table_properties_character),
            table_width_hwpunit: width,
            column_widths_hwpunit: column_widths,
            cells,
        },
        grid,
        formula_limits()?,
        TablePartitionLimits::default(),
    )?)
}

fn split_request(
    grid: &TableGrid,
    state: &TablePartitionState,
    cursor: CellCoordinate,
    policy: TablePartitionFormulaPolicy,
) -> Result<WholeTableSplitRequest, Box<dyn std::error::Error>> {
    Ok(WholeTableSplitRequest::from_draft(
        WholeTableSplitRequestDraft {
            schema_version: TABLE_PARTITION_SCHEMA_VERSION.to_owned(),
            table_id: state.table_id().clone(),
            cursor,
            second_table_id: id("table-second")?,
            separator_paragraph_id: id("paragraph-between")?,
            expected_state_sha256: hex(state.canonical_sha256(TablePartitionLimits::default())?),
            expected_flow_sha256: digest('f'),
            formula_policy: policy,
        },
        state,
        grid,
        &digest('f'),
        TablePartitionLimits::default(),
    )?)
}

fn join_request(
    leading_grid: &TableGrid,
    leading_state: &TablePartitionState,
    trailing_grid: &TableGrid,
    trailing_state: &TablePartitionState,
    tokens: Vec<TableJoinSeparatorToken>,
    policy: TablePartitionFormulaPolicy,
) -> Result<WholeTableJoinRequest, TablePartitionError> {
    WholeTableJoinRequest::from_draft(
        WholeTableJoinRequestDraft {
            schema_version: TABLE_PARTITION_SCHEMA_VERSION.to_owned(),
            leading_table_id: leading_state.table_id().clone(),
            trailing_table_id: trailing_state.table_id().clone(),
            separator_tokens: tokens,
            expected_leading_state_sha256: hex(leading_state
                .canonical_sha256(TablePartitionLimits::default())
                .map_err(|_| TablePartitionError::StateBindingMismatch)?),
            expected_trailing_state_sha256: hex(trailing_state
                .canonical_sha256(TablePartitionLimits::default())
                .map_err(|_| TablePartitionError::StateBindingMismatch)?),
            expected_flow_sha256: digest('f'),
            formula_policy: policy,
        },
        leading_state,
        leading_grid,
        trailing_state,
        trailing_grid,
        &digest('f'),
        TablePartitionLimits::default(),
    )
}

#[test]
fn split_starts_second_table_at_cursor_row_and_preserves_complete_cells() -> TestResult {
    let grid = unmerged_grid("cell", 4, 2)?;
    let state = state(
        &grid,
        "table-main",
        vec![4_000, 6_000],
        &[
            (CellCoordinate { row: 0, column: 1 }, "SUM(A1:B2)"),
            (CellCoordinate { row: 3, column: 1 }, "SUM(A3:B4)"),
        ],
    )?;
    let request = split_request(
        &grid,
        &state,
        CellCoordinate { row: 2, column: 1 },
        TablePartitionFormulaPolicy::RebaseAndClearCache,
    )?;
    assert_eq!(request.capability_id(), TABLE_SPLIT_TABLE_CAPABILITY_ID);
    assert_eq!(request.split_before_row(), 2);

    let plan = TablePartitionBuilder::split(
        &request,
        &state,
        &grid,
        &digest('f'),
        TableGridLimits::default(),
        formula_limits()?,
        TablePartitionLimits::default(),
    )?;
    assert_eq!((plan.first().rows(), plan.first().columns()), (2, 2));
    assert_eq!((plan.second().rows(), plan.second().columns()), (2, 2));
    assert_eq!(plan.first().table_id().as_str(), "table-main");
    assert_eq!(plan.second().table_id().as_str(), "table-second");
    assert_eq!(plan.first().table_width_hwpunit(), 10_000);
    assert_eq!(plan.second().column_widths_hwpunit(), &[4_000, 6_000]);
    assert_eq!(plan.first().table_properties_sha256(), digest('e'));
    assert_eq!(plan.second().table_properties_sha256(), digest('e'));

    let second_formula = plan
        .second()
        .cells()
        .iter()
        .find_map(|cell| cell.formula())
        .ok_or_else(|| std::io::Error::other("second formula missing"))?;
    assert_eq!(second_formula.owner(), CellCoordinate { row: 1, column: 1 });
    assert_eq!(
        second_formula.ast().canonical_formula(formula_limits()?)?,
        "SUM(A1:B2)"
    );
    assert_eq!(second_formula.cache(), &FormulaCache::Absent);
    assert_eq!(plan.receipt().preserved_master_cell_count, 8);
    assert_eq!(plan.receipt().preserved_payload_count, 8);
    assert_eq!(plan.receipt().preserved_cell_properties_count, 8);
    assert_eq!(plan.receipt().formula_rebased_count, 2);
    assert_eq!(plan.receipt().formula_cache_cleared_count, 2);
    assert_eq!(plan.receipt().inherited_table_properties_count, 2);
    assert_eq!(plan.receipt().created_table_count, 1);
    assert_eq!(plan.receipt().created_separator_paragraph_count, 1);
    assert_ne!(
        plan.receipt().before_flow_sha256,
        plan.receipt().after_flow_sha256
    );
    Ok(())
}

#[test]
fn split_rejects_first_row_out_of_bounds_and_stale_state() -> TestResult {
    let grid = unmerged_grid("cell", 3, 2)?;
    let state = state(&grid, "table-main", vec![5_000, 5_000], &[])?;
    let base = WholeTableSplitRequestDraft {
        schema_version: TABLE_PARTITION_SCHEMA_VERSION.to_owned(),
        table_id: state.table_id().clone(),
        cursor: CellCoordinate { row: 0, column: 1 },
        second_table_id: id("table-second")?,
        separator_paragraph_id: id("paragraph-between")?,
        expected_state_sha256: hex(state.canonical_sha256(TablePartitionLimits::default())?),
        expected_flow_sha256: digest('f'),
        formula_policy: TablePartitionFormulaPolicy::Reject,
    };
    assert_eq!(
        WholeTableSplitRequest::from_draft(
            base.clone(),
            &state,
            &grid,
            &digest('f'),
            TablePartitionLimits::default()
        ),
        Err(TablePartitionError::FirstRowSplit)
    );
    let mut out_of_bounds = base.clone();
    out_of_bounds.cursor = CellCoordinate { row: 3, column: 0 };
    assert_eq!(
        WholeTableSplitRequest::from_draft(
            out_of_bounds,
            &state,
            &grid,
            &digest('f'),
            TablePartitionLimits::default()
        ),
        Err(TablePartitionError::CursorOutOfBounds)
    );
    let mut valid = base.clone();
    valid.cursor.row = 1;
    assert_eq!(
        WholeTableSplitRequest::from_draft(
            valid.clone(),
            &state,
            &grid,
            &digest('e'),
            TablePartitionLimits::default()
        ),
        Err(TablePartitionError::FlowBindingMismatch)
    );
    let request = WholeTableSplitRequest::from_draft(
        valid,
        &state,
        &grid,
        &digest('f'),
        TablePartitionLimits::default(),
    )?;
    assert_eq!(
        TablePartitionBuilder::split(
            &request,
            &state,
            &grid,
            &digest('e'),
            TableGridLimits::default(),
            formula_limits()?,
            TablePartitionLimits::default(),
        ),
        Err(TablePartitionError::FlowBindingMismatch)
    );
    let mut drifted_request = base;
    drifted_request.cursor.row = 1;
    drifted_request.expected_state_sha256 = digest('a');
    assert_eq!(
        WholeTableSplitRequest::from_draft(
            drifted_request,
            &state,
            &grid,
            &digest('f'),
            TablePartitionLimits::default()
        ),
        Err(TablePartitionError::StateBindingMismatch)
    );
    Ok(())
}

#[test]
fn split_rejects_a_merged_cell_crossing_the_row_boundary() -> TestResult {
    let grid = TableGrid::new(
        3,
        2,
        vec![
            TableCellSpan {
                master_cell_id: id("merged")?,
                row: 0,
                column: 0,
                row_span: 2,
                column_span: 1,
            },
            TableCellSpan {
                master_cell_id: id("a")?,
                row: 0,
                column: 1,
                row_span: 1,
                column_span: 1,
            },
            TableCellSpan {
                master_cell_id: id("b")?,
                row: 1,
                column: 1,
                row_span: 1,
                column_span: 1,
            },
            TableCellSpan {
                master_cell_id: id("c")?,
                row: 2,
                column: 0,
                row_span: 1,
                column_span: 1,
            },
            TableCellSpan {
                master_cell_id: id("d")?,
                row: 2,
                column: 1,
                row_span: 1,
                column_span: 1,
            },
        ],
        TableGridLimits::default(),
    )?;
    let state = state(&grid, "table-main", vec![5_000, 5_000], &[])?;
    assert_eq!(
        WholeTableSplitRequest::from_draft(
            WholeTableSplitRequestDraft {
                schema_version: TABLE_PARTITION_SCHEMA_VERSION.to_owned(),
                table_id: state.table_id().clone(),
                cursor: CellCoordinate { row: 1, column: 1 },
                second_table_id: id("table-second")?,
                separator_paragraph_id: id("paragraph-between")?,
                expected_state_sha256: hex(state.canonical_sha256(TablePartitionLimits::default())?),
                expected_flow_sha256: digest('f'),
                formula_policy: TablePartitionFormulaPolicy::Reject,
            },
            &state,
            &grid,
            &digest('f'),
            TablePartitionLimits::default(),
        ),
        Err(TablePartitionError::SpanBoundaryConflict)
    );
    Ok(())
}

#[test]
fn split_rejects_cross_table_formula_references_without_partial_output() -> TestResult {
    let grid = unmerged_grid("cell", 4, 2)?;
    let state = state(
        &grid,
        "table-main",
        vec![5_000, 5_000],
        &[(CellCoordinate { row: 0, column: 0 }, "SUM(A1:A4)")],
    )?;
    let request = split_request(
        &grid,
        &state,
        CellCoordinate { row: 2, column: 0 },
        TablePartitionFormulaPolicy::RebaseAndClearCache,
    )?;
    assert_eq!(
        TablePartitionBuilder::split(
            &request,
            &state,
            &grid,
            &digest('f'),
            TableGridLimits::default(),
            formula_limits()?,
            TablePartitionLimits::default(),
        ),
        Err(TablePartitionError::FormulaCrossBoundary)
    );
    Ok(())
}

#[test]
fn reject_formula_policy_fails_before_a_split_request_exists() -> TestResult {
    let grid = unmerged_grid("cell", 2, 2)?;
    let state = state(
        &grid,
        "table-main",
        vec![5_000, 5_000],
        &[(CellCoordinate { row: 0, column: 0 }, "A1")],
    )?;
    assert_eq!(
        WholeTableSplitRequest::from_draft(
            WholeTableSplitRequestDraft {
                schema_version: TABLE_PARTITION_SCHEMA_VERSION.to_owned(),
                table_id: state.table_id().clone(),
                cursor: CellCoordinate { row: 1, column: 0 },
                second_table_id: id("table-second")?,
                separator_paragraph_id: id("paragraph-between")?,
                expected_state_sha256: hex(state.canonical_sha256(TablePartitionLimits::default())?),
                expected_flow_sha256: digest('f'),
                formula_policy: TablePartitionFormulaPolicy::Reject,
            },
            &state,
            &grid,
            &digest('f'),
            TablePartitionLimits::default(),
        ),
        Err(TablePartitionError::FormulaPresent)
    );
    Ok(())
}

#[test]
fn join_builds_common_column_lattice_uses_larger_width_and_leading_properties() -> TestResult {
    let leading_grid = unmerged_grid("lead", 2, 2)?;
    let trailing_grid = unmerged_grid("trail", 2, 3)?;
    let leading_state = state(
        &leading_grid,
        "table-leading",
        vec![50, 50],
        &[(CellCoordinate { row: 0, column: 1 }, "$B$1")],
    )?;
    let trailing_state = state_with_table_properties(
        &trailing_grid,
        "table-trailing",
        vec![40, 40, 40],
        &[(CellCoordinate { row: 0, column: 1 }, "$B$1")],
        'f',
    )?;
    let request = join_request(
        &leading_grid,
        &leading_state,
        &trailing_grid,
        &trailing_state,
        vec![
            TableJoinSeparatorToken::SpaceRun { count: 3 },
            TableJoinSeparatorToken::ParagraphBreak,
        ],
        TablePartitionFormulaPolicy::RebaseAndClearCache,
    )?;
    assert_eq!(request.capability_id(), TABLE_JOIN_TABLE_CAPABILITY_ID);
    let plan = TablePartitionBuilder::join(
        &request,
        &leading_state,
        &leading_grid,
        &trailing_state,
        &trailing_grid,
        &digest('f'),
        TableGridLimits::default(),
        formula_limits()?,
        TablePartitionLimits::default(),
    )?;
    assert_eq!((plan.joined().rows(), plan.joined().columns()), (4, 4));
    assert_eq!(plan.joined().table_width_hwpunit(), 120);
    assert_eq!(plan.joined().column_widths_hwpunit(), &[40, 20, 20, 40]);
    assert_eq!(
        plan.joined().table_properties_sha256(),
        leading_state.table_properties_sha256()
    );
    let leading_formula = plan
        .joined()
        .cells()
        .iter()
        .find(|cell| cell.master_cell_id().as_str() == "lead-0-1")
        .and_then(|cell| cell.formula())
        .ok_or_else(|| std::io::Error::other("leading formula missing"))?;
    assert_eq!(
        leading_formula.owner(),
        CellCoordinate { row: 0, column: 2 }
    );
    assert_eq!(
        leading_formula.ast().canonical_formula(formula_limits()?)?,
        "$C$1"
    );
    let trailing_formula = plan
        .joined()
        .cells()
        .iter()
        .find(|cell| cell.master_cell_id().as_str() == "trail-0-1")
        .and_then(|cell| cell.formula())
        .ok_or_else(|| std::io::Error::other("trailing formula missing"))?;
    assert_eq!(
        trailing_formula.owner(),
        CellCoordinate { row: 2, column: 1 }
    );
    assert_eq!(
        trailing_formula
            .ast()
            .canonical_formula(formula_limits()?)?,
        "$B$3"
    );
    assert_eq!(trailing_formula.cache(), &FormulaCache::Absent);
    assert_eq!(plan.receipt().joined_width_hwpunit, 120);
    assert_eq!(plan.receipt().preserved_master_cell_count, 10);
    assert_eq!(plan.receipt().formula_rebased_count, 2);
    assert_eq!(plan.receipt().formula_cache_cleared_count, 2);
    assert!(plan.receipt().leading_table_properties_retained);
    assert!(plan.receipt().trailing_table_properties_discarded);
    assert_eq!(plan.receipt().removed_table_count, 1);
    assert_eq!(plan.receipt().removed_separator_token_count, 2);
    Ok(())
}

#[test]
fn join_rejects_non_whitespace_missing_break_and_empty_space_tokens() -> TestResult {
    let leading_grid = unmerged_grid("lead", 1, 1)?;
    let trailing_grid = unmerged_grid("trail", 1, 1)?;
    let leading_state = state(&leading_grid, "leading", vec![100], &[])?;
    let trailing_state = state(&trailing_grid, "trailing", vec![100], &[])?;
    assert_eq!(
        join_request(
            &leading_grid,
            &leading_state,
            &trailing_grid,
            &trailing_state,
            vec![TableJoinSeparatorToken::Content {
                content_sha256: digest('a'),
            }],
            TablePartitionFormulaPolicy::Reject,
        ),
        Err(TablePartitionError::InterveningContent)
    );
    assert_eq!(
        join_request(
            &leading_grid,
            &leading_state,
            &trailing_grid,
            &trailing_state,
            vec![TableJoinSeparatorToken::SpaceRun { count: 1 }],
            TablePartitionFormulaPolicy::Reject,
        ),
        Err(TablePartitionError::MissingParagraphBreak)
    );
    assert_eq!(
        join_request(
            &leading_grid,
            &leading_state,
            &trailing_grid,
            &trailing_state,
            vec![
                TableJoinSeparatorToken::SpaceRun { count: 0 },
                TableJoinSeparatorToken::ParagraphBreak,
            ],
            TablePartitionFormulaPolicy::Reject,
        ),
        Err(TablePartitionError::EmptySeparatorToken)
    );
    Ok(())
}

#[test]
fn join_rejects_duplicate_master_identity_and_formula_reject_policy() -> TestResult {
    let leading_grid = unmerged_grid("same", 1, 1)?;
    let trailing_grid = unmerged_grid("same", 1, 1)?;
    let leading_state = state(&leading_grid, "leading", vec![100], &[])?;
    let trailing_state = state(&trailing_grid, "trailing", vec![100], &[])?;
    assert_eq!(
        join_request(
            &leading_grid,
            &leading_state,
            &trailing_grid,
            &trailing_state,
            vec![TableJoinSeparatorToken::ParagraphBreak],
            TablePartitionFormulaPolicy::Reject,
        ),
        Err(TablePartitionError::DuplicateMasterCell)
    );

    let formula_grid = unmerged_grid("formula", 1, 1)?;
    let formula_state = state(
        &formula_grid,
        "formula-table",
        vec![100],
        &[(CellCoordinate { row: 0, column: 0 }, "A1")],
    )?;
    assert_eq!(
        join_request(
            &leading_grid,
            &leading_state,
            &formula_grid,
            &formula_state,
            vec![TableJoinSeparatorToken::ParagraphBreak],
            TablePartitionFormulaPolicy::Reject,
        ),
        Err(TablePartitionError::FormulaPresent)
    );
    Ok(())
}

#[test]
fn state_rejects_inexact_column_geometry_cell_sets_and_formula_owners() -> TestResult {
    let grid = unmerged_grid("cell", 1, 2)?;
    let mut draft = TablePartitionStateDraft {
        schema_version: TABLE_PARTITION_SCHEMA_VERSION.to_owned(),
        table_id: id("table")?,
        grid_sha256: hex(grid.canonical_sha256()?),
        table_properties_sha256: digest('a'),
        table_width_hwpunit: 100,
        column_widths_hwpunit: vec![40, 50],
        cells: grid
            .master_cells()
            .iter()
            .map(|span| TablePartitionCellDraft {
                master_cell_id: span.master_cell_id.clone(),
                coordinate: CellCoordinate {
                    row: span.row,
                    column: span.column,
                },
                payload_sha256: digest('b'),
                cell_properties_sha256: digest('c'),
                formula: None,
            })
            .collect(),
    };
    assert_eq!(
        TablePartitionState::from_draft(
            draft.clone(),
            &grid,
            formula_limits()?,
            TablePartitionLimits::default(),
        ),
        Err(TablePartitionError::ColumnGeometryMismatch)
    );
    draft.column_widths_hwpunit = vec![40, 60];
    draft.cells.pop();
    assert_eq!(
        TablePartitionState::from_draft(
            draft.clone(),
            &grid,
            formula_limits()?,
            TablePartitionLimits::default(),
        ),
        Err(TablePartitionError::CellSetMismatch)
    );
    draft.cells.push(TablePartitionCellDraft {
        master_cell_id: grid.master_cells()[1].master_cell_id.clone(),
        coordinate: CellCoordinate { row: 0, column: 1 },
        payload_sha256: digest('b'),
        cell_properties_sha256: digest('c'),
        formula: Some(formula_draft(
            "A1",
            CellCoordinate { row: 0, column: 0 },
            FormulaCache::Absent,
        )?),
    });
    assert_eq!(
        TablePartitionState::from_draft(
            draft,
            &grid,
            formula_limits()?,
            TablePartitionLimits::default(),
        ),
        Err(TablePartitionError::FormulaOwnerMismatch)
    );
    Ok(())
}

#[test]
fn common_column_lattice_fails_closed_when_hwpunit_rounding_collapses_a_track() -> TestResult {
    let leading_grid = unmerged_grid("lead", 1, 2)?;
    let trailing_grid = unmerged_grid("trail", 1, 3)?;
    let leading_state = state(&leading_grid, "leading", vec![1, 1], &[])?;
    let trailing_state = state(&trailing_grid, "trailing", vec![1, 1, 1], &[])?;
    let request = join_request(
        &leading_grid,
        &leading_state,
        &trailing_grid,
        &trailing_state,
        vec![TableJoinSeparatorToken::ParagraphBreak],
        TablePartitionFormulaPolicy::Reject,
    )?;
    assert_eq!(
        TablePartitionBuilder::join(
            &request,
            &leading_state,
            &leading_grid,
            &trailing_state,
            &trailing_grid,
            &digest('f'),
            TableGridLimits::default(),
            formula_limits()?,
            TablePartitionLimits::default(),
        ),
        Err(TablePartitionError::ColumnGeometryUnrepresentable)
    );
    Ok(())
}

#[test]
fn bounded_json_and_limits_fail_closed() -> TestResult {
    let grid = unmerged_grid("cell", 2, 1)?;
    let state = state(&grid, "table", vec![100], &[])?;
    assert_eq!(
        TablePartitionState::from_json(
            b"{}",
            &grid,
            formula_limits()?,
            TablePartitionLimits::default(),
        ),
        Err(TablePartitionError::InvalidJson)
    );
    let limits = TablePartitionLimits::new(TablePartitionLimitConfig {
        input_bytes: 8,
        ..TablePartitionLimitConfig::default()
    })?;
    assert_eq!(
        TablePartitionState::from_json(br#"{"too":"large"}"#, &grid, formula_limits()?, limits,),
        Err(TablePartitionError::InputLimit)
    );
    assert_eq!(
        TablePartitionLimits::new(TablePartitionLimitConfig {
            separator_tokens: 0,
            ..TablePartitionLimitConfig::default()
        }),
        Err(TablePartitionError::InvalidLimit)
    );
    assert!(
        !state
            .canonical_json(TablePartitionLimits::default())?
            .is_empty()
    );
    Ok(())
}

#[test]
fn canonical_state_is_order_independent_and_debug_redacts_sensitive_values() -> TestResult {
    let grid = unmerged_grid("secret-cell", 2, 2)?;
    let state = state(&grid, "secret-table", vec![50, 50], &[])?;
    let mut draft: TablePartitionStateDraft =
        serde_json::from_slice(&state.canonical_json(TablePartitionLimits::default())?)?;
    draft.cells.reverse();
    let reordered = TablePartitionState::from_draft(
        draft,
        &grid,
        formula_limits()?,
        TablePartitionLimits::default(),
    )?;
    assert_eq!(
        state.canonical_json(TablePartitionLimits::default())?,
        reordered.canonical_json(TablePartitionLimits::default())?
    );
    let debug = format!("{state:?}");
    assert!(!debug.contains("secret-table"));
    assert!(!debug.contains("secret-cell"));
    assert!(!debug.contains(&digest('a')));
    assert!(debug.contains("<redacted>"));
    Ok(())
}

#[test]
fn error_codes_are_stable_and_distinct_for_primary_boundaries() {
    let errors = [
        TablePartitionError::FirstRowSplit,
        TablePartitionError::SpanBoundaryConflict,
        TablePartitionError::FormulaCrossBoundary,
        TablePartitionError::InterveningContent,
        TablePartitionError::MissingParagraphBreak,
        TablePartitionError::ColumnGeometryUnrepresentable,
        TablePartitionError::StateBindingMismatch,
        TablePartitionError::FlowBindingMismatch,
    ];
    let codes = errors.map(TablePartitionError::code);
    let unique: std::collections::HashSet<_> = codes.into_iter().collect();
    assert_eq!(unique.len(), errors.len());
    assert_eq!(
        TablePartitionError::FirstRowSplit.code(),
        "table_partition_first_row_split"
    );
}
