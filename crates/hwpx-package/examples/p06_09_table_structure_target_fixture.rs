use std::env;
use std::error::Error;
use std::fs::{self, OpenOptions};
use std::io::{Cursor, Write as _};
use std::path::{Path, PathBuf};

use domain_ir::{
    CellCoordinate, LogicalId, TABLE_RULING_SCHEMA_VERSION, TABLE_STRUCTURE_SCHEMA_VERSION,
    TableGrid, TableGridLimits, TableRulingAxis, TableRulingCellDraft, TableRulingEdge,
    TableRulingFrame, TableRulingLimits, TableRulingStateDraft, TableStructureOperation,
    TableStructureRequestDraft,
};
use hwpx_package::{
    BoundedZipReader, Compression, PackageLimits, TABLE_STRUCTURE_HWPX_SCHEMA_VERSION,
    TableRulingHwpxBinding, TableRulingHwpxCellBinding, TableStructureHwpxBuilder,
    TableStructureHwpxLimits, TableStructureHwpxLoweredParts, TableStructureHwpxLowerer,
    TableStructureHwpxReadback, TableStructureHwpxReader, TableStructureHwpxRequest,
    TableStructureHwpxRequestDraft,
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use zip::write::SimpleFileOptions;
use zip::{CompressionMethod, DateTime, ZipWriter};

const MAX_FILE_BYTES: u64 = 8 * 1024 * 1024;
const EXPECTED_ANCESTOR_SHA256: &str =
    "6514a69b8c8c9d320bc19a032b16f2b71d59a38f164c690bc9e3d320a93320e5";
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

#[derive(Clone, Copy)]
struct CaseSpec {
    case_id: &'static str,
    feature_id: &'static str,
    capability_id: &'static str,
    file: &'static str,
    operation: TableStructureOperation,
    index: u32,
    expected_rows: u32,
    expected_columns: u32,
    expected_inserted: usize,
    expected_deleted: usize,
}

const CASES: [CaseSpec; 4] = [
    CaseSpec {
        case_id: "table-012-insert-row-3x3",
        feature_id: "TABLE-012",
        capability_id: "table.insert_rows",
        file: "table-012-insert-row-3x3.hwpx",
        operation: TableStructureOperation::InsertRows,
        index: 1,
        expected_rows: 4,
        expected_columns: 3,
        expected_inserted: 3,
        expected_deleted: 0,
    },
    CaseSpec {
        case_id: "table-013-insert-column-3x3",
        feature_id: "TABLE-013",
        capability_id: "table.insert_columns",
        file: "table-013-insert-column-3x3.hwpx",
        operation: TableStructureOperation::InsertColumns,
        index: 1,
        expected_rows: 3,
        expected_columns: 4,
        expected_inserted: 3,
        expected_deleted: 0,
    },
    CaseSpec {
        case_id: "table-014-delete-row-3x3",
        feature_id: "TABLE-014",
        capability_id: "table.delete_rows",
        file: "table-014-delete-row-3x3.hwpx",
        operation: TableStructureOperation::DeleteRows,
        index: 1,
        expected_rows: 2,
        expected_columns: 3,
        expected_inserted: 0,
        expected_deleted: 3,
    },
    CaseSpec {
        case_id: "table-015-delete-column-3x3",
        feature_id: "TABLE-015",
        capability_id: "table.delete_columns",
        file: "table-015-delete-column-3x3.hwpx",
        operation: TableStructureOperation::DeleteColumns,
        index: 1,
        expected_rows: 3,
        expected_columns: 2,
        expected_inserted: 0,
        expected_deleted: 3,
    },
];

#[derive(Serialize)]
struct Manifest {
    schema_version: &'static str,
    source_ancestor_sha256: &'static str,
    prepared_source_section_sha256: String,
    cases: Vec<ManifestCase>,
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
    rows: u32,
    columns: u32,
    master_cell_count: usize,
    payload_block_count: usize,
    inserted_master_cell_count: usize,
    deleted_master_cell_count: usize,
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

struct BuiltCase {
    package: Vec<u8>,
    manifest: ManifestCase,
}

fn main() -> Result<(), Box<dyn Error>> {
    run(&Arguments::parse()?)
}

fn run(arguments: &Arguments) -> Result<(), Box<dyn Error>> {
    require_lower_sha256(&arguments.expected_ancestor_sha256)?;
    if arguments.expected_ancestor_sha256 != EXPECTED_ANCESTOR_SHA256 {
        return Err("exact table-structure ancestor identity differs".into());
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
    let source_section = prepare_source_section(&ancestor_section)?;
    let prepared_source_section_sha256 = hex(Sha256::digest(&source_section));
    let source_binding = source_binding()?;
    let source = TableStructureHwpxReader::read_existing(
        &header,
        &source_section,
        0,
        &source_binding,
        TableStructureHwpxLimits::default(),
    )?;
    if source.ruling.grid.rows() != 3
        || source.ruling.grid.columns() != 3
        || source.ruling.grid.master_cell_count() != 9
        || source.ruling.payload_block_count != 9
        || source.ruling.formula_count != 0
        || source.pagination.repeat_header_rows != 0
        || source.pagination.caption.is_some()
    {
        return Err("prepared source profile differs".into());
    }
    let source_flow_sha256 = prepared_source_section_sha256.clone();
    let mut built = Vec::new();
    built.try_reserve_exact(CASES.len())?;
    for spec in CASES {
        built.push(build_case(
            spec,
            &ancestor,
            &header,
            &source_section,
            &source_binding,
            &source,
            &source_flow_sha256,
        )?);
    }

    fs::create_dir(&arguments.output_directory)?;
    for (spec, case) in CASES.iter().zip(&built) {
        write_create_new(&arguments.output_directory.join(spec.file), &case.package)?;
    }
    let manifest = Manifest {
        schema_version: "hwpx-agent.p06-09-table-structure-target-fixture/v1",
        source_ancestor_sha256: EXPECTED_ANCESTOR_SHA256,
        prepared_source_section_sha256,
        cases: built.into_iter().map(|case| case.manifest).collect(),
        actual_hangul_2020: false,
        render: "not_run",
        automation: "not_run",
        differential: "not_run",
    };
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
        "schema={} state=pass target_count=4 actual_hangul_2020=false",
        manifest.schema_version
    );
    Ok(())
}

#[allow(clippy::too_many_arguments)]
fn build_case(
    spec: CaseSpec,
    ancestor: &[u8],
    header: &[u8],
    source_section: &[u8],
    source_binding: &TableRulingHwpxBinding,
    source: &TableStructureHwpxReadback,
    source_flow_sha256: &str,
) -> Result<BuiltCase, Box<dyn Error>> {
    let limits = TableStructureHwpxLimits::default();
    let new_ids = inserted_ids(spec)?;
    let target_grid = target_grid(&source.ruling.grid, spec, new_ids.clone())?;
    let (row_boundaries, column_boundaries) = target_boundaries(source, spec)?;
    let target_flow_sha256 = transition_flow_sha256(source_flow_sha256, spec.feature_id);
    let target_state = TableRulingStateDraft {
        schema_version: TABLE_RULING_SCHEMA_VERSION.to_owned(),
        table_id: source.ruling.state.table_id().clone(),
        frame: TableRulingFrame {
            left_hwpunit: source.ruling.state.frame().left_hwpunit,
            top_hwpunit: source.ruling.state.frame().top_hwpunit,
            width_hwpunit: *column_boundaries.last().ok_or("missing column boundary")?,
            height_hwpunit: *row_boundaries.last().ok_or("missing row boundary")?,
        },
        grid_sha256: hex(target_grid.canonical_sha256()?),
        table_properties_sha256: source.ruling.state.table_properties_sha256().to_owned(),
        row_boundaries_hwpunit: row_boundaries,
        column_boundaries_hwpunit: column_boundaries,
        edges: uniform_edges(source, &target_grid)?,
        cells: target_cells(source, &target_grid)?,
    };
    let request = TableStructureHwpxRequest::from_draft(
        TableStructureHwpxRequestDraft {
            schema_version: TABLE_STRUCTURE_HWPX_SCHEMA_VERSION.to_owned(),
            table_ordinal: source.table_ordinal,
            expected_header_sha256: hex(source.ruling.header_sha256),
            expected_section_sha256: hex(source.ruling.section_sha256),
            expected_wrapper_sha256: hex(source.wrapper_sha256),
            structure: TableStructureRequestDraft {
                schema_version: TABLE_STRUCTURE_SCHEMA_VERSION.to_owned(),
                operation: spec.operation,
                index: spec.index,
                count: 1,
                new_master_cell_ids: new_ids,
                expected_source_state_sha256: hex(source
                    .ruling
                    .state
                    .canonical_sha256(TableRulingLimits::default())?),
                expected_source_grid_sha256: hex(source.ruling.grid.canonical_sha256()?),
                expected_document_flow_sha256: source_flow_sha256.to_owned(),
                target_document_flow_sha256: target_flow_sha256,
                target_state,
            },
        },
        source,
        source_flow_sha256,
        limits,
    )?;
    let plan = TableStructureHwpxBuilder::build(&request, source, source_flow_sha256, limits)?;
    let lowered = TableStructureHwpxLowerer::lower_existing(
        header,
        source_section,
        source_binding,
        source_flow_sha256,
        &request,
        &plan,
        limits,
    )?;
    validate_lowered(spec, &lowered)?;
    let package = replace_parts(
        ancestor,
        &lowered.header,
        &lowered.section,
        preview_for(spec).as_bytes(),
    )?;
    assert_non_selected_parts_preserved(ancestor, &package)?;
    let manifest = ManifestCase {
        case_id: spec.case_id,
        feature_id: spec.feature_id,
        capability_id: spec.capability_id,
        file: spec.file,
        sha256: hex(Sha256::digest(&package)),
        target_header_sha256: hex(Sha256::digest(&lowered.header)),
        target_section_sha256: hex(Sha256::digest(&lowered.section)),
        request_sha256: hex(request.canonical_sha256(limits)?),
        plan_sha256: hex(plan.canonical_sha256(limits)?),
        source_state_sha256: hex(lowered.receipt.source_state_sha256),
        target_state_sha256: hex(lowered.receipt.target_state_sha256),
        source_grid_sha256: hex(lowered.receipt.source_grid_sha256),
        target_grid_sha256: hex(lowered.receipt.target_grid_sha256),
        rows: spec.expected_rows,
        columns: spec.expected_columns,
        master_cell_count: plan.domain().after_grid().master_cell_count(),
        payload_block_count: lowered.receipt.preserved_payload_block_count,
        inserted_master_cell_count: lowered.receipt.inserted_master_cell_count,
        deleted_master_cell_count: lowered.receipt.deleted_master_cell_count,
        formula_count: 0,
        page_split: "cell",
        binding: binding_evidence(&lowered.binding),
    };
    Ok(BuiltCase { package, manifest })
}

fn validate_lowered(
    spec: CaseSpec,
    lowered: &TableStructureHwpxLoweredParts,
) -> Result<(), Box<dyn Error>> {
    if lowered.receipt.source_table_count != 1
        || lowered.receipt.target_table_count != 1
        || lowered.receipt.inserted_master_cell_count != spec.expected_inserted
        || lowered.receipt.deleted_master_cell_count != spec.expected_deleted
        || lowered.receipt.formula_rebased_count != 0
        || lowered.receipt.formula_deleted_count != 0
        || lowered.receipt.formula_modified_text_count != 0
        || lowered.receipt.pagination_modified_attribute_count != 0
        || lowered.receipt.added_border_fill_count != 0
        || lowered.binding.row_boundaries_hwpunit.len()
            != usize::try_from(spec.expected_rows)?
                .checked_add(1)
                .ok_or("row overflow")?
        || lowered.binding.column_boundaries_hwpunit.len()
            != usize::try_from(spec.expected_columns)?
                .checked_add(1)
                .ok_or("column overflow")?
    {
        return Err(format!("{} lowering receipt differs", spec.feature_id).into());
    }
    Ok(())
}

fn inserted_ids(spec: CaseSpec) -> Result<Vec<LogicalId>, Box<dyn Error>> {
    let count = match spec.operation {
        TableStructureOperation::InsertRows | TableStructureOperation::InsertColumns => 3,
        TableStructureOperation::DeleteRows | TableStructureOperation::DeleteColumns => 0,
    };
    (0..count)
        .map(|index| id(&format!("structure-target-{}-new-{index}", spec.feature_id)))
        .collect()
}

fn target_grid(
    source: &TableGrid,
    spec: CaseSpec,
    new_ids: Vec<LogicalId>,
) -> Result<TableGrid, Box<dyn Error>> {
    let result = match spec.operation {
        TableStructureOperation::InsertRows => {
            source.insert_rows(spec.index, 1, new_ids, TableGridLimits::default())?
        }
        TableStructureOperation::InsertColumns => {
            source.insert_columns(spec.index, 1, new_ids, TableGridLimits::default())?
        }
        TableStructureOperation::DeleteRows => {
            source.delete_rows(spec.index, 1, TableGridLimits::default())?
        }
        TableStructureOperation::DeleteColumns => {
            source.delete_columns(spec.index, 1, TableGridLimits::default())?
        }
    };
    Ok(result.into_parts().0)
}

fn target_boundaries(
    source: &TableStructureHwpxReadback,
    spec: CaseSpec,
) -> Result<(Vec<u32>, Vec<u32>), Box<dyn Error>> {
    let row_edit = matches!(
        spec.operation,
        TableStructureOperation::InsertRows | TableStructureOperation::DeleteRows
    );
    let insert = matches!(
        spec.operation,
        TableStructureOperation::InsertRows | TableStructureOperation::InsertColumns
    );
    let rows = if row_edit {
        boundaries(
            source.ruling.state.row_boundaries_hwpunit(),
            insert,
            spec.index,
            ROW_HEIGHT,
        )?
    } else {
        source.ruling.state.row_boundaries_hwpunit().to_vec()
    };
    let columns = if row_edit {
        source.ruling.state.column_boundaries_hwpunit().to_vec()
    } else {
        boundaries(
            source.ruling.state.column_boundaries_hwpunit(),
            insert,
            spec.index,
            COLUMN_WIDTH,
        )?
    };
    Ok((rows, columns))
}

fn boundaries(
    source: &[u32],
    insert: bool,
    index: u32,
    inserted_size: u32,
) -> Result<Vec<u32>, Box<dyn Error>> {
    let mut sizes = source
        .windows(2)
        .map(|pair| pair[1].checked_sub(pair[0]).ok_or("invalid boundary"))
        .collect::<Result<Vec<_>, _>>()?;
    let index = usize::try_from(index)?;
    if insert {
        sizes.insert(index, inserted_size);
    } else {
        sizes.remove(index);
    }
    let mut output = vec![0_u32];
    for size in sizes {
        output.push(
            output
                .last()
                .copied()
                .ok_or("missing boundary")?
                .checked_add(size)
                .ok_or("boundary overflow")?,
        );
    }
    Ok(output)
}

fn target_cells(
    source: &TableStructureHwpxReadback,
    target_grid: &TableGrid,
) -> Result<Vec<TableRulingCellDraft>, Box<dyn Error>> {
    let inserted_properties = source
        .ruling
        .grid
        .master_cell_at(CellCoordinate { row: 0, column: 0 })
        .ok()
        .and_then(|span| source.ruling.state.cell(&span.master_cell_id))
        .ok_or("inserted property template missing")?
        .properties()
        .clone();
    let mut cells = Vec::new();
    cells.try_reserve_exact(target_grid.master_cell_count())?;
    for span in target_grid.master_cells() {
        let coordinate = CellCoordinate {
            row: span.row,
            column: span.column,
        };
        if let Some(before) = source.ruling.state.cell(&span.master_cell_id) {
            if before.formula().is_some() {
                return Err("formula-free source profile differs".into());
            }
            cells.push(TableRulingCellDraft {
                master_cell_id: span.master_cell_id.clone(),
                coordinate,
                payload: before.payload().to_vec(),
                properties: before.properties().clone(),
                formula: None,
            });
        } else {
            cells.push(TableRulingCellDraft {
                master_cell_id: span.master_cell_id.clone(),
                coordinate,
                payload: Vec::new(),
                properties: inserted_properties.clone(),
                formula: None,
            });
        }
    }
    Ok(cells)
}

fn uniform_edges(
    source: &TableStructureHwpxReadback,
    target: &TableGrid,
) -> Result<Vec<TableRulingEdge>, Box<dyn Error>> {
    let line = source
        .ruling
        .state
        .edges()
        .first()
        .ok_or("source edge missing")?
        .line_sha256
        .clone();
    if !source
        .ruling
        .state
        .edges()
        .iter()
        .all(|edge| edge.line_sha256 == line)
    {
        return Err("source edges are not uniform".into());
    }
    let mut edges = Vec::new();
    for boundary in 0..=target.rows() {
        for offset in 0..target.columns() {
            edges.push(TableRulingEdge {
                axis: TableRulingAxis::Horizontal,
                boundary,
                offset,
                line_sha256: line.clone(),
            });
        }
    }
    for boundary in 0..=target.columns() {
        for offset in 0..target.rows() {
            edges.push(TableRulingEdge {
                axis: TableRulingAxis::Vertical,
                boundary,
                offset,
                line_sha256: line.clone(),
            });
        }
    }
    Ok(edges)
}

fn transition_flow_sha256(source_flow_sha256: &str, feature_id: &str) -> String {
    let mut digest = Sha256::new();
    digest.update(b"hwpx-agent.p06-09-table-structure-target-flow/v1\0");
    digest.update(source_flow_sha256.as_bytes());
    digest.update(feature_id.as_bytes());
    hex(digest.finalize())
}

fn id(value: &str) -> Result<LogicalId, Box<dyn Error>> {
    Ok(LogicalId::parse(value)?)
}

fn source_binding() -> Result<TableRulingHwpxBinding, Box<dyn Error>> {
    let mut cells = Vec::new();
    cells.try_reserve_exact(9)?;
    for row in 0..3 {
        for column in 0..3 {
            cells.push(TableRulingHwpxCellBinding {
                master_cell_id: id(&format!("structure-target-cell-{row}-{column}"))?,
                payload_block_ids: vec![id(&format!("structure-target-payload-{row}-{column}"))?],
            });
        }
    }
    Ok(TableRulingHwpxBinding {
        table_id: id("structure-target-table")?,
        row_boundaries_hwpunit: vec![0, 4_000, 8_000, 12_000],
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
    let outer_paragraph_end = source[table_end..]
        .find("</hp:p>")
        .map(|relative| table_end + relative + "</hp:p>".len())
        .ok_or("ancestor table wrapper end is missing")?;
    let wrapper = format!(
        r#"<hp:p id="3000" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0"><hp:run charPrIDRef="0">{}<hp:t/></hp:run></hp:p>"#,
        target_table()
    );
    let mut output = String::with_capacity(source.len() + wrapper.len());
    output.push_str(&source[..table_start]);
    output.push_str(&source[table_end..outer_paragraph_end]);
    output.push_str(&wrapper);
    output.push_str(&source[outer_paragraph_end..]);
    let output = output.into_bytes();
    if output
        .windows(b"<hp:fieldBegin".len())
        .any(|value| value == b"<hp:fieldBegin")
        || output
            .windows(b"repeatHeader=\"1\"".len())
            .any(|value| value == b"repeatHeader=\"1\"")
    {
        return Err("prepared source retained an unsupported formula or repeat header".into());
    }
    Ok(output)
}

fn target_table() -> String {
    let mut rows = String::new();
    for row in 0..3_u32 {
        rows.push_str("<hp:tr>");
        for column in 0..3_u32 {
            rows.push_str(&cell(row, column, &format!("R{}C{}", row + 1, column + 1)));
        }
        rows.push_str("</hp:tr>");
    }
    format!(
        concat!(
            r#"<hp:tbl id="3001" zOrder="0" numberingType="TABLE" textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" pageBreak="CELL" repeatHeader="0" rowCnt="3" colCnt="3" cellSpacing="0" borderFillIDRef="3" noAdjust="0">"#,
            r#"<hp:sz width="{TABLE_WIDTH}" widthRelTo="ABSOLUTE" height="12000" heightRelTo="ABSOLUTE" protect="0"/>"#,
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
    format!(
        concat!(
            r#"<hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="0" borderFillIDRef="3">"#,
            r#"<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">"#,
            r#"<hp:p id="0" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0"><hp:run charPrIDRef="0"><hp:t>{label}</hp:t></hp:run></hp:p>"#,
            r#"</hp:subList><hp:cellAddr colAddr="{column}" rowAddr="{row}"/>"#,
            r#"<hp:cellSpan colSpan="1" rowSpan="1"/>"#,
            r#"<hp:cellSz width="{COLUMN_WIDTH}" height="{ROW_HEIGHT}"/>"#,
            r#"<hp:cellMargin left="510" right="510" top="141" bottom="141"/></hp:tc>"#
        ),
        label = label,
        column = column,
        row = row,
        COLUMN_WIDTH = COLUMN_WIDTH,
        ROW_HEIGHT = ROW_HEIGHT,
    )
}

fn preview_for(spec: CaseSpec) -> String {
    let labels = match spec.feature_id {
        "TABLE-012" => "<R1C1><R1C2><R1C3><><><><R2C1><R2C2><R2C3><R3C1><R3C2><R3C3>",
        "TABLE-013" => "<R1C1><><R1C2><R1C3><R2C1><><R2C2><R2C3><R3C1><><R3C2><R3C3>",
        "TABLE-014" => "<R1C1><R1C2><R1C3><R3C1><R3C2><R3C3>",
        "TABLE-015" => "<R1C1><R1C3><R2C1><R2C3><R3C1><R3C3>",
        _ => "",
    };
    format!("{labels}\r\n\r\n")
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
