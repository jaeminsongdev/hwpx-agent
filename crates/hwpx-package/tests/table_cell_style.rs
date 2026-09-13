use domain_ir::{FormulaLimitConfig, FormulaLimits};
use hwpx_package::{
    CellMargins, CellProtection, CellTextDirection, CellVerticalAlignment, HorizontalAlignment,
    ParagraphStyleCatalog, ParagraphStyleCatalogReader, ParagraphStyleLimits, TableCellStyle,
    TableCellStyleError, TableCellStyleLimitConfig, TableCellStyleLimits, TableCellStyleLowerer,
    TableCellStyleProfile, TableCellStyleReader, TableFormulaHwpxLimits, TableFormulaHwpxReader,
    TablePaginationHwpxLimits, TablePaginationHwpxReader,
};
use sha2::{Digest as _, Sha256};

const HEADER: &[u8] = include_bytes!("../src/hancom_2020_minimal_header.xml");
const NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";

type TestResult = Result<(), Box<dyn std::error::Error>>;

fn sample_catalog(
    alignment: HorizontalAlignment,
) -> Result<ParagraphStyleCatalog, TableCellStyleError> {
    let mut catalog = ParagraphStyleCatalogReader::read(HEADER, ParagraphStyleLimits::default())
        .map_err(|_| TableCellStyleError::ReferenceMismatch)?;
    catalog.styles[0].horizontal_alignment = alignment;
    Ok(catalog)
}

fn fragment() -> Vec<u8> {
    format!(
        concat!(
            r#"<?xml version="1.0" encoding="UTF-8"?>"#,
            r#"<hp:tc xmlns:hp="{}" name="A1" header="0" hasMargin="1" protect="0" editable="0" dirty="0" borderFillIDRef="1">"#,
            r#"<hp:cellAddr colAddr="0" rowAddr="0"/>"#,
            r#"<hp:cellSpan colSpan="1" rowSpan="1"/>"#,
            r#"<hp:cellSz width="10000" height="5000"/>"#,
            r#"<hp:cellMargin left="141" right="141" top="141" bottom="141"/>"#,
            r#"<hp:subList id="cell-a1" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="TOP" linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">"#,
            r#"<hp:p id="11" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t>A &amp; B</hp:t></hp:run></hp:p>"#,
            r#"<hp:p id="12" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t>둘째 줄</hp:t></hp:run></hp:p>"#,
            r#"</hp:subList></hp:tc>"#,
        ),
        NS
    )
    .into_bytes()
}

fn hangul_2020_fragment() -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    let source = String::from_utf8(fragment())?;
    let start = source.find("<hp:cellAddr").ok_or("cell address missing")?;
    let split = source.find("<hp:subList").ok_or("sub-list missing")?;
    let end = source.rfind("</hp:tc>").ok_or("cell end missing")?;
    let prefix = &source[..start];
    let address_through_margin = &source[start..split];
    let sub_list = &source[split..end];
    Ok(format!("{prefix}{sub_list}{address_through_margin}</hp:tc>").into_bytes())
}

fn styled_cell(name: &str, column: u32, paragraph: &str) -> String {
    format!(
        concat!(
            "<hp:tc name=\"{name}\" header=\"0\" hasMargin=\"1\" protect=\"0\" ",
            "editable=\"0\" dirty=\"0\" borderFillIDRef=\"1\">",
            "<hp:subList id=\"cell-{column}\" textDirection=\"HORIZONTAL\" lineWrap=\"BREAK\" ",
            "vertAlign=\"TOP\" linkListIDRef=\"0\" linkListNextIDRef=\"0\" textWidth=\"0\" ",
            "textHeight=\"0\" hasTextRef=\"0\" hasNumRef=\"0\">{paragraph}</hp:subList>",
            "<hp:cellAddr colAddr=\"{column}\" rowAddr=\"0\"/>",
            "<hp:cellSpan colSpan=\"1\" rowSpan=\"1\"/>",
            "<hp:cellSz width=\"10000\" height=\"5000\"/>",
            "<hp:cellMargin left=\"141\" right=\"141\" top=\"141\" bottom=\"141\"/>",
            "</hp:tc>"
        ),
        name = name,
        column = column,
        paragraph = paragraph
    )
}

