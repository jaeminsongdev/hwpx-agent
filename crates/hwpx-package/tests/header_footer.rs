use std::error::Error;
use std::io::Cursor;

use hwpx_package::{
    BoundedZipReader, FirstPageDisplay, FirstPageVisibility, HEADER_FOOTER_PROFILE_ID,
    Hancom2020Vs0Builder, HeaderFooterBody, HeaderFooterDefinition, HeaderFooterError,
    HeaderFooterInline, HeaderFooterKind, HeaderFooterLimitConfig, HeaderFooterLimits,
    HeaderFooterLowerer, HeaderFooterParagraph, HeaderFooterReader, HeaderFooterRun,
    MasterPageDefinition, MasterPageVariant, NumberFormat, PackageLimits, PageField, PageFieldKind,
    PageNumberPlacement, PageNumberPosition, PageNumberRestart, PageVariant, SectionPagePolicy,
};
use sha2::{Digest as _, Sha256};

type TestResult = Result<(), Box<dyn Error>>;

fn field(kind: PageFieldKind, number: i32) -> PageField {
    PageField {
        displayed_number: number,
        kind,
        format: NumberFormat::Digit,
        user_character: String::new(),
        prefix: "[".to_owned(),
        suffix: "]".to_owned(),
        superscript: false,
    }
}

fn body(id: &str, paragraph_id: &str, label: &str) -> HeaderFooterBody {
    HeaderFooterBody {
        id: id.to_owned(),
        text_direction: hwpx_package::HeaderFooterTextDirection::Horizontal,
        line_wrap: hwpx_package::HeaderFooterLineWrap::Break,
        vertical_alignment: hwpx_package::HeaderFooterVerticalAlignment::Center,
        link_list_id_ref: 0,
        link_list_next_id_ref: 0,
        text_width: 42_520,
        text_height: 2_000,
        has_text_reference: false,
        has_number_reference: true,
        paragraphs: vec![HeaderFooterParagraph {
            id: paragraph_id.to_owned(),
            paragraph_property_id_ref: 0,
            style_id_ref: 0,
            page_break: false,
            column_break: false,
            merged: false,
            runs: vec![HeaderFooterRun {
                character_style_id_ref: 0,
                inlines: vec![
                    HeaderFooterInline::Text {
                        value: label.to_owned(),
                        character_style_id_ref: Some(0),
                    },
                    HeaderFooterInline::Tab {
                        width: 8_000,
                        leader: 0,
                        tab_type: 0,
                    },
                    HeaderFooterInline::PageField(field(PageFieldKind::Page, 1)),
                    HeaderFooterInline::Text {
                        value: "/".to_owned(),
                        character_style_id_ref: None,
                    },
                    HeaderFooterInline::PageField(field(PageFieldKind::TotalPage, 2)),
                    HeaderFooterInline::LineBreak,
                ],
            }],
        }],
    }
}

fn definition(kind: HeaderFooterKind, applies_to: PageVariant, id: u32) -> HeaderFooterDefinition {
    HeaderFooterDefinition {
        id,
        kind,
        applies_to,
        body: body(
            &format!("body-{id}"),
            &format!("paragraph-{id}"),
            match kind {
                HeaderFooterKind::Header => "머리말<&>",
                HeaderFooterKind::Footer => "꼬리말",
            },
        ),
    }
}

fn policy(definitions: Vec<HeaderFooterDefinition>) -> SectionPagePolicy {
    SectionPagePolicy {
        restart: PageNumberRestart {
            page_starts_on: PageVariant::Odd,
            page: 7,
            picture: 1,
            table: 1,
            equation: 1,
        },
        first_page: FirstPageVisibility {
            header: FirstPageDisplay::Hide,
            footer: FirstPageDisplay::Show,
            master_page: FirstPageDisplay::Hide,
            page_number: FirstPageDisplay::Hide,
        },
        page_starts_on: Some(PageVariant::Even),
        page_number: Some(PageNumberPlacement {
            position: PageNumberPosition::OutsideBottom,
            format: NumberFormat::RomanSmall,
            side_character: "-".to_owned(),
        }),
        definitions,
        master_page_references: Vec::new(),
        declared_master_page_count: 0,
    }
}

