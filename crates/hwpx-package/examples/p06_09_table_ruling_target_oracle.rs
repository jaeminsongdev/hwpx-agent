use std::env;
use std::error::Error;
use std::fs;
use std::io::Cursor;
use std::path::{Path, PathBuf};

use domain_ir::{CellCoordinate, LogicalId, TableRulingAxis, TableRulingLimits};
use hwpx_package::{
    BoundedZipReader, HANCOM_2020_PARAGRAPH_NAMESPACE, IdIndex, IdIndexLimits, IdRuleProfile,
    PackageGraph, PackageGraphLimits, PackageLimits, PreservingXmlDocument, TableRulingHwpxBinding,
    TableRulingHwpxCellBinding, TableRulingHwpxLimits, TableRulingHwpxReadback,
    TableRulingHwpxReader, XmlByteSpan, XmlElementToken,
};
use serde::Deserialize;
use sha2::{Digest as _, Sha256};

const MAX_FILE_BYTES: u64 = 8 * 1024 * 1024;
const MAX_MANIFEST_BYTES: u64 = 256 * 1024;
const MAX_PREVIEW_BYTES: usize = 256 * 1024;
const MAX_RENDERER_CACHE_ARRAYS: usize = 512;
const EXPECTED_PACKAGE_PARTS: usize = 11;
const EXPECTED_MANIFEST_SHA256: &str =
    "8296cf4057c1cb6b27c800c15694866008c31cfa290cd6863321179c1efda543";
const EXPECTED_ANCESTOR_SHA256: &str =
    "6514a69b8c8c9d320bc19a032b16f2b71d59a38f164c690bc9e3d320a93320e5";

#[derive(Clone, Copy)]
struct CaseProfile {
    case_id: &'static str,
    feature_id: &'static str,
    capability_id: &'static str,
    file: &'static str,
    table_id: &'static str,
    selected_table_ordinal: usize,
    rows: u32,
    columns: u32,
    master_cells: usize,
    payload_blocks: usize,
    formulas: usize,
    table_count: usize,
    operations: &'static [&'static str],
}

const CASES: [CaseProfile; 5] = [
    CaseProfile {
        case_id: "table-002-draw-outer",
        feature_id: "TABLE-002",
        capability_id: "table.draw",
        file: "table-002-draw-outer.hwpx",
        table_id: "draw-outer-table",
        selected_table_ordinal: 1,
        rows: 1,
        columns: 1,
        master_cells: 1,
        payload_blocks: 0,
        formulas: 0,
        table_count: 2,
        operations: &["draw_outer_rectangle"],
    },
    CaseProfile {
        case_id: "table-002-draw-topology",
        feature_id: "TABLE-002",
        capability_id: "table.draw",
        file: "table-002-draw-topology.hwpx",
        table_id: "draw-topology-table",
        selected_table_ordinal: 0,
        rows: 3,
        columns: 6,
        master_cells: 16,
        payload_blocks: 8,
        formulas: 0,
        table_count: 1,
        operations: &[
            "draw_full_row",
            "draw_full_column",
            "draw_local_cell_split",
            "draw_existing_boundary_style",
        ],
    },
    CaseProfile {
        case_id: "table-002-draw-diagonals-formula",
        feature_id: "TABLE-002",
        capability_id: "table.draw",
        file: "table-002-draw-diagonals-formula.hwpx",
        table_id: "draw-diagonal-table",
        selected_table_ordinal: 0,
        rows: 2,
        columns: 4,
        master_cells: 8,
        payload_blocks: 7,
        formulas: 1,
        table_count: 1,
        operations: &[
            "draw_slash_on_formula_cell",
            "draw_back_slash_on_formula_cell",
        ],
    },
    CaseProfile {
        case_id: "table-003-eraser-structural-merge",
        feature_id: "TABLE-003",
        capability_id: "table.eraser",
        file: "table-003-eraser-structural-merge.hwpx",
        table_id: "eraser-merge-table",
        selected_table_ordinal: 0,
        rows: 2,
        columns: 4,
        master_cells: 6,
        payload_blocks: 8,
        formulas: 0,
        table_count: 1,
        operations: &["erase_shared_column_edge"],
    },
    CaseProfile {
        case_id: "table-003-eraser-transparent-formula",
        feature_id: "TABLE-003",
        capability_id: "table.eraser",
        file: "table-003-eraser-transparent-formula.hwpx",
        table_id: "eraser-transparent-table",
        selected_table_ordinal: 0,
        rows: 2,
        columns: 4,
        master_cells: 8,
        payload_blocks: 7,
        formulas: 1,
        table_count: 1,
        operations: &["erase_outer_edge_on_formula_cell"],
    },
];

struct Arguments {
    manifest: PathBuf,
    expected_manifest_sha256: String,
    case_id: String,
    oracle: PathBuf,
    expected_oracle_sha256: String,
}

