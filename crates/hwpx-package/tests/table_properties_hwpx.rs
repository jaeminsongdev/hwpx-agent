use std::collections::BTreeMap;
use std::io::{Cursor, Write};

use domain_ir::{
    CellCoordinate, FormulaLimits, LogicalId, TABLE_PROPERTIES_SCHEMA_VERSION,
    TABLE_STYLE_DEFINITION_SCHEMA_VERSION, TABLE_STYLE_SCHEMA_VERSION, TableCellBorderPatch,
    TableDiagonalApplyMode, TableDiagonalCenterLine, TableDiagonalPatch, TableDiagonalSlash,
    TableDiagonalSlashType, TableDiagonalValue, TablePropertiesBuilder, TablePropertiesLimits,
    TablePropertiesOperation, TablePropertiesRequest, TablePropertiesRequestDraft,
    TablePropertyDigestPatch, TablePropertyRegion, TableStyleBandPrecedence, TableStyleBanding,
    TableStyleBuilder, TableStyleCellDraft, TableStyleColumnEmphasis, TableStyleDefinition,
    TableStyleDefinitionDraft, TableStyleLimits, TableStyleMergedCellPolicy, TableStyleRegion,
    TableStyleRequest, TableStyleRequestDraft, TableStyleRule, TableUnifiedBorderPatch,
};
use hwpx_package::{
    BorderFill, BorderLine, BorderWidth, BoundedZipReader, CellMargins, CellProtection,
    CellTextDirection, CellVerticalAlignment, CenterLine, Color, Compression, FillBrush,
    HorizontalAlignment, LineType2, PackageGraph, PackageGraphLimits, PackageLimits,
    ParagraphStyleCatalogReader, ParagraphStyleLimits, Slash, SlashType,
    TABLE_PROPERTIES_HWPX_PROFILE_ID, TABLE_STYLE_HWPX_PROFILE_ID, TableFormulaHwpxLimits,
    TableFormulaHwpxReader, TableLayoutHwpxLimitConfig, TableLayoutHwpxLimits,
    TablePaginationHwpxLimits, TablePaginationHwpxReader, TablePropertiesHwpxBinding,
    TablePropertiesHwpxCellValue, TablePropertiesHwpxDiagonalBinding, TablePropertiesHwpxError,
    TablePropertiesHwpxLimits, TablePropertiesHwpxLowerer, TablePropertiesHwpxPartBinding,
    TablePropertiesHwpxReader, TablePropertiesHwpxValueCatalog, TableRulingHwpxBinding,
    TableRulingHwpxCellBinding, TableRulingHwpxError, TableRulingHwpxLimits,
    TableStyleHwpxCellValue, TableStyleHwpxError, TableStyleHwpxLimits, TableStyleHwpxLowerer,
    TableStyleHwpxPartBinding, TableStyleHwpxReadback, TableStyleHwpxReader,
    TableStyleHwpxValueCatalog, WindowBrush,
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

fn header() -> TestResult<Vec<u8>> {
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
    Ok(text
        .replacen(
            "<hh:borderFills itemCnt=\"2\">",
            "<hh:borderFills itemCnt=\"3\">",
            1,
        )
        .replacen("</hh:borderFills>", &format!("{solid}</hh:borderFills>"), 1)
        .into_bytes())
}

fn paragraph(value: &str) -> String {
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
            r#"<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">"#,
            "{payload}</hp:subList>",
            r#"<hp:cellAddr colAddr="{column}" rowAddr="{row}"/>"#,
            r#"<hp:cellSpan colSpan="{column_span}" rowSpan="{row_span}"/>"#,
            r#"<hp:cellSz width="{width}" height="{height}"/>"#,
            r#"<hp:cellMargin left="0" right="0" top="0" bottom="0"/>"#,
            "</hp:tc>"
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
            r#"<hp:p id="90" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t>BEFORE</hp:t></hp:run></hp:p>"#,
            r#"<hp:tbl id="700" zOrder="0" numberingType="TABLE" textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" pageBreak="CELL" repeatHeader="0" rowCnt="{row_count}" colCnt="{column_count}" cellSpacing="0" borderFillIDRef="1" noAdjust="0">"#,
            r#"<hp:sz width="2000" widthRelTo="ABSOLUTE" height="1000" heightRelTo="ABSOLUTE" protect="0"/>"#,
            r#"<hp:pos treatAsChar="0" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP" horzAlign="LEFT" vertOffset="2000" horzOffset="1000"/>"#,
            r#"<hp:outMargin left="0" right="0" top="0" bottom="0"/>"#,
            r#"<hp:inMargin left="0" right="0" top="0" bottom="0"/>"#,
            "{body}</hp:tbl>",
            r#"<hp:p id="91" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t>AFTER</hp:t></hp:run></hp:p></hs:sec>"#,
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
                cell(0, 0, 1, 1, 1000, 500, 3, &paragraph("A")),
                cell(0, 1, 1, 1, 1000, 500, 3, &paragraph("B")),
            ],
            vec![
                cell(1, 0, 1, 1, 1000, 500, 3, &paragraph("C")),
                cell(1, 1, 1, 1, 1000, 500, 3, &paragraph("D")),
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
                cell(0, 0, 1, 1, 1000, 500, 3, &paragraph("1")),
                cell(0, 1, 1, 1, 1000, 500, 3, &paragraph("2")),
            ],
            vec![
                cell(1, 0, 1, 1, 1000, 500, 3, &paragraph("7")),
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
            vec![cell(0, 0, 1, 2, 2000, 500, 3, &paragraph("M"))],
            vec![
                cell(1, 0, 1, 1, 1000, 500, 3, &paragraph("L")),
                cell(1, 1, 1, 1, 1000, 500, 3, &paragraph("R")),
            ],
        ],
        2,
        2,
    )
}

fn binding(merged: bool, formula: bool) -> TestResult<TablePropertiesHwpxBinding> {
    let coordinates = if merged {
        vec![("merged", 1_usize), ("cell-1-0", 1), ("cell-1-1", 1)]
    } else {
        vec![
            ("cell-0-0", 1_usize),
            ("cell-0-1", 1),
            ("cell-1-0", 1),
            ("cell-1-1", usize::from(!formula)),
        ]
    };
    let mut cells = Vec::new();
    for (name, payload_count) in coordinates {
        let mut payload_block_ids = Vec::new();
        for index in 0..payload_count {
            payload_block_ids.push(id(&format!("payload-{name}-{index}"))?);
        }
        cells.push(TableRulingHwpxCellBinding {
            master_cell_id: id(name)?,
            payload_block_ids,
        });
    }
    Ok(TablePropertiesHwpxBinding {
        table: TableRulingHwpxBinding {
            table_id: id("table-properties")?,
            row_boundaries_hwpunit: vec![0, 500, 1000],
            column_boundaries_hwpunit: vec![0, 1000, 2000],
            cells,
        },
        diagonals: Vec::new(),
    })
}

fn request(
    source: &hwpx_package::TablePropertiesHwpxReadback,
    selected_slots: Vec<CellCoordinate>,
    operation: TablePropertiesOperation,
) -> TestResult<TablePropertiesRequest> {
    Ok(TablePropertiesRequest::from_draft(
        TablePropertiesRequestDraft {
            schema_version: TABLE_PROPERTIES_SCHEMA_VERSION.to_owned(),
            table_id: source.state.table_id().clone(),
            expected_state_sha256: hex(source
                .state
                .canonical_sha256(TablePropertiesLimits::default())?),
            selected_slots,
            operation,
        },
        &source.state,
        &source.grid,
        TablePropertiesLimits::default(),
    )?)
}

fn plan(
    source: &hwpx_package::TablePropertiesHwpxReadback,
    selected_slots: Vec<CellCoordinate>,
    operation: TablePropertiesOperation,
) -> TestResult<domain_ir::TablePropertiesPlan> {
    let request = request(source, selected_slots, operation)?;
    Ok(TablePropertiesBuilder::build(
        &request,
        &source.state,
        &source.grid,
        TablePropertiesLimits::default(),
    )?)
}

