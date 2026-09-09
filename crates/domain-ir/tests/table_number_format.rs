use domain_ir::{
    CellCoordinate, FormulaAst, FormulaAstDraft, FormulaCache, FormulaCellDraft, FormulaDecimal,
    FormulaError, FormulaLimitConfig, FormulaLimits, FormulaNumberFormat, FormulaValue, LogicalId,
    TABLE_FORMULA_SCHEMA_VERSION, TABLE_GRID_SCHEMA_VERSION, TABLE_NUMBER_FORMAT_CAPABILITY_ID,
    TABLE_NUMBER_FORMAT_SCHEMA_VERSION, TableCellSpan, TableGrid, TableGridDraft, TableGridLimits,
    TableNumberFormatBuilder, TableNumberFormatCellDraft, TableNumberFormatError,
    TableNumberFormatLimitConfig, TableNumberFormatLimits, TableNumberFormatRequest,
    TableNumberFormatRequestDraft, TableNumberFormatState, TableNumberFormatStateDraft,
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

const fn coordinate(row: u32, column: u32) -> CellCoordinate {
    CellCoordinate { row, column }
}

fn grid() -> Result<TableGrid, Box<dyn std::error::Error>> {
    let mut master_cells = Vec::new();
    for row in 0..2 {
        for column in 0..2 {
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
            rows: 2,
            columns: 2,
            master_cells,
        },
        TableGridLimits::default(),
    )?)
}

fn merged_grid() -> Result<TableGrid, Box<dyn std::error::Error>> {
    Ok(TableGrid::from_draft(
        TableGridDraft {
            schema_version: TABLE_GRID_SCHEMA_VERSION.to_owned(),
            rows: 1,
            columns: 2,
            master_cells: vec![TableCellSpan {
                master_cell_id: id("merged")?,
                row: 0,
                column: 0,
                row_span: 1,
                column_span: 2,
            }],
        },
        TableGridLimits::default(),
    )?)
}

fn formula_limits(rows: u32, columns: u32) -> Result<FormulaLimits, FormulaError> {
    FormulaLimits::new(FormulaLimitConfig {
        rows,
        columns,
        ..FormulaLimitConfig::default()
    })
}

fn formula_draft(
    owner: CellCoordinate,
    source: &str,
    number_format: FormulaNumberFormat,
    cache: FormulaCache,
    limits: FormulaLimits,
) -> Result<FormulaCellDraft, FormulaError> {
    let ast = FormulaAst::parse(source, limits)?;
    Ok(FormulaCellDraft {
        schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
        owner,
        ast: FormulaAstDraft {
            schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
            expression: ast.expression().clone(),
        },
        cache,
        number_format,
    })
}

fn decimal_cache(value: i64) -> FormulaCache {
    FormulaCache::Unverified {
        value: FormulaValue::Decimal {
            value: FormulaDecimal::new(value, 0),
        },
    }
}

fn state_draft(
    grid: &TableGrid,
    formula_limits: FormulaLimits,
) -> Result<TableNumberFormatStateDraft, Box<dyn std::error::Error>> {
    let mut cells = Vec::new();
    for (index, span) in grid.master_cells().iter().enumerate() {
        let owner = coordinate(span.row, span.column);
        let formula = match owner {
            CellCoordinate { row: 0, column: 0 } => Some(formula_draft(
                owner,
                "1+2",
                FormulaNumberFormat::General,
                decimal_cache(3),
                formula_limits,
            )?),
            CellCoordinate { row: 1, column: 1 } => Some(formula_draft(
                owner,
                "SUM(A1:B1)",
                FormulaNumberFormat::Number {
                    decimal_places: 1,
                    use_grouping: false,
                },
                decimal_cache(7),
                formula_limits,
            )?),
            _ => None,
        };
        let digest_character = ['a', 'b', 'c', 'd'][index % 4];
        cells.push(TableNumberFormatCellDraft {
            master_cell_id: span.master_cell_id.clone(),
            coordinate: owner,
            non_formula_payload_sha256: digest(digest_character),
            properties_sha256: digest(['d', 'c', 'b', 'a'][index % 4]),
            formula,
        });
    }
    Ok(TableNumberFormatStateDraft {
        schema_version: TABLE_NUMBER_FORMAT_SCHEMA_VERSION.to_owned(),
        table_id: id("table-main")?,
        grid_sha256: hex(grid.canonical_sha256()?),
        table_properties_sha256: digest('e'),
        cells,
    })
}

