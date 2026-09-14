use std::error::Error;

use hwpx_package::{
    BorderWidth, CenterLine, CharacterStyleCatalogReader, CharacterStyleLimits, Color,
    CompatibleHeading, Heading, HeadingType, HorizontalAlignment, LineSpacingType, LineType2,
    MeasurementUnit, PARAGRAPH_STYLE_PROFILE_ID, ParagraphStyleCatalog,
    ParagraphStyleCatalogReader, ParagraphStyleCatalogWriter, ParagraphStyleError,
    ParagraphStyleLimitConfig, ParagraphStyleLimits, TextDirection, TextFlowLimits, TextFlowReader,
    VerticalAlignment, WordBreak,
};
use sha2::{Digest as _, Sha256};

type TestResult = Result<(), Box<dyn Error>>;

const HEADER: &[u8] = include_bytes!("../src/hancom_2020_minimal_header.xml");

#[test]
fn exact_current_2020_header_lifts_reference_domains_borders_and_paragraphs() -> TestResult {
    let catalog = ParagraphStyleCatalogReader::read(HEADER, ParagraphStyleLimits::default())?;
    assert_eq!(catalog.references.tab_property_ids, [0, 1, 2]);
    assert_eq!(catalog.references.numbering_ids, [1]);
    assert!(catalog.references.bullet_ids.is_empty());
    assert_eq!(catalog.border_fills.len(), 2);
    assert_eq!(catalog.border_fills[0].id, 1);
    assert_eq!(catalog.border_fills[1].id, 2);
    assert_eq!(catalog.styles.len(), 20);
    assert_eq!(catalog.styles[10].layout.current.margin.intent.value, -1310);
    assert_eq!(
        catalog.styles[10].layout.fallback.margin.intent.value,
        -2620
    );
    assert_eq!(
        catalog.styles[10].layout.current.margin.intent.unit,
        MeasurementUnit::HwpUnit
    );
    assert!(matches!(
        catalog.styles[16].heading,
        CompatibleHeading::MetaTag {
            current: Heading {
                heading_type: HeadingType::Outline,
                level: 8,
                ..
            },
            fallback: Heading {
                heading_type: HeadingType::None,
                ..
            }
        }
    ));
    let brush = catalog.border_fills[1]
        .fill_brush
        .ok_or("missing exact 2020 window brush")?;
    assert_eq!(brush.window.face_color, Color::None);
    assert_eq!(brush.window.hatch_color, Some(Color::Rgb(0x99, 0x99, 0x99)));
    assert_eq!(brush.window.hatch_style, None);
    Ok(())
}

#[test]
fn current_2020_header_without_unused_numberings_is_admitted() -> TestResult {
    let header = std::str::from_utf8(HEADER)?;
    let start = header.find("<hh:numberings ").ok_or("numberings start")?;
    let end = header.find("</hh:numberings>").ok_or("numberings end")? + "</hh:numberings>".len();
    let without_numberings = format!("{}{}", &header[..start], &header[end..]);
    let catalog = ParagraphStyleCatalogReader::read(
        without_numberings.as_bytes(),
        ParagraphStyleLimits::default(),
    )?;
    assert!(catalog.references.numbering_ids.is_empty());
    assert_eq!(catalog.border_fills.len(), 2);
    assert_eq!(catalog.styles.len(), 20);
    Ok(())
}

#[test]
fn lower_is_deterministic_and_exactly_readable_with_external_domains() -> TestResult {
    let catalog = ParagraphStyleCatalogReader::read(HEADER, ParagraphStyleLimits::default())?;
    let (first, first_receipt) =
        ParagraphStyleCatalogWriter::lower_with_receipt(&catalog, ParagraphStyleLimits::default())?;
    let (second, second_receipt) =
        ParagraphStyleCatalogWriter::lower_with_receipt(&catalog, ParagraphStyleLimits::default())?;
    assert_eq!(first, second);
    assert_eq!(first_receipt, second_receipt);
    assert_eq!(first_receipt.profile_id, PARAGRAPH_STYLE_PROFILE_ID);
    assert_eq!(first_receipt.output_bytes, first.len());
    assert_eq!(first_receipt.border_fill_count, 2);
    assert_eq!(first_receipt.style_count, 20);
    assert_eq!(
        ParagraphStyleCatalogReader::read_with_reference_domains(
            &first,
            &catalog.references,
            ParagraphStyleLimits::default()
        )?,
        catalog
    );
    let xml = std::str::from_utf8(&first)?;
    assert!(xml.starts_with("<?xml version=\"1.0\" encoding=\"UTF-8\"?><hh:refList"));
    assert!(xml.contains("<hh:borderFills itemCnt=\"2\">"));
    assert!(xml.contains("<hh:paraProperties itemCnt=\"20\">"));
    assert!(xml.contains("http://www.hancom.co.kr/hwpml/2016/HwpUnitChar"));
    assert!(xml.contains("http://www.hancom.co.kr/hwpml/2021/metatag"));
    Ok(())
}

