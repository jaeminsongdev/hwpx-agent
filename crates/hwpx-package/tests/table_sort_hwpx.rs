use std::collections::BTreeMap;
use std::io::{Cursor, Write};

use domain_ir::{
    CellCoordinate, LogicalId, TableBlankOrder, TableFormulaMovePolicy, TableSortAxis,
    TableSortDirection, TableSortKey, TableSortLimitConfig, TableSortLimits, TableSortRegion,
    TableTextCollation,
};
use hwpx_package::{
    BoundedZipReader, Compression, PackageGraph, PackageGraphLimits, PackageLimits,
    TABLE_SORT_HWPX_SCHEMA_VERSION, TableRulingHwpxBinding, TableRulingHwpxCellBinding,
    TableSortHwpxBuilder, TableSortHwpxError, TableSortHwpxLimits, TableSortHwpxLowerer,
    TableSortHwpxPlan, TableSortHwpxReadback, TableSortHwpxReader, TableSortHwpxRequest,
    TableSortHwpxRequestDraft,
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
    let bytes = value.as_ref();
    let mut output = String::with_capacity(bytes.len().saturating_mul(2));
    for byte in bytes {
        output.push(char::from(DIGITS[usize::from(byte >> 4)]));
        output.push(char::from(DIGITS[usize::from(byte & 0x0f)]));
    }
    output
}

fn paragraph(value: &str) -> String {
    if value.is_empty() {
        return r#"<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t/></hp:run></hp:p>"#.to_owned();
    }
    format!(
        r#"<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t>{value}</hp:t></hp:run></hp:p>"#
    )
}

fn formula_paragraph() -> &'static str {
    concat!(
        r#"<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:ctrl>"#,
        r#"<hp:fieldBegin id="101" type="FORMULA" name="" editable="0" dirty="0" zorder="-1" fieldid="202">"#,
        r#"<hp:parameters cnt="5" name=""><hp:integerParam name="Prop">8</hp:integerParam>"#,
        r#"<hp:stringParam name="Command">=SUM(LEFT)??%g,;;7</hp:stringParam>"#,
        r#"<hp:stringParam name="Formula">=SUM(LEFT)</hp:stringParam>"#,
        r#"<hp:stringParam name="ResultFormat">%g,</hp:stringParam>"#,
        r#"<hp:stringParam name="LastResult">7</hp:stringParam></hp:parameters>"#,
        r#"</hp:fieldBegin></hp:ctrl><hp:t>7</hp:t><hp:ctrl>"#,
        r#"<hp:fieldEnd beginIDRef="101" fieldid="202"/></hp:ctrl><hp:t/></hp:run></hp:p>"#,
    )
}

fn cell(row: u32, column: u32, row_span: u32, column_span: u32, payload: &str) -> String {
    let width = if column == 0 { 800 } else { 1200 };
    let height = 500 + row * 100;
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
        header = u8::from(row == 0),
        column = column,
        row = row,
        column_span = column_span,
        row_span = row_span,
        width = width * column_span,
        height = height,
        left = row * 10 + column,
        right = row + column,
        top = row * 2,
        bottom = column * 3,
        vertical = if (row + column).is_multiple_of(2) {
            "CENTER"
        } else {
            "BOTTOM"
        },
        payload = payload,
    )
}

fn caption() -> &'static str {
    concat!(
        r#"<hp:caption side="TOP" fullSz="0" width="42520" gap="850" lastWidth="42520">"#,
        r#"<hp:subList><hp:p><hp:run><hp:t>SORT CAPTION</hp:t></hp:run></hp:p></hp:subList></hp:caption>"#,
    )
}

fn table_xml(rows: &[Vec<String>], row_count: usize, column_count: usize) -> String {
    let mut body = String::new();
    for row in rows {
        body.push_str("<hp:tr>");
        body.push_str(&row.concat());
        body.push_str("</hp:tr>");
    }
    format!(
        concat!(
            r#"<hp:tbl id="700" zOrder="0" numberingType="TABLE" textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" pageBreak="CELL" repeatHeader="1" rowCnt="{row_count}" colCnt="{column_count}" cellSpacing="0" borderFillIDRef="1" noAdjust="0">"#,
            r#"<hp:sz width="2000" widthRelTo="ABSOLUTE" height="2600" heightRelTo="ABSOLUTE" protect="0"/>"#,
            r#"<hp:pos treatAsChar="0" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP" horzAlign="LEFT" vertOffset="2000" horzOffset="1000"/>"#,
            r#"<hp:outMargin left="0" right="0" top="0" bottom="0"/>"#,
            "{caption}",
            r#"<hp:inMargin left="0" right="0" top="0" bottom="0"/>"#,
            "{body}</hp:tbl>"
        ),
        row_count = row_count,
        column_count = column_count,
        caption = caption(),
        body = body,
    )
}

