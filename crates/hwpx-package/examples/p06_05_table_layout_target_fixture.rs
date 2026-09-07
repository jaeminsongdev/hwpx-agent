use std::borrow::Cow;
use std::env;
use std::error::Error;
use std::fs::{self, OpenOptions};
use std::io::{Cursor, Write as _};
use std::path::{Path, PathBuf};

use domain_ir::{
    HwpUnit, LengthMicrometers, LogicalId, TABLE_LAYOUT_SCHEMA_VERSION, TableCellSpan,
    TableColumnConstraint, TableGrid, TableGridLimits, TableLayoutLimits, TableLayoutPlan,
    TableLayoutProblem, TableLayoutSolver, TableWidthSpec,
};
use hwpx_package::{
    BoundedZipReader, CellTextDirection, CellVerticalAlignment, CharacterStyleCatalog,
    CharacterStyleCatalogReader, CharacterStyleLimits, Compression, CurrentFontMetricLimits,
    CurrentFontMetricReceipt, FontType, IdIndex, IdIndexLimits, IdRuleProfile, LanguageSlot,
    PackageGraph, PackageGraphLimits, PackageLimits, PageSetupLimits, PageSetupReader,
    ParagraphChild, ParagraphStyleCatalog, ParagraphStyleCatalogReader, ParagraphStyleLimits,
    PreservingXmlDocument, TableCellStyleLimits, TableCellStyleLowerer, TableCellStyleProfile,
    TableCellStyleReader, TableInnerMarginReadback, TableLayoutHwpxLimits, TableLayoutHwpxLowerer,
    TableLayoutHwpxLoweringReceipt, TableLayoutHwpxReadback, TableLayoutHwpxReader, TextAtom,
    TextFlow, TextFlowLimits, TextFlowReader, TextRunItem, XmlByteSpan, XmlElementToken,
};
use quick_xml::escape::escape;
use sha2::{Digest as _, Sha256};
use zip::write::SimpleFileOptions;
use zip::{CompressionMethod, DateTime, ZipWriter};

const MAX_FIXTURE_BYTES: u64 = 8 * 1024 * 1024;
const MAX_RECEIPT_BYTES: u64 = 1024 * 1024;
const CELL_COUNT: usize = 4;
const NORMALIZED_DEFLATE_LEVEL: i64 = 6;
const TARGET_TABLE_WIDTH_MICROMETERS: i64 = 70_000;
const EXPECTED_SOURCE_INNER_MARGIN: TableInnerMarginReadback = TableInnerMarginReadback {
    left_hwpunit: 510,
    right_hwpunit: 510,
    top_hwpunit: 141,
    bottom_hwpunit: 141,
};
const SOURCE_TEXTS: [&str; CELL_COUNT] = ["P06-04-A", "P06-04-B", "P06-04-C", "P06-04-D"];
const TARGET_TEXTS: [(&str, &str, &str); CELL_COUNT] = [
    (
        "cell-a",
        "P06-05 A",
        "df47d07aa15a6493ed52bcddfbd594ff255d9566138ab7137f90b13fedd2ed98",
    ),
    (
        "cell-b",
        "한글 표 자동 맞춤",
        "b81461d5ac0a8865284ef84c147e0743da482750e1a499d80126e31c7324ee7b",
    ),
    (
        "cell-c",
        "WIDE-CONTENT-1234567890",
        "25dfcb4b0c5e694cf7bf977f1870cd2025fa363bfa2a26118ea00f305a3afdd3",
    ),
    (
        "cell-d",
        "병합 셀",
        "d932f7dee69be5f5763a0647e1ed14067e5231e783b4039a9aabbf8387405845",
    ),
];
const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const SECTION_NS: &str = "http://www.hancom.co.kr/hwpml/2011/section";

