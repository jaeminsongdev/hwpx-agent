use std::collections::{BTreeMap, BTreeSet};
use std::env;
use std::error::Error;
use std::fs;
use std::io::Cursor;
use std::path::{Path, PathBuf};

use domain_ir::{LogicalId, TableRulingLimits};
use hwpx_package::{
    BoundedZipReader, HANCOM_2020_PARAGRAPH_NAMESPACE, PackageGraph, PackageGraphLimits,
    PackageLimits, PreservingXmlDocument, TableLayoutHwpxLimits, TableLayoutHwpxReader,
    TableRulingHwpxBinding, TableRulingHwpxCellBinding, TableSplitHwpxLimits,
    TableSplitHwpxReadback, TableSplitHwpxReader, XmlByteSpan, XmlElementToken,
};
use serde::Deserialize;
use sha2::{Digest as _, Sha256};

const MAX_FILE_BYTES: u64 = 8 * 1024 * 1024;
const MAX_MANIFEST_BYTES: u64 = 256 * 1024;
const EXPECTED_MANIFEST_SHA256: &str =
    "f7c25806e82e2f809d6d6dfde0fc2620493a5cf237fbb9913c9782713db33c25";
const EXPECTED_ANCESTOR_SHA256: &str =
    "6514a69b8c8c9d320bc19a032b16f2b71d59a38f164c690bc9e3d320a93320e5";
const EXPECTED_TARGET_SHA256: [&str; 2] = [
    "8bab0736c9deb47fa577a68b40223087efcbee3560c700dc97456f777c83e9c3",
    "a5a7a475d33fc82c729c2a39b028925a4bb4d528161f36c040d4d3c6204eeecb",
];
const EXPECTED_ORACLE_SHA256: [&str; 2] = [
    "7229ccccd1bfb98dfa3d6a57f4575033718d3644c785103407d8e17795d8db67",
    "28fddc01a7d224f4d79b15e960483a7c754c2acbde518505148364b75c086c95",
];
const EXPECTED_CACHE_COUNT: [usize; 2] = [13, 11];
const EXPECTED_CACHE_SHA256: [&str; 2] = [
    "6c2aed93776177cfcd1b8935b2417f84c51bce0088d0ebcc8be24171759bbcc2",
    "683f76ab4736256762f04ca371ac0206431d3f496e17b607b2daefa20358d516",
];
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
    oracle_paths: [PathBuf; 2],
    expected_oracle_sha256: [String; 2],
}

