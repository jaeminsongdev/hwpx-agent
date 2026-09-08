use domain_ir::{
    CellCoordinate, FormulaCache, FormulaFunction, FormulaGridDimensions, FormulaLimitConfig,
    FormulaLimits, FormulaNumberFormat, TABLE_AGGREGATE_SCHEMA_VERSION, TableAggregateAxis,
    TableAggregateBuilder, TableAggregateError, TableAggregateRange, TableAggregateRequest,
    TableAggregateRequestDraft,
};

type TestResult = Result<(), Box<dyn std::error::Error>>;

const DIMENSIONS: FormulaGridDimensions = FormulaGridDimensions {
    rows: 6,
    columns: 6,
};

fn limits() -> Result<FormulaLimits, Box<dyn std::error::Error>> {
    Ok(FormulaLimits::new(FormulaLimitConfig {
        rows: 10,
        columns: 10,
        ..FormulaLimitConfig::default()
    })?)
}

fn coordinate(row: u32, column: u32) -> CellCoordinate {
    CellCoordinate { row, column }
}

fn request(
    axis: TableAggregateAxis,
    function: FormulaFunction,
    start: CellCoordinate,
    end: CellCoordinate,
    destination: CellCoordinate,
) -> Result<TableAggregateRequest, TableAggregateError> {
    TableAggregateRequest::from_draft(
        TableAggregateRequestDraft {
            schema_version: TABLE_AGGREGATE_SCHEMA_VERSION.to_owned(),
            axis,
            function,
            source: TableAggregateRange { start, end },
            destination,
        },
        DIMENSIONS,
        FormulaLimits::new(FormulaLimitConfig {
            rows: 10,
            columns: 10,
            ..FormulaLimitConfig::default()
        })?,
    )
}

#[test]
fn all_nine_aggregate_operations_compile_to_exact_formulas() -> TestResult {
    for (axis, range, destination, expected_range) in [
        (
            TableAggregateAxis::Block,
            (coordinate(0, 0), coordinate(1, 1)),
            coordinate(3, 3),
            "A1:B2",
        ),
        (
            TableAggregateAxis::Horizontal,
            (coordinate(2, 0), coordinate(2, 2)),
            coordinate(2, 3),
            "A3:C3",
        ),
        (
            TableAggregateAxis::Vertical,
            (coordinate(0, 2), coordinate(2, 2)),
            coordinate(3, 2),
            "C1:C3",
        ),
    ] {
        for (function, name) in [
            (FormulaFunction::Sum, "SUM"),
            (FormulaFunction::Average, "AVG"),
            (FormulaFunction::Product, "PRODUCT"),
        ] {
            let plan = TableAggregateBuilder::build(
                request(axis, function, range.0, range.1, destination)?,
                limits()?,
            )?;
            assert_eq!(
                plan.formula().ast().canonical_formula(limits()?)?,
                format!("{name}({expected_range})")
            );
            assert_eq!(plan.formula().owner(), destination);
            assert_eq!(plan.formula().cache(), &FormulaCache::Absent);
            assert_eq!(plan.formula().number_format(), FormulaNumberFormat::General);
        }
    }
    Ok(())
}