fn main() -> Result<(), Box<dyn Error>> {
    let mut arguments = env::args_os();
    let _program = arguments.next();
    let input = path_argument(&mut arguments, "input HWPX")?;
    let expected_input_sha256 = string_argument(&mut arguments, "expected input SHA-256")?;
    let receipt_path = path_argument(&mut arguments, "font receipt")?;
    let expected_receipt_sha256 = string_argument(&mut arguments, "expected receipt SHA-256")?;
    let output = path_argument(&mut arguments, "output HWPX")?;
    if arguments.next().is_some() {
        return Err("too many arguments".into());
    }
    require_lower_sha256(&expected_input_sha256)?;
    require_lower_sha256(&expected_receipt_sha256)?;
    if input == output || output.extension().and_then(|value| value.to_str()) != Some("hwpx") {
        return Err("output must be a distinct .hwpx path".into());
    }

    let source = read_bounded_file(&input, MAX_FIXTURE_BYTES)?;
    require_digest(&source, &expected_input_sha256, "input")?;
    let source_inspection = inspect_package(&source, TextProfile::Source)?;

    let receipt_bytes = read_bounded_file(&receipt_path, MAX_RECEIPT_BYTES)?;
    require_digest(&receipt_bytes, &expected_receipt_sha256, "font receipt")?;
    let font_receipt =
        CurrentFontMetricReceipt::parse(&receipt_bytes, CurrentFontMetricLimits::default())?;
    if font_receipt.receipt_sha256() != expected_receipt_sha256 {
        return Err("typed font receipt digest mismatch".into());
    }

    let (grid, plan) = build_verified_plan(
        &source_inspection.layout,
        source_inspection.body_width_hwpunit,
        &font_receipt,
    )?;
    let (target_section, lowering) = build_target_section(
        &source_inspection.section,
        &source_inspection.paragraph_styles,
        &grid,
        &plan,
    )?;
    let target = replace_target_parts(&source, &target_section)?;
    let target_inspection = inspect_package(&target, TextProfile::Target)?;
    verify_target(&source_inspection, &target_inspection, &plan, &lowering)?;

    require_digest(
        &read_bounded_file(&input, MAX_FIXTURE_BYTES)?,
        &expected_input_sha256,
        "input after build",
    )?;
    require_digest(
        &read_bounded_file(&receipt_path, MAX_RECEIPT_BYTES)?,
        &expected_receipt_sha256,
        "font receipt after build",
    )?;
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&output)?;
    file.write_all(&target)?;
    file.sync_all()?;

    println!(
        concat!(
            "schema=hwpx-agent.p06-05-table-layout-target/v2 state=pass ",
            "source_sha256={} font_receipt_sha256={} output_sha256={} parts={} ",
            "grid_sha256={} plan_sha256={} text_set_sha256={} ",
            "font_binding=hancom_2020_hcr_batang_10pt cells={} directions=horizontal ",
            "table_width_hwpunit={} table_height_hwpunit={} column_widths_um={} row_heights_um={}"
        ),
        expected_input_sha256,
        expected_receipt_sha256,
        hex(Sha256::digest(&target).into()),
        target_inspection.part_count,
        hex(grid.canonical_sha256()?),
        hex(plan.canonical_sha256(TableLayoutLimits::default())?),
        target_inspection.text_set_sha256,
        target_inspection.texts.len(),
        target_inspection.layout.table_width_hwpunit,
        target_inspection.layout.table_height_hwpunit,
        join_lengths(plan.column_widths()),
        join_lengths(plan.estimated_row_heights()),
    );
    Ok(())
}

#[derive(Clone, Copy)]
enum TextProfile {
    Source,
    Target,
}

struct PackageInspection {
    part_count: usize,
    section: Vec<u8>,
    paragraph_styles: ParagraphStyleCatalog,
    body_width_hwpunit: u32,
    layout: TableLayoutHwpxReadback,
    texts: Vec<CellTextEvidence>,
    text_set_sha256: String,
    preview_text_sha256: String,
}

#[derive(Clone, Debug, Eq, PartialEq)]
struct CellTextEvidence {
    sha256: [u8; 32],
    character_property_id_ref: u32,
    opaque_non_text_count: usize,
}

