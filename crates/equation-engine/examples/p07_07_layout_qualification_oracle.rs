use std::env;
use std::error::Error;
use std::fs;
use std::path::PathBuf;

use domain_ir::MathAstLimits;
use equation_engine::{EquationLayoutEstimator, EquationLayoutLimits};
use serde::Deserialize;
use serde_json::json;
use sha2::{Digest as _, Sha256};

const MAX_INPUT_BYTES: u64 = 4 * 1024 * 1024;
const SCHEMA: &str = "hwpx-agent.equation-layout-qualification/v1";
const PROFILE: &str = "hwpx-agent.equation-layout.hangul-2020-11.0.0.9136-x86-ko-KR/v1";

#[derive(Deserialize)]
struct Summary {
    schema_version: String,
    profile_version: String,
    validation: Validation,
    exact_samples: Vec<serde_json::Value>,
}

#[derive(Deserialize)]
struct Validation {
    sample_count: usize,
    inline_sample_count: usize,
    display_sample_count: usize,
    extent_max_error_hwpunit: u32,
    baseline_max_error_hwpunit: u32,
    ink_box_overflow_count: usize,
    clipping_count: usize,
    overlap_count: usize,
    silent_fallback_count: usize,
    all_pages_inspected: bool,
}

fn main() -> Result<(), Box<dyn Error>> {
    let mut arguments = env::args_os();
    let _program = arguments.next();
    let input = PathBuf::from(arguments.next().ok_or("qualification path is required")?);
    let expected_sha256 = argument(&mut arguments, "expected qualification SHA-256")?;
    if arguments.next().is_some() || !is_digest(&expected_sha256) {
        return Err("qualification oracle arguments are invalid".into());
    }
    let metadata = fs::symlink_metadata(&input)?;
    if !metadata.is_file()
        || metadata.file_type().is_symlink()
        || metadata.len() == 0
        || metadata.len() > MAX_INPUT_BYTES
    {
        return Err("qualification is not a bounded regular file".into());
    }
    let bytes = fs::read(&input)?;
    if hex::encode(Sha256::digest(&bytes)) != expected_sha256 {
        return Err("qualification identity mismatched".into());
    }
    let summary: Summary = serde_json::from_slice(&bytes)?;
    if summary.schema_version != SCHEMA
        || summary.profile_version != PROFILE
        || summary.validation.sample_count != 8
        || summary.validation.inline_sample_count != 4
        || summary.validation.display_sample_count != 4
        || summary.validation.extent_max_error_hwpunit > 150
        || summary.validation.baseline_max_error_hwpunit > 50
        || summary.validation.ink_box_overflow_count != 0
        || summary.validation.clipping_count != 0
        || summary.validation.overlap_count != 0
        || summary.validation.silent_fallback_count != 0
        || !summary.validation.all_pages_inspected
        || summary.exact_samples.len() != 8
    {
        return Err("qualification summary mismatched".into());
    }
    let _estimator = EquationLayoutEstimator::from_qualification_json(
        EquationLayoutLimits::default(),
        MathAstLimits::default(),
        &bytes,
        &expected_sha256,
    )?;
    if fs::read(&input)? != bytes {
        return Err("qualification changed during validation".into());
    }
    println!(
        "{}",
        serde_json::to_string(&json!({
            "schema_version": "hwpx-agent.p07-07-equation-layout-qualification-oracle/v1",
            "state": "pass",
            "qualification_sha256": expected_sha256,
            "input_unchanged": true,
            "sample_count": 8,
            "inline_sample_count": 4,
            "display_sample_count": 4,
            "extent_max_error_hwpunit": summary.validation.extent_max_error_hwpunit,
            "baseline_max_error_hwpunit": summary.validation.baseline_max_error_hwpunit,
            "qualification_schema_valid": true,
            "actual_hangul_asserted_by_oracle": false,
            "render_asserted_by_oracle": false,
            "p07_07_complete_asserted_by_oracle": false,
            "product_complete": false,
        }))?
    );
    Ok(())
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
