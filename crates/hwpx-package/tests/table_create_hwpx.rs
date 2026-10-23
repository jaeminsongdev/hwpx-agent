use std::collections::BTreeMap;
use std::io::{Cursor, Write};

use domain_ir::{LogicalId, TableGridLimitConfig, TableGridLimits, TableRulingAxis};
use hwpx_package::{
    BoundedZipReader, Compression, PackageGraph, PackageGraphLimits, PackageLimits,
    TABLE_CREATE_HWPX_SCHEMA_VERSION, TableCreateHwpxBuilder, TableCreateHwpxError,
    TableCreateHwpxLimits, TableCreateHwpxLowerer, TableCreateHwpxReader, TableCreateHwpxRequest,
    TableCreateHwpxRequestDraft, TableRulingHwpxBinding, TableRulingHwpxCellBinding,
    TableRulingHwpxReader,
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
    let bytes = value.as_ref();
    let mut output = String::with_capacity(bytes.len().saturating_mul(2));
    for byte in bytes {
        output.push(char::from(DIGITS[usize::from(byte >> 4)]));
        output.push(char::from(DIGITS[usize::from(byte & 0x0f)]));
    }
    output
}

fn border_fill(id: u32, left: &str, right: &str, top: &str, bottom: &str) -> String {
    format!(
        concat!(
            r#"<hh:borderFill id="{id}" threeD="0" shadow="0" centerLine="NONE" breakCellSeparateLine="0">"#,
            r#"<hh:slash type="NONE" Crooked="0" isCounter="0"/>"#,
            r#"<hh:backSlash type="NONE" Crooked="0" isCounter="0"/>"#,
            r##"<hh:leftBorder type="{left}" width="0.1 mm" color="#000000"/>"##,
            r##"<hh:rightBorder type="{right}" width="0.1 mm" color="#000000"/>"##,
            r##"<hh:topBorder type="{top}" width="0.1 mm" color="#000000"/>"##,
            r##"<hh:bottomBorder type="{bottom}" width="0.1 mm" color="#000000"/>"##,
            r##"<hh:diagonal type="SOLID" width="0.1 mm" color="#000000"/>"##,
            r#"</hh:borderFill>"#
        ),
        id = id,
        left = left,
        right = right,
        top = top,
        bottom = bottom,
    )
}

pub(crate) fn header() -> TestResult<Vec<u8>> {
    let source = String::from_utf8(HEADER.to_vec())?;
    let additions = [
        border_fill(3, "SOLID", "DOT", "SOLID", "DOT"),
        border_fill(4, "DOT", "SOLID", "SOLID", "DOT"),
        border_fill(5, "SOLID", "DOT", "DOT", "SOLID"),
        border_fill(6, "DOT", "SOLID", "DOT", "SOLID"),
    ]
    .concat();
    Ok(source
        .replacen(
            "<hh:borderFills itemCnt=\"2\">",
            "<hh:borderFills itemCnt=\"6\">",
            1,
        )
        .replacen(
            "</hh:borderFills>",
            &format!("{additions}</hh:borderFills>"),
            1,
        )
        .into_bytes())
}

pub(crate) fn empty_paragraph(identifier: u32) -> String {
    format!(
        r#"<hp:p id="{identifier}" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t/></hp:run></hp:p>"#
    )
}

fn text_paragraph(identifier: u32, text: &str) -> String {
    format!(
        r#"<hp:p id="{identifier}" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t>{text}</hp:t></hp:run></hp:p>"#
    )
}

fn cell(row: u32, column: u32, width: u32, height: u32, border_fill: u32) -> String {
    format!(
        concat!(
            r#"<hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="0" borderFillIDRef="{border_fill}">"#,
            r#"<hp:cellAddr colAddr="{column}" rowAddr="{row}"/>"#,
            r#"<hp:cellSpan colSpan="1" rowSpan="1"/>"#,
            r#"<hp:cellSz width="{width}" height="{height}"/>"#,
            r#"<hp:cellMargin left="0" right="0" top="0" bottom="0"/>"#,
            r#"<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">"#,
            r#"<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t/></hp:run></hp:p>"#,
            r#"</hp:subList></hp:tc>"#
        ),
        border_fill = border_fill,
        column = column,
        row = row,
        width = width,
        height = height,
    )
}

