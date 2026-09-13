use std::io::{Cursor, Write};

use domain_ir::{
    CellCoordinate, FormulaDecimal, LogicalId, TABLE_CHART_SCHEMA_VERSION, TableChartBuilder,
    TableChartCellDraft, TableChartLimits, TableChartRegion, TableChartRequest,
    TableChartRequestDraft, TableChartSourceState, TableChartSourceStateDraft, TableChartValue,
    TableChartValueOrigin,
};
use hwpx_package::{
    BoundedZipReader, IdIndexLimits, PackageGraph, PackageGraphLimits, PackageLimits,
    PreservingWriter, TABLE_CHART_HWPX_PROFILE_ID, TABLE_CHART_HWPX_SCHEMA_VERSION,
    TableChartHwpxBuilder, TableChartHwpxError, TableChartHwpxLimits, TableChartHwpxLowerer,
    TableChartHwpxRequest, TableChartHwpxRequestDraft, TableRulingHwpxBinding,
    TableRulingHwpxCellBinding, TableRulingHwpxLimits, TableRulingHwpxReader, WriterLimits,
};
use sha2::{Digest as _, Sha256};
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
    <opf:item id="preview" href="../Preview/PrvText.txt" media-type="text/plain"/>
  </opf:manifest>
  <opf:spine><opf:itemref idref="section0" linear="yes"/></opf:spine>
</opf:package>"#;

struct Fixture {
    package: Vec<u8>,
    binding: TableRulingHwpxBinding,
    state: TableChartSourceState,
    plan: domain_ir::TableChartPlan,
    source: hwpx_package::TableChartHwpxSource,
    request: TableChartHwpxRequest,
    flow: String,
}

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

fn header() -> TestResult<Vec<u8>> {
    let source = String::from_utf8(HEADER.to_vec())?;
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
    Ok(source
        .replacen(
            "<hh:borderFills itemCnt=\"2\">",
            "<hh:borderFills itemCnt=\"3\">",
            1,
        )
        .replacen("</hh:borderFills>", &format!("{solid}</hh:borderFills>"), 1)
        .into_bytes())
}

fn text_paragraph(value: &str) -> String {
    format!(
        r#"<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t>{value}</hp:t></hp:run></hp:p>"#
    )
}

fn formula_field() -> &'static str {
    concat!(
        r#"<hp:fieldBegin id="101" type="FORMULA" name="" editable="0" dirty="0" zorder="-1" fieldid="202">"#,
        r#"<hp:parameters cnt="5" name=""><hp:integerParam name="Prop">8</hp:integerParam>"#,
        r#"<hp:stringParam name="Command">=SUM(LEFT)??%g,;;4</hp:stringParam>"#,
        r#"<hp:stringParam name="Formula">=SUM(LEFT)</hp:stringParam>"#,
        r#"<hp:stringParam name="ResultFormat">%g,</hp:stringParam>"#,
        r#"<hp:stringParam name="LastResult">4</hp:stringParam></hp:parameters>"#,
        r#"</hp:fieldBegin>"#,
    )
}

fn formula_paragraph() -> String {
    format!(
        concat!(
            r#"<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:ctrl>"#,
            "{field}",
            r#"</hp:ctrl><hp:t>4</hp:t><hp:ctrl><hp:fieldEnd beginIDRef="101" fieldid="202"/>"#,
            r#"</hp:ctrl><hp:t/></hp:run></hp:p>"#,
        ),
        field = formula_field(),
    )
}

fn formula_origin() -> TableChartValueOrigin {
    let mut formula = Sha256::new();
    formula.update(TABLE_CHART_HWPX_PROFILE_ID.as_bytes());
    formula.update(b"\0formula-origin\0");
    formula.update(formula_field().as_bytes());
    let mut cache = Sha256::new();
    cache.update(TABLE_CHART_HWPX_PROFILE_ID.as_bytes());
    cache.update(b"\0formula-display-cache\0");
    cache.update(b"4");
    TableChartValueOrigin::FormulaDisplayCache {
        formula_sha256: hex(formula.finalize()),
        cache_sha256: hex(cache.finalize()),
    }
}