fn section_with_table(table: &str) -> Vec<u8> {
    format!(
        r#"<hs:sec xmlns:hs="{SECTION_NS}" xmlns:hp="{PARAGRAPH_NS}">{before}{table}{after}</hs:sec>"#,
        before = paragraph("BEFORE"),
        table = table,
        after = paragraph("AFTER"),
    )
    .into_bytes()
}

fn values() -> [[&'static str; 2]; 4] {
    [
        ["header", "label"],
        ["20", "Beta"],
        ["3", "alpha"],
        ["", "empty"],
    ]
}

fn regular_section() -> Vec<u8> {
    let rows = values()
        .iter()
        .zip(0_u32..)
        .map(|(values, row)| {
            values
                .iter()
                .zip(0_u32..)
                .map(|(value, column)| cell(row, column, 1, 1, &paragraph(value)))
                .collect::<Vec<_>>()
        })
        .collect::<Vec<_>>();
    section_with_table(&table_xml(&rows, 4, 2))
}

fn regular_binding(prefix: &str) -> TestResult<TableRulingHwpxBinding> {
    let values = values();
    let mut cells = Vec::new();
    for (row, row_values) in values.iter().enumerate() {
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
        row_boundaries_hwpunit: vec![0, 500, 1100, 1800, 2600],
        column_boundaries_hwpunit: vec![0, 800, 2000],
        cells,
    })
}

fn read(
    section: &[u8],
    binding: &TableRulingHwpxBinding,
) -> Result<TableSortHwpxReadback, TableSortHwpxError> {
    TableSortHwpxReader::read_context(HEADER, section, 0, binding, TableSortHwpxLimits::default())
}

#[test]
fn hancom_linesegarray_is_ignored_by_plain_text_reader() -> TestResult {
    let source = regular_section();
    let source_text = String::from_utf8(source)?;
    let cached = source_text.replace(
        "</hp:p>",
        r#"<hp:linesegarray><hp:lineseg textpos="0" vertpos="0"/></hp:linesegarray></hp:p>"#,
    );
    let binding = regular_binding("lineseg")?;
    let plain = read(source_text.as_bytes(), &binding)?;
    let with_cache = read(cached.as_bytes(), &binding)?;
    assert_eq!(plain.text_grid, with_cache.text_grid);
    Ok(())
}

fn key(
    offset: u32,
    direction: TableSortDirection,
    blank_order: TableBlankOrder,
    text_collation: TableTextCollation,
) -> TableSortKey {
    TableSortKey {
        offset,
        direction,
        blank_order,
        text_collation,
    }
}

fn draft(
    source: &TableSortHwpxReadback,
    region: TableSortRegion,
    axis: TableSortAxis,
    keys: Vec<TableSortKey>,
    formula_move_policy: TableFormulaMovePolicy,
    before_flow: char,
    after_flow: char,
) -> TestResult<TableSortHwpxRequestDraft> {
    let limits = TableSortHwpxLimits::default();
    Ok(TableSortHwpxRequestDraft {
        schema_version: TABLE_SORT_HWPX_SCHEMA_VERSION.to_owned(),
        table_ordinal: source.table_ordinal,
        region,
        axis,
        keys,
        formula_move_policy,
        expected_header_sha256: hex(source.header_sha256),
        expected_section_sha256: hex(source.section_sha256),
        expected_table_content_sha256: hex(source.ruling.table_content_sha256),
        expected_source_state_sha256: hex(source
            .ruling
            .state
            .canonical_sha256(limits.native.ruling)?),
        expected_source_grid_sha256: hex(source.ruling.grid.canonical_sha256()?),
        expected_text_grid_sha256: hex(source.text_grid_sha256),
        expected_pagination_policy_sha256: hex(source.pagination_policy_sha256),
        expected_source_table_count: source.source_table_count,
        expected_document_flow_sha256: flow(before_flow),
        target_document_flow_sha256: flow(after_flow),
    })
}

