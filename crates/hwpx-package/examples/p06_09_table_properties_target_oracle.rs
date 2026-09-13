use std::collections::BTreeMap;
use std::env;
use std::error::Error;
use std::fs;
use std::io::Cursor;
use std::path::{Path, PathBuf};

use domain_ir::{
    CellCoordinate, FormulaLimits, LogicalId, TableDiagonalApplyMode, TableDiagonalValue,
    TablePropertiesLimits, table_diagonal_identity_sha256,
};
use hwpx_package::{
    BoundedZipReader, CellMargins, CellProtection, CellTextDirection, CellVerticalAlignment,
    HANCOM_2020_PARAGRAPH_NAMESPACE, HorizontalAlignment, PackageGraph, PackageGraphLimits,
    PackageLimits, PreservingXmlDocument, TableFormulaHwpxLimits, TableFormulaHwpxReader,
    TablePropertiesHwpxBinding, TablePropertiesHwpxCellValue, TablePropertiesHwpxDiagonalBinding,
    TablePropertiesHwpxLimits, TablePropertiesHwpxReader, TableRulingHwpxBinding,
    TableRulingHwpxCellBinding, XmlByteSpan, XmlElementToken,
};
use serde::Deserialize;
use sha2::{Digest as _, Sha256};

const MAX_FILE_BYTES: u64 = 8 * 1024 * 1024;
const MAX_MANIFEST_BYTES: u64 = 256 * 1024;
const EXPECTED_MANIFEST_SHA256: &str =
    "2eee896adddc9435ea04da26af35040fe92417cb0d35f8a304b146f083e41a0c";
const EXPECTED_ANCESTOR_SHA256: &str =
    "6514a69b8c8c9d320bc19a032b16f2b71d59a38f164c690bc9e3d320a93320e5";
const EXPECTED_TARGET_SHA256: &str =
    "940804c73f6cf83b5f1b37821dd18a731f6ad4927c95fb615d68fa4f48829924";
const EXPECTED_BATCH_MANIFEST_SHA256: &str =
    "05387606ca02cd9e06d44556d8ea50aaf5d80d238dbdc41f68b9c9551026bab0";
const EXPECTED_BATCH_TARGET_SHA256: [&str; 3] = [
    "5ec86c45cbb1df724827b5126220643bf37a647d58307bbb8f4840bfe89acc30",
    "c83d13e508fd78cbaa3e65a01ea2d5b7b668a4dce87188c972484c2e8223b0d8",
    "26ab01ea8ba2b02430afbe2173af52bf106dbb251b23ab3a320a3d78361f36ea",
];
const EXPECTED_TARGET_PREVIEW: &[u8] = b"<2><3><4><5><17><10><25><52>\r\n\r\n";
const EXPECTED_ORACLE_PREVIEW: &[u8] = b"<2><3><4><5>\r\n<17><10><25><52>\r\n\r\n";
const IMMUTABLE_PARTS: [&str; 5] = [
    "mimetype",
    "version.xml",
    "META-INF/container.rdf",
    "META-INF/container.xml",
    "META-INF/manifest.xml",
];

struct Arguments {
    manifest: PathBuf,
    expected_manifest_sha256: String,
    oracle: PathBuf,
    expected_oracle_sha256: String,
}

