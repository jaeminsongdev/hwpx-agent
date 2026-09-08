use std::env;
use std::error::Error;
use std::fmt::Write as _;
use std::fs::{self, OpenOptions};
use std::io::{Cursor, Write as _};
use std::path::{Path, PathBuf};

use domain_ir::{CaptionSide, TablePageSplitPolicy};
use hwpx_package::{
    BoundedZipReader, Compression, IdIndex, IdIndexLimits, IdIssueKind, IdRuleProfile,
    PackageGraph, PackageGraphLimits, PackageLimits, PreservingXmlDocument, TableCaptionHwpxTarget,
    TablePaginationHwpxLimits, TablePaginationHwpxLowerer, TablePaginationHwpxReader,
    TablePaginationHwpxTarget,
};
use sha2::{Digest as _, Sha256};
use zip::write::SimpleFileOptions;
use zip::{CompressionMethod, DateTime, ZipWriter};

const MAX_FIXTURE_BYTES: u64 = 8 * 1024 * 1024;
const NORMALIZED_DEFLATE_LEVEL: i64 = 6;
const EXPECTED_INPUT_SHA256: &str =
    "ec08dc8e07dfc1b18c5916b44917b00d27da9905bea26f57e9b16991396c1ec7";
const TARGET_PREVIEW: &[u8] = concat!(
    "P06-07 ALLOW TOP\r\n",
    "P06-07 A HEADER 1\tP06-07 A HEADER 2\r\n",
    "P06-07 A LONG CELL 001..064\r\n",
    "P06-07 AVOID-ROW BOTTOM\r\n",
    "P06-07 B MERGED\r\n",
    "P06-07 B NESTED\r\n",
    "P06-07 B EQUATION\r\n",
    "P06-07 BEFORE\r\nP06-07 EXACT\r\nP06-07 AFTER\r\n\r\n"
)
.as_bytes();

#[derive(Debug)]
struct Arguments {
    input: PathBuf,
    expected_input_sha256: String,
    output: PathBuf,
}

