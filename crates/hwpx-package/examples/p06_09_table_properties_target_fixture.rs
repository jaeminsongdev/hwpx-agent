use std::env;
use std::error::Error;
use std::fs::{self, OpenOptions};
use std::io::{Cursor, Write as _};
use std::path::{Path, PathBuf};

use domain_ir::{
    CellCoordinate, LogicalId, TABLE_PROPERTIES_SCHEMA_VERSION, TableCellBorderPatch,
    TableDiagonalApplyMode, TableDiagonalCenterLine, TableDiagonalPatch, TableDiagonalSlash,
    TableDiagonalSlashType, TableDiagonalValue, TablePropertiesBuilder, TablePropertiesLimits,
    TablePropertiesOperation, TablePropertiesRequest, TablePropertiesRequestDraft,
    TablePropertyDigestPatch, TableUnifiedBorderPatch,
};
use hwpx_package::{
    BorderLine, BorderWidth, BoundedZipReader, CellMargins, CellProtection, CellTextDirection,
    CellVerticalAlignment, Color, Compression, FillBrush, HorizontalAlignment, LineType2,
    PackageLimits, TableFormulaHwpxLimits, TableFormulaHwpxReader, TablePropertiesHwpxBinding,
    TablePropertiesHwpxCellValue, TablePropertiesHwpxLimits, TablePropertiesHwpxLowerer,
    TablePropertiesHwpxPartBinding, TablePropertiesHwpxReader, TablePropertiesHwpxValueCatalog,
    TableRulingHwpxBinding, TableRulingHwpxCellBinding, WindowBrush,
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use zip::write::SimpleFileOptions;
use zip::{CompressionMethod, DateTime, ZipWriter};

const MAX_FIXTURE_BYTES: u64 = 8 * 1024 * 1024;
const NORMALIZED_DEFLATE_LEVEL: i64 = 6;
const EXPECTED_ANCESTOR_SHA256: &str =
    "6514a69b8c8c9d320bc19a032b16f2b71d59a38f164c690bc9e3d320a93320e5";
const OUTPUT_FILE: &str = "table-007-properties-formula-2x4.hwpx";
const TABLE_008_OUTPUT_FILE: &str = "table-008-cell-border-each-formula-2x4.hwpx";
const TABLE_009_OUTPUT_FILE: &str = "table-009-cell-border-unified-formula-2x4.hwpx";
const TABLE_047_OUTPUT_FILE: &str = "table-047-cell-diagonal-formula-2x4.hwpx";
const SOURCE_PREVIEW: &[u8] = b"<2><3><4><5><17><10><25><52>\r\n\r\n";
const TABLE_WIDTH: u32 = 41_952;
const TABLE_HEIGHT: u32 = 8_000;
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
    case: ManifestCase,
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
    selected_table_ordinal: usize,
    selected_cell: CellCoordinate,
    target_header_sha256: String,
    target_section_sha256: String,
    target_state_sha256: String,
    target_grid_sha256: String,
    target_table_value_sha256: String,
    target_cell_value_sha256: String,
    operations: Vec<OperationEvidence>,
    rows: u32,
    columns: u32,
    master_cells: usize,
    payload_blocks: usize,
    formula_count: usize,
    page_split: &'static str,
    table_lock: bool,
    table_no_adjust: bool,
    changed_master_cells: usize,
    preserved_formula_count: usize,
    binding: BindingEvidence,
}

#[derive(Serialize)]
struct OperationEvidence {
    name: &'static str,
    request_sha256: String,
    plan_sha256: String,
    source_state_sha256: String,
    target_state_sha256: String,
    table_properties_changed: bool,
    changed_master_cells: usize,
    preserved_formula_count: usize,
}

#[derive(Serialize)]
struct BindingEvidence {
    table_id: String,
    row_boundaries_hwpunit: Vec<u32>,
    column_boundaries_hwpunit: Vec<u32>,
    cells: Vec<BindingCellEvidence>,
}

#[derive(Serialize)]
struct BindingCellEvidence {
    master_cell_id: String,
    payload_block_ids: Vec<String>,
}

#[derive(Serialize)]
struct PropertyBatchManifest {
    schema_version: &'static str,
    source_ancestor_sha256: &'static str,
    prepared_source_section_sha256: String,
    cases: Vec<PropertyBatchManifestCase>,
    actual_hangul_2020: bool,
    render: &'static str,
    automation: &'static str,
    differential: &'static str,
}

#[derive(Serialize)]
struct PropertyBatchManifestCase {
    case_id: &'static str,
    feature_id: &'static str,
    capability_id: &'static str,
    file: &'static str,
    sha256: String,
    selected_table_ordinal: usize,
    selected_slots: Vec<CellCoordinate>,
    operation_kind: &'static str,
    line_sha256: Vec<String>,
    background_sha256: Option<String>,
    diagonal: Option<TableDiagonalValue>,
    diagonal_apply_mode: Option<TableDiagonalApplyMode>,
    target_header_sha256: String,
    target_section_sha256: String,
    source_state_sha256: String,
    target_state_sha256: String,
    target_grid_sha256: String,
    request_sha256: String,
    plan_sha256: String,
    rows: u32,
    columns: u32,
    master_cells: usize,
    payload_blocks: usize,
    formula_count: usize,
    page_split: &'static str,
    changed_master_cells: usize,
    border_side_change_count: usize,
    background_change_count: usize,
    per_cell_edge_assignment_count: usize,
    outer_edge_assignment_count: usize,
    inner_edge_assignment_count: usize,
    diagonal_change_count: usize,
    diagonal_assignment_count: usize,
    unselected_master_cell_preserved_count: usize,
    preserved_formula_count: usize,
    added_border_fill_count: usize,
    binding: PropertyBatchBindingEvidence,
}

