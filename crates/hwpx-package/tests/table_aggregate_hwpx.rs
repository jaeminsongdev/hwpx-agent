use std::io::{Cursor, Write};

use domain_ir::{
    CellCoordinate, FormulaCache, FormulaDecimal, FormulaFunction, FormulaLimits, FormulaValue,
    LogicalId, TABLE_AGGREGATE_SCHEMA_VERSION, TableAggregateAxis, TableAggregateRange,
    TableAggregateRequestDraft, TableRulingLimits,
};
use hwpx_package::{
    BoundedZipReader, Compression, PackageGraph, PackageGraphLimits, PackageLimits,
    TABLE_AGGREGATE_HWPX_SCHEMA_VERSION, TableAggregateHwpxBuilder, TableAggregateHwpxError,
    TableAggregateHwpxLimits, TableAggregateHwpxLowerer, TableAggregateHwpxReadback,
    TableAggregateHwpxReader, TableAggregateHwpxRequest, TableAggregateHwpxRequestDraft,
    TableFormulaHwpxError, TableFormulaHwpxReader, TableRulingHwpxBinding,
    TableRulingHwpxCellBinding,
};
use zip::write::SimpleFileOptions;
use zip::{CompressionMethod, DateTime, ZipWriter};

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

fn digest(character: char) -> String {
    std::iter::repeat_n(character, 64).collect()
}

fn hex(bytes: impl AsRef<[u8]>) -> String {
    use std::fmt::Write as _;

    bytes
        .as_ref()
        .iter()
        .fold(String::new(), |mut output, byte| {
            let _ = write!(output, "{byte:02x}");
            output
        })
}

fn paragraph(value: &str) -> String {
    format!(
        r#"<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t>{value}</hp:t></hp:run></hp:p>"#
    )
}

fn empty_paragraph() -> &'static str {
    r#"<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t/></hp:run></hp:p>"#
}

#[allow(clippy::too_many_arguments)]
fn cell(
    row: u32,
    column: u32,
    row_span: u32,
    column_span: u32,
    header: bool,
    payload: &str,
) -> String {
    format!(
        concat!(
            r#"<hp:tc name="" header="{header}" hasMargin="0" protect="0" editable="0" dirty="0" borderFillIDRef="1">"#,
            r#"<hp:cellAddr colAddr="{column}" rowAddr="{row}"/>"#,
            r#"<hp:cellSpan colSpan="{column_span}" rowSpan="{row_span}"/>"#,
            r#"<hp:cellSz width="{width}" height="500"/>"#,
            r#"<hp:cellMargin left="0" right="0" top="0" bottom="0"/>"#,
            r#"<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">"#,
            "{payload}</hp:subList></hp:tc>"
        ),
        header = u8::from(header),
        column = column,
        row = row,
        column_span = column_span,
        row_span = row_span,
        width = column_span * 1000,
        payload = payload,
    )
}

fn caption() -> &'static str {
    concat!(
        r#"<hp:caption side="TOP" fullSz="0" width="42520" gap="850" lastWidth="42520">"#,
        r#"<hp:subList><hp:p><hp:run><hp:t>CAPTION &amp; LABEL</hp:t></hp:run></hp:p></hp:subList></hp:caption>"#,
    )
}

fn table(rows: &[Vec<String>]) -> String {
    let mut body = String::new();
    for cells in rows {
        body.push_str("<hp:tr>");
        body.push_str(&cells.concat());
        body.push_str("</hp:tr>");
    }
    let columns = 4_u32;
    let rows = 4_u32;
    format!(
        concat!(
            r#"<hp:tbl id="700" zOrder="0" numberingType="TABLE" textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" pageBreak="TABLE" repeatHeader="1" rowCnt="{rows}" colCnt="{columns}" cellSpacing="0" borderFillIDRef="1" noAdjust="0">"#,
            r#"<hp:sz width="4000" widthRelTo="ABSOLUTE" height="2000" heightRelTo="ABSOLUTE" protect="0"/>"#,
            r#"<hp:pos treatAsChar="0" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP" horzAlign="LEFT" vertOffset="2000" horzOffset="1000"/>"#,
            r#"<hp:outMargin left="0" right="0" top="0" bottom="0"/>"#,
            "{caption}",
            r#"<hp:inMargin left="0" right="0" top="0" bottom="0"/>"#,
            "{body}</hp:tbl>"
        ),
        rows = rows,
        columns = columns,
        caption = caption(),
        body = body,
    )
}

