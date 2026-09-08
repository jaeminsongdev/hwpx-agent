use std::collections::BTreeMap;
use std::io::{Cursor, Write};

use domain_ir::{
    FormulaLimitConfig, FormulaLimits, LengthMicrometers, LogicalId,
    TABLE_PLACEMENT_SCHEMA_VERSION, TableAttachmentMode, TableFloatingPlacement,
    TableHorizontalAlignment, TableHorizontalReference, TableOuterMargins,
    TablePlacementLimitConfig, TablePlacementLimits, TablePlacementOperation, TablePlacementState,
    TablePlacementStateDraft, TableTextFlow, TableTextWrap, TableVerticalAlignment,
    TableVerticalReference,
};
use hwpx_package::{
    BoundedZipReader, Compression, PackageGraph, PackageGraphLimits, PackageLimits,
    TABLE_PLACEMENT_HWPX_PROFILE_ID, TableFormulaHwpxLimits, TableFormulaHwpxReader,
    TableLayoutHwpxLimitConfig, TableLayoutHwpxLimits, TablePaginationHwpxLimits,
    TablePaginationHwpxReader, TablePlacementHwpxError, TablePlacementHwpxLowerer,
    TablePlacementHwpxReader,
};
use sha2::{Digest as _, Sha256};
use zip::write::SimpleFileOptions;
use zip::{CompressionMethod, DateTime, ZipWriter};

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
  </opf:manifest>
  <opf:spine><opf:itemref idref="section0" linear="yes"/></opf:spine>
</opf:package>"#;

type TestResult<T = ()> = Result<T, Box<dyn std::error::Error>>;

fn um(value: i64) -> LengthMicrometers {
    LengthMicrometers::from_raw(value)
}

fn zero_margins() -> TableOuterMargins {
    TableOuterMargins {
        left: um(0),
        right: um(0),
        top: um(0),
        bottom: um(0),
    }
}

fn base_floating() -> TableFloatingPlacement {
    TableFloatingPlacement {
        horizontal_reference: TableHorizontalReference::Column,
        vertical_reference: TableVerticalReference::Paragraph,
        horizontal_alignment: TableHorizontalAlignment::Left,
        vertical_alignment: TableVerticalAlignment::Top,
        horizontal_offset: um(0),
        vertical_offset: um(0),
        flow_with_text: true,
        allow_overlap: false,
        hold_anchor_and_shape: false,
    }
}

fn state(
    identifier: &str,
    attachment: TableAttachmentMode,
    text_wrap: TableTextWrap,
    text_flow: TableTextFlow,
    margins: TableOuterMargins,
) -> TestResult<TablePlacementState> {
    Ok(TablePlacementState::from_draft(
        TablePlacementStateDraft {
            schema_version: TABLE_PLACEMENT_SCHEMA_VERSION.to_owned(),
            table_id: LogicalId::parse(identifier)?,
            attachment,
            text_wrap,
            text_flow,
            outer_margins: margins,
        },
        TablePlacementLimits::default(),
    )?)
}

fn floating_state(identifier: &str) -> TestResult<TablePlacementState> {
    state(
        identifier,
        TableAttachmentMode::Floating {
            placement: base_floating(),
        },
        TableTextWrap::TopAndBottom,
        TableTextFlow::BothSides,
        zero_margins(),
    )
}

fn cell(row: u32, column: u32, column_span: u32, marker: &str) -> String {
    format!(
        concat!(
            r#"<hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="0" borderFillIDRef="1">"#,
            r#"<hp:cellAddr colAddr="{column}" rowAddr="{row}"/>"#,
            r#"<hp:cellSpan colSpan="{column_span}" rowSpan="1"/>"#,
            r#"<hp:cellSz width="1000" height="500"/>"#,
            r#"<hp:cellMargin left="0" right="0" top="0" bottom="0"/>"#,
            r#"<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">"#,
            r#"<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t>{marker}</hp:t></hp:run></hp:p>"#,
            r#"</hp:subList></hp:tc>"#,
        ),
        row = row,
        column = column,
        column_span = column_span,
        marker = marker,
    )
}