impl Arguments {
    fn parse() -> Result<Self, Box<dyn Error>> {
        let mut values = env::args_os();
        let _program = values.next();
        let result = Self {
            input: path_argument(&mut values, "input HWPX")?,
            expected_input_sha256: string_argument(&mut values, "expected input SHA-256")?,
            output: path_argument(&mut values, "output HWPX")?,
        };
        if values.next().is_some() {
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
        return Err("exact P06-07 source identity differs".into());
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
    if source_inspection.table_count != 1 {
        return Err("exact source table cardinality drifted".into());
    }

    let structural_section = build_structural_section(&source_inspection.section)?;
    let target_section = lower_pagination_targets(&structural_section)?;
    require_target_section(&target_section)?;
    let target = replace_parts(&source, &target_section)?;
    let target_inspection = inspect_package(&target)?;
    require_target_section(&target_inspection.section)?;
    if target_inspection.part_count != source_inspection.part_count
        || target_inspection.preview != TARGET_PREVIEW
        || target_inspection.table_count != 6
    {
        return Err("target package identity drifted".into());
    }

    require_digest(
        &read_bounded_file(&arguments.input, MAX_FIXTURE_BYTES)?,
        EXPECTED_INPUT_SHA256,
        "input recheck",
    )?;
    write_create_new(&arguments.output, &target)?;
    println!(
        concat!(
            "schema=hwpx-agent.p06-07-table-pagination-target/v1 state=pass ",
            "input_sha256={} output_sha256={} section_sha256={} tables=6 ",
            "top_level_tables=5 nested_tables=1 captions=5 equation_objects=1 ",
            "line_caches=0 boundary_candidates=before,exact,after"
        ),
        EXPECTED_INPUT_SHA256,
        hex(Sha256::digest(&target).into()),
        hex(Sha256::digest(&target_section).into()),
    );
    Ok(())
}

#[derive(Debug)]
struct PackageInspection {
    part_count: usize,
    section: Vec<u8>,
    preview: Vec<u8>,
    table_count: usize,
}

fn inspect_package(bytes: &[u8]) -> Result<PackageInspection, Box<dyn Error>> {
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    if graph.parts.len() != reader.entries().len() {
        return Err("package graph cardinality mismatch".into());
    }
    let section = read_part(&mut reader, "Contents/section0.xml")?;
    let id_result = IdIndex::build(
        &mut reader,
        &graph,
        IdRuleProfile::current_hancom_2020_formula_v3(),
        IdIndexLimits::default(),
    );
    if let Err(error) = id_result
        && !is_exact_equation_profile_gap(&error, &section)?
    {
        return Err(error.into());
    }
    let preview = read_part(&mut reader, "Preview/PrvText.txt")?;
    let table_count = TablePaginationHwpxReader::count_in_section(
        &section,
        TablePaginationHwpxLimits::default(),
    )?;
    Ok(PackageInspection {
        part_count: graph.parts.len(),
        section,
        preview,
        table_count,
    })
}

fn is_exact_equation_profile_gap(
    error: &hwpx_package::IdIndexError,
    section: &[u8],
) -> Result<bool, Box<dyn Error>> {
    let Some(report) = error.validation() else {
        return Ok(false);
    };
    let [issue] = report.issues() else {
        return Ok(false);
    };
    if issue.kind() != IdIssueKind::UnknownIdLikeAttribute
        || issue.source().part().as_str() != "Contents/section0.xml"
    {
        return Ok(false);
    }
    let document = PreservingXmlDocument::parse(section)?;
    let Some(element) = document.elements().get(issue.source().element_index()) else {
        return Ok(false);
    };
    let Some(attribute) = element.attributes().get(issue.source().attribute_index()) else {
        return Ok(false);
    };
    let value_span = issue.source().value_span();
    let value = section.get(value_span.start()..value_span.end());
    Ok(
        element.name().namespace() == Some("http://www.hancom.co.kr/hwpml/2011/paragraph")
            && element.name().local_name() == "equation"
            && attribute.name().namespace().is_none()
            && attribute.name().local_name() == "id"
            && value == Some(b"2100000100"),
    )
}

fn build_structural_section(source: &[u8]) -> Result<Vec<u8>, Box<dyn Error>> {
    let source = String::from_utf8(source.to_vec())?;
    let table_start = source.find("<hp:tbl ").ok_or("source table is missing")?;
    let table_end = source[table_start..]
        .find("</hp:tbl>")
        .map(|offset| table_start + offset + "</hp:tbl>".len())
        .ok_or("source table end is missing")?;
    if source[table_end..].contains("<hp:tbl ") {
        return Err("source must contain one table".into());
    }

    let allow = build_allow_table(2_100_000_001);
    let avoid_row = build_avoid_row_table(2_100_000_002);
    let before = build_boundary_case(2_100_000_004, "BEFORE", CaptionSide::Top);
    let exact = build_boundary_case(2_100_000_005, "EXACT", CaptionSide::Top);
    let after = build_boundary_case(2_100_000_006, "AFTER", CaptionSide::Bottom);

    let mut target = String::with_capacity(source.len() + 160_000);
    target.push_str(&source[..table_start]);
    target.push_str(&allow);
    target.push_str(&source[table_end..]);
    let closing = target
        .rfind("</hs:sec>")
        .ok_or("section closing tag is missing")?;
    let mut append = String::with_capacity(120_000);
    append.push_str(&page_break_paragraph("P06-07 B START"));
    append.push_str(&table_paragraph(&avoid_row));
    append.push_str(&boundary_group("BEFORE", 34, &before));
    append.push_str(&boundary_group("EXACT", 35, &exact));
    append.push_str(&boundary_group("AFTER", 36, &after));
    target.insert_str(closing, &append);
    let (target, _) = strip_elements(target, "<hp:linesegarray>", "</hp:linesegarray>")?;
    if target.contains("<hp:linesegarray>") {
        return Err("renderer line cache removal drifted".into());
    }
    Ok(target.into_bytes())
}

fn build_allow_table(id: u32) -> String {
    let header = format!(
        "<hp:tr>{}{}</hp:tr>",
        text_cell("P06-07 A HEADER 1", 0, 0, 1, 1, 9_921, 1_400, false),
        text_cell("P06-07 A HEADER 2", 0, 1, 1, 1, 9_922, 1_400, false),
    );
    let mut paragraphs = Vec::with_capacity(64);
    for index in 1..=64 {
        paragraphs.push(text_paragraph(&format!(
            "P06-07 A LONG CELL {index:03} — CELL split continuation"
        )));
    }
    let body = format!(
        "<hp:tr>{}</hp:tr>",
        content_cell(&paragraphs.concat(), 1, 0, 2, 1, 19_843, 1_300, false)
    );
    table(
        id,
        2,
        2,
        2_700,
        Some(caption("P06-07 ALLOW TOP", CaptionSide::Top)),
        &(header + &body),
    )
}

fn build_avoid_row_table(id: u32) -> String {
    let header = format!(
        "<hp:tr>{}{}</hp:tr>",
        text_cell("P06-07 B HEADER 1", 0, 0, 1, 1, 9_921, 1_400, false),
        text_cell("P06-07 B HEADER 2", 0, 1, 1, 1, 9_922, 1_400, false),
    );
    let mut merged_paragraphs = Vec::with_capacity(18);
    for index in 1..=18 {
        merged_paragraphs.push(text_paragraph(&format!("P06-07 B MERGED {index:03}")));
    }
    let merged = format!(
        "<hp:tr>{}</hp:tr>",
        content_cell(
            &merged_paragraphs.concat(),
            1,
            0,
            2,
            1,
            19_843,
            27_000,
            false
        )
    );
    let mut ordinary_rows = String::with_capacity(30 * 600);
    for index in 1..=30 {
        let _ = write!(
            &mut ordinary_rows,
            "<hp:tr>{}</hp:tr>",
            text_cell(
                &format!("P06-07 B ROW {index:03}"),
                index + 1,
                0,
                2,
                1,
                19_843,
                1_300,
                false,
            )
        );
    }
    let nested = nested_table(2_100_000_003);
    let nested_row = format!(
        "<hp:tr>{}</hp:tr>",
        content_cell(
            &format!(
                "{}<hp:p id=\"0\" paraPrIDRef=\"0\" styleIDRef=\"0\" pageBreak=\"0\" columnBreak=\"0\" merged=\"0\"><hp:run charPrIDRef=\"0\">{}</hp:run></hp:p>",
                text_paragraph("P06-07 B NESTED"),
                nested
            ),
            32,
            0,
            2,
            1,
            19_843,
            9_000,
            false,
        )
    );
    let equation_row = format!(
        "<hp:tr>{}</hp:tr>",
        content_cell(
            &format!(
                "{}<hp:p id=\"0\" paraPrIDRef=\"0\" styleIDRef=\"0\" pageBreak=\"0\" columnBreak=\"0\" merged=\"0\"><hp:run charPrIDRef=\"0\">{}</hp:run></hp:p>",
                text_paragraph("P06-07 B EQUATION"),
                equation(2_100_000_100)
            ),
            33,
            0,
            2,
            1,
            19_843,
            10_000,
            false,
        )
    );
    table(
        id,
        34,
        2,
        86_400,
        Some(caption("P06-07 AVOID-ROW BOTTOM", CaptionSide::Top)),
        &(header + &merged + &ordinary_rows + &nested_row + &equation_row),
    )
}

fn build_boundary_case(id: u32, label: &str, side: CaptionSide) -> String {
    let rows = format!(
        "<hp:tr>{}</hp:tr><hp:tr>{}</hp:tr>",
        text_cell(
            &format!("P06-07 {label} HEADER"),
            0,
            0,
            1,
            1,
            19_843,
            1_400,
            false,
        ),
        text_cell(
            &format!("P06-07 {label} BODY"),
            1,
            0,
            1,
            1,
            19_843,
            4_200,
            false,
        ),
    );
    table(
        id,
        2,
        1,
        5_600,
        Some(caption(&format!("P06-07 {label}"), side)),
        &rows,
    )
}

fn table(
    id: u32,
    rows: u32,
    columns: u32,
    height: u32,
    caption: Option<String>,
    row_xml: &str,
) -> String {
    format!(
        concat!(
            "<hp:tbl id=\"{}\" zOrder=\"0\" numberingType=\"TABLE\" ",
            "textWrap=\"TOP_AND_BOTTOM\" textFlow=\"BOTH_SIDES\" lock=\"0\" ",
            "dropcapstyle=\"None\" pageBreak=\"CELL\" repeatHeader=\"0\" ",
            "rowCnt=\"{}\" colCnt=\"{}\" cellSpacing=\"0\" borderFillIDRef=\"3\" noAdjust=\"0\">",
            "<hp:sz width=\"19843\" widthRelTo=\"ABSOLUTE\" height=\"{}\" heightRelTo=\"ABSOLUTE\" protect=\"0\"/>",
            "<hp:pos treatAsChar=\"1\" affectLSpacing=\"1\" flowWithText=\"1\" allowOverlap=\"0\" holdAnchorAndSO=\"0\" vertRelTo=\"PARA\" horzRelTo=\"COLUMN\" vertAlign=\"TOP\" horzAlign=\"LEFT\" vertOffset=\"0\" horzOffset=\"0\"/>",
            "<hp:outMargin left=\"283\" right=\"283\" top=\"283\" bottom=\"283\"/>{}",
            "<hp:inMargin left=\"510\" right=\"510\" top=\"141\" bottom=\"141\"/>{}</hp:tbl>"
        ),
        id,
        rows,
        columns,
        height,
        caption.unwrap_or_default(),
        row_xml,
    )
}

fn caption(text: &str, side: CaptionSide) -> String {
    let side = match side {
        CaptionSide::Top => "TOP",
        CaptionSide::Bottom => "BOTTOM",
    };
    format!(
        concat!(
            "<hp:caption side=\"{}\" fullSz=\"0\" width=\"19843\" gap=\"850\" lastWidth=\"19843\">",
            "<hp:subList id=\"\" textDirection=\"HORIZONTAL\" lineWrap=\"BREAK\" vertAlign=\"TOP\" linkListIDRef=\"0\" linkListNextIDRef=\"0\" textWidth=\"0\" textHeight=\"0\" hasTextRef=\"0\" hasNumRef=\"0\">",
            "{}</hp:subList></hp:caption>"
        ),
        side,
        text_paragraph(text),
    )
}

#[allow(clippy::too_many_arguments)]
fn text_cell(
    text: &str,
    row: u32,
    column: u32,
    col_span: u32,
    row_span: u32,
    width: u32,
    height: u32,
    header: bool,
) -> String {
    content_cell(
        &text_paragraph(text),
        row,
        column,
        col_span,
        row_span,
        width,
        height,
        header,
    )
}

#[allow(clippy::too_many_arguments)]
fn content_cell(
    content: &str,
    row: u32,
    column: u32,
    col_span: u32,
    row_span: u32,
    width: u32,
    height: u32,
    header: bool,
) -> String {
    format!(
        concat!(
            "<hp:tc name=\"\" header=\"{}\" hasMargin=\"0\" protect=\"0\" editable=\"0\" dirty=\"0\" borderFillIDRef=\"3\">",
            "<hp:subList id=\"\" textDirection=\"HORIZONTAL\" lineWrap=\"BREAK\" vertAlign=\"TOP\" linkListIDRef=\"0\" linkListNextIDRef=\"0\" textWidth=\"0\" textHeight=\"0\" hasTextRef=\"0\" hasNumRef=\"0\">{}</hp:subList>",
            "<hp:cellAddr colAddr=\"{}\" rowAddr=\"{}\"/><hp:cellSpan colSpan=\"{}\" rowSpan=\"{}\"/>",
            "<hp:cellSz width=\"{}\" height=\"{}\"/><hp:cellMargin left=\"510\" right=\"510\" top=\"141\" bottom=\"141\"/></hp:tc>"
        ),
        u8::from(header),
        content,
        column,
        row,
        col_span,
        row_span,
        width,
        height,
    )
}

fn text_paragraph(text: &str) -> String {
    format!(
        concat!(
            "<hp:p id=\"0\" paraPrIDRef=\"0\" styleIDRef=\"0\" pageBreak=\"0\" columnBreak=\"0\" merged=\"0\">",
            "<hp:run charPrIDRef=\"0\"><hp:t>{}</hp:t></hp:run></hp:p>"
        ),
        escape_xml(text),
    )
}

fn nested_table(id: u32) -> String {
    let row = format!(
        "<hp:tr>{}</hp:tr>",
        text_cell("P06-07 NESTED TABLE CELL", 0, 0, 1, 1, 15_000, 2_000, false)
    );
    table(id, 1, 1, 2_000, None, &row)
}

fn equation(id: u32) -> String {
    format!(
        concat!(
            "<hp:equation id=\"{}\" zOrder=\"0\" numberingType=\"EQUATION\" textWrap=\"TOP_AND_BOTTOM\" textFlow=\"BOTH_SIDES\" lock=\"0\" dropcapstyle=\"None\" version=\"Equation Version 60\" baseLine=\"85\" textColor=\"#000000\" baseUnit=\"1000\" lineMode=\"CHAR\" font=\"HancomEQN\">",
            "<hp:sz width=\"17000\" widthRelTo=\"ABSOLUTE\" height=\"6000\" heightRelTo=\"ABSOLUTE\" protect=\"0\"/>",
            "<hp:pos treatAsChar=\"1\" affectLSpacing=\"1\" flowWithText=\"1\" allowOverlap=\"0\" holdAnchorAndSO=\"0\" vertRelTo=\"PARA\" horzRelTo=\"COLUMN\" vertAlign=\"TOP\" horzAlign=\"LEFT\" vertOffset=\"0\" horzOffset=\"0\"/>",
            "<hp:outMargin left=\"0\" right=\"0\" top=\"0\" bottom=\"0\"/>",
            "<hp:script>sum _{{i=1}} ^{{32}} {{i^2}} + int _0 ^1 {{x^4 + 3x^2 + 1}} dx = 10416</hp:script>",
            "</hp:equation>"
        ),
        id,
    )
}

fn table_paragraph(table: &str) -> String {
    format!(
        "<hp:p id=\"0\" paraPrIDRef=\"0\" styleIDRef=\"0\" pageBreak=\"0\" columnBreak=\"0\" merged=\"0\"><hp:run charPrIDRef=\"0\">{table}<hp:t/></hp:run></hp:p>"
    )
}

fn page_break_paragraph(text: &str) -> String {
    format!(
        "<hp:p id=\"0\" paraPrIDRef=\"0\" styleIDRef=\"0\" pageBreak=\"1\" columnBreak=\"0\" merged=\"0\"><hp:run charPrIDRef=\"0\"><hp:t>{}</hp:t></hp:run></hp:p>",
        escape_xml(text),
    )
}

fn boundary_group(label: &str, filler_lines: usize, table: &str) -> String {
    let mut output = String::with_capacity(filler_lines * 140 + table.len());
    output.push_str(&page_break_paragraph(&format!("P06-07 {label} PAGE START")));
    for index in 1..=filler_lines {
        output.push_str(&text_paragraph(&format!(
            "P06-07 {label} FILLER {index:02}/{filler_lines:02}"
        )));
    }
    output.push_str(&table_paragraph(table));
    output
}

fn lower_pagination_targets(source: &[u8]) -> Result<Vec<u8>, Box<dyn Error>> {
    let limits = TablePaginationHwpxLimits::default();
    if TablePaginationHwpxReader::count_in_section(source, limits)? != 6 {
        return Err("structural table cardinality drifted".into());
    }
    let mut section = source.to_vec();
    for (ordinal, page_split, header_rows, caption_side) in [
        (0, TablePageSplitPolicy::Allow, 1, Some(CaptionSide::Top)),
        (
            1,
            TablePageSplitPolicy::AvoidRow,
            1,
            Some(CaptionSide::Bottom),
        ),
        (2, TablePageSplitPolicy::AvoidTable, 0, None),
        (
            3,
            TablePageSplitPolicy::AvoidTable,
            1,
            Some(CaptionSide::Top),
        ),
        (
            4,
            TablePageSplitPolicy::AvoidTable,
            1,
            Some(CaptionSide::Top),
        ),
        (
            5,
            TablePageSplitPolicy::AvoidTable,
            1,
            Some(CaptionSide::Bottom),
        ),
    ] {
        let readback = TablePaginationHwpxReader::read_in_section(&section, ordinal, limits)?;
        let caption = match (readback.caption, caption_side) {
            (Some(mut caption), Some(side)) => {
                caption.side = side;
                TableCaptionHwpxTarget::Existing(caption)
            }
            (None, None) => TableCaptionHwpxTarget::Absent,
            _ => return Err("caption target shape drifted".into()),
        };
        let target = TablePaginationHwpxTarget {
            page_split,
            repeat_header_rows: header_rows,
            caption,
        };
        section = TablePaginationHwpxLowerer::lower_in_section(&section, ordinal, &target, limits)?;
        let second =
            TablePaginationHwpxLowerer::lower_in_section(&section, ordinal, &target, limits)?;
        if second != section {
            return Err("pagination lowering is not byte-idempotent".into());
        }
    }
    Ok(section)
}

fn require_target_section(section: &[u8]) -> Result<(), Box<dyn Error>> {
    let limits = TablePaginationHwpxLimits::default();
    let expected = [
        (TablePageSplitPolicy::Allow, 1, Some(CaptionSide::Top)),
        (TablePageSplitPolicy::AvoidRow, 1, Some(CaptionSide::Bottom)),
        (TablePageSplitPolicy::AvoidTable, 0, None),
        (TablePageSplitPolicy::AvoidTable, 1, Some(CaptionSide::Top)),
        (TablePageSplitPolicy::AvoidTable, 1, Some(CaptionSide::Top)),
        (
            TablePageSplitPolicy::AvoidTable,
            1,
            Some(CaptionSide::Bottom),
        ),
    ];
    if TablePaginationHwpxReader::count_in_section(section, limits)? != expected.len() {
        return Err("target table cardinality differs".into());
    }
    for (ordinal, (page_split, header_rows, caption_side)) in expected.into_iter().enumerate() {
        let readback = TablePaginationHwpxReader::read_in_section(section, ordinal, limits)?;
        if readback.page_split != page_split
            || readback.repeat_header_rows != header_rows
            || readback.caption.as_ref().map(|value| value.side) != caption_side
        {
            return Err(format!("target table {ordinal} readback differs").into());
        }
    }
    let text = String::from_utf8(section.to_vec())?;
    for (marker, count) in [
        ("P06-07 ALLOW TOP", 1),
        ("P06-07 AVOID-ROW BOTTOM", 1),
        ("P06-07 B MERGED", 18),
        ("P06-07 B ROW", 30),
        ("P06-07 B NESTED", 1),
        ("P06-07 NESTED TABLE CELL", 1),
        ("P06-07 B EQUATION", 1),
        ("<hp:equation ", 1),
        ("<hp:caption ", 5),
    ] {
        if text.matches(marker).count() != count {
            return Err(format!("target marker cardinality differs: {marker}").into());
        }
    }
    if text.contains("<hp:linesegarray>") {
        return Err("target retains renderer line caches".into());
    }
    Ok(())
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

fn escape_xml(value: &str) -> String {
    value
        .replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
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
    if output.len() as u64 > MAX_FIXTURE_BYTES {
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn structural_target_is_deterministic_and_typed() {
        let source = fs::read(concat!(
            env!("CARGO_MANIFEST_DIR"),
            "/../../fixtures/target-build/p06-05-table-layout-20260907-05/target-readback-output-01.hwpx"
        ));
        let Ok(source) = source else {
            return;
        };
        let first = inspect_package(&source).expect("source package");
        let structural = build_structural_section(&first.section).expect("structural section");
        let target = lower_pagination_targets(&structural).expect("lower target");
        require_target_section(&target).expect("typed target");
        assert_eq!(
            target,
            lower_pagination_targets(&structural).expect("deterministic lower")
        );
    }

    #[test]
    fn xml_escaping_is_fail_safe_for_visible_markers() {
        assert_eq!(escape_xml("A&B<C>"), "A&amp;B&lt;C&gt;");
    }
}
