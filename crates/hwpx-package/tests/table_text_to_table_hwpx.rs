use std::collections::BTreeMap;
use std::io::{Cursor, Write};

use domain_ir::{LogicalId, TableDelimiter};
use hwpx_package::{
    BoundedZipReader, Compression, PackageGraph, PackageGraphLimits, PackageLimits,
    TABLE_TEXT_TO_TABLE_HWPX_SCHEMA_VERSION, TableRulingHwpxBinding, TableRulingHwpxCellBinding,
    TableRulingHwpxReader, TableTextToTableHwpxBuilder, TableTextToTableHwpxError,
    TableTextToTableHwpxLimits, TableTextToTableHwpxLowerer, TableTextToTableHwpxReader,
    TableTextToTableHwpxRequest, TableTextToTableHwpxRequestDraft,
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
    let bytes = value.as_ref();
    let mut output = String::with_capacity(bytes.len().saturating_mul(2));
    for byte in bytes {
        output.push(char::from(DIGITS[usize::from(byte >> 4)]));
        output.push(char::from(DIGITS[usize::from(byte & 0x0f)]));
    }
    output
}

fn border_fill(id: u32, left: &str, right: &str, top: &str, bottom: &str) -> String {
    format!(
        concat!(
            r#"<hh:borderFill id="{id}" threeD="0" shadow="0" centerLine="NONE" breakCellSeparateLine="0">"#,
            r#"<hh:slash type="NONE" Crooked="0" isCounter="0"/>"#,
            r#"<hh:backSlash type="NONE" Crooked="0" isCounter="0"/>"#,
            r##"<hh:leftBorder type="{left}" width="0.1 mm" color="#000000"/>"##,
            r##"<hh:rightBorder type="{right}" width="0.1 mm" color="#000000"/>"##,
            r##"<hh:topBorder type="{top}" width="0.1 mm" color="#000000"/>"##,
            r##"<hh:bottomBorder type="{bottom}" width="0.1 mm" color="#000000"/>"##,
            r##"<hh:diagonal type="SOLID" width="0.1 mm" color="#000000"/>"##,
            r#"</hh:borderFill>"#
        ),
        id = id,
        left = left,
        right = right,
        top = top,
        bottom = bottom,
    )
}

fn header() -> TestResult<Vec<u8>> {
    let source = String::from_utf8(HEADER.to_vec())?;
    let additions = [
        border_fill(3, "SOLID", "DOT", "SOLID", "DOT"),
        border_fill(4, "DOT", "SOLID", "SOLID", "DOT"),
        border_fill(5, "SOLID", "DOT", "DOT", "SOLID"),
        border_fill(6, "DOT", "SOLID", "DOT", "SOLID"),
    ]
    .concat();
    Ok(source
        .replacen(
            "<hh:borderFills itemCnt=\"2\">",
            "<hh:borderFills itemCnt=\"6\">",
            1,
        )
        .replacen(
            "</hh:borderFills>",
            &format!("{additions}</hh:borderFills>"),
            1,
        )
        .into_bytes())
}

fn cell(row: u32, column: u32, width: u32, height: u32, border_fill: u32) -> String {
    format!(
        concat!(
            r#"<hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="0" borderFillIDRef="{border_fill}">"#,
            r#"<hp:cellAddr colAddr="{column}" rowAddr="{row}"/>"#,
            r#"<hp:cellSpan colSpan="1" rowSpan="1"/>"#,
            r#"<hp:cellSz width="{width}" height="{height}"/>"#,
            r#"<hp:cellMargin left="0" right="0" top="0" bottom="0"/>"#,
            r#"<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">"#,
            r#"<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t/></hp:run></hp:p>"#,
            r#"</hp:subList></hp:tc>"#
        ),
        border_fill = border_fill,
        column = column,
        row = row,
        width = width,
        height = height,
    )
}

