use std::collections::{BTreeMap, BTreeSet};
use std::env;
use std::error::Error;
use std::fs;
use std::io::Cursor;
use std::path::{Path, PathBuf};

use domain_ir::{LogicalId, TableRulingLimits};
use hwpx_package::{
    BoundedZipReader, PackageLimits, TableRulingHwpxBinding, TableRulingHwpxCellBinding,
    TableStructureHwpxLimits, TableStructureHwpxReadback, TableStructureHwpxReader,
};
use serde::Deserialize;
use sha2::{Digest as _, Sha256};

const MAX_FILE_BYTES: u64 = 8 * 1024 * 1024;
const MAX_MANIFEST_BYTES: u64 = 256 * 1024;
const EXPECTED_MANIFEST_SHA256: &str =
    "4f02027b798d0c8e3c805ac9be766280421b30a941ed2fc49cfede16b1f4fa09";
const EXPECTED_ANCESTOR_SHA256: &str =
    "6514a69b8c8c9d320bc19a032b16f2b71d59a38f164c690bc9e3d320a93320e5";
const EXPECTED_PREPARED_SECTION_SHA256: &str =
    "ad25a9853990d2e249f3a26c8d87aa4cd3717bf40ecd795de9667af45ee47dd8";
const EXPECTED_TARGET_SHA256: [&str; 4] = [
    "0459a05b8543edb2e05c9c0117f76df999c8543bad255d06d26d4b3b57388252",
    "69be89ead6a7582a80f4d98b17a87ac3908ba9e6e8d02e43e4ddcce3a615fa21",
    "abc5fd06b5f17dbbb201630b3a38a1e77bd65830f50062a7fd468cdfdb0edcea",
    "5c6669b0682f94682b3fc132cf4fc101d444cc93b7284ffb1fee0ef68ab6bb0e",
];
const EXPECTED_ORACLE_SHA256: [&str; 4] = [
    "04f7910b122ded578975f379a7053b3dc62a0a5b73c2ea40505374500e665a0c",
    "1f9c5e40a164d59715547e22b858690504b3bb9895fb6a0e57d887842fe35add",
    "c449bb856589c78a7c80b93bc700e407cff85f3744dd266787bcf03a3fa3b0fe",
    "bd0ffb108bf35289c742bd400a74d3d95f0a69574f3279c3b363f8475a38dce1",
];
const EXPECTED_CACHE_COUNT: [usize; 4] = [15, 15, 9, 9];
const EXPECTED_CACHE_SHA256: [&str; 4] = [
    "44d9a1d66c172f530f561438c38c67b6530bf994332fa4ccddd5c84982b434ad",
    "23eb6840733c3b4c748f9192ee54b9ffb88f04c85ab2eff182bb9657f347adda",
    "a5491d59a064546751144e7d9df920737505cc0698e0838acb59968aa2dd05a4",
    "71928c8f51a481142c90e09243c511df8206180c297dfd656725653c13b7d927",
];
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
    oracle_paths: [PathBuf; 4],
    expected_oracle_sha256: [String; 4],
}

