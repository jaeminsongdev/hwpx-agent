//! Offline compatibility diagnostic; original readers and packages are unchanged.
use hwpx_package::{BoundedZipReader, PackageLimits, PageSetupLimits, PageSetupReader,
    SectionColumnLimits, SectionColumnReader};
use sha2::{Digest as _, Sha256};
use std::{error::Error, io::Cursor, path::{Component, Path, PathBuf}};

fn main() -> Result<(), Box<dyn Error>> {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..");
    let manifest_path = root.join("implementation/p09/evidence/p09-77-document-import-active-security.source-progress.v1.json");
    let metadata = std::fs::symlink_metadata(&manifest_path)?;
    if !metadata.is_file() || metadata.file_type().is_symlink() || metadata.len() != 112_797 {
        return Err("frozen settings input manifest type/size drift".into());
    }
    let manifest = std::fs::read(manifest_path)?;
    if hex::encode(Sha256::digest(&manifest)) != "36b30c931b760bddedb4950c46c8bf7ed84a046dc8998f7f4a51530cfe9f693d" {
        return Err("frozen settings manifest digest drift".into());
    }
    let manifest: serde_json::Value = serde_json::from_slice(&manifest)?;
    let rows = manifest["actual_inputs"].as_array().ok_or("actual input rows")?;
    if rows.len() != 36 { return Err("actual input count drift".into()); }
    let mut sections = 0;
    let mut columns = 0;
    for row in rows {
        let path = Path::new(row["path"].as_str().ok_or("actual input path")?);
        if path.is_absolute() || path.components().any(|c| !matches!(c, Component::Normal(_))) {
            return Err("actual input path scope".into());
        }
        let path = root.join(path);
        let metadata = std::fs::symlink_metadata(&path)?;
        if !metadata.is_file() || metadata.file_type().is_symlink() || metadata.len() > 32 * 1024 * 1024
            || Some(metadata.len()) != row["bytes"].as_u64() {
            return Err("actual input type/length drift".into());
        }
        let bytes = std::fs::read(path)?;
        if Some(hex::encode(Sha256::digest(&bytes)).as_str()) != row["sha256"].as_str() {
            return Err("actual input package SHA drift".into());
        }
        let mut reader = BoundedZipReader::open(Cursor::new(&bytes), PackageLimits::default())?;
        let entries: Vec<_> = reader.entries().iter().enumerate().map(|(i, e)| (i, e.path.as_str().to_owned())).collect();
        let mut header = None;
        let mut actual = Vec::new();
        for (index, name) in entries {
            if name == "Contents/header.xml" { header = Some(reader.read_entry(index)?); }
            if name.starts_with("Contents/section") && Path::new(&name).extension().is_some_and(|v| v.eq_ignore_ascii_case("xml")) {
                let part = reader.read_entry(index)?;
                let page = PageSetupReader::read(&part, PageSetupLimits::default())?;
                let metrics = page.metrics(PageSetupLimits::default())?;
                actual.push((part, metrics.body_width));
            }
        }
        let borrowed: Vec<_> = actual.iter().map(|(b, width)| (b.as_slice(), *width)).collect();
        let sequence = SectionColumnReader::read_sequence_with_header(&header.ok_or("actual header missing")?,
            &borrowed, SectionColumnLimits::default())?;
        sections += sequence.sections.len();
        columns += sequence.sections.iter().map(|s| s.spans.len()).sum::<usize>();
    }
    println!("{}", serde_json::json!({"profile":"section-settings-original-reader-diagnostic/partial-v1",
        "historical_inputs":36,"page_setups":sections,"column_spans":columns,
        "native_started":false,"permission_prompt_requested":false,"not_full_import_or_render":true}));
    Ok(())
}