impl Arguments {
    fn parse() -> Result<Self, Box<dyn Error>> {
        let mut values = env::args_os();
        let _program = values.next();
        let manifest = path_argument(&mut values, "fixture manifest")?;
        let expected_manifest_sha256 = string_argument(&mut values, "manifest SHA-256")?;
        let oracle_010 = path_argument(&mut values, "TABLE-010 oracle HWPX")?;
        let oracle_010_sha256 = string_argument(&mut values, "TABLE-010 oracle SHA-256")?;
        let oracle_011 = path_argument(&mut values, "TABLE-011 oracle HWPX")?;
        let oracle_011_sha256 = string_argument(&mut values, "TABLE-011 oracle SHA-256")?;
        let result = Self {
            manifest,
            expected_manifest_sha256,
            oracle_paths: [oracle_010, oracle_011],
            expected_oracle_sha256: [oracle_010_sha256, oracle_011_sha256],
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
    target_state_sha256: Vec<String>,
    target_grid_sha256: Vec<String>,
    table_count: usize,
    rows_per_table: Vec<u32>,
    columns_per_table: Vec<u32>,
    master_cell_count: usize,
    payload_block_count: usize,
    topology_delta_count: usize,
    separator_paragraph_count: usize,
    bindings: Vec<BindingManifest>,
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

fn main() -> Result<(), Box<dyn Error>> {
    run(&Arguments::parse()?)
}

#[allow(clippy::too_many_lines)]
fn run(arguments: &Arguments) -> Result<(), Box<dyn Error>> {
    require_lower_sha256(&arguments.expected_manifest_sha256)?;
    if arguments.expected_manifest_sha256 != EXPECTED_MANIFEST_SHA256 {
        return Err("exact partition fixture manifest identity differs".into());
    }
    for (actual, expected) in arguments
        .expected_oracle_sha256
        .iter()
        .zip(EXPECTED_ORACLE_SHA256)
    {
        require_lower_sha256(actual)?;
        if actual != expected {
            return Err("exact partition oracle identity differs".into());
        }
    }
    if arguments.oracle_paths[0] == arguments.oracle_paths[1] {
        return Err("oracle paths must differ".into());
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
        let (stripped, cache_sha256, cache_count) = strip_renderer_caches(&oracle.section)?;
        if stripped != target.section
            || cache_count != EXPECTED_CACHE_COUNT[index]
            || hex(cache_sha256) != EXPECTED_CACHE_SHA256[index]
        {
            return Err(format!("{} renderer-cache boundary differs", case.feature_id).into());
        }
        let semantic_oracle = PackageInspection {
            parts: BTreeMap::new(),
            header: oracle.header.clone(),
            section: stripped,
        };
        validate_case_readback(case, &target, &semantic_oracle)?;
        cache_counts.push(cache_count);
        cache_digests.push(hex(cache_sha256));
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
            "schema=hwpx-agent.p06-09-table-partition-target-oracle/v1 state=pass ",
            "feature_ids=TABLE-010,TABLE-011 target_sha256={},{} oracle_sha256={},{} ",
            "renderer_cache_count={},{} renderer_cache_sha256={},{}"
        ),
        EXPECTED_TARGET_SHA256[0],
        EXPECTED_TARGET_SHA256[1],
        EXPECTED_ORACLE_SHA256[0],
        EXPECTED_ORACLE_SHA256[1],
        cache_counts[0],
        cache_counts[1],
        cache_digests[0],
        cache_digests[1],
    );
    Ok(())
}

fn validate_manifest(manifest: &Manifest) -> Result<(), Box<dyn Error>> {
    if manifest.schema_version != "hwpx-agent.p06-09-table-partition-target-fixture/v1"
        || manifest.source_ancestor_sha256 != EXPECTED_ANCESTOR_SHA256
        || manifest.prepared_source_section_sha256
            != "ca1bcc0827d950a2d6517e1229b7c83f3dc3267fb44386295d98a4cb497b70cd"
        || manifest.cases.len() != 2
        || manifest.actual_hangul_2020
        || manifest.render != "not_run"
        || manifest.automation != "not_run"
        || manifest.differential != "not_run"
    {
        return Err("partition fixture manifest boundary differs".into());
    }
    let expected = [
        (
            "table-010-split-table-4x2",
            "TABLE-010",
            "table.split_table",
            "table-010-split-table-4x2.hwpx",
            2,
            vec![2, 2],
            vec![2, 2],
            2,
        ),
        (
            "table-011-join-table-4x2",
            "TABLE-011",
            "table.join_table",
            "table-011-join-table-4x2.hwpx",
            1,
            vec![4],
            vec![2],
            1,
        ),
    ];
    for (index, (case, expected)) in manifest.cases.iter().zip(expected).enumerate() {
        let digests = std::iter::once(&case.sha256)
            .chain([
                &case.target_header_sha256,
                &case.target_section_sha256,
                &case.request_sha256,
                &case.plan_sha256,
                &case.source_state_sha256,
            ])
            .chain(case.target_state_sha256.iter())
            .chain(case.target_grid_sha256.iter());
        if case.case_id != expected.0
            || case.feature_id != expected.1
            || case.capability_id != expected.2
            || case.file != expected.3
            || case.sha256 != EXPECTED_TARGET_SHA256[index]
            || case.table_count != expected.4
            || case.rows_per_table != expected.5
            || case.columns_per_table != expected.6
            || case.bindings.len() != expected.7
            || case.target_state_sha256.len() != expected.7
            || case.target_grid_sha256.len() != expected.7
            || case.master_cell_count != 8
            || case.payload_block_count != 8
            || case.topology_delta_count != 1
            || case.separator_paragraph_count != 1
            || digests.into_iter().any(|value| !is_lower_sha256(value))
        {
            return Err(format!("{} fixture manifest semantics differ", case.feature_id).into());
        }
        let mut identities = BTreeSet::new();
        let mut payload_count = 0;
        for binding in &case.bindings {
            if binding.table_id.is_empty()
                || !identities.insert(binding.table_id.as_str())
                || binding.row_boundaries_hwpunit.first() != Some(&0)
                || binding.column_boundaries_hwpunit != [0, 18_000, 36_000]
            {
                return Err("fixture table binding differs".into());
            }
            for cell in &binding.cells {
                if cell.master_cell_id.is_empty()
                    || !identities.insert(cell.master_cell_id.as_str())
                    || cell.payload_block_ids.len() != 1
                    || cell.payload_block_ids[0].is_empty()
                    || !identities.insert(cell.payload_block_ids[0].as_str())
                {
                    return Err("fixture cell binding differs".into());
                }
                payload_count += 1;
            }
        }
        if payload_count != 8 {
            return Err("fixture payload binding cardinality differs".into());
        }
    }
    Ok(())
}

fn validate_case_readback(
    case: &ManifestCase,
    target: &PackageInspection,
    oracle: &PackageInspection,
) -> Result<(), Box<dyn Error>> {
    if hex(Sha256::digest(&target.header).into()) != case.target_header_sha256
        || hex(Sha256::digest(&target.section).into()) != case.target_section_sha256
    {
        return Err("target parts differ from fixture manifest".into());
    }
    let limits = TableSplitHwpxLimits::default();
    if TableLayoutHwpxReader::count_in_section(&target.section, TableLayoutHwpxLimits::default())?
        != case.table_count
        || TableLayoutHwpxReader::count_in_section(
            &oracle.section,
            TableLayoutHwpxLimits::default(),
        )? != case.table_count
    {
        return Err("target table count differs".into());
    }
    let mut master_cells = 0;
    let mut payload_blocks = 0;
    for (ordinal, binding) in case.bindings.iter().enumerate() {
        let binding = binding_from_manifest(binding)?;
        let target_readback = TableSplitHwpxReader::read_existing(
            &target.header,
            &target.section,
            ordinal,
            &binding,
            limits,
        )
        .map_err(|error| format!("{} target table {ordinal}: {error:?}", case.feature_id))?;
        let oracle_readback = TableSplitHwpxReader::read_existing(
            &oracle.header,
            &oracle.section,
            ordinal,
            &binding,
            limits,
        )
        .map_err(|error| format!("{} oracle table {ordinal}: {error:?}", case.feature_id))?;
        require_typed_equal(&target_readback, &oracle_readback)?;
        if target_readback.ruling.grid.rows() != case.rows_per_table[ordinal]
            || target_readback.ruling.grid.columns() != case.columns_per_table[ordinal]
            || hex(target_readback.ruling.grid.canonical_sha256()?)
                != case.target_grid_sha256[ordinal]
            || hex(target_readback
                .ruling
                .state
                .canonical_sha256(TableRulingLimits::default())?)
                != case.target_state_sha256[ordinal]
        {
            return Err("typed target state differs from fixture manifest".into());
        }
        master_cells += target_readback.ruling.grid.master_cell_count();
        payload_blocks += target_readback.ruling.payload_block_count;
    }
    if master_cells != case.master_cell_count
        || payload_blocks != case.payload_block_count
        || case
            .bindings
            .iter()
            .map(|binding| binding.cells.len())
            .sum::<usize>()
            != master_cells
    {
        return Err("typed target cardinality differs".into());
    }
    Ok(())
}

fn require_typed_equal(
    target: &TableSplitHwpxReadback,
    oracle: &TableSplitHwpxReadback,
) -> Result<(), Box<dyn Error>> {
    if target.ruling.grid != oracle.ruling.grid
        || target.ruling.state != oracle.ruling.state
        || target.partition != oracle.partition
        || target.pagination != oracle.pagination
        || target.ruling.payload_block_count != oracle.ruling.payload_block_count
        || target.ruling.formula_count != 0
        || oracle.ruling.formula_count != 0
    {
        return Err("actual Hangul typed partition state differs".into());
    }
    Ok(())
}

fn binding_from_manifest(
    value: &BindingManifest,
) -> Result<TableRulingHwpxBinding, Box<dyn Error>> {
    Ok(TableRulingHwpxBinding {
        table_id: LogicalId::parse(value.table_id.clone())?,
        row_boundaries_hwpunit: value.row_boundaries_hwpunit.clone(),
        column_boundaries_hwpunit: value.column_boundaries_hwpunit.clone(),
        cells: value
            .cells
            .iter()
            .map(|cell| {
                Ok(TableRulingHwpxCellBinding {
                    master_cell_id: LogicalId::parse(cell.master_cell_id.clone())?,
                    payload_block_ids: cell
                        .payload_block_ids
                        .iter()
                        .map(|identity| LogicalId::parse(identity.clone()))
                        .collect::<Result<Vec<_>, _>>()?,
                })
            })
            .collect::<Result<Vec<_>, Box<dyn Error>>>()?,
    })
}

fn inspect_package(bytes: &[u8]) -> Result<PackageInspection, Box<dyn Error>> {
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    if graph.parts.len() != reader.entries().len() || reader.entries().len() != 11 {
        return Err("package graph or part cardinality differs".into());
    }
    let mut parts = BTreeMap::new();
    for entry in reader.entries().to_vec() {
        let path = entry.path.as_str().to_owned();
        if parts
            .insert(path, reader.read_entry(entry.index)?)
            .is_some()
        {
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
    if target.parts.keys().ne(oracle.parts.keys()) {
        return Err("actual Hangul package part set differs".into());
    }
    for path in IMMUTABLE_PARTS {
        if target.parts.get(path) != oracle.parts.get(path) {
            return Err(format!("actual Hangul immutable part differs: {path}").into());
        }
    }
    Ok(())
}

type RendererCacheStrip = (Vec<u8>, [u8; 32], usize);

fn strip_renderer_caches(section: &[u8]) -> Result<RendererCacheStrip, Box<dyn Error>> {
    let document = PreservingXmlDocument::parse(section)?;
    let arrays = document
        .elements()
        .iter()
        .enumerate()
        .filter(|(_, element)| has_name(element, "linesegarray"))
        .map(|(index, _)| index)
        .collect::<Vec<_>>();
    let mut spans = Vec::new();
    let mut digest = Sha256::new();
    for array in arrays.iter().copied() {
        let element = document
            .elements()
            .get(array)
            .ok_or("cache array missing")?;
        if !element.attributes().is_empty()
            || element
                .parent()
                .and_then(|parent| document.elements().get(parent))
                .is_none_or(|parent| !has_name(parent, "p"))
        {
            return Err("renderer cache array shape differs".into());
        }
        let child = element.first_child().ok_or("cache segment missing")?;
        if element.last_child() != Some(child) {
            return Err("renderer cache segment cardinality differs".into());
        }
        let segment = document
            .elements()
            .get(child)
            .ok_or("cache segment missing")?;
        let names = segment
            .attributes()
            .iter()
            .filter(|attribute| !attribute.is_namespace_declaration())
            .map(|attribute| attribute.name().local_name())
            .collect::<BTreeSet<_>>();
        let expected_names = [
            "textpos",
            "vertpos",
            "vertsize",
            "textheight",
            "baseline",
            "spacing",
            "horzpos",
            "horzsize",
            "flags",
        ]
        .into_iter()
        .collect::<BTreeSet<_>>();
        if !has_name(segment, "lineseg")
            || !segment.is_empty()
            || segment.attributes().len() != 9
            || names != expected_names
        {
            return Err("renderer cache segment shape differs".into());
        }
        let span = element.outer_span().ok_or("cache span missing")?;
        let raw = section
            .get(span.start()..span.end())
            .ok_or("cache span outside section")?;
        digest.update(raw);
        spans.push(span);
    }
    let count = spans.len();
    Ok((
        strip_spans(section, &mut spans)?,
        digest.finalize().into(),
        count,
    ))
}

fn strip_spans(section: &[u8], spans: &mut [XmlByteSpan]) -> Result<Vec<u8>, Box<dyn Error>> {
    spans.sort_by_key(|span| span.start());
    let removed = spans.iter().try_fold(0_usize, |total, span| {
        total
            .checked_add(span.end().checked_sub(span.start()).ok_or("invalid span")?)
            .ok_or("cache size overflow")
    })?;
    let mut output = Vec::new();
    output.try_reserve_exact(
        section
            .len()
            .checked_sub(removed)
            .ok_or("cache size underflow")?,
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
    if u64::try_from(bytes.len())? != metadata.len() {
        return Err("input changed while being read".into());
    }
    Ok(bytes)
}

fn require_digest(bytes: &[u8], expected: &str, label: &str) -> Result<(), Box<dyn Error>> {
    require_lower_sha256(expected)?;
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

fn hex(bytes: [u8; 32]) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let mut output = String::with_capacity(64);
    for byte in bytes {
        output.push(char::from(DIGITS[usize::from(byte >> 4)]));
        output.push(char::from(DIGITS[usize::from(byte & 0x0f)]));
    }
    output
}
