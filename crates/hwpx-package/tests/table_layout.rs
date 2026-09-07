use domain_ir::{
    FontMetricEvidence, FontMetricStatus, LengthMicrometers, LogicalId,
    TABLE_LAYOUT_SCHEMA_VERSION, TableCellMeasure, TableCellSpan, TableColumnConstraint, TableGrid,
    TableGridLimits, TableLayoutLimits, TableLayoutPlan, TableLayoutProblem, TableLayoutSolver,
    TableWidthSpec,
};
use hwpx_package::{
    TableLayoutHwpxError, TableLayoutHwpxLimitConfig, TableLayoutHwpxLimits,
    TableLayoutHwpxLowerer, TableLayoutHwpxReader,
};
use sha2::{Digest as _, Sha256};

const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const SECTION_NS: &str = "http://www.hancom.co.kr/hwpml/2011/section";

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

fn grid_2x2() -> Result<TableGrid, Box<dyn std::error::Error>> {
    Ok(TableGrid::new(
        2,
        2,
        vec![
            span("a", 0, 0, 1, 1)?,
            span("b", 0, 1, 1, 1)?,
            span("c", 1, 0, 1, 1)?,
            span("d", 1, 1, 1, 1)?,
        ],
        TableGridLimits::default(),
    )?)
}

fn merged_grid() -> Result<TableGrid, Box<dyn std::error::Error>> {
    Ok(TableGrid::new(
        2,
        2,
        vec![
            span("wide", 0, 0, 1, 2)?,
            span("left", 1, 0, 1, 1)?,
            span("right", 1, 1, 1, 1)?,
        ],
        TableGridLimits::default(),
    )?)
}

fn metric(status: FontMetricStatus) -> FontMetricEvidence {
    let present = status != FontMetricStatus::Missing;
    FontMetricEvidence {
        status,
        profile_id: present.then(|| "p06-05-test-font/v1".to_owned()),
        source_sha256: present.then(|| "a".repeat(64)),
    }
}

fn measure(
    identifier: &str,
    line_height: i64,
    status: FontMetricStatus,
) -> Result<TableCellMeasure, Box<dyn std::error::Error>> {
    Ok(TableCellMeasure {
        master_cell_id: LogicalId::parse(identifier)?,
        leading_margin: um(127),
        trailing_margin: um(127),
        unbreakable_content_width: um(1_000),
        preferred_content_width: um(1_000),
        line_height: um(line_height),
        font_metric_evidence: metric(status),
    })
}

fn plan_for(
    grid: &TableGrid,
    status: FontMetricStatus,
) -> Result<TableLayoutPlan, Box<dyn std::error::Error>> {
    let identifiers: Vec<(&str, i64)> = match grid.master_cell_count() {
        4 => vec![("a", 1_270), ("b", 1_270), ("c", 2_540), ("d", 2_540)],
        3 => vec![("wide", 1_270), ("left", 2_540), ("right", 2_540)],
        _ => return Err("unsupported test grid".into()),
    };
    let problem = TableLayoutProblem {
        schema_version: TABLE_LAYOUT_SCHEMA_VERSION.to_owned(),
        width: TableWidthSpec::Absolute { width: um(38_100) },
        body_width: um(50_800),
        columns: vec![
            TableColumnConstraint {
                minimum_width: um(12_700),
                preferred_width: um(12_700),
                previous_width: um(12_700),
                fixed_width: Some(um(12_700)),
            },
            TableColumnConstraint {
                minimum_width: um(25_400),
                preferred_width: um(25_400),
                previous_width: um(25_400),
                fixed_width: Some(um(25_400)),
            },
        ],
        cells: identifiers
            .into_iter()
            .map(|(identifier, line_height)| measure(identifier, line_height, status))
            .collect::<Result<Vec<_>, _>>()?,
    };
    Ok(TableLayoutSolver::solve(
        grid,
        &problem,
        TableLayoutLimits::default(),
    )?)
}

