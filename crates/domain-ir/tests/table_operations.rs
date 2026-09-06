use std::error::Error;

use domain_ir::{
    CellCoordinate, LogicalId, TABLE_OPERATIONS_SCHEMA_VERSION, TableCellSpan, TableDimensions,
    TableGrid, TableGridError, TableGridLimits, TableOperationError, TableOperationKind,
};

type TestResult<T = ()> = Result<T, Box<dyn Error>>;

fn logical_ids(prefix: &str, count: usize) -> TestResult<Vec<LogicalId>> {
    (0..count)
        .map(|index| LogicalId::parse(format!("{prefix}-{index}")).map_err(Into::into))
        .collect()
}

fn unmerged(rows: u32, columns: u32, prefix: &str) -> TestResult<TableGrid> {
    let count = usize::try_from(rows)?
        .checked_mul(usize::try_from(columns)?)
        .ok_or("slot overflow")?;
    let result = TableGrid::create_unmerged(
        rows,
        columns,
        logical_ids(prefix, count)?,
        TableGridLimits::default(),
    )?;
    Ok(result.into_parts().0)
}

fn id_at(grid: &TableGrid, row: u32, column: u32) -> TestResult<&str> {
    Ok(grid
        .master_cell_at(CellCoordinate { row, column })?
        .master_cell_id
        .as_str())
}

#[test]
fn creates_unmerged_grid_from_exact_row_major_identifiers() -> TestResult {
    let result =
        TableGrid::create_unmerged(2, 3, logical_ids("create", 6)?, TableGridLimits::default())?;
    assert_eq!(result.grid().rows(), 2);
    assert_eq!(result.grid().columns(), 3);
    assert_eq!(id_at(result.grid(), 0, 0)?, "create-0");
    assert_eq!(id_at(result.grid(), 1, 2)?, "create-5");
    assert_eq!(
        result.receipt().schema_version(),
        TABLE_OPERATIONS_SCHEMA_VERSION
    );
    assert_eq!(result.receipt().operation(), TableOperationKind::Create);
    assert_eq!(result.receipt().before(), None);
    assert_eq!(
        result.receipt().after(),
        TableDimensions {
            rows: 2,
            columns: 3
        }
    );
    assert_eq!(result.receipt().inserted_master_cell_ids().len(), 6);
    assert!(!format!("{:?}", result.receipt()).contains("create-0"));
    Ok(())
}

#[test]
fn receipt_serialization_is_repeatable_and_canonically_ordered() -> TestResult {
    let result =
        TableGrid::create_unmerged(2, 2, logical_ids("receipt", 4)?, TableGridLimits::default())?;
    let first = serde_json::to_vec(result.receipt())?;
    let second = serde_json::to_vec(result.receipt())?;
    assert_eq!(first, second);

    let value: serde_json::Value = serde_json::from_slice(&first)?;
    assert_eq!(value["schema_version"], TABLE_OPERATIONS_SCHEMA_VERSION);
    assert_eq!(value["inserted_master_cell_ids"][0], "receipt-0");
    assert_eq!(value["inserted_master_cell_ids"][3], "receipt-3");
    Ok(())
}