fn section_xml(policy: &SectionPagePolicy) -> TestResultWith<Vec<u8>> {
    let properties =
        HeaderFooterLowerer::lower_section_properties(policy, HeaderFooterLimits::default())?;
    let controls =
        HeaderFooterLowerer::lower_section_controls(policy, HeaderFooterLimits::default())?;
    Ok(format!(
        concat!(
            r#"<?xml version="1.0" encoding="UTF-8"?>"#,
            r#"<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" "#,
            r#"xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">"#,
            r#"<hp:p id="root" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">"#,
            r#"<hp:run charPrIDRef="0"><hp:secPr id="" masterPageCnt="{}">{}"#,
            r#"</hp:secPr>{}</hp:run></hp:p></hs:sec>"#,
        ),
        policy.declared_master_page_count,
        std::str::from_utf8(&properties)?,
        std::str::from_utf8(&controls)?,
    )
    .into_bytes())
}

type TestResultWith<T> = Result<T, Box<dyn Error>>;

#[test]
fn header_and_footer_with_page_fields_roundtrip() -> TestResult {
    for expected in [
        definition(HeaderFooterKind::Header, PageVariant::Odd, 1),
        definition(HeaderFooterKind::Footer, PageVariant::Even, 2),
    ] {
        let (bytes, receipt) =
            HeaderFooterLowerer::lower_definition(&expected, HeaderFooterLimits::default())?;
        assert_eq!(receipt.profile_id, HEADER_FOOTER_PROFILE_ID);
        assert_eq!(receipt.sha256, Sha256::digest(&bytes).as_slice());
        assert_eq!(
            HeaderFooterReader::read_definition(&bytes, HeaderFooterLimits::default())?,
            expected
        );
    }
    Ok(())
}

#[test]
fn odd_even_and_both_variants_are_distinct_and_ordered() -> TestResult {
    let definitions = vec![
        definition(HeaderFooterKind::Header, PageVariant::Both, 1),
        definition(HeaderFooterKind::Header, PageVariant::Even, 2),
        definition(HeaderFooterKind::Header, PageVariant::Odd, 3),
        definition(HeaderFooterKind::Footer, PageVariant::Both, 4),
        definition(HeaderFooterKind::Footer, PageVariant::Even, 5),
        definition(HeaderFooterKind::Footer, PageVariant::Odd, 6),
    ];
    let expected = policy(definitions);
    assert_eq!(
        HeaderFooterReader::read_section(&section_xml(&expected)?, HeaderFooterLimits::default())?,
        expected
    );
    Ok(())
}

#[test]
fn first_page_visibility_restart_and_side_control_roundtrip() -> TestResult {
    let expected = policy(vec![definition(
        HeaderFooterKind::Header,
        PageVariant::Both,
        1,
    )]);
    let actual =
        HeaderFooterReader::read_section(&section_xml(&expected)?, HeaderFooterLimits::default())?;
    assert_eq!(actual.restart.page_starts_on, PageVariant::Odd);
    assert_eq!(actual.restart.page, 7);
    assert_eq!(actual.first_page.header, FirstPageDisplay::Hide);
    assert_eq!(actual.first_page.master_page, FirstPageDisplay::Hide);
    assert_eq!(actual.first_page.page_number, FirstPageDisplay::Hide);
    assert_eq!(actual.page_starts_on, Some(PageVariant::Even));
    assert_eq!(actual.page_number, expected.page_number);
    Ok(())
}