#[test]
fn capability_ids_are_exact_for_all_functions_and_axes() -> TestResult {
    let expected = [
        (
            TableAggregateAxis::Block,
            FormulaFunction::Sum,
            "table.block_sum",
        ),
        (
            TableAggregateAxis::Block,
            FormulaFunction::Average,
            "table.block_average",
        ),
        (
            TableAggregateAxis::Block,
            FormulaFunction::Product,
            "table.block_product",
        ),
        (
            TableAggregateAxis::Horizontal,
            FormulaFunction::Sum,
            "table.horizontal_sum",
        ),
        (
            TableAggregateAxis::Horizontal,
            FormulaFunction::Average,
            "table.horizontal_average",
        ),
        (
            TableAggregateAxis::Horizontal,
            FormulaFunction::Product,
            "table.horizontal_product",
        ),
        (
            TableAggregateAxis::Vertical,
            FormulaFunction::Sum,
            "table.vertical_sum",
        ),
        (
            TableAggregateAxis::Vertical,
            FormulaFunction::Average,
            "table.vertical_average",
        ),
        (
            TableAggregateAxis::Vertical,
            FormulaFunction::Product,
            "table.vertical_product",
        ),
    ];
    for (axis, function, capability) in expected {
        let (start, end, destination) = match axis {
            TableAggregateAxis::Block => (coordinate(0, 0), coordinate(1, 1), coordinate(3, 3)),
            TableAggregateAxis::Horizontal => {
                (coordinate(2, 0), coordinate(2, 2), coordinate(2, 3))
            }
            TableAggregateAxis::Vertical => (coordinate(0, 2), coordinate(2, 2), coordinate(3, 2)),
        };
        assert_eq!(
            request(axis, function, start, end, destination)?.capability_id(),
            capability
        );
    }
    Ok(())
}

#[test]
fn horizontal_and_vertical_ranges_must_be_strictly_before_destination() {
    for invalid in [
        request(
            TableAggregateAxis::Horizontal,
            FormulaFunction::Sum,
            coordinate(1, 0),
            coordinate(2, 1),
            coordinate(2, 2),
        ),
        request(
            TableAggregateAxis::Horizontal,
            FormulaFunction::Sum,
            coordinate(2, 3),
            coordinate(2, 4),
            coordinate(2, 2),
        ),
        request(
            TableAggregateAxis::Vertical,
            FormulaFunction::Sum,
            coordinate(0, 1),
            coordinate(1, 2),
            coordinate(2, 2),
        ),
        request(
            TableAggregateAxis::Vertical,
            FormulaFunction::Sum,
            coordinate(3, 2),
            coordinate(4, 2),
            coordinate(2, 2),
        ),
    ] {
        assert_eq!(invalid, Err(TableAggregateError::AxisMismatch));
    }
}

#[test]
fn reversed_self_referencing_and_out_of_bounds_requests_fail_closed() {
    assert_eq!(
        request(
            TableAggregateAxis::Block,
            FormulaFunction::Average,
            coordinate(2, 2),
            coordinate(1, 1),
            coordinate(4, 4),
        ),
        Err(TableAggregateError::RangeOrder)
    );
    assert_eq!(
        request(
            TableAggregateAxis::Block,
            FormulaFunction::Average,
            coordinate(1, 1),
            coordinate(3, 3),
            coordinate(2, 2),
        ),
        Err(TableAggregateError::SelfReference)
    );
    assert_eq!(
        request(
            TableAggregateAxis::Block,
            FormulaFunction::Average,
            coordinate(0, 0),
            coordinate(6, 1),
            coordinate(2, 2),
        ),
        Err(TableAggregateError::CoordinateOutOfBounds)
    );
}

#[test]
fn strict_json_rejects_duplicate_unknown_and_wrong_version_fields() -> TestResult {
    let valid = br#"{"schema_version":"hwpx-agent.table-aggregate/v1","axis":"block","function":"sum","source":{"start":{"row":0,"column":0},"end":{"row":1,"column":1}},"destination":{"row":3,"column":3}}"#;
    let parsed = TableAggregateRequest::from_json(valid, DIMENSIONS, limits()?)?;
    assert_eq!(parsed.capability_id(), "table.block_sum");

    let duplicate = br#"{"schema_version":"hwpx-agent.table-aggregate/v1","axis":"block","axis":"vertical","function":"sum","source":{"start":{"row":0,"column":0},"end":{"row":1,"column":1}},"destination":{"row":3,"column":3}}"#;
    assert_eq!(
        TableAggregateRequest::from_json(duplicate, DIMENSIONS, limits()?),
        Err(TableAggregateError::InvalidJson)
    );
    let unknown = String::from_utf8(valid.to_vec())?
        .replace("\"destination\":", "\"unknown\":0,\"destination\":");
    assert_eq!(
        TableAggregateRequest::from_json(unknown.as_bytes(), DIMENSIONS, limits()?),
        Err(TableAggregateError::InvalidJson)
    );
    let wrong = String::from_utf8(valid.to_vec())?.replace(
        TABLE_AGGREGATE_SCHEMA_VERSION,
        "hwpx-agent.table-aggregate/v0",
    );
    assert_eq!(
        TableAggregateRequest::from_json(wrong.as_bytes(), DIMENSIONS, limits()?),
        Err(TableAggregateError::UnsupportedVersion)
    );
    Ok(())
}

