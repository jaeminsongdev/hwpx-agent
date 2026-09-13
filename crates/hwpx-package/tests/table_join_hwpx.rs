use std::io::{Cursor, Write};

use domain_ir::{
    LogicalId, TABLE_PARTITION_SCHEMA_VERSION, TableJoinSeparatorToken,
    TablePartitionFormulaPolicy, WholeTableJoinRequestDraft,
};
use hwpx_package::{
    BoundedZipReader, Compression, PackageGraph, PackageGraphLimits, PackageLimits,
    TABLE_JOIN_HWPX_SCHEMA_VERSION, TableFormulaHwpxLimits, TableFormulaHwpxReader,
    TableJoinHwpxBuilder, TableJoinHwpxError, TableJoinHwpxLimits, TableJoinHwpxLowerer,
    TableJoinHwpxReadback, TableJoinHwpxReader, TableJoinHwpxRequest, TableJoinHwpxRequestDraft,
    TableLayoutHwpxReader, TableRulingHwpxBinding, TableRulingHwpxCellBinding,
};
use zip::write::SimpleFileOptions;
use zip::{CompressionMethod, DateTime, ZipWriter};

type TestResult<T = ()> = Result<T, Box<dyn std::error::Error>>;

const HEADER: &[u8] = include_bytes!("../src/hancom_2020_minimal_header.xml");
const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const SECTION_NS: &str = "http://www.hancom.co.kr/hwpml/2011/section";
const CONTAINER: &str = r#"<?xml version="1.0" encoding="UTF-8"?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">
  <rootfiles><rootfile full-path="Contents/content.hpf" media-type="application/oebps-package+xml"/></rootfiles>
</container>"#;
const OPF: &str = r#"<?xml version="1.0" encoding="UTF-8"?>
<opf:package xmlns:opf="http://www.idpf.org/2007/opf" version="2.0">
  <opf:manifest>
    <opf:item id="header" href="header.xml" media-type="application/xml"/>
    <opf:item id="section0" href="section0.xml" media-type="application/xml"/>
    <opf:item id="opaque" href="opaque.bin" media-type="application/octet-stream"/>
  </opf:manifest>
  <opf:spine><opf:itemref idref="section0" linear="yes"/></opf:spine>
</opf:package>"#;

fn id(value: &str) -> TestResult<LogicalId> {
    Ok(LogicalId::parse(value)?)
}

fn digest(character: char) -> String {
    std::iter::repeat_n(character, 64).collect()
}

fn hex(bytes: impl AsRef<[u8]>) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let bytes = bytes.as_ref();
    let mut output = String::with_capacity(bytes.len().saturating_mul(2));
    for byte in bytes {
        output.push(char::from(DIGITS[usize::from(byte >> 4)]));
        output.push(char::from(DIGITS[usize::from(byte & 0x0f)]));
    }
    output
}

fn paragraph(value: &str) -> String {
    format!(
        r#"<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t>{value}</hp:t></hp:run></hp:p>"#
    )
}

fn formula_paragraph() -> &'static str {
    concat!(
        r#"<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:ctrl>"#,
        r#"<hp:fieldBegin id="101" type="FORMULA" name="" editable="0" dirty="0" zorder="-1" fieldid="202">"#,
        r#"<hp:parameters cnt="5" name=""><hp:integerParam name="Prop">8</hp:integerParam>"#,
        r#"<hp:stringParam name="Command">=SUM(LEFT)??%g,;;7</hp:stringParam>"#,
        r#"<hp:stringParam name="Formula">=SUM(LEFT)</hp:stringParam>"#,
        r#"<hp:stringParam name="ResultFormat">%g,</hp:stringParam>"#,
        r#"<hp:stringParam name="LastResult">7</hp:stringParam></hp:parameters>"#,
        r#"</hp:fieldBegin></hp:ctrl><hp:t>7</hp:t><hp:ctrl>"#,
        r#"<hp:fieldEnd beginIDRef="101" fieldid="202"/></hp:ctrl><hp:t/></hp:run></hp:p>"#,
    )
}

