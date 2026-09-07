use std::error::Error;

use domain_ir::{
    CellCoordinate, ContentPreservationPolicy, LogicalId, TABLE_MERGE_SPLIT_SCHEMA_VERSION,
    TableCellContent, TableCellSpan, TableContentState, TableGrid, TableGridError,
    TableGridLimitConfig, TableGridLimits, TableMergeSplitError, TableMergeSplitKind,
    TableSplitRequest,
};

type TestResult = Result<(), Box<dyn Error>>;

fn logical_id(value: &str) -> Result<LogicalId, Box<dyn Error>> {
    Ok(LogicalId::parse(value.to_owned())?)
}

fn identifiers(prefix: &str, count: usize) -> Result<Vec<LogicalId>, Box<dyn Error>> {
    let mut values = Vec::new();
    values.try_reserve_exact(count)?;
    for index in 0..count {
        values.push(logical_id(&format!("{prefix}-{index}"))?);
    }
    Ok(values)
}

fn unmerged(rows: u32, columns: u32, prefix: &str) -> Result<TableGrid, Box<dyn Error>> {
    let count = usize::try_from(rows)? * usize::try_from(columns)?;
    let result = TableGrid::create_unmerged(
        rows,
        columns,
        identifiers(prefix, count)?,
        TableGridLimits::default(),
    )?;
    Ok(result.into_parts().0)
}

fn empty_content(grid: &TableGrid) -> Result<TableContentState, Box<dyn Error>> {
    let mut entries = Vec::new();
    entries.try_reserve_exact(grid.master_cell_count())?;
    for master in grid.master_cells() {
        entries.push(TableCellContent::new(
            master.master_cell_id.clone(),
            Vec::new(),
        ));
    }
    Ok(TableContentState::new(
        grid,
        entries,
        TableGridLimits::default(),
    )?)
}

fn merged_grid_2x3() -> Result<(LogicalId, TableGrid, TableContentState), Box<dyn Error>> {
    let source_id = logical_id("source")?;
    let grid = TableGrid::new(
        2,
        3,
        vec![TableCellSpan {
            master_cell_id: source_id.clone(),
            row: 0,
            column: 0,
            row_span: 2,
            column_span: 3,
        }],
        TableGridLimits::default(),
    )?;
    let content = TableContentState::new(
        &grid,
        vec![TableCellContent::new(source_id.clone(), Vec::new())],
        TableGridLimits::default(),
    )?;
    Ok((source_id, grid, content))
}

fn slots(row: u32, column: u32, row_span: u32, column_span: u32) -> Vec<CellCoordinate> {
    let mut values = Vec::new();
    for current_row in row..row + row_span {
        for current_column in column..column + column_span {
            values.push(CellCoordinate {
                row: current_row,
                column: current_column,
            });
        }
    }
    values
}

fn content_ids<'a>(
    state: &'a TableContentState,
    master: &LogicalId,
) -> Result<Vec<&'a str>, Box<dyn Error>> {
    let entry = state.cell(master).ok_or("expected table content entry")?;
    Ok(entry
        .content_block_ids()
        .iter()
        .map(LogicalId::as_str)
        .collect())
}

#[test]
fn content_state_requires_exact_unique_bounded_ownership() -> TestResult {
    let grid = unmerged(1, 2, "cell")?;
    let first = grid.master_cells()[0].master_cell_id.clone();
    let second = grid.master_cells()[1].master_cell_id.clone();
    let state = TableContentState::new(
        &grid,
        vec![
            TableCellContent::new(second.clone(), vec![logical_id("block-b")?]),
            TableCellContent::new(first.clone(), vec![logical_id("block-a")?]),
        ],
        TableGridLimits::default(),
    )?;
    assert_eq!(state.cells()[0].master_cell_id(), &first);
    assert_eq!(state.cells()[1].master_cell_id(), &second);
    assert_eq!(state.grid_sha256(), &grid.canonical_sha256()?);

    let mismatch = TableContentState::new(
        &grid,
        vec![TableCellContent::new(first.clone(), Vec::new())],
        TableGridLimits::default(),
    );
    assert_eq!(
        mismatch,
        Err(TableMergeSplitError::ContentMasterSetMismatch)
    );

    let duplicate_master = TableContentState::new(
        &grid,
        vec![
            TableCellContent::new(first.clone(), Vec::new()),
            TableCellContent::new(first.clone(), Vec::new()),
        ],
        TableGridLimits::default(),
    );
    assert_eq!(
        duplicate_master,
        Err(TableMergeSplitError::DuplicateContentMaster)
    );

    let duplicate_block = TableContentState::new(
        &grid,
        vec![
            TableCellContent::new(first, vec![logical_id("shared-block")?]),
            TableCellContent::new(second, vec![logical_id("shared-block")?]),
        ],
        TableGridLimits::default(),
    );
    assert_eq!(
        duplicate_block,
        Err(TableMergeSplitError::DuplicateContentBlock)
    );
    assert!(!format!("{state:?}").contains("block-a"));
    Ok(())
}