#[test]
fn plan_serialization_is_deterministic_and_debug_redacts_formula() -> TestResult {
    let request = request(
        TableAggregateAxis::Block,
        FormulaFunction::Product,
        coordinate(0, 0),
        coordinate(1, 1),
        coordinate(3, 3),
    )?;
    let first = TableAggregateBuilder::build(request.clone(), limits()?)?;
    let second = TableAggregateBuilder::build(request, limits()?)?;
    assert_eq!(
        first.canonical_json(limits()?)?,
        second.canonical_json(limits()?)?
    );
    assert_eq!(
        first.canonical_sha256(limits()?)?,
        second.canonical_sha256(limits()?)?
    );
    assert!(!format!("{first:?}").contains("PRODUCT(A1:B2)"));
    Ok(())
}

#[test]
fn input_output_and_dimension_limits_are_enforced() -> TestResult {
    let tight_input = FormulaLimits::new(FormulaLimitConfig {
        serialized_bytes: 8,
        rows: 10,
        columns: 10,
        ..FormulaLimitConfig::default()
    })?;
    assert_eq!(
        TableAggregateRequest::from_json(b"{}", DIMENSIONS, tight_input),
        Err(TableAggregateError::InvalidJson)
    );
    assert_eq!(
        TableAggregateRequest::from_json(b"123456789", DIMENSIONS, tight_input),
        Err(TableAggregateError::InputLimit)
    );
    let bounded_request = request(
        TableAggregateAxis::Block,
        FormulaFunction::Sum,
        coordinate(0, 0),
        coordinate(1, 1),
        coordinate(3, 3),
    )?;
    let normal = TableAggregateBuilder::build(bounded_request.clone(), limits()?)?;
    let formula_bytes = normal.formula().canonical_json(limits()?)?.len();
    assert!(normal.canonical_json(limits()?)?.len() > formula_bytes);
    let tight_output = FormulaLimits::new(FormulaLimitConfig {
        serialized_bytes: formula_bytes,
        rows: 10,
        columns: 10,
        ..FormulaLimitConfig::default()
    })?;
    assert_eq!(
        TableAggregateBuilder::build(bounded_request, tight_output),
        Err(TableAggregateError::OutputLimit)
    );
    let tight_dimensions = FormulaLimits::new(FormulaLimitConfig {
        rows: 2,
        columns: 2,
        ..FormulaLimitConfig::default()
    })?;
    let draft = TableAggregateRequestDraft {
        schema_version: TABLE_AGGREGATE_SCHEMA_VERSION.to_owned(),
        axis: TableAggregateAxis::Block,
        function: FormulaFunction::Sum,
        source: TableAggregateRange {
            start: coordinate(0, 0),
            end: coordinate(1, 1),
        },
        destination: coordinate(3, 3),
    };
    assert_eq!(
        TableAggregateRequest::from_draft(draft, DIMENSIONS, tight_dimensions),
        Err(TableAggregateError::CoordinateOutOfBounds)
    );
    Ok(())
}

#[test]
fn public_error_codes_are_stable() {
    assert_eq!(
        TableAggregateError::UnsupportedVersion.code(),
        "table_aggregate_unsupported_version"
    );
    assert_eq!(
        TableAggregateError::CoordinateOutOfBounds.code(),
        "table_aggregate_coordinate_out_of_bounds"
    );
    assert_eq!(
        TableAggregateError::SelfReference.code(),
        "table_aggregate_self_reference"
    );
    assert_eq!(
        TableAggregateError::AxisMismatch.code(),
        "table_aggregate_axis_mismatch"
    );
}
