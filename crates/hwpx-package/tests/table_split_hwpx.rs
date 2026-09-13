use std::io::{Cursor, Write};

use domain_ir::{
    CellCoordinate, LogicalId, TABLE_PARTITION_SCHEMA_VERSION, TablePartitionError,
    TablePartitionFormulaPolicy, WholeTableSplitRequestDraft,
};
use hwpx_package::{
    BoundedZipReader, Compression, PackageGraph, PackageGraphLimits, PackageLimits,
    TABLE_SPLIT_HWPX_SCHEMA_VERSION, TableFormulaHwpxLimits, TableFormulaHwpxReader,
    TableLayoutHwpxLimits, TableLayoutHwpxReader, TablePaginationHwpxLimits,
    TablePaginationHwpxReader, TableRulingHwpxBinding, TableRulingHwpxCellBinding,
    TableSplitHwpxBuilder, TableSplitHwpxError, TableSplitHwpxLimits, TableSplitHwpxLowerer,
    TableSplitHwpxReadback, TableSplitHwpxReader, TableSplitHwpxRequest,
    TableSplitHwpxRequestDraft,
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
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let bytes = bytes.as_ref();
    let mut output = String::with_capacity(bytes.len().saturating_mul(2));
    for byte in bytes {
        output.push(char::from(DIGITS[usize::from(byte >> 4)]));
        output.push(char::from(DIGITS[usize::from(byte & 0x0f)]));
    }
    output
}

fn paragraph(value: &str) -> String {
    format!(
        r#"<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t>{value}</hp:t></hp:run></hp:p>"#
    )
}