fn admitted(
    source: &TableSortHwpxReadback,
    draft: TableSortHwpxRequestDraft,
    current_flow: char,
) -> TestResult<(TableSortHwpxRequest, TableSortHwpxPlan)> {
    let request = TableSortHwpxRequest::from_draft(
        draft,
        source,
        &flow(current_flow),
        TableSortHwpxLimits::default(),
    )?;
    let plan = TableSortHwpxBuilder::build(
        &request,
        source,
        &flow(current_flow),
        TableSortHwpxLimits::default(),
    )?;
    Ok((request, plan))
}

fn row_region() -> TableSortRegion {
    TableSortRegion {
        start: CellCoordinate { row: 1, column: 0 },
        end: CellCoordinate { row: 3, column: 1 },
    }
}

#[test]
fn row_sort_moves_complete_cells_and_preserves_properties_pagination_and_caption() -> TestResult {
    let section = regular_section();
    let binding = regular_binding("row")?;
    let source = read(&section, &binding)?;
    let request_draft = draft(
        &source,
        row_region(),
        TableSortAxis::Rows,
        vec![key(
            0,
            TableSortDirection::Ascending,
            TableBlankOrder::Last,
            TableTextCollation::Binary,
        )],
        TableFormulaMovePolicy::Reject,
        'a',
        'b',
    )?;
    let (request, plan) = admitted(&source, request_draft.clone(), 'a')?;
    let second_row_source = id("row-cell-2-0")?;
    let target_span = plan
        .target_grid()
        .master_cell_at(CellCoordinate { row: 1, column: 0 })?;
    assert_eq!(target_span.master_cell_id, second_row_source);
    let source_cell = source
        .ruling
        .state
        .cell(&second_row_source)
        .ok_or_else(|| std::io::Error::other("missing source cell"))?;
    let target_cell = plan
        .target_state()
        .cell(&second_row_source)
        .ok_or_else(|| std::io::Error::other("missing target cell"))?;
    assert_eq!(
        target_cell.coordinate(),
        CellCoordinate { row: 1, column: 0 }
    );
    assert_eq!(target_cell.payload(), source_cell.payload());
    assert_eq!(target_cell.properties(), source_cell.properties());
    assert_eq!(plan.sort_plan().relocations().len(), 6);
    assert!(plan.sort_plan().receipt().changed());

    let lowered = TableSortHwpxLowerer::lower(
        HEADER,
        &section,
        &binding,
        &flow('a'),
        &request,
        &plan,
        TableSortHwpxLimits::default(),
    )?;
    let reopened = read(&lowered.section, &lowered.binding)?;
    assert_eq!(reopened.text_grid.cell(0, 0), Some("header"));
    assert_eq!(reopened.text_grid.cell(1, 0), Some("3"));
    assert_eq!(reopened.text_grid.cell(2, 0), Some("20"));
    assert_eq!(reopened.text_grid.cell(3, 0), Some(""));
    assert_eq!(reopened.text_grid.cell(1, 1), Some("alpha"));
    assert_eq!(reopened.text_grid.cell(2, 1), Some("Beta"));
    assert_eq!(reopened.pagination.page_split, source.pagination.page_split);
    assert_eq!(
        reopened.pagination.repeat_header_rows,
        source.pagination.repeat_header_rows
    );
    assert_eq!(reopened.pagination.caption, source.pagination.caption);
    assert_eq!(lowered.receipt.source_table_count, 1);
    assert_eq!(lowered.receipt.target_table_count, 1);
    assert_eq!(lowered.receipt.formula_count, 0);
    assert_eq!(lowered.receipt.repeat_header_rows, 1);
    assert!(lowered.receipt.caption_preserved);
    assert!(String::from_utf8(lowered.section)?.contains("AFTER"));

    let same_request = TableSortHwpxRequest::from_draft(
        request_draft,
        &source,
        &flow('a'),
        TableSortHwpxLimits::default(),
    )?;
    let same_plan = TableSortHwpxBuilder::build(
        &same_request,
        &source,
        &flow('a'),
        TableSortHwpxLimits::default(),
    )?;
    assert_eq!(
        request.canonical_json(TableSortHwpxLimits::default())?,
        same_request.canonical_json(TableSortHwpxLimits::default())?
    );
    assert_eq!(
        plan.canonical_json(TableSortHwpxLimits::default())?,
        same_plan.canonical_json(TableSortHwpxLimits::default())?
    );
    Ok(())
}