#[test]
fn every_official_page_number_position_roundtrips() -> TestResult {
    let positions = [
        PageNumberPosition::None,
        PageNumberPosition::TopLeft,
        PageNumberPosition::TopCenter,
        PageNumberPosition::TopRight,
        PageNumberPosition::BottomLeft,
        PageNumberPosition::BottomCenter,
        PageNumberPosition::BottomRight,
        PageNumberPosition::OutsideTop,
        PageNumberPosition::OutsideBottom,
        PageNumberPosition::InsideTop,
        PageNumberPosition::InsideBottom,
    ];
    for position in positions {
        let mut expected = policy(Vec::new());
        if let Some(page_number) = expected.page_number.as_mut() {
            page_number.position = position;
        } else {
            panic!("fixture page number missing");
        }
        let actual = HeaderFooterReader::read_section(
            &section_xml(&expected)?,
            HeaderFooterLimits::default(),
        )?;
        assert_eq!(actual.page_number, expected.page_number);
    }
    Ok(())
}

#[test]
fn all_non_image_number_formats_roundtrip_in_page_fields() -> TestResult {
    let formats = [
        NumberFormat::Digit,
        NumberFormat::CircledDigit,
        NumberFormat::RomanCapital,
        NumberFormat::RomanSmall,
        NumberFormat::LatinCapital,
        NumberFormat::LatinSmall,
        NumberFormat::CircledLatinCapital,
        NumberFormat::CircledLatinSmall,
        NumberFormat::HangulSyllable,
        NumberFormat::CircledHangulSyllable,
        NumberFormat::HangulJamo,
        NumberFormat::CircledHangulJamo,
        NumberFormat::HangulPhonetic,
        NumberFormat::Ideograph,
        NumberFormat::CircledIdeograph,
        NumberFormat::DecagonCircle,
        NumberFormat::DecagonCircleHanja,
        NumberFormat::Symbol,
        NumberFormat::UserChar,
        NumberFormat::Symbol2,
        NumberFormat::TwoDigit,
    ];
    for format in formats {
        let mut expected = definition(HeaderFooterKind::Footer, PageVariant::Both, 1);
        let HeaderFooterInline::PageField(page_field) =
            &mut expected.body.paragraphs[0].runs[0].inlines[2]
        else {
            panic!("fixture field missing");
        };
        page_field.format = format;
        if format == NumberFormat::UserChar {
            page_field.user_character = "가".to_owned();
        }
        let (bytes, _) =
            HeaderFooterLowerer::lower_definition(&expected, HeaderFooterLimits::default())?;
        assert_eq!(
            HeaderFooterReader::read_definition(&bytes, HeaderFooterLimits::default())?,
            expected
        );
    }
    Ok(())
}

#[test]
fn master_page_variants_and_exact_links_are_closed() -> TestResult {
    let variants = [
        MasterPageVariant::Both,
        MasterPageVariant::Even,
        MasterPageVariant::Odd,
        MasterPageVariant::LastPage,
        MasterPageVariant::OptionalPage,
    ];
    let pages: Vec<_> = variants
        .into_iter()
        .enumerate()
        .map(|(index, applies_to)| MasterPageDefinition {
            id: format!("master-{index}"),
            applies_to,
            optional_page_number: (applies_to == MasterPageVariant::OptionalPage).then_some(9),
            duplicate_on_page: index % 2 == 0,
            in_front: index % 2 == 1,
            body: body(
                &format!("master-body-{index}"),
                &format!("master-p-{index}"),
                "바탕쪽",
            ),
        })
        .collect();
    let mut expected = policy(Vec::new());
    expected.master_page_references = pages.iter().map(|page| page.id.clone()).collect();
    expected.declared_master_page_count = u32::try_from(pages.len())?;
    for page in &pages {
        let (bytes, _) =
            HeaderFooterLowerer::lower_master_page(page, HeaderFooterLimits::default())?;
        assert_eq!(
            HeaderFooterReader::read_master_page(&bytes, HeaderFooterLimits::default())?,
            *page
        );
    }
    HeaderFooterReader::validate_master_pages(&expected, &pages, HeaderFooterLimits::default())?;
    assert_eq!(
        HeaderFooterReader::read_section(&section_xml(&expected)?, HeaderFooterLimits::default())?,
        expected
    );
    Ok(())
}

