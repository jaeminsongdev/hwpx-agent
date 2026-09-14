use std::collections::BTreeMap;
use std::io::{Cursor, Write};

use domain_ir::{CellCoordinate, LogicalId, TableGridLimitConfig, TableGridLimits};
use hwpx_package::{
    BoundedZipReader, Compression, PackageGraph, PackageGraphLimits, PackageLimits,
    TABLE_NESTED_TABLE_HWPX_SCHEMA_VERSION, TableNestedTableHwpxBuilder, TableNestedTableHwpxError,
    TableNestedTableHwpxLimits, TableNestedTableHwpxLowerer, TableNestedTableHwpxReader,
    TableNestedTableHwpxRequest, TableNestedTableHwpxRequestDraft, TableRulingHwpxBinding,
    TableRulingHwpxCellBinding, TableRulingHwpxReader,
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

fn flow(value: char) -> String {
    std::iter::repeat_n(value, 64).collect()
}

fn hex(value: impl AsRef<[u8]>) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let mut output = String::new();
    for byte in value.as_ref() {
        output.push(char::from(DIGITS[usize::from(byte >> 4)]));
        output.push(char::from(DIGITS[usize::from(byte & 0x0f)]));
    }
    output
}

fn header() -> TestResult<Vec<u8>> {
    let text = String::from_utf8(HEADER.to_vec())?;
    let solid = concat!(
        r#"<hh:borderFill id="3" threeD="0" shadow="0" centerLine="NONE" breakCellSeparateLine="0">"#,
        r#"<hh:slash type="NONE" Crooked="0" isCounter="0"/>"#,
        r#"<hh:backSlash type="NONE" Crooked="0" isCounter="0"/>"#,
        r##"<hh:leftBorder type="SOLID" width="0.1 mm" color="#000000"/>"##,
        r##"<hh:rightBorder type="SOLID" width="0.1 mm" color="#000000"/>"##,
        r##"<hh:topBorder type="SOLID" width="0.1 mm" color="#000000"/>"##,
        r##"<hh:bottomBorder type="SOLID" width="0.1 mm" color="#000000"/>"##,
        r##"<hh:diagonal type="SOLID" width="0.1 mm" color="#000000"/>"##,
        r#"</hh:borderFill>"#,
    );
    Ok(text
        .replacen(
            "<hh:borderFills itemCnt=\"2\">",
            "<hh:borderFills itemCnt=\"3\">",
            1,
        )
        .replacen("</hh:borderFills>", &format!("{solid}</hh:borderFills>"), 1)
        .into_bytes())
}

fn text_paragraph(identifier: u32, value: &str) -> String {
    format!(
        r#"<hp:p id="{identifier}" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t>{value}</hp:t></hp:run></hp:p>"#
    )
}

fn empty_paragraph(identifier: u32) -> String {
    format!(
        r#"<hp:p id="{identifier}" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t/></hp:run></hp:p>"#
    )
}

fn formula_paragraph(begin_id: u32, field_id: u32) -> String {
    format!(
        concat!(
            r#"<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:ctrl>"#,
            r#"<hp:fieldBegin id="{begin_id}" type="FORMULA" name="" editable="0" dirty="0" zorder="-1" fieldid="{field_id}">"#,
            r#"<hp:parameters cnt="5" name=""><hp:integerParam name="Prop">8</hp:integerParam>"#,
            r#"<hp:stringParam name="Command">=SUM(LEFT)??%g,;;7</hp:stringParam>"#,
            r#"<hp:stringParam name="Formula">=SUM(LEFT)</hp:stringParam>"#,
            r#"<hp:stringParam name="ResultFormat">%g,</hp:stringParam>"#,
            r#"<hp:stringParam name="LastResult">7</hp:stringParam></hp:parameters>"#,
            r#"</hp:fieldBegin></hp:ctrl><hp:t>7</hp:t><hp:ctrl>"#,
            r#"<hp:fieldEnd beginIDRef="{begin_id}" fieldid="{field_id}"/></hp:ctrl><hp:t/></hp:run></hp:p>"#,
        ),
        begin_id = begin_id,
        field_id = field_id,
    )
}

