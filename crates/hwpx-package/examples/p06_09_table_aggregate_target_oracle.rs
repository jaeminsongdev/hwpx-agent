use std::env;
use std::error::Error;
use std::fs;
use std::io::Cursor;
use std::path::{Path, PathBuf};

use domain_ir::{
    CellCoordinate, FormulaCache, FormulaLimits, FormulaNumberFormat, FormulaValue, LogicalId,
    TableRulingLimits,
};
use hwpx_package::{
    BoundedZipReader, HANCOM_2020_PARAGRAPH_NAMESPACE, IdIndex, IdIndexLimits, IdRuleProfile,
    PackageGraph, PackageGraphLimits, PackageLimits, PreservingXmlDocument,
    TableAggregateHwpxLimits, TableAggregateHwpxReadback, TableAggregateHwpxReader,
    TableLayoutHwpxLimits, TableLayoutHwpxReadback, TableLayoutHwpxReader, TableRulingHwpxBinding,
    TableRulingHwpxCellBinding, XmlByteSpan, XmlElementToken,
};
use sha2::{Digest as _, Sha256};

const MAX_FIXTURE_BYTES: u64 = 8 * 1024 * 1024;
const EXPECTED_PACKAGE_PARTS: usize = 11;
const EXPECTED_ROWS: u32 = 2;
const EXPECTED_COLUMNS: u32 = 4;
const EXPECTED_TARGET_TABLE_HEIGHT: u32 = 564;
const EXPECTED_ORACLE_TABLE_HEIGHT: u32 = 2_564;
const EXPECTED_TABLE_WIDTH: u32 = 41_952;
const EXPECTED_CELL_WIDTH: u32 = 10_488;
const EXPECTED_CELL_HEIGHT: u32 = 282;
const EXPECTED_CELL_CACHE_WIDTH: u32 = 9_468;
const EXPECTED_CELL_CACHE_COUNT: usize = 8;
const EXPECTED_SECTION_CACHE_COUNT: usize = 10;
const TARGET_HEIGHT_MARKER: &str = r#"<hp:sz width="41952" widthRelTo="ABSOLUTE" height="564""#;
const ORACLE_HEIGHT_MARKER: &str = r#"<hp:sz width="41952" widthRelTo="ABSOLUTE" height="2564""#;

#[derive(Clone, Copy)]
struct CaseProfile {
    feature_id: &'static str,
    target_sha256: &'static str,
    target_state_sha256: &'static str,
    formula: &'static str,
    result: &'static str,
}

struct Arguments {
    feature_id: String,
    target: PathBuf,
    expected_target_sha256: String,
    oracle: PathBuf,
    expected_oracle_sha256: String,
}

impl Arguments {
    fn parse() -> Result<Self, Box<dyn Error>> {
        let mut values = env::args_os();
        let _program = values.next();
        let feature_id = string_argument(&mut values, "feature ID")?;
        let target = path_argument(&mut values, "target HWPX")?;
        let expected_target_sha256 = string_argument(&mut values, "target SHA-256")?;
        let oracle = path_argument(&mut values, "oracle HWPX")?;
        let expected_oracle_sha256 = string_argument(&mut values, "oracle SHA-256")?;
        if values.next().is_some() {
            return Err("too many arguments".into());
        }
        Ok(Self {
            feature_id,
            target,
            expected_target_sha256,
            oracle,
            expected_oracle_sha256,
        })
    }
}

struct PackageParts {
    part_count: usize,
    header: Vec<u8>,
    section: Vec<u8>,
    preview: Vec<u8>,
}

struct RendererCacheEvidence {
    total_count: usize,
    cell_count: usize,
    cell_widths: Vec<u32>,
    outside_positions_and_widths: Vec<(u32, u32)>,
    sha256: [u8; 32],
}

struct RendererCacheRecord {
    span: XmlByteSpan,
    in_cell: bool,
    vertpos: u32,
    horzsize: u32,
}

fn main() -> Result<(), Box<dyn Error>> {
    run(&Arguments::parse()?)
}