fn state(
    grid: &TableGrid,
    formula_limits: FormulaLimits,
) -> Result<TableNumberFormatState, Box<dyn std::error::Error>> {
    Ok(TableNumberFormatState::from_draft(
        state_draft(grid, formula_limits)?,
        grid,
        TableNumberFormatLimits::default(),
        formula_limits,
    )?)
}

fn request(
    state: &TableNumberFormatState,
    grid: &TableGrid,
    selected_cells: Vec<CellCoordinate>,
    target_format: FormulaNumberFormat,
    flow: &str,
    limits: TableNumberFormatLimits,
    formula_limits: FormulaLimits,
) -> Result<TableNumberFormatRequest, TableNumberFormatError> {
    TableNumberFormatRequest::from_draft(
        TableNumberFormatRequestDraft {
            schema_version: TABLE_NUMBER_FORMAT_SCHEMA_VERSION.to_owned(),
            table_id: state.table_id().clone(),
            selected_cells,
            target_format,
            expected_source_state_sha256: hex(state.canonical_sha256(limits)?),
            expected_document_flow_sha256: flow.to_owned(),
        },
        state,
        grid,
        flow,
        limits,
        formula_limits,
    )
}

#[test]
fn all_supported_formats_change_only_selected_formula_format() -> TestResult {
    let grid = grid()?;
    let formula_limits = formula_limits(2, 2)?;
    let state = state(&grid, formula_limits)?;
    let formats = [
        FormulaNumberFormat::General,
        FormulaNumberFormat::Number {
            decimal_places: 4,
            use_grouping: true,
        },
        FormulaNumberFormat::Percent { decimal_places: 3 },
        FormulaNumberFormat::Scientific { decimal_places: 2 },
    ];
    for format in formats {
        let request = request(
            &state,
            &grid,
            vec![coordinate(1, 1), coordinate(0, 0)],
            format,
            &digest('f'),
            TableNumberFormatLimits::default(),
            formula_limits,
        )?;
        let plan = TableNumberFormatBuilder::build(
            &request,
            &state,
            &grid,
            &digest('f'),
            TableNumberFormatLimits::default(),
            formula_limits,
        )?;
        assert_eq!(request.capability_id(), TABLE_NUMBER_FORMAT_CAPABILITY_ID);
        assert_eq!(
            request.selected_cells(),
            &[coordinate(0, 0), coordinate(1, 1)]
        );
        assert_eq!(plan.receipt().selected_formula_cells(), 2);
        assert!(plan.receipt().non_format_state_preserved());
        for (before, after) in state.cells().iter().zip(plan.after_state().cells()) {
            assert_eq!(before.master_cell_id(), after.master_cell_id());
            assert_eq!(before.coordinate(), after.coordinate());
            assert_eq!(
                before.non_formula_payload_sha256(),
                after.non_formula_payload_sha256()
            );
            assert_eq!(before.properties_sha256(), after.properties_sha256());
            match (before.formula(), after.formula()) {
                (Some(before), Some(after)) => {
                    assert_eq!(before.owner(), after.owner());
                    assert_eq!(before.ast(), after.ast());
                    assert_eq!(before.cache(), after.cache());
                    assert_eq!(after.number_format(), format);
                }
                (None, None) => {}
                _ => panic!("formula presence drifted"),
            }
        }
    }
    Ok(())
}

