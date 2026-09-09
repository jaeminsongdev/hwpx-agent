use std::collections::BTreeMap;
use std::io::{Cursor, Write};

use domain_ir::{
    CellCoordinate, LogicalId, TABLE_TRANSPOSE_SCHEMA_VERSION, TableRulingAxis, TableRulingLimits,
    TableTransposeCellDraft, TableTransposeFormulaPolicy, TableTransposeLimitConfig,
    TableTransposeLimits, TableTransposeRequestDraft,
};
use hwpx_package::{
    BoundedZipReader, Compression, PackageGraph, PackageGraphLimits, PackageLimits,
    TABLE_TRANSPOSE_HWPX_SCHEMA_VERSION, TableRulingHwpxBinding, TableRulingHwpxCellBinding,
    TableTransposeHwpxBuilder, TableTransposeHwpxError, TableTransposeHwpxLimits,
    TableTransposeHwpxLowerer, TableTransposeHwpxReadback, TableTransposeHwpxReader,
    TableTransposeHwpxRequest, TableTransposeHwpxRequestDraft,
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use zip::write::SimpleFileOptions;
use zip::{CompressionMethod, DateTime, ZipWriter};

type TestResult<T = ()> = Result<T, Box<dyn std::error::Error>>;

const MINIMAL_HEADER: &[u8] = include_bytes!("../src/hancom_2020_minimal_header.xml");
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

fn component_digest<T: Serialize + ?Sized>(value: &T) -> TestResult<String> {
    Ok(hex(Sha256::digest(serde_json::to_vec(value)?)))
}

fn header() -> TestResult<Vec<u8>> {
    let source = String::from_utf8(MINIMAL_HEADER.to_vec())?;
    let solid = concat!(
        r#"<hh:borderFill id="3" threeD="0" shadow="0" centerLine="NONE" breakCellSeparateLine="0">"#,
        r#"<hh:slash type="NONE" Crooked="0" isCounter="0"/>"#,
        r#"<hh:backSlash type="NONE" Crooked="0" isCounter="0"/>"#,
        r##"<hh:leftBorder type="SOLID" width="0.1 mm" color="#000000"/>"##,
        r##"<hh:rightBorder type="SOLID" width="0.1 mm" color="#000000"/>"##,
        r##"<hh:topBorder type="SOLID" width="0.1 mm" color="#000000"/>"##,
        r##"<hh:bottomBorder type="SOLID" width="0.1 mm" color="#000000"/>"##,
        r##"<hh:diagonal type="SOLID" width="0.1 mm" color="#000000"/>"##,
        r#"</hh:borderFill>"#,
    );
    let slash = concat!(
        r#"<hh:borderFill id="4" threeD="0" shadow="0" centerLine="NONE" breakCellSeparateLine="0">"#,
        r#"<hh:slash type="CENTER" Crooked="0" isCounter="0"/>"#,
        r#"<hh:backSlash type="NONE" Crooked="0" isCounter="0"/>"#,
        r##"<hh:leftBorder type="SOLID" width="0.1 mm" color="#000000"/>"##,
        r##"<hh:rightBorder type="SOLID" width="0.1 mm" color="#000000"/>"##,
        r##"<hh:topBorder type="SOLID" width="0.1 mm" color="#000000"/>"##,
        r##"<hh:bottomBorder type="SOLID" width="0.1 mm" color="#000000"/>"##,
        r##"<hh:diagonal type="SOLID" width="0.1 mm" color="#000000"/>"##,
        r#"</hh:borderFill>"#,
    );
    let back_slash = concat!(
        r#"<hh:borderFill id="5" threeD="0" shadow="0" centerLine="NONE" breakCellSeparateLine="0">"#,
        r#"<hh:slash type="NONE" Crooked="0" isCounter="0"/>"#,
        r#"<hh:backSlash type="CENTER" Crooked="0" isCounter="0"/>"#,
        r##"<hh:leftBorder type="SOLID" width="0.1 mm" color="#000000"/>"##,
        r##"<hh:rightBorder type="SOLID" width="0.1 mm" color="#000000"/>"##,
        r##"<hh:topBorder type="SOLID" width="0.1 mm" color="#000000"/>"##,
        r##"<hh:bottomBorder type="SOLID" width="0.1 mm" color="#000000"/>"##,
        r##"<hh:diagonal type="DOT" width="0.1 mm" color="#000000"/>"##,
        r#"</hh:borderFill>"#,
    );
    Ok(source
        .replacen(
            "<hh:borderFills itemCnt=\"2\">",
            "<hh:borderFills itemCnt=\"5\">",
            1,
        )
        .replacen(
            "</hh:borderFills>",
            &format!("{solid}{slash}{back_slash}</hh:borderFills>"),
            1,
        )
        .into_bytes())
}

fn paragraph(value: &str) -> String {
    format!(
        r#"<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t>{value}</hp:t></hp:run></hp:p>"#
    )
}

fn empty_paragraph() -> &'static str {
    r#"<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t/></hp:run></hp:p>"#
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

#[allow(clippy::too_many_arguments)]
fn cell(
    row: u32,
    column: u32,
    row_span: u32,
    column_span: u32,
    width: u32,
    height: u32,
    border_fill: u32,
    header: bool,
    payload: &str,
) -> String {
    format!(
        concat!(
            r#"<hp:tc name="" header="{header}" hasMargin="0" protect="0" editable="0" dirty="0" borderFillIDRef="{border_fill}">"#,
            r#"<hp:cellAddr colAddr="{column}" rowAddr="{row}"/>"#,
            r#"<hp:cellSpan colSpan="{column_span}" rowSpan="{row_span}"/>"#,
            r#"<hp:cellSz width="{width}" height="{height}"/>"#,
            r#"<hp:cellMargin left="{left_margin}" right="0" top="0" bottom="0"/>"#,
            r#"<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="{vertical}" linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">"#,
            "{payload}</hp:subList></hp:tc>"
        ),
        header = u8::from(header),
        border_fill = border_fill,
        column = column,
        row = row,
        column_span = column_span,
        row_span = row_span,
        width = width,
        height = height,
        left_margin = row * 10 + column,
        vertical = if column == 2 { "BOTTOM" } else { "CENTER" },
        payload = payload,
    )
}

fn caption() -> &'static str {
    concat!(
        r#"<hp:caption side="TOP" fullSz="0" width="42520" gap="850" lastWidth="42520">"#,
        r#"<hp:subList><hp:p><hp:run><hp:t>TRANSPOSE CAPTION</hp:t></hp:run></hp:p></hp:subList></hp:caption>"#,
    )
}

