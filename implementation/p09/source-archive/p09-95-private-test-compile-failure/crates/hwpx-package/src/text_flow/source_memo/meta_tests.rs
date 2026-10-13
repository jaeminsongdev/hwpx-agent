use super::super::*;
type TestResult = Result<(), Box<dyn std::error::Error>>;
fn xml(value: &str) -> Result<PreservingXmlDocument, PreservingXmlError> {
    PreservingXmlDocument::parse(format!("<hp:p xmlns:hp='http://www.hancom.co.kr/hwpml/2011/paragraph' id='1'><hp:run><hp:ctrl><hp:fieldBegin id='42' type='MEMO'><hp:metaTag>{value}</hp:metaTag></hp:fieldBegin></hp:ctrl><hp:ctrl><hp:fieldEnd beginIDRef='42'/></hp:ctrl></hp:run></hp:p>").as_bytes())
}
#[test]
fn original_source_profile_counts_complete_meta_bytes_before_accepting_them() -> TestResult {
    let source = xml(&"X".repeat(4096))?;
    let limits = TextFlowLimits::new(TextFlowLimitConfig {
        text_bytes: 512,
        ..Default::default()
    })?;
    assert_eq!(
        TextFlowReader::read_preserving_source(&source, source.root_element(), limits).err(),
        Some(TextFlowError::TextLimit)
    );
    let admitted = TextFlowReader::read_preserving_source(
        &source,
        source.root_element(),
        TextFlowLimits::default(),
    )?;
    assert!(TextFlowLowerer::lower(&admitted, TextFlowLimits::default()).is_err());
    Ok(())
}
#[test]
fn original_source_profile_meta_is_an_item_and_cannot_bypass_finite_budget() -> TestResult {
    let source = xml("OPAQUE")?;
    let meta = source
        .elements()
        .iter()
        .position(|e| has_name(e, "metaTag"))
        .ok_or("fixture meta")?;
    let mut state = ReadState::new(TextFlowLimits::new(TextFlowLimitConfig {
        items: 1,
        runs: 1,
        field_depth: 1,
        ..Default::default()
    })?);
    state.count_item()?;
    assert_eq!(
        super::validate_payload(&source, &[meta], &mut state),
        Err(TextFlowError::ItemLimit)
    );
    Ok(())
}