#[test]
fn typed_variations_and_both_compatibility_branches_round_trip() -> TestResult {
    let mut catalog = ParagraphStyleCatalogReader::read(HEADER, ParagraphStyleLimits::default())?;
    let style = &mut catalog.styles[0];
    style.condense = 75;
    style.font_line_height = true;
    style.snap_to_grid = false;
    style.suppress_line_numbers = true;
    style.checked = true;
    style.text_direction = Some(TextDirection::RightToLeft);
    style.horizontal_alignment = HorizontalAlignment::DistributeSpace;
    style.vertical_alignment = VerticalAlignment::Bottom;
    style.heading = CompatibleHeading::Direct(Heading {
        heading_type: HeadingType::Number,
        id_ref: 1,
        level: 4,
    });
    style.break_settings.latin_word = WordBreak::Hyphenation;
    style.break_settings.non_latin_word = WordBreak::BreakWord;
    style.break_settings.widow_orphan = true;
    style.break_settings.keep_with_next = true;
    style.break_settings.keep_lines = true;
    style.break_settings.page_break_before = true;
    style.break_settings.line_wrap = hwpx_package::LineWrap::Squeeze;
    style.auto_spacing.e_asian_english = true;
    style.auto_spacing.e_asian_number = true;
    style.layout.current.margin.intent.value = -7200;
    style.layout.current.margin.left.value = 7200;
    style.layout.current.margin.left.unit = MeasurementUnit::Character;
    style.layout.current.line_spacing.spacing_type = LineSpacingType::Fixed;
    style.layout.current.line_spacing.value = 1200;
    style.layout.current.line_spacing.unit = MeasurementUnit::Character;
    style.layout.fallback.margin.intent.value = -14400;
    style.layout.fallback.margin.left.value = 14400;
    style.layout.fallback.line_spacing.spacing_type = LineSpacingType::AtLeast;
    style.layout.fallback.line_spacing.value = 1600;
    style.border.offset_left = -100;
    style.border.offset_right = 100;
    style.border.connect = true;
    style.border.ignore_margin = true;

    let border = &mut catalog.border_fills[1];
    border.three_d = true;
    border.shadow = true;
    border.center_line = CenterLine::Cross;
    border.slash.slash_type = hwpx_package::SlashType::CenterBelow;
    border.slash.crooked = true;
    border.slash.is_counter = true;
    border.left.line_type = LineType2::DoubleSlim;
    border.left.width = BorderWidth::Mm5_0;
    border.left.color = Color::Rgb(0x12, 0x34, 0x56);
    let brush = border.fill_brush.as_mut().ok_or("missing brush")?;
    brush.window.hatch_style = Some(hwpx_package::HatchStyle::CrossDiagonal);
    brush.window.alpha = 255;

    let bytes = ParagraphStyleCatalogWriter::lower(&catalog, ParagraphStyleLimits::default())?;
    assert_eq!(
        ParagraphStyleCatalogReader::read_with_reference_domains(
            &bytes,
            &catalog.references,
            ParagraphStyleLimits::default()
        )?,
        catalog
    );
    Ok(())
}

