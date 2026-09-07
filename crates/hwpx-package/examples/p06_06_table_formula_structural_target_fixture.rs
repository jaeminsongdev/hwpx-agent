use std::env;
use std::error::Error;
use std::fmt::Write as _;
use std::fs::{self, OpenOptions};
use std::io::{Cursor, Write as _};
use std::path::{Path, PathBuf};

use domain_ir::{
    FormulaCache, FormulaCachePolicy, FormulaDecimal, FormulaGridDimensions, FormulaGridEdit,
    FormulaLimits, FormulaValue, LogicalId, TableGrid, TableGridLimits, TableOperationKind,
};
use hwpx_package::{
    BoundedZipReader, Compression, IdIndex, IdIndexError, IdIndexLimits, IdRuleProfile,
    PackageGraph, PackageGraphLimits, PackageLimits, PreservingXmlDocument, TableFormulaHwpxLimits,
    TableFormulaHwpxLowerer, TableFormulaHwpxReadback, TableFormulaHwpxReader,
    TableLayoutHwpxLimits, TableLayoutHwpxReadback, TableLayoutHwpxReader,
};
use sha2::{Digest as _, Sha256};
use zip::write::SimpleFileOptions;
use zip::{CompressionMethod, DateTime, ZipWriter};

const MAX_FIXTURE_BYTES: u64 = 8 * 1024 * 1024;
const NORMALIZED_DEFLATE_LEVEL: i64 = 6;
const EXPECTED_INPUT_SHA256: &str =
    "d968cae419a3754b1dc65eb845f9d1d6bf8bbb486736359cd9b838a78e47d38f";
const SOURCE_PREVIEW: &[u8] = b"<17><25><42>\r\n\r\n";
const TARGET_PREVIEW: &[u8] = b"<0><0><0><0><17><10><25><52>\r\n\r\n";
const TARGET_ROWS: u32 = 2;
const TARGET_COLUMNS: u32 = 4;
const TARGET_CELL_WIDTH: u32 = 10_488;
const TARGET_CELL_HEIGHT: u32 = 282;
const TARGET_TABLE_WIDTH: u32 = 41_952;
const TARGET_TABLE_HEIGHT: u32 = 2_564;

struct Arguments {
    input: PathBuf,
    expected_input_sha256: String,
    output: PathBuf,
}