fn formula_style_section() -> Vec<u8> {
    let plain_a = r#"<hp:p id="11" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t>17</hp:t></hp:run></hp:p>"#;
    let plain_b = r#"<hp:p id="12" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t>25</hp:t></hp:run></hp:p>"#;
    let formula = concat!(
        "<hp:p id=\"13\" paraPrIDRef=\"0\" styleIDRef=\"0\"><hp:run charPrIDRef=\"0\">",
        "<hp:ctrl><hp:fieldBegin id=\"101\" type=\"FORMULA\" name=\"\" editable=\"0\" ",
        "dirty=\"0\" zorder=\"-1\" fieldid=\"202\"><hp:parameters cnt=\"5\" name=\"\">",
        "<hp:integerParam name=\"Prop\">8</hp:integerParam>",
        "<hp:stringParam name=\"Command\">=SUM(LEFT)??%g,;;42</hp:stringParam>",
        "<hp:stringParam name=\"Formula\">=SUM(LEFT)</hp:stringParam>",
        "<hp:stringParam name=\"ResultFormat\">%g,</hp:stringParam>",
        "<hp:stringParam name=\"LastResult\">42</hp:stringParam>",
        "</hp:parameters></hp:fieldBegin></hp:ctrl><hp:t>42</hp:t><hp:ctrl>",
        "<hp:fieldEnd beginIDRef=\"101\" fieldid=\"202\"/></hp:ctrl><hp:t/></hp:run></hp:p>"
    );
    format!(
        concat!(
            "<hs:sec xmlns:hs=\"http://www.hancom.co.kr/hwpml/2011/section\" ",
            "xmlns:hp=\"{ns}\"><hp:tbl id=\"100\" lock=\"0\" pageBreak=\"CELL\" ",
            "repeatHeader=\"0\" rowCnt=\"1\" colCnt=\"3\" cellSpacing=\"0\" noAdjust=\"0\">",
            "<hp:sz/><hp:pos/><hp:outMargin/><hp:inMargin/><hp:tr>{cells}</hp:tr></hp:tbl></hs:sec>"
        ),
        ns = NS,
        cells = [
            styled_cell("A1", 0, plain_a),
            styled_cell("B1", 1, plain_b),
            styled_cell("C1", 2, formula),
        ]
        .join("")
    )
    .into_bytes()
}

fn formula_limits() -> Result<FormulaLimits, Box<dyn std::error::Error>> {
    Ok(FormulaLimits::new(FormulaLimitConfig {
        rows: 8,
        columns: 8,
        ..FormulaLimitConfig::default()
    })?)
}

fn target(alignment: HorizontalAlignment) -> TableCellStyle {
    TableCellStyle {
        margins: Some(CellMargins {
            left: 210,
            right: 220,
            top: 230,
            bottom: 240,
        }),
        border_fill_id_ref: 2,
        paragraph_property_id_ref: 0,
        horizontal_alignment: alignment,
        vertical_alignment: CellVerticalAlignment::Center,
        text_direction: CellTextDirection::VerticalAll,
        protection: CellProtection::ProtectedEditable,
    }
}

fn section_with_cells(cells: &[Vec<u8>]) -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    let mut section = format!(
        r#"<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" xmlns:hp="{NS}">"#
    );
    for cell in cells {
        section.push_str(
            std::str::from_utf8(cell)?
                .strip_prefix("<?xml version=\"1.0\" encoding=\"UTF-8\"?>")
                .ok_or("cell XML declaration missing")?,
        );
    }
    section.push_str("</hs:sec>");
    Ok(section.into_bytes())
}