fn inspect_package(
    bytes: &[u8],
    text_profile: TextProfile,
) -> Result<PackageInspection, Box<dyn Error>> {
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    let _index = IdIndex::build(
        &mut reader,
        &graph,
        IdRuleProfile::current_hancom_2020_table_v2(),
        IdIndexLimits::default(),
    )?;
    if graph.parts.len() != reader.entries().len() {
        return Err("package graph cardinality mismatch".into());
    }
    let header = read_part(&mut reader, "Contents/header.xml")?;
    let section = read_part(&mut reader, "Contents/section0.xml")?;
    let preview_text = read_part(&mut reader, "Preview/PrvText.txt")?;
    if preview_text != expected_preview_text(text_profile) {
        return Err("preview text differs from the exact cell-text profile".into());
    }
    let character_styles =
        CharacterStyleCatalogReader::read(&header, CharacterStyleLimits::default())?;
    let paragraph_styles =
        ParagraphStyleCatalogReader::read(&header, ParagraphStyleLimits::default())?;
    paragraph_styles.validate_character_style_references(&character_styles)?;
    validate_font_binding(&character_styles)?;

    let page_setup = PageSetupReader::read(&section, PageSetupLimits::default())?;
    let body_width_hwpunit = page_setup.metrics(PageSetupLimits::default())?.body_width;
    let table_count =
        TableLayoutHwpxReader::count_in_section(&section, TableLayoutHwpxLimits::default())?;
    if table_count != 1 {
        return Err("fixture must contain exactly one table".into());
    }
    let layout =
        TableLayoutHwpxReader::read_in_section(&section, 0, TableLayoutHwpxLimits::default())?;
    if layout.rows != 2
        || layout.columns != 2
        || layout.cells.len() != CELL_COUNT
        || layout.inner_margin != EXPECTED_SOURCE_INNER_MARGIN
    {
        return Err("fixture table shape or inherited margin differs".into());
    }
    let texts = read_cell_text_evidence(&section)?;
    validate_expected_texts(&texts, text_profile)?;
    let text_set_sha256 = text_set_sha256(&texts);
    Ok(PackageInspection {
        part_count: graph.parts.len(),
        section,
        paragraph_styles,
        body_width_hwpunit,
        layout,
        texts,
        text_set_sha256,
        preview_text_sha256: hex(Sha256::digest(&preview_text).into()),
    })
}

fn validate_font_binding(catalog: &CharacterStyleCatalog) -> Result<(), Box<dyn Error>> {
    let style = catalog
        .styles
        .first()
        .ok_or("character style zero is missing")?;
    if style.id != 0
        || style.height != 1_000
        || style.font_refs.hangul != 1
        || style.font_refs.latin != 1
    {
        return Err("cell character style is not the 10pt receipt binding".into());
    }
    for language in [LanguageSlot::Hangul, LanguageSlot::Latin] {
        let group = catalog
            .font_faces
            .iter()
            .find(|group| group.language == language)
            .ok_or("receipt language font group is missing")?;
        let face = group.fonts.get(1).ok_or("receipt font face is missing")?;
        if face.id != 1
            || face.face != "함초롬바탕"
            || face.font_type != FontType::TrueType
            || face.is_embedded
        {
            return Err("cell font face differs from the current receipt".into());
        }
    }
    Ok(())
}