fn table_xml(rows: &[Vec<String>], repeat_header: bool, width: u32, height: u32) -> String {
    let mut body = String::new();
    for row in rows {
        body.push_str("<hp:tr>");
        body.push_str(&row.concat());
        body.push_str("</hp:tr>");
    }
    format!(
        concat!(
            r#"<hp:tbl id="700" zOrder="0" numberingType="TABLE" textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" pageBreak="CELL" repeatHeader="{repeat_header}" rowCnt="{row_count}" colCnt="{column_count}" cellSpacing="0" borderFillIDRef="1" noAdjust="0">"#,
            r#"<hp:sz width="{width}" widthRelTo="ABSOLUTE" height="{height}" heightRelTo="ABSOLUTE" protect="0"/>"#,
            r#"<hp:pos treatAsChar="0" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP" horzAlign="LEFT" vertOffset="2000" horzOffset="1000"/>"#,
            r#"<hp:outMargin left="0" right="0" top="0" bottom="0"/>"#,
            "{caption}",
            r#"<hp:inMargin left="0" right="0" top="0" bottom="0"/>"#,
            "{body}</hp:tbl>"
        ),
        repeat_header = u8::from(repeat_header),
        row_count = rows.len(),
        column_count = if width == 4000 { 3 } else { 1 },
        width = width,
        height = height,
        caption = caption(),
        body = body,
    )
}

fn rectangular_section(formula: bool) -> Vec<u8> {
    let final_payload = if formula {
        formula_paragraph().to_owned()
    } else {
        paragraph("D")
    };
    let rows = vec![
        vec![
            cell(
                0,
                0,
                2,
                1,
                800,
                2000,
                4,
                false,
                &format!("{}{}", paragraph("A1"), paragraph("A2")),
            ),
            cell(0, 1, 1, 2, 3200, 600, 5, false, &paragraph("B")),
        ],
        vec![
            cell(1, 1, 1, 1, 1200, 1400, 3, false, empty_paragraph()),
            cell(1, 2, 1, 1, 2000, 1400, 3, false, &final_payload),
        ],
    ];
    format!(
        r#"<hs:sec xmlns:hs="{SECTION_NS}" xmlns:hp="{PARAGRAPH_NS}">{before}{table}{after}</hs:sec>"#,
        before = paragraph("BEFORE"),
        table = table_xml(&rows, false, 4000, 2000),
        after = paragraph("AFTER"),
    )
    .into_bytes()
}