fn formula_cell(row: u32, column: u32) -> String {
    format!(
        concat!(
            r#"<hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="0" borderFillIDRef="1">"#,
            r#"<hp:cellAddr colAddr="{column}" rowAddr="{row}"/>"#,
            r#"<hp:cellSpan colSpan="1" rowSpan="1"/>"#,
            r#"<hp:cellSz width="1000" height="500"/>"#,
            r#"<hp:cellMargin left="0" right="0" top="0" bottom="0"/>"#,
            r#"<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">"#,
            r#"<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:ctrl>"#,
            r#"<hp:fieldBegin id="101" type="FORMULA" name="" editable="0" dirty="0" zorder="-1" fieldid="202">"#,
            r#"<hp:parameters cnt="5" name=""><hp:integerParam name="Prop">8</hp:integerParam>"#,
            r#"<hp:stringParam name="Command">=SUM(LEFT)??%g,;;7</hp:stringParam>"#,
            r#"<hp:stringParam name="Formula">=SUM(LEFT)</hp:stringParam>"#,
            r#"<hp:stringParam name="ResultFormat">%g,</hp:stringParam>"#,
            r#"<hp:stringParam name="LastResult">7</hp:stringParam></hp:parameters>"#,
            r#"</hp:fieldBegin></hp:ctrl><hp:t>7</hp:t><hp:ctrl>"#,
            r#"<hp:fieldEnd beginIDRef="101" fieldid="202"/></hp:ctrl><hp:t/></hp:run></hp:p>"#,
            r#"</hp:subList></hp:tc>"#,
        ),
        row = row,
        column = column,
    )
}

fn table(identifier: u32, rows: &[Vec<String>], treat_as_char: bool) -> String {
    let mut body = String::new();
    for cells in rows {
        body.push_str("<hp:tr>");
        body.push_str(&cells.concat());
        body.push_str("</hp:tr>");
    }
    format!(
        concat!(
            r#"<hp:tbl xmlns:hp="{PARAGRAPH_NS}" id="{identifier}" zOrder="0" numberingType="TABLE" textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" pageBreak="CELL" repeatHeader="0" rowCnt="{row_count}" colCnt="2" cellSpacing="0" borderFillIDRef="1" noAdjust="0">"#,
            r#"<hp:sz width="2000" widthRelTo="ABSOLUTE" height="1000" heightRelTo="ABSOLUTE" protect="0"/>"#,
            r#"<hp:pos treatAsChar="{treat_as_char}" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP" horzAlign="LEFT" vertOffset="0" horzOffset="0"/>"#,
            r#"<hp:outMargin left="0" right="0" top="0" bottom="0"/>"#,
            r#"<hp:inMargin left="510" right="511" top="141" bottom="142"/>"#,
            "{body}</hp:tbl>"
        ),
        PARAGRAPH_NS = PARAGRAPH_NS,
        identifier = identifier,
        row_count = rows.len(),
        treat_as_char = u8::from(treat_as_char),
        body = body,
    )
}

fn ordinary_table(identifier: u32, marker: &str, treat_as_char: bool) -> String {
    table(
        identifier,
        &[
            vec![cell(0, 0, 1, marker), cell(0, 1, 1, "B")],
            vec![cell(1, 0, 1, "C"), cell(1, 1, 1, "D")],
        ],
        treat_as_char,
    )
}

fn merged_table(identifier: u32, marker: &str) -> String {
    table(
        identifier,
        &[
            vec![cell(0, 0, 2, marker)],
            vec![cell(1, 0, 1, "LEFT"), cell(1, 1, 1, "RIGHT")],
        ],
        false,
    )
}

fn formula_table(identifier: u32) -> String {
    table(
        identifier,
        &[
            vec![cell(0, 0, 1, "1"), cell(0, 1, 1, "2")],
            vec![cell(1, 0, 1, "7"), formula_cell(1, 1)],
        ],
        false,
    )
}

fn section(tables: &[String]) -> Vec<u8> {
    format!(
        r#"<hs:sec xmlns:hs="{SECTION_NS}" xmlns:hp="{PARAGRAPH_NS}">{}</hs:sec>"#,
        tables.concat()
    )
    .into_bytes()
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

fn package(section: &[u8]) -> Result<Vec<u8>, zip::result::ZipError> {
    archive(vec![
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
            b"<header/>".to_vec(),
            CompressionMethod::Deflated,
        ),
        (
            "Contents/section0.xml".to_owned(),
            section.to_vec(),
            CompressionMethod::Deflated,
        ),
    ])
}

