use std::collections::HashSet;
use std::env;
use std::error::Error;
use std::fs;
use std::io::{self, Write};
use std::path::PathBuf;

use domain_ir::{MathAst, MathAstLimits};
use equation_engine::{
    EQEDIT_ADAPTER_SCHEMA_VERSION, EQEDIT_PROFILE_VERSION, EqEditEngine, EqEditLimits,
    EqEditParseRequestDraft, EquationCorpusLimits, EquationCorpusRunner, LatexAdapterLimits,
    MATHML_ADAPTER_SCHEMA_VERSION, MathMlAdapter, MathMlAdapterLimits, MathMlParseRequestDraft,
};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};

const MAX_MANIFEST_BYTES: u64 = 8 * 1024 * 1024;
const MANIFEST_SCHEMA: &str = "hwpx-agent.equation-corpus/v1";
const CORPUS_PROFILE: &str = "hwpx-agent.equation-corpus.hangul-2020-11.0.0.9136-x86-ko-KR/v1";
const PLAN_SCHEMA: &str = "hwpx-agent.p07-08-tier-b-target-plan/v1";

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Manifest {
    schema_version: String,
    profile_version: String,
    cases: Vec<Case>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Case {
    id: String,
    tier: String,
    source_kind: String,
    source: String,
    expectation: String,
    expected_error_code: Option<String>,
}

#[derive(Serialize)]
struct PlannedCase {
    id: String,
    ordinal: usize,
    script: String,
    script_sha256: String,
    semantic_sha256: String,
}

#[derive(Serialize)]
struct PlanSeed<'a> {
    schema_version: &'static str,
    profile_version: &'static str,
    revision: &'a str,
    manifest_sha256: &'a str,
    harness_sha256: &'a str,
    oracle_executable_sha256: &'a str,
    cases: &'a [PlannedCase],
}

#[derive(Serialize)]
struct TargetPlan<'a> {
    schema_version: &'static str,
    profile_version: &'static str,
    revision: &'a str,
    manifest_sha256: &'a str,
    harness_sha256: &'a str,
    oracle_executable_sha256: &'a str,
    cases: &'a [PlannedCase],
    plan_sha256: String,
}

fn main() -> Result<(), Box<dyn Error>> {
    let inputs = inputs()?;
    let bytes = read_manifest(&inputs.manifest_path, &inputs.manifest_sha256)?;
    validate_component_manifest(&bytes, &inputs.manifest_sha256)?;
    let cases = build_cases(&bytes)?;
    write_plan(&inputs, &cases)
}

struct Inputs {
    manifest_path: PathBuf,
    manifest_sha256: String,
    revision: String,
    harness_sha256: String,
    oracle_executable_sha256: String,
}

fn inputs() -> Result<Inputs, Box<dyn Error>> {
    let mut arguments = env::args_os();
    let _program = arguments.next();
    let manifest_path = PathBuf::from(arguments.next().ok_or("manifest path is required")?);
    let manifest_sha256 = argument(&mut arguments, "manifest SHA-256")?;
    let revision = argument(&mut arguments, "revision")?;
    let harness_sha256 = argument(&mut arguments, "harness SHA-256")?;
    let oracle_executable_sha256 = argument(&mut arguments, "oracle executable SHA-256")?;
    if arguments.next().is_some()
        || !is_digest(&manifest_sha256)
        || !is_digest(&harness_sha256)
        || !is_digest(&oracle_executable_sha256)
        || revision.is_empty()
        || revision.len() > 512
    {
        return Err("tier B plan arguments are invalid".into());
    }
    Ok(Inputs {
        manifest_path,
        manifest_sha256,
        revision,
        harness_sha256,
        oracle_executable_sha256,
    })
}

fn read_manifest(path: &PathBuf, expected_sha256: &str) -> Result<Vec<u8>, Box<dyn Error>> {
    let metadata = fs::symlink_metadata(path)?;
    if !metadata.is_file()
        || metadata.file_type().is_symlink()
        || metadata.len() == 0
        || metadata.len() > MAX_MANIFEST_BYTES
    {
        return Err("manifest is not a bounded regular file".into());
    }
    let bytes = fs::read(path)?;
    if hex::encode(Sha256::digest(&bytes)) != expected_sha256 {
        return Err("manifest identity mismatched".into());
    }
    Ok(bytes)
}

