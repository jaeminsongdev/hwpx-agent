use domain_ir::{
    CellCoordinate, LogicalId, TABLE_AUTO_FILL_CAPABILITY_ID, TABLE_AUTO_FILL_SCHEMA_VERSION,
    TABLE_AUTO_FILL_SERIES_CAPABILITY_ID, TABLE_AUTO_FILL_SERIES_SCHEMA_VERSION,
    TableAutoFillBuilder, TableAutoFillCellDraft, TableAutoFillDefinition, TableAutoFillError,
    TableAutoFillFormulaPolicy, TableAutoFillLimitConfig, TableAutoFillLimits, TableAutoFillNumber,
    TableAutoFillOrder, TableAutoFillRegion, TableAutoFillRequest, TableAutoFillRequestDraft,
    TableAutoFillSeries, TableAutoFillSeriesDraft, TableAutoFillValue, TableCellSpan, TableGrid,
    TableGridLimits,
};

type TestResult = Result<(), Box<dyn std::error::Error>>;

fn coordinate(row: u32, column: u32) -> CellCoordinate {
    CellCoordinate { row, column }
}

fn digest(value: u64) -> String {
    format!("{value:064x}")
}

fn hex(value: [u8; 32]) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let mut output = String::with_capacity(64);
    for byte in value {
        output.push(char::from(DIGITS[usize::from(byte >> 4)]));
        output.push(char::from(DIGITS[usize::from(byte & 0x0f)]));
    }
    output
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

fn integer(value: i64) -> TableAutoFillValue {
    TableAutoFillValue::Integer { value }
}

fn text(value: &str) -> TableAutoFillValue {
    TableAutoFillValue::Text {
        value: value.to_owned(),
    }
}

fn cell(row: u32, column: u32, current_value: TableAutoFillValue) -> TableAutoFillCellDraft {
    let ordinal = u64::from(row) * 100 + u64::from(column);
    TableAutoFillCellDraft {
        coordinate: coordinate(row, column),
        payload_sha256: digest(ordinal + 1),
        formula_sha256: None,
        style_sha256: digest(ordinal + 10_000),
        current_value,
    }
}

fn series_draft(
    definition: TableAutoFillDefinition,
) -> Result<TableAutoFillSeriesDraft, Box<dyn std::error::Error>> {
    Ok(TableAutoFillSeriesDraft {
        schema_version: TABLE_AUTO_FILL_SERIES_SCHEMA_VERSION.to_owned(),
        series_id: LogicalId::parse("private-series")?,
        definition,
    })
}

fn explicit_series(
    items: Vec<TableAutoFillValue>,
) -> Result<TableAutoFillSeries, Box<dyn std::error::Error>> {
    Ok(TableAutoFillSeries::from_draft(
        series_draft(TableAutoFillDefinition::ExplicitCycle { items })?,
        TableAutoFillLimits::default(),
    )?)
}

fn request_draft(
    rows: u32,
    columns: u32,
    order: TableAutoFillOrder,
    series: &TableAutoFillSeries,
    cells: Vec<TableAutoFillCellDraft>,
) -> Result<TableAutoFillRequestDraft, Box<dyn std::error::Error>> {
    Ok(TableAutoFillRequestDraft {
        schema_version: TABLE_AUTO_FILL_SCHEMA_VERSION.to_owned(),
        table_id: LogicalId::parse("private-table")?,
        region: TableAutoFillRegion {
            start: coordinate(0, 0),
            end: coordinate(rows - 1, columns - 1),
        },
        order,
        series_id: series.series_id().clone(),
        series_sha256: hex(series.canonical_sha256(TableAutoFillLimits::default())?),
        start_index: 0,
        formula_policy: TableAutoFillFormulaPolicy::Reject,
        cells,
    })
}