fn replace_section(source: &[u8], section: &[u8]) -> TestResult<Vec<u8>> {
    let mut reader = BoundedZipReader::open(Cursor::new(source), PackageLimits::default())?;
    let entries = reader.entries().to_vec();
    let mut parts = Vec::new();
    parts.try_reserve_exact(entries.len())?;
    let mut replacements = 0_usize;
    for entry in entries {
        let path = entry.path.as_str().to_owned();
        let method = match entry.compression {
            Compression::Stored => CompressionMethod::Stored,
            Compression::Deflated => CompressionMethod::Deflated,
        };
        let bytes = if path == "Contents/section0.xml" {
            replacements += 1;
            section.to_vec()
        } else {
            reader.read_entry(entry.index)?
        };
        parts.push((path, bytes, method));
    }
    if replacements != 1 {
        return Err("section replacement cardinality mismatch".into());
    }
    Ok(archive(parts)?)
}

fn inspect_package(source: &[u8]) -> TestResult<(PackageGraph, Vec<u8>)> {
    let mut reader = BoundedZipReader::open(Cursor::new(source), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    let section_index = reader
        .entries()
        .iter()
        .find(|entry| entry.path.as_str() == "Contents/section0.xml")
        .map(|entry| entry.index)
        .ok_or("section part missing")?;
    let section = reader.read_entry(section_index)?;
    Ok((graph, section))
}

fn part_hashes(graph: &PackageGraph) -> BTreeMap<String, [u8; 32]> {
    graph
        .parts
        .iter()
        .map(|part| (part.path.as_str().to_owned(), part.raw_sha256))
        .collect()
}

fn formula_limits() -> TestResult<FormulaLimits> {
    Ok(FormulaLimits::new(FormulaLimitConfig {
        rows: 10,
        columns: 10,
        ..FormulaLimitConfig::default()
    })?)
}

fn apply(
    source: &TablePlacementState,
    operation: TablePlacementOperation,
) -> TestResult<TablePlacementState> {
    Ok(source
        .apply(operation, TablePlacementLimits::default())?
        .state()
        .clone())
}

fn lower(
    source: &[u8],
    from: &TablePlacementState,
    to: &TablePlacementState,
) -> TestResult<Vec<u8>> {
    Ok(TablePlacementHwpxLowerer::lower(
        source,
        from,
        to,
        TablePlacementLimits::default(),
        TableLayoutHwpxLimits::default(),
    )?)
}

#[test]
fn reader_maps_complete_current_profile_and_rejects_malformed_native_values() -> TestResult {
    let source = ordinary_table(10, "READER_SECRET", false)
        .replace(
            "textWrap=\"TOP_AND_BOTTOM\"",
            "textWrap=\"IN_FRONT_OF_TEXT\"",
        )
        .replace("textFlow=\"BOTH_SIDES\"", "textFlow=\"LEFT_ONLY\"")
        .replace("flowWithText=\"1\"", "flowWithText=\"0\"")
        .replace("allowOverlap=\"0\"", "allowOverlap=\"1\"")
        .replace("holdAnchorAndSO=\"0\"", "holdAnchorAndSO=\"1\"")
        .replace("vertRelTo=\"PARA\"", "vertRelTo=\"PAGE\"")
        .replace("horzRelTo=\"COLUMN\"", "horzRelTo=\"PAPER\"")
        .replace("vertAlign=\"TOP\"", "vertAlign=\"INSIDE\"")
        .replace("horzAlign=\"LEFT\"", "horzAlign=\"OUTSIDE\"")
        .replace("vertOffset=\"0\"", "vertOffset=\"360\"")
        .replace("horzOffset=\"0\"", "horzOffset=\"-720\"")
        .replace(
            "<hp:outMargin left=\"0\" right=\"0\" top=\"0\" bottom=\"0\"/>",
            "<hp:outMargin left=\"360\" right=\"720\" top=\"1080\" bottom=\"1440\"/>",
        )
        .into_bytes();
    let readback = TablePlacementHwpxReader::read(&source, TableLayoutHwpxLimits::default())?;
    assert_eq!(
        readback.horizontal_reference,
        TableHorizontalReference::Paper
    );
    assert_eq!(readback.vertical_reference, TableVerticalReference::Page);
    assert_eq!(
        readback.horizontal_alignment,
        TableHorizontalAlignment::Outside
    );
    assert_eq!(readback.vertical_alignment, TableVerticalAlignment::Inside);
    assert_eq!(readback.horizontal_offset_hwpunit, -720);
    assert_eq!(readback.vertical_offset_hwpunit, 360);
    assert!(!readback.floating_flags.flow_with_text);
    assert!(readback.floating_flags.allow_overlap);
    assert!(readback.floating_flags.hold_anchor_and_shape);
    assert_eq!(readback.text_wrap, TableTextWrap::InFrontOfText);
    assert_eq!(readback.text_flow, TableTextFlow::LeftOnly);
    assert_eq!(readback.outer_margins.left_hwpunit, 360);
    assert_eq!(readback.outer_margins.right_hwpunit, 720);
    assert_eq!(readback.outer_margins.top_hwpunit, 1080);
    assert_eq!(readback.outer_margins.bottom_hwpunit, 1440);

    for (malformed, code) in [
        (
            String::from_utf8(source.clone())?
                .replace("horzRelTo=\"PAPER\"", "horzRelTo=\"FRAME\""),
            "table_placement_hwpx_invalid_enum",
        ),
        (
            String::from_utf8(source.clone())?.replace("treatAsChar=\"0\"", "treatAsChar=\"2\""),
            "table_placement_hwpx_invalid_boolean",
        ),
        (
            String::from_utf8(source.clone())?.replace("horzOffset=\"-720\"", "horzOffset=\"-0\""),
            "table_placement_hwpx_invalid_number",
        ),
        (
            String::from_utf8(source.clone())?.replace("left=\"360\"", "left=\"0360\""),
            "table_placement_hwpx_invalid_number",
        ),
        (
            String::from_utf8(source.clone())?.replace("right=\"720\"", "right=\"100000001\""),
            "table_placement_hwpx_out_of_range",
        ),
    ] {
        let Err(error) =
            TablePlacementHwpxReader::read(malformed.as_bytes(), TableLayoutHwpxLimits::default())
        else {
            return Err("malformed native value was accepted".into());
        };
        assert_eq!(error.code(), code);
    }
    Ok(())
}

#[test]
fn position_operation_covers_every_reference_alignment_and_flag_variant() -> TestResult {
    let source = ordinary_table(20, "POSITION", false).into_bytes();
    let source_state = floating_state("position-table")?;
    let horizontal_references = [
        TableHorizontalReference::Paper,
        TableHorizontalReference::Page,
        TableHorizontalReference::Column,
        TableHorizontalReference::Paragraph,
    ];
    let vertical_references = [
        TableVerticalReference::Paper,
        TableVerticalReference::Page,
        TableVerticalReference::Paragraph,
    ];
    let horizontal_alignments = [
        TableHorizontalAlignment::Left,
        TableHorizontalAlignment::Center,
        TableHorizontalAlignment::Right,
        TableHorizontalAlignment::Inside,
        TableHorizontalAlignment::Outside,
    ];
    let vertical_alignments = [
        TableVerticalAlignment::Top,
        TableVerticalAlignment::Center,
        TableVerticalAlignment::Bottom,
        TableVerticalAlignment::Inside,
        TableVerticalAlignment::Outside,
    ];

    for index in 0..20 {
        let placement = TableFloatingPlacement {
            horizontal_reference: horizontal_references[index % horizontal_references.len()],
            vertical_reference: vertical_references[index % vertical_references.len()],
            horizontal_alignment: horizontal_alignments[index % horizontal_alignments.len()],
            vertical_alignment: vertical_alignments[(index * 2) % vertical_alignments.len()],
            horizontal_offset: um(-2_540 + i64::try_from(index)? * 127),
            vertical_offset: um(2_540 - i64::try_from(index)? * 127),
            flow_with_text: index & 1 == 0,
            allow_overlap: index & 2 == 0,
            hold_anchor_and_shape: index & 4 == 0,
        };
        let target = apply(
            &source_state,
            TablePlacementOperation::SetPosition { placement },
        )?;
        let output = lower(&source, &source_state, &target)?;
        let readback = TablePlacementHwpxReader::read(&output, TableLayoutHwpxLimits::default())?;
        assert_eq!(
            readback.horizontal_reference,
            placement.horizontal_reference
        );
        assert_eq!(readback.vertical_reference, placement.vertical_reference);
        assert_eq!(
            readback.horizontal_alignment,
            placement.horizontal_alignment
        );
        assert_eq!(readback.vertical_alignment, placement.vertical_alignment);
        assert_eq!(
            readback.horizontal_offset_hwpunit,
            -720 + i64::try_from(index)? * 36
        );
        assert_eq!(
            readback.vertical_offset_hwpunit,
            720 - i64::try_from(index)? * 36
        );
        assert_eq!(
            readback.floating_flags.flow_with_text,
            placement.flow_with_text
        );
        assert_eq!(
            readback.floating_flags.allow_overlap,
            placement.allow_overlap
        );
        assert_eq!(
            readback.floating_flags.hold_anchor_and_shape,
            placement.hold_anchor_and_shape
        );
    }
    Ok(())
}

#[test]
fn inline_floating_transitions_preserve_inactive_native_fields() -> TestResult {
    let source = ordinary_table(30, "ATTACHMENT", false)
        .replace("affectLSpacing=\"0\"", "affectLSpacing=\"1\"")
        .replace("vertRelTo=\"PARA\"", "vertRelTo=\"PAGE\"")
        .replace("horzRelTo=\"COLUMN\"", "horzRelTo=\"PAPER\"")
        .replace("vertAlign=\"TOP\"", "vertAlign=\"OUTSIDE\"")
        .replace("horzAlign=\"LEFT\"", "horzAlign=\"INSIDE\"")
        .replace("vertOffset=\"0\"", "vertOffset=\"360\"")
        .replace("horzOffset=\"0\"", "horzOffset=\"-720\"")
        .into_bytes();
    let placement = TableFloatingPlacement {
        horizontal_reference: TableHorizontalReference::Paper,
        vertical_reference: TableVerticalReference::Page,
        horizontal_alignment: TableHorizontalAlignment::Inside,
        vertical_alignment: TableVerticalAlignment::Outside,
        horizontal_offset: um(-2_540),
        vertical_offset: um(1_270),
        ..base_floating()
    };
    let source_state = state(
        "attachment-table",
        TableAttachmentMode::Floating { placement },
        TableTextWrap::TopAndBottom,
        TableTextFlow::BothSides,
        zero_margins(),
    )?;
    let inline = apply(
        &source_state,
        TablePlacementOperation::SetInline {
            affect_line_spacing: false,
        },
    )?;
    let inline_bytes = lower(&source, &source_state, &inline)?;
    let inline_readback =
        TablePlacementHwpxReader::read(&inline_bytes, TableLayoutHwpxLimits::default())?;
    assert!(inline_readback.attachment_flags.treat_as_char);
    assert!(!inline_readback.attachment_flags.affect_line_spacing);
    assert_eq!(
        inline_readback.horizontal_reference,
        placement.horizontal_reference
    );
    assert_eq!(
        inline_readback.vertical_reference,
        placement.vertical_reference
    );
    assert_eq!(
        inline_readback.horizontal_alignment,
        placement.horizontal_alignment
    );
    assert_eq!(
        inline_readback.vertical_alignment,
        placement.vertical_alignment
    );
    assert_eq!(inline_readback.horizontal_offset_hwpunit, -720);
    assert_eq!(inline_readback.vertical_offset_hwpunit, 360);

    let replacement = TableFloatingPlacement {
        horizontal_reference: TableHorizontalReference::Paragraph,
        vertical_reference: TableVerticalReference::Paragraph,
        horizontal_alignment: TableHorizontalAlignment::Right,
        vertical_alignment: TableVerticalAlignment::Bottom,
        horizontal_offset: um(3_810),
        vertical_offset: um(-1_270),
        flow_with_text: false,
        allow_overlap: true,
        hold_anchor_and_shape: true,
    };
    let floating = apply(
        &inline,
        TablePlacementOperation::SetFloating {
            placement: replacement,
        },
    )?;
    let floating_bytes = lower(&inline_bytes, &inline, &floating)?;
    let floating_readback =
        TablePlacementHwpxReader::read(&floating_bytes, TableLayoutHwpxLimits::default())?;
    assert!(!floating_readback.attachment_flags.treat_as_char);
    assert!(!floating_readback.attachment_flags.affect_line_spacing);
    assert_eq!(floating_readback.horizontal_offset_hwpunit, 1080);
    assert_eq!(floating_readback.vertical_offset_hwpunit, -360);
    assert!(!floating_readback.floating_flags.flow_with_text);
    assert!(floating_readback.floating_flags.allow_overlap);
    assert!(floating_readback.floating_flags.hold_anchor_and_shape);
    Ok(())
}

#[test]
fn wrap_and_outer_margin_operations_cover_all_native_values() -> TestResult {
    let source = ordinary_table(40, "WRAP-MARGIN", false).into_bytes();
    let source_state = floating_state("wrap-margin-table")?;
    let wraps = [
        TableTextWrap::Square,
        TableTextWrap::TopAndBottom,
        TableTextWrap::BehindText,
        TableTextWrap::InFrontOfText,
    ];
    let flows = [
        TableTextFlow::BothSides,
        TableTextFlow::LeftOnly,
        TableTextFlow::RightOnly,
        TableTextFlow::LargestOnly,
    ];
    for text_wrap in wraps {
        for text_flow in flows {
            let target = apply(
                &source_state,
                TablePlacementOperation::SetWrap {
                    text_wrap,
                    text_flow,
                },
            )?;
            let output = lower(&source, &source_state, &target)?;
            let readback =
                TablePlacementHwpxReader::read(&output, TableLayoutHwpxLimits::default())?;
            assert_eq!(readback.text_wrap, text_wrap);
            assert_eq!(readback.text_flow, text_flow);
        }
    }

    let margins = TableOuterMargins {
        left: um(1_270),
        right: um(2_540),
        top: um(3_810),
        bottom: um(5_080),
    };
    let target = apply(
        &source_state,
        TablePlacementOperation::SetOuterMargins { margins },
    )?;
    let output = lower(&source, &source_state, &target)?;
    let readback = TablePlacementHwpxReader::read(&output, TableLayoutHwpxLimits::default())?;
    assert_eq!(readback.outer_margins.left_hwpunit, 360);
    assert_eq!(readback.outer_margins.right_hwpunit, 720);
    assert_eq!(readback.outer_margins.top_hwpunit, 1080);
    assert_eq!(readback.outer_margins.bottom_hwpunit, 1440);
    Ok(())
}

#[test]
fn state_identity_source_drift_and_finite_limits_fail_closed() -> TestResult {
    let source = ordinary_table(50, "FAIL-CLOSED", false).into_bytes();
    let source_copy = source.clone();
    let source_state = floating_state("fail-closed-table")?;
    let target = apply(
        &source_state,
        TablePlacementOperation::SetOuterMargins {
            margins: TableOuterMargins {
                left: um(1_270),
                ..zero_margins()
            },
        },
    )?;
    let wrong_identity = state(
        "different-table",
        target.attachment(),
        target.text_wrap(),
        target.text_flow(),
        target.outer_margins(),
    )?;
    assert_eq!(
        TablePlacementHwpxLowerer::lower(
            &source,
            &source_state,
            &wrong_identity,
            TablePlacementLimits::default(),
            TableLayoutHwpxLimits::default(),
        ),
        Err(TablePlacementHwpxError::StateIdentityMismatch)
    );

    let drifted_source = state(
        "fail-closed-table",
        source_state.attachment(),
        source_state.text_wrap(),
        source_state.text_flow(),
        TableOuterMargins {
            right: um(1_270),
            ..zero_margins()
        },
    )?;
    assert_eq!(
        TablePlacementHwpxLowerer::lower(
            &source,
            &drifted_source,
            &target,
            TablePlacementLimits::default(),
            TableLayoutHwpxLimits::default(),
        ),
        Err(TablePlacementHwpxError::SourceStateMismatch)
    );

    let tight_state_limits = TablePlacementLimits::new(TablePlacementLimitConfig {
        input_bytes: 1,
        serialized_bytes: 1,
        ..TablePlacementLimitConfig::default()
    })?;
    assert!(matches!(
        TablePlacementHwpxLowerer::lower(
            &source,
            &source_state,
            &target,
            tight_state_limits,
            TableLayoutHwpxLimits::default(),
        ),
        Err(TablePlacementHwpxError::State(_))
    ));

    let tight_hwpx_limits = TableLayoutHwpxLimits::new(TableLayoutHwpxLimitConfig {
        output_bytes: source.len(),
        ..TableLayoutHwpxLimitConfig::default()
    })?;
    assert_eq!(
        TablePlacementHwpxLowerer::lower(
            &source,
            &source_state,
            &target,
            TablePlacementLimits::default(),
            tight_hwpx_limits,
        ),
        Err(TablePlacementHwpxError::OutputLimit)
    );
    assert_eq!(source, source_copy);
    Ok(())
}

#[test]
fn section_selection_is_exact_deterministic_idempotent_and_redacted() -> TestResult {
    let first = merged_table(60, "MERGED-SIBLING-SECRET");
    let second = ordinary_table(61, "SELECTED-SECRET", false);
    let source = section(&[first.clone(), second]);
    let source_state = floating_state("selected-table")?;
    let target = apply(
        &source_state,
        TablePlacementOperation::SetOuterMargins {
            margins: TableOuterMargins {
                left: um(1_270),
                right: um(2_540),
                top: um(3_810),
                bottom: um(5_080),
            },
        },
    )?;
    let (output, receipt) = TablePlacementHwpxLowerer::lower_in_section_with_receipt(
        &source,
        1,
        &source_state,
        &target,
        TablePlacementLimits::default(),
        TableLayoutHwpxLimits::default(),
    )?;
    let repeated = TablePlacementHwpxLowerer::lower_in_section(
        &source,
        1,
        &source_state,
        &target,
        TablePlacementLimits::default(),
        TableLayoutHwpxLimits::default(),
    )?;
    assert_eq!(output, repeated);
    assert!(String::from_utf8(output.clone())?.contains(&first));
    assert_eq!(receipt.profile_id, TABLE_PLACEMENT_HWPX_PROFILE_ID);
    assert_eq!(
        receipt.source_sha256,
        <[u8; 32]>::from(Sha256::digest(&source))
    );
    assert_eq!(
        receipt.output_sha256,
        <[u8; 32]>::from(Sha256::digest(&output))
    );
    assert_eq!(
        receipt.content_sha256,
        TablePlacementHwpxReader::read_in_section(&source, 1, TableLayoutHwpxLimits::default())?
            .content_sha256
    );

    let (idempotent, idempotent_receipt) =
        TablePlacementHwpxLowerer::lower_in_section_with_receipt(
            &output,
            1,
            &target,
            &target,
            TablePlacementLimits::default(),
            TableLayoutHwpxLimits::default(),
        )?;
    assert_eq!(output, idempotent);
    assert_eq!(idempotent_receipt.modified_attribute_count, 0);

    let debug = format!("{receipt:?}");
    for secret in [
        "source_sha256",
        "output_sha256",
        "source_state_sha256",
        "target_state_sha256",
        "content_sha256",
        "MERGED-SIBLING-SECRET",
        "SELECTED-SECRET",
    ] {
        assert!(!debug.contains(secret));
    }
    Ok(())
}

struct PackageOracle<'a> {
    package: &'a [u8],
    graph: &'a PackageGraph,
    section: &'a [u8],
    hashes: &'a BTreeMap<String, [u8; 32]>,
    state: &'a TablePlacementState,
}