#[allow(clippy::too_many_arguments)]
fn cell(row: u32, column: u32, width: u32, payload: &str, border_fill_id: u32) -> String {
    format!(
        concat!(
            r#"<hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="0" borderFillIDRef="{border_fill_id}">"#,
            r#"<hp:cellAddr colAddr="{column}" rowAddr="{row}"/>"#,
            r#"<hp:cellSpan colSpan="1" rowSpan="1"/>"#,
            r#"<hp:cellSz width="{width}" height="500"/>"#,
            r#"<hp:cellMargin left="0" right="0" top="0" bottom="0"/>"#,
            r#"<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">"#,
            "{payload}</hp:subList></hp:tc>"
        ),
        row = row,
        column = column,
        width = width,
        payload = payload,
        border_fill_id = border_fill_id,
    )
}

fn table(
    native_id: u32,
    columns: u32,
    width: u32,
    prefix: &str,
    formula: bool,
    top_border_fill_id: u32,
) -> String {
    let column_width = width / columns;
    let mut rows = String::new();
    for row in 0..2 {
        rows.push_str("<hp:tr>");
        for column in 0..columns {
            let payload = if formula && row == 1 && column + 1 == columns {
                formula_paragraph().to_owned()
            } else {
                paragraph(&format!("{prefix}{row}{column}"))
            };
            let border_fill_id = if row == 0 { top_border_fill_id } else { 1 };
            rows.push_str(&cell(row, column, column_width, &payload, border_fill_id));
        }
        rows.push_str("</hp:tr>");
    }
    format!(
        concat!(
            r#"<hp:tbl id="{native_id}" zOrder="0" numberingType="TABLE" textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" pageBreak="CELL" repeatHeader="0" rowCnt="2" colCnt="{columns}" cellSpacing="0" borderFillIDRef="1" noAdjust="0">"#,
            r#"<hp:sz width="{width}" widthRelTo="ABSOLUTE" height="1000" heightRelTo="ABSOLUTE" protect="0"/>"#,
            r#"<hp:pos treatAsChar="0" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP" horzAlign="LEFT" vertOffset="2000" horzOffset="1000"/>"#,
            r#"<hp:outMargin left="0" right="0" top="0" bottom="0"/>"#,
            r#"<hp:inMargin left="0" right="0" top="0" bottom="0"/>"#,
            "{rows}</hp:tbl>"
        ),
        native_id = native_id,
        columns = columns,
        width = width,
        rows = rows,
    )
}

fn wrapper(paragraph_id: u32, table: &str) -> String {
    format!(
        r#"<hp:p id="{paragraph_id}" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0">{table}</hp:run></hp:p>"#
    )
}

fn separator(value: &str) -> String {
    format!(
        r#"<hp:p id="30" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t>{value}</hp:t></hp:run></hp:p>"#
    )
}

fn tail() -> String {
    r#"<hp:p id="90" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t>TAIL</hp:t></hp:run></hp:p>"#.to_owned()
}

fn section(separator_text: &str, formula: bool, trailing_top_border: u32) -> Vec<u8> {
    let parts = [
        wrapper(10, &table(700, 2, 2000, "L", false, 1)),
        separator(separator_text),
        wrapper(20, &table(701, 3, 3000, "T", formula, trailing_top_border)),
        tail(),
    ];
    format!(
        r#"<hs:sec xmlns:hs="{SECTION_NS}" xmlns:hp="{PARAGRAPH_NS}">{}</hs:sec>"#,
        parts.concat()
    )
    .into_bytes()
}