fn part_binding(
    source: &hwpx_package::TablePropertiesHwpxReadback,
) -> TestResult<TablePropertiesHwpxPartBinding> {
    Ok(TablePropertiesHwpxPartBinding::from_readback(
        source,
        "f".repeat(64),
    )?)
}

fn style_value(
    source: &TableStyleHwpxReadback,
    binding: &TablePropertiesHwpxBinding,
    index: usize,
) -> TestResult<TableStyleHwpxCellValue> {
    let cell = source
        .properties
        .state
        .cells()
        .get(index)
        .ok_or("style source cell missing")?;
    let non_border = *source
        .properties
        .cell_values
        .get(index)
        .ok_or("style source non-border value missing")?;
    let diagonal = binding
        .diagonals
        .iter()
        .find(|value| value.master_cell_id == cell.master_cell_id)
        .map(|value| value.value.clone());
    Ok(TableStyleHwpxCellValue {
        non_border,
        borders: cell.properties.borders.clone(),
        background_sha256: cell.properties.background_sha256.clone(),
        diagonal,
    })
}

fn style_definition(
    table_properties_sha256: String,
    rules: Vec<TableStyleRule>,
) -> TestResult<TableStyleDefinition> {
    Ok(TableStyleDefinition::from_draft(
        TableStyleDefinitionDraft {
            schema_version: TABLE_STYLE_DEFINITION_SCHEMA_VERSION.to_owned(),
            style_id: id("style-hwpx")?,
            table_properties_sha256,
            rules,
        },
        TableStyleLimits::default(),
    )?)
}

fn style_request(
    source: &TableStyleHwpxReadback,
    definition: &TableStyleDefinition,
    header_rows: u32,
    column_emphasis: TableStyleColumnEmphasis,
) -> TestResult<TableStyleRequest> {
    let mut cells = Vec::new();
    for ((cell, span), style_sha256) in source
        .properties
        .state
        .cells()
        .iter()
        .zip(source.properties.grid.master_cells())
        .zip(&source.cell_style_sha256)
    {
        cells.push(TableStyleCellDraft {
            master_cell_id: cell.master_cell_id.clone(),
            coordinate: CellCoordinate {
                row: span.row,
                column: span.column,
            },
            payload_sha256: cell.payload_sha256.clone(),
            formula_sha256: cell.formula_sha256.clone(),
            current_style_sha256: style_sha256.clone(),
        });
    }
    Ok(TableStyleRequest::from_draft(
        TableStyleRequestDraft {
            schema_version: TABLE_STYLE_SCHEMA_VERSION.to_owned(),
            table_id: source.properties.state.table_id().clone(),
            style_id: definition.style_id().clone(),
            style_definition_sha256: hex(definition.canonical_sha256(TableStyleLimits::default())?),
            current_table_properties_sha256: source
                .properties
                .state
                .table_properties_sha256()
                .to_owned(),
            header_rows,
            footer_rows: 0,
            column_emphasis,
            banding: TableStyleBanding::None,
            row_band_size: 1,
            column_band_size: 1,
            band_precedence: TableStyleBandPrecedence::RowsFirst,
            merged_cell_policy: TableStyleMergedCellPolicy::UseMasterAnchor,
            cells,
        },
        definition,
        &source.properties.grid,
        TableStyleLimits::default(),
    )?)
}

fn style_plan(
    source: &TableStyleHwpxReadback,
    definition: &TableStyleDefinition,
    header_rows: u32,
    column_emphasis: TableStyleColumnEmphasis,
) -> TestResult<(TableStyleRequest, domain_ir::TableStylePlan)> {
    let request = style_request(source, definition, header_rows, column_emphasis)?;
    let plan = TableStyleBuilder::build(
        &request,
        definition,
        &source.properties.grid,
        TableStyleLimits::default(),
    )?;
    Ok((request, plan))
}

fn style_part_binding(
    source: &TableStyleHwpxReadback,
    request: &TableStyleRequest,
    definition: &TableStyleDefinition,
    plan: &domain_ir::TableStylePlan,
) -> TestResult<TableStyleHwpxPartBinding> {
    Ok(TableStyleHwpxPartBinding::from_readback(
        source,
        request,
        definition,
        plan,
        "f".repeat(64),
        TableStyleHwpxLimits::default(),
    )?)
}

fn slots(row: u32, column: u32, rows: u32, columns: u32) -> Vec<CellCoordinate> {
    let mut output = Vec::new();
    for current_row in row..row + rows {
        for current_column in column..column + columns {
            output.push(CellCoordinate {
                row: current_row,
                column: current_column,
            });
        }
    }
    output
}

fn line(line_type: LineType2, color: Color) -> BorderLine {
    BorderLine {
        line_type,
        width: BorderWidth::Mm0_3,
        color,
    }
}

fn background() -> FillBrush {
    FillBrush {
        window: WindowBrush {
            face_color: Color::Rgb(0x11, 0x22, 0x33),
            hatch_color: Some(Color::Rgb(0xaa, 0xbb, 0xcc)),
            hatch_style: Some(hwpx_package::HatchStyle::Cross),
            alpha: 180,
        },
    }
}

fn set(value: String) -> TablePropertyDigestPatch {
    TablePropertyDigestPatch::Set { sha256: value }
}

fn preserve() -> TablePropertyDigestPatch {
    TablePropertyDigestPatch::Preserve
}

fn hex(value: [u8; 32]) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let mut output = String::with_capacity(64);
    for byte in value {
        output.push(char::from(DIGITS[usize::from(byte >> 4)]));
        output.push(char::from(DIGITS[usize::from(byte & 0x0f)]));
    }
    output
}

fn table_fragment(section: Vec<u8>) -> TestResult<String> {
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
    Ok((
        graph,
        reader.read_entry(header_index)?,
        reader.read_entry(section_index)?,
    ))
}

fn part_hashes(graph: &PackageGraph) -> BTreeMap<String, [u8; 32]> {
    graph
        .parts
        .iter()
        .map(|part| (part.path.as_str().to_owned(), part.raw_sha256))
        .collect()
}

#[test]
fn solid_background_identity_ignores_inert_native_hatch_color() {
    let without_hatch_color = FillBrush {
        window: WindowBrush {
            face_color: Color::Rgb(0xff, 0xf2, 0xcc),
            hatch_color: None,
            hatch_style: None,
            alpha: 255,
        },
    };
    let native_normalized = FillBrush {
        window: WindowBrush {
            hatch_color: Some(Color::Rgb(0, 0, 0)),
            ..without_hatch_color.window
        },
    };
    assert_eq!(
        TablePropertiesHwpxValueCatalog::background_sha256(&without_hatch_color),
        TablePropertiesHwpxValueCatalog::background_sha256(&native_normalized)
    );
    let active_hatch = FillBrush {
        window: WindowBrush {
            hatch_style: Some(hwpx_package::HatchStyle::Cross),
            ..native_normalized.window
        },
    };
    assert_ne!(
        TablePropertiesHwpxValueCatalog::background_sha256(&without_hatch_color),
        TablePropertiesHwpxValueCatalog::background_sha256(&active_hatch)
    );
}

#[test]
fn reader_lifts_complete_typed_state_and_redacts_debug() -> TestResult {
    let header = header()?;
    let section = ordinary_section();
    let readback = TablePropertiesHwpxReader::read_existing(
        &header,
        &section,
        0,
        &binding(false, false)?,
        TablePropertiesHwpxLimits::default(),
    )?;
    assert_eq!(readback.profile_id, TABLE_PROPERTIES_HWPX_PROFILE_ID);
    assert_eq!((readback.grid.rows(), readback.grid.columns()), (2, 2));
    assert_eq!(readback.state.cells().len(), 4);
    assert_eq!(readback.cell_values.len(), 4);
    assert_eq!(readback.payload_block_count, 4);
    assert_eq!(readback.formula_count, 0);
    assert!(readback.state.cells().iter().all(|cell| {
        cell.properties.borders.top_sha256.is_some()
            && cell.properties.background_sha256.is_none()
            && cell.properties.diagonal_sha256.is_none()
    }));
    let debug = format!("{readback:?}");
    assert!(!debug.contains("payload-cell"));
    Ok(())
}

