use std::error::Error;

use hwpx_package::{
    COLUMN_PROFILE_ID, ColumnDefinition, ColumnLayout, ColumnLineType, ColumnLineWidth,
    ColumnSeparator, ColumnSize, ColumnSizing, ColumnType, SectionColumnError,
    SectionColumnLimitConfig, SectionColumnLimits, SectionColumnLowerer, SectionColumnReader,
};
use sha2::{Digest as _, Sha256};

type TestResult = Result<(), Box<dyn Error>>;

const BODY_WIDTH: u32 = 42_520;
const CURRENT_COLUMN: &str = r#"<hp:colPr xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" id="" type="NEWSPAPER" layout="LEFT" colCount="1" sameSz="1" sameGap="0"/>"#;
const EQUAL_TWO: &str = r##"<hp:colPr xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" id="equal-2" type="BALANCED_NEWSPAPER" layout="RIGHT" colCount="2" sameSz="1" sameGap="1134"><hp:colLine type="DASH_DOT" width="0.25 mm" color="#12ABEF"/></hp:colPr>"##;
const CUSTOM_TWO: &str = r##"<hp:colPr xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" id="custom-2" type="PARALLEL" layout="MIRROR" colCount="2" sameSz="0" sameGap="0"><hp:colLine type="SOLID" width="0.12 mm" color="#000000"/><hp:colSz width="15000" gap="1000"/><hp:colSz width="26520" gap="0"/></hp:colPr>"##;
const SECTION_ONE: &str = r#"<?xml version="1.0" encoding="UTF-8"?><hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"><hp:p id="p"><hp:run><hp:secPr id=""><hp:grid/></hp:secPr><hp:ctrl><hp:colPr id="" type="NEWSPAPER" layout="LEFT" colCount="1" sameSz="1" sameGap="0"/></hp:ctrl></hp:run></hp:p></hs:sec>"#;
const SECTION_TWO_SPANS: &str = r##"<?xml version="1.0" encoding="UTF-8"?><hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"><hp:p id="p"><hp:run><hp:secPr id=""><hp:grid/></hp:secPr><hp:ctrl><hp:colPr id="first" type="NEWSPAPER" layout="LEFT" colCount="1" sameSz="1" sameGap="0"/></hp:ctrl></hp:run><hp:run><hp:t>middle</hp:t><hp:ctrl><hp:colPr id="second" type="BALANCED_NEWSPAPER" layout="RIGHT" colCount="2" sameSz="1" sameGap="1134"><hp:colLine type="DASH_DOT" width="0.25 mm" color="#12ABEF"/></hp:colPr></hp:ctrl></hp:run></hp:p></hs:sec>"##;

fn current_definition() -> ColumnDefinition {
    ColumnDefinition {
        control_id: String::new(),
        column_type: ColumnType::Newspaper,
        layout: ColumnLayout::Left,
        sizing: ColumnSizing::Equal { count: 1, gap: 0 },
        separator: None,
    }
}

fn equal_two() -> ColumnDefinition {
    ColumnDefinition {
        control_id: "equal-2".to_owned(),
        column_type: ColumnType::BalancedNewspaper,
        layout: ColumnLayout::Right,
        sizing: ColumnSizing::Equal {
            count: 2,
            gap: 1_134,
        },
        separator: Some(ColumnSeparator {
            line_type: ColumnLineType::DashDot,
            width: ColumnLineWidth::Mm0_25,
            color: 0x12_ab_ef,
        }),
    }
}

fn custom_two() -> ColumnDefinition {
    ColumnDefinition {
        control_id: "custom-2".to_owned(),
        column_type: ColumnType::Parallel,
        layout: ColumnLayout::Mirror,
        sizing: ColumnSizing::Custom(vec![
            ColumnSize {
                width: 15_000,
                gap: 1_000,
            },
            ColumnSize {
                width: 26_520,
                gap: 0,
            },
        ]),
        separator: Some(ColumnSeparator {
            line_type: ColumnLineType::Solid,
            width: ColumnLineWidth::Mm0_12,
            color: 0,
        }),
    }
}

