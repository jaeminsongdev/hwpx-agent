use domain_ir::{
    CellCoordinate, FormulaAst, FormulaAstDraft, FormulaCache, FormulaCellDraft, FormulaDecimal,
    FormulaGridDimensions, FormulaLimitConfig, FormulaLimits, FormulaNumberFormat, FormulaValue,
    LogicalId, TABLE_FORMULA_SCHEMA_VERSION, TABLE_GRID_SCHEMA_VERSION,
    TABLE_TRANSPOSE_SCHEMA_VERSION, TableCellSpan, TableGrid, TableGridDraft, TableGridLimits,
    TableTransposeBuilder, TableTransposeCellDraft, TableTransposeError,
    TableTransposeFormulaPolicy, TableTransposeLimitConfig, TableTransposeLimits,
    TableTransposeRequest, TableTransposeRequestDraft,
};

type TestResult = Result<(), Box<dyn std::error::Error>>;

fn id(value: &str) -> Result<LogicalId, Box<dyn std::error::Error>> {
    Ok(LogicalId::parse(value)?)
}

fn digest(character: char) -> String {
    std::iter::repeat_n(character, 64).collect()
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
) -> Result<FormulaCellDraft, Box<dyn std::error::Error>> {
    let ast = FormulaAst::parse(source, formula_limits()?)?;
    Ok(FormulaCellDraft {
        schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
        owner,
        ast: FormulaAstDraft {
            schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
            expression: ast.expression().clone(),
        },
        cache: FormulaCache::Unverified {
            value: FormulaValue::Decimal {
                value: FormulaDecimal::new(7, 0),
            },
        },
        number_format: FormulaNumberFormat::Number {
            decimal_places: 2,
            use_grouping: true,
        },
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
    Ok(TableGrid::new(
        2,
        3,
        vec![
            TableCellSpan {
                master_cell_id: id("a")?,
                row: 0,
                column: 0,
                row_span: 1,
                column_span: 2,
            },
            TableCellSpan {
                master_cell_id: id("b")?,
                row: 0,
                column: 2,
                row_span: 1,
                column_span: 1,
            },
            TableCellSpan {
                master_cell_id: id("c")?,
                row: 1,
                column: 0,
                row_span: 1,
                column_span: 1,
            },
            TableCellSpan {
                master_cell_id: id("d")?,
                row: 1,
                column: 1,
                row_span: 1,
                column_span: 2,
            },
        ],
        TableGridLimits::default(),
    )?)
}

fn request_draft(
    grid: &TableGrid,
    with_formula: bool,
) -> Result<TableTransposeRequestDraft, Box<dyn std::error::Error>> {
    let cells = grid
        .master_cells()
        .iter()
        .enumerate()
        .map(|(index, span)| {
            let coordinate = CellCoordinate {
                row: span.row,
                column: span.column,
            };
            Ok(TableTransposeCellDraft {
                master_cell_id: span.master_cell_id.clone(),
                coordinate,
                payload_sha256: digest('a'),
                style_sha256: digest('b'),
                formula: (with_formula && index + 1 == grid.master_cell_count())
                    .then(|| formula_draft("SUM(A1:$C$2)", coordinate))
                    .transpose()?,
            })
        })
        .collect::<Result<Vec<_>, Box<dyn std::error::Error>>>()?;
    Ok(TableTransposeRequestDraft {
        schema_version: TABLE_TRANSPOSE_SCHEMA_VERSION.to_owned(),
        table_id: id("table-main")?,
        table_properties_sha256: digest('c'),
        formula_policy: if with_formula {
            TableTransposeFormulaPolicy::TransposeAndClearCache
        } else {
            TableTransposeFormulaPolicy::Reject
        },
        cells,
    })
}

fn request(
    grid: &TableGrid,
    with_formula: bool,
) -> Result<TableTransposeRequest, Box<dyn std::error::Error>> {
    Ok(TableTransposeRequest::from_draft(
        request_draft(grid, with_formula)?,
        grid,
        formula_limits()?,
        TableTransposeLimits::default(),
    )?)
}

#[test]
fn transposes_complete_merged_grid_payload_style_formula_and_cache() -> TestResult {
    let grid = merged_grid()?;
    let request = request(&grid, true)?;
    let plan = TableTransposeBuilder::build(
        &request,
        &grid,
        TableGridLimits::default(),
        formula_limits()?,
        TableTransposeLimits::default(),
    )?;
    assert_eq!((plan.rows(), plan.columns()), (3, 2));
    let output = TableGrid::new(
        plan.rows(),
        plan.columns(),
        plan.master_cells().to_vec(),
        TableGridLimits::default(),
    )?;
    assert_eq!(output.master_cell_count(), 4);
    let a = output.master_cell_at(CellCoordinate { row: 1, column: 0 })?;
    assert_eq!(a.master_cell_id.as_str(), "a");
    assert_eq!((a.row_span, a.column_span), (2, 1));

    let d = plan
        .relocations()
        .iter()
        .find(|relocation| relocation.master_cell_id.as_str() == "d")
        .ok_or_else(|| std::io::Error::other("d relocation missing"))?;
    assert_eq!(d.before, CellCoordinate { row: 1, column: 1 });
    assert_eq!(d.after, CellCoordinate { row: 1, column: 1 });
    assert_eq!(d.payload_sha256, digest('a'));
    assert_eq!(d.style_sha256, digest('b'));
    let formula = d
        .formula
        .as_ref()
        .ok_or_else(|| std::io::Error::other("transposed formula missing"))?;
    assert_eq!(
        formula.ast().canonical_formula(formula_limits()?)?,
        "SUM(A1:$B$3)"
    );
    assert_eq!(formula.cache(), &FormulaCache::Absent);
    assert_eq!(plan.receipt().merged_cell_count, 2);
    assert_eq!(plan.receipt().formula_count, 1);
    assert_eq!(plan.receipt().cache_cleared_count, 1);
    assert_eq!(plan.receipt().payload_preserved_count, 4);
    assert_eq!(plan.receipt().style_preserved_count, 4);
    Ok(())
}

#[test]
fn absent_formula_cache_is_not_reported_as_cleared() -> TestResult {
    let grid = merged_grid()?;
    let mut draft = request_draft(&grid, true)?;
    draft
        .cells
        .last_mut()
        .ok_or_else(|| std::io::Error::other("formula cell missing"))?
        .formula
        .as_mut()
        .ok_or_else(|| std::io::Error::other("formula missing"))?
        .cache = FormulaCache::Absent;
    let request = TableTransposeRequest::from_draft(
        draft,
        &grid,
        formula_limits()?,
        TableTransposeLimits::default(),
    )?;
    let plan = TableTransposeBuilder::build(
        &request,
        &grid,
        TableGridLimits::default(),
        formula_limits()?,
        TableTransposeLimits::default(),
    )?;
    assert_eq!(plan.receipt().formula_count, 1);
    assert_eq!(plan.receipt().cache_cleared_count, 0);
    assert_eq!(
        plan.relocations()
            .last()
            .ok_or_else(|| std::io::Error::other("transposed formula cell missing"))?
            .formula
            .as_ref()
            .ok_or_else(|| std::io::Error::other("transposed formula missing"))?
            .cache(),
        &FormulaCache::Absent
    );
    Ok(())
}

#[test]
fn formula_transpose_swaps_reference_indexes_and_anchor_axes() -> TestResult {
    let ast = FormulaAst::parse("SUM($B3,C$2,$A$1)", formula_limits()?)?;
    let transposed = ast.transpose(
        FormulaGridDimensions {
            rows: 4,
            columns: 4,
        },
        formula_limits()?,
    )?;
    assert_eq!(
        transposed.canonical_formula(formula_limits()?)?,
        "SUM(C$2,$B3,$A$1)"
    );
    Ok(())
}

#[test]
fn double_formula_transpose_restores_the_exact_ast() -> TestResult {
    let ast = FormulaAst::parse("(A2+$C$4)/SUM(B1:C2)", formula_limits()?)?;
    let once = ast.transpose(
        FormulaGridDimensions {
            rows: 4,
            columns: 3,
        },
        formula_limits()?,
    )?;
    let twice = once.transpose(
        FormulaGridDimensions {
            rows: 3,
            columns: 4,
        },
        formula_limits()?,
    )?;
    assert_eq!(twice, ast);
    Ok(())
}

#[test]
fn reject_policy_fails_before_a_formula_plan_exists() -> TestResult {
    let grid = merged_grid()?;
    let mut draft = request_draft(&grid, true)?;
    draft.formula_policy = TableTransposeFormulaPolicy::Reject;
    assert_eq!(
        TableTransposeRequest::from_draft(
            draft,
            &grid,
            formula_limits()?,
            TableTransposeLimits::default()
        ),
        Err(TableTransposeError::FormulaPresent)
    );
    Ok(())
}

#[test]
fn formula_owner_must_equal_the_master_anchor() -> TestResult {
    let grid = merged_grid()?;
    let mut draft = request_draft(&grid, true)?;
    let formula = draft
        .cells
        .last_mut()
        .and_then(|cell| cell.formula.as_mut())
        .ok_or_else(|| std::io::Error::other("formula missing"))?;
    formula.owner = CellCoordinate { row: 0, column: 0 };
    assert_eq!(
        TableTransposeRequest::from_draft(
            draft,
            &grid,
            formula_limits()?,
            TableTransposeLimits::default()
        ),
        Err(TableTransposeError::FormulaOwnerMismatch)
    );
    Ok(())
}

#[test]
fn incomplete_duplicate_extra_or_invalid_digest_cells_fail_closed() -> TestResult {
    let grid = unmerged_grid(2, 2)?;
    let mut draft = request_draft(&grid, false)?;
    draft.cells.pop();
    assert_eq!(
        TableTransposeRequest::from_draft(
            draft,
            &grid,
            formula_limits()?,
            TableTransposeLimits::default()
        ),
        Err(TableTransposeError::CellSetMismatch)
    );
    let mut draft = request_draft(&grid, false)?;
    draft.cells[1] = draft.cells[0].clone();
    assert_eq!(
        TableTransposeRequest::from_draft(
            draft,
            &grid,
            formula_limits()?,
            TableTransposeLimits::default()
        ),
        Err(TableTransposeError::CellSetMismatch)
    );
    let mut draft = request_draft(&grid, false)?;
    draft.cells[0].style_sha256 = "ABC".to_owned();
    assert_eq!(
        TableTransposeRequest::from_draft(
            draft,
            &grid,
            formula_limits()?,
            TableTransposeLimits::default()
        ),
        Err(TableTransposeError::DigestInvalid)
    );
    Ok(())
}

#[test]
fn strict_json_rejects_duplicate_unknown_version_and_size() -> TestResult {
    let grid = unmerged_grid(2, 2)?;
    let draft = request_draft(&grid, false)?;
    let json = serde_json::to_vec(&draft)?;
    assert!(
        TableTransposeRequest::from_json(
            &json,
            &grid,
            formula_limits()?,
            TableTransposeLimits::default()
        )
        .is_ok()
    );
    let duplicate =
        String::from_utf8(json.clone())?.replacen('{', "{\"schema_version\":\"duplicate\",", 1);
    assert_eq!(
        TableTransposeRequest::from_json(
            duplicate.as_bytes(),
            &grid,
            formula_limits()?,
            TableTransposeLimits::default()
        ),
        Err(TableTransposeError::InvalidJson)
    );
    let unknown = String::from_utf8(json.clone())?.replacen('{', "{\"unknown\":true,", 1);
    assert_eq!(
        TableTransposeRequest::from_json(
            unknown.as_bytes(),
            &grid,
            formula_limits()?,
            TableTransposeLimits::default()
        ),
        Err(TableTransposeError::InvalidJson)
    );
    let wrong =
        String::from_utf8(json)?.replace(TABLE_TRANSPOSE_SCHEMA_VERSION, "table-transpose/wrong");
    assert_eq!(
        TableTransposeRequest::from_json(
            wrong.as_bytes(),
            &grid,
            formula_limits()?,
            TableTransposeLimits::default()
        ),
        Err(TableTransposeError::UnsupportedVersion)
    );
    assert_eq!(
        TableTransposeRequest::from_json(
            &[],
            &grid,
            formula_limits()?,
            TableTransposeLimits::default()
        ),
        Err(TableTransposeError::InputLimit)
    );
    Ok(())
}

#[test]
fn transposed_dimensions_obey_exact_column_ceiling() -> TestResult {
    let grid = unmerged_grid(1_025, 1)?;
    let request = request(&grid, false)?;
    assert_eq!(
        TableTransposeBuilder::build(
            &request,
            &grid,
            TableGridLimits::default(),
            formula_limits()?,
            TableTransposeLimits::default()
        ),
        Err(TableTransposeError::TransposedGridUnsupported)
    );
    let ast = FormulaAst::parse("A1", formula_limits()?)?;
    assert!(
        ast.transpose(
            FormulaGridDimensions {
                rows: 1_025,
                columns: 1,
            },
            formula_limits()?
        )
        .is_err()
    );
    Ok(())
}

#[test]
fn canonical_request_plan_and_receipt_are_repeatable() -> TestResult {
    let grid = merged_grid()?;
    let request = request(&grid, true)?;
    let first = TableTransposeBuilder::build(
        &request,
        &grid,
        TableGridLimits::default(),
        formula_limits()?,
        TableTransposeLimits::default(),
    )?;
    let second = TableTransposeBuilder::build(
        &request,
        &grid,
        TableGridLimits::default(),
        formula_limits()?,
        TableTransposeLimits::default(),
    )?;
    assert_eq!(
        request.canonical_sha256(TableTransposeLimits::default())?,
        request.canonical_sha256(TableTransposeLimits::default())?
    );
    assert_eq!(
        first.canonical_json(TableTransposeLimits::default())?,
        second.canonical_json(TableTransposeLimits::default())?
    );
    assert_eq!(first.receipt(), second.receipt());
    Ok(())
}

#[test]
fn finite_limits_and_output_bound_return_no_partial_plan() -> TestResult {
    assert_eq!(
        TableTransposeLimits::new(TableTransposeLimitConfig {
            master_cells: 0,
            ..TableTransposeLimitConfig::default()
        }),
        Err(TableTransposeError::InvalidLimit)
    );
    let grid = merged_grid()?;
    let request = request(&grid, true)?;
    let tight = TableTransposeLimits::new(TableTransposeLimitConfig {
        input_bytes: 128,
        serialized_bytes: 256,
        ..TableTransposeLimitConfig::default()
    })?;
    assert_eq!(
        TableTransposeBuilder::build(
            &request,
            &grid,
            TableGridLimits::default(),
            formula_limits()?,
            tight
        ),
        Err(TableTransposeError::OutputLimit)
    );
    Ok(())
}

#[test]
fn debug_surfaces_redact_ids_content_digests_and_formulas() -> TestResult {
    let grid = merged_grid()?;
    let draft = request_draft(&grid, true)?;
    let draft_debug = format!("{draft:?}");
    assert!(!draft_debug.contains("table-main"));
    assert!(!draft_debug.contains(&digest('c')));
    let request = request(&grid, true)?;
    let plan = TableTransposeBuilder::build(
        &request,
        &grid,
        TableGridLimits::default(),
        formula_limits()?,
        TableTransposeLimits::default(),
    )?;
    let debug = format!(
        "{request:?}{plan:?}{:?}{:?}",
        plan.relocations()[0],
        plan.receipt()
    );
    for secret in [
        "table-main",
        "SUM",
        &digest('a'),
        &digest('b'),
        &digest('c'),
    ] {
        assert!(!debug.contains(secret));
    }
    Ok(())
}

#[test]
fn fixed_seed_rectangular_corpus_preserves_exact_cell_identity() -> TestResult {
    for rows in 1..=16 {
        for columns in 1..=16 {
            let grid = unmerged_grid(rows, columns)?;
            let request = request(&grid, false)?;
            let plan = TableTransposeBuilder::build(
                &request,
                &grid,
                TableGridLimits::default(),
                formula_limits()?,
                TableTransposeLimits::default(),
            )?;
            assert_eq!((plan.rows(), plan.columns()), (columns, rows));
            assert_eq!(plan.relocations().len(), grid.master_cell_count());
            for relocation in plan.relocations() {
                assert_eq!(relocation.after.row, relocation.before.column);
                assert_eq!(relocation.after.column, relocation.before.row);
                assert_eq!(relocation.payload_sha256, digest('a'));
                assert_eq!(relocation.style_sha256, digest('b'));
            }
        }
    }
    Ok(())
}

#[test]
fn public_error_codes_are_stable() {
    let cases = [
        (
            TableTransposeError::InvalidLimit,
            "table_transpose_invalid_limit",
        ),
        (
            TableTransposeError::UnsupportedVersion,
            "table_transpose_unsupported_version",
        ),
        (
            TableTransposeError::InputLimit,
            "table_transpose_input_limit",
        ),
        (
            TableTransposeError::InvalidJson,
            "table_transpose_invalid_json",
        ),
        (
            TableTransposeError::GridMismatch,
            "table_transpose_grid_mismatch",
        ),
        (
            TableTransposeError::CellSetMismatch,
            "table_transpose_cell_set_mismatch",
        ),
        (
            TableTransposeError::IdentifierLimit,
            "table_transpose_identifier_limit",
        ),
        (
            TableTransposeError::DigestInvalid,
            "table_transpose_digest_invalid",
        ),
        (
            TableTransposeError::FormulaPresent,
            "table_transpose_formula_present",
        ),
        (
            TableTransposeError::FormulaInvalid,
            "table_transpose_formula_invalid",
        ),
        (
            TableTransposeError::FormulaOwnerMismatch,
            "table_transpose_formula_owner_mismatch",
        ),
        (
            TableTransposeError::TransposedGridUnsupported,
            "table_transpose_grid_unsupported",
        ),
        (
            TableTransposeError::MasterCellLimit,
            "table_transpose_master_cell_limit",
        ),
        (
            TableTransposeError::OutputLimit,
            "table_transpose_output_limit",
        ),
        (
            TableTransposeError::Serialization,
            "table_transpose_serialization",
        ),
        (
            TableTransposeError::AllocationFailed,
            "table_transpose_allocation",
        ),
    ];
    for (error, code) in cases {
        assert_eq!(error.code(), code);
    }
}
