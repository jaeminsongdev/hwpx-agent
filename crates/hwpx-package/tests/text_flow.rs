use hwpx_package::{
    Hancom2020Vs0Builder, ParagraphChild, TextAtom, TextFlowError, TextFlowLimitConfig,
    TextFlowLimits, TextFlowReader, TextFlowWriter, TextRunItem,
};
use sha2::{Digest as _, Sha256};
use std::io::{Cursor, Read as _};
use zip::ZipArchive;

type TestResult = Result<(), Box<dyn std::error::Error>>;

const NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";

fn paragraph(children: &str) -> Vec<u8> {
    format!(
        r#"<?xml version="1.0" encoding="UTF-8"?><hp:p xmlns:hp="{NS}" id="7" paraPrIDRef="2" styleIDRef="3" pageBreak="0" columnBreak="0" merged="0">{children}</hp:p>"#,
    )
    .into_bytes()
}

#[test]
fn unicode_tabs_line_breaks_and_escaping_roundtrip() -> TestResult {
    let source = paragraph(concat!(
        r#"<hp:run charPrIDRef="4"><hp:t charStyleIDRef="5">"#,
        "한글 Latin 中 😀 e&#x301; &amp; &lt;",
        r#"<hp:tab width="8000" leader="4" type="3"/>"#,
        r#"<hp:lineBreak/>끝</hp:t></hp:run>"#,
    ));
    let flow = TextFlowReader::read(&source, TextFlowLimits::default())?;
    assert_eq!(flow.run_count(), 1);
    assert_eq!(flow.opaque_count(), 0);
    assert_eq!(flow.visible_text_nfc()?, "한글 Latin 中 😀 é & <\t\n끝");

    let lowered = TextFlowWriter::lower(&flow, TextFlowLimits::default())?;
    assert_eq!(
        TextFlowReader::read(&lowered, TextFlowLimits::default())?,
        flow
    );
    let lowered_text = std::str::from_utf8(&lowered)?;
    assert!(lowered_text.contains("&amp; &lt;"));
    assert!(!lowered_text.contains("e&#x301;"));
    Ok(())
}

#[test]
fn adjacent_runs_and_text_spans_are_not_merged() -> TestResult {
    let source = paragraph(concat!(
        r#"<hp:run charPrIDRef="1"><hp:t>A</hp:t><hp:t charStyleIDRef="9">B</hp:t></hp:run>"#,
        r#"<hp:run charPrIDRef="1"><hp:t>C</hp:t></hp:run>"#,
    ));
    let flow = TextFlowReader::read(&source, TextFlowLimits::default())?;
    assert_eq!(flow.run_count(), 2);
    let ParagraphChild::Run(first) = &flow.children[0] else {
        return Err("first child must be a run".into());
    };
    assert_eq!(first.items.len(), 2);
    let ParagraphChild::Run(second) = &flow.children[1] else {
        return Err("second child must be a run".into());
    };
    assert_eq!(second.items.len(), 1);
    assert_eq!(flow.visible_text_nfc()?, "ABC");
    assert_eq!(
        TextFlowReader::read(
            &TextFlowWriter::lower(&flow, TextFlowLimits::default())?,
            TextFlowLimits::default(),
        )?,
        flow
    );
    Ok(())
}