fn build(
    rows: u32,
    columns: u32,
    order: TableAutoFillOrder,
    series: &TableAutoFillSeries,
    cells: Vec<TableAutoFillCellDraft>,
) -> Result<domain_ir::TableAutoFillPlan, Box<dyn std::error::Error>> {
    let grid = unmerged_grid(rows, columns)?;
    let request = TableAutoFillRequest::from_draft(
        request_draft(rows, columns, order, series, cells)?,
        series,
        &grid,
        TableAutoFillLimits::default(),
    )?;
    Ok(TableAutoFillBuilder::build(
        request,
        series,
        TableAutoFillLimits::default(),
    )?)
}

#[test]
fn explicit_cycle_fills_row_major_and_binds_preserved_cell_state() -> TestResult {
    let series = explicit_series(vec![text("A"), text("B")])?;
    assert_eq!(series.capability_id(), TABLE_AUTO_FILL_SERIES_CAPABILITY_ID);
    let cells = (0..2)
        .flat_map(|row| (0..3).map(move |column| cell(row, column, text("old"))))
        .collect();
    let plan = build(2, 3, TableAutoFillOrder::RowMajor, &series, cells)?;
    assert_eq!(
        plan.request().capability_id(),
        TABLE_AUTO_FILL_CAPABILITY_ID
    );
    let generated: Vec<_> = plan
        .mutations()
        .iter()
        .map(|mutation| mutation.generated_value().clone())
        .collect();
    assert_eq!(
        generated,
        vec![
            text("A"),
            text("B"),
            text("A"),
            text("B"),
            text("A"),
            text("B")
        ]
    );
    assert_eq!(plan.receipt().semantic_change_count(), 6);
    assert_eq!(plan.mutations()[0].prior_payload_sha256(), digest(1));
    assert_eq!(plan.mutations()[0].preserved_style_sha256(), digest(10_000));
    assert!(!plan.mutations()[0].clear_formula());
    Ok(())
}

#[test]
fn column_major_order_is_explicit_even_after_coordinate_canonicalization() -> TestResult {
    let series = explicit_series(vec![integer(10), integer(20), integer(30), integer(40)])?;
    let cells = vec![
        cell(0, 0, integer(0)),
        cell(0, 1, integer(0)),
        cell(1, 0, integer(0)),
        cell(1, 1, integer(0)),
    ];
    let plan = build(2, 2, TableAutoFillOrder::ColumnMajor, &series, cells)?;
    let observed: Vec<_> = plan
        .mutations()
        .iter()
        .map(|mutation| {
            (
                mutation.coordinate(),
                mutation.sequence_index(),
                mutation.generated_value().clone(),
            )
        })
        .collect();
    assert_eq!(
        observed,
        vec![
            (coordinate(0, 0), 0, integer(10)),
            (coordinate(0, 1), 2, integer(30)),
            (coordinate(1, 0), 1, integer(20)),
            (coordinate(1, 1), 3, integer(40)),
        ]
    );
    Ok(())
}

#[test]
fn linear_number_uses_exact_fixed_point_and_canonical_values() -> TestResult {
    let series = TableAutoFillSeries::from_draft(
        series_draft(TableAutoFillDefinition::LinearNumber {
            start: TableAutoFillNumber {
                coefficient: 150,
                scale: 2,
            },
            step: TableAutoFillNumber {
                coefficient: 25,
                scale: 2,
            },
        })?,
        TableAutoFillLimits::default(),
    )?;
    let plan = build(
        1,
        4,
        TableAutoFillOrder::RowMajor,
        &series,
        (0..4).map(|column| cell(0, column, integer(0))).collect(),
    )?;
    assert_eq!(
        plan.mutations()
            .iter()
            .map(|mutation| mutation.generated_value().clone())
            .collect::<Vec<_>>(),
        vec![
            TableAutoFillValue::Decimal {
                coefficient: 15,
                scale: 1,
            },
            TableAutoFillValue::Decimal {
                coefficient: 175,
                scale: 2,
            },
            integer(2),
            TableAutoFillValue::Decimal {
                coefficient: 225,
                scale: 2,
            },
        ]
    );
    Ok(())
}