#[test]
fn exact_current_2020_column_control_lifts_from_fragment_and_section() -> TestResult {
    let limits = SectionColumnLimits::default();
    assert_eq!(
        SectionColumnReader::read(CURRENT_COLUMN.as_bytes(), BODY_WIDTH, limits)?,
        current_definition()
    );
    let section = SectionColumnReader::read_section(SECTION_ONE.as_bytes(), BODY_WIDTH, limits)?;
    assert_eq!(section.spans, vec![current_definition()]);
    let metrics = section.spans[0].metrics(BODY_WIDTH, limits)?;
    assert_eq!(metrics.column_count, 1);
    assert_eq!(metrics.total_gap, 0);
    assert_eq!(metrics.total_column_width, BODY_WIDTH);
    assert_eq!(metrics.minimum_column_width, BODY_WIDTH);
    assert_eq!(metrics.equal_width_remainder, 0);
    Ok(())
}

#[test]
fn equal_balanced_columns_lower_deterministically_and_relift() -> TestResult {
    let limits = SectionColumnLimits::default();
    let definition = equal_two();
    assert_eq!(
        SectionColumnReader::read(EQUAL_TWO.as_bytes(), BODY_WIDTH, limits)?,
        definition
    );
    let (first, first_receipt) =
        SectionColumnLowerer::lower_with_receipt(&definition, BODY_WIDTH, limits)?;
    let (second, second_receipt) =
        SectionColumnLowerer::lower_with_receipt(&definition, BODY_WIDTH, limits)?;
    assert_eq!(first, second);
    assert_eq!(first_receipt, second_receipt);
    assert_eq!(first_receipt.profile_id, COLUMN_PROFILE_ID);
    assert_eq!(first_receipt.output_bytes, first.len());
    assert_eq!(std::str::from_utf8(&first)?, EQUAL_TWO);
    assert_eq!(first_receipt.metrics.column_count, 2);
    assert_eq!(first_receipt.metrics.total_gap, 1_134);
    assert_eq!(first_receipt.metrics.minimum_column_width, 20_693);
    assert_eq!(first_receipt.metrics.equal_width_remainder, 0);
    Ok(())
}

#[test]
fn custom_parallel_columns_are_an_exact_closed_body_partition() -> TestResult {
    let limits = SectionColumnLimits::default();
    let definition = custom_two();
    assert_eq!(
        SectionColumnReader::read(CUSTOM_TWO.as_bytes(), BODY_WIDTH, limits)?,
        definition
    );
    let metrics = definition.metrics(BODY_WIDTH, limits)?;
    assert_eq!(metrics.column_count, 2);
    assert_eq!(metrics.total_gap, 1_000);
    assert_eq!(metrics.total_column_width, 41_520);
    assert_eq!(metrics.minimum_column_width, 15_000);
    assert_eq!(metrics.equal_width_remainder, 0);
    assert_eq!(
        SectionColumnLowerer::lower(&definition, BODY_WIDTH, limits)?,
        CUSTOM_TWO.as_bytes()
    );
    Ok(())
}

#[test]
fn ordered_section_parts_create_typed_section_breaks() -> TestResult {
    let limits = SectionColumnLimits::default();
    let inputs = [
        (SECTION_ONE.as_bytes(), BODY_WIDTH),
        (SECTION_TWO_SPANS.as_bytes(), BODY_WIDTH),
        (SECTION_ONE.as_bytes(), BODY_WIDTH),
    ];
    let sequence = SectionColumnReader::read_sequence(&inputs, limits)?;
    assert_eq!(sequence.sections.len(), 3);
    assert_eq!(sequence.sections[1].spans.len(), 2);
    assert_eq!(sequence.section_break_count(), 2);
    assert_eq!(sequence.boundaries[0].before_section_index, 1);
    assert_eq!(sequence.boundaries[1].before_section_index, 2);
    Ok(())
}

#[test]
fn selected_span_patch_preserves_every_other_section_byte_and_semantic() -> TestResult {
    let source = SECTION_TWO_SPANS.as_bytes().to_vec();
    let replacement = custom_two();
    let limits = SectionColumnLimits::default();
    let (output, receipt) =
        SectionColumnLowerer::replace_in_section(&source, 1, &replacement, BODY_WIDTH, limits)?;
    assert_eq!(source, SECTION_TWO_SPANS.as_bytes());
    assert_eq!(receipt.profile_id, COLUMN_PROFILE_ID);
    assert_eq!(receipt.span_ordinal, 1);
    assert_eq!(
        &output[..receipt.replaced_start],
        &source[..receipt.replaced_start]
    );
    assert!(output.ends_with(&source[receipt.replaced_end..]));
    assert_ne!(receipt.source_sha256, receipt.output_sha256);
    let readback = SectionColumnReader::read_section(&output, BODY_WIDTH, limits)?;
    assert_eq!(readback.spans[0].control_id, "first");
    assert_eq!(readback.spans[1], replacement);
    assert_eq!(
        SectionColumnLowerer::replace_in_section(&source, 2, &custom_two(), BODY_WIDTH, limits),
        Err(SectionColumnError::SpanNotFound)
    );
    Ok(())
}

