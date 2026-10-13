//! Locked actual source headers, no Hangul/COM/UI or raw document values.
use hwpx_package::{
    BoundedZipReader, CharacterStyleCatalogReader, CharacterStyleLimits, PackageLimits,
    ParagraphStyleCatalogReader, ParagraphStyleLimits,
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use std::{collections::BTreeMap, error::Error, io::Cursor, path::PathBuf};

#[derive(Serialize)]
struct Evidence {
    actual_packages: usize,
    original_character_reader_passed: usize,
    original_paragraph_reader_passed: usize,
    original_reader_errors: BTreeMap<String, usize>,
    native_activated: bool,
    p09_complete: bool,
}
fn main() -> Result<(), Box<dyn Error>> {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..");
    let manifest = std::fs::read(root.join(
        "implementation/p09/evidence/p09-75-document-import-bookmarks.source-progress.v1.json",
    ))?;
    if manifest.len() != 111910
        || hex::encode(Sha256::digest(&manifest))
            != "dc23091137a2262c9191cd060b923df282f50a25a0bfb16e605705c712953824"
    {
        return Err("frozen actual-input manifest drift".into());
    }
    let manifest: serde_json::Value = serde_json::from_slice(&manifest)?;
    let rows = manifest["actual_inputs"].as_array().ok_or("input rows")?;
    if rows.len() != 26 {
        return Err("actual corpus count drift".into());
    }
    let mut e = Evidence {
        actual_packages: 0,
        original_character_reader_passed: 0,
        original_paragraph_reader_passed: 0,
        original_reader_errors: BTreeMap::new(),
        native_activated: false,
        p09_complete: false,
    };
    for row in rows {
        let path = row["path"].as_str().ok_or("input path")?;
        let relative = std::path::Path::new(path);
        if relative.is_absolute()
            || relative.components().any(|c| {
                !matches!(c, std::path::Component::Normal(_) | std::path::Component::CurDir)
            })
        {
            return Err("input path scope".into());
        }
        let path = root.join(relative);
        let meta = std::fs::symlink_metadata(&path)?;
        if !meta.is_file()
            || meta.file_type().is_symlink()
            || Some(meta.len()) != row["bytes"].as_u64()
            || meta.len() > 32 * 1024 * 1024
        {
            return Err("actual input type/size drift".into());
        }
        let bytes = std::fs::read(path)?;
        if Some(hex::encode(Sha256::digest(&bytes)).as_str()) != row["sha256"].as_str() {
            return Err("actual input digest drift".into());
        }
        let mut zip = BoundedZipReader::open(Cursor::new(&bytes), PackageLimits::default())?;
        let header = zip
            .entries()
            .iter()
            .position(|entry| entry.path == "Contents/header.xml")
            .ok_or("header missing")?;
        let header = zip.read_entry(header)?;
        match CharacterStyleCatalogReader::read(&header, CharacterStyleLimits::default()) {
            Ok(_) => e.original_character_reader_passed += 1,
            Err(error) => *e.original_reader_errors.entry(error.code().into()).or_default() += 1,
        }
        match ParagraphStyleCatalogReader::read(&header, ParagraphStyleLimits::default()) {
            Ok(_) => e.original_paragraph_reader_passed += 1,
            Err(error) => *e.original_reader_errors.entry(error.code().into()).or_default() += 1,
        }
        e.actual_packages += 1;
    }
    println!("{}", serde_json::to_string(&e)?);
    Ok(())
}