#[test]
fn canonical_order_idempotence_and_digest_are_deterministic() -> TestResult {
    let grid = grid()?;
    let formula_limits = formula_limits(2, 2)?;
    let state = state(&grid, formula_limits)?;
    let limits = TableNumberFormatLimits::default();
    let target = FormulaNumberFormat::Number {
        decimal_places: 2,
        use_grouping: true,
    };
    let first = request(
        &state,
        &grid,
        vec![coordinate(1, 1), coordinate(0, 0)],
        target,
        &digest('f'),
        limits,
        formula_limits,
    )?;
    let second = request(
        &state,
        &grid,
        vec![coordinate(0, 0), coordinate(1, 1)],
        target,
        &digest('f'),
        limits,
        formula_limits,
    )?;
    assert_eq!(
        first.canonical_json(limits)?,
        second.canonical_json(limits)?
    );
    let first_plan = TableNumberFormatBuilder::build(
        &first,
        &state,
        &grid,
        &digest('f'),
        limits,
        formula_limits,
    )?;
    let second_plan = TableNumberFormatBuilder::build(
        &second,
        &state,
        &grid,
        &digest('f'),
        limits,
        formula_limits,
    )?;
    assert_eq!(
        first_plan.canonical_json(limits)?,
        second_plan.canonical_json(limits)?
    );
    assert_eq!(
        first_plan.canonical_sha256(limits)?,
        second_plan.canonical_sha256(limits)?
    );
    Ok(())
}

#[test]
fn request_rejects_state_grid_identity_and_flow_drift() -> TestResult {
    let grid = grid()?;
    let formula_limits = formula_limits(2, 2)?;
    let state = state(&grid, formula_limits)?;
    let limits = TableNumberFormatLimits::default();
    let base = TableNumberFormatRequestDraft {
        schema_version: TABLE_NUMBER_FORMAT_SCHEMA_VERSION.to_owned(),
        table_id: state.table_id().clone(),
        selected_cells: vec![coordinate(0, 0)],
        target_format: FormulaNumberFormat::General,
        expected_source_state_sha256: hex(state.canonical_sha256(limits)?),
        expected_document_flow_sha256: digest('f'),
    };
    let mut wrong_state = base.clone();
    wrong_state.expected_source_state_sha256 = digest('a');
    assert_eq!(
        TableNumberFormatRequest::from_draft(
            wrong_state,
            &state,
            &grid,
            &digest('f'),
            limits,
            formula_limits,
        ),
        Err(TableNumberFormatError::StateBindingMismatch)
    );
    let mut wrong_id = base.clone();
    wrong_id.table_id = id("other")?;
    assert_eq!(
        TableNumberFormatRequest::from_draft(
            wrong_id,
            &state,
            &grid,
            &digest('f'),
            limits,
            formula_limits,
        ),
        Err(TableNumberFormatError::TableIdentityMismatch)
    );
    assert_eq!(
        TableNumberFormatRequest::from_draft(
            base,
            &state,
            &grid,
            &digest('e'),
            limits,
            formula_limits,
        ),
        Err(TableNumberFormatError::FlowBindingMismatch)
    );

    let other_grid = TableGrid::from_draft(
        TableGridDraft {
            schema_version: TABLE_GRID_SCHEMA_VERSION.to_owned(),
            rows: 2,
            columns: 2,
            master_cells: (0..2)
                .flat_map(|row| (0..2).map(move |column| (row, column)))
                .map(|(row, column)| {
                    Ok(TableCellSpan {
                        master_cell_id: id(&format!("other-{row}-{column}"))?,
                        row,
                        column,
                        row_span: 1,
                        column_span: 1,
                    })
                })
                .collect::<Result<Vec<_>, Box<dyn std::error::Error>>>()?,
        },
        TableGridLimits::default(),
    )?;
    let draft = TableNumberFormatRequestDraft {
        schema_version: TABLE_NUMBER_FORMAT_SCHEMA_VERSION.to_owned(),
        table_id: state.table_id().clone(),
        selected_cells: vec![coordinate(0, 0)],
        target_format: FormulaNumberFormat::General,
        expected_source_state_sha256: hex(state.canonical_sha256(limits)?),
        expected_document_flow_sha256: digest('f'),
    };
    assert_eq!(
        TableNumberFormatRequest::from_draft(
            draft,
            &state,
            &other_grid,
            &digest('f'),
            limits,
            formula_limits,
        ),
        Err(TableNumberFormatError::GridMismatch)
    );
    Ok(())
}

