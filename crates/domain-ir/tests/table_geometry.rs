use domain_ir::{
    CellCoordinate, LengthMicrometers, LogicalId, TABLE_GEOMETRY_SCHEMA_VERSION, TableCellSpan,
    TableGeometryError, TableGeometryLimitConfig, TableGeometryLimits, TableGeometryOperation,
    TableGeometryState, TableGeometryStateDraft, TableGrid, TableGridLimits, TableTrackRange,
};

type TestResult = Result<(), Box<dyn std::error::Error>>;

fn um(value: i64) -> LengthMicrometers {
    LengthMicrometers::from_raw(value)
}

fn cell(
    identifier: &str,
    row: u32,
    column: u32,
    row_span: u32,
    column_span: u32,
) -> Result<TableCellSpan, Box<dyn std::error::Error>> {
    Ok(TableCellSpan {
        master_cell_id: LogicalId::parse(identifier)?,
        row,
        column,
        row_span,
        column_span,
    })
}

fn grid() -> Result<TableGrid, Box<dyn std::error::Error>> {
    Ok(TableGrid::new(
        3,
        3,
        vec![
            cell("merged", 0, 0, 2, 2)?,
            cell("top-right", 0, 2, 1, 1)?,
            cell("middle-right", 1, 2, 1, 1)?,
            cell("bottom-left", 2, 0, 1, 1)?,
            cell("bottom-middle", 2, 1, 1, 1)?,
            cell("bottom-right", 2, 2, 1, 1)?,
        ],
        TableGridLimits::default(),
    )?)
}

fn state(grid: &TableGrid) -> Result<TableGeometryState, TableGeometryError> {
    TableGeometryState::new(
        grid,
        vec![um(1_000), um(2_000), um(3_000)],
        vec![um(500), um(1_200), um(1_000)],
        vec![um(4_000), um(3_000), um(2_000)],
        vec![um(1_000), um(2_500), um(1_000)],
        TableGeometryLimits::default(),
    )
}

#[test]
fn equalizes_rows_with_ceiling_average_and_content_minimum() -> TestResult {
    let grid = grid()?;
    let state = state(&grid)?;
    let result = state.apply(
        &grid,
        TableGeometryOperation::EqualRowHeights {
            range: TableTrackRange::new(0, 3),
        },
        TableGeometryLimits::default(),
    )?;
    assert_eq!(result.state().row_heights(), &[um(2_000); 3]);
    assert_eq!(result.receipt().changed_rows(), &[0, 2]);
    assert!(result.receipt().changed_columns().is_empty());

    let constrained = TableGeometryState::new(
        &grid,
        vec![um(1_000), um(5_000), um(3_000)],
        vec![um(500), um(4_000), um(1_000)],
        vec![um(4_000), um(3_000), um(3_000)],
        vec![um(1_000), um(2_500), um(1_000)],
        TableGeometryLimits::default(),
    )?;
    let result = constrained.apply(
        &grid,
        TableGeometryOperation::EqualRowHeights {
            range: TableTrackRange::new(0, 3),
        },
        TableGeometryLimits::default(),
    )?;
    assert_eq!(result.state().row_heights(), &[um(4_000); 3]);
    Ok(())
}

#[test]
fn equalizes_columns_without_touching_rows() -> TestResult {
    let grid = grid()?;
    let state = state(&grid)?;
    let result = state.apply(
        &grid,
        TableGeometryOperation::EqualColumnWidths {
            range: TableTrackRange::new(0, 3),
        },
        TableGeometryLimits::default(),
    )?;
    assert_eq!(result.state().column_widths(), &[um(3_000); 3]);
    assert_eq!(result.state().row_heights(), state.row_heights());
    assert_eq!(result.receipt().changed_columns(), &[0, 2]);
    Ok(())
}

