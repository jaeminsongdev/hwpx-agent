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
    TableLayoutHwpxReadback, TableLayoutHwpxReader, TextFlowLimits, TextFlowReader,
    XmlElementToken,
};
use sha2::{Digest as _, Sha256};

const MAX_FIXTURE_BYTES: u64 = 8 * 1024 * 1024;
const EXPECTED_TARGET_SHA256: &str =
    "6514a69b8c8c9d320bc19a032b16f2b71d59a38f164c690bc9e3d320a93320e5";
const EXPECTED_PREVIEW: &[u8] = b"<0><0><0><0><17><10><25><52>\r\n\r\n";
const EXPECTED_VISIBLE: &[&str] = &["0", "0", "0", "0", "17", "10", "25", "52"];
const EXPECTED_ROWS: u32 = 2;
const EXPECTED_COLUMNS: u32 = 4;
const EXPECTED_CELL_WIDTH: u32 = 10_488;
const EXPECTED_CELL_HEIGHT: u32 = 282;
const EXPECTED_TABLE_WIDTH: u32 = 41_952;
const EXPECTED_TARGET_TABLE_HEIGHT: u32 = 2_564;

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
            "oracle_line_cache_counts={} cache_value=52 cache_oracle=verified_external_receipt"
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
    Ok(PackageInspection {
        part_count: graph.parts.len(),
        preview,
        formula,
        layout,
        cell_text_set_sha256,
        line_cache_counts,
    })
}

fn require_target(value: &PackageInspection) -> Result<(), Box<dyn Error>> {
    let formula_limits = FormulaLimits::default();
    if value.preview != EXPECTED_PREVIEW
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
        || value.layout.cells.iter().any(|cell| {
            cell.width_hwpunit != EXPECTED_CELL_WIDTH
                || cell.height_hwpunit != EXPECTED_CELL_HEIGHT
                || cell.row_span != 1
                || cell.column_span != 1
        })
        || value.cell_text_set_sha256 != expected_text_set_sha256()
        || value.line_cache_counts != vec![0; EXPECTED_VISIBLE.len()]
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
        || oracle.preview != target.preview
        || oracle.formula != target.formula
        || (oracle.layout.rows, oracle.layout.columns) != (EXPECTED_ROWS, EXPECTED_COLUMNS)
        || oracle.layout.cells.len() != EXPECTED_VISIBLE.len()
        || oracle.layout.table_width_hwpunit != EXPECTED_TABLE_WIDTH
        || oracle.layout.cells != target.layout.cells
        || oracle.layout.content_sha256 != target.layout.content_sha256
        || oracle.cell_text_set_sha256 != target.cell_text_set_sha256
        || oracle.line_cache_counts.len() != EXPECTED_VISIBLE.len()
        || oracle.line_cache_counts.contains(&0)
    {
        return Err("oracle semantic readback differs".into());
    }
    Ok(())
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