impl Arguments {
    fn parse() -> Result<Self, Box<dyn Error>> {
        let mut values = env::args_os();
        let _program = values.next();
        let manifest = path_argument(&mut values, "fixture manifest")?;
        let expected_manifest_sha256 = string_argument(&mut values, "manifest SHA-256")?;
        let mut oracle_paths = Vec::new();
        let mut expected_oracle_sha256 = Vec::new();
        for index in 0..4 {
            oracle_paths.push(path_argument(
                &mut values,
                &format!("TABLE-01{} oracle HWPX", index + 2),
            )?);
            expected_oracle_sha256.push(string_argument(
                &mut values,
                &format!("TABLE-01{} oracle SHA-256", index + 2),
            )?);
        }
        if values.next().is_some() {
            return Err("too many arguments".into());
        }
        Ok(Self {
            manifest,
            expected_manifest_sha256,
            oracle_paths: oracle_paths.try_into().map_err(|_| "oracle path count")?,
            expected_oracle_sha256: expected_oracle_sha256
                .try_into()
                .map_err(|_| "oracle digest count")?,
        })
    }
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Manifest {
    schema_version: String,
    source_ancestor_sha256: String,
    prepared_source_section_sha256: String,
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
    if arguments.expected_manifest_sha256 != EXPECTED_MANIFEST_SHA256 {
        return Err("exact structure fixture manifest identity differs".into());
    }
    let unique_paths = arguments.oracle_paths.iter().collect::<BTreeSet<_>>();
    if unique_paths.len() != 4 {
        return Err("oracle paths must be distinct".into());
    }
    for (actual, expected) in arguments
        .expected_oracle_sha256
        .iter()
        .zip(EXPECTED_ORACLE_SHA256)
    {
        require_lower_sha256(actual)?;
        if actual != expected {
            return Err("exact structure oracle identity differs".into());
        }
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
    for (index, ((case, oracle_path), expected_oracle_sha256)) in manifest
        .cases
        .iter()
        .zip(arguments.oracle_paths.iter())
        .zip(arguments.expected_oracle_sha256.iter())
        .enumerate()
    {
        let target_path = parent.join(&case.file);
        if &target_path == oracle_path {
            return Err("target and oracle paths must differ".into());
        }
        let target_bytes = read_bounded_file(&target_path, MAX_FILE_BYTES)?;
        let oracle_bytes = read_bounded_file(oracle_path, MAX_FILE_BYTES)?;
        require_digest(&target_bytes, EXPECTED_TARGET_SHA256[index], "target")?;
        require_digest(&oracle_bytes, expected_oracle_sha256, "oracle")?;
        let target = inspect_package(&target_bytes)?;
        let oracle = inspect_package(&oracle_bytes)?;
        require_package_boundary(&target, &oracle)?;
        let stripped = strip_renderer_caches(&oracle.section)?;
        if stripped.section != target.section
            || stripped.count != EXPECTED_CACHE_COUNT[index]
            || hex(stripped.sha256) != EXPECTED_CACHE_SHA256[index]
        {
            return Err(format!("{} renderer-cache boundary differs", case.feature_id).into());
        }
        validate_case_readback(case, &target, &oracle.header, &stripped.section)?;
        cache_counts.push(stripped.count);
        cache_digests.push(hex(stripped.sha256));
        require_digest(
            &read_bounded_file(&target_path, MAX_FILE_BYTES)?,
            EXPECTED_TARGET_SHA256[index],
            "target recheck",
        )?;
        require_digest(
            &read_bounded_file(oracle_path, MAX_FILE_BYTES)?,
            expected_oracle_sha256,
            "oracle recheck",
        )?;
    }
    require_digest(
        &read_bounded_file(&arguments.manifest, MAX_MANIFEST_BYTES)?,
        EXPECTED_MANIFEST_SHA256,
        "manifest recheck",
    )?;
    println!(
        concat!(
            "schema=hwpx-agent.p06-09-table-structure-target-oracle/v1 state=pass ",
            "feature_ids=TABLE-012,TABLE-013,TABLE-014,TABLE-015 ",
            "renderer_cache_count={},{},{},{} renderer_cache_sha256={},{},{},{}"
        ),
        cache_counts[0],
        cache_counts[1],
        cache_counts[2],
        cache_counts[3],
        cache_digests[0],
        cache_digests[1],
        cache_digests[2],
        cache_digests[3],
    );
    Ok(())
}

#[allow(clippy::too_many_lines)]
fn validate_manifest(manifest: &Manifest) -> Result<(), Box<dyn Error>> {
    if manifest.schema_version != "hwpx-agent.p06-09-table-structure-target-fixture/v1"
        || manifest.source_ancestor_sha256 != EXPECTED_ANCESTOR_SHA256
        || manifest.prepared_source_section_sha256 != EXPECTED_PREPARED_SECTION_SHA256
        || manifest.cases.len() != 4
        || manifest.actual_hangul_2020
        || manifest.render != "not_run"
        || manifest.automation != "not_run"
        || manifest.differential != "not_run"
    {
        return Err("structure fixture manifest boundary differs".into());
    }
    let expected = [
        (
            "table-012-insert-row-3x3",
            "TABLE-012",
            "table.insert_rows",
            "table-012-insert-row-3x3.hwpx",
            4,
            3,
            12,
            9,
            3,
            0,
        ),
        (
            "table-013-insert-column-3x3",
            "TABLE-013",
            "table.insert_columns",
            "table-013-insert-column-3x3.hwpx",
            3,
            4,
            12,
            9,
            3,
            0,
        ),
        (
            "table-014-delete-row-3x3",
            "TABLE-014",
            "table.delete_rows",
            "table-014-delete-row-3x3.hwpx",
            2,
            3,
            6,
            6,
            0,
            3,
        ),
        (
            "table-015-delete-column-3x3",
            "TABLE-015",
            "table.delete_columns",
            "table-015-delete-column-3x3.hwpx",
            3,
            2,
            6,
            6,
            0,
            3,
        ),
    ];
    let mut source_state = None;
    let mut source_grid = None;
    for (index, (case, expected)) in manifest.cases.iter().zip(expected).enumerate() {
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
        ];
        if case.case_id != expected.0
            || case.feature_id != expected.1
            || case.capability_id != expected.2
            || case.file != expected.3
            || case.sha256 != EXPECTED_TARGET_SHA256[index]
            || case.rows != expected.4
            || case.columns != expected.5
            || case.master_cell_count != expected.6
            || case.payload_block_count != expected.7
            || case.inserted_master_cell_count != expected.8
            || case.deleted_master_cell_count != expected.9
            || case.formula_count != 0
            || case.page_split != "cell"
            || digests.into_iter().any(|value| !is_lower_sha256(value))
        {
            return Err(format!("{} fixture manifest semantics differ", case.feature_id).into());
        }
        if source_state
            .replace(case.source_state_sha256.as_str())
            .is_some_and(|value| value != case.source_state_sha256)
            || source_grid
                .replace(case.source_grid_sha256.as_str())
                .is_some_and(|value| value != case.source_grid_sha256)
        {
            return Err("fixture cases do not share one exact source".into());
        }
        validate_binding(case)?;
    }
    Ok(())
}

fn validate_binding(case: &ManifestCase) -> Result<(), Box<dyn Error>> {
    if case.binding.table_id.is_empty()
        || case.binding.row_boundaries_hwpunit.first() != Some(&0)
        || case.binding.column_boundaries_hwpunit.first() != Some(&0)
        || case.binding.row_boundaries_hwpunit.len()
            != usize::try_from(case.rows)?
                .checked_add(1)
                .ok_or("row overflow")?
        || case.binding.column_boundaries_hwpunit.len()
            != usize::try_from(case.columns)?
                .checked_add(1)
                .ok_or("column overflow")?
        || case.binding.cells.len() != case.master_cell_count
    {
        return Err("fixture table binding differs".into());
    }
    let mut identities = BTreeSet::new();
    let mut payload_count = 0_usize;
    for cell in &case.binding.cells {
        if cell.master_cell_id.is_empty() || !identities.insert(cell.master_cell_id.as_str()) {
            return Err("fixture cell identity differs".into());
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
        return Err("fixture payload binding cardinality differs".into());
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
    let limits = TableStructureHwpxLimits::default();
    let target_readback = TableStructureHwpxReader::read_existing(
        &target.header,
        &target.section,
        0,
        &binding,
        limits,
    )?;
    let oracle_readback = TableStructureHwpxReader::read_existing(
        oracle_header,
        stripped_oracle_section,
        0,
        &binding,
        limits,
    )?;
    require_typed_equal(&target_readback, &oracle_readback)?;
    if target_readback.ruling.grid.rows() != case.rows
        || target_readback.ruling.grid.columns() != case.columns
        || target_readback.ruling.grid.master_cell_count() != case.master_cell_count
        || target_readback.ruling.payload_block_count != case.payload_block_count
        || target_readback.ruling.formula_count != case.formula_count
        || target_readback.pagination.repeat_header_rows != 0
        || target_readback.pagination.caption.is_some()
        || hex(target_readback.ruling.grid.canonical_sha256()?) != case.target_grid_sha256
        || hex(target_readback
            .ruling
            .state
            .canonical_sha256(TableRulingLimits::default())?)
            != case.target_state_sha256
    {
        return Err("typed target state differs from fixture manifest".into());
    }
    Ok(())
}

fn require_typed_equal(
    target: &TableStructureHwpxReadback,
    oracle: &TableStructureHwpxReadback,
) -> Result<(), Box<dyn Error>> {
    if target.ruling.grid != oracle.ruling.grid
        || target.ruling.state != oracle.ruling.state
        || target.pagination != oracle.pagination
        || target.wrapper_paragraph_id != oracle.wrapper_paragraph_id
        || target.native_table_id != oracle.native_table_id
        || target.ruling.payload_block_count != oracle.ruling.payload_block_count
        || target.ruling.formula_count != 0
        || oracle.ruling.formula_count != 0
    {
        return Err("actual Hangul typed structure state differs".into());
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
