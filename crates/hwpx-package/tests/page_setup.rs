use std::error::Error;

use hwpx_package::{
    PAGE_SETUP_PROFILE_ID, PageDimensions, PageGutterType, PageMargins, PageOrientation,
    PagePreset, PageSetup, PageSetupError, PageSetupLimitConfig, PageSetupLimits, PageSetupLowerer,
    PageSetupReader,
};
use sha2::{Digest as _, Sha256};

type TestResult = Result<(), Box<dyn Error>>;

const PAGE: &str = r#"<hp:pagePr xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" landscape="WIDELY" width="59528" height="84186" gutterType="LEFT_ONLY"><hp:margin header="4252" footer="4252" gutter="0" left="8504" right="8504" top="5668" bottom="4252"/></hp:pagePr>"#;
const SECTION: &str = r#"<?xml version="1.0" encoding="UTF-8"?><hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"><hp:p id="p"><hp:run><hp:secPr id=""><hp:grid lineGrid="0"/><hp:pagePr landscape="WIDELY" width="59528" height="84186" gutterType="LEFT_ONLY"><hp:margin header="4252" footer="4252" gutter="0" left="8504" right="8504" top="5668" bottom="4252"/></hp:pagePr><hp:startNum page="0"/></hp:secPr></hp:run></hp:p></hs:sec>"#;

fn margins() -> PageMargins {
    PageMargins {
        header: 4_252,
        footer: 4_252,
        gutter: 0,
        left: 8_504,
        right: 8_504,
        top: 5_668,
        bottom: 4_252,
    }
}

fn a4_portrait() -> PageSetup {
    PageSetup {
        orientation: PageOrientation::Portrait,
        dimensions: PageDimensions {
            width: 59_528,
            height: 84_186,
        },
        gutter_type: PageGutterType::LeftOnly,
        margins: margins(),
    }
}

#[test]
fn exact_current_2020_page_setup_lifts_with_checked_metrics() -> TestResult {
    let setup = PageSetupReader::read(PAGE.as_bytes(), PageSetupLimits::default())?;
    assert_eq!(setup.orientation, PageOrientation::Landscape);
    assert_eq!(setup.dimensions.width, 59_528);
    assert_eq!(setup.dimensions.height, 84_186);
    assert_eq!(setup.gutter_type, PageGutterType::LeftOnly);
    assert_eq!(setup.margins, margins());
    let metrics = setup.metrics(PageSetupLimits::default())?;
    assert_eq!(metrics.effective_width, 84_186);
    assert_eq!(metrics.effective_height, 59_528);
    assert_eq!(metrics.body_width, 67_178);
    assert_eq!(metrics.body_height, 49_608);
    assert_eq!(
        PageSetupReader::read(SECTION.as_bytes(), PageSetupLimits::default())?,
        setup
    );
    Ok(())
}

#[test]
fn presets_and_custom_mm_are_deterministic_unrotated_dimensions() -> TestResult {
    let cases = [
        (PagePreset::A3, 84_189, 119_055),
        (PagePreset::A4, 59_528, 84_189),
        (PagePreset::A5, 41_953, 59_528),
        (PagePreset::B4Iso, 70_866, 100_063),
        (PagePreset::B4Jis, 72_850, 103_181),
        (PagePreset::B5Iso, 49_890, 70_866),
        (PagePreset::B5Jis, 51_591, 72_850),
        (PagePreset::Letter, 61_200, 79_200),
        (PagePreset::Legal, 61_200, 100_800),
        (PagePreset::Tabloid, 79_200, 122_400),
    ];
    for (preset, width, height) in cases {
        assert_eq!(preset.dimensions()?, PageDimensions { width, height });
    }
    assert_eq!(
        PageDimensions::from_milli_mm(210_000, 297_000)?,
        PagePreset::A4.dimensions()?
    );
    assert_eq!(
        PageDimensions::from_milli_mm(297_000, 210_000),
        Err(PageSetupError::PaperSizeInvalid)
    );
    Ok(())
}

#[test]
fn lower_is_deterministic_and_exactly_readable() -> TestResult {
    let setup = a4_portrait();
    let (first, first_receipt) =
        PageSetupLowerer::lower_with_receipt(&setup, PageSetupLimits::default())?;
    let (second, second_receipt) =
        PageSetupLowerer::lower_with_receipt(&setup, PageSetupLimits::default())?;
    assert_eq!(first, second);
    assert_eq!(first_receipt, second_receipt);
    assert_eq!(first_receipt.profile_id, PAGE_SETUP_PROFILE_ID);
    assert_eq!(first_receipt.output_bytes, first.len());
    assert_eq!(
        PageSetupReader::read(&first, PageSetupLimits::default())?,
        setup
    );
    assert_eq!(
        std::str::from_utf8(&first)?,
        r#"<hp:pagePr xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" landscape="NARROWLY" width="59528" height="84186" gutterType="LEFT_ONLY"><hp:margin header="4252" footer="4252" gutter="0" left="8504" right="8504" top="5668" bottom="4252"/></hp:pagePr>"#
    );
    Ok(())
}