#[test]
fn linear_date_and_start_index_are_checked_and_deterministic() -> TestResult {
    let series = TableAutoFillSeries::from_draft(
        series_draft(TableAutoFillDefinition::LinearDateDays {
            start_days_since_unix_epoch: 10,
            step_days: -2,
        })?,
        TableAutoFillLimits::default(),
    )?;
    let grid = unmerged_grid(1, 3)?;
    let cells = (0..3).map(|column| cell(0, column, integer(0))).collect();
    let mut draft = request_draft(1, 3, TableAutoFillOrder::RowMajor, &series, cells)?;
    draft.start_index = 2;
    let request =
        TableAutoFillRequest::from_draft(draft, &series, &grid, TableAutoFillLimits::default())?;
    let plan = TableAutoFillBuilder::build(request, &series, TableAutoFillLimits::default())?;
    assert_eq!(
        plan.mutations()
            .iter()
            .map(|mutation| mutation.generated_value().clone())
            .collect::<Vec<_>>(),
        vec![
            TableAutoFillValue::DateDays {
                days_since_unix_epoch: 6,
            },
            TableAutoFillValue::DateDays {
                days_since_unix_epoch: 4,
            },
            TableAutoFillValue::DateDays {
                days_since_unix_epoch: 2,
            },
        ]
    );
    Ok(())
}

#[test]
fn formula_replacement_requires_an_explicit_bound_policy() -> TestResult {
    let series = explicit_series(vec![integer(7)])?;
    let grid = unmerged_grid(1, 1)?;
    let mut formula_cell = cell(0, 0, integer(6));
    formula_cell.formula_sha256 = Some(digest(900));
    let rejected = request_draft(
        1,
        1,
        TableAutoFillOrder::RowMajor,
        &series,
        vec![formula_cell.clone()],
    )?;
    assert_eq!(
        TableAutoFillRequest::from_draft(rejected, &series, &grid, TableAutoFillLimits::default()),
        Err(TableAutoFillError::FormulaPresent)
    );
    let mut admitted = request_draft(
        1,
        1,
        TableAutoFillOrder::RowMajor,
        &series,
        vec![formula_cell],
    )?;
    admitted.formula_policy = TableAutoFillFormulaPolicy::ReplaceBound;
    let request =
        TableAutoFillRequest::from_draft(admitted, &series, &grid, TableAutoFillLimits::default())?;
    let plan = TableAutoFillBuilder::build(request, &series, TableAutoFillLimits::default())?;
    assert!(plan.mutations()[0].clear_formula());
    assert_eq!(
        plan.mutations()[0].prior_formula_sha256(),
        Some(digest(900).as_str())
    );
    assert_eq!(
        plan.receipt().formula_policy(),
        TableAutoFillFormulaPolicy::ReplaceBound
    );
    Ok(())
}

#[test]
fn merged_region_fails_before_a_fill_plan_exists() -> TestResult {
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
    let series = explicit_series(vec![integer(1)])?;
    let request = request_draft(
        1,
        2,
        TableAutoFillOrder::RowMajor,
        &series,
        vec![cell(0, 0, integer(0)), cell(0, 1, integer(0))],
    )?;
    assert_eq!(
        TableAutoFillRequest::from_draft(request, &series, &grid, TableAutoFillLimits::default()),
        Err(TableAutoFillError::MergedCell)
    );
    Ok(())
}