fn template_wrapper(native_id: u32, nonempty: bool) -> String {
    let first = if nonempty {
        cell(0, 0, 800, 500, 3).replacen("<hp:t/>", "<hp:t>X</hp:t>", 1)
    } else {
        cell(0, 0, 800, 500, 3)
    };
    format!(
        concat!(
            r#"<hp:p id="900" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0">"#,
            r#"<hp:tbl id="{native_id}" zOrder="0" numberingType="TABLE" textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" pageBreak="CELL" repeatHeader="0" rowCnt="2" colCnt="2" cellSpacing="0" borderFillIDRef="1" noAdjust="0">"#,
            r#"<hp:sz width="2000" widthRelTo="ABSOLUTE" height="1100" heightRelTo="ABSOLUTE" protect="0"/>"#,
            r#"<hp:pos treatAsChar="0" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP" horzAlign="LEFT" vertOffset="2000" horzOffset="1000"/>"#,
            r#"<hp:outMargin left="0" right="0" top="0" bottom="0"/><hp:inMargin left="0" right="0" top="0" bottom="0"/>"#,
            "<hp:tr>{first}{top_right}</hp:tr><hp:tr>{bottom_left}{bottom_right}</hp:tr>",
            r#"</hp:tbl><hp:t/></hp:run></hp:p>"#
        ),
        native_id = native_id,
        first = first,
        top_right = cell(0, 1, 1200, 500, 4),
        bottom_left = cell(1, 0, 800, 600, 5),
        bottom_right = cell(1, 1, 1200, 600, 6),
    )
}

fn template_section(nonempty: bool) -> Vec<u8> {
    format!(
        r#"<hs:sec xmlns:hs="{SECTION_NS}" xmlns:hp="{PARAGRAPH_NS}">{}</hs:sec>"#,
        template_wrapper(700, nonempty)
    )
    .into_bytes()
}

fn paragraph(identifier: u32, text_xml: &str) -> String {
    format!(
        r#"<hp:p id="{identifier}" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t>{text_xml}</hp:t></hp:run></hp:p>"#
    )
}

fn source_section(text_xml: &str) -> Vec<u8> {
    format!(
        r#"<hs:sec xmlns:hs="{SECTION_NS}" xmlns:hp="{PARAGRAPH_NS}">{}{source}{}</hs:sec>"#,
        paragraph(10, "BEFORE"),
        paragraph(12, "AFTER"),
        source = paragraph(11, text_xml),
    )
    .into_bytes()
}

fn complex_source() -> Vec<u8> {
    source_section(concat!(
        "name,amount",
        "<hp:lineBreak/>",
        "&quot;한글,값&quot;,7",
        "<hp:lineBreak/>",
        "&quot;multi<hp:lineBreak/>line&quot;,"
    ))
}

fn template_binding() -> TestResult<TableRulingHwpxBinding> {
    Ok(TableRulingHwpxBinding {
        table_id: id("template-table")?,
        row_boundaries_hwpunit: vec![0, 500, 1100],
        column_boundaries_hwpunit: vec![0, 800, 2000],
        cells: ["template-a", "template-b", "template-c", "template-d"]
            .into_iter()
            .map(|value| {
                Ok(TableRulingHwpxCellBinding {
                    master_cell_id: id(value)?,
                    payload_block_ids: Vec::new(),
                })
            })
            .collect::<TestResult<Vec<_>>>()?,
    })
}

fn read_context(
    header: &[u8],
    section: &[u8],
    template: &[u8],
    delimiter: TableDelimiter,
) -> TestResult<hwpx_package::TableTextToTableHwpxReadback> {
    Ok(TableTextToTableHwpxReader::read_context(
        header,
        section,
        1,
        delimiter,
        template,
        0,
        &template_binding()?,
        TableTextToTableHwpxLimits::default(),
    )?)
}

fn draft(
    source: &hwpx_package::TableTextToTableHwpxReadback,
    before_flow: char,
    after_flow: char,
) -> TestResult<TableTextToTableHwpxRequestDraft> {
    let cells = source.text_grid.row_count() * source.text_grid.column_count();
    let mut payload_block_ids = Vec::with_capacity(cells);
    for (index, value) in source.text_grid.rows().iter().flatten().enumerate() {
        payload_block_ids.push(if value.is_empty() {
            None
        } else {
            Some(id(&format!("text-payload-{index}"))?)
        });
    }
    Ok(TableTextToTableHwpxRequestDraft {
        schema_version: TABLE_TEXT_TO_TABLE_HWPX_SCHEMA_VERSION.to_owned(),
        paragraph_ordinal: source.paragraph_ordinal,
        template_table_ordinal: source.template_table_ordinal,
        delimiter: source.delimiter,
        expected_header_sha256: hex(source.header_sha256),
        expected_section_sha256: hex(source.section_sha256),
        expected_template_section_sha256: hex(source.template_section_sha256),
        expected_template_state_sha256: hex(source
            .template
            .state
            .canonical_sha256(TableTextToTableHwpxLimits::default().create.ruling.ruling)?),
        expected_template_grid_sha256: hex(source.template.grid.canonical_sha256()?),
        expected_paragraph_sha256: hex(source.paragraph_sha256),
        expected_paragraph_context_sha256: source.paragraph_context_sha256.clone(),
        expected_text_grid_sha256: hex(source
            .text_grid
            .canonical_sha256(TableTextToTableHwpxLimits::default().text)?),
        expected_document_flow_sha256: flow(before_flow),
        target_document_flow_sha256: flow(after_flow),
        table_id: id("text-table")?,
        master_cell_ids: (0..cells)
            .map(|index| id(&format!("text-cell-{index}")))
            .collect::<TestResult<Vec<_>>>()?,
        payload_block_ids,
        row_heights_hwpunit: (0..source.text_grid.row_count())
            .map(|index| 400 + u32::try_from(index).unwrap_or(u32::MAX) * 100)
            .collect(),
        column_widths_hwpunit: (0..source.text_grid.column_count())
            .map(|index| 700 + u32::try_from(index).unwrap_or(u32::MAX) * 200)
            .collect(),
    })
}