#[test]
fn each_cell_borders_background_and_formula_round_trip() -> TestResult {
    let header = header()?;
    let section = formula_section();
    let binding = binding(false, true)?;
    let source = TablePropertiesHwpxReader::read_existing(
        &header,
        &section,
        0,
        &binding,
        TablePropertiesHwpxLimits::default(),
    )?;
    let lines = [
        line(LineType2::Dot, Color::Rgb(1, 2, 3)),
        line(LineType2::Dash, Color::Rgb(4, 5, 6)),
        line(LineType2::DoubleSlim, Color::Rgb(7, 8, 9)),
        line(LineType2::Circle, Color::Rgb(10, 11, 12)),
    ];
    let fill = background();
    let operation = TablePropertiesOperation::BorderEach {
        border: TableCellBorderPatch {
            top: set(TablePropertiesHwpxValueCatalog::line_sha256(lines[0])?),
            right: set(TablePropertiesHwpxValueCatalog::line_sha256(lines[1])?),
            bottom: set(TablePropertiesHwpxValueCatalog::line_sha256(lines[2])?),
            left: set(TablePropertiesHwpxValueCatalog::line_sha256(lines[3])?),
        },
        background: set(TablePropertiesHwpxValueCatalog::background_sha256(&fill)),
    };
    let plan = plan(
        &source,
        vec![CellCoordinate { row: 0, column: 0 }],
        operation,
    )?;
    let values = TablePropertiesHwpxValueCatalog {
        lines: lines.to_vec(),
        backgrounds: vec![fill],
        ..TablePropertiesHwpxValueCatalog::default()
    };
    let output = TablePropertiesHwpxLowerer::lower_existing(
        &header,
        &section,
        0,
        &binding,
        &part_binding(&source)?,
        &"f".repeat(64),
        &source.state,
        &source.grid,
        &plan,
        &values,
        TablePropertiesHwpxLimits::default(),
    )?;
    let reopened = TablePropertiesHwpxReader::read_existing(
        &output.header,
        &output.section,
        0,
        &output.binding,
        TablePropertiesHwpxLimits::default(),
    )?;
    assert_eq!(reopened.formula_count, 1);
    assert_eq!(
        reopened.state.cells()[3].formula_sha256,
        source.state.cells()[3].formula_sha256
    );
    assert_eq!(
        reopened.state.cells()[0].properties,
        plan.mutations()[0].after
    );
    assert!(output.receipt.added_border_fill_count >= 1);
    assert!(String::from_utf8(output.section)?.contains("BEFORE"));
    Ok(())
}

#[test]
fn unified_border_resolves_outer_and_inner_roles_on_merged_grid() -> TestResult {
    let header = header()?;
    let section = merged_section();
    let binding = binding(true, false)?;
    let source = TablePropertiesHwpxReader::read_existing(
        &header,
        &section,
        0,
        &binding,
        TablePropertiesHwpxLimits::default(),
    )?;
    let lines = [
        LineType2::Dot,
        LineType2::Dash,
        LineType2::DashDot,
        LineType2::DashDotDot,
        LineType2::LongDash,
        LineType2::Circle,
    ]
    .map(|kind| line(kind, Color::Rgb(0x22, 0x33, 0x44)));
    let digests = lines
        .iter()
        .map(|value| TablePropertiesHwpxValueCatalog::line_sha256(*value))
        .collect::<Result<Vec<_>, _>>()?;
    let operation = TablePropertiesOperation::BorderUnified {
        border: TableUnifiedBorderPatch {
            outer_top: set(digests[0].clone()),
            outer_right: set(digests[1].clone()),
            outer_bottom: set(digests[2].clone()),
            outer_left: set(digests[3].clone()),
            inner_horizontal: set(digests[4].clone()),
            inner_vertical: set(digests[5].clone()),
        },
        background: preserve(),
    };
    let plan = plan(&source, slots(0, 0, 2, 2), operation)?;
    let output = TablePropertiesHwpxLowerer::lower_existing(
        &header,
        &section,
        0,
        &binding,
        &part_binding(&source)?,
        &"f".repeat(64),
        &source.state,
        &source.grid,
        &plan,
        &TablePropertiesHwpxValueCatalog {
            lines: lines.to_vec(),
            ..TablePropertiesHwpxValueCatalog::default()
        },
        TablePropertiesHwpxLimits::default(),
    )?;
    let reopened = TablePropertiesHwpxReader::read_existing(
        &output.header,
        &output.section,
        0,
        &output.binding,
        TablePropertiesHwpxLimits::default(),
    )?;
    assert_eq!(reopened.grid.master_cell_count(), 3);
    for mutation in plan.mutations() {
        let actual = reopened
            .state
            .cells()
            .iter()
            .find(|cell| cell.master_cell_id == mutation.master_cell_id)
            .ok_or("missing mutation")?;
        assert_eq!(actual.properties, mutation.after);
    }
    Ok(())
}

fn diagonal_value(line_sha256: String) -> TableDiagonalValue {
    TableDiagonalValue {
        slash: TableDiagonalSlash {
            slash_type: TableDiagonalSlashType::Center,
            crooked: true,
            is_counter: false,
        },
        back_slash: TableDiagonalSlash {
            slash_type: TableDiagonalSlashType::All,
            crooked: false,
            is_counter: true,
        },
        center_line: TableDiagonalCenterLine::Cross,
        line_sha256,
    }
}