#[test]
fn dangling_duplicate_and_count_drift_master_pages_fail_closed() {
    let page = MasterPageDefinition {
        id: "master".to_owned(),
        applies_to: MasterPageVariant::Both,
        optional_page_number: None,
        duplicate_on_page: false,
        in_front: false,
        body: body("master-body", "master-p", "바탕쪽"),
    };
    let mut expected = policy(Vec::new());
    expected.master_page_references = vec!["missing".to_owned()];
    expected.declared_master_page_count = 1;
    assert_eq!(
        HeaderFooterReader::validate_master_pages(
            &expected,
            std::slice::from_ref(&page),
            HeaderFooterLimits::default()
        ),
        Err(HeaderFooterError::MasterPageReference)
    );
    expected.master_page_references = vec!["master".to_owned(), "master".to_owned()];
    expected.declared_master_page_count = 2;
    assert_eq!(
        HeaderFooterReader::validate_master_pages(
            &expected,
            &[page.clone(), page],
            HeaderFooterLimits::default()
        ),
        Err(HeaderFooterError::MasterPageReference)
    );
    expected.declared_master_page_count = 1;
    assert_eq!(
        HeaderFooterLowerer::lower_section_properties(&expected, HeaderFooterLimits::default()),
        Err(HeaderFooterError::MasterPageReference)
    );
}

#[test]
fn duplicate_id_or_kind_variant_never_selects_first() {
    let same_id = policy(vec![
        definition(HeaderFooterKind::Header, PageVariant::Even, 1),
        definition(HeaderFooterKind::Footer, PageVariant::Odd, 1),
    ]);
    assert_eq!(
        HeaderFooterLowerer::lower_section_controls(&same_id, HeaderFooterLimits::default()),
        Err(HeaderFooterError::DuplicateDefinition)
    );
    let same_variant = policy(vec![
        definition(HeaderFooterKind::Header, PageVariant::Even, 1),
        definition(HeaderFooterKind::Header, PageVariant::Even, 2),
    ]);
    assert_eq!(
        HeaderFooterLowerer::lower_section_controls(&same_variant, HeaderFooterLimits::default()),
        Err(HeaderFooterError::DuplicateDefinition)
    );
}

#[test]
fn exact_current_2020_section_reads_default_restart_and_visibility() -> TestResult {
    let artifact = Hancom2020Vs0Builder::build("P05-08-current-2020")?;
    let bytes = artifact.with_verified_bytes(ToOwned::to_owned)?;
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let entry = reader
        .entries()
        .iter()
        .find(|entry| entry.path.as_str() == "Contents/section0.xml")
        .ok_or("section0 missing")?
        .index;
    let section = reader.read_entry(entry)?;
    let policy = HeaderFooterReader::read_section(&section, HeaderFooterLimits::default())?;
    assert_eq!(policy.restart.page_starts_on, PageVariant::Both);
    assert_eq!(policy.restart.page, 0);
    assert_eq!(policy.first_page.header, FirstPageDisplay::Show);
    assert!(policy.definitions.is_empty());
    assert!(policy.master_page_references.is_empty());
    Ok(())
}

#[test]
fn malformed_namespace_shape_numbers_booleans_and_enums_are_distinct() -> TestResult {
    let expected = definition(HeaderFooterKind::Header, PageVariant::Both, 1);
    let (bytes, _) =
        HeaderFooterLowerer::lower_definition(&expected, HeaderFooterLimits::default())?;
    let xml = std::str::from_utf8(&bytes)?;
    let wrong_namespace = xml.replace(PARAGRAPH_NAMESPACE, "urn:wrong");
    assert_eq!(
        HeaderFooterReader::read_definition(
            wrong_namespace.as_bytes(),
            HeaderFooterLimits::default()
        ),
        Err(HeaderFooterError::WrongRoot)
    );
    let bad_number = xml.replace("id=\"1\"", "id=\"x\"");
    assert_eq!(
        HeaderFooterReader::read_definition(bad_number.as_bytes(), HeaderFooterLimits::default()),
        Err(HeaderFooterError::InvalidNumber)
    );
    let bad_boolean = xml.replace("hasNumRef=\"1\"", "hasNumRef=\"yes\"");
    assert_eq!(
        HeaderFooterReader::read_definition(bad_boolean.as_bytes(), HeaderFooterLimits::default()),
        Err(HeaderFooterError::InvalidBoolean)
    );
    let bad_enum = xml.replace("applyPageType=\"BOTH\"", "applyPageType=\"FIRST\"");
    assert_eq!(
        HeaderFooterReader::read_definition(bad_enum.as_bytes(), HeaderFooterLimits::default()),
        Err(HeaderFooterError::InvalidEnum)
    );
    let bad_shape = xml.replace("<hp:subList", "<hp:unknown");
    assert!(
        HeaderFooterReader::read_definition(bad_shape.as_bytes(), HeaderFooterLimits::default())
            .is_err()
    );
    Ok(())
}

