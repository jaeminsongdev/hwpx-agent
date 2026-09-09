use std::env;
use std::error::Error;
use std::fs::{self, OpenOptions};
use std::io::{Cursor, Write as _};
use std::path::{Path, PathBuf};

use domain_ir::{
    CellCoordinate, FormulaCache, FormulaDecimal, FormulaFunction, FormulaValue, LogicalId,
    TABLE_AGGREGATE_SCHEMA_VERSION, TableAggregateAxis, TableAggregateRange,
    TableAggregateRequestDraft, TableRulingLimits,
};
use hwpx_package::{
    BoundedZipReader, Compression, PackageLimits, TABLE_AGGREGATE_HWPX_SCHEMA_VERSION,
    TableAggregateHwpxBuilder, TableAggregateHwpxLimits, TableAggregateHwpxLoweredParts,
    TableAggregateHwpxLowerer, TableAggregateHwpxPlan, TableAggregateHwpxReadback,
    TableAggregateHwpxReader, TableAggregateHwpxRequest, TableAggregateHwpxRequestDraft,
    TableRulingHwpxBinding, TableRulingHwpxCellBinding,
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use zip::write::SimpleFileOptions;
use zip::{CompressionMethod, DateTime, ZipWriter};

const MAX_FIXTURE_BYTES: u64 = 8 * 1024 * 1024;
const NORMALIZED_DEFLATE_LEVEL: i64 = 6;
const EXPECTED_INPUT_SHA256: &str =
    "6514a69b8c8c9d320bc19a032b16f2b71d59a38f164c690bc9e3d320a93320e5";
const SOURCE_PREVIEW: &[u8] = b"<2><3><4><5><17><10><25><>\r\n\r\n";
const EMPTY_RUN: &str = r"<hp:t/>";
const FORMULA_RUN_CONTENT: &str = concat!(
    r#"<hp:ctrl><hp:fieldBegin id="1188510575" type="FORMULA" name="" editable="0" dirty="0" zorder="-1" fieldid="627469685">"#,
    r#"<hp:parameters cnt="5" name=""><hp:integerParam name="Prop">8</hp:integerParam>"#,
    r#"<hp:stringParam name="Command">=SUM(LEFT)??%g,;;52</hp:stringParam>"#,
    r#"<hp:stringParam name="Formula">=SUM(LEFT)</hp:stringParam>"#,
    r#"<hp:stringParam name="ResultFormat">%g,</hp:stringParam>"#,
    r#"<hp:stringParam name="LastResult">52</hp:stringParam></hp:parameters>"#,
    r#"</hp:fieldBegin></hp:ctrl><hp:t>52</hp:t><hp:ctrl>"#,
    r#"<hp:fieldEnd beginIDRef="1188510575" fieldid="627469685"/></hp:ctrl><hp:t/>"#,
);

struct Arguments {
    input: PathBuf,
    expected_input_sha256: String,
    output_directory: PathBuf,
}

impl Arguments {
    fn parse() -> Result<Self, Box<dyn Error>> {
        let mut arguments = env::args_os();
        let _program = arguments.next();
        let input = arguments
            .next()
            .map(PathBuf::from)
            .ok_or("missing input HWPX")?;
        let expected_input_sha256 = arguments
            .next()
            .ok_or("missing expected input SHA-256")?
            .into_string()
            .map_err(|_| "expected input SHA-256 is not Unicode")?;
        let output_directory = arguments
            .next()
            .map(PathBuf::from)
            .ok_or("missing output directory")?;
        if arguments.next().is_some() {
            return Err("too many arguments".into());
        }
        Ok(Self {
            input,
            expected_input_sha256,
            output_directory,
        })
    }
}

#[derive(Clone, Copy)]
struct Case {
    feature_id: &'static str,
    capability_id: &'static str,
    name: &'static str,
    axis: TableAggregateAxis,
    function: FormulaFunction,
    source: TableAggregateRange,
    result: FormulaDecimal,
}

#[derive(Serialize)]
struct Manifest {
    schema_version: &'static str,
    source_ancestor_sha256: &'static str,
    source_file: &'static str,
    source_sha256: String,
    source_section_sha256: String,
    cases: Vec<ManifestCase>,
    actual_hangul_2020: bool,
    render: &'static str,
    automation: &'static str,
    differential: &'static str,
}

#[derive(Serialize)]
struct ManifestCase {
    feature_id: &'static str,
    capability_id: &'static str,
    file: String,
    sha256: String,
    formula: String,
    unverified_cache: String,
    expected_hangul_text_sha256: String,
    source_state_sha256: String,
    target_state_sha256: String,
    source_grid_sha256: String,
    target_grid_sha256: String,
    request_sha256: String,
    plan_sha256: String,
}

struct CaseContext<'a> {
    header: &'a [u8],
    section: &'a [u8],
    source_package: &'a [u8],
    binding: &'a TableRulingHwpxBinding,
    source: &'a TableAggregateHwpxReadback,
    source_state_sha256: &'a str,
    source_grid_sha256: &'a str,
    before_flow: &'a str,
    output_directory: &'a Path,
    limits: TableAggregateHwpxLimits,
}

