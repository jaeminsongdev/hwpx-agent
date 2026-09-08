use std::collections::BTreeMap;
use std::io::{Cursor, Write};

use domain_ir::{
    FontMetricEvidence, FontMetricStatus, FormulaLimitConfig, FormulaLimits, LengthMicrometers,
    LogicalId, TABLE_LAYOUT_SCHEMA_VERSION, TableCellMeasure, TableCellSpan, TableColumnConstraint,
    TableGrid, TableGridLimits, TableLayoutLimits, TableLayoutPlan, TableLayoutProblem,
    TableLayoutSolver, TableWidthSpec,
};
use hwpx_package::{
    BoundedZipReader, Compression, PackageGraph, PackageGraphLimits, PackageLimits,
    TableFormulaHwpxLimits, TableFormulaHwpxReader, TableLayoutHwpxError,
    TableLayoutHwpxLimitConfig, TableLayoutHwpxLimits, TableLayoutHwpxLowerer,
    TableLayoutHwpxReader, TablePaginationHwpxLimits, TablePaginationHwpxReader,
};
use zip::write::SimpleFileOptions;
use zip::{CompressionMethod, DateTime, ZipWriter};

const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const SECTION_NS: &str = "http://www.hancom.co.kr/hwpml/2011/section";
const CONTAINER: &str = r#"<?xml version="1.0" encoding="UTF-8"?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">
  <rootfiles><rootfile full-path="Contents/content.hpf" media-type="application/oebps-package+xml"/></rootfiles>
</container>"#;
const OPF: &str = r#"<?xml version="1.0" encoding="UTF-8"?>
<opf:package xmlns:opf="http://www.idpf.org/2007/opf" version="2.0">
  <opf:manifest>
    <opf:item id="header" href="header.xml" media-type="application/xml"/>
    <opf:item id="section0" href="section0.xml" media-type="application/xml"/>
  </opf:manifest>
  <opf:spine><opf:itemref idref="section0" linear="yes"/></opf:spine>
</opf:package>"#;

type TestResult<T = ()> = Result<T, Box<dyn std::error::Error>>;

#[derive(Clone, Copy)]
enum LayoutCase {
    FixedColumn,
    FitContent,
    FitPage,
}

fn um(value: i64) -> LengthMicrometers {
    LengthMicrometers::from_raw(value)
}

fn span(identifier: &str, row: u32, column: u32, column_span: u32) -> TestResult<TableCellSpan> {
    Ok(TableCellSpan {
        master_cell_id: LogicalId::parse(identifier)?,
        row,
        column,
        row_span: 1,
        column_span,
    })
}

fn grid_2x2() -> TestResult<TableGrid> {
    Ok(TableGrid::new(
        2,
        2,
        vec![
            span("a", 0, 0, 1)?,
            span("b", 0, 1, 1)?,
            span("c", 1, 0, 1)?,
            span("d", 1, 1, 1)?,
        ],
        TableGridLimits::default(),
    )?)
}

fn merged_grid() -> TestResult<TableGrid> {
    Ok(TableGrid::new(
        2,
        2,
        vec![
            span("wide", 0, 0, 2)?,
            span("left", 1, 0, 1)?,
            span("right", 1, 1, 1)?,
        ],
        TableGridLimits::default(),
    )?)
}

fn metric(status: FontMetricStatus) -> FontMetricEvidence {
    let present = status != FontMetricStatus::Missing;
    FontMetricEvidence {
        status,
        profile_id: present.then(|| "p06-09-layout-modes-test-font/v1".to_owned()),
        source_sha256: present.then(|| "a".repeat(64)),
    }
}

