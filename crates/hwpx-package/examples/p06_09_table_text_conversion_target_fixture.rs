use std::env;
use std::error::Error;
use std::fs::{self, OpenOptions};
use std::io::{Cursor, Write as _};
use std::path::{Path, PathBuf};

use domain_ir::{LogicalId, TableDelimiter, TableLineEnding, TableRulingLimits};
use hwpx_package::{
    BoundedZipReader, Compression, PackageLimits, TABLE_TABLE_TO_TEXT_HWPX_SCHEMA_VERSION,
    TABLE_TEXT_TO_TABLE_HWPX_SCHEMA_VERSION, TableRulingHwpxBinding, TableRulingHwpxCellBinding,
    TableTableToTextHwpxBuilder, TableTableToTextHwpxLimits, TableTableToTextHwpxLowerer,
    TableTableToTextHwpxReader, TableTableToTextHwpxRequest, TableTableToTextHwpxRequestDraft,
    TableTextToTableHwpxBuilder, TableTextToTableHwpxLimits, TableTextToTableHwpxLowerer,
    TableTextToTableHwpxReader, TableTextToTableHwpxRequest, TableTextToTableHwpxRequestDraft,
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
    table_file: &'static str,
    text_file: &'static str,
    source_paragraph: &'static str,
    delimiter: TableDelimiter,
    line_ending: TableLineEnding,
    rows: u32,
    columns: u32,
    row_heights_hwpunit: &'static [u32],
    column_widths_hwpunit: &'static [u32],
    nonempty_cell_count: usize,
}

struct BuiltTableCase {
    case: Case,
    header: Vec<u8>,
    section: Vec<u8>,
    binding: TableRulingHwpxBinding,
    package: Vec<u8>,
    manifest: ManifestCase,
}

#[derive(Serialize)]
struct Manifest {
    schema_version: &'static str,
    source_ancestor_sha256: &'static str,
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
    case_id: String,
    source_case_id: &'static str,
    feature_id: &'static str,
    capability_id: &'static str,
    file: &'static str,
    sha256: String,
    operation_table_ordinal: usize,
    target_paragraph_ordinal: Option<usize>,
    rows: u32,
    columns: u32,
    row_heights_hwpunit: &'static [u32],
    column_widths_hwpunit: &'static [u32],
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
        return Err("exact table text-conversion fixture ancestor identity differs".into());
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
    let (header, _) = read_parts(&ancestor)?;
    let template_section = template_section();
    let template_binding = template_binding()?;
    let template = TableTextToTableHwpxReader::read_context(
        &header,
        &source_section(&read_parts(&ancestor)?.1, cases()[0].source_paragraph)?,
        1,
        cases()[0].delimiter,
        &template_section,
        0,
        &template_binding,
        TableTextToTableHwpxLimits::default(),
    )?;
    fs::create_dir(&arguments.output_directory)?;