#[test]
fn build_rechecks_late_state_grid_and_flow_drift() -> TestResult {
    let grid = grid()?;
    let formula_limits = formula_limits(2, 2)?;
    let state = state(&grid, formula_limits)?;
    let limits = TableNumberFormatLimits::default();
    let request = request(
        &state,
        &grid,
        vec![coordinate(0, 0)],
        FormulaNumberFormat::Percent { decimal_places: 1 },
        &digest('f'),
        limits,
        formula_limits,
    )?;

    assert_eq!(
        TableNumberFormatBuilder::build(
            &request,
            &state,
            &grid,
            &digest('e'),
            limits,
            formula_limits,
        ),
        Err(TableNumberFormatError::FlowBindingMismatch)
    );
    let mut drifted = state_draft(&grid, formula_limits)?;
    drifted.cells[0].non_formula_payload_sha256 = digest('f');
    let drifted = TableNumberFormatState::from_draft(drifted, &grid, limits, formula_limits)?;
    assert_eq!(
        TableNumberFormatBuilder::build(
            &request,
            &drifted,
            &grid,
            &digest('f'),
            limits,
            formula_limits,
        ),
        Err(TableNumberFormatError::StateBindingMismatch)
    );
    Ok(())
}

#[test]
fn state_rejects_incomplete_duplicate_misaligned_and_wrong_formula_owner() -> TestResult {
    let grid = grid()?;
    let too_small_formula_limits = formula_limits(1, 1)?;
    let formula_limits = formula_limits(2, 2)?;
    let limits = TableNumberFormatLimits::default();

    let mut incomplete = state_draft(&grid, formula_limits)?;
    incomplete.cells.pop();
    assert_eq!(
        TableNumberFormatState::from_draft(incomplete, &grid, limits, formula_limits),
        Err(TableNumberFormatError::IncompleteCellSet)
    );

    let mut duplicate = state_draft(&grid, formula_limits)?;
    duplicate.cells[1].master_cell_id = duplicate.cells[0].master_cell_id.clone();
    assert_eq!(
        TableNumberFormatState::from_draft(duplicate, &grid, limits, formula_limits),
        Err(TableNumberFormatError::DuplicateCell)
    );

    let mut misaligned = state_draft(&grid, formula_limits)?;
    misaligned.cells[0].coordinate = coordinate(0, 1);
    assert_eq!(
        TableNumberFormatState::from_draft(misaligned, &grid, limits, formula_limits),
        Err(TableNumberFormatError::CellGridMismatch)
    );

    let mut wrong_owner = state_draft(&grid, formula_limits)?;
    let formula = wrong_owner.cells[0]
        .formula
        .as_mut()
        .ok_or_else(|| std::io::Error::other("fixture formula missing"))?;
    formula.owner = coordinate(0, 1);
    assert_eq!(
        TableNumberFormatState::from_draft(wrong_owner, &grid, limits, formula_limits),
        Err(TableNumberFormatError::FormulaOwnerMismatch)
    );

    let mut no_formulas = state_draft(&grid, formula_limits)?;
    for cell in &mut no_formulas.cells {
        cell.formula = None;
    }
    assert_eq!(
        TableNumberFormatState::from_draft(no_formulas, &grid, limits, too_small_formula_limits),
        Err(TableNumberFormatError::Formula(
            FormulaError::InvalidGridDimensions
        ))
    );
    Ok(())
}

#[test]
fn selection_requires_unique_formula_master_cells() -> TestResult {
    let grid = grid()?;
    let formula_limits = formula_limits(2, 2)?;
    let state = state(&grid, formula_limits)?;
    let limits = TableNumberFormatLimits::default();

    assert_eq!(
        request(
            &state,
            &grid,
            Vec::new(),
            FormulaNumberFormat::General,
            &digest('f'),
            limits,
            formula_limits,
        ),
        Err(TableNumberFormatError::EmptySelection)
    );
    assert_eq!(
        request(
            &state,
            &grid,
            vec![coordinate(0, 0), coordinate(0, 0)],
            FormulaNumberFormat::General,
            &digest('f'),
            limits,
            formula_limits,
        ),
        Err(TableNumberFormatError::DuplicateSelection)
    );
    assert_eq!(
        request(
            &state,
            &grid,
            vec![coordinate(0, 1)],
            FormulaNumberFormat::General,
            &digest('f'),
            limits,
            formula_limits,
        ),
        Err(TableNumberFormatError::SelectionNotFormula)
    );
    Ok(())
}