#[test]
fn content_state_enforces_block_and_identifier_limits() -> TestResult {
    let limits = TableGridLimits::new(TableGridLimitConfig {
        rows: 1,
        columns: 1,
        slots: 1,
        master_cells: 1,
        identifier_bytes: 5,
        serialized_bytes: 1_024,
    })?;
    let grid = TableGrid::create_unmerged(1, 1, vec![logical_id("cell")?], limits)?
        .into_parts()
        .0;
    assert_eq!(
        TableContentState::new(
            &grid,
            vec![TableCellContent::new(
                logical_id("cell")?,
                vec![logical_id("a")?, logical_id("b")?],
            )],
            limits,
        ),
        Err(TableMergeSplitError::ContentBlockLimitExceeded)
    );
    assert_eq!(
        TableContentState::new(
            &grid,
            vec![TableCellContent::new(
                logical_id("cell")?,
                vec![logical_id("abcdef")?],
            )],
            limits,
        ),
        Err(TableMergeSplitError::IdentifierLimitExceeded)
    );
    Ok(())
}

#[test]
fn merge_concatenates_in_canonical_cell_order_and_preserves_top_left_identity() -> TestResult {
    let grid = unmerged(2, 2, "cell")?;
    let ids: Vec<LogicalId> = grid
        .master_cells()
        .iter()
        .map(|cell| cell.master_cell_id.clone())
        .collect();
    let content = TableContentState::new(
        &grid,
        vec![
            TableCellContent::new(ids[3].clone(), vec![logical_id("block-d")?]),
            TableCellContent::new(
                ids[1].clone(),
                vec![logical_id("block-b1")?, logical_id("block-b2")?],
            ),
            TableCellContent::new(ids[0].clone(), vec![logical_id("block-a")?]),
            TableCellContent::new(ids[2].clone(), Vec::new()),
        ],
        TableGridLimits::default(),
    )?;
    let result = grid.merge_cells(
        vec![
            CellCoordinate { row: 1, column: 1 },
            CellCoordinate { row: 0, column: 1 },
            CellCoordinate { row: 1, column: 0 },
            CellCoordinate { row: 0, column: 0 },
        ],
        &content,
        ContentPreservationPolicy::Concatenate,
        TableGridLimits::default(),
    )?;

    assert_eq!(result.grid().master_cell_count(), 1);
    let merged = &result.grid().master_cells()[0];
    assert_eq!(merged.master_cell_id, ids[0]);
    assert_eq!(
        (
            merged.row,
            merged.column,
            merged.row_span,
            merged.column_span
        ),
        (0, 0, 2, 2)
    );
    assert_eq!(
        content_ids(result.content(), &ids[0])?,
        vec!["block-a", "block-b1", "block-b2", "block-d"]
    );
    let receipt = result.receipt();
    assert_eq!(receipt.schema_version(), TABLE_MERGE_SPLIT_SCHEMA_VERSION);
    assert_eq!(receipt.operation(), TableMergeSplitKind::Merge);
    assert_eq!(receipt.preserved_master_cell_id(), &ids[0]);
    assert_eq!(receipt.retired_master_cell_ids(), &ids[1..]);
    assert_eq!(receipt.content_transfers().len(), 3);
    assert!(receipt.discarded_content_block_ids().is_empty());
    assert_eq!(receipt.before_grid_sha256(), &grid.canonical_sha256()?);
    assert_eq!(
        receipt.after_grid_sha256(),
        &result.grid().canonical_sha256()?
    );
    assert_eq!(receipt.canonical_json()?, receipt.canonical_json()?);
    assert_eq!(
        receipt.canonical_json_with_max_bytes(1),
        Err(TableMergeSplitError::ReceiptOutputLimitExceeded)
    );
    assert!(!format!("{receipt:?}").contains("block-b1"));
    Ok(())
}