#[test]
fn lowers_every_style_dimension_and_preserves_content() -> TestResult {
    let catalog = sample_catalog(HorizontalAlignment::Center)?;
    let source = fragment();
    let source_readback = TableCellStyleReader::read(
        &source,
        &sample_catalog(HorizontalAlignment::Justify)?,
        TableCellStyleLimits::default(),
    )?;
    let (output, receipt) = TableCellStyleLowerer::lower_with_receipt(
        &source,
        &target(HorizontalAlignment::Center),
        &catalog,
        TableCellStyleLimits::default(),
    )?;
    let readback = TableCellStyleReader::read(&output, &catalog, TableCellStyleLimits::default())?;
    assert_eq!(readback.style, target(HorizontalAlignment::Center));
    assert_eq!(readback.paragraph_count, 2);
    assert_eq!(readback.content_sha256, source_readback.content_sha256);
    assert_eq!(receipt.content_sha256, source_readback.content_sha256);
    let text = std::str::from_utf8(&output)?;
    assert!(text.contains("A &amp; B"));
    assert!(text.contains("둘째 줄"));
    assert_eq!(text.matches("paraPrIDRef=\"0\"").count(), 2);
    Ok(())
}

#[test]
fn complete_cell_style_batch_preserves_formula_and_page_split() -> TestResult {
    let source = formula_style_section();
    let source_formula = TableFormulaHwpxReader::read_in_section(
        &source,
        0,
        TableFormulaHwpxLimits::default(),
        formula_limits()?,
    )?;
    let source_pagination = TablePaginationHwpxReader::read_in_section(
        &source,
        0,
        TablePaginationHwpxLimits::default(),
    )?;
    let catalog = sample_catalog(HorizontalAlignment::Center)?;
    let output = TableCellStyleLowerer::lower_in_section_with_profile(
        &source,
        2,
        TableCellStyleProfile::Hangul2020V2,
        &target(HorizontalAlignment::Center),
        &catalog,
        TableCellStyleLimits::default(),
    )?;
    let target_formula = TableFormulaHwpxReader::read_in_section(
        &output,
        0,
        TableFormulaHwpxLimits::default(),
        formula_limits()?,
    )?;
    let target_pagination = TablePaginationHwpxReader::read_in_section(
        &output,
        0,
        TablePaginationHwpxLimits::default(),
    )?;
    let style = TableCellStyleReader::read_in_section_with_profile(
        &output,
        2,
        TableCellStyleProfile::Hangul2020V2,
        &catalog,
        TableCellStyleLimits::default(),
    )?;

    assert_eq!(style.style, target(HorizontalAlignment::Center));
    assert_eq!(source_formula.formula, target_formula.formula);
    assert_eq!(
        source_formula.formula_field_count,
        target_formula.formula_field_count
    );
    assert_eq!(source_pagination.page_split, target_pagination.page_split);
    assert_eq!(
        source_pagination.repeat_header_rows,
        target_pagination.repeat_header_rows
    );
    assert_eq!(source_pagination.caption, target_pagination.caption);
    Ok(())
}

#[test]
fn exact_hangul_2020_v2_order_is_explicit_and_preserving() -> TestResult {
    let source = hangul_2020_fragment()?;
    let catalog = sample_catalog(HorizontalAlignment::Center)?;
    let Err(v1_error) =
        TableCellStyleReader::read(&source, &catalog, TableCellStyleLimits::default())
    else {
        return Err("v1 silently accepted the v2 child order".into());
    };
    assert_eq!(v1_error.code(), "table_cell_style_unsupported_shape");

    let source_readback = TableCellStyleReader::read_with_profile(
        &source,
        TableCellStyleProfile::Hangul2020V2,
        &sample_catalog(HorizontalAlignment::Justify)?,
        TableCellStyleLimits::default(),
    )?;
    let (output, receipt) = TableCellStyleLowerer::lower_with_profile_and_receipt(
        &source,
        TableCellStyleProfile::Hangul2020V2,
        &target(HorizontalAlignment::Center),
        &catalog,
        TableCellStyleLimits::default(),
    )?;
    let readback = TableCellStyleReader::read_with_profile(
        &output,
        TableCellStyleProfile::Hangul2020V2,
        &catalog,
        TableCellStyleLimits::default(),
    )?;
    assert_eq!(readback.style, target(HorizontalAlignment::Center));
    assert_eq!(readback.content_sha256, source_readback.content_sha256);
    assert_eq!(
        receipt.profile_id,
        "hwpx-agent.table-cell-style.hancom-2020/2"
    );
    assert!(
        std::str::from_utf8(&output)?
            .contains("<hp:subList id=\"cell-a1\" textDirection=\"VERTICALALL\"")
    );
    Ok(())
}

