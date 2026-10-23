use domain_ir::formula_evaluation::{
    EvaluationCell, EvaluationError, EvaluationInput, EvaluationLimitConfig, EvaluationLimits,
    FORMULA_EVALUATION_SCOPE, FormulaEvaluationContext,
};
use domain_ir::{CellCoordinate, FormulaAst, FormulaDecimal, FormulaGridDimensions, FormulaLimits};
use std::error::Error;
type TestResult = Result<(), Box<dyn Error>>;
fn c(column: u32) -> CellCoordinate {
    CellCoordinate { row: 0, column }
}
fn numeric(column: u32, coefficient: i64, scale: u8) -> EvaluationCell<'static> {
    EvaluationCell {
        coordinate: c(column),
        input: EvaluationInput::Decimal {
            value: FormulaDecimal::new(coefficient, scale),
        },
    }
}
fn formula(column: u32, ast: &FormulaAst) -> EvaluationCell<'_> {
    EvaluationCell {
        coordinate: c(column),
        input: EvaluationInput::Formula { ast },
    }
}
fn context<'a>(
    cells: &[EvaluationCell<'a>],
    columns: u32,
    limits: EvaluationLimits,
) -> Result<FormulaEvaluationContext<'a>, EvaluationError> {
    FormulaEvaluationContext::bind(
        FormulaGridDimensions { rows: 1, columns },
        cells,
        limits,
        FormulaLimits::default(),
    )
}
fn value(expression: &str) -> Result<FormulaDecimal, Box<dyn Error>> {
    let ast = FormulaAst::parse(expression, FormulaLimits::default())?;
    let cells = [formula(0, &ast)];
    let result = context(&cells, 1, EvaluationLimits::default())?.evaluate(&[c(0)])?;
    Ok(result.values()[0].value)
}
fn error(expression: &str) -> Result<EvaluationError, Box<dyn Error>> {
    let ast = FormulaAst::parse(expression, FormulaLimits::default())?;
    let cells = [formula(0, &ast)];
    Ok(context(&cells, 1, EvaluationLimits::default())?
        .evaluate(&[c(0)])
        .err()
        .ok_or("expected rejection")?)
}