#[test]
fn all_official_separator_line_and_width_tokens_roundtrip() -> TestResult {
    let line_types = [
        ColumnLineType::None,
        ColumnLineType::Solid,
        ColumnLineType::Dot,
        ColumnLineType::Dash,
        ColumnLineType::DashDot,
        ColumnLineType::DashDotDot,
        ColumnLineType::LongDash,
        ColumnLineType::Circle,
        ColumnLineType::DoubleSlim,
        ColumnLineType::SlimThick,
        ColumnLineType::ThickSlim,
        ColumnLineType::SlimThickSlim,
        ColumnLineType::Wave,
        ColumnLineType::DoubleWave,
        ColumnLineType::Thick3d,
        ColumnLineType::ThickReverse3d,
        ColumnLineType::ThreeD,
        ColumnLineType::Reverse3d,
    ];
    let widths = [
        ColumnLineWidth::Mm0_1,
        ColumnLineWidth::Mm0_12,
        ColumnLineWidth::Mm0_15,
        ColumnLineWidth::Mm0_2,
        ColumnLineWidth::Mm0_25,
        ColumnLineWidth::Mm0_3,
        ColumnLineWidth::Mm0_4,
        ColumnLineWidth::Mm0_5,
        ColumnLineWidth::Mm0_6,
        ColumnLineWidth::Mm0_7,
        ColumnLineWidth::Mm1_0,
        ColumnLineWidth::Mm1_5,
        ColumnLineWidth::Mm2_0,
        ColumnLineWidth::Mm3_0,
        ColumnLineWidth::Mm4_0,
        ColumnLineWidth::Mm5_0,
    ];
    let limits = SectionColumnLimits::default();
    for (index, line_type) in line_types.into_iter().enumerate() {
        let mut definition = equal_two();
        definition.separator = Some(ColumnSeparator {
            line_type,
            width: widths[index % widths.len()],
            color: u32::try_from(index)? * 0x0001_0101,
        });
        let bytes = SectionColumnLowerer::lower(&definition, BODY_WIDTH, limits)?;
        assert_eq!(
            SectionColumnReader::read(&bytes, BODY_WIDTH, limits)?,
            definition
        );
    }
    Ok(())
}

#[test]
fn impossible_equal_and_custom_layouts_fail_closed() {
    let limits = SectionColumnLimits::default();
    let mut definition = equal_two();
    definition.sizing = ColumnSizing::Equal { count: 0, gap: 0 };
    assert_eq!(
        definition.metrics(BODY_WIDTH, limits),
        Err(SectionColumnError::ColumnLimit)
    );
    definition = equal_two();
    definition.sizing = ColumnSizing::Equal { count: 1, gap: 1 };
    assert_eq!(
        definition.metrics(BODY_WIDTH, limits),
        Err(SectionColumnError::LayoutOverflow)
    );
    definition = equal_two();
    definition.sizing = ColumnSizing::Equal {
        count: 255,
        gap: 1_000,
    };
    assert_eq!(
        definition.metrics(BODY_WIDTH, limits),
        Err(SectionColumnError::LayoutOverflow)
    );
    definition = custom_two();
    if let ColumnSizing::Custom(columns) = &mut definition.sizing {
        columns[1].gap = 1;
    }
    assert_eq!(
        definition.metrics(BODY_WIDTH, limits),
        Err(SectionColumnError::CustomShape)
    );
    definition = custom_two();
    if let ColumnSizing::Custom(columns) = &mut definition.sizing {
        columns[1].width -= 1;
    }
    assert_eq!(
        definition.metrics(BODY_WIDTH, limits),
        Err(SectionColumnError::CustomShape)
    );
    definition = custom_two();
    if let ColumnSizing::Custom(columns) = &mut definition.sizing {
        columns[0].width = 283;
        columns[1].width = BODY_WIDTH - 283 - 1_000;
    }
    assert_eq!(
        definition.metrics(BODY_WIDTH, limits),
        Err(SectionColumnError::LayoutOverflow)
    );
}