fn main() -> Result<(), Box<dyn Error>> {
    run(&Arguments::parse()?)
}

fn run(arguments: &Arguments) -> Result<(), Box<dyn Error>> {
    require_lower_sha256(&arguments.expected_input_sha256)?;
    if arguments.expected_input_sha256 != EXPECTED_INPUT_SHA256 {
        return Err("exact aggregate fixture ancestor identity differs".into());
    }
    if arguments.input.extension().and_then(|value| value.to_str()) != Some("hwpx") {
        return Err("input must be an .hwpx file".into());
    }
    fs::create_dir(&arguments.output_directory)?;

    let ancestor = read_bounded_file(&arguments.input, MAX_FIXTURE_BYTES)?;
    require_digest(&ancestor, EXPECTED_INPUT_SHA256, "input")?;
    let (ancestor_header, ancestor_section) = read_parts(&ancestor)?;
    let source_section = prepare_source_section(&ancestor_section)?;
    let source_package =
        replace_parts(&ancestor, &ancestor_header, &source_section, SOURCE_PREVIEW)?;
    let source_path = arguments.output_directory.join("source.hwpx");
    write_create_new(&source_path, &source_package)?;

    let binding = binding()?;
    let limits = TableAggregateHwpxLimits::default();
    let source = TableAggregateHwpxReader::read_existing(
        &ancestor_header,
        &source_section,
        0,
        &binding,
        limits,
    )?;
    if source.ruling.grid.rows() != 2
        || source.ruling.grid.columns() != 4
        || source.ruling.formula_count != 0
        || source.ruling.payload_block_count != 7
    {
        return Err("prepared aggregate source readback differs".into());
    }
    let source_state_sha256 = hex(source
        .ruling
        .state
        .canonical_sha256(TableRulingLimits::default())?);
    let source_grid_sha256 = hex(source.ruling.grid.canonical_sha256()?);
    let before_flow = tagged_digest(b"source-flow", &source_section);
    let context = CaseContext {
        header: &ancestor_header,
        section: &source_section,
        source_package: &source_package,
        binding: &binding,
        source: &source,
        source_state_sha256: &source_state_sha256,
        source_grid_sha256: &source_grid_sha256,
        before_flow: &before_flow,
        output_directory: &arguments.output_directory,
        limits,
    };
    let manifest_cases = cases()
        .into_iter()
        .map(|case| build_case(&context, case))
        .collect::<Result<Vec<_>, _>>()?;

    let manifest = Manifest {
        schema_version: "hwpx-agent.p06-09-table-aggregate-target-fixture/v1",
        source_ancestor_sha256: EXPECTED_INPUT_SHA256,
        source_file: "source.hwpx",
        source_sha256: hex(Sha256::digest(&source_package)),
        source_section_sha256: hex(Sha256::digest(&source_section)),
        cases: manifest_cases,
        actual_hangul_2020: false,
        render: "not_run",
        automation: "not_run",
        differential: "not_run",
    };
    let manifest_bytes = serde_json::to_vec_pretty(&manifest)?;
    write_create_new(
        &arguments.output_directory.join("fixture-manifest.json"),
        &manifest_bytes,
    )?;
    require_digest(
        &read_bounded_file(&arguments.input, MAX_FIXTURE_BYTES)?,
        EXPECTED_INPUT_SHA256,
        "input recheck",
    )?;
    println!(
        "schema={} state=pass source_sha256={} target_count={} actual_hangul_2020=false",
        manifest.schema_version,
        manifest.source_sha256,
        manifest.cases.len(),
    );
    Ok(())
}