impl PackageOracle<'_> {
    fn assert_operation(&self, operation: TablePlacementOperation) -> TestResult {
        let source_formula = TableFormulaHwpxReader::read_in_section(
            self.section,
            1,
            TableFormulaHwpxLimits::default(),
            formula_limits()?,
        )?;
        let source_pagination = TablePaginationHwpxReader::read_in_section(
            self.section,
            1,
            TablePaginationHwpxLimits::default(),
        )?;
        let target_state = apply(self.state, operation)?;
        let target_section = TablePlacementHwpxLowerer::lower_in_section(
            self.section,
            1,
            self.state,
            &target_state,
            TablePlacementLimits::default(),
            TableLayoutHwpxLimits::default(),
        )?;
        let target_package = replace_section(self.package, &target_section)?;
        assert_eq!(
            target_package,
            replace_section(self.package, &target_section)?
        );

        let (target_graph, reopened_target_section) = inspect_package(&target_package)?;
        assert_eq!(self.graph.package_document, target_graph.package_document);
        assert_eq!(self.graph.relationships, target_graph.relationships);
        assert_eq!(self.graph.spine, target_graph.spine);
        let target_hashes = part_hashes(&target_graph);
        for (path, source_sha256) in self.hashes {
            let target_sha256 = target_hashes.get(path).ok_or("target part missing")?;
            if path == "Contents/section0.xml" {
                assert_ne!(source_sha256, target_sha256);
            } else {
                assert_eq!(source_sha256, target_sha256, "part changed: {path}");
            }
        }
        assert!(String::from_utf8(reopened_target_section.clone())?.contains("MERGED-PRESERVE"));

        let target_formula = TableFormulaHwpxReader::read_in_section(
            &reopened_target_section,
            1,
            TableFormulaHwpxLimits::default(),
            formula_limits()?,
        )?;
        assert_eq!(source_formula.rows, target_formula.rows);
        assert_eq!(source_formula.columns, target_formula.columns);
        assert_eq!(source_formula.formula, target_formula.formula);
        assert_eq!(
            source_formula.formula_field_count,
            target_formula.formula_field_count
        );

        let target_pagination = TablePaginationHwpxReader::read_in_section(
            &reopened_target_section,
            1,
            TablePaginationHwpxLimits::default(),
        )?;
        assert_eq!(source_pagination.page_split, target_pagination.page_split);
        assert_eq!(
            source_pagination.repeat_header_rows,
            target_pagination.repeat_header_rows
        );
        assert_eq!(source_pagination.row_count, target_pagination.row_count);
        assert_eq!(
            source_pagination.column_count,
            target_pagination.column_count
        );
        assert_eq!(source_pagination.caption, target_pagination.caption);
        Ok(())
    }
}