#[test]
fn inserts_rows_and_columns_with_deterministic_identity_remaps() -> TestResult {
    let original = unmerged(2, 2, "old")?;
    let rows =
        original.insert_rows(1, 1, logical_ids("new-row", 2)?, TableGridLimits::default())?;
    assert_eq!((rows.grid().rows(), rows.grid().columns()), (3, 2));
    assert_eq!(id_at(rows.grid(), 0, 1)?, "old-1");
    assert_eq!(id_at(rows.grid(), 1, 0)?, "new-row-0");
    assert_eq!(id_at(rows.grid(), 2, 1)?, "old-3");
    assert_eq!(rows.receipt().operation(), TableOperationKind::InsertRows);
    assert_eq!(rows.receipt().preserved_master_cells().len(), 4);
    assert_eq!(rows.receipt().inserted_master_cell_ids().len(), 2);
    let moved = rows
        .receipt()
        .preserved_master_cells()
        .iter()
        .find(|entry| entry.master_cell_id().as_str() == "old-2")
        .ok_or("missing remap")?;
    assert_eq!(moved.before(), CellCoordinate { row: 1, column: 0 });
    assert_eq!(moved.after(), CellCoordinate { row: 2, column: 0 });

    let columns = rows.grid().insert_columns(
        0,
        1,
        logical_ids("new-column", 3)?,
        TableGridLimits::default(),
    )?;
    assert_eq!((columns.grid().rows(), columns.grid().columns()), (3, 3));
    assert_eq!(id_at(columns.grid(), 0, 0)?, "new-column-0");
    assert_eq!(id_at(columns.grid(), 2, 2)?, "old-3");
    assert_eq!(
        columns.receipt().operation(),
        TableOperationKind::InsertColumns
    );
    Ok(())
}

#[test]
fn insertion_inside_an_existing_span_fails_without_mutating_source() -> TestResult {
    let merged = TableGrid::new(
        2,
        2,
        vec![
            TableCellSpan {
                master_cell_id: LogicalId::parse("left")?,
                row: 0,
                column: 0,
                row_span: 2,
                column_span: 1,
            },
            TableCellSpan {
                master_cell_id: LogicalId::parse("top-right")?,
                row: 0,
                column: 1,
                row_span: 1,
                column_span: 1,
            },
            TableCellSpan {
                master_cell_id: LogicalId::parse("bottom-right")?,
                row: 1,
                column: 1,
                row_span: 1,
                column_span: 1,
            },
        ],
        TableGridLimits::default(),
    )?;
    let before = merged.canonical_sha256()?;
    assert_eq!(
        merged.insert_rows(1, 1, logical_ids("blocked", 2)?, TableGridLimits::default(),),
        Err(TableOperationError::SpanBoundaryConflict)
    );
    assert_eq!(merged.canonical_sha256()?, before);

    let appended = merged.insert_rows(
        2,
        1,
        logical_ids("appended", 2)?,
        TableGridLimits::default(),
    )?;
    assert_eq!(id_at(appended.grid(), 2, 1)?, "appended-1");
    assert_eq!(merged.canonical_sha256()?, before);

    let horizontal = TableGrid::new(
        2,
        2,
        vec![
            TableCellSpan {
                master_cell_id: LogicalId::parse("top")?,
                row: 0,
                column: 0,
                row_span: 1,
                column_span: 2,
            },
            TableCellSpan {
                master_cell_id: LogicalId::parse("bottom-left")?,
                row: 1,
                column: 0,
                row_span: 1,
                column_span: 1,
            },
            TableCellSpan {
                master_cell_id: LogicalId::parse("bottom-right")?,
                row: 1,
                column: 1,
                row_span: 1,
                column_span: 1,
            },
        ],
        TableGridLimits::default(),
    )?;
    assert_eq!(
        horizontal.insert_columns(
            1,
            1,
            logical_ids("blocked-column", 2)?,
            TableGridLimits::default(),
        ),
        Err(TableOperationError::SpanBoundaryConflict)
    );
    Ok(())
}

#[test]
fn deletes_complete_rows_and_columns_and_preserves_survivor_ids() -> TestResult {
    let original = unmerged(3, 3, "cell")?;
    let rows = original.delete_rows(1, 1, TableGridLimits::default())?;
    assert_eq!((rows.grid().rows(), rows.grid().columns()), (2, 3));
    assert_eq!(id_at(rows.grid(), 1, 0)?, "cell-6");
    assert_eq!(rows.receipt().deleted_master_cell_ids().len(), 3);
    assert_eq!(rows.receipt().preserved_master_cells().len(), 6);

    let columns = rows
        .grid()
        .delete_columns(0, 1, TableGridLimits::default())?;
    assert_eq!((columns.grid().rows(), columns.grid().columns()), (2, 2));
    assert_eq!(id_at(columns.grid(), 0, 0)?, "cell-1");
    assert_eq!(id_at(columns.grid(), 1, 1)?, "cell-8");
    assert_eq!(
        columns.receipt().operation(),
        TableOperationKind::DeleteColumns
    );
    Ok(())
}