fn run(arguments: &Arguments) -> Result<(), Box<dyn Error>> {
    require_lower_sha256(&arguments.expected_target_sha256)?;
    require_lower_sha256(&arguments.expected_oracle_sha256)?;
    let profile = case_profile(&arguments.feature_id)?;
    if arguments.expected_target_sha256 != profile.target_sha256 {
        return Err("exact aggregate target identity differs".into());
    }
    if arguments.target == arguments.oracle {
        return Err("target and oracle paths must differ".into());
    }
    let target_bytes = read_bounded_file(&arguments.target, MAX_FIXTURE_BYTES)?;
    let oracle_bytes = read_bounded_file(&arguments.oracle, MAX_FIXTURE_BYTES)?;
    require_digest(&target_bytes, &arguments.expected_target_sha256, "target")?;
    require_digest(&oracle_bytes, &arguments.expected_oracle_sha256, "oracle")?;

    let target = read_package(&target_bytes)?;
    let oracle = read_package(&oracle_bytes)?;
    let (target_without_cache, target_cache) = strip_renderer_caches(&target.section)?;
    let (oracle_without_cache, oracle_cache) = strip_renderer_caches(&oracle.section)?;
    require_renderer_profiles(&target_cache, &oracle_cache)?;
    let normalized_oracle = normalize_oracle_height(&oracle_without_cache)?;
    if target_without_cache != target.section || normalized_oracle != target.section {
        return Err("oracle section differs beyond renderer cache and aggregate height".into());
    }

    let binding = binding()?;
    let target_readback = read_aggregate(&target.header, &target.section, &binding)?;
    let oracle_readback = read_aggregate(&oracle.header, &normalized_oracle, &binding)?;
    require_semantics(profile, &target_readback, &oracle_readback)?;
    let target_layout = read_layout(&target.section)?;
    let oracle_layout = read_layout(&oracle.section)?;
    require_layouts(&target_layout, &oracle_layout)?;
    require_previews(profile, &target.preview, &oracle.preview)?;
    if target.part_count != EXPECTED_PACKAGE_PARTS || oracle.part_count != target.part_count {
        return Err("aggregate package part cardinality differs".into());
    }

    require_digest(
        &read_bounded_file(&arguments.target, MAX_FIXTURE_BYTES)?,
        &arguments.expected_target_sha256,
        "target recheck",
    )?;
    require_digest(
        &read_bounded_file(&arguments.oracle, MAX_FIXTURE_BYTES)?,
        &arguments.expected_oracle_sha256,
        "oracle recheck",
    )?;
    println!(
        concat!(
            "schema=hwpx-agent.p06-09-table-aggregate-target-oracle/v1 state=pass ",
            "feature_id={} target_sha256={} oracle_sha256={} formula={} cache={} ",
            "target_state_sha256={} target_table_height_hwpunit={} ",
            "oracle_table_height_hwpunit={} section_renderer_cache_count={} ",
            "cell_renderer_cache_count={} renderer_cache_sha256={} ",
            "outside_cache_positions_and_widths={} ",
            "section_equal_after_renderer_cache_strip_and_height_normalization=true"
        ),
        profile.feature_id,
        arguments.expected_target_sha256,
        arguments.expected_oracle_sha256,
        profile.formula,
        profile.result,
        profile.target_state_sha256,
        target_layout.table_height_hwpunit,
        oracle_layout.table_height_hwpunit,
        oracle_cache.total_count,
        oracle_cache.cell_count,
        hex(oracle_cache.sha256),
        join_pairs(&oracle_cache.outside_positions_and_widths),
    );
    Ok(())
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
        return Err("package graph cardinality differs".into());
    }
    Ok(PackageParts {
        part_count: graph.parts.len(),
        header: read_part(&mut reader, "Contents/header.xml")?,
        section: read_part(&mut reader, "Contents/section0.xml")?,
        preview: read_part(&mut reader, "Preview/PrvText.txt")?,
    })
}