#[test]
fn hangul_2020_v2_preserves_inactive_default_margin_numbers() -> TestResult {
    let mut source = String::from_utf8(hangul_2020_fragment()?)?;
    source = source.replace("hasMargin=\"1\"", "hasMargin=\"0\"");
    source = source.replace(
        "left=\"141\" right=\"141\" top=\"141\" bottom=\"141\"",
        "left=\"510\" right=\"510\" top=\"141\" bottom=\"141\"",
    );
    let source = source.into_bytes();
    let catalog = sample_catalog(HorizontalAlignment::Center)?;

    let Err(v1_error) =
        TableCellStyleReader::read(&source, &catalog, TableCellStyleLimits::default())
    else {
        return Err("v1 silently accepted inactive nonzero margins".into());
    };
    assert_eq!(v1_error.code(), "table_cell_style_unsupported_shape");

    let readback = TableCellStyleReader::read_with_profile(
        &source,
        TableCellStyleProfile::Hangul2020V2,
        &catalog,
        TableCellStyleLimits::default(),
    )?;
    assert_eq!(readback.style.margins, None);

    let mut no_margin = target(HorizontalAlignment::Center);
    no_margin.margins = None;
    let output = TableCellStyleLowerer::lower_with_profile(
        &source,
        TableCellStyleProfile::Hangul2020V2,
        &no_margin,
        &catalog,
        TableCellStyleLimits::default(),
    )?;
    assert!(
        std::str::from_utf8(&output)?
            .contains("<hp:cellMargin left=\"510\" right=\"510\" top=\"141\" bottom=\"141\"/>")
    );
    Ok(())
}

#[test]
fn all_direction_alignment_and_protection_variants_round_trip() -> TestResult {
    let alignments = [
        HorizontalAlignment::Justify,
        HorizontalAlignment::Left,
        HorizontalAlignment::Right,
        HorizontalAlignment::Center,
        HorizontalAlignment::Distribute,
        HorizontalAlignment::DistributeSpace,
    ];
    let directions = [
        CellTextDirection::Horizontal,
        CellTextDirection::Vertical,
        CellTextDirection::VerticalAll,
    ];
    let verticals = [
        CellVerticalAlignment::Top,
        CellVerticalAlignment::Center,
        CellVerticalAlignment::Bottom,
    ];
    let protections = [
        CellProtection::Open,
        CellProtection::Editable,
        CellProtection::Protected,
        CellProtection::ProtectedEditable,
    ];
    for alignment in alignments {
        let catalog = sample_catalog(alignment)?;
        for direction in directions {
            for vertical in verticals {
                for protection in protections {
                    let mut style = target(alignment);
                    style.text_direction = direction;
                    style.vertical_alignment = vertical;
                    style.protection = protection;
                    let output = TableCellStyleLowerer::lower(
                        &fragment(),
                        &style,
                        &catalog,
                        TableCellStyleLimits::default(),
                    )?;
                    assert_eq!(
                        TableCellStyleReader::read(
                            &output,
                            &catalog,
                            TableCellStyleLimits::default()
                        )?
                        .style,
                        style
                    );
                }
            }
        }
    }
    Ok(())
}

#[test]
fn no_margin_is_canonicalized_without_touching_text() -> TestResult {
    let catalog = sample_catalog(HorizontalAlignment::Justify)?;
    let mut style = target(HorizontalAlignment::Justify);
    style.margins = None;
    let output = TableCellStyleLowerer::lower(
        &fragment(),
        &style,
        &catalog,
        TableCellStyleLimits::default(),
    )?;
    let text = std::str::from_utf8(&output)?;
    assert!(text.contains("hasMargin=\"0\""));
    assert!(text.contains("left=\"0\" right=\"0\" top=\"0\" bottom=\"0\""));
    assert_eq!(
        TableCellStyleReader::read(&output, &catalog, TableCellStyleLimits::default())?.style,
        style
    );
    Ok(())
}

