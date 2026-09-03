use std::error::Error;

use hwpx_package::{
    HANCOM_2020_VS1_LAYOUT_PROFILE_ID, Hancom2020Vs1LayoutBuilder, Hancom2020Vs1LayoutDocument,
};

type TestResult = Result<(), Box<dyn Error>>;

fn document() -> Result<Hancom2020Vs1LayoutDocument, Box<dyn Error>> {
    Ok(Hancom2020Vs1LayoutDocument::new(
        "분기 운영 보고서",
        vec![
            "요약은 첫째 단에 배치합니다.".to_owned(),
            "상세 내용은 둘째 단에서 시작합니다.".to_owned(),
            "마지막 단락은 저장 후에도 보존되어야 합니다.".to_owned(),
        ],
    )?)
}

#[test]
fn public_vertical_slice_builds_and_reopens() -> TestResult {
    let document = document()?;
    let artifact = Hancom2020Vs1LayoutBuilder::build(&document)?;
    assert_eq!(
        artifact.inspection().profile_id,
        HANCOM_2020_VS1_LAYOUT_PROFILE_ID
    );
    assert_eq!(artifact.inspection().paragraph_count, 4);
    assert_eq!(artifact.inspection().column_break_count, 1);
    assert_eq!(artifact.inspection().page_metrics.body_width, 80_220);
    assert_eq!(artifact.inspection().column_metrics.column_count, 2);
    artifact.verify()?;
    let inspected = artifact.with_verified_bytes(Hancom2020Vs1LayoutBuilder::inspect)??;
    assert_eq!(inspected, *artifact.inspection());
    Ok(())
}

#[test]
fn public_input_is_bounded_and_normalized() -> TestResult {
    let document = Hancom2020Vs1LayoutDocument::new(
        "Cafe\u{301}",
        vec!["첫 문단".to_owned(), "둘째 문단".to_owned()],
    )?;
    assert_eq!(document.title(), "Caf\u{e9}");
    assert_eq!(document.body_paragraphs().len(), 2);
    assert_eq!(document.paragraph_count(), 3);
    assert!(Hancom2020Vs1LayoutDocument::new("제목", vec!["한 문단만".to_owned()]).is_err());
    Ok(())
}