#[test]
#[allow(clippy::too_many_lines)]
fn diagonal_each_unified_and_clear_keep_explicit_logical_bindings() -> TestResult {
    let header = header()?;
    let section = ordinary_section();
    let binding = binding(false, false)?;
    let source = TablePropertiesHwpxReader::read_existing(
        &header,
        &section,
        0,
        &binding,
        TablePropertiesHwpxLimits::default(),
    )?;
    let diagonal_line = line(LineType2::DashDot, Color::Rgb(9, 8, 7));
    let value = diagonal_value(TablePropertiesHwpxValueCatalog::line_sha256(diagonal_line)?);
    let each = plan(
        &source,
        vec![
            CellCoordinate { row: 0, column: 0 },
            CellCoordinate { row: 1, column: 1 },
        ],
        TablePropertiesOperation::CellDiagonal {
            apply_mode: TableDiagonalApplyMode::EachCell,
            patch: TableDiagonalPatch::Set {
                value: value.clone(),
            },
        },
    )?;
    let first = TablePropertiesHwpxLowerer::lower_existing(
        &header,
        &section,
        0,
        &binding,
        &part_binding(&source)?,
        &"f".repeat(64),
        &source.state,
        &source.grid,
        &each,
        &TablePropertiesHwpxValueCatalog {
            lines: vec![diagonal_line],
            ..TablePropertiesHwpxValueCatalog::default()
        },
        TablePropertiesHwpxLimits::default(),
    )?;
    assert_eq!(first.binding.diagonals.len(), 2);
    let mut incomplete_unified = first.binding.clone();
    incomplete_unified.diagonals[0].apply_mode = TableDiagonalApplyMode::Unified;
    incomplete_unified.diagonals[0].region = Some(TablePropertyRegion::new(0, 0, 2, 2)?);
    assert!(matches!(
        TablePropertiesHwpxReader::read_existing(
            &first.header,
            &first.section,
            0,
            &incomplete_unified,
            TablePropertiesHwpxLimits::default(),
        ),
        Err(TablePropertiesHwpxError::DiagonalBindingMismatch)
    ));
    let missing = TablePropertiesHwpxBinding {
        table: first.binding.table.clone(),
        diagonals: Vec::new(),
    };
    assert!(matches!(
        TablePropertiesHwpxReader::read_existing(
            &first.header,
            &first.section,
            0,
            &missing,
            TablePropertiesHwpxLimits::default(),
        ),
        Err(TablePropertiesHwpxError::MissingDiagonalBinding)
    ));
    let first_read = TablePropertiesHwpxReader::read_existing(
        &first.header,
        &first.section,
        0,
        &first.binding,
        TablePropertiesHwpxLimits::default(),
    )?;
    let clear = plan(
        &first_read,
        vec![
            CellCoordinate { row: 0, column: 0 },
            CellCoordinate { row: 1, column: 1 },
        ],
        TablePropertiesOperation::CellDiagonal {
            apply_mode: TableDiagonalApplyMode::EachCell,
            patch: TableDiagonalPatch::Clear,
        },
    )?;
    let second = TablePropertiesHwpxLowerer::lower_existing(
        &first.header,
        &first.section,
        0,
        &first.binding,
        &part_binding(&first_read)?,
        &"f".repeat(64),
        &first_read.state,
        &first_read.grid,
        &clear,
        &TablePropertiesHwpxValueCatalog::default(),
        TablePropertiesHwpxLimits::default(),
    )?;
    assert!(second.binding.diagonals.is_empty());

    let base = TablePropertiesHwpxReader::read_existing(
        &header,
        &section,
        0,
        &binding,
        TablePropertiesHwpxLimits::default(),
    )?;
    let unified = plan(
        &base,
        slots(0, 0, 2, 2),
        TablePropertiesOperation::CellDiagonal {
            apply_mode: TableDiagonalApplyMode::Unified,
            patch: TableDiagonalPatch::Set { value },
        },
    )?;
    let unified_output = TablePropertiesHwpxLowerer::lower_existing(
        &header,
        &section,
        0,
        &binding,
        &part_binding(&base)?,
        &"f".repeat(64),
        &base.state,
        &base.grid,
        &unified,
        &TablePropertiesHwpxValueCatalog {
            lines: vec![diagonal_line],
            ..TablePropertiesHwpxValueCatalog::default()
        },
        TablePropertiesHwpxLimits::default(),
    )?;
    assert_eq!(unified_output.binding.diagonals.len(), 4);
    assert!(
        unified_output
            .binding
            .diagonals
            .iter()
            .all(|entry| entry.apply_mode == TableDiagonalApplyMode::Unified
                && entry.region.is_some())
    );
    Ok(())
}

#[test]
fn typed_table_and_cell_property_catalogs_lower_without_raw_xml() -> TestResult {
    let header = header()?;
    let section = ordinary_section();
    let binding = binding(false, false)?;
    let source = TablePropertiesHwpxReader::read_existing(
        &header,
        &section,
        0,
        &binding,
        TablePropertiesHwpxLimits::default(),
    )?;
    let mut table_value = source.table_value.clone();
    table_value.lock = true;
    table_value.no_adjust = true;
    let table_digest = table_value.canonical_sha256()?;
    let table_plan = plan(
        &source,
        Vec::new(),
        TablePropertiesOperation::SetProperties {
            table_properties_sha256: Some(table_digest),
            cell_properties_sha256: None,
        },
    )?;
    let first = TablePropertiesHwpxLowerer::lower_existing(
        &header,
        &section,
        0,
        &binding,
        &part_binding(&source)?,
        &"f".repeat(64),
        &source.state,
        &source.grid,
        &table_plan,
        &TablePropertiesHwpxValueCatalog {
            table_values: vec![table_value.clone()],
            ..TablePropertiesHwpxValueCatalog::default()
        },
        TablePropertiesHwpxLimits::default(),
    )?;
    let first_read = TablePropertiesHwpxReader::read_existing(
        &first.header,
        &first.section,
        0,
        &first.binding,
        TablePropertiesHwpxLimits::default(),
    )?;
    assert_eq!(first_read.table_value, table_value);

    let cell_value = TablePropertiesHwpxCellValue {
        margins: Some(CellMargins {
            left: 111,
            right: 222,
            top: 333,
            bottom: 444,
        }),
        paragraph_property_id_ref: 0,
        horizontal_alignment: HorizontalAlignment::Justify,
        vertical_alignment: CellVerticalAlignment::Bottom,
        text_direction: CellTextDirection::VerticalAll,
        protection: CellProtection::ProtectedEditable,
    };
    let cell_plan = plan(
        &first_read,
        vec![CellCoordinate { row: 1, column: 0 }],
        TablePropertiesOperation::SetProperties {
            table_properties_sha256: None,
            cell_properties_sha256: Some(cell_value.canonical_sha256()),
        },
    )?;
    let second = TablePropertiesHwpxLowerer::lower_existing(
        &first.header,
        &first.section,
        0,
        &first.binding,
        &part_binding(&first_read)?,
        &"f".repeat(64),
        &first_read.state,
        &first_read.grid,
        &cell_plan,
        &TablePropertiesHwpxValueCatalog {
            cell_values: vec![cell_value],
            ..TablePropertiesHwpxValueCatalog::default()
        },
        TablePropertiesHwpxLimits::default(),
    )?;
    let second_read = TablePropertiesHwpxReader::read_existing(
        &second.header,
        &second.section,
        0,
        &second.binding,
        TablePropertiesHwpxLimits::default(),
    )?;
    assert_eq!(second_read.cell_values[2], cell_value);
    assert!(String::from_utf8(second.section)?.contains(">C</hp:t>"));
    Ok(())
}

#[test]
fn unused_typed_catalog_values_are_prevalidated_and_debug_is_redacted() -> TestResult {
    let header = header()?;
    let section = ordinary_section();
    let binding = binding(false, false)?;
    let source = TablePropertiesHwpxReader::read_existing(
        &header,
        &section,
        0,
        &binding,
        TablePropertiesHwpxLimits::default(),
    )?;
    let mut target = source.table_value.clone();
    target.lock = true;
    let target_digest = target.canonical_sha256()?;
    let table_plan = plan(
        &source,
        Vec::new(),
        TablePropertiesOperation::SetProperties {
            table_properties_sha256: Some(target_digest),
            cell_properties_sha256: None,
        },
    )?;
    let mut invalid_cell = source.cell_values[0];
    invalid_cell.paragraph_property_id_ref = 123_456;
    let invalid_table_digest = "a".repeat(64);
    let mut invalid_table = target.clone();
    invalid_table
        .border_fill_sha256
        .clone_from(&invalid_table_digest);
    let values = TablePropertiesHwpxValueCatalog {
        table_values: vec![target, invalid_table],
        cell_values: vec![invalid_cell],
        ..TablePropertiesHwpxValueCatalog::default()
    };
    let debug = format!("{values:?}");
    assert!(!debug.contains(&invalid_table_digest));
    assert!(!debug.contains("123456"));
    assert!(matches!(
        TablePropertiesHwpxLowerer::lower_existing(
            &header,
            &section,
            0,
            &binding,
            &part_binding(&source)?,
            &"f".repeat(64),
            &source.state,
            &source.grid,
            &table_plan,
            &values,
            TablePropertiesHwpxLimits::default(),
        ),
        Err(TablePropertiesHwpxError::MissingCatalogValue)
    ));
    Ok(())
}