#[test]
fn series_and_cell_bindings_fail_closed() -> TestResult {
    let series = explicit_series(vec![integer(1)])?;
    let other = explicit_series(vec![integer(2)])?;
    let grid = unmerged_grid(1, 1)?;
    let mut wrong_series = request_draft(
        1,
        1,
        TableAutoFillOrder::RowMajor,
        &series,
        vec![cell(0, 0, integer(0))],
    )?;
    wrong_series.series_sha256 = hex(other.canonical_sha256(TableAutoFillLimits::default())?);
    assert_eq!(
        TableAutoFillRequest::from_draft(
            wrong_series,
            &series,
            &grid,
            TableAutoFillLimits::default()
        ),
        Err(TableAutoFillError::SeriesBindingMismatch)
    );
    let mut missing = request_draft(
        1,
        1,
        TableAutoFillOrder::RowMajor,
        &series,
        vec![cell(0, 0, integer(0))],
    )?;
    missing.cells[0].coordinate = coordinate(0, 1);
    assert_eq!(
        TableAutoFillRequest::from_draft(missing, &series, &grid, TableAutoFillLimits::default()),
        Err(TableAutoFillError::CellSetMismatch)
    );
    let mut bad_digest = request_draft(
        1,
        1,
        TableAutoFillOrder::RowMajor,
        &series,
        vec![cell(0, 0, integer(0))],
    )?;
    bad_digest.cells[0].style_sha256 = "ABC".to_owned();
    assert_eq!(
        TableAutoFillRequest::from_draft(
            bad_digest,
            &series,
            &grid,
            TableAutoFillLimits::default()
        ),
        Err(TableAutoFillError::DigestInvalid)
    );
    Ok(())
}

#[test]
fn value_series_selection_and_work_limits_are_finite() -> TestResult {
    assert_eq!(
        TableAutoFillLimits::new(TableAutoFillLimitConfig {
            selected_cells: 0,
            ..TableAutoFillLimitConfig::default()
        }),
        Err(TableAutoFillError::InvalidLimit)
    );
    let empty = series_draft(TableAutoFillDefinition::ExplicitCycle { items: vec![] })?;
    assert_eq!(
        TableAutoFillSeries::from_draft(empty, TableAutoFillLimits::default()),
        Err(TableAutoFillError::SeriesItemLimit)
    );
    let item_limits = TableAutoFillLimits::new(TableAutoFillLimitConfig {
        series_items: 1,
        ..TableAutoFillLimitConfig::default()
    })?;
    let too_many_items = series_draft(TableAutoFillDefinition::ExplicitCycle {
        items: vec![integer(1), integer(2)],
    })?;
    assert_eq!(
        TableAutoFillSeries::from_draft(too_many_items, item_limits),
        Err(TableAutoFillError::SeriesItemLimit)
    );
    let oversized_text = series_draft(TableAutoFillDefinition::ExplicitCycle {
        items: vec![text(&"x".repeat(16 * 1024 + 1))],
    })?;
    assert_eq!(
        TableAutoFillSeries::from_draft(oversized_text, TableAutoFillLimits::default()),
        Err(TableAutoFillError::ValueInvalid)
    );
    let aggregate_text_limits = TableAutoFillLimits::new(TableAutoFillLimitConfig {
        text_bytes: 8,
        total_text_bytes: 8,
        ..TableAutoFillLimitConfig::default()
    })?;
    let aggregate_text = series_draft(TableAutoFillDefinition::ExplicitCycle {
        items: vec![text("12345"), text("67890")],
    })?;
    assert_eq!(
        TableAutoFillSeries::from_draft(aggregate_text, aggregate_text_limits),
        Err(TableAutoFillError::ValueInvalid)
    );
    let invalid_scale = series_draft(TableAutoFillDefinition::LinearNumber {
        start: TableAutoFillNumber {
            coefficient: 1,
            scale: 19,
        },
        step: TableAutoFillNumber {
            coefficient: 1,
            scale: 0,
        },
    })?;
    assert_eq!(
        TableAutoFillSeries::from_draft(invalid_scale, TableAutoFillLimits::default()),
        Err(TableAutoFillError::ValueInvalid)
    );
    let limits = TableAutoFillLimits::new(TableAutoFillLimitConfig {
        selected_cells: 4,
        generation_work: 1,
        ..TableAutoFillLimitConfig::default()
    })?;
    let series = explicit_series(vec![integer(1)])?;
    let grid = unmerged_grid(1, 2)?;
    let selection_limits = TableAutoFillLimits::new(TableAutoFillLimitConfig {
        selected_cells: 1,
        generation_work: 2,
        ..TableAutoFillLimitConfig::default()
    })?;
    let mut selection_draft = request_draft(
        1,
        2,
        TableAutoFillOrder::RowMajor,
        &series,
        vec![cell(0, 0, integer(0)), cell(0, 1, integer(0))],
    )?;
    selection_draft.series_sha256 = hex(series.canonical_sha256(selection_limits)?);
    assert_eq!(
        TableAutoFillRequest::from_draft(selection_draft, &series, &grid, selection_limits),
        Err(TableAutoFillError::SelectionLimit)
    );
    let mut draft = request_draft(
        1,
        2,
        TableAutoFillOrder::RowMajor,
        &series,
        vec![cell(0, 0, integer(0)), cell(0, 1, integer(0))],
    )?;
    draft.series_sha256 = hex(series.canonical_sha256(limits)?);
    assert_eq!(
        TableAutoFillRequest::from_draft(draft, &series, &grid, limits),
        Err(TableAutoFillError::WorkLimit)
    );
    Ok(())
}