fn build_case(context: &CaseContext<'_>, case: Case) -> Result<ManifestCase, Box<dyn Error>> {
    let after_flow = tagged_digest(b"target-flow", case.feature_id.as_bytes());
    let draft = TableAggregateHwpxRequestDraft {
        schema_version: TABLE_AGGREGATE_HWPX_SCHEMA_VERSION.to_owned(),
        table_ordinal: 0,
        expected_header_sha256: hex(Sha256::digest(context.header)),
        expected_section_sha256: hex(Sha256::digest(context.section)),
        expected_source_state_sha256: context.source_state_sha256.to_owned(),
        expected_source_grid_sha256: context.source_grid_sha256.to_owned(),
        expected_document_flow_sha256: context.before_flow.to_owned(),
        target_document_flow_sha256: after_flow,
        aggregate: TableAggregateRequestDraft {
            schema_version: TABLE_AGGREGATE_SCHEMA_VERSION.to_owned(),
            axis: case.axis,
            function: case.function,
            source: case.source,
            destination: CellCoordinate { row: 1, column: 3 },
        },
        target_cache: FormulaCache::Unverified {
            value: FormulaValue::Decimal { value: case.result },
        },
    };
    let request = TableAggregateHwpxRequest::from_draft(
        draft,
        context.source,
        context.before_flow,
        context.limits,
    )?;
    if request.capability_id() != case.capability_id {
        return Err("aggregate feature and capability identity differ".into());
    }
    let plan = TableAggregateHwpxBuilder::build(
        &request,
        context.source,
        context.before_flow,
        context.limits,
    )?;
    let first = lower_case(context, &request, &plan)?;
    let second = lower_case(context, &request, &plan)?;
    if first.header != second.header || first.section != second.section {
        return Err("aggregate target lowering is nondeterministic".into());
    }
    let result_text = decimal_text(case.result);
    let preview = format!("<2><3><4><5><17><10><25><{result_text}>\r\n\r\n");
    let target_package = replace_parts(
        context.source_package,
        &first.header,
        &first.section,
        preview.as_bytes(),
    )?;
    assert_non_selected_parts_preserved(context.source_package, &target_package)?;
    let (target_header, target_section) = read_parts(&target_package)?;
    let reopened = TableAggregateHwpxReader::read_existing(
        &target_header,
        &target_section,
        0,
        &first.binding,
        context.limits,
    )?;
    if reopened.ruling.state != *plan.target_state()
        || reopened.ruling.grid != *plan.target_grid()
        || !same_pagination_semantics(&reopened.pagination, &context.source.pagination)
    {
        return Err("aggregate target package semantic reopen differs".into());
    }
    let formula = plan
        .target_formula()
        .ast()
        .canonical_formula(context.limits.ruling.formula)?;
    let file = format!(
        "{}-{}.hwpx",
        case.feature_id.to_ascii_lowercase(),
        case.name
    );
    write_create_new(&context.output_directory.join(&file), &target_package)?;
    Ok(ManifestCase {
        feature_id: case.feature_id,
        capability_id: request.capability_id(),
        file,
        sha256: hex(Sha256::digest(&target_package)),
        formula,
        unverified_cache: result_text.clone(),
        expected_hangul_text_sha256: hangul_text_digest(&result_text),
        source_state_sha256: hex(first.receipt.source_state_sha256),
        target_state_sha256: hex(first.receipt.target_state_sha256),
        source_grid_sha256: hex(first.receipt.source_grid_sha256),
        target_grid_sha256: hex(first.receipt.target_grid_sha256),
        request_sha256: hex(first.receipt.request_sha256),
        plan_sha256: hex(first.receipt.plan_sha256),
    })
}