#[test]
fn clear_removes_only_selected_border_sides_background_and_diagonal() -> TestResult {
    let header = header()?;
    let section = ordinary_section();
    let binding = binding(false, false)?;
    let source = TablePropertiesHwpxReader::read_existing(
        &header,
        &section,
        0,
        &binding,
        TablePropertiesHwpxLimits::default(),
    )?;
    let fill = background();
    let first_plan = plan(
        &source,
        vec![CellCoordinate { row: 0, column: 0 }],
        TablePropertiesOperation::BorderEach {
            border: TableCellBorderPatch {
                top: preserve(),
                right: preserve(),
                bottom: preserve(),
                left: preserve(),
            },
            background: set(TablePropertiesHwpxValueCatalog::background_sha256(&fill)),
        },
    )?;
    let first = TablePropertiesHwpxLowerer::lower_existing(
        &header,
        &section,
        0,
        &binding,
        &part_binding(&source)?,
        &"f".repeat(64),
        &source.state,
        &source.grid,
        &first_plan,
        &TablePropertiesHwpxValueCatalog {
            backgrounds: vec![fill],
            ..TablePropertiesHwpxValueCatalog::default()
        },
        TablePropertiesHwpxLimits::default(),
    )?;
    let first_read = TablePropertiesHwpxReader::read_existing(
        &first.header,
        &first.section,
        0,
        &first.binding,
        TablePropertiesHwpxLimits::default(),
    )?;
    let clear = TablePropertyDigestPatch::Clear;
    let clear_plan = plan(
        &first_read,
        vec![CellCoordinate { row: 0, column: 0 }],
        TablePropertiesOperation::BorderEach {
            border: TableCellBorderPatch {
                top: clear.clone(),
                right: clear.clone(),
                bottom: clear.clone(),
                left: clear,
            },
            background: TablePropertyDigestPatch::Clear,
        },
    )?;
    let second = TablePropertiesHwpxLowerer::lower_existing(
        &first.header,
        &first.section,
        0,
        &first.binding,
        &part_binding(&first_read)?,
        &"f".repeat(64),
        &first_read.state,
        &first_read.grid,
        &clear_plan,
        &TablePropertiesHwpxValueCatalog::default(),
        TablePropertiesHwpxLimits::default(),
    )?;
    let reopened = TablePropertiesHwpxReader::read_existing(
        &second.header,
        &second.section,
        0,
        &second.binding,
        TablePropertiesHwpxLimits::default(),
    )?;
    let changed = &reopened.state.cells()[0].properties;
    assert_eq!(changed.borders.top_sha256, None);
    assert_eq!(changed.borders.right_sha256, None);
    assert_eq!(changed.borders.bottom_sha256, None);
    assert_eq!(changed.borders.left_sha256, None);
    assert_eq!(changed.background_sha256, None);
    assert_eq!(
        reopened.state.cells()[1].properties,
        source.state.cells()[1].properties
    );
    Ok(())
}

#[test]
fn typed_table_border_fill_is_interned_and_exactly_reopened() -> TestResult {
    let header = header()?;
    let section = ordinary_section();
    let binding = binding(false, false)?;
    let source = TablePropertiesHwpxReader::read_existing(
        &header,
        &section,
        0,
        &binding,
        TablePropertiesHwpxLimits::default(),
    )?;
    let catalog = ParagraphStyleCatalogReader::read(&header, ParagraphStyleLimits::default())?;
    let mut border = catalog
        .border_fills
        .iter()
        .find(|value| value.id == 3)
        .ok_or("solid border missing")?
        .clone();
    border.id = 0;
    border.three_d = true;
    border.shadow = true;
    border.left = line(LineType2::DoubleSlim, Color::Rgb(20, 30, 40));
    border.fill_brush = Some(background());
    let mut table_value = source.table_value.clone();
    table_value.lock = true;
    table_value.border_fill_sha256 = TablePropertiesHwpxValueCatalog::border_fill_sha256(&border);
    let table_plan = plan(
        &source,
        Vec::new(),
        TablePropertiesOperation::SetProperties {
            table_properties_sha256: Some(table_value.canonical_sha256()?),
            cell_properties_sha256: None,
        },
    )?;
    let output = TablePropertiesHwpxLowerer::lower_existing(
        &header,
        &section,
        0,
        &binding,
        &part_binding(&source)?,
        &"f".repeat(64),
        &source.state,
        &source.grid,
        &table_plan,
        &TablePropertiesHwpxValueCatalog {
            table_values: vec![table_value.clone()],
            border_fills: vec![border],
            ..TablePropertiesHwpxValueCatalog::default()
        },
        TablePropertiesHwpxLimits::default(),
    )?;
    assert_eq!(output.receipt.added_border_fill_count, 1);
    let reopened = TablePropertiesHwpxReader::read_existing(
        &output.header,
        &output.section,
        0,
        &output.binding,
        TablePropertiesHwpxLimits::default(),
    )?;
    assert_eq!(reopened.table_value, table_value);
    assert_eq!(reopened.border_fill_count, source.border_fill_count + 1);
    Ok(())
}

#[test]
fn source_state_grid_and_output_bounds_fail_closed() -> TestResult {
    let header = header()?;
    let section = ordinary_section();
    let binding = binding(false, false)?;
    let source = TablePropertiesHwpxReader::read_existing(
        &header,
        &section,
        0,
        &binding,
        TablePropertiesHwpxLimits::default(),
    )?;
    let dot = line(LineType2::Dot, Color::Rgb(1, 2, 3));
    let plan = plan(
        &source,
        vec![CellCoordinate { row: 0, column: 0 }],
        TablePropertiesOperation::BorderEach {
            border: TableCellBorderPatch {
                top: set(TablePropertiesHwpxValueCatalog::line_sha256(dot)?),
                right: preserve(),
                bottom: preserve(),
                left: preserve(),
            },
            background: preserve(),
        },
    )?;
    let drifted_section = String::from_utf8(section.clone())?
        .replacen(">A</hp:t>", ">Z</hp:t>", 1)
        .into_bytes();
    let drifted = TablePropertiesHwpxReader::read_existing(
        &header,
        &drifted_section,
        0,
        &binding,
        TablePropertiesHwpxLimits::default(),
    )?;
    assert!(matches!(
        TablePropertiesHwpxLowerer::lower_existing(
            &header,
            &drifted_section,
            0,
            &binding,
            &part_binding(&drifted)?,
            &"f".repeat(64),
            &source.state,
            &source.grid,
            &plan,
            &TablePropertiesHwpxValueCatalog {
                lines: vec![dot],
                ..TablePropertiesHwpxValueCatalog::default()
            },
            TablePropertiesHwpxLimits::default(),
        ),
        Err(TablePropertiesHwpxError::SourceStateMismatch)
    ));

    let layout_config = TableLayoutHwpxLimitConfig {
        output_bytes: section.len() - 1,
        ..TableLayoutHwpxLimitConfig::default()
    };
    let limits = TablePropertiesHwpxLimits {
        native: TableRulingHwpxLimits {
            layout: TableLayoutHwpxLimits::new(layout_config)?,
            ..TableRulingHwpxLimits::default()
        },
        ..TablePropertiesHwpxLimits::default()
    };
    assert!(matches!(
        TablePropertiesHwpxLowerer::lower_existing(
            &header,
            &section,
            0,
            &binding,
            &part_binding(&source)?,
            &"f".repeat(64),
            &source.state,
            &source.grid,
            &plan,
            &TablePropertiesHwpxValueCatalog {
                lines: vec![dot],
                ..TablePropertiesHwpxValueCatalog::default()
            },
            limits,
        ),
        Err(TablePropertiesHwpxError::Native(
            TableRulingHwpxError::OutputLimit
        ))
    ));
    Ok(())
}

