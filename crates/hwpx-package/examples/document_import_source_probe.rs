//! Fresh-process consumer of actual package import, not a synthetic graph oracle.
use std::{error::Error, path::PathBuf};

use domain_ir::DocumentId;
use hwpx_package::document_import::{ImportedSourcePackage, SourceImportLimits};
use serde::Serialize;
use sha2::{Digest as _, Sha256};

#[derive(Serialize)]
struct Evidence {
    profile: &'static str,
    package_cases: usize,
    resolved_part_anchors: usize,
    resolved_element_anchors: usize,
    receipts: Vec<hwpx_package::document_import::SourceImportReceipt>,
}

fn main() -> Result<(), Box<dyn Error>> {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../fixtures/target-build/p09-42-product-form-values-01/output");
    let manifest: serde_json::Value =
        serde_json::from_slice(&std::fs::read(root.join("fixture-manifest.json"))?)?;
    let cases = manifest["cases"]
        .as_array()
        .ok_or("fixture manifest shape")?;
    if cases.len() != 5 {
        return Err("fixture count".into());
    }
    let mut evidence = Evidence {
        profile: "hwpx-agent.document-import-source-probe/v1",
        package_cases: 0,
        resolved_part_anchors: 0,
        resolved_element_anchors: 0,
        receipts: vec![],
    };
    for row in cases {
        for kind in ["source", "output"] {
            let name = row[kind]["path"].as_str().ok_or("fixture path")?;
            if name.contains(['/', '\\', ':']) {
                return Err("fixture path".into());
            }
            let path = root.join(name);
            let metadata = std::fs::symlink_metadata(&path)?;
            if !metadata.is_file()
                || metadata.file_type().is_symlink()
                || metadata.len() > 32 * 1024 * 1024
            {
                return Err("fixture type or bound".into());
            }
            let bytes = std::fs::read(&path)?;
            let sha256: [u8; 32] = Sha256::digest(&bytes).into();
            if bytes.len() as u64 != row[kind]["bytes"].as_u64().ok_or("fixture length")?
                || hex::encode(sha256) != row[kind]["sha256"].as_str().ok_or("fixture digest")?
            {
                return Err("fixture drift".into());
            }
            let source = ImportedSourcePackage::import(
                &bytes,
                DocumentId::parse("source-probe-document")?,
                sha256,
                SourceImportLimits::default(),
            )?;
            if source.verify_source(&bytes)? != *source.receipt() {
                return Err("fresh source drift".into());
            }
            for part in source.parts() {
                source.resolve_anchor(part.anchor())?;
                evidence.resolved_part_anchors += 1;
                if let Some(xml) = part.xml() {
                    for index in 0..xml.elements().len() {
                        let anchor = part
                            .element_anchor(index)
                            .ok_or("missing actual source anchor")?;
                        if source.resolve_anchor(anchor)?.element_index() != Some(index) {
                            return Err("source location drift".into());
                        }
                        evidence.resolved_element_anchors += 1;
                    }
                }
            }
            evidence.receipts.push(source.receipt().clone());
            evidence.package_cases += 1;
        }
    }
    if evidence.package_cases != 10 {
        return Err("missing fixture".into());
    }
    println!("{}", serde_json::to_string(&evidence)?);
    Ok(())
}