#[test]
fn delete_accepts_full_span_removal_and_rejects_partial_span_removal() -> TestResult {
    let grid = TableGrid::new(
        3,
        2,
        vec![
            TableCellSpan {
                master_cell_id: LogicalId::parse("top")?,
                row: 0,
                column: 0,
                row_span: 1,
                column_span: 2,
            },
            TableCellSpan {
                master_cell_id: LogicalId::parse("lower-left")?,
                row: 1,
                column: 0,
                row_span: 2,
                column_span: 1,
            },
            TableCellSpan {
                master_cell_id: LogicalId::parse("lower-right")?,
                row: 1,
                column: 1,
                row_span: 2,
                column_span: 1,
            },
        ],
        TableGridLimits::default(),
    )?;
    assert_eq!(
        grid.delete_rows(1, 1, TableGridLimits::default()),
        Err(TableOperationError::SpanBoundaryConflict)
    );
    assert_eq!(
        grid.delete_columns(0, 1, TableGridLimits::default()),
        Err(TableOperationError::SpanBoundaryConflict)
    );
    let full = grid.delete_rows(1, 2, TableGridLimits::default())?;
    assert_eq!((full.grid().rows(), full.grid().columns()), (1, 2));
    assert_eq!(id_at(full.grid(), 0, 0)?, "top");
    assert_eq!(full.receipt().deleted_master_cell_ids().len(), 2);
    Ok(())
}

#[test]
fn invalid_ranges_counts_limits_and_ids_fail_atomically() -> TestResult {
    let grid = unmerged(2, 2, "base")?;
    let before = grid.canonical_sha256()?;
    assert_eq!(
        grid.insert_rows(0, 0, Vec::new(), TableGridLimits::default()),
        Err(TableOperationError::ZeroCount)
    );
    assert_eq!(
        grid.insert_columns(3, 1, logical_ids("outside", 2)?, TableGridLimits::default()),
        Err(TableOperationError::InsertionIndexOutOfBounds)
    );
    assert_eq!(
        grid.insert_rows(1, 1, logical_ids("short", 1)?, TableGridLimits::default()),
        Err(TableOperationError::NewMasterCellCountMismatch)
    );
    assert_eq!(
        grid.insert_rows(0, 9_999, Vec::new(), TableGridLimits::default()),
        Err(TableOperationError::Grid(
            TableGridError::DimensionLimitExceeded
        ))
    );
    assert_eq!(
        grid.insert_columns(0, 1_023, Vec::new(), TableGridLimits::default()),
        Err(TableOperationError::Grid(
            TableGridError::DimensionLimitExceeded
        ))
    );
    assert_eq!(
        grid.delete_rows(0, 0, TableGridLimits::default()),
        Err(TableOperationError::ZeroCount)
    );
    assert_eq!(
        grid.delete_columns(2, 1, TableGridLimits::default()),
        Err(TableOperationError::DeletionRangeOutOfBounds)
    );
    assert_eq!(
        grid.delete_rows(u32::MAX, 1, TableGridLimits::default()),
        Err(TableOperationError::DeletionRangeOutOfBounds)
    );
    assert_eq!(
        grid.delete_rows(0, 2, TableGridLimits::default()),
        Err(TableOperationError::WouldEmptyGrid)
    );
    assert_eq!(
        grid.insert_rows(
            1,
            1,
            vec![LogicalId::parse("base-0")?, LogicalId::parse("duplicate")?],
            TableGridLimits::default(),
        ),
        Err(TableOperationError::Grid(
            TableGridError::DuplicateMasterCell
        ))
    );
    assert_eq!(grid.canonical_sha256()?, before);
    assert_eq!(
        TableGrid::create_unmerged(2, 2, logical_ids("short", 3)?, TableGridLimits::default()),
        Err(TableOperationError::NewMasterCellCountMismatch)
    );
    assert_eq!(
        TableGrid::create_unmerged(10_000, 1_024, Vec::new(), TableGridLimits::default()),
        Err(TableOperationError::Grid(TableGridError::SlotLimitExceeded))
    );
    Ok(())
}