fn build_verified_plan(
    layout: &TableLayoutHwpxReadback,
    body_width_hwpunit: u32,
    receipt: &CurrentFontMetricReceipt,
) -> Result<(TableGrid, TableLayoutPlan), Box<dyn Error>> {
    let grid = TableGrid::new(
        2,
        2,
        TARGET_TEXTS
            .iter()
            .enumerate()
            .map(|(index, (identifier, _, _))| {
                Ok(TableCellSpan {
                    master_cell_id: LogicalId::parse(*identifier)?,
                    row: u32::try_from(index / 2)?,
                    column: u32::try_from(index % 2)?,
                    row_span: 1,
                    column_span: 1,
                })
            })
            .collect::<Result<Vec<_>, Box<dyn Error>>>()?,
        TableGridLimits::default(),
    )?;
    let leading = hwpunit_to_micrometers(layout.inner_margin.left_hwpunit)?;
    let trailing = hwpunit_to_micrometers(layout.inner_margin.right_hwpunit)?;
    let cells = TARGET_TEXTS
        .iter()
        .map(|(identifier, _, _)| {
            let cell_id = LogicalId::parse(*identifier)?;
            Ok(receipt.table_cell_measure(&cell_id, leading, trailing)?)
        })
        .collect::<Result<Vec<_>, Box<dyn Error>>>()?;
    let columns = (0..2)
        .map(|column| {
            let source = layout
                .cells
                .iter()
                .find(|cell| cell.row == 0 && cell.column == column)
                .ok_or("source column width is missing")?;
            Ok(TableColumnConstraint {
                minimum_width: LengthMicrometers::from_raw(1_000),
                preferred_width: LengthMicrometers::from_raw(1_000),
                previous_width: hwpunit_to_micrometers(source.width_hwpunit)?,
                fixed_width: None,
            })
        })
        .collect::<Result<Vec<_>, Box<dyn Error>>>()?;
    let problem = TableLayoutProblem {
        schema_version: TABLE_LAYOUT_SCHEMA_VERSION.to_owned(),
        width: TableWidthSpec::Absolute {
            width: LengthMicrometers::from_raw(TARGET_TABLE_WIDTH_MICROMETERS),
        },
        body_width: hwpunit_to_micrometers(body_width_hwpunit)?,
        columns,
        cells,
    };
    let plan = TableLayoutSolver::solve(&grid, &problem, TableLayoutLimits::default())?;
    plan.require_verified()?;
    let columns: Vec<i64> = plan
        .column_widths()
        .iter()
        .map(|value| value.as_i64())
        .collect();
    let rows: Vec<i64> = plan
        .estimated_row_heights()
        .iter()
        .map(|value| value.as_i64())
        .collect();
    if columns != [52_990, 17_010]
        || rows != [13_758, 4_586]
        || plan.total_width().as_i64() != TARGET_TABLE_WIDTH_MICROMETERS
        || plan.body_overflow().as_i64() != 0
        || plan.target_overflow().as_i64() != 0
        || plan.target_underfill().as_i64() != 0
        || !plan.content_deficits().is_empty()
    {
        return Err("verified layout plan differs from the exact target".into());
    }
    Ok((grid, plan))
}

fn build_target_section(
    source: &[u8],
    paragraph_styles: &ParagraphStyleCatalog,
    grid: &TableGrid,
    plan: &TableLayoutPlan,
) -> Result<(Vec<u8>, TableLayoutHwpxLoweringReceipt), Box<dyn Error>> {
    let mut section = source.to_vec();
    for ordinal in 0..CELL_COUNT {
        let readback = TableCellStyleReader::read_in_section_with_profile(
            &section,
            ordinal,
            TableCellStyleProfile::Hangul2020V2,
            paragraph_styles,
            TableCellStyleLimits::default(),
        )?;
        if readback.style.margins.is_some() {
            return Err("fixture must inherit its table inner margin".into());
        }
        let mut target = readback.style;
        target.text_direction = CellTextDirection::Horizontal;
        target.vertical_alignment = CellVerticalAlignment::Top;
        section = TableCellStyleLowerer::lower_in_section_with_profile(
            &section,
            ordinal,
            TableCellStyleProfile::Hangul2020V2,
            &target,
            paragraph_styles,
            TableCellStyleLimits::default(),
        )?;
    }
    section = replace_cell_texts(&section)?;
    Ok(TableLayoutHwpxLowerer::lower_in_section_with_receipt(
        &section,
        0,
        grid,
        plan,
        TableLayoutHwpxLimits::default(),
    )?)
}

fn verify_target(
    source: &PackageInspection,
    target: &PackageInspection,
    plan: &TableLayoutPlan,
    lowering: &TableLayoutHwpxLoweringReceipt,
) -> Result<(), Box<dyn Error>> {
    if target.part_count != source.part_count
        || target.body_width_hwpunit != source.body_width_hwpunit
        || target.layout.inner_margin != source.layout.inner_margin
        || target.layout.content_sha256 != lowering.content_sha256
        || target.layout.table_width_hwpunit != lowering.table_width_hwpunit
        || target.layout.table_height_hwpunit != lowering.table_height_hwpunit
        || lowering.layout_plan_sha256 != plan.canonical_sha256(TableLayoutLimits::default())?
        || target.text_set_sha256 == source.text_set_sha256
        || target.preview_text_sha256 == source.preview_text_sha256
    {
        return Err("target package readback differs from its source-bound plan".into());
    }
    for ordinal in 0..CELL_COUNT {
        let style = TableCellStyleReader::read_in_section_with_profile(
            &target.section,
            ordinal,
            TableCellStyleProfile::Hangul2020V2,
            &target.paragraph_styles,
            TableCellStyleLimits::default(),
        )?;
        if style.style.text_direction != CellTextDirection::Horizontal
            || style.style.vertical_alignment != CellVerticalAlignment::Top
            || style.style.margins.is_some()
        {
            return Err("target cell style is not the horizontal layout profile".into());
        }
    }
    Ok(())
}