fn build_cases(bytes: &[u8]) -> Result<Vec<PlannedCase>, Box<dyn Error>> {
    let manifest: Manifest = serde_json::from_slice(bytes)?;
    if manifest.schema_version != MANIFEST_SCHEMA
        || manifest.profile_version != CORPUS_PROFILE
        || manifest.cases.len() != 64
    {
        return Err("manifest profile or count mismatched".into());
    }
    let math_limits = MathAstLimits::default();
    let eqedit_limits = EqEditLimits::default();
    let engine = EqEditEngine::new(eqedit_limits, math_limits)?;
    let mathml = MathMlAdapter::new(MathMlAdapterLimits::default(), math_limits)?;
    let mut ids = HashSet::new();
    let mut cases = Vec::new();
    for case in manifest.cases {
        if !ids.insert(case.id.clone()) {
            return Err("manifest case identity duplicated".into());
        }
        if case.tier != "b" {
            continue;
        }
        if case.expectation != "semantic_roundtrip" || case.expected_error_code.is_some() {
            return Err("Tier B policy mismatched".into());
        }
        let ast = match case.source_kind.as_str() {
            "eqedit" => engine
                .parse(EqEditParseRequestDraft {
                    schema_version: EQEDIT_ADAPTER_SCHEMA_VERSION.to_owned(),
                    profile_version: EQEDIT_PROFILE_VERSION.to_owned(),
                    source: case.source,
                })?
                .ast()
                .clone(),
            "mathml" => mathml
                .parse(MathMlParseRequestDraft {
                    schema_version: MATHML_ADAPTER_SCHEMA_VERSION.to_owned(),
                    source: case.source,
                })?
                .ast()
                .clone(),
            _ => return Err("Tier B source kind is unsupported".into()),
        };
        cases.push(planned_case(&engine, &ast, case.id, cases.len())?);
    }
    if cases.len() != 14
        || !cases
            .iter()
            .enumerate()
            .all(|(index, case)| case.ordinal == index)
    {
        return Err("Tier B case set is incomplete".into());
    }
    Ok(cases)
}

fn write_plan(inputs: &Inputs, cases: &[PlannedCase]) -> Result<(), Box<dyn Error>> {
    let seed = PlanSeed {
        schema_version: PLAN_SCHEMA,
        profile_version: CORPUS_PROFILE,
        revision: &inputs.revision,
        manifest_sha256: &inputs.manifest_sha256,
        harness_sha256: &inputs.harness_sha256,
        oracle_executable_sha256: &inputs.oracle_executable_sha256,
        cases,
    };
    let plan_sha256 = hex::encode(Sha256::digest(serde_json::to_vec(&seed)?));
    let plan = TargetPlan {
        schema_version: PLAN_SCHEMA,
        profile_version: CORPUS_PROFILE,
        revision: &inputs.revision,
        manifest_sha256: &inputs.manifest_sha256,
        harness_sha256: &inputs.harness_sha256,
        oracle_executable_sha256: &inputs.oracle_executable_sha256,
        cases,
        plan_sha256,
    };
    let output = serde_json::to_vec(&plan)?;
    if output.len() > 4 * 1024 * 1024 {
        return Err("Tier B plan exceeds output limit".into());
    }
    io::stdout().write_all(&output)?;
    io::stdout().write_all(b"\n")?;
    Ok(())
}

fn validate_component_manifest(bytes: &[u8], manifest_sha256: &str) -> Result<(), Box<dyn Error>> {
    let receipt = EquationCorpusRunner::new(
        EquationCorpusLimits::default(),
        MathAstLimits::default(),
        LatexAdapterLimits::default(),
        MathMlAdapterLimits::default(),
        EqEditLimits::default(),
    )?
    .run_json(bytes, manifest_sha256)?;
    if receipt.tier_b_semantic_passed() != 14 || receipt.tier_b_target_state() != "not_run" {
        return Err("component manifest did not pass exact Tier B admission".into());
    }
    Ok(())
}

fn planned_case(
    engine: &EqEditEngine,
    ast: &MathAst,
    id: String,
    ordinal: usize,
) -> Result<PlannedCase, Box<dyn Error>> {
    if !valid_case_id(&id) {
        return Err("Tier B case identity is invalid".into());
    }
    let compiled = engine.compile(ast)?;
    let reparsed = engine.parse(EqEditParseRequestDraft {
        schema_version: EQEDIT_ADAPTER_SCHEMA_VERSION.to_owned(),
        profile_version: EQEDIT_PROFILE_VERSION.to_owned(),
        source: compiled.script().to_owned(),
    })?;
    if !ast.semantically_eq(reparsed.ast()) {
        return Err("canonical Tier B EqEdit did not roundtrip".into());
    }
    Ok(PlannedCase {
        id,
        ordinal,
        script: compiled.script().to_owned(),
        script_sha256: compiled.script_sha256().to_owned(),
        semantic_sha256: hex::encode(ast.semantic_sha256(MathAstLimits::default())?),
    })
}

fn valid_case_id(value: &str) -> bool {
    value.len() == 5
        && value.starts_with("b-")
        && value[2..].bytes().all(|byte| byte.is_ascii_digit())
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