#[test]
fn closed_package_reopen_preserves_grid_formula_cache_pagination_and_other_parts() -> TestResult {
    let source_section = section(&[merged_table(70, "MERGED-PRESERVE"), formula_table(71)]);
    let source_package = package(&source_section)?;
    let source_copy = source_package.clone();
    let (source_graph, reopened_source_section) = inspect_package(&source_package)?;
    let source_hashes = part_hashes(&source_graph);
    let source_state = floating_state("package-table")?;
    let positioned = TableFloatingPlacement {
        horizontal_reference: TableHorizontalReference::Page,
        vertical_reference: TableVerticalReference::Paper,
        horizontal_alignment: TableHorizontalAlignment::Center,
        vertical_alignment: TableVerticalAlignment::Bottom,
        horizontal_offset: um(-2_540),
        vertical_offset: um(3_810),
        flow_with_text: false,
        allow_overlap: true,
        hold_anchor_and_shape: true,
    };
    let operations = [
        TablePlacementOperation::SetPosition {
            placement: positioned,
        },
        TablePlacementOperation::SetInline {
            affect_line_spacing: true,
        },
        TablePlacementOperation::SetFloating {
            placement: positioned,
        },
        TablePlacementOperation::SetWrap {
            text_wrap: TableTextWrap::BehindText,
            text_flow: TableTextFlow::RightOnly,
        },
        TablePlacementOperation::SetOuterMargins {
            margins: TableOuterMargins {
                left: um(1_270),
                right: um(2_540),
                top: um(3_810),
                bottom: um(5_080),
            },
        },
    ];
    let oracle = PackageOracle {
        package: &source_package,
        graph: &source_graph,
        section: &reopened_source_section,
        hashes: &source_hashes,
        state: &source_state,
    };
    for operation in operations {
        oracle.assert_operation(operation)?;
        assert_eq!(source_package, source_copy);
    }
    Ok(())
}
