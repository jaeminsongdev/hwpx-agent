use domain_ir::{
    CellCoordinate, LogicalId, TABLE_CELL_BORDER_EACH_CAPABILITY_ID,
    TABLE_CELL_BORDER_UNIFIED_CAPABILITY_ID, TABLE_GRID_SCHEMA_VERSION,
    TABLE_PROPERTIES_CAPABILITY_ID, TABLE_PROPERTIES_SCHEMA_VERSION, TableBorderEdgeRole,
    TableCellBorderPatch, TableCellBorderState, TableCellPropertyDraft, TableCellPropertyValue,
    TableCellSpan, TableGrid, TableGridDraft, TableGridLimits, TablePropertiesBuilder,
    TablePropertiesError, TablePropertiesLimitConfig, TablePropertiesLimits,
    TablePropertiesOperation, TablePropertiesRequest, TablePropertiesRequestDraft,
    TablePropertiesState, TablePropertiesStateDraft, TablePropertyDigestPatch,
    TableUnifiedBorderPatch,
};

type TestResult = Result<(), Box<dyn std::error::Error>>;

fn id(value: &str) -> Result<LogicalId, Box<dyn std::error::Error>> {
    Ok(LogicalId::parse(value)?)
}

fn digest(character: char) -> String {
    let normalized = match character {
        '0'..='9' | 'a'..='f' => character,
        'p' => '8',
        't' => '9',
        'u' => '0',
        'z' => '7',
        _ => '6',
    };
    std::iter::repeat_n(normalized, 64).collect()
}

fn set(character: char) -> TablePropertyDigestPatch {
    TablePropertyDigestPatch::Set {
        sha256: digest(character),
    }
}

fn preserve() -> TablePropertyDigestPatch {
    TablePropertyDigestPatch::Preserve
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
    Ok(TableGrid::new(
        2,
        3,
        vec![
            TableCellSpan {
                master_cell_id: id("merged")?,
                row: 0,
                column: 0,
                row_span: 1,
                column_span: 2,
            },
            TableCellSpan {
                master_cell_id: id("top-right")?,
                row: 0,
                column: 2,
                row_span: 1,
                column_span: 1,
            },
            TableCellSpan {
                master_cell_id: id("bottom-left")?,
                row: 1,
                column: 0,
                row_span: 1,
                column_span: 1,
            },
            TableCellSpan {
                master_cell_id: id("bottom-middle")?,
                row: 1,
                column: 1,
                row_span: 1,
                column_span: 1,
            },
            TableCellSpan {
                master_cell_id: id("bottom-right")?,
                row: 1,
                column: 2,
                row_span: 1,
                column_span: 1,
            },
        ],
        TableGridLimits::default(),
    )?)
}

fn value(index: usize) -> TableCellPropertyValue {
    const HEX: &[u8; 16] = b"0123456789abcdef";
    let character = char::from(HEX[index % HEX.len()]);
    TableCellPropertyValue {
        non_border_properties_sha256: digest(character),
        borders: TableCellBorderState {
            top_sha256: None,
            right_sha256: None,
            bottom_sha256: None,
            left_sha256: None,
        },
        background_sha256: None,
        diagonal_sha256: Some(digest('d')),
    }
}

fn state_draft(
    grid: &TableGrid,
    table_property_character: char,
) -> Result<TablePropertiesStateDraft, Box<dyn std::error::Error>> {
    let cells = grid
        .master_cells()
        .iter()
        .enumerate()
        .map(|(index, span)| TableCellPropertyDraft {
            master_cell_id: span.master_cell_id.clone(),
            coordinate: CellCoordinate {
                row: span.row,
                column: span.column,
            },
            payload_sha256: digest('p'),
            formula_sha256: (index == 0).then(|| digest('f')),
            properties: value(index),
        })
        .collect();
    Ok(TablePropertiesStateDraft {
        schema_version: TABLE_PROPERTIES_SCHEMA_VERSION.to_owned(),
        table_id: id("table-private")?,
        grid_sha256: hex(grid.canonical_sha256()?),
        table_properties_sha256: digest(table_property_character),
        cells,
    })
}