#[test]
fn column_sort_moves_complete_columns_inside_only_the_selected_region() -> TestResult {
    let section = regular_section();
    let binding = regular_binding("column")?;
    let source = read(&section, &binding)?;
    let (request, plan) = admitted(
        &source,
        draft(
            &source,
            row_region(),
            TableSortAxis::Columns,
            vec![key(
                0,
                TableSortDirection::Descending,
                TableBlankOrder::Last,
                TableTextCollation::AsciiCaseInsensitive,
            )],
            TableFormulaMovePolicy::Reject,
            'a',
            'b',
        )?,
        'a',
    )?;
    assert_eq!(
        plan.target_grid()
            .master_cell_at(CellCoordinate { row: 1, column: 0 })?
            .master_cell_id,
        id("column-cell-1-1")?
    );
    assert_eq!(
        plan.target_grid()
            .master_cell_at(CellCoordinate { row: 0, column: 0 })?
            .master_cell_id,
        id("column-cell-0-0")?
    );
    let lowered = TableSortHwpxLowerer::lower(
        HEADER,
        &section,
        &binding,
        &flow('a'),
        &request,
        &plan,
        TableSortHwpxLimits::default(),
    )?;
    let reopened = read(&lowered.section, &lowered.binding)?;
    assert_eq!(reopened.text_grid.cell(0, 0), Some("header"));
    assert_eq!(reopened.text_grid.cell(1, 0), Some("Beta"));
    assert_eq!(reopened.text_grid.cell(1, 1), Some("20"));
    assert_eq!(reopened.text_grid.cell(3, 0), Some("empty"));
    assert_eq!(reopened.text_grid.cell(3, 1), Some(""));
    Ok(())
}