    let mut manifest_cases = Vec::with_capacity(4);
    for case in cases() {
        let built = build_table_case(
            &ancestor,
            &header,
            &template_section,
            &template_binding,
            case,
        )?;
        write_create_new(
            &arguments.output_directory.join(built.case.table_file),
            &built.package,
        )?;
        let text_manifest = build_text_case(&built, &arguments.output_directory)?;
        manifest_cases.push(built.manifest);
        manifest_cases.push(text_manifest);
    }
    let manifest = Manifest {
        schema_version: "hwpx-agent.p06-09-table-text-conversion-target-fixture/v1",
        source_ancestor_sha256: EXPECTED_ANCESTOR_SHA256,
        template_section_sha256: hex(Sha256::digest(&template_section)),
        template_state_sha256: hex(template
            .template
            .state
            .canonical_sha256(TableRulingLimits::default())?),
        template_grid_sha256: hex(template.template.grid.canonical_sha256()?),
        cases: manifest_cases,
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

fn build_table_case(
    ancestor: &[u8],
    header: &[u8],
    template_section: &[u8],
    template_binding: &TableRulingHwpxBinding,
    case: Case,
) -> Result<BuiltTableCase, Box<dyn Error>> {
    let (_, ancestor_section) = read_parts(ancestor)?;
    let section = source_section(&ancestor_section, case.source_paragraph)?;
    let limits = TableTextToTableHwpxLimits::default();
    let source = TableTextToTableHwpxReader::read_context(
        header,
        &section,
        1,
        case.delimiter,
        template_section,
        0,
        template_binding,
        limits,
    )?;
    if source.source_table_count != 1
        || source.text_grid.row_count() != usize::try_from(case.rows)?
        || source.text_grid.column_count() != usize::try_from(case.columns)?
    {
        return Err("text-to-table source profile differs".into());
    }
    let count = usize::try_from(case.rows)?
        .checked_mul(usize::try_from(case.columns)?)
        .ok_or("text-to-table master count overflow")?;
    let before_flow = tagged_digest(b"text-to-table-source-flow", &section);
    let draft = table_request_draft(case, &source, &before_flow, count, &limits)?;
    let request = TableTextToTableHwpxRequest::from_draft(draft, &source, &before_flow, limits)?;
    let plan = TableTextToTableHwpxBuilder::build(&request, &source, &before_flow, limits)?;
    let first = TableTextToTableHwpxLowerer::lower(
        header,
        &section,
        template_section,
        template_binding,
        &before_flow,
        &request,
        &plan,
        limits,
    )?;
    let second = TableTextToTableHwpxLowerer::lower(
        header,
        &section,
        template_section,
        template_binding,
        &before_flow,
        &request,
        &plan,
        limits,
    )?;
    if first.header != second.header
        || first.section != second.section
        || first.binding != second.binding
        || first.receipt != second.receipt
    {
        return Err("text-to-table target lowering is nondeterministic".into());
    }
    if request.capability_id() != "table.text_to_table"
        || first.table_ordinal != 1
        || first.receipt.target_rows != case.rows
        || first.receipt.target_columns != case.columns
        || first.receipt.nonempty_cell_count != case.nonempty_cell_count
        || first.receipt.payload_block_count != case.nonempty_cell_count
        || first.receipt.formula_count != 0
        || !first.receipt.page_split_preserved
    {
        return Err("text-to-table target receipt differs".into());
    }
    let package = replace_parts(ancestor, &first.header, &first.section)?;
    assert_non_selected_parts_preserved(ancestor, &package)?;
    let (reopened_header, reopened_section) = read_parts(&package)?;
    if reopened_header != first.header || reopened_section != first.section {
        return Err("closed text-to-table package parts differ".into());
    }
    let manifest = table_manifest(
        case,
        &package,
        request.capability_id(),
        first.table_ordinal,
        count,
        &first.receipt,
        &first.binding,
    );
    Ok(BuiltTableCase {
        case,
        header: first.header,
        section: first.section,
        binding: first.binding,
        package,
        manifest,
    })
}

fn table_request_draft(
    case: Case,
    source: &hwpx_package::TableTextToTableHwpxReadback,
    before_flow: &str,
    count: usize,
    limits: &TableTextToTableHwpxLimits,
) -> Result<TableTextToTableHwpxRequestDraft, Box<dyn Error>> {
    let payload_block_ids = source
        .text_grid
        .rows()
        .iter()
        .flatten()
        .enumerate()
        .map(|(index, value)| {
            if value.is_empty() {
                Ok(None)
            } else {
                Ok(Some(id(&format!("{}-payload-{index}", case.id))?))
            }
        })
        .collect::<Result<Vec<_>, Box<dyn Error>>>()?;
    Ok(TableTextToTableHwpxRequestDraft {
        schema_version: TABLE_TEXT_TO_TABLE_HWPX_SCHEMA_VERSION.to_owned(),
        paragraph_ordinal: source.paragraph_ordinal,
        template_table_ordinal: source.template_table_ordinal,
        delimiter: source.delimiter,
        expected_header_sha256: hex(source.header_sha256),
        expected_section_sha256: hex(source.section_sha256),
        expected_template_section_sha256: hex(source.template_section_sha256),
        expected_template_state_sha256: hex(source
            .template
            .state
            .canonical_sha256(limits.create.ruling.ruling)?),
        expected_template_grid_sha256: hex(source.template.grid.canonical_sha256()?),
        expected_paragraph_sha256: hex(source.paragraph_sha256),
        expected_paragraph_context_sha256: source.paragraph_context_sha256.clone(),
        expected_text_grid_sha256: hex(source.text_grid.canonical_sha256(limits.text)?),
        expected_document_flow_sha256: before_flow.to_owned(),
        target_document_flow_sha256: tagged_digest(
            b"text-to-table-target-flow",
            case.id.as_bytes(),
        ),
        table_id: id(&format!("{}-table", case.id))?,
        master_cell_ids: (0..count)
            .map(|index| id(&format!("{}-cell-{index}", case.id)))
            .collect::<Result<Vec<_>, _>>()?,
        payload_block_ids,
        row_heights_hwpunit: case.row_heights_hwpunit.to_vec(),
        column_widths_hwpunit: case.column_widths_hwpunit.to_vec(),
    })
}

fn table_manifest(
    case: Case,
    package: &[u8],
    capability_id: &'static str,
    table_ordinal: usize,
    master_cell_count: usize,
    receipt: &hwpx_package::TableTextToTableHwpxLoweringReceipt,
    binding: &TableRulingHwpxBinding,
) -> ManifestCase {
    ManifestCase {
        case_id: format!("table-004-{}", case.id),
        source_case_id: case.id,
        feature_id: "TABLE-004",
        capability_id,
        file: case.table_file,
        sha256: hex(Sha256::digest(package)),
        operation_table_ordinal: table_ordinal,
        target_paragraph_ordinal: None,
        rows: case.rows,
        columns: case.columns,
        row_heights_hwpunit: case.row_heights_hwpunit,
        column_widths_hwpunit: case.column_widths_hwpunit,
        target_header_sha256: hex(receipt.output_header_sha256),
        target_section_sha256: hex(receipt.output_section_sha256),
        state_sha256: hex(receipt.target_state_sha256),
        grid_sha256: hex(receipt.target_grid_sha256),
        text_grid_sha256: hex(receipt.text_grid_sha256),
        serialized_text_sha256: None,
        target_paragraph_sha256: None,
        request_sha256: hex(receipt.request_sha256),
        plan_sha256: hex(receipt.plan_sha256),
        master_cell_count,
        payload_block_count: receipt.payload_block_count,
        formula_count: receipt.formula_count,
        target_table_count: receipt.target_table_count,
        page_split_preserved: receipt.page_split_preserved,
        binding: binding_evidence(binding),
    }
}

fn build_text_case(
    built: &BuiltTableCase,
    output_directory: &Path,
) -> Result<ManifestCase, Box<dyn Error>> {
    let limits = TableTableToTextHwpxLimits::default();
    let source = TableTableToTextHwpxReader::read_context(
        &built.header,
        &built.section,
        1,
        &built.binding,
        built.case.delimiter,
        built.case.line_ending,
        limits,
    )?;
    let before_flow = tagged_digest(b"table-to-text-source-flow", &built.section);
    let draft = TableTableToTextHwpxRequestDraft {
        schema_version: TABLE_TABLE_TO_TEXT_HWPX_SCHEMA_VERSION.to_owned(),
        table_ordinal: source.table_ordinal,
        expected_paragraph_ordinal: source.paragraph_ordinal,
        delimiter: source.delimiter,
        line_ending: source.line_ending,
        expected_header_sha256: hex(source.header_sha256),
        expected_section_sha256: hex(source.section_sha256),
        expected_wrapper_sha256: hex(source.wrapper_sha256),
        expected_wrapper_context_sha256: source.wrapper_context_sha256.clone(),
        expected_table_content_sha256: hex(source.ruling.table_content_sha256),
        expected_source_state_sha256: hex(source
            .ruling
            .state
            .canonical_sha256(limits.ruling.ruling)?),
        expected_source_grid_sha256: hex(source.ruling.grid.canonical_sha256()?),
        expected_text_grid_sha256: hex(source.text_grid.canonical_sha256(limits.text)?),
        expected_serialized_text_sha256: hex(source.serialized_text_sha256),
        expected_target_paragraph_sha256: hex(source.target_paragraph_sha256),
        expected_source_table_count: source.source_table_count,
        expected_document_flow_sha256: before_flow.clone(),
        target_document_flow_sha256: tagged_digest(
            b"table-to-text-target-flow",
            built.case.id.as_bytes(),
        ),
        output_text_block_id: id(&format!("{}-text-block", built.case.id))?,
    };
    let request = TableTableToTextHwpxRequest::from_draft(draft, &source, &before_flow, limits)?;
    let plan = TableTableToTextHwpxBuilder::build(&request, &source, &before_flow, limits)?;
    let first = TableTableToTextHwpxLowerer::lower(
        &built.header,
        &built.section,
        &built.binding,
        built.case.delimiter,
        built.case.line_ending,
        &before_flow,
        &request,
        &plan,
        limits,
    )?;
    let second = TableTableToTextHwpxLowerer::lower(
        &built.header,
        &built.section,
        &built.binding,
        built.case.delimiter,
        built.case.line_ending,
        &before_flow,
        &request,
        &plan,
        limits,
    )?;
    if first.header != second.header
        || first.section != second.section
        || first.text != second.text
        || first.receipt != second.receipt
    {
        return Err("table-to-text target lowering is nondeterministic".into());
    }
    if request.capability_id() != "table.table_to_text"
        || first.receipt.source_table_count != 2
        || first.receipt.target_table_count != 1
        || first.receipt.rows != built.case.rows
        || first.receipt.columns != built.case.columns
        || first.receipt.payload_block_count != built.case.nonempty_cell_count
        || first.receipt.formula_count != 0
    {
        return Err("table-to-text target receipt differs".into());
    }
    let package = replace_parts(&built.package, &first.header, &first.section)?;
    assert_non_selected_parts_preserved(&built.package, &package)?;
    let (reopened_header, reopened_section) = read_parts(&package)?;
    if reopened_header != first.header || reopened_section != first.section {
        return Err("closed table-to-text package parts differ".into());
    }
    write_create_new(&output_directory.join(built.case.text_file), &package)?;
    Ok(text_manifest(
        built.case,
        &package,
        request.capability_id(),
        source.table_ordinal,
        &first.receipt,
        &built.binding,
    ))
}

fn text_manifest(
    case: Case,
    package: &[u8],
    capability_id: &'static str,
    table_ordinal: usize,
    receipt: &hwpx_package::TableTableToTextHwpxLoweringReceipt,
    binding: &TableRulingHwpxBinding,
) -> ManifestCase {
    ManifestCase {
        case_id: format!("table-005-{}", case.id),
        source_case_id: case.id,
        feature_id: "TABLE-005",
        capability_id,
        file: case.text_file,
        sha256: hex(Sha256::digest(package)),
        operation_table_ordinal: table_ordinal,
        target_paragraph_ordinal: Some(receipt.paragraph_ordinal),
        rows: case.rows,
        columns: case.columns,
        row_heights_hwpunit: case.row_heights_hwpunit,
        column_widths_hwpunit: case.column_widths_hwpunit,
        target_header_sha256: hex(receipt.output_header_sha256),
        target_section_sha256: hex(receipt.output_section_sha256),
        state_sha256: hex(receipt.source_state_sha256),
        grid_sha256: hex(receipt.source_grid_sha256),
        text_grid_sha256: hex(receipt.text_grid_sha256),
        serialized_text_sha256: Some(hex(receipt.serialized_text_sha256)),
        target_paragraph_sha256: Some(hex(receipt.target_paragraph_sha256)),
        request_sha256: hex(receipt.request_sha256),
        plan_sha256: hex(receipt.plan_sha256),
        master_cell_count: receipt.master_cell_count,
        payload_block_count: receipt.payload_block_count,
        formula_count: receipt.formula_count,
        target_table_count: receipt.target_table_count,
        page_split_preserved: true,
        binding: binding_evidence(binding),
    }
}

fn cases() -> [Case; 2] {
    [
        Case {
            id: "quoted-multiline-3x2",
            table_file: "table-004-text-to-table-quoted-multiline-3x2.hwpx",
            text_file: "table-005-table-to-text-quoted-multiline-3x2.hwpx",
            source_paragraph: concat!(
                r#"<hp:p id="0" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0"><hp:run charPrIDRef="0">"#,
                r#"<hp:t>name,amount<hp:lineBreak/>&quot;한글,값&quot;,7<hp:lineBreak/>&quot;multi<hp:lineBreak/>line&quot;,</hp:t></hp:run></hp:p>"#,
            ),
            delimiter: TableDelimiter::Comma,
            line_ending: TableLineEnding::CrLf,
            rows: 3,
            columns: 2,
            row_heights_hwpunit: &[4_000, 5_000, 6_000],
            column_widths_hwpunit: &[12_000, 16_000],
            nonempty_cell_count: 5,
        },
        Case {
            id: "boundary-1x1",
            table_file: "table-004-text-to-table-boundary-1x1.hwpx",
            text_file: "table-005-table-to-text-boundary-1x1.hwpx",
            source_paragraph: concat!(
                r#"<hp:p id="0" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">"#,
                r#"<hp:run charPrIDRef="0"><hp:t>only</hp:t></hp:run></hp:p>"#,
            ),
            delimiter: TableDelimiter::Semicolon,
            line_ending: TableLineEnding::Lf,
            rows: 1,
            columns: 1,
            row_heights_hwpunit: &[6_000],
            column_widths_hwpunit: &[14_000],
            nonempty_cell_count: 1,
        },
    ]
}

fn source_section(ancestor_section: &[u8], paragraph: &str) -> Result<Vec<u8>, Box<dyn Error>> {
    Ok(replace_once(
        &String::from_utf8(ancestor_section.to_vec())?,
        EMPTY_TRAILING_PARAGRAPH,
        paragraph,
    )?
    .into_bytes())
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
        height = height,
    )
}

fn template_binding() -> Result<TableRulingHwpxBinding, Box<dyn Error>> {
    Ok(TableRulingHwpxBinding {
        table_id: id("table-text-conversion-template")?,
        row_boundaries_hwpunit: vec![0, 3_500, 8_000],
        column_boundaries_hwpunit: vec![0, 8_000, 20_000],
        cells: (0..4)
            .map(|index| {
                Ok(TableRulingHwpxCellBinding {
                    master_cell_id: id(&format!("table-text-conversion-template-cell-{index}"))?,
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
        return Err("table text-conversion target package exceeds fixture bound".into());
    }
    Ok(output)
}

fn assert_non_selected_parts_preserved(source: &[u8], target: &[u8]) -> Result<(), Box<dyn Error>> {
    let mut source_archive = BoundedZipReader::open(Cursor::new(source), PackageLimits::default())?;
    let mut target_archive = BoundedZipReader::open(Cursor::new(target), PackageLimits::default())?;
    if source_archive.entries().len() != target_archive.entries().len() {
        return Err("table text-conversion target package entry count differs".into());
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
            .ok_or("table text-conversion target package entry is missing")?;
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
        return Err("table text-conversion fixture replacement cardinality differs".into());
    }
    Ok(source.replacen(before, after, 1))
}

fn tagged_digest(domain: &[u8], payload: &[u8]) -> String {
    let mut digest = Sha256::new();
    digest.update(b"hwpx-agent.p06-09-table-text-conversion-target-flow/v1\0");
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
    fn target_profiles_cover_quoted_multiline_and_minimum_boundaries() {
        let profiles = cases();
        assert_eq!((profiles[0].rows, profiles[0].columns), (3, 2));
        assert_eq!(profiles[0].nonempty_cell_count, 5);
        assert_eq!((profiles[1].rows, profiles[1].columns), (1, 1));
        assert_eq!(profiles[1].delimiter, TableDelimiter::Semicolon);
    }

    #[test]
    fn exact_template_is_native_run_direct_blank_two_by_two() {
        let section = String::from_utf8(template_section()).unwrap();
        assert_eq!(section.matches("<hp:tbl ").count(), 1);
        assert_eq!(section.matches("<hp:tr>").count(), 2);
        assert_eq!(section.matches("<hp:tc ").count(), 4);
        assert_eq!(section.matches("<hp:t/>").count(), 5);
        assert!(!section.contains("<hp:ctrl>"));
        assert_eq!(section.matches("pageBreak=\"0\"").count(), 5);
    }

    #[test]
    fn multiline_source_is_bound_to_csv_quotes() {
        let source = cases()[0].source_paragraph;
        assert_eq!(source.matches("<hp:lineBreak/>").count(), 3);
        assert!(source.contains("&quot;한글,값&quot;,7"));
        assert!(source.contains("&quot;multi"));
    }
}