#[test]
fn merge_first_records_discarded_content_and_reject_policy_is_atomic() -> TestResult {
    let grid = unmerged(1, 3, "cell")?;
    let ids: Vec<LogicalId> = grid
        .master_cells()
        .iter()
        .map(|cell| cell.master_cell_id.clone())
        .collect();
    let content = TableContentState::new(
        &grid,
        vec![
            TableCellContent::new(ids[0].clone(), vec![logical_id("keep")?]),
            TableCellContent::new(ids[1].clone(), vec![logical_id("drop-b")?]),
            TableCellContent::new(ids[2].clone(), vec![logical_id("drop-c")?]),
        ],
        TableGridLimits::default(),
    )?;
    let before_grid = grid.canonical_json()?;
    let before_content = content.clone();
    let selection = slots(0, 0, 1, 3);
    assert_eq!(
        grid.merge_cells(
            selection.clone(),
            &content,
            ContentPreservationPolicy::RejectIfMultiple,
            TableGridLimits::default(),
        ),
        Err(TableMergeSplitError::MultipleNonemptyCells)
    );
    assert_eq!(grid.canonical_json()?, before_grid);
    assert_eq!(content, before_content);

    let result = grid.merge_cells(
        selection,
        &content,
        ContentPreservationPolicy::First,
        TableGridLimits::default(),
    )?;
    assert_eq!(content_ids(result.content(), &ids[0])?, vec!["keep"]);
    assert_eq!(
        result
            .receipt()
            .discarded_content_block_ids()
            .iter()
            .map(LogicalId::as_str)
            .collect::<Vec<_>>(),
        vec!["drop-b", "drop-c"]
    );
    Ok(())
}

#[test]
fn merge_rejects_nonrectangular_duplicate_out_of_bounds_and_noop_selections() -> TestResult {
    let grid = unmerged(2, 2, "cell")?;
    let content = empty_content(&grid)?;
    let limits = TableGridLimits::default();
    assert_eq!(
        grid.merge_cells(
            Vec::new(),
            &content,
            ContentPreservationPolicy::Concatenate,
            limits
        ),
        Err(TableMergeSplitError::EmptySelection)
    );
    assert_eq!(
        grid.merge_cells(
            vec![
                CellCoordinate { row: 0, column: 0 },
                CellCoordinate { row: 0, column: 0 },
            ],
            &content,
            ContentPreservationPolicy::Concatenate,
            limits,
        ),
        Err(TableMergeSplitError::DuplicateSelectedSlot)
    );
    assert_eq!(
        grid.merge_cells(
            vec![
                CellCoordinate { row: 0, column: 0 },
                CellCoordinate { row: 0, column: 1 },
                CellCoordinate { row: 1, column: 0 },
            ],
            &content,
            ContentPreservationPolicy::Concatenate,
            limits,
        ),
        Err(TableMergeSplitError::NonRectangularSelection)
    );
    assert_eq!(
        grid.merge_cells(
            vec![CellCoordinate { row: 2, column: 0 }],
            &content,
            ContentPreservationPolicy::Concatenate,
            limits,
        ),
        Err(TableMergeSplitError::SelectionOutOfBounds)
    );
    assert_eq!(
        grid.merge_cells(
            vec![CellCoordinate { row: 0, column: 0 }],
            &content,
            ContentPreservationPolicy::Concatenate,
            limits,
        ),
        Err(TableMergeSplitError::NoStructuralChange)
    );
    Ok(())
}

#[test]
fn merge_rejects_partial_intersection_with_existing_span() -> TestResult {
    let grid = unmerged(2, 2, "cell")?;
    let content = empty_content(&grid)?;
    let merged = grid.merge_cells(
        slots(0, 0, 1, 2),
        &content,
        ContentPreservationPolicy::Concatenate,
        TableGridLimits::default(),
    )?;
    assert_eq!(
        merged.grid().merge_cells(
            slots(0, 0, 2, 1),
            merged.content(),
            ContentPreservationPolicy::Concatenate,
            TableGridLimits::default(),
        ),
        Err(TableMergeSplitError::PartialMasterSelection)
    );
    Ok(())
}

