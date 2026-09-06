use domain_ir::{
    CellCoordinate, LogicalId, TABLE_GRID_SCHEMA_VERSION, TableCellSpan, TableGrid, TableGridDraft,
    TableGridError, TableGridLimitConfig, TableGridLimits,
};

type TestResult = Result<(), Box<dyn std::error::Error>>;

fn cell(
    identifier: &str,
    row: u32,
    column: u32,
    row_span: u32,
    column_span: u32,
) -> Result<TableCellSpan, TableGridError> {
    let master_cell_id = LogicalId::parse(identifier).map_err(|_| TableGridError::InvalidJson)?;
    Ok(TableCellSpan {
        master_cell_id,
        row,
        column,
        row_span,
        column_span,
    })
}

fn grid_2x3() -> Result<TableGrid, TableGridError> {
    TableGrid::new(
        2,
        3,
        vec![
            cell("bottom-right", 1, 2, 1, 1)?,
            cell("left", 0, 0, 2, 1)?,
            cell("top-right", 0, 1, 1, 2)?,
            cell("bottom-middle", 1, 1, 1, 1)?,
        ],
        TableGridLimits::default(),
    )
}

#[test]
fn maps_every_slot_to_one_canonical_master() -> TestResult {
    let grid = grid_2x3()?;
    assert_eq!(grid.rows(), 2);
    assert_eq!(grid.columns(), 3);
    assert_eq!(grid.slot_count(), 6);
    assert_eq!(grid.master_cell_count(), 4);
    assert_eq!(
        grid.master_cell_at(CellCoordinate { row: 1, column: 0 })?
            .master_cell_id
            .as_str(),
        "left"
    );
    assert_eq!(
        grid.master_cell_at(CellCoordinate { row: 0, column: 2 })?
            .master_cell_id
            .as_str(),
        "top-right"
    );
    assert_eq!(
        grid.master_cell_at(CellCoordinate { row: 1, column: 1 })?
            .master_cell_id
            .as_str(),
        "bottom-middle"
    );
    assert_eq!(
        grid.master_cell_at(CellCoordinate { row: 2, column: 0 }),
        Err(TableGridError::CoordinateOutOfBounds)
    );
    assert!(!format!("{grid:?}").contains("bottom-right"));
    Ok(())
}

#[test]
fn canonical_json_is_order_independent_and_roundtrips() -> TestResult {
    let grid = grid_2x3()?;
    let canonical = grid.canonical_json()?;
    let reparsed = TableGrid::from_json(&canonical, TableGridLimits::default())?;
    assert_eq!(reparsed, grid);
    assert_eq!(reparsed.canonical_json()?, canonical);
    assert_eq!(reparsed.canonical_sha256()?, grid.canonical_sha256()?);

    let text = std::str::from_utf8(&canonical)?;
    assert!(text.starts_with(concat!(
        r#"{"schema_version":"hwpx-agent.table-grid/v1","rows":2,"columns":3,"master_cells":["#,
        r#"{"master_cell_id":"left","row":0,"column":0,"row_span":2,"column_span":1}"#
    )));
    assert!(text.ends_with(
        r#"{"master_cell_id":"bottom-right","row":1,"column":2,"row_span":1,"column_span":1}]}"#
    ));
    Ok(())
}