#[derive(Serialize)]
struct PropertyBatchBindingEvidence {
    table: BindingEvidence,
    diagonals: Vec<DiagonalBindingEvidence>,
}

#[derive(Serialize)]
struct DiagonalBindingEvidence {
    master_cell_id: String,
    apply_mode: TableDiagonalApplyMode,
    region: Option<domain_ir::TablePropertyRegion>,
    value: TableDiagonalValue,
}

struct BuiltPropertyTarget {
    capability_id: &'static str,
    package: Vec<u8>,
    output_binding: TablePropertiesHwpxBinding,
    target_header_sha256: String,
    target_section_sha256: String,
    source_state_sha256: String,
    target_state_sha256: String,
    target_grid_sha256: String,
    request_sha256: String,
    plan_sha256: String,
    rows: u32,
    columns: u32,
    master_cells: usize,
    payload_blocks: usize,
    formula_count: usize,
    changed_master_cells: usize,
    border_side_change_count: usize,
    background_change_count: usize,
    per_cell_edge_assignment_count: usize,
    outer_edge_assignment_count: usize,
    inner_edge_assignment_count: usize,
    diagonal_change_count: usize,
    diagonal_assignment_count: usize,
    unselected_master_cell_preserved_count: usize,
    preserved_formula_count: usize,
    added_border_fill_count: usize,
}

fn main() -> Result<(), Box<dyn Error>> {
    run(&Arguments::parse()?)
}