fn template_wrapper(native_id: u32, nonempty: bool) -> String {
    let payload = if nonempty {
        r#"<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t>X</hp:t></hp:run></hp:p>"#
    } else {
        r#"<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t/></hp:run></hp:p>"#
    };
    let first = if nonempty {
        format!(
            concat!(
                r#"<hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="0" borderFillIDRef="3">"#,
                r#"<hp:cellAddr colAddr="0" rowAddr="0"/><hp:cellSpan colSpan="1" rowSpan="1"/>"#,
                r#"<hp:cellSz width="800" height="500"/><hp:cellMargin left="0" right="0" top="0" bottom="0"/>"#,
                r#"<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">{payload}</hp:subList></hp:tc>"#
            ),
            payload = payload,
        )
    } else {
        cell(0, 0, 800, 500, 3)
    };
    format!(
        concat!(
            r#"<hp:p id="900" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0">"#,
            r#"<hp:tbl id="{native_id}" zOrder="0" numberingType="TABLE" textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" pageBreak="CELL" repeatHeader="0" rowCnt="2" colCnt="2" cellSpacing="0" borderFillIDRef="1" noAdjust="0">"#,
            r#"<hp:sz width="2000" widthRelTo="ABSOLUTE" height="1100" heightRelTo="ABSOLUTE" protect="0"/>"#,
            r#"<hp:pos treatAsChar="0" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP" horzAlign="LEFT" vertOffset="2000" horzOffset="1000"/>"#,
            r#"<hp:outMargin left="0" right="0" top="0" bottom="0"/><hp:inMargin left="0" right="0" top="0" bottom="0"/>"#,
            "<hp:tr>{first}{top_right}</hp:tr><hp:tr>{bottom_left}{bottom_right}</hp:tr>",
            r#"</hp:tbl><hp:t/></hp:run></hp:p>"#
        ),
        native_id = native_id,
        first = first,
        top_right = cell(0, 1, 1200, 500, 4),
        bottom_left = cell(1, 0, 800, 600, 5),
        bottom_right = cell(1, 1, 1200, 600, 6),
    )
}

pub(crate) fn template_section(nonempty: bool) -> Vec<u8> {
    format!(
        r#"<hs:sec xmlns:hs="{SECTION_NS}" xmlns:hp="{PARAGRAPH_NS}">{}</hs:sec>"#,
        template_wrapper(700, nonempty)
    )
    .into_bytes()
}

fn destination_section() -> Vec<u8> {
    format!(
        r#"<hs:sec xmlns:hs="{SECTION_NS}" xmlns:hp="{PARAGRAPH_NS}">{}{}{}</hs:sec>"#,
        text_paragraph(10, "BEFORE"),
        empty_paragraph(11),
        text_paragraph(12, "AFTER"),
    )
    .into_bytes()
}

fn destination_with_collision() -> Vec<u8> {
    format!(
        r#"<hs:sec xmlns:hs="{SECTION_NS}" xmlns:hp="{PARAGRAPH_NS}">{}{}</hs:sec>"#,
        template_wrapper(700, false),
        empty_paragraph(11),
    )
    .into_bytes()
}

fn template_binding() -> TestResult<TableRulingHwpxBinding> {
    Ok(TableRulingHwpxBinding {
        table_id: id("template-table")?,
        row_boundaries_hwpunit: vec![0, 500, 1100],
        column_boundaries_hwpunit: vec![0, 800, 2000],
        cells: ["template-a", "template-b", "template-c", "template-d"]
            .into_iter()
            .map(|value| {
                Ok(TableRulingHwpxCellBinding {
                    master_cell_id: id(value)?,
                    payload_block_ids: Vec::new(),
                })
            })
            .collect::<TestResult<Vec<_>>>()?,
    })
}

fn read_context(
    header: &[u8],
    section: &[u8],
    template: &[u8],
    placeholder: usize,
) -> TestResult<hwpx_package::TableCreateHwpxReadback> {
    Ok(TableCreateHwpxReader::read_context(
        header,
        section,
        placeholder,
        template,
        0,
        &template_binding()?,
        TableCreateHwpxLimits::default(),
    )?)
}

