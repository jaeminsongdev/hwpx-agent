use std::collections::BTreeMap;
use std::env;
use std::error::Error;
use std::fs;
use std::io::Cursor;
use std::path::{Path, PathBuf};

use domain_ir::{
    FormulaLimits, LogicalId, TableDelimiter, TableLineEnding, TableRulingLimits,
    TableTextConversionLimits, TableTextGrid,
};
use hwpx_package::{
    BoundedZipReader, HANCOM_2020_PARAGRAPH_NAMESPACE, IdIndex, IdIndexLimits, IdRuleProfile,
    PackageGraph, PackageGraphLimits, PackageLimits, PreservingXmlDocument, TableFormulaHwpxLimits,
    TableFormulaHwpxReader, TablePaginationHwpxLimits, TablePaginationHwpxReader,
    TableRulingHwpxBinding, TableRulingHwpxCellBinding, TableRulingHwpxLimits,
    TableRulingHwpxReadback, TableRulingHwpxReader, TableTableToTextHwpxLimits,
    TableTableToTextHwpxReader, TextFlowLimits, TextFlowReader, XmlByteSpan, XmlElementToken,
};
use serde::Deserialize;
use sha2::{Digest as _, Sha256};

const MAX_FILE_BYTES: u64 = 8 * 1024 * 1024;
const MAX_MANIFEST_BYTES: u64 = 256 * 1024;
const MAX_RENDERER_CACHE_ARRAYS: usize = 512;
const EXPECTED_PACKAGE_PARTS: usize = 11;
const EXPECTED_MANIFEST_SHA256: &str =
    "6c32f7ccdaad74ad62a2e32257e203ce2c61dc74dafc11026d9ddfe0f045220a";
const EXPECTED_ANCESTOR_SHA256: &str =
    "6514a69b8c8c9d320bc19a032b16f2b71d59a38f164c690bc9e3d320a93320e5";
const IMMUTABLE_PARTS: [&str; 5] = [
    "mimetype",
    "version.xml",
    "META-INF/container.rdf",
    "META-INF/container.xml",
    "META-INF/manifest.xml",
];

#[derive(Clone, Copy)]
struct CaseProfile {
    case_id: &'static str,
    feature_id: &'static str,
    capability_id: &'static str,
    file: &'static str,
    table_output: bool,
    delimiter: TableDelimiter,
    line_ending: TableLineEnding,
    rows: u32,
    columns: u32,
    master_cells: usize,
    payload_blocks: usize,
    target_table_count: usize,
    target_paragraph_ordinal: Option<usize>,
    row_heights_hwpunit: &'static [u32],
    column_widths_hwpunit: &'static [u32],
    row_boundaries_hwpunit: &'static [u32],
    column_boundaries_hwpunit: &'static [u32],
}