fn replace_cell_texts(source: &[u8]) -> Result<Vec<u8>, Box<dyn Error>> {
    let document = PreservingXmlDocument::parse(source)?;
    let paragraphs = table_cell_paragraphs(&document)?;
    let before = read_text_evidence_from_paragraphs(source, &document, &paragraphs)?;
    validate_expected_texts(&before, TextProfile::Source)?;
    let mut edits = Vec::new();
    for (ordinal, paragraph) in paragraphs.iter().copied().enumerate() {
        let text = exactly_one_text_element(&document, paragraph)?;
        let line_cache = exactly_one_line_cache_span(&document, paragraph)?;
        let element = document
            .elements()
            .get(text)
            .ok_or("text element is missing")?;
        if element.first_child().is_some() {
            return Err("nested text content is unsupported".into());
        }
        let span = element
            .content_span()
            .ok_or("text content span is missing")?;
        let escaped: Cow<'_, str> = escape(TARGET_TEXTS[ordinal].1);
        edits.push((span, escaped.into_owned().into_bytes()));
        edits.push((line_cache, Vec::new()));
    }
    edits.sort_unstable_by_key(|(span, _)| span.start());
    if edits
        .windows(2)
        .any(|pair| pair[0].0.end() > pair[1].0.start())
    {
        return Err("text edit spans overlap".into());
    }
    let mut output = source.to_vec();
    for (span, replacement) in edits.into_iter().rev() {
        output.splice(span.start()..span.end(), replacement);
        if output.len() > TableLayoutHwpxLimits::default().config().output_bytes {
            return Err("text replacement exceeds section limit".into());
        }
    }
    let output_document = PreservingXmlDocument::parse(&output)?;
    let output_paragraphs = table_cell_paragraphs(&output_document)?;
    let after = read_text_evidence_from_paragraphs(&output, &output_document, &output_paragraphs)?;
    validate_expected_texts(&after, TextProfile::Target)?;
    if before
        .iter()
        .zip(&after)
        .any(|(left, right)| left.character_property_id_ref != right.character_property_id_ref)
    {
        return Err("text replacement changed paragraph structure or font binding".into());
    }
    Ok(output)
}

fn read_cell_text_evidence(section: &[u8]) -> Result<Vec<CellTextEvidence>, Box<dyn Error>> {
    let document = PreservingXmlDocument::parse(section)?;
    let paragraphs = table_cell_paragraphs(&document)?;
    read_text_evidence_from_paragraphs(section, &document, &paragraphs)
}

fn read_text_evidence_from_paragraphs(
    section: &[u8],
    document: &PreservingXmlDocument,
    paragraphs: &[usize],
) -> Result<Vec<CellTextEvidence>, Box<dyn Error>> {
    let mut evidence = Vec::new();
    evidence.try_reserve_exact(paragraphs.len())?;
    for paragraph in paragraphs {
        let flow = standalone_flow(section, document, *paragraph)?;
        evidence.push(simple_text_evidence(&flow)?);
    }
    Ok(evidence)
}