#[test]
fn exact_decimal_operations_no_float_rounding_or_cache() -> TestResult {
    for (expression, coefficient, scale) in [
        ("0.1+0.2", 3, 1),
        ("1.2-0.05", 115, 2),
        ("-1.5*2.4", -36, 1),
        ("1/8", 125, 3),
        ("(-2)^3", -8, 0),
        ("2^-3", 125, 3),
        ("SUM(1,2,3)", 6, 0),
        ("AVG(1,2)", 15, 1),
        ("PRODUCT(0.2,5)", 1, 0),
    ] {
        assert_eq!(value(expression)?, FormulaDecimal::new(coefficient, scale));
    }
    Ok(())
}
#[test]
fn wide_aggregate_intermediates_preserve_representable_final_values() -> TestResult {
    assert_eq!(
        value("AVG(9223372036854775807,9223372036854775807)")?,
        FormulaDecimal::new(i64::MAX, 0)
    );
    assert_eq!(
        value("SUM(9223372036854775807,1,-1)")?,
        FormulaDecimal::new(i64::MAX, 0)
    );
    assert_eq!(
        value("PRODUCT(9223372036854775807,2,0.5)")?,
        FormulaDecimal::new(i64::MAX, 0)
    );
    Ok(())
}
#[test]
fn every_binary_operator_is_checked_and_errors_are_typed() -> TestResult {
    assert_eq!(error("1/0")?, EvaluationError::DivisionByZero);
    assert_eq!(error("1/3")?, EvaluationError::NonTerminatingDecimal);
    assert_eq!(
        error("1/10000000000000")?,
        EvaluationError::DecimalPrecision
    );
    assert_eq!(error("9223372036854775807+1")?, EvaluationError::Overflow);
    assert_eq!(error("9223372036854775807*2")?, EvaluationError::Overflow);
    assert_eq!(error("2^0.5")?, EvaluationError::UnsupportedExponent);
    assert_eq!(error("2^129")?, EvaluationError::UnsupportedExponent);
    assert_eq!(error("0^0")?, EvaluationError::UndefinedPower);
    assert_eq!(error("0^-1")?, EvaluationError::DivisionByZero);
    Ok(())
}
#[test]
fn complete_dependency_diamond_memoization_and_deterministic_receipts() -> TestResult {
    let b = FormulaAst::parse("A1+3", FormulaLimits::default())?;
    let d = FormulaAst::parse("B1+C1", FormulaLimits::default())?;
    let e = FormulaAst::parse("A1*4", FormulaLimits::default())?;
    let cells = [
        numeric(0, 2, 0),
        formula(1, &b),
        formula(2, &e),
        formula(3, &d),
    ];
    let ctx = context(&cells, 4, EvaluationLimits::default())?;
    let first = ctx.evaluate(&[c(3), c(1)])?;
    let second = ctx.evaluate(&[c(3), c(1)])?;
    assert_eq!(first.values(), second.values());
    assert_eq!(first.receipt(), second.receipt());
    assert_eq!(first.values()[0].value, FormulaDecimal::new(13, 0));
    assert_eq!(first.values()[1].value, FormulaDecimal::new(5, 0));
    assert_eq!(first.receipt().computed_cells, 4);
    assert!(first.receipt().reused_dependency_values >= 2);
    assert_eq!(first.receipt().qualification, FORMULA_EVALUATION_SCOPE);
    let reordered = ctx.evaluate(&[c(1), c(3)])?;
    assert_eq!(
        first.receipt().input_sha256,
        reordered.receipt().input_sha256
    );
    assert_ne!(
        first.receipt().result_sha256,
        reordered.receipt().result_sha256
    );
    assert_eq!(format!("{ctx:?}"), "FormulaEvaluationContext(<redacted>)");
    assert_eq!(format!("{first:?}"), "FormulaEvaluation(<redacted>)");
    Ok(())
}
#[test]
fn rectangle_ranges_all_cells_and_all_aggregate_functions() -> TestResult {
    let sum = FormulaAst::parse("SUM($A$1:B2)", FormulaLimits::default())?;
    let avg = FormulaAst::parse("AVG(A1:B2)", FormulaLimits::default())?;
    let product = FormulaAst::parse("PRODUCT(A1:B2)", FormulaLimits::default())?;
    let mut cells = Vec::new();
    for row in 0..2 {
        for column in 0..2 {
            cells.push(EvaluationCell {
                coordinate: CellCoordinate { row, column },
                input: EvaluationInput::Decimal {
                    value: FormulaDecimal::new(i64::from(1 + row * 2 + column), 0),
                },
            });
        }
    }
    for (ast, expected) in [
        (&sum, FormulaDecimal::new(10, 0)),
        (&avg, FormulaDecimal::new(25, 1)),
        (&product, FormulaDecimal::new(24, 0)),
    ] {
        let mut all = cells.clone();
        all.push(formula(2, ast));
        let ctx = FormulaEvaluationContext::bind(
            FormulaGridDimensions {
                rows: 2,
                columns: 3,
            },
            &all,
            EvaluationLimits::default(),
            FormulaLimits::default(),
        )?;
        assert_eq!(ctx.evaluate(&[c(2)])?.values()[0].value, expected);
    }
    Ok(())
}
#[test]
fn missing_blank_text_or_unqualified_values_never_default_to_zero() -> TestResult {
    let ast = FormulaAst::parse("SUM(A1:B1)", FormulaLimits::default())?;
    for cells in [
        vec![formula(2, &ast), numeric(0, 1, 0)],
        vec![
            formula(2, &ast),
            numeric(0, 1, 0),
            EvaluationCell {
                coordinate: c(1),
                input: EvaluationInput::Unavailable,
            },
        ],
    ] {
        assert!(matches!(
            context(&cells, 3, EvaluationLimits::default())?.evaluate(&[c(2)]),
            Err(EvaluationError::MissingValue)
        ));
    }
    Ok(())
}
#[test]
fn cycles_in_direct_indirect_and_aggregate_dependencies_are_rejected() -> TestResult {
    let self_ref = FormulaAst::parse("A1+1", FormulaLimits::default())?;
    assert!(matches!(
        context(&[formula(0, &self_ref)], 1, EvaluationLimits::default())?.evaluate(&[c(0)]),
        Err(EvaluationError::Cycle)
    ));
    let left = FormulaAst::parse("B1", FormulaLimits::default())?;
    let right = FormulaAst::parse("A1", FormulaLimits::default())?;
    assert!(matches!(
        context(
            &[formula(0, &left), formula(1, &right)],
            2,
            EvaluationLimits::default()
        )?
        .evaluate(&[c(0)]),
        Err(EvaluationError::Cycle)
    ));
    let range = FormulaAst::parse("SUM(A1:B1)", FormulaLimits::default())?;
    assert!(matches!(
        context(
            &[formula(0, &range), numeric(1, 1, 0)],
            2,
            EvaluationLimits::default()
        )?
        .evaluate(&[c(0)]),
        Err(EvaluationError::Cycle)
    ));
    Ok(())
}
#[test]
fn work_depth_input_and_result_budgets_fail_without_partial_outputs() -> TestResult {
    let ast = FormulaAst::parse("1+2", FormulaLimits::default())?;
    let cells = [formula(0, &ast)];
    let work = EvaluationLimits::new(EvaluationLimitConfig {
        work: 2,
        ..EvaluationLimitConfig::default()
    })?;
    assert!(matches!(
        context(&cells, 1, work)?.evaluate(&[c(0)]),
        Err(EvaluationError::WorkLimit)
    ));
    let depth = EvaluationLimits::new(EvaluationLimitConfig {
        depth: 1,
        ..EvaluationLimitConfig::default()
    })?;
    assert!(matches!(
        context(&cells, 1, depth)?.evaluate(&[c(0)]),
        Err(EvaluationError::DepthLimit)
    ));
    let input = EvaluationLimits::new(EvaluationLimitConfig {
        input_bytes: 1,
        ..EvaluationLimitConfig::default()
    })?;
    assert!(matches!(
        context(&cells, 1, input),
        Err(EvaluationError::InputLimit)
    ));
    let result = EvaluationLimits::new(EvaluationLimitConfig {
        result_bytes: 1,
        ..EvaluationLimitConfig::default()
    })?;
    assert!(matches!(
        context(&cells, 1, result)?.evaluate(&[c(0)]),
        Err(EvaluationError::ResultLimit)
    ));
    Ok(())
}
#[test]
fn original_ast_grid_and_duplicate_coordinate_guards_are_reused() -> TestResult {
    let ast = FormulaAst::parse("A2", FormulaLimits::default())?;
    assert!(matches!(
        context(&[formula(0, &ast)], 1, EvaluationLimits::default()),
        Err(EvaluationError::OriginalAst)
    ));
    assert!(matches!(
        context(
            &[numeric(0, 1, 0), numeric(0, 2, 0)],
            1,
            EvaluationLimits::default()
        ),
        Err(EvaluationError::DuplicateCell)
    ));
    assert!(matches!(
        context(&[numeric(2, 1, 0)], 1, EvaluationLimits::default()),
        Err(EvaluationError::OutOfBounds)
    ));
    assert!(matches!(
        context(&[], 0, EvaluationLimits::default()),
        Err(EvaluationError::Grid)
    ));
    let zero = EvaluationLimitConfig {
        cells: 0,
        ..EvaluationLimitConfig::default()
    };
    assert!(matches!(
        EvaluationLimits::new(zero),
        Err(EvaluationError::InvalidLimits)
    ));
    Ok(())
}
#[test]
fn target_order_identity_duplicates_and_nonformula_denied() -> TestResult {
    let ast = FormulaAst::parse("2", FormulaLimits::default())?;
    let ctx = context(
        &[formula(0, &ast), numeric(1, 9, 0)],
        2,
        EvaluationLimits::default(),
    )?;
    assert!(matches!(
        ctx.evaluate(&[]),
        Err(EvaluationError::EmptyTargets)
    ));
    assert!(matches!(
        ctx.evaluate(&[c(0), c(0)]),
        Err(EvaluationError::DuplicateTarget)
    ));
    assert!(matches!(
        ctx.evaluate(&[c(1)]),
        Err(EvaluationError::NotFormulaTarget)
    ));
    assert!(matches!(
        ctx.evaluate(&[c(99)]),
        Err(EvaluationError::NotFormulaTarget)
    ));
    Ok(())
}
#[test]
fn bounded_integer_property_checks_for_all_signs() -> TestResult {
    let sum = FormulaAst::parse("A1+B1", FormulaLimits::default())?;
    let product = FormulaAst::parse("A1*B1", FormulaLimits::default())?;
    for left in -20..=20 {
        for right in -20..=20 {
            for (ast, expected) in [(&sum, left + right), (&product, left * right)] {
                let cells = [numeric(0, left, 0), numeric(1, right, 0), formula(2, ast)];
                assert_eq!(
                    context(&cells, 3, EvaluationLimits::default())?
                        .evaluate(&[c(2)])?
                        .values()[0]
                        .value,
                    FormulaDecimal::new(expected, 0)
                );
            }
        }
    }
    Ok(())
}
#[test]
fn input_snapshot_drift_changes_binding_without_mutating_prior_context() -> TestResult {
    let ast = FormulaAst::parse("A1+1", FormulaLimits::default())?;
    let mut cells = [numeric(0, 2, 0), formula(1, &ast)];
    let old = context(&cells, 2, EvaluationLimits::default())?;
    let before = old.evaluate(&[c(1)])?;
    cells[0] = numeric(0, 9, 0);
    let after = context(&cells, 2, EvaluationLimits::default())?.evaluate(&[c(1)])?;
    assert_ne!(before.receipt().input_sha256, after.receipt().input_sha256);
    assert_eq!(before.receipt(), old.evaluate(&[c(1)])?.receipt());
    assert_eq!(after.values()[0].value, FormulaDecimal::new(10, 0));
    Ok(())
}

