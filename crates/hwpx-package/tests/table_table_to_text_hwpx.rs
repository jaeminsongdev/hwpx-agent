use std::collections::BTreeMap;
use std::io::{Cursor, Write};

use domain_ir::{LogicalId, TableDelimiter, TableLineEnding};
use hwpx_package::{
    BoundedZipReader, Compression, PackageGraph, PackageGraphLimits, PackageLimits,
    TABLE_TABLE_TO_TEXT_HWPX_SCHEMA_VERSION, TableRulingHwpxBinding, TableRulingHwpxCellBinding,
    TableTableToTextHwpxBuilder, TableTableToTextHwpxError, TableTableToTextHwpxLimits,
    TableTableToTextHwpxLowerer, TableTableToTextHwpxReader, TableTableToTextHwpxRequest,
    TableTableToTextHwpxRequestDraft,
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

fn flow(value: char) -> String {
    std::iter::repeat_n(value, 64).collect()
}

fn hex(value: impl AsRef<[u8]>) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let mut output = String::new();
    for byte in value.as_ref() {
        output.push(char::from(DIGITS[usize::from(byte >> 4)]));
        output.push(char::from(DIGITS[usize::from(byte & 0x0f)]));
    }
    output
}

fn header() -> TestResult<Vec<u8>> {
    let source = String::from_utf8(HEADER.to_vec())?;
    let border = concat!(
        r#"<hh:borderFill id="3" threeD="0" shadow="0" centerLine="NONE" breakCellSeparateLine="0">"#,
        r#"<hh:slash type="NONE" Crooked="0" isCounter="0"/>"#,
        r#"<hh:backSlash type="NONE" Crooked="0" isCounter="0"/>"#,
        r##"<hh:leftBorder type="SOLID" width="0.1 mm" color="#000000"/>"##,
        r##"<hh:rightBorder type="SOLID" width="0.1 mm" color="#000000"/>"##,
        r##"<hh:topBorder type="SOLID" width="0.1 mm" color="#000000"/>"##,
        r##"<hh:bottomBorder type="SOLID" width="0.1 mm" color="#000000"/>"##,
        r##"<hh:diagonal type="SOLID" width="0.1 mm" color="#000000"/>"##,
        "</hh:borderFill>"
    );
    Ok(source
        .replacen(
            "<hh:borderFills itemCnt=\"2\">",
            "<hh:borderFills itemCnt=\"3\">",
            1,
        )
        .replacen(
            "</hh:borderFills>",
            &format!("{border}</hh:borderFills>"),
            1,
        )
        .into_bytes())
}

fn row_height(row: usize) -> u32 {
    500 + u32::try_from(row).unwrap_or(u32::MAX) * 100
}

fn column_width(column: usize) -> u32 {
    800 + u32::try_from(column).unwrap_or(u32::MAX) * 400
}

fn cell(row: usize, column: usize, text_xml: &str) -> String {
    let text = if text_xml.is_empty() {
        "<hp:t/>".to_owned()
    } else {
        format!("<hp:t>{text_xml}</hp:t>")
    };
    format!(
        concat!(
            r#"<hp:tc name="" header="{header}" hasMargin="0" protect="0" editable="0" dirty="0" borderFillIDRef="3">"#,
            r#"<hp:cellAddr colAddr="{column}" rowAddr="{row}"/>"#,
            r#"<hp:cellSpan colSpan="1" rowSpan="1"/>"#,
            r#"<hp:cellSz width="{width}" height="{height}"/>"#,
            r#"<hp:cellMargin left="10" right="20" top="30" bottom="40"/>"#,
            r#"<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">"#,
            r#"<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0">{text}</hp:run></hp:p>"#,
            r#"</hp:subList></hp:tc>"#
        ),
        row = row,
        column = column,
        header = u8::from(row == 0),
        width = column_width(column),
        height = row_height(row),
        text = text,
    )
}