fn read_aggregate(
    header: &[u8],
    section: &[u8],
    binding: &TableRulingHwpxBinding,
) -> Result<TableAggregateHwpxReadback, Box<dyn Error>> {
    Ok(TableAggregateHwpxReader::read_existing(
        header,
        section,
        0,
        binding,
        TableAggregateHwpxLimits::default(),
    )?)
}

fn require_semantics(
    profile: CaseProfile,
    target: &TableAggregateHwpxReadback,
    oracle: &TableAggregateHwpxReadback,
) -> Result<(), Box<dyn Error>> {
    if target.ruling.grid != oracle.ruling.grid
        || target.ruling.state != oracle.ruling.state
        || target.ruling.formula_count != 1
        || oracle.ruling.formula_count != 1
        || !same_pagination_semantics(target, oracle)
        || target.ruling.grid.rows() != EXPECTED_ROWS
        || target.ruling.grid.columns() != EXPECTED_COLUMNS
    {
        return Err("aggregate typed semantic readback differs".into());
    }
    let formula = target
        .ruling
        .state
        .cells()
        .iter()
        .find(|cell| cell.coordinate() == (CellCoordinate { row: 1, column: 3 }))
        .and_then(|cell| cell.formula())
        .ok_or("aggregate target formula is missing")?;
    if formula.ast().canonical_formula(FormulaLimits::default())? != profile.formula
        || decimal_cache(formula.cache())?.as_str() != profile.result
        || formula.number_format() != FormulaNumberFormat::General
        || hex(target
            .ruling
            .state
            .canonical_sha256(TableRulingLimits::default())?)
            != profile.target_state_sha256
    {
        return Err("aggregate formula profile differs".into());
    }
    Ok(())
}

fn require_layouts(
    target: &TableLayoutHwpxReadback,
    oracle: &TableLayoutHwpxReadback,
) -> Result<(), Box<dyn Error>> {
    let cells_match = target.cells.len() == 8
        && oracle.cells == target.cells
        && target.cells.iter().all(|cell| {
            cell.row_span == 1
                && cell.column_span == 1
                && cell.width_hwpunit == EXPECTED_CELL_WIDTH
                && cell.height_hwpunit == EXPECTED_CELL_HEIGHT
        });
    if (target.rows, target.columns) != (EXPECTED_ROWS, EXPECTED_COLUMNS)
        || (oracle.rows, oracle.columns) != (EXPECTED_ROWS, EXPECTED_COLUMNS)
        || target.table_width_hwpunit != EXPECTED_TABLE_WIDTH
        || oracle.table_width_hwpunit != EXPECTED_TABLE_WIDTH
        || target.table_height_hwpunit != EXPECTED_TARGET_TABLE_HEIGHT
        || oracle.table_height_hwpunit != EXPECTED_ORACLE_TABLE_HEIGHT
        || oracle.inner_margin != target.inner_margin
        || oracle.content_sha256 != target.content_sha256
        || !cells_match
    {
        return Err("aggregate layout relation differs".into());
    }
    Ok(())
}

fn require_previews(
    profile: CaseProfile,
    target: &[u8],
    oracle: &[u8],
) -> Result<(), Box<dyn Error>> {
    let expected_target = format!("<2><3><4><5><17><10><25><{}>\r\n\r\n", profile.result);
    let expected_oracle = format!("<2><3><4><5>\r\n<17><10><25><{}>\r\n\r\n", profile.result);
    if target != expected_target.as_bytes() || oracle != expected_oracle.as_bytes() {
        return Err("aggregate preview relation differs".into());
    }
    Ok(())
}