#[test]
fn mixed_scale_first_value_normalizes_before_i64_admission() -> TestResult {
    let mixed_scale_series = TableAutoFillSeries::from_draft(
        series_draft(TableAutoFillDefinition::LinearNumber {
            start: TableAutoFillNumber {
                coefficient: i64::MAX,
                scale: 0,
            },
            step: TableAutoFillNumber {
                coefficient: 1,
                scale: 18,
            },
        })?,
        TableAutoFillLimits::default(),
    )?;
    let single_grid = unmerged_grid(1, 1)?;
    let representable_first = TableAutoFillRequest::from_draft(
        request_draft(
            1,
            1,
            TableAutoFillOrder::RowMajor,
            &mixed_scale_series,
            vec![cell(0, 0, integer(0))],
        )?,
        &mixed_scale_series,
        &single_grid,
        TableAutoFillLimits::default(),
    )?;
    let first = TableAutoFillBuilder::build(
        representable_first,
        &mixed_scale_series,
        TableAutoFillLimits::default(),
    )?;
    assert_eq!(first.mutations()[0].generated_value(), &integer(i64::MAX));
    Ok(())
}

#[test]
fn numeric_date_and_index_overflow_return_no_partial_plan() -> TestResult {
    let number_series = TableAutoFillSeries::from_draft(
        series_draft(TableAutoFillDefinition::LinearNumber {
            start: TableAutoFillNumber {
                coefficient: i64::MAX,
                scale: 0,
            },
            step: TableAutoFillNumber {
                coefficient: 1,
                scale: 0,
            },
        })?,
        TableAutoFillLimits::default(),
    )?;
    let grid = unmerged_grid(1, 2)?;
    let request = TableAutoFillRequest::from_draft(
        request_draft(
            1,
            2,
            TableAutoFillOrder::RowMajor,
            &number_series,
            vec![cell(0, 0, integer(0)), cell(0, 1, integer(0))],
        )?,
        &number_series,
        &grid,
        TableAutoFillLimits::default(),
    )?;
    assert_eq!(
        TableAutoFillBuilder::build(request, &number_series, TableAutoFillLimits::default()),
        Err(TableAutoFillError::GenerationOverflow)
    );

    let date_series = TableAutoFillSeries::from_draft(
        series_draft(TableAutoFillDefinition::LinearDateDays {
            start_days_since_unix_epoch: i32::MAX,
            step_days: 1,
        })?,
        TableAutoFillLimits::default(),
    )?;
    let request = TableAutoFillRequest::from_draft(
        request_draft(
            1,
            2,
            TableAutoFillOrder::RowMajor,
            &date_series,
            vec![cell(0, 0, integer(0)), cell(0, 1, integer(0))],
        )?,
        &date_series,
        &grid,
        TableAutoFillLimits::default(),
    )?;
    assert_eq!(
        TableAutoFillBuilder::build(request, &date_series, TableAutoFillLimits::default()),
        Err(TableAutoFillError::GenerationOverflow)
    );

    let cycle = explicit_series(vec![integer(1)])?;
    let mut index_draft = request_draft(
        1,
        2,
        TableAutoFillOrder::RowMajor,
        &cycle,
        vec![cell(0, 0, integer(0)), cell(0, 1, integer(0))],
    )?;
    index_draft.start_index = u64::MAX;
    let request = TableAutoFillRequest::from_draft(
        index_draft,
        &cycle,
        &grid,
        TableAutoFillLimits::default(),
    )?;
    assert_eq!(
        TableAutoFillBuilder::build(request, &cycle, TableAutoFillLimits::default()),
        Err(TableAutoFillError::GenerationOverflow)
    );
    Ok(())
}

