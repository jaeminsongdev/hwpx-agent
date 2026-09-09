use std::io::{Cursor, Write};

use domain_ir::{
    CellCoordinate, LogicalId, TABLE_AUTO_FILL_SERIES_SCHEMA_VERSION, TableAutoFillDefinition,
    TableAutoFillFormulaPolicy, TableAutoFillLimits, TableAutoFillNumber, TableAutoFillOrder,
    TableAutoFillRegion, TableAutoFillSeries, TableAutoFillSeriesDraft, TableAutoFillValue,
};
use hwpx_package::{
    BoundedZipReader, Compression, PackageGraph, PackageGraphLimits, PackageLimits,
    TABLE_AUTO_FILL_HWPX_SCHEMA_VERSION, TableAutoFillHwpxBuilder, TableAutoFillHwpxError,
    TableAutoFillHwpxLimits, TableAutoFillHwpxLowerer, TableAutoFillHwpxPlan,
    TableAutoFillHwpxReadback, TableAutoFillHwpxReader, TableAutoFillHwpxRequest,
    TableAutoFillHwpxRequestDraft, TableRulingHwpxBinding, TableRulingHwpxCellBinding,
};
use sha2::{Digest as _, Sha256};
use zip::write::SimpleFileOptions;
use zip::{CompressionMethod, DateTime, ZipArchive, ZipWriter};

type TestResult<T = ()> = Result<T, Box<dyn std::error::Error>>;

const HEADER: &[u8] = include_bytes!("../src/hancom_2020_minimal_header.xml");
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
    <opf:item id="opaque" href="opaque.bin" media-type="application/octet-stream"/>
  </opf:manifest>
  <opf:spine><opf:itemref idref="section0" linear="yes"/></opf:spine>
</opf:package>"#;

fn id(value: &str) -> TestResult<LogicalId> {
    Ok(LogicalId::parse(value)?)
}

fn flow(character: char) -> String {
    std::iter::repeat_n(character, 64).collect()
}

fn hex(value: impl AsRef<[u8]>) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let mut output = String::with_capacity(value.as_ref().len().saturating_mul(2));
    for byte in value.as_ref() {
        output.push(char::from(DIGITS[usize::from(byte >> 4)]));
        output.push(char::from(DIGITS[usize::from(byte & 0x0f)]));
    }
    output
}

fn paragraph(value: &str, row: u32, column: u32) -> String {
    if value.is_empty() {
        return format!(
            r#"<hp:p id="{row}{column}" paraPrIDRef="{row}" styleIDRef="{column}"><hp:run charPrIDRef="{sum}"><hp:t/></hp:run></hp:p>"#,
            sum = row + column + 1,
        );
    }
    format!(
        r#"<hp:p id="{row}{column}" paraPrIDRef="{row}" styleIDRef="{column}"><hp:run charPrIDRef="{sum}"><hp:t>{value}</hp:t></hp:run></hp:p>"#,
        sum = row + column + 1,
    )
}

fn formula_paragraph(row: u32, column: u32, result: &str) -> String {
    format!(
        concat!(
            r#"<hp:p id="{row}{column}" paraPrIDRef="{row}" styleIDRef="{column}"><hp:run charPrIDRef="{sum}"><hp:ctrl>"#,
            r#"<hp:fieldBegin id="101" type="FORMULA" name="" editable="0" dirty="0" zorder="-1" fieldid="202">"#,
            r#"<hp:parameters cnt="5" name=""><hp:integerParam name="Prop">8</hp:integerParam>"#,
            r#"<hp:stringParam name="Command">=SUM(LEFT)??%g,;;{result}</hp:stringParam>"#,
            r#"<hp:stringParam name="Formula">=SUM(LEFT)</hp:stringParam>"#,
            r#"<hp:stringParam name="ResultFormat">%g,</hp:stringParam>"#,
            r#"<hp:stringParam name="LastResult">{result}</hp:stringParam></hp:parameters>"#,
            r#"</hp:fieldBegin></hp:ctrl><hp:t>{result}</hp:t><hp:ctrl>"#,
            r#"<hp:fieldEnd beginIDRef="101" fieldid="202"/></hp:ctrl><hp:t/></hp:run></hp:p>"#,
        ),
        row = row,
        column = column,
        result = result,
        sum = row + column + 1,
    )
}