fn require_renderer_profiles(
    target: &RendererCacheEvidence,
    oracle: &RendererCacheEvidence,
) -> Result<(), Box<dyn Error>> {
    if target.total_count != 0
        || target.cell_count != 0
        || !target.cell_widths.is_empty()
        || !target.outside_positions_and_widths.is_empty()
        || oracle.total_count != EXPECTED_SECTION_CACHE_COUNT
        || oracle.cell_count != EXPECTED_CELL_CACHE_COUNT
        || oracle.cell_widths != vec![EXPECTED_CELL_CACHE_WIDTH; EXPECTED_CELL_CACHE_COUNT]
        || oracle.outside_positions_and_widths != [(0, 0), (3_130, 42_520)]
    {
        return Err("aggregate renderer cache profile differs".into());
    }
    Ok(())
}

fn normalize_oracle_height(section: &[u8]) -> Result<Vec<u8>, Box<dyn Error>> {
    let text = std::str::from_utf8(section)?;
    if text.matches(ORACLE_HEIGHT_MARKER).count() != 1 || text.contains(TARGET_HEIGHT_MARKER) {
        return Err("oracle aggregate table height profile differs".into());
    }
    Ok(text
        .replacen(ORACLE_HEIGHT_MARKER, TARGET_HEIGHT_MARKER, 1)
        .into_bytes())
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
    let mut spans = Vec::new();
    let mut cell_widths = Vec::new();
    let mut outside_positions_and_widths = Vec::new();
    let mut digest = Sha256::new();
    digest.update(b"hwpx-agent.p06-09-table-aggregate-renderer-cache/v1\0");
    for array in arrays.iter().copied() {
        let record = inspect_renderer_cache(section, &document, array)?;
        if record.in_cell {
            if record.vertpos != 0 {
                return Err("cell renderer cache vertical position differs".into());
            }
            cell_widths.push(record.horzsize);
        } else {
            outside_positions_and_widths.push((record.vertpos, record.horzsize));
        }
        let raw = section
            .get(record.span.start()..record.span.end())
            .ok_or("renderer cache span is outside section")?;
        digest.update(Sha256::digest(raw));
        spans.push(record.span);
    }
    let stripped = strip_spans(section, &mut spans)?;
    Ok((
        stripped,
        RendererCacheEvidence {
            total_count: arrays.len(),
            cell_count: cell_widths.len(),
            cell_widths,
            outside_positions_and_widths,
            sha256: digest.finalize().into(),
        },
    ))
}

fn inspect_renderer_cache(
    section: &[u8],
    document: &PreservingXmlDocument,
    array: usize,
) -> Result<RendererCacheRecord, Box<dyn Error>> {
    let array_element = document
        .elements()
        .get(array)
        .ok_or("cache array missing")?;
    if !array_element.attributes().is_empty()
        || array_element
            .parent()
            .and_then(|parent| document.elements().get(parent))
            .is_none_or(|parent| !has_name(parent, "p"))
    {
        return Err("renderer cache array shape differs".into());
    }
    let segment_index = array_element.first_child().ok_or("cache segment missing")?;
    if array_element.last_child() != Some(segment_index) {
        return Err("renderer cache segment cardinality differs".into());
    }
    let segment = document
        .elements()
        .get(segment_index)
        .ok_or("cache segment missing")?;
    if !has_name(segment, "lineseg") || !segment.is_empty() || segment.attributes().len() != 9 {
        return Err("renderer cache segment shape differs".into());
    }
    let fixed = [
        exact_u32_attribute(section, segment, "textpos")?,
        exact_u32_attribute(section, segment, "vertsize")?,
        exact_u32_attribute(section, segment, "textheight")?,
        exact_u32_attribute(section, segment, "baseline")?,
        exact_u32_attribute(section, segment, "spacing")?,
        exact_u32_attribute(section, segment, "horzpos")?,
        exact_u32_attribute(section, segment, "flags")?,
    ];
    if fixed != [0, 1_000, 1_000, 850, 600, 0, 393_216] {
        return Err("renderer cache fixed geometry differs".into());
    }
    Ok(RendererCacheRecord {
        span: array_element.outer_span().ok_or("cache span missing")?,
        in_cell: nearest_ancestor(document, array, "tc").is_some(),
        vertpos: exact_u32_attribute(section, segment, "vertpos")?,
        horzsize: exact_u32_attribute(section, segment, "horzsize")?,
    })
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
    let attribute = values.next().ok_or("cache attribute missing")?;
    if values.next().is_some() {
        return Err("cache attribute duplicated".into());
    }
    let span = attribute.value_span();
    Ok(std::str::from_utf8(
        source
            .get(span.start()..span.end())
            .ok_or("cache attribute span outside section")?,
    )?
    .parse()?)
}

