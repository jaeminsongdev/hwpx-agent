//! In-memory derivative of exact Native670; original bytes/parts are preserved.
use domain_ir::{LogicalId, ReferenceAuxiliaryLimits, SourceAnchorHandle};
use hwpx_package::document_import::fields::{
    ImportedDocumentFields, block_bookmarks::ImportedBlockBookmarks,
};
use hwpx_package::document_import::forms::ImportedDocumentForms;
use sha2::{Digest as _, Sha256};
use std::{
    error::Error,
    io::{Cursor, Read, Write},
    path::PathBuf,
};
use zip::{CompressionMethod, ZipArchive, ZipWriter, write::SimpleFileOptions};
pub const DISPLAY: &str = "P09_BLOCK679_DISPLAY";
pub fn native_source() -> Result<Vec<u8>, Box<dyn Error>> {
    let p=PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../implementation/p09/evidence/private/p09-361-block-bookmark670-source-document001/created.hwpx");
    let meta = std::fs::symlink_metadata(&p)?;
    if !meta.is_file() || meta.file_type().is_symlink() || meta.len() != 17331 {
        return Err("FIXTURE679_NATIVE_TYPE_SIZE".into());
    }
    let raw = std::fs::read(p)?;
    if hex::encode(Sha256::digest(&raw))
        != "aa0ae8f3042a0b3be43733deb0196488bdd1bac14e6025f7785915cca5660076"
    {
        return Err("FIXTURE679_NATIVE_SHA".into());
    }
    Ok(raw)
}
pub fn map_section(
    raw: &[u8],
    map: impl FnOnce(&str) -> Result<String, Box<dyn Error>>,
) -> Result<Vec<u8>, Box<dyn Error>> {
    let mut input = ZipArchive::new(Cursor::new(raw))?;
    let mut out = ZipWriter::new(Cursor::new(Vec::new()));
    let mut map = Some(map);
    let mut changes = 0;
    for i in 0..input.len() {
        let mut entry = input.by_index(i)?;
        let name = entry.name().to_owned();
        if entry.is_dir() || entry.size() > 4194304 {
            return Err("FIXTURE679_ENTRY_BOUND".into());
        }
        let mut data = Vec::new();
        entry.read_to_end(&mut data)?;
        if name == "Contents/section0.xml" {
            data = map.take().ok_or("FIXTURE679_ONE_SECTION")?(std::str::from_utf8(&data)?)?
                .into_bytes();
            changes += 1;
        }
        out.start_file(
            name,
            SimpleFileOptions::default().compression_method(CompressionMethod::Stored),
        )?;
        out.write_all(&data)?;
    }
    if changes != 1 {
        return Err("FIXTURE679_ONE_SECTION".into());
    }
    Ok(out.finish()?.into_inner())
}
pub fn derived_source() -> Result<Vec<u8>, Box<dyn Error>> {
    map_section(&native_source()?, |section| {
        let close = "</hs:sec>";
        let index = section.rfind(close).ok_or("FIXTURE679_SECTION_CLOSE")?;
        let insertion = format!(
            "<hp:p id=\"0\" paraPrIDRef=\"0\" styleIDRef=\"0\" pageBreak=\"0\" columnBreak=\"0\" merged=\"0\"><hp:run charPrIDRef=\"0\"><hp:t>{DISPLAY}</hp:t></hp:run></hp:p>"
        );
        Ok(format!(
            "{}{}{}",
            &section[..index],
            insertion,
            &section[index..]
        ))
    })
}
pub fn select(
    forms: &ImportedDocumentForms,
    raw: &[u8],
) -> Result<(SourceAnchorHandle, LogicalId), Box<dyn Error>> {
    let fields = ImportedDocumentFields::import(forms)?;
    let limits = ReferenceAuxiliaryLimits::new(Default::default())?;
    let blocks = ImportedBlockBookmarks::import(&fields, limits)?;
    let target = blocks
        .by_exact_source_name("p09_block643_01")?
        .field_reference_id()
        .clone();
    let mut matches = Vec::new();
    let mut zip=ZipArchive::new(Cursor::new(raw))?;
    for part in forms.source().parts() {
        if part.path().as_str()!="Contents/section0.xml"{continue;}
        if let Some(xml) = part.xml() {
            let mut bytes=Vec::new();zip.by_name(part.path().as_str())?.read_to_end(&mut bytes)?;
            if <[u8;32]>::from(Sha256::digest(&bytes))!=xml.original_sha256(){return Err("FIXTURE679_EXACT_PART_BYTES".into());}
            for (i, n) in xml.elements().iter().enumerate() {
                if n.name().local_name() != "run" {
                    continue;
                }
                let Some(child) = n.first_child().and_then(|j| xml.elements().get(j)) else {
                    continue;
                };
                if child.name().local_name() == "t"
                    && child.next_sibling().is_none()
                    && child.first_child().is_none()
                    && child
                        .content_span()
                        .is_some_and(|s| bytes.get(s.start()..s.end())==Some(DISPLAY.as_bytes()))
                {
                    matches.push(part.element_anchor(i).ok_or("FIXTURE679_ANCHOR")?.clone());
                }
            }
        }
    }
    if matches.len() != 1 {
        return Err("FIXTURE679_ONE_PLAIN_RUN".into());
    }
    Ok((matches.remove(0), target))
}