fn measure(
    identifier: &str,
    line_height: i64,
    status: FontMetricStatus,
) -> TestResult<TableCellMeasure> {
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
    case: LayoutCase,
    status: FontMetricStatus,
) -> TestResult<TableLayoutPlan> {
    let identifiers: Vec<(&str, i64)> = match grid.master_cell_count() {
        4 => vec![("a", 1_270), ("b", 1_270), ("c", 2_540), ("d", 2_540)],
        3 => vec![("wide", 1_270), ("left", 2_540), ("right", 2_540)],
        _ => return Err("unsupported test grid".into()),
    };
    let (width, columns) = match case {
        LayoutCase::FixedColumn => (
            TableWidthSpec::Absolute { width: um(50_800) },
            vec![
                TableColumnConstraint {
                    minimum_width: um(12_700),
                    preferred_width: um(12_700),
                    previous_width: um(12_700),
                    fixed_width: Some(um(12_700)),
                },
                TableColumnConstraint {
                    minimum_width: um(12_700),
                    preferred_width: um(25_400),
                    previous_width: um(12_700),
                    fixed_width: None,
                },
            ],
        ),
        LayoutCase::FitContent | LayoutCase::FitPage => (
            match case {
                LayoutCase::FitContent => TableWidthSpec::FitContent,
                LayoutCase::FitPage => TableWidthSpec::FitPage,
                LayoutCase::FixedColumn => unreachable!(),
            },
            vec![
                TableColumnConstraint {
                    minimum_width: um(12_700),
                    preferred_width: um(15_240),
                    previous_width: um(12_700),
                    fixed_width: None,
                },
                TableColumnConstraint {
                    minimum_width: um(12_700),
                    preferred_width: um(22_860),
                    previous_width: um(12_700),
                    fixed_width: None,
                },
            ],
        ),
    };
    let problem = TableLayoutProblem {
        schema_version: TABLE_LAYOUT_SCHEMA_VERSION.to_owned(),
        width,
        body_width: um(50_800),
        columns,
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

fn cell(row: u32, column: u32, column_span: u32, marker: &str) -> String {
    format!(
        concat!(
            r#"<hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="0" borderFillIDRef="1">"#,
            r#"<hp:cellAddr colAddr="{column}" rowAddr="{row}"/>"#,
            r#"<hp:cellSpan colSpan="{column_span}" rowSpan="1"/>"#,
            r#"<hp:cellSz width="1000" height="500"/>"#,
            r#"<hp:cellMargin left="0" right="0" top="0" bottom="0"/>"#,
            r#"<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">"#,
            r#"<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t>{marker}</hp:t></hp:run></hp:p>"#,
            r#"</hp:subList></hp:tc>"#,
        ),
        row = row,
        column = column,
        column_span = column_span,
        marker = marker,
    )
}

fn formula_cell(row: u32, column: u32) -> String {
    format!(
        concat!(
            r#"<hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="0" borderFillIDRef="1">"#,
            r#"<hp:cellAddr colAddr="{column}" rowAddr="{row}"/>"#,
            r#"<hp:cellSpan colSpan="1" rowSpan="1"/>"#,
            r#"<hp:cellSz width="1000" height="500"/>"#,
            r#"<hp:cellMargin left="0" right="0" top="0" bottom="0"/>"#,
            r#"<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">"#,
            r#"<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:ctrl>"#,
            r#"<hp:fieldBegin id="101" type="FORMULA" name="" editable="0" dirty="0" zorder="-1" fieldid="202">"#,
            r#"<hp:parameters cnt="5" name=""><hp:integerParam name="Prop">8</hp:integerParam>"#,
            r#"<hp:stringParam name="Command">=SUM(LEFT)??%g,;;7</hp:stringParam>"#,
            r#"<hp:stringParam name="Formula">=SUM(LEFT)</hp:stringParam>"#,
            r#"<hp:stringParam name="ResultFormat">%g,</hp:stringParam>"#,
            r#"<hp:stringParam name="LastResult">7</hp:stringParam></hp:parameters>"#,
            r#"</hp:fieldBegin></hp:ctrl><hp:t>7</hp:t><hp:ctrl>"#,
            r#"<hp:fieldEnd beginIDRef="101" fieldid="202"/></hp:ctrl><hp:t/></hp:run></hp:p>"#,
            r#"</hp:subList></hp:tc>"#,
        ),
        row = row,
        column = column,
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
                cell(0, 0, 1, &format!("{prefix}-A")),
                cell(0, 1, 1, &format!("{prefix}-B")),
            ],
            vec![
                cell(1, 0, 1, &format!("{prefix}-C")),
                cell(1, 1, 1, &format!("{prefix}-D")),
            ],
        ],
    )
}

fn formula_table(identifier: u32) -> String {
    table(
        identifier,
        &[
            vec![cell(0, 0, 1, "1"), cell(0, 1, 1, "2")],
            vec![cell(1, 0, 1, "7"), formula_cell(1, 1)],
        ],
    )
}