fn nearest_ancestor(
    document: &PreservingXmlDocument,
    index: usize,
    local_name: &str,
) -> Option<usize> {
    let mut parent = document.elements().get(index)?.parent();
    while let Some(candidate) = parent {
        let element = document.elements().get(candidate)?;
        if has_name(element, local_name) {
            return Some(candidate);
        }
        parent = element.parent();
    }
    None
}

fn has_name(element: &XmlElementToken, local_name: &str) -> bool {
    element.name().namespace() == Some(HANCOM_2020_PARAGRAPH_NAMESPACE)
        && element.name().local_name() == local_name
}

fn binding() -> Result<TableRulingHwpxBinding, Box<dyn Error>> {
    let mut cells = Vec::new();
    for index in 0..8 {
        cells.push(TableRulingHwpxCellBinding {
            master_cell_id: LogicalId::parse(format!("aggregate-cell-{index}"))?,
            payload_block_ids: if index == 7 {
                Vec::new()
            } else {
                vec![LogicalId::parse(format!("aggregate-payload-{index}"))?]
            },
        });
    }
    Ok(TableRulingHwpxBinding {
        table_id: LogicalId::parse("aggregate-table")?,
        row_boundaries_hwpunit: vec![0, 282, 564],
        column_boundaries_hwpunit: vec![0, 10_488, 20_976, 31_464, 41_952],
        cells,
    })
}

fn read_layout(section: &[u8]) -> Result<TableLayoutHwpxReadback, Box<dyn Error>> {
    Ok(TableLayoutHwpxReader::read_in_section(
        section,
        0,
        TableLayoutHwpxLimits::default(),
    )?)
}

fn same_pagination_semantics(
    left: &TableAggregateHwpxReadback,
    right: &TableAggregateHwpxReadback,
) -> bool {
    left.pagination.page_split == right.pagination.page_split
        && left.pagination.repeat_header_rows == right.pagination.repeat_header_rows
        && left.pagination.row_count == right.pagination.row_count
        && left.pagination.column_count == right.pagination.column_count
        && left.pagination.caption == right.pagination.caption
}

fn decimal_cache(cache: &FormulaCache) -> Result<String, Box<dyn Error>> {
    let FormulaCache::Unverified {
        value: FormulaValue::Decimal { value },
    } = cache
    else {
        return Err("aggregate cache profile differs".into());
    };
    let coefficient = value.coefficient();
    let scale = usize::from(value.scale());
    if scale == 0 {
        return Ok(coefficient.to_string());
    }
    let negative = coefficient < 0;
    let mut digits = coefficient.unsigned_abs().to_string();
    if digits.len() <= scale {
        digits.insert_str(0, &"0".repeat(scale + 1 - digits.len()));
    }
    let split = digits.len() - scale;
    Ok(format!(
        "{}{}.{}",
        if negative { "-" } else { "" },
        &digits[..split],
        &digits[split..]
    ))
}

fn case_profile(feature_id: &str) -> Result<CaseProfile, Box<dyn Error>> {
    cases()
        .into_iter()
        .find(|profile| profile.feature_id == feature_id)
        .ok_or_else(|| "unsupported aggregate feature ID".into())
}