fn ordinary_table(destination_empty: bool) -> String {
    let mut rows = Vec::new();
    for row in 0..4 {
        let mut cells = Vec::new();
        for column in 0..4 {
            let payload = if destination_empty && row == 3 && column == 3 {
                empty_paragraph().to_owned()
            } else {
                paragraph(&(row * 4 + column + 1).to_string())
            };
            cells.push(cell(row, column, 1, 1, row == 0, &payload));
        }
        rows.push(cells);
    }
    table(&rows)
}

fn merged_table() -> String {
    let mut rows = Vec::new();
    for row in 0..3 {
        rows.push(
            (0..4)
                .map(|column| {
                    cell(
                        row,
                        column,
                        1,
                        1,
                        row == 0,
                        &paragraph(&(row * 4 + column + 1).to_string()),
                    )
                })
                .collect(),
        );
    }
    rows.push(vec![
        cell(3, 0, 1, 1, false, &paragraph("13")),
        cell(3, 1, 1, 1, false, &paragraph("14")),
        cell(3, 2, 1, 2, false, &paragraph("15")),
    ]);
    table(&rows)
}

fn section(table: &str) -> Vec<u8> {
    format!(
        r#"<hs:sec xmlns:hs="{SECTION_NS}" xmlns:hp="{PARAGRAPH_NS}"><hp:p id="10" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0">{table}</hp:run></hp:p><hp:p id="90"><hp:run><hp:t>TAIL</hp:t></hp:run></hp:p></hs:sec>"#
    )
    .into_bytes()
}

fn binding(prefix: &str, destination_empty: bool) -> TestResult<TableRulingHwpxBinding> {
    let mut cells = Vec::new();
    for row in 0..4 {
        for column in 0..4 {
            cells.push(TableRulingHwpxCellBinding {
                master_cell_id: id(&format!("{prefix}-cell-{row}-{column}"))?,
                payload_block_ids: if destination_empty && row == 3 && column == 3 {
                    Vec::new()
                } else {
                    vec![id(&format!("{prefix}-payload-{row}-{column}"))?]
                },
            });
        }
    }
    Ok(TableRulingHwpxBinding {
        table_id: id(&format!("{prefix}-table"))?,
        row_boundaries_hwpunit: vec![0, 500, 1000, 1500, 2000],
        column_boundaries_hwpunit: vec![0, 1000, 2000, 3000, 4000],
        cells,
    })
}

fn merged_binding() -> TestResult<TableRulingHwpxBinding> {
    let mut cells = Vec::new();
    for row in 0..4 {
        for column in 0..4 {
            if row == 3 && column == 3 {
                continue;
            }
            cells.push(TableRulingHwpxCellBinding {
                master_cell_id: id(&format!("merged-cell-{row}-{column}"))?,
                payload_block_ids: vec![id(&format!("merged-payload-{row}-{column}"))?],
            });
        }
    }
    Ok(TableRulingHwpxBinding {
        table_id: id("merged-table")?,
        row_boundaries_hwpunit: vec![0, 500, 1000, 1500, 2000],
        column_boundaries_hwpunit: vec![0, 1000, 2000, 3000, 4000],
        cells,
    })
}

fn read(
    section: &[u8],
    binding: &TableRulingHwpxBinding,
) -> Result<TableAggregateHwpxReadback, TableAggregateHwpxError> {
    TableAggregateHwpxReader::read_existing(
        HEADER,
        section,
        0,
        binding,
        TableAggregateHwpxLimits::default(),
    )
}

fn cache(value: i64) -> FormulaCache {
    FormulaCache::Unverified {
        value: FormulaValue::Decimal {
            value: FormulaDecimal::new(value, 0),
        },
    }
}

fn source_range(axis: TableAggregateAxis) -> TableAggregateRange {
    match axis {
        TableAggregateAxis::Block => TableAggregateRange {
            start: CellCoordinate { row: 0, column: 0 },
            end: CellCoordinate { row: 1, column: 1 },
        },
        TableAggregateAxis::Horizontal => TableAggregateRange {
            start: CellCoordinate { row: 3, column: 0 },
            end: CellCoordinate { row: 3, column: 2 },
        },
        TableAggregateAxis::Vertical => TableAggregateRange {
            start: CellCoordinate { row: 0, column: 3 },
            end: CellCoordinate { row: 2, column: 3 },
        },
    }
}