#[test]
fn malformed_shape_namespace_and_child_order_are_rejected() {
    let limits = SectionColumnLimits::default();
    assert_eq!(
        SectionColumnReader::read(
            CURRENT_COLUMN
                .replace("2011/paragraph", "2011/head")
                .as_bytes(),
            BODY_WIDTH,
            limits
        ),
        Err(SectionColumnError::WrongRoot)
    );
    assert_eq!(
        SectionColumnReader::read(
            CURRENT_COLUMN
                .replace(" sameGap=\"0\"", " extra=\"1\" sameGap=\"0\"")
                .as_bytes(),
            BODY_WIDTH,
            limits
        ),
        Err(SectionColumnError::UnsupportedShape)
    );
    assert_eq!(
        SectionColumnReader::read(
            CURRENT_COLUMN.replace(" id=\"\"", "").as_bytes(),
            BODY_WIDTH,
            limits
        ),
        Err(SectionColumnError::UnsupportedShape)
    );
    let wrong_parent = SECTION_ONE
        .replace("<hp:ctrl>", "<hp:x>")
        .replace("</hp:ctrl>", "</hp:x>");
    assert_eq!(
        SectionColumnReader::read_section(wrong_parent.as_bytes(), BODY_WIDTH, limits),
        Err(SectionColumnError::UnsupportedShape)
    );
    let duplicate_sec = SECTION_ONE.replace("<hp:grid/>", "<hp:grid/></hp:secPr><hp:secPr>");
    assert_eq!(
        SectionColumnReader::read_section(duplicate_sec.as_bytes(), BODY_WIDTH, limits),
        Err(SectionColumnError::UnsupportedShape)
    );
    let bad_order = CUSTOM_TWO
        .replace(
            "<hp:colLine type=\"SOLID\" width=\"0.12 mm\" color=\"#000000\"/>",
            "",
        )
        .replace(
            "</hp:colPr>",
            "<hp:colLine type=\"SOLID\" width=\"0.12 mm\" color=\"#000000\"/></hp:colPr>",
        );
    assert_eq!(
        SectionColumnReader::read(bad_order.as_bytes(), BODY_WIDTH, limits),
        Err(SectionColumnError::UnsupportedShape)
    );
}

#[test]
fn invalid_number_boolean_enum_id_and_color_are_distinct() {
    let limits = SectionColumnLimits::default();
    assert_eq!(
        SectionColumnReader::read(
            CURRENT_COLUMN
                .replace("colCount=\"1\"", "colCount=\"-1\"")
                .as_bytes(),
            BODY_WIDTH,
            limits
        ),
        Err(SectionColumnError::InvalidNumber)
    );
    assert_eq!(
        SectionColumnReader::read(
            CURRENT_COLUMN
                .replace("sameSz=\"1\"", "sameSz=\"true\"")
                .as_bytes(),
            BODY_WIDTH,
            limits
        ),
        Err(SectionColumnError::InvalidBoolean)
    );
    assert_eq!(
        SectionColumnReader::read(
            CURRENT_COLUMN.replace("NEWSPAPER", "MAGAZINE").as_bytes(),
            BODY_WIDTH,
            limits
        ),
        Err(SectionColumnError::InvalidEnum)
    );
    assert_eq!(
        SectionColumnReader::read(
            CURRENT_COLUMN
                .replace("id=\"\"", "id=\"bad:id\"")
                .as_bytes(),
            BODY_WIDTH,
            limits
        ),
        Err(SectionColumnError::InvalidId)
    );
    assert_eq!(
        SectionColumnReader::read(
            EQUAL_TWO.replace("#12ABEF", "#ABCDEG").as_bytes(),
            BODY_WIDTH,
            limits
        ),
        Err(SectionColumnError::InvalidColor)
    );
}

#[test]
fn malformed_custom_counts_and_same_gap_never_partially_lift() {
    let limits = SectionColumnLimits::default();
    assert_eq!(
        SectionColumnReader::read(
            CUSTOM_TWO
                .replace("colCount=\"2\"", "colCount=\"3\"")
                .as_bytes(),
            BODY_WIDTH,
            limits
        ),
        Err(SectionColumnError::CustomShape)
    );
    assert_eq!(
        SectionColumnReader::read(
            CUSTOM_TWO
                .replace("sameGap=\"0\"", "sameGap=\"1\"")
                .as_bytes(),
            BODY_WIDTH,
            limits
        ),
        Err(SectionColumnError::CustomShape)
    );
    assert_eq!(
        SectionColumnReader::read(
            CUSTOM_TWO
                .replace("<hp:colSz width=\"26520\" gap=\"0\"/>", "")
                .as_bytes(),
            BODY_WIDTH,
            limits
        ),
        Err(SectionColumnError::CustomShape)
    );
    assert_eq!(
        SectionColumnReader::read(
            EQUAL_TWO
                .replace(
                    "</hp:colPr>",
                    "<hp:colSz width=\"20693\" gap=\"0\"/></hp:colPr>",
                )
                .as_bytes(),
            BODY_WIDTH,
            limits
        ),
        Err(SectionColumnError::CustomShape)
    );
}