fn text_wrapper(paragraph_id: u32, value: &str) -> String {
    format!(
        r#"<hp:p id="{paragraph_id}" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t>{value}</hp:t></hp:run></hp:p>"#
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

#[allow(clippy::too_many_arguments)]
fn cell(row: u32, column: u32, row_span: u32, width: u32, height: u32, payload: &str) -> String {
    format!(
        concat!(
            r#"<hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="0" borderFillIDRef="1">"#,
            r#"<hp:cellAddr colAddr="{column}" rowAddr="{row}"/>"#,
            r#"<hp:cellSpan colSpan="1" rowSpan="{row_span}"/>"#,
            r#"<hp:cellSz width="{width}" height="{height}"/>"#,
            r#"<hp:cellMargin left="0" right="0" top="0" bottom="0"/>"#,
            r#"<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">"#,
            "{payload}</hp:subList></hp:tc>"
        ),
        row = row,
        column = column,
        row_span = row_span,
        width = width,
        height = height,
        payload = payload,
    )
}

fn table(native_id: u32, rows: &[Vec<String>], row_count: u32) -> String {
    let mut body = String::new();
    for row in rows {
        body.push_str("<hp:tr>");
        body.push_str(&row.concat());
        body.push_str("</hp:tr>");
    }
    format!(
        concat!(
            r#"<hp:tbl id="{native_id}" zOrder="0" numberingType="TABLE" textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" pageBreak="CELL" repeatHeader="0" rowCnt="{row_count}" colCnt="2" cellSpacing="0" borderFillIDRef="1" noAdjust="0">"#,
            r#"<hp:sz width="2000" widthRelTo="ABSOLUTE" height="{height}" heightRelTo="ABSOLUTE" protect="0"/>"#,
            r#"<hp:pos treatAsChar="0" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP" horzAlign="LEFT" vertOffset="2000" horzOffset="1000"/>"#,
            r#"<hp:outMargin left="0" right="0" top="0" bottom="0"/>"#,
            r#"<hp:inMargin left="0" right="0" top="0" bottom="0"/>"#,
            "{body}</hp:tbl>"
        ),
        native_id = native_id,
        row_count = row_count,
        height = row_count * 500,
        body = body,
    )
}

fn wrapper(paragraph_id: u32, table: &str) -> String {
    format!(
        r#"<hp:p id="{paragraph_id}" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0">{table}</hp:run></hp:p>"#
    )
}

fn ordinary_table(native_id: u32) -> String {
    table(
        native_id,
        &[
            vec![
                cell(0, 0, 1, 1000, 500, &paragraph("A")),
                cell(0, 1, 1, 1000, 500, &paragraph("B")),
            ],
            vec![
                cell(1, 0, 1, 1000, 500, &paragraph("C")),
                cell(1, 1, 1, 1000, 500, &paragraph("D")),
            ],
            vec![
                cell(2, 0, 1, 1000, 500, &paragraph("E")),
                cell(2, 1, 1, 1000, 500, &paragraph("F")),
            ],
            vec![
                cell(3, 0, 1, 1000, 500, &paragraph("G")),
                cell(3, 1, 1, 1000, 500, &paragraph("H")),
            ],
        ],
        4,
    )
}

fn formula_table(native_id: u32) -> String {
    table(
        native_id,
        &[
            vec![
                cell(0, 0, 1, 1000, 500, &paragraph("1")),
                cell(0, 1, 1, 1000, 500, &paragraph("2")),
            ],
            vec![
                cell(1, 0, 1, 1000, 500, &paragraph("7")),
                cell(1, 1, 1, 1000, 500, formula_paragraph()),
            ],
        ],
        2,
    )
}

fn crossing_merged_table(native_id: u32) -> String {
    table(
        native_id,
        &[
            vec![
                cell(0, 0, 1, 1000, 500, &paragraph("A")),
                cell(0, 1, 1, 1000, 500, &paragraph("B")),
            ],
            vec![
                cell(1, 0, 2, 1000, 1000, &paragraph("CROSS")),
                cell(1, 1, 1, 1000, 500, &paragraph("D")),
            ],
            vec![cell(2, 1, 1, 1000, 500, &paragraph("F"))],
            vec![
                cell(3, 0, 1, 1000, 500, &paragraph("G")),
                cell(3, 1, 1, 1000, 500, &paragraph("H")),
            ],
        ],
        4,
    )
}

fn section(parts: &[String]) -> Vec<u8> {
    format!(
        r#"<hs:sec xmlns:hs="{SECTION_NS}" xmlns:hp="{PARAGRAPH_NS}">{}</hs:sec>"#,
        parts.concat()
    )
    .into_bytes()
}

fn ordinary_section() -> Vec<u8> {
    section(&[wrapper(10, &ordinary_table(700)), text_wrapper(90, "TAIL")])
}

fn binding(
    prefix: &str,
    rows: usize,
    payload_counts: &[usize],
) -> TestResult<TableRulingHwpxBinding> {
    let row_count = u32::try_from(rows)?;
    let mut cells = Vec::new();
    for (index, count) in payload_counts.iter().copied().enumerate() {
        let mut payload_block_ids = Vec::new();
        for payload_index in 0..count {
            payload_block_ids.push(id(&format!("{prefix}-payload-{index}-{payload_index}"))?);
        }
        cells.push(TableRulingHwpxCellBinding {
            master_cell_id: id(&format!("{prefix}-cell-{index}"))?,
            payload_block_ids,
        });
    }
    Ok(TableRulingHwpxBinding {
        table_id: id(&format!("{prefix}-table"))?,
        row_boundaries_hwpunit: (0..=row_count).map(|row| row * 500).collect(),
        column_boundaries_hwpunit: vec![0, 1000, 2000],
        cells,
    })
}

fn request_draft(
    source: &TableSplitHwpxReadback,
    split_row: u32,
    formula_policy: TablePartitionFormulaPolicy,
) -> TestResult<TableSplitHwpxRequestDraft> {
    let limits = TableSplitHwpxLimits::default();
    Ok(TableSplitHwpxRequestDraft {
        schema_version: TABLE_SPLIT_HWPX_SCHEMA_VERSION.to_owned(),
        table_ordinal: source.table_ordinal,
        expected_header_sha256: hex(source.ruling.header_sha256),
        expected_section_sha256: hex(source.ruling.section_sha256),
        expected_wrapper_sha256: hex(source.wrapper_sha256),
        split: WholeTableSplitRequestDraft {
            schema_version: TABLE_PARTITION_SCHEMA_VERSION.to_owned(),
            table_id: source.partition.table_id().clone(),
            cursor: CellCoordinate {
                row: split_row,
                column: 1,
            },
            second_table_id: id("split-second-table")?,
            separator_paragraph_id: id("split-separator")?,
            expected_state_sha256: hex(source.partition.canonical_sha256(limits.partition)?),
            expected_flow_sha256: digest('f'),
            formula_policy,
        },
    })
}

fn build(
    source: &TableSplitHwpxReadback,
    split_row: u32,
) -> TestResult<(TableSplitHwpxRequest, hwpx_package::TableSplitHwpxPlan)> {
    let limits = TableSplitHwpxLimits::default();
    let request = TableSplitHwpxRequest::from_draft(
        request_draft(source, split_row, TablePartitionFormulaPolicy::Reject)?,
        source,
        &digest('f'),
        limits,
    )?;
    let plan = TableSplitHwpxBuilder::build(&request, source, &digest('f'), limits)?;
    Ok((request, plan))
}

#[test]
fn split_table_hwpx_creates_two_exact_tables_and_separator() -> TestResult {
    let section = ordinary_section();
    let source_binding = binding("source", 4, &[1; 8])?;
    let limits = TableSplitHwpxLimits::default();
    let source = TableSplitHwpxReader::read_existing(HEADER, &section, 0, &source_binding, limits)?;
    let (request, plan) = build(&source, 2)?;
    let output = TableSplitHwpxLowerer::lower_existing(
        HEADER,
        &section,
        &source_binding,
        &digest('f'),
        &request,
        &plan,
        limits,
    )?;

    assert_eq!(plan.first_grid().rows(), 2);
    assert_eq!(plan.second_grid().rows(), 2);
    assert_eq!(
        TableLayoutHwpxReader::count_in_section(&output.section, TableLayoutHwpxLimits::default())?,
        2
    );
    let text = String::from_utf8(output.section.clone())?;
    assert!(text.contains(r#"<hp:p id="701""#));
    assert!(text.contains(r#"<hp:p id="702""#));
    assert!(text.contains(r#"<hp:tbl id="703""#));
    assert!(text.contains(
        r#"<hp:p id="701" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"/></hp:p>"#
    ));
    assert_eq!(text.matches("</hp:tbl><hp:t/></hp:run></hp:p>").count(), 2);
    assert!(text.ends_with(&(text_wrapper(90, "TAIL") + "</hs:sec>")));
    assert_eq!(output.receipt.source_table_count, 1);
    assert_eq!(output.receipt.target_table_count, 2);
    assert_eq!(output.receipt.preserved_master_cell_count, 8);
    assert_eq!(output.receipt.preserved_payload_block_count, 8);
    assert_eq!(output.receipt.allocated_native_id_count, 3);
    assert_eq!(output.header, HEADER);
    Ok(())
}

#[test]
fn split_table_hwpx_formula_and_boundary_profiles_fail_closed() -> TestResult {
    let ordinary = ordinary_section();
    let ordinary_binding = binding("source", 4, &[1; 8])?;
    let limits = TableSplitHwpxLimits::default();
    let source =
        TableSplitHwpxReader::read_existing(HEADER, &ordinary, 0, &ordinary_binding, limits)?;
    assert!(matches!(
        TableSplitHwpxRequest::from_draft(
            request_draft(&source, 0, TablePartitionFormulaPolicy::Reject)?,
            &source,
            &digest('f'),
            limits,
        ),
        Err(TableSplitHwpxError::Partition(
            TablePartitionError::FirstRowSplit
        ))
    ));
    assert!(matches!(
        TableSplitHwpxRequest::from_draft(
            request_draft(&source, 2, TablePartitionFormulaPolicy::RebaseAndClearCache,)?,
            &source,
            &digest('f'),
            limits,
        ),
        Err(TableSplitHwpxError::UnsupportedFormulaProfile)
    ));

    let repeated_header = String::from_utf8(ordinary_section())?
        .replacen(r#"repeatHeader="0""#, r#"repeatHeader="1""#, 1)
        .replacen(r#"header="0""#, r#"header="1""#, 2)
        .into_bytes();
    assert!(matches!(
        TableSplitHwpxReader::read_existing(HEADER, &repeated_header, 0, &ordinary_binding, limits,),
        Err(TableSplitHwpxError::UnsupportedPaginationProfile)
    ));

    let formula_section = section(&[wrapper(20, &formula_table(800))]);
    let formula_binding = binding("formula", 2, &[1, 1, 1, 0])?;
    let formula_source =
        TableSplitHwpxReader::read_existing(HEADER, &formula_section, 0, &formula_binding, limits)?;
    assert!(matches!(
        TableSplitHwpxRequest::from_draft(
            request_draft(&formula_source, 1, TablePartitionFormulaPolicy::Reject)?,
            &formula_source,
            &digest('f'),
            limits,
        ),
        Err(TableSplitHwpxError::Partition(
            TablePartitionError::FormulaPresent
        ))
    ));
    Ok(())
}

#[test]
fn split_table_hwpx_crossing_merge_and_wrapper_fail_closed() -> TestResult {
    let limits = TableSplitHwpxLimits::default();
    let merged = section(&[wrapper(10, &crossing_merged_table(700))]);
    let merged_binding = binding("merged", 4, &[1; 7])?;
    let source = TableSplitHwpxReader::read_existing(HEADER, &merged, 0, &merged_binding, limits)?;
    assert!(matches!(
        TableSplitHwpxRequest::from_draft(
            request_draft(&source, 2, TablePartitionFormulaPolicy::Reject)?,
            &source,
            &digest('f'),
            limits,
        ),
        Err(TableSplitHwpxError::Partition(
            TablePartitionError::SpanBoundaryConflict
        ))
    ));

    let bare = section(&[ordinary_table(700)]);
    assert!(matches!(
        TableSplitHwpxReader::read_existing(
            HEADER,
            &bare,
            0,
            &binding("bare", 4, &[1; 8])?,
            limits
        ),
        Err(TableSplitHwpxError::UnsupportedWrapper)
    ));
    Ok(())
}

#[test]
fn split_table_hwpx_part_flow_plan_and_json_drift_fail_closed() -> TestResult {
    let section = ordinary_section();
    let source_binding = binding("source", 4, &[1; 8])?;
    let limits = TableSplitHwpxLimits::default();
    let source = TableSplitHwpxReader::read_existing(HEADER, &section, 0, &source_binding, limits)?;
    let (request, plan) = build(&source, 2)?;

    let mut part_drift = request_draft(&source, 2, TablePartitionFormulaPolicy::Reject)?;
    part_drift.expected_section_sha256 = digest('a');
    assert!(matches!(
        TableSplitHwpxRequest::from_draft(part_drift, &source, &digest('f'), limits),
        Err(TableSplitHwpxError::SourceBindingMismatch)
    ));
    assert!(matches!(
        TableSplitHwpxBuilder::build(&request, &source, &digest('e'), limits),
        Err(TableSplitHwpxError::Partition(
            TablePartitionError::FlowBindingMismatch
        ))
    ));
    let (_, alternate_plan) = build(&source, 1)?;
    assert!(matches!(
        TableSplitHwpxLowerer::lower_existing(
            HEADER,
            &section,
            &source_binding,
            &digest('f'),
            &request,
            &alternate_plan,
            limits,
        ),
        Err(TableSplitHwpxError::PlanBindingMismatch)
    ));
    assert!(matches!(
        TableSplitHwpxRequest::from_json(b"", &source, &digest('f'), limits),
        Err(TableSplitHwpxError::InputLimit)
    ));
    let unknown =
        String::from_utf8(request.canonical_json(limits)?)?.replacen('{', r#"{"unknown":0,"#, 1);
    assert!(matches!(
        TableSplitHwpxRequest::from_json(unknown.as_bytes(), &source, &digest('f'), limits),
        Err(TableSplitHwpxError::InvalidJson)
    ));
    let duplicate = String::from_utf8(request.canonical_json(limits)?)?.replacen(
        '{',
        r#"{"schema_version":"hwpx-agent.table-split-hwpx/v1","#,
        1,
    );
    assert!(matches!(
        TableSplitHwpxRequest::from_json(duplicate.as_bytes(), &source, &digest('f'), limits),
        Err(TableSplitHwpxError::InvalidJson)
    ));
    let debug = format!("{request:?}{plan:?}{:?}", output_debug_source(&source));
    assert!(!debug.contains("source-table"));
    assert!(!debug.contains(&digest('f')));
    Ok(())
}

fn output_debug_source(source: &TableSplitHwpxReadback) -> String {
    format!("{source:?}")
}

#[test]
fn split_table_hwpx_closed_package_preserves_sibling_formula_and_parts() -> TestResult {
    let sibling = wrapper(20, &formula_table(800));
    let tail = text_wrapper(90, "BETWEEN");
    let section = section(&[
        wrapper(10, &ordinary_table(700)),
        tail.clone(),
        sibling.clone(),
    ]);
    let source_binding = binding("source", 4, &[1; 8])?;
    let limits = TableSplitHwpxLimits::default();
    let source = TableSplitHwpxReader::read_existing(HEADER, &section, 0, &source_binding, limits)?;
    let formula_before = TableFormulaHwpxReader::read_in_section(
        &section,
        1,
        TableFormulaHwpxLimits::default(),
        limits.ruling.formula,
    )
    .map_err(|error| format!("formula-before fixture: {error:?}"))?;
    let pagination_before = TablePaginationHwpxReader::read_in_section(
        &section,
        0,
        TablePaginationHwpxLimits::default(),
    )
    .map_err(|error| format!("pagination-before fixture: {error:?}"))?;
    let (request, plan) = build(&source, 2)?;
    let output = TableSplitHwpxLowerer::lower_existing(
        HEADER,
        &section,
        &source_binding,
        &digest('f'),
        &request,
        &plan,
        limits,
    )
    .map_err(|error| format!("split lowering: {error:?}"))?;
    let output_text = String::from_utf8(output.section.clone())?;
    assert!(output_text.ends_with(&(tail + &sibling + "</hs:sec>")));
    let formula_after = TableFormulaHwpxReader::read_in_section(
        &output.section,
        2,
        TableFormulaHwpxLimits::default(),
        limits.ruling.formula,
    )
    .map_err(|error| format!("formula-after fixture: {error:?}"))?;
    assert_eq!(formula_before.profile_id, formula_after.profile_id);
    assert_eq!(formula_before.rows, formula_after.rows);
    assert_eq!(formula_before.columns, formula_after.columns);
    assert_eq!(formula_before.formula, formula_after.formula);
    assert_eq!(
        formula_before.formula_field_count,
        formula_after.formula_field_count
    );
    let first_pagination = TablePaginationHwpxReader::read_in_section(
        &output.section,
        0,
        TablePaginationHwpxLimits::default(),
    )?;
    let second_pagination = TablePaginationHwpxReader::read_in_section(
        &output.section,
        1,
        TablePaginationHwpxLimits::default(),
    )?;
    assert_eq!(pagination_before.page_split, first_pagination.page_split);
    assert_eq!(pagination_before.page_split, second_pagination.page_split);
    assert_eq!(
        pagination_before.repeat_header_rows,
        first_pagination.repeat_header_rows
    );
    assert_eq!(
        pagination_before.repeat_header_rows,
        second_pagination.repeat_header_rows
    );
    assert_eq!(pagination_before.caption, first_pagination.caption);
    assert_eq!(pagination_before.caption, second_pagination.caption);

    let source_package = package(HEADER, &section)?;
    let output_package = replace_parts(&source_package, &output.header, &output.section)?;
    assert_non_section_parts_preserved(&source_package, &output_package)?;
    let mut reader = BoundedZipReader::open(Cursor::new(output_package), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    assert_eq!(graph.spine.len(), 1);
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

fn assert_non_section_parts_preserved(source: &[u8], target: &[u8]) -> TestResult {
    let mut source = BoundedZipReader::open(Cursor::new(source), PackageLimits::default())?;
    let mut target = BoundedZipReader::open(Cursor::new(target), PackageLimits::default())?;
    let source_entries = source.entries().to_vec();
    for entry in source_entries {
        let path = entry.path.as_str();
        if !matches!(path, "Contents/header.xml" | "Contents/section0.xml") {
            let target_index = target
                .entries()
                .iter()
                .find(|target_entry| target_entry.path.as_str() == path)
                .map(|target_entry| target_entry.index)
                .ok_or("target package entry missing")?;
            assert_eq!(
                source.read_entry(entry.index)?,
                target.read_entry(target_index)?
            );
        }
    }
    Ok(())
}