fn request_draft(
    source: &TableAggregateHwpxReadback,
    axis: TableAggregateAxis,
    function: FormulaFunction,
    target_cache: FormulaCache,
) -> TestResult<TableAggregateHwpxRequestDraft> {
    Ok(TableAggregateHwpxRequestDraft {
        schema_version: TABLE_AGGREGATE_HWPX_SCHEMA_VERSION.to_owned(),
        table_ordinal: 0,
        expected_header_sha256: hex(source.ruling.header_sha256),
        expected_section_sha256: hex(source.ruling.section_sha256),
        expected_source_state_sha256: hex(source
            .ruling
            .state
            .canonical_sha256(TableRulingLimits::default())?),
        expected_source_grid_sha256: hex(source.ruling.grid.canonical_sha256()?),
        expected_document_flow_sha256: digest('f'),
        target_document_flow_sha256: digest('e'),
        aggregate: TableAggregateRequestDraft {
            schema_version: TABLE_AGGREGATE_SCHEMA_VERSION.to_owned(),
            axis,
            function,
            source: source_range(axis),
            destination: CellCoordinate { row: 3, column: 3 },
        },
        target_cache,
    })
}

fn admitted(
    source: &TableAggregateHwpxReadback,
    draft: TableAggregateHwpxRequestDraft,
) -> TestResult<(
    TableAggregateHwpxRequest,
    hwpx_package::TableAggregateHwpxPlan,
)> {
    let request = TableAggregateHwpxRequest::from_draft(
        draft,
        source,
        &digest('f'),
        TableAggregateHwpxLimits::default(),
    )?;
    let plan = TableAggregateHwpxBuilder::build(
        &request,
        source,
        &digest('f'),
        TableAggregateHwpxLimits::default(),
    )?;
    Ok((request, plan))
}

#[test]
fn all_nine_axis_function_mappings_lower_and_preserve_complete_state() -> TestResult {
    let section = section(&ordinary_table(true));
    let binding = binding("all", true)?;
    let source = read(&section, &binding)?;
    let immutable_source = source.clone();
    for axis in [
        TableAggregateAxis::Block,
        TableAggregateAxis::Horizontal,
        TableAggregateAxis::Vertical,
    ] {
        for function in [
            FormulaFunction::Sum,
            FormulaFunction::Average,
            FormulaFunction::Product,
        ] {
            let draft = request_draft(&source, axis, function, cache(99))?;
            let canonical_draft = serde_json::to_vec(&draft)?;
            let request = TableAggregateHwpxRequest::from_json(
                &canonical_draft,
                &source,
                &digest('f'),
                TableAggregateHwpxLimits::default(),
            )?;
            assert_eq!(request.capability_id(), request.aggregate().capability_id());
            let plan = TableAggregateHwpxBuilder::build(
                &request,
                &source,
                &digest('f'),
                TableAggregateHwpxLimits::default(),
            )?;
            let lowered = TableAggregateHwpxLowerer::lower_existing(
                HEADER,
                &section,
                &binding,
                &digest('f'),
                &request,
                &plan,
                TableAggregateHwpxLimits::default(),
            )?;
            let reopened = read(&lowered.section, &binding)?;
            assert_eq!(lowered.header, HEADER);
            assert_eq!(reopened.ruling.state, *plan.target_state());
            assert_eq!(reopened.ruling.grid, *plan.target_grid());
            assert_eq!(reopened.pagination.page_split, source.pagination.page_split);
            assert_eq!(
                reopened.pagination.repeat_header_rows,
                source.pagination.repeat_header_rows
            );
            assert_eq!(reopened.pagination.caption, source.pagination.caption);
            assert_eq!(reopened.ruling.formula_count, 1);
            assert!(matches!(
                TableFormulaHwpxReader::read_in_section(
                    &lowered.section,
                    0,
                    TableAggregateHwpxLimits::default().ruling.formula_hwpx,
                    FormulaLimits::default(),
                ),
                Err(TableFormulaHwpxError::UnsupportedShape)
            ));
            assert_eq!(
                plan.target_formula()
                    .ast()
                    .canonical_formula(FormulaLimits::default())?,
                match (axis, function) {
                    (TableAggregateAxis::Block, FormulaFunction::Sum) => "SUM(A1:B2)",
                    (TableAggregateAxis::Block, FormulaFunction::Average) => "AVG(A1:B2)",
                    (TableAggregateAxis::Block, FormulaFunction::Product) => "PRODUCT(A1:B2)",
                    (TableAggregateAxis::Horizontal, FormulaFunction::Sum) => "SUM(A4:C4)",
                    (TableAggregateAxis::Horizontal, FormulaFunction::Average) => "AVG(A4:C4)",
                    (TableAggregateAxis::Horizontal, FormulaFunction::Product) => "PRODUCT(A4:C4)",
                    (TableAggregateAxis::Vertical, FormulaFunction::Sum) => "SUM(D1:D3)",
                    (TableAggregateAxis::Vertical, FormulaFunction::Average) => "AVG(D1:D3)",
                    (TableAggregateAxis::Vertical, FormulaFunction::Product) => "PRODUCT(D1:D3)",
                }
            );
            assert_eq!(lowered.receipt.preserved_master_cell_count, 16);
            assert_eq!(lowered.receipt.preserved_payload_block_count, 15);
            assert_eq!(lowered.receipt.preserved_edge_count, 40);
            assert_eq!(lowered.receipt.inserted_formula_field_count, 1);
            assert!(lowered.receipt.pagination_preserved);
            assert!(lowered.receipt.caption_preserved);
            assert!(String::from_utf8(lowered.section)?.contains("??%g,;;99"));
        }
    }
    assert_eq!(source, immutable_source);
    Ok(())
}