#[test]
fn finite_input_element_section_span_column_and_output_limits_hold() -> TestResult {
    assert_eq!(
        SectionColumnLimits::new(SectionColumnLimitConfig {
            sections: 0,
            ..SectionColumnLimitConfig::default()
        }),
        Err(SectionColumnError::InvalidLimit)
    );
    let tiny_input = SectionColumnLimits::new(SectionColumnLimitConfig {
        input_bytes: 8,
        ..SectionColumnLimitConfig::default()
    })?;
    assert_eq!(
        SectionColumnReader::read(CURRENT_COLUMN.as_bytes(), BODY_WIDTH, tiny_input),
        Err(SectionColumnError::InputLimit)
    );
    let tiny_elements = SectionColumnLimits::new(SectionColumnLimitConfig {
        elements: 1,
        ..SectionColumnLimitConfig::default()
    })?;
    assert_eq!(
        SectionColumnReader::read(EQUAL_TWO.as_bytes(), BODY_WIDTH, tiny_elements),
        Err(SectionColumnError::ElementLimit)
    );
    let one_section = SectionColumnLimits::new(SectionColumnLimitConfig {
        sections: 1,
        ..SectionColumnLimitConfig::default()
    })?;
    assert_eq!(
        SectionColumnReader::read_sequence(
            &[
                (SECTION_ONE.as_bytes(), BODY_WIDTH),
                (SECTION_ONE.as_bytes(), BODY_WIDTH)
            ],
            one_section
        ),
        Err(SectionColumnError::SectionLimit)
    );
    let one_span = SectionColumnLimits::new(SectionColumnLimitConfig {
        spans_per_section: 1,
        ..SectionColumnLimitConfig::default()
    })?;
    assert_eq!(
        SectionColumnReader::read_section(SECTION_TWO_SPANS.as_bytes(), BODY_WIDTH, one_span),
        Err(SectionColumnError::SpanLimit)
    );
    let one_column = SectionColumnLimits::new(SectionColumnLimitConfig {
        columns_per_span: 1,
        ..SectionColumnLimitConfig::default()
    })?;
    assert_eq!(
        SectionColumnReader::read(EQUAL_TWO.as_bytes(), BODY_WIDTH, one_column),
        Err(SectionColumnError::ColumnLimit)
    );
    let tiny_output = SectionColumnLimits::new(SectionColumnLimitConfig {
        output_bytes: 32,
        ..SectionColumnLimitConfig::default()
    })?;
    assert_eq!(
        SectionColumnLowerer::lower(&equal_two(), BODY_WIDTH, tiny_output),
        Err(SectionColumnError::OutputLimit)
    );
    assert_eq!(
        SectionColumnReader::read_sequence(&[], SectionColumnLimits::default()),
        Err(SectionColumnError::SectionLimit)
    );
    Ok(())
}

#[test]
fn preserving_admission_blocks_dtd_comments_and_ambiguous_local_names() {
    let limits = SectionColumnLimits::default();
    let dtd = format!("<!DOCTYPE x [<!ENTITY e 'x'>]>{CURRENT_COLUMN}");
    assert!(matches!(
        SectionColumnReader::read(dtd.as_bytes(), BODY_WIDTH, limits),
        Err(SectionColumnError::Preserving(_))
    ));
    assert_eq!(
        SectionColumnReader::read(
            CURRENT_COLUMN
                .replace("/>", "><!--x--></hp:colPr>")
                .as_bytes(),
            BODY_WIDTH,
            limits
        ),
        Err(SectionColumnError::UnsupportedShape)
    );
    let wrong_local = SECTION_ONE.replace("<hp:colPr", "<bad:colPr xmlns:bad=\"urn:bad\"");
    assert_eq!(
        SectionColumnReader::read_section(wrong_local.as_bytes(), BODY_WIDTH, limits),
        Err(SectionColumnError::UnsupportedShape)
    );
}