fn merged_table(identifier: u32) -> String {
    table(
        identifier,
        &[
            vec![cell(0, 0, 2, "MERGED")],
            vec![cell(1, 0, 1, "LEFT"), cell(1, 1, 1, "RIGHT")],
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

fn archive(
    parts: Vec<(String, Vec<u8>, CompressionMethod)>,
) -> Result<Vec<u8>, zip::result::ZipError> {
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    for (path, bytes, method) in parts {
        let options = SimpleFileOptions::default()
            .compression_method(method)
            .last_modified_time(DateTime::default())
            .system(zip::System::Unix)
            .unix_permissions(0o644);
        writer.start_file(path, options)?;
        writer.write_all(&bytes)?;
    }
    Ok(writer.finish()?.into_inner())
}

fn package(section: &[u8]) -> Result<Vec<u8>, zip::result::ZipError> {
    archive(vec![
        (
            "mimetype".to_owned(),
            b"application/hwp+zip".to_vec(),
            CompressionMethod::Stored,
        ),
        (
            "version.xml".to_owned(),
            b"<version/>".to_vec(),
            CompressionMethod::Stored,
        ),
        (
            "META-INF/container.xml".to_owned(),
            CONTAINER.as_bytes().to_vec(),
            CompressionMethod::Deflated,
        ),
        (
            "Contents/content.hpf".to_owned(),
            OPF.as_bytes().to_vec(),
            CompressionMethod::Deflated,
        ),
        (
            "Contents/header.xml".to_owned(),
            b"<header/>".to_vec(),
            CompressionMethod::Deflated,
        ),
        (
            "Contents/section0.xml".to_owned(),
            section.to_vec(),
            CompressionMethod::Deflated,
        ),
    ])
}

fn replace_section(source: &[u8], section: &[u8]) -> TestResult<Vec<u8>> {
    let mut reader = BoundedZipReader::open(Cursor::new(source), PackageLimits::default())?;
    let entries = reader.entries().to_vec();
    let mut parts = Vec::new();
    parts.try_reserve_exact(entries.len())?;
    let mut replacements = 0_usize;
    for entry in entries {
        let path = entry.path.as_str().to_owned();
        let method = match entry.compression {
            Compression::Stored => CompressionMethod::Stored,
            Compression::Deflated => CompressionMethod::Deflated,
        };
        let bytes = if path == "Contents/section0.xml" {
            replacements += 1;
            section.to_vec()
        } else {
            reader.read_entry(entry.index)?
        };
        parts.push((path, bytes, method));
    }
    if replacements != 1 {
        return Err("section replacement cardinality mismatch".into());
    }
    Ok(archive(parts)?)
}

fn inspect_package(source: &[u8]) -> TestResult<(PackageGraph, Vec<u8>)> {
    let mut reader = BoundedZipReader::open(Cursor::new(source), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    let section_index = reader
        .entries()
        .iter()
        .find(|entry| entry.path.as_str() == "Contents/section0.xml")
        .map(|entry| entry.index)
        .ok_or("section part missing")?;
    let section = reader.read_entry(section_index)?;
    Ok((graph, section))
}

fn part_hashes(graph: &PackageGraph) -> BTreeMap<String, [u8; 32]> {
    graph
        .parts
        .iter()
        .map(|part| (part.path.as_str().to_owned(), part.raw_sha256))
        .collect()
}

fn formula_limits() -> TestResult<FormulaLimits> {
    Ok(FormulaLimits::new(FormulaLimitConfig {
        rows: 10,
        columns: 10,
        ..FormulaLimitConfig::default()
    })?)
}

#[test]
fn three_layout_modes_have_exact_distinct_readback() -> TestResult {
    let grid = grid_2x2()?;
    let source = ordinary_table(10, "MODES").into_bytes();
    let cases = [
        (LayoutCase::FixedColumn, vec![3_600, 10_800], 14_400),
        (LayoutCase::FitContent, vec![4_320, 6_480], 10_800),
        (LayoutCase::FitPage, vec![6_120, 8_280], 14_400),
    ];
    for (case, expected_columns, expected_total) in cases {
        let plan = plan_for(&grid, case, FontMetricStatus::Verified)?;
        plan.require_verified()?;
        let output =
            TableLayoutHwpxLowerer::lower(&source, &grid, &plan, TableLayoutHwpxLimits::default())?;
        let readback = TableLayoutHwpxReader::read(&output, TableLayoutHwpxLimits::default())?;
        assert_eq!(readback.table_width_hwpunit, expected_total);
        assert_eq!(
            readback
                .cells
                .iter()
                .take(2)
                .map(|cell| cell.width_hwpunit)
                .collect::<Vec<_>>(),
            expected_columns
        );
        assert_eq!(readback.table_height_hwpunit, 1_080);
    }
    Ok(())
}

#[test]
fn fixed_column_remains_exact_while_automatic_column_absorbs_remainder() -> TestResult {
    let grid = grid_2x2()?;
    let plan = plan_for(&grid, LayoutCase::FixedColumn, FontMetricStatus::Verified)?;
    assert_eq!(plan.column_widths(), &[um(12_700), um(38_100)]);
    assert_eq!(plan.total_width(), um(50_800));
    assert_eq!(plan.target_underfill(), um(0));
    let source = ordinary_table(20, "FIXED").into_bytes();
    let output =
        TableLayoutHwpxLowerer::lower(&source, &grid, &plan, TableLayoutHwpxLimits::default())?;
    let readback = TableLayoutHwpxReader::read(&output, TableLayoutHwpxLimits::default())?;
    assert_eq!(readback.cells[0].width_hwpunit, 3_600);
    assert_eq!(readback.cells[1].width_hwpunit, 10_800);
    Ok(())
}

#[test]
fn fit_content_underfills_while_fit_page_exactly_fills_body() -> TestResult {
    let grid = grid_2x2()?;
    let content = plan_for(&grid, LayoutCase::FitContent, FontMetricStatus::Verified)?;
    let page = plan_for(&grid, LayoutCase::FitPage, FontMetricStatus::Verified)?;
    assert_eq!(content.column_widths(), &[um(15_240), um(22_860)]);
    assert_eq!(content.total_width(), um(38_100));
    assert_eq!(content.body_width(), um(50_800));
    assert_eq!(content.target_underfill(), um(0));
    assert_eq!(page.column_widths(), &[um(21_590), um(29_210)]);
    assert_eq!(page.total_width(), um(50_800));
    content.require_verified()?;
    page.require_verified()?;
    Ok(())
}

#[test]
fn full_package_reopen_preserves_formula_pagination_and_non_section_parts() -> TestResult {
    let grid = grid_2x2()?;
    let source_package = package(&section(&[formula_table(30)]))?;
    let source_copy = source_package.clone();
    let (source_graph, source_section) = inspect_package(&source_package)?;
    let source_formula = TableFormulaHwpxReader::read_in_section(
        &source_section,
        0,
        TableFormulaHwpxLimits::default(),
        formula_limits()?,
    )?;
    let source_pagination = TablePaginationHwpxReader::read_in_section(
        &source_section,
        0,
        TablePaginationHwpxLimits::default(),
    )?;
    let source_hashes = part_hashes(&source_graph);

    for case in [
        LayoutCase::FixedColumn,
        LayoutCase::FitContent,
        LayoutCase::FitPage,
    ] {
        let plan = plan_for(&grid, case, FontMetricStatus::Verified)?;
        let target_section = TableLayoutHwpxLowerer::lower_in_section(
            &source_section,
            0,
            &grid,
            &plan,
            TableLayoutHwpxLimits::default(),
        )?;
        let target_package = replace_section(&source_package, &target_section)?;
        assert_eq!(
            target_package,
            replace_section(&source_package, &target_section)?,
            "full-package rebuild must be deterministic"
        );
        assert_eq!(
            source_package, source_copy,
            "source package must be immutable"
        );

        let (target_graph, reopened_section) = inspect_package(&target_package)?;
        assert_eq!(source_graph.package_document, target_graph.package_document);
        assert_eq!(source_graph.relationships, target_graph.relationships);
        assert_eq!(source_graph.spine, target_graph.spine);
        let target_hashes = part_hashes(&target_graph);
        assert_eq!(source_hashes.len(), target_hashes.len());
        for (path, source_sha256) in &source_hashes {
            let target_sha256 = target_hashes.get(path).ok_or("target part missing")?;
            if path == "Contents/section0.xml" {
                assert_ne!(source_sha256, target_sha256);
            } else {
                assert_eq!(source_sha256, target_sha256, "part changed: {path}");
            }
        }

        let target_formula = TableFormulaHwpxReader::read_in_section(
            &reopened_section,
            0,
            TableFormulaHwpxLimits::default(),
            formula_limits()?,
        )?;
        assert_eq!(source_formula.rows, target_formula.rows);
        assert_eq!(source_formula.columns, target_formula.columns);
        assert_eq!(source_formula.formula, target_formula.formula);
        assert_eq!(
            source_formula.formula_field_count,
            target_formula.formula_field_count
        );

        let target_pagination = TablePaginationHwpxReader::read_in_section(
            &reopened_section,
            0,
            TablePaginationHwpxLimits::default(),
        )?;
        assert_eq!(source_pagination.page_split, target_pagination.page_split);
        assert_eq!(
            source_pagination.repeat_header_rows,
            target_pagination.repeat_header_rows
        );
        assert_eq!(source_pagination.row_count, target_pagination.row_count);
        assert_eq!(
            source_pagination.column_count,
            target_pagination.column_count
        );
        assert_eq!(source_pagination.caption, target_pagination.caption);
    }
    Ok(())
}

#[test]
fn merged_cell_and_selected_table_preservation_hold_for_all_modes() -> TestResult {
    let grid = merged_grid()?;
    let first = ordinary_table(40, "FIRST");
    let second = merged_table(41);
    let source = section(&[first.clone(), second]);
    for case in [
        LayoutCase::FixedColumn,
        LayoutCase::FitContent,
        LayoutCase::FitPage,
    ] {
        let plan = plan_for(&grid, case, FontMetricStatus::Verified)?;
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
        assert_eq!(readback.cells[0].column_span, 2);
        assert_eq!(
            readback.cells[0].width_hwpunit,
            readback.table_width_hwpunit
        );
    }
    Ok(())
}

#[test]
fn unverified_mode_plans_and_output_limit_fail_before_publication() -> TestResult {
    let grid = grid_2x2()?;
    let source = ordinary_table(50, "NEGATIVE").into_bytes();
    for case in [
        LayoutCase::FixedColumn,
        LayoutCase::FitContent,
        LayoutCase::FitPage,
    ] {
        let plan = plan_for(&grid, case, FontMetricStatus::Estimated)?;
        assert_eq!(
            TableLayoutHwpxLowerer::lower(&source, &grid, &plan, TableLayoutHwpxLimits::default()),
            Err(TableLayoutHwpxError::UnverifiedPlan)
        );
    }
    let plan = plan_for(&grid, LayoutCase::FitPage, FontMetricStatus::Verified)?;
    let limits = TableLayoutHwpxLimits::new(TableLayoutHwpxLimitConfig {
        output_bytes: source.len() - 1,
        ..TableLayoutHwpxLimitConfig::default()
    })?;
    assert_eq!(
        TableLayoutHwpxLowerer::lower(&source, &grid, &plan, limits),
        Err(TableLayoutHwpxError::OutputLimit)
    );
    Ok(())
}

#[test]
fn lowering_is_deterministic_idempotent_and_receipt_omits_visible_text() -> TestResult {
    let grid = grid_2x2()?;
    let source = ordinary_table(60, "RECEIPT").into_bytes();
    for case in [
        LayoutCase::FixedColumn,
        LayoutCase::FitContent,
        LayoutCase::FitPage,
    ] {
        let plan = plan_for(&grid, case, FontMetricStatus::Verified)?;
        let (first, receipt) = TableLayoutHwpxLowerer::lower_with_receipt(
            &source,
            &grid,
            &plan,
            TableLayoutHwpxLimits::default(),
        )?;
        let second =
            TableLayoutHwpxLowerer::lower(&source, &grid, &plan, TableLayoutHwpxLimits::default())?;
        let third =
            TableLayoutHwpxLowerer::lower(&first, &grid, &plan, TableLayoutHwpxLimits::default())?;
        assert_eq!(first, second);
        assert_eq!(first, third);
        let debug = format!("{receipt:?}");
        assert!(!debug.contains("RECEIPT-A"));
        assert!(!debug.contains("RECEIPT-D"));
        assert_eq!(receipt.source_sha256, sha256(&source));
        assert_eq!(receipt.output_sha256, sha256(&first));
    }
    Ok(())
}

fn sha256(bytes: &[u8]) -> [u8; 32] {
    use sha2::Digest as _;
    sha2::Sha256::digest(bytes).into()
}
