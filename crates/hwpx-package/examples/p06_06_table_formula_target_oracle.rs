use std::env;
use std::error::Error;
use std::fs;
use std::io::Cursor;
use std::path::{Path, PathBuf};

use domain_ir::{FormulaCache, FormulaLimits, FormulaNumberFormat, FormulaValue};
use hwpx_package::{
    BoundedZipReader, HANCOM_2020_PARAGRAPH_NAMESPACE, IdIndex, IdIndexLimits, IdRuleProfile,
    PackageGraph, PackageGraphLimits, PackageLimits, PreservingXmlDocument, TableFormulaHwpxLimits,
    TableFormulaHwpxReadback, TableFormulaHwpxReader, TableLayoutHwpxLimits,
    TableLayoutHwpxReadback, TableLayoutHwpxReader, TextFlowLimits, TextFlowReader, XmlByteSpan,
    XmlElementToken,
};
use sha2::{Digest as _, Sha256};

const MAX_FIXTURE_BYTES: u64 = 8 * 1024 * 1024;
const EXPECTED_TARGET_SHA256: &str =
    "6514a69b8c8c9d320bc19a032b16f2b71d59a38f164c690bc9e3d320a93320e5";
const EXPECTED_ORACLE_SHA256: &str =
    "8b33d2353ebec9eccbcbbde0c0b31eb440390ddf9c38bad7c064f179b1ab2325";
const EXPECTED_PREVIEW: &[u8] = b"<0><0><0><0><17><10><25><52>\r\n\r\n";
const EXPECTED_ORACLE_PREVIEW: &[u8] = b"<0><0><0><0>\r\n<17><10><25><52>\r\n\r\n";
const EXPECTED_VISIBLE: &[&str] = &["0", "0", "0", "0", "17", "10", "25", "52"];
const EXPECTED_ROWS: u32 = 2;
const EXPECTED_COLUMNS: u32 = 4;
const EXPECTED_CELL_WIDTH: u32 = 10_488;
const EXPECTED_CELL_HEIGHT: u32 = 282;
const EXPECTED_TABLE_WIDTH: u32 = 41_952;
const EXPECTED_TARGET_TABLE_HEIGHT: u32 = 2_564;
const EXPECTED_INNER_MARGIN: u32 = 510;
const EXPECTED_INNER_MARGIN_VERTICAL: u32 = 141;
const EXPECTED_PACKAGE_PARTS: usize = 11;
const EXPECTED_ORACLE_SECTION_CACHE_COUNT: usize = 10;
const EXPECTED_ORACLE_CELL_CACHE_WIDTH: u32 = 9_468;

struct Arguments {
    target: PathBuf,
    expected_target_sha256: String,
    oracle: PathBuf,
    expected_oracle_sha256: String,
}

impl Arguments {
    fn parse() -> Result<Self, Box<dyn Error>> {
        let mut arguments = env::args_os();
        let _program = arguments.next();
        let result = Self {
            target: path_argument(&mut arguments, "target HWPX")?,
            expected_target_sha256: string_argument(&mut arguments, "target SHA-256")?,
            oracle: path_argument(&mut arguments, "oracle HWPX")?,
            expected_oracle_sha256: string_argument(&mut arguments, "oracle SHA-256")?,
        };
        if arguments.next().is_some() {
            return Err("too many arguments".into());
        }
        Ok(result)
    }
}

fn main() -> Result<(), Box<dyn Error>> {
    run(&Arguments::parse()?)
}

