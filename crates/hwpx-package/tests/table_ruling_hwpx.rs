use std::collections::BTreeMap;
use std::io::{Cursor, Write};

use domain_ir::{
    CellCoordinate, ContentPreservationPolicy, FormulaLimits, LogicalId,
    TABLE_RULING_SCHEMA_VERSION, TableGrid, TableGridLimits, TableRulingAxis, TableRulingBuilder,
    TableRulingDiagonalDirection, TableRulingFormulaPolicy, TableRulingLimits,
    TableRulingOperation, TableRulingPlan, TableRulingRequest, TableRulingRequestDraft,
    TableRulingState, TableRulingStroke,
};
use hwpx_package::{
    BoundedZipReader, Compression, PackageGraph, PackageGraphLimits, PackageLimits,
    TABLE_MERGE_SPLIT_HWPX_SCHEMA_VERSION, TABLE_RULING_HWPX_PROFILE_ID, TableFormulaHwpxLimits,
    TableFormulaHwpxReader, TableMergeSplitHwpxBuilder, TableMergeSplitHwpxError,
    TableMergeSplitHwpxLimits, TableMergeSplitHwpxLowerer, TableMergeSplitHwpxOperation,
    TableMergeSplitHwpxPartBinding, TableMergeSplitHwpxPlan, TableMergeSplitHwpxReadback,
    TableMergeSplitHwpxReader, TableMergeSplitHwpxRequest, TableMergeSplitHwpxRequestDraft,
    TablePaginationHwpxLimits, TablePaginationHwpxReader, TableRulingHwpxBinding,
    TableRulingHwpxCellBinding, TableRulingHwpxError, TableRulingHwpxLimits,
    TableRulingHwpxLowerer, TableRulingHwpxReader,
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
  </opf:manifest>
  <opf:spine><opf:itemref idref="section0" linear="yes"/></opf:spine>
</opf:package>"#;

fn id(value: &str) -> Result<LogicalId, Box<dyn std::error::Error>> {
    Ok(LogicalId::parse(value)?)
}

fn header() -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    let text = String::from_utf8(HEADER.to_vec())?;
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
    Ok(text
        .replacen(
            "<hh:borderFills itemCnt=\"2\">",
            "<hh:borderFills itemCnt=\"4\">",
            1,
        )
        .replacen(
            "</hh:borderFills>",
            &format!("{solid}{slash}</hh:borderFills>"),
            1,
        )
        .into_bytes())
}

fn header_with_dot() -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    let text = String::from_utf8(header()?)?;
    let dot = concat!(
        r#"<hh:borderFill id="5" threeD="0" shadow="0" centerLine="NONE" breakCellSeparateLine="0">"#,
        r#"<hh:slash type="NONE" Crooked="0" isCounter="0"/>"#,
        r#"<hh:backSlash type="NONE" Crooked="0" isCounter="0"/>"#,
        r##"<hh:leftBorder type="DOT" width="0.1 mm" color="#000000"/>"##,
        r##"<hh:rightBorder type="DOT" width="0.1 mm" color="#000000"/>"##,
        r##"<hh:topBorder type="DOT" width="0.1 mm" color="#000000"/>"##,
        r##"<hh:bottomBorder type="DOT" width="0.1 mm" color="#000000"/>"##,
        r##"<hh:diagonal type="SOLID" width="0.1 mm" color="#000000"/>"##,
        r#"</hh:borderFill>"#,
    );
    Ok(text
        .replacen(
            "<hh:borderFills itemCnt=\"4\">",
            "<hh:borderFills itemCnt=\"5\">",
            1,
        )
        .replacen("</hh:borderFills>", &format!("{dot}</hh:borderFills>"), 1)
        .into_bytes())
}

fn header_with_back_slash() -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    let text = String::from_utf8(header()?)?;
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
    Ok(text
        .replacen(
            "<hh:borderFills itemCnt=\"4\">",
            "<hh:borderFills itemCnt=\"5\">",
            1,
        )
        .replacen(
            "</hh:borderFills>",
            &format!("{back_slash}</hh:borderFills>"),
            1,
        )
        .into_bytes())
}

fn text_paragraph(value: &str) -> String {
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

#[allow(clippy::too_many_arguments)]
fn cell(
    row: u32,
    column: u32,
    row_span: u32,
    column_span: u32,
    width: u32,
    height: u32,
    border_fill: u32,
    payload: &str,
) -> String {
    format!(
        concat!(
            r#"<hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="0" borderFillIDRef="{border_fill}">"#,
            r#"<hp:cellAddr colAddr="{column}" rowAddr="{row}"/>"#,
            r#"<hp:cellSpan colSpan="{column_span}" rowSpan="{row_span}"/>"#,
            r#"<hp:cellSz width="{width}" height="{height}"/>"#,
            r#"<hp:cellMargin left="0" right="0" top="0" bottom="0"/>"#,
            r#"<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">"#,
            "{payload}</hp:subList></hp:tc>"
        ),
        border_fill = border_fill,
        column = column,
        row = row,
        column_span = column_span,
        row_span = row_span,
        width = width,
        height = height,
        payload = payload,
    )
}

fn table(rows: &[Vec<String>], row_count: u32, column_count: u32) -> Vec<u8> {
    let mut body = String::new();
    for cells in rows {
        body.push_str("<hp:tr>");
        for cell in cells {
            body.push_str(cell);
        }
        body.push_str("</hp:tr>");
    }
    format!(
        concat!(
            r#"<hs:sec xmlns:hs="{SECTION_NS}" xmlns:hp="{PARAGRAPH_NS}">"#,
            r#"<hp:tbl id="700" zOrder="0" numberingType="TABLE" textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" pageBreak="CELL" repeatHeader="0" rowCnt="{row_count}" colCnt="{column_count}" cellSpacing="0" borderFillIDRef="1" noAdjust="0">"#,
            r#"<hp:sz width="2000" widthRelTo="ABSOLUTE" height="1000" heightRelTo="ABSOLUTE" protect="0"/>"#,
            r#"<hp:pos treatAsChar="0" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP" horzAlign="LEFT" vertOffset="2000" horzOffset="1000"/>"#,
            r#"<hp:outMargin left="0" right="0" top="0" bottom="0"/>"#,
            r#"<hp:inMargin left="0" right="0" top="0" bottom="0"/>"#,
            "{body}</hp:tbl></hs:sec>"
        ),
        SECTION_NS = SECTION_NS,
        PARAGRAPH_NS = PARAGRAPH_NS,
        row_count = row_count,
        column_count = column_count,
        body = body,
    )
    .into_bytes()
}

fn ordinary_section() -> Vec<u8> {
    table(
        &[
            vec![
                cell(0, 0, 1, 1, 1000, 500, 3, &text_paragraph("A")),
                cell(0, 1, 1, 1, 1000, 500, 3, &text_paragraph("B")),
            ],
            vec![
                cell(1, 0, 1, 1, 1000, 500, 3, &text_paragraph("C")),
                cell(1, 1, 1, 1, 1000, 500, 3, &text_paragraph("D")),
            ],
        ],
        2,
        2,
    )
}

fn formula_section() -> Vec<u8> {
    table(
        &[
            vec![
                cell(0, 0, 1, 1, 1000, 500, 3, &text_paragraph("1")),
                cell(0, 1, 1, 1, 1000, 500, 3, &text_paragraph("2")),
            ],
            vec![
                cell(1, 0, 1, 1, 1000, 500, 3, &text_paragraph("7")),
                cell(1, 1, 1, 1, 1000, 500, 3, formula_paragraph()),
            ],
        ],
        2,
        2,
    )
}

fn merged_section() -> Vec<u8> {
    table(
        &[
            vec![cell(0, 0, 1, 2, 2000, 500, 3, &text_paragraph("MERGED"))],
            vec![
                cell(1, 0, 1, 1, 1000, 500, 3, &text_paragraph("7")),
                cell(1, 1, 1, 1, 1000, 500, 3, &text_paragraph("8")),
            ],
        ],
        2,
        2,
    )
}

fn merged_four_payload_section() -> Vec<u8> {
    let payload = ["A", "B", "C", "D"]
        .into_iter()
        .map(text_paragraph)
        .collect::<String>();
    table(
        &[vec![cell(0, 0, 2, 2, 2000, 1000, 3, &payload)], vec![]],
        2,
        2,
    )
}

fn single_section() -> Vec<u8> {
    table(
        &[vec![cell(
            0,
            0,
            1,
            1,
            2000,
            1000,
            3,
            &text_paragraph("ONLY"),
        )]],
        1,
        1,
    )
}

fn table_fragment(section: Vec<u8>) -> Result<String, Box<dyn std::error::Error>> {
    let source = String::from_utf8(section)?;
    let start = source.find("<hp:tbl ").ok_or("table start missing")?;
    let end = source
        .find("</hp:tbl>")
        .and_then(|value| value.checked_add("</hp:tbl>".len()))
        .ok_or("table end missing")?;
    Ok(source
        .get(start..end)
        .ok_or("table span invalid")?
        .to_owned())
}

fn empty_wrapped_template_section() -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    let table = table_fragment(table(
        &[vec![cell(
            0,
            0,
            1,
            1,
            2000,
            1000,
            3,
            r#"<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t/></hp:run></hp:p>"#,
        )]],
        1,
        1,
    ))?;
    Ok(format!(
        concat!(
            r#"<hs:sec xmlns:hs="{SECTION_NS}" xmlns:hp="{PARAGRAPH_NS}">"#,
            r#"<hp:p id="880" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:ctrl>"#,
            "{table}</hp:ctrl><hp:t/></hp:run></hp:p></hs:sec>"
        ),
        SECTION_NS = SECTION_NS,
        PARAGRAPH_NS = PARAGRAPH_NS,
        table = table,
    )
    .into_bytes())
}