fn draft(
    source: &hwpx_package::TableCreateHwpxReadback,
    rows: u32,
    columns: u32,
    before_flow: char,
    after_flow: char,
) -> TestResult<TableCreateHwpxRequestDraft> {
    let count = usize::try_from(rows)? * usize::try_from(columns)?;
    Ok(TableCreateHwpxRequestDraft {
        schema_version: TABLE_CREATE_HWPX_SCHEMA_VERSION.to_owned(),
        placeholder_paragraph_ordinal: source.placeholder_paragraph_ordinal,
        template_table_ordinal: source.template_table_ordinal,
        expected_header_sha256: hex(source.header_sha256),
        expected_section_sha256: hex(source.section_sha256),
        expected_template_section_sha256: hex(source.template_section_sha256),
        expected_template_state_sha256: hex(source
            .template
            .state
            .canonical_sha256(TableCreateHwpxLimits::default().ruling.ruling)?),
        expected_template_grid_sha256: hex(source.template.grid.canonical_sha256()?),
        expected_insertion_context_sha256: source.insertion_context_sha256.clone(),
        expected_document_flow_sha256: flow(before_flow),
        target_document_flow_sha256: flow(after_flow),
        table_id: id("created-table")?,
        rows,
        columns,
        master_cell_ids: (0..count)
            .map(|index| id(&format!("created-cell-{index}")))
            .collect::<TestResult<Vec<_>>>()?,
        row_heights_hwpunit: (0..rows).map(|index| 400 + index * 100).collect(),
        column_widths_hwpunit: (0..columns).map(|index| 600 + index * 200).collect(),
    })
}

fn admitted(
    source: &hwpx_package::TableCreateHwpxReadback,
    draft: TableCreateHwpxRequestDraft,
    current_flow: char,
) -> TestResult<(TableCreateHwpxRequest, hwpx_package::TableCreateHwpxPlan)> {
    let request = TableCreateHwpxRequest::from_draft(
        draft,
        source,
        &flow(current_flow),
        TableCreateHwpxLimits::default(),
    )?;
    let plan = TableCreateHwpxBuilder::build(
        &request,
        source,
        &flow(current_flow),
        TableCreateHwpxLimits::default(),
    )?;
    Ok((request, plan))
}

fn assert_profile_drift_fails(
    source: &hwpx_package::TableCreateHwpxReadback,
    valid: &TableCreateHwpxRequestDraft,
) {
    let mut foreign_source = source.clone();
    foreign_source.profile_id = "foreign-create-profile";
    assert!(matches!(
        TableCreateHwpxRequest::from_draft(
            valid.clone(),
            &foreign_source,
            &flow('a'),
            TableCreateHwpxLimits::default(),
        ),
        Err(TableCreateHwpxError::SourceBindingMismatch)
    ));
    let mut foreign_template = source.clone();
    foreign_template.template.profile_id = "foreign-ruling-profile";
    assert!(matches!(
        TableCreateHwpxRequest::from_draft(
            valid.clone(),
            &foreign_template,
            &flow('a'),
            TableCreateHwpxLimits::default(),
        ),
        Err(TableCreateHwpxError::SourceBindingMismatch)
    ));
}

