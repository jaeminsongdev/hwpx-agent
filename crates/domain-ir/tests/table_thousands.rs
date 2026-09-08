use domain_ir::{
    CellCoordinate, FormulaAst, FormulaAstDraft, FormulaCache, FormulaCell, FormulaCellDraft,
    FormulaDecimal, FormulaError, FormulaGridDimensions, FormulaLimitConfig, FormulaLimits,
    FormulaNumberFormat, FormulaValue, TABLE_FORMULA_SCHEMA_VERSION,
    TABLE_THOUSANDS_SCHEMA_VERSION, TableThousandsBuilder, TableThousandsError, TableThousandsMode,
    TableThousandsRequest, TableThousandsRequestDraft,
};

type TestResult = Result<(), Box<dyn std::error::Error>>;

const DIMENSIONS: FormulaGridDimensions = FormulaGridDimensions {
    rows: 4,
    columns: 4,
};

fn limits() -> Result<FormulaLimits, FormulaError> {
    FormulaLimits::new(FormulaLimitConfig {
        rows: DIMENSIONS.rows,
        columns: DIMENSIONS.columns,
        ..FormulaLimitConfig::default()
    })
}

const fn coordinate(row: u32, column: u32) -> CellCoordinate {
    CellCoordinate { row, column }
}

fn request(
    mode: TableThousandsMode,
    selected_cells: Vec<CellCoordinate>,
    dimensions: FormulaGridDimensions,
    limits: FormulaLimits,
) -> Result<TableThousandsRequest, TableThousandsError> {
    TableThousandsRequest::from_draft(
        TableThousandsRequestDraft {
            schema_version: TABLE_THOUSANDS_SCHEMA_VERSION.to_owned(),
            mode,
            selected_cells,
        },
        dimensions,
        limits,
    )
}

fn formula_cell(
    owner: CellCoordinate,
    source: &str,
    number_format: FormulaNumberFormat,
    cache: FormulaCache,
    dimensions: FormulaGridDimensions,
    limits: FormulaLimits,
) -> Result<FormulaCell, FormulaError> {
    let ast = FormulaAst::parse(source, limits)?;
    FormulaCell::from_draft(
        FormulaCellDraft {
            schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
            owner,
            ast: FormulaAstDraft {
                schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
                expression: ast.expression().clone(),
            },
            cache,
            number_format,
        },
        dimensions,
        limits,
    )
}

fn decimal_cache(value: i64) -> FormulaCache {
    FormulaCache::Unverified {
        value: FormulaValue::Decimal {
            value: FormulaDecimal::new(value, 0),
        },
    }
}

#[test]
fn add_and_remove_change_only_grouping_and_preserve_sorted_selection() -> TestResult {
    let first_owner = coordinate(0, 0);
    let second_owner = coordinate(2, 1);
    let cells = vec![
        formula_cell(
            second_owner,
            "PRODUCT(A1:B1)",
            FormulaNumberFormat::Number {
                decimal_places: 3,
                use_grouping: false,
            },
            decimal_cache(12_345),
            DIMENSIONS,
            limits()?,
        )?,
        formula_cell(
            first_owner,
            "SUM(B2:C2)",
            FormulaNumberFormat::Number {
                decimal_places: 1,
                use_grouping: false,
            },
            FormulaCache::Absent,
            DIMENSIONS,
            limits()?,
        )?,
    ];
    let before = cells
        .iter()
        .map(|cell| {
            Ok::<_, FormulaError>((
                cell.owner(),
                cell.ast().canonical_sha256(limits()?)?,
                cell.cache().clone(),
            ))
        })
        .collect::<Result<Vec<_>, _>>()?;
    let added = TableThousandsBuilder::build(
        request(
            TableThousandsMode::Add,
            vec![second_owner, first_owner],
            DIMENSIONS,
            limits()?,
        )?,
        &cells,
        limits()?,
    )?;

    assert_eq!(added.capability_id(), "table.thousands_add");
    assert_eq!(
        added.request().selected_cells(),
        &[first_owner, second_owner]
    );
    assert_eq!(added.formatted_cells()[0].owner(), first_owner);
    assert_eq!(added.formatted_cells()[1].owner(), second_owner);
    assert_eq!(
        added.formatted_cells()[0].number_format(),
        FormulaNumberFormat::Number {
            decimal_places: 1,
            use_grouping: true,
        }
    );
    assert_eq!(
        added.formatted_cells()[1].number_format(),
        FormulaNumberFormat::Number {
            decimal_places: 3,
            use_grouping: true,
        }
    );
    for output in added.formatted_cells() {
        let (_, expected_ast, expected_cache) = before
            .iter()
            .find(|(owner, _, _)| *owner == output.owner())
            .ok_or("missing original")?;
        assert_eq!(output.ast().canonical_sha256(limits()?)?, *expected_ast);
        assert_eq!(output.cache(), expected_cache);
    }

    let removed = TableThousandsBuilder::build(
        request(
            TableThousandsMode::Remove,
            vec![first_owner, second_owner],
            DIMENSIONS,
            limits()?,
        )?,
        added.formatted_cells(),
        limits()?,
    )?;
    assert_eq!(removed.capability_id(), "table.thousands_remove");
    assert!(removed.formatted_cells().iter().all(|cell| matches!(
        cell.number_format(),
        FormulaNumberFormat::Number {
            use_grouping: false,
            ..
        }
    )));
    Ok(())
}