#[test]
fn explicit_coverage_requires_one_complete_rectangle() -> TestResult {
    let rectangle = TableCellSpan::from_covered_slots(
        LogicalId::parse("rect")?,
        vec![
            CellCoordinate { row: 3, column: 5 },
            CellCoordinate { row: 2, column: 4 },
            CellCoordinate { row: 3, column: 4 },
            CellCoordinate { row: 2, column: 5 },
        ],
        TableGridLimits::default(),
    )?;
    assert_eq!((rectangle.row, rectangle.column), (2, 4));
    assert_eq!((rectangle.row_span, rectangle.column_span), (2, 2));

    let l_shape = TableCellSpan::from_covered_slots(
        LogicalId::parse("l-shape")?,
        vec![
            CellCoordinate { row: 0, column: 0 },
            CellCoordinate { row: 0, column: 1 },
            CellCoordinate { row: 1, column: 0 },
        ],
        TableGridLimits::default(),
    );
    assert_eq!(l_shape, Err(TableGridError::NonRectangularSpan));

    let diagonal = TableCellSpan::from_covered_slots(
        LogicalId::parse("diagonal")?,
        vec![
            CellCoordinate { row: 0, column: 5 },
            CellCoordinate { row: 1, column: 4 },
        ],
        TableGridLimits::default(),
    );
    assert_eq!(diagonal, Err(TableGridError::NonRectangularSpan));

    let duplicate = TableCellSpan::from_covered_slots(
        LogicalId::parse("duplicate")?,
        vec![
            CellCoordinate { row: 0, column: 0 },
            CellCoordinate { row: 0, column: 0 },
        ],
        TableGridLimits::default(),
    );
    assert_eq!(duplicate, Err(TableGridError::DuplicateCoveredSlot));
    assert_eq!(
        TableCellSpan::from_covered_slots(
            LogicalId::parse("empty")?,
            Vec::new(),
            TableGridLimits::default(),
        ),
        Err(TableGridError::EmptySpan)
    );
    Ok(())
}

#[test]
fn gaps_overlaps_bounds_and_identifiers_fail_closed() -> TestResult {
    let limits = TableGridLimits::default();
    assert_eq!(
        TableGrid::new(1, 2, vec![cell("only", 0, 0, 1, 1)?], limits),
        Err(TableGridError::UncoveredSlot)
    );
    assert_eq!(
        TableGrid::new(
            1,
            2,
            vec![cell("wide", 0, 0, 1, 2)?, cell("overlap", 0, 1, 1, 1)?],
            limits,
        ),
        Err(TableGridError::OverlappingSpan)
    );
    assert_eq!(
        TableGrid::new(1, 1, vec![cell("outside", 0, 0, 1, 2)?], limits),
        Err(TableGridError::SpanOutOfBounds)
    );
    assert_eq!(
        TableGrid::new(1, 1, vec![cell("empty", 0, 0, 0, 1)?], limits),
        Err(TableGridError::EmptySpan)
    );
    assert_eq!(
        TableGrid::new(1, 1, vec![cell("overflow", u32::MAX, 0, 2, 1)?], limits,),
        Err(TableGridError::SpanOverflow)
    );
    assert_eq!(
        TableGrid::new(
            1,
            2,
            vec![cell("same", 0, 0, 1, 1)?, cell("same", 0, 1, 1, 1)?],
            limits,
        ),
        Err(TableGridError::DuplicateMasterCell)
    );
    Ok(())
}