#[test]
fn creates_arbitrary_rectangular_nonuniform_unmerged_table_and_reopens_exactly() -> TestResult {
    let header = header()?;
    let section = destination_section();
    let template = template_section(false);
    let source = read_context(&header, &section, &template, 1)?;
    let immutable_source = source.clone();
    let (request, plan) = admitted(&source, draft(&source, 3, 4, 'a', 'b')?, 'a')?;
    let lowered = TableCreateHwpxLowerer::lower_at_placeholder(
        &header,
        &section,
        &template,
        &template_binding()?,
        &flow('a'),
        &request,
        &plan,
        TableCreateHwpxLimits::default(),
    )?;
    let reopened = TableRulingHwpxReader::read_existing(
        &lowered.header,
        &lowered.section,
        lowered.table_ordinal,
        &lowered.binding,
        TableCreateHwpxLimits::default().ruling,
    )?;

    assert_eq!(source, immutable_source);
    assert_eq!(reopened.grid, *plan.target_grid());
    assert_eq!(reopened.state, *plan.target_state());
    assert_eq!(reopened.grid.rows(), 3);
    assert_eq!(reopened.grid.columns(), 4);
    assert_eq!(reopened.grid.master_cell_count(), 12);
    assert_eq!(
        reopened.state.row_boundaries_hwpunit(),
        &[0, 400, 900, 1500]
    );
    assert_eq!(
        reopened.state.column_boundaries_hwpunit(),
        &[0, 600, 1400, 2400, 3600]
    );
    assert_eq!(reopened.state.frame().width_hwpunit, 3600);
    assert_eq!(reopened.state.frame().height_hwpunit, 1500);
    assert_eq!(reopened.payload_block_count, 0);
    assert_eq!(reopened.formula_count, 0);
    assert_eq!(lowered.receipt.source_table_count, 0);
    assert_eq!(lowered.receipt.target_table_count, 1);
    assert_eq!(lowered.receipt.created_master_cell_count, 12);
    assert!(lowered.receipt.page_split_preserved);
    let xml = String::from_utf8(lowered.section)?;
    assert!(xml.contains("BEFORE"));
    assert!(xml.contains("AFTER"));
    assert!(!xml.contains("<hp:ctrl><hp:tbl"));
    assert_eq!(
        xml.matches(
            r#"<hp:p id="0" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0"><hp:run charPrIDRef="0"><hp:t/></hp:run></hp:p>"#
        )
        .count(),
        12
    );
    Ok(())
}

#[test]
fn rejects_control_wrapped_table_template_as_non_native_profile() -> TestResult {
    let header = header()?;
    let section = destination_section();
    let template = String::from_utf8(template_section(false))?
        .replace(
            "<hp:run charPrIDRef=\"0\"><hp:tbl",
            "<hp:run charPrIDRef=\"0\"><hp:ctrl><hp:tbl",
        )
        .replace(
            "</hp:tbl><hp:t/></hp:run>",
            "</hp:tbl></hp:ctrl><hp:t/></hp:run>",
        )
        .into_bytes();
    assert!(matches!(
        TableCreateHwpxReader::read_context(
            &header,
            &section,
            1,
            &template,
            0,
            &template_binding()?,
            TableCreateHwpxLimits::default(),
        ),
        Err(TableCreateHwpxError::UnsupportedTemplateProfile)
    ));
    Ok(())
}

#[test]
fn one_by_one_boundary_uses_only_template_outer_edges() -> TestResult {
    let header = header()?;
    let section = destination_section();
    let template = template_section(false);
    let source = read_context(&header, &section, &template, 1)?;
    let (request, plan) = admitted(&source, draft(&source, 1, 1, 'a', 'b')?, 'a')?;
    assert_eq!(plan.target_grid().master_cell_count(), 1);
    assert_eq!(plan.target_state().edges().len(), 4);
    for (axis, boundary) in [
        (TableRulingAxis::Horizontal, 0),
        (TableRulingAxis::Horizontal, 1),
        (TableRulingAxis::Vertical, 0),
        (TableRulingAxis::Vertical, 1),
    ] {
        assert!(plan.target_state().edge(axis, boundary, 0).is_some());
    }
    let lowered = TableCreateHwpxLowerer::lower_at_placeholder(
        &header,
        &section,
        &template,
        &template_binding()?,
        &flow('a'),
        &request,
        &plan,
        TableCreateHwpxLimits::default(),
    )?;
    assert_eq!(lowered.receipt.target_rows, 1);
    assert_eq!(lowered.receipt.target_columns, 1);
    Ok(())
}