fn cell(row: u32, column: u32, row_span: u32, column_span: u32, payload: &str) -> String {
    let width = 1_000 * column_span;
    let height = 600 * row_span;
    format!(
        concat!(
            r#"<hp:tc name="" header="{header}" hasMargin="1" protect="0" editable="0" dirty="0" borderFillIDRef="1">"#,
            r#"<hp:cellAddr colAddr="{column}" rowAddr="{row}"/>"#,
            r#"<hp:cellSpan colSpan="{column_span}" rowSpan="{row_span}"/>"#,
            r#"<hp:cellSz width="{width}" height="{height}"/>"#,
            r#"<hp:cellMargin left="{left}" right="{right}" top="{top}" bottom="{bottom}"/>"#,
            r#"<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="{vertical}" linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">"#,
            "{payload}</hp:subList></hp:tc>"
        ),
        column = column,
        row = row,
        column_span = column_span,
        row_span = row_span,
        width = width,
        height = height,
        payload = payload,
        header = u8::from(row == 0),
        left = row * 10 + column,
        right = row + column,
        top = row * 2,
        bottom = column * 3,
        vertical = if (row + column).is_multiple_of(2) {
            "CENTER"
        } else {
            "BOTTOM"
        },
    )
}

fn caption() -> &'static str {
    concat!(
        r#"<hp:caption side="TOP" fullSz="0" width="42520" gap="850" lastWidth="42520">"#,
        r#"<hp:subList><hp:p><hp:run><hp:t>AUTO FILL CAPTION</hp:t></hp:run></hp:p></hp:subList></hp:caption>"#,
    )
}

fn table_xml(rows: &[Vec<String>], row_count: usize, column_count: usize) -> String {
    let mut body = String::new();
    for row in rows {
        body.push_str("<hp:tr>");
        for cell in row {
            body.push_str(cell);
        }
        body.push_str("</hp:tr>");
    }
    format!(
        concat!(
            r#"<hp:tbl id="700" zOrder="0" numberingType="TABLE" textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" pageBreak="CELL" repeatHeader="1" rowCnt="{row_count}" colCnt="{column_count}" cellSpacing="0" borderFillIDRef="1" noAdjust="0">"#,
            r#"<hp:sz width="{width}" widthRelTo="ABSOLUTE" height="{height}" heightRelTo="ABSOLUTE" protect="0"/>"#,
            r#"<hp:pos treatAsChar="0" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP" horzAlign="LEFT" vertOffset="2000" horzOffset="1000"/>"#,
            r#"<hp:outMargin left="0" right="0" top="0" bottom="0"/>"#,
            "{caption}",
            r#"<hp:inMargin left="0" right="0" top="0" bottom="0"/>"#,
            "{body}</hp:tbl>"
        ),
        row_count = row_count,
        column_count = column_count,
        body = body,
        width = column_count * 1_000,
        height = row_count * 600,
        caption = caption(),
    )
}

fn section_with_table(table: &str) -> Vec<u8> {
    format!(
        r#"<hs:sec xmlns:hs="{SECTION_NS}" xmlns:hp="{PARAGRAPH_NS}">{before}{table}{after}</hs:sec>"#,
        before = paragraph("BEFORE", 8, 8),
        after = paragraph("AFTER", 9, 9),
    )
    .into_bytes()
}