#[test]
fn repeated_lowering_is_byte_deterministic() -> TestResult {
    let catalog = sample_catalog(HorizontalAlignment::Right)?;
    let style = target(HorizontalAlignment::Right);
    let first = TableCellStyleLowerer::lower(
        &fragment(),
        &style,
        &catalog,
        TableCellStyleLimits::default(),
    )?;
    let second =
        TableCellStyleLowerer::lower(&first, &style, &catalog, TableCellStyleLimits::default())?;
    assert_eq!(first, second);
    Ok(())
}

#[test]
fn selected_section_cell_changes_without_touching_its_sibling() -> TestResult {
    let first = String::from_utf8(fragment())?
        .replace("<?xml version=\"1.0\" encoding=\"UTF-8\"?>", "")
        .replace("A &amp; B", "첫 셀");
    let second = String::from_utf8(fragment())?
        .replace("<?xml version=\"1.0\" encoding=\"UTF-8\"?>", "")
        .replace("A &amp; B", "둘째 셀");
    let section = format!(
        r#"<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" xmlns:hp="{NS}">{first}{second}</hs:sec>"#
    );
    let catalog = sample_catalog(HorizontalAlignment::Center)?;
    let output = TableCellStyleLowerer::lower_in_section(
        section.as_bytes(),
        1,
        &target(HorizontalAlignment::Center),
        &catalog,
        TableCellStyleLimits::default(),
    )?;
    let readback = TableCellStyleReader::read_in_section(
        &output,
        1,
        &catalog,
        TableCellStyleLimits::default(),
    )?;
    assert_eq!(readback.style, target(HorizontalAlignment::Center));
    let output_text = std::str::from_utf8(&output)?;
    let first_end = output_text.find("</hp:tc>").ok_or("first cell missing")? + 8;
    let source_first_end = section
        .find("</hp:tc>")
        .ok_or("source first cell missing")?
        + 8;
    assert_eq!(
        &output_text[..first_end],
        &section[..source_first_end],
        "the unselected cell changed"
    );
    Ok(())
}

#[test]
fn exact_section_root_and_total_cell_limit_fail_closed() -> TestResult {
    let catalog = sample_catalog(HorizontalAlignment::Justify)?;
    let cells = [fragment(), fragment()];
    let section = section_with_cells(&cells)?;
    assert_eq!(
        TableCellStyleReader::count_in_section(&section, TableCellStyleLimits::default())?,
        2
    );

    let one_cell = TableCellStyleLimits::new(TableCellStyleLimitConfig {
        cells: 1,
        ..TableCellStyleLimitConfig::default()
    })?;
    let Err(error) = TableCellStyleReader::count_in_section(&section, one_cell) else {
        return Err("the total section cell limit was not enforced".into());
    };
    assert_eq!(error.code(), "table_cell_style_cell_limit");

    let Err(error) = TableCellStyleReader::read_in_section(
        &fragment(),
        0,
        &catalog,
        TableCellStyleLimits::default(),
    ) else {
        return Err("a standalone tc was accepted as a section".into());
    };
    assert_eq!(error.code(), "table_cell_style_wrong_root");

    let wrong_namespace = std::str::from_utf8(&section)?
        .replace("http://www.hancom.co.kr/hwpml/2011/section", "urn:wrong");
    let Err(error) = TableCellStyleReader::count_in_section(
        wrong_namespace.as_bytes(),
        TableCellStyleLimits::default(),
    ) else {
        return Err("a wrong section namespace was accepted".into());
    };
    assert_eq!(error.code(), "table_cell_style_wrong_root");
    Ok(())
}