#[test]
fn split_distributes_contiguous_balanced_content_and_roundtrips_merge() -> TestResult {
    let source_id = logical_id("source-cell")?;
    let grid = TableGrid::new(
        2,
        2,
        vec![TableCellSpan {
            master_cell_id: source_id.clone(),
            row: 0,
            column: 0,
            row_span: 2,
            column_span: 2,
        }],
        TableGridLimits::default(),
    )?;
    let source_blocks = identifiers("block", 5)?;
    let content = TableContentState::new(
        &grid,
        vec![TableCellContent::new(
            source_id.clone(),
            source_blocks.clone(),
        )],
        TableGridLimits::default(),
    )?;
    let new_ids = identifiers("split-cell", 3)?;
    let split = grid.split_cell(
        TableSplitRequest::new(
            source_id.clone(),
            2,
            2,
            new_ids.clone(),
            ContentPreservationPolicy::Distribute,
        ),
        &content,
        TableGridLimits::default(),
    )?;
    assert_eq!(split.grid().master_cell_count(), 4);
    assert_eq!(
        content_ids(split.content(), &source_id)?,
        vec!["block-0", "block-1"]
    );
    assert_eq!(content_ids(split.content(), &new_ids[0])?, vec!["block-2"]);
    assert_eq!(content_ids(split.content(), &new_ids[1])?, vec!["block-3"]);
    assert_eq!(content_ids(split.content(), &new_ids[2])?, vec!["block-4"]);
    assert_eq!(split.receipt().operation(), TableMergeSplitKind::Split);
    assert_eq!(split.receipt().created_master_cell_ids(), new_ids);
    assert_eq!(split.receipt().content_transfers().len(), 4);
    assert!(split.receipt().discarded_content_block_ids().is_empty());

    let merged = split.grid().merge_cells(
        slots(0, 0, 2, 2),
        split.content(),
        ContentPreservationPolicy::Concatenate,
        TableGridLimits::default(),
    )?;
    assert_eq!(merged.grid(), &grid);
    assert_eq!(
        content_ids(merged.content(), &source_id)?,
        source_blocks
            .iter()
            .map(LogicalId::as_str)
            .collect::<Vec<_>>()
    );
    Ok(())
}

#[test]
fn split_non_distribute_policies_keep_all_content_in_preserved_cell() -> TestResult {
    let source_id = logical_id("source")?;
    let grid = TableGrid::new(
        1,
        2,
        vec![TableCellSpan {
            master_cell_id: source_id.clone(),
            row: 0,
            column: 0,
            row_span: 1,
            column_span: 2,
        }],
        TableGridLimits::default(),
    )?;
    let content = TableContentState::new(
        &grid,
        vec![TableCellContent::new(
            source_id.clone(),
            identifiers("block", 3)?,
        )],
        TableGridLimits::default(),
    )?;
    for policy in [
        ContentPreservationPolicy::Concatenate,
        ContentPreservationPolicy::First,
        ContentPreservationPolicy::RejectIfMultiple,
    ] {
        let result = grid.split_cell(
            TableSplitRequest::new(
                source_id.clone(),
                1,
                2,
                vec![logical_id(&format!("new-{policy:?}"))?],
                policy,
            ),
            &content,
            TableGridLimits::default(),
        )?;
        assert_eq!(content_ids(result.content(), &source_id)?.len(), 3);
        assert!(result.receipt().discarded_content_block_ids().is_empty());
    }
    Ok(())
}

#[test]
fn split_rejects_invalid_and_nondivisible_geometry_atomically() -> TestResult {
    let (source_id, grid, content) = merged_grid_2x3()?;
    assert_eq!(
        grid.split_cell(
            TableSplitRequest::new(
                source_id.clone(),
                0,
                1,
                Vec::new(),
                ContentPreservationPolicy::Distribute,
            ),
            &content,
            TableGridLimits::default(),
        ),
        Err(TableMergeSplitError::InvalidSplitDimensions)
    );
    assert_eq!(
        grid.split_cell(
            TableSplitRequest::new(
                source_id.clone(),
                1,
                1,
                Vec::new(),
                ContentPreservationPolicy::Distribute,
            ),
            &content,
            TableGridLimits::default(),
        ),
        Err(TableMergeSplitError::NoStructuralChange)
    );
    assert_eq!(
        grid.split_cell(
            TableSplitRequest::new(
                logical_id("missing")?,
                1,
                2,
                vec![logical_id("new")?],
                ContentPreservationPolicy::Distribute,
            ),
            &content,
            TableGridLimits::default(),
        ),
        Err(TableMergeSplitError::MasterCellNotFound)
    );
    assert_eq!(
        grid.split_cell(
            TableSplitRequest::new(
                source_id.clone(),
                2,
                2,
                identifiers("new", 3)?,
                ContentPreservationPolicy::Distribute,
            ),
            &content,
            TableGridLimits::default(),
        ),
        Err(TableMergeSplitError::SplitNotDivisible)
    );
    Ok(())
}