#[allow(clippy::too_many_arguments)]
fn cell(
    row: u32,
    column: u32,
    row_span: u32,
    column_span: u32,
    width: u32,
    height: u32,
    payload: &str,
) -> String {
    format!(
        concat!(
            r#"<hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="0" borderFillIDRef="3">"#,
            r#"<hp:cellAddr colAddr="{column}" rowAddr="{row}"/>"#,
            r#"<hp:cellSpan colSpan="{column_span}" rowSpan="{row_span}"/>"#,
            r#"<hp:cellSz width="{width}" height="{height}"/>"#,
            r#"<hp:cellMargin left="0" right="0" top="0" bottom="0"/>"#,
            r#"<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">"#,
            "{payload}</hp:subList></hp:tc>"
        ),
        row = row,
        column = column,
        row_span = row_span,
        column_span = column_span,
        width = width,
        height = height,
        payload = payload,
    )
}

fn table(
    native_id: u32,
    treat_as_char: bool,
    rows: u32,
    columns: u32,
    width: u32,
    height: u32,
    body: &str,
) -> String {
    format!(
        concat!(
            r#"<hp:tbl id="{native_id}" zOrder="0" numberingType="TABLE" textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" pageBreak="CELL" repeatHeader="0" rowCnt="{rows}" colCnt="{columns}" cellSpacing="0" borderFillIDRef="1" noAdjust="0">"#,
            r#"<hp:sz width="{width}" widthRelTo="ABSOLUTE" height="{height}" heightRelTo="ABSOLUTE" protect="0"/>"#,
            r#"<hp:pos treatAsChar="{inline}" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP" horzAlign="LEFT" vertOffset="0" horzOffset="0"/>"#,
            r#"<hp:outMargin left="0" right="0" top="0" bottom="0"/><hp:inMargin left="0" right="0" top="0" bottom="0"/>"#,
            "{body}</hp:tbl>"
        ),
        native_id = native_id,
        rows = rows,
        columns = columns,
        width = width,
        height = height,
        inline = u8::from(treat_as_char),
        body = body,
    )
}

fn table_paragraph(identifier: u32, table: &str) -> String {
    format!(
        r#"<hp:p id="{identifier}" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0">{table}</hp:run></hp:p>"#
    )
}

fn parent_section() -> Vec<u8> {
    let payload = format!(
        "{}{}{}",
        text_paragraph(11, "PARENT-BEFORE"),
        empty_paragraph(12),
        text_paragraph(13, "PARENT-AFTER")
    );
    let body = format!("<hp:tr>{}</hp:tr>", cell(0, 0, 1, 1, 5000, 3000, &payload));
    let parent = table(700, false, 1, 1, 5000, 3000, &body);
    format!(
        r#"<hs:sec xmlns:hs="{SECTION_NS}" xmlns:hp="{PARAGRAPH_NS}">{}{}{}{}</hs:sec>"#,
        text_paragraph(1, "DOCUMENT-BEFORE"),
        table_paragraph(2, &parent),
        text_paragraph(3, "DOCUMENT-AFTER"),
        text_paragraph(4, "PRESERVE-SENTINEL"),
    )
    .into_bytes()
}

fn merged_parent_section() -> Vec<u8> {
    let payload = format!("{}{}", empty_paragraph(12), text_paragraph(13, "KEEP"));
    let body = format!("<hp:tr>{}</hp:tr>", cell(0, 0, 1, 2, 5000, 3000, &payload));
    let parent = table(700, false, 1, 2, 5000, 3000, &body);
    format!(
        r#"<hs:sec xmlns:hs="{SECTION_NS}" xmlns:hp="{PARAGRAPH_NS}">{}</hs:sec>"#,
        table_paragraph(2, &parent),
    )
    .into_bytes()
}

fn template_section(inline: bool, native_id: u32, begin_id: u32, field_id: u32) -> Vec<u8> {
    let row0 = format!(
        "<hp:tr>{}{}</hp:tr>",
        cell(0, 0, 1, 1, 1000, 500, &text_paragraph(0, "A")),
        cell(0, 1, 1, 1, 1000, 500, &text_paragraph(0, "B")),
    );
    let row1 = format!(
        "<hp:tr>{}{}</hp:tr>",
        cell(1, 0, 1, 1, 1000, 500, &text_paragraph(0, "7")),
        cell(
            1,
            1,
            1,
            1,
            1000,
            500,
            &formula_paragraph(begin_id, field_id)
        ),
    );
    let nested = table(
        native_id,
        inline,
        2,
        2,
        2000,
        1000,
        &format!("{row0}{row1}"),
    );
    format!(
        r#"<hs:sec xmlns:hs="{SECTION_NS}" xmlns:hp="{PARAGRAPH_NS}">{}</hs:sec>"#,
        table_paragraph(900, &nested),
    )
    .into_bytes()
}