const PARAGRAPH_NAMESPACE: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";

#[test]
fn preserving_admission_blocks_dtd_processing_instruction_and_comments() -> TestResult {
    let expected = definition(HeaderFooterKind::Header, PageVariant::Both, 1);
    let (bytes, _) =
        HeaderFooterLowerer::lower_definition(&expected, HeaderFooterLimits::default())?;
    let xml = std::str::from_utf8(&bytes)?;
    for poisoned in [
        format!("<!DOCTYPE x>{xml}"),
        format!("<?probe value?>{xml}"),
        xml.replace("<hp:t", "<!--hidden--><hp:t"),
    ] {
        assert!(
            HeaderFooterReader::read_definition(poisoned.as_bytes(), HeaderFooterLimits::default())
                .is_err()
        );
    }
    Ok(())
}

#[test]
fn finite_input_element_definition_text_and_output_limits_hold() -> TestResult {
    assert_eq!(
        HeaderFooterLimits::new(HeaderFooterLimitConfig {
            input_bytes: 0,
            ..HeaderFooterLimitConfig::default()
        }),
        Err(HeaderFooterError::InvalidLimit)
    );
    let expected = definition(HeaderFooterKind::Header, PageVariant::Both, 1);
    let (bytes, _) =
        HeaderFooterLowerer::lower_definition(&expected, HeaderFooterLimits::default())?;
    let tiny_input = HeaderFooterLimits::new(HeaderFooterLimitConfig {
        input_bytes: bytes.len() - 1,
        ..HeaderFooterLimitConfig::default()
    })?;
    assert_eq!(
        HeaderFooterReader::read_definition(&bytes, tiny_input),
        Err(HeaderFooterError::InputLimit)
    );
    let tiny_elements = HeaderFooterLimits::new(HeaderFooterLimitConfig {
        elements: 1,
        ..HeaderFooterLimitConfig::default()
    })?;
    assert_eq!(
        HeaderFooterReader::read_definition(&bytes, tiny_elements),
        Err(HeaderFooterError::ElementLimit)
    );
    let tiny_text = HeaderFooterLimits::new(HeaderFooterLimitConfig {
        text_bytes: 1,
        ..HeaderFooterLimitConfig::default()
    })?;
    assert_eq!(
        HeaderFooterLowerer::lower_definition(&expected, tiny_text),
        Err(HeaderFooterError::InvalidText)
    );
    let tiny_output = HeaderFooterLimits::new(HeaderFooterLimitConfig {
        output_bytes: 64,
        ..HeaderFooterLimitConfig::default()
    })?;
    assert_eq!(
        HeaderFooterLowerer::lower_definition(&expected, tiny_output),
        Err(HeaderFooterError::OutputLimit)
    );
    Ok(())
}