#[test]
#[allow(clippy::too_many_lines)]
fn closed_package_preserves_unselected_table_formula_pagination_and_other_parts() -> TestResult {
    let header = header()?;
    let first_table = table_fragment(ordinary_section())?;
    let second_table = table_fragment(formula_section())?.replacen("id=\"700\"", "id=\"701\"", 1);
    let section = format!(
        r#"<hs:sec xmlns:hs="{SECTION_NS}" xmlns:hp="{PARAGRAPH_NS}">{first_table}{second_table}</hs:sec>"#
    )
    .into_bytes();
    let source_package = package(&header, &section)?;
    let immutable_source = source_package.clone();
    let (source_graph, source_header, source_section) = inspect_package(&source_package)?;
    let hashes = part_hashes(&source_graph);
    let source_formula = TableFormulaHwpxReader::read_in_section(
        &source_section,
        1,
        TableFormulaHwpxLimits::default(),
        FormulaLimits::default(),
    )?;
    let source_pagination = TablePaginationHwpxReader::read_in_section(
        &source_section,
        1,
        TablePaginationHwpxLimits::default(),
    )?;
    let binding = binding(false, false)?;
    let source = TablePropertiesHwpxReader::read_existing(
        &source_header,
        &source_section,
        0,
        &binding,
        TablePropertiesHwpxLimits::default(),
    )?;
    let fill = background();
    let plan = plan(
        &source,
        vec![CellCoordinate { row: 0, column: 1 }],
        TablePropertiesOperation::BorderEach {
            border: TableCellBorderPatch {
                top: preserve(),
                right: preserve(),
                bottom: preserve(),
                left: preserve(),
            },
            background: set(TablePropertiesHwpxValueCatalog::background_sha256(&fill)),
        },
    )?;
    let lowered = TablePropertiesHwpxLowerer::lower_existing(
        &source_header,
        &source_section,
        0,
        &binding,
        &part_binding(&source)?,
        &"f".repeat(64),
        &source.state,
        &source.grid,
        &plan,
        &TablePropertiesHwpxValueCatalog {
            backgrounds: vec![fill],
            ..TablePropertiesHwpxValueCatalog::default()
        },
        TablePropertiesHwpxLimits::default(),
    )?;
    let target_package =
        replace_header_and_section(&source_package, &lowered.header, &lowered.section)?;
    assert_eq!(source_package, immutable_source);
    assert_eq!(
        target_package,
        replace_header_and_section(&source_package, &lowered.header, &lowered.section)?
    );
    let (target_graph, target_header, target_section) = inspect_package(&target_package)?;
    assert_eq!(source_graph.package_document, target_graph.package_document);
    assert_eq!(source_graph.relationships, target_graph.relationships);
    assert_eq!(source_graph.spine, target_graph.spine);
    let target_hashes = part_hashes(&target_graph);
    for (path, source_hash) in hashes {
        let target_hash = target_hashes.get(&path).ok_or("target part missing")?;
        if matches!(
            path.as_str(),
            "Contents/header.xml" | "Contents/section0.xml"
        ) {
            assert_ne!(&source_hash, target_hash);
        } else {
            assert_eq!(&source_hash, target_hash);
        }
    }
    let reopened = TablePropertiesHwpxReader::read_existing(
        &target_header,
        &target_section,
        0,
        &lowered.binding,
        TablePropertiesHwpxLimits::default(),
    )?;
    assert_eq!(
        reopened.state.cells()[1].properties,
        plan.mutations()[0].after
    );
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
    assert_eq!(source_formula.formula, target_formula.formula);
    assert_eq!(source_pagination, target_pagination);
    Ok(())
}

#[test]
fn part_state_flow_and_catalog_drift_fail_closed() -> TestResult {
    let header = header()?;
    let section = ordinary_section();
    let binding = binding(false, false)?;
    let source = TablePropertiesHwpxReader::read_existing(
        &header,
        &section,
        0,
        &binding,
        TablePropertiesHwpxLimits::default(),
    )?;
    let dot = line(LineType2::Dot, Color::Rgb(1, 1, 1));
    let plan = plan(
        &source,
        vec![CellCoordinate { row: 0, column: 0 }],
        TablePropertiesOperation::BorderEach {
            border: TableCellBorderPatch {
                top: set(TablePropertiesHwpxValueCatalog::line_sha256(dot)?),
                right: preserve(),
                bottom: preserve(),
                left: preserve(),
            },
            background: preserve(),
        },
    )?;
    let part = part_binding(&source)?;
    assert!(matches!(
        TablePropertiesHwpxLowerer::lower_existing(
            &header,
            &section,
            0,
            &binding,
            &part,
            &"e".repeat(64),
            &source.state,
            &source.grid,
            &plan,
            &TablePropertiesHwpxValueCatalog {
                lines: vec![dot],
                ..TablePropertiesHwpxValueCatalog::default()
            },
            TablePropertiesHwpxLimits::default(),
        ),
        Err(TablePropertiesHwpxError::PartBindingMismatch)
    ));
    assert!(matches!(
        TablePropertiesHwpxLowerer::lower_existing(
            &header,
            &section,
            0,
            &binding,
            &part,
            &"f".repeat(64),
            &source.state,
            &source.grid,
            &plan,
            &TablePropertiesHwpxValueCatalog::default(),
            TablePropertiesHwpxLimits::default(),
        ),
        Err(TablePropertiesHwpxError::MissingCatalogValue)
    ));
    let mut drifted = section.clone();
    let last = drifted.len() - 1;
    drifted[last] = b' ';
    assert!(matches!(
        TablePropertiesHwpxLowerer::lower_existing(
            &header,
            &drifted,
            0,
            &binding,
            &part,
            &"f".repeat(64),
            &source.state,
            &source.grid,
            &plan,
            &TablePropertiesHwpxValueCatalog {
                lines: vec![dot],
                ..TablePropertiesHwpxValueCatalog::default()
            },
            TablePropertiesHwpxLimits::default(),
        ),
        Err(TablePropertiesHwpxError::PartBindingMismatch)
    ));
    Ok(())
}

#[test]
fn malformed_cell_shape_and_ambiguous_diagonal_bindings_are_rejected() -> TestResult {
    let header = header()?;
    let section = ordinary_section();
    let binding = binding(false, false)?;
    let malformed = String::from_utf8(section.clone())?
        .replacen(" dirty=\"0\"", " unknown=\"0\"", 1)
        .into_bytes();
    assert!(matches!(
        TablePropertiesHwpxReader::read_existing(
            &header,
            &malformed,
            0,
            &binding,
            TablePropertiesHwpxLimits::default(),
        ),
        Err(TablePropertiesHwpxError::CellStyle(_) | TablePropertiesHwpxError::Native(_))
    ));

    let catalog = ParagraphStyleCatalogReader::read(&header, ParagraphStyleLimits::default())?;
    let source_border = catalog
        .border_fills
        .iter()
        .find(|value| value.id == 3)
        .ok_or("missing source border")?;
    let diagonal_border = BorderFill {
        id: 0,
        slash: Slash {
            slash_type: SlashType::Center,
            crooked: false,
            is_counter: false,
        },
        back_slash: Slash {
            slash_type: SlashType::None,
            crooked: false,
            is_counter: false,
        },
        center_line: CenterLine::None,
        ..source_border.clone()
    };
    let line_sha256 = TablePropertiesHwpxValueCatalog::line_sha256(diagonal_border.diagonal)?;
    let duplicate = TablePropertiesHwpxDiagonalBinding {
        master_cell_id: id("cell-0-0")?,
        apply_mode: TableDiagonalApplyMode::EachCell,
        region: None,
        value: TableDiagonalValue {
            slash: TableDiagonalSlash {
                slash_type: TableDiagonalSlashType::Center,
                crooked: false,
                is_counter: false,
            },
            back_slash: TableDiagonalSlash {
                slash_type: TableDiagonalSlashType::None,
                crooked: false,
                is_counter: false,
            },
            center_line: TableDiagonalCenterLine::None,
            line_sha256,
        },
    };
    let ambiguous = TablePropertiesHwpxBinding {
        table: binding.table,
        diagonals: vec![duplicate.clone(), duplicate],
    };
    assert!(matches!(
        TablePropertiesHwpxReader::read_existing(
            &header,
            &section,
            0,
            &ambiguous,
            TablePropertiesHwpxLimits::default(),
        ),
        Err(TablePropertiesHwpxError::InvalidBinding)
    ));
    Ok(())
}

