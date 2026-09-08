use std::collections::BTreeMap;

use domain_ir::{
    CellCoordinate, FormulaDecimal, LogicalId, TABLE_CHART_FROM_TABLE_CAPABILITY_ID,
    TABLE_CHART_SCHEMA_VERSION, TABLE_GRID_SCHEMA_VERSION, TableCellSpan, TableChartBuilder,
    TableChartCellDraft, TableChartError, TableChartInitialType, TableChartInsertionContext,
    TableChartLimitConfig, TableChartLimits, TableChartRegion, TableChartRequest,
    TableChartRequestDraft, TableChartSourceState, TableChartSourceStateDraft, TableChartValue,
    TableChartValueOrigin, TableGrid, TableGridDraft, TableGridLimits,
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

fn merged_grid() -> Result<TableGrid, Box<dyn std::error::Error>> {
    Ok(TableGrid::from_draft(
        TableGridDraft {
            schema_version: TABLE_GRID_SCHEMA_VERSION.to_owned(),
            rows: 3,
            columns: 3,
            master_cells: vec![
                TableCellSpan {
                    master_cell_id: id("cell-0-0")?,
                    row: 0,
                    column: 0,
                    row_span: 1,
                    column_span: 1,
                },
                TableCellSpan {
                    master_cell_id: id("cell-0-1")?,
                    row: 0,
                    column: 1,
                    row_span: 1,
                    column_span: 2,
                },
                TableCellSpan {
                    master_cell_id: id("cell-1-0")?,
                    row: 1,
                    column: 0,
                    row_span: 1,
                    column_span: 1,
                },
                TableCellSpan {
                    master_cell_id: id("cell-1-1")?,
                    row: 1,
                    column: 1,
                    row_span: 1,
                    column_span: 1,
                },
                TableCellSpan {
                    master_cell_id: id("cell-1-2")?,
                    row: 1,
                    column: 2,
                    row_span: 1,
                    column_span: 1,
                },
                TableCellSpan {
                    master_cell_id: id("cell-2-0")?,
                    row: 2,
                    column: 0,
                    row_span: 1,
                    column_span: 1,
                },
                TableCellSpan {
                    master_cell_id: id("cell-2-1")?,
                    row: 2,
                    column: 1,
                    row_span: 1,
                    column_span: 1,
                },
                TableCellSpan {
                    master_cell_id: id("cell-2-2")?,
                    row: 2,
                    column: 2,
                    row_span: 1,
                    column_span: 1,
                },
            ],
        },
        TableGridLimits::default(),
    )?)
}

fn default_value(coordinate: CellCoordinate) -> TableChartValue {
    if coordinate.row == 0 && coordinate.column == 0 {
        TableChartValue::Text {
            value: "ignored corner".to_owned(),
        }
    } else if coordinate.row == 0 {
        TableChartValue::Text {
            value: format!("Series {}", coordinate.column),
        }
    } else if coordinate.column == 0 {
        TableChartValue::Text {
            value: format!("Category {}", coordinate.row),
        }
    } else {
        TableChartValue::Number {
            value: FormulaDecimal::new(i64::from(coordinate.row * 10 + coordinate.column), 0),
        }
    }
}

fn state_draft(
    grid: &TableGrid,
    overrides: &BTreeMap<CellCoordinate, (TableChartValue, TableChartValueOrigin)>,
) -> Result<TableChartSourceStateDraft, Box<dyn std::error::Error>> {
    let digest_characters = ['a', 'b', 'c', 'd', 'e', 'f'];
    let mut cells = Vec::new();
    for (index, span) in grid.master_cells().iter().enumerate() {
        let coordinate = CellCoordinate {
            row: span.row,
            column: span.column,
        };
        let (value, value_origin) = overrides
            .get(&coordinate)
            .cloned()
            .unwrap_or_else(|| (default_value(coordinate), TableChartValueOrigin::Literal));
        cells.push(TableChartCellDraft {
            master_cell_id: span.master_cell_id.clone(),
            coordinate,
            source_sha256: digest(digest_characters[index % digest_characters.len()]),
            value,
            value_origin,
        });
    }
    Ok(TableChartSourceStateDraft {
        schema_version: TABLE_CHART_SCHEMA_VERSION.to_owned(),
        table_id: id("table-main")?,
        grid_sha256: hex(grid.canonical_sha256()?),
        table_state_sha256: digest('f'),
        cells,
    })
}

fn state(
    grid: &TableGrid,
    overrides: &BTreeMap<CellCoordinate, (TableChartValue, TableChartValueOrigin)>,
) -> Result<TableChartSourceState, Box<dyn std::error::Error>> {
    Ok(TableChartSourceState::from_draft(
        state_draft(grid, overrides)?,
        grid,
        TableChartLimits::default(),
    )?)
}

fn request(
    grid: &TableGrid,
    state: &TableChartSourceState,
    source_region: TableChartRegion,
) -> Result<TableChartRequest, Box<dyn std::error::Error>> {
    Ok(TableChartRequest::from_draft(
        TableChartRequestDraft {
            schema_version: TABLE_CHART_SCHEMA_VERSION.to_owned(),
            table_id: state.table_id().clone(),
            chart_id: id("chart-new")?,
            data_resource_id: id("chart-data-new")?,
            source_region,
            expected_source_state_sha256: hex(state.canonical_sha256(TableChartLimits::default())?),
            expected_document_flow_sha256: digest('e'),
        },
        state,
        grid,
        &digest('e'),
        TableChartLimits::default(),
    )?)
}

fn full_region() -> TableChartRegion {
    TableChartRegion {
        start: CellCoordinate { row: 0, column: 0 },
        end: CellCoordinate { row: 2, column: 2 },
    }
}

#[test]
fn linked_cell_block_projects_default_chart_roles_and_preserves_source() -> TestResult {
    let grid = unmerged_grid(3, 3)?;
    let formula_coordinate = CellCoordinate { row: 2, column: 2 };
    let mut overrides = BTreeMap::new();
    overrides.insert(
        formula_coordinate,
        (
            TableChartValue::Number {
                value: FormulaDecimal::new(125, 1),
            },
            TableChartValueOrigin::FormulaDisplayCache {
                formula_sha256: digest('a'),
                cache_sha256: digest('b'),
            },
        ),
    );
    let state = state(&grid, &overrides)?;
    let request = request(&grid, &state, full_region())?;
    assert_eq!(
        request.capability_id(),
        TABLE_CHART_FROM_TABLE_CAPABILITY_ID
    );

    let plan = TableChartBuilder::build(
        &request,
        &state,
        &grid,
        &digest('e'),
        TableChartLimits::default(),
    )?;
    assert_eq!(
        plan.initial_type(),
        TableChartInitialType::ThreeDimensionalVerticalBar
    );
    assert_eq!(
        plan.insertion_context(),
        TableChartInsertionContext::ExactSelectedCellBlock
    );
    assert_eq!(plan.capability_id(), TABLE_CHART_FROM_TABLE_CAPABILITY_ID);
    assert_eq!(plan.table_id().as_str(), "table-main");
    assert_eq!(plan.chart_id().as_str(), "chart-new");
    assert_eq!(plan.data_resource_id().as_str(), "chart-data-new");
    assert_eq!(plan.source_region(), full_region());
    assert_eq!(plan.categories().len(), 2);
    assert_eq!(plan.categories()[0].label(), "Category 1");
    assert_eq!(plan.categories()[1].coordinate().row, 2);
    assert_eq!(plan.series().len(), 2);
    assert_eq!(plan.series()[0].label(), "Series 1");
    assert_eq!(plan.series()[0].header_source_sha256().len(), 64);
    assert_eq!(plan.series()[0].values().len(), 2);
    assert_eq!(
        plan.series()[1].values()[1].value(),
        Some(FormulaDecimal::new(125, 1))
    );
    assert!(matches!(
        plan.series()[1].values()[1].value_origin(),
        TableChartValueOrigin::FormulaDisplayCache { .. }
    ));
    assert_eq!(plan.receipt().ignored_corner, full_region().start);
    assert_eq!(plan.receipt().data_point_count, 4);
    assert_eq!(plan.receipt().blank_data_point_count, 0);
    assert!(plan.receipt().source_table_preserved);
    assert_eq!(
        plan.receipt().source_state_sha256_before,
        plan.receipt().source_state_sha256_after
    );
    assert_eq!(
        plan.canonical_sha256(TableChartLimits::default())?,
        plan.canonical_sha256(TableChartLimits::default())?
    );
    Ok(())
}

#[test]
fn blank_body_value_is_preserved_as_missing_data_point() -> TestResult {
    let grid = unmerged_grid(3, 3)?;
    let mut overrides = BTreeMap::new();
    overrides.insert(
        CellCoordinate { row: 1, column: 2 },
        (TableChartValue::Blank, TableChartValueOrigin::Literal),
    );
    let state = state(&grid, &overrides)?;
    let request = request(&grid, &state, full_region())?;
    let plan = TableChartBuilder::build(
        &request,
        &state,
        &grid,
        &digest('e'),
        TableChartLimits::default(),
    )?;
    assert_eq!(plan.receipt().blank_data_point_count, 1);
    assert_eq!(plan.series()[1].values()[0].value(), None);
    Ok(())
}

#[test]
fn numeric_headers_are_rendered_as_exact_decimal_labels() -> TestResult {
    let grid = unmerged_grid(3, 3)?;
    let mut overrides = BTreeMap::new();
    overrides.insert(
        CellCoordinate { row: 0, column: 1 },
        (
            TableChartValue::Number {
                value: FormulaDecimal::new(-5, 2),
            },
            TableChartValueOrigin::Literal,
        ),
    );
    overrides.insert(
        CellCoordinate { row: 1, column: 0 },
        (
            TableChartValue::Number {
                value: FormulaDecimal::new(25, 1),
            },
            TableChartValueOrigin::Literal,
        ),
    );
    let state = state(&grid, &overrides)?;
    let request = request(&grid, &state, full_region())?;
    let plan = TableChartBuilder::build(
        &request,
        &state,
        &grid,
        &digest('e'),
        TableChartLimits::default(),
    )?;
    assert_eq!(plan.series()[0].label(), "-0.05");
    assert_eq!(plan.categories()[0].label(), "2.5");
    Ok(())
}

#[test]
fn subregion_is_exact_and_does_not_admit_cursor_only_creation() -> TestResult {
    let grid = unmerged_grid(4, 4)?;
    let state = state(&grid, &BTreeMap::new())?;
    let region = TableChartRegion {
        start: CellCoordinate { row: 1, column: 1 },
        end: CellCoordinate { row: 3, column: 3 },
    };
    let request = request(&grid, &state, region)?;
    let plan = TableChartBuilder::build(
        &request,
        &state,
        &grid,
        &digest('e'),
        TableChartLimits::default(),
    )?;
    assert_eq!(plan.categories().len(), 2);
    assert_eq!(plan.series().len(), 2);

    let error = TableChartRequest::from_draft(
        TableChartRequestDraft {
            schema_version: TABLE_CHART_SCHEMA_VERSION.to_owned(),
            table_id: state.table_id().clone(),
            chart_id: id("chart-new")?,
            data_resource_id: id("chart-data-new")?,
            source_region: TableChartRegion {
                start: CellCoordinate { row: 1, column: 1 },
                end: CellCoordinate { row: 1, column: 1 },
            },
            expected_source_state_sha256: hex(state.canonical_sha256(TableChartLimits::default())?),
            expected_document_flow_sha256: digest('e'),
        },
        &state,
        &grid,
        &digest('e'),
        TableChartLimits::default(),
    )
    .err()
    .ok_or("cursor-only/default-data chart creation was accepted")?;
    assert_eq!(error, TableChartError::InvalidRegion);
    Ok(())
}

#[test]
fn text_in_numeric_body_fails_closed() -> TestResult {
    let grid = unmerged_grid(3, 3)?;
    let mut overrides = BTreeMap::new();
    overrides.insert(
        CellCoordinate { row: 1, column: 1 },
        (
            TableChartValue::Text {
                value: "not a number".to_owned(),
            },
            TableChartValueOrigin::Literal,
        ),
    );
    let state = state(&grid, &overrides)?;
    let request = request(&grid, &state, full_region())?;
    assert_eq!(
        TableChartBuilder::build(
            &request,
            &state,
            &grid,
            &digest('e'),
            TableChartLimits::default(),
        ),
        Err(TableChartError::NonNumericDataCell)
    );
    Ok(())
}

#[test]
fn merged_cell_in_selected_block_fails_closed() -> TestResult {
    let grid = merged_grid()?;
    let state = state(&grid, &BTreeMap::new())?;
    let error = request(&grid, &state, full_region())
        .err()
        .ok_or("merged source was accepted")?;
    assert_eq!(
        error.downcast_ref::<TableChartError>(),
        Some(&TableChartError::MergedCellInSource)
    );
    Ok(())
}

#[test]
fn state_requires_complete_unique_grid_coverage() -> TestResult {
    let grid = unmerged_grid(3, 3)?;
    let mut incomplete = state_draft(&grid, &BTreeMap::new())?;
    let _ = incomplete.cells.pop();
    assert_eq!(
        TableChartSourceState::from_draft(incomplete, &grid, TableChartLimits::default()),
        Err(TableChartError::IncompleteCellSet)
    );

    let mut duplicate = state_draft(&grid, &BTreeMap::new())?;
    duplicate.cells[8].coordinate = duplicate.cells[0].coordinate;
    duplicate.cells[8].master_cell_id = duplicate.cells[0].master_cell_id.clone();
    assert_eq!(
        TableChartSourceState::from_draft(duplicate, &grid, TableChartLimits::default()),
        Err(TableChartError::DuplicateCell)
    );
    Ok(())
}

#[test]
fn nfc_scale_and_formula_origin_digests_are_validated() -> TestResult {
    let grid = unmerged_grid(3, 3)?;
    let coordinate = CellCoordinate { row: 0, column: 1 };
    let mut non_nfc = BTreeMap::new();
    non_nfc.insert(
        coordinate,
        (
            TableChartValue::Text {
                value: "e\u{301}".to_owned(),
            },
            TableChartValueOrigin::Literal,
        ),
    );
    assert_eq!(
        state(&grid, &non_nfc)
            .err()
            .ok_or("non-NFC text was accepted")?
            .downcast_ref(),
        Some(&TableChartError::NonCanonicalText)
    );

    let tight_limits = TableChartLimits::new(TableChartLimitConfig {
        decimal_scale: 2,
        ..TableChartLimitConfig::default()
    })?;
    let mut scale_draft = state_draft(&grid, &BTreeMap::new())?;
    scale_draft.cells[4].value = TableChartValue::Number {
        value: FormulaDecimal::new(1, 3),
    };
    assert_eq!(
        TableChartSourceState::from_draft(scale_draft, &grid, tight_limits),
        Err(TableChartError::InvalidNumber)
    );

    let mut bad_origin = state_draft(&grid, &BTreeMap::new())?;
    bad_origin.cells[4].value_origin = TableChartValueOrigin::FormulaDisplayCache {
        formula_sha256: "bad".to_owned(),
        cache_sha256: digest('a'),
    };
    assert_eq!(
        TableChartSourceState::from_draft(bad_origin, &grid, TableChartLimits::default()),
        Err(TableChartError::InvalidDigest)
    );
    Ok(())
}

#[test]
fn request_and_build_both_reject_state_or_flow_drift() -> TestResult {
    let grid = unmerged_grid(3, 3)?;
    let state = state(&grid, &BTreeMap::new())?;
    let mut draft = TableChartRequestDraft {
        schema_version: TABLE_CHART_SCHEMA_VERSION.to_owned(),
        table_id: state.table_id().clone(),
        chart_id: id("chart-new")?,
        data_resource_id: id("chart-data-new")?,
        source_region: full_region(),
        expected_source_state_sha256: digest('a'),
        expected_document_flow_sha256: digest('e'),
    };
    assert_eq!(
        TableChartRequest::from_draft(
            draft.clone(),
            &state,
            &grid,
            &digest('e'),
            TableChartLimits::default(),
        ),
        Err(TableChartError::StateBindingMismatch)
    );
    draft.expected_source_state_sha256 = hex(state.canonical_sha256(TableChartLimits::default())?);
    assert_eq!(
        TableChartRequest::from_draft(
            draft,
            &state,
            &grid,
            &digest('d'),
            TableChartLimits::default(),
        ),
        Err(TableChartError::FlowBindingMismatch)
    );

    let request = request(&grid, &state, full_region())?;
    assert_eq!(
        TableChartBuilder::build(
            &request,
            &state,
            &grid,
            &digest('d'),
            TableChartLimits::default(),
        ),
        Err(TableChartError::FlowBindingMismatch)
    );
    let mut changed_draft = state_draft(&grid, &BTreeMap::new())?;
    changed_draft.table_state_sha256 = digest('a');
    let changed_state =
        TableChartSourceState::from_draft(changed_draft, &grid, TableChartLimits::default())?;
    assert_eq!(
        TableChartBuilder::build(
            &request,
            &changed_state,
            &grid,
            &digest('e'),
            TableChartLimits::default(),
        ),
        Err(TableChartError::StateBindingMismatch)
    );
    Ok(())
}

#[test]
fn identifier_collisions_fail_before_planning() -> TestResult {
    let grid = unmerged_grid(3, 3)?;
    let state = state(&grid, &BTreeMap::new())?;
    let error = TableChartRequest::from_draft(
        TableChartRequestDraft {
            schema_version: TABLE_CHART_SCHEMA_VERSION.to_owned(),
            table_id: state.table_id().clone(),
            chart_id: state.table_id().clone(),
            data_resource_id: id("chart-data-new")?,
            source_region: full_region(),
            expected_source_state_sha256: hex(state.canonical_sha256(TableChartLimits::default())?),
            expected_document_flow_sha256: digest('e'),
        },
        &state,
        &grid,
        &digest('e'),
        TableChartLimits::default(),
    )
    .err()
    .ok_or("colliding IDs were accepted")?;
    assert_eq!(error, TableChartError::IdentifierCollision);
    Ok(())
}

#[test]
fn canonical_state_is_deterministic_and_json_is_strict() -> TestResult {
    let grid = unmerged_grid(3, 3)?;
    let ordered = state_draft(&grid, &BTreeMap::new())?;
    let mut reversed = ordered.clone();
    reversed.cells.reverse();
    let ordered = TableChartSourceState::from_draft(ordered, &grid, TableChartLimits::default())?;
    let reversed = TableChartSourceState::from_draft(reversed, &grid, TableChartLimits::default())?;
    assert_eq!(
        ordered.canonical_json(TableChartLimits::default())?,
        reversed.canonical_json(TableChartLimits::default())?
    );
    let bytes = ordered.canonical_json(TableChartLimits::default())?;
    let parsed = TableChartSourceState::from_json(&bytes, &grid, TableChartLimits::default())?;
    assert_eq!(parsed, ordered);

    let mut value: serde_json::Value = serde_json::from_slice(&bytes)?;
    value["unexpected"] = serde_json::Value::Bool(true);
    assert_eq!(
        TableChartSourceState::from_json(
            &serde_json::to_vec(&value)?,
            &grid,
            TableChartLimits::default(),
        ),
        Err(TableChartError::InvalidJson)
    );
    Ok(())
}

#[test]
fn finite_input_output_and_debug_redaction_are_enforced() -> TestResult {
    let grid = unmerged_grid(3, 3)?;
    let state = state(&grid, &BTreeMap::new())?;
    let bytes = state.canonical_json(TableChartLimits::default())?;
    let input_limits = TableChartLimits::new(TableChartLimitConfig {
        input_bytes: bytes.len() - 1,
        serialized_bytes: bytes.len() + 1024,
        ..TableChartLimitConfig::default()
    })?;
    assert_eq!(
        TableChartSourceState::from_json(&bytes, &grid, input_limits),
        Err(TableChartError::InputLimitExceeded)
    );

    let output_limits = TableChartLimits::new(TableChartLimitConfig {
        input_bytes: 128,
        serialized_bytes: 128,
        ..TableChartLimitConfig::default()
    })?;
    assert_eq!(
        state.canonical_json(output_limits),
        Err(TableChartError::SerializedLimitExceeded)
    );

    let debug = format!("{state:?}");
    assert!(!debug.contains("table-main"));
    assert!(!debug.contains(&digest('f')));
    let plan = TableChartBuilder::build(
        &request(&grid, &state, full_region())?,
        &state,
        &grid,
        &digest('e'),
        TableChartLimits::default(),
    )?;
    let plan_debug = format!("{plan:?}");
    assert!(!plan_debug.contains("Series 1"));
    assert!(!plan_debug.contains("chart-new"));
    let origin_debug = format!(
        "{:?}",
        TableChartValueOrigin::FormulaDisplayCache {
            formula_sha256: digest('a'),
            cache_sha256: digest('b'),
        }
    );
    assert!(!origin_debug.contains(&digest('a')));
    let receipt_debug = format!("{:?}", plan.receipt());
    assert!(!receipt_debug.contains(&digest('e')));
    Ok(())
}