#[allow(clippy::too_many_arguments)]
fn cell(row: u32, column: u32, payload: &str) -> String {
    format!(
        concat!(
            r#"<hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="0" borderFillIDRef="3">"#,
            r#"<hp:cellAddr colAddr="{column}" rowAddr="{row}"/>"#,
            r#"<hp:cellSpan colSpan="1" rowSpan="1"/>"#,
            r#"<hp:cellSz width="1000" height="500"/>"#,
            r#"<hp:cellMargin left="0" right="0" top="0" bottom="0"/>"#,
            r#"<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">"#,
            "{payload}</hp:subList></hp:tc>"
        ),
        row = row,
        column = column,
        payload = payload,
    )
}

fn cells() -> Vec<String> {
    let payloads = [
        text_paragraph(""),
        text_paragraph("Series A"),
        text_paragraph("Series B"),
        text_paragraph("Category A"),
        text_paragraph("1"),
        text_paragraph("2"),
        text_paragraph("Category B"),
        text_paragraph("3"),
        formula_paragraph(),
    ];
    let coordinates = [
        (0, 0),
        (0, 1),
        (0, 2),
        (1, 0),
        (1, 1),
        (1, 2),
        (2, 0),
        (2, 1),
        (2, 2),
    ];
    payloads
        .into_iter()
        .zip(coordinates)
        .map(|(payload, (row, column))| cell(row, column, &payload))
        .collect()
}