#[allow(clippy::too_many_lines)]
fn run(arguments: &Arguments) -> Result<(), Box<dyn Error>> {
    require_lower_sha256(&arguments.expected_ancestor_sha256)?;
    if arguments.expected_ancestor_sha256 != EXPECTED_ANCESTOR_SHA256 {
        return Err("exact properties fixture ancestor identity differs".into());
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

    let ancestor = read_bounded_file(&arguments.ancestor, MAX_FIXTURE_BYTES)?;
    require_digest(&ancestor, EXPECTED_ANCESTOR_SHA256, "ancestor")?;
    let (header, ancestor_section) = read_parts(&ancestor)?;
    let source_section = prepare_source_section(&ancestor_section)?;
    let prepared_source_section_sha256 = hex(Sha256::digest(&source_section));
    let binding = properties_binding()?;
    let limits = TablePropertiesHwpxLimits::default();
    let source =
        TablePropertiesHwpxReader::read_existing(&header, &source_section, 0, &binding, limits)?;
    require_source(&source)?;

    let mut table_value = source.table_value.clone();
    table_value.lock = true;
    table_value.no_adjust = true;
    let cell_value = TablePropertiesHwpxCellValue {
        margins: Some(CellMargins {
            left: 1_200,
            right: 200,
            top: 900,
            bottom: 100,
        }),
        paragraph_property_id_ref: 0,
        horizontal_alignment: HorizontalAlignment::Justify,
        vertical_alignment: CellVerticalAlignment::Bottom,
        text_direction: CellTextDirection::VerticalAll,
        protection: CellProtection::ProtectedEditable,
    };
    let properties_limits = TablePropertiesLimits::default();
    let table_digest = table_value.canonical_sha256()?;
    let cell_digest = cell_value.canonical_sha256();
    let table_request = TablePropertiesRequest::from_draft(
        TablePropertiesRequestDraft {
            schema_version: TABLE_PROPERTIES_SCHEMA_VERSION.to_owned(),
            table_id: source.state.table_id().clone(),
            expected_state_sha256: hex(source.state.canonical_sha256(properties_limits)?),
            selected_slots: Vec::new(),
            operation: TablePropertiesOperation::SetProperties {
                table_properties_sha256: Some(table_digest.clone()),
                cell_properties_sha256: None,
            },
        },
        &source.state,
        &source.grid,
        properties_limits,
    )?;
    let table_plan = TablePropertiesBuilder::build(
        &table_request,
        &source.state,
        &source.grid,
        properties_limits,
    )?;
    let flow = document_flow_sha256(&source_section);
    let part_binding = TablePropertiesHwpxPartBinding::from_readback(&source, flow.clone())?;
    let first = TablePropertiesHwpxLowerer::lower_existing(
        &header,
        &source_section,
        0,
        &binding,
        &part_binding,
        &flow,
        &source.state,
        &source.grid,
        &table_plan,
        &TablePropertiesHwpxValueCatalog {
            table_values: vec![table_value.clone()],
            ..TablePropertiesHwpxValueCatalog::default()
        },
        limits,
    )
    .map_err(|error| format!("table properties step failed: {error:?}"))?;
    let first_read = TablePropertiesHwpxReader::read_existing(
        &first.header,
        &first.section,
        0,
        &first.binding,
        limits,
    )?;
    if first_read.table_value != table_value
        || hex(first_read.state.canonical_sha256(properties_limits)?)
            != table_plan.receipt().after_state_sha256
    {
        return Err("table-only properties step differs".into());
    }
    let cell_request = TablePropertiesRequest::from_draft(
        TablePropertiesRequestDraft {
            schema_version: TABLE_PROPERTIES_SCHEMA_VERSION.to_owned(),
            table_id: first_read.state.table_id().clone(),
            expected_state_sha256: hex(first_read.state.canonical_sha256(properties_limits)?),
            selected_slots: vec![CellCoordinate { row: 1, column: 0 }],
            operation: TablePropertiesOperation::SetProperties {
                table_properties_sha256: None,
                cell_properties_sha256: Some(cell_digest.clone()),
            },
        },
        &first_read.state,
        &first_read.grid,
        properties_limits,
    )?;
    let cell_plan = TablePropertiesBuilder::build(
        &cell_request,
        &first_read.state,
        &first_read.grid,
        properties_limits,
    )?;
    let second_flow = document_flow_sha256(&first.section);
    let second_binding =
        TablePropertiesHwpxPartBinding::from_readback(&first_read, second_flow.clone())?;
    let lowered = TablePropertiesHwpxLowerer::lower_existing(
        &first.header,
        &first.section,
        0,
        &first.binding,
        &second_binding,
        &second_flow,
        &first_read.state,
        &first_read.grid,
        &cell_plan,
        &TablePropertiesHwpxValueCatalog {
            cell_values: vec![cell_value],
            ..TablePropertiesHwpxValueCatalog::default()
        },
        limits,
    )
    .map_err(|error| format!("cell properties step failed: {error:?}"))?;
    let reopened = TablePropertiesHwpxReader::read_existing(
        &lowered.header,
        &lowered.section,
        0,
        &lowered.binding,
        limits,
    )
    .map_err(|error| format!("final properties reopen failed: {error:?}"))?;
    require_target(&reopened, &table_value, cell_value)?;
    require_formula_and_pagination(&lowered.section)
        .map_err(|error| format!("formula or pagination verification failed: {error}"))?;

    let package = replace_parts(&ancestor, &lowered.header, &lowered.section, SOURCE_PREVIEW)?;
    assert_non_selected_parts_preserved(&ancestor, &package)?;
    let output_path = arguments.output_directory.join(OUTPUT_FILE);
    fs::create_dir(&arguments.output_directory)?;
    write_create_new(&output_path, &package)?;
    let manifest = Manifest {
        schema_version: "hwpx-agent.p06-09-table-properties-target-fixture/v1",
        source_ancestor_sha256: EXPECTED_ANCESTOR_SHA256,
        prepared_source_section_sha256,
        case: ManifestCase {
            case_id: "table-007-properties-formula-2x4",
            feature_id: "TABLE-007",
            capability_id: cell_plan.capability_id(),
            file: OUTPUT_FILE,
            sha256: hex(Sha256::digest(&package)),
            selected_table_ordinal: 0,
            selected_cell: CellCoordinate { row: 1, column: 0 },
            target_header_sha256: hex(Sha256::digest(&lowered.header)),
            target_section_sha256: hex(Sha256::digest(&lowered.section)),
            target_state_sha256: hex(reopened.state.canonical_sha256(properties_limits)?),
            target_grid_sha256: hex(reopened.grid.canonical_sha256()?),
            target_table_value_sha256: table_digest,
            target_cell_value_sha256: cell_digest,
            operations: vec![
                operation_evidence("set_table_properties", &table_request, &table_plan)?,
                operation_evidence("set_cell_properties", &cell_request, &cell_plan)?,
            ],
            rows: reopened.grid.rows(),
            columns: reopened.grid.columns(),
            master_cells: reopened.grid.master_cell_count(),
            payload_blocks: reopened.payload_block_count,
            formula_count: reopened.formula_count,
            page_split: "cell",
            table_lock: reopened.table_value.lock,
            table_no_adjust: reopened.table_value.no_adjust,
            changed_master_cells: lowered.receipt.changed_master_cell_count,
            preserved_formula_count: lowered.receipt.preserved_formula_count,
            binding: binding_evidence(&lowered.binding.table),
        },
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
        &read_bounded_file(&arguments.ancestor, MAX_FIXTURE_BYTES)?,
        EXPECTED_ANCESTOR_SHA256,
        "ancestor recheck",
    )?;
    println!(
        "schema={} state=pass target_count=1 actual_hangul_2020=false",
        manifest.schema_version
    );
    Ok(())
}

/// Builds the exact TABLE-008/009/047 current-target batch without mutating its ancestor.
///
/// This entry point is shared by the dedicated example binary while the original TABLE-007
/// command-line behavior and artifact remain byte stable.
///
/// # Errors
///
/// Rejects wrong ancestor identity, malformed packages, invalid plans, readback drift, output
/// limits, existing destinations, and any file publication failure.
#[allow(clippy::too_many_lines)]
pub fn run_table_008_009_047(
    ancestor_path: &Path,
    expected_ancestor_sha256: &str,
    output_directory: &Path,
) -> Result<(), Box<dyn Error>> {
    require_lower_sha256(expected_ancestor_sha256)?;
    if expected_ancestor_sha256 != EXPECTED_ANCESTOR_SHA256 {
        return Err("exact property batch ancestor identity differs".into());
    }
    if ancestor_path.extension().and_then(|value| value.to_str()) != Some("hwpx") {
        return Err("ancestor must be an .hwpx file".into());
    }
    if output_directory.exists() {
        return Err("output directory already exists".into());
    }
    let parent = output_directory
        .parent()
        .ok_or("output directory has no parent")?;
    if !parent.is_dir() {
        return Err("output parent is not an existing directory".into());
    }

    let ancestor = read_bounded_file(ancestor_path, MAX_FIXTURE_BYTES)?;
    require_digest(&ancestor, EXPECTED_ANCESTOR_SHA256, "ancestor")?;
    let (header, ancestor_section) = read_parts(&ancestor)?;
    let source_section = prepare_source_section(&ancestor_section)?;
    let prepared_source_section_sha256 = hex(Sha256::digest(&source_section));
    let binding = properties_binding()?;
    let each_lines = [
        border_line(LineType2::Solid, Color::Rgb(0xc0, 0x00, 0x00)),
        border_line(LineType2::Dash, Color::Rgb(0x00, 0x70, 0xc0)),
        border_line(LineType2::DoubleSlim, Color::Rgb(0x70, 0x30, 0xa0)),
        border_line(LineType2::Dot, Color::Rgb(0x00, 0x80, 0x00)),
    ];
    let each_line_sha256 = each_lines
        .iter()
        .map(|line| TablePropertiesHwpxValueCatalog::line_sha256(*line))
        .collect::<Result<Vec<_>, _>>()?;
    let each_background = border_background();
    let each_background_sha256 =
        TablePropertiesHwpxValueCatalog::background_sha256(&each_background);
    let rectangle = vec![
        CellCoordinate { row: 0, column: 0 },
        CellCoordinate { row: 0, column: 1 },
        CellCoordinate { row: 1, column: 0 },
        CellCoordinate { row: 1, column: 1 },
    ];
    let each = build_property_target(
        &ancestor,
        &header,
        &source_section,
        &binding,
        rectangle.clone(),
        TablePropertiesOperation::BorderEach {
            border: TableCellBorderPatch {
                top: digest_set(each_line_sha256[0].clone()),
                right: digest_set(each_line_sha256[1].clone()),
                bottom: digest_set(each_line_sha256[2].clone()),
                left: digest_set(each_line_sha256[3].clone()),
            },
            background: digest_set(each_background_sha256.clone()),
        },
        &TablePropertiesHwpxValueCatalog {
            lines: each_lines.to_vec(),
            backgrounds: vec![each_background],
            ..TablePropertiesHwpxValueCatalog::default()
        },
    )?;

    let unified_lines = [
        border_line(LineType2::Solid, Color::Rgb(0x00, 0x00, 0x00)),
        border_line(LineType2::Dash, Color::Rgb(0x00, 0x70, 0xc0)),
        border_line(LineType2::DoubleSlim, Color::Rgb(0xc0, 0x00, 0x00)),
        border_line(LineType2::Dot, Color::Rgb(0x00, 0x80, 0x00)),
        border_line(LineType2::DashDot, Color::Rgb(0x70, 0x30, 0xa0)),
        border_line(LineType2::LongDash, Color::Rgb(0xc6, 0x59, 0x11)),
    ];
    let unified_line_sha256 = unified_lines
        .iter()
        .map(|line| TablePropertiesHwpxValueCatalog::line_sha256(*line))
        .collect::<Result<Vec<_>, _>>()?;
    let unified_background = FillBrush {
        window: WindowBrush {
            face_color: Color::Rgb(0xe2, 0xf0, 0xd9),
            hatch_color: None,
            hatch_style: None,
            alpha: 255,
        },
    };
    let unified_background_sha256 =
        TablePropertiesHwpxValueCatalog::background_sha256(&unified_background);
    let unified = build_property_target(
        &ancestor,
        &header,
        &source_section,
        &binding,
        rectangle.clone(),
        TablePropertiesOperation::BorderUnified {
            border: TableUnifiedBorderPatch {
                outer_top: digest_set(unified_line_sha256[0].clone()),
                outer_right: digest_set(unified_line_sha256[1].clone()),
                outer_bottom: digest_set(unified_line_sha256[2].clone()),
                outer_left: digest_set(unified_line_sha256[3].clone()),
                inner_horizontal: digest_set(unified_line_sha256[4].clone()),
                inner_vertical: digest_set(unified_line_sha256[5].clone()),
            },
            background: digest_set(unified_background_sha256.clone()),
        },
        &TablePropertiesHwpxValueCatalog {
            lines: unified_lines.to_vec(),
            backgrounds: vec![unified_background],
            ..TablePropertiesHwpxValueCatalog::default()
        },
    )?;

    let diagonal_line = border_line(LineType2::Solid, Color::Rgb(0x70, 0x30, 0xa0));
    let diagonal_line_sha256 = TablePropertiesHwpxValueCatalog::line_sha256(diagonal_line)?;
    let diagonal_value = TableDiagonalValue {
        slash: TableDiagonalSlash {
            slash_type: TableDiagonalSlashType::Center,
            crooked: false,
            is_counter: false,
        },
        back_slash: TableDiagonalSlash {
            slash_type: TableDiagonalSlashType::Center,
            crooked: false,
            is_counter: false,
        },
        center_line: TableDiagonalCenterLine::None,
        line_sha256: diagonal_line_sha256.clone(),
    };
    let diagonal_slots = vec![CellCoordinate { row: 0, column: 2 }];
    let diagonal = build_property_target(
        &ancestor,
        &header,
        &source_section,
        &binding,
        diagonal_slots.clone(),
        TablePropertiesOperation::CellDiagonal {
            apply_mode: TableDiagonalApplyMode::EachCell,
            patch: TableDiagonalPatch::Set {
                value: diagonal_value.clone(),
            },
        },
        &TablePropertiesHwpxValueCatalog {
            lines: vec![diagonal_line],
            ..TablePropertiesHwpxValueCatalog::default()
        },
    )?;

    if (
        each.changed_master_cells,
        each.border_side_change_count,
        each.background_change_count,
        each.per_cell_edge_assignment_count,
        each.unselected_master_cell_preserved_count,
        each.preserved_formula_count,
    ) != (4, 16, 4, 16, 4, 1)
        || (
            unified.changed_master_cells,
            unified.background_change_count,
            unified.outer_edge_assignment_count,
            unified.inner_edge_assignment_count,
            unified.unselected_master_cell_preserved_count,
            unified.preserved_formula_count,
        ) != (4, 4, 8, 8, 4, 1)
        || (
            diagonal.changed_master_cells,
            diagonal.diagonal_change_count,
            diagonal.diagonal_assignment_count,
            diagonal.unselected_master_cell_preserved_count,
            diagonal.preserved_formula_count,
        ) != (1, 1, 1, 7, 1)
    {
        return Err("property batch planner receipt differs".into());
    }

    let cases = vec![
        property_batch_case(
            "table-008-cell-border-each-formula-2x4",
            "TABLE-008",
            TABLE_008_OUTPUT_FILE,
            rectangle.clone(),
            "border_each",
            each_line_sha256,
            Some(each_background_sha256),
            None,
            None,
            &each,
        ),
        property_batch_case(
            "table-009-cell-border-unified-formula-2x4",
            "TABLE-009",
            TABLE_009_OUTPUT_FILE,
            rectangle,
            "border_unified",
            unified_line_sha256,
            Some(unified_background_sha256),
            None,
            None,
            &unified,
        ),
        property_batch_case(
            "table-047-cell-diagonal-formula-2x4",
            "TABLE-047",
            TABLE_047_OUTPUT_FILE,
            diagonal_slots,
            "cell_diagonal_each",
            vec![diagonal_line_sha256],
            None,
            Some(diagonal_value),
            Some(TableDiagonalApplyMode::EachCell),
            &diagonal,
        ),
    ];
    fs::create_dir(output_directory)?;
    for (file, target) in [
        (TABLE_008_OUTPUT_FILE, &each),
        (TABLE_009_OUTPUT_FILE, &unified),
        (TABLE_047_OUTPUT_FILE, &diagonal),
    ] {
        write_create_new(&output_directory.join(file), &target.package)?;
    }
    let manifest = PropertyBatchManifest {
        schema_version: "hwpx-agent.p06-09-table-borders-diagonal-target-fixture/v1",
        source_ancestor_sha256: EXPECTED_ANCESTOR_SHA256,
        prepared_source_section_sha256,
        cases,
        actual_hangul_2020: false,
        render: "not_run",
        automation: "not_run",
        differential: "not_run",
    };
    write_create_new(
        &output_directory.join("fixture-manifest.json"),
        &serde_json::to_vec_pretty(&manifest)?,
    )?;
    require_digest(
        &read_bounded_file(ancestor_path, MAX_FIXTURE_BYTES)?,
        EXPECTED_ANCESTOR_SHA256,
        "ancestor recheck",
    )?;
    println!(
        "schema={} state=pass target_count=3 actual_hangul_2020=false",
        manifest.schema_version
    );
    Ok(())
}

fn build_property_target(
    ancestor: &[u8],
    header: &[u8],
    source_section: &[u8],
    binding: &TablePropertiesHwpxBinding,
    selected_slots: Vec<CellCoordinate>,
    operation: TablePropertiesOperation,
    catalog: &TablePropertiesHwpxValueCatalog,
) -> Result<BuiltPropertyTarget, Box<dyn Error>> {
    let hwpx_limits = TablePropertiesHwpxLimits::default();
    let properties_limits = TablePropertiesLimits::default();
    let source =
        TablePropertiesHwpxReader::read_existing(header, source_section, 0, binding, hwpx_limits)?;
    require_source(&source)?;
    let request = TablePropertiesRequest::from_draft(
        TablePropertiesRequestDraft {
            schema_version: TABLE_PROPERTIES_SCHEMA_VERSION.to_owned(),
            table_id: source.state.table_id().clone(),
            expected_state_sha256: hex(source.state.canonical_sha256(properties_limits)?),
            selected_slots,
            operation,
        },
        &source.state,
        &source.grid,
        properties_limits,
    )?;
    let plan =
        TablePropertiesBuilder::build(&request, &source.state, &source.grid, properties_limits)?;
    let flow = document_flow_sha256(source_section);
    let part_binding = TablePropertiesHwpxPartBinding::from_readback(&source, flow.clone())?;
    let lowered = TablePropertiesHwpxLowerer::lower_existing(
        header,
        source_section,
        0,
        binding,
        &part_binding,
        &flow,
        &source.state,
        &source.grid,
        &plan,
        catalog,
        hwpx_limits,
    )?;
    let reopened = TablePropertiesHwpxReader::read_existing(
        &lowered.header,
        &lowered.section,
        0,
        &lowered.binding,
        hwpx_limits,
    )?;
    if reopened.grid != source.grid
        || reopened.table_value != source.table_value
        || reopened.cell_values != source.cell_values
        || reopened.payload_block_count != 7
        || reopened.formula_count != 1
        || plan.mutations().iter().any(|mutation| {
            reopened
                .state
                .cells()
                .iter()
                .find(|cell| cell.master_cell_id == mutation.master_cell_id)
                .is_none_or(|cell| cell.properties != mutation.after)
        })
    {
        return Err("property batch semantic reopen differs".into());
    }
    require_formula_and_pagination(&lowered.section)?;
    let package = replace_parts(ancestor, &lowered.header, &lowered.section, SOURCE_PREVIEW)?;
    assert_non_selected_parts_preserved(ancestor, &package)?;
    let receipt = plan.receipt();
    Ok(BuiltPropertyTarget {
        capability_id: plan.capability_id(),
        package,
        output_binding: lowered.binding,
        target_header_sha256: hex(Sha256::digest(&lowered.header)),
        target_section_sha256: hex(Sha256::digest(&lowered.section)),
        source_state_sha256: receipt.before_state_sha256.clone(),
        target_state_sha256: receipt.after_state_sha256.clone(),
        target_grid_sha256: receipt.grid_sha256.clone(),
        request_sha256: receipt.request_sha256.clone(),
        plan_sha256: hex(plan.canonical_sha256(properties_limits)?),
        rows: reopened.grid.rows(),
        columns: reopened.grid.columns(),
        master_cells: reopened.grid.master_cell_count(),
        payload_blocks: reopened.payload_block_count,
        formula_count: reopened.formula_count,
        changed_master_cells: receipt.changed_master_cell_count,
        border_side_change_count: receipt.border_side_change_count,
        background_change_count: receipt.background_change_count,
        per_cell_edge_assignment_count: receipt.per_cell_edge_assignment_count,
        outer_edge_assignment_count: receipt.outer_edge_assignment_count,
        inner_edge_assignment_count: receipt.inner_edge_assignment_count,
        diagonal_change_count: receipt.diagonal_change_count,
        diagonal_assignment_count: receipt.diagonal_assignment_count,
        unselected_master_cell_preserved_count: receipt.unselected_master_cell_preserved_count,
        preserved_formula_count: lowered.receipt.preserved_formula_count,
        added_border_fill_count: lowered.receipt.added_border_fill_count,
    })
}

#[allow(clippy::too_many_arguments)]
fn property_batch_case(
    case_id: &'static str,
    feature_id: &'static str,
    file: &'static str,
    selected_slots: Vec<CellCoordinate>,
    operation_kind: &'static str,
    line_sha256: Vec<String>,
    background_sha256: Option<String>,
    diagonal: Option<TableDiagonalValue>,
    diagonal_apply_mode: Option<TableDiagonalApplyMode>,
    target: &BuiltPropertyTarget,
) -> PropertyBatchManifestCase {
    PropertyBatchManifestCase {
        case_id,
        feature_id,
        capability_id: target.capability_id,
        file,
        sha256: hex(Sha256::digest(&target.package)),
        selected_table_ordinal: 0,
        selected_slots,
        operation_kind,
        line_sha256,
        background_sha256,
        diagonal,
        diagonal_apply_mode,
        target_header_sha256: target.target_header_sha256.clone(),
        target_section_sha256: target.target_section_sha256.clone(),
        source_state_sha256: target.source_state_sha256.clone(),
        target_state_sha256: target.target_state_sha256.clone(),
        target_grid_sha256: target.target_grid_sha256.clone(),
        request_sha256: target.request_sha256.clone(),
        plan_sha256: target.plan_sha256.clone(),
        rows: target.rows,
        columns: target.columns,
        master_cells: target.master_cells,
        payload_blocks: target.payload_blocks,
        formula_count: target.formula_count,
        page_split: "cell",
        changed_master_cells: target.changed_master_cells,
        border_side_change_count: target.border_side_change_count,
        background_change_count: target.background_change_count,
        per_cell_edge_assignment_count: target.per_cell_edge_assignment_count,
        outer_edge_assignment_count: target.outer_edge_assignment_count,
        inner_edge_assignment_count: target.inner_edge_assignment_count,
        diagonal_change_count: target.diagonal_change_count,
        diagonal_assignment_count: target.diagonal_assignment_count,
        unselected_master_cell_preserved_count: target.unselected_master_cell_preserved_count,
        preserved_formula_count: target.preserved_formula_count,
        added_border_fill_count: target.added_border_fill_count,
        binding: property_batch_binding_evidence(&target.output_binding),
    }
}

fn property_batch_binding_evidence(
    value: &TablePropertiesHwpxBinding,
) -> PropertyBatchBindingEvidence {
    PropertyBatchBindingEvidence {
        table: binding_evidence(&value.table),
        diagonals: value
            .diagonals
            .iter()
            .map(|binding| DiagonalBindingEvidence {
                master_cell_id: binding.master_cell_id.as_str().to_owned(),
                apply_mode: binding.apply_mode,
                region: binding.region,
                value: binding.value.clone(),
            })
            .collect(),
    }
}

fn border_line(line_type: LineType2, color: Color) -> BorderLine {
    BorderLine {
        line_type,
        width: BorderWidth::Mm0_3,
        color,
    }
}

fn border_background() -> FillBrush {
    FillBrush {
        window: WindowBrush {
            face_color: Color::Rgb(0xff, 0xf2, 0xcc),
            hatch_color: None,
            hatch_style: None,
            alpha: 255,
        },
    }
}

fn digest_set(sha256: String) -> TablePropertyDigestPatch {
    TablePropertyDigestPatch::Set { sha256 }
}

fn require_source(
    source: &hwpx_package::TablePropertiesHwpxReadback,
) -> Result<(), Box<dyn Error>> {
    if source.grid.rows() != 2
        || source.grid.columns() != 4
        || source.grid.master_cell_count() != 8
        || source.payload_block_count != 7
        || source.formula_count != 1
        || source.table_value.lock
        || source.table_value.no_adjust
    {
        return Err("prepared properties source shape differs".into());
    }
    Ok(())
}

fn require_target(
    target: &hwpx_package::TablePropertiesHwpxReadback,
    table_value: &hwpx_package::TablePropertiesHwpxTableValue,
    cell_value: TablePropertiesHwpxCellValue,
) -> Result<(), Box<dyn Error>> {
    if target.table_value != *table_value
        || target.cell_values.get(4) != Some(&cell_value)
        || target.grid.rows() != 2
        || target.grid.columns() != 4
        || target.grid.master_cell_count() != 8
        || target.payload_block_count != 7
        || target.formula_count != 1
    {
        return Err("properties target semantic reopen differs".into());
    }
    Ok(())
}

fn require_formula_and_pagination(section: &[u8]) -> Result<(), Box<dyn Error>> {
    let formula = TableFormulaHwpxReader::read_in_section(
        section,
        0,
        TableFormulaHwpxLimits::default(),
        domain_ir::FormulaLimits::default(),
    )?;
    if formula.formula.owner() != (CellCoordinate { row: 1, column: 3 })
        || formula
            .formula
            .ast()
            .canonical_formula(domain_ir::FormulaLimits::default())?
            != "SUM(A2:C2)"
    {
        return Err("properties target formula drifted".into());
    }
    if section
        .windows(b"pageBreak=\"CELL\"".len())
        .filter(|window| *window == b"pageBreak=\"CELL\"")
        .count()
        != 1
    {
        return Err("properties target page split drifted".into());
    }
    Ok(())
}

fn properties_binding() -> Result<TablePropertiesHwpxBinding, Box<dyn Error>> {
    let mut cells = Vec::new();
    for index in 0..8 {
        cells.push(TableRulingHwpxCellBinding {
            master_cell_id: id(&format!("properties-target-cell-{index}"))?,
            payload_block_ids: if index == 7 {
                Vec::new()
            } else {
                vec![id(&format!("properties-target-payload-{index}"))?]
            },
        });
    }
    Ok(TablePropertiesHwpxBinding {
        table: TableRulingHwpxBinding {
            table_id: id("properties-target-table")?,
            row_boundaries_hwpunit: vec![0, ROW_HEIGHT, TABLE_HEIGHT],
            column_boundaries_hwpunit: vec![0, 10_488, 20_976, 31_464, TABLE_WIDTH],
            cells,
        },
        diagonals: Vec::new(),
    })
}

fn binding_evidence(binding: &TableRulingHwpxBinding) -> BindingEvidence {
    BindingEvidence {
        table_id: binding.table_id.as_str().to_owned(),
        row_boundaries_hwpunit: binding.row_boundaries_hwpunit.clone(),
        column_boundaries_hwpunit: binding.column_boundaries_hwpunit.clone(),
        cells: binding
            .cells
            .iter()
            .map(|cell| BindingCellEvidence {
                master_cell_id: cell.master_cell_id.as_str().to_owned(),
                payload_block_ids: cell
                    .payload_block_ids
                    .iter()
                    .map(|block| block.as_str().to_owned())
                    .collect(),
            })
            .collect(),
    }
}

fn operation_evidence(
    name: &'static str,
    request: &TablePropertiesRequest,
    plan: &domain_ir::TablePropertiesPlan,
) -> Result<OperationEvidence, Box<dyn Error>> {
    let receipt = plan.receipt();
    if hex(request.canonical_sha256(TablePropertiesLimits::default())?) != receipt.request_sha256 {
        return Err("properties request receipt drifted".into());
    }
    Ok(OperationEvidence {
        name,
        request_sha256: receipt.request_sha256.clone(),
        plan_sha256: hex(plan.canonical_sha256(TablePropertiesLimits::default())?),
        source_state_sha256: receipt.before_state_sha256.clone(),
        target_state_sha256: receipt.after_state_sha256.clone(),
        table_properties_changed: receipt.table_properties_changed,
        changed_master_cells: receipt.changed_master_cell_count,
        preserved_formula_count: receipt.formula_preserved_count,
    })
}

fn prepare_source_section(bytes: &[u8]) -> Result<Vec<u8>, Box<dyn Error>> {
    let mut source = String::from_utf8(bytes.to_vec())?;
    source = replace_once(
        &source,
        "height=\"2564\" heightRelTo=\"ABSOLUTE\"",
        "height=\"8000\" heightRelTo=\"ABSOLUTE\"",
    )?;
    if source.matches("height=\"282\"").count() != 8 {
        return Err("source cell height cardinality differs".into());
    }
    source = source.replace("height=\"282\"", "height=\"4000\"");
    for value in ["2", "3", "4", "5"] {
        source = replace_first(&source, "<hp:t>0</hp:t>", &format!("<hp:t>{value}</hp:t>"))?;
    }
    if source.matches("<hp:t>0</hp:t>").count() != 0
        || source.matches("type=\"FORMULA\"").count() != 1
    {
        return Err("source visible value or formula cardinality differs".into());
    }
    Ok(source.into_bytes())
}

fn read_parts(source: &[u8]) -> Result<(Vec<u8>, Vec<u8>), Box<dyn Error>> {
    let mut archive = BoundedZipReader::open(Cursor::new(source), PackageLimits::default())?;
    Ok((
        read_part(&mut archive, "Contents/header.xml")?,
        read_part(&mut archive, "Contents/section0.xml")?,
    ))
}

fn read_part(
    archive: &mut BoundedZipReader<Cursor<&[u8]>>,
    path: &str,
) -> Result<Vec<u8>, Box<dyn Error>> {
    let index = archive
        .entries()
        .iter()
        .find(|entry| entry.path.as_str() == path)
        .map(|entry| entry.index)
        .ok_or("required package part is missing")?;
    Ok(archive.read_entry(index)?)
}

fn replace_parts(
    source: &[u8],
    header: &[u8],
    section: &[u8],
    preview: &[u8],
) -> Result<Vec<u8>, Box<dyn Error>> {
    let mut archive = BoundedZipReader::open(Cursor::new(source), PackageLimits::default())?;
    let entries = archive.entries().to_vec();
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    let mut replacements = [0_u8; 3];
    for entry in entries {
        let path = entry.path.as_str();
        let method = match entry.compression {
            Compression::Stored => CompressionMethod::Stored,
            Compression::Deflated => CompressionMethod::Deflated,
        };
        let bytes = match path {
            "Contents/header.xml" => {
                replacements[0] += 1;
                header.to_vec()
            }
            "Contents/section0.xml" => {
                replacements[1] += 1;
                section.to_vec()
            }
            "Preview/PrvText.txt" => {
                replacements[2] += 1;
                preview.to_vec()
            }
            _ => archive.read_entry(entry.index)?,
        };
        let mut options = SimpleFileOptions::default()
            .compression_method(method)
            .last_modified_time(DateTime::default())
            .system(zip::System::Unix)
            .unix_permissions(0o644);
        if method == CompressionMethod::Deflated {
            options = options.compression_level(Some(NORMALIZED_DEFLATE_LEVEL));
        }
        writer.start_file(path, options)?;
        writer.write_all(&bytes)?;
    }
    if replacements != [1, 1, 1] {
        return Err("package replacement cardinality differs".into());
    }
    Ok(writer.finish()?.into_inner())
}

fn assert_non_selected_parts_preserved(source: &[u8], target: &[u8]) -> Result<(), Box<dyn Error>> {
    let mut source_archive = BoundedZipReader::open(Cursor::new(source), PackageLimits::default())?;
    let mut target_archive = BoundedZipReader::open(Cursor::new(target), PackageLimits::default())?;
    let source_entries = source_archive.entries().to_vec();
    let target_entries = target_archive.entries().to_vec();
    if source_entries.len() != target_entries.len() {
        return Err("target package entry count differs".into());
    }
    for (source_entry, target_entry) in source_entries.iter().zip(&target_entries) {
        if source_entry.path != target_entry.path
            || source_entry.compression != target_entry.compression
        {
            return Err("target package graph differs".into());
        }
        let path = source_entry.path.as_str();
        if !matches!(
            path,
            "Contents/header.xml" | "Contents/section0.xml" | "Preview/PrvText.txt"
        ) && source_archive.read_entry(source_entry.index)?
            != target_archive.read_entry(target_entry.index)?
        {
            return Err(format!("non-selected package part changed: {path}").into());
        }
    }
    Ok(())
}

fn write_create_new(path: &Path, bytes: &[u8]) -> Result<(), Box<dyn Error>> {
    let mut file = OpenOptions::new().write(true).create_new(true).open(path)?;
    file.write_all(bytes)?;
    file.sync_all()?;
    Ok(())
}

fn read_bounded_file(path: &Path, limit: u64) -> Result<Vec<u8>, Box<dyn Error>> {
    let metadata = fs::symlink_metadata(path)?;
    if !metadata.file_type().is_file()
        || metadata.file_type().is_symlink()
        || metadata.len() > limit
    {
        return Err("input is not a bounded regular file".into());
    }
    Ok(fs::read(path)?)
}

fn require_digest(bytes: &[u8], expected: &str, label: &str) -> Result<(), Box<dyn Error>> {
    if hex(Sha256::digest(bytes)) != expected {
        return Err(format!("{label} SHA-256 differs").into());
    }
    Ok(())
}

fn require_lower_sha256(value: &str) -> Result<(), Box<dyn Error>> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err("SHA-256 must be lowercase hexadecimal".into());
    }
    Ok(())
}