#[test]
fn merged_master_is_exact_but_covered_nonmaster_slot_is_rejected() -> TestResult {
    let grid = merged_grid()?;
    let formula_limits = formula_limits(1, 2)?;
    let mut draft = state_draft(&grid, formula_limits)?;
    draft.cells[0].formula = Some(formula_draft(
        coordinate(0, 0),
        "1+2",
        FormulaNumberFormat::General,
        decimal_cache(3),
        formula_limits,
    )?);
    let state = TableNumberFormatState::from_draft(
        draft,
        &grid,
        TableNumberFormatLimits::default(),
        formula_limits,
    )?;
    assert!(
        request(
            &state,
            &grid,
            vec![coordinate(0, 0)],
            FormulaNumberFormat::Number {
                decimal_places: 0,
                use_grouping: false,
            },
            &digest('f'),
            TableNumberFormatLimits::default(),
            formula_limits,
        )
        .is_ok()
    );
    assert_eq!(
        request(
            &state,
            &grid,
            vec![coordinate(0, 1)],
            FormulaNumberFormat::General,
            &digest('f'),
            TableNumberFormatLimits::default(),
            formula_limits,
        ),
        Err(TableNumberFormatError::SelectionNotFormula)
    );
    Ok(())
}

#[test]
fn strict_json_rejects_unknown_duplicate_version_and_bad_digest() -> TestResult {
    let grid = grid()?;
    let formula_limits = formula_limits(2, 2)?;
    let state = state(&grid, formula_limits)?;
    let limits = TableNumberFormatLimits::default();
    let source_sha = hex(state.canonical_sha256(limits)?);
    let base = format!(
        r#"{{"schema_version":"{TABLE_NUMBER_FORMAT_SCHEMA_VERSION}","table_id":"table-main","selected_cells":[{{"row":0,"column":0}}],"target_format":{{"kind":"general"}},"expected_source_state_sha256":"{source_sha}","expected_document_flow_sha256":"{}"}}"#,
        digest('f')
    );
    assert!(
        TableNumberFormatRequest::from_json(
            base.as_bytes(),
            &state,
            &grid,
            &digest('f'),
            limits,
            formula_limits,
        )
        .is_ok()
    );
    for invalid in [
        base.replace("{\"schema_version\"", "{\"unknown\":1,\"schema_version\""),
        base.replace(
            "{\"schema_version\"",
            "{\"schema_version\":\"duplicate\",\"schema_version\"",
        ),
        base.replace(TABLE_NUMBER_FORMAT_SCHEMA_VERSION, "future"),
        base.replace(&digest('f'), "ABC"),
    ] {
        assert!(
            TableNumberFormatRequest::from_json(
                invalid.as_bytes(),
                &state,
                &grid,
                &digest('f'),
                limits,
                formula_limits,
            )
            .is_err()
        );
    }
    Ok(())
}

#[test]
fn target_precision_and_selection_limits_fail_closed() -> TestResult {
    let grid = grid()?;
    let formula_limits = formula_limits(2, 2)?;
    let state = state(&grid, formula_limits)?;
    assert_eq!(
        request(
            &state,
            &grid,
            vec![coordinate(0, 0)],
            FormulaNumberFormat::Scientific { decimal_places: 13 },
            &digest('f'),
            TableNumberFormatLimits::default(),
            formula_limits,
        ),
        Err(TableNumberFormatError::InvalidNumberFormat)
    );
    let limits = TableNumberFormatLimits::new(TableNumberFormatLimitConfig {
        cells: 4,
        selected_cells: 1,
        ..TableNumberFormatLimitConfig::default()
    })?;
    assert_eq!(
        request(
            &state,
            &grid,
            vec![coordinate(0, 0), coordinate(1, 1)],
            FormulaNumberFormat::General,
            &digest('f'),
            limits,
            formula_limits,
        ),
        Err(TableNumberFormatError::SelectionLimitExceeded)
    );
    Ok(())
}