fn repeated_header_section() -> Vec<u8> {
    let rows = vec![
        vec![
            cell(0, 0, 1, 1, 800, 600, 3, true, &paragraph("H1")),
            cell(0, 1, 1, 1, 1200, 600, 3, true, &paragraph("H2")),
            cell(0, 2, 1, 1, 2000, 600, 3, true, &paragraph("H3")),
        ],
        vec![
            cell(1, 0, 1, 1, 800, 1400, 3, false, &paragraph("A")),
            cell(1, 1, 1, 1, 1200, 1400, 3, false, &paragraph("B")),
            cell(1, 2, 1, 1, 2000, 1400, 3, false, &paragraph("C")),
        ],
    ];
    format!(
        r#"<hs:sec xmlns:hs="{SECTION_NS}" xmlns:hp="{PARAGRAPH_NS}">{}</hs:sec>"#,
        table_xml(&rows, true, 4000, 2000),
    )
    .into_bytes()
}

fn square_single_section() -> Vec<u8> {
    let rows = vec![vec![cell(
        0,
        0,
        1,
        1,
        2000,
        2000,
        4,
        false,
        &paragraph("ONLY"),
    )]];
    format!(
        r#"<hs:sec xmlns:hs="{SECTION_NS}" xmlns:hp="{PARAGRAPH_NS}">{}</hs:sec>"#,
        table_xml(&rows, false, 2000, 2000),
    )
    .into_bytes()
}

fn rectangular_binding() -> TestResult<TableRulingHwpxBinding> {
    Ok(TableRulingHwpxBinding {
        table_id: id("transpose-table")?,
        row_boundaries_hwpunit: vec![0, 600, 2000],
        column_boundaries_hwpunit: vec![0, 800, 2000, 4000],
        cells: vec![
            TableRulingHwpxCellBinding {
                master_cell_id: id("cell-a")?,
                payload_block_ids: vec![id("payload-a1")?, id("payload-a2")?],
            },
            TableRulingHwpxCellBinding {
                master_cell_id: id("cell-b")?,
                payload_block_ids: vec![id("payload-b")?],
            },
            TableRulingHwpxCellBinding {
                master_cell_id: id("cell-c")?,
                payload_block_ids: Vec::new(),
            },
            TableRulingHwpxCellBinding {
                master_cell_id: id("cell-d")?,
                payload_block_ids: vec![id("payload-d")?],
            },
        ],
    })
}

fn ordinary_binding(prefix: &str) -> TestResult<TableRulingHwpxBinding> {
    let mut cells = Vec::new();
    for row in 0..2 {
        for column in 0..3 {
            cells.push(TableRulingHwpxCellBinding {
                master_cell_id: id(&format!("{prefix}-cell-{row}-{column}"))?,
                payload_block_ids: vec![id(&format!("{prefix}-payload-{row}-{column}"))?],
            });
        }
    }
    Ok(TableRulingHwpxBinding {
        table_id: id(&format!("{prefix}-table"))?,
        row_boundaries_hwpunit: vec![0, 600, 2000],
        column_boundaries_hwpunit: vec![0, 800, 2000, 4000],
        cells,
    })
}

fn single_binding() -> TestResult<TableRulingHwpxBinding> {
    Ok(TableRulingHwpxBinding {
        table_id: id("single-table")?,
        row_boundaries_hwpunit: vec![0, 2000],
        column_boundaries_hwpunit: vec![0, 2000],
        cells: vec![TableRulingHwpxCellBinding {
            master_cell_id: id("single-cell")?,
            payload_block_ids: vec![id("single-payload")?],
        }],
    })
}

fn read(
    header: &[u8],
    section: &[u8],
    binding: &TableRulingHwpxBinding,
) -> Result<TableTransposeHwpxReadback, TableTransposeHwpxError> {
    TableTransposeHwpxReader::read_existing(
        header,
        section,
        0,
        binding,
        TableTransposeHwpxLimits::default(),
    )
}