#[test]
fn semantic_dedup_is_stable_and_rewrites_only_typed_paragraph_reference() -> TestResult {
    let mut catalog = ParagraphStyleCatalogReader::read(HEADER, ParagraphStyleLimits::default())?;
    let mut duplicate = catalog.styles[0].clone();
    duplicate.id = u32::try_from(catalog.styles.len())?;
    catalog.styles.push(duplicate);
    let result = catalog.deduplicate(ParagraphStyleLimits::default())?;
    assert_eq!(result.old_to_new.len(), 21);
    assert_eq!(result.old_to_new[20], 0);

    let paragraph = br#"<hp:p xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" id="9" paraPrIDRef="20" styleIDRef="7"><hp:run charPrIDRef="3"><hp:t>text</hp:t></hp:run></hp:p>"#;
    let mut flow = TextFlowReader::read(paragraph, TextFlowLimits::default())?;
    result.rewrite_text_flow(&mut flow)?;
    assert_eq!(flow.paragraph.paragraph_property_id_ref, Some(0));
    assert_eq!(flow.paragraph.style_id_ref, Some(7));
    assert_eq!(flow.paragraph.id, 9);

    let mut invalid = flow.clone();
    invalid.paragraph.paragraph_property_id_ref = Some(99);
    let unchanged = invalid.clone();
    assert_eq!(
        result.rewrite_text_flow(&mut invalid),
        Err(ParagraphStyleError::DanglingReference)
    );
    assert_eq!(invalid, unchanged);
    Ok(())
}

#[test]
fn character_style_border_references_are_checked_across_p05_modules() -> TestResult {
    let paragraphs = ParagraphStyleCatalogReader::read(HEADER, ParagraphStyleLimits::default())?;
    let mut characters =
        CharacterStyleCatalogReader::read(HEADER, CharacterStyleLimits::default())?;
    paragraphs.validate_character_style_references(&characters)?;
    characters.styles[0].border_fill_id_ref = Some(99);
    assert_eq!(
        paragraphs.validate_character_style_references(&characters),
        Err(ParagraphStyleError::DanglingReference)
    );
    Ok(())
}

#[test]
fn malformed_counts_ids_references_ranges_and_enums_fail_closed() -> TestResult {
    let source = std::str::from_utf8(HEADER)?;
    let cases = [
        (
            source.replacen(
                "<hh:borderFills itemCnt=\"2\"",
                "<hh:borderFills itemCnt=\"1\"",
                1,
            ),
            ParagraphStyleError::CountMismatch,
        ),
        (
            source.replacen("<hh:borderFill id=\"1\"", "<hh:borderFill id=\"0\"", 1),
            ParagraphStyleError::InvalidId,
        ),
        (
            source.replacen(
                "<hh:paraProperties itemCnt=\"20\"",
                "<hh:paraProperties itemCnt=\"19\"",
                1,
            ),
            ParagraphStyleError::CountMismatch,
        ),
        (
            source.replacen("<hh:paraPr id=\"0\"", "<hh:paraPr id=\"7\"", 1),
            ParagraphStyleError::InvalidId,
        ),
        (
            source.replacen("<hh:numbering id=\"1\"", "<hh:numbering id=\"2\"", 1),
            ParagraphStyleError::InvalidId,
        ),
        (
            source.replacen(
                "<hh:border borderFillIDRef=\"2\"",
                "<hh:border borderFillIDRef=\"99\"",
                1,
            ),
            ParagraphStyleError::DanglingReference,
        ),
        (
            source.replacen("condense=\"0\"", "condense=\"76\"", 1),
            ParagraphStyleError::OutOfRange,
        ),
        (
            source.replacen(
                "<hh:lineSpacing type=\"PERCENT\" value=\"160\"",
                "<hh:lineSpacing type=\"PERCENT\" value=\"501\"",
                1,
            ),
            ParagraphStyleError::OutOfRange,
        ),
        (
            source.replacen("lineWrap=\"BREAK\"", "lineWrap=\"UNKNOWN\"", 1),
            ParagraphStyleError::InvalidEnum,
        ),
        (
            source.replacen("alpha=\"0\"", "alpha=\"256\"", 1),
            ParagraphStyleError::OutOfRange,
        ),
        (
            source.replacen(
                "hp:required-namespace=\"http://www.hancom.co.kr/hwpml/2016/HwpUnitChar\"",
                "hp:required-namespace=\"urn:not-hwpunit-char\"",
                1,
            ),
            ParagraphStyleError::UnsupportedShape,
        ),
    ];
    for (bytes, expected) in cases {
        let Err(error) =
            ParagraphStyleCatalogReader::read(bytes.as_bytes(), ParagraphStyleLimits::default())
        else {
            return Err("invalid paragraph catalog was admitted".into());
        };
        assert_eq!(error, expected);
    }
    Ok(())
}