#[test]
fn merged_nonempty_and_existing_formula_sources_fail_closed() -> TestResult {
    let nonempty_section = section(&ordinary_table(false));
    let nonempty_binding = binding("nonempty", false)?;
    let nonempty = read(&nonempty_section, &nonempty_binding)?;
    let draft = request_draft(
        &nonempty,
        TableAggregateAxis::Block,
        FormulaFunction::Sum,
        cache(10),
    )?;
    assert!(matches!(
        TableAggregateHwpxRequest::from_draft(
            draft,
            &nonempty,
            &digest('f'),
            TableAggregateHwpxLimits::default(),
        ),
        Err(TableAggregateHwpxError::DestinationNotEmpty)
    ));

    assert!(matches!(
        read(&section(&merged_table()), &merged_binding()?),
        Err(TableAggregateHwpxError::UnsupportedSourceProfile)
    ));

    let malformed_empty = String::from_utf8(section(&ordinary_table(true)))?.replace(
        empty_paragraph(),
        r#"<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t/></hp:run><hp:run charPrIDRef="0"><hp:t/></hp:run></hp:p>"#,
    );
    let malformed_empty = malformed_empty.into_bytes();
    let malformed_binding = binding("malformed-empty", true)?;
    let malformed_source = read(&malformed_empty, &malformed_binding)?;
    let (malformed_request, malformed_plan) = admitted(
        &malformed_source,
        request_draft(
            &malformed_source,
            TableAggregateAxis::Block,
            FormulaFunction::Sum,
            cache(10),
        )?,
    )?;
    assert!(matches!(
        TableAggregateHwpxLowerer::lower_existing(
            HEADER,
            &malformed_empty,
            &malformed_binding,
            &digest('f'),
            &malformed_request,
            &malformed_plan,
            TableAggregateHwpxLimits::default(),
        ),
        Err(TableAggregateHwpxError::Formula(
            TableFormulaHwpxError::UnsupportedShape
        ))
    ));

    let section = section(&ordinary_table(true));
    let binding = binding("existing", true)?;
    let source = read(&section, &binding)?;
    let (request, plan) = admitted(
        &source,
        request_draft(
            &source,
            TableAggregateAxis::Horizontal,
            FormulaFunction::Sum,
            cache(42),
        )?,
    )?;
    let lowered = TableAggregateHwpxLowerer::lower_existing(
        HEADER,
        &section,
        &binding,
        &digest('f'),
        &request,
        &plan,
        TableAggregateHwpxLimits::default(),
    )?;
    let with_formula = read(&lowered.section, &binding)?;
    let existing_draft = request_draft(
        &with_formula,
        TableAggregateAxis::Vertical,
        FormulaFunction::Average,
        cache(7),
    )?;
    assert!(matches!(
        TableAggregateHwpxRequest::from_draft(
            existing_draft,
            &with_formula,
            &digest('f'),
            TableAggregateHwpxLimits::default(),
        ),
        Err(TableAggregateHwpxError::UnsupportedSourceProfile)
    ));
    Ok(())
}