#[test]
fn request_rejects_every_source_digest_shape_flow_and_json_tamper() -> TestResult {
    let section = regular_section();
    let binding = regular_binding("tamper")?;
    let source = read(&section, &binding)?;
    let valid = draft(
        &source,
        row_region(),
        TableSortAxis::Rows,
        vec![key(
            0,
            TableSortDirection::Ascending,
            TableBlankOrder::Last,
            TableTextCollation::Binary,
        )],
        TableFormulaMovePolicy::Reject,
        'a',
        'b',
    )?;
    for field in [
        "header",
        "section",
        "content",
        "state",
        "grid",
        "text",
        "pagination",
        "flow",
    ] {
        let mut invalid = valid.clone();
        match field {
            "header" => invalid.expected_header_sha256 = flow('1'),
            "section" => invalid.expected_section_sha256 = flow('2'),
            "content" => invalid.expected_table_content_sha256 = flow('3'),
            "state" => invalid.expected_source_state_sha256 = flow('4'),
            "grid" => invalid.expected_source_grid_sha256 = flow('5'),
            "text" => invalid.expected_text_grid_sha256 = flow('6'),
            "pagination" => invalid.expected_pagination_policy_sha256 = flow('7'),
            "flow" => invalid.expected_document_flow_sha256 = flow('8'),
            _ => unreachable!(),
        }
        assert!(matches!(
            TableSortHwpxRequest::from_draft(
                invalid,
                &source,
                &flow('a'),
                TableSortHwpxLimits::default(),
            ),
            Err(TableSortHwpxError::SourceBindingMismatch)
        ));
    }
    let mut same_flow = valid.clone();
    same_flow.target_document_flow_sha256 = flow('a');
    assert!(matches!(
        TableSortHwpxRequest::from_draft(
            same_flow,
            &source,
            &flow('a'),
            TableSortHwpxLimits::default(),
        ),
        Err(TableSortHwpxError::FlowBindingMismatch)
    ));
    let mut wrong_count = valid.clone();
    wrong_count.expected_source_table_count += 1;
    assert!(matches!(
        TableSortHwpxRequest::from_draft(
            wrong_count,
            &source,
            &flow('a'),
            TableSortHwpxLimits::default(),
        ),
        Err(TableSortHwpxError::SourceBindingMismatch)
    ));

    let json = serde_json::to_vec(&valid)?;
    let parsed = TableSortHwpxRequest::from_json(
        &json,
        &source,
        &flow('a'),
        TableSortHwpxLimits::default(),
    )?;
    assert_eq!(parsed.capability_id(), "table.sort_cells");
    let unknown = String::from_utf8(json.clone())?.replacen('{', r#"{"unknown":true,"#, 1);
    assert!(matches!(
        TableSortHwpxRequest::from_json(
            unknown.as_bytes(),
            &source,
            &flow('a'),
            TableSortHwpxLimits::default(),
        ),
        Err(TableSortHwpxError::InvalidJson)
    ));
    let duplicate = String::from_utf8(json)?.replacen('{', r#"{"schema_version":"duplicate","#, 1);
    assert!(matches!(
        TableSortHwpxRequest::from_json(
            duplicate.as_bytes(),
            &source,
            &flow('a'),
            TableSortHwpxLimits::default(),
        ),
        Err(TableSortHwpxError::InvalidJson)
    ));
    Ok(())
}

#[test]
fn builder_and_lowerer_recheck_source_flow_and_plan_binding() -> TestResult {
    let section = regular_section();
    let binding = regular_binding("drift")?;
    let source = read(&section, &binding)?;
    let (request, plan) = admitted(
        &source,
        draft(
            &source,
            row_region(),
            TableSortAxis::Rows,
            vec![key(
                0,
                TableSortDirection::Ascending,
                TableBlankOrder::Last,
                TableTextCollation::Binary,
            )],
            TableFormulaMovePolicy::Reject,
            'a',
            'b',
        )?,
        'a',
    )?;
    assert!(matches!(
        TableSortHwpxBuilder::build(
            &request,
            &source,
            &flow('c'),
            TableSortHwpxLimits::default(),
        ),
        Err(TableSortHwpxError::SourceBindingMismatch)
    ));
    let (_, other_plan) = admitted(
        &source,
        draft(
            &source,
            row_region(),
            TableSortAxis::Rows,
            vec![key(
                0,
                TableSortDirection::Descending,
                TableBlankOrder::Last,
                TableTextCollation::Binary,
            )],
            TableFormulaMovePolicy::Reject,
            'a',
            'a',
        )?,
        'a',
    )?;
    assert!(matches!(
        TableSortHwpxLowerer::lower(
            HEADER,
            &section,
            &binding,
            &flow('a'),
            &request,
            &other_plan,
            TableSortHwpxLimits::default(),
        ),
        Err(TableSortHwpxError::PlanBindingMismatch)
    ));
    let mut drifted = section.clone();
    drifted.extend_from_slice(b"\n");
    assert!(
        TableSortHwpxLowerer::lower(
            HEADER,
            &drifted,
            &binding,
            &flow('a'),
            &request,
            &plan,
            TableSortHwpxLimits::default(),
        )
        .is_err()
    );
    Ok(())
}

fn assert_merged_table_is_rejected() -> TestResult {
    let source_values = values();
    let mut merged_rows = Vec::new();
    for (row, row_values) in (0_u32..3).zip(source_values.iter()) {
        merged_rows.push(vec![
            cell(row, 0, 1, 1, &paragraph(row_values[0])),
            cell(row, 1, 1, 1, &paragraph(row_values[1])),
        ]);
    }
    let merged =
        cell(3, 0, 1, 2, &paragraph("merged")).replacen("width=\"1600\"", "width=\"2000\"", 1);
    merged_rows.push(vec![merged]);
    let merged_section = section_with_table(&table_xml(&merged_rows, 4, 2));
    let merged_binding = TableRulingHwpxBinding {
        table_id: id("merged-table")?,
        row_boundaries_hwpunit: vec![0, 500, 1100, 1800, 2600],
        column_boundaries_hwpunit: vec![0, 800, 2000],
        cells: (0..7)
            .map(|index| {
                Ok(TableRulingHwpxCellBinding {
                    master_cell_id: id(&format!("merged-cell-{index}"))?,
                    payload_block_ids: vec![id(&format!("merged-payload-{index}"))?],
                })
            })
            .collect::<TestResult<Vec<_>>>()?,
    };
    assert!(matches!(
        read(&merged_section, &merged_binding),
        Err(TableSortHwpxError::UnsupportedMergedCells)
    ));
    Ok(())
}

#[test]
fn merged_formula_nonplain_regions_and_invalid_policies_fail_closed() -> TestResult {
    assert_merged_table_is_rejected()?;

    let mut formula_section = String::from_utf8(regular_section())?;
    formula_section = formula_section.replacen(&paragraph("alpha"), formula_paragraph(), 1);
    assert!(read(formula_section.as_bytes(), &regular_binding("formula")?).is_err());

    let mut multiparagraph = String::from_utf8(regular_section())?;
    multiparagraph = multiparagraph.replacen(
        &paragraph("alpha"),
        &format!("{}{}", paragraph("alpha"), paragraph("second")),
        1,
    );
    let mut multi_binding = regular_binding("multi")?;
    multi_binding.cells[5]
        .payload_block_ids
        .push(id("multi-payload-extra")?);
    assert!(read(multiparagraph.as_bytes(), &multi_binding).is_err());

    let mut opaque = String::from_utf8(regular_section())?;
    opaque = opaque.replacen(
        &paragraph("alpha"),
        r#"<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:tab/></hp:run></hp:p>"#,
        1,
    );
    assert!(read(opaque.as_bytes(), &regular_binding("opaque")?).is_err());

    let section = regular_section();
    let source = read(&section, &regular_binding("policy")?)?;
    let mut invalid_policy = draft(
        &source,
        row_region(),
        TableSortAxis::Rows,
        vec![key(
            0,
            TableSortDirection::Ascending,
            TableBlankOrder::Last,
            TableTextCollation::Binary,
        )],
        TableFormulaMovePolicy::MoveVerbatim,
        'a',
        'b',
    )?;
    assert!(matches!(
        TableSortHwpxRequest::from_draft(
            invalid_policy.clone(),
            &source,
            &flow('a'),
            TableSortHwpxLimits::default(),
        ),
        Err(TableSortHwpxError::UnsupportedFormulaPolicy)
    ));
    invalid_policy.formula_move_policy = TableFormulaMovePolicy::Reject;
    invalid_policy.region = TableSortRegion {
        start: CellCoordinate { row: 3, column: 0 },
        end: CellCoordinate { row: 1, column: 1 },
    };
    assert!(matches!(
        TableSortHwpxRequest::from_draft(
            invalid_policy,
            &source,
            &flow('a'),
            TableSortHwpxLimits::default(),
        ),
        Err(TableSortHwpxError::Sort(_))
    ));
    let mut out_of_bounds = draft(
        &source,
        row_region(),
        TableSortAxis::Rows,
        vec![key(
            0,
            TableSortDirection::Ascending,
            TableBlankOrder::Last,
            TableTextCollation::Binary,
        )],
        TableFormulaMovePolicy::Reject,
        'a',
        'b',
    )?;
    out_of_bounds.region.end.row = 4;
    assert!(matches!(
        TableSortHwpxRequest::from_draft(
            out_of_bounds,
            &source,
            &flow('a'),
            TableSortHwpxLimits::default(),
        ),
        Err(TableSortHwpxError::Sort(_))
    ));
    Ok(())
}

#[test]
fn noop_is_byte_exact_and_limits_and_debug_are_fail_closed() -> TestResult {
    let section = regular_section();
    let binding = regular_binding("noop-secret")?;
    let source = read(&section, &binding)?;
    let (request, plan) = admitted(
        &source,
        draft(
            &source,
            row_region(),
            TableSortAxis::Rows,
            vec![key(
                0,
                TableSortDirection::Descending,
                TableBlankOrder::Last,
                TableTextCollation::Binary,
            )],
            TableFormulaMovePolicy::Reject,
            'a',
            'a',
        )?,
        'a',
    )?;
    assert!(!plan.sort_plan().receipt().changed());
    let lowered = TableSortHwpxLowerer::lower(
        HEADER,
        &section,
        &binding,
        &flow('a'),
        &request,
        &plan,
        TableSortHwpxLimits::default(),
    )?;
    assert_eq!(lowered.header, HEADER);
    assert_eq!(lowered.section, section);
    assert!(!lowered.receipt.changed);
    assert_eq!(
        lowered.receipt.before_document_flow_sha256,
        lowered.receipt.after_document_flow_sha256
    );

    let debug = format!("{source:?} {request:?} {plan:?} {lowered:?}");
    for secret in [
        "noop-secret-table",
        "noop-secret-cell-1-0",
        "noop-secret-payload-1-0",
        "Beta",
        request.target_document_flow_sha256(),
    ] {
        assert!(!debug.contains(secret));
    }
    let limits = TableSortHwpxLimits {
        sort: TableSortLimits::new(TableSortLimitConfig {
            input_bytes: 128,
            selected_cells: 8,
            sort_keys: 2,
            text_bytes: 32,
            comparison_work: 64,
            serialized_bytes: 128,
        })?,
        ..TableSortHwpxLimits::default()
    };
    assert!(matches!(
        TableSortHwpxRequest::from_json(&[b' '; 129], &source, &flow('a'), limits),
        Err(TableSortHwpxError::InputLimit)
    ));
    assert_eq!(
        TableSortHwpxError::FlowBindingMismatch.code(),
        "table_sort_hwpx_flow_binding_mismatch"
    );
    assert_eq!(
        TableSortHwpxError::ReadbackMismatch.code(),
        "table_sort_hwpx_readback_mismatch"
    );
    Ok(())
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

fn package(section: &[u8], opaque: &[u8]) -> TestResult<Vec<u8>> {
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
            HEADER.to_vec(),
            CompressionMethod::Deflated,
        ),
        (
            "Contents/section0.xml".to_owned(),
            section.to_vec(),
            CompressionMethod::Deflated,
        ),
        (
            "Contents/opaque.bin".to_owned(),
            opaque.to_vec(),
            CompressionMethod::Stored,
        ),
    ])
    .map_err(Into::into)
}