#[test]
fn row_minimum_grows_small_rows_but_never_shrinks_large_rows() -> TestResult {
    let grid = grid()?;
    let state = state(&grid)?;
    let result = state.apply(
        &grid,
        TableGeometryOperation::SetRowMinimumHeight {
            range: TableTrackRange::new(0, 2),
            minimum_height: um(1_500),
        },
        TableGeometryLimits::default(),
    )?;
    assert_eq!(
        result.state().row_heights(),
        &[um(1_500), um(2_000), um(3_000)]
    );
    assert_eq!(
        result.state().row_minimum_heights(),
        &[um(1_500), um(1_500), um(1_000)]
    );
    assert_eq!(result.receipt().changed_rows(), &[0, 1]);
    Ok(())
}

#[test]
fn operations_are_deterministic_and_idempotent() -> TestResult {
    let grid = grid()?;
    let state = state(&grid)?;
    let operation = TableGeometryOperation::EqualRowHeights {
        range: TableTrackRange::new(0, 3),
    };
    let first = state.apply(&grid, operation, TableGeometryLimits::default())?;
    let second = state.apply(&grid, operation, TableGeometryLimits::default())?;
    assert_eq!(first, second);
    assert_eq!(
        first
            .receipt()
            .canonical_json(TableGeometryLimits::default())?,
        second
            .receipt()
            .canonical_json(TableGeometryLimits::default())?
    );
    let repeated = first
        .state()
        .apply(&grid, operation, TableGeometryLimits::default())?;
    assert_eq!(first.state(), repeated.state());
    assert!(repeated.receipt().changed_rows().is_empty());
    Ok(())
}

#[test]
fn merged_cell_extent_sums_every_covered_track() -> TestResult {
    let grid = grid()?;
    let state = state(&grid)?;
    assert_eq!(
        state.cell_extent(&grid, CellCoordinate { row: 1, column: 1 })?,
        (um(7_000), um(3_000))
    );
    assert_eq!(
        state.cell_extent(&grid, CellCoordinate { row: 3, column: 0 }),
        Err(TableGeometryError::CoordinateOutOfBounds)
    );
    Ok(())
}

#[test]
fn canonical_state_roundtrips_and_is_grid_bound() -> TestResult {
    let grid = grid()?;
    let state = state(&grid)?;
    let canonical = state.canonical_json(TableGeometryLimits::default())?;
    let reopened =
        TableGeometryState::from_json(&grid, &canonical, TableGeometryLimits::default())?;
    assert_eq!(reopened, state);
    assert_eq!(
        reopened.canonical_sha256(TableGeometryLimits::default())?,
        state.canonical_sha256(TableGeometryLimits::default())?
    );

    let other_grid = TableGrid::new(
        1,
        1,
        vec![cell("only", 0, 0, 1, 1)?],
        TableGridLimits::default(),
    )?;
    assert_eq!(
        TableGeometryState::from_json(&other_grid, &canonical, TableGeometryLimits::default()),
        Err(TableGeometryError::GridMismatch)
    );
    assert_eq!(
        state.apply(
            &other_grid,
            TableGeometryOperation::EqualRowHeights {
                range: TableTrackRange::new(0, 1)
            },
            TableGeometryLimits::default()
        ),
        Err(TableGeometryError::GridMismatch)
    );
    Ok(())
}

#[test]
fn malformed_unknown_duplicate_and_oversized_json_fail_closed() -> TestResult {
    let grid = grid()?;
    let state = state(&grid)?;
    let canonical = String::from_utf8(state.canonical_json(TableGeometryLimits::default())?)?;
    let unknown = canonical.replacen('{', "{\"unknown\":true,", 1);
    assert_eq!(
        TableGeometryState::from_json(&grid, unknown.as_bytes(), TableGeometryLimits::default()),
        Err(TableGeometryError::InvalidJson)
    );
    let duplicate = canonical.replacen(
        "{\"schema_version\":",
        "{\"schema_version\":\"duplicate\",\"schema_version\":",
        1,
    );
    assert_eq!(
        TableGeometryState::from_json(&grid, duplicate.as_bytes(), TableGeometryLimits::default()),
        Err(TableGeometryError::InvalidJson)
    );
    assert_eq!(
        TableGeometryState::from_json(&grid, b"not-json", TableGeometryLimits::default()),
        Err(TableGeometryError::InvalidJson)
    );
    let tiny = TableGeometryLimits::new(TableGeometryLimitConfig {
        rows: 3,
        columns: 3,
        dimension_micrometers: 10_000,
        serialized_bytes: 64,
    })?;
    assert_eq!(
        TableGeometryState::from_json(&grid, &[b' '; 65], tiny),
        Err(TableGeometryError::InputLimitExceeded)
    );
    assert_eq!(
        TableGeometryState::new(
            &grid,
            vec![um(1_000); 3],
            vec![um(500); 3],
            vec![um(1_000); 3],
            vec![um(500); 3],
            tiny
        ),
        Err(TableGeometryError::OutputLimitExceeded)
    );
    Ok(())
}