#[test]
fn add_is_idempotent_and_plan_bytes_are_deterministic() -> TestResult {
    let owner = coordinate(1, 1);
    let cell = formula_cell(
        owner,
        "AVG(A1:A2)",
        FormulaNumberFormat::Number {
            decimal_places: 2,
            use_grouping: true,
        },
        decimal_cache(1000),
        DIMENSIONS,
        limits()?,
    )?;
    let first = TableThousandsBuilder::build(
        request(TableThousandsMode::Add, vec![owner], DIMENSIONS, limits()?)?,
        &[cell],
        limits()?,
    )?;
    let second = TableThousandsBuilder::build(
        request(TableThousandsMode::Add, vec![owner], DIMENSIONS, limits()?)?,
        first.formatted_cells(),
        limits()?,
    )?;
    assert_eq!(
        first.canonical_json(limits()?)?,
        second.canonical_json(limits()?)?
    );
    assert_eq!(
        first.canonical_sha256(limits()?)?,
        second.canonical_sha256(limits()?)?
    );
    assert!(!format!("{first:?}").contains("AVG(A1:A2)"));
    assert!(format!("{first:?}").contains("<redacted>"));
    Ok(())
}

#[test]
fn request_rejects_empty_duplicate_out_of_bounds_and_oversized_selection() -> TestResult {
    assert_eq!(
        request(TableThousandsMode::Add, vec![], DIMENSIONS, limits()?),
        Err(TableThousandsError::EmptySelection)
    );
    assert_eq!(
        request(
            TableThousandsMode::Add,
            vec![coordinate(0, 0), coordinate(0, 0)],
            DIMENSIONS,
            limits()?,
        ),
        Err(TableThousandsError::DuplicateSelection)
    );
    assert_eq!(
        request(
            TableThousandsMode::Add,
            vec![coordinate(4, 0)],
            DIMENSIONS,
            limits()?,
        ),
        Err(TableThousandsError::CoordinateOutOfBounds)
    );

    let bounded = FormulaLimits::new(FormulaLimitConfig {
        rows: DIMENSIONS.rows,
        columns: DIMENSIONS.columns,
        function_arguments: 1,
        ..FormulaLimitConfig::default()
    })?;
    assert_eq!(
        request(
            TableThousandsMode::Add,
            vec![coordinate(0, 0), coordinate(0, 1)],
            DIMENSIONS,
            bounded,
        ),
        Err(TableThousandsError::SelectionLimit)
    );
    assert_eq!(
        request(
            TableThousandsMode::Add,
            vec![coordinate(0, 0)],
            FormulaGridDimensions {
                rows: 0,
                columns: 4,
            },
            limits()?,
        ),
        Err(TableThousandsError::CoordinateOutOfBounds)
    );
    Ok(())
}

#[test]
fn build_requires_exact_unique_supplied_cells() -> TestResult {
    let first_owner = coordinate(0, 0);
    let second_owner = coordinate(0, 1);
    let make = |owner| {
        formula_cell(
            owner,
            "1+2",
            FormulaNumberFormat::Number {
                decimal_places: 0,
                use_grouping: false,
            },
            FormulaCache::Absent,
            DIMENSIONS,
            limits()?,
        )
    };
    let selected = || {
        request(
            TableThousandsMode::Add,
            vec![first_owner, second_owner],
            DIMENSIONS,
            limits()?,
        )
    };

    assert_eq!(
        TableThousandsBuilder::build(selected()?, &[make(first_owner)?], limits()?),
        Err(TableThousandsError::SelectionMismatch)
    );
    assert_eq!(
        TableThousandsBuilder::build(
            selected()?,
            &[make(first_owner)?, make(first_owner)?],
            limits()?,
        ),
        Err(TableThousandsError::SelectionMismatch)
    );
    assert_eq!(
        TableThousandsBuilder::build(
            selected()?,
            &[make(first_owner)?, make(coordinate(2, 2))?],
            limits()?,
        ),
        Err(TableThousandsError::SelectionMismatch)
    );
    Ok(())
}

#[test]
fn non_number_formats_fail_closed_without_partial_plan() -> TestResult {
    let owner = coordinate(0, 0);
    for number_format in [
        FormulaNumberFormat::General,
        FormulaNumberFormat::Percent { decimal_places: 2 },
        FormulaNumberFormat::Scientific { decimal_places: 2 },
    ] {
        let cell = formula_cell(
            owner,
            "1+2",
            number_format,
            FormulaCache::Absent,
            DIMENSIONS,
            limits()?,
        )?;
        assert_eq!(
            TableThousandsBuilder::build(
                request(TableThousandsMode::Add, vec![owner], DIMENSIONS, limits()?)?,
                &[cell],
                limits()?,
            ),
            Err(TableThousandsError::UnsupportedFormat)
        );
    }
    Ok(())
}