fn run(arguments: &Arguments) -> Result<(), Box<dyn Error>> {
    require_lower_sha256(&arguments.expected_target_sha256)?;
    require_lower_sha256(&arguments.expected_oracle_sha256)?;
    if arguments.expected_target_sha256 != EXPECTED_TARGET_SHA256 {
        return Err("exact structural target identity differs".into());
    }
    if arguments.expected_oracle_sha256 != EXPECTED_ORACLE_SHA256 {
        return Err("exact Hangul 2020 oracle identity differs".into());
    }
    if arguments.target == arguments.oracle {
        return Err("target and oracle paths must differ".into());
    }

    let target_bytes = read_bounded_file(&arguments.target, MAX_FIXTURE_BYTES)?;
    let oracle_bytes = read_bounded_file(&arguments.oracle, MAX_FIXTURE_BYTES)?;
    require_digest(&target_bytes, &arguments.expected_target_sha256, "target")?;
    require_digest(&oracle_bytes, &arguments.expected_oracle_sha256, "oracle")?;

    let target = inspect_package(&target_bytes)?;
    let oracle = inspect_package(&oracle_bytes)?;
    require_target(&target)?;
    require_oracle(&target, &oracle)?;

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
            "schema=hwpx-agent.p06-06-formula-target-oracle/v1 state=pass ",
            "target_sha256={} oracle_sha256={} formula_sha256={} content_sha256={} ",
            "cell_text_set_sha256={} rows={} columns={} owner_row={} owner_column={} ",
            "target_table_height_hwpunit={} oracle_table_height_hwpunit={} ",
            "target_formula_unowned_sha256={} oracle_formula_unowned_sha256={} ",
            "oracle_renderer_cache_sha256={} oracle_section_cache_count={} ",
            "oracle_line_cache_counts={} section_equal_after_renderer_cache_strip=true ",
            "cache_value=52 cache_oracle=verified_external_receipt"
        ),
        arguments.expected_target_sha256,
        arguments.expected_oracle_sha256,
        hex(oracle
            .formula
            .formula
            .canonical_sha256(FormulaLimits::default())?),
        hex(oracle.layout.content_sha256),
        hex(oracle.cell_text_set_sha256),
        EXPECTED_ROWS,
        EXPECTED_COLUMNS,
        oracle.formula.formula.owner().row,
        oracle.formula.formula.owner().column,
        target.layout.table_height_hwpunit,
        oracle.layout.table_height_hwpunit,
        hex(target.formula.unowned_sha256),
        hex(oracle.formula.unowned_sha256),
        hex(oracle.renderer_cache.sha256),
        oracle.renderer_cache.total_count,
        join_usize(&oracle.line_cache_counts),
    );
    Ok(())
}

struct PackageInspection {
    part_count: usize,
    preview: Vec<u8>,
    formula: TableFormulaHwpxReadback,
    layout: TableLayoutHwpxReadback,
    cell_text_set_sha256: [u8; 32],
    line_cache_counts: Vec<usize>,
    section_without_renderer_cache: Vec<u8>,
    renderer_cache: RendererCacheEvidence,
}

struct RendererCacheEvidence {
    total_count: usize,
    cell_count: usize,
    outside_positions_and_widths: Vec<(u32, u32)>,
    sha256: [u8; 32],
}

struct RendererCacheRecord {
    span: XmlByteSpan,
    in_cell: bool,
    vertpos: u32,
    horzsize: u32,
}

fn inspect_package(bytes: &[u8]) -> Result<PackageInspection, Box<dyn Error>> {
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    let _index = IdIndex::build(
        &mut reader,
        &graph,
        IdRuleProfile::current_hancom_2020_formula_v3(),
        IdIndexLimits::default(),
    )?;
    if graph.parts.len() != reader.entries().len() {
        return Err("package graph cardinality mismatch".into());
    }
    let section = read_part(&mut reader, "Contents/section0.xml")?;
    let preview = read_part(&mut reader, "Preview/PrvText.txt")?;
    if TableFormulaHwpxReader::formula_count_in_section(
        &section,
        0,
        TableFormulaHwpxLimits::default(),
        FormulaLimits::default(),
    )? != 1
        || TableLayoutHwpxReader::count_in_section(&section, TableLayoutHwpxLimits::default())? != 1
    {
        return Err("package must contain exactly one table and formula".into());
    }
    let formula = TableFormulaHwpxReader::read_in_section(
        &section,
        0,
        TableFormulaHwpxLimits::default(),
        FormulaLimits::default(),
    )?;
    let layout =
        TableLayoutHwpxReader::read_in_section(&section, 0, TableLayoutHwpxLimits::default())?;
    let (cell_text_set_sha256, line_cache_counts) = read_cell_evidence(&section, &formula)?;
    let (section_without_renderer_cache, renderer_cache) =
        strip_and_inspect_renderer_caches(&section)?;
    Ok(PackageInspection {
        part_count: graph.parts.len(),
        preview,
        formula,
        layout,
        cell_text_set_sha256,
        line_cache_counts,
        section_without_renderer_cache,
        renderer_cache,
    })
}