fn cell(row: u32, column: u32, row_span: u32, column_span: u32, marker: &str) -> String {
    format!(
        concat!(
            r#"<hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="0" borderFillIDRef="1">"#,
            r#"<hp:cellAddr colAddr="{column}" rowAddr="{row}"/>"#,
            r#"<hp:cellSpan colSpan="{column_span}" rowSpan="{row_span}"/>"#,
            r#"<hp:cellSz width="1000" height="500"/>"#,
            r#"<hp:cellMargin left="0" right="0" top="0" bottom="0"/>"#,
            r#"<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">"#,
            r#"<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t>{marker}</hp:t></hp:run></hp:p>"#,
            r#"</hp:subList></hp:tc>"#,
        ),
        row = row,
        column = column,
        row_span = row_span,
        column_span = column_span,
        marker = marker,
    )
}

fn table(identifier: u32, rows: &[Vec<String>]) -> String {
    let mut body = String::new();
    for cells in rows {
        body.push_str("<hp:tr>");
        body.push_str(&cells.concat());
        body.push_str("</hp:tr>");
    }
    format!(
        concat!(
            r#"<hp:tbl xmlns:hp="{PARAGRAPH_NS}" id="{identifier}" zOrder="0" numberingType="TABLE" textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" pageBreak="CELL" repeatHeader="0" rowCnt="{row_count}" colCnt="2" cellSpacing="0" borderFillIDRef="1" noAdjust="0">"#,
            r#"<hp:sz width="2000" widthRelTo="ABSOLUTE" height="1000" heightRelTo="ABSOLUTE" protect="0"/>"#,
            r#"<hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP" horzAlign="LEFT" vertOffset="0" horzOffset="0"/>"#,
            r#"<hp:outMargin left="0" right="0" top="0" bottom="0"/>"#,
            r#"<hp:inMargin left="0" right="0" top="0" bottom="0"/>"#,
            "{body}</hp:tbl>"
        ),
        PARAGRAPH_NS = PARAGRAPH_NS,
        identifier = identifier,
        row_count = rows.len(),
        body = body,
    )
}

fn ordinary_table(identifier: u32, prefix: &str) -> String {
    table(
        identifier,
        &[
            vec![
                cell(0, 0, 1, 1, &format!("{prefix}-A")),
                cell(0, 1, 1, 1, &format!("{prefix}-B")),
            ],
            vec![
                cell(1, 0, 1, 1, &format!("{prefix}-C")),
                cell(1, 1, 1, 1, &format!("{prefix}-D")),
            ],
        ],
    )
}

fn merged_table(identifier: u32) -> String {
    table(
        identifier,
        &[
            vec![cell(0, 0, 1, 2, "MERGED")],
            vec![cell(1, 0, 1, 1, "LEFT"), cell(1, 1, 1, 1, "RIGHT")],
        ],
    )
}

fn section(tables: &[String]) -> Vec<u8> {
    format!(
        r#"<hs:sec xmlns:hs="{SECTION_NS}" xmlns:hp="{PARAGRAPH_NS}">{}</hs:sec>"#,
        tables.concat()
    )
    .into_bytes()
}