fn admitted(
    source: &hwpx_package::TableTextToTableHwpxReadback,
    draft: TableTextToTableHwpxRequestDraft,
    current_flow: char,
) -> TestResult<(
    TableTextToTableHwpxRequest,
    hwpx_package::TableTextToTableHwpxPlan,
)> {
    let request = TableTextToTableHwpxRequest::from_draft(
        draft,
        source,
        &flow(current_flow),
        TableTextToTableHwpxLimits::default(),
    )?;
    let plan = TableTextToTableHwpxBuilder::build(
        &request,
        source,
        &flow(current_flow),
        TableTextToTableHwpxLimits::default(),
    )?;
    Ok((request, plan))
}

#[test]
fn converts_complete_quoted_multiline_grid_and_reopens_exactly() -> TestResult {
    let header = header()?;
    let section = complex_source();
    let template = template_section(false);
    let source = read_context(&header, &section, &template, TableDelimiter::Comma)?;
    assert_eq!(source.text_grid.rows()[1][0], "한글,값");
    assert_eq!(source.text_grid.rows()[2][0], "multi\nline");
    assert_eq!(source.text_grid.rows()[2][1], "");
    let immutable = source.clone();
    let (request, plan) = admitted(&source, draft(&source, 'a', 'b')?, 'a')?;
    let lowered = TableTextToTableHwpxLowerer::lower(
        &header,
        &section,
        &template,
        &template_binding()?,
        &flow('a'),
        &request,
        &plan,
        TableTextToTableHwpxLimits::default(),
    )?;
    let reopened = TableRulingHwpxReader::read_existing(
        &lowered.header,
        &lowered.section,
        lowered.table_ordinal,
        &lowered.binding,
        TableTextToTableHwpxLimits::default().create.ruling,
    )?;
    assert_eq!(source, immutable);
    assert_eq!(reopened.grid, *plan.target_grid());
    assert_eq!(reopened.state, *plan.target_state());
    assert_eq!(reopened.grid.rows(), 3);
    assert_eq!(reopened.grid.columns(), 2);
    assert_eq!(reopened.payload_block_count, 5);
    assert_eq!(reopened.formula_count, 0);
    assert_eq!(lowered.receipt.nonempty_cell_count, 5);
    assert!(lowered.receipt.page_split_preserved);
    let xml = String::from_utf8(lowered.section)?;
    assert!(xml.contains("BEFORE"));
    assert!(xml.contains("AFTER"));
    assert!(!xml.contains("name,amount"));
    assert!(!xml.contains("<hp:p xmlns:hp="));
    Ok(())
}

#[test]
fn one_cell_semicolon_boundary_and_all_empty_slots_are_exact() -> TestResult {
    let header = header()?;
    let section = source_section("only");
    let template = template_section(false);
    let source = read_context(&header, &section, &template, TableDelimiter::Semicolon)?;
    let (request, plan) = admitted(&source, draft(&source, 'a', 'b')?, 'a')?;
    let lowered = TableTextToTableHwpxLowerer::lower(
        &header,
        &section,
        &template,
        &template_binding()?,
        &flow('a'),
        &request,
        &plan,
        TableTextToTableHwpxLimits::default(),
    )?;
    assert_eq!(plan.target_grid().rows(), 1);
    assert_eq!(plan.target_grid().columns(), 1);
    assert_eq!(lowered.receipt.payload_block_count, 1);
    assert_eq!(lowered.receipt.target_table_count, 1);
    Ok(())
}

