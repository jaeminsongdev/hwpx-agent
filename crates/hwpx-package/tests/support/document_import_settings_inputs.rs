//! Exact frozen P77 historical source manifest; no source rewriting or native use.
use sha2::{Digest as _, Sha256};
use std::{
    error::Error,
    path::{Component, Path, PathBuf},
};
pub fn actual_corpus() -> Result<Vec<Vec<u8>>, Box<dyn Error>> {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..");
    let manifest_path = root.join("implementation/p09/evidence/p09-77-document-import-active-security.source-progress.v1.json");
    let metadata = std::fs::symlink_metadata(&manifest_path)?;
    if !metadata.is_file() || metadata.file_type().is_symlink() || metadata.len() != 112_797 {
        return Err("frozen P77 input manifest type/size drift".into());
    }
    let manifest = std::fs::read(manifest_path)?;
    if hex::encode(Sha256::digest(&manifest))
        != "36b30c931b760bddedb4950c46c8bf7ed84a046dc8998f7f4a51530cfe9f693d"
    {
        return Err("frozen P77 input manifest SHA drift".into());
    }
    let manifest: serde_json::Value = serde_json::from_slice(&manifest)?;
    let rows = manifest["actual_inputs"]
        .as_array()
        .ok_or("actual input rows")?;
    if rows.len() != 36 {
        return Err("actual input count drift".into());
    }
    let mut inputs = Vec::new();
    for row in rows {
        let path = Path::new(row["path"].as_str().ok_or("actual input path")?);
        if path.is_absolute()
            || path
                .components()
                .any(|c| !matches!(c, Component::Normal(_)))
        {
            return Err("actual input path scope".into());
        }
        let path = root.join(path);
        let metadata = std::fs::symlink_metadata(&path)?;
        if !metadata.is_file()
            || metadata.file_type().is_symlink()
            || metadata.len() > 32 * 1024 * 1024
            || Some(metadata.len()) != row["bytes"].as_u64()
        {
            return Err("actual input type/length drift".into());
        }
        let bytes = std::fs::read(path)?;
        if Some(hex::encode(Sha256::digest(&bytes)).as_str()) != row["sha256"].as_str() {
            return Err("actual input package SHA drift".into());
        }
        inputs.push(bytes);
    }
    Ok(inputs)
}
