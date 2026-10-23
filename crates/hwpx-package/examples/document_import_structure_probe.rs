//! Fresh actual source-to-IR consumer; intentionally partial typed qualification.
use std::{error::Error, path::PathBuf};

use domain_ir::{DocumentId, Flow, Node};
use hwpx_package::document_import::{
    ImportedSourcePackage, SourceImportLimits,
    structure::{ImportedDocumentStructure, StructureImportReceipt},
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};

#[derive(Serialize)]
struct Evidence {
    profile: &'static str,
    cases: usize,
    resolved_node_anchors: usize,
    receipts: Vec<StructureImportReceipt>,
}

fn check_nodes(imported: &ImportedDocumentStructure, flow: &Flow) -> Result<usize, Box<dyn Error>> {
    let mut count = 0;
    for node in &flow.children {
        let anchor = node
            .common()
            .source_anchor
            .as_ref()
            .ok_or("missing actual node anchor")?;
        if imported
            .source()
            .resolve_anchor(anchor)?
            .element()
            .is_none()
        {
            return Err("node source location".into());
        }
        count += 1;
        if let Node::Table(table) = node {
            for cell in &table.cells {
                count += check_nodes(imported, &cell.body)?;
            }
        }
    }
    Ok(count)
}

fn main() -> Result<(), Box<dyn Error>> {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../fixtures/target-build/p09-42-product-form-values-01/output");
    let manifest: serde_json::Value =
        serde_json::from_slice(&std::fs::read(root.join("fixture-manifest.json"))?)?;
    let cases = manifest["cases"].as_array().ok_or("fixture manifest")?;
    if cases.len() != 5 {
        return Err("fixture count".into());
    }
    let mut evidence = Evidence {
        profile: "hwpx-agent.document-import-structure-probe/v1",
        cases: 0,
        resolved_node_anchors: 0,
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
            let bytes = std::fs::read(path)?;
            let sha256: [u8; 32] = Sha256::digest(&bytes).into();
            if bytes.len() as u64 != row[kind]["bytes"].as_u64().ok_or("fixture bytes")?
                || hex::encode(sha256) != row[kind]["sha256"].as_str().ok_or("fixture digest")?
            {
                return Err("fixture drift".into());
            }
            let source = ImportedSourcePackage::import(
                &bytes,
                DocumentId::parse("actual-structure-probe")?,
                sha256,
                SourceImportLimits::default(),
            )?;
            let imported = ImportedDocumentStructure::import(source)?;
            if imported.verify_source(&bytes)? != *imported.receipt() {
                return Err("fresh full structure drift".into());
            }
            for section in imported.graph().sections() {
                evidence.resolved_node_anchors += check_nodes(&imported, &section.body)?;
            }
            evidence.receipts.push(imported.receipt().clone());
            evidence.cases += 1;
        }
    }
    if evidence.cases != 10 {
        return Err("missing case".into());
    }
    println!("{}", serde_json::to_string(&evidence)?);
    Ok(())
}