fn parent_binding(merged: bool) -> TestResult<TableRulingHwpxBinding> {
    Ok(TableRulingHwpxBinding {
        table_id: id("parent-table")?,
        row_boundaries_hwpunit: vec![0, 3000],
        column_boundaries_hwpunit: if merged {
            vec![0, 2500, 5000]
        } else {
            vec![0, 5000]
        },
        cells: vec![TableRulingHwpxCellBinding {
            master_cell_id: id("parent-cell")?,
            payload_block_ids: if merged {
                vec![id("parent-keep")?]
            } else {
                vec![id("parent-before")?, id("parent-after")?]
            },
        }],
    })
}

fn template_binding() -> TestResult<TableRulingHwpxBinding> {
    Ok(TableRulingHwpxBinding {
        table_id: id("nested-table")?,
        row_boundaries_hwpunit: vec![0, 500, 1000],
        column_boundaries_hwpunit: vec![0, 1000, 2000],
        cells: ["nested-a", "nested-b", "nested-c", "nested-d"]
            .into_iter()
            .enumerate()
            .map(|(index, value)| {
                Ok(TableRulingHwpxCellBinding {
                    master_cell_id: id(value)?,
                    payload_block_ids: if index < 3 {
                        vec![id(&format!("nested-payload-{index}"))?]
                    } else {
                        Vec::new()
                    },
                })
            })
            .collect::<TestResult<Vec<_>>>()?,
    })
}

fn context(
    header: &[u8],
    section: &[u8],
    template: &[u8],
) -> TestResult<hwpx_package::TableNestedTableHwpxReadback> {
    Ok(TableNestedTableHwpxReader::read_context(
        header,
        section,
        0,
        CellCoordinate { row: 0, column: 0 },
        1,
        &parent_binding(false)?,
        template,
        0,
        &template_binding()?,
        TableNestedTableHwpxLimits::default(),
    )?)
}

fn draft(
    source: &hwpx_package::TableNestedTableHwpxReadback,
    before_flow: char,
    after_flow: char,
) -> TestResult<TableNestedTableHwpxRequestDraft> {
    let limits = TableNestedTableHwpxLimits::default();
    Ok(TableNestedTableHwpxRequestDraft {
        schema_version: TABLE_NESTED_TABLE_HWPX_SCHEMA_VERSION.to_owned(),
        capability_id: "table.nested_table".to_owned(),
        parent_table_ordinal: source.parent_table_ordinal,
        parent_cell: source.parent_cell,
        placeholder_paragraph_ordinal: source.placeholder_paragraph_ordinal,
        template_table_ordinal: source.template_table_ordinal,
        nested_payload_block_id: id("parent-nested-table-payload")?,
        expected_header_sha256: hex(source.header_sha256),
        expected_section_sha256: hex(source.section_sha256),
        expected_parent_state_sha256: hex(source
            .parent
            .state
            .canonical_sha256(limits.ruling.ruling)?),
        expected_parent_grid_sha256: hex(source.parent.grid.canonical_sha256()?),
        expected_parent_table_content_sha256: hex(source.parent.table_content_sha256),
        expected_template_section_sha256: hex(source.template_section_sha256),
        expected_template_state_sha256: hex(source
            .template
            .state
            .canonical_sha256(limits.ruling.ruling)?),
        expected_template_grid_sha256: hex(source.template.grid.canonical_sha256()?),
        expected_template_table_content_sha256: hex(source.template.table_content_sha256),
        expected_insertion_context_sha256: source.insertion_context_sha256.clone(),
        expected_nested_wrapper_sha256: source.nested_wrapper_sha256.clone(),
        expected_source_table_count: source.source_table_count,
        expected_document_flow_sha256: flow(before_flow),
        target_document_flow_sha256: flow(after_flow),
    })
}