fn cases() -> [CaseProfile; 8] {
    [
        CaseProfile {
            feature_id: "TABLE-022",
            target_sha256: "56942277d33e114e6d6a960751b337b715903d0fec82018a7eb22c8fcbd4773c",
            target_state_sha256: "46cb8be768008bab7d575ca4d3be0aaccbec0060ca16944973f7d56de05e5500",
            formula: "SUM(A1:B2)",
            result: "32",
        },
        CaseProfile {
            feature_id: "TABLE-023",
            target_sha256: "f41282f85af76278259d3b08a947c6afa73b58c8598d5cc1f4c042a8cfa7d79a",
            target_state_sha256: "28d2f00da19838a13c98f92873cf06861308956c6edb3471a07d4c83e8a2490e",
            formula: "AVG(A1:B2)",
            result: "8",
        },
        CaseProfile {
            feature_id: "TABLE-024",
            target_sha256: "a87247142a5ae9699adfbf931e2be81ce1957f2cc985fb40ce1b63efee8b13c1",
            target_state_sha256: "608af33e448f832d1e70b83134a7d59a69f0ca0f0b60197742068e4f66796eb3",
            formula: "PRODUCT(A1:B2)",
            result: "1020",
        },
        CaseProfile {
            feature_id: "TABLE-026",
            target_sha256: "f48fa45a4cd107a086ea6a0411f5102141d8e90317e775944bf5bf0eedd588cf",
            target_state_sha256: "b5ddd2cd2ab6f68efab8b80e59a31090c3eb852fff31ced918a03020c08f38b0",
            formula: "SUM(D1:D1)",
            result: "5",
        },
        CaseProfile {
            feature_id: "TABLE-027",
            target_sha256: "2a693e1d09a14cea67c2f27c3d81bfa1574bc8938aafdba7933bedffb38dd84c",
            target_state_sha256: "bb8147c15114f3192808c1831f9de9f9cade3cde8341c7ffafe1ca58d013333e",
            formula: "AVG(A2:B2)",
            result: "13.5",
        },
        CaseProfile {
            feature_id: "TABLE-028",
            target_sha256: "7129fb774e5e12c0e320cfffdb2394776078c3be2c2065555b1720873dcb0788",
            target_state_sha256: "0f4cc1136ae667890637c5ba8e0153ecc22c082ad505947a24f8868d6f78fe7b",
            formula: "AVG(D1:D1)",
            result: "5",
        },
        CaseProfile {
            feature_id: "TABLE-029",
            target_sha256: "186af7b72b812a5bbf3ee2b0d8756cd1e617ab0606be3a6a53b5a17db88f9f96",
            target_state_sha256: "a53001e1f9596044141c0466e5ce1d8ca62725c299422256a07afc9505fdec09",
            formula: "PRODUCT(A2:B2)",
            result: "170",
        },
        CaseProfile {
            feature_id: "TABLE-030",
            target_sha256: "403e4645923362719262f142a9c59b904a058f8d009d7a57b0b772d1cfe62a14",
            target_state_sha256: "56b138d854b36c2a8f4db44bb68435264fbc1486af5fbc9ccad9b42916123afe",
            formula: "PRODUCT(D1:D1)",
            result: "5",
        },
    ]
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
    if hex(Sha256::digest(bytes)) != expected {
        return Err(format!("{label} SHA-256 mismatch").into());
    }
    Ok(())
}

fn path_argument(
    values: &mut impl Iterator<Item = std::ffi::OsString>,
    name: &str,
) -> Result<PathBuf, Box<dyn Error>> {
    values
        .next()
        .map(PathBuf::from)
        .ok_or_else(|| format!("missing {name}").into())
}