impl Arguments {
    fn parse() -> Result<Self, Box<dyn Error>> {
        let mut values = env::args_os();
        let _program = values.next();
        let result = Self {
            manifest: path_argument(&mut values, "fixture manifest")?,
            expected_manifest_sha256: string_argument(&mut values, "manifest SHA-256")?,
            oracle: path_argument(&mut values, "oracle HWPX")?,
            expected_oracle_sha256: string_argument(&mut values, "oracle SHA-256")?,
        };
        if values.next().is_some() {
            return Err("too many arguments".into());
        }
        Ok(result)
    }
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Manifest {
    schema_version: String,
    source_ancestor_sha256: String,
    prepared_source_section_sha256: String,
    case: ManifestCase,
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
    selected_cell: CoordinateManifest,
    target_header_sha256: String,
    target_section_sha256: String,
    target_state_sha256: String,
    target_grid_sha256: String,
    target_table_value_sha256: String,
    target_cell_value_sha256: String,
    operations: Vec<OperationManifest>,
    rows: u32,
    columns: u32,
    master_cells: usize,
    payload_blocks: usize,
    formula_count: usize,
    page_split: String,
    table_lock: bool,
    table_no_adjust: bool,
    changed_master_cells: usize,
    preserved_formula_count: usize,
    binding: BindingManifest,
}

#[derive(Deserialize, Eq, PartialEq)]
#[serde(deny_unknown_fields)]
struct CoordinateManifest {
    row: u32,
    column: u32,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct OperationManifest {
    name: String,
    request_sha256: String,
    plan_sha256: String,
    source_state_sha256: String,
    target_state_sha256: String,
    table_properties_changed: bool,
    changed_master_cells: usize,
    preserved_formula_count: usize,
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
struct BatchManifest {
    schema_version: String,
    source_ancestor_sha256: String,
    prepared_source_section_sha256: String,
    cases: Vec<BatchManifestCase>,
    actual_hangul_2020: bool,
    render: String,
    automation: String,
    differential: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct BatchManifestCase {
    case_id: String,
    feature_id: String,
    capability_id: String,
    file: String,
    sha256: String,
    selected_table_ordinal: usize,
    selected_slots: Vec<CoordinateManifest>,
    operation_kind: String,
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
    page_split: String,
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
    binding: BatchBindingManifest,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct BatchBindingManifest {
    table: BindingManifest,
    diagonals: Vec<BatchDiagonalBindingManifest>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct BatchDiagonalBindingManifest {
    master_cell_id: String,
    apply_mode: TableDiagonalApplyMode,
    region: Option<serde_json::Value>,
    value: TableDiagonalValue,
}

struct PackageInspection {
    parts: BTreeMap<String, Vec<u8>>,
    header: Vec<u8>,
    section: Vec<u8>,
    preview: Vec<u8>,
}

fn main() -> Result<(), Box<dyn Error>> {
    run(&Arguments::parse()?)
}

fn run(arguments: &Arguments) -> Result<(), Box<dyn Error>> {
    require_lower_sha256(&arguments.expected_manifest_sha256)?;
    require_lower_sha256(&arguments.expected_oracle_sha256)?;
    if arguments.expected_manifest_sha256 != EXPECTED_MANIFEST_SHA256 {
        return Err("exact properties fixture manifest identity differs".into());
    }
    let manifest_bytes = read_bounded_file(&arguments.manifest, MAX_MANIFEST_BYTES)?;
    require_digest(
        &manifest_bytes,
        &arguments.expected_manifest_sha256,
        "manifest",
    )?;
    let manifest: Manifest = serde_json::from_slice(&manifest_bytes)?;
    validate_manifest(&manifest)?;
    let target_path = arguments
        .manifest
        .parent()
        .ok_or("fixture manifest has no parent")?
        .join(&manifest.case.file);
    if target_path == arguments.oracle {
        return Err("target and oracle paths must differ".into());
    }
    let target_bytes = read_bounded_file(&target_path, MAX_FILE_BYTES)?;
    let oracle_bytes = read_bounded_file(&arguments.oracle, MAX_FILE_BYTES)?;
    require_digest(&target_bytes, EXPECTED_TARGET_SHA256, "target")?;
    require_digest(&oracle_bytes, &arguments.expected_oracle_sha256, "oracle")?;

    let target_package = inspect_package(&target_bytes)?;
    let oracle_package = inspect_package(&oracle_bytes)?;
    require_package_boundary(&target_package, &oracle_package)?;
    let binding = binding_from_manifest(&manifest.case.binding)?;
    let limits = TablePropertiesHwpxLimits::default();
    let target = TablePropertiesHwpxReader::read_existing(
        &target_package.header,
        &target_package.section,
        manifest.case.selected_table_ordinal,
        &binding,
        limits,
    )?;
    let oracle = TablePropertiesHwpxReader::read_existing(
        &oracle_package.header,
        &oracle_package.section,
        manifest.case.selected_table_ordinal,
        &binding,
        limits,
    )?;
    require_target_manifest(&manifest.case, &target, &target_package)?;
    require_typed_oracle(&target, &oracle)?;
    require_formula_oracle(&target_package.section, &oracle_package.section)?;
    let (stripped, cache_sha256, cache_count) = strip_renderer_caches(&oracle_package.section)?;
    if cache_count != 10 || stripped != target_package.section {
        return Err("oracle section differs outside exact renderer caches".into());
    }

    require_digest(
        &read_bounded_file(&arguments.manifest, MAX_MANIFEST_BYTES)?,
        EXPECTED_MANIFEST_SHA256,
        "manifest recheck",
    )?;
    require_digest(
        &read_bounded_file(&target_path, MAX_FILE_BYTES)?,
        EXPECTED_TARGET_SHA256,
        "target recheck",
    )?;
    println!(
        concat!(
            "schema=hwpx-agent.p06-09-table-properties-target-oracle/v1 state=pass ",
            "target_sha256={} oracle_sha256={} state_sha256={} grid_sha256={} ",
            "table_value_sha256={} cell_value_sha256={} formula_count=1 ",
            "renderer_cache_count={} renderer_cache_sha256={} ",
            "section_equal_after_renderer_cache_strip=true"
        ),
        EXPECTED_TARGET_SHA256,
        arguments.expected_oracle_sha256,
        manifest.case.target_state_sha256,
        manifest.case.target_grid_sha256,
        manifest.case.target_table_value_sha256,
        manifest.case.target_cell_value_sha256,
        cache_count,
        hex(cache_sha256),
    );
    Ok(())
}

/// Verifies TABLE-008, TABLE-009, and TABLE-047 against three exact Hangul 2020
/// save/reopen outputs in one fail-closed pass.
///
/// # Errors
///
/// Rejects identity, path, size, package, typed semantic, formula, renderer-cache, or input
/// recheck drift for any of the three cases.
pub fn run_table_008_009_047(
    manifest_path: &Path,
    expected_manifest_sha256: &str,
    oracle_paths: [&Path; 3],
    expected_oracle_sha256: [&str; 3],
) -> Result<(), Box<dyn Error>> {
    require_lower_sha256(expected_manifest_sha256)?;
    if expected_manifest_sha256 != EXPECTED_BATCH_MANIFEST_SHA256 {
        return Err("exact border/diagonal fixture manifest identity differs".into());
    }
    for digest in expected_oracle_sha256 {
        require_lower_sha256(digest)?;
    }
    if oracle_paths[0] == oracle_paths[1]
        || oracle_paths[0] == oracle_paths[2]
        || oracle_paths[1] == oracle_paths[2]
    {
        return Err("oracle paths must be distinct".into());
    }

    let manifest_bytes = read_bounded_file(manifest_path, MAX_MANIFEST_BYTES)?;
    require_digest(&manifest_bytes, expected_manifest_sha256, "batch manifest")?;
    let manifest: BatchManifest = serde_json::from_slice(&manifest_bytes)?;
    validate_batch_manifest(&manifest)?;
    let parent = manifest_path
        .parent()
        .ok_or("batch fixture manifest has no parent")?;
    let mut cache_digests = Vec::with_capacity(3);
    for (index, ((case, oracle_path), expected_oracle)) in manifest
        .cases
        .iter()
        .zip(oracle_paths)
        .zip(expected_oracle_sha256)
        .enumerate()
    {
        let target_path = parent.join(&case.file);
        if target_path == oracle_path {
            return Err("target and oracle paths must differ".into());
        }
        let target_bytes = read_bounded_file(&target_path, MAX_FILE_BYTES)?;
        let oracle_bytes = read_bounded_file(oracle_path, MAX_FILE_BYTES)?;
        require_digest(
            &target_bytes,
            EXPECTED_BATCH_TARGET_SHA256[index],
            "batch target",
        )?;
        require_digest(&oracle_bytes, expected_oracle, "batch oracle")?;

        let target_package = inspect_package(&target_bytes)?;
        let oracle_package = inspect_package(&oracle_bytes)?;
        require_package_boundary(&target_package, &oracle_package)?;
        let binding = binding_from_batch_manifest(&case.binding)?;
        let limits = TablePropertiesHwpxLimits::default();
        let target = TablePropertiesHwpxReader::read_existing(
            &target_package.header,
            &target_package.section,
            case.selected_table_ordinal,
            &binding,
            limits,
        )?;
        let oracle = TablePropertiesHwpxReader::read_existing(
            &oracle_package.header,
            &oracle_package.section,
            case.selected_table_ordinal,
            &binding,
            limits,
        )?;
        require_batch_target_manifest(case, &target, &target_package)?;
        require_typed_oracle(&target, &oracle)?;
        require_formula_oracle(&target_package.section, &oracle_package.section)?;
        let (stripped, cache_sha256, cache_count) =
            strip_standard_renderer_caches(&oracle_package.section)?;
        if cache_count != 10 || stripped != target_package.section {
            return Err(format!(
                "{} oracle section differs outside exact renderer caches",
                case.feature_id
            )
            .into());
        }
        cache_digests.push(hex(cache_sha256));

        require_digest(
            &read_bounded_file(&target_path, MAX_FILE_BYTES)?,
            EXPECTED_BATCH_TARGET_SHA256[index],
            "batch target recheck",
        )?;
        require_digest(
            &read_bounded_file(oracle_path, MAX_FILE_BYTES)?,
            expected_oracle,
            "batch oracle recheck",
        )?;
    }
    require_digest(
        &read_bounded_file(manifest_path, MAX_MANIFEST_BYTES)?,
        EXPECTED_BATCH_MANIFEST_SHA256,
        "batch manifest recheck",
    )?;
    println!(
        concat!(
            "schema=hwpx-agent.p06-09-table-borders-diagonal-target-oracle/v1 state=pass ",
            "case_count=3 features=TABLE-008,TABLE-009,TABLE-047 formula_count_each=1 ",
            "renderer_cache_count_each=10 renderer_cache_sha256={},{},{} ",
            "section_equal_after_renderer_cache_strip=true"
        ),
        cache_digests[0], cache_digests[1], cache_digests[2],
    );
    Ok(())
}

fn validate_manifest(manifest: &Manifest) -> Result<(), Box<dyn Error>> {
    let case = &manifest.case;
    if manifest.schema_version != "hwpx-agent.p06-09-table-properties-target-fixture/v1"
        || manifest.source_ancestor_sha256 != EXPECTED_ANCESTOR_SHA256
        || manifest.prepared_source_section_sha256
            != "461aa5bfe8b451212b1b2bc522e504128c451df7fe27d763793d37e39aa60a83"
        || case.case_id != "table-007-properties-formula-2x4"
        || case.feature_id != "TABLE-007"
        || case.capability_id != "table.properties"
        || case.file != "table-007-properties-formula-2x4.hwpx"
        || case.sha256 != EXPECTED_TARGET_SHA256
        || case.selected_table_ordinal != 0
        || case.selected_cell != (CoordinateManifest { row: 1, column: 0 })
        || case.rows != 2
        || case.columns != 4
        || case.master_cells != 8
        || case.payload_blocks != 7
        || case.formula_count != 1
        || case.page_split != "cell"
        || !case.table_lock
        || !case.table_no_adjust
        || case.changed_master_cells != 1
        || case.preserved_formula_count != 1
        || manifest.actual_hangul_2020
        || manifest.render != "not_run"
        || manifest.automation != "not_run"
        || manifest.differential != "not_run"
    {
        return Err("properties fixture manifest semantics differ".into());
    }
    require_lower_sha256(&case.target_header_sha256)?;
    require_lower_sha256(&case.target_section_sha256)?;
    require_lower_sha256(&case.target_state_sha256)?;
    require_lower_sha256(&case.target_grid_sha256)?;
    require_lower_sha256(&case.target_table_value_sha256)?;
    require_lower_sha256(&case.target_cell_value_sha256)?;
    if case.operations.len() != 2
        || case.operations[0].name != "set_table_properties"
        || !case.operations[0].table_properties_changed
        || case.operations[0].changed_master_cells != 0
        || case.operations[1].name != "set_cell_properties"
        || case.operations[1].table_properties_changed
        || case.operations[1].changed_master_cells != 1
        || case
            .operations
            .iter()
            .any(|operation| operation.preserved_formula_count != 1)
        || case.operations[0].target_state_sha256 != case.operations[1].source_state_sha256
        || case.operations[1].target_state_sha256 != case.target_state_sha256
    {
        return Err("properties operation chain differs".into());
    }
    for operation in &case.operations {
        for digest in [
            &operation.request_sha256,
            &operation.plan_sha256,
            &operation.source_state_sha256,
            &operation.target_state_sha256,
        ] {
            require_lower_sha256(digest)?;
        }
    }
    Ok(())
}

#[allow(clippy::too_many_lines)]
fn validate_batch_manifest(manifest: &BatchManifest) -> Result<(), Box<dyn Error>> {
    if manifest.schema_version != "hwpx-agent.p06-09-table-borders-diagonal-target-fixture/v1"
        || manifest.source_ancestor_sha256 != EXPECTED_ANCESTOR_SHA256
        || manifest.prepared_source_section_sha256
            != "461aa5bfe8b451212b1b2bc522e504128c451df7fe27d763793d37e39aa60a83"
        || manifest.cases.len() != 3
        || manifest.actual_hangul_2020
        || manifest.render != "not_run"
        || manifest.automation != "not_run"
        || manifest.differential != "not_run"
    {
        return Err("border/diagonal fixture manifest boundary differs".into());
    }
    let expected_identity = [
        (
            "table-008-cell-border-each-formula-2x4",
            "TABLE-008",
            "table.cell_border_each",
            "table-008-cell-border-each-formula-2x4.hwpx",
            "border_each",
        ),
        (
            "table-009-cell-border-unified-formula-2x4",
            "TABLE-009",
            "table.cell_border_unified",
            "table-009-cell-border-unified-formula-2x4.hwpx",
            "border_unified",
        ),
        (
            "table-047-cell-diagonal-formula-2x4",
            "TABLE-047",
            "table.cell_diagonal",
            "table-047-cell-diagonal-formula-2x4.hwpx",
            "cell_diagonal_each",
        ),
    ];
    let expected_counts = [
        (4, 16, 4, 16, 0, 0, 0, 0, 4, 1),
        (4, 16, 4, 0, 8, 8, 0, 0, 4, 4),
        (1, 0, 0, 0, 0, 0, 1, 1, 7, 1),
    ];
    let rectangle = [
        CoordinateManifest { row: 0, column: 0 },
        CoordinateManifest { row: 0, column: 1 },
        CoordinateManifest { row: 1, column: 0 },
        CoordinateManifest { row: 1, column: 1 },
    ];
    let expected_lines: [&[&str]; 3] = [
        &[
            "d551cd593156bed60d35d59631c7c9c22428af9f7d71d83035fe3089c9f54115",
            "beec11775d2aa8d8402236e7fcc75ad78a8bf76ac71cc0614a71d5fcded6ed23",
            "453b8ca0d491d8204e8aadecc7bfc249ecb994f0c05295291796b2c71f4f35e4",
            "e815a2e57f0dae1923e699389b1f54973d11c280d7fc43b48579589b562d8caa",
        ],
        &[
            "0fb475031033d3f5a28fab4289ec0e055cb00381a6c1123157949d2dca80d7e5",
            "beec11775d2aa8d8402236e7fcc75ad78a8bf76ac71cc0614a71d5fcded6ed23",
            "bfaec0b29be4f4be1b971007e1e8e17fe7ed1a7fd843fb0334e77f9daa6a4e54",
            "e815a2e57f0dae1923e699389b1f54973d11c280d7fc43b48579589b562d8caa",
            "e65645a80c964dce64a1d2e7bdad1ae4c15041ebdab93cc1ad6686768b6ecbe9",
            "356089275f36ff8e7cc34f82a2aa5163e4a12d35e03b650e4735b95f015769dc",
        ],
        &["e9e90807f21d8523242832479d0b063eb02f3a5b44bc8c410295bdb318834979"],
    ];
    let expected_background = [
        Some("9f35d88cedf0906326790b76d64d755bdcf771f4687eb9aedfbf4469ce9ea94f"),
        Some("03ac15c161e37cc9d8ea2ab3480f38bf689b727406666319d9a6c4960faaba6f"),
        None,
    ];
    for (index, case) in manifest.cases.iter().enumerate() {
        let identity = expected_identity[index];
        let counts = expected_counts[index];
        let expected_slots: &[CoordinateManifest] = if index == 2 {
            &[CoordinateManifest { row: 0, column: 2 }]
        } else {
            &rectangle
        };
        if case.case_id != identity.0
            || case.feature_id != identity.1
            || case.capability_id != identity.2
            || case.file != identity.3
            || case.operation_kind != identity.4
            || case.sha256 != EXPECTED_BATCH_TARGET_SHA256[index]
            || case.selected_table_ordinal != 0
            || case.selected_slots != expected_slots
            || case.rows != 2
            || case.columns != 4
            || case.master_cells != 8
            || case.payload_blocks != 7
            || case.formula_count != 1
            || case.page_split != "cell"
            || (
                case.changed_master_cells,
                case.border_side_change_count,
                case.background_change_count,
                case.per_cell_edge_assignment_count,
                case.outer_edge_assignment_count,
                case.inner_edge_assignment_count,
                case.diagonal_change_count,
                case.diagonal_assignment_count,
                case.unselected_master_cell_preserved_count,
                case.added_border_fill_count,
            ) != counts
            || case.preserved_formula_count != 1
            || case
                .line_sha256
                .iter()
                .map(String::as_str)
                .collect::<Vec<_>>()
                != expected_lines[index]
            || case.background_sha256.as_deref() != expected_background[index]
        {
            return Err(format!("{} fixture manifest semantics differ", case.feature_id).into());
        }
        for digest in [
            &case.sha256,
            &case.target_header_sha256,
            &case.target_section_sha256,
            &case.source_state_sha256,
            &case.target_state_sha256,
            &case.target_grid_sha256,
            &case.request_sha256,
            &case.plan_sha256,
        ] {
            require_lower_sha256(digest)?;
        }
        for digest in &case.line_sha256 {
            require_lower_sha256(digest)?;
        }
        if let Some(digest) = &case.background_sha256 {
            require_lower_sha256(digest)?;
        }
        require_batch_binding_shape(case, index)?;
    }
    Ok(())
}

fn require_batch_binding_shape(
    case: &BatchManifestCase,
    index: usize,
) -> Result<(), Box<dyn Error>> {
    let table = &case.binding.table;
    if table.table_id != "properties-target-table"
        || table.row_boundaries_hwpunit != [0, 4_000, 8_000]
        || table.column_boundaries_hwpunit != [0, 10_488, 20_976, 31_464, 41_952]
        || table.cells.len() != 8
    {
        return Err("border/diagonal binding table shape differs".into());
    }
    for (cell_index, cell) in table.cells.iter().enumerate() {
        let expected_cell_id = format!("properties-target-cell-{cell_index}");
        let expected_payloads = if cell_index < 7 {
            vec![format!("properties-target-payload-{cell_index}")]
        } else {
            Vec::new()
        };
        if cell.master_cell_id != expected_cell_id || cell.payload_block_ids != expected_payloads {
            return Err("border/diagonal binding cell shape differs".into());
        }
    }
    if index < 2 {
        if case.diagonal.is_some()
            || case.diagonal_apply_mode.is_some()
            || !case.binding.diagonals.is_empty()
        {
            return Err("border case unexpectedly carries a diagonal binding".into());
        }
        return Ok(());
    }
    let diagonal = case
        .diagonal
        .as_ref()
        .ok_or("diagonal case value is missing")?;
    let binding = case
        .binding
        .diagonals
        .first()
        .filter(|_| case.binding.diagonals.len() == 1)
        .ok_or("diagonal binding cardinality differs")?;
    if case.diagonal_apply_mode != Some(TableDiagonalApplyMode::EachCell)
        || binding.master_cell_id != "properties-target-cell-2"
        || binding.apply_mode != TableDiagonalApplyMode::EachCell
        || binding.region.is_some()
        || binding.value != *diagonal
        || diagonal.slash.slash_type != domain_ir::TableDiagonalSlashType::Center
        || diagonal.back_slash.slash_type != domain_ir::TableDiagonalSlashType::Center
        || diagonal.slash.crooked
        || diagonal.slash.is_counter
        || diagonal.back_slash.crooked
        || diagonal.back_slash.is_counter
        || diagonal.center_line != domain_ir::TableDiagonalCenterLine::None
        || diagonal.line_sha256 != case.line_sha256[0]
    {
        return Err("diagonal manifest binding differs".into());
    }
    Ok(())
}

fn inspect_package(bytes: &[u8]) -> Result<PackageInspection, Box<dyn Error>> {
    let mut archive = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut archive, PackageGraphLimits::default())?;
    if graph.parts.len() != archive.entries().len() || graph.parts.len() != 11 {
        return Err("package graph cardinality differs".into());
    }
    let entries = archive.entries().to_vec();
    let mut parts = BTreeMap::new();
    for entry in entries {
        let path = entry.path.as_str().to_owned();
        if parts
            .insert(path, archive.read_entry(entry.index)?)
            .is_some()
        {
            return Err("package part is duplicated".into());
        }
    }
    let header = parts
        .get("Contents/header.xml")
        .ok_or("header part is missing")?
        .clone();
    let section = parts
        .get("Contents/section0.xml")
        .ok_or("section part is missing")?
        .clone();
    let preview = parts
        .get("Preview/PrvText.txt")
        .ok_or("preview part is missing")?
        .clone();
    Ok(PackageInspection {
        parts,
        header,
        section,
        preview,
    })
}

fn require_package_boundary(
    target: &PackageInspection,
    oracle: &PackageInspection,
) -> Result<(), Box<dyn Error>> {
    if target.parts.keys().ne(oracle.parts.keys())
        || target.preview != EXPECTED_TARGET_PREVIEW
        || oracle.preview != EXPECTED_ORACLE_PREVIEW
    {
        return Err("package graph or preview boundary differs".into());
    }
    for part in IMMUTABLE_PARTS {
        if target.parts.get(part) != oracle.parts.get(part) {
            return Err(format!("immutable package part changed: {part}").into());
        }
    }
    Ok(())
}

fn require_target_manifest(
    case: &ManifestCase,
    target: &hwpx_package::TablePropertiesHwpxReadback,
    package: &PackageInspection,
) -> Result<(), Box<dyn Error>> {
    let selected = TablePropertiesHwpxCellValue {
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
    if hex(Sha256::digest(&package.header).into()) != case.target_header_sha256
        || hex(Sha256::digest(&package.section).into()) != case.target_section_sha256
        || hex(target
            .state
            .canonical_sha256(TablePropertiesLimits::default())?)
            != case.target_state_sha256
        || hex(target.grid.canonical_sha256()?) != case.target_grid_sha256
        || target.table_value.canonical_sha256()? != case.target_table_value_sha256
        || selected.canonical_sha256() != case.target_cell_value_sha256
        || target.cell_values.get(4) != Some(&selected)
        || !target.table_value.lock
        || !target.table_value.no_adjust
        || target.payload_block_count != 7
        || target.formula_count != 1
    {
        return Err("target typed properties differ from manifest".into());
    }
    Ok(())
}

fn require_typed_oracle(
    target: &hwpx_package::TablePropertiesHwpxReadback,
    oracle: &hwpx_package::TablePropertiesHwpxReadback,
) -> Result<(), Box<dyn Error>> {
    let comparisons = [
        ("grid", oracle.grid == target.grid),
        (
            "state_without_renderer_payload",
            semantic_state_equal(&oracle.state, &target.state),
        ),
        ("table_value", oracle.table_value == target.table_value),
        ("cell_values", oracle.cell_values == target.cell_values),
        (
            "payload_blocks",
            oracle.payload_block_count == target.payload_block_count,
        ),
        (
            "formula_count",
            oracle.formula_count == target.formula_count,
        ),
    ];
    if let Some((name, _)) = comparisons.iter().find(|(_, equal)| !equal) {
        if *name == "state_without_renderer_payload" {
            return Err(semantic_state_difference(&oracle.state, &target.state).into());
        }
        return Err(format!("oracle typed table-properties field differs: {name}").into());
    }
    Ok(())
}

fn semantic_state_difference(
    oracle: &domain_ir::TablePropertiesState,
    target: &domain_ir::TablePropertiesState,
) -> String {
    if oracle.table_id() != target.table_id() {
        return "oracle typed state differs: table_id".to_owned();
    }
    if oracle.grid_sha256() != target.grid_sha256() {
        return "oracle typed state differs: grid_sha256".to_owned();
    }
    if oracle.table_properties_sha256() != target.table_properties_sha256() {
        return "oracle typed state differs: table_properties_sha256".to_owned();
    }
    if oracle.cells().len() != target.cells().len() {
        return "oracle typed state differs: cell cardinality".to_owned();
    }
    for (index, (oracle_cell, target_cell)) in oracle.cells().iter().zip(target.cells()).enumerate()
    {
        if oracle_cell.master_cell_id != target_cell.master_cell_id {
            return format!("oracle typed state differs: cell[{index}].master_cell_id");
        }
        if oracle_cell.coordinate != target_cell.coordinate {
            return format!("oracle typed state differs: cell[{index}].coordinate");
        }
        if oracle_cell.formula_sha256 != target_cell.formula_sha256 {
            return format!("oracle typed state differs: cell[{index}].formula_sha256");
        }
        let left = &oracle_cell.properties;
        let right = &target_cell.properties;
        if left.non_border_properties_sha256 != right.non_border_properties_sha256 {
            return format!(
                "oracle typed state differs: cell[{index}].non_border_properties_sha256"
            );
        }
        for (field, equal) in [
            (
                "border.top_sha256",
                left.borders.top_sha256 == right.borders.top_sha256,
            ),
            (
                "border.right_sha256",
                left.borders.right_sha256 == right.borders.right_sha256,
            ),
            (
                "border.bottom_sha256",
                left.borders.bottom_sha256 == right.borders.bottom_sha256,
            ),
            (
                "border.left_sha256",
                left.borders.left_sha256 == right.borders.left_sha256,
            ),
            (
                "background_sha256",
                left.background_sha256 == right.background_sha256,
            ),
            (
                "diagonal_sha256",
                left.diagonal_sha256 == right.diagonal_sha256,
            ),
        ] {
            if !equal {
                return format!("oracle typed state differs: cell[{index}].{field}");
            }
        }
    }
    "oracle typed state differs: unknown semantic field".to_owned()
}

fn semantic_state_equal(
    left: &domain_ir::TablePropertiesState,
    right: &domain_ir::TablePropertiesState,
) -> bool {
    left.table_id() == right.table_id()
        && left.grid_sha256() == right.grid_sha256()
        && left.table_properties_sha256() == right.table_properties_sha256()
        && left.cells().len() == right.cells().len()
        && left.cells().iter().zip(right.cells()).all(|(left, right)| {
            left.master_cell_id == right.master_cell_id
                && left.coordinate == right.coordinate
                && left.formula_sha256 == right.formula_sha256
                && left.properties == right.properties
        })
}

fn require_formula_oracle(target: &[u8], oracle: &[u8]) -> Result<(), Box<dyn Error>> {
    let limits = FormulaLimits::default();
    let target_formula = TableFormulaHwpxReader::read_in_section(
        target,
        0,
        TableFormulaHwpxLimits::default(),
        limits,
    )?;
    let oracle_formula = TableFormulaHwpxReader::read_in_section(
        oracle,
        0,
        TableFormulaHwpxLimits::default(),
        limits,
    )?;
    if target_formula.formula != oracle_formula.formula
        || target_formula.formula.owner() != (CellCoordinate { row: 1, column: 3 })
        || target_formula.formula.ast().canonical_formula(limits)? != "SUM(A2:C2)"
        || target_formula.formula_field_count != 1
        || oracle_formula.formula_field_count != 1
        || target
            .windows(b"pageBreak=\"CELL\"".len())
            .filter(|window| *window == b"pageBreak=\"CELL\"")
            .count()
            != 1
        || oracle
            .windows(b"pageBreak=\"CELL\"".len())
            .filter(|window| *window == b"pageBreak=\"CELL\"")
            .count()
            != 1
    {
        return Err("formula or page-split oracle differs".into());
    }
    Ok(())
}

fn binding_from_manifest(
    value: &BindingManifest,
) -> Result<TablePropertiesHwpxBinding, Box<dyn Error>> {
    let mut cells = Vec::new();
    cells.try_reserve_exact(value.cells.len())?;
    for cell in &value.cells {
        cells.push(TableRulingHwpxCellBinding {
            master_cell_id: LogicalId::parse(&cell.master_cell_id)?,
            payload_block_ids: cell
                .payload_block_ids
                .iter()
                .map(LogicalId::parse)
                .collect::<Result<Vec<_>, _>>()?,
        });
    }
    Ok(TablePropertiesHwpxBinding {
        table: TableRulingHwpxBinding {
            table_id: LogicalId::parse(&value.table_id)?,
            row_boundaries_hwpunit: value.row_boundaries_hwpunit.clone(),
            column_boundaries_hwpunit: value.column_boundaries_hwpunit.clone(),
            cells,
        },
        diagonals: Vec::new(),
    })
}

fn binding_from_batch_manifest(
    value: &BatchBindingManifest,
) -> Result<TablePropertiesHwpxBinding, Box<dyn Error>> {
    let mut binding = binding_from_manifest(&value.table)?;
    binding.diagonals = value
        .diagonals
        .iter()
        .map(|diagonal| {
            if diagonal.region.is_some() {
                return Err("deserializing non-null diagonal regions is unsupported".into());
            }
            Ok(TablePropertiesHwpxDiagonalBinding {
                master_cell_id: LogicalId::parse(&diagonal.master_cell_id)?,
                apply_mode: diagonal.apply_mode,
                region: None,
                value: diagonal.value.clone(),
            })
        })
        .collect::<Result<Vec<_>, Box<dyn Error>>>()?;
    Ok(binding)
}

fn require_batch_target_manifest(
    case: &BatchManifestCase,
    target: &hwpx_package::TablePropertiesHwpxReadback,
    package: &PackageInspection,
) -> Result<(), Box<dyn Error>> {
    if hex(Sha256::digest(&package.header).into()) != case.target_header_sha256
        || hex(Sha256::digest(&package.section).into()) != case.target_section_sha256
        || hex(target
            .state
            .canonical_sha256(TablePropertiesLimits::default())?)
            != case.target_state_sha256
        || hex(target.grid.canonical_sha256()?) != case.target_grid_sha256
        || target.payload_block_count != 7
        || target.formula_count != 1
        || target.state.cells().len() != 8
    {
        return Err(format!("{} target typed boundary differs", case.feature_id).into());
    }
    match case.feature_id.as_str() {
        "TABLE-008" => require_each_border_target(case, target),
        "TABLE-009" => require_unified_border_target(case, target),
        "TABLE-047" => require_diagonal_target(case, target),
        _ => Err("unexpected border/diagonal feature identity".into()),
    }
}

fn require_each_border_target(
    case: &BatchManifestCase,
    target: &hwpx_package::TablePropertiesHwpxReadback,
) -> Result<(), Box<dyn Error>> {
    for coordinate in &case.selected_slots {
        let properties = &state_cell_at(target, coordinate)?.properties;
        if properties.borders.top_sha256.as_deref() != Some(&case.line_sha256[0])
            || properties.borders.right_sha256.as_deref() != Some(&case.line_sha256[1])
            || properties.borders.bottom_sha256.as_deref() != Some(&case.line_sha256[2])
            || properties.borders.left_sha256.as_deref() != Some(&case.line_sha256[3])
            || properties.background_sha256 != case.background_sha256
            || properties.diagonal_sha256.is_some()
        {
            return Err("TABLE-008 selected-cell semantic value differs".into());
        }
    }
    Ok(())
}

fn require_unified_border_target(
    case: &BatchManifestCase,
    target: &hwpx_package::TablePropertiesHwpxReadback,
) -> Result<(), Box<dyn Error>> {
    for coordinate in &case.selected_slots {
        let properties = &state_cell_at(target, coordinate)?.properties;
        let top = if coordinate.row == 0 { 0 } else { 4 };
        let right = if coordinate.column == 1 { 1 } else { 5 };
        let bottom = if coordinate.row == 1 { 2 } else { 4 };
        let left = if coordinate.column == 0 { 3 } else { 5 };
        if properties.borders.top_sha256.as_deref() != Some(&case.line_sha256[top])
            || properties.borders.right_sha256.as_deref() != Some(&case.line_sha256[right])
            || properties.borders.bottom_sha256.as_deref() != Some(&case.line_sha256[bottom])
            || properties.borders.left_sha256.as_deref() != Some(&case.line_sha256[left])
            || properties.background_sha256 != case.background_sha256
            || properties.diagonal_sha256.is_some()
        {
            return Err("TABLE-009 selected-cell border role differs".into());
        }
    }
    Ok(())
}

fn require_diagonal_target(
    case: &BatchManifestCase,
    target: &hwpx_package::TablePropertiesHwpxReadback,
) -> Result<(), Box<dyn Error>> {
    let value = case
        .diagonal
        .as_ref()
        .ok_or("TABLE-047 diagonal value is missing")?;
    let identity = table_diagonal_identity_sha256(
        target.state.table_id(),
        target.state.grid_sha256(),
        TableDiagonalApplyMode::EachCell,
        None,
        value,
        TablePropertiesLimits::default(),
    )?;
    for cell in target.state.cells() {
        let expected = if cell.coordinate == (CellCoordinate { row: 0, column: 2 }) {
            Some(identity.as_str())
        } else {
            None
        };
        if cell.properties.diagonal_sha256.as_deref() != expected {
            return Err("TABLE-047 diagonal semantic assignment differs".into());
        }
    }
    Ok(())
}

fn state_cell_at<'a>(
    target: &'a hwpx_package::TablePropertiesHwpxReadback,
    coordinate: &CoordinateManifest,
) -> Result<&'a domain_ir::TableCellPropertyDraft, Box<dyn Error>> {
    target
        .state
        .cells()
        .iter()
        .find(|cell| {
            cell.coordinate
                == (CellCoordinate {
                    row: coordinate.row,
                    column: coordinate.column,
                })
        })
        .ok_or_else(|| "selected state cell is missing".into())
}

type RendererCacheStrip = (Vec<u8>, [u8; 32], usize);

fn strip_renderer_caches(section: &[u8]) -> Result<RendererCacheStrip, Box<dyn Error>> {
    let expected_geometry = [
        (0, 850, 9_468),
        (0, 850, 9_468),
        (0, 850, 9_468),
        (0, 850, 9_468),
        (0, 500, 3_000),
        (0, 850, 9_468),
        (0, 850, 9_468),
        (0, 850, 9_468),
        (0, 850, 0),
        (8_566, 850, 42_520),
    ];
    strip_renderer_caches_with_geometry(section, &expected_geometry)
}

fn strip_standard_renderer_caches(section: &[u8]) -> Result<RendererCacheStrip, Box<dyn Error>> {
    let expected_geometry = [
        (0, 850, 9_468),
        (0, 850, 9_468),
        (0, 850, 9_468),
        (0, 850, 9_468),
        (0, 850, 9_468),
        (0, 850, 9_468),
        (0, 850, 9_468),
        (0, 850, 9_468),
        (0, 850, 0),
        (8_566, 850, 42_520),
    ];
    strip_renderer_caches_with_geometry(section, &expected_geometry)
}

fn strip_renderer_caches_with_geometry(
    section: &[u8],
    expected_geometry: &[(u32, u32, u32)],
) -> Result<RendererCacheStrip, Box<dyn Error>> {
    let document = PreservingXmlDocument::parse(section)?;
    let arrays: Vec<_> = document
        .elements()
        .iter()
        .enumerate()
        .filter(|(_, element)| has_name(element, "linesegarray"))
        .map(|(index, _)| index)
        .collect();
    if arrays.len() != expected_geometry.len() {
        return Err("renderer cache cardinality differs".into());
    }
    let mut spans = Vec::new();
    let mut digest = Sha256::new();
    digest.update(b"hwpx-agent.p06-09-table-properties-renderer-cache/v1\0");
    for (array, expected) in arrays
        .iter()
        .copied()
        .zip(expected_geometry.iter().copied())
    {
        let element = document
            .elements()
            .get(array)
            .ok_or("renderer cache array is missing")?;
        if !element.attributes().is_empty()
            || element
                .parent()
                .and_then(|parent| document.elements().get(parent))
                .is_none_or(|parent| !has_name(parent, "p"))
        {
            return Err("renderer cache array shape differs".into());
        }
        let child = element
            .first_child()
            .ok_or("renderer cache segment is missing")?;
        if element.last_child() != Some(child) {
            return Err("renderer cache segment cardinality differs".into());
        }
        let segment = document
            .elements()
            .get(child)
            .ok_or("renderer cache segment is missing")?;
        if !has_name(segment, "lineseg") || !segment.is_empty() || segment.attributes().len() != 9 {
            return Err("renderer cache segment shape differs".into());
        }
        let fixed = [
            exact_u32_attribute(section, segment, "textpos")?,
            exact_u32_attribute(section, segment, "vertsize")?,
            exact_u32_attribute(section, segment, "textheight")?,
            exact_u32_attribute(section, segment, "spacing")?,
            exact_u32_attribute(section, segment, "horzpos")?,
            exact_u32_attribute(section, segment, "flags")?,
        ];
        let geometry = (
            exact_u32_attribute(section, segment, "vertpos")?,
            exact_u32_attribute(section, segment, "baseline")?,
            exact_u32_attribute(section, segment, "horzsize")?,
        );
        if fixed != [0, 1_000, 1_000, 600, 0, 393_216] || geometry != expected {
            return Err("renderer cache values differ".into());
        }
        let span = element
            .outer_span()
            .ok_or("renderer cache span is missing")?;
        let raw = section
            .get(span.start()..span.end())
            .ok_or("renderer cache span is outside section")?;
        digest.update(Sha256::digest(raw));
        spans.push(span);
    }
    let stripped = strip_spans(section, &mut spans)?;
    Ok((stripped, digest.finalize().into(), arrays.len()))
}

fn strip_spans(section: &[u8], spans: &mut [XmlByteSpan]) -> Result<Vec<u8>, Box<dyn Error>> {
    spans.sort_by_key(|span| span.start());
    let removed = spans.iter().try_fold(0usize, |total, span| {
        total
            .checked_add(span.end().checked_sub(span.start()).ok_or("invalid span")?)
            .ok_or("renderer cache size overflow")
    })?;
    let mut output = Vec::new();
    output.try_reserve_exact(
        section
            .len()
            .checked_sub(removed)
            .ok_or("renderer cache size underflow")?,
    )?;
    let mut cursor = 0;
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

fn exact_u32_attribute(
    source: &[u8],
    element: &XmlElementToken,
    name: &str,
) -> Result<u32, Box<dyn Error>> {
    let mut values = element.attributes().iter().filter(|attribute| {
        !attribute.is_namespace_declaration()
            && attribute.name().namespace().is_none()
            && attribute.name().local_name() == name
    });
    let value = values.next().ok_or("renderer cache attribute is missing")?;
    if values.next().is_some() {
        return Err("renderer cache attribute is duplicated".into());
    }
    let span = value.value_span();
    let raw = source
        .get(span.start()..span.end())
        .ok_or("renderer cache attribute span is outside section")?;
    Ok(std::str::from_utf8(raw)?.parse()?)
}

fn has_name(element: &XmlElementToken, local_name: &str) -> bool {
    element.name().namespace() == Some(HANCOM_2020_PARAGRAPH_NAMESPACE)
        && element.name().local_name() == local_name
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
    if bytes.len() as u64 != metadata.len() {
        return Err("input changed while being read".into());
    }
    Ok(bytes)
}

fn require_digest(bytes: &[u8], expected: &str, label: &str) -> Result<(), Box<dyn Error>> {
    if hex(Sha256::digest(bytes).into()) != expected {
        return Err(format!("{label} SHA-256 differs").into());
    }
    Ok(())
}

fn path_argument(
    arguments: &mut impl Iterator<Item = std::ffi::OsString>,
    name: &str,
) -> Result<PathBuf, Box<dyn Error>> {
    arguments
        .next()
        .map(PathBuf::from)
        .ok_or_else(|| format!("missing {name}").into())
}

fn string_argument(
    arguments: &mut impl Iterator<Item = std::ffi::OsString>,
    name: &str,
) -> Result<String, Box<dyn Error>> {
    arguments
        .next()
        .ok_or_else(|| format!("missing {name}"))?
        .into_string()
        .map_err(|_| format!("{name} is not Unicode").into())
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

fn hex(value: [u8; 32]) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let mut output = String::with_capacity(64);
    for byte in value {
        output.push(char::from(DIGITS[usize::from(byte >> 4)]));
        output.push(char::from(DIGITS[usize::from(byte & 0x0f)]));
    }
    output
}