fn require_target(value: &PackageInspection) -> Result<(), Box<dyn Error>> {
    let formula_limits = FormulaLimits::default();
    if value.part_count != EXPECTED_PACKAGE_PARTS
        || value.preview != EXPECTED_PREVIEW
        || value.formula.formula_field_count != 1
        || (value.formula.rows, value.formula.columns) != (EXPECTED_ROWS, EXPECTED_COLUMNS)
        || (
            value.formula.formula.owner().row,
            value.formula.formula.owner().column,
        ) != (1, 3)
        || value
            .formula
            .formula
            .ast()
            .canonical_formula(formula_limits)?
            != "SUM(A2:C2)"
        || cache_decimal(value.formula.formula.cache()) != Some((52, 0))
        || value.formula.formula.number_format() != FormulaNumberFormat::General
        || (value.layout.rows, value.layout.columns) != (EXPECTED_ROWS, EXPECTED_COLUMNS)
        || value.layout.cells.len() != EXPECTED_VISIBLE.len()
        || value.layout.table_width_hwpunit != EXPECTED_TABLE_WIDTH
        || value.layout.table_height_hwpunit != EXPECTED_TARGET_TABLE_HEIGHT
        || value.layout.inner_margin.left_hwpunit != EXPECTED_INNER_MARGIN
        || value.layout.inner_margin.right_hwpunit != EXPECTED_INNER_MARGIN
        || value.layout.inner_margin.top_hwpunit != EXPECTED_INNER_MARGIN_VERTICAL
        || value.layout.inner_margin.bottom_hwpunit != EXPECTED_INNER_MARGIN_VERTICAL
        || value.layout.cells.iter().any(|cell| {
            cell.width_hwpunit != EXPECTED_CELL_WIDTH
                || cell.height_hwpunit != EXPECTED_CELL_HEIGHT
                || cell.row_span != 1
                || cell.column_span != 1
        })
        || value.cell_text_set_sha256 != expected_text_set_sha256()
        || value.line_cache_counts != vec![0; EXPECTED_VISIBLE.len()]
        || value.renderer_cache.total_count != 0
        || value.renderer_cache.cell_count != 0
        || !value.renderer_cache.outside_positions_and_widths.is_empty()
    {
        return Err("target semantic profile differs".into());
    }
    Ok(())
}

fn require_oracle(
    target: &PackageInspection,
    oracle: &PackageInspection,
) -> Result<(), Box<dyn Error>> {
    if oracle.part_count != target.part_count
        || oracle.preview != EXPECTED_ORACLE_PREVIEW
        || oracle.formula.profile_id != target.formula.profile_id
        || oracle.formula.rows != target.formula.rows
        || oracle.formula.columns != target.formula.columns
        || oracle.formula.formula != target.formula.formula
        || oracle.formula.formula_field_count != target.formula.formula_field_count
        || (oracle.layout.rows, oracle.layout.columns) != (EXPECTED_ROWS, EXPECTED_COLUMNS)
        || oracle.layout.cells.len() != EXPECTED_VISIBLE.len()
        || oracle.layout.table_width_hwpunit != EXPECTED_TABLE_WIDTH
        || oracle.layout.table_height_hwpunit != EXPECTED_TARGET_TABLE_HEIGHT
        || oracle.layout.inner_margin != target.layout.inner_margin
        || oracle.layout.cells != target.layout.cells
        || oracle.layout.content_sha256 != target.layout.content_sha256
        || oracle.cell_text_set_sha256 != target.cell_text_set_sha256
        || oracle.line_cache_counts != vec![1; EXPECTED_VISIBLE.len()]
        || oracle.renderer_cache.total_count != EXPECTED_ORACLE_SECTION_CACHE_COUNT
        || oracle.renderer_cache.cell_count != EXPECTED_VISIBLE.len()
        || oracle.renderer_cache.outside_positions_and_widths != [(0, 0), (3_130, 42_520)]
        || oracle.section_without_renderer_cache != target.section_without_renderer_cache
    {
        return Err("oracle semantic readback differs".into());
    }
    Ok(())
}