#[test]
#[allow(clippy::too_many_lines)]
fn table_style_full_regions_round_trip_table_cells_formula_and_pagination() -> TestResult {
    let header = header()?;
    let section = formula_section();
    let binding = binding(false, true)?;
    let source = TableStyleHwpxReader::read_existing(
        &header,
        &section,
        0,
        &binding,
        TableStyleHwpxLimits::default(),
    )?;
    assert_eq!(source.profile_id, TABLE_STYLE_HWPX_PROFILE_ID);
    let source_formula = TableFormulaHwpxReader::read_in_section(
        &section,
        0,
        TableFormulaHwpxLimits::default(),
        FormulaLimits::default(),
    )?;
    let source_pagination = TablePaginationHwpxReader::read_in_section(
        &section,
        0,
        TablePaginationHwpxLimits::default(),
    )?;

    let bottom = line(LineType2::Dash, Color::Rgb(0x22, 0x44, 0x66));
    let top = line(LineType2::DoubleSlim, Color::Rgb(0x77, 0x55, 0x33));
    let fill = background();
    let mut whole = style_value(&source, &binding, 0)?;
    whole.borders.bottom_sha256 = Some(TablePropertiesHwpxValueCatalog::line_sha256(bottom)?);
    let mut header_style = whole.clone();
    header_style.borders.top_sha256 = Some(TablePropertiesHwpxValueCatalog::line_sha256(top)?);
    header_style.background_sha256 =
        Some(TablePropertiesHwpxValueCatalog::background_sha256(&fill));
    header_style.non_border = TablePropertiesHwpxCellValue {
        margins: Some(CellMargins {
            left: 111,
            right: 222,
            top: 333,
            bottom: 444,
        }),
        paragraph_property_id_ref: 0,
        horizontal_alignment: HorizontalAlignment::Justify,
        vertical_alignment: CellVerticalAlignment::Bottom,
        text_direction: CellTextDirection::VerticalAll,
        protection: CellProtection::ProtectedEditable,
    };
    let whole_sha256 = whole.canonical_sha256()?;
    let header_sha256 = header_style.canonical_sha256()?;
    let mut table_value = source.properties.table_value.clone();
    table_value.lock = true;
    table_value.no_adjust = true;
    let definition = style_definition(
        table_value.canonical_sha256()?,
        vec![
            TableStyleRule {
                region: TableStyleRegion::HeaderRows,
                cell_style_sha256: header_sha256,
            },
            TableStyleRule {
                region: TableStyleRegion::WholeTable,
                cell_style_sha256: whole_sha256,
            },
        ],
    )?;
    let (request, plan) = style_plan(&source, &definition, 1, TableStyleColumnEmphasis::None)?;
    let part = style_part_binding(&source, &request, &definition, &plan)?;
    let output = TableStyleHwpxLowerer::lower_existing(
        &header,
        &section,
        0,
        &binding,
        &part,
        &"f".repeat(64),
        &request,
        &definition,
        &plan,
        &TableStyleHwpxValueCatalog {
            table_values: vec![table_value.clone()],
            cell_styles: vec![whole, header_style],
            lines: vec![bottom, top],
            backgrounds: vec![fill],
            border_fills: Vec::new(),
        },
        TableStyleHwpxLimits::default(),
    )?;
    assert_eq!(output.receipt.changed_master_cell_count, 4);
    assert_eq!(output.receipt.preserved_payload_count, 4);
    assert_eq!(output.receipt.preserved_formula_count, 1);
    assert_eq!(output.receipt.normalized_unified_diagonal_cell_count, 0);
    let reopened = TableStyleHwpxReader::read_existing(
        &output.header,
        &output.section,
        0,
        &output.binding,
        TableStyleHwpxLimits::default(),
    )?;
    assert_eq!(reopened.properties.table_value, table_value);
    assert_eq!(
        reopened.cell_style_sha256,
        plan.mutations()
            .iter()
            .map(|mutation| mutation.after_style_sha256.clone())
            .collect::<Vec<_>>()
    );
    let target_formula = TableFormulaHwpxReader::read_in_section(
        &output.section,
        0,
        TableFormulaHwpxLimits::default(),
        FormulaLimits::default(),
    )?;
    let target_pagination = TablePaginationHwpxReader::read_in_section(
        &output.section,
        0,
        TablePaginationHwpxLimits::default(),
    )?;
    assert_eq!(source_formula.formula, target_formula.formula);
    assert_eq!(source_pagination, target_pagination);
    assert!(String::from_utf8(output.section)?.contains(">BEFORE</hp:t>"));
    Ok(())
}

#[test]
#[allow(clippy::too_many_lines)]
fn table_style_breaks_only_untruthful_unified_diagonal_groups() -> TestResult {
    let header = header()?;
    let section = ordinary_section();
    let binding = binding(false, false)?;
    let properties = TablePropertiesHwpxReader::read_existing(
        &header,
        &section,
        0,
        &binding,
        TablePropertiesHwpxLimits::default(),
    )?;
    let diagonal_line = line(LineType2::Solid, Color::Rgb(0x12, 0x34, 0x56));
    let diagonal = diagonal_value(TablePropertiesHwpxValueCatalog::line_sha256(diagonal_line)?);
    let diagonal_plan = plan(
        &properties,
        slots(0, 0, 2, 2),
        TablePropertiesOperation::CellDiagonal {
            apply_mode: TableDiagonalApplyMode::Unified,
            patch: TableDiagonalPatch::Set {
                value: diagonal.clone(),
            },
        },
    )?;
    let diagonal_output = TablePropertiesHwpxLowerer::lower_existing(
        &header,
        &section,
        0,
        &binding,
        &part_binding(&properties)?,
        &"f".repeat(64),
        &properties.state,
        &properties.grid,
        &diagonal_plan,
        &TablePropertiesHwpxValueCatalog {
            lines: vec![diagonal_line],
            ..TablePropertiesHwpxValueCatalog::default()
        },
        TablePropertiesHwpxLimits::default(),
    )?;
    let source = TableStyleHwpxReader::read_existing(
        &diagonal_output.header,
        &diagonal_output.section,
        0,
        &diagonal_output.binding,
        TableStyleHwpxLimits::default(),
    )?;
    let whole = style_value(&source, &diagonal_output.binding, 0)?;
    let mut first_column = whole.clone();
    first_column.diagonal = None;
    let definition = style_definition(
        source.properties.state.table_properties_sha256().to_owned(),
        vec![
            TableStyleRule {
                region: TableStyleRegion::WholeTable,
                cell_style_sha256: whole.canonical_sha256()?,
            },
            TableStyleRule {
                region: TableStyleRegion::FirstColumn,
                cell_style_sha256: first_column.canonical_sha256()?,
            },
        ],
    )?;
    let (request, style_plan) =
        style_plan(&source, &definition, 0, TableStyleColumnEmphasis::First)?;
    let output = TableStyleHwpxLowerer::lower_existing(
        &diagonal_output.header,
        &diagonal_output.section,
        0,
        &diagonal_output.binding,
        &style_part_binding(&source, &request, &definition, &style_plan)?,
        &"f".repeat(64),
        &request,
        &definition,
        &style_plan,
        &TableStyleHwpxValueCatalog {
            cell_styles: vec![whole, first_column],
            lines: vec![diagonal_line],
            ..TableStyleHwpxValueCatalog::default()
        },
        TableStyleHwpxLimits::default(),
    )?;
    assert_eq!(output.binding.diagonals.len(), 2);
    assert!(
        output
            .binding
            .diagonals
            .iter()
            .all(|entry| entry.apply_mode == TableDiagonalApplyMode::EachCell
                && entry.region.is_none()
                && entry.value == diagonal)
    );
    assert_eq!(output.receipt.normalized_unified_diagonal_cell_count, 2);
    let reopened = TableStyleHwpxReader::read_existing(
        &output.header,
        &output.section,
        0,
        &output.binding,
        TableStyleHwpxLimits::default(),
    )?;
    assert_eq!(
        reopened.cell_style_sha256,
        style_plan
            .mutations()
            .iter()
            .map(|mutation| mutation.after_style_sha256.clone())
            .collect::<Vec<_>>()
    );
    Ok(())
}