#[test]
fn original_formula_cached_value_is_never_an_evaluation_input_or_overwritten() -> TestResult {
    let ast = FormulaAst::parse("2+3", FormulaLimits::default())?;
    let original = domain_ir::FormulaCell::from_draft(
        domain_ir::FormulaCellDraft {
            schema_version: domain_ir::TABLE_FORMULA_SCHEMA_VERSION.into(),
            owner: c(0),
            ast: domain_ir::FormulaAstDraft {
                schema_version: ast.schema_version().into(),
                expression: ast.expression().clone(),
            },
            cache: domain_ir::FormulaCache::Unverified {
                value: domain_ir::FormulaValue::Decimal {
                    value: FormulaDecimal::new(999_999, 0),
                },
            },
            number_format: domain_ir::FormulaNumberFormat::General,
        },
        FormulaGridDimensions {
            rows: 1,
            columns: 1,
        },
        FormulaLimits::default(),
    )?;
    let before = original.canonical_json(FormulaLimits::default())?;
    let result = context(
        &[formula(0, original.ast())],
        1,
        EvaluationLimits::default(),
    )?
    .evaluate(&[c(0)])?;
    assert_eq!(result.values()[0].value, FormulaDecimal::new(5, 0));
    assert_eq!(before, original.canonical_json(FormulaLimits::default())?);
    assert_eq!(result.receipt().qualification, FORMULA_EVALUATION_SCOPE);
    Ok(())
}

#[test]
fn large_rectangle_streaming_stops_at_work_budget_without_eager_range_allocation() -> TestResult {
    let ast = FormulaAst::parse("SUM(A1:AMJ10000)", FormulaLimits::default())?;
    let target = CellCoordinate {
        row: 9_999,
        column: 1_023,
    };
    let inputs = [
        numeric(0, 1, 0),
        EvaluationCell {
            coordinate: target,
            input: EvaluationInput::Formula { ast: &ast },
        },
    ];
    let limits = EvaluationLimits::new(EvaluationLimitConfig {
        work: 4,
        ..EvaluationLimitConfig::default()
    })?;
    let ctx = FormulaEvaluationContext::bind(
        FormulaGridDimensions {
            rows: 10_000,
            columns: 1_024,
        },
        &inputs,
        limits,
        FormulaLimits::default(),
    )?;
    assert!(matches!(
        ctx.evaluate(&[target]),
        Err(EvaluationError::WorkLimit)
    ));
    Ok(())
}