#[test]
fn input_and_output_bounds_are_enforced() -> TestResult {
    let grid = grid()?;
    let formula_limits = formula_limits(2, 2)?;
    let state = state(&grid, formula_limits)?;
    let tiny_input = TableNumberFormatLimits::new(TableNumberFormatLimitConfig {
        input_bytes: 1,
        cells: 4,
        selected_cells: 2,
        serialized_bytes: 1024,
        ..TableNumberFormatLimitConfig::default()
    })?;
    assert_eq!(
        TableNumberFormatRequest::from_json(
            b"{}",
            &state,
            &grid,
            &digest('f'),
            tiny_input,
            formula_limits,
        ),
        Err(TableNumberFormatError::InputLimitExceeded)
    );

    let request = request(
        &state,
        &grid,
        vec![coordinate(0, 0)],
        FormulaNumberFormat::General,
        &digest('f'),
        TableNumberFormatLimits::default(),
        formula_limits,
    )?;
    let tiny_output = TableNumberFormatLimits::new(TableNumberFormatLimitConfig {
        input_bytes: 1,
        cells: 4,
        selected_cells: 2,
        serialized_bytes: 1,
        ..TableNumberFormatLimitConfig::default()
    })?;
    assert_eq!(
        request.canonical_json(tiny_output),
        Err(TableNumberFormatError::OutputLimitExceeded)
    );
    assert_eq!(
        TableNumberFormatLimits::new(TableNumberFormatLimitConfig {
            cells: 1,
            selected_cells: 2,
            ..TableNumberFormatLimitConfig::default()
        }),
        Err(TableNumberFormatError::InvalidLimit)
    );
    Ok(())
}

#[test]
fn debug_redacts_identifiers_digests_formula_and_cache() -> TestResult {
    let grid = grid()?;
    let formula_limits = formula_limits(2, 2)?;
    let state = state(&grid, formula_limits)?;
    let request_draft = TableNumberFormatRequestDraft {
        schema_version: TABLE_NUMBER_FORMAT_SCHEMA_VERSION.to_owned(),
        table_id: state.table_id().clone(),
        selected_cells: vec![coordinate(0, 0)],
        target_format: FormulaNumberFormat::Percent { decimal_places: 1 },
        expected_source_state_sha256: hex(
            state.canonical_sha256(TableNumberFormatLimits::default())?
        ),
        expected_document_flow_sha256: digest('f'),
    };
    let draft_debug = format!("{request_draft:?}");
    let request = TableNumberFormatRequest::from_draft(
        request_draft,
        &state,
        &grid,
        &digest('f'),
        TableNumberFormatLimits::default(),
        formula_limits,
    )?;
    let plan = TableNumberFormatBuilder::build(
        &request,
        &state,
        &grid,
        &digest('f'),
        TableNumberFormatLimits::default(),
        formula_limits,
    )?;
    for debug in [
        draft_debug,
        format!("{state:?}"),
        format!("{request:?}"),
        format!("{plan:?}"),
    ] {
        assert!(debug.contains("<redacted>"));
        assert!(!debug.contains("table-main"));
        assert!(!debug.contains(&digest('f')));
        assert!(!debug.contains("SUM(A1:B1)"));
    }
    Ok(())
}

#[test]
fn state_json_round_trip_preserves_canonical_bytes() -> TestResult {
    let grid = grid()?;
    let formula_limits = formula_limits(2, 2)?;
    let limits = TableNumberFormatLimits::default();
    let state = state(&grid, formula_limits)?;
    let bytes = state.canonical_json(limits)?;
    let restored = TableNumberFormatState::from_json(&bytes, &grid, limits, formula_limits)?;
    assert_eq!(bytes, restored.canonical_json(limits)?);
    Ok(())
}