fn table_wrapper(
    native_id: u32,
    paragraph_id: u32,
    rows: usize,
    columns: usize,
    values: &[&str],
) -> String {
    assert_eq!(values.len(), rows * columns);
    let mut body = String::new();
    for row in 0..rows {
        body.push_str("<hp:tr>");
        for column in 0..columns {
            body.push_str(&cell(row, column, values[row * columns + column]));
        }
        body.push_str("</hp:tr>");
    }
    let width: u32 = (0..columns).map(column_width).sum();
    let height: u32 = (0..rows).map(row_height).sum();
    format!(
        concat!(
            r#"<hp:p id="{paragraph_id}" paraPrIDRef="2" styleIDRef="3"><hp:run charPrIDRef="4"><hp:ctrl>"#,
            r#"<hp:tbl id="{native_id}" zOrder="0" numberingType="TABLE" textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" pageBreak="TABLE" repeatHeader="1" rowCnt="{rows}" colCnt="{columns}" cellSpacing="0" borderFillIDRef="1" noAdjust="0">"#,
            r#"<hp:sz width="{width}" widthRelTo="ABSOLUTE" height="{height}" heightRelTo="ABSOLUTE" protect="0"/>"#,
            r#"<hp:pos treatAsChar="0" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP" horzAlign="LEFT" vertOffset="2000" horzOffset="1000"/>"#,
            r#"<hp:outMargin left="5" right="6" top="7" bottom="8"/><hp:inMargin left="9" right="10" top="11" bottom="12"/>"#,
            "{body}</hp:tbl></hp:ctrl><hp:t/></hp:run></hp:p>"
        ),
        paragraph_id = paragraph_id,
        native_id = native_id,
        rows = rows,
        columns = columns,
        width = width,
        height = height,
        body = body,
    )
}

fn paragraph(identifier: u32, text: &str) -> String {
    format!(
        r#"<hp:p id="{identifier}" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t>{text}</hp:t></hp:run></hp:p>"#
    )
}

fn complex_values() -> [&'static str; 6] {
    [
        "name",
        "amount",
        "한글,값",
        "7",
        "multi<hp:lineBreak/>line",
        "quote&quot;x",
    ]
}

fn complex_section() -> Vec<u8> {
    format!(
        r#"<hs:sec xmlns:hs="{SECTION_NS}" xmlns:hp="{PARAGRAPH_NS}">{}{target}{}{other}{}</hs:sec>"#,
        paragraph(10, "BEFORE"),
        paragraph(12, "BETWEEN"),
        paragraph(14, "AFTER"),
        target = table_wrapper(700, 11, 3, 2, &complex_values()),
        other = table_wrapper(701, 13, 1, 1, &["OTHER"]),
    )
    .into_bytes()
}

fn boundaries(count: usize, value: impl Fn(usize) -> u32) -> Vec<u32> {
    let mut output = vec![0];
    for index in 0..count {
        output.push(output.last().copied().unwrap_or(0) + value(index));
    }
    output
}

fn binding(rows: usize, columns: usize, values: &[&str]) -> TestResult<TableRulingHwpxBinding> {
    Ok(TableRulingHwpxBinding {
        table_id: id("source-table")?,
        row_boundaries_hwpunit: boundaries(rows, row_height),
        column_boundaries_hwpunit: boundaries(columns, column_width),
        cells: values
            .iter()
            .enumerate()
            .map(|(index, value)| {
                Ok(TableRulingHwpxCellBinding {
                    master_cell_id: id(&format!("source-cell-{index}"))?,
                    payload_block_ids: if value.is_empty() {
                        Vec::new()
                    } else {
                        vec![id(&format!("source-payload-{index}"))?]
                    },
                })
            })
            .collect::<TestResult<Vec<_>>>()?,
    })
}

fn read_context(
    header: &[u8],
    section: &[u8],
    rows: usize,
    columns: usize,
    values: &[&str],
    delimiter: TableDelimiter,
    line_ending: TableLineEnding,
) -> TestResult<hwpx_package::TableTableToTextHwpxReadback> {
    Ok(TableTableToTextHwpxReader::read_context(
        header,
        section,
        0,
        &binding(rows, columns, values)?,
        delimiter,
        line_ending,
        TableTableToTextHwpxLimits::default(),
    )?)
}