fn lower_case(
    context: &CaseContext<'_>,
    request: &TableAggregateHwpxRequest,
    plan: &TableAggregateHwpxPlan,
) -> Result<TableAggregateHwpxLoweredParts, Box<dyn Error>> {
    Ok(TableAggregateHwpxLowerer::lower_existing(
        context.header,
        context.section,
        context.binding,
        context.before_flow,
        request,
        plan,
        context.limits,
    )?)
}

fn same_pagination_semantics(
    left: &hwpx_package::TablePaginationHwpxReadback,
    right: &hwpx_package::TablePaginationHwpxReadback,
) -> bool {
    left.page_split == right.page_split
        && left.repeat_header_rows == right.repeat_header_rows
        && left.row_count == right.row_count
        && left.column_count == right.column_count
        && left.caption == right.caption
}

fn cases() -> [Case; 8] {
    let block = TableAggregateRange {
        start: CellCoordinate { row: 0, column: 0 },
        end: CellCoordinate { row: 1, column: 1 },
    };
    let horizontal = TableAggregateRange {
        start: CellCoordinate { row: 1, column: 0 },
        end: CellCoordinate { row: 1, column: 1 },
    };
    let vertical = TableAggregateRange {
        start: CellCoordinate { row: 0, column: 3 },
        end: CellCoordinate { row: 0, column: 3 },
    };
    [
        Case {
            feature_id: "TABLE-022",
            capability_id: "table.block_sum",
            name: "block-sum",
            axis: TableAggregateAxis::Block,
            function: FormulaFunction::Sum,
            source: block,
            result: FormulaDecimal::new(32, 0),
        },
        Case {
            feature_id: "TABLE-023",
            capability_id: "table.block_average",
            name: "block-average",
            axis: TableAggregateAxis::Block,
            function: FormulaFunction::Average,
            source: block,
            result: FormulaDecimal::new(8, 0),
        },
        Case {
            feature_id: "TABLE-024",
            capability_id: "table.block_product",
            name: "block-product",
            axis: TableAggregateAxis::Block,
            function: FormulaFunction::Product,
            source: block,
            result: FormulaDecimal::new(1020, 0),
        },
        Case {
            feature_id: "TABLE-026",
            capability_id: "table.vertical_sum",
            name: "vertical-sum",
            axis: TableAggregateAxis::Vertical,
            function: FormulaFunction::Sum,
            source: vertical,
            result: FormulaDecimal::new(5, 0),
        },
        Case {
            feature_id: "TABLE-027",
            capability_id: "table.horizontal_average",
            name: "horizontal-average",
            axis: TableAggregateAxis::Horizontal,
            function: FormulaFunction::Average,
            source: horizontal,
            result: FormulaDecimal::new(135, 1),
        },
        Case {
            feature_id: "TABLE-028",
            capability_id: "table.vertical_average",
            name: "vertical-average",
            axis: TableAggregateAxis::Vertical,
            function: FormulaFunction::Average,
            source: vertical,
            result: FormulaDecimal::new(5, 0),
        },
        Case {
            feature_id: "TABLE-029",
            capability_id: "table.horizontal_product",
            name: "horizontal-product",
            axis: TableAggregateAxis::Horizontal,
            function: FormulaFunction::Product,
            source: horizontal,
            result: FormulaDecimal::new(170, 0),
        },
        Case {
            feature_id: "TABLE-030",
            capability_id: "table.vertical_product",
            name: "vertical-product",
            axis: TableAggregateAxis::Vertical,
            function: FormulaFunction::Product,
            source: vertical,
            result: FormulaDecimal::new(5, 0),
        },
    ]
}