fn draft(
    source: &TableTransposeHwpxReadback,
    before_flow: char,
    after_flow: char,
) -> TestResult<TableTransposeHwpxRequestDraft> {
    let cells = source
        .ruling
        .state
        .cells()
        .iter()
        .map(|cell| {
            Ok(TableTransposeCellDraft {
                master_cell_id: cell.master_cell_id().clone(),
                coordinate: cell.coordinate(),
                payload_sha256: component_digest(cell.payload())?,
                style_sha256: component_digest(cell.properties())?,
                formula: None,
            })
        })
        .collect::<TestResult<Vec<_>>>()?;
    Ok(TableTransposeHwpxRequestDraft {
        schema_version: TABLE_TRANSPOSE_HWPX_SCHEMA_VERSION.to_owned(),
        table_ordinal: source.table_ordinal,
        expected_header_sha256: hex(source.ruling.header_sha256),
        expected_section_sha256: hex(source.ruling.section_sha256),
        expected_source_state_sha256: hex(source
            .ruling
            .state
            .canonical_sha256(TableRulingLimits::default())?),
        expected_source_grid_sha256: hex(source.ruling.grid.canonical_sha256()?),
        expected_document_flow_sha256: flow(before_flow),
        target_document_flow_sha256: flow(after_flow),
        transpose: TableTransposeRequestDraft {
            schema_version: TABLE_TRANSPOSE_SCHEMA_VERSION.to_owned(),
            table_id: source.ruling.state.table_id().clone(),
            table_properties_sha256: source.ruling.state.table_properties_sha256().to_owned(),
            formula_policy: TableTransposeFormulaPolicy::Reject,
            cells,
        },
    })
}

fn admitted(
    source: &TableTransposeHwpxReadback,
    draft: TableTransposeHwpxRequestDraft,
    current_flow: char,
) -> TestResult<(
    TableTransposeHwpxRequest,
    hwpx_package::TableTransposeHwpxPlan,
)> {
    let request = TableTransposeHwpxRequest::from_draft(
        draft,
        source,
        &flow(current_flow),
        TableTransposeHwpxLimits::default(),
    )?;
    let plan = TableTransposeHwpxBuilder::build(
        &request,
        source,
        &flow(current_flow),
        TableTransposeHwpxLimits::default(),
    )?;
    Ok((request, plan))
}

fn assert_transposed_state(
    source: &TableTransposeHwpxReadback,
    target: &TableTransposeHwpxReadback,
) -> TestResult {
    assert_eq!(target.ruling.grid.rows(), 3);
    assert_eq!(target.ruling.grid.columns(), 2);
    assert_eq!(
        target.ruling.state.row_boundaries_hwpunit(),
        &[0, 800, 2000, 4000]
    );
    assert_eq!(
        target.ruling.state.column_boundaries_hwpunit(),
        &[0, 600, 2000]
    );
    assert_eq!(target.ruling.state.frame().width_hwpunit, 2000);
    assert_eq!(target.ruling.state.frame().height_hwpunit, 4000);
    assert_eq!(target.ruling.state.frame().left_hwpunit, 1000);
    assert_eq!(target.ruling.state.frame().top_hwpunit, 2000);
    assert_eq!(target.ruling.grid.master_cell_count(), 4);
    assert_eq!(target.ruling.payload_block_count, 4);

    for source_cell in source.ruling.state.cells() {
        let target_cell = target
            .ruling
            .state
            .cell(source_cell.master_cell_id())
            .ok_or("transposed cell missing")?;
        assert_eq!(target_cell.payload(), source_cell.payload());
        assert_eq!(target_cell.properties(), source_cell.properties());
        assert_eq!(
            target_cell.coordinate(),
            CellCoordinate {
                row: source_cell.coordinate().column,
                column: source_cell.coordinate().row,
            }
        );
    }
    for edge in source.ruling.state.edges() {
        let target_axis = match edge.axis {
            TableRulingAxis::Horizontal => TableRulingAxis::Vertical,
            TableRulingAxis::Vertical => TableRulingAxis::Horizontal,
        };
        let target_edge = target
            .ruling
            .state
            .edge(target_axis, edge.boundary, edge.offset)
            .ok_or("transposed edge missing")?;
        assert_eq!(target_edge.line_sha256, edge.line_sha256);
    }
    Ok(())
}