#[test]
fn exact_dimensions_are_revalidated_during_build() -> TestResult {
    let owner = coordinate(0, 0);
    let cell = formula_cell(
        owner,
        "D4",
        FormulaNumberFormat::Number {
            decimal_places: 0,
            use_grouping: false,
        },
        FormulaCache::Absent,
        DIMENSIONS,
        limits()?,
    )?;
    let small = FormulaGridDimensions {
        rows: 2,
        columns: 2,
    };
    assert_eq!(
        TableThousandsBuilder::build(
            request(TableThousandsMode::Add, vec![owner], small, limits()?)?,
            &[cell],
            limits()?,
        ),
        Err(TableThousandsError::Formula(
            FormulaError::ReferenceOutOfBounds
        ))
    );
    Ok(())
}

#[test]
fn strict_json_and_input_bounds_fail_closed() -> TestResult {
    let valid = br#"{"schema_version":"hwpx-agent.table-thousands/v1","mode":"add","selected_cells":[{"row":1,"column":2}]}"#;
    let parsed = TableThousandsRequest::from_json(valid, DIMENSIONS, limits()?)?;
    assert_eq!(parsed.capability_id(), "table.thousands_add");

    for invalid in [
        br#"{"schema_version":"hwpx-agent.table-thousands/v1","mode":"add","mode":"remove","selected_cells":[{"row":1,"column":2}]}"#.as_slice(),
        br#"{"schema_version":"hwpx-agent.table-thousands/v1","mode":"add","selected_cells":[{"row":1,"row":2,"column":2}]}"#.as_slice(),
        br#"{"schema_version":"hwpx-agent.table-thousands/v1","mode":"add","selected_cells":[{"row":1,"column":2}],"unknown":true}"#.as_slice(),
    ] {
        assert_eq!(
            TableThousandsRequest::from_json(invalid, DIMENSIONS, limits()?),
            Err(TableThousandsError::InvalidJson)
        );
    }

    let wrong_version = valid
        .windows(TABLE_THOUSANDS_SCHEMA_VERSION.len())
        .position(|window| window == TABLE_THOUSANDS_SCHEMA_VERSION.as_bytes())
        .ok_or("version marker missing")?;
    let mut wrong = valid.to_vec();
    wrong[wrong_version] = b'x';
    assert_eq!(
        TableThousandsRequest::from_json(&wrong, DIMENSIONS, limits()?),
        Err(TableThousandsError::UnsupportedVersion)
    );

    let tight = FormulaLimits::new(FormulaLimitConfig {
        rows: DIMENSIONS.rows,
        columns: DIMENSIONS.columns,
        input_bytes: valid.len() - 1,
        ..FormulaLimitConfig::default()
    })?;
    assert_eq!(
        TableThousandsRequest::from_json(valid, DIMENSIONS, tight),
        Err(TableThousandsError::InputLimit)
    );
    Ok(())
}

#[test]
fn thousands_plan_output_bound_is_enforced_after_cell_validation() -> TestResult {
    let owner = coordinate(0, 0);
    let cell = formula_cell(
        owner,
        "SUM(A2:B2)",
        FormulaNumberFormat::Number {
            decimal_places: 2,
            use_grouping: false,
        },
        FormulaCache::Absent,
        DIMENSIONS,
        limits()?,
    )?;
    let normal = TableThousandsBuilder::build(
        request(TableThousandsMode::Add, vec![owner], DIMENSIONS, limits()?)?,
        std::slice::from_ref(&cell),
        limits()?,
    )?;
    let cell_bytes = cell.canonical_json(limits()?)?.len();
    let plan_bytes = normal.canonical_json(limits()?)?.len();
    assert!(plan_bytes > cell_bytes + 1);
    let tight = FormulaLimits::new(FormulaLimitConfig {
        rows: DIMENSIONS.rows,
        columns: DIMENSIONS.columns,
        serialized_bytes: plan_bytes - 1,
        ..FormulaLimitConfig::default()
    })?;
    assert_eq!(
        TableThousandsBuilder::build(
            request(TableThousandsMode::Add, vec![owner], DIMENSIONS, tight)?,
            &[cell],
            tight,
        ),
        Err(TableThousandsError::OutputLimit)
    );
    Ok(())
}

#[test]
fn public_error_codes_are_stable() {
    assert_eq!(
        TableThousandsError::UnsupportedVersion.code(),
        "table_thousands_unsupported_version"
    );
    assert_eq!(
        TableThousandsError::DuplicateSelection.code(),
        "table_thousands_duplicate_selection"
    );
    assert_eq!(
        TableThousandsError::SelectionMismatch.code(),
        "table_thousands_selection_mismatch"
    );
    assert_eq!(
        TableThousandsError::UnsupportedFormat.code(),
        "table_thousands_unsupported_format"
    );
    assert_eq!(
        TableThousandsError::OutputLimit.code(),
        "table_thousands_output_limit"
    );
}