impl Arguments {
    fn parse() -> Result<Self, Box<dyn Error>> {
        let mut arguments = env::args_os();
        let _program = arguments.next();
        let result = Self {
            input: path_argument(&mut arguments, "input HWPX")?,
            expected_input_sha256: string_argument(&mut arguments, "expected input SHA-256")?,
            output: path_argument(&mut arguments, "output HWPX")?,
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
    require_lower_sha256(&arguments.expected_input_sha256)?;
    if arguments.expected_input_sha256 != EXPECTED_INPUT_SHA256 {
        return Err("exact formula source identity differs".into());
    }
    if arguments.input == arguments.output
        || arguments
            .output
            .extension()
            .and_then(|value| value.to_str())
            != Some("hwpx")
    {
        return Err("output must be a distinct .hwpx path".into());
    }

    let source = read_bounded_file(&arguments.input, MAX_FIXTURE_BYTES)?;
    require_digest(&source, EXPECTED_INPUT_SHA256, "input")?;
    let source_inspection = inspect_package(&source)?;
    require_source(&source_inspection)?;

    let (grid, column_receipt, row_receipt) = transformed_grid()?;
    let target_formula = transformed_formula(&source_inspection.formula.formula)?;
    if grid.rows() != TARGET_ROWS
        || grid.columns() != TARGET_COLUMNS
        || column_receipt.operation() != TableOperationKind::InsertColumns
        || row_receipt.operation() != TableOperationKind::InsertRows
    {
        return Err("pure structural grid differential drifted".into());
    }

    let structural_section = build_structural_section(&source_inspection.section)?;
    let formula_limits = FormulaLimits::default();
    let structural_formula = TableFormulaHwpxReader::read_in_section(
        &structural_section,
        0,
        TableFormulaHwpxLimits::default(),
        formula_limits,
    )?;
    if structural_formula.formula.owner() != target_formula.owner()
        || structural_formula
            .formula
            .ast()
            .canonical_sha256(formula_limits)?
            != target_formula.ast().canonical_sha256(formula_limits)?
    {
        return Err("structural HWPX formula did not match the pure differential".into());
    }
    let (target_section, formula_receipt) = TableFormulaHwpxLowerer::lower_in_section_with_receipt(
        &structural_section,
        0,
        &target_formula,
        FormulaGridDimensions {
            rows: TARGET_ROWS,
            columns: TARGET_COLUMNS,
        },
        TableFormulaHwpxLimits::default(),
        formula_limits,
    )?;
    let target = replace_parts(&source, &target_section)?;
    let target_inspection = inspect_package(&target)?;
    require_target(&target_inspection, &target_formula)?;
    if target_inspection.part_count != source_inspection.part_count
        || formula_receipt.target_formula_sha256
            != target_formula.canonical_sha256(formula_limits)?
    {
        return Err("target package identity or formula receipt drifted".into());
    }

    require_digest(
        &read_bounded_file(&arguments.input, MAX_FIXTURE_BYTES)?,
        EXPECTED_INPUT_SHA256,
        "input recheck",
    )?;
    write_create_new(&arguments.output, &target)?;
    print_receipt(
        &target,
        &grid,
        &target_formula,
        &column_receipt,
        &row_receipt,
        formula_receipt.unowned_sha256,
    )
}

fn transformed_formula(
    source: &domain_ir::FormulaCell,
) -> Result<domain_ir::FormulaCell, Box<dyn Error>> {
    let formula_limits = FormulaLimits::default();
    let column_formula = source.apply_grid_edit(
        FormulaGridEdit::InsertColumns {
            before: FormulaGridDimensions {
                rows: 1,
                columns: 3,
            },
            index: 1,
            count: 1,
        },
        FormulaCachePolicy::Update,
        Some(result_cache()),
        formula_limits,
    )?;
    let target_formula = column_formula.apply_grid_edit(
        FormulaGridEdit::InsertRows {
            before: FormulaGridDimensions {
                rows: 1,
                columns: 4,
            },
            index: 0,
            count: 1,
        },
        FormulaCachePolicy::Update,
        Some(result_cache()),
        formula_limits,
    )?;
    if target_formula.owner().row != 1
        || target_formula.owner().column != 3
        || target_formula.ast().canonical_formula(formula_limits)? != "SUM(A2:C2)"
    {
        return Err("pure structural formula differential drifted".into());
    }
    Ok(target_formula)
}

fn print_receipt(
    target: &[u8],
    grid: &TableGrid,
    target_formula: &domain_ir::FormulaCell,
    column_receipt: &domain_ir::TableOperationReceipt,
    row_receipt: &domain_ir::TableOperationReceipt,
    unowned_sha256: [u8; 32],
) -> Result<(), Box<dyn Error>> {
    let formula_limits = FormulaLimits::default();
    println!(
        concat!(
            "schema=hwpx-agent.p06-06-formula-structural-target/v1 state=pass ",
            "input_sha256={} output_sha256={} grid_sha256={} formula_sha256={} ",
            "column_receipt_sha256={} row_receipt_sha256={} unowned_sha256={} ",
            "rows={} columns={} owner_row={} owner_column={} cache_provenance=unverified"
        ),
        EXPECTED_INPUT_SHA256,
        hex(Sha256::digest(target).into()),
        hex(grid.canonical_sha256()?),
        hex(target_formula.canonical_sha256(formula_limits)?),
        hex(Sha256::digest(serde_json::to_vec(&column_receipt)?).into()),
        hex(Sha256::digest(serde_json::to_vec(&row_receipt)?).into()),
        hex(unowned_sha256),
        TARGET_ROWS,
        TARGET_COLUMNS,
        target_formula.owner().row,
        target_formula.owner().column,
    );
    Ok(())
}

struct PackageInspection {
    part_count: usize,
    section: Vec<u8>,
    preview: Vec<u8>,
    formula: TableFormulaHwpxReadback,
    layout: TableLayoutHwpxReadback,
}

fn inspect_package(bytes: &[u8]) -> Result<PackageInspection, Box<dyn Error>> {
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    validate_ids(&mut reader, &graph)?;
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
        return Err("fixture must contain exactly one table and formula".into());
    }
    let formula = TableFormulaHwpxReader::read_in_section(
        &section,
        0,
        TableFormulaHwpxLimits::default(),
        FormulaLimits::default(),
    )?;
    let layout =
        TableLayoutHwpxReader::read_in_section(&section, 0, TableLayoutHwpxLimits::default())?;
    Ok(PackageInspection {
        part_count: graph.parts.len(),
        section,
        preview,
        formula,
        layout,
    })
}

fn validate_ids(
    reader: &mut BoundedZipReader<Cursor<&[u8]>>,
    graph: &PackageGraph,
) -> Result<(), Box<dyn Error>> {
    match IdIndex::build(
        reader,
        graph,
        IdRuleProfile::current_hancom_2020_formula_v3(),
        IdIndexLimits::default(),
    ) {
        Ok(_) => Ok(()),
        Err(error) => {
            print_id_issue_shapes(reader, &error)?;
            Err(error.into())
        }
    }
}

fn print_id_issue_shapes(
    reader: &mut BoundedZipReader<Cursor<&[u8]>>,
    error: &IdIndexError,
) -> Result<(), Box<dyn Error>> {
    let Some(report) = error.validation() else {
        return Ok(());
    };
    for issue in report.issues().iter().take(16) {
        let location = issue.source();
        let part = read_part(reader, location.part().as_str())?;
        let document = PreservingXmlDocument::parse(&part)?;
        let element = document
            .elements()
            .get(location.element_index())
            .ok_or("ID issue element index is invalid")?;
        let attribute = element
            .attributes()
            .get(location.attribute_index())
            .ok_or("ID issue attribute index is invalid")?;
        eprintln!(
            "id_issue code={} part={} element={} attribute={}",
            issue.code(),
            location.part().as_str(),
            element.name().qualified_name(),
            attribute.name().qualified_name(),
        );
    }
    Ok(())
}

fn require_source(value: &PackageInspection) -> Result<(), Box<dyn Error>> {
    if value.preview != SOURCE_PREVIEW
        || (value.formula.rows, value.formula.columns) != (1, 3)
        || (
            value.formula.formula.owner().row,
            value.formula.formula.owner().column,
        ) != (0, 2)
        || value
            .formula
            .formula
            .ast()
            .canonical_formula(FormulaLimits::default())?
            != "SUM(A1:B1)"
        || cache_decimal(value.formula.formula.cache()) != Some((42, 0))
    {
        return Err("source differs from the exact formula profile".into());
    }
    Ok(())
}

fn require_target(
    value: &PackageInspection,
    target_formula: &domain_ir::FormulaCell,
) -> Result<(), Box<dyn Error>> {
    if value.preview != TARGET_PREVIEW
        || value.formula.formula != *target_formula
        || (value.layout.rows, value.layout.columns) != (TARGET_ROWS, TARGET_COLUMNS)
        || value.layout.cells.len() != 8
        || value.layout.table_width_hwpunit != TARGET_TABLE_WIDTH
        || value.layout.table_height_hwpunit != TARGET_TABLE_HEIGHT
        || value.layout.cells.iter().any(|cell| {
            cell.width_hwpunit != TARGET_CELL_WIDTH
                || cell.height_hwpunit != TARGET_CELL_HEIGHT
                || cell.row_span != 1
                || cell.column_span != 1
        })
        || String::from_utf8(value.section.clone())?.contains("<hp:linesegarray>")
    {
        return Err("target semantic readback differs".into());
    }
    Ok(())
}

fn transformed_grid() -> Result<
    (
        TableGrid,
        domain_ir::TableOperationReceipt,
        domain_ir::TableOperationReceipt,
    ),
    Box<dyn Error>,
> {
    let source = TableGrid::create_unmerged(
        1,
        3,
        logical_ids(&["operand-a", "operand-b", "formula"])?,
        TableGridLimits::default(),
    )?
    .into_parts()
    .0;
    let columns = source.insert_columns(
        1,
        1,
        logical_ids(&["inserted-operand"])?,
        TableGridLimits::default(),
    )?;
    let (column_grid, column_receipt) = columns.into_parts();
    let rows = column_grid.insert_rows(
        0,
        1,
        logical_ids(&[
            "inserted-row-a",
            "inserted-row-b",
            "inserted-row-c",
            "inserted-row-d",
        ])?,
        TableGridLimits::default(),
    )?;
    let (grid, row_receipt) = rows.into_parts();
    Ok((grid, column_receipt, row_receipt))
}

fn logical_ids(values: &[&str]) -> Result<Vec<LogicalId>, Box<dyn Error>> {
    values
        .iter()
        .map(|value| LogicalId::parse(*value).map_err(Into::into))
        .collect()
}

fn result_cache() -> FormulaCache {
    FormulaCache::Unverified {
        value: FormulaValue::Decimal {
            value: FormulaDecimal::new(52, 0),
        },
    }
}

fn cache_decimal(cache: &FormulaCache) -> Option<(i64, u8)> {
    match cache {
        FormulaCache::Unverified {
            value: FormulaValue::Decimal { value },
        } => Some((value.coefficient(), value.scale())),
        _ => None,
    }
}

fn build_structural_section(source: &[u8]) -> Result<Vec<u8>, Box<dyn Error>> {
    let source = String::from_utf8(source.to_vec())?;
    if source.matches("<hp:tr>").count() != 1 || source.matches("<hp:linesegarray>").count() != 5 {
        return Err("source row or line-cache cardinality drifted".into());
    }
    let row_start = source.find("<hp:tr>").ok_or("source row is missing")?;
    let row_end = source[row_start..]
        .find("</hp:tr>")
        .map(|offset| row_start + offset + "</hp:tr>".len())
        .ok_or("source row end is missing")?;
    let cells = extract_cells(&source[row_start..row_end])?;
    if cells.len() != 3 {
        return Err("source cell cardinality drifted".into());
    }
    let base_a = text_cell(&cells[0], "17", "17", 1, 0)?;
    let inserted = text_cell(&cells[0], "17", "10", 1, 1)?;
    let base_b = text_cell(&cells[1], "25", "25", 1, 2)?;
    let formula = formula_cell(&cells[2], 1, 3)?;
    let top = [
        text_cell(&cells[0], "17", "0", 0, 0)?,
        text_cell(&cells[0], "17", "0", 0, 1)?,
        text_cell(&cells[0], "17", "0", 0, 2)?,
        text_cell(&cells[0], "17", "0", 0, 3)?,
    ];
    let rows = format!(
        "<hp:tr>{}</hp:tr><hp:tr>{}</hp:tr>",
        top.concat(),
        [base_a, inserted, base_b, formula].concat()
    );
    let mut target = String::with_capacity(source.len() + rows.len());
    target.push_str(&source[..row_start]);
    target.push_str(&rows);
    target.push_str(&source[row_end..]);
    target = replace_once(
        &target,
        "rowCnt=\"1\" colCnt=\"3\"",
        "rowCnt=\"2\" colCnt=\"4\"",
    )?;
    target = replace_once(
        &target,
        "<hp:sz width=\"41952\" widthRelTo=\"ABSOLUTE\" height=\"1282\"",
        "<hp:sz width=\"41952\" widthRelTo=\"ABSOLUTE\" height=\"2564\"",
    )?;
    let (target, removed) = strip_elements(target, "<hp:linesegarray>", "</hp:linesegarray>")?;
    if removed != 2 || target.matches("<hp:linesegarray>").next().is_some() {
        return Err("renderer cache removal drifted".into());
    }
    Ok(target.into_bytes())
}

fn extract_cells(row: &str) -> Result<Vec<String>, Box<dyn Error>> {
    let mut output = Vec::new();
    let mut cursor = 0;
    while let Some(start_offset) = row[cursor..].find("<hp:tc ") {
        let start = cursor + start_offset;
        let end = row[start..]
            .find("</hp:tc>")
            .map(|offset| start + offset + "</hp:tc>".len())
            .ok_or("cell end is missing")?;
        output.push(row[start..end].to_owned());
        cursor = end;
    }
    Ok(output)
}

fn text_cell(
    source: &str,
    source_text: &str,
    target_text: &str,
    row: u32,
    column: u32,
) -> Result<String, Box<dyn Error>> {
    let mut value = replace_once(
        source,
        &format!("<hp:t>{source_text}</hp:t>"),
        &format!("<hp:t>{target_text}</hp:t>"),
    )?;
    value = replace_cell_geometry(&value, row, column)?;
    let (value, removed) = strip_elements(value, "<hp:linesegarray>", "</hp:linesegarray>")?;
    if removed != 1 {
        return Err("cell line-cache cardinality drifted".into());
    }
    Ok(value)
}

fn formula_cell(source: &str, row: u32, column: u32) -> Result<String, Box<dyn Error>> {
    let value = replace_cell_geometry(source, row, column)?;
    let (value, removed) = strip_elements(value, "<hp:linesegarray>", "</hp:linesegarray>")?;
    if removed != 1 {
        return Err("formula cell line-cache cardinality drifted".into());
    }
    Ok(value)
}

fn replace_cell_geometry(source: &str, row: u32, column: u32) -> Result<String, Box<dyn Error>> {
    let address_start = source
        .find("<hp:cellAddr ")
        .ok_or("cell address is missing")?;
    let address_end = source[address_start..]
        .find("/>")
        .map(|offset| address_start + offset + 2)
        .ok_or("cell address end is missing")?;
    let mut value = String::with_capacity(source.len());
    value.push_str(&source[..address_start]);
    write!(
        &mut value,
        "<hp:cellAddr colAddr=\"{column}\" rowAddr=\"{row}\"/>"
    )?;
    value.push_str(&source[address_end..]);
    replace_once(
        &value,
        "<hp:cellSz width=\"13984\" height=\"282\"/>",
        &format!("<hp:cellSz width=\"{TARGET_CELL_WIDTH}\" height=\"{TARGET_CELL_HEIGHT}\"/>"),
    )
}

fn strip_elements(
    mut source: String,
    start_marker: &str,
    end_marker: &str,
) -> Result<(String, usize), Box<dyn Error>> {
    let mut count = 0;
    while let Some(start) = source.find(start_marker) {
        let end = source[start..]
            .find(end_marker)
            .map(|offset| start + offset + end_marker.len())
            .ok_or("element end is missing")?;
        source.replace_range(start..end, "");
        count += 1;
    }
    Ok((source, count))
}

fn replace_once(source: &str, old: &str, new: &str) -> Result<String, Box<dyn Error>> {
    if old.is_empty() || source.matches(old).count() != 1 {
        return Err("exact replacement cardinality mismatch".into());
    }
    Ok(source.replacen(old, new, 1))
}

fn replace_parts(source: &[u8], target_section: &[u8]) -> Result<Vec<u8>, Box<dyn Error>> {
    let mut archive = BoundedZipReader::open(Cursor::new(source), PackageLimits::default())?;
    let entries = archive.entries().to_vec();
    let mut parts = Vec::new();
    parts.try_reserve_exact(entries.len())?;
    let mut section_replacements = 0_u8;
    let mut preview_replacements = 0_u8;
    for entry in entries {
        let path = entry.path.as_str().to_owned();
        let method = match entry.compression {
            Compression::Stored => CompressionMethod::Stored,
            Compression::Deflated => CompressionMethod::Deflated,
        };
        let bytes = match path.as_str() {
            "Contents/section0.xml" => {
                section_replacements += 1;
                target_section.to_vec()
            }
            "Preview/PrvText.txt" => {
                preview_replacements += 1;
                TARGET_PREVIEW.to_vec()
            }
            _ => archive.read_entry(entry.index)?,
        };
        parts.push((path, method, bytes));
    }
    if section_replacements != 1 || preview_replacements != 1 {
        return Err("target part replacement cardinality mismatch".into());
    }
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    for (path, method, bytes) in parts {
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
    let output = writer.finish()?.into_inner();
    if output.len() > TableFormulaHwpxLimits::default().config().output_bytes {
        return Err("target package exceeds output limit".into());
    }
    Ok(output)
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

fn write_create_new(path: &Path, bytes: &[u8]) -> Result<(), Box<dyn Error>> {
    let mut file = OpenOptions::new().write(true).create_new(true).open(path)?;
    file.write_all(bytes)?;
    Ok(file.sync_all()?)
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

fn hex(value: [u8; 32]) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let mut output = String::with_capacity(64);
    for byte in value {
        output.push(char::from(DIGITS[usize::from(byte >> 4)]));
        output.push(char::from(DIGITS[usize::from(byte & 0x0f)]));
    }
    output
}
