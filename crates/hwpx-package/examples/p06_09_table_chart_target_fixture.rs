use std::env;
use std::error::Error;
use std::fs::{self, OpenOptions};
use std::io::{Cursor, Write as _};
use std::path::{Path, PathBuf};

use domain_ir::{
    CellCoordinate, FormulaDecimal, LogicalId, TABLE_CHART_SCHEMA_VERSION, TableChartBuilder,
    TableChartCellDraft, TableChartLimits, TableChartPlan, TableChartRegion, TableChartRequest,
    TableChartRequestDraft, TableChartSourceState, TableChartSourceStateDraft, TableChartValue,
    TableChartValueOrigin, TableRulingLimits,
};
use hwpx_agent_foundation::workdir::SecureWorkspace;
use hwpx_package::{
    AtomicPackagePublisher, BoundedZipReader, Compression, IdIndexLimits, PackageGraph,
    PackageGraphLimits, PackageLimits, PreservingWriter, PreservingXmlDocument,
    TABLE_CHART_HWPX_PROFILE_ID, TABLE_CHART_HWPX_SCHEMA_VERSION, TableChartHwpxBuilder,
    TableChartHwpxLimits, TableChartHwpxLowered, TableChartHwpxLowerer, TableChartHwpxRequest,
    TableChartHwpxRequestDraft, TableChartHwpxSource, TableRulingHwpxBinding,
    TableRulingHwpxCellBinding, TableRulingHwpxLimits, TableRulingHwpxReader, WriterLimits,
};
use serde_json::json;
use sha2::{Digest as _, Sha256};
use zip::write::SimpleFileOptions;
use zip::{CompressionMethod, DateTime, ZipWriter};

const SECTION_PART: &str = "Contents/section0.xml";
const HEADER_PART: &str = "Contents/header.xml";
const OUTPUT_RELATIVE: &str = "p06-09-table-chart-product.hwpx";
const SOURCE_RELATIVE: &str = "p06-09-table-chart-source-normalized.hwpx";
const EXPECTED_INPUT_SHA256: &str =
    "7ed2006c862be671eba82c1a3648c2a30ce7176fef8a6ceb58469b167a5e4929";
const MAX_INPUT_BYTES: u64 = 8 * 1024 * 1024;

struct Arguments {
    input: PathBuf,
    expected_input_sha256: String,
    workspace_root: PathBuf,
}

impl Arguments {
    fn parse() -> Result<Self, Box<dyn Error>> {
        let mut values = env::args_os();
        let _program = values.next();
        let input = values
            .next()
            .map(PathBuf::from)
            .ok_or("input HWPX is required")?;
        let expected_input_sha256 = values
            .next()
            .ok_or("expected input SHA-256 is required")?
            .into_string()
            .map_err(|_| "expected input SHA-256 is not Unicode")?;
        let workspace_root = values
            .next()
            .map(PathBuf::from)
            .ok_or("workspace root is required")?;
        if values.next().is_some() {
            return Err("too many arguments".into());
        }
        Ok(Self {
            input,
            expected_input_sha256,
            workspace_root,
        })
    }
}

fn main() -> Result<(), Box<dyn Error>> {
    run(&Arguments::parse()?)
}