#[test]
fn request_rejects_part_template_context_flow_identity_track_and_json_tampering() -> TestResult {
    let header = header()?;
    let section = destination_section();
    let template = template_section(false);
    let source = read_context(&header, &section, &template, 1)?;
    let valid = draft(&source, 2, 3, 'a', 'b')?;

    for field in [
        "header",
        "section",
        "template",
        "template_state",
        "template_grid",
        "context",
        "flow",
    ] {
        let mut tampered = valid.clone();
        match field {
            "header" => tampered.expected_header_sha256 = flow('1'),
            "section" => tampered.expected_section_sha256 = flow('2'),
            "template" => tampered.expected_template_section_sha256 = flow('3'),
            "template_state" => tampered.expected_template_state_sha256 = flow('6'),
            "template_grid" => tampered.expected_template_grid_sha256 = flow('7'),
            "context" => tampered.expected_insertion_context_sha256 = flow('4'),
            "flow" => tampered.expected_document_flow_sha256 = flow('5'),
            _ => unreachable!(),
        }
        assert!(matches!(
            TableCreateHwpxRequest::from_draft(
                tampered,
                &source,
                &flow('a'),
                TableCreateHwpxLimits::default(),
            ),
            Err(TableCreateHwpxError::SourceBindingMismatch)
        ));
    }

    assert_profile_drift_fails(&source, &valid);

    let mut same_flow = valid.clone();
    same_flow.target_document_flow_sha256 = flow('a');
    assert!(matches!(
        TableCreateHwpxRequest::from_draft(
            same_flow,
            &source,
            &flow('a'),
            TableCreateHwpxLimits::default(),
        ),
        Err(TableCreateHwpxError::FlowBindingMismatch)
    ));
    let mut identity = valid.clone();
    identity.master_cell_ids[0] = identity.table_id.clone();
    assert!(matches!(
        TableCreateHwpxRequest::from_draft(
            identity,
            &source,
            &flow('a'),
            TableCreateHwpxLimits::default(),
        ),
        Err(TableCreateHwpxError::IdentityConflict)
    ));
    let mut tracks = valid.clone();
    tracks.row_heights_hwpunit[0] = 0;
    assert!(matches!(
        TableCreateHwpxRequest::from_draft(
            tracks,
            &source,
            &flow('a'),
            TableCreateHwpxLimits::default(),
        ),
        Err(TableCreateHwpxError::InvalidTracks)
    ));

    let json = serde_json::to_string(&valid)?;
    for invalid in [
        json.replacen(
            '{',
            r#"{"schema_version":"hwpx-agent.table-create-hwpx/v1","#,
            1,
        ),
        json.replacen('{', r#"{"unknown":true,"#, 1),
    ] {
        assert!(matches!(
            TableCreateHwpxRequest::from_json(
                invalid.as_bytes(),
                &source,
                &flow('a'),
                TableCreateHwpxLimits::default(),
            ),
            Err(TableCreateHwpxError::InvalidJson)
        ));
    }
    Ok(())
}

#[test]
fn lowerer_rechecks_source_template_current_flow_and_foreign_plan() -> TestResult {
    let header = header()?;
    let section = destination_section();
    let template = template_section(false);
    let source = read_context(&header, &section, &template, 1)?;
    let (request, plan) = admitted(&source, draft(&source, 2, 3, 'a', 'b')?, 'a')?;
    let (_, foreign_plan) = admitted(&source, draft(&source, 2, 2, 'a', 'c')?, 'a')?;

    let mut changed_section = section.clone();
    let index = changed_section
        .windows("BEFORE".len())
        .position(|window| window == b"BEFORE")
        .ok_or("sentinel missing")?;
    changed_section[index] = b'X';
    for result in [
        TableCreateHwpxLowerer::lower_at_placeholder(
            &header,
            &changed_section,
            &template,
            &template_binding()?,
            &flow('a'),
            &request,
            &plan,
            TableCreateHwpxLimits::default(),
        ),
        TableCreateHwpxLowerer::lower_at_placeholder(
            &header,
            &section,
            &template,
            &template_binding()?,
            &flow('c'),
            &request,
            &plan,
            TableCreateHwpxLimits::default(),
        ),
        TableCreateHwpxLowerer::lower_at_placeholder(
            &header,
            &section,
            &template,
            &template_binding()?,
            &flow('a'),
            &request,
            &foreign_plan,
            TableCreateHwpxLimits::default(),
        ),
    ] {
        assert!(result.is_err());
    }
    Ok(())
}

#[test]
fn nonblank_template_and_native_identifier_collision_fail_closed() -> TestResult {
    let header = header()?;
    let section = destination_section();
    assert!(read_context(&header, &section, &template_section(true), 1).is_err());

    let collision = destination_with_collision();
    let template = template_section(false);
    let source = read_context(&header, &collision, &template, 1)?;
    let (request, plan) = admitted(&source, draft(&source, 2, 2, 'a', 'b')?, 'a')?;
    assert!(matches!(
        TableCreateHwpxLowerer::lower_at_placeholder(
            &header,
            &collision,
            &template,
            &template_binding()?,
            &flow('a'),
            &request,
            &plan,
            TableCreateHwpxLimits::default(),
        ),
        Err(TableCreateHwpxError::Ruling(_))
    ));
    Ok(())
}

#[test]
fn input_is_bounded_and_debug_omits_ids_hashes_and_content() -> TestResult {
    let header = header()?;
    let section = destination_section();
    let template = template_section(false);
    let source = read_context(&header, &section, &template, 1)?;
    let valid = draft(&source, 2, 2, 'a', 'b')?;
    let request = TableCreateHwpxRequest::from_draft(
        valid,
        &source,
        &flow('a'),
        TableCreateHwpxLimits::default(),
    )?;
    let plan = TableCreateHwpxBuilder::build(
        &request,
        &source,
        &flow('a'),
        TableCreateHwpxLimits::default(),
    )?;
    let debug = format!("{request:?} {plan:?} {source:?}");
    for secret in [
        "created-table",
        "created-cell-0",
        request.target_document_flow_sha256(),
        &hex(source.header_sha256),
        &source.insertion_context_sha256,
    ] {
        assert!(!debug.contains(secret));
    }

    let limits = TableCreateHwpxLimits {
        ruling: hwpx_package::TableRulingHwpxLimits {
            grid: TableGridLimits::new(TableGridLimitConfig {
                serialized_bytes: 1024,
                ..TableGridLimitConfig::default()
            })?,
            ..hwpx_package::TableRulingHwpxLimits::default()
        },
        ..TableCreateHwpxLimits::default()
    };
    assert!(matches!(
        TableCreateHwpxRequest::from_json(&vec![b' '; 1025], &source, &flow('a'), limits),
        Err(TableCreateHwpxError::InputLimit)
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

pub(crate) fn package(header: &[u8], section: &[u8], opaque: &[u8]) -> TestResult<Vec<u8>> {
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

fn replace_target_parts(source: &[u8], header: &[u8], section: &[u8]) -> TestResult<Vec<u8>> {
    let mut reader = BoundedZipReader::open(Cursor::new(source), PackageLimits::default())?;
    let entries = reader.entries().to_vec();
    let mut parts = Vec::new();
    for entry in entries {
        let path = entry.path.as_str().to_owned();
        let compression = match entry.compression {
            Compression::Stored => CompressionMethod::Stored,
            Compression::Deflated => CompressionMethod::Deflated,
        };
        let bytes = match path.as_str() {
            "Contents/header.xml" => header.to_vec(),
            "Contents/section0.xml" => section.to_vec(),
            _ => reader.read_entry(entry.index)?,
        };
        parts.push((path, bytes, compression));
    }
    Ok(archive(parts)?)
}

fn expanded_package_parts(source: &[u8]) -> TestResult<BTreeMap<String, Vec<u8>>> {
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
fn closed_package_replacement_preserves_every_nontarget_part_and_graph() -> TestResult {
    let header = header()?;
    let section = destination_section();
    let template = template_section(false);
    let source = read_context(&header, &section, &template, 1)?;
    let (request, plan) = admitted(&source, draft(&source, 2, 3, 'a', 'b')?, 'a')?;
    let lowered = TableCreateHwpxLowerer::lower_at_placeholder(
        &header,
        &section,
        &template,
        &template_binding()?,
        &flow('a'),
        &request,
        &plan,
        TableCreateHwpxLimits::default(),
    )?;
    let opaque = b"PRIVATE OPAQUE BYTES\0\xff";
    let original_package = package(&header, &section, opaque)?;
    let output_package =
        replace_target_parts(&original_package, &lowered.header, &lowered.section)?;
    let original_parts = expanded_package_parts(&original_package)?;
    let output_parts = expanded_package_parts(&output_package)?;
    assert_eq!(output_parts.len(), original_parts.len());
    for (path, bytes) in &original_parts {
        if path != "Contents/header.xml" && path != "Contents/section0.xml" {
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
    let reopened = TableRulingHwpxReader::read_existing(
        packaged_header,
        packaged_section,
        lowered.table_ordinal,
        &lowered.binding,
        TableCreateHwpxLimits::default().ruling,
    )?;
    assert_eq!(reopened.grid, *plan.target_grid());
    assert_eq!(reopened.state, *plan.target_state());
    Ok(())
}