fn insertion_section() -> Vec<u8> {
    format!(
        r#"<hs:sec xmlns:hs="{SECTION_NS}" xmlns:hp="{PARAGRAPH_NS}">{}{}{} </hs:sec>"#,
        text_paragraph("BEFORE"),
        text_paragraph(""),
        text_paragraph("AFTER"),
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

fn package(header: &[u8], section: &[u8]) -> Result<Vec<u8>, zip::result::ZipError> {
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
    ])
}

fn replace_header_and_section(source: &[u8], header: &[u8], section: &[u8]) -> TestResult<Vec<u8>> {
    let mut reader = BoundedZipReader::open(Cursor::new(source), PackageLimits::default())?;
    let entries = reader.entries().to_vec();
    let mut parts = Vec::new();
    parts.try_reserve_exact(entries.len())?;
    let mut header_replacements = 0_usize;
    let mut section_replacements = 0_usize;
    for entry in entries {
        let path = entry.path.as_str().to_owned();
        let method = match entry.compression {
            Compression::Stored => CompressionMethod::Stored,
            Compression::Deflated => CompressionMethod::Deflated,
        };
        let bytes = match path.as_str() {
            "Contents/header.xml" => {
                header_replacements += 1;
                header.to_vec()
            }
            "Contents/section0.xml" => {
                section_replacements += 1;
                section.to_vec()
            }
            _ => reader.read_entry(entry.index)?,
        };
        parts.push((path, bytes, method));
    }
    if header_replacements != 1 || section_replacements != 1 {
        return Err("part replacement cardinality mismatch".into());
    }
    Ok(archive(parts)?)
}

