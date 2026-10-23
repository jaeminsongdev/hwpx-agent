//! Fresh actual source-backed form consumer; values remain private document data.
use std::{error::Error, path::PathBuf};

use domain_ir::{DocumentId, Flow, Node};
use hwpx_package::document_import::{
    ImportedSourcePackage, SourceImportLimits,
    forms::{FormImportReceipt, ImportedDocumentForms},
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};

#[derive(Serialize)]
struct Evidence {
    profile: &'static str,
    cases: usize,
    resolved_node_anchors: usize,
    typed_forms: usize,
    kinds: [usize; 5],
    receipts: Vec<FormImportReceipt>,
}

fn check_nodes(imported: &ImportedDocumentForms, flow: &Flow) -> Result<usize, Box<dyn Error>> {
    let mut count = 0;
    for node in &flow.children {
        let anchor = node
            .common()
            .source_anchor
            .as_ref()
            .ok_or("missing node anchor")?;
        if imported
            .source()
            .resolve_anchor(anchor)?
            .element()
            .is_none()
        {
            return Err("node source element".into());
        }
        count += 1;
        if let Node::FormControl(form) = node {
            let observed = imported
                .forms()
                .iter()
                .find(|o| o.node_id == form.common.node_id)
                .ok_or("actual observed form")?;
            if &observed.source_anchor != anchor {
                return Err("form anchor drift".into());
            }
        }
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
    let manifest_bytes = std::fs::read(root.join("fixture-manifest.json"))?;
    if hex::encode(Sha256::digest(&manifest_bytes))
        != "8208bff3f87a4e56ec68caecaf41b00c3fdccc5b3f083289f3c13ccede19466e"
    {
        return Err("fixture manifest drift".into());
    }
    let manifest: serde_json::Value = serde_json::from_slice(&manifest_bytes)?;
    let cases = manifest["cases"].as_array().ok_or("fixture cases")?;
    if cases.len() != 5 {
        return Err("fixture count".into());
    }
    let mut evidence = Evidence {
        profile: "hwpx-agent.document-import-observed-forms-probe/v1",
        cases: 0,
        resolved_node_anchors: 0,
        typed_forms: 0,
        kinds: [0; 5],
        receipts: vec![],
    };
    for row in cases {
        for kind in ["source", "output"] {
            let entry = &row[kind];
            let name = entry["path"].as_str().ok_or("fixture name")?;
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
            if bytes.len() as u64 != entry["bytes"].as_u64().ok_or("fixture length")?
                || hex::encode(sha256) != entry["sha256"].as_str().ok_or("fixture sha")?
            {
                return Err("fixture drift".into());
            }
            let source = ImportedSourcePackage::import(
                &bytes,
                DocumentId::parse("actual-forms-probe")?,
                sha256,
                SourceImportLimits::default(),
            )?;
            let imported = ImportedDocumentForms::import(source)?;
            if imported.verify_source(&bytes)? != *imported.receipt() {
                return Err("fresh full form drift".into());
            }
            for section in imported.graph().sections() {
                evidence.resolved_node_anchors += check_nodes(&imported, &section.body)?;
            }
            evidence.typed_forms += imported.forms().len();
            for (sum, value) in evidence.kinds.iter_mut().zip(imported.receipt().kinds) {
                *sum += value;
            }
            evidence.receipts.push(imported.receipt().clone());
            evidence.cases += 1;
        }
    }
    if evidence.cases != 10 || evidence.kinds.contains(&0) {
        return Err("missing form family".into());
    }
    println!("{}", serde_json::to_string(&evidence)?);
    Ok(())
}
