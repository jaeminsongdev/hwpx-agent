use domain_ir::{
    FontMetricEvidence, FontMetricStatus, FontMetricVerification, LengthMicrometers, LogicalId,
    TABLE_GRID_SCHEMA_VERSION, TABLE_LAYOUT_SCHEMA_VERSION, TableCellMeasure, TableCellSpan,
    TableColumnConstraint, TableGrid, TableGridDraft, TableGridLimits, TableLayoutError,
    TableLayoutLimitConfig, TableLayoutLimits, TableLayoutProblem, TableLayoutSolver,
    TableWidthSpec,
};

type TestResult = Result<(), Box<dyn std::error::Error>>;

fn um(value: i64) -> LengthMicrometers {
    LengthMicrometers::from_raw(value)
}

fn span(
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

fn grid_1x2() -> Result<TableGrid, Box<dyn std::error::Error>> {
    Ok(TableGrid::new(
        1,
        2,
        vec![span("a", 0, 0, 1, 1)?, span("b", 0, 1, 1, 1)?],
        TableGridLimits::default(),
    )?)
}

fn columns() -> Vec<TableColumnConstraint> {
    vec![
        TableColumnConstraint {
            minimum_width: um(1_000),
            preferred_width: um(2_000),
            previous_width: um(2_000),
            fixed_width: Some(um(2_000)),
        },
        TableColumnConstraint {
            minimum_width: um(1_000),
            preferred_width: um(3_000),
            previous_width: um(4_500),
            fixed_width: None,
        },
    ]
}

fn measure(
    identifier: &str,
    minimum: i64,
    preferred: i64,
    line_height: i64,
    metric: FontMetricStatus,
) -> Result<TableCellMeasure, Box<dyn std::error::Error>> {
    Ok(TableCellMeasure {
        master_cell_id: LogicalId::parse(identifier)?,
        leading_margin: um(100),
        trailing_margin: um(100),
        unbreakable_content_width: um(minimum),
        preferred_content_width: um(preferred),
        line_height: um(line_height),
        font_metric_evidence: metric_evidence(metric),
    })
}

fn metric_evidence(status: FontMetricStatus) -> FontMetricEvidence {
    let present = status != FontMetricStatus::Missing;
    FontMetricEvidence {
        status,
        profile_id: present.then(|| "test-font-metrics/v1".to_owned()),
        source_sha256: present.then(|| "a".repeat(64)),
    }
}

fn problem(width: TableWidthSpec) -> Result<TableLayoutProblem, Box<dyn std::error::Error>> {
    Ok(TableLayoutProblem {
        schema_version: TABLE_LAYOUT_SCHEMA_VERSION.to_owned(),
        width,
        body_width: um(7_000),
        columns: columns(),
        cells: vec![
            measure("a", 1_000, 1_500, 500, FontMetricStatus::Verified)?,
            measure("b", 2_000, 4_000, 600, FontMetricStatus::Verified)?,
        ],
    })
}

#[test]
fn fit_content_honors_fixed_minimum_and_preferred_widths() -> TestResult {
    let grid = grid_1x2()?;
    let plan = TableLayoutSolver::solve(
        &grid,
        &problem(TableWidthSpec::FitContent)?,
        TableLayoutLimits::default(),
    )?;
    assert_eq!(plan.column_widths(), &[um(2_000), um(4_200)]);
    assert_eq!(plan.total_width(), um(6_200));
    assert_eq!(plan.body_overflow(), um(0));
    assert_eq!(plan.estimated_row_heights(), &[um(600)]);
    assert_eq!(
        plan.font_metric_verification(),
        FontMetricVerification::Verified
    );
    assert!(!plan.has_overflow());
    plan.require_verified()?;
    assert_eq!(plan.grid_sha256().len(), 64);
    Ok(())
}

#[test]
fn fit_body_preserves_fixed_column_and_fills_available_width() -> TestResult {
    let grid = grid_1x2()?;
    let plan = TableLayoutSolver::solve(
        &grid,
        &problem(TableWidthSpec::FitPage)?,
        TableLayoutLimits::default(),
    )?;
    assert_eq!(plan.column_widths(), &[um(2_000), um(5_000)]);
    assert_eq!(plan.total_width(), um(7_000));
    assert_eq!(plan.width(), TableWidthSpec::FitPage);
    Ok(())
}

#[test]
fn fixed_column_never_moves_toward_a_different_preferred_or_previous_width() -> TestResult {
    let grid = grid_1x2()?;
    let mut problem = problem(TableWidthSpec::FitPage)?;
    problem.columns[0].preferred_width = um(6_000);
    problem.columns[0].previous_width = um(6_500);
    let plan = TableLayoutSolver::solve(&grid, &problem, TableLayoutLimits::default())?;
    assert_eq!(plan.column_widths()[0], um(2_000));
    assert_eq!(plan.column_widths()[1], um(5_000));
    plan.require_verified()?;
    Ok(())
}

#[test]
fn absolute_and_percent_widths_resolve_to_exact_targets() -> TestResult {
    let grid = grid_1x2()?;
    let absolute = TableLayoutSolver::solve(
        &grid,
        &problem(TableWidthSpec::Absolute { width: um(6_000) })?,
        TableLayoutLimits::default(),
    )?;
    assert_eq!(absolute.target_width(), um(6_000));
    assert_eq!(absolute.total_width(), um(6_000));
    assert_eq!(absolute.target_overflow(), um(0));
    assert_eq!(absolute.target_underfill(), um(0));

    let percent = TableLayoutSolver::solve(
        &grid,
        &problem(TableWidthSpec::Percent {
            ratio: domain_ir::RatioMillionths::from_raw(800_000),
        })?,
        TableLayoutLimits::default(),
    )?;
    assert_eq!(percent.target_width(), um(5_600));
    assert_eq!(percent.total_width(), um(5_600));
    percent.require_verified()?;
    Ok(())
}

#[test]
fn exact_target_underfill_is_not_a_verified_fit() -> TestResult {
    let grid = TableGrid::new(
        1,
        1,
        vec![span("fixed", 0, 0, 1, 1)?],
        TableGridLimits::default(),
    )?;
    let problem = TableLayoutProblem {
        schema_version: TABLE_LAYOUT_SCHEMA_VERSION.to_owned(),
        width: TableWidthSpec::FitPage,
        body_width: um(5_000),
        columns: vec![TableColumnConstraint {
            minimum_width: um(1_000),
            preferred_width: um(1_000),
            previous_width: um(1_000),
            fixed_width: Some(um(1_000)),
        }],
        cells: vec![measure("fixed", 500, 500, 500, FontMetricStatus::Verified)?],
    };
    let plan = TableLayoutSolver::solve(&grid, &problem, TableLayoutLimits::default())?;
    assert!(!plan.has_overflow());
    assert_eq!(plan.target_underfill(), um(4_000));
    assert_eq!(
        plan.require_verified(),
        Err(TableLayoutError::TargetWidthUnsatisfied)
    );
    Ok(())
}

#[test]
fn merged_minimum_is_distributed_only_across_automatic_columns() -> TestResult {
    let grid = TableGrid::new(
        1,
        3,
        vec![span("merged", 0, 0, 1, 3)?],
        TableGridLimits::default(),
    )?;
    let problem = TableLayoutProblem {
        schema_version: TABLE_LAYOUT_SCHEMA_VERSION.to_owned(),
        width: TableWidthSpec::FitContent,
        body_width: um(4_000),
        columns: vec![
            TableColumnConstraint {
                minimum_width: um(1_000),
                preferred_width: um(1_000),
                previous_width: um(1_000),
                fixed_width: Some(um(1_000)),
            },
            TableColumnConstraint {
                minimum_width: um(500),
                preferred_width: um(500),
                previous_width: um(500),
                fixed_width: None,
            },
            TableColumnConstraint {
                minimum_width: um(500),
                preferred_width: um(500),
                previous_width: um(500),
                fixed_width: None,
            },
        ],
        cells: vec![measure(
            "merged",
            3_800,
            3_800,
            500,
            FontMetricStatus::Verified,
        )?],
    };
    let plan = TableLayoutSolver::solve(&grid, &problem, TableLayoutLimits::default())?;
    assert_eq!(plan.column_widths(), &[um(1_000), um(1_500), um(1_500)]);
    plan.require_verified()?;
    Ok(())
}

#[test]
fn minimums_are_not_shrunk_when_body_overflows() -> TestResult {
    let grid = TableGrid::new(
        1,
        3,
        vec![span("merged", 0, 0, 1, 3)?],
        TableGridLimits::default(),
    )?;
    let mut problem = problem(TableWidthSpec::FitContent)?;
    problem.body_width = um(3_000);
    problem.columns = vec![
        TableColumnConstraint {
            minimum_width: um(1_000),
            preferred_width: um(1_000),
            previous_width: um(1_000),
            fixed_width: Some(um(1_000)),
        },
        TableColumnConstraint {
            minimum_width: um(500),
            preferred_width: um(500),
            previous_width: um(500),
            fixed_width: None,
        },
        TableColumnConstraint {
            minimum_width: um(500),
            preferred_width: um(500),
            previous_width: um(500),
            fixed_width: None,
        },
    ];
    problem.cells = vec![measure(
        "merged",
        3_800,
        3_800,
        500,
        FontMetricStatus::Verified,
    )?];
    let plan = TableLayoutSolver::solve(&grid, &problem, TableLayoutLimits::default())?;
    assert_eq!(plan.total_width(), um(4_000));
    assert_eq!(plan.body_overflow(), um(1_000));
    assert!(plan.content_deficits().is_empty());
    assert_eq!(
        plan.require_verified(),
        Err(TableLayoutError::LayoutOverflow)
    );
    Ok(())
}

#[test]
fn impossible_fixed_span_reports_exact_content_deficit() -> TestResult {
    let grid = TableGrid::new(
        1,
        1,
        vec![span("fixed", 0, 0, 1, 1)?],
        TableGridLimits::default(),
    )?;
    let problem = TableLayoutProblem {
        schema_version: TABLE_LAYOUT_SCHEMA_VERSION.to_owned(),
        width: TableWidthSpec::FitPage,
        body_width: um(5_000),
        columns: vec![TableColumnConstraint {
            minimum_width: um(1_000),
            preferred_width: um(1_000),
            previous_width: um(1_000),
            fixed_width: Some(um(1_000)),
        }],
        cells: vec![measure(
            "fixed",
            1_800,
            2_800,
            500,
            FontMetricStatus::Verified,
        )?],
    };
    let plan = TableLayoutSolver::solve(&grid, &problem, TableLayoutLimits::default())?;
    assert_eq!(plan.column_widths(), &[um(1_000)]);
    assert_eq!(plan.content_deficits().len(), 1);
    assert_eq!(plan.content_deficits()[0].deficit, um(1_000));
    assert_eq!(plan.objective().content_overflow, um(1_000));
    assert_eq!(
        plan.require_verified(),
        Err(TableLayoutError::LayoutOverflow)
    );
    Ok(())
}

#[test]
fn absent_or_estimated_metrics_never_promote_to_verified() -> TestResult {
    let grid = grid_1x2()?;
    for status in [FontMetricStatus::Estimated, FontMetricStatus::Missing] {
        let mut problem = problem(TableWidthSpec::FitContent)?;
        problem.cells[1].font_metric_evidence = metric_evidence(status);
        let plan = TableLayoutSolver::solve(&grid, &problem, TableLayoutLimits::default())?;
        assert_eq!(
            plan.font_metric_verification(),
            FontMetricVerification::Unverified
        );
        assert_eq!(
            plan.require_verified(),
            Err(TableLayoutError::FontMetricsUnverified)
        );
    }
    Ok(())
}

#[test]
fn font_metric_provenance_is_exact_and_bound_into_the_plan() -> TestResult {
    let grid = grid_1x2()?;
    let baseline = problem(TableWidthSpec::FitContent)?;
    let first = TableLayoutSolver::solve(&grid, &baseline, TableLayoutLimits::default())?;
    assert_eq!(first.font_metric_evidence_sha256().len(), 64);

    let mut changed = baseline.clone();
    changed.cells[1].font_metric_evidence.source_sha256 = Some("b".repeat(64));
    let second = TableLayoutSolver::solve(&grid, &changed, TableLayoutLimits::default())?;
    assert_ne!(
        first.font_metric_evidence_sha256(),
        second.font_metric_evidence_sha256()
    );

    let mut invalid = baseline.clone();
    invalid.cells[0].font_metric_evidence.profile_id = None;
    assert_eq!(
        TableLayoutSolver::solve(&grid, &invalid, TableLayoutLimits::default()),
        Err(TableLayoutError::InvalidFontMetricEvidence)
    );

    let mut invalid = baseline;
    invalid.cells[0].font_metric_evidence.source_sha256 = Some("A".repeat(64));
    assert_eq!(
        TableLayoutSolver::solve(&grid, &invalid, TableLayoutLimits::default()),
        Err(TableLayoutError::InvalidFontMetricEvidence)
    );

    let mut invalid = problem(TableWidthSpec::FitContent)?;
    invalid.cells[0].font_metric_evidence.profile_id = Some(" metric-profile ".to_owned());
    assert_eq!(
        TableLayoutSolver::solve(&grid, &invalid, TableLayoutLimits::default()),
        Err(TableLayoutError::InvalidFontMetricEvidence)
    );
    Ok(())
}

#[test]
fn input_measure_order_does_not_change_the_canonical_plan() -> TestResult {
    let grid = grid_1x2()?;
    let first = problem(TableWidthSpec::FitContent)?;
    let mut second = first.clone();
    second.cells.reverse();
    let left = TableLayoutSolver::solve(&grid, &first, TableLayoutLimits::default())?;
    let right = TableLayoutSolver::solve(&grid, &second, TableLayoutLimits::default())?;
    assert_eq!(left, right);
    assert_eq!(
        left.canonical_json(TableLayoutLimits::default())?,
        right.canonical_json(TableLayoutLimits::default())?
    );
    assert_eq!(
        left.canonical_sha256(TableLayoutLimits::default())?,
        right.canonical_sha256(TableLayoutLimits::default())?
    );
    Ok(())
}

#[test]
fn malformed_shapes_and_bounds_fail_closed() -> TestResult {
    let grid = grid_1x2()?;
    let mut invalid = problem(TableWidthSpec::FitContent)?;
    invalid.schema_version = "unknown".to_owned();
    assert_eq!(
        TableLayoutSolver::solve(&grid, &invalid, TableLayoutLimits::default()),
        Err(TableLayoutError::UnsupportedVersion)
    );

    let mut invalid = problem(TableWidthSpec::FitContent)?;
    invalid.columns.pop();
    assert_eq!(
        TableLayoutSolver::solve(&grid, &invalid, TableLayoutLimits::default()),
        Err(TableLayoutError::ColumnCountMismatch)
    );

    let mut invalid = problem(TableWidthSpec::FitContent)?;
    invalid.cells[1] = invalid.cells[0].clone();
    assert_eq!(
        TableLayoutSolver::solve(&grid, &invalid, TableLayoutLimits::default()),
        Err(TableLayoutError::DuplicateCellMeasure)
    );

    let mut invalid = problem(TableWidthSpec::FitContent)?;
    invalid.columns[1].preferred_width = um(999);
    assert_eq!(
        TableLayoutSolver::solve(&grid, &invalid, TableLayoutLimits::default()),
        Err(TableLayoutError::InvalidColumnConstraint)
    );

    let mut invalid = problem(TableWidthSpec::FitContent)?;
    invalid.cells[1].line_height = um(0);
    assert_eq!(
        TableLayoutSolver::solve(&grid, &invalid, TableLayoutLimits::default()),
        Err(TableLayoutError::DimensionLimitExceeded)
    );
    Ok(())
}

#[test]
fn public_layout_error_codes_are_stable() {
    assert_eq!(
        TableLayoutError::LayoutOverflow.code(),
        "table_layout_overflow"
    );
    assert_eq!(
        TableLayoutError::TargetWidthUnsatisfied.code(),
        "table_layout_target_width_unsatisfied"
    );
    assert_eq!(
        TableLayoutError::FontMetricsUnverified.code(),
        "table_layout_font_metrics_unverified"
    );
    assert_eq!(
        TableLayoutError::InvalidFontMetricEvidence.code(),
        "table_layout_invalid_font_metric_evidence"
    );
}

#[test]
fn output_limit_fails_without_partial_json() -> TestResult {
    let grid = grid_1x2()?;
    let plan = TableLayoutSolver::solve(
        &grid,
        &problem(TableWidthSpec::FitContent)?,
        TableLayoutLimits::default(),
    )?;
    let limits = TableLayoutLimits::new(TableLayoutLimitConfig {
        serialized_bytes: 1,
        ..TableLayoutLimitConfig::default()
    })?;
    assert_eq!(
        plan.canonical_json(limits),
        Err(TableLayoutError::OutputLimitExceeded)
    );
    assert!(!format!("{plan:?}").contains("grid_sha256"));
    Ok(())
}

#[test]
fn deterministic_128_case_overflow_and_metric_corpus() -> TestResult {
    let grid = TableGrid::from_draft(
        TableGridDraft {
            schema_version: TABLE_GRID_SCHEMA_VERSION.to_owned(),
            rows: 1,
            columns: 3,
            master_cells: vec![
                span("a", 0, 0, 1, 1)?,
                span("b", 0, 1, 1, 1)?,
                span("c", 0, 2, 1, 1)?,
            ],
        },
        TableGridLimits::default(),
    )?;
    for case in 0_i64..128 {
        let metric = match case % 3 {
            0 => FontMetricStatus::Verified,
            1 => FontMetricStatus::Estimated,
            _ => FontMetricStatus::Missing,
        };
        let mode = if case % 2 == 0 {
            TableWidthSpec::FitContent
        } else {
            TableWidthSpec::FitPage
        };
        let mut problem = TableLayoutProblem {
            schema_version: TABLE_LAYOUT_SCHEMA_VERSION.to_owned(),
            width: mode,
            body_width: um(2_000 + case * 37),
            columns: (0_i64..3)
                .map(|column| TableColumnConstraint {
                    minimum_width: um(500 + column * 50),
                    preferred_width: um(900 + column * 100 + case),
                    previous_width: um(700 + column * 80),
                    fixed_width: (column == 0 && case % 5 == 0).then_some(um(650)),
                })
                .collect(),
            cells: vec![
                measure("a", 400 + case, 800 + case * 2, 300, metric)?,
                measure("b", 500 + case, 900 + case * 2, 320, metric)?,
                measure("c", 600 + case, 1_000 + case * 2, 340, metric)?,
            ],
        };
        let first = TableLayoutSolver::solve(&grid, &problem, TableLayoutLimits::default())?;
        problem.cells.rotate_left(1);
        let second = TableLayoutSolver::solve(&grid, &problem, TableLayoutLimits::default())?;
        assert_eq!(first, second, "case {case}");
        assert_eq!(
            first.canonical_sha256(TableLayoutLimits::default())?,
            second.canonical_sha256(TableLayoutLimits::default())?,
            "case {case}"
        );
        if metric == FontMetricStatus::Verified && !first.has_overflow() {
            first.require_verified()?;
        }
    }
    Ok(())
}