fn expanded_parts(source: &[u8]) -> TestResult<BTreeMap<String, Vec<u8>>> {
    let mut archive = ZipArchive::new(Cursor::new(source))?;
    let mut output = BTreeMap::new();
    for index in 0..archive.len() {
        let mut entry = archive.by_index(index)?;
        let mut bytes = Vec::new();
        std::io::copy(&mut entry, &mut bytes)?;
        output.insert(entry.name().to_owned(), bytes);
    }
    Ok(output)
}

fn replace_target_parts(source: &[u8], header: &[u8], section: &[u8]) -> TestResult<Vec<u8>> {
    let mut reader = BoundedZipReader::open(Cursor::new(source), PackageLimits::default())?;
    let entries = reader.entries().to_vec();
    let mut parts = Vec::new();
    for entry in entries {
        let path = entry.path.as_str().to_owned();
        let replacement = match path.as_str() {
            "Contents/header.xml" => header.to_vec(),
            "Contents/section0.xml" => section.to_vec(),
            _ => reader.read_entry(entry.index)?,
        };
        let method = match entry.compression {
            Compression::Stored => CompressionMethod::Stored,
            Compression::Deflated => CompressionMethod::Deflated,
        };
        parts.push((path, replacement, method));
    }
    archive(parts).map_err(Into::into)
}

