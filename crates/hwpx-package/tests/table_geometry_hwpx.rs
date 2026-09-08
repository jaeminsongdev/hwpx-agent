use domain_ir::{
    LengthMicrometers, LogicalId, TableCellSpan, TableGeometryLimits, TableGeometryOperation,
    TableGeometryState, TableGrid, TableGridLimits, TableTrackRange,
};
use hwpx_package::{
    TABLE_GEOMETRY_HWPX_PROFILE_ID, TableGeometryHwpxLowerer, TableLayoutHwpxError,
    TableLayoutHwpxLimitConfig, TableLayoutHwpxLimits, TableLayoutHwpxReader,
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

fn state(grid: &TableGrid) -> Result<TableGeometryState, Box<dyn std::error::Error>> {
    Ok(TableGeometryState::new(
        grid,
        vec![um(1_270), um(2_540)],
        vec![um(1_270), um(1_270)],
        vec![um(12_700), um(25_400)],
        vec![um(12_700), um(12_700)],
        TableGeometryLimits::default(),
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
            r#"<hp:inMargin left="510" right="511" top="141" bottom="142"/>"#,
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
fn lowers_all_three_geometry_operations_with_exact_readback() -> TestResult {
    let grid = grid_2x2()?;
    let source = ordinary_table(10, "GEOMETRY").into_bytes();
    let base = state(&grid)?;
    let cases = [
        (
            TableGeometryOperation::EqualRowHeights {
                range: TableTrackRange::new(0, 2),
            },
            vec![(3_600, 540), (7_200, 540), (3_600, 540), (7_200, 540)],
            (10_800, 1_080),
        ),
        (
            TableGeometryOperation::EqualColumnWidths {
                range: TableTrackRange::new(0, 2),
            },
            vec![(5_400, 360), (5_400, 360), (5_400, 720), (5_400, 720)],
            (10_800, 1_080),
        ),
        (
            TableGeometryOperation::SetRowMinimumHeight {
                range: TableTrackRange::new(0, 2),
                minimum_height: um(1_905),
            },
            vec![(3_600, 540), (7_200, 540), (3_600, 720), (7_200, 720)],
            (10_800, 1_260),
        ),
    ];
    for (operation, cell_sizes, table_size) in cases {
        let result = base.apply(&grid, operation, TableGeometryLimits::default())?;
        let output = TableGeometryHwpxLowerer::lower(
            &source,
            &grid,
            result.state(),
            TableLayoutHwpxLimits::default(),
        )?;
        let readback = TableLayoutHwpxReader::read(&output, TableLayoutHwpxLimits::default())?;
        assert_eq!(
            readback
                .cells
                .iter()
                .map(|cell| (cell.width_hwpunit, cell.height_hwpunit))
                .collect::<Vec<_>>(),
            cell_sizes
        );
        assert_eq!(
            (readback.table_width_hwpunit, readback.table_height_hwpunit),
            table_size
        );
    }
    Ok(())
}

#[test]
fn receipt_binds_state_and_preserves_content_and_margins() -> TestResult {
    let grid = grid_2x2()?;
    let source = ordinary_table(20, "RECEIPT").into_bytes();
    let before = TableLayoutHwpxReader::read(&source, TableLayoutHwpxLimits::default())?;
    let state = state(&grid)?;
    let (output, receipt) = TableGeometryHwpxLowerer::lower_with_receipt(
        &source,
        &grid,
        &state,
        TableLayoutHwpxLimits::default(),
    )?;
    let after = TableLayoutHwpxReader::read(&output, TableLayoutHwpxLimits::default())?;
    assert_eq!(receipt.profile_id, TABLE_GEOMETRY_HWPX_PROFILE_ID);
    assert_eq!(
        receipt.geometry_state_sha256,
        state.canonical_sha256(TableGeometryLimits::default())?
    );
    let source_sha256: [u8; 32] = Sha256::digest(&source).into();
    let output_sha256: [u8; 32] = Sha256::digest(&output).into();
    assert_eq!(receipt.source_sha256, source_sha256);
    assert_eq!(receipt.output_sha256, output_sha256);
    assert_eq!(receipt.modified_attribute_count, 10);
    assert_eq!(after.content_sha256, before.content_sha256);
    assert_eq!(after.inner_margin, before.inner_margin);
    assert_eq!(receipt.content_sha256, before.content_sha256);
    assert!(std::str::from_utf8(&output)?.contains("RECEIPT-D"));
    Ok(())
}

#[test]
fn merged_cell_uses_exact_row_and_column_track_sums() -> TestResult {
    let grid = merged_grid()?;
    let state = state(&grid)?;
    let output = TableGeometryHwpxLowerer::lower(
        merged_table(30).as_bytes(),
        &grid,
        &state,
        TableLayoutHwpxLimits::default(),
    )?;
    let readback = TableLayoutHwpxReader::read(&output, TableLayoutHwpxLimits::default())?;
    assert_eq!(readback.cells.len(), 3);
    assert_eq!(readback.cells[0].column_span, 2);
    assert_eq!(readback.cells[0].width_hwpunit, 10_800);
    assert_eq!(readback.cells[0].height_hwpunit, 360);
    Ok(())
}

#[test]
fn section_selection_preserves_the_unselected_table_exactly() -> TestResult {
    let grid = grid_2x2()?;
    let state = state(&grid)?;
    let first = ordinary_table(41, "FIRST");
    let source = section(&[first.clone(), ordinary_table(42, "SECOND")]);
    let output = TableGeometryHwpxLowerer::lower_in_section(
        &source,
        1,
        &grid,
        &state,
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
fn lowering_is_deterministic_and_idempotent() -> TestResult {
    let grid = grid_2x2()?;
    let state = state(&grid)?;
    let source = ordinary_table(50, "IDEMPOTENT").into_bytes();
    let first =
        TableGeometryHwpxLowerer::lower(&source, &grid, &state, TableLayoutHwpxLimits::default())?;
    let second =
        TableGeometryHwpxLowerer::lower(&source, &grid, &state, TableLayoutHwpxLimits::default())?;
    let third =
        TableGeometryHwpxLowerer::lower(&first, &grid, &state, TableLayoutHwpxLimits::default())?;
    assert_eq!(first, second);
    assert_eq!(first, third);
    Ok(())
}

#[test]
fn grid_identity_and_source_shape_fail_before_publication() -> TestResult {
    let source_grid = grid_2x2()?;
    let state = state(&source_grid)?;
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
    let source = ordinary_table(60, "FAIL");
    assert_eq!(
        TableGeometryHwpxLowerer::lower(
            source.as_bytes(),
            &different,
            &state,
            TableLayoutHwpxLimits::default()
        ),
        Err(TableLayoutHwpxError::GeometryGridMismatch)
    );
    let drift = source.replacen(r#"colSpan="1""#, r#"colSpan="2""#, 1);
    assert_eq!(
        TableGeometryHwpxLowerer::lower(
            drift.as_bytes(),
            &source_grid,
            &state,
            TableLayoutHwpxLimits::default()
        ),
        Err(TableLayoutHwpxError::GridShapeMismatch)
    );
    Ok(())
}

#[test]
fn output_and_dimension_limits_fail_closed() -> TestResult {
    let grid = grid_2x2()?;
    let state = state(&grid)?;
    let source = ordinary_table(70, "LIMIT").into_bytes();
    let output_limit = TableLayoutHwpxLimits::new(TableLayoutHwpxLimitConfig {
        output_bytes: source.len() - 1,
        ..TableLayoutHwpxLimitConfig::default()
    })?;
    assert_eq!(
        TableGeometryHwpxLowerer::lower(&source, &grid, &state, output_limit),
        Err(TableLayoutHwpxError::OutputLimit)
    );
    let dimension_limit = TableLayoutHwpxLimits::new(TableLayoutHwpxLimitConfig {
        dimension_hwpunit: 5_000,
        ..TableLayoutHwpxLimitConfig::default()
    })?;
    assert_eq!(
        TableGeometryHwpxLowerer::lower(&source, &grid, &state, dimension_limit),
        Err(TableLayoutHwpxError::OutOfRange)
    );
    Ok(())
}

#[test]
fn receipt_debug_and_public_errors_are_stable() -> TestResult {
    let grid = grid_2x2()?;
    let state = state(&grid)?;
    let source = ordinary_table(80, "DEBUG").into_bytes();
    let (_, receipt) = TableGeometryHwpxLowerer::lower_with_receipt(
        &source,
        &grid,
        &state,
        TableLayoutHwpxLimits::default(),
    )?;
    let debug = format!("{receipt:?}");
    assert!(!debug.contains(&hex(receipt.source_sha256)));
    assert!(!debug.contains(&hex(receipt.output_sha256)));
    assert!(!debug.contains(&receipt.table_width_hwpunit.to_string()));
    assert_eq!(
        TableLayoutHwpxError::GeometryGridMismatch.code(),
        "table_layout_hwpx_geometry_grid_mismatch"
    );
    assert_eq!(
        TableLayoutHwpxError::GeometryShapeMismatch.code(),
        "table_layout_hwpx_geometry_shape_mismatch"
    );
    Ok(())
}

fn hex(bytes: [u8; 32]) -> String {
    bytes
        .iter()
        .fold(String::with_capacity(64), |mut output, byte| {
            use std::fmt::Write as _;
            let _ = write!(output, "{byte:02x}");
            output
        })
}
