use std::env;
use std::error::Error;
use std::fs;
use std::io::{self, Write};
use std::path::PathBuf;

use domain_ir::{MathAstDraft, MathAstLimits};
use equation_engine::{
    EQEDIT_ADAPTER_SCHEMA_VERSION, EQEDIT_PROFILE_VERSION, EQUATION_EDITOR_SMOKE_PROFILE_VERSION,
    EQUATION_EDITOR_SMOKE_SCHEMA_VERSION, EqEditEngine, EqEditLimits, EqEditParseRequestDraft,
    EquationEditorSmokeLimits, EquationEditorSmokePlanner, EquationEditorSmokeRequestDraft,
    EquationEditorSmokeSnapshot, EquationEditorSmokeSourceState,
};
use serde::Deserialize;
use sha2::{Digest as _, Sha256};

const MAX_ORACLE_BYTES: u64 = 1024 * 1024;

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
    let oracle_path = PathBuf::from(arguments.next().ok_or("before oracle JSON is required")?);
    let expected_oracle_sha256 = argument(&mut arguments, "before oracle SHA-256")?;
    let revision = argument(&mut arguments, "revision")?;
    let before_source = argument(&mut arguments, "before EqEdit")?;
    let after_source = argument(&mut arguments, "after EqEdit")?;
    let saved_after_script = argument(&mut arguments, "saved native after EqEdit")?;
    let harness_sha256 = argument(&mut arguments, "harness SHA-256")?;
    let oracle_contract_sha256 = argument(&mut arguments, "oracle contract SHA-256")?;
    if arguments.next().is_some()
        || !is_digest(&expected_oracle_sha256)
        || !is_digest(&harness_sha256)
        || !is_digest(&oracle_contract_sha256)
    {
        return Err("plan arguments are invalid".into());
    }
    let metadata = fs::symlink_metadata(&oracle_path)?;
    if !metadata.is_file()
        || metadata.file_type().is_symlink()
        || metadata.len() == 0
        || metadata.len() > MAX_ORACLE_BYTES
    {
        return Err("before oracle is not a bounded regular file".into());
    }
    let oracle_bytes = fs::read(&oracle_path)?;
    if hex::encode(Sha256::digest(&oracle_bytes)) != expected_oracle_sha256 {
        return Err("before oracle identity mismatched".into());
    }
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
    let math_limits = MathAstLimits::default();
    let eqedit_limits = EqEditLimits::default();
    let engine = EqEditEngine::new(eqedit_limits, math_limits)?;
    let request = EquationEditorSmokeRequestDraft {
        schema_version: EQUATION_EDITOR_SMOKE_SCHEMA_VERSION.to_owned(),
        profile_version: EQUATION_EDITOR_SMOKE_PROFILE_VERSION.to_owned(),
        harness_sha256,
        oracle_contract_sha256,
        source: source.clone(),
        before_math_ast: ast(&engine, &before_source, math_limits)?,
        after_math_ast: ast(&engine, &after_source, math_limits)?,
        saved_after_script,
    };
    let plan = EquationEditorSmokePlanner::new(
        EquationEditorSmokeLimits::default(),
        math_limits,
        eqedit_limits,
    )
    .build(request, &source)?;
    let bytes = plan.canonical_json(EquationEditorSmokeLimits::default())?;
    io::stdout().write_all(&bytes)?;
    io::stdout().write_all(b"\n")?;
    Ok(())
}

fn ast(
    engine: &EqEditEngine,
    source: &str,
    limits: MathAstLimits,
) -> Result<MathAstDraft, Box<dyn Error>> {
    let parsed = engine.parse(EqEditParseRequestDraft {
        schema_version: EQEDIT_ADAPTER_SCHEMA_VERSION.to_owned(),
        profile_version: EQEDIT_PROFILE_VERSION.to_owned(),
        source: source.to_owned(),
    })?;
    Ok(serde_json::from_slice(
        &parsed.ast().canonical_json(limits)?,
    )?)
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