fn strip_and_inspect_renderer_caches(
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
    spans.try_reserve_exact(arrays.len())?;
    let mut cell_count = 0usize;
    let mut outside_positions_and_widths = Vec::new();
    let mut digest = Sha256::new();
    digest.update(b"hwpx-agent.p06-06-renderer-cache/v1\0");

    for array in arrays.iter().copied() {
        let record = inspect_renderer_cache(section, &document, array)?;
        if record.in_cell {
            if record.vertpos != 0 || record.horzsize != EXPECTED_ORACLE_CELL_CACHE_WIDTH {
                return Err("cell renderer cache geometry differs".into());
            }
            cell_count = cell_count
                .checked_add(1)
                .ok_or("renderer cache count overflow")?;
        } else {
            outside_positions_and_widths
                .try_reserve(1)
                .map_err(|_| "renderer cache allocation failed")?;
            outside_positions_and_widths.push((record.vertpos, record.horzsize));
        }
        let raw = section
            .get(record.span.start()..record.span.end())
            .ok_or("renderer cache span is outside section")?;
        digest.update(Sha256::digest(raw));
        spans.push(record.span);
    }

    let stripped = strip_renderer_cache_spans(section, &mut spans)?;
    Ok((
        stripped,
        RendererCacheEvidence {
            total_count: arrays.len(),
            cell_count,
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
        .ok_or("renderer cache array is missing")?;
    if !array_element.attributes().is_empty()
        || array_element
            .parent()
            .and_then(|parent| document.elements().get(parent))
            .is_none_or(|parent| !has_name(parent, "p"))
    {
        return Err("renderer cache array shape differs".into());
    }
    let segment_index = array_element
        .first_child()
        .ok_or("renderer cache segment is missing")?;
    if array_element.last_child() != Some(segment_index) {
        return Err("renderer cache segment cardinality differs".into());
    }
    let segment = document
        .elements()
        .get(segment_index)
        .ok_or("renderer cache segment is missing")?;
    if !has_name(segment, "lineseg") || !segment.is_empty() {
        return Err("renderer cache segment shape differs".into());
    }
    let attributes = [
        exact_u32_attribute(section, segment, "textpos")?,
        exact_u32_attribute(section, segment, "vertsize")?,
        exact_u32_attribute(section, segment, "textheight")?,
        exact_u32_attribute(section, segment, "baseline")?,
        exact_u32_attribute(section, segment, "spacing")?,
        exact_u32_attribute(section, segment, "horzpos")?,
        exact_u32_attribute(section, segment, "flags")?,
    ];
    if segment.attributes().len() != 9 || attributes != [0, 1_000, 1_000, 850, 600, 0, 393_216] {
        return Err("renderer cache attribute profile differs".into());
    }
    Ok(RendererCacheRecord {
        span: array_element
            .outer_span()
            .ok_or("renderer cache span is missing")?,
        in_cell: nearest_ancestor(document, array, "tc").is_some(),
        vertpos: exact_u32_attribute(section, segment, "vertpos")?,
        horzsize: exact_u32_attribute(section, segment, "horzsize")?,
    })
}

fn strip_renderer_cache_spans(
    section: &[u8],
    spans: &mut [XmlByteSpan],
) -> Result<Vec<u8>, Box<dyn Error>> {
    spans.sort_by_key(|span| span.start());
    let removed_bytes = spans.iter().try_fold(0usize, |total, span| {
        total
            .checked_add(span.end().saturating_sub(span.start()))
            .ok_or("renderer cache size overflow")
    })?;
    let mut stripped = Vec::new();
    stripped.try_reserve_exact(
        section
            .len()
            .checked_sub(removed_bytes)
            .ok_or("renderer cache size underflow")?,
    )?;
    let mut cursor = 0usize;
    for span in spans {
        if span.start() < cursor || span.end() > section.len() {
            return Err("renderer cache spans overlap".into());
        }
        stripped.extend_from_slice(&section[cursor..span.start()]);
        cursor = span.end();
    }
    stripped.extend_from_slice(&section[cursor..]);
    Ok(stripped)
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
    let attribute = values.next().ok_or("renderer cache attribute is missing")?;
    if values.next().is_some() {
        return Err("renderer cache attribute is duplicated".into());
    }
    let span = attribute.value_span();
    let raw = source
        .get(span.start()..span.end())
        .ok_or("renderer cache attribute span is outside section")?;
    Ok(std::str::from_utf8(raw)?.parse()?)
}

fn read_cell_evidence(
    section: &[u8],
    formula: &TableFormulaHwpxReadback,
) -> Result<([u8; 32], Vec<usize>), Box<dyn Error>> {
    let document = PreservingXmlDocument::parse(section)?;
    let tables: Vec<_> = document
        .elements()
        .iter()
        .enumerate()
        .filter(|(_, element)| has_name(element, "tbl"))
        .map(|(index, _)| index)
        .collect();
    if tables.len() != 1 {
        return Err("section table cardinality differs".into());
    }
    let table = tables[0];
    let cells: Vec<_> = document
        .elements()
        .iter()
        .enumerate()
        .filter(|(index, element)| {
            has_name(element, "tc") && nearest_ancestor(&document, *index, "tbl") == Some(table)
        })
        .map(|(index, _)| index)
        .collect();
    if cells.len() != EXPECTED_VISIBLE.len() {
        return Err("section cell cardinality differs".into());
    }

    let mut digest = Sha256::new();
    digest.update(b"hwpx-agent.p06-06-cell-text-set/v1\0");
    let mut line_cache_counts = Vec::new();
    line_cache_counts.try_reserve_exact(cells.len())?;
    let formula_ordinal = usize::try_from(
        formula
            .formula
            .owner()
            .row
            .checked_mul(formula.columns)
            .and_then(|value| value.checked_add(formula.formula.owner().column))
            .ok_or("formula owner ordinal overflow")?,
    )?;
    if formula_ordinal >= cells.len() {
        return Err("formula owner is outside cell evidence".into());
    }
    let formula_visible = match cache_decimal(formula.formula.cache()) {
        Some((coefficient, 0)) => coefficient.to_string(),
        _ => return Err("formula visible cache is unsupported".into()),
    };

    for (ordinal, cell) in cells.into_iter().enumerate() {
        let paragraphs: Vec<_> = document
            .elements()
            .iter()
            .enumerate()
            .filter(|(index, element)| {
                has_name(element, "p") && nearest_ancestor(&document, *index, "tc") == Some(cell)
            })
            .map(|(index, _)| index)
            .collect();
        if paragraphs.len() != 1 {
            return Err("cell paragraph cardinality differs".into());
        }
        let paragraph = paragraphs[0];
        // Formula fields carry nested native parameters that the generic text-flow profile
        // intentionally does not admit. TableFormulaHwpxReader already proves that its typed cache,
        // LastResult and visible hp:t agree, so use that typed result only for the formula owner.
        let visible = if ordinal == formula_ordinal {
            formula_visible.clone()
        } else {
            TextFlowReader::read(
                &standalone_paragraph(section, &document, paragraph)?,
                TextFlowLimits::default(),
            )?
            .visible_text_nfc()?
        };
        if visible != EXPECTED_VISIBLE[ordinal] {
            return Err("cell visible text differs".into());
        }
        digest.update(Sha256::digest(visible.as_bytes()));
        let count = document
            .elements()
            .iter()
            .enumerate()
            .filter(|(index, element)| {
                has_name(element, "linesegarray")
                    && nearest_ancestor(&document, *index, "p") == Some(paragraph)
            })
            .count();
        line_cache_counts.push(count);
    }
    Ok((digest.finalize().into(), line_cache_counts))
}

fn standalone_paragraph(
    section: &[u8],
    document: &PreservingXmlDocument,
    paragraph: usize,
) -> Result<Vec<u8>, Box<dyn Error>> {
    let element = document
        .elements()
        .get(paragraph)
        .ok_or("paragraph element is missing")?;
    let outer = element.outer_span().ok_or("paragraph span is missing")?;
    let source = section
        .get(outer.start()..outer.end())
        .ok_or("paragraph span is outside section")?;
    let declaration_name = match element.name().prefix() {
        Some(prefix) => format!("xmlns:{prefix}"),
        None => "xmlns".to_owned(),
    };
    let has_local_declaration = element.attributes().iter().any(|attribute| {
        attribute.is_namespace_declaration()
            && attribute.name().qualified_name() == declaration_name
    });
    if has_local_declaration {
        return Ok(source.to_vec());
    }
    let insertion = element
        .start_name_span()
        .end()
        .checked_sub(outer.start())
        .ok_or("paragraph namespace insertion underflow")?;
    let mut standalone = Vec::new();
    standalone.try_reserve_exact(
        source.len() + declaration_name.len() + HANCOM_2020_PARAGRAPH_NAMESPACE.len() + 5,
    )?;
    standalone.extend_from_slice(&source[..insertion]);
    standalone.extend_from_slice(
        format!(" {declaration_name}=\"{HANCOM_2020_PARAGRAPH_NAMESPACE}\"").as_bytes(),
    );
    standalone.extend_from_slice(&source[insertion..]);
    Ok(standalone)
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

fn expected_text_set_sha256() -> [u8; 32] {
    let mut digest = Sha256::new();
    digest.update(b"hwpx-agent.p06-06-cell-text-set/v1\0");
    for value in EXPECTED_VISIBLE {
        digest.update(Sha256::digest(value.as_bytes()));
    }
    digest.finalize().into()
}

fn cache_decimal(cache: &FormulaCache) -> Option<(i64, u8)> {
    match cache {
        FormulaCache::Unverified {
            value: FormulaValue::Decimal { value },
        } => Some((value.coefficient(), value.scale())),
        _ => None,
    }
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
    if hex(Sha256::digest(bytes).into()) != expected {
        return Err(format!("{label} SHA-256 mismatch").into());
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
        return Err("SHA-256 must be 64 lowercase hexadecimal characters".into());
    }
    Ok(())
}

fn join_usize(values: &[usize]) -> String {
    values
        .iter()
        .map(usize::to_string)
        .collect::<Vec<_>>()
        .join(",")
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
            "{PREFIX}<hp:tbl><hp:tr><hp:tc><hp:p><hp:run><hp:t>52</hp:t></hp:run>{segment}</hp:p></hp:tc></hp:tr></hp:tbl></hs:sec>"
        )
        .into_bytes()
    }

    #[test]
    fn exact_cell_renderer_cache_is_stripped_without_other_byte_drift() {
        let source = section(SEGMENT);
        let expected = section("");
        let (stripped, evidence) = strip_and_inspect_renderer_caches(&source).unwrap();
        assert_eq!(stripped, expected);
        assert_eq!(evidence.total_count, 1);
        assert_eq!(evidence.cell_count, 1);
        assert!(evidence.outside_positions_and_widths.is_empty());
    }

    #[test]
    fn renderer_cache_attribute_drift_fails_closed() {
        let source = section(&SEGMENT.replacen("baseline=\"850\"", "baseline=\"851\"", 1));
        assert!(strip_and_inspect_renderer_caches(&source).is_err());
    }

    #[test]
    fn duplicate_renderer_cache_segment_fails_closed() {
        let duplicate = SEGMENT.replacen(
            "</hp:linesegarray>",
            concat!(
                "<hp:lineseg textpos=\"0\" vertpos=\"0\" vertsize=\"1000\" ",
                "textheight=\"1000\" baseline=\"850\" spacing=\"600\" horzpos=\"0\" ",
                "horzsize=\"9468\" flags=\"393216\"/></hp:linesegarray>"
            ),
            1,
        );
        assert!(strip_and_inspect_renderer_caches(&section(&duplicate)).is_err());
    }
}
