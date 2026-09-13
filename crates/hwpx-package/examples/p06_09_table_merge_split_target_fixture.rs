use std::env;
use std::error::Error;
use std::fs::{self, OpenOptions};
use std::io::{Cursor, Write as _};
use std::path::{Path, PathBuf};

use domain_ir::{CellCoordinate, ContentPreservationPolicy, LogicalId, TableRulingAxis};
use hwpx_package::{
    BoundedZipReader, Compression, PackageLimits, TABLE_MERGE_SPLIT_HWPX_SCHEMA_VERSION,
    TableMergeSplitHwpxBuilder, TableMergeSplitHwpxLimits, TableMergeSplitHwpxLoweredParts,
    TableMergeSplitHwpxLowerer, TableMergeSplitHwpxOperation, TableMergeSplitHwpxPartBinding,
    TableMergeSplitHwpxPlan, TableMergeSplitHwpxReadback, TableMergeSplitHwpxReader,
    TableMergeSplitHwpxRequest, TableMergeSplitHwpxRequestDraft, TableRulingHwpxBinding,
    TableRulingHwpxCellBinding,
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use zip::write::SimpleFileOptions;
use zip::{CompressionMethod, DateTime, ZipWriter};

const MAX_FILE_BYTES: u64 = 8 * 1024 * 1024;
const EXPECTED_ANCESTOR_SHA256: &str =
    "6514a69b8c8c9d320bc19a032b16f2b71d59a38f164c690bc9e3d320a93320e5";
const SPLIT_FILE: &str = "table-016-split-cells-4x3.hwpx";
const MERGE_FILE: &str = "table-017-merge-cells-4x3.hwpx";
const SOURCE_PREVIEW: &[u8] =
    b"<R1C1><R1C2><R1C3><><><><R2C1><R2C2><R2C3><R3C1><R3C2><R3C3>\r\n\r\n";
const TABLE_WIDTH: u32 = 36_000;
const COLUMN_WIDTH: u32 = 12_000;
const ROW_HEIGHT: u32 = 4_000;

struct Arguments {
    ancestor: PathBuf,
    expected_ancestor_sha256: String,
    output_directory: PathBuf,
}

impl Arguments {
    fn parse() -> Result<Self, Box<dyn Error>> {
        let mut values = env::args_os();
        let _program = values.next();
        let result = Self {
            ancestor: values
                .next()
                .map(PathBuf::from)
                .ok_or("missing ancestor HWPX")?,
            expected_ancestor_sha256: values
                .next()
                .ok_or("missing ancestor SHA-256")?
                .into_string()
                .map_err(|_| "ancestor SHA-256 is not Unicode")?,
            output_directory: values
                .next()
                .map(PathBuf::from)
                .ok_or("missing output directory")?,
        };
        if values.next().is_some() {
            return Err("too many arguments".into());
        }
        Ok(result)
    }
}

#[derive(Serialize)]
struct Manifest {
    schema_version: &'static str,
    source_ancestor_sha256: &'static str,
    prepared_source_section_sha256: String,
    merged_seed_section_sha256: String,
    cases: Vec<ManifestCase>,
    inverse_roundtrip_exact: bool,
    actual_hangul_2020: bool,
    render: &'static str,
    automation: &'static str,
    differential: &'static str,
}

#[derive(Serialize)]
struct ManifestCase {
    case_id: &'static str,
    feature_id: &'static str,
    capability_id: &'static str,
    operation: &'static str,
    file: &'static str,
    sha256: String,
    target_header_sha256: String,
    target_section_sha256: String,
    request_sha256: String,
    plan_sha256: String,
    source_state_sha256: String,
    target_state_sha256: String,
    source_grid_sha256: String,
    target_grid_sha256: String,
    source_content_sha256: String,
    target_content_sha256: String,
    rows: u32,
    columns: u32,
    source_master_cell_count: usize,
    target_master_cell_count: usize,
    topology_delta_count: usize,
    payload_block_count: usize,
    discarded_content_block_count: usize,
    added_border_fill_count: usize,
    formula_count: usize,
    page_split: &'static str,
    binding: BindingEvidence,
}

#[derive(Serialize)]
struct BindingEvidence {
    table_id: String,
    row_boundaries_hwpunit: Vec<u32>,
    column_boundaries_hwpunit: Vec<u32>,
    cells: Vec<CellBindingEvidence>,
}

#[derive(Serialize)]
struct CellBindingEvidence {
    master_cell_id: String,
    payload_block_ids: Vec<String>,
}

struct Executed {
    source: TableMergeSplitHwpxReadback,
    request: TableMergeSplitHwpxRequest,
    plan: TableMergeSplitHwpxPlan,
    lowered: TableMergeSplitHwpxLoweredParts,
}

fn main() -> Result<(), Box<dyn Error>> {
    run(&Arguments::parse()?)
}

#[allow(clippy::too_many_lines)]
fn run(arguments: &Arguments) -> Result<(), Box<dyn Error>> {
    require_lower_sha256(&arguments.expected_ancestor_sha256)?;
    if arguments.expected_ancestor_sha256 != EXPECTED_ANCESTOR_SHA256 {
        return Err("exact table merge/split ancestor identity differs".into());
    }
    if arguments
        .ancestor
        .extension()
        .and_then(|value| value.to_str())
        != Some("hwpx")
    {
        return Err("ancestor must be an .hwpx file".into());
    }
    if arguments.output_directory.exists() {
        return Err("output directory already exists".into());
    }
    let parent = arguments
        .output_directory
        .parent()
        .ok_or("output directory has no parent")?;
    if !parent.is_dir() {
        return Err("output parent is not an existing directory".into());
    }

    let ancestor = read_bounded_file(&arguments.ancestor, MAX_FILE_BYTES)?;
    require_digest(&ancestor, EXPECTED_ANCESTOR_SHA256, "ancestor")?;
    let (header, ancestor_section) = read_parts(&ancestor)?;
    let prepared_section = prepare_source_section(&ancestor_section)?;
    let prepared_source_section_sha256 = hex(Sha256::digest(&prepared_section));
    let base_binding = source_binding()?;

    // Build the exact 2x2 merged seed through the production adapter. The seed is private to this
    // fixture; TABLE-016 then splits it and TABLE-017 consumes that exact split output.
    let seed = execute(
        &header,
        &prepared_section,
        &base_binding,
        &prepared_source_section_sha256,
        TableMergeSplitHwpxOperation::Merge {
            selected_slots: top_left_2x2(),
            content_policy: ContentPreservationPolicy::Concatenate,
        },
    )?;
    if seed.source.ruling.grid.master_cell_count() != 12
        || seed.plan.target_grid().master_cell_count() != 9
        || seed.lowered.receipt.source_payload_block_count != 9
        || seed.lowered.receipt.target_payload_block_count != 9
        || seed.lowered.receipt.discarded_content_block_count != 0
    {
        return Err("merged seed topology or receipt differs".into());
    }
    let merged_seed_section_sha256 = hex(Sha256::digest(&seed.lowered.section));
    let split_line_sha256 = seed
        .source
        .ruling
        .state
        .edge(TableRulingAxis::Horizontal, 0, 0)
        .and_then(|edge| edge.line_sha256.clone())
        .ok_or("split line identity is missing")?;

    let split = execute(
        &seed.lowered.header,
        &seed.lowered.section,
        &seed.lowered.binding,
        &merged_seed_section_sha256,
        TableMergeSplitHwpxOperation::Split {
            master_cell_id: id("merge-split-target-cell-0-0")?,
            rows: 2,
            columns: 2,
            new_master_cell_ids: vec![
                id("merge-split-target-cell-0-1")?,
                id("merge-split-target-cell-1-0")?,
                id("merge-split-target-cell-1-1")?,
            ],
            content_policy: ContentPreservationPolicy::Distribute,
            split_line_sha256,
        },
    )?;
    validate_split(&split, &seed)?;
    let split_flow_sha256 = hex(Sha256::digest(&split.lowered.section));

    let merge = execute(
        &split.lowered.header,
        &split.lowered.section,
        &split.lowered.binding,
        &split_flow_sha256,
        TableMergeSplitHwpxOperation::Merge {
            selected_slots: top_left_2x2(),
            content_policy: ContentPreservationPolicy::Concatenate,
        },
    )?;
    validate_merge(&merge, &seed)?;

    let split_package = replace_parts(
        &ancestor,
        &split.lowered.header,
        &split.lowered.section,
        SOURCE_PREVIEW,
    )?;
    let merge_package = replace_parts(
        &ancestor,
        &merge.lowered.header,
        &merge.lowered.section,
        SOURCE_PREVIEW,
    )?;
    assert_non_selected_parts_preserved(&ancestor, &split_package)?;
    assert_non_selected_parts_preserved(&ancestor, &merge_package)?;

    let manifest = Manifest {
        schema_version: "hwpx-agent.p06-09-table-merge-split-target-fixture/v1",
        source_ancestor_sha256: EXPECTED_ANCESTOR_SHA256,
        prepared_source_section_sha256,
        merged_seed_section_sha256,
        cases: vec![
            manifest_case(
                &split_package,
                &split,
                "table-016-split-cells-4x3",
                "TABLE-016",
                "table.split_cell",
                "split",
                SPLIT_FILE,
            )?,
            manifest_case(
                &merge_package,
                &merge,
                "table-017-merge-cells-4x3",
                "TABLE-017",
                "table.merge_cells",
                "merge",
                MERGE_FILE,
            )?,
        ],
        inverse_roundtrip_exact: merge.plan.target_grid() == seed.plan.target_grid()
            && merge.plan.target_state() == seed.plan.target_state(),
        actual_hangul_2020: false,
        render: "not_run",
        automation: "not_run",
        differential: "not_run",
    };
    if !manifest.inverse_roundtrip_exact {
        return Err("split/merge inverse state differs".into());
    }

    fs::create_dir(&arguments.output_directory)?;
    write_create_new(&arguments.output_directory.join(SPLIT_FILE), &split_package)?;
    write_create_new(&arguments.output_directory.join(MERGE_FILE), &merge_package)?;
    write_create_new(
        &arguments.output_directory.join("fixture-manifest.json"),
        &serde_json::to_vec_pretty(&manifest)?,
    )?;
    require_digest(
        &read_bounded_file(&arguments.ancestor, MAX_FILE_BYTES)?,
        EXPECTED_ANCESTOR_SHA256,
        "ancestor recheck",
    )?;
    println!(
        "schema={} state=pass feature_ids=TABLE-016,TABLE-017 inverse_roundtrip_exact=true actual_hangul_2020=false",
        manifest.schema_version
    );
    Ok(())
}

fn execute(
    header: &[u8],
    section: &[u8],
    binding: &TableRulingHwpxBinding,
    flow_sha256: &str,
    operation: TableMergeSplitHwpxOperation,
) -> Result<Executed, Box<dyn Error>> {
    let limits = TableMergeSplitHwpxLimits::default();
    let source = TableMergeSplitHwpxReader::read_existing(header, section, 0, binding, limits)?;
    let request = TableMergeSplitHwpxRequest::from_draft(
        TableMergeSplitHwpxRequestDraft {
            schema_version: TABLE_MERGE_SPLIT_HWPX_SCHEMA_VERSION.to_owned(),
            table_id: source.ruling.state.table_id().clone(),
            expected_state_sha256: hex(source
                .ruling
                .state
                .canonical_sha256(limits.ruling.ruling)?),
            expected_grid_sha256: hex(source.ruling.grid.canonical_sha256()?),
            expected_content_sha256: hex(source.content_state_sha256),
            expected_document_flow_sha256: flow_sha256.to_owned(),
            operation,
        },
        &source,
        flow_sha256,
        limits,
    )?;
    let plan = TableMergeSplitHwpxBuilder::build(&request, &source, flow_sha256, limits)?;
    let part_binding = TableMergeSplitHwpxPartBinding::from_readback(
        &source,
        &request,
        &plan,
        flow_sha256.to_owned(),
        limits,
    )?;
    let lowered = TableMergeSplitHwpxLowerer::lower_existing(
        header,
        section,
        0,
        binding,
        &part_binding,
        flow_sha256,
        &request,
        &plan,
        limits,
    )?;
    Ok(Executed {
        source,
        request,
        plan,
        lowered,
    })
}

fn validate_split(value: &Executed, seed: &Executed) -> Result<(), Box<dyn Error>> {
    if value.source.ruling.grid.master_cell_count() != 9
        || value.plan.target_grid().master_cell_count() != 12
        || value.lowered.binding.cells.len() != 12
        || value.lowered.receipt.source_payload_block_count != 9
        || value.lowered.receipt.target_payload_block_count != 9
        || value.lowered.receipt.discarded_content_block_count != 0
        || value.lowered.receipt.preserved_formula_count != 0
        || value.lowered.receipt.added_border_fill_count != 0
        || value.plan.target_grid() != &seed.source.ruling.grid
        || value.plan.target_state() != &seed.source.ruling.state
    {
        return Err(format!(
            "TABLE-016 split topology or receipt differs: source_masters={} target_masters={} binding_cells={} source_payloads={} target_payloads={} discarded={} formulas={} border_fills={} grid_inverse={} state_inverse={}",
            value.source.ruling.grid.master_cell_count(),
            value.plan.target_grid().master_cell_count(),
            value.lowered.binding.cells.len(),
            value.lowered.receipt.source_payload_block_count,
            value.lowered.receipt.target_payload_block_count,
            value.lowered.receipt.discarded_content_block_count,
            value.lowered.receipt.preserved_formula_count,
            value.lowered.receipt.added_border_fill_count,
            value.plan.target_grid() == &seed.source.ruling.grid,
            value.plan.target_state() == &seed.source.ruling.state,
        )
        .into());
    }
    Ok(())
}

fn validate_merge(value: &Executed, seed: &Executed) -> Result<(), Box<dyn Error>> {
    if value.source.ruling.grid.master_cell_count() != 12
        || value.plan.target_grid().master_cell_count() != 9
        || value.lowered.binding.cells.len() != 9
        || value.lowered.receipt.source_payload_block_count != 9
        || value.lowered.receipt.target_payload_block_count != 9
        || value.lowered.receipt.discarded_content_block_count != 0
        || value.lowered.receipt.preserved_formula_count != 0
        || value.lowered.receipt.added_border_fill_count != 0
        || value.lowered.binding.cells[0].payload_block_ids.len() != 2
        || value.plan.target_grid() != seed.plan.target_grid()
        || value.plan.target_state() != seed.plan.target_state()
    {
        return Err("TABLE-017 merge topology, receipt or inverse state differs".into());
    }
    Ok(())
}

#[allow(clippy::too_many_arguments)]
fn manifest_case(
    package: &[u8],
    value: &Executed,
    case_id: &'static str,
    feature_id: &'static str,
    capability_id: &'static str,
    operation: &'static str,
    file: &'static str,
) -> Result<ManifestCase, Box<dyn Error>> {
    let limits = TableMergeSplitHwpxLimits::default();
    let source_masters = value.source.ruling.grid.master_cell_count();
    let target_masters = value.plan.target_grid().master_cell_count();
    Ok(ManifestCase {
        case_id,
        feature_id,
        capability_id,
        operation,
        file,
        sha256: hex(Sha256::digest(package)),
        target_header_sha256: hex(Sha256::digest(&value.lowered.header)),
        target_section_sha256: hex(Sha256::digest(&value.lowered.section)),
        request_sha256: hex(value.request.canonical_sha256(limits)?),
        plan_sha256: hex(value.plan.canonical_sha256(limits)?),
        source_state_sha256: hex(value.lowered.receipt.source_state_sha256),
        target_state_sha256: hex(value.lowered.receipt.target_state_sha256),
        source_grid_sha256: hex(value.lowered.receipt.source_grid_sha256),
        target_grid_sha256: hex(value.lowered.receipt.target_grid_sha256),
        source_content_sha256: hex(value.lowered.receipt.source_content_sha256),
        target_content_sha256: hex(value.lowered.receipt.target_content_sha256),
        rows: value.plan.target_grid().rows(),
        columns: value.plan.target_grid().columns(),
        source_master_cell_count: source_masters,
        target_master_cell_count: target_masters,
        topology_delta_count: source_masters.abs_diff(target_masters),
        payload_block_count: value.lowered.receipt.target_payload_block_count,
        discarded_content_block_count: value.lowered.receipt.discarded_content_block_count,
        added_border_fill_count: value.lowered.receipt.added_border_fill_count,
        formula_count: value.lowered.receipt.preserved_formula_count,
        page_split: "cell",
        binding: binding_evidence(&value.lowered.binding),
    })
}

fn top_left_2x2() -> Vec<CellCoordinate> {
    vec![
        CellCoordinate { row: 0, column: 0 },
        CellCoordinate { row: 0, column: 1 },
        CellCoordinate { row: 1, column: 0 },
        CellCoordinate { row: 1, column: 1 },
    ]
}

fn id(value: &str) -> Result<LogicalId, Box<dyn Error>> {
    Ok(LogicalId::parse(value)?)
}

fn source_binding() -> Result<TableRulingHwpxBinding, Box<dyn Error>> {
    let mut cells = Vec::new();
    cells.try_reserve_exact(12)?;
    for row in 0..4 {
        for column in 0..3 {
            cells.push(TableRulingHwpxCellBinding {
                master_cell_id: id(&format!("merge-split-target-cell-{row}-{column}"))?,
                payload_block_ids: if row == 1 {
                    Vec::new()
                } else {
                    vec![id(&format!("merge-split-target-payload-{row}-{column}"))?]
                },
            });
        }
    }
    Ok(TableRulingHwpxBinding {
        table_id: id("merge-split-target-table")?,
        row_boundaries_hwpunit: vec![0, 4_000, 8_000, 12_000, 16_000],
        column_boundaries_hwpunit: vec![0, 12_000, 24_000, 36_000],
        cells,
    })
}

fn binding_evidence(value: &TableRulingHwpxBinding) -> BindingEvidence {
    BindingEvidence {
        table_id: value.table_id.as_str().to_owned(),
        row_boundaries_hwpunit: value.row_boundaries_hwpunit.clone(),
        column_boundaries_hwpunit: value.column_boundaries_hwpunit.clone(),
        cells: value
            .cells
            .iter()
            .map(|cell| CellBindingEvidence {
                master_cell_id: cell.master_cell_id.as_str().to_owned(),
                payload_block_ids: cell
                    .payload_block_ids
                    .iter()
                    .map(|identity| identity.as_str().to_owned())
                    .collect(),
            })
            .collect(),
    }
}

fn prepare_source_section(ancestor: &[u8]) -> Result<Vec<u8>, Box<dyn Error>> {
    let source = std::str::from_utf8(ancestor)?.replacen(
        r#"<hp:p id="3121190098""#,
        r#"<hp:p id="1000""#,
        1,
    );
    let table_start = source
        .find("<hp:tbl ")
        .ok_or("ancestor table start is missing")?;
    let relative_end = source[table_start..]
        .find("</hp:tbl>")
        .ok_or("ancestor table end is missing")?;
    let table_end = table_start + relative_end + "</hp:tbl>".len();
    let wrapper_end = source[table_end..]
        .find("</hp:p>")
        .map(|relative| table_end + relative + "</hp:p>".len())
        .ok_or("ancestor table wrapper end is missing")?;
    let wrapper = format!(
        r#"<hp:p id="3000" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0"><hp:run charPrIDRef="0">{}<hp:t/></hp:run></hp:p>"#,
        target_table()
    );
    let mut output = String::with_capacity(source.len() + wrapper.len());
    output.push_str(&source[..table_start]);
    output.push_str(&source[table_end..wrapper_end]);
    output.push_str(&wrapper);
    output.push_str(&source[wrapper_end..]);
    let output = output.into_bytes();
    if output
        .windows(b"<hp:fieldBegin".len())
        .any(|value| value == b"<hp:fieldBegin")
        || output
            .windows(b"repeatHeader=\"1\"".len())
            .any(|value| value == b"repeatHeader=\"1\"")
    {
        return Err("prepared source retained a formula or repeat header".into());
    }
    Ok(output)
}

fn target_table() -> String {
    let mut rows = String::new();
    for row in 0..4_u32 {
        rows.push_str("<hp:tr>");
        for column in 0..3_u32 {
            let label = match row {
                0 => format!("R1C{}", column + 1),
                1 => String::new(),
                _ => format!("R{}C{}", row, column + 1),
            };
            rows.push_str(&cell(row, column, &label));
        }
        rows.push_str("</hp:tr>");
    }
    format!(
        concat!(
            r#"<hp:tbl id="3001" zOrder="0" numberingType="TABLE" textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" pageBreak="CELL" repeatHeader="0" rowCnt="4" colCnt="3" cellSpacing="0" borderFillIDRef="3" noAdjust="0">"#,
            r#"<hp:sz width="{TABLE_WIDTH}" widthRelTo="ABSOLUTE" height="16000" heightRelTo="ABSOLUTE" protect="0"/>"#,
            r#"<hp:pos treatAsChar="0" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP" horzAlign="CENTER" vertOffset="0" horzOffset="0"/>"#,
            r#"<hp:outMargin left="283" right="283" top="283" bottom="283"/>"#,
            r#"<hp:inMargin left="510" right="510" top="141" bottom="141"/>"#,
            "{rows}</hp:tbl>"
        ),
        TABLE_WIDTH = TABLE_WIDTH,
        rows = rows,
    )
}

fn cell(row: u32, column: u32, label: &str) -> String {
    let paragraph = if label.is_empty() {
        r#"<hp:p id="0" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0"><hp:run charPrIDRef="0"/></hp:p>"#.to_owned()
    } else {
        format!(
            r#"<hp:p id="0" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0"><hp:run charPrIDRef="0"><hp:t>{label}</hp:t></hp:run></hp:p>"#
        )
    };
    format!(
        concat!(
            r#"<hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="0" borderFillIDRef="3">"#,
            r#"<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">"#,
            "{paragraph}",
            r#"</hp:subList><hp:cellAddr colAddr="{column}" rowAddr="{row}"/>"#,
            r#"<hp:cellSpan colSpan="1" rowSpan="1"/>"#,
            r#"<hp:cellSz width="{COLUMN_WIDTH}" height="{ROW_HEIGHT}"/>"#,
            r#"<hp:cellMargin left="510" right="510" top="141" bottom="141"/></hp:tc>"#
        ),
        paragraph = paragraph,
        column = column,
        row = row,
        COLUMN_WIDTH = COLUMN_WIDTH,
        ROW_HEIGHT = ROW_HEIGHT,
    )
}

fn read_parts(package: &[u8]) -> Result<(Vec<u8>, Vec<u8>), Box<dyn Error>> {
    let mut reader = BoundedZipReader::open(Cursor::new(package), PackageLimits::default())?;
    Ok((
        read_part(&mut reader, "Contents/header.xml")?,
        read_part(&mut reader, "Contents/section0.xml")?,
    ))
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

fn replace_parts(
    source: &[u8],
    header: &[u8],
    section: &[u8],
    preview: &[u8],
) -> Result<Vec<u8>, Box<dyn Error>> {
    let mut reader = BoundedZipReader::open(Cursor::new(source), PackageLimits::default())?;
    let entries = reader.entries().to_vec();
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    for entry in entries {
        let path = entry.path.as_str();
        let bytes = match path {
            "Contents/header.xml" => header.to_vec(),
            "Contents/section0.xml" => section.to_vec(),
            "Preview/PrvText.txt" => preview.to_vec(),
            _ => reader.read_entry(entry.index)?,
        };
        let method = match entry.compression {
            Compression::Stored => CompressionMethod::Stored,
            Compression::Deflated => CompressionMethod::Deflated,
        };
        let mut options = SimpleFileOptions::default()
            .compression_method(method)
            .last_modified_time(DateTime::default())
            .system(zip::System::Unix)
            .unix_permissions(0o644);
        if method == CompressionMethod::Deflated {
            options = options.compression_level(Some(6));
        }
        writer.start_file(path, options)?;
        writer.write_all(&bytes)?;
    }
    Ok(writer.finish()?.into_inner())
}

fn assert_non_selected_parts_preserved(source: &[u8], target: &[u8]) -> Result<(), Box<dyn Error>> {
    let mut source = BoundedZipReader::open(Cursor::new(source), PackageLimits::default())?;
    let mut target = BoundedZipReader::open(Cursor::new(target), PackageLimits::default())?;
    if source.entries().len() != target.entries().len() {
        return Err("target package entry count differs".into());
    }
    for entry in source.entries().to_vec() {
        let path = entry.path.as_str();
        if matches!(
            path,
            "Contents/header.xml" | "Contents/section0.xml" | "Preview/PrvText.txt"
        ) {
            continue;
        }
        let target_index = target
            .entries()
            .iter()
            .find(|candidate| candidate.path.as_str() == path)
            .map(|candidate| candidate.index)
            .ok_or("target package entry is missing")?;
        if source.read_entry(entry.index)? != target.read_entry(target_index)? {
            return Err(format!("non-selected package part differs: {path}").into());
        }
    }
    Ok(())
}

fn read_bounded_file(path: &Path, maximum: u64) -> Result<Vec<u8>, Box<dyn Error>> {
    let metadata = fs::symlink_metadata(path)?;
    if !metadata.is_file()
        || metadata.file_type().is_symlink()
        || metadata.len() == 0
        || metadata.len() > maximum
    {
        return Err("input is not a bounded regular file".into());
    }
    let bytes = fs::read(path)?;
    if u64::try_from(bytes.len())? != metadata.len() {
        return Err("input changed while being read".into());
    }
    Ok(bytes)
}

fn write_create_new(path: &Path, bytes: &[u8]) -> Result<(), Box<dyn Error>> {
    let mut output = OpenOptions::new().write(true).create_new(true).open(path)?;
    output.write_all(bytes)?;
    output.sync_all()?;
    Ok(())
}

fn require_lower_sha256(value: &str) -> Result<(), Box<dyn Error>> {
    if value.len() != 64
        || value
            .bytes()
            .any(|byte| !matches!(byte, b'0'..=b'9' | b'a'..=b'f'))
    {
        return Err("SHA-256 must be 64 lowercase hexadecimal characters".into());
    }
    Ok(())
}

fn require_digest(bytes: &[u8], expected: &str, label: &str) -> Result<(), Box<dyn Error>> {
    require_lower_sha256(expected)?;
    if hex(Sha256::digest(bytes)) != expected {
        return Err(format!("{label} SHA-256 differs").into());
    }
    Ok(())
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