fn admitted(
    source: &hwpx_package::TableNestedTableHwpxReadback,
    draft: TableNestedTableHwpxRequestDraft,
    current_flow: char,
) -> TestResult<(
    TableNestedTableHwpxRequest,
    hwpx_package::TableNestedTableHwpxPlan,
)> {
    let limits = TableNestedTableHwpxLimits::default();
    let request =
        TableNestedTableHwpxRequest::from_draft(draft, source, &flow(current_flow), limits)?;
    let plan = TableNestedTableHwpxBuilder::build(&request, source, &flow(current_flow), limits)?;
    Ok((request, plan))
}

#[test]
fn inserts_complete_nested_table_and_reopens_parent_payload_formula_and_pagination() -> TestResult {
    let header = header()?;
    let section = parent_section();
    let template = template_section(true, 800, 101, 202);
    let source = context(&header, &section, &template)?;
    let immutable_source = source.clone();
    let (request, plan) = admitted(&source, draft(&source, 'a', 'b')?, 'a')?;
    let output = TableNestedTableHwpxLowerer::lower_at_cell_placeholder(
        &header,
        &section,
        &parent_binding(false)?,
        &template,
        &template_binding()?,
        &flow('a'),
        &request,
        &plan,
        TableNestedTableHwpxLimits::default(),
    )?;
    let parent = TableRulingHwpxReader::read_existing(
        &output.header,
        &output.section,
        output.parent_table_ordinal,
        &output.parent_binding,
        TableNestedTableHwpxLimits::default().ruling,
    )?;
    let nested = TableRulingHwpxReader::read_existing(
        &output.header,
        &output.section,
        output.nested_table_ordinal,
        &output.nested_binding,
        TableNestedTableHwpxLimits::default().ruling,
    )?;

    assert_eq!(source, immutable_source);
    assert_eq!(parent.state, *plan.target_parent_state());
    assert_eq!(nested.state, *plan.target_nested_state());
    assert_eq!(nested.grid, *plan.target_nested_grid());
    assert_eq!(parent.formula_count, 0);
    assert_eq!(nested.formula_count, 1);
    assert_eq!(parent.payload_block_count, 3);
    assert_eq!(nested.payload_block_count, 3);
    assert_eq!(output.receipt.source_table_count, 1);
    assert_eq!(output.receipt.target_table_count, 2);
    assert!(output.receipt.parent_pagination_preserved);
    assert!(output.receipt.nested_pagination_preserved);
    let payload_ids: Vec<_> = parent.state.cells()[0]
        .payload()
        .iter()
        .map(|block| block.block_id.as_str())
        .collect();
    assert_eq!(
        payload_ids,
        [
            "parent-before",
            "parent-nested-table-payload",
            "parent-after"
        ]
    );
    let xml = String::from_utf8(output.section)?;
    for sentinel in [
        "DOCUMENT-BEFORE",
        "PARENT-BEFORE",
        "PARENT-AFTER",
        "DOCUMENT-AFTER",
        "PRESERVE-SENTINEL",
        "=SUM(LEFT)",
    ] {
        assert!(xml.contains(sentinel));
    }
    Ok(())
}

