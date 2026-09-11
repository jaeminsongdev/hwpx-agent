use std::env;
use std::error::Error;
use std::fs;
use std::io::{self, Write};
use std::path::{Path, PathBuf};

use domain_ir::MathAstLimits;
use equation_engine::{
    EqEditLimits, EquationEditorSmokeLimits, EquationEditorSmokePlanner,
    EquationEditorSmokeSnapshot, EquationEditorSmokeSourceState,
};
use serde::Deserialize;
use sha2::{Digest as _, Sha256};

const MAX_JSON_BYTES: u64 = 16 * 1024 * 1024;

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct OracleDraft {
    schema_version: String,
    state: String,
    input_unchanged: bool,
    snapshot: EquationEditorSmokeSnapshot,
    anchor_fingerprint_sha256: String,
    package_parts: usize,
    id_declarations: usize,
    id_references: usize,
    layout: String,
    base_unit: u32,
    baseline_percent: u8,
    width_hwpunit: u32,
    height_hwpunit: u32,
}

fn main() -> Result<(), Box<dyn Error>> {
    let mut arguments = env::args_os();
    let _program = arguments.next();
    let plan_path = PathBuf::from(arguments.next().ok_or("plan JSON is required")?);
    let plan_file_sha256 = argument(&mut arguments, "plan file SHA-256")?;
    let evidence_path = PathBuf::from(arguments.next().ok_or("evidence JSON is required")?);
    let evidence_sha256 = argument(&mut arguments, "evidence SHA-256")?;
    let oracle_path = PathBuf::from(arguments.next().ok_or("before oracle JSON is required")?);
    let oracle_sha256 = argument(&mut arguments, "before oracle SHA-256")?;
    let revision = argument(&mut arguments, "revision")?;
    if arguments.next().is_some()
        || !is_digest(&plan_file_sha256)
        || !is_digest(&evidence_sha256)
        || !is_digest(&oracle_sha256)
    {
        return Err("evidence oracle arguments are invalid".into());
    }
    let plan_bytes = read_exact(&plan_path, &plan_file_sha256)?;
    let evidence_bytes = read_exact(&evidence_path, &evidence_sha256)?;
    let oracle_bytes = read_exact(&oracle_path, &oracle_sha256)?;
    let oracle: OracleDraft = serde_json::from_slice(&oracle_bytes)?;
    if oracle.schema_version != "hwpx-agent.p07-09-equation-editor-oracle/v1"
        || oracle.state != "pass"
        || !oracle.input_unchanged
        || oracle.snapshot.native_object_count != 1
        || oracle.package_parts == 0
        || oracle.id_declarations == 0
        || oracle.id_references == 0
        || oracle.layout != "display"
        || oracle.base_unit != 1_000
        || oracle.baseline_percent == 0
        || oracle.width_hwpunit == 0
        || oracle.height_hwpunit == 0
        || !is_digest(&oracle.anchor_fingerprint_sha256)
    {
        return Err("before oracle state is not admissible".into());
    }
    let source = EquationEditorSmokeSourceState {
        revision,
        artifact_sha256: oracle.snapshot.artifact_sha256,
        package_graph_sha256: oracle.snapshot.package_graph_sha256,
        document_flow_sha256: oracle.snapshot.document_flow_sha256,
        anchor_fingerprint_sha256: oracle.anchor_fingerprint_sha256,
        object_id: oracle.snapshot.object_id,
        semantic_sha256: oracle.snapshot.semantic_sha256,
        script_sha256: oracle.snapshot.script_sha256,
        native_object_count: oracle.snapshot.native_object_count,
    };
    let limits = EquationEditorSmokeLimits::default();
    let planner =
        EquationEditorSmokePlanner::new(limits, MathAstLimits::default(), EqEditLimits::default());
    let plan = planner.load_plan_json(&plan_bytes, &plan_file_sha256, &source)?;
    let receipt = planner.verify_evidence_json(&plan, &evidence_bytes, &evidence_sha256)?;
    let bytes = receipt.canonical_json(limits)?;
    io::stdout().write_all(&bytes)?;
    io::stdout().write_all(b"\n")?;
    Ok(())
}

fn read_exact(path: &Path, expected_sha256: &str) -> Result<Vec<u8>, Box<dyn Error>> {
    let metadata = fs::symlink_metadata(path)?;
    if !metadata.is_file()
        || metadata.file_type().is_symlink()
        || metadata.len() == 0
        || metadata.len() > MAX_JSON_BYTES
    {
        return Err("input is not a bounded regular file".into());
    }
    let bytes = fs::read(path)?;
    if hex::encode(Sha256::digest(&bytes)) != expected_sha256 {
        return Err("input identity mismatched".into());
    }
    Ok(bytes)
}

fn argument(
    values: &mut impl Iterator<Item = std::ffi::OsString>,
    name: &'static str,
) -> Result<String, Box<dyn Error>> {
    let Some(value) = values.next() else {
        return Err(format!("{name} is required").into());
    };
    value
        .into_string()
        .map_err(|_| format!("{name} is not Unicode").into())
}

fn is_digest(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}