fn prepare_source_section(bytes: &[u8]) -> Result<Vec<u8>, Box<dyn Error>> {
    let mut source = String::from_utf8(bytes.to_vec())?;
    source = replace_once(&source, "repeatHeader=\"1\"", "repeatHeader=\"0\"")?;
    source = replace_once(
        &source,
        "<hp:sz width=\"41952\" widthRelTo=\"ABSOLUTE\" height=\"2564\"",
        "<hp:sz width=\"41952\" widthRelTo=\"ABSOLUTE\" height=\"564\"",
    )?;
    for value in ["2", "3", "4", "5"] {
        source = replace_first(&source, "<hp:t>0</hp:t>", &format!("<hp:t>{value}</hp:t>"))?;
    }
    source = replace_once(&source, FORMULA_RUN_CONTENT, EMPTY_RUN)?;
    if source.contains("<hp:fieldBegin")
        || source.contains("<hp:t>0</hp:t>")
        || source.matches("<hp:t/>").count() < 2
    {
        return Err("prepared source formula or values drifted".into());
    }
    Ok(source.into_bytes())
}

fn binding() -> Result<TableRulingHwpxBinding, Box<dyn Error>> {
    let mut cells = Vec::new();
    for index in 0..8 {
        let payload_block_ids = if index == 7 {
            Vec::new()
        } else {
            vec![LogicalId::parse(format!("aggregate-payload-{index}"))?]
        };
        cells.push(TableRulingHwpxCellBinding {
            master_cell_id: LogicalId::parse(format!("aggregate-cell-{index}"))?,
            payload_block_ids,
        });
    }
    Ok(TableRulingHwpxBinding {
        table_id: LogicalId::parse("aggregate-table")?,
        row_boundaries_hwpunit: vec![0, 282, 564],
        column_boundaries_hwpunit: vec![0, 10_488, 20_976, 31_464, 41_952],
        cells,
    })
}

fn read_parts(source: &[u8]) -> Result<(Vec<u8>, Vec<u8>), Box<dyn Error>> {
    let mut archive = BoundedZipReader::open(Cursor::new(source), PackageLimits::default())?;
    let header = read_part(&mut archive, "Contents/header.xml")?;
    let section = read_part(&mut archive, "Contents/section0.xml")?;
    Ok((header, section))
}

fn read_part(
    archive: &mut BoundedZipReader<Cursor<&[u8]>>,
    path: &str,
) -> Result<Vec<u8>, Box<dyn Error>> {
    let index = archive
        .entries()
        .iter()
        .find(|entry| entry.path.as_str() == path)
        .map(|entry| entry.index)
        .ok_or("required package part is missing")?;
    Ok(archive.read_entry(index)?)
}