#[test]
fn invalid_counts_dimensions_minimums_and_limits_are_rejected() -> TestResult {
    let grid = grid()?;
    let limits = TableGeometryLimits::default();
    assert_eq!(
        TableGeometryState::new(
            &grid,
            vec![um(1_000); 2],
            vec![um(500); 2],
            vec![um(1_000); 3],
            vec![um(500); 3],
            limits
        ),
        Err(TableGeometryError::RowCountMismatch)
    );
    assert_eq!(
        TableGeometryState::new(
            &grid,
            vec![um(1_000); 3],
            vec![um(500); 3],
            vec![um(1_000); 2],
            vec![um(500); 2],
            limits
        ),
        Err(TableGeometryError::ColumnCountMismatch)
    );
    assert_eq!(
        TableGeometryState::new(
            &grid,
            vec![um(0), um(1_000), um(1_000)],
            vec![um(500); 3],
            vec![um(1_000); 3],
            vec![um(500); 3],
            limits
        ),
        Err(TableGeometryError::InvalidDimension)
    );
    assert_eq!(
        TableGeometryState::new(
            &grid,
            vec![um(1_000); 3],
            vec![um(1_500), um(500), um(500)],
            vec![um(1_000); 3],
            vec![um(500); 3],
            limits
        ),
        Err(TableGeometryError::MinimumViolation)
    );
    assert_eq!(
        TableGeometryLimits::new(TableGeometryLimitConfig {
            rows: 0,
            columns: 3,
            dimension_micrometers: 10_000,
            serialized_bytes: 1_024,
        }),
        Err(TableGeometryError::InvalidLimit)
    );
    Ok(())
}

#[test]
fn invalid_ranges_and_operation_dimensions_leave_source_unchanged() -> TestResult {
    let grid = grid()?;
    let state = state(&grid)?;
    let before = state.canonical_sha256(TableGeometryLimits::default())?;
    for (operation, expected) in [
        (
            TableGeometryOperation::EqualRowHeights {
                range: TableTrackRange::new(0, 0),
            },
            TableGeometryError::EmptyRange,
        ),
        (
            TableGeometryOperation::EqualColumnWidths {
                range: TableTrackRange::new(2, 2),
            },
            TableGeometryError::RangeOutOfBounds,
        ),
        (
            TableGeometryOperation::SetRowMinimumHeight {
                range: TableTrackRange::new(0, 1),
                minimum_height: um(-1),
            },
            TableGeometryError::InvalidDimension,
        ),
    ] {
        assert_eq!(
            state.apply(&grid, operation, TableGeometryLimits::default()),
            Err(expected)
        );
        assert_eq!(
            state.canonical_sha256(TableGeometryLimits::default())?,
            before
        );
    }
    let restrictive = TableGeometryLimits::new(TableGeometryLimitConfig {
        rows: 2,
        columns: 3,
        dimension_micrometers: 10_000,
        serialized_bytes: 4_096,
    })?;
    assert_eq!(
        state.apply(
            &grid,
            TableGeometryOperation::EqualColumnWidths {
                range: TableTrackRange::new(0, 3)
            },
            restrictive
        ),
        Err(TableGeometryError::TrackLimitExceeded)
    );
    assert_eq!(
        state.canonical_sha256(TableGeometryLimits::default())?,
        before
    );
    Ok(())
}