#[test]
fn strict_series_and_request_json_reject_duplicate_unknown_version_and_size() -> TestResult {
    let series_value = series_draft(TableAutoFillDefinition::ExplicitCycle {
        items: vec![integer(1)],
    })?;
    let series_bytes = serde_json::to_vec(&series_value)?;
    let series = TableAutoFillSeries::from_json(&series_bytes, TableAutoFillLimits::default())?;
    let series_text = String::from_utf8(series_bytes)?;
    let duplicate = series_text.replacen(
        '{',
        &format!("{{\"schema_version\":\"{TABLE_AUTO_FILL_SERIES_SCHEMA_VERSION}\","),
        1,
    );
    assert_eq!(
        TableAutoFillSeries::from_json(duplicate.as_bytes(), TableAutoFillLimits::default()),
        Err(TableAutoFillError::InvalidJson)
    );
    let unknown = series_text.replacen('{', "{\"unknown\":true,", 1);
    assert_eq!(
        TableAutoFillSeries::from_json(unknown.as_bytes(), TableAutoFillLimits::default()),
        Err(TableAutoFillError::InvalidJson)
    );
    let wrong_version = series_text.replace(
        TABLE_AUTO_FILL_SERIES_SCHEMA_VERSION,
        "table-auto-fill-series/wrong",
    );
    assert_eq!(
        TableAutoFillSeries::from_json(wrong_version.as_bytes(), TableAutoFillLimits::default()),
        Err(TableAutoFillError::UnsupportedSeriesVersion)
    );

    let grid = unmerged_grid(1, 1)?;
    let request_value = request_draft(
        1,
        1,
        TableAutoFillOrder::RowMajor,
        &series,
        vec![cell(0, 0, integer(0))],
    )?;
    let request_bytes = serde_json::to_vec(&request_value)?;
    let request = TableAutoFillRequest::from_json(
        &request_bytes,
        &series,
        &grid,
        TableAutoFillLimits::default(),
    )?;
    assert_eq!(request.capability_id(), TABLE_AUTO_FILL_CAPABILITY_ID);
    let request_text = String::from_utf8(request_bytes)?;
    let duplicate = request_text.replacen(
        '{',
        &format!("{{\"schema_version\":\"{TABLE_AUTO_FILL_SCHEMA_VERSION}\","),
        1,
    );
    assert_eq!(
        TableAutoFillRequest::from_json(
            duplicate.as_bytes(),
            &series,
            &grid,
            TableAutoFillLimits::default()
        ),
        Err(TableAutoFillError::InvalidJson)
    );
    let unknown = request_text.replacen('{', "{\"unknown\":true,", 1);
    assert_eq!(
        TableAutoFillRequest::from_json(
            unknown.as_bytes(),
            &series,
            &grid,
            TableAutoFillLimits::default()
        ),
        Err(TableAutoFillError::InvalidJson)
    );
    let wrong_version = request_text.replace(
        TABLE_AUTO_FILL_SCHEMA_VERSION,
        "table-auto-fill-request/wrong",
    );
    assert_eq!(
        TableAutoFillRequest::from_json(
            wrong_version.as_bytes(),
            &series,
            &grid,
            TableAutoFillLimits::default()
        ),
        Err(TableAutoFillError::UnsupportedRequestVersion)
    );
    assert_eq!(
        TableAutoFillRequest::from_json(&[], &series, &grid, TableAutoFillLimits::default()),
        Err(TableAutoFillError::InputLimit)
    );
    Ok(())
}