const CASES: [CaseProfile; 4] = [
    CaseProfile {
        case_id: "table-004-quoted-multiline-3x2",
        feature_id: "TABLE-004",
        capability_id: "table.text_to_table",
        file: "table-004-text-to-table-quoted-multiline-3x2.hwpx",
        table_output: true,
        delimiter: TableDelimiter::Comma,
        line_ending: TableLineEnding::CrLf,
        rows: 3,
        columns: 2,
        master_cells: 6,
        payload_blocks: 5,
        target_table_count: 2,
        target_paragraph_ordinal: None,
        row_heights_hwpunit: &[4_000, 5_000, 6_000],
        column_widths_hwpunit: &[12_000, 16_000],
        row_boundaries_hwpunit: &[0, 4_000, 9_000, 15_000],
        column_boundaries_hwpunit: &[0, 12_000, 28_000],
    },
    CaseProfile {
        case_id: "table-005-quoted-multiline-3x2",
        feature_id: "TABLE-005",
        capability_id: "table.table_to_text",
        file: "table-005-table-to-text-quoted-multiline-3x2.hwpx",
        table_output: false,
        delimiter: TableDelimiter::Comma,
        line_ending: TableLineEnding::CrLf,
        rows: 3,
        columns: 2,
        master_cells: 6,
        payload_blocks: 5,
        target_table_count: 1,
        target_paragraph_ordinal: Some(1),
        row_heights_hwpunit: &[4_000, 5_000, 6_000],
        column_widths_hwpunit: &[12_000, 16_000],
        row_boundaries_hwpunit: &[0, 4_000, 9_000, 15_000],
        column_boundaries_hwpunit: &[0, 12_000, 28_000],
    },
    CaseProfile {
        case_id: "table-004-boundary-1x1",
        feature_id: "TABLE-004",
        capability_id: "table.text_to_table",
        file: "table-004-text-to-table-boundary-1x1.hwpx",
        table_output: true,
        delimiter: TableDelimiter::Semicolon,
        line_ending: TableLineEnding::Lf,
        rows: 1,
        columns: 1,
        master_cells: 1,
        payload_blocks: 1,
        target_table_count: 2,
        target_paragraph_ordinal: None,
        row_heights_hwpunit: &[6_000],
        column_widths_hwpunit: &[14_000],
        row_boundaries_hwpunit: &[0, 6_000],
        column_boundaries_hwpunit: &[0, 14_000],
    },
    CaseProfile {
        case_id: "table-005-boundary-1x1",
        feature_id: "TABLE-005",
        capability_id: "table.table_to_text",
        file: "table-005-table-to-text-boundary-1x1.hwpx",
        table_output: false,
        delimiter: TableDelimiter::Semicolon,
        line_ending: TableLineEnding::Lf,
        rows: 1,
        columns: 1,
        master_cells: 1,
        payload_blocks: 1,
        target_table_count: 1,
        target_paragraph_ordinal: Some(1),
        row_heights_hwpunit: &[6_000],
        column_widths_hwpunit: &[14_000],
        row_boundaries_hwpunit: &[0, 6_000],
        column_boundaries_hwpunit: &[0, 14_000],
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
        let result = Self {
            manifest: path_argument(&mut values, "fixture manifest")?,
            expected_manifest_sha256: string_argument(&mut values, "manifest SHA-256")?,
            case_id: string_argument(&mut values, "case ID")?,
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
    template_section_sha256: String,
    template_state_sha256: String,
    template_grid_sha256: String,
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
    source_case_id: String,
    feature_id: String,
    capability_id: String,
    file: String,
    sha256: String,
    operation_table_ordinal: usize,
    target_paragraph_ordinal: Option<usize>,
    rows: u32,
    columns: u32,
    row_heights_hwpunit: Vec<u32>,
    column_widths_hwpunit: Vec<u32>,
    target_header_sha256: String,
    target_section_sha256: String,
    state_sha256: String,
    grid_sha256: String,
    text_grid_sha256: String,
    serialized_text_sha256: Option<String>,
    target_paragraph_sha256: Option<String>,
    request_sha256: String,
    plan_sha256: String,
    master_cell_count: usize,
    payload_block_count: usize,
    formula_count: usize,
    target_table_count: usize,
    page_split_preserved: bool,
    binding: BindingManifest,
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

struct PackageParts {
    parts: BTreeMap<String, Vec<u8>>,
    header: Vec<u8>,
    section: Vec<u8>,
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
        return Err("exact table-text-conversion fixture manifest identity differs".into());
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
        .ok_or("table-text-conversion case is missing from manifest")?;
    let target_path = arguments
        .manifest
        .parent()
        .ok_or("manifest parent is missing")?
        .join(&case.file);
    if fs::canonicalize(&target_path)? == fs::canonicalize(&arguments.oracle)? {
        return Err("target and oracle paths must differ".into());
    }
    let target_bytes = read_bounded_file(&target_path, MAX_FILE_BYTES)?;
    let oracle_bytes = read_bounded_file(&arguments.oracle, MAX_FILE_BYTES)?;
    require_digest(&target_bytes, &case.sha256, "target")?;
    require_digest(&oracle_bytes, &arguments.expected_oracle_sha256, "oracle")?;

    let target = read_package(&target_bytes)?;
    let oracle = read_package(&oracle_bytes)?;
    let oracle_cache = validate_package_semantics(&target, &oracle, profile, case)?;
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
    println!(
        concat!(
            "schema=hwpx-agent.p06-09-table-text-conversion-target-oracle/v1 state=pass ",
            "case_id={} feature_id={} capability_id={} target_sha256={} oracle_sha256={} ",
            "state_sha256={} grid_sha256={} text_grid_sha256={} rows={} columns={} ",
            "master_cells={} payload_blocks={} formulas=0 preexisting_formula_fields=1 ",
            "renderer_cache_count={} renderer_cache_sha256={} ",
            "typed_conversion_pagination_text_and_exterior_preserved=true"
        ),
        profile.case_id,
        profile.feature_id,
        profile.capability_id,
        case.sha256,
        arguments.expected_oracle_sha256,
        case.state_sha256,
        case.grid_sha256,
        case.text_grid_sha256,
        profile.rows,
        profile.columns,
        profile.master_cells,
        profile.payload_blocks,
        oracle_cache.count,
        hex(oracle_cache.sha256),
    );
    Ok(())
}

fn validate_package_semantics(
    target: &PackageParts,
    oracle: &PackageParts,
    profile: CaseProfile,
    case: &ManifestCase,
) -> Result<RendererCacheEvidence, Box<dyn Error>> {
    require_package_boundary(target, oracle)?;
    require_digest(&target.header, &case.target_header_sha256, "target header")?;
    require_digest(
        &target.section,
        &case.target_section_sha256,
        "target section",
    )?;

    let (target_section, target_cache) = strip_renderer_caches(&target.section)?;
    let (oracle_section, oracle_cache) = strip_renderer_caches(&oracle.section)?;
    if target_cache.count != 0 || oracle_cache.count == 0 {
        return Err("table-text-conversion renderer-cache evidence differs".into());
    }
    if count_elements(&target_section, "tbl")? != profile.target_table_count
        || count_elements(&oracle_section, "tbl")? != profile.target_table_count
        || count_formula_fields(&target_section)? != 1
        || count_formula_fields(&oracle_section)? != 1
    {
        return Err("table-text-conversion document-level preservation differs".into());
    }

    require_formula_table_preserved(target, oracle, &target_section, &oracle_section)?;
    if profile.table_output {
        validate_table_output(
            target,
            oracle,
            &target_section,
            &oracle_section,
            profile,
            case,
        )?;
    } else {
        validate_text_output(&target_section, &oracle_section, profile, case)?;
    }
    Ok(oracle_cache)
}

fn require_formula_table_preserved(
    target: &PackageParts,
    oracle: &PackageParts,
    target_section: &[u8],
    oracle_section: &[u8],
) -> Result<(), Box<dyn Error>> {
    let target_formula = TableFormulaHwpxReader::read_in_section(
        target_section,
        0,
        TableFormulaHwpxLimits::default(),
        FormulaLimits::default(),
    )?;
    let oracle_formula = TableFormulaHwpxReader::read_in_section(
        oracle_section,
        0,
        TableFormulaHwpxLimits::default(),
        FormulaLimits::default(),
    )?;
    if target_formula.profile_id != oracle_formula.profile_id
        || target_formula.rows != oracle_formula.rows
        || target_formula.columns != oracle_formula.columns
        || target_formula.formula != oracle_formula.formula
        || target_formula.formula_field_count != 1
        || oracle_formula.formula_field_count != 1
        || target.header.is_empty()
        || oracle.header.is_empty()
    {
        return Err("pre-existing formula table preservation differs".into());
    }
    Ok(())
}

fn validate_table_output(
    target: &PackageParts,
    oracle: &PackageParts,
    target_section: &[u8],
    oracle_section: &[u8],
    profile: CaseProfile,
    case: &ManifestCase,
) -> Result<(), Box<dyn Error>> {
    let binding = binding_from_manifest(&case.binding)?;
    let target_readback = read_ruling(&target.header, target_section, 1, &binding)?;
    let oracle_readback = read_ruling(&oracle.header, oracle_section, 1, &binding)?;
    require_case_semantics(profile, case, &target_readback)
        .map_err(|error| format!("target {error}"))?;
    require_case_semantics(profile, case, &oracle_readback)
        .map_err(|error| format!("oracle {error}"))?;
    require_equivalent_readback(&target_readback, &oracle_readback)?;

    let target_conversion = TableTableToTextHwpxReader::read_context(
        &target.header,
        target_section,
        1,
        &binding,
        profile.delimiter,
        profile.line_ending,
        TableTableToTextHwpxLimits::default(),
    )?;
    let oracle_conversion = TableTableToTextHwpxReader::read_context(
        &oracle.header,
        oracle_section,
        1,
        &binding,
        profile.delimiter,
        profile.line_ending,
        TableTableToTextHwpxLimits::default(),
    )?;
    if target_conversion.text_grid != oracle_conversion.text_grid
        || hex(target_conversion
            .text_grid
            .canonical_sha256(TableTextConversionLimits::default())?)
            != case.text_grid_sha256
    {
        return Err("text-to-table text-grid oracle differs".into());
    }

    let target_pagination = TablePaginationHwpxReader::read_in_section(
        target_section,
        1,
        TablePaginationHwpxLimits::default(),
    )?;
    let oracle_pagination = TablePaginationHwpxReader::read_in_section(
        oracle_section,
        1,
        TablePaginationHwpxLimits::default(),
    )?;
    if target_pagination != oracle_pagination
        || target_pagination.row_count != profile.rows
        || target_pagination.column_count != profile.columns
        || target_pagination.repeat_header_rows != 0
        || target_pagination.caption.is_some()
    {
        return Err("text-to-table pagination readback differs".into());
    }
    require_selected_table_exterior_equal(target_section, oracle_section, 1)
}

fn validate_text_output(
    target_section: &[u8],
    oracle_section: &[u8],
    profile: CaseProfile,
    case: &ManifestCase,
) -> Result<(), Box<dyn Error>> {
    let ordinal = profile
        .target_paragraph_ordinal
        .ok_or("target paragraph ordinal is missing")?;
    let target_paragraph = top_level_paragraph(target_section, ordinal)?;
    let oracle_paragraph = top_level_paragraph(oracle_section, ordinal)?;
    require_digest(
        &target_paragraph,
        case.target_paragraph_sha256
            .as_deref()
            .ok_or("target paragraph digest is missing")?,
        "target paragraph",
    )?;
    let target_flow = TextFlowReader::read(
        &standalone_paragraph(&target_paragraph)?,
        TextFlowLimits::default(),
    )?;
    let oracle_flow = TextFlowReader::read(
        &standalone_paragraph(&oracle_paragraph)?,
        TextFlowLimits::default(),
    )?;
    if target_flow != oracle_flow {
        return Err("table-to-text typed paragraph oracle differs".into());
    }
    let visible = target_flow.visible_text_nfc()?;
    let grid = TableTextGrid::parse_delimited(
        visible.as_bytes(),
        profile.delimiter,
        TableTextConversionLimits::default(),
    )?;
    if grid.row_count() != usize::try_from(profile.rows)?
        || grid.column_count() != usize::try_from(profile.columns)?
        || hex(grid.canonical_sha256(TableTextConversionLimits::default())?)
            != case.text_grid_sha256
    {
        return Err("table-to-text visible grid differs".into());
    }
    let serialized = grid.to_delimited(
        profile.delimiter,
        profile.line_ending,
        TableTextConversionLimits::default(),
    )?;
    require_digest(
        &serialized,
        case.serialized_text_sha256
            .as_deref()
            .ok_or("serialized text digest is missing")?,
        "serialized text",
    )?;
    require_selected_paragraph_exterior_equal(target_section, oracle_section, ordinal)
}

fn validate_manifest(manifest: &Manifest) -> Result<(), Box<dyn Error>> {
    if manifest.schema_version != "hwpx-agent.p06-09-table-text-conversion-target-fixture/v1"
        || manifest.source_ancestor_sha256 != EXPECTED_ANCESTOR_SHA256
        || manifest.actual_hangul_2020
        || manifest.render != "not_run"
        || manifest.automation != "not_run"
        || manifest.differential != "not_run"
        || manifest.cases.len() != CASES.len()
    {
        return Err("table-text-conversion manifest state differs".into());
    }
    for digest in [
        &manifest.template_section_sha256,
        &manifest.template_state_sha256,
        &manifest.template_grid_sha256,
    ] {
        require_lower_sha256(digest)?;
    }
    for (case, profile) in manifest.cases.iter().zip(CASES) {
        for digest in [
            &case.sha256,
            &case.target_header_sha256,
            &case.target_section_sha256,
            &case.state_sha256,
            &case.grid_sha256,
            &case.text_grid_sha256,
            &case.request_sha256,
            &case.plan_sha256,
        ] {
            require_lower_sha256(digest)?;
        }
        let text_digests_match = if profile.table_output {
            case.serialized_text_sha256.is_none() && case.target_paragraph_sha256.is_none()
        } else {
            case.serialized_text_sha256
                .as_deref()
                .is_some_and(|value| require_lower_sha256(value).is_ok())
                && case
                    .target_paragraph_sha256
                    .as_deref()
                    .is_some_and(|value| require_lower_sha256(value).is_ok())
        };
        if case.case_id != profile.case_id
            || case.feature_id != profile.feature_id
            || case.capability_id != profile.capability_id
            || case.file != profile.file
            || case.operation_table_ordinal != 1
            || case.target_paragraph_ordinal != profile.target_paragraph_ordinal
            || case.rows != profile.rows
            || case.columns != profile.columns
            || case.row_heights_hwpunit != profile.row_heights_hwpunit
            || case.column_widths_hwpunit != profile.column_widths_hwpunit
            || case.master_cell_count != profile.master_cells
            || case.payload_block_count != profile.payload_blocks
            || case.formula_count != 0
            || case.target_table_count != profile.target_table_count
            || !case.page_split_preserved
            || case.binding.row_boundaries_hwpunit != profile.row_boundaries_hwpunit
            || case.binding.column_boundaries_hwpunit != profile.column_boundaries_hwpunit
            || case.binding.cells.len() != profile.master_cells
            || case
                .binding
                .cells
                .iter()
                .flat_map(|cell| &cell.payload_block_ids)
                .count()
                != profile.payload_blocks
            || !text_digests_match
            || case.source_case_id.is_empty()
        {
            return Err("table-text-conversion manifest case profile differs".into());
        }
    }
    for pair in manifest.cases.chunks_exact(2) {
        if pair[0].source_case_id != pair[1].source_case_id
            || pair[0].state_sha256 != pair[1].state_sha256
            || pair[0].grid_sha256 != pair[1].grid_sha256
            || pair[0].text_grid_sha256 != pair[1].text_grid_sha256
        {
            return Err("paired conversion manifest semantics differ".into());
        }
    }
    Ok(())
}

fn require_package_boundary(
    target: &PackageParts,
    oracle: &PackageParts,
) -> Result<(), Box<dyn Error>> {
    if target.parts.len() != EXPECTED_PACKAGE_PARTS || oracle.parts.len() != target.parts.len() {
        return Err("table-text-conversion package part cardinality differs".into());
    }
    let target_names: Vec<_> = target.parts.keys().collect();
    let oracle_names: Vec<_> = oracle.parts.keys().collect();
    if target_names != oracle_names {
        return Err("table-text-conversion package part names differ".into());
    }
    for name in IMMUTABLE_PARTS {
        if target.parts.get(name) != oracle.parts.get(name) {
            return Err(format!("immutable package part differs: {name}").into());
        }
    }
    Ok(())
}

fn binding_from_manifest(
    value: &BindingManifest,
) -> Result<TableRulingHwpxBinding, Box<dyn Error>> {
    Ok(TableRulingHwpxBinding {
        table_id: LogicalId::parse(&value.table_id)?,
        row_boundaries_hwpunit: value.row_boundaries_hwpunit.clone(),
        column_boundaries_hwpunit: value.column_boundaries_hwpunit.clone(),
        cells: value
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
            .collect::<Result<Vec<_>, Box<dyn Error>>>()?,
    })
}

fn require_case_semantics(
    profile: CaseProfile,
    case: &ManifestCase,
    readback: &TableRulingHwpxReadback,
) -> Result<(), Box<dyn Error>> {
    let observed_state_sha256 = hex(readback
        .state
        .canonical_sha256(TableRulingLimits::default())?);
    let observed_grid_sha256 = hex(readback.grid.canonical_sha256()?);
    if readback.grid.rows() != profile.rows
        || readback.grid.columns() != profile.columns
        || readback.grid.master_cell_count() != profile.master_cells
        || readback
            .grid
            .master_cells()
            .iter()
            .any(|cell| cell.row_span != 1 || cell.column_span != 1)
        || readback.state.row_boundaries_hwpunit() != profile.row_boundaries_hwpunit
        || readback.state.column_boundaries_hwpunit() != profile.column_boundaries_hwpunit
        || readback.payload_block_count != profile.payload_blocks
        || readback.formula_count != 0
        || observed_state_sha256 != case.state_sha256
        || observed_grid_sha256 != case.grid_sha256
    {
        return Err(format!(
            concat!(
                "table-text-conversion typed semantic profile differs: ",
                "rows={} columns={} master_cells={} payload_blocks={} formulas={} ",
                "state_sha256={} grid_sha256={}"
            ),
            readback.grid.rows(),
            readback.grid.columns(),
            readback.grid.master_cell_count(),
            readback.payload_block_count,
            readback.formula_count,
            observed_state_sha256,
            observed_grid_sha256,
        )
        .into());
    }
    Ok(())
}

fn require_equivalent_readback(
    target: &TableRulingHwpxReadback,
    oracle: &TableRulingHwpxReadback,
) -> Result<(), Box<dyn Error>> {
    if target.profile_id != oracle.profile_id
        || target.grid != oracle.grid
        || target.state != oracle.state
        || target.table_content_sha256 != oracle.table_content_sha256
        || target.payload_block_count != oracle.payload_block_count
        || target.formula_count != oracle.formula_count
    {
        return Err("table-text-conversion typed oracle readback differs".into());
    }
    Ok(())
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

fn require_selected_table_exterior_equal(
    target: &[u8],
    oracle: &[u8],
    ordinal: usize,
) -> Result<(), Box<dyn Error>> {
    if selected_table_exterior(target, ordinal)? != selected_table_exterior(oracle, ordinal)? {
        return Err("table-text-conversion section exterior differs".into());
    }
    Ok(())
}

fn require_selected_paragraph_exterior_equal(
    target: &[u8],
    oracle: &[u8],
    ordinal: usize,
) -> Result<(), Box<dyn Error>> {
    if selected_paragraph_exterior(target, ordinal)?
        != selected_paragraph_exterior(oracle, ordinal)?
    {
        return Err("table-to-text paragraph exterior differs".into());
    }
    Ok(())
}

fn selected_paragraph_exterior(section: &[u8], ordinal: usize) -> Result<Vec<u8>, Box<dyn Error>> {
    const MARKER: &[u8] = b"<hwpx-agent-selected-paragraph/>";
    let document = PreservingXmlDocument::parse(section)?;
    let root = document.root_element();
    let paragraph = document
        .elements()
        .iter()
        .filter(|element| element.parent() == Some(root) && has_name(element, "p"))
        .nth(ordinal)
        .ok_or("selected paragraph is missing")?;
    let span = paragraph
        .outer_span()
        .ok_or("selected paragraph span is missing")?;
    replace_span_with_marker(section, span, MARKER)
}

fn top_level_paragraph(section: &[u8], ordinal: usize) -> Result<Vec<u8>, Box<dyn Error>> {
    let document = PreservingXmlDocument::parse(section)?;
    let root = document.root_element();
    let paragraph = document
        .elements()
        .iter()
        .filter(|element| element.parent() == Some(root) && has_name(element, "p"))
        .nth(ordinal)
        .ok_or("selected paragraph is missing")?;
    let span = paragraph
        .outer_span()
        .ok_or("selected paragraph span is missing")?;
    Ok(section
        .get(span.start()..span.end())
        .ok_or("selected paragraph is outside section")?
        .to_vec())
}

fn replace_span_with_marker(
    source: &[u8],
    span: XmlByteSpan,
    marker: &[u8],
) -> Result<Vec<u8>, Box<dyn Error>> {
    let mut output = Vec::new();
    output.try_reserve_exact(
        source
            .len()
            .checked_sub(
                span.end()
                    .checked_sub(span.start())
                    .ok_or("span underflow")?,
            )
            .and_then(|size| size.checked_add(marker.len()))
            .ok_or("marked exterior size overflow")?,
    )?;
    output.extend_from_slice(
        source
            .get(..span.start())
            .ok_or("prefix is outside source")?,
    );
    output.extend_from_slice(marker);
    output.extend_from_slice(source.get(span.end()..).ok_or("suffix is outside source")?);
    Ok(output)
}

fn standalone_paragraph(fragment: &[u8]) -> Result<Vec<u8>, Box<dyn Error>> {
    const PREFIX: &[u8] = b"<hp:p";
    if !fragment.starts_with(PREFIX) {
        return Err("paragraph fragment prefix differs".into());
    }
    let mut output = Vec::new();
    output.try_reserve_exact(
        fragment
            .len()
            .checked_add(HANCOM_2020_PARAGRAPH_NAMESPACE.len())
            .and_then(|size| size.checked_add(12))
            .ok_or("standalone paragraph size overflow")?,
    )?;
    output.extend_from_slice(PREFIX);
    output.extend_from_slice(b" xmlns:hp=\"");
    output.extend_from_slice(HANCOM_2020_PARAGRAPH_NAMESPACE.as_bytes());
    output.push(b'"');
    output.extend_from_slice(&fragment[PREFIX.len()..]);
    Ok(output)
}

fn selected_table_exterior(section: &[u8], ordinal: usize) -> Result<Vec<u8>, Box<dyn Error>> {
    const MARKER: &[u8] = b"<hwpx-agent-selected-table/>";
    let document = PreservingXmlDocument::parse(section)?;
    let table = document
        .elements()
        .iter()
        .filter(|element| has_name(element, "tbl"))
        .nth(ordinal)
        .ok_or("selected table is missing")?;
    let span = table.outer_span().ok_or("selected table span is missing")?;
    let mut output = Vec::new();
    output.try_reserve_exact(
        section
            .len()
            .checked_sub(span.end().saturating_sub(span.start()))
            .and_then(|size| size.checked_add(MARKER.len()))
            .ok_or("selected table exterior size overflow")?,
    )?;
    output.extend_from_slice(
        section
            .get(..span.start())
            .ok_or("selected table prefix is outside section")?,
    );
    output.extend_from_slice(MARKER);
    output.extend_from_slice(
        section
            .get(span.end()..)
            .ok_or("selected table suffix is outside section")?,
    );
    Ok(output)
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
        return Err("table-text-conversion package graph cardinality differs".into());
    }
    let entries: Vec<_> = reader
        .entries()
        .iter()
        .map(|entry| (entry.path.as_str().to_owned(), entry.index))
        .collect();
    let mut parts = BTreeMap::new();
    for (path, index) in entries {
        if parts.insert(path, reader.read_entry(index)?).is_some() {
            return Err("duplicate package part".into());
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
    Ok(PackageParts {
        parts,
        header,
        section,
    })
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
    digest.update(b"hwpx-agent.p06-09-table-text-conversion-renderer-cache/v1\0");
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
            line_count = line_count
                .checked_add(1)
                .ok_or("renderer line count overflow")?;
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
        let _: u32 = exact_attribute(source, line, name)?.parse()?;
    }
    Ok(())
}

fn strip_spans(section: &[u8], spans: &mut [XmlByteSpan]) -> Result<Vec<u8>, Box<dyn Error>> {
    spans.sort_by_key(|span| span.start());
    let removed = spans.iter().try_fold(0usize, |total, span| {
        total
            .checked_add(
                span.end()
                    .checked_sub(span.start())
                    .ok_or("renderer cache span underflow")?,
            )
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
        .ok_or_else(|| "unsupported table-text-conversion case ID".into())
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
    fn exact_case_profiles_cover_arbitrary_and_boundary_shapes() {
        assert_eq!(CASES.len(), 4);
        assert_eq!(CASES[0].master_cells, 6);
        assert_eq!(CASES[2].master_cells, 1);
        assert_ne!(
            CASES[0].row_heights_hwpunit[0],
            CASES[0].row_heights_hwpunit[1]
        );
        assert_ne!(
            CASES[0].column_widths_hwpunit[0],
            CASES[0].column_widths_hwpunit[1]
        );
        assert!(CASES[0].table_output);
        assert!(!CASES[1].table_output);
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
    fn selected_table_exterior_detects_nonselected_change() {
        let target = concat!(
            r#"<hs:sec xmlns:hs="urn:s" xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">"#,
            r#"<hp:p><hp:run><hp:t>KEEP</hp:t><hp:tbl id="1"/></hp:run></hp:p>"#,
            r#"<hp:p><hp:run><hp:tbl id="2"/></hp:run></hp:p></hs:sec>"#,
        );
        let selected_changed = target.replace("id=\"2\"", "id=\"3\"");
        require_selected_table_exterior_equal(target.as_bytes(), selected_changed.as_bytes(), 1)
            .unwrap();
        let outside_changed = target.replace("KEEP", "CHANGED");
        assert!(
            require_selected_table_exterior_equal(target.as_bytes(), outside_changed.as_bytes(), 1)
                .is_err()
        );
    }
}