#[test]
fn dangling_and_mismatched_references_fail_closed() -> TestResult {
    let catalog = sample_catalog(HorizontalAlignment::Left)?;
    let mut style = target(HorizontalAlignment::Left);
    style.border_fill_id_ref = 99;
    let Err(error) = TableCellStyleLowerer::lower(
        &fragment(),
        &style,
        &catalog,
        TableCellStyleLimits::default(),
    ) else {
        return Err("dangling border reference was accepted".into());
    };
    assert_eq!(error.code(), "table_cell_style_dangling_reference");

    let mut style = target(HorizontalAlignment::Right);
    style.horizontal_alignment = HorizontalAlignment::Center;
    let right_catalog = sample_catalog(HorizontalAlignment::Right)?;
    let Err(error) = TableCellStyleLowerer::lower(
        &fragment(),
        &style,
        &right_catalog,
        TableCellStyleLimits::default(),
    ) else {
        return Err("mismatched paragraph reference was accepted".into());
    };
    assert_eq!(error.code(), "table_cell_style_reference_mismatch");

    let oversized_border = String::from_utf8(fragment())?
        .replace("borderFillIDRef=\"1\"", "borderFillIDRef=\"65536\"");
    let Err(error) = TableCellStyleReader::read(
        oversized_border.as_bytes(),
        &catalog,
        TableCellStyleLimits::default(),
    ) else {
        return Err("an out-of-range source border reference was accepted".into());
    };
    assert_eq!(error.code(), "table_cell_style_out_of_range");
    Ok(())
}

#[test]
fn malformed_shapes_and_noncanonical_absent_margin_fail_closed() -> TestResult {
    let catalog = sample_catalog(HorizontalAlignment::Justify)?;
    for malformed in [
        String::from_utf8(fragment())?.replace("<hp:cellSz", "<hp:unknown"),
        String::from_utf8(fragment())?.replace("vertAlign=\"TOP\"", "vertAlign=\"MIDDLE\""),
        String::from_utf8(fragment())?.replace(
            "paraPrIDRef=\"0\" styleIDRef=\"0\"><hp:run",
            "paraPrIDRef=\"0\" paraPrIDRef=\"0\" styleIDRef=\"0\"><hp:run",
        ),
        String::from_utf8(fragment())?.replace("hasMargin=\"1\"", "hasMargin=\"0\""),
    ] {
        assert!(
            TableCellStyleReader::read(
                malformed.as_bytes(),
                &catalog,
                TableCellStyleLimits::default()
            )
            .is_err()
        );
    }
    Ok(())
}

#[test]
fn limits_and_range_overflow_fail_closed() -> TestResult {
    let Err(error) = TableCellStyleLimits::new(TableCellStyleLimitConfig {
        input_bytes: 0,
        ..TableCellStyleLimitConfig::default()
    }) else {
        return Err("zero input limit was accepted".into());
    };
    assert_eq!(error.code(), "table_cell_style_invalid_limit");
    let catalog = sample_catalog(HorizontalAlignment::Justify)?;
    let mut style = target(HorizontalAlignment::Justify);
    style.margins = Some(CellMargins {
        left: TableCellStyleLimitConfig::default().margin_hwpunit + 1,
        right: 0,
        top: 0,
        bottom: 0,
    });
    let Err(error) = TableCellStyleLowerer::lower(
        &fragment(),
        &style,
        &catalog,
        TableCellStyleLimits::default(),
    ) else {
        return Err("oversized margin was accepted".into());
    };
    assert_eq!(error.code(), "table_cell_style_out_of_range");

    let source = fragment();
    let tight_input = TableCellStyleLimits::new(TableCellStyleLimitConfig {
        input_bytes: source.len() - 1,
        ..TableCellStyleLimitConfig::default()
    })?;
    assert!(TableCellStyleReader::read(&source, &catalog, tight_input).is_err());
    let one_paragraph = TableCellStyleLimits::new(TableCellStyleLimitConfig {
        paragraphs: 1,
        ..TableCellStyleLimitConfig::default()
    })?;
    assert!(TableCellStyleReader::read(&source, &catalog, one_paragraph).is_err());
    let one_element = TableCellStyleLimits::new(TableCellStyleLimitConfig {
        elements: 1,
        ..TableCellStyleLimitConfig::default()
    })?;
    assert!(TableCellStyleReader::read(&source, &catalog, one_element).is_err());
    let tight_output = TableCellStyleLimits::new(TableCellStyleLimitConfig {
        output_bytes: source.len(),
        ..TableCellStyleLimitConfig::default()
    })?;
    let mut growing = target(HorizontalAlignment::Justify);
    growing.text_direction = CellTextDirection::VerticalAll;
    assert!(TableCellStyleLowerer::lower(&source, &growing, &catalog, tight_output).is_err());
    Ok(())
}