#[test]
fn rectangular_merged_nonuniform_table_transposes_twice_without_semantic_loss() -> TestResult {
    let header = header()?;
    let section = rectangular_section(false);
    let binding = rectangular_binding()?;
    let source = read(&header, &section, &binding)?;
    let immutable_source = source.clone();
    let request_json = serde_json::to_vec(&draft(&source, 'f', 'e')?)?;
    let request = TableTransposeHwpxRequest::from_json(
        &request_json,
        &source,
        &flow('f'),
        TableTransposeHwpxLimits::default(),
    )?;
    assert_eq!(request.capability_id(), "table.transpose");
    assert_eq!(
        request.canonical_json(TableTransposeHwpxLimits::default())?,
        request.canonical_json(TableTransposeHwpxLimits::default())?
    );
    let plan = TableTransposeHwpxBuilder::build(
        &request,
        &source,
        &flow('f'),
        TableTransposeHwpxLimits::default(),
    )?;
    let lowered = TableTransposeHwpxLowerer::lower_existing(
        &header,
        &section,
        &binding,
        &flow('f'),
        &request,
        &plan,
        TableTransposeHwpxLimits::default(),
    )?;
    let reopened = read(&lowered.header, &lowered.section, &lowered.binding)?;

    assert_eq!(source, immutable_source);
    assert_transposed_state(&source, &reopened)?;
    assert_eq!(reopened.pagination.caption, source.pagination.caption);
    assert_eq!(reopened.pagination.page_split, source.pagination.page_split);
    assert!(String::from_utf8(lowered.section.clone())?.contains("BEFORE"));
    assert!(String::from_utf8(lowered.section.clone())?.contains("AFTER"));
    assert_eq!(lowered.receipt.preserved_merged_cell_count, 2);
    assert_eq!(
        lowered.receipt.preserved_edge_count,
        source.ruling.state.edges().len()
    );
    assert!(lowered.receipt.page_split_preserved);
    assert!(lowered.receipt.caption_preserved);

    let second_draft = draft(&reopened, 'e', 'f')?;
    let (second_request, second_plan) = admitted(&reopened, second_draft, 'e')?;
    let restored_parts = TableTransposeHwpxLowerer::lower_existing(
        &lowered.header,
        &lowered.section,
        &lowered.binding,
        &flow('e'),
        &second_request,
        &second_plan,
        TableTransposeHwpxLimits::default(),
    )?;
    let restored = read(
        &restored_parts.header,
        &restored_parts.section,
        &restored_parts.binding,
    )?;
    assert_eq!(restored.ruling.grid, source.ruling.grid);
    assert_eq!(restored.ruling.state, source.ruling.state);
    assert_eq!(restored.pagination.page_split, source.pagination.page_split);
    assert_eq!(restored.pagination.caption, source.pagination.caption);
    Ok(())
}