#[test]
fn split_rejects_identity_and_content_state_conflicts_atomically() -> TestResult {
    let (source_id, grid, content) = merged_grid_2x3()?;
    assert_eq!(
        grid.split_cell(
            TableSplitRequest::new(
                source_id.clone(),
                1,
                3,
                vec![logical_id("new")?],
                ContentPreservationPolicy::Distribute,
            ),
            &content,
            TableGridLimits::default(),
        ),
        Err(TableMergeSplitError::NewMasterCellCountMismatch)
    );
    assert_eq!(
        grid.split_cell(
            TableSplitRequest::new(
                source_id.clone(),
                1,
                3,
                vec![logical_id("dup")?, logical_id("dup")?],
                ContentPreservationPolicy::Distribute,
            ),
            &content,
            TableGridLimits::default(),
        ),
        Err(TableMergeSplitError::Grid(
            TableGridError::DuplicateMasterCell
        ))
    );

    let other_grid = unmerged(2, 3, "other")?;
    let other_content = empty_content(&other_grid)?;
    assert_eq!(
        grid.split_cell(
            TableSplitRequest::new(
                source_id.clone(),
                1,
                3,
                identifiers("new", 2)?,
                ContentPreservationPolicy::Distribute,
            ),
            &other_content,
            TableGridLimits::default(),
        ),
        Err(TableMergeSplitError::ContentGridMismatch)
    );
    Ok(())
}

#[test]
fn fixed_seed_merge_split_corpus_preserves_all_content_and_grid_invariants() -> TestResult {
    let limits = TableGridLimits::default();
    for case in 0..128usize {
        let grid = unmerged(4, 4, &format!("cell-{case}"))?;
        let mut entries = Vec::new();
        let mut expected_blocks = Vec::new();
        for (index, master) in grid.master_cells().iter().enumerate() {
            let block = logical_id(&format!("block-{case}-{index}"))?;
            expected_blocks.push(block.clone());
            entries.push(TableCellContent::new(
                master.master_cell_id.clone(),
                vec![block],
            ));
        }
        let content = TableContentState::new(&grid, entries, limits)?;
        let region_index = case % 4;
        let row = u32::try_from((region_index / 2) * 2)?;
        let column = u32::try_from((region_index % 2) * 2)?;
        let survivor = grid
            .master_cell_at(CellCoordinate { row, column })?
            .master_cell_id
            .clone();
        let merged = grid.merge_cells(
            slots(row, column, 2, 2),
            &content,
            ContentPreservationPolicy::Concatenate,
            limits,
        )?;
        let split = merged.grid().split_cell(
            TableSplitRequest::new(
                survivor.clone(),
                2,
                2,
                identifiers(&format!("split-{case}"), 3)?,
                ContentPreservationPolicy::Distribute,
            ),
            merged.content(),
            limits,
        )?;
        assert_eq!(split.grid().master_cell_count(), 16);
        assert_eq!(
            TableGrid::from_json(&split.grid().canonical_json()?, limits)?,
            *split.grid()
        );
        assert_eq!(
            merged.receipt().canonical_json()?,
            merged.receipt().canonical_json()?
        );
        assert_eq!(
            split.receipt().canonical_json()?,
            split.receipt().canonical_json()?
        );

        let mut actual_blocks: Vec<LogicalId> = split
            .content()
            .cells()
            .iter()
            .flat_map(|entry| entry.content_block_ids().iter().cloned())
            .collect();
        actual_blocks.sort_unstable();
        expected_blocks.sort_unstable();
        assert_eq!(actual_blocks, expected_blocks);
        assert!(split.receipt().discarded_content_block_ids().is_empty());
    }
    Ok(())
}

#[test]
fn merge_split_error_codes_are_stable() {
    assert_eq!(
        TableMergeSplitError::NonRectangularSelection.code(),
        "table_merge_split_non_rectangular_selection"
    );
    assert_eq!(
        TableMergeSplitError::PartialMasterSelection.code(),
        "table_merge_split_partial_master_selection"
    );
    assert_eq!(
        TableMergeSplitError::SplitNotDivisible.code(),
        "table_merge_split_not_divisible"
    );
    assert_eq!(
        TableMergeSplitError::Grid(TableGridError::OverlappingSpan).code(),
        "table_grid_overlapping_span"
    );
}