#[test]
fn section_replacement_changes_only_the_page_pr_span() -> TestResult {
    let source = SECTION.as_bytes().to_vec();
    let mut changed = a4_portrait();
    changed.dimensions = PagePreset::Letter.dimensions()?;
    changed.margins.gutter = 567;
    changed.gutter_type = PageGutterType::LeftRight;
    let (output, receipt) =
        PageSetupLowerer::replace_in_section(&source, &changed, PageSetupLimits::default())?;
    assert_eq!(source, SECTION.as_bytes());
    assert_eq!(
        &output[..receipt.replaced_start],
        &source[..receipt.replaced_start]
    );
    let old_tail = &source[receipt.replaced_end..];
    assert!(output.ends_with(old_tail));
    assert_ne!(receipt.source_sha256, receipt.output_sha256);
    assert_eq!(receipt.profile_id, PAGE_SETUP_PROFILE_ID);
    assert_eq!(
        PageSetupReader::read(&output, PageSetupLimits::default())?,
        changed
    );
    Ok(())
}

#[test]
fn impossible_paper_margin_and_header_footer_layouts_fail_closed() {
    let mut setup = a4_portrait();
    setup.dimensions.width = 0;
    assert_eq!(
        setup.metrics(PageSetupLimits::default()),
        Err(PageSetupError::PaperSizeInvalid)
    );
    setup = a4_portrait();
    setup.margins.left = setup.dimensions.width;
    assert_eq!(
        setup.metrics(PageSetupLimits::default()),
        Err(PageSetupError::MarginExceedsPaper)
    );
    setup = a4_portrait();
    setup.margins.header = setup.margins.top + 1;
    assert_eq!(
        setup.metrics(PageSetupLimits::default()),
        Err(PageSetupError::HeaderFooterInvalid)
    );
    setup = a4_portrait();
    setup.gutter_type = PageGutterType::TopBottom;
    setup.margins.gutter = setup.dimensions.height;
    assert_eq!(
        setup.metrics(PageSetupLimits::default()),
        Err(PageSetupError::MarginExceedsPaper)
    );
}

#[test]
fn gutter_axis_is_explicit_and_never_double_subtracted() -> TestResult {
    let mut setup = a4_portrait();
    setup.margins.gutter = 1_000;
    let left_only = setup.metrics(PageSetupLimits::default())?;
    setup.gutter_type = PageGutterType::LeftRight;
    let facing = setup.metrics(PageSetupLimits::default())?;
    assert_eq!(left_only, facing);
    setup.gutter_type = PageGutterType::TopBottom;
    let top = setup.metrics(PageSetupLimits::default())?;
    assert_eq!(top.body_width, left_only.body_width + 1_000);
    assert_eq!(top.body_height + 1_000, left_only.body_height);
    Ok(())
}

#[test]
fn malformed_namespace_shape_number_and_enum_are_distinct() {
    assert!(matches!(
        PageSetupReader::read(
            PAGE.replace("2011/paragraph", "2011/head").as_bytes(),
            PageSetupLimits::default()
        ),
        Err(PageSetupError::WrongRoot)
    ));
    assert_eq!(
        PageSetupReader::read(
            PAGE.replace(
                " gutterType=\"LEFT_ONLY\"",
                " extra=\"1\" gutterType=\"LEFT_ONLY\""
            )
            .as_bytes(),
            PageSetupLimits::default()
        ),
        Err(PageSetupError::UnsupportedShape)
    );
    assert_eq!(
        PageSetupReader::read(
            PAGE.replace("width=\"59528\"", "width=\"-1\"").as_bytes(),
            PageSetupLimits::default()
        ),
        Err(PageSetupError::InvalidNumber)
    );
    assert_eq!(
        PageSetupReader::read(
            PAGE.replace("WIDELY", "SIDEWAYS").as_bytes(),
            PageSetupLimits::default()
        ),
        Err(PageSetupError::InvalidEnum)
    );
}

#[test]
fn duplicate_missing_or_nested_margin_and_duplicate_page_pr_reject() {
    assert_eq!(
        PageSetupReader::read(
            PAGE.replace(" height=\"84186\"", "").as_bytes(),
            PageSetupLimits::default()
        ),
        Err(PageSetupError::UnsupportedShape)
    );
    assert_eq!(
        PageSetupReader::read(
            PAGE.replace("<hp:margin", "<hp:margin><hp:x/></hp:margin><hp:margin")
                .as_bytes(),
            PageSetupLimits::default()
        ),
        Err(PageSetupError::UnsupportedShape)
    );
    let duplicate = SECTION.replace("<hp:startNum", &format!("{PAGE}<hp:startNum"));
    assert_eq!(
        PageSetupReader::read(duplicate.as_bytes(), PageSetupLimits::default()),
        Err(PageSetupError::UnsupportedShape)
    );
    let duplicate_sec_pr = SECTION.replace("</hp:run>", "<hp:secPr><hp:grid/></hp:secPr></hp:run>");
    assert_eq!(
        PageSetupReader::read(duplicate_sec_pr.as_bytes(), PageSetupLimits::default()),
        Err(PageSetupError::UnsupportedShape)
    );
}