#[test]
fn public_error_codes_are_stable() {
    let errors = [
        SectionColumnError::InvalidLimit,
        SectionColumnError::InputLimit,
        SectionColumnError::ElementLimit,
        SectionColumnError::SectionLimit,
        SectionColumnError::SpanLimit,
        SectionColumnError::ColumnLimit,
        SectionColumnError::WrongRoot,
        SectionColumnError::UnsupportedShape,
        SectionColumnError::InvalidNumber,
        SectionColumnError::InvalidBoolean,
        SectionColumnError::InvalidEnum,
        SectionColumnError::InvalidId,
        SectionColumnError::InvalidColor,
        SectionColumnError::LayoutOverflow,
        SectionColumnError::CustomShape,
        SectionColumnError::SpanNotFound,
        SectionColumnError::OutputLimit,
        SectionColumnError::ArithmeticOverflow,
        SectionColumnError::AllocationFailed,
        SectionColumnError::ReadbackMismatch,
    ];
    let codes: Vec<_> = errors.iter().map(SectionColumnError::code).collect();
    assert_eq!(codes.len(), 20);
    assert!(
        codes
            .iter()
            .all(|code| code.starts_with("section_columns_"))
    );
    let unique: std::collections::BTreeSet<_> = codes.iter().copied().collect();
    assert_eq!(unique.len(), codes.len());
}

#[test]
fn fixed_128_case_section_column_corpus_is_deterministic() -> TestResult {
    let limits = SectionColumnLimits::default();
    let line_types = [
        ColumnLineType::None,
        ColumnLineType::Solid,
        ColumnLineType::Dot,
        ColumnLineType::Dash,
        ColumnLineType::DashDot,
        ColumnLineType::DashDotDot,
        ColumnLineType::LongDash,
        ColumnLineType::Circle,
        ColumnLineType::DoubleSlim,
        ColumnLineType::SlimThick,
        ColumnLineType::ThickSlim,
        ColumnLineType::SlimThickSlim,
        ColumnLineType::Wave,
        ColumnLineType::DoubleWave,
        ColumnLineType::Thick3d,
        ColumnLineType::ThickReverse3d,
        ColumnLineType::ThreeD,
        ColumnLineType::Reverse3d,
    ];
    let widths = [
        ColumnLineWidth::Mm0_1,
        ColumnLineWidth::Mm0_12,
        ColumnLineWidth::Mm0_15,
        ColumnLineWidth::Mm0_2,
        ColumnLineWidth::Mm0_25,
        ColumnLineWidth::Mm0_3,
        ColumnLineWidth::Mm0_4,
        ColumnLineWidth::Mm0_5,
        ColumnLineWidth::Mm0_6,
        ColumnLineWidth::Mm0_7,
        ColumnLineWidth::Mm1_0,
        ColumnLineWidth::Mm1_5,
        ColumnLineWidth::Mm2_0,
        ColumnLineWidth::Mm3_0,
        ColumnLineWidth::Mm4_0,
        ColumnLineWidth::Mm5_0,
    ];
    let mut corpus = Vec::new();
    for index in 0_u32..128 {
        let count = u16::try_from(index % 4 + 1)?;
        let gap = if count == 1 { 0 } else { (index * 37) % 1_500 };
        let mut definition = ColumnDefinition {
            control_id: format!("case-{index:03}"),
            column_type: match index % 3 {
                0 => ColumnType::Newspaper,
                1 => ColumnType::BalancedNewspaper,
                _ => ColumnType::Parallel,
            },
            layout: match (index / 3) % 3 {
                0 => ColumnLayout::Left,
                1 => ColumnLayout::Right,
                _ => ColumnLayout::Mirror,
            },
            sizing: ColumnSizing::Equal { count, gap },
            separator: Some(ColumnSeparator {
                line_type: line_types[usize::try_from(index)? % line_types.len()],
                width: widths[usize::try_from(index * 5)? % widths.len()],
                color: (index * 0x0001_0203) & 0x00ff_ffff,
            }),
        };
        if index % 5 == 0 {
            definition.separator = None;
        }
        let bytes = SectionColumnLowerer::lower(&definition, BODY_WIDTH, limits)?;
        assert_eq!(
            SectionColumnReader::read(&bytes, BODY_WIDTH, limits)?,
            definition
        );
        corpus.extend_from_slice(&(u32::try_from(bytes.len())?).to_le_bytes());
        corpus.extend_from_slice(&bytes);
    }
    let digest = hex::encode(Sha256::digest(&corpus));
    assert_eq!(
        digest,
        "308c3e4b1e3083a0d445541d0a6ed29ae3471b97ba65af768134601997b94d01"
    );
    Ok(())
}
