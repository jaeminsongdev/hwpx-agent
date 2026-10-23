use super::same_position;
use crate::document_import::{ImportedSourcePackage, SourceImportLimits};
use domain_ir::{DocumentId, SourceAnchorHandle};
use sha2::{Digest as _, Sha256};
use std::io::{Cursor, Write};
use zip::{CompressionMethod, ZipWriter, write::SimpleFileOptions};
type TestResult = Result<(), Box<dyn std::error::Error>>;

fn source(text: &str) -> Result<ImportedSourcePackage, Box<dyn std::error::Error>> {
    let container = br#"<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="Contents/content.hpf" media-type="application/hwpml-package+xml"/></rootfiles></container>"#;
    let opf = br#"<o:package xmlns:o="http://www.idpf.org/2007/opf/"><o:manifest><o:item id="h" href="Contents/header.xml" media-type="application/xml"/><o:item id="s0" href="Contents/section0.xml" media-type="application/xml"/><o:item id="s1" href="Contents/section1.xml" media-type="application/xml"/></o:manifest><o:spine><o:itemref idref="s0"/><o:itemref idref="s1"/></o:spine></o:package>"#;
    let section = format!(
        r#"<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"><hp:p id="0"><hp:run><hp:t>{text}</hp:t><hp:t>{text}</hp:t></hp:run></hp:p></hs:sec>"#
    );
    let mut zip = ZipWriter::new(Cursor::new(Vec::new()));
    for (path, data) in [
        ("mimetype", b"application/hwp+zip".as_slice()),
        ("version.xml", b"<version/>"),
        ("META-INF/container.xml", container),
        ("Contents/content.hpf", opf),
        ("Contents/header.xml", b"<header/>"),
        ("Contents/section0.xml", section.as_bytes()),
        ("Contents/section1.xml", section.as_bytes()),
    ] {
        zip.start_file(
            path,
            SimpleFileOptions::default().compression_method(CompressionMethod::Stored),
        )?;
        zip.write_all(data)?;
    }
    let bytes = zip.finish()?.into_inner();
    Ok(ImportedSourcePackage::import(
        &bytes,
        DocumentId::parse("value-binding")?,
        Sha256::digest(&bytes).into(),
        SourceImportLimits::default(),
    )?)
}
fn text_anchor(
    source: &ImportedSourcePackage,
    section: usize,
    text: usize,
) -> Result<SourceAnchorHandle, Box<dyn std::error::Error>> {
    let path = format!("Contents/section{section}.xml");
    let part = source
        .parts()
        .iter()
        .find(|p| p.path().as_str() == path)
        .ok_or("part")?;
    let xml = part.xml().ok_or("xml")?;
    let index = xml
        .elements()
        .iter()
        .enumerate()
        .filter(|(_, n)| n.name().local_name() == "t")
        .nth(text)
        .ok_or("text")?
        .0;
    Ok(part.element_anchor(index).ok_or("anchor")?.clone())
}
#[test]
fn source_version_hash_change_does_not_break_same_actual_position() -> TestResult {
    let before = source("42")?;
    let after = source("60001")?;
    let old = text_anchor(&before, 0, 0)?;
    let new = text_anchor(&after, 0, 0)?;
    assert_ne!(old.opaque_handle, new.opaque_handle);
    same_position(&before, &old, &after, &new)?;
    Ok(())
}
#[test]
fn equal_text_in_another_section_cannot_substitute_for_source_position() -> TestResult {
    let before = source("42")?;
    let after = source("42")?;
    assert!(
        same_position(
            &before,
            &text_anchor(&before, 0, 0)?,
            &after,
            &text_anchor(&after, 1, 0)?
        )
        .is_err()
    );
    Ok(())
}
#[test]
fn adjacent_equal_text_cannot_substitute_for_actual_element_index() -> TestResult {
    let before = source("42")?;
    let after = source("42")?;
    assert!(
        same_position(
            &before,
            &text_anchor(&before, 0, 0)?,
            &after,
            &text_anchor(&after, 0, 1)?
        )
        .is_err()
    );
    Ok(())
}
#[test]
fn anchors_must_resolve_in_their_own_whole_source_version() -> TestResult {
    let before = source("42")?;
    let after = source("60001")?;
    let old = text_anchor(&before, 0, 0)?;
    assert!(same_position(&before, &old, &after, &old).is_err());
    let mut forged = text_anchor(&after, 0, 0)?;
    forged.fingerprint_sha256[0] ^= 1;
    assert!(same_position(&before, &old, &after, &forged).is_err());
    Ok(())
}