#[test]
fn closed_package_preserves_every_nontarget_part_and_relationship() -> TestResult {
    let section = regular_section();
    let opaque = b"opaque-preserved-sort-evidence";
    let original = package(&section, opaque)?;
    let binding = regular_binding("package")?;
    let source = read(&section, &binding)?;
    let (request, plan) = admitted(
        &source,
        draft(
            &source,
            row_region(),
            TableSortAxis::Rows,
            vec![key(
                0,
                TableSortDirection::Ascending,
                TableBlankOrder::Last,
                TableTextCollation::Binary,
            )],
            TableFormulaMovePolicy::Reject,
            'a',
            'b',
        )?,
        'a',
    )?;
    let lowered = TableSortHwpxLowerer::lower(
        HEADER,
        &section,
        &binding,
        &flow('a'),
        &request,
        &plan,
        TableSortHwpxLimits::default(),
    )?;
    let output = replace_target_parts(&original, &lowered.header, &lowered.section)?;
    let before = expanded_parts(&original)?;
    let after = expanded_parts(&output)?;
    for (path, bytes) in &before {
        if path == "Contents/section0.xml" {
            assert_ne!(after.get(path), Some(bytes));
        } else {
            assert_eq!(after.get(path), Some(bytes), "changed part: {path}");
        }
    }
    assert_eq!(after.get("Contents/opaque.bin"), Some(&opaque.to_vec()));
    let mut reader = BoundedZipReader::open(Cursor::new(&output), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    assert!(!graph.parts.is_empty());
    assert_eq!(Sha256::digest(&lowered.header), Sha256::digest(HEADER));
    Ok(())
}