#[test]
fn request_rejects_all_bound_state_identity_flow_and_json_tampering() -> TestResult {
    let header = header()?;
    let section = complex_source();
    let template = template_section(false);
    let source = read_context(&header, &section, &template, TableDelimiter::Comma)?;
    let valid = draft(&source, 'a', 'b')?;
    for field in [
        "header",
        "section",
        "template",
        "template_state",
        "template_grid",
        "paragraph",
        "context",
        "text_grid",
        "flow",
    ] {
        let mut tampered = valid.clone();
        match field {
            "header" => tampered.expected_header_sha256 = flow('1'),
            "section" => tampered.expected_section_sha256 = flow('2'),
            "template" => tampered.expected_template_section_sha256 = flow('3'),
            "template_state" => tampered.expected_template_state_sha256 = flow('4'),
            "template_grid" => tampered.expected_template_grid_sha256 = flow('5'),
            "paragraph" => tampered.expected_paragraph_sha256 = flow('6'),
            "context" => tampered.expected_paragraph_context_sha256 = flow('7'),
            "text_grid" => tampered.expected_text_grid_sha256 = flow('8'),
            "flow" => tampered.expected_document_flow_sha256 = flow('9'),
            _ => unreachable!(),
        }
        assert!(matches!(
            TableTextToTableHwpxRequest::from_draft(
                tampered,
                &source,
                &flow('a'),
                TableTextToTableHwpxLimits::default(),
            ),
            Err(TableTextToTableHwpxError::SourceBindingMismatch)
        ));
    }
    let mut same_flow = valid.clone();
    same_flow.target_document_flow_sha256 = flow('a');
    assert!(matches!(
        TableTextToTableHwpxRequest::from_draft(
            same_flow,
            &source,
            &flow('a'),
            TableTextToTableHwpxLimits::default(),
        ),
        Err(TableTextToTableHwpxError::FlowBindingMismatch)
    ));
    for mutation in ["master", "payload", "slot"] {
        let mut invalid = valid.clone();
        match mutation {
            "master" => invalid.master_cell_ids[0] = invalid.table_id.clone(),
            "payload" => invalid.payload_block_ids[0] = Some(invalid.master_cell_ids[1].clone()),
            "slot" => invalid.payload_block_ids[0] = None,
            _ => unreachable!(),
        }
        assert!(matches!(
            TableTextToTableHwpxRequest::from_draft(
                invalid,
                &source,
                &flow('a'),
                TableTextToTableHwpxLimits::default(),
            ),
            Err(TableTextToTableHwpxError::IdentityConflict)
        ));
    }
    let json = serde_json::to_string(&valid)?;
    for invalid in [
        json.replacen(
            '{',
            r#"{"schema_version":"hwpx-agent.table-text-to-table-hwpx/v1","#,
            1,
        ),
        json.replacen('{', r#"{"unknown":true,"#, 1),
    ] {
        assert!(matches!(
            TableTextToTableHwpxRequest::from_json(
                invalid.as_bytes(),
                &source,
                &flow('a'),
                TableTextToTableHwpxLimits::default(),
            ),
            Err(TableTextToTableHwpxError::InvalidJson)
        ));
    }
    Ok(())
}

#[test]
fn lowerer_rechecks_source_template_flow_and_plan() -> TestResult {
    let header = header()?;
    let section = complex_source();
    let template = template_section(false);
    let source = read_context(&header, &section, &template, TableDelimiter::Comma)?;
    let (request, plan) = admitted(&source, draft(&source, 'a', 'b')?, 'a')?;
    let simple_section = source_section("x,y");
    let simple_source = read_context(&header, &simple_section, &template, TableDelimiter::Comma)?;
    let (_, foreign_plan) = admitted(&simple_source, draft(&simple_source, 'c', 'd')?, 'c')?;
    for result in [
        TableTextToTableHwpxLowerer::lower(
            &header,
            &simple_section,
            &template,
            &template_binding()?,
            &flow('a'),
            &request,
            &plan,
            TableTextToTableHwpxLimits::default(),
        ),
        TableTextToTableHwpxLowerer::lower(
            &header,
            &section,
            &template,
            &template_binding()?,
            &flow('c'),
            &request,
            &plan,
            TableTextToTableHwpxLimits::default(),
        ),
        TableTextToTableHwpxLowerer::lower(
            &header,
            &section,
            &template,
            &template_binding()?,
            &flow('a'),
            &request,
            &foreign_plan,
            TableTextToTableHwpxLimits::default(),
        ),
    ] {
        assert!(result.is_err());
    }
    Ok(())
}

#[test]
fn malformed_or_opaque_text_and_nonblank_template_fail_closed() -> TestResult {
    let header = header()?;
    let template = template_section(false);
    for section in [
        source_section("a,b<hp:lineBreak/>c"),
        source_section("a<hp:ctrl><hp:unknown/></hp:ctrl>,b"),
        source_section(concat!(
            "a,",
            "</hp:t><hp:fieldBegin id=\"7\" type=\"FORMULA\" name=\"f\"/>",
            "<hp:t>b</hp:t><hp:fieldEnd beginIDRef=\"7\"/><hp:t>"
        )),
    ] {
        assert!(read_context(&header, &section, &template, TableDelimiter::Comma).is_err());
    }
    assert!(
        read_context(
            &header,
            &complex_source(),
            &template_section(true),
            TableDelimiter::Comma,
        )
        .is_err()
    );
    Ok(())
}

#[test]
fn control_wrapped_table_template_fails_closed() -> TestResult {
    let header = header()?;
    let template = String::from_utf8(template_section(false))?
        .replace(
            "<hp:run charPrIDRef=\"0\"><hp:tbl",
            "<hp:run charPrIDRef=\"0\"><hp:ctrl><hp:tbl",
        )
        .replace(
            "</hp:tbl><hp:t/></hp:run>",
            "</hp:tbl></hp:ctrl><hp:t/></hp:run>",
        )
        .into_bytes();
    assert!(read_context(&header, &complex_source(), &template, TableDelimiter::Comma,).is_err());
    Ok(())
}

#[test]
fn bounds_and_debug_redact_hashes_ids_and_text() -> TestResult {
    let header = header()?;
    let section = complex_source();
    let template = template_section(false);
    let source = read_context(&header, &section, &template, TableDelimiter::Comma)?;
    let valid = draft(&source, 'a', 'b')?;
    let (request, plan) = admitted(&source, valid, 'a')?;
    let debug = format!("{source:?} {request:?} {plan:?}");
    for secret in [
        "한글,값",
        "text-table",
        "text-cell-0",
        "text-payload-0",
        request.target_document_flow_sha256(),
        &hex(source.header_sha256),
        &source.paragraph_context_sha256,
    ] {
        assert!(!debug.contains(secret));
    }
    assert!(matches!(
        TableTextToTableHwpxRequest::from_json(
            &vec![b' '; 70 * 1024 * 1024],
            &source,
            &flow('a'),
            TableTextToTableHwpxLimits::default(),
        ),
        Err(TableTextToTableHwpxError::InputLimit)
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
    let mut parts = BTreeMap::new();
    for index in 0..archive.len() {
        let mut entry = archive.by_index(index)?;
        let mut bytes = Vec::new();
        std::io::Read::read_to_end(&mut entry, &mut bytes)?;
        if parts.insert(entry.name().to_owned(), bytes).is_some() {
            return Err("duplicate package path".into());
        }
    }
    Ok(parts)
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
fn closed_package_preserves_every_nontarget_part_and_graph() -> TestResult {
    let header = header()?;
    let section = complex_source();
    let template = template_section(false);
    let source = read_context(&header, &section, &template, TableDelimiter::Comma)?;
    let (request, plan) = admitted(&source, draft(&source, 'a', 'b')?, 'a')?;
    let lowered = TableTextToTableHwpxLowerer::lower(
        &header,
        &section,
        &template,
        &template_binding()?,
        &flow('a'),
        &request,
        &plan,
        TableTextToTableHwpxLimits::default(),
    )?;
    let opaque = b"PRIVATE-OPAQUE-UNTOUCHED";
    let input = package(&header, &section, opaque)?;
    let output = replace_target_parts(&input, &lowered.header, &lowered.section)?;
    let input_parts = expanded_parts(&input)?;
    let output_parts = expanded_parts(&output)?;
    assert_eq!(
        input_parts.keys().collect::<Vec<_>>(),
        output_parts.keys().collect::<Vec<_>>()
    );
    for (path, bytes) in &input_parts {
        if !matches!(
            path.as_str(),
            "Contents/header.xml" | "Contents/section0.xml"
        ) {
            assert_eq!(output_parts.get(path), Some(bytes));
        }
    }
    assert_eq!(output_parts["Contents/opaque.bin"], opaque);
    let mut reader = BoundedZipReader::open(Cursor::new(&output), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    assert!(!graph.parts.is_empty());
    assert_eq!(
        Sha256::digest(&input_parts["Contents/opaque.bin"]),
        Sha256::digest(opaque)
    );
    Ok(())
}