fn draft(
    source: &hwpx_package::TableTableToTextHwpxReadback,
    before_flow: char,
    after_flow: char,
) -> TestResult<TableTableToTextHwpxRequestDraft> {
    let limits = TableTableToTextHwpxLimits::default();
    Ok(TableTableToTextHwpxRequestDraft {
        schema_version: TABLE_TABLE_TO_TEXT_HWPX_SCHEMA_VERSION.to_owned(),
        table_ordinal: source.table_ordinal,
        expected_paragraph_ordinal: source.paragraph_ordinal,
        delimiter: source.delimiter,
        line_ending: source.line_ending,
        expected_header_sha256: hex(source.header_sha256),
        expected_section_sha256: hex(source.section_sha256),
        expected_wrapper_sha256: hex(source.wrapper_sha256),
        expected_wrapper_context_sha256: source.wrapper_context_sha256.clone(),
        expected_table_content_sha256: hex(source.ruling.table_content_sha256),
        expected_source_state_sha256: hex(source
            .ruling
            .state
            .canonical_sha256(limits.ruling.ruling)?),
        expected_source_grid_sha256: hex(source.ruling.grid.canonical_sha256()?),
        expected_text_grid_sha256: hex(source.text_grid.canonical_sha256(limits.text)?),
        expected_serialized_text_sha256: hex(source.serialized_text_sha256),
        expected_target_paragraph_sha256: hex(source.target_paragraph_sha256),
        expected_source_table_count: source.source_table_count,
        expected_document_flow_sha256: flow(before_flow),
        target_document_flow_sha256: flow(after_flow),
        output_text_block_id: id("output-text-block")?,
    })
}

fn admitted(
    source: &hwpx_package::TableTableToTextHwpxReadback,
    request_draft: TableTableToTextHwpxRequestDraft,
    current_flow: char,
) -> TestResult<(
    TableTableToTextHwpxRequest,
    hwpx_package::TableTableToTextHwpxPlan,
)> {
    let limits = TableTableToTextHwpxLimits::default();
    let request = TableTableToTextHwpxRequest::from_draft(
        request_draft,
        source,
        &flow(current_flow),
        limits,
    )?;
    let plan = TableTableToTextHwpxBuilder::build(&request, source, &flow(current_flow), limits)?;
    Ok((request, plan))
}

#[test]
fn converts_complete_grid_to_crlf_text_and_reopens_exact_paragraph() -> TestResult {
    let header = header()?;
    let section = complex_section();
    let values = complex_values();
    let source = read_context(
        &header,
        &section,
        3,
        2,
        &values,
        TableDelimiter::Comma,
        TableLineEnding::CrLf,
    )?;
    let immutable = source.clone();
    let (request, plan) = admitted(&source, draft(&source, 'a', 'b')?, 'a')?;
    let lowered = TableTableToTextHwpxLowerer::lower(
        &header,
        &section,
        &binding(3, 2, &values)?,
        TableDelimiter::Comma,
        TableLineEnding::CrLf,
        &flow('a'),
        &request,
        &plan,
        TableTableToTextHwpxLimits::default(),
    )?;
    assert_eq!(source, immutable);
    assert_eq!(plan.source_state(), &source.ruling.state);
    assert_eq!(plan.source_grid(), &source.ruling.grid);
    assert_eq!(
        lowered.text,
        "name,amount\r\n\"한글,값\",7\r\n\"multi\r\nline\",\"quote\"\"x\"".as_bytes()
    );
    assert_eq!(lowered.header, header);
    assert_eq!(lowered.receipt.source_table_count, 2);
    assert_eq!(lowered.receipt.target_table_count, 1);
    assert_eq!(lowered.receipt.master_cell_count, 6);
    assert_eq!(lowered.receipt.payload_block_count, 6);
    assert_eq!(lowered.receipt.formula_count, 0);
    let xml = String::from_utf8(lowered.section)?;
    assert!(xml.contains("BEFORE"));
    assert!(xml.contains("BETWEEN"));
    assert!(xml.contains("AFTER"));
    assert!(xml.contains("id=\"701\""));
    assert!(!xml.contains("id=\"700\""));
    assert!(xml.contains("<hp:lineBreak"));
    Ok(())
}