fn inspect_package(source: &[u8]) -> TestResult<(PackageGraph, Vec<u8>, Vec<u8>)> {
    let mut reader = BoundedZipReader::open(Cursor::new(source), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    let header_index = reader
        .entries()
        .iter()
        .find(|entry| entry.path.as_str() == "Contents/header.xml")
        .map(|entry| entry.index)
        .ok_or("header part missing")?;
    let section_index = reader
        .entries()
        .iter()
        .find(|entry| entry.path.as_str() == "Contents/section0.xml")
        .map(|entry| entry.index)
        .ok_or("section part missing")?;
    let header = reader.read_entry(header_index)?;
    let section = reader.read_entry(section_index)?;
    Ok((graph, header, section))
}

fn part_hashes(graph: &PackageGraph) -> BTreeMap<String, [u8; 32]> {
    graph
        .parts
        .iter()
        .map(|part| (part.path.as_str().to_owned(), part.raw_sha256))
        .collect()
}

fn assert_package_preservation(
    source: &PackageGraph,
    source_hashes: BTreeMap<String, [u8; 32]>,
    target: &PackageGraph,
) -> TestResult {
    assert_eq!(source.package_document, target.package_document);
    assert_eq!(source.relationships, target.relationships);
    assert_eq!(source.spine, target.spine);
    let target_hashes = part_hashes(target);
    for (path, source_sha256) in source_hashes {
        let target_sha256 = target_hashes.get(&path).ok_or("target part missing")?;
        if matches!(
            path.as_str(),
            "Contents/header.xml" | "Contents/section0.xml"
        ) {
            assert_ne!(&source_sha256, target_sha256, "part did not change: {path}");
        } else {
            assert_eq!(&source_sha256, target_sha256, "part changed: {path}");
        }
    }
    Ok(())
}

fn assert_section_only_package_change(
    source: &PackageGraph,
    source_hashes: BTreeMap<String, [u8; 32]>,
    target: &PackageGraph,
) -> TestResult {
    assert_eq!(source.package_document, target.package_document);
    assert_eq!(source.relationships, target.relationships);
    assert_eq!(source.spine, target.spine);
    let target_hashes = part_hashes(target);
    for (path, source_sha256) in source_hashes {
        let target_sha256 = target_hashes.get(&path).ok_or("target part missing")?;
        if path == "Contents/section0.xml" {
            assert_ne!(&source_sha256, target_sha256);
        } else {
            assert_eq!(&source_sha256, target_sha256, "part changed: {path}");
        }
    }
    Ok(())
}

fn binding(payload_counts: &[usize]) -> Result<TableRulingHwpxBinding, Box<dyn std::error::Error>> {
    binding_with_boundaries(payload_counts, vec![0, 500, 1000], vec![0, 1000, 2000])
}

fn binding_with_boundaries(
    payload_counts: &[usize],
    row_boundaries_hwpunit: Vec<u32>,
    column_boundaries_hwpunit: Vec<u32>,
) -> Result<TableRulingHwpxBinding, Box<dyn std::error::Error>> {
    let mut cells = Vec::new();
    for (index, count) in payload_counts.iter().copied().enumerate() {
        let mut payload_block_ids = Vec::new();
        for payload_index in 0..count {
            payload_block_ids.push(id(&format!("payload-{index}-{payload_index}"))?);
        }
        cells.push(TableRulingHwpxCellBinding {
            master_cell_id: id(&format!("cell-{index}"))?,
            payload_block_ids,
        });
    }
    Ok(TableRulingHwpxBinding {
        table_id: id("secret-table")?,
        row_boundaries_hwpunit,
        column_boundaries_hwpunit,
        cells,
    })
}

fn binding_from_state(
    state: &TableRulingState,
    grid: &TableGrid,
) -> Result<TableRulingHwpxBinding, Box<dyn std::error::Error>> {
    let mut cells = Vec::new();
    for span in grid.master_cells() {
        let cell = state
            .cell(&span.master_cell_id)
            .ok_or("missing state cell")?;
        cells.push(TableRulingHwpxCellBinding {
            master_cell_id: span.master_cell_id.clone(),
            payload_block_ids: cell
                .payload()
                .iter()
                .map(|block| block.block_id.clone())
                .collect(),
        });
    }
    Ok(TableRulingHwpxBinding {
        table_id: state.table_id().clone(),
        row_boundaries_hwpunit: state.row_boundaries_hwpunit().to_vec(),
        column_boundaries_hwpunit: state.column_boundaries_hwpunit().to_vec(),
        cells,
    })
}

fn grid_from_plan(plan: &TableRulingPlan) -> Result<TableGrid, Box<dyn std::error::Error>> {
    Ok(TableGrid::new(
        plan.after_grid().rows(),
        plan.after_grid().columns(),
        plan.after_grid().master_cells().to_vec(),
        TableGridLimits::default(),
    )?)
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

fn build_plan(
    state: &TableRulingState,
    grid: &TableGrid,
    operation: TableRulingOperation,
) -> Result<TableRulingPlan, Box<dyn std::error::Error>> {
    let flow = digest('f');
    let request = TableRulingRequest::from_draft(
        TableRulingRequestDraft {
            schema_version: TABLE_RULING_SCHEMA_VERSION.to_owned(),
            table_id: state.table_id().clone(),
            expected_state_sha256: Some(hex(state.canonical_sha256(TableRulingLimits::default())?)),
            expected_grid_sha256: Some(hex(grid.canonical_sha256()?)),
            expected_document_flow_sha256: flow.clone(),
            operation,
        },
        Some(state),
        Some(grid),
        &flow,
        TableRulingLimits::default(),
    )?;
    Ok(TableRulingBuilder::build(
        &request,
        Some(state),
        Some(grid),
        &flow,
        TableGridLimits::default(),
        FormulaLimits::default(),
        TableRulingLimits::default(),
    )?)
}

fn build_outer_plan(
    template: &hwpx_package::TableRulingHwpxReadback,
    insertion_context_sha256: String,
) -> Result<TableRulingPlan, Box<dyn std::error::Error>> {
    let flow = digest('f');
    let line_sha256 = template
        .state
        .edge(TableRulingAxis::Horizontal, 0, 0)
        .and_then(|edge| edge.line_sha256.clone())
        .ok_or("template outer line missing")?;
    let cell = template
        .state
        .cells()
        .first()
        .ok_or("template cell missing")?;
    let request = TableRulingRequest::from_draft(
        TableRulingRequestDraft {
            schema_version: TABLE_RULING_SCHEMA_VERSION.to_owned(),
            table_id: template.state.table_id().clone(),
            expected_state_sha256: None,
            expected_grid_sha256: None,
            expected_document_flow_sha256: flow.clone(),
            operation: TableRulingOperation::DrawOuterRectangle {
                frame: template.state.frame(),
                initial_master_cell_id: cell.master_cell_id().clone(),
                table_properties_sha256: template.state.table_properties_sha256().to_owned(),
                initial_cell_properties: cell.properties().clone(),
                line_sha256,
                insertion_context_sha256,
            },
        },
        None,
        None,
        &flow,
        TableRulingLimits::default(),
    )?;
    Ok(TableRulingBuilder::build(
        &request,
        None,
        None,
        &flow,
        TableGridLimits::default(),
        FormulaLimits::default(),
        TableRulingLimits::default(),
    )?)
}

fn build_merge_split_plan(
    source: &TableMergeSplitHwpxReadback,
    operation: TableMergeSplitHwpxOperation,
) -> Result<
    (
        TableMergeSplitHwpxRequest,
        TableMergeSplitHwpxPlan,
        TableMergeSplitHwpxPartBinding,
    ),
    Box<dyn std::error::Error>,
> {
    let limits = TableMergeSplitHwpxLimits::default();
    let flow = digest('f');
    let request = TableMergeSplitHwpxRequest::from_draft(
        merge_split_request_draft(source, operation)?,
        source,
        &flow,
        limits,
    )?;
    let plan = TableMergeSplitHwpxBuilder::build(&request, source, &flow, limits)?;
    let part_binding =
        TableMergeSplitHwpxPartBinding::from_readback(source, &request, &plan, flow, limits)?;
    Ok((request, plan, part_binding))
}

fn merge_split_request_draft(
    source: &TableMergeSplitHwpxReadback,
    operation: TableMergeSplitHwpxOperation,
) -> Result<TableMergeSplitHwpxRequestDraft, Box<dyn std::error::Error>> {
    let limits = TableMergeSplitHwpxLimits::default();
    Ok(TableMergeSplitHwpxRequestDraft {
        schema_version: TABLE_MERGE_SPLIT_HWPX_SCHEMA_VERSION.to_owned(),
        table_id: source.ruling.state.table_id().clone(),
        expected_state_sha256: hex(source.ruling.state.canonical_sha256(limits.ruling.ruling)?),
        expected_grid_sha256: hex(source.ruling.grid.canonical_sha256()?),
        expected_content_sha256: hex(source.content_state_sha256),
        expected_document_flow_sha256: digest('f'),
        operation,
    })
}

fn assert_merge_request_canonicalization(
    source: &TableMergeSplitHwpxReadback,
    selected_slots: &[CellCoordinate],
    request: &TableMergeSplitHwpxRequest,
    limits: &TableMergeSplitHwpxLimits,
) -> TestResult {
    let reordered = TableMergeSplitHwpxRequest::from_draft(
        merge_split_request_draft(
            source,
            TableMergeSplitHwpxOperation::Merge {
                selected_slots: selected_slots.iter().rev().copied().collect(),
                content_policy: ContentPreservationPolicy::Concatenate,
            },
        )?,
        source,
        &digest('f'),
        *limits,
    )?;
    assert_eq!(
        request.canonical_json(*limits)?,
        reordered.canonical_json(*limits)?
    );
    Ok(())
}

fn assert_diagonal_round_trip(
    header: &[u8],
    section: &[u8],
    binding: &TableRulingHwpxBinding,
    source: &hwpx_package::TableRulingHwpxReadback,
    direction: TableRulingDiagonalDirection,
    line_sha256: String,
) -> TestResult {
    let master_cell_id = source.state.cells()[0].master_cell_id().clone();
    let draw = build_plan(
        &source.state,
        &source.grid,
        TableRulingOperation::DrawDiagonal {
            master_cell_id: master_cell_id.clone(),
            direction,
            line_sha256,
        },
    )?;
    let drawn = TableRulingHwpxLowerer::lower_existing(
        header,
        section,
        0,
        binding,
        &source.state,
        &source.grid,
        &draw,
        &digest('f'),
        TableRulingHwpxLimits::default(),
    )?;
    assert_eq!(drawn.receipt.added_border_fill_count, 0);
    assert_eq!(drawn.header, header);
    let erase = build_plan(
        draw.after_state(),
        &source.grid,
        TableRulingOperation::EraseDiagonal {
            master_cell_id,
            direction,
        },
    )?;
    let erased = TableRulingHwpxLowerer::lower_existing(
        &drawn.header,
        &drawn.section,
        0,
        binding,
        draw.after_state(),
        &source.grid,
        &erase,
        &digest('f'),
        TableRulingHwpxLimits::default(),
    )?;
    let reopened = TableRulingHwpxReader::read_existing(
        &erased.header,
        &erased.section,
        0,
        binding,
        TableRulingHwpxLimits::default(),
    )?;
    assert_eq!(reopened.state, source.state);
    assert_eq!(reopened.grid, source.grid);
    Ok(())
}

#[test]
fn outer_rectangle_replaces_exact_empty_paragraph_and_reopens_target() -> TestResult {
    let header = header()?;
    let template_section = empty_wrapped_template_section()?;
    let target_binding = binding_with_boundaries(&[0], vec![0, 1000], vec![0, 2000])?;
    let template = TableRulingHwpxReader::read_existing(
        &header,
        &template_section,
        0,
        &target_binding,
        TableRulingHwpxLimits::default(),
    )?;
    let source = insertion_section();
    let insertion_context = TableRulingHwpxLowerer::outer_insertion_context_sha256(&source, 1)?;
    let plan = build_outer_plan(&template, insertion_context)?;
    let output = TableRulingHwpxLowerer::lower_outer_rectangle(
        &header,
        &source,
        1,
        &template_section,
        0,
        &plan,
        &digest('f'),
        TableRulingHwpxLimits::default(),
    )?;
    assert!(output.receipt.source_state_sha256.is_none());
    assert!(output.receipt.source_grid_sha256.is_none());
    assert!(output.receipt.template_section_sha256.is_some());
    assert!(output.receipt.insertion_context_sha256.is_some());
    assert_eq!(output.receipt.target_cell_count, 1);
    assert_eq!(output.receipt.payload_block_count, 0);
    assert_eq!(output.receipt.formula_count, 0);

    let placeholder = text_paragraph("").into_bytes();
    let start = source
        .windows(placeholder.len())
        .position(|window| window == placeholder)
        .ok_or("placeholder bytes missing")?;
    let end = start + placeholder.len();
    let suffix_len = source.len() - end;
    assert_eq!(output.section.get(..start), source.get(..start));
    assert_eq!(
        output.section.get(output.section.len() - suffix_len..),
        source.get(end..)
    );
    let reopened = TableRulingHwpxReader::read_existing(
        &output.header,
        &output.section,
        0,
        &target_binding,
        TableRulingHwpxLimits::default(),
    )?;
    assert_eq!(reopened.state, *plan.after_state());
    assert_eq!(reopened.grid, grid_from_plan(&plan)?);

    let drifted = String::from_utf8(source.clone())?.replace("AFTER", "DRIFT");
    assert!(matches!(
        TableRulingHwpxLowerer::lower_outer_rectangle(
            &header,
            drifted.as_bytes(),
            1,
            &template_section,
            0,
            &plan,
            &digest('f'),
            TableRulingHwpxLimits::default(),
        ),
        Err(TableRulingHwpxError::PlanBindingMismatch)
    ));

    let existing_table = table_fragment(ordinary_section())?;
    let colliding_source = format!(
        r#"<hs:sec xmlns:hs="{SECTION_NS}" xmlns:hp="{PARAGRAPH_NS}">{existing_table}{}</hs:sec>"#,
        text_paragraph("")
    )
    .into_bytes();
    let colliding_context =
        TableRulingHwpxLowerer::outer_insertion_context_sha256(&colliding_source, 0)?;
    let colliding_plan = build_outer_plan(&template, colliding_context)?;
    assert!(matches!(
        TableRulingHwpxLowerer::lower_outer_rectangle(
            &header,
            &colliding_source,
            0,
            &template_section,
            0,
            &colliding_plan,
            &digest('f'),
            TableRulingHwpxLimits::default(),
        ),
        Err(TableRulingHwpxError::NativeTableIdCollision)
    ));
    Ok(())
}

#[test]
fn lifts_complete_edges_payloads_properties_and_physical_state() -> TestResult {
    let readback = TableRulingHwpxReader::read_existing(
        &header()?,
        &ordinary_section(),
        0,
        &binding(&[1, 1, 1, 1])?,
        TableRulingHwpxLimits::default(),
    )?;
    assert_eq!(readback.profile_id, TABLE_RULING_HWPX_PROFILE_ID);
    assert_eq!((readback.grid.rows(), readback.grid.columns()), (2, 2));
    assert_eq!(readback.state.frame().left_hwpunit, 1000);
    assert_eq!(readback.state.frame().top_hwpunit, 2000);
    assert_eq!(readback.payload_block_count, 4);
    assert_eq!(readback.formula_count, 0);
    assert_eq!(readback.border_fill_count, 4);
    assert_eq!(readback.state.edges().len(), 12);
    let line = readback
        .state
        .edge(TableRulingAxis::Horizontal, 0, 0)
        .and_then(|edge| edge.line_sha256.as_deref())
        .ok_or("missing top line")?;
    assert!(
        readback
            .state
            .edges()
            .iter()
            .all(|edge| edge.line_sha256.as_deref() == Some(line))
    );
    assert_eq!(readback.state.cells()[0].payload().len(), 1);
    Ok(())
}

#[test]
fn merged_cell_uses_bound_internal_lattice_and_formula_is_separate_from_payload() -> TestResult {
    let merged_section = merged_section();
    let readback = TableRulingHwpxReader::read_existing(
        &header()?,
        &merged_section,
        0,
        &binding(&[1, 1, 1])?,
        TableRulingHwpxLimits::default(),
    )?;
    assert_eq!(readback.grid.master_cell_count(), 3);
    assert_eq!(readback.formula_count, 0);
    assert_eq!(readback.payload_block_count, 3);
    assert_eq!(
        readback
            .state
            .edge(TableRulingAxis::Vertical, 1, 0)
            .and_then(|edge| edge.line_sha256.as_deref()),
        None
    );

    let formula_section = formula_section();
    let formula_readback = TableRulingHwpxReader::read_existing(
        &header()?,
        &formula_section,
        0,
        &binding(&[1, 1, 1, 0])?,
        TableRulingHwpxLimits::default(),
    )?;
    assert_eq!(formula_readback.formula_count, 1);
    assert_eq!(formula_readback.payload_block_count, 3);
    assert!(formula_readback.state.cells()[3].formula().is_some());
    assert!(formula_readback.state.cells()[3].payload().is_empty());
    Ok(())
}

#[test]
fn hancom_self_closing_empty_run_is_scaffold_not_payload() -> TestResult {
    let empty = r#"<hp:p id="0" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0"><hp:run charPrIDRef="0"/></hp:p>"#;
    let section = table(&[vec![cell(0, 0, 1, 1, 2000, 1000, 3, empty)]], 1, 1);
    let binding = binding_with_boundaries(&[0], vec![0, 1000], vec![0, 2000])?;
    let readback = TableRulingHwpxReader::read_existing(
        &header()?,
        &section,
        0,
        &binding,
        TableRulingHwpxLimits::default(),
    )?;
    assert_eq!(readback.payload_block_count, 0);
    assert!(readback.state.cells()[0].payload().is_empty());

    let control = empty.replace("/>", "><hp:ctrl/></hp:run>");
    let nonempty_section = table(&[vec![cell(0, 0, 1, 1, 2000, 1000, 3, &control)]], 1, 1);
    assert!(matches!(
        TableRulingHwpxReader::read_existing(
            &header()?,
            &nonempty_section,
            0,
            &binding,
            TableRulingHwpxLimits::default(),
        ),
        Err(TableRulingHwpxError::PayloadBindingMismatch)
    ));
    Ok(())
}

#[test]
fn bindings_extents_payloads_and_shared_edges_fail_closed() -> TestResult {
    let header = header()?;
    let section = ordinary_section();
    let mut bad_extent = binding(&[1, 1, 1, 1])?;
    bad_extent.column_boundaries_hwpunit[1] = 900;
    assert!(matches!(
        TableRulingHwpxReader::read_existing(
            &header,
            &section,
            0,
            &bad_extent,
            TableRulingHwpxLimits::default(),
        ),
        Err(TableRulingHwpxError::PhysicalExtentMismatch)
    ));

    assert!(matches!(
        TableRulingHwpxReader::read_existing(
            &header,
            &section,
            0,
            &binding(&[0, 1, 1, 1])?,
            TableRulingHwpxLimits::default(),
        ),
        Err(TableRulingHwpxError::PayloadBindingMismatch)
    ));

    let mismatch =
        String::from_utf8(section)?.replacen("borderFillIDRef=\"3\"", "borderFillIDRef=\"1\"", 1);
    assert!(matches!(
        TableRulingHwpxReader::read_existing(
            &header,
            mismatch.as_bytes(),
            0,
            &binding(&[1, 1, 1, 1])?,
            TableRulingHwpxLimits::default(),
        ),
        Err(TableRulingHwpxError::SharedEdgeMismatch)
    ));
    Ok(())
}

#[test]
fn debug_output_redacts_all_logical_ids_and_digests() -> TestResult {
    let binding = binding(&[1, 1, 1, 1])?;
    let readback = TableRulingHwpxReader::read_existing(
        &header()?,
        &ordinary_section(),
        0,
        &binding,
        TableRulingHwpxLimits::default(),
    )?;
    let binding_debug = format!("{binding:?}");
    let readback_debug = format!("{readback:?}");
    assert!(!binding_debug.contains("secret-table"));
    assert!(!binding_debug.contains("cell-0"));
    assert!(!binding_debug.contains("payload-0-0"));
    assert!(!readback_debug.contains(readback.state.table_properties_sha256()));
    assert!(!readback_debug.contains(readback.state.grid_sha256()));
    Ok(())
}

#[test]
fn structural_eraser_merges_rows_and_preserves_payload_order() -> TestResult {
    let header = header()?;
    let section = ordinary_section();
    let binding = binding(&[1, 1, 1, 1])?;
    let source = TableRulingHwpxReader::read_existing(
        &header,
        &section,
        0,
        &binding,
        TableRulingHwpxLimits::default(),
    )?;
    let plan = build_plan(
        &source.state,
        &source.grid,
        TableRulingOperation::EraseStroke {
            stroke: TableRulingStroke {
                axis: TableRulingAxis::Vertical,
                fixed_hwpunit: 1000,
                start_hwpunit: 0,
                end_hwpunit: 1000,
            },
            formula_policy: TableRulingFormulaPolicy::RejectRebase,
        },
    )?;
    let output = TableRulingHwpxLowerer::lower_existing(
        &header,
        &section,
        0,
        &binding,
        &source.state,
        &source.grid,
        &plan,
        &digest('f'),
        TableRulingHwpxLimits::default(),
    )?;
    assert_eq!(plan.after_grid().master_cells().len(), 2);
    assert_eq!(output.receipt.target_cell_count, 2);
    assert_eq!(output.receipt.payload_block_count, 4);
    assert_eq!(output.receipt.added_border_fill_count, 0);
    let xml = String::from_utf8(output.section)?;
    assert_eq!(xml.matches("<hp:tc ").count(), 2);
    assert!(xml.find(">A<").ok_or("missing A")? < xml.find(">B<").ok_or("missing B")?);
    assert!(xml.find(">C<").ok_or("missing C")? < xml.find(">D<").ok_or("missing D")?);
    Ok(())
}

#[test]
fn draw_split_creates_empty_cell_and_diagonal_uses_reviewed_header_identity() -> TestResult {
    let header = header()?;
    let section = merged_section();
    let source_binding = binding(&[1, 1, 1])?;
    let source = TableRulingHwpxReader::read_existing(
        &header,
        &section,
        0,
        &source_binding,
        TableRulingHwpxLimits::default(),
    )?;
    let line = source
        .state
        .edge(TableRulingAxis::Horizontal, 0, 0)
        .and_then(|edge| edge.line_sha256.clone())
        .ok_or("missing line")?;
    let split = build_plan(
        &source.state,
        &source.grid,
        TableRulingOperation::DrawStroke {
            stroke: TableRulingStroke {
                axis: TableRulingAxis::Vertical,
                fixed_hwpunit: 1000,
                start_hwpunit: 0,
                end_hwpunit: 500,
            },
            line_sha256: line,
            new_master_cell_ids: vec![id("cell-split-new")?],
            formula_policy: TableRulingFormulaPolicy::RejectRebase,
        },
    )?;
    let split_output = TableRulingHwpxLowerer::lower_existing(
        &header,
        &section,
        0,
        &source_binding,
        &source.state,
        &source.grid,
        &split,
        &digest('f'),
        TableRulingHwpxLimits::default(),
    )?;
    assert_eq!(split_output.receipt.target_cell_count, 4);
    assert_eq!(split_output.receipt.payload_block_count, 3);
    assert_eq!(split_output.receipt.added_border_fill_count, 0);

    let diagonal_header = header_with_back_slash()?;
    let ordinary = ordinary_section();
    let ordinary_binding = binding(&[1, 1, 1, 1])?;
    let ordinary_source = TableRulingHwpxReader::read_existing(
        &diagonal_header,
        &ordinary,
        0,
        &ordinary_binding,
        TableRulingHwpxLimits::default(),
    )?;
    let slash = ordinary_source
        .style_catalog
        .slash_diagonal_sha256
        .first()
        .cloned()
        .ok_or("missing slash identity")?;
    let back_slash = ordinary_source
        .style_catalog
        .back_slash_diagonal_sha256
        .first()
        .cloned()
        .ok_or("missing back-slash identity")?;
    assert_diagonal_round_trip(
        &diagonal_header,
        &ordinary,
        &ordinary_binding,
        &ordinary_source,
        TableRulingDiagonalDirection::Slash,
        slash,
    )?;
    assert_diagonal_round_trip(
        &diagonal_header,
        &ordinary,
        &ordinary_binding,
        &ordinary_source,
        TableRulingDiagonalDirection::BackSlash,
        back_slash,
    )?;
    Ok(())
}

#[test]
fn nonstructural_eraser_synthesizes_and_deduplicates_one_border_fill() -> TestResult {
    let header = header()?;
    let section = ordinary_section();
    let binding = binding(&[1, 1, 1, 1])?;
    let source = TableRulingHwpxReader::read_existing(
        &header,
        &section,
        0,
        &binding,
        TableRulingHwpxLimits::default(),
    )?;
    let plan = build_plan(
        &source.state,
        &source.grid,
        TableRulingOperation::EraseStroke {
            stroke: TableRulingStroke {
                axis: TableRulingAxis::Horizontal,
                fixed_hwpunit: 0,
                start_hwpunit: 0,
                end_hwpunit: 2000,
            },
            formula_policy: TableRulingFormulaPolicy::RejectRebase,
        },
    )?;
    let output = TableRulingHwpxLowerer::lower_existing(
        &header,
        &section,
        0,
        &binding,
        &source.state,
        &source.grid,
        &plan,
        &digest('f'),
        TableRulingHwpxLimits::default(),
    )?;
    assert_eq!(output.receipt.added_border_fill_count, 1);
    let output_header = String::from_utf8(output.header)?;
    assert!(output_header.contains("<hh:borderFills itemCnt=\"5\">"));
    assert_eq!(output_header.matches("<hh:borderFill id=\"5\"").count(), 1);
    assert_eq!(
        String::from_utf8(output.section)?
            .matches("borderFillIDRef=\"5\"")
            .count(),
        2
    );
    Ok(())
}

#[test]
fn lowerer_rejects_flow_drift_and_redacts_receipt_hashes() -> TestResult {
    let header = header()?;
    let section = ordinary_section();
    let binding = binding(&[1, 1, 1, 1])?;
    let source = TableRulingHwpxReader::read_existing(
        &header,
        &section,
        0,
        &binding,
        TableRulingHwpxLimits::default(),
    )?;
    let plan = build_plan(
        &source.state,
        &source.grid,
        TableRulingOperation::EraseStroke {
            stroke: TableRulingStroke {
                axis: TableRulingAxis::Horizontal,
                fixed_hwpunit: 0,
                start_hwpunit: 0,
                end_hwpunit: 2000,
            },
            formula_policy: TableRulingFormulaPolicy::RejectRebase,
        },
    )?;
    assert!(matches!(
        TableRulingHwpxLowerer::lower_existing(
            &header,
            &section,
            0,
            &binding,
            &source.state,
            &source.grid,
            &plan,
            &digest('e'),
            TableRulingHwpxLimits::default(),
        ),
        Err(TableRulingHwpxError::FlowBindingMismatch)
    ));
    let output = TableRulingHwpxLowerer::lower_existing(
        &header,
        &section,
        0,
        &binding,
        &source.state,
        &source.grid,
        &plan,
        &digest('f'),
        TableRulingHwpxLimits::default(),
    )?;
    let debug = format!("{:?}", output.receipt);
    let source_state_sha256 = output
        .receipt
        .source_state_sha256
        .ok_or("source state digest missing")?;
    assert!(!debug.contains(&hex(source_state_sha256)));
    assert!(!debug.contains(&digest('f')));
    Ok(())
}

#[test]
fn lowerer_rejects_source_state_grid_and_missing_line_drift() -> TestResult {
    let header = header()?;
    let section = ordinary_section();
    let binding = binding(&[1, 1, 1, 1])?;
    let source = TableRulingHwpxReader::read_existing(
        &header,
        &section,
        0,
        &binding,
        TableRulingHwpxLimits::default(),
    )?;
    let plan = build_plan(
        &source.state,
        &source.grid,
        TableRulingOperation::DrawStroke {
            stroke: TableRulingStroke {
                axis: TableRulingAxis::Horizontal,
                fixed_hwpunit: 0,
                start_hwpunit: 0,
                end_hwpunit: 2000,
            },
            line_sha256: digest('a'),
            new_master_cell_ids: Vec::new(),
            formula_policy: TableRulingFormulaPolicy::RejectRebase,
        },
    )?;
    assert!(matches!(
        TableRulingHwpxLowerer::lower_existing(
            &header,
            &section,
            0,
            &binding,
            &source.state,
            &source.grid,
            &plan,
            &digest('f'),
            TableRulingHwpxLimits::default(),
        ),
        Err(TableRulingHwpxError::MissingLineIdentity)
    ));

    let drifted_section = String::from_utf8(section.clone())?
        .replacen("horzOffset=\"1000\"", "horzOffset=\"1100\"", 1)
        .into_bytes();
    let drifted = TableRulingHwpxReader::read_existing(
        &header,
        &drifted_section,
        0,
        &binding,
        TableRulingHwpxLimits::default(),
    )?;
    assert!(matches!(
        TableRulingHwpxLowerer::lower_existing(
            &header,
            &section,
            0,
            &binding,
            &drifted.state,
            &source.grid,
            &plan,
            &digest('f'),
            TableRulingHwpxLimits::default(),
        ),
        Err(TableRulingHwpxError::SourceStateMismatch)
    ));

    let mut spans = source.grid.master_cells().to_vec();
    let first = spans[0].master_cell_id.clone();
    spans[0].master_cell_id = spans[1].master_cell_id.clone();
    spans[1].master_cell_id = first;
    let wrong_grid = TableGrid::new(2, 2, spans, TableGridLimits::default())?;
    assert!(matches!(
        TableRulingHwpxLowerer::lower_existing(
            &header,
            &section,
            0,
            &binding,
            &source.state,
            &wrong_grid,
            &plan,
            &digest('f'),
            TableRulingHwpxLimits::default(),
        ),
        Err(TableRulingHwpxError::SourceStateMismatch)
    ));
    Ok(())
}

#[test]
fn nonuniform_native_cell_side_fails_closed() -> TestResult {
    let header = header_with_dot()?;
    let section = merged_section();
    let binding = binding(&[1, 1, 1])?;
    let source = TableRulingHwpxReader::read_existing(
        &header,
        &section,
        0,
        &binding,
        TableRulingHwpxLimits::default(),
    )?;
    let current = source
        .state
        .edge(TableRulingAxis::Horizontal, 0, 0)
        .and_then(|edge| edge.line_sha256.as_deref())
        .ok_or("current line missing")?;
    let alternate = source
        .style_catalog
        .edge_line_sha256
        .iter()
        .find(|digest| digest.as_str() != current)
        .cloned()
        .ok_or("alternate line missing")?;
    let plan = build_plan(
        &source.state,
        &source.grid,
        TableRulingOperation::DrawStroke {
            stroke: TableRulingStroke {
                axis: TableRulingAxis::Horizontal,
                fixed_hwpunit: 0,
                start_hwpunit: 0,
                end_hwpunit: 1000,
            },
            line_sha256: alternate,
            new_master_cell_ids: Vec::new(),
            formula_policy: TableRulingFormulaPolicy::RejectRebase,
        },
    )?;
    assert!(matches!(
        TableRulingHwpxLowerer::lower_existing(
            &header,
            &section,
            0,
            &binding,
            &source.state,
            &source.grid,
            &plan,
            &digest('f'),
            TableRulingHwpxLimits::default(),
        ),
        Err(TableRulingHwpxError::NonUniformCellSide)
    ));
    Ok(())
}

#[test]
fn incompatible_dual_diagonal_lines_fail_closed() -> TestResult {
    let header = header_with_back_slash()?;
    let section = ordinary_section();
    let binding = binding(&[1, 1, 1, 1])?;
    let source = TableRulingHwpxReader::read_existing(
        &header,
        &section,
        0,
        &binding,
        TableRulingHwpxLimits::default(),
    )?;
    let cell_id = source.state.cells()[0].master_cell_id().clone();
    let slash = source
        .style_catalog
        .slash_diagonal_sha256
        .first()
        .cloned()
        .ok_or("slash line missing")?;
    let back_slash = source
        .style_catalog
        .back_slash_diagonal_sha256
        .first()
        .cloned()
        .ok_or("back-slash line missing")?;
    let slash_plan = build_plan(
        &source.state,
        &source.grid,
        TableRulingOperation::DrawDiagonal {
            master_cell_id: cell_id.clone(),
            direction: TableRulingDiagonalDirection::Slash,
            line_sha256: slash,
        },
    )?;
    let slash_output = TableRulingHwpxLowerer::lower_existing(
        &header,
        &section,
        0,
        &binding,
        &source.state,
        &source.grid,
        &slash_plan,
        &digest('f'),
        TableRulingHwpxLimits::default(),
    )?;
    let both_plan = build_plan(
        slash_plan.after_state(),
        &source.grid,
        TableRulingOperation::DrawDiagonal {
            master_cell_id: cell_id,
            direction: TableRulingDiagonalDirection::BackSlash,
            line_sha256: back_slash,
        },
    )?;
    assert!(matches!(
        TableRulingHwpxLowerer::lower_existing(
            &slash_output.header,
            &slash_output.section,
            0,
            &binding,
            slash_plan.after_state(),
            &source.grid,
            &both_plan,
            &digest('f'),
            TableRulingHwpxLimits::default(),
        ),
        Err(TableRulingHwpxError::NonUniformCellSide)
    ));
    Ok(())
}

#[test]
fn full_row_then_column_draw_refines_native_lattice_without_losing_payload() -> TestResult {
    let header = header()?;
    let section = single_section();
    let binding = binding_with_boundaries(&[1], vec![0, 1000], vec![0, 2000])?;
    let source = TableRulingHwpxReader::read_existing(
        &header,
        &section,
        0,
        &binding,
        TableRulingHwpxLimits::default(),
    )?;
    let line = source
        .style_catalog
        .edge_line_sha256
        .first()
        .cloned()
        .ok_or("missing edge identity")?;
    let row_plan = build_plan(
        &source.state,
        &source.grid,
        TableRulingOperation::DrawStroke {
            stroke: TableRulingStroke {
                axis: TableRulingAxis::Horizontal,
                fixed_hwpunit: 500,
                start_hwpunit: 0,
                end_hwpunit: 2000,
            },
            line_sha256: line.clone(),
            new_master_cell_ids: vec![id("row-new")?],
            formula_policy: TableRulingFormulaPolicy::RejectRebase,
        },
    )?;
    let row_output = TableRulingHwpxLowerer::lower_existing(
        &header,
        &section,
        0,
        &binding,
        &source.state,
        &source.grid,
        &row_plan,
        &digest('f'),
        TableRulingHwpxLimits::default(),
    )?;
    let row_grid = grid_from_plan(&row_plan)?;
    let row_binding = binding_from_state(row_plan.after_state(), &row_grid)?;
    let column_plan = build_plan(
        row_plan.after_state(),
        &row_grid,
        TableRulingOperation::DrawStroke {
            stroke: TableRulingStroke {
                axis: TableRulingAxis::Vertical,
                fixed_hwpunit: 1000,
                start_hwpunit: 0,
                end_hwpunit: 1000,
            },
            line_sha256: line,
            new_master_cell_ids: vec![id("top-right-new")?, id("bottom-right-new")?],
            formula_policy: TableRulingFormulaPolicy::RejectRebase,
        },
    )?;
    let column_output = TableRulingHwpxLowerer::lower_existing(
        &row_output.header,
        &row_output.section,
        0,
        &row_binding,
        row_plan.after_state(),
        &row_grid,
        &column_plan,
        &digest('f'),
        TableRulingHwpxLimits::default(),
    )?;
    assert_eq!(column_output.receipt.target_cell_count, 4);
    assert_eq!(column_output.receipt.payload_block_count, 1);
    let xml = String::from_utf8(column_output.section)?;
    assert!(xml.contains("rowCnt=\"2\" colCnt=\"2\""));
    assert_eq!(xml.matches("<hp:tc ").count(), 4);
    assert_eq!(xml.matches(">ONLY<").count(), 1);
    Ok(())
}

#[test]
fn line_only_edit_preserves_formula_and_structural_formula_change_fails_closed() -> TestResult {
    let header = header()?;
    let section = formula_section();
    let binding = binding(&[1, 1, 1, 0])?;
    let source = TableRulingHwpxReader::read_existing(
        &header,
        &section,
        0,
        &binding,
        TableRulingHwpxLimits::default(),
    )?;
    let line_only = build_plan(
        &source.state,
        &source.grid,
        TableRulingOperation::EraseStroke {
            stroke: TableRulingStroke {
                axis: TableRulingAxis::Horizontal,
                fixed_hwpunit: 0,
                start_hwpunit: 0,
                end_hwpunit: 2000,
            },
            formula_policy: TableRulingFormulaPolicy::RejectRebase,
        },
    )?;
    let output = TableRulingHwpxLowerer::lower_existing(
        &header,
        &section,
        0,
        &binding,
        &source.state,
        &source.grid,
        &line_only,
        &digest('f'),
        TableRulingHwpxLimits::default(),
    )?;
    assert_eq!(output.receipt.formula_count, 1);
    assert_eq!(output.receipt.payload_block_count, 3);
    assert!(String::from_utf8(output.section)?.contains("=SUM(LEFT)??%g,;;7"));

    let structural = build_plan(
        &source.state,
        &source.grid,
        TableRulingOperation::EraseStroke {
            stroke: TableRulingStroke {
                axis: TableRulingAxis::Vertical,
                fixed_hwpunit: 1000,
                start_hwpunit: 0,
                end_hwpunit: 500,
            },
            formula_policy: TableRulingFormulaPolicy::RebaseAndClearTopologyStaleCache,
        },
    )?;
    assert!(matches!(
        TableRulingHwpxLowerer::lower_existing(
            &header,
            &section,
            0,
            &binding,
            &source.state,
            &source.grid,
            &structural,
            &digest('f'),
            TableRulingHwpxLimits::default(),
        ),
        Err(TableRulingHwpxError::UnsupportedFormulaMutation)
    ));

    Ok(())
}

#[test]
fn closed_package_reopen_preserves_formula_pagination_and_unselected_parts() -> TestResult {
    let header = header()?;
    let first_table = table_fragment(ordinary_section())?;
    let second_table = table_fragment(formula_section())?.replacen("id=\"700\"", "id=\"701\"", 1);
    let section = format!(
        r#"<hs:sec xmlns:hs="{SECTION_NS}" xmlns:hp="{PARAGRAPH_NS}">{first_table}{second_table}</hs:sec>"#
    )
    .into_bytes();
    let source_package = package(&header, &section)?;
    let immutable_source = source_package.clone();
    let (source_graph, reopened_header, reopened_section) = inspect_package(&source_package)?;
    let source_hashes = part_hashes(&source_graph);
    let source_formula = TableFormulaHwpxReader::read_in_section(
        &reopened_section,
        1,
        TableFormulaHwpxLimits::default(),
        FormulaLimits::default(),
    )?;
    let source_pagination = TablePaginationHwpxReader::read_in_section(
        &reopened_section,
        1,
        TablePaginationHwpxLimits::default(),
    )?;
    let source_binding = binding(&[1, 1, 1, 1])?;
    let source = TableRulingHwpxReader::read_existing(
        &reopened_header,
        &reopened_section,
        0,
        &source_binding,
        TableRulingHwpxLimits::default(),
    )?;
    let plan = build_plan(
        &source.state,
        &source.grid,
        TableRulingOperation::EraseStroke {
            stroke: TableRulingStroke {
                axis: TableRulingAxis::Horizontal,
                fixed_hwpunit: 0,
                start_hwpunit: 0,
                end_hwpunit: 2000,
            },
            formula_policy: TableRulingFormulaPolicy::RejectRebase,
        },
    )?;
    let lowered = TableRulingHwpxLowerer::lower_existing(
        &reopened_header,
        &reopened_section,
        0,
        &source_binding,
        &source.state,
        &source.grid,
        &plan,
        &digest('f'),
        TableRulingHwpxLimits::default(),
    )?;
    let target_package =
        replace_header_and_section(&source_package, &lowered.header, &lowered.section)?;
    assert_eq!(
        target_package,
        replace_header_and_section(&source_package, &lowered.header, &lowered.section)?
    );
    assert_eq!(source_package, immutable_source);

    let (target_graph, target_header, target_section) = inspect_package(&target_package)?;
    assert_package_preservation(&source_graph, source_hashes, &target_graph)?;
    let reopened_target = TableRulingHwpxReader::read_existing(
        &target_header,
        &target_section,
        0,
        &source_binding,
        TableRulingHwpxLimits::default(),
    )?;
    assert_eq!(reopened_target.state, *plan.after_state());
    assert_eq!(reopened_target.grid, grid_from_plan(&plan)?);
    assert!(String::from_utf8(target_section.clone())?.contains(&second_table));
    let target_formula = TableFormulaHwpxReader::read_in_section(
        &target_section,
        1,
        TableFormulaHwpxLimits::default(),
        FormulaLimits::default(),
    )?;
    let target_pagination = TablePaginationHwpxReader::read_in_section(
        &target_section,
        1,
        TablePaginationHwpxLimits::default(),
    )?;
    assert_eq!(source_formula.rows, target_formula.rows);
    assert_eq!(source_formula.columns, target_formula.columns);
    assert_eq!(source_formula.formula, target_formula.formula);
    assert_eq!(
        source_formula.formula_field_count,
        target_formula.formula_field_count
    );
    assert_eq!(source_pagination, target_pagination);
    Ok(())
}

#[test]
fn merge_split_hwpx_split_distributes_payload_and_reopens_exactly() -> TestResult {
    let header = header()?;
    let section = merged_four_payload_section();
    let source_binding = binding(&[4])?;
    let limits = TableMergeSplitHwpxLimits::default();
    let source =
        TableMergeSplitHwpxReader::read_existing(&header, &section, 0, &source_binding, limits)?;
    let split_line_sha256 = source
        .ruling
        .state
        .edge(TableRulingAxis::Horizontal, 0, 0)
        .and_then(|edge| edge.line_sha256.clone())
        .ok_or("source line identity missing")?;
    let (request, plan, part_binding) = build_merge_split_plan(
        &source,
        TableMergeSplitHwpxOperation::Split {
            master_cell_id: id("cell-0")?,
            rows: 2,
            columns: 2,
            new_master_cell_ids: vec![id("cell-1")?, id("cell-2")?, id("cell-3")?],
            content_policy: ContentPreservationPolicy::Distribute,
            split_line_sha256,
        },
    )?;
    assert_eq!(plan.target_grid().master_cell_count(), 4);
    assert!(
        plan.target_state()
            .cells()
            .iter()
            .all(|cell| cell.payload().len() == 1)
    );

    let output = TableMergeSplitHwpxLowerer::lower_existing(
        &header,
        &section,
        0,
        &source_binding,
        &part_binding,
        &digest('f'),
        &request,
        &plan,
        limits,
    )?;
    assert_eq!(output.receipt.source_payload_block_count, 4);
    assert_eq!(output.receipt.target_payload_block_count, 4);
    assert_eq!(output.receipt.discarded_content_block_count, 0);
    assert_eq!(output.receipt.preserved_formula_count, 0);
    assert_eq!(output.binding.cells.len(), 4);
    let reopened = TableMergeSplitHwpxReader::read_existing(
        &output.header,
        &output.section,
        0,
        &output.binding,
        limits,
    )?;
    assert_eq!(reopened.ruling.grid, *plan.target_grid());
    assert_eq!(reopened.ruling.state, *plan.target_state());
    let xml = String::from_utf8(output.section)?;
    assert_eq!(xml.matches("<hp:tc ").count(), 4);
    for value in ["A", "B", "C", "D"] {
        assert_eq!(xml.matches(&format!(">{value}<")).count(), 1);
    }
    let debug = format!("{:?}", output.receipt);
    assert!(!debug.contains(&digest('f')));
    assert!(!debug.contains("secret-table"));
    Ok(())
}

#[test]
fn merge_split_hwpx_split_writes_native_empty_cell_scaffold() -> TestResult {
    let header = header()?;
    let payload = ["A", "B"]
        .into_iter()
        .map(text_paragraph)
        .collect::<String>();
    let section = table(
        &[vec![cell(0, 0, 2, 2, 2000, 1000, 3, &payload)], vec![]],
        2,
        2,
    );
    let source_binding = binding(&[2])?;
    let limits = TableMergeSplitHwpxLimits::default();
    let source =
        TableMergeSplitHwpxReader::read_existing(&header, &section, 0, &source_binding, limits)?;
    let split_line_sha256 = source
        .ruling
        .state
        .edge(TableRulingAxis::Horizontal, 0, 0)
        .and_then(|edge| edge.line_sha256.clone())
        .ok_or("source line identity missing")?;
    let (request, plan, part_binding) = build_merge_split_plan(
        &source,
        TableMergeSplitHwpxOperation::Split {
            master_cell_id: id("cell-0")?,
            rows: 2,
            columns: 2,
            new_master_cell_ids: vec![id("cell-1")?, id("cell-2")?, id("cell-3")?],
            content_policy: ContentPreservationPolicy::Distribute,
            split_line_sha256,
        },
    )?;
    let output = TableMergeSplitHwpxLowerer::lower_existing(
        &header,
        &section,
        0,
        &source_binding,
        &part_binding,
        &digest('f'),
        &request,
        &plan,
        limits,
    )?;
    let xml = String::from_utf8(output.section)?;
    let native_empty = r#"<hp:p id="0" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0"><hp:run charPrIDRef="0"/></hp:p>"#;
    assert_eq!(xml.matches(native_empty).count(), 2);
    assert_eq!(output.receipt.source_payload_block_count, 2);
    assert_eq!(output.receipt.target_payload_block_count, 2);
    assert_eq!(output.binding.cells.len(), 4);
    Ok(())
}

#[test]
fn merge_split_hwpx_merge_supports_every_content_policy() -> TestResult {
    let header = header()?;
    let section = ordinary_section();
    let source_binding = binding(&[1, 1, 1, 1])?;
    let limits = TableMergeSplitHwpxLimits::default();
    let source =
        TableMergeSplitHwpxReader::read_existing(&header, &section, 0, &source_binding, limits)?;
    let selected_slots = vec![
        CellCoordinate { row: 0, column: 0 },
        CellCoordinate { row: 0, column: 1 },
        CellCoordinate { row: 1, column: 0 },
        CellCoordinate { row: 1, column: 1 },
    ];

    for policy in [
        ContentPreservationPolicy::Concatenate,
        ContentPreservationPolicy::Distribute,
        ContentPreservationPolicy::First,
    ] {
        let (request, plan, part_binding) = build_merge_split_plan(
            &source,
            TableMergeSplitHwpxOperation::Merge {
                selected_slots: selected_slots.clone(),
                content_policy: policy,
            },
        )?;
        let output = TableMergeSplitHwpxLowerer::lower_existing(
            &header,
            &section,
            0,
            &source_binding,
            &part_binding,
            &digest('f'),
            &request,
            &plan,
            limits,
        )?;
        assert_eq!(plan.target_grid().master_cell_count(), 1);
        let expected_payloads = if policy == ContentPreservationPolicy::First {
            1
        } else {
            4
        };
        assert_eq!(output.receipt.target_payload_block_count, expected_payloads);
        assert_eq!(
            output.binding.cells[0].payload_block_ids.len(),
            expected_payloads
        );
        assert_eq!(
            output.receipt.discarded_content_block_count,
            if policy == ContentPreservationPolicy::First {
                3
            } else {
                0
            }
        );
        let xml = String::from_utf8(output.section)?;
        assert_eq!(xml.matches("<hp:tc ").count(), 1);
        assert!(xml.contains(">A<"));
        if policy == ContentPreservationPolicy::First {
            for value in ["B", "C", "D"] {
                assert!(!xml.contains(&format!(">{value}<")));
            }
        } else {
            let mut positions = Vec::new();
            for value in ["A", "B", "C", "D"] {
                positions.push(
                    xml.find(&format!(">{value}<"))
                        .ok_or("preserved payload missing")?,
                );
            }
            assert!(positions.windows(2).all(|pair| pair[0] < pair[1]));
        }
    }

    let error = TableMergeSplitHwpxRequest::from_draft(
        merge_split_request_draft(
            &source,
            TableMergeSplitHwpxOperation::Merge {
                selected_slots,
                content_policy: ContentPreservationPolicy::RejectIfMultiple,
            },
        )?,
        &source,
        &digest('f'),
        limits,
    );
    assert!(matches!(
        error,
        Err(TableMergeSplitHwpxError::Domain(
            domain_ir::TableMergeSplitError::MultipleNonemptyCells
        ))
    ));
    Ok(())
}

#[test]
fn merge_split_hwpx_drift_and_json_tamper_fail_closed() -> TestResult {
    let header = header()?;
    let section = ordinary_section();
    let source_binding = binding(&[1, 1, 1, 1])?;
    let limits = TableMergeSplitHwpxLimits::default();
    let source =
        TableMergeSplitHwpxReader::read_existing(&header, &section, 0, &source_binding, limits)?;
    let selected_top = vec![
        CellCoordinate { row: 0, column: 0 },
        CellCoordinate { row: 0, column: 1 },
    ];
    let operation = TableMergeSplitHwpxOperation::Merge {
        selected_slots: selected_top.clone(),
        content_policy: ContentPreservationPolicy::Concatenate,
    };
    let (request, plan, part_binding) = build_merge_split_plan(&source, operation.clone())?;
    assert_merge_request_canonicalization(&source, &selected_top, &request, &limits)?;

    let mut state_drift = merge_split_request_draft(&source, operation.clone())?;
    state_drift.expected_state_sha256 = digest('a');
    assert!(matches!(
        TableMergeSplitHwpxRequest::from_draft(state_drift, &source, &digest('f'), limits),
        Err(TableMergeSplitHwpxError::SourceStateMismatch)
    ));
    assert!(matches!(
        TableMergeSplitHwpxBuilder::build(&request, &source, &digest('e'), limits),
        Err(TableMergeSplitHwpxError::FlowBindingMismatch)
    ));
    let mut drifted_header = header.clone();
    drifted_header.push(b' ');
    assert!(matches!(
        TableMergeSplitHwpxLowerer::lower_existing(
            &drifted_header,
            &section,
            0,
            &source_binding,
            &part_binding,
            &digest('f'),
            &request,
            &plan,
            limits,
        ),
        Err(TableMergeSplitHwpxError::PartBindingMismatch)
    ));
    let mut binding_drift = part_binding.clone();
    binding_drift.source_content_sha256 = digest('b');
    assert!(matches!(
        TableMergeSplitHwpxLowerer::lower_existing(
            &header,
            &section,
            0,
            &source_binding,
            &binding_drift,
            &digest('f'),
            &request,
            &plan,
            limits,
        ),
        Err(TableMergeSplitHwpxError::PartBindingMismatch)
    ));
    let (alternate_request, alternate_plan, _) = build_merge_split_plan(
        &source,
        TableMergeSplitHwpxOperation::Merge {
            selected_slots: selected_top.clone(),
            content_policy: ContentPreservationPolicy::First,
        },
    )?;
    assert!(matches!(
        TableMergeSplitHwpxLowerer::lower_existing(
            &header,
            &section,
            0,
            &source_binding,
            &part_binding,
            &digest('f'),
            &alternate_request,
            &alternate_plan,
            limits,
        ),
        Err(TableMergeSplitHwpxError::PartBindingMismatch)
    ));
    assert!(matches!(
        TableMergeSplitHwpxRequest::from_json(b"", &source, &digest('f'), limits),
        Err(TableMergeSplitHwpxError::InputLimit)
    ));
    let unknown_json =
        String::from_utf8(request.canonical_json(limits)?)?.replacen('{', r#"{"unknown":0,"#, 1);
    assert!(matches!(
        TableMergeSplitHwpxRequest::from_json(
            unknown_json.as_bytes(),
            &source,
            &digest('f'),
            limits
        ),
        Err(TableMergeSplitHwpxError::InvalidJson)
    ));

    let debug = format!("{request:?}{part_binding:?}{operation:?}");
    assert!(!debug.contains("secret-table"));
    assert!(!debug.contains(&digest('f')));
    Ok(())
}

#[test]
fn merge_split_hwpx_property_and_diagonal_selection_fail_closed() -> TestResult {
    let header = header()?;
    let section = ordinary_section();
    let source_binding = binding(&[1, 1, 1, 1])?;
    let limits = TableMergeSplitHwpxLimits::default();
    let operation = TableMergeSplitHwpxOperation::Merge {
        selected_slots: vec![
            CellCoordinate { row: 0, column: 0 },
            CellCoordinate { row: 0, column: 1 },
        ],
        content_policy: ContentPreservationPolicy::Concatenate,
    };

    let property_section = String::from_utf8(section.clone())?
        .replacen(
            r#"name="" header="0" hasMargin="0" protect="0""#,
            r#"name="" header="0" hasMargin="0" protect="1""#,
            1,
        )
        .into_bytes();
    let property_source = TableMergeSplitHwpxReader::read_existing(
        &header,
        &property_section,
        0,
        &source_binding,
        limits,
    )?;
    assert!(matches!(
        TableMergeSplitHwpxRequest::from_draft(
            merge_split_request_draft(&property_source, operation.clone())?,
            &property_source,
            &digest('f'),
            limits,
        ),
        Err(TableMergeSplitHwpxError::UnsupportedSelectedProperties)
    ));

    let diagonal_section = String::from_utf8(section.clone())?
        .replacen("borderFillIDRef=\"3\"", "borderFillIDRef=\"4\"", 1)
        .into_bytes();
    let diagonal_source = TableMergeSplitHwpxReader::read_existing(
        &header,
        &diagonal_section,
        0,
        &source_binding,
        limits,
    )?;
    assert!(matches!(
        TableMergeSplitHwpxRequest::from_draft(
            merge_split_request_draft(&diagonal_source, operation.clone())?,
            &diagonal_source,
            &digest('f'),
            limits,
        ),
        Err(TableMergeSplitHwpxError::UnsupportedSelectedDiagonal)
    ));
    Ok(())
}

#[test]
fn merge_split_hwpx_formula_and_split_line_selection_fail_closed() -> TestResult {
    let header = header()?;
    let limits = TableMergeSplitHwpxLimits::default();
    assert_eq!(
        TableMergeSplitHwpxError::UnsupportedSelectedFormula.code(),
        "table_merge_split_hwpx_unsupported_selected_formula"
    );

    let formula_section = formula_section();
    let formula_binding = binding(&[1, 1, 1, 0])?;
    let formula_source = TableMergeSplitHwpxReader::read_existing(
        &header,
        &formula_section,
        0,
        &formula_binding,
        limits,
    )?;
    let formula_operation = TableMergeSplitHwpxOperation::Merge {
        selected_slots: vec![
            CellCoordinate { row: 1, column: 0 },
            CellCoordinate { row: 1, column: 1 },
        ],
        content_policy: ContentPreservationPolicy::Concatenate,
    };
    assert!(matches!(
        TableMergeSplitHwpxRequest::from_draft(
            merge_split_request_draft(&formula_source, formula_operation)?,
            &formula_source,
            &digest('f'),
            limits,
        ),
        Err(TableMergeSplitHwpxError::UnsupportedSelectedFormula)
    ));

    let split_section = merged_four_payload_section();
    let split_binding = binding(&[4])?;
    let split_source = TableMergeSplitHwpxReader::read_existing(
        &header,
        &split_section,
        0,
        &split_binding,
        limits,
    )?;
    assert!(matches!(
        TableMergeSplitHwpxRequest::from_draft(
            merge_split_request_draft(
                &split_source,
                TableMergeSplitHwpxOperation::Split {
                    master_cell_id: id("cell-0")?,
                    rows: 2,
                    columns: 2,
                    new_master_cell_ids: vec![id("cell-1")?, id("cell-2")?, id("cell-3")?],
                    content_policy: ContentPreservationPolicy::Concatenate,
                    split_line_sha256: digest('a'),
                },
            )?,
            &split_source,
            &digest('f'),
            limits,
        ),
        Err(TableMergeSplitHwpxError::UnsupportedSplitLine)
    ));
    Ok(())
}

#[test]
fn merge_split_hwpx_closed_package_preserves_unselected_formula_and_table() -> TestResult {
    let header = header()?;
    let first_table = table_fragment(formula_section())?;
    let second_table = table_fragment(ordinary_section())?.replacen("id=\"700\"", "id=\"701\"", 1);
    let section = format!(
        r#"<hs:sec xmlns:hs="{SECTION_NS}" xmlns:hp="{PARAGRAPH_NS}">{first_table}{second_table}</hs:sec>"#
    )
    .into_bytes();
    let source_package = package(&header, &section)?;
    let immutable_source = source_package.clone();
    let (source_graph, reopened_header, reopened_section) = inspect_package(&source_package)?;
    let source_hashes = part_hashes(&source_graph);
    let source_formula = TableFormulaHwpxReader::read_in_section(
        &reopened_section,
        0,
        TableFormulaHwpxLimits::default(),
        FormulaLimits::default(),
    )?;
    let source_pagination = TablePaginationHwpxReader::read_in_section(
        &reopened_section,
        0,
        TablePaginationHwpxLimits::default(),
    )?;
    let source_binding = binding(&[1, 1, 1, 0])?;
    let limits = TableMergeSplitHwpxLimits::default();
    let source = TableMergeSplitHwpxReader::read_existing(
        &reopened_header,
        &reopened_section,
        0,
        &source_binding,
        limits,
    )?;
    let (request, plan, part_binding) = build_merge_split_plan(
        &source,
        TableMergeSplitHwpxOperation::Merge {
            selected_slots: vec![
                CellCoordinate { row: 0, column: 0 },
                CellCoordinate { row: 0, column: 1 },
            ],
            content_policy: ContentPreservationPolicy::Concatenate,
        },
    )?;
    let lowered = TableMergeSplitHwpxLowerer::lower_existing(
        &reopened_header,
        &reopened_section,
        0,
        &source_binding,
        &part_binding,
        &digest('f'),
        &request,
        &plan,
        limits,
    )?;
    assert_eq!(lowered.receipt.preserved_formula_count, 1);
    assert_eq!(lowered.receipt.source_payload_block_count, 3);
    assert_eq!(lowered.receipt.target_payload_block_count, 3);
    assert!(String::from_utf8(lowered.section.clone())?.contains(&second_table));

    let target_package =
        replace_header_and_section(&source_package, &lowered.header, &lowered.section)?;
    assert_eq!(
        target_package,
        replace_header_and_section(&source_package, &lowered.header, &lowered.section)?
    );
    assert_eq!(source_package, immutable_source);
    let (target_graph, target_header, target_section) = inspect_package(&target_package)?;
    assert_section_only_package_change(&source_graph, source_hashes, &target_graph)?;
    let target_readback = TableMergeSplitHwpxReader::read_existing(
        &target_header,
        &target_section,
        0,
        &lowered.binding,
        limits,
    )?;
    assert_eq!(target_readback.ruling.state, *plan.target_state());
    assert_eq!(target_readback.ruling.grid, *plan.target_grid());
    let target_formula = target_readback
        .ruling
        .state
        .cells()
        .iter()
        .find_map(|cell| cell.formula())
        .ok_or("preserved formula missing")?;
    let target_pagination = TablePaginationHwpxReader::read_in_section(
        &target_section,
        0,
        TablePaginationHwpxLimits::default(),
    )?;
    assert_eq!(&source_formula.formula, target_formula);
    assert_eq!(source_formula.formula_field_count, 1);
    assert_eq!(source_pagination, target_pagination);
    Ok(())
}