fn run(arguments: &Arguments) -> Result<(), Box<dyn Error>> {
    let source_package = prepare_source(arguments)?;
    let limits = TableChartHwpxLimits::default();
    let chart_limits = TableChartLimits::default();
    let mut reader = BoundedZipReader::open(
        Cursor::new(source_package.as_slice()),
        PackageLimits::default(),
    )?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    let header = read_part(&mut reader, HEADER_PART)?;
    let section = read_part(&mut reader, SECTION_PART)?;
    let binding = exact_binding()?;
    let ruling = TableRulingHwpxReader::read_existing(
        &header,
        &section,
        0,
        &binding,
        TableRulingHwpxLimits::default(),
    )?;
    if ruling.grid.rows() != 3
        || ruling.grid.columns() != 3
        || ruling.grid.master_cell_count() != 9
        || ruling.payload_block_count != 8
        || ruling.formula_count != 0
    {
        return Err("exact table-chart source grid or payload differs".into());
    }
    let state = exact_state(&section, &ruling, chart_limits)?;
    let before_flow = tagged_digest(b"p06-09-table-chart-flow-before", &source_package);
    let after_flow = tagged_digest(b"p06-09-table-chart-flow-after", &source_package);
    let domain_request = TableChartRequest::from_draft(
        TableChartRequestDraft {
            schema_version: TABLE_CHART_SCHEMA_VERSION.to_owned(),
            table_id: state.table_id().clone(),
            chart_id: id("p06-09-table-chart")?,
            data_resource_id: id("p06-09-table-chart-data")?,
            source_region: TableChartRegion {
                start: CellCoordinate { row: 0, column: 0 },
                end: CellCoordinate { row: 2, column: 2 },
            },
            expected_source_state_sha256: hex(state.canonical_sha256(chart_limits)?),
            expected_document_flow_sha256: before_flow.clone(),
        },
        &state,
        &ruling.grid,
        &before_flow,
        chart_limits,
    )?;
    let plan = TableChartBuilder::build(
        &domain_request,
        &state,
        &ruling.grid,
        &before_flow,
        chart_limits,
    )?;
    let source = TableChartHwpxBuilder::inspect_source(
        &mut reader,
        &graph,
        SECTION_PART,
        0,
        &binding,
        &state,
        limits,
        chart_limits,
    )?;
    let request = build_hwpx_request(
        &source,
        &plan,
        &before_flow,
        after_flow,
        &limits,
        chart_limits,
    )?;
    let lowered = TableChartHwpxLowerer::lower(
        &mut reader,
        &graph,
        &request,
        &binding,
        &state,
        &plan,
        &before_flow,
        limits,
        chart_limits,
    )?;
    println!(
        "{}",
        serde_json::to_string(&publish_result(
            arguments,
            &source_package,
            &lowered,
            &limits,
        )?)?
    );
    Ok(())
}

fn prepare_source(arguments: &Arguments) -> Result<Vec<u8>, Box<dyn Error>> {
    require_lower_sha256(&arguments.expected_input_sha256)?;
    if arguments.expected_input_sha256 != EXPECTED_INPUT_SHA256 {
        return Err("exact table-chart source identity differs".into());
    }
    if arguments.input.extension().and_then(|value| value.to_str()) != Some("hwpx") {
        return Err("input must be an .hwpx file".into());
    }
    if arguments.workspace_root.exists() {
        return Err("workspace root already exists".into());
    }
    let input = read_bounded(&arguments.input, MAX_INPUT_BYTES)?;
    require_digest(&input, &arguments.expected_input_sha256, "input")?;
    let mut input_reader =
        BoundedZipReader::open(Cursor::new(input.as_slice()), PackageLimits::default())?;
    let input_section = read_part(&mut input_reader, SECTION_PART)?;
    let source_section = normalize_small_native_table(&input_section)?;
    replace_section(&input, &source_section)
}

fn build_hwpx_request(
    source: &TableChartHwpxSource,
    plan: &TableChartPlan,
    before_flow: &str,
    after_flow: String,
    limits: &TableChartHwpxLimits,
    chart_limits: TableChartLimits,
) -> Result<TableChartHwpxRequest, Box<dyn Error>> {
    Ok(TableChartHwpxRequest::from_draft(
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
            expected_document_flow_sha256: before_flow.to_owned(),
            target_document_flow_sha256: after_flow,
            native_chart_id: source.next_native_chart_id(),
            z_order: source.next_z_order(),
            chart_part: source.next_chart_part().to_owned(),
            manifest_item_id: plan.data_resource_id().as_str().to_owned(),
        },
        source,
        plan,
        before_flow,
        *limits,
        chart_limits,
    )?)
}

