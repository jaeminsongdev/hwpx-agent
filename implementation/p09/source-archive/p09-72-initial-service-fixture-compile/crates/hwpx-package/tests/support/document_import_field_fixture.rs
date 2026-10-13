//! Bounded synthetic packages and one immutable historical captured input.
use domain_ir::DocumentId;
use hwpx_package::document_import::{
    ImportedSourcePackage, SourceImportLimits, forms::ImportedDocumentForms,
};
use sha2::{Digest as _, Sha256};
use std::{
    error::Error,
    io::{Cursor, Write},
    path::PathBuf,
};
use zip::{CompressionMethod, ZipWriter, write::SimpleFileOptions};

pub fn package(body: &str) -> Result<Vec<u8>, Box<dyn Error>> {
    let section = format!(
        r#"<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" xmlns:u="urn:future">{body}</hs:sec>"#
    );
    let container=br#"<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="Contents/content.hpf" media-type="application/hwpml-package+xml"/></rootfiles></container>"#;
    let opf=br#"<o:package xmlns:o="http://www.idpf.org/2007/opf/"><o:manifest><o:item id="h" href="Contents/header.xml" media-type="application/xml"/><o:item id="s" href="Contents/section0.xml" media-type="application/xml"/></o:manifest><o:spine><o:itemref idref="s"/></o:spine></o:package>"#;
    let mut zip = ZipWriter::new(Cursor::new(Vec::new()));
    for (name, bytes) in [
        ("mimetype", b"application/hwp+zip".as_slice()),
        ("version.xml", b"<version/>".as_slice()),
        ("META-INF/container.xml", container.as_slice()),
        ("Contents/content.hpf", opf.as_slice()),
        ("Contents/header.xml", b"<header/>".as_slice()),
        ("Contents/section0.xml", section.as_bytes()),
    ] {
        zip.start_file(
            name,
            SimpleFileOptions::default().compression_method(CompressionMethod::Stored),
        )?;
        zip.write_all(bytes)?;
    }
    Ok(zip.finish()?.into_inner())
}
pub fn forms(bytes: &[u8], document: &str) -> Result<ImportedDocumentForms, Box<dyn Error>> {
    Ok(ImportedDocumentForms::import(
        ImportedSourcePackage::import(
            bytes,
            DocumentId::parse(document)?,
            Sha256::digest(bytes).into(),
            SourceImportLimits::default(),
        )?,
    )?)
}
pub fn captured() -> Result<Vec<u8>, Box<dyn Error>> {
    let path=PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../implementation/p09/evidence/private/p09-14-hyperlink-discovery-20260912-attempt02/after.hwpx");
    let metadata = std::fs::symlink_metadata(&path)?;
    if !metadata.is_file() || metadata.file_type().is_symlink() || metadata.len() != 15097 {
        return Err("captured fixture type or size drift".into());
    }
    let bytes = std::fs::read(path)?;
    if hex::encode(Sha256::digest(&bytes))
        != "feb312b974de2dd7d0275e6043e927ea5cf8348cfc0a04b44045e0bf669d4480"
    {
        return Err("captured fixture whole digest drift".into());
    }
    Ok(bytes)
}