#[test]
fn version_json_and_limits_are_strict() -> TestResult {
    let limits = TableGridLimits::default();
    assert_eq!(
        TableGrid::from_draft(
            TableGridDraft {
                schema_version: "hwpx-agent.table-grid/v0".to_owned(),
                rows: 1,
                columns: 1,
                master_cells: vec![cell("one", 0, 0, 1, 1)?],
            },
            limits,
        ),
        Err(TableGridError::UnsupportedVersion)
    );
    assert_eq!(
        TableGrid::from_json(br#"{"schema_version":"hwpx-agent.table-grid/v1"}"#, limits),
        Err(TableGridError::InvalidJson)
    );
    assert_eq!(
        TableGrid::new(0, 1, Vec::new(), limits),
        Err(TableGridError::EmptyGrid)
    );
    assert_eq!(
        TableGrid::new(10_001, 1, vec![cell("oversized", 0, 0, 10_001, 1)?], limits,),
        Err(TableGridError::DimensionLimitExceeded)
    );
    assert_eq!(
        TableGrid::new(
            1_000,
            1_001,
            vec![cell("too-many-slots", 0, 0, 1_000, 1_001)?],
            limits,
        ),
        Err(TableGridError::SlotLimitExceeded)
    );
    assert_eq!(
        TableGrid::new(1, 1, vec![cell(&"x".repeat(257), 0, 0, 1, 1)?], limits,),
        Err(TableGridError::IdentifierLimitExceeded)
    );
    let tiny = TableGridLimits::new(TableGridLimitConfig {
        rows: 2,
        columns: 2,
        slots: 4,
        master_cells: 4,
        identifier_bytes: 16,
        serialized_bytes: 32,
    })?;
    assert_eq!(
        TableGrid::new(1, 1, vec![cell("one", 0, 0, 1, 1)?], tiny),
        Err(TableGridError::OutputLimitExceeded)
    );
    assert_eq!(
        TableGrid::from_json(&[b' '; 33], tiny),
        Err(TableGridError::InputLimitExceeded)
    );
    let one_master = TableGridLimits::new(TableGridLimitConfig {
        rows: 1,
        columns: 2,
        slots: 2,
        master_cells: 1,
        identifier_bytes: 16,
        serialized_bytes: 1_024,
    })?;
    assert_eq!(
        TableGrid::new(
            1,
            2,
            vec![cell("left", 0, 0, 1, 1)?, cell("right", 0, 1, 1, 1)?],
            one_master,
        ),
        Err(TableGridError::MasterCellLimitExceeded)
    );
    assert_eq!(
        TableGridLimits::new(TableGridLimitConfig {
            rows: 1,
            columns: 1,
            slots: 1,
            master_cells: 2,
            identifier_bytes: 16,
            serialized_bytes: 128,
        }),
        Err(TableGridError::InvalidLimit)
    );
    assert_eq!(
        TableGridError::NonRectangularSpan.code(),
        "table_grid_non_rectangular_span"
    );
    Ok(())
}

#[test]
fn fixed_seed_partition_corpus_preserves_all_grid_properties() -> TestResult {
    for seed in 0_u64..256 {
        let mut state = seed ^ 0x9e37_79b9_7f4a_7c15;
        let rows = 1 + u32::try_from(next(&mut state) % 12)?;
        let columns = 1 + u32::try_from(next(&mut state) % 12)?;
        let row_parts = partitions(rows, &mut state);
        let column_parts = partitions(columns, &mut state);
        let mut master_cells = Vec::new();
        let mut row = 0;
        for row_span in &row_parts {
            let mut column = 0;
            for column_span in &column_parts {
                master_cells.push(cell(
                    &format!("cell-{seed}-{row}-{column}"),
                    row,
                    column,
                    *row_span,
                    *column_span,
                )?);
                column = column.checked_add(*column_span).ok_or("column overflow")?;
            }
            row = row.checked_add(*row_span).ok_or("row overflow")?;
        }
        shuffle(&mut master_cells, &mut state);
        let grid = TableGrid::new(rows, columns, master_cells, TableGridLimits::default())?;

        assert_eq!(grid.slot_count(), usize::try_from(rows * columns)?);
        for slot_row in 0..rows {
            for slot_column in 0..columns {
                let coordinate = CellCoordinate {
                    row: slot_row,
                    column: slot_column,
                };
                assert!(grid.master_cell_at(coordinate)?.covers(coordinate));
            }
        }
        let canonical = grid.canonical_json()?;
        let reparsed = TableGrid::from_json(&canonical, TableGridLimits::default())?;
        assert_eq!(reparsed, grid);
        assert_eq!(reparsed.canonical_json()?, canonical);
    }
    Ok(())
}

fn next(state: &mut u64) -> u64 {
    *state = state
        .wrapping_mul(6_364_136_223_846_793_005)
        .wrapping_add(1_442_695_040_888_963_407);
    *state
}

fn partitions(total: u32, state: &mut u64) -> Vec<u32> {
    let mut remaining = total;
    let mut result = Vec::new();
    while remaining > 0 {
        let width = 1 + u32::try_from(next(state) % u64::from(remaining.min(4))).unwrap_or(1);
        result.push(width);
        remaining -= width;
    }
    result
}

fn shuffle(values: &mut [TableCellSpan], state: &mut u64) {
    for index in (1..values.len()).rev() {
        let upper_bound = u64::try_from(index + 1).unwrap_or(1);
        let selected = usize::try_from(next(state) % upper_bound).unwrap_or(0);
        values.swap(index, selected);
    }
}

#[test]
fn contract_version_is_exact() {
    assert_eq!(TABLE_GRID_SCHEMA_VERSION, "hwpx-agent.table-grid/v1");
}