#[test]
fn nested_field_boundaries_can_cross_run_boundaries() -> TestResult {
    let source = paragraph(concat!(
        r#"<hp:run><hp:ctrl><hp:fieldBegin id="10" type="CLICK_HERE" name="outer&amp;name" editable="1" dirty="0" fieldid="100"/></hp:ctrl></hp:run>"#,
        r#"<hp:run><hp:t>앞</hp:t><hp:ctrl><hp:fieldBegin id="11" type="BOOKMARK" editable="0" dirty="1" zorder="-2"/></hp:ctrl><hp:t>안</hp:t></hp:run>"#,
        r#"<hp:run><hp:ctrl><hp:fieldEnd beginIDRef="11"/></hp:ctrl><hp:t>뒤</hp:t><hp:ctrl><hp:fieldEnd beginIDRef="10" fieldid="100"/></hp:ctrl></hp:run>"#,
    ));
    let flow = TextFlowReader::read(&source, TextFlowLimits::default())?;
    assert_eq!(flow.run_count(), 3);
    assert_eq!(flow.visible_text_nfc()?, "앞안뒤");
    assert_eq!(flow.opaque_count(), 0);
    let lowered = TextFlowWriter::lower(&flow, TextFlowLimits::default())?;
    assert_eq!(
        TextFlowReader::read(&lowered, TextFlowLimits::default())?,
        flow
    );
    assert!(!format!("{flow:?}").contains("outer&name"));
    Ok(())
}