fn simple_text_evidence(flow: &TextFlow) -> Result<CellTextEvidence, Box<dyn Error>> {
    let visible = flow.visible_text_nfc()?;
    let runs: Vec<_> = flow
        .children
        .iter()
        .filter_map(|child| match child {
            ParagraphChild::Run(run) => Some(run),
            ParagraphChild::Opaque(_) => None,
        })
        .collect();
    let opaque_non_text_count = flow
        .children
        .iter()
        .filter_map(|child| match child {
            ParagraphChild::Opaque(opaque) => Some(opaque),
            ParagraphChild::Run(_) => None,
        })
        .try_fold(0_usize, |count, opaque| {
            if opaque.may_contain_visible_text()
                || opaque.namespace() != Some(PARAGRAPH_NS)
                || opaque.local_name() != "linesegarray"
            {
                Err("unexpected opaque cell paragraph element")
            } else {
                count.checked_add(1).ok_or("opaque count overflow")
            }
        })?;
    if runs.len() != 1 || runs[0].items.len() != 1 {
        return Err("cell paragraph must contain one typed text run".into());
    }
    if opaque_non_text_count > 1 {
        return Err("cell paragraph has duplicate line-segment caches".into());
    }
    let TextRunItem::Text(span) = &runs[0].items[0] else {
        return Err("cell paragraph item is not typed text".into());
    };
    if span.character_style_id_ref.is_some()
        || span.atoms.len() != 1
        || !matches!(&span.atoms[0], TextAtom::Text(_))
        || runs[0].character_change_id.is_some()
    {
        return Err("cell text span shape is unsupported".into());
    }
    let character_property_id_ref = runs[0]
        .character_property_id_ref
        .ok_or("cell run character property reference is missing")?;
    if character_property_id_ref != 0 {
        return Err("cell run is not bound to character style zero".into());
    }
    Ok(CellTextEvidence {
        sha256: Sha256::digest(visible.as_bytes()).into(),
        character_property_id_ref,
        opaque_non_text_count,
    })
}

fn standalone_flow(
    section: &[u8],
    document: &PreservingXmlDocument,
    paragraph: usize,
) -> Result<TextFlow, Box<dyn Error>> {
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
    let standalone = if has_local_declaration {
        source.to_vec()
    } else {
        let insertion = element
            .start_name_span()
            .end()
            .checked_sub(outer.start())
            .ok_or("paragraph namespace insertion underflow")?;
        let mut value = Vec::new();
        value.try_reserve_exact(source.len() + declaration_name.len() + PARAGRAPH_NS.len() + 5)?;
        value.extend_from_slice(&source[..insertion]);
        value.extend_from_slice(format!(" {declaration_name}=\"{PARAGRAPH_NS}\"").as_bytes());
        value.extend_from_slice(&source[insertion..]);
        value
    };
    Ok(TextFlowReader::read(
        &standalone,
        TextFlowLimits::default(),
    )?)
}

fn table_cell_paragraphs(document: &PreservingXmlDocument) -> Result<Vec<usize>, Box<dyn Error>> {
    let root = document
        .elements()
        .get(document.root_element())
        .ok_or("section root is missing")?;
    if !has_name(root, SECTION_NS, "sec") {
        return Err("document is not an exact section".into());
    }
    let tables: Vec<_> = document
        .elements()
        .iter()
        .enumerate()
        .filter(|(_, element)| has_name(element, PARAGRAPH_NS, "tbl"))
        .map(|(index, _)| index)
        .collect();
    if tables.len() != 1 {
        return Err("section must contain exactly one table".into());
    }
    let table = tables[0];
    let cells: Vec<_> = document
        .elements()
        .iter()
        .enumerate()
        .filter(|(index, element)| {
            has_name(element, PARAGRAPH_NS, "tc")
                && nearest_ancestor(document, *index, PARAGRAPH_NS, "tbl") == Some(table)
        })
        .map(|(index, _)| index)
        .collect();
    if cells.len() != CELL_COUNT {
        return Err("table must contain exactly four cells".into());
    }
    let mut paragraphs = Vec::new();
    paragraphs.try_reserve_exact(CELL_COUNT)?;
    for cell in cells {
        let matches: Vec<_> = document
            .elements()
            .iter()
            .enumerate()
            .filter(|(index, element)| {
                has_name(element, PARAGRAPH_NS, "p")
                    && nearest_ancestor(document, *index, PARAGRAPH_NS, "tc") == Some(cell)
            })
            .map(|(index, _)| index)
            .collect();
        if matches.len() != 1 {
            return Err("cell must contain exactly one paragraph".into());
        }
        paragraphs.push(matches[0]);
    }
    Ok(paragraphs)
}