fn regular_values() -> [[&'static str; 2]; 3] {
    [["header", "label"], ["old", ""], ["true", "3.50"]]
}

fn regular_section() -> Vec<u8> {
    let rows = regular_values()
        .iter()
        .zip(0_u32..)
        .map(|(values, row)| {
            values
                .iter()
                .zip(0_u32..)
                .map(|(value, column)| cell(row, column, 1, 1, &paragraph(value, row, column)))
                .collect::<Vec<_>>()
        })
        .collect::<Vec<_>>();
    section_with_table(&table_xml(&rows, 3, 2))
}

fn regular_binding(prefix: &str) -> TestResult<TableRulingHwpxBinding> {
    let mut cells = Vec::new();
    for (row, row_values) in regular_values().iter().enumerate() {
        for (column, value) in row_values.iter().enumerate() {
            cells.push(TableRulingHwpxCellBinding {
                master_cell_id: id(&format!("{prefix}-cell-{row}-{column}"))?,
                payload_block_ids: if value.is_empty() {
                    Vec::new()
                } else {
                    vec![id(&format!("{prefix}-payload-{row}-{column}"))?]
                },
            });
        }
    }
    Ok(TableRulingHwpxBinding {
        table_id: id(&format!("{prefix}-table"))?,
        row_boundaries_hwpunit: vec![0, 600, 1_200, 1_800],
        column_boundaries_hwpunit: vec![0, 1_000, 2_000],
        cells,
    })
}

fn region() -> TableAutoFillRegion {
    TableAutoFillRegion {
        start: CellCoordinate { row: 1, column: 0 },
        end: CellCoordinate { row: 2, column: 1 },
    }
}

fn make_series(
    prefix: &str,
    definition: TableAutoFillDefinition,
) -> TestResult<TableAutoFillSeries> {
    Ok(TableAutoFillSeries::from_draft(
        TableAutoFillSeriesDraft {
            schema_version: TABLE_AUTO_FILL_SERIES_SCHEMA_VERSION.to_owned(),
            series_id: id(&format!("{prefix}-series"))?,
            definition,
        },
        TableAutoFillLimits::default(),
    )?)
}

fn explicit_series(prefix: &str) -> TestResult<TableAutoFillSeries> {
    make_series(
        prefix,
        TableAutoFillDefinition::ExplicitCycle {
            items: vec![
                TableAutoFillValue::Text {
                    value: "A<&".to_owned(),
                },
                TableAutoFillValue::Integer { value: 2 },
                TableAutoFillValue::Blank,
                TableAutoFillValue::Decimal {
                    coefficient: 123,
                    scale: 2,
                },
            ],
        },
    )
}

fn read(
    section: &[u8],
    binding: &TableRulingHwpxBinding,
    selected: TableAutoFillRegion,
) -> Result<TableAutoFillHwpxReadback, TableAutoFillHwpxError> {
    TableAutoFillHwpxReader::read_context(
        HEADER,
        section,
        0,
        selected,
        binding,
        TableAutoFillHwpxLimits::default(),
    )
}

#[allow(clippy::too_many_arguments)]
fn draft(
    source: &TableAutoFillHwpxReadback,
    series: &TableAutoFillSeries,
    order: TableAutoFillOrder,
    start_index: u64,
    formula_policy: TableAutoFillFormulaPolicy,
    target_payload_block_ids: Vec<Option<LogicalId>>,
    before_flow: char,
    after_flow: char,
) -> TestResult<TableAutoFillHwpxRequestDraft> {
    let limits = TableAutoFillHwpxLimits::default();
    Ok(TableAutoFillHwpxRequestDraft {
        schema_version: TABLE_AUTO_FILL_HWPX_SCHEMA_VERSION.to_owned(),
        table_ordinal: source.table_ordinal,
        region: source.region,
        order,
        start_index,
        formula_policy,
        expected_header_sha256: hex(source.header_sha256),
        expected_section_sha256: hex(source.section_sha256),
        expected_table_content_sha256: hex(source.ruling.table_content_sha256),
        expected_source_state_sha256: hex(source
            .ruling
            .state
            .canonical_sha256(limits.native.ruling)?),
        expected_source_grid_sha256: hex(source.ruling.grid.canonical_sha256()?),
        expected_scalar_state_sha256: hex(source.scalar_state_sha256),
        expected_pagination_policy_sha256: hex(source.pagination_policy_sha256),
        expected_series_sha256: hex(series.canonical_sha256(limits.auto_fill)?),
        expected_source_table_count: source.source_table_count,
        expected_document_flow_sha256: flow(before_flow),
        target_document_flow_sha256: flow(after_flow),
        target_payload_block_ids,
    })
}

fn admitted(
    source: &TableAutoFillHwpxReadback,
    series: &TableAutoFillSeries,
    draft: TableAutoFillHwpxRequestDraft,
    current_flow: char,
) -> TestResult<(TableAutoFillHwpxRequest, TableAutoFillHwpxPlan)> {
    let limits = TableAutoFillHwpxLimits::default();
    let request =
        TableAutoFillHwpxRequest::from_draft(draft, series, source, &flow(current_flow), limits)?;
    let plan =
        TableAutoFillHwpxBuilder::build(&request, series, source, &flow(current_flow), limits)?;
    Ok((request, plan))
}

fn regular_target_ids(prefix: &str) -> TestResult<Vec<Option<LogicalId>>> {
    Ok(vec![
        Some(id(&format!("{prefix}-payload-1-0"))?),
        Some(id(&format!("{prefix}-generated-1-1"))?),
        None,
        Some(id(&format!("{prefix}-payload-2-1"))?),
    ])
}

#[test]
fn explicit_cycle_rewrites_only_selected_runs_and_preserves_styles_pagination_and_caption()
-> TestResult {
    let section = regular_section();
    let binding = regular_binding("cycle")?;
    let source = read(&section, &binding, region())?;
    let series = explicit_series("cycle")?;
    let request_draft = draft(
        &source,
        &series,
        TableAutoFillOrder::RowMajor,
        0,
        TableAutoFillFormulaPolicy::Reject,
        regular_target_ids("cycle")?,
        'a',
        'b',
    )?;
    let (request, plan) = admitted(&source, &series, request_draft, 'a')?;
    let output = TableAutoFillHwpxLowerer::lower(
        HEADER,
        &section,
        &binding,
        &flow('a'),
        &series,
        &request,
        &plan,
        TableAutoFillHwpxLimits::default(),
    )?;
    let xml = String::from_utf8(output.section.clone())?;
    assert!(xml.contains("<hp:t>A&lt;&amp;</hp:t>"));
    assert!(xml.contains("<hp:t>2</hp:t>"));
    assert!(xml.contains("<hp:t>1.23</hp:t>"));
    assert!(!xml.contains("<hp:t>true</hp:t>"));
    assert!(xml.contains("paraPrIDRef=\"1\" styleIDRef=\"0\""));
    assert!(xml.contains("charPrIDRef=\"2\""));
    assert!(xml.contains("AUTO FILL CAPTION"));
    assert!(xml.contains("<hp:t>header</hp:t>"));
    assert!(xml.contains("<hp:t>label</hp:t>"));
    assert_eq!(output.header, HEADER);
    assert_eq!(output.receipt.selected_cell_count, 4);
    assert_eq!(output.receipt.semantic_change_count, 4);
    assert_eq!(output.receipt.source_formula_count, 0);
    assert_eq!(output.receipt.target_formula_count, 0);
    assert_eq!(output.receipt.repeat_header_rows, 1);
    assert!(output.receipt.caption_preserved);
    assert_eq!(output.receipt.source_table_count, 1);
    assert_eq!(output.receipt.target_table_count, 1);
    Ok(())
}

#[test]
fn column_major_numbers_and_extended_dates_follow_exact_series_order() -> TestResult {
    let section = regular_section();
    let binding = regular_binding("column")?;
    let selected = region();
    let source = read(&section, &binding, selected)?;
    let series = make_series(
        "column",
        TableAutoFillDefinition::LinearNumber {
            start: TableAutoFillNumber {
                coefficient: 15,
                scale: 1,
            },
            step: TableAutoFillNumber {
                coefficient: -5,
                scale: 1,
            },
        },
    )?;
    let ids = vec![
        Some(id("column-payload-1-0")?),
        Some(id("column-generated-1-1")?),
        Some(id("column-payload-2-0")?),
        Some(id("column-payload-2-1")?),
    ];
    let request_draft = draft(
        &source,
        &series,
        TableAutoFillOrder::ColumnMajor,
        1,
        TableAutoFillFormulaPolicy::Reject,
        ids,
        'c',
        'd',
    )?;
    let (request, plan) = admitted(&source, &series, request_draft, 'c')?;
    let output = TableAutoFillHwpxLowerer::lower(
        HEADER,
        &section,
        &binding,
        &flow('c'),
        &series,
        &request,
        &plan,
        TableAutoFillHwpxLimits::default(),
    )?;
    let xml = String::from_utf8(output.section)?;
    for expected in ["1", "0.5", "0", "-0.5"] {
        assert!(xml.contains(&format!("<hp:t>{expected}</hp:t>")));
    }

    let one_cell = TableAutoFillRegion {
        start: CellCoordinate { row: 1, column: 1 },
        end: CellCoordinate { row: 1, column: 1 },
    };
    let source = read(&section, &binding, one_cell)?;
    let dates = make_series(
        "date",
        TableAutoFillDefinition::LinearDateDays {
            start_days_since_unix_epoch: 0,
            step_days: 1,
        },
    )?;
    let request_draft = draft(
        &source,
        &dates,
        TableAutoFillOrder::RowMajor,
        0,
        TableAutoFillFormulaPolicy::Reject,
        vec![Some(id("date-generated")?)],
        'e',
        'f',
    )?;
    let (request, plan) = admitted(&source, &dates, request_draft, 'e')?;
    let output = TableAutoFillHwpxLowerer::lower(
        HEADER,
        &section,
        &binding,
        &flow('e'),
        &dates,
        &request,
        &plan,
        TableAutoFillHwpxLimits::default(),
    )?;
    assert!(String::from_utf8(output.section)?.contains("<hp:t>1970-01-01</hp:t>"));
    Ok(())
}

fn formula_section() -> Vec<u8> {
    let rows = vec![
        vec![
            cell(0, 0, 1, 1, &paragraph("header", 0, 0)),
            cell(0, 1, 1, 1, &paragraph("value", 0, 1)),
        ],
        vec![
            cell(1, 0, 1, 1, &paragraph("3", 1, 0)),
            cell(1, 1, 1, 1, &formula_paragraph(1, 1, "3")),
        ],
    ];
    section_with_table(&table_xml(&rows, 2, 2))
}

fn formula_binding(prefix: &str) -> TestResult<TableRulingHwpxBinding> {
    Ok(TableRulingHwpxBinding {
        table_id: id(&format!("{prefix}-table"))?,
        row_boundaries_hwpunit: vec![0, 600, 1_200],
        column_boundaries_hwpunit: vec![0, 1_000, 2_000],
        cells: vec![
            TableRulingHwpxCellBinding {
                master_cell_id: id(&format!("{prefix}-cell-0-0"))?,
                payload_block_ids: vec![id(&format!("{prefix}-payload-0-0"))?],
            },
            TableRulingHwpxCellBinding {
                master_cell_id: id(&format!("{prefix}-cell-0-1"))?,
                payload_block_ids: vec![id(&format!("{prefix}-payload-0-1"))?],
            },
            TableRulingHwpxCellBinding {
                master_cell_id: id(&format!("{prefix}-cell-1-0"))?,
                payload_block_ids: vec![id(&format!("{prefix}-payload-1-0"))?],
            },
            TableRulingHwpxCellBinding {
                master_cell_id: id(&format!("{prefix}-cell-1-1"))?,
                payload_block_ids: Vec::new(),
            },
        ],
    })
}

#[test]
#[allow(clippy::too_many_lines)]
fn replace_bound_clears_exact_formula_while_reject_and_unselected_formula_fail_or_preserve()
-> TestResult {
    let section = formula_section();
    let binding = formula_binding("formula")?;
    let selected = TableAutoFillRegion {
        start: CellCoordinate { row: 1, column: 1 },
        end: CellCoordinate { row: 1, column: 1 },
    };
    let source = read(&section, &binding, selected)?;
    let series = make_series(
        "formula",
        TableAutoFillDefinition::ExplicitCycle {
            items: vec![TableAutoFillValue::Integer { value: 9 }],
        },
    )?;
    let reject = draft(
        &source,
        &series,
        TableAutoFillOrder::RowMajor,
        0,
        TableAutoFillFormulaPolicy::Reject,
        vec![Some(id("formula-generated")?)],
        '1',
        '2',
    )?;
    assert!(matches!(
        TableAutoFillHwpxRequest::from_draft(
            reject,
            &series,
            &source,
            &flow('1'),
            TableAutoFillHwpxLimits::default(),
        ),
        Err(TableAutoFillHwpxError::AutoFill(_))
    ));
    let replace = draft(
        &source,
        &series,
        TableAutoFillOrder::RowMajor,
        0,
        TableAutoFillFormulaPolicy::ReplaceBound,
        vec![Some(id("formula-generated")?)],
        '1',
        '2',
    )?;
    let (request, plan) = admitted(&source, &series, replace, '1')?;
    let output = TableAutoFillHwpxLowerer::lower(
        HEADER,
        &section,
        &binding,
        &flow('1'),
        &series,
        &request,
        &plan,
        TableAutoFillHwpxLimits::default(),
    )?;
    let xml = String::from_utf8(output.section)?;
    assert!(!xml.contains("fieldBegin"));
    assert!(xml.contains("<hp:t>9</hp:t>"));
    assert_eq!(output.receipt.source_formula_count, 1);
    assert_eq!(output.receipt.target_formula_count, 0);

    let other = TableAutoFillRegion {
        start: CellCoordinate { row: 1, column: 0 },
        end: CellCoordinate { row: 1, column: 0 },
    };
    let source = read(&section, &binding, other)?;
    let one = make_series(
        "other",
        TableAutoFillDefinition::ExplicitCycle {
            items: vec![TableAutoFillValue::Integer { value: 4 }],
        },
    )?;
    let other_draft = draft(
        &source,
        &one,
        TableAutoFillOrder::RowMajor,
        0,
        TableAutoFillFormulaPolicy::Reject,
        vec![Some(id("formula-payload-1-0")?)],
        '3',
        '4',
    )?;
    assert!(matches!(
        TableAutoFillHwpxRequest::from_draft(
            other_draft,
            &one,
            &source,
            &flow('3'),
            TableAutoFillHwpxLimits::default(),
        ),
        Err(TableAutoFillHwpxError::UnsupportedFormulaDependency)
    ));

    let unrelated = TableAutoFillRegion {
        start: CellCoordinate { row: 0, column: 0 },
        end: CellCoordinate { row: 0, column: 0 },
    };
    let source = read(&section, &binding, unrelated)?;
    let unrelated_series = make_series(
        "unrelated",
        TableAutoFillDefinition::ExplicitCycle {
            items: vec![TableAutoFillValue::Text {
                value: "changed-header".to_owned(),
            }],
        },
    )?;
    let unrelated_draft = draft(
        &source,
        &unrelated_series,
        TableAutoFillOrder::RowMajor,
        0,
        TableAutoFillFormulaPolicy::Reject,
        vec![Some(id("formula-payload-0-0")?)],
        '3',
        '4',
    )?;
    let (request, plan) = admitted(&source, &unrelated_series, unrelated_draft, '3')?;
    let output = TableAutoFillHwpxLowerer::lower(
        HEADER,
        &section,
        &binding,
        &flow('3'),
        &unrelated_series,
        &request,
        &plan,
        TableAutoFillHwpxLimits::default(),
    )?;
    assert!(String::from_utf8(output.section)?.contains("fieldBegin"));
    assert_eq!(output.receipt.target_formula_count, 1);
    Ok(())
}

#[test]
fn request_rejects_source_series_payload_flow_and_json_tamper() -> TestResult {
    let section = regular_section();
    let binding = regular_binding("request")?;
    let source = read(&section, &binding, region())?;
    let series = explicit_series("request")?;
    let base = draft(
        &source,
        &series,
        TableAutoFillOrder::RowMajor,
        0,
        TableAutoFillFormulaPolicy::Reject,
        regular_target_ids("request")?,
        '5',
        '6',
    )?;
    for mutate in 0..8 {
        let mut value = base.clone();
        match mutate {
            0 => value.expected_header_sha256 = flow('z'),
            1 => value.expected_section_sha256 = flow('z'),
            2 => value.expected_source_state_sha256 = flow('z'),
            3 => value.expected_source_grid_sha256 = flow('z'),
            4 => value.expected_scalar_state_sha256 = flow('z'),
            5 => value.expected_pagination_policy_sha256 = flow('z'),
            6 => value.expected_series_sha256 = flow('z'),
            _ => value.expected_document_flow_sha256 = flow('z'),
        }
        assert!(
            TableAutoFillHwpxRequest::from_draft(
                value,
                &series,
                &source,
                &flow('5'),
                TableAutoFillHwpxLimits::default(),
            )
            .is_err()
        );
    }
    let mut wrong_id = base.clone();
    wrong_id.target_payload_block_ids[0] = Some(id("request-wrong-id")?);
    assert!(matches!(
        TableAutoFillHwpxRequest::from_draft(
            wrong_id,
            &series,
            &source,
            &flow('5'),
            TableAutoFillHwpxLimits::default(),
        ),
        Err(TableAutoFillHwpxError::PayloadIdentityMismatch)
    ));
    let json = serde_json::to_vec(&base)?;
    let request = TableAutoFillHwpxRequest::from_json(
        &json,
        &series,
        &source,
        &flow('5'),
        TableAutoFillHwpxLimits::default(),
    )?;
    assert_eq!(request.capability_id(), "table.auto_fill");
    let duplicate = String::from_utf8(json)?.replacen('{', r#"{"schema_version":"duplicate","#, 1);
    assert!(matches!(
        TableAutoFillHwpxRequest::from_json(
            duplicate.as_bytes(),
            &series,
            &source,
            &flow('5'),
            TableAutoFillHwpxLimits::default(),
        ),
        Err(TableAutoFillHwpxError::InvalidJson)
    ));
    Ok(())
}

#[test]
fn builder_and_lowerer_recheck_source_flow_series_and_plan_binding() -> TestResult {
    let section = regular_section();
    let binding = regular_binding("drift")?;
    let source = read(&section, &binding, region())?;
    let series = explicit_series("drift")?;
    let request_draft = draft(
        &source,
        &series,
        TableAutoFillOrder::RowMajor,
        0,
        TableAutoFillFormulaPolicy::Reject,
        regular_target_ids("drift")?,
        '7',
        '8',
    )?;
    let (request, plan) = admitted(&source, &series, request_draft, '7')?;
    assert!(
        TableAutoFillHwpxBuilder::build(
            &request,
            &series,
            &source,
            &flow('z'),
            TableAutoFillHwpxLimits::default(),
        )
        .is_err()
    );
    let other_series = make_series(
        "drift-other",
        TableAutoFillDefinition::ExplicitCycle {
            items: vec![TableAutoFillValue::Integer { value: 1 }],
        },
    )?;
    assert!(
        TableAutoFillHwpxBuilder::build(
            &request,
            &other_series,
            &source,
            &flow('7'),
            TableAutoFillHwpxLimits::default(),
        )
        .is_err()
    );
    let mut drifted_section = section.clone();
    let position = drifted_section
        .windows(b"old".len())
        .position(|window| window == b"old")
        .ok_or("missing test text")?;
    drifted_section[position] = b'X';
    assert!(
        TableAutoFillHwpxLowerer::lower(
            HEADER,
            &drifted_section,
            &binding,
            &flow('7'),
            &series,
            &request,
            &plan,
            TableAutoFillHwpxLimits::default(),
        )
        .is_err()
    );

    let no_change = make_series(
        "plan-other",
        TableAutoFillDefinition::ExplicitCycle {
            items: vec![TableAutoFillValue::Text {
                value: "old".to_owned(),
            }],
        },
    )?;
    let selected = TableAutoFillRegion {
        start: CellCoordinate { row: 1, column: 0 },
        end: CellCoordinate { row: 1, column: 0 },
    };
    let other_source = read(&section, &binding, selected)?;
    let other_draft = draft(
        &other_source,
        &no_change,
        TableAutoFillOrder::RowMajor,
        0,
        TableAutoFillFormulaPolicy::Reject,
        vec![Some(id("drift-payload-1-0")?)],
        '7',
        '7',
    )?;
    let (_, other_plan) = admitted(&other_source, &no_change, other_draft, '7')?;
    assert!(matches!(
        TableAutoFillHwpxLowerer::lower(
            HEADER,
            &section,
            &binding,
            &flow('7'),
            &series,
            &request,
            &other_plan,
            TableAutoFillHwpxLimits::default(),
        ),
        Err(TableAutoFillHwpxError::PlanBindingMismatch)
    ));
    Ok(())
}

#[test]
fn merged_multi_paragraph_multi_run_and_inline_style_fail_closed() -> TestResult {
    let merged_rows = vec![vec![cell(0, 0, 1, 2, &paragraph("merged", 0, 0))]];
    let merged = section_with_table(&table_xml(&merged_rows, 1, 2));
    let merged_binding = TableRulingHwpxBinding {
        table_id: id("merged-table")?,
        row_boundaries_hwpunit: vec![0, 600],
        column_boundaries_hwpunit: vec![0, 1_000, 2_000],
        cells: vec![TableRulingHwpxCellBinding {
            master_cell_id: id("merged-cell")?,
            payload_block_ids: vec![id("merged-payload")?],
        }],
    };
    let merged_region = TableAutoFillRegion {
        start: CellCoordinate { row: 0, column: 0 },
        end: CellCoordinate { row: 0, column: 0 },
    };
    assert!(matches!(
        read(&merged, &merged_binding, merged_region),
        Err(TableAutoFillHwpxError::UnsupportedMergedCells)
    ));

    let binding = regular_binding("rich")?;
    for replacement in [
        concat!(
            r#"<hp:p id="10" paraPrIDRef="1" styleIDRef="0"><hp:run charPrIDRef="2"><hp:t>one</hp:t></hp:run></hp:p>"#,
            r#"<hp:p id="11" paraPrIDRef="1" styleIDRef="0"><hp:run charPrIDRef="2"><hp:t>two</hp:t></hp:run></hp:p>"#,
        ),
        r#"<hp:p id="10" paraPrIDRef="1" styleIDRef="0"><hp:run charPrIDRef="2"><hp:t>one</hp:t></hp:run><hp:run charPrIDRef="3"><hp:t>two</hp:t></hp:run></hp:p>"#,
        r#"<hp:p id="10" paraPrIDRef="1" styleIDRef="0"><hp:run charPrIDRef="2"><hp:t charPrIDRef="9">styled</hp:t></hp:run></hp:p>"#,
    ] {
        let source = String::from_utf8(regular_section())?;
        let rich = source
            .replace(&paragraph("old", 1, 0), replacement)
            .into_bytes();
        assert!(read(&rich, &binding, region()).is_err());
    }
    Ok(())
}

#[test]
fn noop_is_byte_exact_for_target_typed_text_collision_and_debug_is_redacted() -> TestResult {
    let section = regular_section();
    let binding = regular_binding("noop")?;
    let selected = TableAutoFillRegion {
        start: CellCoordinate { row: 2, column: 0 },
        end: CellCoordinate { row: 2, column: 0 },
    };
    let source = read(&section, &binding, selected)?;
    let series = make_series(
        "noop",
        TableAutoFillDefinition::ExplicitCycle {
            items: vec![TableAutoFillValue::Text {
                value: "true".to_owned(),
            }],
        },
    )?;
    let request_draft = draft(
        &source,
        &series,
        TableAutoFillOrder::RowMajor,
        0,
        TableAutoFillFormulaPolicy::Reject,
        vec![Some(id("noop-payload-2-0")?)],
        '9',
        '9',
    )?;
    let (request, plan) = admitted(&source, &series, request_draft, '9')?;
    let output = TableAutoFillHwpxLowerer::lower(
        HEADER,
        &section,
        &binding,
        &flow('9'),
        &series,
        &request,
        &plan,
        TableAutoFillHwpxLimits::default(),
    )?;
    assert_eq!(output.section, section);
    assert_eq!(output.header, HEADER);
    assert_eq!(output.receipt.semantic_change_count, 0);
    let debug = format!("{source:?} {series:?} {request:?} {plan:?} {output:?}");
    let private_flow = flow('9');
    for private in ["noop-table", "noop-series", private_flow.as_str()] {
        assert!(!debug.contains(private));
    }
    let codes = [
        TableAutoFillHwpxError::UnsupportedVersion.code(),
        TableAutoFillHwpxError::InputLimit.code(),
        TableAutoFillHwpxError::InvalidJson.code(),
        TableAutoFillHwpxError::SourceBindingMismatch.code(),
        TableAutoFillHwpxError::FlowBindingMismatch.code(),
        TableAutoFillHwpxError::UnsupportedMergedCells.code(),
        TableAutoFillHwpxError::UnsupportedRichContent.code(),
        TableAutoFillHwpxError::UnsupportedFormulaCache.code(),
        TableAutoFillHwpxError::UnsupportedFormulaDependency.code(),
        TableAutoFillHwpxError::PayloadIdentityMismatch.code(),
        TableAutoFillHwpxError::PlanBindingMismatch.code(),
        TableAutoFillHwpxError::ReadbackMismatch.code(),
        TableAutoFillHwpxError::Allocation.code(),
        TableAutoFillHwpxError::Serialization.code(),
        TableAutoFillHwpxError::OutputLimit.code(),
    ];
    assert_eq!(codes.len(), 15);
    assert!(
        codes
            .iter()
            .all(|code| code.starts_with("table_auto_fill_hwpx_"))
    );
    Ok(())
}

fn package(section: &[u8]) -> TestResult<Vec<u8>> {
    let mut cursor = Cursor::new(Vec::new());
    {
        let mut writer = ZipWriter::new(&mut cursor);
        let stored = SimpleFileOptions::default()
            .compression_method(CompressionMethod::Stored)
            .last_modified_time(DateTime::default());
        let deflated = SimpleFileOptions::default()
            .compression_method(CompressionMethod::Deflated)
            .last_modified_time(DateTime::default());
        writer.start_file("mimetype", stored)?;
        writer.write_all(b"application/hwp+zip")?;
        writer.start_file("version.xml", stored)?;
        writer.write_all(b"<version/>")?;
        writer.start_file("META-INF/container.xml", deflated)?;
        writer.write_all(CONTAINER.as_bytes())?;
        writer.start_file("Contents/content.hpf", deflated)?;
        writer.write_all(OPF.as_bytes())?;
        writer.start_file("Contents/header.xml", deflated)?;
        writer.write_all(HEADER)?;
        writer.start_file("Contents/section0.xml", deflated)?;
        writer.write_all(section)?;
        writer.start_file("Contents/opaque.bin", stored)?;
        writer.write_all(b"opaque-auto-fill-evidence")?;
        writer.finish()?;
    }
    Ok(cursor.into_inner())
}

fn repack(source: &[u8], header: &[u8], section: &[u8]) -> TestResult<Vec<u8>> {
    let mut input = ZipArchive::new(Cursor::new(source))?;
    let mut cursor = Cursor::new(Vec::new());
    {
        let mut writer = ZipWriter::new(&mut cursor);
        for index in 0..input.len() {
            let mut entry = input.by_index(index)?;
            let mut bytes = Vec::new();
            std::io::copy(&mut entry, &mut bytes)?;
            let replacement = match entry.name() {
                "Contents/header.xml" => header,
                "Contents/section0.xml" => section,
                _ => &bytes,
            };
            let method = if entry.name() == "mimetype" || entry.name() == "Contents/opaque.bin" {
                CompressionMethod::Stored
            } else {
                CompressionMethod::Deflated
            };
            writer.start_file(
                entry.name(),
                SimpleFileOptions::default()
                    .compression_method(method)
                    .last_modified_time(DateTime::default()),
            )?;
            writer.write_all(replacement)?;
        }
        writer.finish()?;
    }
    Ok(cursor.into_inner())
}

fn read_package_entry(
    reader: &mut BoundedZipReader<Cursor<Vec<u8>>>,
    path: &str,
) -> TestResult<Vec<u8>> {
    let index = reader
        .entries()
        .iter()
        .find(|entry| entry.path.as_str() == path)
        .map(|entry| entry.index)
        .ok_or("package entry missing")?;
    Ok(reader.read_entry(index)?)
}

#[test]
fn closed_package_reopens_and_preserves_every_non_target_part() -> TestResult {
    let section = regular_section();
    let binding = regular_binding("package")?;
    let source = read(&section, &binding, region())?;
    let series = explicit_series("package")?;
    let request_draft = draft(
        &source,
        &series,
        TableAutoFillOrder::RowMajor,
        0,
        TableAutoFillFormulaPolicy::Reject,
        regular_target_ids("package")?,
        '0',
        'a',
    )?;
    let (request, plan) = admitted(&source, &series, request_draft, '0')?;
    let output = TableAutoFillHwpxLowerer::lower(
        HEADER,
        &section,
        &binding,
        &flow('0'),
        &series,
        &request,
        &plan,
        TableAutoFillHwpxLimits::default(),
    )?;
    let source_package = package(&section)?;
    let target_package = repack(&source_package, &output.header, &output.section)?;
    let limits = PackageLimits::default();
    let mut source_reader = BoundedZipReader::open(Cursor::new(source_package), limits)?;
    let mut target_reader = BoundedZipReader::open(Cursor::new(target_package), limits)?;
    let source_graph = PackageGraph::build(&mut source_reader, PackageGraphLimits::default())?;
    let target_graph = PackageGraph::build(&mut target_reader, PackageGraphLimits::default())?;
    assert_eq!(source_graph.spine, target_graph.spine);
    assert_eq!(
        source_graph.relationships.len(),
        target_graph.relationships.len()
    );
    assert_eq!(
        read_package_entry(&mut source_reader, "Contents/opaque.bin")?,
        read_package_entry(&mut target_reader, "Contents/opaque.bin")?
    );
    assert_eq!(
        target_reader
            .entries()
            .iter()
            .find(|entry| entry.path.as_str() == "mimetype")
            .map(|entry| entry.compression),
        Some(Compression::Stored)
    );
    assert_eq!(
        Sha256::digest(read_package_entry(
            &mut target_reader,
            "Contents/header.xml"
        )?),
        Sha256::digest(HEADER)
    );
    let reopened_section = read_package_entry(&mut target_reader, "Contents/section0.xml")?;
    let reopened = read(&reopened_section, &output.binding, region())?;
    assert_eq!(
        reopened.scalar_state_sha256,
        output.receipt.target_scalar_state_sha256
    );
    Ok(())
}