fn section(cells: &[String], wrapped: bool) -> Vec<u8> {
    let mut rows = String::new();
    for row in 0..3 {
        rows.push_str("<hp:tr>");
        for column in 0..3 {
            rows.push_str(&cells[row * 3 + column]);
        }
        rows.push_str("</hp:tr>");
    }
    let table = format!(
        concat!(
            r#"<hp:tbl id="700" zOrder="0" numberingType="TABLE" textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" pageBreak="CELL" repeatHeader="0" rowCnt="3" colCnt="3" cellSpacing="0" borderFillIDRef="1" noAdjust="0">"#,
            r#"<hp:sz width="3000" widthRelTo="ABSOLUTE" height="1500" heightRelTo="ABSOLUTE" protect="0"/>"#,
            r#"<hp:pos treatAsChar="0" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP" horzAlign="LEFT" vertOffset="2000" horzOffset="1000"/>"#,
            r#"<hp:outMargin left="0" right="0" top="0" bottom="0"/>"#,
            r#"<hp:inMargin left="0" right="0" top="0" bottom="0"/>"#,
            "{rows}</hp:tbl>"
        ),
        rows = rows,
    );
    let body = if wrapped {
        format!(
            r#"<hp:p id="800" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0">{table}<hp:t/></hp:run></hp:p>"#
        )
    } else {
        table
    };
    format!(r#"<hs:sec xmlns:hs="{SECTION_NS}" xmlns:hp="{PARAGRAPH_NS}">{body}</hs:sec>"#)
        .into_bytes()
}

fn archive(parts: Vec<(&str, Vec<u8>, CompressionMethod)>) -> TestResult<Vec<u8>> {
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

fn package(header: &[u8], section: &[u8]) -> TestResult<Vec<u8>> {
    archive(vec![
        (
            "mimetype",
            b"application/hwp+zip".to_vec(),
            CompressionMethod::Stored,
        ),
        (
            "version.xml",
            b"<version/>".to_vec(),
            CompressionMethod::Stored,
        ),
        (
            "META-INF/container.xml",
            CONTAINER.as_bytes().to_vec(),
            CompressionMethod::Deflated,
        ),
        (
            "Contents/content.hpf",
            OPF.as_bytes().to_vec(),
            CompressionMethod::Deflated,
        ),
        (
            "Contents/header.xml",
            header.to_vec(),
            CompressionMethod::Deflated,
        ),
        (
            "Contents/section0.xml",
            section.to_vec(),
            CompressionMethod::Deflated,
        ),
        (
            "Preview/PrvText.txt",
            b"<preview-text/>".to_vec(),
            CompressionMethod::Deflated,
        ),
    ])
}

fn binding() -> TestResult<TableRulingHwpxBinding> {
    let cells = (0..9)
        .map(|index| {
            Ok(TableRulingHwpxCellBinding {
                master_cell_id: id(&format!("cell-{index}"))?,
                payload_block_ids: if matches!(index, 0 | 8) {
                    Vec::new()
                } else {
                    vec![id(&format!("payload-{index}"))?]
                },
            })
        })
        .collect::<TestResult<Vec<_>>>()?;
    Ok(TableRulingHwpxBinding {
        table_id: id("table-main")?,
        row_boundaries_hwpunit: vec![0, 500, 1000, 1500],
        column_boundaries_hwpunit: vec![0, 1000, 2000, 3000],
        cells,
    })
}

fn values() -> [TableChartValue; 9] {
    [
        TableChartValue::Blank,
        TableChartValue::Text {
            value: "Series A".to_owned(),
        },
        TableChartValue::Text {
            value: "Series B".to_owned(),
        },
        TableChartValue::Text {
            value: "Category A".to_owned(),
        },
        TableChartValue::Number {
            value: FormulaDecimal::new(1, 0),
        },
        TableChartValue::Number {
            value: FormulaDecimal::new(2, 0),
        },
        TableChartValue::Text {
            value: "Category B".to_owned(),
        },
        TableChartValue::Number {
            value: FormulaDecimal::new(3, 0),
        },
        TableChartValue::Number {
            value: FormulaDecimal::new(4, 0),
        },
    ]
}

fn state(
    readback: &hwpx_package::TableRulingHwpxReadback,
    cells: &[String],
    digest_override: Option<usize>,
    formula_origin_override: bool,
    chart_limits: TableChartLimits,
) -> TestResult<TableChartSourceState> {
    let values = values();
    let mut drafts = Vec::new();
    for (index, span) in readback.grid.master_cells().iter().enumerate() {
        let source_sha256 = if digest_override == Some(index) {
            digest('9')
        } else {
            hex(Sha256::digest(cells[index].as_bytes()))
        };
        drafts.push(TableChartCellDraft {
            master_cell_id: span.master_cell_id.clone(),
            coordinate: CellCoordinate {
                row: span.row,
                column: span.column,
            },
            source_sha256,
            value: values[index].clone(),
            value_origin: if index == 8 && formula_origin_override {
                TableChartValueOrigin::FormulaDisplayCache {
                    formula_sha256: digest('7'),
                    cache_sha256: digest('8'),
                }
            } else if index == 8 {
                formula_origin()
            } else {
                TableChartValueOrigin::Literal
            },
        });
    }
    Ok(TableChartSourceState::from_draft(
        TableChartSourceStateDraft {
            schema_version: TABLE_CHART_SCHEMA_VERSION.to_owned(),
            table_id: id("table-main")?,
            grid_sha256: hex(readback.grid.canonical_sha256()?),
            table_state_sha256: hex(readback
                .state
                .canonical_sha256(TableRulingHwpxLimits::default().ruling)?),
            cells: drafts,
        },
        &readback.grid,
        chart_limits,
    )?)
}

fn make_fixture(chart_limits: TableChartLimits) -> TestResult<Fixture> {
    let header = header()?;
    let cells = cells();
    let section = section(&cells, true);
    let package = package(&header, &section)?;
    let binding = binding()?;
    let readback = TableRulingHwpxReader::read_existing(
        &header,
        &section,
        0,
        &binding,
        TableRulingHwpxLimits::default(),
    )?;
    let state = state(&readback, &cells, None, false, chart_limits)?;
    let flow = digest('e');
    let domain_request = TableChartRequest::from_draft(
        TableChartRequestDraft {
            schema_version: TABLE_CHART_SCHEMA_VERSION.to_owned(),
            table_id: state.table_id().clone(),
            chart_id: id("chart-new")?,
            data_resource_id: id("chart-data-new")?,
            source_region: TableChartRegion {
                start: CellCoordinate { row: 0, column: 0 },
                end: CellCoordinate { row: 2, column: 2 },
            },
            expected_source_state_sha256: hex(state.canonical_sha256(chart_limits)?),
            expected_document_flow_sha256: flow.clone(),
        },
        &state,
        &readback.grid,
        &flow,
        chart_limits,
    )?;
    let plan =
        TableChartBuilder::build(&domain_request, &state, &readback.grid, &flow, chart_limits)?;
    let mut reader = BoundedZipReader::open(Cursor::new(&package), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    let source = TableChartHwpxBuilder::inspect_source(
        &mut reader,
        &graph,
        "Contents/section0.xml",
        0,
        &binding,
        &state,
        TableChartHwpxLimits::default(),
        chart_limits,
    )?;
    let request = TableChartHwpxRequest::from_draft(
        TableChartHwpxRequestDraft {
            schema_version: TABLE_CHART_HWPX_SCHEMA_VERSION.to_owned(),
            profile_id: TABLE_CHART_HWPX_PROFILE_ID.to_owned(),
            section_part: source.section_part().to_owned(),
            table_ordinal: source.table_ordinal(),
            expected_package_state_sha256: source.package_state_sha256().to_owned(),
            expected_section_sha256: source.section_sha256().to_owned(),
            expected_table_sha256: source.table_sha256().to_owned(),
            expected_source_state_sha256: source.source_state_sha256().to_owned(),
            expected_source_grid_sha256: source.source_grid_sha256().to_owned(),
            expected_source_table_state_sha256: source.source_table_state_sha256().to_owned(),
            expected_plan_sha256: hex(plan.canonical_sha256(chart_limits)?),
            expected_document_flow_sha256: flow.clone(),
            target_document_flow_sha256: digest('f'),
            native_chart_id: source.next_native_chart_id(),
            z_order: source.next_z_order(),
            chart_part: source.next_chart_part().to_owned(),
            manifest_item_id: plan.data_resource_id().as_str().to_owned(),
        },
        &source,
        &plan,
        &flow,
        TableChartHwpxLimits::default(),
        chart_limits,
    )?;
    Ok(Fixture {
        package,
        binding,
        state,
        plan,
        source,
        request,
        flow,
    })
}

#[test]
fn direct_chart_lowering_is_closed_strict_and_preserves_the_source_table() -> TestResult {
    let fixture = make_fixture(TableChartLimits::default())?;
    let mut reader =
        BoundedZipReader::open(Cursor::new(&fixture.package), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    let lowered = TableChartHwpxLowerer::lower(
        &mut reader,
        &graph,
        &fixture.request,
        &fixture.binding,
        &fixture.state,
        &fixture.plan,
        &fixture.flow,
        TableChartHwpxLimits::default(),
        TableChartLimits::default(),
    )?;
    assert_eq!(lowered.patch().intent_count(), 3);
    assert_eq!(lowered.patch().changed_parts(), 2);
    assert_eq!(lowered.patch().added_parts(), 1);
    assert_eq!(lowered.patch().relationship_count(), 1);
    assert!(lowered.receipt().source_table_preserved());
    assert!(lowered.receipt().static_readback_verified());
    assert!(lowered.receipt().relationship_closure_verified());
    assert!(lowered.receipt().render_required());
    assert_eq!(lowered.receipt().output_chart_count(), 1);
    assert!(
        String::from_utf8(
            lowered
                .receipt()
                .canonical_json(TableChartHwpxLimits::default())?
        )?
        .contains("\"render_required\":true")
    );
    let artifact = PreservingWriter::build(
        lowered.patch(),
        PackageLimits::default(),
        PackageGraphLimits::default(),
        IdIndexLimits::default(),
        WriterLimits::default(),
    )?;
    artifact.verify()?;
    Ok(())
}

#[test]
fn source_inspection_requires_the_native_table_to_be_inside_a_run() -> TestResult {
    let header = header()?;
    let cells = cells();
    let section = section(&cells, false);
    let package = package(&header, &section)?;
    let binding = binding()?;
    let readback = TableRulingHwpxReader::read_existing(
        &header,
        &section,
        0,
        &binding,
        TableRulingHwpxLimits::default(),
    )?;
    let state = state(&readback, &cells, None, false, TableChartLimits::default())?;
    let mut reader = BoundedZipReader::open(Cursor::new(package), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    let error = TableChartHwpxBuilder::inspect_source(
        &mut reader,
        &graph,
        "Contents/section0.xml",
        0,
        &binding,
        &state,
        TableChartHwpxLimits::default(),
        TableChartLimits::default(),
    )
    .err()
    .ok_or("unwrapped table was accepted")?;
    assert_eq!(error.code(), TableChartHwpxError::UnsupportedSource.code());
    Ok(())
}

#[test]
fn source_inspection_rejects_cell_digest_or_formula_provenance_drift() -> TestResult {
    let header = header()?;
    let cells = cells();
    let section = section(&cells, true);
    let package = package(&header, &section)?;
    let binding = binding()?;
    let readback = TableRulingHwpxReader::read_existing(
        &header,
        &section,
        0,
        &binding,
        TableRulingHwpxLimits::default(),
    )?;
    let digest_state = state(
        &readback,
        &cells,
        Some(8),
        false,
        TableChartLimits::default(),
    )?;
    let formula_state = state(&readback, &cells, None, true, TableChartLimits::default())?;
    let mut reader = BoundedZipReader::open(Cursor::new(&package), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    let error = TableChartHwpxBuilder::inspect_source(
        &mut reader,
        &graph,
        "Contents/section0.xml",
        0,
        &binding,
        &digest_state,
        TableChartHwpxLimits::default(),
        TableChartLimits::default(),
    )
    .err()
    .ok_or("cell digest drift was accepted")?;
    assert_eq!(error.code(), TableChartHwpxError::SourceCellMismatch.code());

    let mut reader = BoundedZipReader::open(Cursor::new(package), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    let error = TableChartHwpxBuilder::inspect_source(
        &mut reader,
        &graph,
        "Contents/section0.xml",
        0,
        &binding,
        &formula_state,
        TableChartHwpxLimits::default(),
        TableChartLimits::default(),
    )
    .err()
    .ok_or("formula provenance drift was accepted")?;
    assert_eq!(error.code(), TableChartHwpxError::SourceCellMismatch.code());
    Ok(())
}

#[test]
fn request_json_rejects_duplicate_unknown_and_allocation_tampering() -> TestResult {
    let fixture = make_fixture(TableChartLimits::default())?;
    let json = String::from_utf8(
        fixture
            .request
            .canonical_json(TableChartHwpxLimits::default())?,
    )?;
    let duplicate = format!(
        "{{\"schema_version\":\"{TABLE_CHART_HWPX_SCHEMA_VERSION}\",{}",
        &json[1..]
    );
    let error = TableChartHwpxRequest::from_json(
        duplicate.as_bytes(),
        &fixture.source,
        &fixture.plan,
        &fixture.flow,
        TableChartHwpxLimits::default(),
        TableChartLimits::default(),
    )
    .err()
    .ok_or("duplicate JSON key was accepted")?;
    assert_eq!(error.code(), TableChartHwpxError::InvalidJson.code());
    let unknown = format!("{{\"unknown\":true,{}", &json[1..]);
    let error = TableChartHwpxRequest::from_json(
        unknown.as_bytes(),
        &fixture.source,
        &fixture.plan,
        &fixture.flow,
        TableChartHwpxLimits::default(),
        TableChartLimits::default(),
    )
    .err()
    .ok_or("unknown JSON field was accepted")?;
    assert_eq!(error.code(), TableChartHwpxError::InvalidJson.code());
    let tampered = json.replace("Chart/chart1.xml", "Chart/chart2.xml");
    let error = TableChartHwpxRequest::from_json(
        tampered.as_bytes(),
        &fixture.source,
        &fixture.plan,
        &fixture.flow,
        TableChartHwpxLimits::default(),
        TableChartLimits::default(),
    )
    .err()
    .ok_or("chart part allocation tamper was accepted")?;
    assert_eq!(error.code(), TableChartHwpxError::AllocationDrift.code());
    assert!(!format!("{:?}", fixture.request).contains(&fixture.flow));
    Ok(())
}

#[test]
fn lowering_rechecks_document_flow_and_emits_no_partial_result() -> TestResult {
    let fixture = make_fixture(TableChartLimits::default())?;
    let mut reader =
        BoundedZipReader::open(Cursor::new(&fixture.package), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    let error = TableChartHwpxLowerer::lower(
        &mut reader,
        &graph,
        &fixture.request,
        &fixture.binding,
        &fixture.state,
        &fixture.plan,
        &digest('0'),
        TableChartHwpxLimits::default(),
        TableChartLimits::default(),
    )
    .err()
    .ok_or("document-flow drift was accepted")?;
    assert_eq!(error.code(), TableChartHwpxError::FlowDrift.code());
    Ok(())
}

#[test]
fn custom_domain_limits_are_used_consistently_during_lowering() -> TestResult {
    let chart_limits = TableChartLimits::new(domain_ir::TableChartLimitConfig {
        cells: 9,
        ..domain_ir::TableChartLimitConfig::default()
    })?;
    let fixture = make_fixture(chart_limits)?;
    let mut reader =
        BoundedZipReader::open(Cursor::new(&fixture.package), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    let lowered = TableChartHwpxLowerer::lower(
        &mut reader,
        &graph,
        &fixture.request,
        &fixture.binding,
        &fixture.state,
        &fixture.plan,
        &fixture.flow,
        TableChartHwpxLimits::default(),
        chart_limits,
    )?;
    assert_eq!(lowered.receipt().output_chart_count(), 1);
    Ok(())
}
