//! Reads the entire locked historical table corpus without launching Hangul.
use std::{error::Error, path::PathBuf};

use domain_ir::{DocumentId, Flow, Node};
use hwpx_package::document_import::{
    ImportedSourcePackage, SourceImportLimits,
    structure::{ImportedDocumentStructure, StructureImportReceipt},
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};

const MANIFEST: &str =
    "implementation/p06/evidence/target/p06-table-aggregate.current-2020.attempt02.v2.json";
const MANIFEST_SHA: &str = "edc71d554e0975d511ffe6f0de1b140a30ca932d0bf2b9c7b70517c5e8674fc5";
const PREFIX: &str = "fixtures/target-build/p06-09-table-aggregate-target-20260909-05/";
const IDS: [&str; 8] = [
    "TABLE-022",
    "TABLE-023",
    "TABLE-024",
    "TABLE-026",
    "TABLE-027",
    "TABLE-028",
    "TABLE-029",
    "TABLE-030",
];

#[derive(Serialize)]
struct Outcome {
    feature_id: String,
    kind: &'static str,
    source_sha256: String,
    state: &'static str,
    // Only closed importer diagnostics, never XML, values, paths or raw logs.
    error: Option<String>,
    resolved_node_anchors: usize,
    grids: Vec<[u32; 3]>,
    receipt: Option<StructureImportReceipt>,
}

#[derive(Serialize)]
struct Evidence {
    profile: &'static str,
    authority_sha256: &'static str,
    cases: usize,
    passed: usize,
    outcomes: Vec<Outcome>,
}

fn check_flow(
    imported: &ImportedDocumentStructure,
    flow: &Flow,
    grids: &mut Vec<[u32; 3]>,
) -> Result<usize, Box<dyn Error>> {
    let mut anchors = 0;
    for node in &flow.children {
        let anchor = node.common().source_anchor.as_ref().ok_or("node anchor")?;
        if imported
            .source()
            .resolve_anchor(anchor)?
            .element()
            .is_none()
        {
            return Err("node source element".into());
        }
        anchors += 1;
        if let Node::Table(table) = node {
            grids.push([table.rows, table.columns, u32::try_from(table.cells.len())?]);
            for cell in &table.cells {
                anchors += check_flow(imported, &cell.body, grids)?;
            }
        }
    }
    Ok(anchors)
}

fn outcome(
    bytes: &[u8],
    feature_id: &str,
    kind: &'static str,
    expected_grid: [u32; 3],
) -> Result<Outcome, Box<dyn Error>> {
    let sha256: [u8; 32] = Sha256::digest(bytes).into();
    let mut result = Outcome {
        feature_id: feature_id.into(),
        kind,
        source_sha256: hex::encode(sha256),
        state: "FAIL",
        error: None,
        resolved_node_anchors: 0,
        grids: vec![],
        receipt: None,
    };
    let source = match ImportedSourcePackage::import(
        bytes,
        DocumentId::parse("actual-saved-table-import")?,
        sha256,
        SourceImportLimits::default(),
    ) {
        Ok(source) => source,
        Err(error) => {
            result.error = Some(error.to_string());
            return Ok(result);
        }
    };
    let imported = match ImportedDocumentStructure::import(source) {
        Ok(imported) => imported,
        Err(error) => {
            result.error = Some(error.to_string());
            return Ok(result);
        }
    };
    if imported.verify_source(bytes)? != *imported.receipt() {
        return Err("fresh full structure drift".into());
    }
    for section in imported.graph().sections() {
        result.resolved_node_anchors += check_flow(&imported, &section.body, &mut result.grids)?;
    }
    if result.grids != [expected_grid] {
        result.error = Some("historical grid oracle mismatch".into());
        return Ok(result);
    }
    result.receipt = Some(imported.receipt().clone());
    result.state = "PASS";
    Ok(result)
}

fn read_locked(
    path: &std::path::Path,
    bytes: u64,
    sha256: &str,
) -> Result<Vec<u8>, Box<dyn Error>> {
    let metadata = std::fs::symlink_metadata(path)?;
    if !metadata.is_file()
        || metadata.file_type().is_symlink()
        || metadata.len() != bytes
        || metadata.len() > 32 * 1024 * 1024
    {
        return Err("fixture type or byte bound".into());
    }
    let original = std::fs::read(path)?;
    if original.len() as u64 != bytes || hex::encode(Sha256::digest(&original)) != sha256 {
        return Err("fixture drift".into());
    }
    Ok(original)
}

fn main() -> Result<(), Box<dyn Error>> {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..");
    let manifest_path = root.join(MANIFEST);
    let manifest_length = std::fs::metadata(&manifest_path)?.len();
    let manifest: serde_json::Value =
        serde_json::from_slice(&read_locked(&manifest_path, manifest_length, MANIFEST_SHA)?)?;
    let cases = manifest["cases"].as_array().ok_or("fixture manifest")?;
    if cases.len() != IDS.len() {
        return Err("complete fixture count".into());
    }
    let mut evidence = Evidence {
        profile: "hwpx-agent.document-import-saved-table-probe/v1",
        authority_sha256: MANIFEST_SHA,
        cases: 0,
        passed: 0,
        outcomes: vec![],
    };
    for (row, expected_id) in cases.iter().zip(IDS) {
        let feature_id = row["feature_id"].as_str().ok_or("feature ID")?;
        if feature_id != expected_id {
            return Err("fixture identity or order".into());
        }
        let expected_grid = ["rows", "columns", "master_cells"]
            .map(|key| row["oracle"][key].as_u64().ok_or("grid oracle"))
            .into_iter()
            .collect::<Result<Vec<_>, _>>()?
            .into_iter()
            .map(u32::try_from)
            .collect::<Result<Vec<_>, _>>()?;
        let expected_grid: [u32; 3] = expected_grid.try_into().map_err(|_| "grid length")?;
        for kind in ["input", "output"] {
            let entry = &row[kind];
            let name = entry["path"].as_str().ok_or("fixture path")?;
            let basename = name.strip_prefix(PREFIX).ok_or("fixture root")?;
            if basename.is_empty() || basename.contains(['/', '\\', ':']) {
                return Err("fixture path shape".into());
            }
            let bytes = read_locked(
                &root.join(name),
                entry["bytes"].as_u64().ok_or("fixture length")?,
                entry["sha256"].as_str().ok_or("fixture sha")?,
            )?;
            let result = outcome(&bytes, feature_id, kind, expected_grid)?;
            evidence.passed += usize::from(result.state == "PASS");
            evidence.outcomes.push(result);
            evidence.cases += 1;
        }
    }
    println!("{}", serde_json::to_string(&evidence)?);
    if evidence.passed != 16 || evidence.cases != 16 {
        return Err("saved table corpus import incomplete".into());
    }
    Ok(())
}