fn exactly_one_text_element(
    document: &PreservingXmlDocument,
    paragraph: usize,
) -> Result<usize, Box<dyn Error>> {
    let matches: Vec<_> = document
        .elements()
        .iter()
        .enumerate()
        .filter(|(index, element)| {
            has_name(element, PARAGRAPH_NS, "t")
                && nearest_ancestor(document, *index, PARAGRAPH_NS, "p") == Some(paragraph)
        })
        .map(|(index, _)| index)
        .collect();
    if matches.len() != 1 {
        return Err("cell paragraph must contain exactly one text element".into());
    }
    Ok(matches[0])
}

fn exactly_one_line_cache_span(
    document: &PreservingXmlDocument,
    paragraph: usize,
) -> Result<XmlByteSpan, Box<dyn Error>> {
    let matches: Vec<_> = document
        .elements()
        .iter()
        .filter(|element| {
            has_name(element, PARAGRAPH_NS, "linesegarray") && element.parent() == Some(paragraph)
        })
        .collect();
    if matches.len() != 1 {
        return Err("cell paragraph must contain exactly one direct line-segment cache".into());
    }
    matches[0]
        .outer_span()
        .ok_or_else(|| "line-segment cache span is missing".into())
}

fn nearest_ancestor(
    document: &PreservingXmlDocument,
    index: usize,
    namespace: &str,
    local_name: &str,
) -> Option<usize> {
    let mut parent = document.elements().get(index)?.parent();
    while let Some(candidate) = parent {
        let element = document.elements().get(candidate)?;
        if has_name(element, namespace, local_name) {
            return Some(candidate);
        }
        parent = element.parent();
    }
    None
}

fn has_name(element: &XmlElementToken, namespace: &str, local_name: &str) -> bool {
    element.name().namespace() == Some(namespace) && element.name().local_name() == local_name
}

fn validate_expected_texts(
    actual: &[CellTextEvidence],
    profile: TextProfile,
) -> Result<(), Box<dyn Error>> {
    if actual.len() != CELL_COUNT {
        return Err("cell text cardinality mismatch".into());
    }
    for (ordinal, evidence) in actual.iter().enumerate() {
        let (expected, expected_line_cache_count) = match profile {
            TextProfile::Source => (
                hex(Sha256::digest(SOURCE_TEXTS[ordinal].as_bytes()).into()),
                1,
            ),
            TextProfile::Target => (TARGET_TEXTS[ordinal].2.to_owned(), 0),
        };
        if hex(evidence.sha256) != expected
            || evidence.opaque_non_text_count != expected_line_cache_count
        {
            return Err(format!("cell {ordinal} text or line-cache profile mismatch").into());
        }
    }
    Ok(())
}

fn text_set_sha256(texts: &[CellTextEvidence]) -> String {
    let mut digest = Sha256::new();
    digest.update(b"hwpx-agent.p06-05-cell-text-set/v1\0");
    for text in texts {
        digest.update(text.sha256);
    }
    hex(digest.finalize().into())
}