#[test]
fn request_rejects_part_state_grid_flow_cell_and_json_tampering() -> TestResult {
    let header = header()?;
    let section = rectangular_section(false);
    let binding = rectangular_binding()?;
    let source = read(&header, &section, &binding)?;

    let valid = draft(&source, 'f', 'e')?;
    let request = TableTransposeHwpxRequest::from_draft(
        valid.clone(),
        &source,
        &flow('f'),
        TableTransposeHwpxLimits::default(),
    )?;
    assert_eq!(
        TableTransposeHwpxBuilder::build(
            &request,
            &source,
            &flow('d'),
            TableTransposeHwpxLimits::default(),
        )
        .err()
        .map(|error| error.code()),
        Some("table_transpose_hwpx_source_binding_mismatch")
    );

    for mutate in ["header", "section", "state", "grid", "flow", "cell"] {
        let mut tampered = valid.clone();
        match mutate {
            "header" => tampered.expected_header_sha256 = flow('1'),
            "section" => tampered.expected_section_sha256 = flow('2'),
            "state" => tampered.expected_source_state_sha256 = flow('3'),
            "grid" => tampered.expected_source_grid_sha256 = flow('4'),
            "flow" => tampered.expected_document_flow_sha256 = flow('5'),
            "cell" => tampered.transpose.cells[0].payload_sha256 = flow('6'),
            _ => unreachable!(),
        }
        assert!(matches!(
            TableTransposeHwpxRequest::from_draft(
                tampered,
                &source,
                &flow('f'),
                TableTransposeHwpxLimits::default(),
            ),
            Err(TableTransposeHwpxError::SourceBindingMismatch
                | TableTransposeHwpxError::Transpose(_))
        ));
    }

    let json = serde_json::to_string(&valid)?;
    let duplicate = json.replacen(
        '{',
        r#"{"schema_version":"hwpx-agent.table-transpose-hwpx/v1","#,
        1,
    );
    assert!(matches!(
        TableTransposeHwpxRequest::from_json(
            duplicate.as_bytes(),
            &source,
            &flow('f'),
            TableTransposeHwpxLimits::default(),
        ),
        Err(TableTransposeHwpxError::InvalidJson)
    ));
    let unknown = json.replacen('{', r#"{"unknown":true,"#, 1);
    assert!(matches!(
        TableTransposeHwpxRequest::from_json(
            unknown.as_bytes(),
            &source,
            &flow('f'),
            TableTransposeHwpxLimits::default(),
        ),
        Err(TableTransposeHwpxError::InvalidJson)
    ));
    Ok(())
}

#[test]
fn lowerer_rechecks_source_parts_and_plan_binding() -> TestResult {
    let header = header()?;
    let section = rectangular_section(false);
    let binding = rectangular_binding()?;
    let source = read(&header, &section, &binding)?;
    let (request, plan) = admitted(&source, draft(&source, 'f', 'e')?, 'f')?;

    let mut tampered_section = section.clone();
    let index = tampered_section
        .windows("BEFORE".len())
        .position(|window| window == b"BEFORE")
        .ok_or("sentinel missing")?;
    tampered_section[index] = b'X';
    assert!(matches!(
        TableTransposeHwpxLowerer::lower_existing(
            &header,
            &tampered_section,
            &binding,
            &flow('f'),
            &request,
            &plan,
            TableTransposeHwpxLimits::default(),
        ),
        Err(TableTransposeHwpxError::SourceBindingMismatch)
    ));
    assert!(matches!(
        TableTransposeHwpxLowerer::lower_existing(
            &header,
            &section,
            &binding,
            &flow('d'),
            &request,
            &plan,
            TableTransposeHwpxLimits::default(),
        ),
        Err(TableTransposeHwpxError::SourceBindingMismatch)
    ));
    Ok(())
}

#[test]
fn formula_and_repeat_header_profiles_fail_closed() -> TestResult {
    let header = header()?;
    let mut formula_binding = rectangular_binding()?;
    formula_binding.cells[3].payload_block_ids.clear();
    assert!(matches!(
        read(&header, &rectangular_section(true), &formula_binding),
        Err(TableTransposeHwpxError::UnsupportedSourceProfile)
    ));
    assert!(matches!(
        read(
            &header,
            &repeated_header_section(),
            &ordinary_binding("repeat")?,
        ),
        Err(TableTransposeHwpxError::UnsupportedSourceProfile)
    ));
    Ok(())
}

#[test]
fn square_single_cell_noop_requires_unchanged_document_flow() -> TestResult {
    let header = header()?;
    let section = square_single_section();
    let binding = single_binding()?;
    let source = read(&header, &section, &binding)?;

    let same = draft(&source, 'f', 'f')?;
    let (request, plan) = admitted(&source, same, 'f')?;
    let lowered = TableTransposeHwpxLowerer::lower_existing(
        &header,
        &section,
        &binding,
        &flow('f'),
        &request,
        &plan,
        TableTransposeHwpxLimits::default(),
    )?;
    let reopened = read(&lowered.header, &lowered.section, &lowered.binding)?;
    assert_eq!(reopened.ruling.grid, source.ruling.grid);
    assert_eq!(reopened.ruling.state, source.ruling.state);

    assert!(matches!(
        TableTransposeHwpxRequest::from_draft(
            draft(&source, 'f', 'e')?,
            &source,
            &flow('f'),
            TableTransposeHwpxLimits::default(),
        ),
        Err(TableTransposeHwpxError::FlowBindingMismatch)
    ));
    Ok(())
}

#[test]
fn requests_are_bounded_and_debug_output_is_redacted() -> TestResult {
    let header = header()?;
    let section = rectangular_section(false);
    let binding = rectangular_binding()?;
    let source = read(&header, &section, &binding)?;
    let draft = draft(&source, 'f', 'e')?;
    let request = TableTransposeHwpxRequest::from_draft(
        draft,
        &source,
        &flow('f'),
        TableTransposeHwpxLimits::default(),
    )?;
    let plan = TableTransposeHwpxBuilder::build(
        &request,
        &source,
        &flow('f'),
        TableTransposeHwpxLimits::default(),
    )?;
    let request_debug = format!("{request:?}");
    let plan_debug = format!("{plan:?}");
    for secret in [
        "transpose-table",
        "cell-a",
        "payload-a1",
        request.expected_document_flow_sha256(),
        request.target_document_flow_sha256(),
    ] {
        assert!(!request_debug.contains(secret));
        assert!(!plan_debug.contains(secret));
    }

    let bounded = TableTransposeHwpxLimits {
        transpose: TableTransposeLimits::new(TableTransposeLimitConfig {
            input_bytes: 64,
            master_cells: 8,
            identifier_bytes: 64,
            serialized_bytes: 64,
        })?,
        ..TableTransposeHwpxLimits::default()
    };
    assert!(matches!(
        TableTransposeHwpxRequest::from_json(&[b'x'; 65], &source, &flow('f'), bounded,),
        Err(TableTransposeHwpxError::InputLimit)
    ));
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

fn package(header: &[u8], section: &[u8], opaque: &[u8]) -> TestResult<Vec<u8>> {
    Ok(archive(vec![
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
            header.to_vec(),
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
    ])?)
}

fn replace_target_parts(source: &[u8], header: &[u8], section: &[u8]) -> TestResult<Vec<u8>> {
    let mut reader = BoundedZipReader::open(Cursor::new(source), PackageLimits::default())?;
    let entries = reader.entries().to_vec();
    let mut parts = Vec::new();
    for entry in entries {
        let path = entry.path.as_str().to_owned();
        let compression = match entry.compression {
            Compression::Stored => CompressionMethod::Stored,
            Compression::Deflated => CompressionMethod::Deflated,
        };
        let bytes = match path.as_str() {
            "Contents/header.xml" => header.to_vec(),
            "Contents/section0.xml" => section.to_vec(),
            _ => reader.read_entry(entry.index)?,
        };
        parts.push((path, bytes, compression));
    }
    Ok(archive(parts)?)
}

fn expanded_package_parts(source: &[u8]) -> TestResult<BTreeMap<String, Vec<u8>>> {
    let mut reader = BoundedZipReader::open(Cursor::new(source), PackageLimits::default())?;
    let entries = reader.entries().to_vec();
    let mut parts = BTreeMap::new();
    for entry in entries {
        if parts
            .insert(
                entry.path.as_str().to_owned(),
                reader.read_entry(entry.index)?,
            )
            .is_some()
        {
            return Err("duplicate package path".into());
        }
    }
    Ok(parts)
}

#[test]
fn package_replacement_preserves_all_nontarget_parts_and_graph() -> TestResult {
    let header = header()?;
    let section = rectangular_section(false);
    let binding = rectangular_binding()?;
    let source = read(&header, &section, &binding)?;
    let (request, plan) = admitted(&source, draft(&source, 'f', 'e')?, 'f')?;
    let lowered = TableTransposeHwpxLowerer::lower_existing(
        &header,
        &section,
        &binding,
        &flow('f'),
        &request,
        &plan,
        TableTransposeHwpxLimits::default(),
    )?;
    let opaque = b"PRIVATE OPAQUE BYTES\0\xff";
    let original_package = package(&header, &section, opaque)?;
    let output_package =
        replace_target_parts(&original_package, &lowered.header, &lowered.section)?;
    let original_parts = expanded_package_parts(&original_package)?;
    let output_parts = expanded_package_parts(&output_package)?;
    assert_eq!(output_parts.len(), original_parts.len());
    for (path, bytes) in &original_parts {
        if path != "Contents/header.xml" && path != "Contents/section0.xml" {
            assert_eq!(output_parts.get(path), Some(bytes), "part drift: {path}");
        }
    }
    let packaged_header = output_parts
        .get("Contents/header.xml")
        .ok_or("packaged header missing")?;
    let packaged_section = output_parts
        .get("Contents/section0.xml")
        .ok_or("packaged section missing")?;
    assert_eq!(packaged_header, &lowered.header);
    assert_eq!(packaged_section, &lowered.section);
    let mut reader =
        BoundedZipReader::open(Cursor::new(&output_package), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    assert!(!graph.parts.is_empty());
    let reopened = read(packaged_header, packaged_section, &lowered.binding)?;
    assert_eq!(reopened.ruling.grid, *plan.target_grid());
    assert_eq!(reopened.ruling.state, *plan.target_state());
    Ok(())
}