fn replace_once(source: &str, before: &str, after: &str) -> Result<String, Box<dyn Error>> {
    if source.matches(before).count() != 1 {
        return Err(format!("exact replacement cardinality differs: {before}").into());
    }
    Ok(source.replacen(before, after, 1))
}

fn replace_first(source: &str, before: &str, after: &str) -> Result<String, Box<dyn Error>> {
    if !source.contains(before) {
        return Err(format!("replacement marker is missing: {before}").into());
    }
    Ok(source.replacen(before, after, 1))
}

fn document_flow_sha256(section: &[u8]) -> String {
    let mut digest = Sha256::new();
    digest.update(b"hwpx-agent.p06-09-table-properties-target-flow/v1\0");
    digest.update(section);
    hex(digest.finalize())
}

fn id(value: &str) -> Result<LogicalId, Box<dyn Error>> {
    Ok(LogicalId::parse(value)?)
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn exact_target_values_are_distinct_and_bounded() {
        let value = TablePropertiesHwpxCellValue {
            margins: Some(CellMargins {
                left: 1_200,
                right: 200,
                top: 900,
                bottom: 100,
            }),
            paragraph_property_id_ref: 0,
            horizontal_alignment: HorizontalAlignment::Justify,
            vertical_alignment: CellVerticalAlignment::Bottom,
            text_direction: CellTextDirection::VerticalAll,
            protection: CellProtection::ProtectedEditable,
        };
        assert_eq!(value.margins.unwrap().left, 1_200);
        assert_eq!(OUTPUT_FILE, "table-007-properties-formula-2x4.hwpx");
        assert_eq!(SOURCE_PREVIEW, b"<2><3><4><5><17><10><25><52>\r\n\r\n");
    }
}
