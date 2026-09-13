use std::env;
use std::error::Error;
use std::fs::{self, OpenOptions};
use std::io::{Cursor, Write as _};
use std::path::{Path, PathBuf};

use domain_ir::{LogicalId, TableRulingLimits};
use hwpx_package::{
    BoundedZipReader, Compression, PackageLimits, TABLE_CREATE_HWPX_SCHEMA_VERSION,
    TableCreateHwpxBuilder, TableCreateHwpxLimits, TableCreateHwpxLowerer, TableCreateHwpxReader,
    TableCreateHwpxRequest, TableCreateHwpxRequestDraft, TableRulingHwpxBinding,
    TableRulingHwpxCellBinding,
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use zip::write::SimpleFileOptions;
use zip::{CompressionMethod, DateTime, ZipWriter};

const MAX_FIXTURE_BYTES: u64 = 8 * 1024 * 1024;
const NORMALIZED_DEFLATE_LEVEL: i64 = 6;
const EXPECTED_ANCESTOR_SHA256: &str =
    "6514a69b8c8c9d320bc19a032b16f2b71d59a38f164c690bc9e3d320a93320e5";
const EMPTY_TRAILING_PARAGRAPH: &str = concat!(
    r#"<hp:p id="0" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">"#,
    r#"<hp:run charPrIDRef="0"/></hp:p>"#,
);
const CREATE_PLACEHOLDER_PARAGRAPH: &str = concat!(
    r#"<hp:p id="0" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">"#,
    r#"<hp:run charPrIDRef="0"><hp:t/></hp:run></hp:p>"#,
);

struct Arguments {
    ancestor: PathBuf,
    expected_ancestor_sha256: String,
    output_directory: PathBuf,
}

impl Arguments {
    fn parse() -> Result<Self, Box<dyn Error>> {
        let mut values = env::args_os();
        let _program = values.next();
        let ancestor = values
            .next()
            .map(PathBuf::from)
            .ok_or("missing ancestor HWPX")?;
        let expected_ancestor_sha256 = values
            .next()
            .ok_or("missing ancestor SHA-256")?
            .into_string()
            .map_err(|_| "ancestor SHA-256 is not Unicode")?;
        let output_directory = values
            .next()
            .map(PathBuf::from)
            .ok_or("missing output directory")?;
        if values.next().is_some() {
            return Err("too many arguments".into());
        }
        Ok(Self {
            ancestor,
            expected_ancestor_sha256,
            output_directory,
        })
    }
}

#[derive(Clone, Copy)]
struct Case {
    id: &'static str,
    file: &'static str,
    rows: u32,
    columns: u32,
    row_heights_hwpunit: &'static [u32],
    column_widths_hwpunit: &'static [u32],
}

#[derive(Serialize)]
struct Manifest {
    schema_version: &'static str,
    source_ancestor_sha256: &'static str,
    destination_section_sha256: String,
    template_section_sha256: String,
    template_state_sha256: String,
    template_grid_sha256: String,
    cases: Vec<ManifestCase>,
    actual_hangul_2020: bool,
    render: &'static str,
    automation: &'static str,
    differential: &'static str,
}

#[derive(Serialize)]
struct ManifestCase {
    case_id: &'static str,
    feature_id: &'static str,
    capability_id: &'static str,
    file: &'static str,
    sha256: String,
    selected_table_ordinal: usize,
    rows: u32,
    columns: u32,
    row_heights_hwpunit: &'static [u32],
    column_widths_hwpunit: &'static [u32],
    target_header_sha256: String,
    target_section_sha256: String,
    target_state_sha256: String,
    target_grid_sha256: String,
    request_sha256: String,
    plan_sha256: String,
    created_master_cell_count: usize,
    payload_block_count: usize,
    formula_count: usize,
    page_split_preserved: bool,
    binding: BindingEvidence,
}

#[derive(Serialize)]
struct BindingEvidence {
    table_id: String,
    row_boundaries_hwpunit: Vec<u32>,
    column_boundaries_hwpunit: Vec<u32>,
    cells: Vec<BindingCellEvidence>,
}

#[derive(Serialize)]
struct BindingCellEvidence {
    master_cell_id: String,
    payload_block_ids: Vec<String>,
}

fn main() -> Result<(), Box<dyn Error>> {
    run(&Arguments::parse()?)
}

fn run(arguments: &Arguments) -> Result<(), Box<dyn Error>> {
    require_lower_sha256(&arguments.expected_ancestor_sha256)?;
    if arguments.expected_ancestor_sha256 != EXPECTED_ANCESTOR_SHA256 {
        return Err("exact table-create fixture ancestor identity differs".into());
    }
    if arguments
        .ancestor
        .extension()
        .and_then(|value| value.to_str())
        != Some("hwpx")
    {
        return Err("ancestor must be an .hwpx file".into());
    }
    if arguments.output_directory.exists() {
        return Err("output directory already exists".into());
    }
    let parent = arguments
        .output_directory
        .parent()
        .ok_or("output directory has no parent")?;
    if !parent.is_dir() {
        return Err("output parent is not an existing directory".into());
    }

    let ancestor = read_bounded_file(&arguments.ancestor, MAX_FIXTURE_BYTES)?;
    require_digest(&ancestor, EXPECTED_ANCESTOR_SHA256, "ancestor")?;
    let (header, ancestor_section) = read_parts(&ancestor)?;
    let destination_section = replace_once(
        &String::from_utf8(ancestor_section)?,
        EMPTY_TRAILING_PARAGRAPH,
        CREATE_PLACEHOLDER_PARAGRAPH,
    )?
    .into_bytes();
    let template_section = template_section();
    let template_binding = template_binding()?;
    let limits = TableCreateHwpxLimits::default();
    let source = TableCreateHwpxReader::read_context(
        &header,
        &destination_section,
        1,
        &template_section,
        0,
        &template_binding,
        limits,
    )?;
    if source.source_table_count != 1
        || source.template.grid.rows() != 2
        || source.template.grid.columns() != 2
        || source.template.ruling_payload_or_formula_present()
    {
        return Err("table-create source or template profile differs".into());
    }
    fs::create_dir(&arguments.output_directory)?;

    let before_flow = tagged_digest(b"source-flow", &destination_section);
    let cases = cases()
        .into_iter()
        .map(|case| {
            build_case(
                &ancestor,
                &header,
                &destination_section,
                &template_section,
                &template_binding,
                &source,
                &before_flow,
                &arguments.output_directory,
                case,
            )
        })
        .collect::<Result<Vec<_>, _>>()?;
    let manifest = Manifest {
        schema_version: "hwpx-agent.p06-09-table-create-target-fixture/v1",
        source_ancestor_sha256: EXPECTED_ANCESTOR_SHA256,
        destination_section_sha256: hex(Sha256::digest(&destination_section)),
        template_section_sha256: hex(Sha256::digest(&template_section)),
        template_state_sha256: hex(source
            .template
            .state
            .canonical_sha256(TableRulingLimits::default())?),
        template_grid_sha256: hex(source.template.grid.canonical_sha256()?),
        cases,
        actual_hangul_2020: false,
        render: "not_run",
        automation: "not_run",
        differential: "not_run",
    };
    write_create_new(
        &arguments.output_directory.join("fixture-manifest.json"),
        &serde_json::to_vec_pretty(&manifest)?,
    )?;
    require_digest(
        &read_bounded_file(&arguments.ancestor, MAX_FIXTURE_BYTES)?,
        EXPECTED_ANCESTOR_SHA256,
        "ancestor recheck",
    )?;
    println!(
        "schema={} state=pass target_count={} actual_hangul_2020=false",
        manifest.schema_version,
        manifest.cases.len(),
    );
    Ok(())
}

#[allow(clippy::too_many_arguments)]
fn build_case(
    ancestor: &[u8],
    header: &[u8],
    destination_section: &[u8],
    template_section: &[u8],
    template_binding: &TableRulingHwpxBinding,
    source: &hwpx_package::TableCreateHwpxReadback,
    before_flow: &str,
    output_directory: &Path,
    case: Case,
) -> Result<ManifestCase, Box<dyn Error>> {
    let limits = TableCreateHwpxLimits::default();
    let count = usize::try_from(case.rows)?
        .checked_mul(usize::try_from(case.columns)?)
        .ok_or("table-create master count overflow")?;
    let draft = TableCreateHwpxRequestDraft {
        schema_version: TABLE_CREATE_HWPX_SCHEMA_VERSION.to_owned(),
        placeholder_paragraph_ordinal: source.placeholder_paragraph_ordinal,
        template_table_ordinal: source.template_table_ordinal,
        expected_header_sha256: hex(source.header_sha256),
        expected_section_sha256: hex(source.section_sha256),
        expected_template_section_sha256: hex(source.template_section_sha256),
        expected_template_state_sha256: hex(source
            .template
            .state
            .canonical_sha256(TableRulingLimits::default())?),
        expected_template_grid_sha256: hex(source.template.grid.canonical_sha256()?),
        expected_insertion_context_sha256: source.insertion_context_sha256.clone(),
        expected_document_flow_sha256: before_flow.to_owned(),
        target_document_flow_sha256: tagged_digest(b"target-flow", case.id.as_bytes()),
        table_id: id(&format!("{}-table", case.id))?,
        rows: case.rows,
        columns: case.columns,
        master_cell_ids: (0..count)
            .map(|index| id(&format!("{}-cell-{index}", case.id)))
            .collect::<Result<Vec<_>, _>>()?,
        row_heights_hwpunit: case.row_heights_hwpunit.to_vec(),
        column_widths_hwpunit: case.column_widths_hwpunit.to_vec(),
    };
    let request = TableCreateHwpxRequest::from_draft(draft, source, before_flow, limits)?;
    if request.capability_id() != "table.create" {
        return Err("table-create capability identity differs".into());
    }
    let plan = TableCreateHwpxBuilder::build(&request, source, before_flow, limits)?;
    let first = TableCreateHwpxLowerer::lower_at_placeholder(
        header,
        destination_section,
        template_section,
        template_binding,
        before_flow,
        &request,
        &plan,
        limits,
    )?;
    let second = TableCreateHwpxLowerer::lower_at_placeholder(
        header,
        destination_section,
        template_section,
        template_binding,
        before_flow,
        &request,
        &plan,
        limits,
    )?;
    if first.header != second.header
        || first.section != second.section
        || first.binding != second.binding
        || first.receipt != second.receipt
    {
        return Err("table-create target lowering is nondeterministic".into());
    }
    if first.table_ordinal != 1
        || first.receipt.target_rows != case.rows
        || first.receipt.target_columns != case.columns
        || first.receipt.created_master_cell_count != count
        || first.receipt.payload_block_count != 0
        || first.receipt.formula_count != 0
        || !first.receipt.page_split_preserved
    {
        return Err("table-create target receipt differs".into());
    }
    let target_package = replace_parts(ancestor, &first.header, &first.section)?;
    assert_non_selected_parts_preserved(ancestor, &target_package)?;
    let (reopened_header, reopened_section) = read_parts(&target_package)?;
    if reopened_header != first.header || reopened_section != first.section {
        return Err("closed table-create package parts differ".into());
    }
    write_create_new(&output_directory.join(case.file), &target_package)?;
    Ok(ManifestCase {
        case_id: case.id,
        feature_id: "TABLE-001",
        capability_id: request.capability_id(),
        file: case.file,
        sha256: hex(Sha256::digest(&target_package)),
        selected_table_ordinal: first.table_ordinal,
        rows: case.rows,
        columns: case.columns,
        row_heights_hwpunit: case.row_heights_hwpunit,
        column_widths_hwpunit: case.column_widths_hwpunit,
        target_header_sha256: hex(first.receipt.output_header_sha256),
        target_section_sha256: hex(first.receipt.output_section_sha256),
        target_state_sha256: hex(first.receipt.target_state_sha256),
        target_grid_sha256: hex(first.receipt.target_grid_sha256),
        request_sha256: hex(first.receipt.request_sha256),
        plan_sha256: hex(first.receipt.plan_sha256),
        created_master_cell_count: first.receipt.created_master_cell_count,
        payload_block_count: first.receipt.payload_block_count,
        formula_count: first.receipt.formula_count,
        page_split_preserved: first.receipt.page_split_preserved,
        binding: binding_evidence(&first.binding),
    })
}

trait TableCreateTemplateReadbackExt {
    fn ruling_payload_or_formula_present(&self) -> bool;
}

impl TableCreateTemplateReadbackExt for hwpx_package::TableRulingHwpxReadback {
    fn ruling_payload_or_formula_present(&self) -> bool {
        self.payload_block_count != 0 || self.formula_count != 0
    }
}

fn cases() -> [Case; 2] {
    [
        Case {
            id: "arbitrary-3x4-nonuniform",
            file: "table-001-create-3x4-nonuniform.hwpx",
            rows: 3,
            columns: 4,
            row_heights_hwpunit: &[4_000, 5_000, 6_000],
            column_widths_hwpunit: &[7_000, 9_000, 11_000, 13_000],
        },
        Case {
            id: "boundary-1x1",
            file: "table-001-create-1x1.hwpx",
            rows: 1,
            columns: 1,
            row_heights_hwpunit: &[6_000],
            column_widths_hwpunit: &[12_000],
        },
    ]
}

fn template_section() -> Vec<u8> {
    format!(
        concat!(
            r#"<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">"#,
            r#"<hp:p id="900" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0"><hp:run charPrIDRef="0">"#,
            r#"<hp:tbl id="700" zOrder="0" numberingType="TABLE" textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" pageBreak="CELL" repeatHeader="0" rowCnt="2" colCnt="2" cellSpacing="0" borderFillIDRef="3" noAdjust="0">"#,
            r#"<hp:sz width="20000" widthRelTo="ABSOLUTE" height="8000" heightRelTo="ABSOLUTE" protect="0"/>"#,
            r#"<hp:pos treatAsChar="0" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP" horzAlign="LEFT" vertOffset="0" horzOffset="0"/>"#,
            r#"<hp:outMargin left="283" right="283" top="283" bottom="283"/><hp:inMargin left="510" right="510" top="141" bottom="141"/>"#,
            "<hp:tr>{}{}</hp:tr><hp:tr>{}{}</hp:tr>",
            r#"</hp:tbl><hp:t/></hp:run></hp:p></hs:sec>"#,
        ),
        template_cell(0, 0, 8_000, 3_500),
        template_cell(0, 1, 12_000, 3_500),
        template_cell(1, 0, 8_000, 4_500),
        template_cell(1, 1, 12_000, 4_500),
    )
    .into_bytes()
}

fn template_cell(row: u32, column: u32, width: u32, height: u32) -> String {
    format!(
        concat!(
            r#"<hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="0" borderFillIDRef="3">"#,
            r#"<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">"#,
            r#"<hp:p id="0" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0"><hp:run charPrIDRef="0"><hp:t/></hp:run></hp:p></hp:subList>"#,
            r#"<hp:cellAddr colAddr="{column}" rowAddr="{row}"/><hp:cellSpan colSpan="1" rowSpan="1"/><hp:cellSz width="{width}" height="{height}"/>"#,
            r#"<hp:cellMargin left="510" right="510" top="141" bottom="141"/></hp:tc>"#,
        ),
        column = column,
        row = row,
        width = width,
        height = height
    )
}

fn template_binding() -> Result<TableRulingHwpxBinding, Box<dyn Error>> {
    Ok(TableRulingHwpxBinding {
        table_id: id("table-create-template")?,
        row_boundaries_hwpunit: vec![0, 3_500, 8_000],
        column_boundaries_hwpunit: vec![0, 8_000, 20_000],
        cells: (0..4)
            .map(|index| {
                Ok(TableRulingHwpxCellBinding {
                    master_cell_id: id(&format!("table-create-template-cell-{index}"))?,
                    payload_block_ids: Vec::new(),
                })
            })
            .collect::<Result<Vec<_>, Box<dyn Error>>>()?,
    })
}

fn binding_evidence(binding: &TableRulingHwpxBinding) -> BindingEvidence {
    BindingEvidence {
        table_id: binding.table_id.as_str().to_owned(),
        row_boundaries_hwpunit: binding.row_boundaries_hwpunit.clone(),
        column_boundaries_hwpunit: binding.column_boundaries_hwpunit.clone(),
        cells: binding
            .cells
            .iter()
            .map(|cell| BindingCellEvidence {
                master_cell_id: cell.master_cell_id.as_str().to_owned(),
                payload_block_ids: cell
                    .payload_block_ids
                    .iter()
                    .map(|identifier| identifier.as_str().to_owned())
                    .collect(),
            })
            .collect(),
    }
}

fn read_parts(source: &[u8]) -> Result<(Vec<u8>, Vec<u8>), Box<dyn Error>> {
    let mut archive = BoundedZipReader::open(Cursor::new(source), PackageLimits::default())?;
    Ok((
        read_part(&mut archive, "Contents/header.xml")?,
        read_part(&mut archive, "Contents/section0.xml")?,
    ))
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

fn replace_parts(source: &[u8], header: &[u8], section: &[u8]) -> Result<Vec<u8>, Box<dyn Error>> {
    let mut reader = BoundedZipReader::open(Cursor::new(source), PackageLimits::default())?;
    let entries = reader.entries().to_vec();
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    for entry in entries {
        let method = match entry.compression {
            Compression::Stored => CompressionMethod::Stored,
            Compression::Deflated => CompressionMethod::Deflated,
        };
        let mut options = SimpleFileOptions::default()
            .compression_method(method)
            .last_modified_time(DateTime::default())
            .system(zip::System::Unix)
            .unix_permissions(0o644);
        if method == CompressionMethod::Deflated {
            options = options.compression_level(Some(NORMALIZED_DEFLATE_LEVEL));
        }
        writer.start_file(entry.path.as_str(), options)?;
        let bytes = match entry.path.as_str() {
            "Contents/header.xml" => header.to_vec(),
            "Contents/section0.xml" => section.to_vec(),
            _ => reader.read_entry(entry.index)?,
        };
        writer.write_all(&bytes)?;
    }
    let output = writer.finish()?.into_inner();
    if output.len() as u64 > MAX_FIXTURE_BYTES {
        return Err("table-create target package exceeds fixture bound".into());
    }
    Ok(output)
}

fn assert_non_selected_parts_preserved(source: &[u8], target: &[u8]) -> Result<(), Box<dyn Error>> {
    let mut source_archive = BoundedZipReader::open(Cursor::new(source), PackageLimits::default())?;
    let mut target_archive = BoundedZipReader::open(Cursor::new(target), PackageLimits::default())?;
    if source_archive.entries().len() != target_archive.entries().len() {
        return Err("table-create target package entry count differs".into());
    }
    for entry in source_archive.entries().to_vec() {
        if matches!(
            entry.path.as_str(),
            "Contents/header.xml" | "Contents/section0.xml"
        ) {
            continue;
        }
        let target_index = target_archive
            .entries()
            .iter()
            .find(|candidate| candidate.path == entry.path)
            .map(|candidate| candidate.index)
            .ok_or("table-create target package entry is missing")?;
        if source_archive.read_entry(entry.index)? != target_archive.read_entry(target_index)? {
            return Err(
                format!("non-selected package part differs: {}", entry.path.as_str()).into(),
            );
        }
    }
    Ok(())
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

fn write_create_new(path: &Path, bytes: &[u8]) -> Result<(), Box<dyn Error>> {
    let mut file = OpenOptions::new().write(true).create_new(true).open(path)?;
    file.write_all(bytes)?;
    file.sync_all()?;
    Ok(())
}

fn replace_once(source: &str, before: &str, after: &str) -> Result<String, Box<dyn Error>> {
    if before.is_empty() || source.matches(before).count() != 1 {
        return Err("table-create fixture replacement cardinality differs".into());
    }
    Ok(source.replacen(before, after, 1))
}

fn tagged_digest(domain: &[u8], payload: &[u8]) -> String {
    let mut digest = Sha256::new();
    digest.update(b"hwpx-agent.p06-09-table-create-target-flow/v1\0");
    digest.update(domain);
    digest.update(b"\0");
    digest.update(payload);
    hex(digest.finalize())
}

fn require_digest(bytes: &[u8], expected: &str, label: &str) -> Result<(), Box<dyn Error>> {
    if hex(Sha256::digest(bytes)) != expected {
        return Err(format!("{label} SHA-256 mismatch").into());
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

fn id(value: &str) -> Result<LogicalId, Box<dyn Error>> {
    Ok(LogicalId::parse(value)?)
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
    fn target_case_profiles_cover_nonuniform_and_minimum_boundaries() {
        let profiles = cases();
        assert_eq!(profiles[0].row_heights_hwpunit, [4_000, 5_000, 6_000]);
        assert_eq!(
            profiles[0].column_widths_hwpunit,
            [7_000, 9_000, 11_000, 13_000]
        );
        assert_eq!((profiles[1].rows, profiles[1].columns), (1, 1));
    }

    #[test]
    fn exact_template_is_blank_unmerged_two_by_two() {
        let section = String::from_utf8(template_section()).unwrap();
        assert_eq!(section.matches("<hp:tbl ").count(), 1);
        assert_eq!(section.matches("<hp:tr>").count(), 2);
        assert_eq!(section.matches("<hp:tc ").count(), 4);
        assert_eq!(section.matches("<hp:t/>").count(), 5);
        assert!(section.contains("repeatHeader=\"0\" rowCnt=\"2\" colCnt=\"2\""));
        assert!(!section.contains("<hp:fieldBegin"));
    }
}