#[test]
fn canonical_series_request_plan_and_receipt_are_repeatable() -> TestResult {
    let make = || -> Result<_, Box<dyn std::error::Error>> {
        let series = explicit_series(vec![
            TableAutoFillValue::Decimal {
                coefficient: 10,
                scale: 1,
            },
            integer(2),
        ])?;
        let plan = build(
            1,
            2,
            TableAutoFillOrder::RowMajor,
            &series,
            vec![cell(0, 0, integer(1)), cell(0, 1, integer(2))],
        )?;
        Ok((series, plan))
    };
    let (first_series, first) = make()?;
    let (second_series, second) = make()?;
    assert_eq!(
        first_series.canonical_json(TableAutoFillLimits::default())?,
        second_series.canonical_json(TableAutoFillLimits::default())?
    );
    assert_eq!(
        first.canonical_sha256(TableAutoFillLimits::default())?,
        second.canonical_sha256(TableAutoFillLimits::default())?
    );
    assert_eq!(first.receipt().semantic_change_count(), 0);
    assert_eq!(first.receipt().request_sha256().len(), 64);
    assert_eq!(first.receipt().mutation_sha256().len(), 64);
    Ok(())
}

#[test]
fn output_limit_fails_without_returning_a_partial_plan() -> TestResult {
    let series = explicit_series(vec![integer(1)])?;
    let grid = unmerged_grid(1, 1)?;
    let initial = TableAutoFillRequest::from_draft(
        request_draft(
            1,
            1,
            TableAutoFillOrder::RowMajor,
            &series,
            vec![cell(0, 0, integer(0))],
        )?,
        &series,
        &grid,
        TableAutoFillLimits::default(),
    )?;
    let request_size = initial
        .canonical_json(TableAutoFillLimits::default())?
        .len();
    let limits = TableAutoFillLimits::new(TableAutoFillLimitConfig {
        input_bytes: request_size,
        selected_cells: 1,
        series_items: 1,
        text_bytes: 8,
        total_text_bytes: 8,
        generation_work: 1,
        serialized_bytes: request_size + 8,
    })?;
    let request = TableAutoFillRequest::from_draft(
        request_draft(
            1,
            1,
            TableAutoFillOrder::RowMajor,
            &series,
            vec![cell(0, 0, integer(0))],
        )?,
        &series,
        &grid,
        limits,
    )?;
    assert_eq!(
        TableAutoFillBuilder::build(request, &series, limits),
        Err(TableAutoFillError::OutputLimit)
    );
    Ok(())
}

#[test]
fn debug_surfaces_redact_ids_values_indices_and_digests() -> TestResult {
    let series = explicit_series(vec![text("secret-series-value")])?;
    let grid = unmerged_grid(1, 1)?;
    let mut secret_cell = cell(0, 0, text("secret-cell-value"));
    secret_cell.payload_sha256 = "a".repeat(64);
    secret_cell.style_sha256 = "b".repeat(64);
    secret_cell.formula_sha256 = Some("c".repeat(64));
    let mut draft = request_draft(
        1,
        1,
        TableAutoFillOrder::RowMajor,
        &series,
        vec![secret_cell],
    )?;
    draft.formula_policy = TableAutoFillFormulaPolicy::ReplaceBound;
    draft.start_index = 777;
    let request =
        TableAutoFillRequest::from_draft(draft, &series, &grid, TableAutoFillLimits::default())?;
    let plan = TableAutoFillBuilder::build(request, &series, TableAutoFillLimits::default())?;
    let debug = format!("{series:?} {plan:?}");
    for secret in [
        "private-series",
        "private-table",
        "secret-series-value",
        "secret-cell-value",
        "777",
        &"a".repeat(64),
        &"b".repeat(64),
        &"c".repeat(64),
    ] {
        assert!(!debug.contains(secret));
    }
    Ok(())
}