#[test]
fn finite_input_element_output_and_dimension_limits_are_enforced() -> TestResult {
    let tiny_input = PageSetupLimits::new(PageSetupLimitConfig {
        input_bytes: 8,
        ..PageSetupLimitConfig::default()
    })?;
    assert_eq!(
        PageSetupReader::read(PAGE.as_bytes(), tiny_input),
        Err(PageSetupError::InputLimit)
    );
    let tiny_elements = PageSetupLimits::new(PageSetupLimitConfig {
        elements: 1,
        ..PageSetupLimitConfig::default()
    })?;
    assert_eq!(
        PageSetupReader::read(PAGE.as_bytes(), tiny_elements),
        Err(PageSetupError::ElementLimit)
    );
    let tiny_output = PageSetupLimits::new(PageSetupLimitConfig {
        output_bytes: 8,
        ..PageSetupLimitConfig::default()
    })?;
    assert_eq!(
        PageSetupLowerer::lower(&a4_portrait(), tiny_output),
        Err(PageSetupError::OutputLimit)
    );
    let tiny_dimension = PageSetupLimits::new(PageSetupLimitConfig {
        max_hwpunit: 50_000,
        ..PageSetupLimitConfig::default()
    })?;
    assert_eq!(
        a4_portrait().metrics(tiny_dimension),
        Err(PageSetupError::PaperSizeInvalid)
    );
    Ok(())
}

#[test]
fn stable_error_codes_cover_every_failure_class() {
    let errors = [
        PageSetupError::InvalidLimit,
        PageSetupError::InputLimit,
        PageSetupError::ElementLimit,
        PageSetupError::WrongRoot,
        PageSetupError::UnsupportedShape,
        PageSetupError::InvalidNumber,
        PageSetupError::InvalidEnum,
        PageSetupError::PaperSizeInvalid,
        PageSetupError::MarginExceedsPaper,
        PageSetupError::HeaderFooterInvalid,
        PageSetupError::OutputLimit,
        PageSetupError::ArithmeticOverflow,
        PageSetupError::AllocationFailed,
        PageSetupError::ReadbackMismatch,
    ];
    for error in errors {
        assert!(error.code().starts_with("page_setup_"));
        assert!(!format!("{error:?}").contains("59528"));
    }
}

#[test]
fn invalid_limit_configuration_rejects() {
    assert_eq!(
        PageSetupLimits::new(PageSetupLimitConfig {
            input_bytes: 0,
            ..PageSetupLimitConfig::default()
        }),
        Err(PageSetupError::InvalidLimit)
    );
    assert_eq!(
        PageSetupLimits::new(PageSetupLimitConfig {
            max_hwpunit: PageSetupLimits::HARD_MAX_HWPUNIT + 1,
            ..PageSetupLimitConfig::default()
        }),
        Err(PageSetupError::InvalidLimit)
    );
}

#[test]
fn fixed_128_case_page_setup_corpus_is_deterministic() -> TestResult {
    let presets = [
        PagePreset::A3,
        PagePreset::A4,
        PagePreset::A5,
        PagePreset::B4Iso,
        PagePreset::B4Jis,
        PagePreset::B5Iso,
        PagePreset::B5Jis,
        PagePreset::Letter,
        PagePreset::Legal,
        PagePreset::Tabloid,
    ];
    let mut aggregate = Sha256::new();
    for case in 0_u32..128 {
        let preset_index = usize::try_from(case % u32::try_from(presets.len())?)?;
        let gutter_type = match case % 3 {
            0 => PageGutterType::LeftOnly,
            1 => PageGutterType::LeftRight,
            _ => PageGutterType::TopBottom,
        };
        let setup = PageSetup::from_preset(
            presets[preset_index],
            if case % 2 == 0 {
                PageOrientation::Portrait
            } else {
                PageOrientation::Landscape
            },
            gutter_type,
            PageMargins {
                header: 1_000 + case,
                footer: 900 + case,
                gutter: case * 7,
                left: 3_000 + case * 3,
                right: 3_100 + case * 2,
                top: 4_000 + case * 4,
                bottom: 3_900 + case * 5,
            },
            PageSetupLimits::default(),
        )?;
        let bytes = PageSetupLowerer::lower(&setup, PageSetupLimits::default())?;
        aggregate.update(u64::try_from(bytes.len())?.to_le_bytes());
        aggregate.update(bytes);
    }
    assert_eq!(
        hex::encode(aggregate.finalize()),
        "415b0a465a046f89d88481c3a9f8518e430517bbe3b46cb3564bc942ffbebc00"
    );
    Ok(())
}
