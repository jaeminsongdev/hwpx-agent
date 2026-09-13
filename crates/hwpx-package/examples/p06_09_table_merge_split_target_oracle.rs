use std::collections::{BTreeMap, BTreeSet};
use std::env;
use std::error::Error;
use std::fs;
use std::io::Cursor;
use std::path::{Path, PathBuf};

use domain_ir::{LogicalId, TableRulingLimits};
use hwpx_package::{
    BoundedZipReader, PackageLimits, TableMergeSplitHwpxLimits, TableMergeSplitHwpxReader,
    TableRulingHwpxBinding, TableRulingHwpxCellBinding,
};
use serde::Deserialize;
use sha2::{Digest as _, Sha256};

const MAX_FILE_BYTES: u64 = 8 * 1024 * 1024;
const MAX_MANIFEST_BYTES: u64 = 256 * 1024;
const EXPECTED_ANCESTOR_SHA256: &str =
    "6514a69b8c8c9d320bc19a032b16f2b71d59a38f164c690bc9e3d320a93320e5";
const IMMUTABLE_PARTS: [&str; 5] = [
    "mimetype",
    "version.xml",
    "META-INF/container.rdf",
    "META-INF/container.xml",
    "META-INF/manifest.xml",
];
const EXPECTED_PARTS: [&str; 11] = [
    "mimetype",
    "version.xml",
    "Contents/header.xml",
    "Contents/section0.xml",
    "Preview/PrvText.txt",
    "settings.xml",
    "Preview/PrvImage.png",
    "META-INF/container.rdf",
    "Contents/content.hpf",
    "META-INF/container.xml",
    "META-INF/manifest.xml",
];

struct Arguments {
    manifest: PathBuf,
    expected_manifest_sha256: String,
    oracle_paths: [PathBuf; 2],
    expected_oracle_sha256: [String; 2],
}