fn replace_parts(
    source: &[u8],
    header: &[u8],
    section: &[u8],
    preview: &[u8],
) -> Result<Vec<u8>, Box<dyn Error>> {
    let mut archive = BoundedZipReader::open(Cursor::new(source), PackageLimits::default())?;
    let entries = archive.entries().to_vec();
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    let mut replacements = [0_u8; 3];
    for entry in entries {
        let path = entry.path.as_str();
        let method = match entry.compression {
            Compression::Stored => CompressionMethod::Stored,
            Compression::Deflated => CompressionMethod::Deflated,
        };
        let bytes = match path {
            "Contents/header.xml" => {
                replacements[0] += 1;
                header.to_vec()
            }
            "Contents/section0.xml" => {
                replacements[1] += 1;
                section.to_vec()
            }
            "Preview/PrvText.txt" => {
                replacements[2] += 1;
                preview.to_vec()
            }
            _ => archive.read_entry(entry.index)?,
        };
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
    if replacements != [1, 1, 1] {
        return Err("package replacement cardinality differs".into());
    }
    let output = writer.finish()?.into_inner();
    if output.len() as u64 > MAX_FIXTURE_BYTES {
        return Err("target package exceeds fixture bound".into());
    }
    Ok(output)
}

fn assert_non_selected_parts_preserved(source: &[u8], target: &[u8]) -> Result<(), Box<dyn Error>> {
    let mut source_archive = BoundedZipReader::open(Cursor::new(source), PackageLimits::default())?;
    let mut target_archive = BoundedZipReader::open(Cursor::new(target), PackageLimits::default())?;
    if source_archive.entries().len() != target_archive.entries().len() {
        return Err("target package entry count differs".into());
    }
    for entry in source_archive.entries().to_vec() {
        let path = entry.path.as_str();
        if matches!(path, "Contents/section0.xml" | "Preview/PrvText.txt") {
            continue;
        }
        let target_index = target_archive
            .entries()
            .iter()
            .find(|candidate| candidate.path.as_str() == path)
            .map(|candidate| candidate.index)
            .ok_or("target package entry is missing")?;
        if source_archive.read_entry(entry.index)? != target_archive.read_entry(target_index)? {
            return Err(format!("non-selected package part changed: {path}").into());
        }
    }
    Ok(())
}

fn hangul_text_digest(result: &str) -> String {
    let text = format!("\n2\n3\n4\n5\n17\n10\n25\n{result}");
    hex(Sha256::digest(text.as_bytes()))
}

fn decimal_text(value: FormulaDecimal) -> String {
    let coefficient = value.coefficient();
    let scale = usize::from(value.scale());
    if scale == 0 {
        return coefficient.to_string();
    }
    let negative = coefficient < 0;
    let digits = coefficient.unsigned_abs().to_string();
    let mut output = String::new();
    if negative {
        output.push('-');
    }
    if digits.len() <= scale {
        output.push_str("0.");
        output.extend(std::iter::repeat_n('0', scale - digits.len()));
        output.push_str(&digits);
    } else {
        let split = digits.len() - scale;
        output.push_str(&digits[..split]);
        output.push('.');
        output.push_str(&digits[split..]);
    }
    output
}

fn tagged_digest(tag: &[u8], value: &[u8]) -> String {
    let mut digest = Sha256::new();
    digest.update(b"hwpx-agent.p06-09-table-aggregate-target-flow/v1\0");
    digest.update((tag.len() as u64).to_be_bytes());
    digest.update(tag);
    digest.update((value.len() as u64).to_be_bytes());
    digest.update(value);
    hex(digest.finalize())
}

fn replace_once(source: &str, old: &str, new: &str) -> Result<String, Box<dyn Error>> {
    if old.is_empty() || source.matches(old).count() != 1 {
        return Err("exact replacement cardinality differs".into());
    }
    Ok(source.replacen(old, new, 1))
}

fn replace_first(source: &str, old: &str, new: &str) -> Result<String, Box<dyn Error>> {
    if old.is_empty() || !source.contains(old) {
        return Err("required replacement value is missing".into());
    }
    Ok(source.replacen(old, new, 1))
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

fn write_create_new(path: &Path, bytes: &[u8]) -> Result<(), Box<dyn Error>> {
    let mut file = OpenOptions::new().write(true).create_new(true).open(path)?;
    file.write_all(bytes)?;
    Ok(file.sync_all()?)
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

    #[test]
    fn cases_match_the_authoritative_feature_capability_matrix() {
        let observed: Vec<_> = cases()
            .into_iter()
            .map(|case| (case.feature_id, case.capability_id))
            .collect();
        assert_eq!(
            observed,
            [
                ("TABLE-022", "table.block_sum"),
                ("TABLE-023", "table.block_average"),
                ("TABLE-024", "table.block_product"),
                ("TABLE-026", "table.vertical_sum"),
                ("TABLE-027", "table.horizontal_average"),
                ("TABLE-028", "table.vertical_average"),
                ("TABLE-029", "table.horizontal_product"),
                ("TABLE-030", "table.vertical_product"),
            ]
        );
    }
}