#[test]
fn public_error_codes_are_stable() {
    let cases = [
        (
            ParagraphStyleError::InvalidLimit,
            "paragraph_style_invalid_limit",
        ),
        (
            ParagraphStyleError::InputLimit,
            "paragraph_style_input_limit",
        ),
        (ParagraphStyleError::WrongRoot, "paragraph_style_wrong_root"),
        (
            ParagraphStyleError::UnsupportedShape,
            "paragraph_style_unsupported_shape",
        ),
        (
            ParagraphStyleError::CountMismatch,
            "paragraph_style_count_mismatch",
        ),
        (ParagraphStyleError::InvalidId, "paragraph_style_invalid_id"),
        (
            ParagraphStyleError::DanglingReference,
            "paragraph_style_dangling_reference",
        ),
        (
            ParagraphStyleError::InvalidNumber,
            "paragraph_style_invalid_number",
        ),
        (
            ParagraphStyleError::InvalidBoolean,
            "paragraph_style_invalid_boolean",
        ),
        (
            ParagraphStyleError::InvalidEnum,
            "paragraph_style_invalid_enum",
        ),
        (
            ParagraphStyleError::InvalidColor,
            "paragraph_style_invalid_color",
        ),
        (
            ParagraphStyleError::OutOfRange,
            "paragraph_style_out_of_range",
        ),
        (
            ParagraphStyleError::StyleLimit,
            "paragraph_style_style_limit",
        ),
        (
            ParagraphStyleError::BorderFillLimit,
            "paragraph_style_border_fill_limit",
        ),
        (
            ParagraphStyleError::ReferenceLimit,
            "paragraph_style_reference_limit",
        ),
        (
            ParagraphStyleError::ElementLimit,
            "paragraph_style_element_limit",
        ),
        (
            ParagraphStyleError::OutputLimit,
            "paragraph_style_output_limit",
        ),
        (
            ParagraphStyleError::AllocationFailed,
            "paragraph_style_allocation_failed",
        ),
        (
            ParagraphStyleError::ReadbackMismatch,
            "paragraph_style_readback_mismatch",
        ),
    ];
    for (error, code) in cases {
        assert_eq!(error.code(), code);
    }
}

#[test]
fn wrong_namespace_malformed_xml_and_missing_external_domains_are_not_admitted() -> TestResult {
    let source = std::str::from_utf8(HEADER)?;
    let wrong_namespace = source.replacen(
        "http://www.hancom.co.kr/hwpml/2011/head",
        "urn:not-hancom-head",
        1,
    );
    assert_eq!(
        ParagraphStyleCatalogReader::read(
            wrong_namespace.as_bytes(),
            ParagraphStyleLimits::default()
        ),
        Err(ParagraphStyleError::WrongRoot)
    );
    assert!(matches!(
        ParagraphStyleCatalogReader::read(b"<hh:head", ParagraphStyleLimits::default()),
        Err(ParagraphStyleError::Preserving(_))
    ));

    let catalog = ParagraphStyleCatalogReader::read(HEADER, ParagraphStyleLimits::default())?;
    let fragment = ParagraphStyleCatalogWriter::lower(&catalog, ParagraphStyleLimits::default())?;
    assert_eq!(
        ParagraphStyleCatalogReader::read(&fragment, ParagraphStyleLimits::default()),
        Err(ParagraphStyleError::UnsupportedShape)
    );
    Ok(())
}

#[test]
fn finite_input_model_and_output_limits_are_enforced() -> TestResult {
    let tiny_input = ParagraphStyleLimits::new(ParagraphStyleLimitConfig {
        input_bytes: 1,
        ..ParagraphStyleLimitConfig::default()
    })?;
    assert_eq!(
        ParagraphStyleCatalogReader::read(HEADER, tiny_input),
        Err(ParagraphStyleError::InputLimit)
    );

    let catalog = ParagraphStyleCatalogReader::read(HEADER, ParagraphStyleLimits::default())?;
    let tiny_style = ParagraphStyleLimits::new(ParagraphStyleLimitConfig {
        styles: 1,
        ..ParagraphStyleLimitConfig::default()
    })?;
    assert_eq!(
        ParagraphStyleCatalogWriter::lower(&catalog, tiny_style),
        Err(ParagraphStyleError::StyleLimit)
    );
    let tiny_border = ParagraphStyleLimits::new(ParagraphStyleLimitConfig {
        border_fills: 1,
        ..ParagraphStyleLimitConfig::default()
    })?;
    assert_eq!(
        ParagraphStyleCatalogWriter::lower(&catalog, tiny_border),
        Err(ParagraphStyleError::BorderFillLimit)
    );
    let tiny_output = ParagraphStyleLimits::new(ParagraphStyleLimitConfig {
        input_bytes: 10_000,
        ..ParagraphStyleLimitConfig::default()
    })?;
    assert_eq!(
        ParagraphStyleCatalogWriter::lower(&catalog, tiny_output),
        Err(ParagraphStyleError::OutputLimit)
    );
    Ok(())
}