#[test]
fn hancom_nested_wrapper_normalization_preserves_composed_semantics() -> TestResult {
    let header = header()?;
    let section = parent_section();
    let template = template_section(true, 800, 101, 202);
    let source = context(&header, &section, &template)?;
    let (request, plan) = admitted(&source, draft(&source, 'a', 'b')?, 'a')?;
    let output = TableNestedTableHwpxLowerer::lower_at_cell_placeholder(
        &header,
        &section,
        &parent_binding(false)?,
        &template,
        &template_binding()?,
        &flow('a'),
        &request,
        &plan,
        TableNestedTableHwpxLimits::default(),
    )?;
    let target_parent = TableRulingHwpxReader::read_existing(
        &output.header,
        &output.section,
        output.parent_table_ordinal,
        &output.parent_binding,
        TableNestedTableHwpxLimits::default().ruling,
    )?;
    let target_nested = TableRulingHwpxReader::read_existing(
        &output.header,
        &output.section,
        output.nested_table_ordinal,
        &output.nested_binding,
        TableNestedTableHwpxLimits::default().ruling,
    )?;

    let mut normalized = String::from_utf8(output.section.clone())?;
    normalized = normalized.replacen(
        r#"<hp:p id="900" paraPrIDRef="0" styleIDRef="0">"#,
        r#"<hp:p id="900" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">"#,
        1,
    );
    let formula_tail =
        r#"<hp:fieldEnd beginIDRef="101" fieldid="202"/></hp:ctrl><hp:t/></hp:run></hp:p>"#;
    let cached_formula_tail = concat!(
        r#"<hp:fieldEnd beginIDRef="101" fieldid="202"/></hp:ctrl><hp:t/></hp:run>"#,
        r#"<hp:linesegarray><hp:lineseg textpos="0" vertpos="0"/></hp:linesegarray></hp:p>"#,
    );
    assert!(normalized.contains(formula_tail));
    normalized = normalized.replacen(formula_tail, cached_formula_tail, 1);
    assert_eq!(normalized.matches(r#"fieldid="202""#).count(), 2);
    normalized = normalized.replace(r#"fieldid="202""#, r#"fieldid="627469685""#);
    normalized = normalized.replacen(
        "</hp:tbl></hp:run></hp:p>",
        "</hp:tbl><hp:t/></hp:run></hp:p>",
        1,
    );

    let normalized_parent = TableRulingHwpxReader::read_existing(
        &output.header,
        normalized.as_bytes(),
        output.parent_table_ordinal,
        &output.parent_binding,
        TableNestedTableHwpxLimits::default().ruling,
    )?;
    let normalized_nested = TableRulingHwpxReader::read_existing(
        &output.header,
        normalized.as_bytes(),
        output.nested_table_ordinal,
        &output.nested_binding,
        TableNestedTableHwpxLimits::default().ruling,
    )?;
    assert_eq!(target_parent.state, normalized_parent.state);
    assert_eq!(target_nested.state, normalized_nested.state);

    let nondefault = normalized.replacen(r#"pageBreak="0""#, r#"pageBreak="1""#, 1);
    let nondefault_parent = TableRulingHwpxReader::read_existing(
        &output.header,
        nondefault.as_bytes(),
        output.parent_table_ordinal,
        &output.parent_binding,
        TableNestedTableHwpxLimits::default().ruling,
    )?;
    assert_ne!(target_parent.state, nondefault_parent.state);
    Ok(())
}

#[test]
fn covered_merged_cell_and_non_inline_template_fail_closed() -> TestResult {
    let header = header()?;
    let merged = merged_parent_section();
    let template = template_section(true, 800, 101, 202);
    assert!(matches!(
        TableNestedTableHwpxReader::read_context(
            &header,
            &merged,
            0,
            CellCoordinate { row: 0, column: 1 },
            0,
            &parent_binding(true)?,
            &template,
            0,
            &template_binding()?,
            TableNestedTableHwpxLimits::default(),
        ),
        Err(TableNestedTableHwpxError::CoveredCellSelector)
    ));

    let section = parent_section();
    let floating = template_section(false, 800, 101, 202);
    assert!(matches!(
        context(&header, &section, &floating),
        Err(error) if error.downcast_ref::<TableNestedTableHwpxError>()
            .is_some_and(|value| matches!(value, TableNestedTableHwpxError::UnsupportedTemplateProfile))
    ));

    let control_wrapped = String::from_utf8(template.clone())?
        .replacen(r#"<hp:tbl id="800""#, r#"<hp:ctrl><hp:tbl id="800""#, 1)
        .replacen("</hp:tbl>", "</hp:tbl></hp:ctrl>", 1)
        .into_bytes();
    assert!(matches!(
        context(&header, &section, &control_wrapped),
        Err(error) if error.downcast_ref::<TableNestedTableHwpxError>()
            .is_some_and(|value| matches!(value, TableNestedTableHwpxError::UnsupportedTemplateProfile))
    ));

    let resource_bearing = String::from_utf8(template)?
        .replacen(
            "<hp:t>A</hp:t>",
            "<hp:t binaryItemIDRef=\"image1\">A</hp:t>",
            1,
        )
        .into_bytes();
    assert!(matches!(
        context(&header, &section, &resource_bearing),
        Err(error) if error.downcast_ref::<TableNestedTableHwpxError>()
            .is_some_and(|value| matches!(value, TableNestedTableHwpxError::UnsupportedTemplateProfile))
    ));
    Ok(())
}

#[test]
fn request_rejects_all_bound_drift_duplicate_unknown_and_identity_tampering() -> TestResult {
    let header = header()?;
    let section = parent_section();
    let template = template_section(true, 800, 101, 202);
    let source = context(&header, &section, &template)?;
    let valid = draft(&source, 'a', 'b')?;

    for field in [
        "header",
        "section",
        "parent_state",
        "parent_grid",
        "parent_content",
        "template",
        "template_state",
        "template_grid",
        "template_content",
        "insertion",
        "wrapper",
        "flow",
    ] {
        let mut tampered = valid.clone();
        match field {
            "header" => tampered.expected_header_sha256 = flow('1'),
            "section" => tampered.expected_section_sha256 = flow('2'),
            "parent_state" => tampered.expected_parent_state_sha256 = flow('3'),
            "parent_grid" => tampered.expected_parent_grid_sha256 = flow('4'),
            "parent_content" => tampered.expected_parent_table_content_sha256 = flow('5'),
            "template" => tampered.expected_template_section_sha256 = flow('6'),
            "template_state" => tampered.expected_template_state_sha256 = flow('7'),
            "template_grid" => tampered.expected_template_grid_sha256 = flow('8'),
            "template_content" => tampered.expected_template_table_content_sha256 = flow('9'),
            "insertion" => tampered.expected_insertion_context_sha256 = flow('a'),
            "wrapper" => tampered.expected_nested_wrapper_sha256 = flow('b'),
            "flow" => tampered.expected_document_flow_sha256 = flow('c'),
            _ => unreachable!(),
        }
        assert!(matches!(
            TableNestedTableHwpxRequest::from_draft(
                tampered,
                &source,
                &flow('a'),
                TableNestedTableHwpxLimits::default(),
            ),
            Err(TableNestedTableHwpxError::SourceBindingMismatch)
        ));
    }

    let mut same_flow = valid.clone();
    same_flow.target_document_flow_sha256 = flow('a');
    assert!(matches!(
        TableNestedTableHwpxRequest::from_draft(
            same_flow,
            &source,
            &flow('a'),
            TableNestedTableHwpxLimits::default(),
        ),
        Err(TableNestedTableHwpxError::FlowBindingMismatch)
    ));
    let mut identity = valid.clone();
    identity.nested_payload_block_id = id("nested-a")?;
    assert!(matches!(
        TableNestedTableHwpxRequest::from_draft(
            identity,
            &source,
            &flow('a'),
            TableNestedTableHwpxLimits::default(),
        ),
        Err(TableNestedTableHwpxError::IdentityConflict)
    ));

    let json = serde_json::to_string(&valid)?;
    for invalid in [
        json.replacen(
            '{',
            r#"{"schema_version":"hwpx-agent.table-nested-table-hwpx/v1","#,
            1,
        ),
        json.replacen('{', r#"{"unknown":true,"#, 1),
    ] {
        assert!(matches!(
            TableNestedTableHwpxRequest::from_json(
                invalid.as_bytes(),
                &source,
                &flow('a'),
                TableNestedTableHwpxLimits::default(),
            ),
            Err(TableNestedTableHwpxError::InvalidJson)
        ));
    }
    Ok(())
}

#[test]
fn lowerer_rechecks_source_template_current_flow_and_foreign_plan() -> TestResult {
    let header = header()?;
    let section = parent_section();
    let template = template_section(true, 800, 101, 202);
    let source = context(&header, &section, &template)?;
    let (request, plan) = admitted(&source, draft(&source, 'a', 'b')?, 'a')?;
    let (_, foreign_plan) = admitted(&source, draft(&source, 'a', 'c')?, 'a')?;

    let mut changed_section = section.clone();
    let offset = changed_section
        .windows("DOCUMENT-BEFORE".len())
        .position(|window| window == b"DOCUMENT-BEFORE")
        .ok_or("sentinel missing")?;
    changed_section[offset] = b'X';
    let mut changed_template = template.clone();
    let offset = changed_template
        .windows("=SUM(LEFT)".len())
        .position(|window| window == b"=SUM(LEFT)")
        .ok_or("formula missing")?;
    changed_template[offset + 5] = b'R';

    for result in [
        TableNestedTableHwpxLowerer::lower_at_cell_placeholder(
            &header,
            &changed_section,
            &parent_binding(false)?,
            &template,
            &template_binding()?,
            &flow('a'),
            &request,
            &plan,
            TableNestedTableHwpxLimits::default(),
        ),
        TableNestedTableHwpxLowerer::lower_at_cell_placeholder(
            &header,
            &section,
            &parent_binding(false)?,
            &changed_template,
            &template_binding()?,
            &flow('a'),
            &request,
            &plan,
            TableNestedTableHwpxLimits::default(),
        ),
        TableNestedTableHwpxLowerer::lower_at_cell_placeholder(
            &header,
            &section,
            &parent_binding(false)?,
            &template,
            &template_binding()?,
            &flow('f'),
            &request,
            &plan,
            TableNestedTableHwpxLimits::default(),
        ),
        TableNestedTableHwpxLowerer::lower_at_cell_placeholder(
            &header,
            &section,
            &parent_binding(false)?,
            &template,
            &template_binding()?,
            &flow('a'),
            &request,
            &foreign_plan,
            TableNestedTableHwpxLimits::default(),
        ),
    ] {
        assert!(result.is_err());
    }
    Ok(())
}

#[test]
fn native_table_and_formula_identity_collisions_fail_before_mutation() -> TestResult {
    let header = header()?;
    let base = parent_section();
    let template = template_section(true, 800, 101, 202);
    let colliding_table = String::from_utf8(base.clone())?.replacen("id=\"700\"", "id=\"800\"", 1);
    assert!(
        TableNestedTableHwpxReader::read_context(
            &header,
            colliding_table.as_bytes(),
            0,
            CellCoordinate { row: 0, column: 0 },
            1,
            &parent_binding(false)?,
            &template,
            0,
            &template_binding()?,
            TableNestedTableHwpxLimits::default(),
        )
        .is_err()
    );

    let field = formula_paragraph(101, 202);
    let colliding_formula =
        String::from_utf8(base)?.replacen(&text_paragraph(1, "DOCUMENT-BEFORE"), &field, 1);
    assert!(matches!(
        TableNestedTableHwpxReader::read_context(
            &header,
            colliding_formula.as_bytes(),
            0,
            CellCoordinate { row: 0, column: 0 },
            1,
            &parent_binding(false)?,
            &template,
            0,
            &template_binding()?,
            TableNestedTableHwpxLimits::default(),
        ),
        Err(TableNestedTableHwpxError::NativeIdentityCollision)
    ));
    Ok(())
}

#[test]
fn input_is_bounded_and_debug_redacts_ids_hashes_and_formula_content() -> TestResult {
    let header = header()?;
    let section = parent_section();
    let template = template_section(true, 800, 101, 202);
    let source = context(&header, &section, &template)?;
    let valid = draft(&source, 'a', 'b')?;
    let (request, plan) = admitted(&source, valid, 'a')?;
    let debug = format!("{source:?} {request:?} {plan:?}");
    for secret in [
        "parent-nested-table-payload",
        "parent-table",
        "nested-a",
        "=SUM(LEFT)",
        &hex(source.header_sha256),
        &source.insertion_context_sha256,
        request.target_document_flow_sha256(),
    ] {
        assert!(!debug.contains(secret));
    }

    let limits = TableNestedTableHwpxLimits {
        ruling: hwpx_package::TableRulingHwpxLimits {
            grid: TableGridLimits::new(TableGridLimitConfig {
                serialized_bytes: 1024,
                ..TableGridLimitConfig::default()
            })?,
            ..hwpx_package::TableRulingHwpxLimits::default()
        },
        ..TableNestedTableHwpxLimits::default()
    };
    assert!(matches!(
        TableNestedTableHwpxRequest::from_json(&vec![b' '; 1025], &source, &flow('a'), limits),
        Err(TableNestedTableHwpxError::InputLimit)
    ));
    Ok(())
}

fn archive(
    parts: Vec<(String, Vec<u8>, CompressionMethod)>,
) -> Result<Vec<u8>, zip::result::ZipError> {
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    for (path, bytes, method) in parts {
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

fn package(header: &[u8], section: &[u8], opaque: &[u8]) -> TestResult<Vec<u8>> {
    Ok(archive(vec![
        (
            "mimetype".to_owned(),
            b"application/hwp+zip".to_vec(),
            CompressionMethod::Stored,
        ),
        (
            "version.xml".to_owned(),
            b"<version/>".to_vec(),
            CompressionMethod::Stored,
        ),
        (
            "META-INF/container.xml".to_owned(),
            CONTAINER.as_bytes().to_vec(),
            CompressionMethod::Deflated,
        ),
        (
            "Contents/content.hpf".to_owned(),
            OPF.as_bytes().to_vec(),
            CompressionMethod::Deflated,
        ),
        (
            "Contents/header.xml".to_owned(),
            header.to_vec(),
            CompressionMethod::Deflated,
        ),
        (
            "Contents/section0.xml".to_owned(),
            section.to_vec(),
            CompressionMethod::Deflated,
        ),
        (
            "Contents/opaque.bin".to_owned(),
            opaque.to_vec(),
            CompressionMethod::Stored,
        ),
    ])?)
}

fn replace_section(source: &[u8], section: &[u8]) -> TestResult<Vec<u8>> {
    let mut reader = BoundedZipReader::open(Cursor::new(source), PackageLimits::default())?;
    let entries = reader.entries().to_vec();
    let mut parts = Vec::new();
    for entry in entries {
        let path = entry.path.as_str().to_owned();
        let compression = match entry.compression {
            Compression::Stored => CompressionMethod::Stored,
            Compression::Deflated => CompressionMethod::Deflated,
        };
        let bytes = if path == "Contents/section0.xml" {
            section.to_vec()
        } else {
            reader.read_entry(entry.index)?
        };
        parts.push((path, bytes, compression));
    }
    Ok(archive(parts)?)
}

fn expanded_parts(source: &[u8]) -> TestResult<BTreeMap<String, Vec<u8>>> {
    let mut reader = BoundedZipReader::open(Cursor::new(source), PackageLimits::default())?;
    let entries = reader.entries().to_vec();
    let mut parts = BTreeMap::new();
    for entry in entries {
        if parts
            .insert(
                entry.path.as_str().to_owned(),
                reader.read_entry(entry.index)?,
            )
            .is_some()
        {
            return Err("duplicate package path".into());
        }
    }
    Ok(parts)
}

#[test]
fn closed_package_reopen_preserves_all_nontarget_parts_and_nested_state() -> TestResult {
    let header = header()?;
    let section = parent_section();
    let template = template_section(true, 800, 101, 202);
    let source = context(&header, &section, &template)?;
    let (request, plan) = admitted(&source, draft(&source, 'a', 'b')?, 'a')?;
    let output = TableNestedTableHwpxLowerer::lower_at_cell_placeholder(
        &header,
        &section,
        &parent_binding(false)?,
        &template,
        &template_binding()?,
        &flow('a'),
        &request,
        &plan,
        TableNestedTableHwpxLimits::default(),
    )?;
    let opaque = b"PRIVATE OPAQUE BYTES\0\xff";
    let original_package = package(&header, &section, opaque)?;
    let output_package = replace_section(&original_package, &output.section)?;
    let original_parts = expanded_parts(&original_package)?;
    let output_parts = expanded_parts(&output_package)?;
    assert_eq!(output_parts.len(), original_parts.len());
    for (path, bytes) in &original_parts {
        if path != "Contents/section0.xml" {
            assert_eq!(output_parts.get(path), Some(bytes), "part drift: {path}");
        }
    }
    let mut reader =
        BoundedZipReader::open(Cursor::new(&output_package), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    assert!(!graph.parts.is_empty());
    let packaged_header = output_parts
        .get("Contents/header.xml")
        .ok_or("packaged header missing")?;
    let packaged_section = output_parts
        .get("Contents/section0.xml")
        .ok_or("packaged section missing")?;
    let parent = TableRulingHwpxReader::read_existing(
        packaged_header,
        packaged_section,
        output.parent_table_ordinal,
        &output.parent_binding,
        TableNestedTableHwpxLimits::default().ruling,
    )?;
    let nested = TableRulingHwpxReader::read_existing(
        packaged_header,
        packaged_section,
        output.nested_table_ordinal,
        &output.nested_binding,
        TableNestedTableHwpxLimits::default().ruling,
    )?;
    assert_eq!(parent.state, *plan.target_parent_state());
    assert_eq!(nested.state, *plan.target_nested_state());
    assert_eq!(nested.formula_count, 1);
    Ok(())
}