#[test]
#[allow(clippy::too_many_lines)]
fn source_flow_plan_json_native_shape_and_debug_tampering_fail_closed() -> TestResult {
    let section = section(&ordinary_table(true));
    let binding = binding("tamper", true)?;
    let source = read(&section, &binding)?;
    let base = request_draft(
        &source,
        TableAggregateAxis::Block,
        FormulaFunction::Product,
        cache(24),
    )?;

    let mut state_drift = base.clone();
    state_drift.expected_source_state_sha256 = digest('a');
    assert!(matches!(
        TableAggregateHwpxRequest::from_draft(
            state_drift,
            &source,
            &digest('f'),
            TableAggregateHwpxLimits::default(),
        ),
        Err(TableAggregateHwpxError::SourceBindingMismatch)
    ));
    let mut grid_drift = base.clone();
    grid_drift.expected_source_grid_sha256 = digest('b');
    assert!(matches!(
        TableAggregateHwpxRequest::from_draft(
            grid_drift,
            &source,
            &digest('f'),
            TableAggregateHwpxLimits::default(),
        ),
        Err(TableAggregateHwpxError::SourceBindingMismatch)
    ));
    assert!(matches!(
        TableAggregateHwpxRequest::from_draft(
            base.clone(),
            &source,
            &digest('d'),
            TableAggregateHwpxLimits::default(),
        ),
        Err(TableAggregateHwpxError::SourceBindingMismatch)
    ));

    let (request, plan) = admitted(&source, base.clone())?;
    let (_, foreign_plan) = admitted(
        &source,
        request_draft(
            &source,
            TableAggregateAxis::Block,
            FormulaFunction::Average,
            cache(24),
        )?,
    )?;
    assert!(matches!(
        TableAggregateHwpxLowerer::lower_existing(
            HEADER,
            &section,
            &binding,
            &digest('f'),
            &request,
            &foreign_plan,
            TableAggregateHwpxLimits::default(),
        ),
        Err(TableAggregateHwpxError::PlanBindingMismatch)
    ));
    let mut part_drift = section.clone();
    part_drift.extend_from_slice(b" ");
    assert!(matches!(
        TableAggregateHwpxLowerer::lower_existing(
            HEADER,
            &part_drift,
            &binding,
            &digest('f'),
            &request,
            &plan,
            TableAggregateHwpxLimits::default(),
        ),
        Err(TableAggregateHwpxError::SourceBindingMismatch)
    ));

    let lowered = TableAggregateHwpxLowerer::lower_existing(
        HEADER,
        &section,
        &binding,
        &digest('f'),
        &request,
        &plan,
        TableAggregateHwpxLimits::default(),
    )?;
    for tampered in [
        String::from_utf8(lowered.section.clone())?.replace(
            "<hp:stringParam name=\"ResultFormat\">%g,</hp:stringParam>",
            "<hp:stringParam name=\"ResultFormat\">%0.2f</hp:stringParam>",
        ),
        String::from_utf8(lowered.section.clone())?.replace(
            "<hp:stringParam name=\"LastResult\">24</hp:stringParam>",
            "<hp:stringParam name=\"LastResult\">25</hp:stringParam>",
        ),
    ] {
        assert!(matches!(
            read(tampered.as_bytes(), &binding),
            Err(TableAggregateHwpxError::Ruling(_))
        ));
    }

    let duplicate = serde_json::to_vec(&base)?;
    let duplicate = String::from_utf8(duplicate)?.replacen(
        r#""schema_version":"hwpx-agent.table-aggregate-hwpx/v1""#,
        r#""schema_version":"hwpx-agent.table-aggregate-hwpx/v1","schema_version":"hwpx-agent.table-aggregate-hwpx/v1""#,
        1,
    );
    assert!(matches!(
        TableAggregateHwpxRequest::from_json(
            duplicate.as_bytes(),
            &source,
            &digest('f'),
            TableAggregateHwpxLimits::default(),
        ),
        Err(TableAggregateHwpxError::InvalidJson)
    ));
    let unknown = serde_json::to_vec(&base)?;
    let unknown = String::from_utf8(unknown)?.replacen('{', r#"{"unknown":1,"#, 1);
    assert!(matches!(
        TableAggregateHwpxRequest::from_json(
            unknown.as_bytes(),
            &source,
            &digest('f'),
            TableAggregateHwpxLimits::default(),
        ),
        Err(TableAggregateHwpxError::InvalidJson)
    ));

    let debug = format!("{base:?} {request:?} {plan:?}");
    assert!(!debug.contains(&digest('f')));
    assert!(!debug.contains("coefficient"));
    assert!(!debug.contains("99"));
    Ok(())
}

#[test]
fn closed_package_reopen_preserves_every_unselected_part() -> TestResult {
    let section = section(&ordinary_table(true));
    let binding = binding("package", true)?;
    let source = read(&section, &binding)?;
    let (request, plan) = admitted(
        &source,
        request_draft(
            &source,
            TableAggregateAxis::Vertical,
            FormulaFunction::Product,
            cache(120),
        )?,
    )?;
    let lowered = TableAggregateHwpxLowerer::lower_existing(
        HEADER,
        &section,
        &binding,
        &digest('f'),
        &request,
        &plan,
        TableAggregateHwpxLimits::default(),
    )?;
    let source_package = package(HEADER, &section)?;
    let immutable_source = source_package.clone();
    let target_package = replace_parts(&source_package, &lowered.header, &lowered.section)?;
    assert_eq!(source_package, immutable_source);
    assert_non_selected_parts_preserved(&source_package, &target_package)?;

    let mut reader = BoundedZipReader::open(Cursor::new(target_package), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    assert_eq!(graph.spine.len(), 1);
    let header = read_entry(&mut reader, "Contents/header.xml")?;
    let section = read_entry(&mut reader, "Contents/section0.xml")?;
    let reopened = TableAggregateHwpxReader::read_existing(
        &header,
        &section,
        0,
        &lowered.binding,
        TableAggregateHwpxLimits::default(),
    )?;
    assert_eq!(reopened.ruling.state, *plan.target_state());
    assert_eq!(reopened.ruling.grid, *plan.target_grid());
    Ok(())
}

fn package(header: &[u8], section: &[u8]) -> Result<Vec<u8>, zip::result::ZipError> {
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    for (path, bytes, method) in [
        (
            "mimetype",
            b"application/hwp+zip".as_slice(),
            CompressionMethod::Stored,
        ),
        (
            "version.xml",
            b"<version/>".as_slice(),
            CompressionMethod::Stored,
        ),
        (
            "META-INF/container.xml",
            CONTAINER.as_bytes(),
            CompressionMethod::Deflated,
        ),
        (
            "Contents/content.hpf",
            OPF.as_bytes(),
            CompressionMethod::Deflated,
        ),
        ("Contents/header.xml", header, CompressionMethod::Deflated),
        (
            "Contents/section0.xml",
            section,
            CompressionMethod::Deflated,
        ),
        (
            "Contents/opaque.bin",
            b"opaque".as_slice(),
            CompressionMethod::Stored,
        ),
    ] {
        let options = SimpleFileOptions::default()
            .compression_method(method)
            .last_modified_time(DateTime::default())
            .system(zip::System::Unix)
            .unix_permissions(0o644);
        writer.start_file(path, options)?;
        writer.write_all(bytes)?;
    }
    Ok(writer.finish()?.into_inner())
}

fn replace_parts(source: &[u8], header: &[u8], section: &[u8]) -> TestResult<Vec<u8>> {
    let mut reader = BoundedZipReader::open(Cursor::new(source), PackageLimits::default())?;
    let entries = reader.entries().to_vec();
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    for entry in entries {
        let path = entry.path.as_str();
        let bytes = match path {
            "Contents/header.xml" => header.to_vec(),
            "Contents/section0.xml" => section.to_vec(),
            _ => reader.read_entry(entry.index)?,
        };
        let method = match entry.compression {
            Compression::Stored => CompressionMethod::Stored,
            Compression::Deflated => CompressionMethod::Deflated,
        };
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

fn assert_non_selected_parts_preserved(source: &[u8], target: &[u8]) -> TestResult {
    let mut source = BoundedZipReader::open(Cursor::new(source), PackageLimits::default())?;
    let mut target = BoundedZipReader::open(Cursor::new(target), PackageLimits::default())?;
    for entry in source.entries().to_vec() {
        let path = entry.path.as_str();
        if !matches!(path, "Contents/header.xml" | "Contents/section0.xml") {
            let target_index = target
                .entries()
                .iter()
                .find(|candidate| candidate.path.as_str() == path)
                .map(|candidate| candidate.index)
                .ok_or("target package entry missing")?;
            assert_eq!(
                source.read_entry(entry.index)?,
                target.read_entry(target_index)?
            );
        }
    }
    Ok(())
}

fn read_entry(reader: &mut BoundedZipReader<Cursor<Vec<u8>>>, path: &str) -> TestResult<Vec<u8>> {
    let index = reader
        .entries()
        .iter()
        .find(|entry| entry.path.as_str() == path)
        .map(|entry| entry.index)
        .ok_or("package entry missing")?;
    Ok(reader.read_entry(index)?)
}