#[test]
fn fixed_seed_unmerged_edit_sequences_preserve_indexes_and_roundtrip() -> TestResult {
    for seed in 0_u64..128 {
        let mut state = seed ^ 0xd1b5_4a32_d192_ed03;
        let mut next_id = 4_u64;
        let mut grid = unmerged(2, 2, &format!("seed-{seed}-initial"))?;
        for _ in 0..24 {
            let choice = next(&mut state) % 4;
            let result = match choice {
                0 if grid.rows() < 8 => {
                    let index = u32::try_from(next(&mut state) % u64::from(grid.rows() + 1))?;
                    let ids = unique_ids(seed, &mut next_id, usize::try_from(grid.columns())?)?;
                    grid.insert_rows(index, 1, ids, TableGridLimits::default())
                }
                1 if grid.columns() < 8 => {
                    let index = u32::try_from(next(&mut state) % u64::from(grid.columns() + 1))?;
                    let ids = unique_ids(seed, &mut next_id, usize::try_from(grid.rows())?)?;
                    grid.insert_columns(index, 1, ids, TableGridLimits::default())
                }
                2 if grid.rows() > 1 => {
                    let index = u32::try_from(next(&mut state) % u64::from(grid.rows()))?;
                    grid.delete_rows(index, 1, TableGridLimits::default())
                }
                _ if grid.columns() > 1 => {
                    let index = u32::try_from(next(&mut state) % u64::from(grid.columns()))?;
                    grid.delete_columns(index, 1, TableGridLimits::default())
                }
                _ => {
                    let ids = unique_ids(seed, &mut next_id, usize::try_from(grid.columns())?)?;
                    grid.insert_rows(grid.rows(), 1, ids, TableGridLimits::default())
                }
            }?;
            grid = result.into_parts().0;
            assert_eq!(grid.master_cell_count(), grid.slot_count());
            for row in 0..grid.rows() {
                for column in 0..grid.columns() {
                    let coordinate = CellCoordinate { row, column };
                    assert!(grid.master_cell_at(coordinate)?.covers(coordinate));
                }
            }
            let canonical = grid.canonical_json()?;
            assert_eq!(
                TableGrid::from_json(&canonical, TableGridLimits::default())?,
                grid
            );
        }
    }
    Ok(())
}

fn unique_ids(seed: u64, next_id: &mut u64, count: usize) -> TestResult<Vec<LogicalId>> {
    let mut result = Vec::new();
    result.try_reserve_exact(count)?;
    for _ in 0..count {
        result.push(LogicalId::parse(format!("seed-{seed}-new-{next_id}"))?);
        *next_id = next_id
            .checked_add(1)
            .ok_or("identifier counter overflow")?;
    }
    Ok(result)
}

fn next(state: &mut u64) -> u64 {
    *state = state
        .wrapping_mul(2_862_933_555_777_941_757)
        .wrapping_add(3_037_000_493);
    *state
}

#[test]
fn public_error_codes_are_stable() {
    assert_eq!(
        TableOperationError::SpanBoundaryConflict.code(),
        "table_operation_span_boundary_conflict"
    );
    assert_eq!(
        TableOperationError::Grid(TableGridError::SlotLimitExceeded).code(),
        "table_grid_slot_limit_exceeded"
    );
}