#[test]
fn compatibility_branch_difference_is_part_of_semantic_identity() -> TestResult {
    let mut catalog = ParagraphStyleCatalogReader::read(HEADER, ParagraphStyleLimits::default())?;
    let mut same_current_different_fallback = catalog.styles[0].clone();
    same_current_different_fallback.id = u32::try_from(catalog.styles.len())?;
    same_current_different_fallback
        .layout
        .fallback
        .margin
        .left
        .value = 1;
    catalog.styles.push(same_current_different_fallback);
    let result = catalog.deduplicate(ParagraphStyleLimits::default())?;
    assert_ne!(result.old_to_new[20], result.old_to_new[0]);
    Ok(())
}

#[test]
fn malformed_public_dedup_mapping_cannot_partially_rewrite() -> TestResult {
    let catalog = ParagraphStyleCatalogReader::read(HEADER, ParagraphStyleLimits::default())?;
    let mut result = catalog.deduplicate(ParagraphStyleLimits::default())?;
    result.old_to_new.clear();
    result.old_to_new.push(0);
    let paragraph = br#"<hp:p xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" id="1" paraPrIDRef="0"><hp:run><hp:t>x</hp:t></hp:run></hp:p>"#;
    let mut flow = TextFlowReader::read(paragraph, TextFlowLimits::default())?;
    let unchanged = flow.clone();
    assert_eq!(
        result.rewrite_text_flow(&mut flow),
        Err(ParagraphStyleError::InvalidId)
    );
    assert_eq!(flow, unchanged);
    Ok(())
}

#[test]
fn deterministic_128_case_variation_corpus_has_locked_digest() -> TestResult {
    let base = ParagraphStyleCatalogReader::read(HEADER, ParagraphStyleLimits::default())?;
    let mut digest = Sha256::new();
    for case in 0_u32..128 {
        let mut catalog: ParagraphStyleCatalog = base.clone();
        let style = &mut catalog.styles[0];
        style.horizontal_alignment = match case % 6 {
            0 => HorizontalAlignment::Justify,
            1 => HorizontalAlignment::Left,
            2 => HorizontalAlignment::Right,
            3 => HorizontalAlignment::Center,
            4 => HorizontalAlignment::Distribute,
            _ => HorizontalAlignment::DistributeSpace,
        };
        style.vertical_alignment = match (case / 2) % 4 {
            0 => VerticalAlignment::Baseline,
            1 => VerticalAlignment::Top,
            2 => VerticalAlignment::Center,
            _ => VerticalAlignment::Bottom,
        };
        style.break_settings.widow_orphan = case & 1 != 0;
        style.break_settings.keep_with_next = case & 2 != 0;
        style.break_settings.keep_lines = case & 4 != 0;
        style.break_settings.page_break_before = case & 8 != 0;
        style.break_settings.line_wrap = match (case / 3) % 3 {
            0 => hwpx_package::LineWrap::Break,
            1 => hwpx_package::LineWrap::Squeeze,
            _ => hwpx_package::LineWrap::Keep,
        };
        style.auto_spacing.e_asian_english = case & 16 != 0;
        style.auto_spacing.e_asian_number = case & 32 != 0;
        style.layout.current.margin.intent.value = i32::try_from(case)? - 64;
        style.layout.fallback.margin.intent.value = (i32::try_from(case)? - 64) * 2;
        style.layout.current.line_spacing.value = 100 + i32::try_from(case)?;
        style.layout.fallback.line_spacing.value = 200 + i32::try_from(case)?;
        let bytes = ParagraphStyleCatalogWriter::lower(&catalog, ParagraphStyleLimits::default())?;
        digest.update(u64::try_from(bytes.len())?.to_le_bytes());
        digest.update(bytes);
    }
    assert_eq!(
        hex::encode(digest.finalize()),
        "ae926c9940e0989eb49f977bcacf1266b12f2a62309896cb7c112b87220ed339"
    );
    Ok(())
}