#[test]
fn verified_plan_lowers_table_and_cells_and_preserves_content() -> TestResult {
    let grid = grid_2x2()?;
    let plan = plan_for(&grid, FontMetricStatus::Verified)?;
    let source = ordinary_table(10, "P06-05").into_bytes();
    let before = TableLayoutHwpxReader::read(&source, TableLayoutHwpxLimits::default())?;
    let (output, receipt) = TableLayoutHwpxLowerer::lower_with_receipt(
        &source,
        &grid,
        &plan,
        TableLayoutHwpxLimits::default(),
    )?;
    let after = TableLayoutHwpxReader::read(&output, TableLayoutHwpxLimits::default())?;

    assert_eq!(after.table_width_hwpunit, 10_800);
    assert_eq!(after.table_height_hwpunit, 1_080);
    assert_eq!(
        after
            .cells
            .iter()
            .map(|cell| (cell.width_hwpunit, cell.height_hwpunit))
            .collect::<Vec<_>>(),
        vec![(3_600, 360), (7_200, 360), (3_600, 720), (7_200, 720)]
    );
    assert_eq!(after.content_sha256, before.content_sha256);
    assert_eq!(receipt.content_sha256, before.content_sha256);
    assert_eq!(receipt.modified_attribute_count, 10);
    let source_sha256: [u8; 32] = Sha256::digest(&source).into();
    let output_sha256: [u8; 32] = Sha256::digest(&output).into();
    assert_eq!(receipt.source_sha256, source_sha256);
    assert_eq!(receipt.output_sha256, output_sha256);
    assert_ne!(source, output);
    assert!(std::str::from_utf8(&output)?.contains("P06-05-D"));
    let mut expected = std::str::from_utf8(&source)?.replacen(
        r#"<hp:sz width="2000" widthRelTo="ABSOLUTE" height="1000""#,
        r#"<hp:sz width="10800" widthRelTo="ABSOLUTE" height="1080""#,
        1,
    );
    for (width, height) in [(3_600, 360), (7_200, 360), (3_600, 720), (7_200, 720)] {
        expected = expected.replacen(
            r#"<hp:cellSz width="1000" height="500"/>"#,
            &format!(r#"<hp:cellSz width="{width}" height="{height}"/>"#),
            1,
        );
    }
    assert_eq!(
        output,
        expected.into_bytes(),
        "an unrelated source byte changed"
    );
    Ok(())
}

#[test]
fn merged_cell_uses_exact_column_span_sum() -> TestResult {
    let grid = merged_grid()?;
    let plan = plan_for(&grid, FontMetricStatus::Verified)?;
    let source = merged_table(11).into_bytes();
    let output =
        TableLayoutHwpxLowerer::lower(&source, &grid, &plan, TableLayoutHwpxLimits::default())?;
    let readback = TableLayoutHwpxReader::read(&output, TableLayoutHwpxLimits::default())?;
    assert_eq!(readback.cells.len(), 3);
    assert_eq!(readback.cells[0].column_span, 2);
    assert_eq!(readback.cells[0].width_hwpunit, 10_800);
    assert_eq!(readback.cells[0].height_hwpunit, 360);
    Ok(())
}

#[test]
fn selected_section_table_changes_without_touching_sibling() -> TestResult {
    let grid = grid_2x2()?;
    let plan = plan_for(&grid, FontMetricStatus::Verified)?;
    let first = ordinary_table(21, "FIRST");
    let second = ordinary_table(22, "SECOND");
    let source = section(&[first.clone(), second]);
    assert_eq!(
        TableLayoutHwpxReader::count_in_section(&source, TableLayoutHwpxLimits::default())?,
        2
    );
    let output = TableLayoutHwpxLowerer::lower_in_section(
        &source,
        1,
        &grid,
        &plan,
        TableLayoutHwpxLimits::default(),
    )?;
    let output_text = std::str::from_utf8(&output)?;
    let first_end = output_text.find("</hp:tbl>").ok_or("first table missing")? + 9;
    let source_text = std::str::from_utf8(&source)?;
    let source_first_end = source_text
        .find("</hp:tbl>")
        .ok_or("source table missing")?
        + 9;
    assert_eq!(&output_text[..first_end], &source_text[..source_first_end]);
    let readback =
        TableLayoutHwpxReader::read_in_section(&output, 1, TableLayoutHwpxLimits::default())?;
    assert_eq!(readback.table_width_hwpunit, 10_800);
    Ok(())
}

#[test]
fn lowering_is_idempotent_and_deterministic() -> TestResult {
    let grid = grid_2x2()?;
    let plan = plan_for(&grid, FontMetricStatus::Verified)?;
    let source = ordinary_table(30, "IDEMPOTENT").into_bytes();
    let first =
        TableLayoutHwpxLowerer::lower(&source, &grid, &plan, TableLayoutHwpxLimits::default())?;
    let second =
        TableLayoutHwpxLowerer::lower(&source, &grid, &plan, TableLayoutHwpxLimits::default())?;
    let third =
        TableLayoutHwpxLowerer::lower(&first, &grid, &plan, TableLayoutHwpxLimits::default())?;
    assert_eq!(first, second);
    assert_eq!(first, third);
    Ok(())
}

#[test]
fn estimated_or_missing_font_metrics_cannot_be_published() -> TestResult {
    let grid = grid_2x2()?;
    let source = ordinary_table(40, "UNVERIFIED").into_bytes();
    for status in [FontMetricStatus::Estimated, FontMetricStatus::Missing] {
        let plan = plan_for(&grid, status)?;
        assert_eq!(
            TableLayoutHwpxLowerer::lower(&source, &grid, &plan, TableLayoutHwpxLimits::default()),
            Err(TableLayoutHwpxError::UnverifiedPlan)
        );
    }
    Ok(())
}

#[test]
fn plan_bound_to_a_different_grid_fails_before_mutation() -> TestResult {
    let source_grid = grid_2x2()?;
    let plan = plan_for(&source_grid, FontMetricStatus::Verified)?;
    let different = TableGrid::new(
        2,
        2,
        vec![
            span("w", 0, 0, 1, 1)?,
            span("x", 0, 1, 1, 1)?,
            span("y", 1, 0, 1, 1)?,
            span("z", 1, 1, 1, 1)?,
        ],
        TableGridLimits::default(),
    )?;
    let source = ordinary_table(50, "GRID").into_bytes();
    assert_eq!(
        TableLayoutHwpxLowerer::lower(&source, &different, &plan, TableLayoutHwpxLimits::default()),
        Err(TableLayoutHwpxError::PlanGridMismatch)
    );
    Ok(())
}

#[test]
fn source_grid_overlap_gap_or_span_drift_fails_closed() -> TestResult {
    let grid = grid_2x2()?;
    let plan = plan_for(&grid, FontMetricStatus::Verified)?;
    let source = ordinary_table(60, "BAD-GRID");
    let overlap = source.replacen(
        r#"<hp:cellAddr colAddr="1" rowAddr="0"/>"#,
        r#"<hp:cellAddr colAddr="0" rowAddr="0"/>"#,
        1,
    );
    assert_eq!(
        TableLayoutHwpxLowerer::lower(
            overlap.as_bytes(),
            &grid,
            &plan,
            TableLayoutHwpxLimits::default()
        ),
        Err(TableLayoutHwpxError::GridShapeMismatch)
    );

    let span_drift = source.replacen(r#"colSpan="1""#, r#"colSpan="2""#, 1);
    assert_eq!(
        TableLayoutHwpxLowerer::lower(
            span_drift.as_bytes(),
            &grid,
            &plan,
            TableLayoutHwpxLimits::default()
        ),
        Err(TableLayoutHwpxError::GridShapeMismatch)
    );
    Ok(())
}

#[test]
fn relative_table_size_nonzero_spacing_and_unknown_shape_are_rejected() {
    let source = ordinary_table(70, "SHAPE");
    for (case, changed) in [
        (
            "relative width",
            source.replacen(r#"widthRelTo="ABSOLUTE""#, r#"widthRelTo="PAPER""#, 1),
        ),
        (
            "nonzero spacing",
            source.replacen(r#"cellSpacing="0""#, r#"cellSpacing="1""#, 1),
        ),
        (
            "unknown cell size attribute",
            source.replacen("<hp:cellSz ", r#"<hp:cellSz mystery="1" "#, 1),
        ),
        (
            "unknown table child",
            source.replacen("<hp:inMargin ", "<hp:unknown ", 1),
        ),
    ] {
        assert!(
            TableLayoutHwpxReader::read(changed.as_bytes(), TableLayoutHwpxLimits::default())
                .is_err(),
            "{case} was admitted"
        );
    }
}

#[test]
fn malformed_numbers_booleans_and_dimensions_are_rejected() {
    let source = ordinary_table(80, "VALUES");
    let cases = [
        source.replacen(r#"rowCnt="2""#, r#"rowCnt="+2""#, 1),
        source.replacen(r#"noAdjust="0""#, r#"noAdjust="true""#, 1),
        source.replacen(r#"width="2000""#, r#"width="0""#, 1),
        source.replacen(r#"rowSpan="1""#, r#"rowSpan="0""#, 1),
    ];
    for changed in cases {
        assert!(
            TableLayoutHwpxReader::read(changed.as_bytes(), TableLayoutHwpxLimits::default())
                .is_err()
        );
    }
}

#[test]
fn finite_input_output_element_cell_and_dimension_limits_hold() -> TestResult {
    let source = ordinary_table(90, "LIMITS").into_bytes();
    let input = TableLayoutHwpxLimits::new(TableLayoutHwpxLimitConfig {
        input_bytes: source.len() - 1,
        ..TableLayoutHwpxLimitConfig::default()
    })?;
    assert_eq!(
        TableLayoutHwpxReader::read(&source, input),
        Err(TableLayoutHwpxError::InputLimit)
    );
    let elements = TableLayoutHwpxLimits::new(TableLayoutHwpxLimitConfig {
        elements: 1,
        ..TableLayoutHwpxLimitConfig::default()
    })?;
    assert_eq!(
        TableLayoutHwpxReader::read(&source, elements),
        Err(TableLayoutHwpxError::ElementLimit)
    );
    let cells = TableLayoutHwpxLimits::new(TableLayoutHwpxLimitConfig {
        cells: 3,
        ..TableLayoutHwpxLimitConfig::default()
    })?;
    assert_eq!(
        TableLayoutHwpxReader::read(&source, cells),
        Err(TableLayoutHwpxError::CellLimit)
    );
    let dimensions = TableLayoutHwpxLimits::new(TableLayoutHwpxLimitConfig {
        dimension_hwpunit: 999,
        ..TableLayoutHwpxLimitConfig::default()
    })?;
    assert_eq!(
        TableLayoutHwpxReader::read(&source, dimensions),
        Err(TableLayoutHwpxError::OutOfRange)
    );

    let grid = grid_2x2()?;
    let plan = plan_for(&grid, FontMetricStatus::Verified)?;
    let output = TableLayoutHwpxLimits::new(TableLayoutHwpxLimitConfig {
        output_bytes: source.len() - 1,
        ..TableLayoutHwpxLimitConfig::default()
    })?;
    assert_eq!(
        TableLayoutHwpxLowerer::lower(&source, &grid, &plan, output),
        Err(TableLayoutHwpxError::OutputLimit)
    );
    Ok(())
}

#[test]
fn invalid_limits_and_missing_table_selector_fail_closed() {
    assert_eq!(
        TableLayoutHwpxLimits::new(TableLayoutHwpxLimitConfig {
            tables: 0,
            ..TableLayoutHwpxLimitConfig::default()
        }),
        Err(TableLayoutHwpxError::InvalidLimit)
    );
    let source = section(&[ordinary_table(100, "SELECTOR")]);
    assert_eq!(
        TableLayoutHwpxReader::read_in_section(&source, 1, TableLayoutHwpxLimits::default()),
        Err(TableLayoutHwpxError::UnsupportedShape)
    );
}

#[test]
fn public_error_codes_are_stable() {
    assert_eq!(
        TableLayoutHwpxError::UnverifiedPlan.code(),
        "table_layout_hwpx_unverified_plan"
    );
    assert_eq!(
        TableLayoutHwpxError::PlanGridMismatch.code(),
        "table_layout_hwpx_plan_grid_mismatch"
    );
    assert_eq!(
        TableLayoutHwpxError::GridShapeMismatch.code(),
        "table_layout_hwpx_grid_shape_mismatch"
    );
    assert_eq!(
        TableLayoutHwpxError::ReadbackMismatch.code(),
        "table_layout_hwpx_readback_mismatch"
    );
}