fn state(grid: &TableGrid) -> Result<TablePropertiesState, Box<dyn std::error::Error>> {
    Ok(TablePropertiesState::from_draft(
        state_draft(grid, 't')?,
        grid,
        TablePropertiesLimits::default(),
    )?)
}

fn slots(row: u32, column: u32, rows: u32, columns: u32) -> Vec<CellCoordinate> {
    let mut result = Vec::new();
    for current_row in row..row + rows {
        for current_column in column..column + columns {
            result.push(CellCoordinate {
                row: current_row,
                column: current_column,
            });
        }
    }
    result
}

fn request(
    state: &TablePropertiesState,
    grid: &TableGrid,
    selected_slots: Vec<CellCoordinate>,
    operation: TablePropertiesOperation,
) -> Result<TablePropertiesRequest, Box<dyn std::error::Error>> {
    Ok(TablePropertiesRequest::from_draft(
        TablePropertiesRequestDraft {
            schema_version: TABLE_PROPERTIES_SCHEMA_VERSION.to_owned(),
            table_id: state.table_id().clone(),
            expected_state_sha256: hex(state.canonical_sha256(TablePropertiesLimits::default())?),
            selected_slots,
            operation,
        },
        state,
        grid,
        TablePropertiesLimits::default(),
    )?)
}

fn each_operation() -> TablePropertiesOperation {
    TablePropertiesOperation::BorderEach {
        border: TableCellBorderPatch {
            top: set('1'),
            right: set('2'),
            bottom: set('3'),
            left: set('4'),
        },
        background: set('5'),
    }
}

