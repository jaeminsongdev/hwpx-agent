use std::error::Error;

use hwpx_package::{
    COLUMN_PROFILE_ID, SectionColumnError, SectionColumnLimitConfig, SectionColumnLimits,
    SectionColumnLowerer, SectionColumnReader,
};
use sha2::{Digest as _, Sha256};

type TestResult = Result<(), Box<dyn Error>>;
const HEAD_NS: &str = "http://www.hancom.co.kr/hwpml/2011/head";
const SECTION: &str = r#"<s:sec xmlns:s="http://www.hancom.co.kr/hwpml/2011/section" xmlns:p="http://www.hancom.co.kr/hwpml/2011/paragraph"><p:p><p:run><p:secPr/><p:ctrl><p:colPr id="" type="NEWSPAPER" layout="LEFT" colCount="1" sameSz="1" sameGap="0"/></p:ctrl></p:run></p:p></s:sec>"#;

fn header(count: &str) -> String {
    format!(r#"<h:head xmlns:h="{HEAD_NS}" version="1.4" secCnt="{count}"/>"#)
}

#[test]
fn header_count_is_namespace_aware_and_bounded() -> TestResult {
    let limits = SectionColumnLimits::default();
    for count in [1, 2, 12, limits.config().sections] {
        assert_eq!(
            SectionColumnReader::read_header_section_count(
                header(&count.to_string()).as_bytes(),
                limits
            )?,
            count
        );
    }
    let default_namespace = format!(r#"<head xmlns="{HEAD_NS}" secCnt='&#50;'/>"#);
    assert_eq!(
        SectionColumnReader::read_header_section_count(default_namespace.as_bytes(), limits)?,
        2
    );
    Ok(())
}

#[test]
fn stale_header_cannot_qualify_a_multi_section_sequence() -> TestResult {
    let limits = SectionColumnLimits::default();
    let inputs = [(SECTION.as_bytes(), 42_520), (SECTION.as_bytes(), 42_520)];
    assert_eq!(
        SectionColumnReader::read_sequence(&inputs, limits)?
            .sections
            .len(),
        2
    );
    assert_eq!(
        SectionColumnReader::read_sequence_with_header(header("1").as_bytes(), &inputs, limits),
        Err(SectionColumnError::SectionCountMismatch),
    );
    let sequence =
        SectionColumnReader::read_sequence_with_header(header("2").as_bytes(), &inputs, limits)?;
    assert_eq!(sequence.sections.len(), 2);
    assert_eq!(sequence.section_break_count(), 1);
    assert_eq!(
        SectionColumnReader::read_sequence_with_header(header("3").as_bytes(), &inputs, limits),
        Err(SectionColumnError::SectionCountMismatch),
    );
    // A contradictory count is rejected before attempting to parse any section.
    assert_eq!(
        SectionColumnReader::read_sequence_with_header(
            header("1").as_bytes(),
            &[(b"invalid", 1), (b"invalid", 1)],
            limits
        ),
        Err(SectionColumnError::SectionCountMismatch),
    );
    Ok(())
}

#[test]
fn header_update_preserves_all_bytes_outside_the_count_and_binds_receipt() -> TestResult {
    let limits = SectionColumnLimits::default();
    let source = format!(
        "\u{feff}<?xml version='1.0'?>\r\n<h:head xmlns:h='{HEAD_NS}' version='1.4' secCnt = '&#49;' ><h:refList><!-- secCnt='1' --><h:font face='한글 &amp; serif'/></h:refList></h:head>\r\n"
    );
    let (output, receipt) =
        SectionColumnLowerer::replace_header_section_count(source.as_bytes(), 1, 12, limits)?;
    let expected = source.replacen("secCnt = '&#49;'", "secCnt = '12'", 1);
    assert_eq!(output, expected.as_bytes());
    assert_eq!(
        &output[..receipt.replaced_start],
        &source.as_bytes()[..receipt.replaced_start]
    );
    assert_eq!(
        &output[receipt.replaced_start + 2..],
        &source.as_bytes()[receipt.replaced_end..]
    );
    assert_eq!(receipt.profile_id, COLUMN_PROFILE_ID);
    assert_eq!(
        receipt.source_sha256,
        <[u8; 32]>::from(Sha256::digest(source.as_bytes()))
    );
    assert_eq!(
        receipt.output_sha256,
        <[u8; 32]>::from(Sha256::digest(&output))
    );
    assert_eq!(receipt.output_bytes, output.len());
    assert_eq!((receipt.previous_count, receipt.section_count), (1, 12));
    assert_eq!(
        SectionColumnReader::read_header_section_count(&output, limits)?,
        12
    );
    let repeat =
        SectionColumnLowerer::replace_header_section_count(source.as_bytes(), 1, 12, limits)?;
    assert_eq!(repeat, (output, receipt));
    Ok(())
}

#[test]
fn header_update_rejects_stale_precondition_and_invalid_target_without_mutation() {
    let limits = SectionColumnLimits::default();
    let source = header("2");
    let original = source.clone();
    assert_eq!(
        SectionColumnLowerer::replace_header_section_count(source.as_bytes(), 1, 3, limits),
        Err(SectionColumnError::SectionCountMismatch)
    );
    for target in [0, limits.config().sections + 1, usize::MAX] {
        assert_eq!(
            SectionColumnLowerer::replace_header_section_count(
                source.as_bytes(),
                2,
                target,
                limits
            ),
            Err(SectionColumnError::SectionLimit)
        );
    }
    assert_eq!(source, original);
}

#[test]
fn invalid_or_ambiguous_header_count_is_rejected() {
    let limits = SectionColumnLimits::default();
    for count in [
        "",
        "-1",
        "+2",
        "2.0",
        " 2",
        "2 ",
        "two",
        "18446744073709551616",
        "0",
        "4097",
    ] {
        assert!(
            SectionColumnReader::read_header_section_count(header(count).as_bytes(), limits)
                .is_err(),
            "count {count}"
        );
    }
    let documents = [
        header("2").replace(HEAD_NS, "urn:foreign"),
        header("2").replace("h:head", "h:refList"),
        header("2").replace(" secCnt=\"2\"", ""),
        header("2").replace("secCnt=\"2\"", "h:secCnt=\"2\""),
        header("2").replace("secCnt=\"2\"", "secCnt=\"2\" h:secCnt=\"1\""),
        header("2").replace("secCnt=\"2\"", "secCnt=\"2\" secCnt=\"1\""),
        format!(r#"<h:head xmlns:h="{HEAD_NS}"><h:child secCnt="2"/></h:head>"#),
        format!("{}{}", header("2"), header("2")),
        format!("<!DOCTYPE head [<!ENTITY count '2'>]>{}", header("&count;")),
    ];
    for document in documents {
        assert!(
            SectionColumnReader::read_header_section_count(document.as_bytes(), limits).is_err()
        );
        assert!(
            SectionColumnLowerer::replace_header_section_count(document.as_bytes(), 2, 3, limits)
                .is_err()
        );
    }
}

#[test]
fn header_sequence_admission_still_rejects_bad_sections_and_empty_sequences() {
    let limits = SectionColumnLimits::default();
    assert_eq!(
        SectionColumnReader::read_sequence_with_header(header("1").as_bytes(), &[], limits),
        Err(SectionColumnError::SectionLimit)
    );
    assert!(
        SectionColumnReader::read_sequence_with_header(
            header("1").as_bytes(),
            &[(b"invalid", 42_520)],
            limits
        )
        .is_err()
    );
    assert!(
        SectionColumnReader::read_sequence_with_header(
            header("1").as_bytes(),
            &[(SECTION.as_bytes(), 0)],
            limits
        )
        .is_err()
    );
}

#[test]
fn header_count_respects_input_element_section_and_output_limits() -> TestResult {
    let source = header("1");
    let limits = SectionColumnLimits::new(SectionColumnLimitConfig {
        input_bytes: source.len() - 1,
        ..Default::default()
    })?;
    assert_eq!(
        SectionColumnReader::read_header_section_count(source.as_bytes(), limits),
        Err(SectionColumnError::InputLimit)
    );
    let limits = SectionColumnLimits::new(SectionColumnLimitConfig {
        sections: 1,
        ..Default::default()
    })?;
    assert_eq!(
        SectionColumnReader::read_header_section_count(header("2").as_bytes(), limits),
        Err(SectionColumnError::SectionLimit)
    );
    let limits = SectionColumnLimits::new(SectionColumnLimitConfig {
        output_bytes: source.len(),
        ..Default::default()
    })?;
    assert_eq!(
        SectionColumnLowerer::replace_header_section_count(source.as_bytes(), 1, 10, limits),
        Err(SectionColumnError::OutputLimit)
    );
    let limits = SectionColumnLimits::new(SectionColumnLimitConfig {
        elements: 1,
        ..Default::default()
    })?;
    let nested = source.replace("/>", "><h:refList/></h:head>");
    assert_eq!(
        SectionColumnReader::read_header_section_count(nested.as_bytes(), limits),
        Err(SectionColumnError::ElementLimit)
    );
    Ok(())
}

#[test]
fn count_mismatch_has_a_stable_public_error_code() {
    assert_eq!(
        SectionColumnError::SectionCountMismatch.code(),
        "section_columns_section_count_mismatch"
    );
}