#[test]
fn field_mismatch_duplicate_unclosed_and_depth_fail_closed() -> TestResult {
    let mismatch = paragraph(concat!(
        r#"<hp:run><hp:ctrl><hp:fieldBegin id="1" type="DATE"/></hp:ctrl>"#,
        r#"<hp:ctrl><hp:fieldEnd beginIDRef="2"/></hp:ctrl></hp:run>"#,
    ));
    assert_eq!(
        TextFlowReader::read(&mismatch, TextFlowLimits::default()),
        Err(TextFlowError::FieldMismatch)
    );

    let duplicate = paragraph(concat!(
        r#"<hp:run><hp:ctrl><hp:fieldBegin id="1" type="DATE"/></hp:ctrl>"#,
        r#"<hp:ctrl><hp:fieldEnd beginIDRef="1"/></hp:ctrl>"#,
        r#"<hp:ctrl><hp:fieldBegin id="1" type="DATE"/></hp:ctrl></hp:run>"#,
    ));
    assert_eq!(
        TextFlowReader::read(&duplicate, TextFlowLimits::default()),
        Err(TextFlowError::DuplicateField)
    );

    let unclosed =
        paragraph(r#"<hp:run><hp:ctrl><hp:fieldBegin id="1" type="DATE"/></hp:ctrl></hp:run>"#);
    assert_eq!(
        TextFlowReader::read(&unclosed, TextFlowLimits::default()),
        Err(TextFlowError::UnclosedField)
    );

    let shallow = TextFlowLimits::new(TextFlowLimitConfig {
        field_depth: 1,
        ..TextFlowLimitConfig::default()
    })?;
    let nested = paragraph(concat!(
        r#"<hp:run><hp:ctrl><hp:fieldBegin id="1" type="DATE"/></hp:ctrl>"#,
        r#"<hp:ctrl><hp:fieldBegin id="2" type="DATE"/></hp:ctrl></hp:run>"#,
    ));
    assert_eq!(
        TextFlowReader::read(&nested, shallow),
        Err(TextFlowError::FieldDepth)
    );
    Ok(())
}

#[test]
fn unsupported_content_is_opaque_and_never_normalized() -> TestResult {
    let source = paragraph(concat!(
        r#"<hp:run><hp:secPr id=""/><hp:t>secret-body-9381</hp:t></hp:run>"#,
        r#"<hp:linesegarray><hp:lineseg textpos="0"/></hp:linesegarray>"#,
    ));
    let flow = TextFlowReader::read(&source, TextFlowLimits::default())?;
    assert_eq!(flow.visible_text_nfc()?, "secret-body-9381");
    assert_eq!(flow.opaque_count(), 2);
    assert_eq!(
        TextFlowWriter::lower(&flow, TextFlowLimits::default()),
        Err(TextFlowError::OpaqueLoweringForbidden)
    );
    let debug = format!("{flow:?}");
    assert!(!debug.contains("secret-body-9381"));
    assert!(!debug.contains("textpos"));
    Ok(())
}

#[test]
fn potentially_visible_opaque_content_blocks_semantic_text() -> TestResult {
    let source = paragraph(concat!(
        r#"<hp:run><hp:t>typed</hp:t></hp:run>"#,
        r#"<hp:unknown><hp:t>opaque-secret-1742</hp:t></hp:unknown>"#,
    ));
    let flow = TextFlowReader::read(&source, TextFlowLimits::default())?;
    assert_eq!(
        flow.visible_text_nfc(),
        Err(TextFlowError::OpaqueSemanticForbidden)
    );
    let ParagraphChild::Opaque(opaque) = &flow.children[1] else {
        return Err("second child must be opaque".into());
    };
    assert!(opaque.may_contain_visible_text());
    assert!(!format!("{flow:?}").contains("opaque-secret-1742"));

    let disguised_layout = paragraph(concat!(
        r#"<hp:run><hp:secPr><hp:t>layout-secret-2841</hp:t></hp:secPr>"#,
        r#"<hp:t>typed</hp:t></hp:run>"#,
    ));
    let flow = TextFlowReader::read(&disguised_layout, TextFlowLimits::default())?;
    assert_eq!(
        flow.visible_text_nfc(),
        Err(TextFlowError::OpaqueSemanticForbidden)
    );
    assert!(!format!("{flow:?}").contains("layout-secret-2841"));
    Ok(())
}

#[test]
fn invalid_profile_attributes_text_tabs_and_fields_are_distinct() {
    let cases = [
        (
            paragraph(r#"<hp:run extra="1"><hp:t>x</hp:t></hp:run>"#),
            TextFlowError::UnsupportedShape,
        ),
        (
            paragraph(r#"<hp:run charPrIDRef="-1"><hp:t>x</hp:t></hp:run>"#),
            TextFlowError::InvalidNumber,
        ),
        (
            paragraph(
                r#"<hp:run><hp:t><hp:tab width="1" leader="0" type="MIDDLE"/></hp:t></hp:run>"#,
            ),
            TextFlowError::InvalidTab,
        ),
        (
            paragraph(
                r#"<hp:run><hp:ctrl><hp:fieldBegin id="1" type="UNKNOWN"/></hp:ctrl></hp:run>"#,
            ),
            TextFlowError::InvalidField,
        ),
    ];
    for (source, expected) in cases {
        assert_eq!(
            TextFlowReader::read(&source, TextFlowLimits::default()),
            Err(expected)
        );
    }

    let wrong_namespace = br#"<hp:p xmlns:hp="urn:not-hwpx" id="1"><hp:run/></hp:p>"#;
    assert_eq!(
        TextFlowReader::read(wrong_namespace, TextFlowLimits::default()),
        Err(TextFlowError::WrongRoot)
    );
}

#[test]
fn finite_limits_reject_before_partial_flow_or_output() -> TestResult {
    assert_eq!(
        TextFlowLimits::new(TextFlowLimitConfig {
            runs: 0,
            ..TextFlowLimitConfig::default()
        }),
        Err(TextFlowError::InvalidLimit)
    );
    let one_run = paragraph(r"<hp:run><hp:t>bounded</hp:t></hp:run>");
    let run_limit = TextFlowLimits::new(TextFlowLimitConfig {
        runs: 1,
        ..TextFlowLimitConfig::default()
    })?;
    assert_eq!(
        TextFlowReader::read(&paragraph(r"<hp:run/><hp:run/>"), run_limit),
        Err(TextFlowError::RunLimit)
    );
    let tiny_input = TextFlowLimits::new(TextFlowLimitConfig {
        input_bytes: 128,
        text_bytes: 64,
        runs: 1,
        items: 2,
        field_depth: 1,
    })?;
    assert_eq!(
        TextFlowReader::read(&one_run, tiny_input),
        Err(TextFlowError::InputLimit)
    );
    let element_limit = TextFlowLimits::new(TextFlowLimitConfig {
        runs: 1,
        items: 4,
        field_depth: 1,
        ..TextFlowLimitConfig::default()
    })?;
    assert_eq!(
        TextFlowReader::read(
            &paragraph(r"<hp:run><hp:unknown><hp:a/><hp:b/></hp:unknown></hp:run>"),
            element_limit,
        ),
        Err(TextFlowError::ItemLimit)
    );
    Ok(())
}

#[test]
fn nonsemantic_document_envelope_is_not_silently_discarded() {
    let source = format!(
        r#"<!--outside--><hp:p xmlns:hp="{NS}" id="7"><hp:run><hp:t>x</hp:t></hp:run></hp:p>"#
    );
    assert_eq!(
        TextFlowReader::read(source.as_bytes(), TextFlowLimits::default()),
        Err(TextFlowError::UnsupportedShape)
    );
}

#[test]
fn writer_revalidates_publicly_mutable_text_and_fields() -> TestResult {
    let source = paragraph(r"<hp:run><hp:t>safe</hp:t></hp:run>");
    let mut flow = TextFlowReader::read(&source, TextFlowLimits::default())?;
    let ParagraphChild::Run(run) = &mut flow.children[0] else {
        return Err("expected run".into());
    };
    let TextRunItem::Text(span) = &mut run.items[0] else {
        return Err("expected text".into());
    };
    span.atoms[0] = TextAtom::Text("bad\ntext".to_owned());
    assert_eq!(
        TextFlowWriter::lower(&flow, TextFlowLimits::default()),
        Err(TextFlowError::InvalidText)
    );
    Ok(())
}

#[test]
fn fixed_unicode_run_boundary_corpus_is_deterministic() -> TestResult {
    let mut aggregate = Sha256::new();
    for index in 0..128_u32 {
        let source = paragraph(&format!(
            "<hp:run charPrIDRef=\"{}\"><hp:t>한글-{index}-中-😀</hp:t></hp:run><hp:run charPrIDRef=\"{}\"><hp:t>e&#x301;<hp:tab width=\"{}\" leader=\"{}\" type=\"{}\"/><hp:lineBreak/>끝</hp:t></hp:run>",
            index % 7,
            (index + 1) % 7,
            1000 + index,
            index % 12,
            index % 4,
        ));
        let flow = TextFlowReader::read(&source, TextFlowLimits::default())?;
        let first = TextFlowWriter::lower(&flow, TextFlowLimits::default())?;
        let second = TextFlowWriter::lower(&flow, TextFlowLimits::default())?;
        assert_eq!(first, second);
        assert_eq!(
            TextFlowReader::read(&first, TextFlowLimits::default())?,
            flow
        );
        aggregate.update(Sha256::digest(&first));
    }
    assert_eq!(
        hex::encode(aggregate.finalize()),
        "947426874dd0f0e5680934cfdad687e01c23edb9f8126eeb942fe6245e11188b"
    );
    Ok(())
}

#[test]
fn current_2020_vs0_paragraph_lifts_text_without_promoting_layout() -> TestResult {
    let expected = "2020 구조 lift 검증";
    let artifact = Hancom2020Vs0Builder::build(expected)?;
    let bytes = artifact.with_verified_bytes(ToOwned::to_owned)?;
    let mut archive = ZipArchive::new(Cursor::new(bytes))?;
    let mut section = String::new();
    archive
        .by_name("Contents/section0.xml")?
        .read_to_string(&mut section)?;
    let start = section.find("<hp:p ").ok_or("paragraph start missing")?;
    let end = section.find("</hp:p>").ok_or("paragraph end missing")? + "</hp:p>".len();
    let fragment = section[start..end].replacen("<hp:p ", &format!("<hp:p xmlns:hp=\"{NS}\" "), 1);
    let flow = TextFlowReader::read(fragment.as_bytes(), TextFlowLimits::default())?;
    assert_eq!(flow.run_count(), 2);
    assert_eq!(flow.visible_text_nfc()?, expected);
    assert_eq!(flow.opaque_count(), 3);
    assert_eq!(
        TextFlowWriter::lower(&flow, TextFlowLimits::default()),
        Err(TextFlowError::OpaqueLoweringForbidden)
    );
    Ok(())
}