fn binding(prefix: &str, columns: u32, width: u32) -> TestResult<TableRulingHwpxBinding> {
    let mut cells = Vec::new();
    for index in 0..(2 * columns) {
        cells.push(TableRulingHwpxCellBinding {
            master_cell_id: id(&format!("{prefix}-cell-{index}"))?,
            payload_block_ids: vec![id(&format!("{prefix}-payload-{index}"))?],
        });
    }
    let column_width = width / columns;
    Ok(TableRulingHwpxBinding {
        table_id: id(&format!("{prefix}-table"))?,
        row_boundaries_hwpunit: vec![0, 500, 1000],
        column_boundaries_hwpunit: (0..=columns).map(|column| column * column_width).collect(),
        cells,
    })
}

fn read(section: &[u8]) -> TestResult<TableJoinHwpxReadback> {
    Ok(TableJoinHwpxReader::read_existing(
        HEADER,
        section,
        0,
        1,
        &binding("leading", 2, 2000)?,
        &binding("trailing", 3, 3000)?,
        TableJoinHwpxLimits::default(),
    )?)
}

fn request_draft(source: &TableJoinHwpxReadback) -> TestResult<TableJoinHwpxRequestDraft> {
    let limits = TableJoinHwpxLimits::default();
    Ok(TableJoinHwpxRequestDraft {
        schema_version: TABLE_JOIN_HWPX_SCHEMA_VERSION.to_owned(),
        leading_table_ordinal: 0,
        trailing_table_ordinal: 1,
        expected_header_sha256: hex(source.leading.ruling.header_sha256),
        expected_section_sha256: hex(source.leading.ruling.section_sha256),
        expected_leading_wrapper_sha256: hex(source.leading.wrapper_sha256),
        expected_trailing_wrapper_sha256: hex(source.trailing.wrapper_sha256),
        expected_separator_sha256: hex(source.separator_sha256),
        join: WholeTableJoinRequestDraft {
            schema_version: TABLE_PARTITION_SCHEMA_VERSION.to_owned(),
            leading_table_id: source.leading.partition.table_id().clone(),
            trailing_table_id: source.trailing.partition.table_id().clone(),
            separator_tokens: source.separator_tokens.clone(),
            expected_leading_state_sha256: hex(source
                .leading
                .partition
                .canonical_sha256(limits.partition)?),
            expected_trailing_state_sha256: hex(source
                .trailing
                .partition
                .canonical_sha256(limits.partition)?),
            expected_flow_sha256: digest('f'),
            formula_policy: TablePartitionFormulaPolicy::Reject,
        },
    })
}

