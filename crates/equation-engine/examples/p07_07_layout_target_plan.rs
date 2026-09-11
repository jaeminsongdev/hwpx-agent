use std::collections::{HashMap, HashSet};
use std::env;
use std::error::Error;
use std::fs;
use std::io::{self, Write};
use std::path::{Path, PathBuf};

use domain_ir::{MathAstDraft, MathAstLimits};
use equation_engine::{
    EQEDIT_ADAPTER_SCHEMA_VERSION, EQEDIT_PROFILE_VERSION, EqEditEngine, EqEditLimits,
    EqEditParseRequestDraft, EquationLayoutEstimator, EquationLayoutLimits, EquationLayoutMetrics,
    EquationLayoutMode,
};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};

const MAX_JSON_BYTES: u64 = 8 * 1024 * 1024;
const SAMPLE_SCHEMA: &str = "hwpx-agent.p07-07-equation-layout-samples/v1";
const LAYOUT_PROFILE: &str = "hwpx-agent.equation-layout.hangul-2020-11.0.0.9136-x86-ko-KR/v1";
const TIER_PLAN_SCHEMA: &str = "hwpx-agent.p07-08-tier-b-target-plan/v1";
const TARGET_PLAN_SCHEMA: &str = "hwpx-agent.p07-07-equation-layout-target-plan/v1";

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct SampleManifest {
    schema_version: String,
    profile_version: String,
    samples: Vec<SampleRef>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct SampleRef {
    id: String,
    corpus_case_id: String,
    layout: EquationLayoutMode,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct TierPlan {
    schema_version: String,
    profile_version: String,
    revision: String,
    manifest_sha256: String,
    harness_sha256: String,
    oracle_executable_sha256: String,
    cases: Vec<TierCase>,
    plan_sha256: String,
}

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct TierCase {
    id: String,
    ordinal: usize,
    script: String,
    script_sha256: String,
    semantic_sha256: String,
}

#[derive(Serialize)]
struct TierPlanSeed<'a> {
    schema_version: &'a str,
    profile_version: &'a str,
    revision: &'a str,
    manifest_sha256: &'a str,
    harness_sha256: &'a str,
    oracle_executable_sha256: &'a str,
    cases: &'a [TierCase],
}

#[derive(Serialize)]
struct TargetSample {
    id: String,
    ordinal: usize,
    corpus_case_id: String,
    layout: EquationLayoutMode,
    base_unit: u32,
    script: String,
    script_sha256: String,
    semantic_sha256: String,
    metrics: EquationLayoutMetrics,
}

#[derive(Serialize)]
struct TargetPlanSeed<'a> {
    schema_version: &'static str,
    profile_version: &'static str,
    revision: &'a str,
    sample_manifest_sha256: &'a str,
    tier_b_plan_file_sha256: &'a str,
    tier_b_plan_sha256: &'a str,
    harness_sha256: &'a str,
    oracle_executable_sha256: &'a str,
    samples: &'a [TargetSample],
}

#[derive(Serialize)]
struct TargetPlan<'a> {
    schema_version: &'static str,
    profile_version: &'static str,
    revision: &'a str,
    sample_manifest_sha256: &'a str,
    tier_b_plan_file_sha256: &'a str,
    tier_b_plan_sha256: &'a str,
    harness_sha256: &'a str,
    oracle_executable_sha256: &'a str,
    samples: &'a [TargetSample],
    plan_sha256: String,
}

struct Inputs {
    sample_manifest_path: PathBuf,
    sample_manifest_sha256: String,
    tier_plan_path: PathBuf,
    tier_plan_sha256: String,
    revision: String,
    harness_sha256: String,
    oracle_executable_sha256: String,
}

fn main() -> Result<(), Box<dyn Error>> {
    let inputs = inputs()?;
    let sample_bytes = read_exact(&inputs.sample_manifest_path, &inputs.sample_manifest_sha256)?;
    let tier_bytes = read_exact(&inputs.tier_plan_path, &inputs.tier_plan_sha256)?;
    let manifest: SampleManifest = serde_json::from_slice(&sample_bytes)?;
    let tier_plan: TierPlan = serde_json::from_slice(&tier_bytes)?;
    let samples = build_samples(manifest, &tier_plan, &inputs.revision)?;
    write_plan(&inputs, &tier_plan, &samples)
}