fn unified_operation() -> TablePropertiesOperation {
    TablePropertiesOperation::BorderUnified {
        border: TableUnifiedBorderPatch {
            outer_top: set('1'),
            outer_right: set('2'),
            outer_bottom: set('3'),
            outer_left: set('4'),
            inner_horizontal: set('5'),
            inner_vertical: set('6'),
        },
        background: set('7'),
    }
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

#[test]
fn table_only_properties_change_preserves_every_cell_without_selection() -> TestResult {
    let grid = unmerged_grid(2, 2)?;
    let state = state(&grid)?;
    let request = request(
        &state,
        &grid,
        Vec::new(),
        TablePropertiesOperation::SetProperties {
            table_properties_sha256: Some(digest('z')),
            cell_properties_sha256: None,
        },
    )?;
    assert_eq!(request.capability_id(), TABLE_PROPERTIES_CAPABILITY_ID);
    assert_eq!(request.region(), None);
    let plan =
        TablePropertiesBuilder::build(&request, &state, &grid, TablePropertiesLimits::default())?;
    assert!(plan.receipt().table_properties_changed);
    assert_eq!(plan.table_properties_sha256(), digest('z'));
    assert!(plan.mutations().is_empty());
    assert_eq!(plan.receipt().unselected_master_cell_preserved_count, 4);
    assert_eq!(plan.receipt().payload_preserved_count, 4);
    assert_eq!(plan.receipt().formula_preserved_count, 1);
    assert_eq!(plan.receipt().diagonal_preserved_count, 4);
    Ok(())
}

#[test]
fn selected_cell_properties_change_only_the_declared_non_border_facet() -> TestResult {
    let grid = unmerged_grid(3, 3)?;
    let state = state(&grid)?;
    let request = request(
        &state,
        &grid,
        slots(1, 1, 2, 2),
        TablePropertiesOperation::SetProperties {
            table_properties_sha256: None,
            cell_properties_sha256: Some(digest('f')),
        },
    )?;
    let plan =
        TablePropertiesBuilder::build(&request, &state, &grid, TablePropertiesLimits::default())?;
    assert_eq!(plan.mutations().len(), 4);
    assert_eq!(plan.receipt().changed_master_cell_count, 4);
    assert_eq!(plan.receipt().cell_properties_change_count, 4);
    assert_eq!(plan.receipt().border_side_change_count, 0);
    assert_eq!(plan.receipt().background_change_count, 0);
    assert_eq!(plan.receipt().unselected_master_cell_preserved_count, 5);
    for mutation in plan.mutations() {
        assert_eq!(mutation.after.non_border_properties_sha256, digest('f'));
        assert_eq!(mutation.before.borders, mutation.after.borders);
        assert_eq!(
            mutation.before.background_sha256,
            mutation.after.background_sha256
        );
        assert_eq!(
            mutation.before.diagonal_sha256,
            mutation.after.diagonal_sha256
        );
        assert_eq!(mutation.payload_sha256, digest('p'));
    }
    Ok(())
}

#[test]
fn each_cell_border_applies_four_independent_edges_and_background_per_master() -> TestResult {
    let grid = unmerged_grid(3, 3)?;
    let state = state(&grid)?;
    let request = request(&state, &grid, slots(1, 1, 2, 2), each_operation())?;
    assert_eq!(
        request.capability_id(),
        TABLE_CELL_BORDER_EACH_CAPABILITY_ID
    );
    let plan =
        TablePropertiesBuilder::build(&request, &state, &grid, TablePropertiesLimits::default())?;
    assert_eq!(plan.mutations().len(), 4);
    assert_eq!(plan.receipt().border_side_change_count, 16);
    assert_eq!(plan.receipt().background_change_count, 4);
    assert_eq!(plan.receipt().per_cell_edge_assignment_count, 16);
    assert_eq!(plan.receipt().outer_edge_assignment_count, 0);
    assert_eq!(plan.receipt().inner_edge_assignment_count, 0);
    for mutation in plan.mutations() {
        assert_eq!(mutation.after.borders.top_sha256, Some(digest('1')));
        assert_eq!(mutation.after.borders.right_sha256, Some(digest('2')));
        assert_eq!(mutation.after.borders.bottom_sha256, Some(digest('3')));
        assert_eq!(mutation.after.borders.left_sha256, Some(digest('4')));
        assert_eq!(mutation.after.background_sha256, Some(digest('5')));
        let roles = mutation.border_roles.ok_or("missing each-cell roles")?;
        assert_eq!(roles.top, TableBorderEdgeRole::PerCell);
        assert_eq!(roles.right, TableBorderEdgeRole::PerCell);
        assert_eq!(roles.bottom, TableBorderEdgeRole::PerCell);
        assert_eq!(roles.left, TableBorderEdgeRole::PerCell);
    }
    Ok(())
}

#[test]
fn unified_border_maps_outer_frame_and_internal_grid_lines_separately() -> TestResult {
    let grid = unmerged_grid(3, 3)?;
    let state = state(&grid)?;
    let request = request(&state, &grid, slots(1, 1, 2, 2), unified_operation())?;
    assert_eq!(
        request.capability_id(),
        TABLE_CELL_BORDER_UNIFIED_CAPABILITY_ID
    );
    let plan =
        TablePropertiesBuilder::build(&request, &state, &grid, TablePropertiesLimits::default())?;
    assert_eq!(plan.receipt().outer_edge_assignment_count, 8);
    assert_eq!(plan.receipt().inner_edge_assignment_count, 8);
    assert_eq!(plan.receipt().border_side_change_count, 16);
    let top_left = &plan.mutations()[0];
    assert_eq!(top_left.coordinate, CellCoordinate { row: 1, column: 1 });
    assert_eq!(top_left.after.borders.top_sha256, Some(digest('1')));
    assert_eq!(top_left.after.borders.left_sha256, Some(digest('4')));
    assert_eq!(top_left.after.borders.right_sha256, Some(digest('6')));
    assert_eq!(top_left.after.borders.bottom_sha256, Some(digest('5')));
    let roles = top_left.border_roles.ok_or("missing unified roles")?;
    assert_eq!(roles.top, TableBorderEdgeRole::SelectionOuter);
    assert_eq!(roles.left, TableBorderEdgeRole::SelectionOuter);
    assert_eq!(roles.right, TableBorderEdgeRole::SelectionInner);
    assert_eq!(roles.bottom, TableBorderEdgeRole::SelectionInner);

    let bottom_right = &plan.mutations()[3];
    assert_eq!(bottom_right.after.borders.right_sha256, Some(digest('2')));
    assert_eq!(bottom_right.after.borders.bottom_sha256, Some(digest('3')));
    assert_eq!(bottom_right.after.borders.top_sha256, Some(digest('5')));
    assert_eq!(bottom_right.after.borders.left_sha256, Some(digest('6')));
    assert_eq!(bottom_right.after.background_sha256, Some(digest('7')));
    Ok(())
}

#[test]
fn merged_cells_must_be_fully_selected_and_resolve_from_their_real_edges() -> TestResult {
    let grid = merged_grid()?;
    let state = state(&grid)?;
    let expected_state_sha256 = hex(state.canonical_sha256(TablePropertiesLimits::default())?);
    assert_eq!(
        TablePropertiesRequest::from_draft(
            TablePropertiesRequestDraft {
                schema_version: TABLE_PROPERTIES_SCHEMA_VERSION.to_owned(),
                table_id: state.table_id().clone(),
                expected_state_sha256,
                selected_slots: vec![CellCoordinate { row: 0, column: 0 }],
                operation: unified_operation(),
            },
            &state,
            &grid,
            TablePropertiesLimits::default(),
        ),
        Err(TablePropertiesError::MergedSelectionConflict)
    );

    let request = request(&state, &grid, slots(0, 0, 1, 3), unified_operation())?;
    let plan =
        TablePropertiesBuilder::build(&request, &state, &grid, TablePropertiesLimits::default())?;
    assert_eq!(request.selected_slots().len(), 3);
    assert_eq!(request.selected_master_cell_count(), 2);
    assert_eq!(plan.receipt().selected_merged_cell_count, 1);
    let merged = &plan.mutations()[0];
    assert_eq!(merged.master_cell_id.as_str(), "merged");
    assert_eq!(merged.after.borders.top_sha256, Some(digest('1')));
    assert_eq!(merged.after.borders.bottom_sha256, Some(digest('3')));
    assert_eq!(merged.after.borders.left_sha256, Some(digest('4')));
    assert_eq!(merged.after.borders.right_sha256, Some(digest('6')));
    Ok(())
}

#[test]
fn duplicate_out_of_bounds_and_non_rectangular_unified_selections_fail_closed() -> TestResult {
    let grid = unmerged_grid(2, 2)?;
    let state = state(&grid)?;
    let cases = [
        (
            vec![
                CellCoordinate { row: 0, column: 0 },
                CellCoordinate { row: 0, column: 0 },
            ],
            TablePropertiesError::DuplicateSelectedSlot,
        ),
        (
            vec![CellCoordinate { row: 2, column: 0 }],
            TablePropertiesError::SelectionOutOfBounds,
        ),
    ];
    for (selected_slots, expected) in cases {
        let result = TablePropertiesRequest::from_draft(
            TablePropertiesRequestDraft {
                schema_version: TABLE_PROPERTIES_SCHEMA_VERSION.to_owned(),
                table_id: state.table_id().clone(),
                expected_state_sha256: hex(
                    state.canonical_sha256(TablePropertiesLimits::default())?
                ),
                selected_slots,
                operation: each_operation(),
            },
            &state,
            &grid,
            TablePropertiesLimits::default(),
        );
        assert_eq!(result, Err(expected));
    }
    let result = TablePropertiesRequest::from_draft(
        TablePropertiesRequestDraft {
            schema_version: TABLE_PROPERTIES_SCHEMA_VERSION.to_owned(),
            table_id: state.table_id().clone(),
            expected_state_sha256: hex(state.canonical_sha256(TablePropertiesLimits::default())?),
            selected_slots: vec![
                CellCoordinate { row: 0, column: 0 },
                CellCoordinate { row: 1, column: 1 },
            ],
            operation: unified_operation(),
        },
        &state,
        &grid,
        TablePropertiesLimits::default(),
    );
    assert_eq!(result, Err(TablePropertiesError::NonRectangularSelection));
    Ok(())
}

#[test]
fn properties_and_each_cell_border_accept_exact_non_contiguous_cell_sets() -> TestResult {
    let grid = unmerged_grid(2, 2)?;
    let state = state(&grid)?;
    let selected = vec![
        CellCoordinate { row: 0, column: 0 },
        CellCoordinate { row: 1, column: 1 },
    ];
    let property_request = request(
        &state,
        &grid,
        selected.clone(),
        TablePropertiesOperation::SetProperties {
            table_properties_sha256: None,
            cell_properties_sha256: Some(digest('f')),
        },
    )?;
    assert_eq!(property_request.region(), None);
    assert_eq!(property_request.selected_master_cell_count(), 2);
    let each_request = request(&state, &grid, selected, each_operation())?;
    assert_eq!(each_request.region(), None);
    let plan = TablePropertiesBuilder::build(
        &each_request,
        &state,
        &grid,
        TablePropertiesLimits::default(),
    )?;
    assert_eq!(plan.mutations().len(), 2);
    assert_eq!(
        plan.mutations()[0].coordinate,
        CellCoordinate { row: 0, column: 0 }
    );
    assert_eq!(
        plan.mutations()[1].coordinate,
        CellCoordinate { row: 1, column: 1 }
    );
    Ok(())
}

#[test]
fn selection_order_is_canonical_and_plans_are_byte_deterministic() -> TestResult {
    let grid = unmerged_grid(3, 3)?;
    let state = state(&grid)?;
    let ordered = slots(1, 1, 2, 2);
    let mut reversed = ordered.clone();
    reversed.reverse();
    let first = request(&state, &grid, ordered, unified_operation())?;
    let second = request(&state, &grid, reversed, unified_operation())?;
    assert_eq!(
        first.canonical_json(TablePropertiesLimits::default())?,
        second.canonical_json(TablePropertiesLimits::default())?
    );
    let first_plan =
        TablePropertiesBuilder::build(&first, &state, &grid, TablePropertiesLimits::default())?;
    let second_plan =
        TablePropertiesBuilder::build(&second, &state, &grid, TablePropertiesLimits::default())?;
    assert_eq!(
        first_plan.canonical_json(TablePropertiesLimits::default())?,
        second_plan.canonical_json(TablePropertiesLimits::default())?
    );
    assert_eq!(first_plan.receipt(), second_plan.receipt());
    Ok(())
}

#[test]
fn state_requires_complete_unique_cells_and_valid_digests() -> TestResult {
    let grid = unmerged_grid(2, 2)?;
    let mut missing = state_draft(&grid, 't')?;
    missing.cells.pop();
    assert_eq!(
        TablePropertiesState::from_draft(missing, &grid, TablePropertiesLimits::default()),
        Err(TablePropertiesError::CellSetMismatch)
    );
    let mut duplicate = state_draft(&grid, 't')?;
    duplicate.cells[1] = duplicate.cells[0].clone();
    assert_eq!(
        TablePropertiesState::from_draft(duplicate, &grid, TablePropertiesLimits::default()),
        Err(TablePropertiesError::CellSetMismatch)
    );
    let mut bad_digest = state_draft(&grid, 't')?;
    bad_digest.cells[0].properties.background_sha256 = Some("ABC".to_owned());
    assert_eq!(
        TablePropertiesState::from_draft(bad_digest, &grid, TablePropertiesLimits::default()),
        Err(TablePropertiesError::DigestInvalid)
    );
    let mut wrong_grid = state_draft(&grid, 't')?;
    wrong_grid.grid_sha256 = digest('a');
    assert_eq!(
        TablePropertiesState::from_draft(wrong_grid, &grid, TablePropertiesLimits::default()),
        Err(TablePropertiesError::GridMismatch)
    );
    Ok(())
}

#[test]
fn strict_json_rejects_duplicates_unknown_fields_versions_and_empty_input() -> TestResult {
    let grid = unmerged_grid(2, 2)?;
    let draft = state_draft(&grid, 't')?;
    let json = serde_json::to_vec(&draft)?;
    assert!(
        TablePropertiesState::from_json(&json, &grid, TablePropertiesLimits::default()).is_ok()
    );
    let canonical = state(&grid)?.canonical_json(TablePropertiesLimits::default())?;
    assert!(
        TablePropertiesState::from_json(&canonical, &grid, TablePropertiesLimits::default())
            .is_ok()
    );
    let duplicate =
        String::from_utf8(json.clone())?.replacen('{', "{\"schema_version\":\"duplicate\",", 1);
    assert_eq!(
        TablePropertiesState::from_json(
            duplicate.as_bytes(),
            &grid,
            TablePropertiesLimits::default()
        ),
        Err(TablePropertiesError::InvalidJson)
    );
    let unknown = String::from_utf8(json.clone())?.replacen('{', "{\"unknown\":true,", 1);
    assert_eq!(
        TablePropertiesState::from_json(
            unknown.as_bytes(),
            &grid,
            TablePropertiesLimits::default()
        ),
        Err(TablePropertiesError::InvalidJson)
    );
    let wrong =
        String::from_utf8(json)?.replace(TABLE_PROPERTIES_SCHEMA_VERSION, "table-properties/wrong");
    assert_eq!(
        TablePropertiesState::from_json(wrong.as_bytes(), &grid, TablePropertiesLimits::default()),
        Err(TablePropertiesError::UnsupportedVersion)
    );
    assert_eq!(
        TablePropertiesState::from_json(&[], &grid, TablePropertiesLimits::default()),
        Err(TablePropertiesError::InputLimit)
    );

    let state = state(&grid)?;
    let request_draft = TablePropertiesRequestDraft {
        schema_version: TABLE_PROPERTIES_SCHEMA_VERSION.to_owned(),
        table_id: state.table_id().clone(),
        expected_state_sha256: hex(state.canonical_sha256(TablePropertiesLimits::default())?),
        selected_slots: slots(0, 0, 1, 1),
        operation: each_operation(),
    };
    let json = serde_json::to_vec(&request_draft)?;
    let unknown = String::from_utf8(json)?.replacen('{', "{\"unexpected\":0,", 1);
    assert_eq!(
        TablePropertiesRequest::from_json(
            unknown.as_bytes(),
            &state,
            &grid,
            TablePropertiesLimits::default()
        ),
        Err(TablePropertiesError::InvalidJson)
    );
    Ok(())
}

#[test]
fn empty_operations_and_inconsistent_selection_scope_fail_closed() -> TestResult {
    let grid = unmerged_grid(2, 2)?;
    let state = state(&grid)?;
    let empty = TablePropertiesOperation::SetProperties {
        table_properties_sha256: None,
        cell_properties_sha256: None,
    };
    let table_only = TablePropertiesOperation::SetProperties {
        table_properties_sha256: Some(digest('z')),
        cell_properties_sha256: None,
    };
    let cell_only = TablePropertiesOperation::SetProperties {
        table_properties_sha256: None,
        cell_properties_sha256: Some(digest('z')),
    };
    let expected = hex(state.canonical_sha256(TablePropertiesLimits::default())?);
    let draft = |selected_slots, operation| TablePropertiesRequestDraft {
        schema_version: TABLE_PROPERTIES_SCHEMA_VERSION.to_owned(),
        table_id: state.table_id().clone(),
        expected_state_sha256: expected.clone(),
        selected_slots,
        operation,
    };
    assert_eq!(
        TablePropertiesRequest::from_draft(
            draft(Vec::new(), empty),
            &state,
            &grid,
            TablePropertiesLimits::default()
        ),
        Err(TablePropertiesError::EmptyOperation)
    );
    assert_eq!(
        TablePropertiesRequest::from_draft(
            draft(slots(0, 0, 1, 1), table_only),
            &state,
            &grid,
            TablePropertiesLimits::default()
        ),
        Err(TablePropertiesError::SelectionForbidden)
    );
    assert_eq!(
        TablePropertiesRequest::from_draft(
            draft(Vec::new(), cell_only),
            &state,
            &grid,
            TablePropertiesLimits::default()
        ),
        Err(TablePropertiesError::SelectionRequired)
    );
    let noop_border = TablePropertiesOperation::BorderEach {
        border: TableCellBorderPatch {
            top: preserve(),
            right: preserve(),
            bottom: preserve(),
            left: preserve(),
        },
        background: preserve(),
    };
    assert_eq!(
        TablePropertiesRequest::from_draft(
            draft(slots(0, 0, 1, 1), noop_border),
            &state,
            &grid,
            TablePropertiesLimits::default()
        ),
        Err(TablePropertiesError::EmptyOperation)
    );
    Ok(())
}

#[test]
fn stale_state_is_rejected_before_any_plan_exists() -> TestResult {
    let grid = unmerged_grid(2, 2)?;
    let original = state(&grid)?;
    let request = request(&original, &grid, slots(0, 0, 1, 1), each_operation())?;
    let changed = TablePropertiesState::from_draft(
        state_draft(&grid, 'u')?,
        &grid,
        TablePropertiesLimits::default(),
    )?;
    assert_eq!(
        TablePropertiesBuilder::build(&request, &changed, &grid, TablePropertiesLimits::default()),
        Err(TablePropertiesError::BindingDrift)
    );
    Ok(())
}

#[test]
fn clear_and_preserve_are_distinct_and_changes_are_counted_from_actual_state() -> TestResult {
    let grid = unmerged_grid(1, 1)?;
    let mut draft = state_draft(&grid, 't')?;
    draft.cells[0].properties.borders.top_sha256 = Some(digest('a'));
    draft.cells[0].properties.borders.right_sha256 = None;
    draft.cells[0].properties.background_sha256 = Some(digest('b'));
    let state = TablePropertiesState::from_draft(draft, &grid, TablePropertiesLimits::default())?;
    let request = request(
        &state,
        &grid,
        slots(0, 0, 1, 1),
        TablePropertiesOperation::BorderEach {
            border: TableCellBorderPatch {
                top: TablePropertyDigestPatch::Clear,
                right: TablePropertyDigestPatch::Clear,
                bottom: preserve(),
                left: preserve(),
            },
            background: TablePropertyDigestPatch::Clear,
        },
    )?;
    let plan =
        TablePropertiesBuilder::build(&request, &state, &grid, TablePropertiesLimits::default())?;
    assert_eq!(plan.receipt().border_side_change_count, 1);
    assert_eq!(plan.receipt().background_change_count, 1);
    assert_eq!(plan.receipt().changed_master_cell_count, 1);
    assert_eq!(plan.mutations()[0].after.borders.top_sha256, None);
    assert_eq!(plan.mutations()[0].after.borders.right_sha256, None);
    Ok(())
}

#[test]
fn finite_limits_and_output_bounds_fail_closed() -> TestResult {
    assert_eq!(
        TablePropertiesLimits::new(TablePropertiesLimitConfig {
            selected_slots: 0,
            ..TablePropertiesLimitConfig::default()
        }),
        Err(TablePropertiesError::InvalidLimit)
    );
    let grid = unmerged_grid(2, 2)?;
    let state = state(&grid)?;
    let selection_limited = TablePropertiesLimits::new(TablePropertiesLimitConfig {
        selected_slots: 1,
        ..TablePropertiesLimitConfig::default()
    })?;
    let result = TablePropertiesRequest::from_draft(
        TablePropertiesRequestDraft {
            schema_version: TABLE_PROPERTIES_SCHEMA_VERSION.to_owned(),
            table_id: state.table_id().clone(),
            expected_state_sha256: hex(state.canonical_sha256(TablePropertiesLimits::default())?),
            selected_slots: slots(0, 0, 1, 2),
            operation: each_operation(),
        },
        &state,
        &grid,
        selection_limited,
    );
    assert_eq!(result, Err(TablePropertiesError::SelectionLimit));

    let request = request(&state, &grid, slots(0, 0, 2, 2), unified_operation())?;
    let tight_output = TablePropertiesLimits::new(TablePropertiesLimitConfig {
        input_bytes: 64,
        serialized_bytes: 128,
        ..TablePropertiesLimitConfig::default()
    })?;
    assert_eq!(
        TablePropertiesBuilder::build(&request, &state, &grid, tight_output),
        Err(TablePropertiesError::OutputLimit)
    );
    Ok(())
}

#[test]
fn debug_surfaces_redact_ids_digests_payloads_and_formula_identities() -> TestResult {
    let grid = unmerged_grid(2, 2)?;
    let draft = state_draft(&grid, 't')?;
    let draft_debug = format!("{draft:?}");
    assert!(!draft_debug.contains("table-private"));
    assert!(!draft_debug.contains(&digest('t')));
    let state = state(&grid)?;
    let request = request(&state, &grid, slots(0, 0, 2, 2), unified_operation())?;
    let plan =
        TablePropertiesBuilder::build(&request, &state, &grid, TablePropertiesLimits::default())?;
    let debug = format!(
        "{state:?}{request:?}{plan:?}{:?}{:?}",
        plan.mutations()[0],
        plan.receipt()
    );
    for secret in [
        "table-private",
        "cell-0-0",
        &digest('p'),
        &digest('f'),
        &digest('t'),
        &digest('1'),
        &digest('7'),
    ] {
        assert!(!debug.contains(secret));
    }
    Ok(())
}

#[test]
fn fixed_shape_corpus_assigns_every_selected_master_exactly_once() -> TestResult {
    for rows in 1..=12 {
        for columns in 1..=12 {
            let grid = unmerged_grid(rows, columns)?;
            let state = state(&grid)?;
            let request = request(
                &state,
                &grid,
                slots(0, 0, rows, columns),
                unified_operation(),
            )?;
            let plan = TablePropertiesBuilder::build(
                &request,
                &state,
                &grid,
                TablePropertiesLimits::default(),
            )?;
            assert_eq!(plan.mutations().len(), grid.master_cell_count());
            assert_eq!(
                plan.receipt().selected_master_cell_count,
                grid.master_cell_count()
            );
            assert_eq!(plan.receipt().selected_slot_count, grid.slot_count());
            assert_eq!(plan.receipt().unselected_master_cell_preserved_count, 0);
        }
    }
    Ok(())
}

#[test]
fn public_error_codes_are_stable() {
    let cases = [
        (
            TablePropertiesError::InvalidLimit,
            "table_properties_invalid_limit",
        ),
        (
            TablePropertiesError::UnsupportedVersion,
            "table_properties_unsupported_version",
        ),
        (
            TablePropertiesError::InputLimit,
            "table_properties_input_limit",
        ),
        (
            TablePropertiesError::InvalidJson,
            "table_properties_invalid_json",
        ),
        (
            TablePropertiesError::GridMismatch,
            "table_properties_grid_mismatch",
        ),
        (
            TablePropertiesError::CellSetMismatch,
            "table_properties_cell_set_mismatch",
        ),
        (
            TablePropertiesError::IdentifierLimit,
            "table_properties_identifier_limit",
        ),
        (
            TablePropertiesError::DigestInvalid,
            "table_properties_digest_invalid",
        ),
        (
            TablePropertiesError::StateBindingMismatch,
            "table_properties_state_binding_mismatch",
        ),
        (
            TablePropertiesError::EmptyOperation,
            "table_properties_empty_operation",
        ),
        (
            TablePropertiesError::SelectionRequired,
            "table_properties_selection_required",
        ),
        (
            TablePropertiesError::SelectionForbidden,
            "table_properties_selection_forbidden",
        ),
        (
            TablePropertiesError::SelectionLimit,
            "table_properties_selection_limit",
        ),
        (
            TablePropertiesError::DuplicateSelectedSlot,
            "table_properties_duplicate_selected_slot",
        ),
        (
            TablePropertiesError::SelectionOutOfBounds,
            "table_properties_selection_out_of_bounds",
        ),
        (
            TablePropertiesError::NonRectangularSelection,
            "table_properties_non_rectangular_selection",
        ),
        (
            TablePropertiesError::MergedSelectionConflict,
            "table_properties_merged_selection_conflict",
        ),
        (
            TablePropertiesError::DimensionOverflow,
            "table_properties_dimension_overflow",
        ),
        (
            TablePropertiesError::BindingDrift,
            "table_properties_binding_drift",
        ),
        (
            TablePropertiesError::MasterCellLimit,
            "table_properties_master_cell_limit",
        ),
        (
            TablePropertiesError::OutputLimit,
            "table_properties_output_limit",
        ),
        (
            TablePropertiesError::Serialization,
            "table_properties_serialization",
        ),
        (
            TablePropertiesError::AllocationFailed,
            "table_properties_allocation",
        ),
    ];
    for (error, code) in cases {
        assert_eq!(error.code(), code);
    }
}