#[test]
fn duplicate_catalog_references_and_missing_section_cell_fail_closed() -> TestResult {
    let mut duplicate_border = sample_catalog(HorizontalAlignment::Justify)?;
    duplicate_border
        .border_fills
        .push(duplicate_border.border_fills[0].clone());
    let Err(error) = TableCellStyleReader::read(
        &fragment(),
        &duplicate_border,
        TableCellStyleLimits::default(),
    ) else {
        return Err("an invalid duplicate catalog was accepted".into());
    };
    assert_eq!(error.code(), "table_cell_style_catalog_invalid");

    let mut duplicate_paragraph = sample_catalog(HorizontalAlignment::Justify)?;
    duplicate_paragraph
        .styles
        .push(duplicate_paragraph.styles[0].clone());
    assert!(
        TableCellStyleReader::read(
            &fragment(),
            &duplicate_paragraph,
            TableCellStyleLimits::default()
        )
        .is_err()
    );
    assert!(
        TableCellStyleReader::read_in_section(
            &fragment(),
            1,
            &sample_catalog(HorizontalAlignment::Justify)?,
            TableCellStyleLimits::default()
        )
        .is_err()
    );
    Ok(())
}

#[test]
fn fixed_128_case_style_corpus_is_deterministic() -> TestResult {
    let alignments = [
        HorizontalAlignment::Justify,
        HorizontalAlignment::Left,
        HorizontalAlignment::Right,
        HorizontalAlignment::Center,
        HorizontalAlignment::Distribute,
        HorizontalAlignment::DistributeSpace,
    ];
    let directions = [
        CellTextDirection::Horizontal,
        CellTextDirection::Vertical,
        CellTextDirection::VerticalAll,
    ];
    let verticals = [
        CellVerticalAlignment::Top,
        CellVerticalAlignment::Center,
        CellVerticalAlignment::Bottom,
    ];
    let protections = [
        CellProtection::Open,
        CellProtection::Editable,
        CellProtection::Protected,
        CellProtection::ProtectedEditable,
    ];
    let mut digest = Sha256::new();
    for index in 0_u32..128 {
        let alignment = alignments[index as usize % alignments.len()];
        let catalog = sample_catalog(alignment)?;
        let style = TableCellStyle {
            margins: (index % 11 != 0).then_some(CellMargins {
                left: index * 3,
                right: index * 5,
                top: index * 7,
                bottom: index * 11,
            }),
            border_fill_id_ref: 1 + (index % 2),
            paragraph_property_id_ref: 0,
            horizontal_alignment: alignment,
            vertical_alignment: verticals[index as usize % verticals.len()],
            text_direction: directions[index as usize % directions.len()],
            protection: protections[index as usize % protections.len()],
        };
        let output = TableCellStyleLowerer::lower(
            &fragment(),
            &style,
            &catalog,
            TableCellStyleLimits::default(),
        )?;
        digest.update((output.len() as u64).to_le_bytes());
        digest.update(output);
    }
    assert_eq!(
        hex::encode(digest.finalize()),
        "1ea84bb01fd6ca76986f5a142ca8964ca7e8002ce7acca0b6e668be3f7a09411"
    );
    Ok(())
}

#[test]
fn debug_surfaces_do_not_expose_cell_text() -> TestResult {
    let catalog = sample_catalog(HorizontalAlignment::Center)?;
    let source = fragment();
    let (_, receipt) = TableCellStyleLowerer::lower_with_receipt(
        &source,
        &target(HorizontalAlignment::Center),
        &catalog,
        TableCellStyleLimits::default(),
    )?;
    let diagnostic = format!("{receipt:?}");
    assert!(!diagnostic.contains("둘째 줄"));
    assert!(!diagnostic.contains("A & B"));
    Ok(())
}