#[test]
fn empty_one_cell_tab_lf_boundary_is_exact() -> TestResult {
    let header = header()?;
    let values = [""];
    let section = format!(
        r#"<hs:sec xmlns:hs="{SECTION_NS}" xmlns:hp="{PARAGRAPH_NS}">{}</hs:sec>"#,
        table_wrapper(700, 11, 1, 1, &values)
    )
    .into_bytes();
    let source = read_context(
        &header,
        &section,
        1,
        1,
        &values,
        TableDelimiter::Tab,
        TableLineEnding::Lf,
    )?;
    let (request, plan) = admitted(&source, draft(&source, 'a', 'b')?, 'a')?;
    let lowered = TableTableToTextHwpxLowerer::lower(
        &header,
        &section,
        &binding(1, 1, &values)?,
        TableDelimiter::Tab,
        TableLineEnding::Lf,
        &flow('a'),
        &request,
        &plan,
        TableTableToTextHwpxLimits::default(),
    )?;
    assert!(lowered.text.is_empty());
    assert_eq!(lowered.receipt.target_table_count, 0);
    assert_eq!(lowered.receipt.payload_block_count, 0);
    assert!(String::from_utf8(lowered.section)?.contains("<hp:t/>"));
    Ok(())
}

#[test]
fn request_rejects_every_bound_digest_shape_flow_identity_and_json_tamper() -> TestResult {
    let header = header()?;
    let section = complex_section();
    let values = complex_values();
    let source = read_context(
        &header,
        &section,
        3,
        2,
        &values,
        TableDelimiter::Comma,
        TableLineEnding::CrLf,
    )?;
    let valid = draft(&source, 'a', 'b')?;
    for field in [
        "header",
        "section",
        "wrapper",
        "context",
        "content",
        "state",
        "grid",
        "text",
        "serialized",
        "paragraph",
        "flow",
    ] {
        let mut invalid = valid.clone();
        match field {
            "header" => invalid.expected_header_sha256 = flow('1'),
            "section" => invalid.expected_section_sha256 = flow('2'),
            "wrapper" => invalid.expected_wrapper_sha256 = flow('3'),
            "context" => invalid.expected_wrapper_context_sha256 = flow('4'),
            "content" => invalid.expected_table_content_sha256 = flow('5'),
            "state" => invalid.expected_source_state_sha256 = flow('6'),
            "grid" => invalid.expected_source_grid_sha256 = flow('7'),
            "text" => invalid.expected_text_grid_sha256 = flow('8'),
            "serialized" => invalid.expected_serialized_text_sha256 = flow('9'),
            "paragraph" => invalid.expected_target_paragraph_sha256 = flow('c'),
            "flow" => invalid.expected_document_flow_sha256 = flow('d'),
            _ => unreachable!(),
        }
        assert!(matches!(
            TableTableToTextHwpxRequest::from_draft(
                invalid,
                &source,
                &flow('a'),
                TableTableToTextHwpxLimits::default(),
            ),
            Err(TableTableToTextHwpxError::SourceBindingMismatch)
        ));
    }
    for mutation in [
        "ordinal",
        "count",
        "delimiter",
        "ending",
        "same_flow",
        "identity",
    ] {
        let mut invalid = valid.clone();
        match mutation {
            "ordinal" => invalid.expected_paragraph_ordinal += 1,
            "count" => invalid.expected_source_table_count += 1,
            "delimiter" => invalid.delimiter = TableDelimiter::Semicolon,
            "ending" => invalid.line_ending = TableLineEnding::Lf,
            "same_flow" => invalid.target_document_flow_sha256 = flow('a'),
            "identity" => invalid.output_text_block_id = source.ruling.state.table_id().clone(),
            _ => unreachable!(),
        }
        assert!(
            TableTableToTextHwpxRequest::from_draft(
                invalid,
                &source,
                &flow('a'),
                TableTableToTextHwpxLimits::default(),
            )
            .is_err()
        );
    }
    let json = serde_json::to_string(&valid)?;
    for invalid in [
        json.replacen(
            '{',
            r#"{"schema_version":"hwpx-agent.table-table-to-text-hwpx/v1","#,
            1,
        ),
        json.replacen('{', r#"{"unknown":true,"#, 1),
    ] {
        assert!(matches!(
            TableTableToTextHwpxRequest::from_json(
                invalid.as_bytes(),
                &source,
                &flow('a'),
                TableTableToTextHwpxLimits::default(),
            ),
            Err(TableTableToTextHwpxError::InvalidJson)
        ));
    }
    Ok(())
}

#[test]
fn lowerer_rechecks_source_binding_flow_and_plan() -> TestResult {
    let header = header()?;
    let section = complex_section();
    let values = complex_values();
    let source = read_context(
        &header,
        &section,
        3,
        2,
        &values,
        TableDelimiter::Comma,
        TableLineEnding::CrLf,
    )?;
    let (request, plan) = admitted(&source, draft(&source, 'a', 'b')?, 'a')?;
    let foreign_values = ["OTHER"];
    let foreign_section = format!(
        r#"<hs:sec xmlns:hs="{SECTION_NS}" xmlns:hp="{PARAGRAPH_NS}">{}</hs:sec>"#,
        table_wrapper(702, 20, 1, 1, &foreign_values)
    )
    .into_bytes();
    let foreign = read_context(
        &header,
        &foreign_section,
        1,
        1,
        &foreign_values,
        TableDelimiter::Comma,
        TableLineEnding::Lf,
    )?;
    let (_, foreign_plan) = admitted(&foreign, draft(&foreign, 'c', 'd')?, 'c')?;
    for result in [
        TableTableToTextHwpxLowerer::lower(
            &header,
            &foreign_section,
            &binding(1, 1, &foreign_values)?,
            TableDelimiter::Comma,
            TableLineEnding::CrLf,
            &flow('a'),
            &request,
            &plan,
            TableTableToTextHwpxLimits::default(),
        ),
        TableTableToTextHwpxLowerer::lower(
            &header,
            &section,
            &binding(3, 2, &values)?,
            TableDelimiter::Comma,
            TableLineEnding::CrLf,
            &flow('c'),
            &request,
            &plan,
            TableTableToTextHwpxLimits::default(),
        ),
        TableTableToTextHwpxLowerer::lower(
            &header,
            &section,
            &binding(3, 2, &values)?,
            TableDelimiter::Comma,
            TableLineEnding::CrLf,
            &flow('a'),
            &request,
            &foreign_plan,
            TableTableToTextHwpxLimits::default(),
        ),
    ] {
        assert!(result.is_err());
    }
    Ok(())
}

#[test]
fn merged_formula_multi_paragraph_opaque_and_nonempty_wrapper_fail_closed() -> TestResult {
    let header = header()?;
    let values = ["A"];
    let valid = format!(
        r#"<hs:sec xmlns:hs="{SECTION_NS}" xmlns:hp="{PARAGRAPH_NS}">{}</hs:sec>"#,
        table_wrapper(700, 11, 1, 1, &values)
    );
    let opaque = valid.replacen("<hp:t>A</hp:t>", "<hp:ctrl><hp:unknown/></hp:ctrl>", 1);
    let multiple = valid.replacen(
        "</hp:subList>",
        r#"<hp:p id="1" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t>B</hp:t></hp:run></hp:p></hp:subList>"#,
        1,
    );
    let visible_wrapper =
        valid.replacen("</hp:ctrl><hp:t/>", "</hp:ctrl><hp:t>unexpected</hp:t>", 1);
    let reordered_wrapper = valid.replacen("<hp:ctrl>", "<hp:t/><hp:ctrl>", 1).replacen(
        "</hp:ctrl><hp:t/>",
        "</hp:ctrl>",
        1,
    );
    let extra_control_child = valid.replacen("<hp:tbl", "<hp:t/><hp:tbl", 1);
    let formula = valid.replacen(
        "<hp:t>A</hp:t>",
        r#"<hp:fieldBegin id="7" type="FORMULA" name="=SUM(A1:A1)"/><hp:t>A</hp:t><hp:fieldEnd beginIDRef="7"/>"#,
        1,
    );
    for section in [
        opaque,
        multiple,
        visible_wrapper,
        reordered_wrapper,
        extra_control_child,
        formula,
    ] {
        assert!(
            TableTableToTextHwpxReader::read_context(
                &header,
                section.as_bytes(),
                0,
                &binding(1, 1, &values)?,
                TableDelimiter::Comma,
                TableLineEnding::Lf,
                TableTableToTextHwpxLimits::default(),
            )
            .is_err()
        );
    }
    let merged = valid
        .replacen("rowCnt=\"1\" colCnt=\"1\"", "rowCnt=\"1\" colCnt=\"2\"", 1)
        .replacen("colSpan=\"1\"", "colSpan=\"2\"", 1)
        .replacen("width=\"800\"", "width=\"2000\"", 2);
    let merged_binding = TableRulingHwpxBinding {
        table_id: id("source-table")?,
        row_boundaries_hwpunit: vec![0, 500],
        column_boundaries_hwpunit: vec![0, 800, 2000],
        cells: vec![TableRulingHwpxCellBinding {
            master_cell_id: id("source-cell-0")?,
            payload_block_ids: vec![id("source-payload-0")?],
        }],
    };
    assert!(
        TableTableToTextHwpxReader::read_context(
            &header,
            merged.as_bytes(),
            0,
            &merged_binding,
            TableDelimiter::Comma,
            TableLineEnding::Lf,
            TableTableToTextHwpxLimits::default(),
        )
        .is_err()
    );
    Ok(())
}

#[test]
fn bounds_and_debug_redact_content_hashes_and_ids() -> TestResult {
    let header = header()?;
    let section = complex_section();
    let values = complex_values();
    let source = read_context(
        &header,
        &section,
        3,
        2,
        &values,
        TableDelimiter::Comma,
        TableLineEnding::CrLf,
    )?;
    let (request, plan) = admitted(&source, draft(&source, 'a', 'b')?, 'a')?;
    let debug = format!("{source:?} {request:?} {plan:?}");
    for secret in [
        "한글,값",
        "source-table",
        "source-cell-0",
        "source-payload-0",
        "output-text-block",
        request.target_document_flow_sha256(),
        &source.wrapper_context_sha256,
        plan.serialized_text_sha256(),
    ] {
        assert!(!debug.contains(secret));
    }
    assert!(matches!(
        TableTableToTextHwpxRequest::from_json(
            &vec![b' '; 3 * 1024 * 1024],
            &source,
            &flow('a'),
            TableTableToTextHwpxLimits::default(),
        ),
        Err(TableTableToTextHwpxError::InputLimit)
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
    let header = header()?;
    let section = complex_section();
    let values = complex_values();
    let opaque = b"opaque-secret-bytes";
    let original = package(&header, &section, opaque)?;
    let source = read_context(
        &header,
        &section,
        3,
        2,
        &values,
        TableDelimiter::Comma,
        TableLineEnding::CrLf,
    )?;
    let (request, plan) = admitted(&source, draft(&source, 'a', 'b')?, 'a')?;
    let lowered = TableTableToTextHwpxLowerer::lower(
        &header,
        &section,
        &binding(3, 2, &values)?,
        TableDelimiter::Comma,
        TableLineEnding::CrLf,
        &flow('a'),
        &request,
        &plan,
        TableTableToTextHwpxLimits::default(),
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
    assert_eq!(Sha256::digest(&lowered.text), source.serialized_text_sha256);
    Ok(())
}
