//! Existing original fixtures; synthetic typed output is NOT native author/time acceptance.
use hwpx_package::{
    BoundedZipReader, PackageLimits, TextFlowLimits, TextFlowReader, TextFlowWriter, WriterLimits,
    document_import::structure::review::{
        ImportedDocumentReviewBodies, ReviewBodyKind, body_output::ReviewBodyOutputError,
    },
};
use sha2::{Digest as _, Sha256};
use std::{error::Error, io::Cursor};
#[path = "support/document_import_field_fixture.rs"]
mod fixture;
type TestResult = Result<(), Box<dyn Error>>;
type Parts = Vec<(String, Vec<u8>)>;

fn paragraph(text: &str) -> String {
    format!("<hp:p id='1'><hp:run>{text}</hp:run></hp:p>")
}
fn source_body() -> String {
    "<hp:subList u:flag='opaque' textDirection='HORIZONTAL'><hp:p id='2'><hp:run><hp:t>OLD</hp:t></hp:run></hp:p></hp:subList>".into()
}
fn source() -> Result<Vec<u8>, Box<dyn Error>> {
    fixture::package(&paragraph(&format!(
        "<hp:ctrl><hp:fieldBegin id='1' type='MEMO'><hp:parameters cnt='0'/>{}<hp:metaTag>{{&quot;author&quot;:&quot;UNINTERPRETED&quot;}}</hp:metaTag></hp:fieldBegin></hp:ctrl><hp:t>VISIBLE</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='1'/></hp:ctrl><hp:hiddenComment><hp:subList><hp:p id='3'><hp:run><hp:t>HIDDEN</hp:t></hp:run></hp:p></hp:subList></hp:hiddenComment>",
        source_body()
    )))
}
fn target(id: u32) -> Result<hwpx_package::TextFlow, Box<dyn Error>> {
    Ok(TextFlowReader::read(format!("<hp:p xmlns:hp='http://www.hancom.co.kr/hwpml/2011/paragraph' id='{id}'><hp:run><hp:t>한글 &amp; &lt;새&gt; <hp:tab/><hp:lineBreak/>끝</hp:t></hp:run><hp:run><hp:t>두번째 run</hp:t></hp:run></hp:p>").as_bytes(), TextFlowLimits::default())?)
}
fn parts(bytes: &[u8]) -> Result<Parts, Box<dyn Error>> {
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let names: Vec<_> = reader.entries().iter().map(|e| e.path().clone()).collect();
    let mut result = Vec::new();
    for name in names {
        result.push((name.as_str().to_owned(), reader.read_part(name.as_str())?));
    }
    result.sort_by(|a, b| a.0.cmp(&b.0));
    Ok(result)
}
#[test]
fn complete_memo_body_output_keeps_wrapper_metadata_main_body_and_every_other_part_exact()
-> TestResult {
    let bytes = source()?;
    let forms = fixture::forms(&bytes, "body-output")?;
    let review = ImportedDocumentReviewBodies::import(&forms)?;
    let values = vec![target(10)?, target(11)?];
    let result = review.lower_body(
        &bytes,
        &review.observations()[0].marker_anchor,
        &values,
        WriterLimits::default(),
    )?;
    assert_eq!(result.receipt().kind, ReviewBodyKind::MemoField);
    assert_eq!(result.receipt().target_paragraphs, 2);
    assert!(result.receipt().outside_selected_content_exact);
    assert!(!result.receipt().native_author_time_state_verified);
    assert!(!result.receipt().execution_publication_authority);
    let output = result.with_verified_bytes(<[u8]>::to_vec)?;
    let mut replacement = String::new();
    for value in &values {
        let lowered = TextFlowWriter::lower(value, TextFlowLimits::default())?;
        replacement.push_str(
            std::str::from_utf8(&lowered)?
                .split_once("?>")
                .ok_or("decl")?
                .1,
        );
    }
    let expected = source_body().replacen(
        "<hp:p id='2'><hp:run><hp:t>OLD</hp:t></hp:run></hp:p>",
        &replacement,
        1,
    );
    for ((path, old), (other, new)) in parts(&bytes)?.iter().zip(parts(&output)?) {
        assert_eq!(path, &other);
        if path == "Contents/section0.xml" {
            assert_eq!(
                std::str::from_utf8(&new)?,
                std::str::from_utf8(old)?.replacen(&source_body(), &expected, 1)
            );
        } else {
            assert_eq!(*old, new);
        }
    }
    assert_eq!(
        Sha256::digest(&output).as_slice(),
        result.receipt().output_package_sha256
    );
    let lifted = fixture::forms(&output, "body-output")?;
    let read = ImportedDocumentReviewBodies::import(&lifted)?;
    assert_eq!(read.receipt().memo_fields, 1);
    assert_eq!(read.receipt().hidden_explanations, 1);
    assert_eq!(
        review.observations()[0]
            .meta_tag
            .as_ref()
            .ok_or("meta")?
            .element_sha256,
        read.observations()[0]
            .meta_tag
            .as_ref()
            .ok_or("meta")?
            .element_sha256
    );
    assert!(!format!("{result:?}").contains("한글"));
    Ok(())
}
#[test]
fn hidden_body_uses_same_original_writer_and_preserves_memo_body_and_metadata() -> TestResult {
    let bytes = source()?;
    let forms = fixture::forms(&bytes, "body-output")?;
    let review = ImportedDocumentReviewBodies::import(&forms)?;
    let result = review.lower_body(
        &bytes,
        &review.observations()[1].marker_anchor,
        &[target(20)?],
        WriterLimits::default(),
    )?;
    assert_eq!(result.receipt().kind, ReviewBodyKind::HiddenExplanation);
    let output = result.with_verified_bytes(<[u8]>::to_vec)?;
    let old = parts(&bytes)?
        .into_iter()
        .find(|p| p.0 == "Contents/section0.xml")
        .ok_or("part")?
        .1;
    let new = parts(&output)?
        .into_iter()
        .find(|p| p.0 == "Contents/section0.xml")
        .ok_or("part")?
        .1;
    let memo_end = std::str::from_utf8(&old)?
        .find("<hp:hiddenComment>")
        .ok_or("hidden")?;
    assert_eq!(old[..memo_end], new[..memo_end]);
    Ok(())
}
#[test]
fn stale_foreign_missing_noop_empty_unsafe_nested_and_dangling_bodies_do_not_output() -> TestResult
{
    let bytes = source()?;
    let forms = fixture::forms(&bytes, "body-output")?;
    let review = ImportedDocumentReviewBodies::import(&forms)?;
    let marker = &review.observations()[0].marker_anchor;
    assert!(
        review
            .lower_body(&[0], marker, &[target(5)?], WriterLimits::default())
            .is_err()
    );
    assert!(
        review
            .lower_body(
                &bytes,
                review.observations()[0]
                    .body_anchor
                    .as_ref()
                    .ok_or("anchor")?,
                &[target(5)?],
                WriterLimits::default()
            )
            .is_err()
    );
    assert!(
        review
            .lower_body(&bytes, marker, &[], WriterLimits::default())
            .is_err()
    );
    let original = TextFlowReader::read(b"<hp:p xmlns:hp='http://www.hancom.co.kr/hwpml/2011/paragraph' id='2'><hp:run><hp:t>OLD</hp:t></hp:run></hp:p>", TextFlowLimits::default())?;
    assert_eq!(
        review
            .lower_body(&bytes, marker, &[original], WriterLimits::default())
            .err(),
        Some(ReviewBodyOutputError::NoChange)
    );
    let mut unsafe_value = target(6)?;
    if let hwpx_package::ParagraphChild::Run(run) = &mut unsafe_value.children[0] {
        if let hwpx_package::TextRunItem::Text(span) = &mut run.items[0] {
            span.atoms = vec![hwpx_package::TextAtom::Text("bad\0text".into())];
        }
    }
    assert!(
        review
            .lower_body(&bytes, marker, &[unsafe_value], WriterLimits::default())
            .is_err()
    );
    let mut dangling = target(7)?;
    dangling.paragraph.paragraph_property_id_ref = Some(987);
    assert!(
        review
            .lower_body(&bytes, marker, &[dangling], WriterLimits::default())
            .is_err()
    );
    let nested = TextFlowReader::read(b"<hp:p xmlns:hp='http://www.hancom.co.kr/hwpml/2011/paragraph' id='8'><hp:run><hp:ctrl><hp:fieldBegin id='19' type='DATE'/></hp:ctrl><hp:ctrl><hp:fieldEnd beginIDRef='19'/></hp:ctrl></hp:run></hp:p>", TextFlowLimits::default())?;
    assert!(
        review
            .lower_body(&bytes, marker, &[nested], WriterLimits::default())
            .is_err()
    );
    Ok(())
}
