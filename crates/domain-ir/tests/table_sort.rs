use domain_ir::{
    CellCoordinate, LogicalId, TABLE_SORT_CAPABILITY_ID, TABLE_SORT_SCHEMA_VERSION,
    TableBlankOrder, TableCellSpan, TableFormulaMovePolicy, TableGrid, TableGridLimits,
    TableSortAxis, TableSortBuilder, TableSortCellDraft, TableSortDirection, TableSortError,
    TableSortKey, TableSortLimitConfig, TableSortLimits, TableSortRegion, TableSortRequest,
    TableSortRequestDraft, TableSortValue, TableTextCollation,
};

type TestResult = Result<(), Box<dyn std::error::Error>>;

fn coordinate(row: u32, column: u32) -> CellCoordinate {
    CellCoordinate { row, column }
}

fn digest(value: u64) -> String {
    format!("{value:064x}")
}

fn unmerged_grid(rows: u32, columns: u32) -> Result<TableGrid, Box<dyn std::error::Error>> {
    let mut cells = Vec::new();
    for row in 0..rows {
        for column in 0..columns {
            cells.push(TableCellSpan {
                master_cell_id: LogicalId::parse(format!("cell-{row}-{column}"))?,
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

fn cell(row: u32, column: u32, value: TableSortValue) -> TableSortCellDraft {
    TableSortCellDraft {
        coordinate: coordinate(row, column),
        payload_sha256: digest(u64::from(row) * 100 + u64::from(column) + 1),
        formula_sha256: None,
        sort_value: value,
    }
}

fn integer(value: i64) -> TableSortValue {
    TableSortValue::Integer { value }
}

fn text(value: &str) -> TableSortValue {
    TableSortValue::Text {
        value: value.to_owned(),
    }
}

fn key(offset: u32) -> TableSortKey {
    TableSortKey {
        offset,
        direction: TableSortDirection::Ascending,
        blank_order: TableBlankOrder::Last,
        text_collation: TableTextCollation::Binary,
    }
}

fn draft(
    rows: u32,
    columns: u32,
    axis: TableSortAxis,
    keys: Vec<TableSortKey>,
    cells: Vec<TableSortCellDraft>,
) -> Result<TableSortRequestDraft, Box<dyn std::error::Error>> {
    Ok(TableSortRequestDraft {
        schema_version: TABLE_SORT_SCHEMA_VERSION.to_owned(),
        table_id: LogicalId::parse("private-table")?,
        region: TableSortRegion {
            start: coordinate(0, 0),
            end: coordinate(rows - 1, columns - 1),
        },
        axis,
        keys,
        formula_move_policy: TableFormulaMovePolicy::Reject,
        cells,
    })
}

#[test]
fn row_sort_moves_complete_payload_rows_in_destination_order() -> TestResult {
    let grid = unmerged_grid(3, 2)?;
    let cells = vec![
        cell(0, 0, integer(2)),
        cell(0, 1, text("row-a")),
        cell(1, 0, integer(1)),
        cell(1, 1, text("row-b")),
        cell(2, 0, integer(3)),
        cell(2, 1, text("row-c")),
    ];
    let request = TableSortRequest::from_draft(
        draft(3, 2, TableSortAxis::Rows, vec![key(0)], cells)?,
        &grid,
        TableSortLimits::default(),
    )?;
    let plan = TableSortBuilder::build(request, TableSortLimits::default())?;
    let sources: Vec<_> = plan
        .relocations()
        .iter()
        .map(domain_ir::TableSortRelocation::source)
        .collect();
    assert_eq!(
        sources,
        vec![
            coordinate(1, 0),
            coordinate(1, 1),
            coordinate(0, 0),
            coordinate(0, 1),
            coordinate(2, 0),
            coordinate(2, 1),
        ]
    );
    assert!(plan.receipt().changed());
    assert_eq!(plan.receipt().capability_id(), TABLE_SORT_CAPABILITY_ID);
    Ok(())
}

#[test]
fn key_precedence_is_preserved_and_equal_lines_stay_stable() -> TestResult {
    let grid = unmerged_grid(4, 2)?;
    let cells = vec![
        cell(0, 0, integer(1)),
        cell(0, 1, integer(1)),
        cell(1, 0, integer(1)),
        cell(1, 1, integer(3)),
        cell(2, 0, integer(0)),
        cell(2, 1, integer(9)),
        cell(3, 0, integer(1)),
        cell(3, 1, integer(3)),
    ];
    let mut secondary = key(1);
    secondary.direction = TableSortDirection::Descending;
    let request = TableSortRequest::from_draft(
        draft(4, 2, TableSortAxis::Rows, vec![key(0), secondary], cells)?,
        &grid,
        TableSortLimits::default(),
    )?;
    let plan = TableSortBuilder::build(request, TableSortLimits::default())?;
    let first_column_sources: Vec<_> = plan
        .relocations()
        .iter()
        .filter(|item| item.destination().column == 0)
        .map(|item| item.source().row)
        .collect();
    assert_eq!(first_column_sources, vec![2, 1, 3, 0]);
    Ok(())
}

#[test]
fn descending_does_not_reverse_explicit_blank_placement() -> TestResult {
    let grid = unmerged_grid(3, 1)?;
    let cells = vec![
        cell(0, 0, TableSortValue::Blank),
        cell(1, 0, integer(1)),
        cell(2, 0, integer(2)),
    ];
    let sort_key = TableSortKey {
        direction: TableSortDirection::Descending,
        blank_order: TableBlankOrder::First,
        ..key(0)
    };
    let request = TableSortRequest::from_draft(
        draft(3, 1, TableSortAxis::Rows, vec![sort_key], cells)?,
        &grid,
        TableSortLimits::default(),
    )?;
    let plan = TableSortBuilder::build(request, TableSortLimits::default())?;
    assert_eq!(
        plan.relocations()
            .iter()
            .map(|item| item.source().row)
            .collect::<Vec<_>>(),
        vec![0, 2, 1]
    );
    Ok(())
}

#[test]
fn column_sort_supports_explicit_ascii_case_insensitive_text() -> TestResult {
    let grid = unmerged_grid(2, 3)?;
    let cells = vec![
        cell(0, 0, text("beta")),
        cell(0, 1, text("Alpha")),
        cell(0, 2, text("alpha")),
        cell(1, 0, integer(10)),
        cell(1, 1, integer(20)),
        cell(1, 2, integer(30)),
    ];
    let sort_key = TableSortKey {
        text_collation: TableTextCollation::AsciiCaseInsensitive,
        ..key(0)
    };
    let request = TableSortRequest::from_draft(
        draft(2, 3, TableSortAxis::Columns, vec![sort_key], cells)?,
        &grid,
        TableSortLimits::default(),
    )?;
    let plan = TableSortBuilder::build(request, TableSortLimits::default())?;
    let top_row_sources: Vec<_> = plan
        .relocations()
        .iter()
        .filter(|item| item.destination().row == 0)
        .map(|item| item.source().column)
        .collect();
    assert_eq!(top_row_sources, vec![1, 2, 0]);
    Ok(())
}

#[test]
fn integer_and_fixed_decimal_compare_exactly_without_floating_point() -> TestResult {
    let grid = unmerged_grid(4, 1)?;
    let cells = vec![
        cell(
            0,
            0,
            TableSortValue::Decimal {
                coefficient: 100,
                scale: 2,
            },
        ),
        cell(1, 0, integer(2)),
        cell(
            2,
            0,
            TableSortValue::Decimal {
                coefficient: 15,
                scale: 1,
            },
        ),
        cell(3, 0, integer(1)),
    ];
    let request = TableSortRequest::from_draft(
        draft(4, 1, TableSortAxis::Rows, vec![key(0)], cells)?,
        &grid,
        TableSortLimits::default(),
    )?;
    let plan = TableSortBuilder::build(request, TableSortLimits::default())?;
    assert_eq!(
        plan.relocations()
            .iter()
            .map(|item| item.source().row)
            .collect::<Vec<_>>(),
        vec![0, 3, 2, 1]
    );
    Ok(())
}

#[test]
fn formula_policy_is_explicit_and_bound_into_relocations() -> TestResult {
    let grid = unmerged_grid(2, 1)?;
    let mut cells = vec![cell(0, 0, integer(2)), cell(1, 0, integer(1))];
    cells[0].formula_sha256 = Some(digest(900));
    let rejected = draft(2, 1, TableSortAxis::Rows, vec![key(0)], cells.clone())?;
    assert_eq!(
        TableSortRequest::from_draft(rejected, &grid, TableSortLimits::default()),
        Err(TableSortError::FormulaPresent)
    );

    let mut admitted = draft(2, 1, TableSortAxis::Rows, vec![key(0)], cells)?;
    admitted.formula_move_policy = TableFormulaMovePolicy::RebaseRelative;
    let request = TableSortRequest::from_draft(admitted, &grid, TableSortLimits::default())?;
    let plan = TableSortBuilder::build(request, TableSortLimits::default())?;
    assert_eq!(
        plan.receipt().formula_move_policy(),
        TableFormulaMovePolicy::RebaseRelative
    );
    assert_eq!(
        plan.relocations()[1].formula_sha256(),
        Some(digest(900).as_str())
    );
    Ok(())
}

#[test]
fn merged_region_fails_before_a_sort_plan_exists() -> TestResult {
    let grid = TableGrid::new(
        1,
        2,
        vec![TableCellSpan {
            master_cell_id: LogicalId::parse("merged")?,
            row: 0,
            column: 0,
            row_span: 1,
            column_span: 2,
        }],
        TableGridLimits::default(),
    )?;
    let request = draft(
        1,
        2,
        TableSortAxis::Rows,
        vec![key(0)],
        vec![cell(0, 0, integer(1)), cell(0, 1, integer(2))],
    )?;
    assert_eq!(
        TableSortRequest::from_draft(request, &grid, TableSortLimits::default()),
        Err(TableSortError::MergedCell)
    );
    Ok(())
}

#[test]
fn region_keys_cells_values_and_limits_fail_closed() -> TestResult {
    let grid = unmerged_grid(2, 2)?;
    let cells = vec![
        cell(0, 0, integer(1)),
        cell(0, 1, integer(2)),
        cell(1, 0, integer(3)),
        cell(1, 1, integer(4)),
    ];
    let mut bad_region = draft(2, 2, TableSortAxis::Rows, vec![key(0)], cells.clone())?;
    bad_region.region.start.row = 1;
    bad_region.region.end.row = 0;
    assert_eq!(
        TableSortRequest::from_draft(bad_region, &grid, TableSortLimits::default()),
        Err(TableSortError::RegionOrder)
    );

    let duplicate_keys = draft(
        2,
        2,
        TableSortAxis::Rows,
        vec![key(0), key(0)],
        cells.clone(),
    )?;
    assert_eq!(
        TableSortRequest::from_draft(duplicate_keys, &grid, TableSortLimits::default()),
        Err(TableSortError::DuplicateKey)
    );

    let mut bad_cells = cells;
    bad_cells[0].payload_sha256 = "ABC".to_owned();
    let bad_digest = draft(2, 2, TableSortAxis::Rows, vec![key(0)], bad_cells)?;
    assert_eq!(
        TableSortRequest::from_draft(bad_digest, &grid, TableSortLimits::default()),
        Err(TableSortError::DigestInvalid)
    );

    assert_eq!(
        TableSortLimits::new(TableSortLimitConfig {
            selected_cells: 0,
            ..TableSortLimitConfig::default()
        }),
        Err(TableSortError::InvalidLimit)
    );
    let work_limits = TableSortLimits::new(TableSortLimitConfig {
        comparison_work: 1,
        ..TableSortLimitConfig::default()
    })?;
    let work_cells = vec![
        cell(0, 0, integer(1)),
        cell(0, 1, integer(2)),
        cell(1, 0, integer(3)),
        cell(1, 1, integer(4)),
    ];
    assert_eq!(
        TableSortRequest::from_draft(
            draft(2, 2, TableSortAxis::Rows, vec![key(0)], work_cells)?,
            &grid,
            work_limits
        ),
        Err(TableSortError::WorkLimit)
    );
    Ok(())
}

#[test]
fn strict_json_rejects_duplicate_unknown_version_and_size() -> TestResult {
    let grid = unmerged_grid(1, 1)?;
    let value = draft(
        1,
        1,
        TableSortAxis::Rows,
        vec![key(0)],
        vec![cell(0, 0, integer(1))],
    )?;
    let bytes = serde_json::to_vec(&value)?;
    let reopened = TableSortRequest::from_json(&bytes, &grid, TableSortLimits::default())?;
    assert_eq!(reopened.capability_id(), TABLE_SORT_CAPABILITY_ID);

    let text = String::from_utf8(bytes)?;
    let duplicate = text.replacen(
        '{',
        &format!("{{\"schema_version\":\"{TABLE_SORT_SCHEMA_VERSION}\","),
        1,
    );
    assert_eq!(
        TableSortRequest::from_json(duplicate.as_bytes(), &grid, TableSortLimits::default()),
        Err(TableSortError::InvalidJson)
    );
    let unknown = text.replacen('{', "{\"unknown\":true,", 1);
    assert_eq!(
        TableSortRequest::from_json(unknown.as_bytes(), &grid, TableSortLimits::default()),
        Err(TableSortError::InvalidJson)
    );
    let wrong_version = text.replace(TABLE_SORT_SCHEMA_VERSION, "table-sort/wrong");
    assert_eq!(
        TableSortRequest::from_json(wrong_version.as_bytes(), &grid, TableSortLimits::default()),
        Err(TableSortError::UnsupportedVersion)
    );
    assert_eq!(
        TableSortRequest::from_json(&[], &grid, TableSortLimits::default()),
        Err(TableSortError::InputLimit)
    );
    Ok(())
}

#[test]
fn plan_and_receipt_are_deterministic_and_noop_is_explicit() -> TestResult {
    let grid = unmerged_grid(3, 1)?;
    let cells = vec![
        cell(0, 0, integer(1)),
        cell(1, 0, integer(2)),
        cell(2, 0, integer(3)),
    ];
    let build = || -> Result<_, Box<dyn std::error::Error>> {
        let request = TableSortRequest::from_draft(
            draft(3, 1, TableSortAxis::Rows, vec![key(0)], cells.clone())?,
            &grid,
            TableSortLimits::default(),
        )?;
        Ok(TableSortBuilder::build(
            request,
            TableSortLimits::default(),
        )?)
    };
    let first = build()?;
    let second = build()?;
    assert!(!first.receipt().changed());
    assert_eq!(
        first.canonical_json(TableSortLimits::default())?,
        second.canonical_json(TableSortLimits::default())?
    );
    assert_eq!(
        first.canonical_sha256(TableSortLimits::default())?,
        second.canonical_sha256(TableSortLimits::default())?
    );
    let mut equivalent_cells = cells;
    equivalent_cells[0].sort_value = TableSortValue::Decimal {
        coefficient: 10,
        scale: 1,
    };
    let equivalent_request = TableSortRequest::from_draft(
        draft(3, 1, TableSortAxis::Rows, vec![key(0)], equivalent_cells)?,
        &grid,
        TableSortLimits::default(),
    )?;
    assert_eq!(
        first.request().canonical_json(TableSortLimits::default())?,
        equivalent_request.canonical_json(TableSortLimits::default())?
    );
    Ok(())
}

#[test]
fn output_limit_fails_without_returning_a_partial_plan() -> TestResult {
    let grid = unmerged_grid(1, 1)?;
    let initial = TableSortRequest::from_draft(
        draft(
            1,
            1,
            TableSortAxis::Rows,
            vec![key(0)],
            vec![cell(0, 0, integer(1))],
        )?,
        &grid,
        TableSortLimits::default(),
    )?;
    let request_size = initial.canonical_json(TableSortLimits::default())?.len();
    let limits = TableSortLimits::new(TableSortLimitConfig {
        input_bytes: request_size,
        selected_cells: 1,
        sort_keys: 1,
        text_bytes: 8,
        comparison_work: 8,
        serialized_bytes: request_size + 8,
    })?;
    let request = TableSortRequest::from_draft(
        draft(
            1,
            1,
            TableSortAxis::Rows,
            vec![key(0)],
            vec![cell(0, 0, integer(1))],
        )?,
        &grid,
        limits,
    )?;
    assert_eq!(
        TableSortBuilder::build(request, limits),
        Err(TableSortError::OutputLimit)
    );
    Ok(())
}

#[test]
fn debug_output_redacts_ids_values_and_digests() -> TestResult {
    let grid = unmerged_grid(2, 1)?;
    let mut cells = vec![cell(0, 0, text("secret-cell-text")), cell(1, 0, text("x"))];
    cells[0].payload_sha256 = "a".repeat(64);
    cells[0].formula_sha256 = Some("b".repeat(64));
    let mut value = draft(2, 1, TableSortAxis::Rows, vec![key(0)], cells)?;
    value.formula_move_policy = TableFormulaMovePolicy::MoveVerbatim;
    let request = TableSortRequest::from_draft(value, &grid, TableSortLimits::default())?;
    let plan = TableSortBuilder::build(request, TableSortLimits::default())?;
    let debug = format!("{plan:?}");
    for secret in [
        "private-table",
        "secret-cell-text",
        &"a".repeat(64),
        &"b".repeat(64),
    ] {
        assert!(!debug.contains(secret));
    }
    Ok(())
}

#[test]
fn fixed_seed_permutations_sort_to_exact_numeric_order() -> TestResult {
    let grid = unmerged_grid(64, 1)?;
    let mut seed = 0x5eed_u64;
    let mut values: Vec<i64> = (0..64).collect();
    for index in (1..values.len()).rev() {
        seed = seed.wrapping_mul(6_364_136_223_846_793_005).wrapping_add(1);
        let swap = usize::try_from(seed % u64::try_from(index + 1)?)?;
        values.swap(index, swap);
    }
    let cells = values
        .iter()
        .enumerate()
        .map(|(row, value)| {
            Ok(cell(
                u32::try_from(row)?,
                0,
                TableSortValue::Integer { value: *value },
            ))
        })
        .collect::<Result<Vec<_>, Box<dyn std::error::Error>>>()?;
    let request = TableSortRequest::from_draft(
        draft(64, 1, TableSortAxis::Rows, vec![key(0)], cells)?,
        &grid,
        TableSortLimits::default(),
    )?;
    let plan = TableSortBuilder::build(request, TableSortLimits::default())?;
    let observed: Vec<_> = plan
        .relocations()
        .iter()
        .map(|item| values[usize::try_from(item.source().row).unwrap_or(usize::MAX)])
        .collect();
    assert_eq!(observed, (0..64).collect::<Vec<_>>());
    Ok(())
}

#[test]
fn public_error_codes_are_stable() {
    let cases = [
        (TableSortError::InvalidLimit, "table_sort_invalid_limit"),
        (
            TableSortError::UnsupportedVersion,
            "table_sort_unsupported_version",
        ),
        (TableSortError::InputLimit, "table_sort_input_limit"),
        (TableSortError::InvalidJson, "table_sort_invalid_json"),
        (TableSortError::RegionOrder, "table_sort_region_order"),
        (
            TableSortError::RegionOutOfBounds,
            "table_sort_region_out_of_bounds",
        ),
        (TableSortError::SelectionLimit, "table_sort_selection_limit"),
        (TableSortError::MergedCell, "table_sort_merged_cell"),
        (TableSortError::GridMismatch, "table_sort_grid_mismatch"),
        (TableSortError::KeyLimit, "table_sort_key_limit"),
        (TableSortError::DuplicateKey, "table_sort_duplicate_key"),
        (
            TableSortError::KeyOutOfBounds,
            "table_sort_key_out_of_bounds",
        ),
        (TableSortError::WorkLimit, "table_sort_work_limit"),
        (
            TableSortError::CellSetMismatch,
            "table_sort_cell_set_mismatch",
        ),
        (TableSortError::DigestInvalid, "table_sort_digest_invalid"),
        (TableSortError::SortValueInvalid, "table_sort_value_invalid"),
        (TableSortError::FormulaPresent, "table_sort_formula_present"),
        (TableSortError::OutputLimit, "table_sort_output_limit"),
        (TableSortError::Serialization, "table_sort_serialization"),
    ];
    for (error, code) in cases {
        assert_eq!(error.code(), code);
    }
}