#[test]
fn debug_output_redacts_hashes_and_dimensions() -> TestResult {
    let grid = grid()?;
    let state = state(&grid)?;
    let result = state.apply(
        &grid,
        TableGeometryOperation::SetRowMinimumHeight {
            range: TableTrackRange::new(0, 1),
            minimum_height: um(1_500),
        },
        TableGeometryLimits::default(),
    )?;
    let debug = format!("{result:?}");
    assert!(!debug.contains(result.receipt().source_state_sha256()));
    assert!(!debug.contains(result.receipt().output_state_sha256()));
    assert!(!debug.contains("1500"));
    Ok(())
}

#[test]
fn fixed_seed_corpus_preserves_minima_and_determinism() -> TestResult {
    let grid = grid()?;
    for seed in 1_i64..=256 {
        let heights = vec![um(seed * 11 + 1), um(seed * 13 + 2), um(seed * 17 + 3)];
        let minimums = vec![um(seed + 1), um(seed + 2), um(seed + 3)];
        let state = TableGeometryState::new(
            &grid,
            heights,
            minimums,
            vec![um(seed * 19 + 4), um(seed * 23 + 5), um(seed * 29 + 6)],
            vec![um(seed + 4), um(seed + 5), um(seed + 6)],
            TableGeometryLimits::default(),
        )?;
        let operation = if seed % 2 == 0 {
            TableGeometryOperation::EqualRowHeights {
                range: TableTrackRange::new(0, 3),
            }
        } else {
            TableGeometryOperation::EqualColumnWidths {
                range: TableTrackRange::new(0, 3),
            }
        };
        let first = state.apply(&grid, operation, TableGeometryLimits::default())?;
        let second = state.apply(&grid, operation, TableGeometryLimits::default())?;
        assert_eq!(first, second);
        assert!(
            first
                .state()
                .row_heights()
                .iter()
                .zip(first.state().row_minimum_heights())
                .all(|(value, minimum)| value >= minimum)
        );
        assert!(
            first
                .state()
                .column_widths()
                .iter()
                .zip(first.state().column_minimum_widths())
                .all(|(value, minimum)| value >= minimum)
        );
    }
    Ok(())
}

#[test]
fn schema_and_error_codes_are_stable() {
    assert_eq!(
        TABLE_GEOMETRY_SCHEMA_VERSION,
        "hwpx-agent.table-geometry/v1"
    );
    assert_eq!(
        TableGeometryError::GridMismatch.code(),
        "table_geometry_grid_mismatch"
    );
    assert_eq!(
        TableGeometryError::MinimumViolation.code(),
        "table_geometry_minimum_violation"
    );
    assert_eq!(
        TableGeometryError::RangeOutOfBounds.code(),
        "table_geometry_range_out_of_bounds"
    );
}

#[test]
fn unsupported_version_and_explicit_grid_hash_mismatch_fail_closed() -> TestResult {
    let grid = grid()?;
    let state = state(&grid)?;
    let canonical = String::from_utf8(state.canonical_json(TableGeometryLimits::default())?)?;
    let wrong_version = canonical.replace(TABLE_GEOMETRY_SCHEMA_VERSION, "unsupported/v0");
    assert_eq!(
        TableGeometryState::from_json(
            &grid,
            wrong_version.as_bytes(),
            TableGeometryLimits::default()
        ),
        Err(TableGeometryError::UnsupportedVersion)
    );
    let draft = TableGeometryStateDraft {
        schema_version: TABLE_GEOMETRY_SCHEMA_VERSION.to_owned(),
        grid_sha256: "0".repeat(64),
        row_heights: vec![um(1_000); 3],
        row_minimum_heights: vec![um(500); 3],
        column_widths: vec![um(1_000); 3],
        column_minimum_widths: vec![um(500); 3],
    };
    assert_eq!(
        TableGeometryState::from_draft(&grid, draft, TableGeometryLimits::default()),
        Err(TableGeometryError::GridMismatch)
    );
    Ok(())
}