impl Arguments {
    fn parse() -> Result<Self, Box<dyn Error>> {
        let mut values = env::args_os();
        let _program = values.next();
        let manifest = path_argument(&mut values, "fixture manifest")?;
        let expected_manifest_sha256 = string_argument(&mut values, "manifest SHA-256")?;
        let oracle_016 = path_argument(&mut values, "TABLE-016 oracle HWPX")?;
        let oracle_016_sha256 = string_argument(&mut values, "TABLE-016 oracle SHA-256")?;
        let oracle_017 = path_argument(&mut values, "TABLE-017 oracle HWPX")?;
        let oracle_017_sha256 = string_argument(&mut values, "TABLE-017 oracle SHA-256")?;
        if values.next().is_some() {
            return Err("too many arguments".into());
        }
        Ok(Self {
            manifest,
            expected_manifest_sha256,
            oracle_paths: [oracle_016, oracle_017],
            expected_oracle_sha256: [oracle_016_sha256, oracle_017_sha256],
        })
    }
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Manifest {
    schema_version: String,
    source_ancestor_sha256: String,
    prepared_source_section_sha256: String,
    merged_seed_section_sha256: String,
    cases: Vec<ManifestCase>,
    inverse_roundtrip_exact: bool,
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
    operation: String,
    file: String,
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
    page_split: String,
    binding: BindingManifest,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct BindingManifest {
    table_id: String,
    row_boundaries_hwpunit: Vec<u32>,
    column_boundaries_hwpunit: Vec<u32>,
    cells: Vec<CellBindingManifest>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct CellBindingManifest {
    master_cell_id: String,
    payload_block_ids: Vec<String>,
}

struct PackageInspection {
    parts: BTreeMap<String, Vec<u8>>,
    header: Vec<u8>,
    section: Vec<u8>,
}

struct RendererCacheStrip {
    section: Vec<u8>,
    sha256: [u8; 32],
    count: usize,
}

fn main() -> Result<(), Box<dyn Error>> {
    run(&Arguments::parse()?)
}

fn run(arguments: &Arguments) -> Result<(), Box<dyn Error>> {
    require_lower_sha256(&arguments.expected_manifest_sha256)?;
    for digest in &arguments.expected_oracle_sha256 {
        require_lower_sha256(digest)?;
    }
    if arguments.oracle_paths[0] == arguments.oracle_paths[1] {
        return Err("oracle paths must be distinct".into());
    }
    let manifest_bytes = read_bounded_file(&arguments.manifest, MAX_MANIFEST_BYTES)?;
    require_digest(
        &manifest_bytes,
        &arguments.expected_manifest_sha256,
        "manifest",
    )?;
    let manifest: Manifest = serde_json::from_slice(&manifest_bytes)?;
    validate_manifest(&manifest)?;
    let parent = arguments
        .manifest
        .parent()
        .ok_or("fixture manifest has no parent")?;
    let mut cache_counts = Vec::new();
    let mut cache_digests = Vec::new();
    for ((case, oracle_path), oracle_sha256) in manifest
        .cases
        .iter()
        .zip(&arguments.oracle_paths)
        .zip(&arguments.expected_oracle_sha256)
    {
        let target_path = parent.join(&case.file);
        if target_path == *oracle_path {
            return Err("target and oracle paths must be distinct".into());
        }
        let target_bytes = read_bounded_file(&target_path, MAX_FILE_BYTES)?;
        let oracle_bytes = read_bounded_file(oracle_path, MAX_FILE_BYTES)?;
        require_digest(&target_bytes, &case.sha256, "target")?;
        require_digest(&oracle_bytes, oracle_sha256, "oracle")?;
        let target = inspect_package(&target_bytes)?;
        let oracle = inspect_package(&oracle_bytes)?;
        require_package_boundary(&target, &oracle)?;
        let stripped = strip_renderer_caches(&oracle.section)?;
        if stripped.count == 0 || stripped.section != target.section {
            return Err(format!("{} renderer-cache boundary differs", case.feature_id).into());
        }
        validate_case_readback(case, &target, &oracle.header, &stripped.section)?;
        cache_counts.push(stripped.count);
        cache_digests.push(hex(stripped.sha256));
        require_digest(
            &read_bounded_file(&target_path, MAX_FILE_BYTES)?,
            &case.sha256,
            "target recheck",
        )?;
        require_digest(
            &read_bounded_file(oracle_path, MAX_FILE_BYTES)?,
            oracle_sha256,
            "oracle recheck",
        )?;
    }
    require_digest(
        &read_bounded_file(&arguments.manifest, MAX_MANIFEST_BYTES)?,
        &arguments.expected_manifest_sha256,
        "manifest recheck",
    )?;
    println!(
        concat!(
            "schema=hwpx-agent.p06-09-table-merge-split-target-oracle/v1 state=pass ",
            "feature_ids=TABLE-016,TABLE-017 inverse_roundtrip_exact=true ",
            "renderer_cache_count={},{} renderer_cache_sha256={},{}"
        ),
        cache_counts[0], cache_counts[1], cache_digests[0], cache_digests[1]
    );
    Ok(())
}

fn validate_manifest(manifest: &Manifest) -> Result<(), Box<dyn Error>> {
    if manifest.schema_version != "hwpx-agent.p06-09-table-merge-split-target-fixture/v1"
        || manifest.source_ancestor_sha256 != EXPECTED_ANCESTOR_SHA256
        || !is_lower_sha256(&manifest.prepared_source_section_sha256)
        || !is_lower_sha256(&manifest.merged_seed_section_sha256)
        || manifest.cases.len() != 2
        || !manifest.inverse_roundtrip_exact
        || manifest.actual_hangul_2020
        || manifest.render != "not_run"
        || manifest.automation != "not_run"
        || manifest.differential != "not_run"
    {
        return Err("fixture manifest identity differs".into());
    }
    let expected = [
        (
            "table-016-split-cells-4x3",
            "TABLE-016",
            "table.split_cell",
            "split",
            "table-016-split-cells-4x3.hwpx",
            9,
            12,
        ),
        (
            "table-017-merge-cells-4x3",
            "TABLE-017",
            "table.merge_cells",
            "merge",
            "table-017-merge-cells-4x3.hwpx",
            12,
            9,
        ),
    ];
    for (case, expected) in manifest.cases.iter().zip(expected) {
        let digests = [
            &case.sha256,
            &case.target_header_sha256,
            &case.target_section_sha256,
            &case.request_sha256,
            &case.plan_sha256,
            &case.source_state_sha256,
            &case.target_state_sha256,
            &case.source_grid_sha256,
            &case.target_grid_sha256,
            &case.source_content_sha256,
            &case.target_content_sha256,
        ];
        if case.case_id != expected.0
            || case.feature_id != expected.1
            || case.capability_id != expected.2
            || case.operation != expected.3
            || case.file != expected.4
            || case.rows != 4
            || case.columns != 3
            || case.source_master_cell_count != expected.5
            || case.target_master_cell_count != expected.6
            || case.topology_delta_count != 3
            || case.payload_block_count != 9
            || case.discarded_content_block_count != 0
            || case.added_border_fill_count != 0
            || case.formula_count != 0
            || case.page_split != "cell"
            || digests.into_iter().any(|value| !is_lower_sha256(value))
        {
            return Err(format!("{} fixture semantics differ", case.feature_id).into());
        }
        validate_binding(case)?;
    }
    let split = &manifest.cases[0];
    let merge = &manifest.cases[1];
    if split.source_state_sha256 != merge.target_state_sha256
        || split.target_state_sha256 != merge.source_state_sha256
        || split.source_grid_sha256 != merge.target_grid_sha256
        || split.target_grid_sha256 != merge.source_grid_sha256
        || split.source_content_sha256 != merge.target_content_sha256
        || split.target_content_sha256 != merge.source_content_sha256
    {
        return Err("split/merge inverse manifest binding differs".into());
    }
    Ok(())
}

fn validate_binding(case: &ManifestCase) -> Result<(), Box<dyn Error>> {
    if case.binding.table_id.is_empty()
        || case.binding.row_boundaries_hwpunit != [0, 4_000, 8_000, 12_000, 16_000]
        || case.binding.column_boundaries_hwpunit != [0, 12_000, 24_000, 36_000]
        || case.binding.cells.len() != case.target_master_cell_count
    {
        return Err("fixture table binding differs".into());
    }
    let mut identities = BTreeSet::new();
    let mut payload_count = 0_usize;
    for cell in &case.binding.cells {
        if cell.master_cell_id.is_empty() || !identities.insert(cell.master_cell_id.as_str()) {
            return Err("fixture master identity differs".into());
        }
        payload_count = payload_count
            .checked_add(cell.payload_block_ids.len())
            .ok_or("payload count overflow")?;
        for payload in &cell.payload_block_ids {
            if payload.is_empty() || !identities.insert(payload.as_str()) {
                return Err("fixture payload identity differs".into());
            }
        }
    }
    if payload_count != case.payload_block_count {
        return Err("fixture payload count differs".into());
    }
    Ok(())
}

fn validate_case_readback(
    case: &ManifestCase,
    target: &PackageInspection,
    oracle_header: &[u8],
    stripped_oracle_section: &[u8],
) -> Result<(), Box<dyn Error>> {
    if hex(Sha256::digest(&target.header)) != case.target_header_sha256
        || hex(Sha256::digest(&target.section)) != case.target_section_sha256
    {
        return Err("target parts differ from fixture manifest".into());
    }
    let binding = binding_from_manifest(&case.binding)?;
    let limits = TableMergeSplitHwpxLimits::default();
    let target_readback = TableMergeSplitHwpxReader::read_existing(
        &target.header,
        &target.section,
        0,
        &binding,
        limits,
    )?;
    let oracle_readback = TableMergeSplitHwpxReader::read_existing(
        oracle_header,
        stripped_oracle_section,
        0,
        &binding,
        limits,
    )?;
    if target_readback.ruling.grid != oracle_readback.ruling.grid
        || target_readback.ruling.state != oracle_readback.ruling.state
        || target_readback.content != oracle_readback.content
        || target_readback.content_state_sha256 != oracle_readback.content_state_sha256
        || target_readback.ruling.grid.rows() != case.rows
        || target_readback.ruling.grid.columns() != case.columns
        || target_readback.ruling.grid.master_cell_count() != case.target_master_cell_count
        || target_readback.ruling.payload_block_count != case.payload_block_count
        || target_readback.ruling.formula_count != 0
        || oracle_readback.ruling.formula_count != 0
        || hex(target_readback.ruling.grid.canonical_sha256()?) != case.target_grid_sha256
        || hex(target_readback
            .ruling
            .state
            .canonical_sha256(TableRulingLimits::default())?)
            != case.target_state_sha256
        || hex(target_readback.content_state_sha256) != case.target_content_sha256
    {
        return Err("actual Hangul typed merge/split state differs".into());
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

fn inspect_package(bytes: &[u8]) -> Result<PackageInspection, Box<dyn Error>> {
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let entries = reader.entries().to_vec();
    let mut parts = BTreeMap::new();
    for entry in entries {
        if parts
            .insert(
                entry.path.as_str().to_owned(),
                reader.read_entry(entry.index)?,
            )
            .is_some()
        {
            return Err("duplicate package part".into());
        }
    }
    if parts.keys().map(String::as_str).collect::<BTreeSet<_>>()
        != EXPECTED_PARTS.into_iter().collect::<BTreeSet<_>>()
    {
        return Err("package part inventory differs".into());
    }
    let header = parts
        .get("Contents/header.xml")
        .ok_or("header missing")?
        .clone();
    let section = parts
        .get("Contents/section0.xml")
        .ok_or("section missing")?
        .clone();
    Ok(PackageInspection {
        parts,
        header,
        section,
    })
}

fn require_package_boundary(
    target: &PackageInspection,
    oracle: &PackageInspection,
) -> Result<(), Box<dyn Error>> {
    if target.parts.len() != oracle.parts.len() {
        return Err("package entry count differs".into());
    }
    for path in IMMUTABLE_PARTS {
        if target.parts.get(path) != oracle.parts.get(path) {
            return Err(format!("immutable package part differs: {path}").into());
        }
    }
    Ok(())
}

fn strip_renderer_caches(section: &[u8]) -> Result<RendererCacheStrip, Box<dyn Error>> {
    const OPEN: &[u8] = b"<hp:linesegarray>";
    const CLOSE: &[u8] = b"</hp:linesegarray>";
    let mut output = Vec::new();
    output.try_reserve_exact(section.len())?;
    let mut cache_digest = Sha256::new();
    let mut count = 0_usize;
    let mut cursor = 0_usize;
    while let Some(relative_start) = find_bytes(&section[cursor..], OPEN) {
        let start = cursor
            .checked_add(relative_start)
            .ok_or("cache start overflow")?;
        let content_start = start
            .checked_add(OPEN.len())
            .ok_or("cache content overflow")?;
        let relative_end = find_bytes(&section[content_start..], CLOSE)
            .ok_or("renderer cache close is missing")?;
        let end = content_start
            .checked_add(relative_end)
            .and_then(|value| value.checked_add(CLOSE.len()))
            .ok_or("cache end overflow")?;
        if find_bytes(&section[content_start..end], OPEN).is_some() {
            return Err("nested renderer cache array".into());
        }
        output.extend_from_slice(&section[cursor..start]);
        cache_digest.update(&section[start..end]);
        count = count.checked_add(1).ok_or("cache count overflow")?;
        cursor = end;
    }
    output.extend_from_slice(&section[cursor..]);
    if find_bytes(&output, CLOSE).is_some() || find_bytes(&output, b"<hp:linesegarray ").is_some() {
        return Err("unrecognized renderer cache shape".into());
    }
    Ok(RendererCacheStrip {
        section: output,
        sha256: cache_digest.finalize().into(),
        count,
    })
}

fn find_bytes(haystack: &[u8], needle: &[u8]) -> Option<usize> {
    haystack
        .windows(needle.len())
        .position(|window| window == needle)
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

fn is_lower_sha256(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|byte| matches!(byte, b'0'..=b'9' | b'a'..=b'f'))
}

fn require_lower_sha256(value: &str) -> Result<(), Box<dyn Error>> {
    if !is_lower_sha256(value) {
        return Err("SHA-256 must be lowercase hexadecimal".into());
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