fn inputs() -> Result<Inputs, Box<dyn Error>> {
    let mut values = env::args_os();
    let _program = values.next();
    let inputs = Inputs {
        sample_manifest_path: PathBuf::from(values.next().ok_or("sample manifest is required")?),
        sample_manifest_sha256: argument(&mut values, "sample manifest SHA-256")?,
        tier_plan_path: PathBuf::from(values.next().ok_or("Tier B plan is required")?),
        tier_plan_sha256: argument(&mut values, "Tier B plan SHA-256")?,
        revision: argument(&mut values, "revision")?,
        harness_sha256: argument(&mut values, "harness SHA-256")?,
        oracle_executable_sha256: argument(&mut values, "oracle executable SHA-256")?,
    };
    if values.next().is_some()
        || !is_digest(&inputs.sample_manifest_sha256)
        || !is_digest(&inputs.tier_plan_sha256)
        || !is_digest(&inputs.harness_sha256)
        || !is_digest(&inputs.oracle_executable_sha256)
        || inputs.revision.is_empty()
        || inputs.revision.len() > 512
    {
        return Err("layout target plan arguments are invalid".into());
    }
    Ok(inputs)
}

fn build_samples(
    manifest: SampleManifest,
    tier_plan: &TierPlan,
    revision: &str,
) -> Result<Vec<TargetSample>, Box<dyn Error>> {
    if manifest.schema_version != SAMPLE_SCHEMA
        || manifest.profile_version != LAYOUT_PROFILE
        || manifest.samples.len() != 8
    {
        return Err("layout sample manifest identity mismatched".into());
    }
    validate_tier_plan(tier_plan, revision)?;
    let cases: HashMap<_, _> = tier_plan
        .cases
        .iter()
        .map(|case| (case.id.as_str(), case))
        .collect();
    if cases.len() != 14
        || !tier_plan
            .cases
            .iter()
            .enumerate()
            .all(|(index, case)| case.ordinal == index && case.id == format!("b-{:03}", index + 1))
    {
        return Err("Tier B plan case identity mismatched".into());
    }
    let math_limits = MathAstLimits::default();
    let engine = EqEditEngine::new(EqEditLimits::default(), math_limits)?;
    let estimator =
        EquationLayoutEstimator::provisional(EquationLayoutLimits::default(), math_limits);
    let mut ids = HashSet::new();
    let mut pairs = HashSet::new();
    let mut samples = Vec::new();
    for (index, reference) in manifest.samples.into_iter().enumerate() {
        let (expected_id, expected_mode) = expected_sample_identity(index);
        if !valid_sample_id(&reference.id)
            || reference.id != expected_id
            || reference.layout != expected_mode
            || !ids.insert(reference.id.clone())
            || !pairs.insert((reference.corpus_case_id.clone(), reference.layout))
        {
            return Err("layout sample identity duplicated or invalid".into());
        }
        let case = cases
            .get(reference.corpus_case_id.as_str())
            .ok_or("layout sample references an absent Tier B case")?;
        validate_case(&engine, case)?;
        let parsed = engine.parse(EqEditParseRequestDraft {
            schema_version: EQEDIT_ADAPTER_SCHEMA_VERSION.to_owned(),
            profile_version: EQEDIT_PROFILE_VERSION.to_owned(),
            source: case.script.clone(),
        })?;
        let draft: MathAstDraft =
            serde_json::from_slice(&parsed.ast().canonical_json(math_limits)?)?;
        let metrics = estimator.measure(draft)?;
        samples.push(TargetSample {
            id: reference.id,
            ordinal: samples.len(),
            corpus_case_id: reference.corpus_case_id,
            layout: reference.layout,
            base_unit: 1_000,
            script: case.script.clone(),
            script_sha256: case.script_sha256.clone(),
            semantic_sha256: case.semantic_sha256.clone(),
            metrics,
        });
    }
    let inline = samples
        .iter()
        .filter(|sample| sample.layout == EquationLayoutMode::Inline)
        .count();
    let display = samples.len() - inline;
    if inline != 4 || display != 4 {
        return Err("layout sample mode coverage is incomplete".into());
    }
    Ok(samples)
}