fn string_argument(
    values: &mut impl Iterator<Item = std::ffi::OsString>,
    name: &str,
) -> Result<String, Box<dyn Error>> {
    values
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

fn join_pairs(values: &[(u32, u32)]) -> String {
    values
        .iter()
        .map(|(left, right)| format!("{left}:{right}"))
        .collect::<Vec<_>>()
        .join(",")
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

    const PREFIX: &str = concat!(
        "<hs:sec xmlns:hs=\"http://www.hancom.co.kr/hwpml/2011/section\" ",
        "xmlns:hp=\"http://www.hancom.co.kr/hwpml/2011/paragraph\">"
    );
    const SEGMENT: &str = concat!(
        "<hp:linesegarray><hp:lineseg textpos=\"0\" vertpos=\"0\" vertsize=\"1000\" ",
        "textheight=\"1000\" baseline=\"850\" spacing=\"600\" horzpos=\"0\" ",
        "horzsize=\"9468\" flags=\"393216\"/></hp:linesegarray>"
    );

    fn section(segment: &str) -> Vec<u8> {
        format!(
            "{PREFIX}<hp:tbl><hp:tr><hp:tc><hp:p>{segment}</hp:p></hp:tc></hp:tr></hp:tbl></hs:sec>"
        )
        .into_bytes()
    }

    #[test]
    fn exact_feature_target_formula_and_result_matrix_is_locked() {
        let observed: Vec<_> = cases()
            .into_iter()
            .map(|case| (case.feature_id, case.formula, case.result))
            .collect();
        assert_eq!(
            observed,
            [
                ("TABLE-022", "SUM(A1:B2)", "32"),
                ("TABLE-023", "AVG(A1:B2)", "8"),
                ("TABLE-024", "PRODUCT(A1:B2)", "1020"),
                ("TABLE-026", "SUM(D1:D1)", "5"),
                ("TABLE-027", "AVG(A2:B2)", "13.5"),
                ("TABLE-028", "AVG(D1:D1)", "5"),
                ("TABLE-029", "PRODUCT(A2:B2)", "170"),
                ("TABLE-030", "PRODUCT(D1:D1)", "5"),
            ]
        );
    }

    #[test]
    fn renderer_cache_strip_is_exact_and_attribute_drift_fails_closed() {
        let source = section(SEGMENT);
        let expected = section("");
        let (stripped, evidence) = strip_renderer_caches(&source).unwrap();
        assert_eq!(stripped, expected);
        assert_eq!(evidence.total_count, 1);
        assert_eq!(evidence.cell_count, 1);
        assert_eq!(evidence.cell_widths, [EXPECTED_CELL_CACHE_WIDTH]);
        let drift = source
            .windows(b"baseline=\"850\"".len())
            .position(|window| window == b"baseline=\"850\"")
            .unwrap();
        let mut tampered = source;
        tampered[drift + b"baseline=\"85".len()] = b'1';
        assert!(strip_renderer_caches(&tampered).is_err());
    }

    #[test]
    fn oracle_height_normalization_is_exact_and_single_use() {
        let oracle = format!("<hp:tbl>{ORACLE_HEIGHT_MARKER}/></hp:tbl>");
        let expected = format!("<hp:tbl>{TARGET_HEIGHT_MARKER}/></hp:tbl>");
        assert_eq!(
            normalize_oracle_height(oracle.as_bytes()).unwrap(),
            expected.as_bytes()
        );
        assert!(normalize_oracle_height(expected.as_bytes()).is_err());
        let duplicate = format!("{oracle}{oracle}");
        assert!(normalize_oracle_height(duplicate.as_bytes()).is_err());
    }

    #[test]
    fn known_hancom_2020_formula_oracle_matches_the_renderer_cache_envelope() {
        let path = concat!(
            env!("CARGO_MANIFEST_DIR"),
            "/../../fixtures/target-build/p06-06-formula-target-20260907-01/",
            "target-readback-output-04.hwpx"
        );
        let Ok(bytes) = fs::read(path) else {
            return;
        };
        let package = read_package(&bytes).unwrap();
        let (_, evidence) = strip_renderer_caches(&package.section).unwrap();
        assert_eq!(evidence.total_count, EXPECTED_SECTION_CACHE_COUNT);
        assert_eq!(evidence.cell_count, EXPECTED_CELL_CACHE_COUNT);
        assert_eq!(
            evidence.cell_widths,
            vec![EXPECTED_CELL_CACHE_WIDTH; EXPECTED_CELL_CACHE_COUNT]
        );
        assert_eq!(
            evidence.outside_positions_and_widths,
            [(0, 0), (3_130, 42_520)]
        );
    }
}