fn replace_target_parts(source: &[u8], target_section: &[u8]) -> Result<Vec<u8>, Box<dyn Error>> {
    let mut archive = BoundedZipReader::open(Cursor::new(source), PackageLimits::default())?;
    let entries = archive.entries().to_vec();
    let mut parts = Vec::new();
    parts.try_reserve_exact(entries.len())?;
    let mut replaced_section = 0_u8;
    let mut replaced_preview = 0_u8;
    for entry in entries {
        let path = entry.path.as_str().to_owned();
        let method = match entry.compression {
            Compression::Stored => CompressionMethod::Stored,
            Compression::Deflated => CompressionMethod::Deflated,
        };
        let bytes = match path.as_str() {
            "Contents/section0.xml" => {
                replaced_section += 1;
                target_section.to_vec()
            }
            "Preview/PrvText.txt" => {
                let source_preview = archive.read_entry(entry.index)?;
                if source_preview != expected_preview_text(TextProfile::Source) {
                    return Err("source preview text differs".into());
                }
                replaced_preview += 1;
                expected_preview_text(TextProfile::Target)
            }
            _ => archive.read_entry(entry.index)?,
        };
        parts.push((path, method, bytes));
    }
    if replaced_section != 1 || replaced_preview != 1 {
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
    Ok(writer.finish()?.into_inner())
}

fn expected_preview_text(profile: TextProfile) -> Vec<u8> {
    let texts: Vec<&str> = match profile {
        TextProfile::Source => SOURCE_TEXTS.to_vec(),
        TextProfile::Target => TARGET_TEXTS.iter().map(|(_, text, _)| *text).collect(),
    };
    format!(
        "<{}><{}>\r\n<{}><{}>\r\n\r\n",
        texts[0], texts[1], texts[2], texts[3]
    )
    .into_bytes()
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

fn require_lower_sha256(value: &str) -> Result<(), Box<dyn Error>> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || matches!(byte, b'a'..=b'f'))
    {
        return Err("expected SHA-256 must be lowercase hexadecimal".into());
    }
    Ok(())
}

fn hwpunit_to_micrometers(value: u32) -> Result<LengthMicrometers, Box<dyn Error>> {
    Ok(*LengthMicrometers::from_hwp_unit(HwpUnit::from_raw(i64::from(value)))?.value())
}

fn path_argument(
    arguments: &mut impl Iterator<Item = std::ffi::OsString>,
    label: &str,
) -> Result<PathBuf, Box<dyn Error>> {
    arguments
        .next()
        .map(PathBuf::from)
        .ok_or_else(|| format!("missing {label}").into())
}

fn string_argument(
    arguments: &mut impl Iterator<Item = std::ffi::OsString>,
    label: &str,
) -> Result<String, Box<dyn Error>> {
    arguments
        .next()
        .and_then(|value| value.into_string().ok())
        .ok_or_else(|| format!("missing or non-Unicode {label}").into())
}

fn join_lengths(values: &[LengthMicrometers]) -> String {
    values
        .iter()
        .map(|value| value.as_i64().to_string())
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

    #[test]
    fn structured_text_rewrite_invalidates_four_line_caches() -> Result<(), Box<dyn Error>> {
        let source = synthetic_section(&SOURCE_TEXTS);
        let target = replace_cell_texts(source.as_bytes())?;
        let evidence = read_cell_text_evidence(&target)?;
        validate_expected_texts(&evidence, TextProfile::Target)?;
        let target_text = std::str::from_utf8(&target)?;
        assert!(!target_text.contains("<hp:linesegarray>"));
        assert!(
            SOURCE_TEXTS
                .iter()
                .all(|value| !target_text.contains(value))
        );
        Ok(())
    }

    #[test]
    fn text_rewrite_rejects_missing_or_duplicate_line_cache() {
        let source = synthetic_section(&SOURCE_TEXTS);
        let missing = source.replacen("<hp:linesegarray></hp:linesegarray>", "", 1);
        assert!(replace_cell_texts(missing.as_bytes()).is_err());

        let duplicate = source.replacen("</hp:p>", "<hp:linesegarray></hp:linesegarray></hp:p>", 1);
        assert!(replace_cell_texts(duplicate.as_bytes()).is_err());
    }

    fn synthetic_section(texts: &[&str; CELL_COUNT]) -> String {
        let mut cells = String::new();
        for (index, text) in texts.iter().enumerate() {
            if index % 2 == 0 {
                cells.push_str("<hp:tr>");
            }
            cells.push_str(&format!(
                concat!(
                    "<hp:tc><hp:subList><hp:p id=\"0\"><hp:run charPrIDRef=\"0\">",
                    "<hp:t>{}</hp:t></hp:run><hp:linesegarray></hp:linesegarray>",
                    "</hp:p></hp:subList></hp:tc>"
                ),
                text
            ));
            if index % 2 == 1 {
                cells.push_str("</hp:tr>");
            }
        }
        format!(
            "<hs:sec xmlns:hs=\"{SECTION_NS}\" xmlns:hp=\"{PARAGRAPH_NS}\"><hp:tbl>{cells}</hp:tbl></hs:sec>"
        )
    }
}
