use std::error::Error;

use hwpx_package::{
    PAGE_SETUP_PROFILE_ID, PageDimensions, PageGutterType, PageMargins, PageOrientation, PageSetup,
    PageSetupLimits, PageSetupLowerer, PageSetupReader,
};

type TestResult = Result<(), Box<dyn Error>>;

// Exact pagePr values from the hash-pinned P05-07 attempt21 input and saved HWPX.
// The actual 2020 PDF has portrait MediaBoxes; do not infer direction from the token's name.
const ATTEMPT21_PAGE: &str = r#"<hp:pagePr xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" landscape="WIDELY" width="65197" height="87874" gutterType="TOP_BOTTOM"><hp:margin header="2835" footer="2268" gutter="1417" left="4252" right="3402" top="5669" bottom="4252"/></hp:pagePr>"#;

fn setup(orientation: PageOrientation) -> PageSetup {
    PageSetup {
        orientation,
        dimensions: PageDimensions {
            width: 65_197,
            height: 87_874,
        },
        gutter_type: PageGutterType::TopBottom,
        margins: PageMargins {
            header: 2_835,
            footer: 2_268,
            gutter: 1_417,
            left: 4_252,
            right: 3_402,
            top: 5_669,
            bottom: 4_252,
        },
    }
}

#[test]
fn observed_2020_widely_page_is_portrait_without_swapping_stored_dimensions() -> TestResult {
    let actual = PageSetupReader::read(ATTEMPT21_PAGE.as_bytes(), PageSetupLimits::default())?;
    assert_eq!(actual, setup(PageOrientation::Portrait));
    let metrics = actual.metrics(PageSetupLimits::default())?;
    assert_eq!(
        (metrics.effective_width, metrics.effective_height),
        (65_197, 87_874)
    );
    assert_eq!((metrics.body_width, metrics.body_height), (57_543, 76_536));
    Ok(())
}

#[test]
fn portrait_writer_uses_the_observed_2020_token() -> TestResult {
    let bytes = PageSetupLowerer::lower(
        &setup(PageOrientation::Portrait),
        PageSetupLimits::default(),
    )?;
    assert_eq!(bytes, ATTEMPT21_PAGE.as_bytes());
    Ok(())
}

#[test]
fn landscape_writer_uses_narrowly_and_keeps_the_physical_sheet_basis() -> TestResult {
    let (bytes, receipt) = PageSetupLowerer::lower_with_receipt(
        &setup(PageOrientation::Landscape),
        PageSetupLimits::default(),
    )?;
    assert_eq!(
        std::str::from_utf8(&bytes)?,
        ATTEMPT21_PAGE.replace("WIDELY", "NARROWLY")
    );
    assert_eq!(
        (
            receipt.metrics.effective_width,
            receipt.metrics.effective_height
        ),
        (87_874, 65_197)
    );
    assert_eq!(
        (receipt.metrics.body_width, receipt.metrics.body_height),
        (80_220, 53_859)
    );
    assert_eq!(
        PageSetupReader::read(&bytes, PageSetupLimits::default())?,
        setup(PageOrientation::Landscape)
    );
    Ok(())
}

#[test]
fn corrected_receipts_have_a_distinct_profile_from_the_reversed_v1_mapping() {
    assert_eq!(PAGE_SETUP_PROFILE_ID, "hwpx-agent.page-setup/2");
}