#[test]
fn fixed_seed_cycle_corpus_preserves_exact_sequence_and_styles() -> TestResult {
    let series = explicit_series((0..17).map(integer).collect())?;
    let cells = (0..16)
        .flat_map(|row| (0..16).map(move |column| cell(row, column, integer(-1))))
        .collect();
    let plan = build(16, 16, TableAutoFillOrder::RowMajor, &series, cells)?;
    assert_eq!(plan.mutations().len(), 256);
    for (index, mutation) in plan.mutations().iter().enumerate() {
        assert_eq!(
            mutation.generated_value(),
            &integer(i64::try_from(index % 17)?)
        );
        let coordinate = mutation.coordinate();
        let ordinal = u64::from(coordinate.row) * 100 + u64::from(coordinate.column);
        assert_eq!(mutation.preserved_style_sha256(), digest(ordinal + 10_000));
    }
    Ok(())
}

#[test]
fn public_error_codes_are_stable() {
    let cases = [
        (
            TableAutoFillError::InvalidLimit,
            "table_auto_fill_invalid_limit",
        ),
        (
            TableAutoFillError::UnsupportedSeriesVersion,
            "table_auto_fill_unsupported_series_version",
        ),
        (
            TableAutoFillError::UnsupportedRequestVersion,
            "table_auto_fill_unsupported_request_version",
        ),
        (
            TableAutoFillError::InputLimit,
            "table_auto_fill_input_limit",
        ),
        (
            TableAutoFillError::InvalidJson,
            "table_auto_fill_invalid_json",
        ),
        (
            TableAutoFillError::SeriesItemLimit,
            "table_auto_fill_series_item_limit",
        ),
        (
            TableAutoFillError::ValueInvalid,
            "table_auto_fill_value_invalid",
        ),
        (
            TableAutoFillError::SeriesBindingMismatch,
            "table_auto_fill_series_binding_mismatch",
        ),
        (
            TableAutoFillError::RegionOrder,
            "table_auto_fill_region_order",
        ),
        (
            TableAutoFillError::RegionOutOfBounds,
            "table_auto_fill_region_out_of_bounds",
        ),
        (
            TableAutoFillError::SelectionLimit,
            "table_auto_fill_selection_limit",
        ),
        (
            TableAutoFillError::MergedCell,
            "table_auto_fill_merged_cell",
        ),
        (
            TableAutoFillError::GridMismatch,
            "table_auto_fill_grid_mismatch",
        ),
        (
            TableAutoFillError::CellSetMismatch,
            "table_auto_fill_cell_set_mismatch",
        ),
        (
            TableAutoFillError::DigestInvalid,
            "table_auto_fill_digest_invalid",
        ),
        (
            TableAutoFillError::FormulaPresent,
            "table_auto_fill_formula_present",
        ),
        (TableAutoFillError::WorkLimit, "table_auto_fill_work_limit"),
        (
            TableAutoFillError::GenerationOverflow,
            "table_auto_fill_generation_overflow",
        ),
        (
            TableAutoFillError::OutputLimit,
            "table_auto_fill_output_limit",
        ),
        (
            TableAutoFillError::Serialization,
            "table_auto_fill_serialization",
        ),
    ];
    for (error, code) in cases {
        assert_eq!(error.code(), code);
    }
}