#[test]
fn join_projects_unequal_tables_and_reopens_complete_state() -> TestResult {
    let section = section("   ", false, 1);
    let limits = TableJoinHwpxLimits::default();
    let source = read(&section)?;
    assert_eq!(
        source.separator_tokens,
        vec![
            TableJoinSeparatorToken::SpaceRun { count: 3 },
            TableJoinSeparatorToken::ParagraphBreak,
        ]
    );
    let request =
        TableJoinHwpxRequest::from_draft(request_draft(&source)?, &source, &digest('f'), limits)?;
    let plan = TableJoinHwpxBuilder::build(&request, &source, &digest('f'), limits)?;
    assert_eq!(plan.joined_grid().rows(), 4);
    assert_eq!(plan.joined_grid().columns(), 4);
    assert_eq!(plan.joined_state().frame().width_hwpunit, 3000);
    assert_eq!(
        plan.joined_state().column_boundaries_hwpunit(),
        &[0, 1000, 1500, 2000, 3000]
    );
    let lowered = TableJoinHwpxLowerer::lower_existing(
        HEADER,
        &section,
        &binding("leading", 2, 2000)?,
        &binding("trailing", 3, 3000)?,
        &digest('f'),
        &request,
        &plan,
        limits,
    )?;
    let layout = TableLayoutHwpxReader::read_in_section(&lowered.section, 0, limits.ruling.layout)?;
    assert_eq!((layout.rows, layout.columns), (4, 4));
    assert_eq!(
        TableLayoutHwpxReader::count_in_section(&lowered.section, limits.ruling.layout)?,
        1
    );
    let text = std::str::from_utf8(&lowered.section)?;
    assert!(text.contains("L00"));
    assert!(text.contains("T12"));
    assert!(text.contains("TAIL"));
    assert!(text.contains(r#"<hp:tbl id="700""#));
    assert!(!text.contains(r#"id="701""#));
    assert!(!text.contains(r#"<hp:p id="30""#));
    assert_eq!(lowered.receipt.preserved_master_cell_count, 10);
    assert_eq!(lowered.receipt.preserved_payload_block_count, 10);
    assert_eq!(lowered.receipt.removed_table_count, 1);
    assert_eq!(lowered.receipt.removed_separator_paragraph_count, 1);
    assert_eq!(
        request.canonical_json(limits)?,
        request.canonical_json(limits)?
    );
    Ok(())
}

#[test]
fn join_rejects_non_whitespace_or_missing_separator() -> TestResult {
    let source = section("   ", false, 1);
    let needle = b"<hp:t>   </hp:t>";
    let start = source
        .windows(needle.len())
        .position(|window| window == needle)
        .ok_or("separator text is missing")?;
    let native_empty_run = [
        source[..start].to_vec(),
        source[start + needle.len()..].to_vec(),
    ]
    .concat();
    let native = read(&native_empty_run)?;
    assert_eq!(
        native.separator_tokens,
        vec![TableJoinSeparatorToken::ParagraphBreak]
    );
    assert!(matches!(read(&section("X", false, 1)), Err(error) if error
            .downcast_ref::<TableJoinHwpxError>()
            .is_some_and(|value| matches!(value, TableJoinHwpxError::UnsupportedSeparator))));
    let no_separator = format!(
        r#"<hs:sec xmlns:hs="{SECTION_NS}" xmlns:hp="{PARAGRAPH_NS}">{}{}</hs:sec>"#,
        wrapper(10, &table(700, 2, 2000, "L", false, 1)),
        wrapper(20, &table(701, 3, 3000, "T", false, 1)),
    )
    .into_bytes();
    assert!(matches!(read(&no_separator), Err(error) if error
            .downcast_ref::<TableJoinHwpxError>()
            .is_some_and(|value| matches!(value, TableJoinHwpxError::UnsupportedSeparator))));
    let hidden_content = format!(
        r#"<hs:sec xmlns:hs="{SECTION_NS}" xmlns:hp="{PARAGRAPH_NS}">{}{}{}</hs:sec>"#,
        wrapper(10, &table(700, 2, 2000, "L", false, 1)),
        separator("").replacen("<hp:run", "<!--hidden--><hp:run", 1),
        wrapper(20, &table(701, 3, 3000, "T", false, 1)),
    )
    .into_bytes();
    assert!(matches!(read(&hidden_content), Err(error) if error
            .downcast_ref::<TableJoinHwpxError>()
            .is_some_and(|value| matches!(value, TableJoinHwpxError::UnsupportedSeparator))));
    let interstitial_comment = format!(
        r#"<hs:sec xmlns:hs="{SECTION_NS}" xmlns:hp="{PARAGRAPH_NS}">{}<!--hidden-->{}{}</hs:sec>"#,
        wrapper(10, &table(700, 2, 2000, "L", false, 1)),
        separator(""),
        wrapper(20, &table(701, 3, 3000, "T", false, 1)),
    )
    .into_bytes();
    assert!(matches!(read(&interstitial_comment), Err(error) if error
            .downcast_ref::<TableJoinHwpxError>()
            .is_some_and(|value| matches!(value, TableJoinHwpxError::UnsupportedSeparator))));
    Ok(())
}

#[test]
fn join_rejects_formula_profile_and_junction_edge_loss() -> TestResult {
    let formula_section = section("", true, 1);
    let mut trailing_binding = binding("trailing", 3, 3000)?;
    trailing_binding
        .cells
        .last_mut()
        .ok_or("missing trailing cell")?
        .payload_block_ids
        .clear();
    assert!(matches!(
        TableJoinHwpxReader::read_existing(
            HEADER,
            &formula_section,
            0,
            1,
            &binding("leading", 2, 2000)?,
            &trailing_binding,
            TableJoinHwpxLimits::default(),
        ),
        Err(TableJoinHwpxError::UnsupportedFormulaProfile)
    ));

    let mut header = String::from_utf8(HEADER.to_vec())?;
    header = header.replacen(
        r#"<hh:borderFills itemCnt="2">"#,
        r#"<hh:borderFills itemCnt="3">"#,
        1,
    );
    let border = concat!(
        r#"<hh:borderFill id="3" threeD="0" shadow="0" centerLine="NONE" breakCellSeparateLine="0">"#,
        r#"<hh:slash type="NONE" Crooked="0" isCounter="0"/><hh:backSlash type="NONE" Crooked="0" isCounter="0"/>"#,
        r##"<hh:leftBorder type="NONE" width="0.1 mm" color="#000000"/><hh:rightBorder type="NONE" width="0.1 mm" color="#000000"/>"##,
        r##"<hh:topBorder type="SOLID" width="0.1 mm" color="#000000"/><hh:bottomBorder type="NONE" width="0.1 mm" color="#000000"/>"##,
        r##"<hh:diagonal type="SOLID" width="0.1 mm" color="#000000"/></hh:borderFill>"##,
    );
    header = header.replacen(
        "</hh:borderFills>",
        &format!("{border}</hh:borderFills>"),
        1,
    );
    let section = section("", false, 3);
    let limits = TableJoinHwpxLimits::default();
    let source = TableJoinHwpxReader::read_existing(
        header.as_bytes(),
        &section,
        0,
        1,
        &binding("leading", 2, 2000)?,
        &binding("trailing", 3, 3000)?,
        limits,
    )?;
    let mut draft = request_draft(&source)?;
    draft.expected_header_sha256 = hex(source.leading.ruling.header_sha256);
    let result = TableJoinHwpxRequest::from_draft(draft, &source, &digest('f'), limits);
    assert!(matches!(
        result,
        Err(TableJoinHwpxError::JunctionEdgeMismatch)
    ));
    Ok(())
}

#[test]
fn join_rejects_divergent_page_split() -> TestResult {
    let section = String::from_utf8(section("", false, 1))?;
    let trailing_start = section
        .find(r#"id="701""#)
        .ok_or("trailing table missing")?;
    let (prefix, suffix) = section.split_at(trailing_start);
    let mismatch = format!(
        "{prefix}{}",
        suffix.replacen(r#"pageBreak="CELL""#, r#"pageBreak="TABLE""#, 1)
    );
    assert!(matches!(
        TableJoinHwpxReader::read_existing(
            HEADER,
            mismatch.as_bytes(),
            0,
            1,
            &binding("leading", 2, 2000)?,
            &binding("trailing", 3, 3000)?,
            TableJoinHwpxLimits::default(),
        ),
        Err(TableJoinHwpxError::PaginationMismatch)
    ));
    Ok(())
}

#[test]
fn join_rejects_source_flow_and_plan_drift() -> TestResult {
    let original_section = section("", false, 1);
    let limits = TableJoinHwpxLimits::default();
    let source = read(&original_section)?;
    let mut draft = request_draft(&source)?;
    draft.expected_separator_sha256 = digest('0');
    assert!(matches!(
        TableJoinHwpxRequest::from_draft(draft, &source, &digest('f'), limits),
        Err(TableJoinHwpxError::SourceBindingMismatch)
    ));
    let request =
        TableJoinHwpxRequest::from_draft(request_draft(&source)?, &source, &digest('f'), limits)?;
    assert!(TableJoinHwpxBuilder::build(&request, &source, &digest('e'), limits).is_err());
    let plan = TableJoinHwpxBuilder::build(&request, &source, &digest('f'), limits)?;
    let tampered = section(" ", false, 1);
    assert!(
        TableJoinHwpxLowerer::lower_existing(
            HEADER,
            &tampered,
            &binding("leading", 2, 2000)?,
            &binding("trailing", 3, 3000)?,
            &digest('f'),
            &request,
            &plan,
            limits,
        )
        .is_err()
    );
    Ok(())
}

#[test]
fn join_json_is_strict_bounded_and_debug_is_redacted() -> TestResult {
    let section = section("", false, 1);
    let limits = TableJoinHwpxLimits::default();
    let source = read(&section)?;
    let request =
        TableJoinHwpxRequest::from_draft(request_draft(&source)?, &source, &digest('f'), limits)?;
    assert!(matches!(
        TableJoinHwpxRequest::from_json(b"", &source, &digest('f'), limits),
        Err(TableJoinHwpxError::InputLimit)
    ));
    let oversized = vec![b' '; limits.partition.config().input_bytes + 1];
    assert!(matches!(
        TableJoinHwpxRequest::from_json(&oversized, &source, &digest('f'), limits),
        Err(TableJoinHwpxError::InputLimit)
    ));
    let json = request.canonical_json(limits)?;
    let duplicate = String::from_utf8(json.clone())?.replacen(
        r#"{"schema_version":"hwpx-agent.table-join-hwpx/v1""#,
        r#"{"schema_version":"hwpx-agent.table-join-hwpx/v1","schema_version":"hwpx-agent.table-join-hwpx/v1""#,
        1,
    );
    assert!(matches!(
        TableJoinHwpxRequest::from_json(duplicate.as_bytes(), &source, &digest('f'), limits),
        Err(TableJoinHwpxError::InvalidJson)
    ));
    let unknown = String::from_utf8(json)?.replacen('{', r#"{"unknown":true,"#, 1);
    assert!(matches!(
        TableJoinHwpxRequest::from_json(unknown.as_bytes(), &source, &digest('f'), limits),
        Err(TableJoinHwpxError::InvalidJson)
    ));
    let debug = format!("{request:?}");
    assert!(!debug.contains(source.leading.partition.table_id().as_str()));
    assert!(!debug.contains(&hex(source.separator_sha256)));
    assert!(debug.contains("<redacted>"));
    Ok(())
}

#[test]
fn join_closed_package_preserves_sibling_formula_and_non_section_parts() -> TestResult {
    let sibling = wrapper(40, &table(800, 3, 3000, "S", true, 1));
    let trailing_tail = tail();
    let source_section = format!(
        r#"<hs:sec xmlns:hs="{SECTION_NS}" xmlns:hp="{PARAGRAPH_NS}">{}{}{}{}{}</hs:sec>"#,
        wrapper(10, &table(700, 2, 2000, "L", false, 1)),
        separator("  "),
        wrapper(20, &table(701, 3, 3000, "T", false, 1)),
        trailing_tail,
        sibling,
    )
    .into_bytes();
    let limits = TableJoinHwpxLimits::default();
    let source = TableJoinHwpxReader::read_existing(
        HEADER,
        &source_section,
        0,
        1,
        &binding("leading", 2, 2000)?,
        &binding("trailing", 3, 3000)?,
        limits,
    )?;
    let formula_before = TableFormulaHwpxReader::read_in_section(
        &source_section,
        2,
        TableFormulaHwpxLimits::default(),
        limits.ruling.formula,
    )?;
    let request =
        TableJoinHwpxRequest::from_draft(request_draft(&source)?, &source, &digest('f'), limits)?;
    let plan = TableJoinHwpxBuilder::build(&request, &source, &digest('f'), limits)?;
    let lowered = TableJoinHwpxLowerer::lower_existing(
        HEADER,
        &source_section,
        &binding("leading", 2, 2000)?,
        &binding("trailing", 3, 3000)?,
        &digest('f'),
        &request,
        &plan,
        limits,
    )?;
    let expected_tail = format!("{trailing_tail}{sibling}</hs:sec>");
    assert!(std::str::from_utf8(&lowered.section)?.ends_with(&expected_tail));
    let formula_after = TableFormulaHwpxReader::read_in_section(
        &lowered.section,
        1,
        TableFormulaHwpxLimits::default(),
        limits.ruling.formula,
    )?;
    assert_eq!(formula_before.rows, formula_after.rows);
    assert_eq!(formula_before.columns, formula_after.columns);
    assert_eq!(formula_before.formula, formula_after.formula);
    assert_eq!(
        formula_before.formula_field_count,
        formula_after.formula_field_count
    );

    let source_package = package(HEADER, &source_section)?;
    let output_package = replace_parts(&source_package, &lowered.header, &lowered.section)?;
    assert_non_section_parts_preserved(&source_package, &output_package)?;
    let mut reader = BoundedZipReader::open(Cursor::new(output_package), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    assert_eq!(graph.spine.len(), 1);
    Ok(())
}

fn package(header: &[u8], section: &[u8]) -> Result<Vec<u8>, zip::result::ZipError> {
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    for (path, bytes, method) in [
        (
            "mimetype",
            b"application/hwp+zip".as_slice(),
            CompressionMethod::Stored,
        ),
        (
            "version.xml",
            b"<version/>".as_slice(),
            CompressionMethod::Stored,
        ),
        (
            "META-INF/container.xml",
            CONTAINER.as_bytes(),
            CompressionMethod::Deflated,
        ),
        (
            "Contents/content.hpf",
            OPF.as_bytes(),
            CompressionMethod::Deflated,
        ),
        ("Contents/header.xml", header, CompressionMethod::Deflated),
        (
            "Contents/section0.xml",
            section,
            CompressionMethod::Deflated,
        ),
        (
            "Contents/opaque.bin",
            b"opaque".as_slice(),
            CompressionMethod::Stored,
        ),
    ] {
        let options = SimpleFileOptions::default()
            .compression_method(method)
            .last_modified_time(DateTime::default())
            .system(zip::System::Unix)
            .unix_permissions(0o644);
        writer.start_file(path, options)?;
        writer.write_all(bytes)?;
    }
    Ok(writer.finish()?.into_inner())
}

fn replace_parts(source: &[u8], header: &[u8], section: &[u8]) -> TestResult<Vec<u8>> {
    let mut reader = BoundedZipReader::open(Cursor::new(source), PackageLimits::default())?;
    let entries = reader.entries().to_vec();
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    for entry in entries {
        let path = entry.path.as_str();
        let bytes = match path {
            "Contents/header.xml" => header.to_vec(),
            "Contents/section0.xml" => section.to_vec(),
            _ => reader.read_entry(entry.index)?,
        };
        let method = match entry.compression {
            Compression::Stored => CompressionMethod::Stored,
            Compression::Deflated => CompressionMethod::Deflated,
        };
        let options = SimpleFileOptions::default()
            .compression_method(method)
            .last_modified_time(DateTime::default())
            .system(zip::System::Unix)
            .unix_permissions(0o644);
        writer.start_file(path, options)?;
        writer.write_all(&bytes)?;
    }
    Ok(writer.finish()?.into_inner())
}

fn assert_non_section_parts_preserved(source: &[u8], target: &[u8]) -> TestResult {
    let mut source = BoundedZipReader::open(Cursor::new(source), PackageLimits::default())?;
    let mut target = BoundedZipReader::open(Cursor::new(target), PackageLimits::default())?;
    for entry in source.entries().to_vec() {
        let path = entry.path.as_str();
        if !matches!(path, "Contents/header.xml" | "Contents/section0.xml") {
            let target_index = target
                .entries()
                .iter()
                .find(|target_entry| target_entry.path.as_str() == path)
                .map(|target_entry| target_entry.index)
                .ok_or("target package entry missing")?;
            assert_eq!(
                source.read_entry(entry.index)?,
                target.read_entry(target_index)?
            );
        }
    }
    Ok(())
}