#[test]
#[allow(clippy::too_many_lines)]
fn table_style_part_state_plan_and_complete_catalog_drift_fail_closed() -> TestResult {
    let header = header()?;
    let section = ordinary_section();
    let binding = binding(false, false)?;
    let source = TableStyleHwpxReader::read_existing(
        &header,
        &section,
        0,
        &binding,
        TableStyleHwpxLimits::default(),
    )?;
    let whole = style_value(&source, &binding, 0)?;
    let definition = style_definition(
        source.properties.state.table_properties_sha256().to_owned(),
        vec![TableStyleRule {
            region: TableStyleRegion::WholeTable,
            cell_style_sha256: whole.canonical_sha256()?,
        }],
    )?;
    let (request, plan) = style_plan(&source, &definition, 0, TableStyleColumnEmphasis::None)?;
    let part = style_part_binding(&source, &request, &definition, &plan)?;
    assert!(matches!(
        TableStyleHwpxLowerer::lower_existing(
            &header,
            &section,
            0,
            &binding,
            &part,
            &"e".repeat(64),
            &request,
            &definition,
            &plan,
            &TableStyleHwpxValueCatalog {
                cell_styles: vec![whole.clone()],
                ..TableStyleHwpxValueCatalog::default()
            },
            TableStyleHwpxLimits::default(),
        ),
        Err(TableStyleHwpxError::PartBindingMismatch)
    ));
    assert!(matches!(
        TableStyleHwpxLowerer::lower_existing(
            &header,
            &section,
            0,
            &binding,
            &part,
            &"f".repeat(64),
            &request,
            &definition,
            &plan,
            &TableStyleHwpxValueCatalog::default(),
            TableStyleHwpxLimits::default(),
        ),
        Err(TableStyleHwpxError::MissingCatalogValue)
    ));

    let mut invalid = whole.clone();
    invalid.non_border.paragraph_property_id_ref = 123_456;
    let values = TableStyleHwpxValueCatalog {
        cell_styles: vec![whole.clone(), invalid],
        ..TableStyleHwpxValueCatalog::default()
    };
    assert!(matches!(
        TableStyleHwpxLowerer::lower_existing(
            &header,
            &section,
            0,
            &binding,
            &part,
            &"f".repeat(64),
            &request,
            &definition,
            &plan,
            &values,
            TableStyleHwpxLimits::default(),
        ),
        Err(TableStyleHwpxError::Properties(
            TablePropertiesHwpxError::MissingCatalogValue
        ))
    ));
    let drifted_section = String::from_utf8(section.clone())?
        .replacen(">A</hp:t>", ">Z</hp:t>", 1)
        .into_bytes();
    let drifted = TableStyleHwpxReader::read_existing(
        &header,
        &drifted_section,
        0,
        &binding,
        TableStyleHwpxLimits::default(),
    )?;
    let mut drift_binding = part.clone();
    drift_binding.section_sha256 = hex(drifted.properties.section_sha256);
    drift_binding.source_style_state_sha256 = hex(drifted.style_state_sha256);
    assert!(matches!(
        TableStyleHwpxLowerer::lower_existing(
            &header,
            &drifted_section,
            0,
            &binding,
            &drift_binding,
            &"f".repeat(64),
            &request,
            &definition,
            &plan,
            &TableStyleHwpxValueCatalog {
                cell_styles: vec![whole.clone()],
                ..TableStyleHwpxValueCatalog::default()
            },
            TableStyleHwpxLimits::default(),
        ),
        Err(TableStyleHwpxError::SourceStateMismatch)
    ));
    let debug = format!("{part:?}{values:?}{source:?}");
    assert!(!debug.contains("table-properties"));
    assert!(!debug.contains(&part.request_sha256));
    let diagonal_secret = "d".repeat(64);
    let mut diagonal_debug = whole.clone();
    diagonal_debug.diagonal = Some(diagonal_value(diagonal_secret.clone()));
    assert!(!format!("{diagonal_debug:?}").contains(&diagonal_secret));
    let mut malformed = whole;
    malformed.background_sha256 = Some("not-a-digest".to_owned());
    assert!(matches!(
        malformed.canonical_sha256(),
        Err(TableStyleHwpxError::InvalidStyleValue)
    ));
    assert_eq!(
        TableStyleHwpxError::PlanBindingMismatch.code(),
        "table_style_hwpx_plan_binding_mismatch"
    );
    Ok(())
}

#[test]
#[allow(clippy::too_many_lines)]
fn table_style_closed_package_preserves_other_table_and_non_section_parts() -> TestResult {
    let header = header()?;
    let first_table = table_fragment(ordinary_section())?;
    let second_table = table_fragment(formula_section())?.replacen("id=\"700\"", "id=\"701\"", 1);
    let section = format!(
        r#"<hs:sec xmlns:hs="{SECTION_NS}" xmlns:hp="{PARAGRAPH_NS}">{first_table}{second_table}</hs:sec>"#
    )
    .into_bytes();
    let source_package = package(&header, &section)?;
    let immutable_source = source_package.clone();
    let (source_graph, source_header, source_section) = inspect_package(&source_package)?;
    let hashes = part_hashes(&source_graph);
    let other_formula = TableFormulaHwpxReader::read_in_section(
        &source_section,
        1,
        TableFormulaHwpxLimits::default(),
        FormulaLimits::default(),
    )?;
    let binding = binding(false, false)?;
    let source = TableStyleHwpxReader::read_existing(
        &source_header,
        &source_section,
        0,
        &binding,
        TableStyleHwpxLimits::default(),
    )?;
    let fill = background();
    let mut whole = style_value(&source, &binding, 0)?;
    whole.background_sha256 = Some(TablePropertiesHwpxValueCatalog::background_sha256(&fill));
    let definition = style_definition(
        source.properties.state.table_properties_sha256().to_owned(),
        vec![TableStyleRule {
            region: TableStyleRegion::WholeTable,
            cell_style_sha256: whole.canonical_sha256()?,
        }],
    )?;
    let (request, plan) = style_plan(&source, &definition, 0, TableStyleColumnEmphasis::None)?;
    let lowered = TableStyleHwpxLowerer::lower_existing(
        &source_header,
        &source_section,
        0,
        &binding,
        &style_part_binding(&source, &request, &definition, &plan)?,
        &"f".repeat(64),
        &request,
        &definition,
        &plan,
        &TableStyleHwpxValueCatalog {
            cell_styles: vec![whole],
            backgrounds: vec![fill],
            ..TableStyleHwpxValueCatalog::default()
        },
        TableStyleHwpxLimits::default(),
    )?;
    let target_package =
        replace_header_and_section(&source_package, &lowered.header, &lowered.section)?;
    assert_eq!(source_package, immutable_source);
    let (target_graph, _, target_section) = inspect_package(&target_package)?;
    assert_eq!(source_graph.package_document, target_graph.package_document);
    assert_eq!(source_graph.relationships, target_graph.relationships);
    assert_eq!(source_graph.spine, target_graph.spine);
    let target_hashes = part_hashes(&target_graph);
    for (path, source_hash) in hashes {
        let target_hash = target_hashes.get(&path).ok_or("target part missing")?;
        if matches!(
            path.as_str(),
            "Contents/header.xml" | "Contents/section0.xml"
        ) {
            assert_ne!(&source_hash, target_hash);
        } else {
            assert_eq!(&source_hash, target_hash);
        }
    }
    assert!(String::from_utf8(target_section.clone())?.contains(&second_table));
    let target_formula = TableFormulaHwpxReader::read_in_section(
        &target_section,
        1,
        TableFormulaHwpxLimits::default(),
        FormulaLimits::default(),
    )?;
    assert_eq!(other_formula.formula, target_formula.formula);
    Ok(())
}