fn publish_result(
    arguments: &Arguments,
    source_package: &[u8],
    lowered: &TableChartHwpxLowered,
    limits: &TableChartHwpxLimits,
) -> Result<serde_json::Value, Box<dyn Error>> {
    let receipt = lowered.receipt().canonical_json(*limits)?;
    let artifact = PreservingWriter::build(
        lowered.patch(),
        PackageLimits::default(),
        PackageGraphLimits::default(),
        IdIndexLimits::default(),
        WriterLimits::default(),
    )?;
    artifact.verify()?;
    let workspace = SecureWorkspace::create(&arguments.workspace_root)?;
    write_create_new(
        &arguments
            .workspace_root
            .join("output")
            .join(SOURCE_RELATIVE),
        source_package,
    )?;
    let publication = AtomicPackagePublisher::publish(
        &artifact,
        &workspace,
        Path::new("staged/table-chart-product.hwpx"),
        Path::new(OUTPUT_RELATIVE),
    )?;
    require_digest(
        &read_bounded(&arguments.input, MAX_INPUT_BYTES)?,
        &arguments.expected_input_sha256,
        "input recheck",
    )?;

    Ok(json!({
        "schema_version": "hwpx-agent.p06-09-table-chart-target-fixture/v1",
        "state": "pass",
        "input_sha256": arguments.expected_input_sha256,
        "source_relative": SOURCE_RELATIVE,
        "source_sha256": hex(Sha256::digest(source_package)),
        "output_relative": publication.output_relative().to_string_lossy(),
        "output_sha256": hex(publication.sha256()),
        "output_bytes": publication.size_bytes(),
        "staged_reopen_verified": publication.staged_reopen_verified(),
        "published_reopen_verified": publication.published_reopen_verified(),
        "lowering_receipt": serde_json::from_slice::<serde_json::Value>(&receipt)?,
        "actual_hangul_2020": false,
        "save_reopen": "not_run",
        "render": "not_run",
        "automation": "not_run",
        "differential": "not_run"
    }))
}

fn exact_binding() -> Result<TableRulingHwpxBinding, Box<dyn Error>> {
    let cells = (0..9)
        .map(|index| {
            Ok(TableRulingHwpxCellBinding {
                master_cell_id: id(&format!("p06-09-chart-cell-{index}"))?,
                payload_block_ids: if index == 0 {
                    Vec::new()
                } else {
                    vec![id(&format!("p06-09-chart-payload-{index}"))?]
                },
            })
        })
        .collect::<Result<Vec<_>, Box<dyn Error>>>()?;
    Ok(TableRulingHwpxBinding {
        table_id: id("p06-09-table-chart-source")?,
        row_boundaries_hwpunit: vec![0, 1_282, 2_564, 3_846],
        column_boundaries_hwpunit: vec![0, 13_984, 27_968, 41_952],
        cells,
    })
}

fn exact_state(
    section: &[u8],
    ruling: &hwpx_package::TableRulingHwpxReadback,
    limits: TableChartLimits,
) -> Result<TableChartSourceState, Box<dyn Error>> {
    let document = PreservingXmlDocument::parse(section)?;
    document.verify_untouched_round_trip()?;
    let raw_cell_sha256 = document
        .elements()
        .iter()
        .filter(|element| {
            element.name().namespace() == Some(PARAGRAPH_NS) && element.name().local_name() == "tc"
        })
        .map(|element| {
            let span = element.outer_span().ok_or("table cell span missing")?;
            Ok(hex(Sha256::digest(
                section
                    .get(span.start()..span.end())
                    .ok_or("table cell span is outside the section")?,
            )))
        })
        .collect::<Result<Vec<_>, Box<dyn Error>>>()?;
    if raw_cell_sha256.len() != 9 {
        return Err("exact table-chart source cell count differs".into());
    }
    let values = [
        TableChartValue::Blank,
        text_value("Series-A"),
        text_value("Series-B"),
        text_value("Category-A"),
        number_value(1),
        number_value(2),
        text_value("Category-B"),
        number_value(3),
        number_value(4),
    ];
    let cells = ruling
        .grid
        .master_cells()
        .iter()
        .enumerate()
        .map(|(index, span)| TableChartCellDraft {
            master_cell_id: span.master_cell_id.clone(),
            coordinate: CellCoordinate {
                row: span.row,
                column: span.column,
            },
            source_sha256: raw_cell_sha256[index].clone(),
            value: values[index].clone(),
            value_origin: TableChartValueOrigin::Literal,
        })
        .collect();
    Ok(TableChartSourceState::from_draft(
        TableChartSourceStateDraft {
            schema_version: TABLE_CHART_SCHEMA_VERSION.to_owned(),
            table_id: ruling.state.table_id().clone(),
            grid_sha256: hex(ruling.grid.canonical_sha256()?),
            table_state_sha256: hex(ruling
                .state
                .canonical_sha256(TableRulingLimits::default())?),
            cells,
        },
        &ruling.grid,
        limits,
    )?)
}

const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";

fn text_value(value: &str) -> TableChartValue {
    TableChartValue::Text {
        value: value.to_owned(),
    }
}

fn number_value(value: i64) -> TableChartValue {
    TableChartValue::Number {
        value: FormulaDecimal::new(value, 0),
    }
}

fn id(value: &str) -> Result<LogicalId, Box<dyn Error>> {
    Ok(LogicalId::parse(value)?)
}