impl Arguments {
    fn parse() -> Result<Self, Box<dyn Error>> {
        let mut values = env::args_os();
        let _program = values.next();
        let manifest = path_argument(&mut values, "fixture manifest")?;
        let expected_manifest_sha256 = string_argument(&mut values, "manifest SHA-256")?;
        let case_id = string_argument(&mut values, "case ID")?;
        let oracle = path_argument(&mut values, "oracle HWPX")?;
        let expected_oracle_sha256 = string_argument(&mut values, "oracle SHA-256")?;
        if values.next().is_some() {
            return Err("too many arguments".into());
        }
        Ok(Self {
            manifest,
            expected_manifest_sha256,
            case_id,
            oracle,
            expected_oracle_sha256,
        })
    }
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Manifest {
    schema_version: String,
    source_ancestor_sha256: String,
    cases: Vec<ManifestCase>,
    actual_hangul_2020: bool,
    render: String,
    automation: String,
    differential: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ManifestCase {
    case_id: String,
    feature_id: String,
    capability_id: String,
    file: String,
    sha256: String,
    selected_table_ordinal: usize,
    source_section_sha256: String,
    target_header_sha256: String,
    target_section_sha256: String,
    target_state_sha256: String,
    target_grid_sha256: String,
    target_rows: u32,
    target_columns: u32,
    target_master_cells: usize,
    payload_block_count: usize,
    formula_count: usize,
    binding: BindingManifest,
    operations: Vec<OperationManifest>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct BindingManifest {
    table_id: String,
    row_boundaries_hwpunit: Vec<u32>,
    column_boundaries_hwpunit: Vec<u32>,
    cells: Vec<BindingCellManifest>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct BindingCellManifest {
    master_cell_id: String,
    payload_block_ids: Vec<String>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct OperationManifest {
    name: String,
    capability_id: String,
    request_sha256: String,
    plan_sha256: String,
    source_state_sha256: Option<String>,
    source_grid_sha256: Option<String>,
    target_state_sha256: String,
    target_grid_sha256: String,
    added_border_fill_count: usize,
}

struct PackageParts {
    part_count: usize,
    header: Vec<u8>,
    section: Vec<u8>,
    preview: Vec<u8>,
}

struct RendererCacheEvidence {
    count: usize,
    sha256: [u8; 32],
}

fn main() -> Result<(), Box<dyn Error>> {
    run(&Arguments::parse()?)
}

fn run(arguments: &Arguments) -> Result<(), Box<dyn Error>> {
    require_lower_sha256(&arguments.expected_manifest_sha256)?;
    require_lower_sha256(&arguments.expected_oracle_sha256)?;
    if arguments.expected_manifest_sha256 != EXPECTED_MANIFEST_SHA256 {
        return Err("exact ruling fixture manifest identity differs".into());
    }
    let manifest_bytes = read_bounded_file(&arguments.manifest, MAX_MANIFEST_BYTES)?;
    require_digest(
        &manifest_bytes,
        &arguments.expected_manifest_sha256,
        "manifest",
    )?;
    let manifest: Manifest = serde_json::from_slice(&manifest_bytes)?;
    validate_manifest(&manifest)?;
    let profile = case_profile(&arguments.case_id)?;
    let case = manifest
        .cases
        .iter()
        .find(|case| case.case_id == profile.case_id)
        .ok_or("ruling case is missing from manifest")?;
    let manifest_directory = arguments
        .manifest
        .parent()
        .ok_or("manifest parent is missing")?;
    let target_path = manifest_directory.join(&case.file);
    if fs::canonicalize(&target_path)? == fs::canonicalize(&arguments.oracle)? {
        return Err("target and oracle paths must differ".into());
    }
    let target_bytes = read_bounded_file(&target_path, MAX_FILE_BYTES)?;
    let oracle_bytes = read_bounded_file(&arguments.oracle, MAX_FILE_BYTES)?;
    require_digest(&target_bytes, &case.sha256, "target")?;
    require_digest(&oracle_bytes, &arguments.expected_oracle_sha256, "oracle")?;

    let target = read_package(&target_bytes)?;
    let oracle = read_package(&oracle_bytes)?;
    if target.part_count != EXPECTED_PACKAGE_PARTS || oracle.part_count != target.part_count {
        return Err("ruling package part cardinality differs".into());
    }
    require_digest(&target.header, &case.target_header_sha256, "target header")?;
    require_digest(
        &target.section,
        &case.target_section_sha256,
        "target section",
    )?;
    if target.preview.len() > MAX_PREVIEW_BYTES || oracle.preview.len() > MAX_PREVIEW_BYTES {
        return Err("ruling preview is not bounded".into());
    }

    let (target_section, target_cache) = strip_renderer_caches(&target.section)?;
    let (oracle_section, oracle_cache) = strip_renderer_caches(&oracle.section)?;
    if target_cache.count != 0 {
        return Err("ruling target unexpectedly contains renderer caches".into());
    }
    let target_table_count = count_elements(&target_section, "tbl")?;
    let oracle_table_count = count_elements(&oracle_section, "tbl")?;
    let expected_document_formulas = usize::from(matches!(
        profile.case_id,
        "table-002-draw-outer"
            | "table-002-draw-diagonals-formula"
            | "table-003-eraser-transparent-formula"
    ));
    if target_table_count != profile.table_count
        || oracle_table_count != target_table_count
        || count_formula_fields(&target_section)? != expected_document_formulas
        || count_formula_fields(&oracle_section)? != expected_document_formulas
    {
        return Err("ruling document-level preservation differs".into());
    }

    let binding = binding_from_manifest(&case.binding)?;
    let target_readback = read_ruling(
        &target.header,
        &target_section,
        case.selected_table_ordinal,
        &binding,
    )?;
    let oracle_readback = read_ruling(
        &oracle.header,
        &oracle_section,
        case.selected_table_ordinal,
        &binding,
    )?;
    require_case_semantics(profile, case, &target_readback)?;
    require_equivalent_readback(&target_readback, &oracle_readback)?;
    require_case_semantics(profile, case, &oracle_readback)?;
    require_selected_table_exterior_equal(profile, &target_section, &oracle_section)?;

    require_digest(
        &read_bounded_file(&target_path, MAX_FILE_BYTES)?,
        &case.sha256,
        "target recheck",
    )?;
    require_digest(
        &read_bounded_file(&arguments.oracle, MAX_FILE_BYTES)?,
        &arguments.expected_oracle_sha256,
        "oracle recheck",
    )?;
    print_receipt(
        arguments,
        profile,
        case,
        expected_document_formulas,
        &oracle_cache,
    );
    Ok(())
}

fn print_receipt(
    arguments: &Arguments,
    profile: CaseProfile,
    case: &ManifestCase,
    expected_document_formulas: usize,
    oracle_cache: &RendererCacheEvidence,
) {
    println!(
        concat!(
            "schema=hwpx-agent.p06-09-table-ruling-target-oracle/v1 state=pass ",
            "case_id={} feature_id={} capability_id={} target_sha256={} oracle_sha256={} ",
            "target_state_sha256={} target_grid_sha256={} rows={} columns={} ",
            "master_cells={} payload_blocks={} formulas={} document_formula_fields={} ",
            "renderer_cache_count={} renderer_cache_sha256={} ",
            "typed_selected_table_and_section_exterior_equal_after_renderer_normalization=true"
        ),
        profile.case_id,
        profile.feature_id,
        profile.capability_id,
        case.sha256,
        arguments.expected_oracle_sha256,
        case.target_state_sha256,
        case.target_grid_sha256,
        profile.rows,
        profile.columns,
        profile.master_cells,
        profile.payload_blocks,
        profile.formulas,
        expected_document_formulas,
        oracle_cache.count,
        hex(oracle_cache.sha256),
    );
}

fn validate_manifest(manifest: &Manifest) -> Result<(), Box<dyn Error>> {
    if manifest.schema_version != "hwpx-agent.p06-09-table-ruling-target-fixture/v1"
        || manifest.source_ancestor_sha256 != EXPECTED_ANCESTOR_SHA256
        || manifest.actual_hangul_2020
        || manifest.render != "not_run"
        || manifest.automation != "not_run"
        || manifest.differential != "not_run"
        || manifest.cases.len() != CASES.len()
    {
        return Err("ruling manifest state differs".into());
    }
    for (index, (case, profile)) in manifest.cases.iter().zip(CASES).enumerate() {
        for digest in [
            &case.sha256,
            &case.source_section_sha256,
            &case.target_header_sha256,
            &case.target_section_sha256,
            &case.target_state_sha256,
            &case.target_grid_sha256,
        ] {
            require_lower_sha256(digest)?;
        }
        if case.case_id != profile.case_id
            || case.feature_id != profile.feature_id
            || case.capability_id != profile.capability_id
            || case.file != profile.file
            || case.selected_table_ordinal != profile.selected_table_ordinal
            || case.target_rows != profile.rows
            || case.target_columns != profile.columns
            || case.target_master_cells != profile.master_cells
            || case.payload_block_count != profile.payload_blocks
            || case.formula_count != profile.formulas
            || case.binding.table_id != profile.table_id
            || case.binding.cells.len() != profile.master_cells
            || case.operations.len() != profile.operations.len()
        {
            return Err("ruling manifest case profile differs".into());
        }
        let (expected_rows, expected_columns) = expected_boundaries(index);
        if case.binding.row_boundaries_hwpunit != expected_rows
            || case.binding.column_boundaries_hwpunit != expected_columns
            || case
                .binding
                .cells
                .iter()
                .map(|cell| cell.payload_block_ids.len())
                .sum::<usize>()
                != profile.payload_blocks
        {
            return Err("ruling manifest binding differs".into());
        }
        let mut previous_state: Option<&str> = None;
        let mut previous_grid: Option<&str> = None;
        for (operation_index, (operation, expected_name)) in
            case.operations.iter().zip(profile.operations).enumerate()
        {
            for digest in [
                &operation.request_sha256,
                &operation.plan_sha256,
                &operation.target_state_sha256,
                &operation.target_grid_sha256,
            ] {
                require_lower_sha256(digest)?;
            }
            let source_must_be_none = index == 0 && operation_index == 0;
            if operation.name != *expected_name
                || operation.capability_id != profile.capability_id
                || operation.added_border_fill_count > 64
                || source_must_be_none
                    != (operation.source_state_sha256.is_none()
                        && operation.source_grid_sha256.is_none())
            {
                return Err("ruling manifest operation differs".into());
            }
            if let (Some(source_state), Some(source_grid)) = (
                operation.source_state_sha256.as_deref(),
                operation.source_grid_sha256.as_deref(),
            ) {
                require_lower_sha256(source_state)?;
                require_lower_sha256(source_grid)?;
                if operation_index > 0
                    && (Some(source_state) != previous_state || Some(source_grid) != previous_grid)
                {
                    return Err("ruling manifest operation chain differs".into());
                }
            }
            previous_state = Some(&operation.target_state_sha256);
            previous_grid = Some(&operation.target_grid_sha256);
        }
        if previous_state != Some(case.target_state_sha256.as_str())
            || previous_grid != Some(case.target_grid_sha256.as_str())
        {
            return Err("ruling manifest final operation differs".into());
        }
    }
    Ok(())
}

fn expected_boundaries(index: usize) -> (&'static [u32], &'static [u32]) {
    match index {
        0 => (&[0, 8_000], &[0, 41_952]),
        1 => (
            &[0, 2_000, 4_000, 8_000],
            &[0, 5_244, 10_488, 15_732, 20_976, 31_464, 41_952],
        ),
        _ => (&[0, 4_000, 8_000], &[0, 10_488, 20_976, 31_464, 41_952]),
    }
}

fn binding_from_manifest(
    value: &BindingManifest,
) -> Result<TableRulingHwpxBinding, Box<dyn Error>> {
    let cells = value
        .cells
        .iter()
        .map(|cell| {
            Ok(TableRulingHwpxCellBinding {
                master_cell_id: LogicalId::parse(&cell.master_cell_id)?,
                payload_block_ids: cell
                    .payload_block_ids
                    .iter()
                    .map(LogicalId::parse)
                    .collect::<Result<Vec<_>, _>>()?,
            })
        })
        .collect::<Result<Vec<_>, Box<dyn Error>>>()?;
    Ok(TableRulingHwpxBinding {
        table_id: LogicalId::parse(&value.table_id)?,
        row_boundaries_hwpunit: value.row_boundaries_hwpunit.clone(),
        column_boundaries_hwpunit: value.column_boundaries_hwpunit.clone(),
        cells,
    })
}

fn require_case_semantics(
    profile: CaseProfile,
    case: &ManifestCase,
    readback: &TableRulingHwpxReadback,
) -> Result<(), Box<dyn Error>> {
    if readback.grid.rows() != profile.rows
        || readback.grid.columns() != profile.columns
        || readback.grid.master_cell_count() != profile.master_cells
        || readback.payload_block_count != profile.payload_blocks
        || readback.formula_count != profile.formulas
        || hex(readback
            .state
            .canonical_sha256(TableRulingLimits::default())?)
            != case.target_state_sha256
        || hex(readback.grid.canonical_sha256()?) != case.target_grid_sha256
    {
        return Err("ruling typed semantic profile differs".into());
    }
    match profile.case_id {
        "table-002-draw-outer" => require_outer_semantics(readback),
        "table-002-draw-topology" => require_draw_topology_semantics(profile, readback),
        "table-002-draw-diagonals-formula" => require_diagonal_semantics(readback),
        "table-003-eraser-structural-merge" => require_structural_merge_semantics(readback),
        "table-003-eraser-transparent-formula" => require_transparent_erase_semantics(readback),
        _ => Err("unsupported ruling case".into()),
    }
}

fn require_outer_semantics(readback: &TableRulingHwpxReadback) -> Result<(), Box<dyn Error>> {
    let perimeter = [
        (TableRulingAxis::Horizontal, 0, 0),
        (TableRulingAxis::Horizontal, 1, 0),
        (TableRulingAxis::Vertical, 0, 0),
        (TableRulingAxis::Vertical, 1, 0),
    ];
    if readback.state.edges().len() != perimeter.len()
        || perimeter
            .iter()
            .any(|&(axis, boundary, offset)| !edge_visible(readback, axis, boundary, offset))
    {
        return Err("outer rectangle ruling differs".into());
    }
    Ok(())
}

fn require_draw_topology_semantics(
    profile: CaseProfile,
    readback: &TableRulingHwpxReadback,
) -> Result<(), Box<dyn Error>> {
    let row_line = line_at(readback, TableRulingAxis::Horizontal, 1, 0)?;
    let styled_line = line_at(readback, TableRulingAxis::Horizontal, 2, 0)?;
    if row_line == styled_line {
        return Err("draw topology style distinction differs".into());
    }
    if (0..profile.columns).any(|offset| {
        line_at(readback, TableRulingAxis::Horizontal, 1, offset)
            .map_or(true, |line| line != row_line)
    }) {
        return Err("draw full-row ruling differs".into());
    }
    if (0..profile.columns).any(|offset| {
        line_at(readback, TableRulingAxis::Horizontal, 2, offset)
            .map_or(true, |line| line != styled_line)
    }) {
        return Err("draw styled existing boundary differs".into());
    }
    if (0..profile.rows).any(|offset| !edge_visible(readback, TableRulingAxis::Vertical, 1, offset))
    {
        return Err("draw full-column ruling differs".into());
    }
    if !edge_visible(readback, TableRulingAxis::Vertical, 3, 2) {
        return Err("draw local cell split ruling is missing".into());
    }
    if edge_visible(readback, TableRulingAxis::Vertical, 3, 0)
        || edge_visible(readback, TableRulingAxis::Vertical, 3, 1)
    {
        return Err("draw local cell split escaped its cell".into());
    }
    Ok(())
}

fn require_diagonal_semantics(readback: &TableRulingHwpxReadback) -> Result<(), Box<dyn Error>> {
    let formula = readback
        .state
        .cells()
        .iter()
        .find(|cell| cell.coordinate() == (CellCoordinate { row: 1, column: 3 }))
        .ok_or("diagonal formula cell is missing")?;
    if formula.formula().is_none()
        || formula.properties().slash_diagonal_sha256.is_none()
        || formula.properties().back_slash_diagonal_sha256.is_none()
    {
        return Err("directional diagonal semantics differ".into());
    }
    Ok(())
}

fn require_structural_merge_semantics(
    readback: &TableRulingHwpxReadback,
) -> Result<(), Box<dyn Error>> {
    let merged = readback
        .grid
        .master_cells()
        .iter()
        .filter(|cell| cell.column == 0 && cell.column_span == 2 && cell.row_span == 1)
        .count();
    if merged != 2 {
        return Err("eraser structural merge spans differ".into());
    }
    if edge_visible(readback, TableRulingAxis::Vertical, 1, 0)
        || edge_visible(readback, TableRulingAxis::Vertical, 1, 1)
    {
        return Err("eraser structural shared edge remains visible".into());
    }
    Ok(())
}

fn require_transparent_erase_semantics(
    readback: &TableRulingHwpxReadback,
) -> Result<(), Box<dyn Error>> {
    let edge = readback
        .state
        .edge(TableRulingAxis::Horizontal, 2, 3)
        .ok_or("transparent edge record is missing")?;
    let formula = readback
        .state
        .cells()
        .iter()
        .find(|cell| cell.coordinate() == (CellCoordinate { row: 1, column: 3 }))
        .ok_or("transparent formula cell is missing")?;
    if edge.line_sha256.is_some()
        || formula.formula().is_none()
        || readback
            .grid
            .master_cells()
            .iter()
            .any(|cell| cell.row_span != 1 || cell.column_span != 1)
    {
        return Err("eraser transparent-line semantics differ".into());
    }
    Ok(())
}

fn require_equivalent_readback(
    target: &TableRulingHwpxReadback,
    oracle: &TableRulingHwpxReadback,
) -> Result<(), Box<dyn Error>> {
    if oracle.profile_id != target.profile_id
        || oracle.grid != target.grid
        || oracle.state != target.state
        || oracle.table_content_sha256 != target.table_content_sha256
        || oracle.style_catalog != target.style_catalog
        || oracle.payload_block_count != target.payload_block_count
        || oracle.formula_count != target.formula_count
    {
        return Err("ruling typed oracle readback differs".into());
    }
    Ok(())
}

fn require_selected_table_exterior_equal(
    profile: CaseProfile,
    target: &[u8],
    oracle: &[u8],
) -> Result<(), Box<dyn Error>> {
    let target_exterior = selected_table_exterior(target, profile.selected_table_ordinal)?;
    let oracle_exterior = selected_table_exterior(oracle, profile.selected_table_ordinal)?;
    let target_exterior = normalize_outer_anchor(profile, target_exterior)?;
    let oracle_exterior = normalize_outer_anchor(profile, oracle_exterior)?;
    if target_exterior != oracle_exterior {
        return Err("ruling section exterior differs beyond admitted normalization".into());
    }
    Ok(())
}

fn selected_table_exterior(section: &[u8], ordinal: usize) -> Result<Vec<u8>, Box<dyn Error>> {
    const MARKER: &[u8] = b"<hwpx-agent-selected-table/>";
    let document = PreservingXmlDocument::parse(section)?;
    let table = document
        .elements()
        .iter()
        .filter(|element| has_name(element, "tbl"))
        .nth(ordinal)
        .ok_or("selected ruling table is missing")?;
    let span = table
        .outer_span()
        .ok_or("selected ruling table span is missing")?;
    let prefix = section
        .get(..span.start())
        .ok_or("selected ruling table prefix is outside section")?;
    let suffix = section
        .get(span.end()..)
        .ok_or("selected ruling table suffix is outside section")?;
    let capacity = prefix
        .len()
        .checked_add(MARKER.len())
        .and_then(|size| size.checked_add(suffix.len()))
        .ok_or("selected ruling table exterior size overflow")?;
    let mut output = Vec::new();
    output.try_reserve_exact(capacity)?;
    output.extend_from_slice(prefix);
    output.extend_from_slice(MARKER);
    output.extend_from_slice(suffix);
    Ok(output)
}

fn normalize_outer_anchor(
    profile: CaseProfile,
    section: Vec<u8>,
) -> Result<Vec<u8>, Box<dyn Error>> {
    const CANONICAL: &[u8] = concat!(
        r#"<hp:p id="700" paraPrIDRef="0" styleIDRef="0">"#,
        r#"<hp:run charPrIDRef="0"><hwpx-agent-selected-table/>"#,
    )
    .as_bytes();
    const HANCOM_2020: &[u8] = concat!(
        r#"<hp:p id="700" paraPrIDRef="0" styleIDRef="0" "#,
        r#"pageBreak="0" columnBreak="0" merged="0">"#,
        r#"<hp:run charPrIDRef="0"><hwpx-agent-selected-table/>"#,
    )
    .as_bytes();
    if profile.case_id != "table-002-draw-outer" {
        return Ok(section);
    }
    let canonical_count = count_bytes(&section, CANONICAL);
    let hancom_count = count_bytes(&section, HANCOM_2020);
    if canonical_count == 1 && hancom_count == 0 {
        return Ok(section);
    }
    if canonical_count != 0 || hancom_count != 1 {
        return Err("outer ruling anchor normalization shape differs".into());
    }
    let start = section
        .windows(HANCOM_2020.len())
        .position(|window| window == HANCOM_2020)
        .ok_or("outer ruling anchor normalization is missing")?;
    let capacity = section
        .len()
        .checked_sub(HANCOM_2020.len())
        .and_then(|size| size.checked_add(CANONICAL.len()))
        .ok_or("outer ruling anchor normalization size overflow")?;
    let mut output = Vec::new();
    output.try_reserve_exact(capacity)?;
    output.extend_from_slice(&section[..start]);
    output.extend_from_slice(CANONICAL);
    output.extend_from_slice(&section[start + HANCOM_2020.len()..]);
    Ok(output)
}

fn count_bytes(source: &[u8], needle: &[u8]) -> usize {
    if needle.is_empty() || needle.len() > source.len() {
        return 0;
    }
    source
        .windows(needle.len())
        .filter(|window| *window == needle)
        .count()
}

fn edge_visible(
    readback: &TableRulingHwpxReadback,
    axis: TableRulingAxis,
    boundary: u32,
    offset: u32,
) -> bool {
    readback
        .state
        .edge(axis, boundary, offset)
        .is_some_and(|edge| edge.line_sha256.is_some())
}

fn line_at(
    readback: &TableRulingHwpxReadback,
    axis: TableRulingAxis,
    boundary: u32,
    offset: u32,
) -> Result<&str, Box<dyn Error>> {
    readback
        .state
        .edge(axis, boundary, offset)
        .and_then(|edge| edge.line_sha256.as_deref())
        .ok_or_else(|| "visible ruling edge is missing".into())
}

fn read_ruling(
    header: &[u8],
    section: &[u8],
    ordinal: usize,
    binding: &TableRulingHwpxBinding,
) -> Result<TableRulingHwpxReadback, Box<dyn Error>> {
    Ok(TableRulingHwpxReader::read_existing(
        header,
        section,
        ordinal,
        binding,
        TableRulingHwpxLimits::default(),
    )?)
}

fn read_package(bytes: &[u8]) -> Result<PackageParts, Box<dyn Error>> {
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    let _index = IdIndex::build(
        &mut reader,
        &graph,
        IdRuleProfile::current_hancom_2020_formula_v3(),
        IdIndexLimits::default(),
    )?;
    if graph.parts.len() != reader.entries().len() {
        return Err("ruling package graph cardinality differs".into());
    }
    Ok(PackageParts {
        part_count: graph.parts.len(),
        header: read_part(&mut reader, "Contents/header.xml")?,
        section: read_part(&mut reader, "Contents/section0.xml")?,
        preview: read_part(&mut reader, "Preview/PrvText.txt")?,
    })
}

fn read_part<R: std::io::Read + std::io::Seek>(
    reader: &mut BoundedZipReader<R>,
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

fn strip_renderer_caches(
    section: &[u8],
) -> Result<(Vec<u8>, RendererCacheEvidence), Box<dyn Error>> {
    let document = PreservingXmlDocument::parse(section)?;
    let arrays: Vec<_> = document
        .elements()
        .iter()
        .enumerate()
        .filter(|(_, element)| has_name(element, "linesegarray"))
        .map(|(index, _)| index)
        .collect();
    if arrays.len() > MAX_RENDERER_CACHE_ARRAYS {
        return Err("renderer cache array limit exceeded".into());
    }
    let mut spans = Vec::new();
    let mut digest = Sha256::new();
    digest.update(b"hwpx-agent.p06-09-table-ruling-renderer-cache/v1\0");
    for index in arrays.iter().copied() {
        let array = document
            .elements()
            .get(index)
            .ok_or("renderer cache array is missing")?;
        if !array.attributes().is_empty()
            || array
                .parent()
                .and_then(|parent| document.elements().get(parent))
                .is_none_or(|parent| !has_name(parent, "p"))
        {
            return Err("renderer cache array shape differs".into());
        }
        let mut child = array.first_child();
        let mut line_count = 0usize;
        while let Some(child_index) = child {
            let line = document
                .elements()
                .get(child_index)
                .ok_or("renderer cache line is missing")?;
            validate_renderer_line(section, line)?;
            line_count += 1;
            child = line.next_sibling();
        }
        if line_count == 0 {
            return Err("renderer cache array is empty".into());
        }
        let span = array.outer_span().ok_or("renderer cache span is missing")?;
        digest.update(Sha256::digest(
            section
                .get(span.start()..span.end())
                .ok_or("renderer cache span is outside section")?,
        ));
        spans.push(span);
    }
    let stripped = strip_spans(section, &mut spans)?;
    Ok((
        stripped,
        RendererCacheEvidence {
            count: arrays.len(),
            sha256: digest.finalize().into(),
        },
    ))
}

fn validate_renderer_line(source: &[u8], line: &XmlElementToken) -> Result<(), Box<dyn Error>> {
    const ATTRIBUTES: [&str; 9] = [
        "textpos",
        "vertpos",
        "vertsize",
        "textheight",
        "baseline",
        "spacing",
        "horzpos",
        "horzsize",
        "flags",
    ];
    if !has_name(line, "lineseg") || !line.is_empty() || line.attributes().len() != ATTRIBUTES.len()
    {
        return Err("renderer cache line shape differs".into());
    }
    for name in ATTRIBUTES {
        let value = exact_attribute(source, line, name)?;
        let _: u32 = value.parse()?;
    }
    Ok(())
}

fn strip_spans(section: &[u8], spans: &mut [XmlByteSpan]) -> Result<Vec<u8>, Box<dyn Error>> {
    spans.sort_by_key(|span| span.start());
    let removed = spans.iter().try_fold(0usize, |total, span| {
        total
            .checked_add(span.end().saturating_sub(span.start()))
            .ok_or("renderer cache size overflow")
    })?;
    let mut output = Vec::new();
    output.try_reserve_exact(
        section
            .len()
            .checked_sub(removed)
            .ok_or("renderer cache size underflow")?,
    )?;
    let mut cursor = 0usize;
    for span in spans {
        if span.start() < cursor || span.end() > section.len() {
            return Err("renderer cache spans overlap".into());
        }
        output.extend_from_slice(&section[cursor..span.start()]);
        cursor = span.end();
    }
    output.extend_from_slice(&section[cursor..]);
    Ok(output)
}

fn count_elements(source: &[u8], local_name: &str) -> Result<usize, Box<dyn Error>> {
    let document = PreservingXmlDocument::parse(source)?;
    Ok(document
        .elements()
        .iter()
        .filter(|element| has_name(element, local_name))
        .count())
}

fn count_formula_fields(source: &[u8]) -> Result<usize, Box<dyn Error>> {
    let document = PreservingXmlDocument::parse(source)?;
    let mut count = 0usize;
    for element in document
        .elements()
        .iter()
        .filter(|element| has_name(element, "fieldBegin"))
    {
        if exact_attribute(source, element, "type")? == "FORMULA" {
            count = count.checked_add(1).ok_or("formula count overflow")?;
        }
    }
    Ok(count)
}

fn exact_attribute<'a>(
    source: &'a [u8],
    element: &XmlElementToken,
    name: &str,
) -> Result<&'a str, Box<dyn Error>> {
    let mut attributes = element.attributes().iter().filter(|attribute| {
        !attribute.is_namespace_declaration()
            && attribute.name().namespace().is_none()
            && attribute.name().local_name() == name
    });
    let attribute = attributes.next().ok_or("required attribute is missing")?;
    if attributes.next().is_some() {
        return Err("required attribute is duplicated".into());
    }
    let span = attribute.value_span();
    Ok(std::str::from_utf8(
        source
            .get(span.start()..span.end())
            .ok_or("attribute span is outside source")?,
    )?)
}

fn has_name(element: &XmlElementToken, local_name: &str) -> bool {
    element.name().namespace() == Some(HANCOM_2020_PARAGRAPH_NAMESPACE)
        && element.name().local_name() == local_name
}

fn case_profile(case_id: &str) -> Result<CaseProfile, Box<dyn Error>> {
    CASES
        .into_iter()
        .find(|profile| profile.case_id == case_id)
        .ok_or_else(|| "unsupported ruling case ID".into())
}

fn path_argument(
    values: &mut impl Iterator<Item = std::ffi::OsString>,
    label: &str,
) -> Result<PathBuf, Box<dyn Error>> {
    values
        .next()
        .map(PathBuf::from)
        .ok_or_else(|| format!("missing {label}").into())
}

fn string_argument(
    values: &mut impl Iterator<Item = std::ffi::OsString>,
    label: &str,
) -> Result<String, Box<dyn Error>> {
    values
        .next()
        .ok_or_else(|| format!("missing {label}"))?
        .into_string()
        .map_err(|_| format!("{label} is not Unicode").into())
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
    require_lower_sha256(expected)?;
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

fn hex(value: impl AsRef<[u8]>) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let bytes = value.as_ref();
    let mut output = String::with_capacity(bytes.len() * 2);
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
    fn exact_case_set_and_ruling_semantics_are_complete() {
        assert_eq!(CASES.len(), 5);
        assert_eq!(
            CASES
                .iter()
                .map(|case| case.operations.len())
                .sum::<usize>(),
            9
        );
        assert_eq!(
            CASES
                .iter()
                .filter(|case| case.feature_id == "TABLE-002")
                .count(),
            3
        );
        assert_eq!(
            CASES
                .iter()
                .filter(|case| case.feature_id == "TABLE-003")
                .count(),
            2
        );
    }

    #[test]
    fn renderer_cache_stripping_is_exact_and_bounded() {
        let source = concat!(
            r#"<hp:sec xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">"#,
            r#"<hp:p><hp:linesegarray><hp:lineseg textpos="0" vertpos="0" "#,
            r#"vertsize="1000" textheight="1000" baseline="850" spacing="600" "#,
            r#"horzpos="0" horzsize="100" flags="393216"/></hp:linesegarray>"#,
            r#"<hp:run/></hp:p></hp:sec>"#,
        );
        let expected = concat!(
            r#"<hp:sec xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">"#,
            r#"<hp:p><hp:run/></hp:p></hp:sec>"#,
        );
        let (stripped, evidence) = strip_renderer_caches(source.as_bytes()).unwrap();
        assert_eq!(stripped, expected.as_bytes());
        assert_eq!(evidence.count, 1);
    }

    #[test]
    fn selected_table_exterior_admits_only_exact_outer_anchor_defaults() {
        let target = concat!(
            r#"<hs:sec xmlns:hs="urn:s" xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">"#,
            r#"<hp:p id="1"><hp:run><hp:t>KEEP</hp:t></hp:run></hp:p>"#,
            r#"<hp:tbl id="1"/>"#,
            r#"<hp:p id="700" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0">"#,
            r#"<hp:tbl id="700"/><hp:t/></hp:run></hp:p></hs:sec>"#,
        );
        let oracle = concat!(
            r#"<hs:sec xmlns:hs="urn:s" xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">"#,
            r#"<hp:p id="1"><hp:run><hp:t>KEEP</hp:t></hp:run></hp:p>"#,
            r#"<hp:tbl id="1"/>"#,
            r#"<hp:p id="700" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0"><hp:run charPrIDRef="0">"#,
            r#"<hp:tbl id="700" changed="inside-selected-table"/><hp:t/></hp:run></hp:p></hs:sec>"#,
        );
        require_selected_table_exterior_equal(CASES[0], target.as_bytes(), oracle.as_bytes())
            .unwrap();

        let changed = oracle.replace(">KEEP<", ">CHANGED<");
        assert!(
            require_selected_table_exterior_equal(CASES[0], target.as_bytes(), changed.as_bytes(),)
                .is_err()
        );
    }
}