#[test]
fn image_page_field_negative_number_and_invalid_identity_fail_closed() {
    let mut expected = definition(HeaderFooterKind::Header, PageVariant::Both, 1);
    if let HeaderFooterInline::PageField(page_field) =
        &mut expected.body.paragraphs[0].runs[0].inlines[2]
    {
        page_field.format = NumberFormat::Image;
    } else {
        panic!("fixture field missing");
    }
    assert_eq!(
        HeaderFooterLowerer::lower_definition(&expected, HeaderFooterLimits::default()),
        Err(HeaderFooterError::InvalidField)
    );
    if let HeaderFooterInline::PageField(page_field) =
        &mut expected.body.paragraphs[0].runs[0].inlines[2]
    {
        page_field.format = NumberFormat::Digit;
        page_field.displayed_number = -1;
    } else {
        panic!("fixture field missing");
    }
    assert_eq!(
        HeaderFooterLowerer::lower_definition(&expected, HeaderFooterLimits::default()),
        Err(HeaderFooterError::InvalidField)
    );
    if let HeaderFooterInline::PageField(page_field) =
        &mut expected.body.paragraphs[0].runs[0].inlines[2]
    {
        page_field.displayed_number = 1;
    } else {
        panic!("fixture field missing");
    }
    expected.body.id = "private/path".to_owned();
    assert_eq!(
        HeaderFooterLowerer::lower_definition(&expected, HeaderFooterLimits::default()),
        Err(HeaderFooterError::InvalidIdentity)
    );
}

#[test]
fn public_debug_and_errors_do_not_expose_text_or_identity_values() {
    let expected = definition(HeaderFooterKind::Header, PageVariant::Both, 1);
    let debug = format!("{expected:?}");
    assert!(!debug.contains("머리말"));
    assert!(!debug.contains("body-1"));
    let error = HeaderFooterError::InvalidText;
    assert!(!format!("{error:?} {error}").contains("머리말"));
    assert!(!format!("{error:?} {error}").contains("private/path"));
}

#[test]
fn fixed_128_case_header_footer_corpus_is_deterministic() -> TestResult {
    let mut digest = Sha256::new();
    for index in 0..128_u32 {
        let kind = if index % 2 == 0 {
            HeaderFooterKind::Header
        } else {
            HeaderFooterKind::Footer
        };
        let applies_to = match index % 3 {
            0 => PageVariant::Both,
            1 => PageVariant::Even,
            _ => PageVariant::Odd,
        };
        let mut expected = definition(kind, applies_to, index + 1);
        let HeaderFooterInline::PageField(page_field) =
            &mut expected.body.paragraphs[0].runs[0].inlines[2]
        else {
            panic!("fixture field missing");
        };
        page_field.displayed_number = i32::try_from(index)?;
        page_field.superscript = index % 5 == 0;
        let (bytes, _) =
            HeaderFooterLowerer::lower_definition(&expected, HeaderFooterLimits::default())?;
        digest.update(u32::try_from(bytes.len())?.to_le_bytes());
        digest.update(bytes);
    }
    assert_eq!(
        hex::encode(digest.finalize()),
        "8a773267deaa3b10d610d2216eb4cd7e2bd421a2d47815b46a26c7337a2a840d"
    );
    Ok(())
}

#[test]
fn stable_error_codes_cover_every_failure_class() {
    let errors = [
        HeaderFooterError::InvalidLimit,
        HeaderFooterError::InputLimit,
        HeaderFooterError::ElementLimit,
        HeaderFooterError::DefinitionLimit,
        HeaderFooterError::MasterPageLimit,
        HeaderFooterError::ParagraphLimit,
        HeaderFooterError::RunLimit,
        HeaderFooterError::InlineLimit,
        HeaderFooterError::TextLimit,
        HeaderFooterError::OutputLimit,
        HeaderFooterError::WrongRoot,
        HeaderFooterError::UnsupportedShape,
        HeaderFooterError::InvalidNumber,
        HeaderFooterError::InvalidBoolean,
        HeaderFooterError::InvalidEnum,
        HeaderFooterError::InvalidIdentity,
        HeaderFooterError::InvalidText,
        HeaderFooterError::InvalidField,
        HeaderFooterError::DuplicateDefinition,
        HeaderFooterError::MasterPageReference,
        HeaderFooterError::AllocationFailed,
        HeaderFooterError::ReadbackMismatch,
    ];
    let mut codes = std::collections::BTreeSet::new();
    for error in errors {
        assert!(codes.insert(error.code()));
        assert!(error.code().starts_with("header_footer_"));
    }
}
