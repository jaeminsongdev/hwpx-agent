//! Whole in-memory derivatives only; captured originals are never rewritten.
use hwpx_package::{BoundedZipReader, PackageLimits, PreservingXmlDocument};
use sha2::{Digest as _, Sha256};
use std::{
    error::Error,
    io::{Cursor, Write},
    path::{Component, Path, PathBuf},
};
use zip::{CompressionMethod, ZipWriter, write::SimpleFileOptions};

pub fn actual_corpus() -> Result<Vec<Vec<u8>>, Box<dyn Error>> {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..");
    let manifest_path = root.join(
        "implementation/p09/evidence/p09-75-document-import-bookmarks.source-progress.v1.json",
    );
    let meta = std::fs::symlink_metadata(&manifest_path)?;
    if !meta.is_file() || meta.file_type().is_symlink() || meta.len() != 111910 {
        return Err("frozen manifest type/size drift".into());
    }
    let manifest = std::fs::read(manifest_path)?;
    if hex::encode(Sha256::digest(&manifest))
        != "dc23091137a2262c9191cd060b923df282f50a25a0bfb16e605705c712953824"
    {
        return Err("frozen actual-input manifest digest drift".into());
    }
    let manifest: serde_json::Value = serde_json::from_slice(&manifest)?;
    let rows = manifest["actual_inputs"]
        .as_array()
        .ok_or("actual input rows")?;
    if rows.len() != 26 {
        return Err("actual input count drift".into());
    }
    let mut corpus = Vec::new();
    for row in rows {
        let relative = Path::new(row["path"].as_str().ok_or("actual path")?);
        if relative.is_absolute()
            || relative
                .components()
                .any(|c| !matches!(c, Component::Normal(_)))
        {
            return Err("actual path scope".into());
        }
        let path = root.join(relative);
        let meta = std::fs::symlink_metadata(&path)?;
        if !meta.is_file()
            || meta.file_type().is_symlink()
            || Some(meta.len()) != row["bytes"].as_u64()
            || meta.len() > 32 * 1024 * 1024
        {
            return Err("actual type/size drift".into());
        }
        let bytes = std::fs::read(path)?;
        if Some(hex::encode(Sha256::digest(&bytes)).as_str()) != row["sha256"].as_str() {
            return Err("actual whole package digest drift".into());
        }
        corpus.push(bytes);
    }
    Ok(corpus)
}
pub fn read_part(bytes: &[u8], path: &str) -> Result<Vec<u8>, Box<dyn Error>> {
    let mut zip = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let index = zip
        .entries()
        .iter()
        .position(|entry| entry.path.as_str() == path)
        .ok_or("fixture part missing")?;
    Ok(zip.read_entry(index)?)
}
pub fn mutate_part(
    bytes: &[u8],
    path: &str,
    change: impl FnOnce(&str) -> Result<String, Box<dyn Error>>,
) -> Result<Vec<u8>, Box<dyn Error>> {
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let old = read_part(bytes, path)?;
    let new = change(std::str::from_utf8(&old)?)?;
    if new.as_bytes() == old {
        return Err("fixture mutation did not change bytes".into());
    }
    let names: Vec<_> = reader
        .entries()
        .iter()
        .map(|entry| entry.path.as_str().to_owned())
        .collect();
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    for (index, name) in names.into_iter().enumerate() {
        let data = reader.read_entry(index)?;
        writer.start_file(
            &name,
            SimpleFileOptions::default().compression_method(CompressionMethod::Stored),
        )?;
        writer.write_all(if name == path { new.as_bytes() } else { &data })?;
    }
    Ok(writer.finish()?.into_inner())
}
pub fn change_attribute(
    bytes: &[u8],
    path: &str,
    tag: &str,
    key: &str,
    value: &str,
) -> Result<Vec<u8>, Box<dyn Error>> {
    mutate_part(bytes, path, |text| {
        let xml = PreservingXmlDocument::parse(text.as_bytes())?;
        let element = xml
            .elements()
            .iter()
            .find(|e| e.name().local_name() == tag)
            .ok_or("fixture element missing")?;
        let attribute = element
            .attributes()
            .iter()
            .find(|a| a.name().namespace().is_none() && a.name().local_name() == key)
            .ok_or("fixture attribute missing")?;
        let mut result = text.to_owned();
        result.replace_range(
            attribute.value_span().start()..attribute.value_span().end(),
            value,
        );
        Ok(result)
    })
}