fn validate_tier_plan(tier_plan: &TierPlan, revision: &str) -> Result<(), Box<dyn Error>> {
    if tier_plan.schema_version != TIER_PLAN_SCHEMA
        || tier_plan.profile_version
            != "hwpx-agent.equation-corpus.hangul-2020-11.0.0.9136-x86-ko-KR/v1"
        || tier_plan.cases.len() != 14
        || tier_plan.revision != revision
        || !is_digest(&tier_plan.manifest_sha256)
        || !is_digest(&tier_plan.harness_sha256)
        || !is_digest(&tier_plan.oracle_executable_sha256)
        || !is_digest(&tier_plan.plan_sha256)
    {
        return Err("Tier B plan identity mismatched".into());
    }
    let seed = TierPlanSeed {
        schema_version: &tier_plan.schema_version,
        profile_version: &tier_plan.profile_version,
        revision: &tier_plan.revision,
        manifest_sha256: &tier_plan.manifest_sha256,
        harness_sha256: &tier_plan.harness_sha256,
        oracle_executable_sha256: &tier_plan.oracle_executable_sha256,
        cases: &tier_plan.cases,
    };
    if hex::encode(Sha256::digest(serde_json::to_vec(&seed)?)) != tier_plan.plan_sha256 {
        return Err("Tier B plan digest mismatched".into());
    }
    Ok(())
}

fn expected_sample_identity(index: usize) -> (String, EquationLayoutMode) {
    let mode = if index < 4 {
        EquationLayoutMode::Inline
    } else {
        EquationLayoutMode::Display
    };
    let prefix = if mode == EquationLayoutMode::Inline {
        "inline"
    } else {
        "display"
    };
    (format!("{prefix}-{:03}", index % 4 + 1), mode)
}

fn validate_case(engine: &EqEditEngine, case: &TierCase) -> Result<(), Box<dyn Error>> {
    if !is_digest(&case.script_sha256)
        || !is_digest(&case.semantic_sha256)
        || hex::encode(Sha256::digest(case.script.as_bytes())) != case.script_sha256
    {
        return Err("Tier B case digest mismatched".into());
    }
    let parsed = engine.parse(EqEditParseRequestDraft {
        schema_version: EQEDIT_ADAPTER_SCHEMA_VERSION.to_owned(),
        profile_version: EQEDIT_PROFILE_VERSION.to_owned(),
        source: case.script.clone(),
    })?;
    let semantic = hex::encode(parsed.ast().semantic_sha256(MathAstLimits::default())?);
    let compiled = engine.compile(parsed.ast())?;
    if semantic != case.semantic_sha256
        || compiled.script() != case.script
        || compiled.script_sha256() != case.script_sha256
    {
        return Err("Tier B canonical semantic binding mismatched".into());
    }
    Ok(())
}

fn write_plan(
    inputs: &Inputs,
    tier_plan: &TierPlan,
    samples: &[TargetSample],
) -> Result<(), Box<dyn Error>> {
    let seed = TargetPlanSeed {
        schema_version: TARGET_PLAN_SCHEMA,
        profile_version: LAYOUT_PROFILE,
        revision: &inputs.revision,
        sample_manifest_sha256: &inputs.sample_manifest_sha256,
        tier_b_plan_file_sha256: &inputs.tier_plan_sha256,
        tier_b_plan_sha256: &tier_plan.plan_sha256,
        harness_sha256: &inputs.harness_sha256,
        oracle_executable_sha256: &inputs.oracle_executable_sha256,
        samples,
    };
    let plan_sha256 = hex::encode(Sha256::digest(serde_json::to_vec(&seed)?));
    let plan = TargetPlan {
        schema_version: TARGET_PLAN_SCHEMA,
        profile_version: LAYOUT_PROFILE,
        revision: &inputs.revision,
        sample_manifest_sha256: &inputs.sample_manifest_sha256,
        tier_b_plan_file_sha256: &inputs.tier_plan_sha256,
        tier_b_plan_sha256: &tier_plan.plan_sha256,
        harness_sha256: &inputs.harness_sha256,
        oracle_executable_sha256: &inputs.oracle_executable_sha256,
        samples,
        plan_sha256,
    };
    let bytes = serde_json::to_vec(&plan)?;
    if bytes.len() > 4 * 1024 * 1024 {
        return Err("layout target plan exceeds output limit".into());
    }
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
        return Err("layout plan input is not a bounded regular file".into());
    }
    let bytes = fs::read(path)?;
    if hex::encode(Sha256::digest(&bytes)) != expected_sha256 {
        return Err("layout plan input identity mismatched".into());
    }
    Ok(bytes)
}

fn valid_sample_id(value: &str) -> bool {
    let Some((mode, suffix)) = value.rsplit_once('-') else {
        return false;
    };
    matches!(mode, "inline" | "display")
        && suffix.len() == 3
        && suffix.bytes().all(|byte| byte.is_ascii_digit())
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