fn read_part(
    reader: &mut BoundedZipReader<Cursor<&[u8]>>,
    path: &str,
) -> Result<Vec<u8>, Box<dyn Error>> {
    let index = reader
        .entries()
        .iter()
        .find(|entry| entry.path.as_str() == path)
        .map(|entry| entry.index)
        .ok_or("required package part is missing")?;
    Ok(reader.read_entry(index)?)
}

fn normalize_small_native_table(section: &[u8]) -> Result<Vec<u8>, Box<dyn Error>> {
    let mut source = String::from_utf8(section.to_vec())?;
    let old_size = r#"<hp:cellSz width="13984" height="282"/>"#;
    let new_size = r#"<hp:cellSz width="13984" height="1282"/>"#;
    if source.matches(old_size).count() != 9
        || source.matches("<hp:tbl ").count() != 1
        || !source.contains(
            r#"<hp:sz width="41952" widthRelTo="ABSOLUTE" height="3846" heightRelTo="ABSOLUTE""#,
        )
    {
        return Err("exact small native table geometry differs".into());
    }
    source = source.replace(old_size, new_size);
    let (source, removed) = strip_elements(source, "<hp:linesegarray>", "</hp:linesegarray>")?;
    if removed != 11 || source.contains("<hp:linesegarray>") {
        return Err("native table line-cache cardinality differs".into());
    }
    Ok(source.into_bytes())
}

fn strip_elements(
    mut source: String,
    start_marker: &str,
    end_marker: &str,
) -> Result<(String, usize), Box<dyn Error>> {
    let mut count = 0;
    while let Some(start) = source.find(start_marker) {
        let end = source[start..]
            .find(end_marker)
            .and_then(|offset| start.checked_add(offset + end_marker.len()))
            .ok_or("native table line-cache end is missing")?;
        source.replace_range(start..end, "");
        count += 1;
    }
    Ok((source, count))
}

fn replace_section(source: &[u8], section: &[u8]) -> Result<Vec<u8>, Box<dyn Error>> {
    let mut reader = BoundedZipReader::open(Cursor::new(source), PackageLimits::default())?;
    let entries = reader.entries().to_vec();
    let mut output = ZipWriter::new(Cursor::new(Vec::new()));
    let mut replacements = 0_u8;
    for entry in entries {
        let path = entry.path.as_str().to_owned();
        let bytes = if path == SECTION_PART {
            replacements += 1;
            section.to_vec()
        } else {
            reader.read_entry(entry.index)?
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
        output.start_file(path, options)?;
        output.write_all(&bytes)?;
    }
    if replacements != 1 {
        return Err("section replacement cardinality differs".into());
    }
    Ok(output.finish()?.into_inner())
}

fn read_bounded(path: &Path, maximum: u64) -> Result<Vec<u8>, Box<dyn Error>> {
    let metadata = fs::symlink_metadata(path)?;
    if !metadata.is_file()
        || metadata.file_type().is_symlink()
        || metadata.len() == 0
        || metadata.len() > maximum
    {
        return Err("input file is empty or exceeds its bound".into());
    }
    let bytes = fs::read(path)?;
    if bytes.len() as u64 != metadata.len() {
        return Err("input changed while being read".into());
    }
    Ok(bytes)
}

fn write_create_new(path: &Path, bytes: &[u8]) -> Result<(), Box<dyn Error>> {
    let mut file = OpenOptions::new().write(true).create_new(true).open(path)?;
    file.write_all(bytes)?;
    file.sync_all()?;
    Ok(())
}

fn require_digest(bytes: &[u8], expected: &str, label: &str) -> Result<(), Box<dyn Error>> {
    if hex(Sha256::digest(bytes)) != expected {
        return Err(format!("{label} SHA-256 differs").into());
    }
    Ok(())
}

fn require_lower_sha256(value: &str) -> Result<(), Box<dyn Error>> {
    if value.len() != 64
        || value
            .bytes()
            .any(|byte| !(byte.is_ascii_digit() || matches!(byte, b'a'..=b'f')))
    {
        return Err("expected SHA-256 is not lowercase hexadecimal".into());
    }
    Ok(())
}

fn tagged_digest(tag: &[u8], source: &[u8]) -> String {
    let mut digest = Sha256::new();
    digest.update(tag);
    digest.update(b"\0");
    digest.update(source);
    hex(digest.finalize())
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
