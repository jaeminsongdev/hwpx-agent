use std::env;
use std::error::Error;
use std::fs;
use std::io::Cursor;
use std::path::PathBuf;

use domain_ir::{MathAstDraft, MathAstLimits};
use equation_engine::{EquationLayoutEstimator, EquationLayoutLimits, EquationLayoutMode};
use hwpx_package::{
    BoundedZipReader, EquationHwpxLimits, EquationHwpxReader, EquationLayout, IdIndex,
    IdRuleProfile, PackageGraph,
};
use serde_json::json;
use sha2::{Digest as _, Sha256};

const MAX_INPUT_BYTES: usize = 8 * 1024 * 1024;
const SECTION_PATH: &str = "Contents/section0.xml";

fn main() -> Result<(), Box<dyn Error>> {
    let mut arguments = env::args_os();
    let _program = arguments.next();
    let input = PathBuf::from(arguments.next().ok_or("input HWPX is required")?);
    let expected_input_sha256 = argument(&mut arguments, "expected input SHA-256")?;
    let expected_layout = parse_layout(&argument(&mut arguments, "expected layout")?)?;
    let expected_script_sha256 = argument(&mut arguments, "expected script SHA-256")?;
    let expected_semantic_sha256 = argument(&mut arguments, "expected semantic SHA-256")?;
    if arguments.next().is_some()
        || !is_digest(&expected_input_sha256)
        || !is_digest(&expected_script_sha256)
        || !is_digest(&expected_semantic_sha256)
    {
        return Err("layout oracle arguments are invalid".into());
    }
    let bytes = read_exact(&input, &expected_input_sha256)?;
    let limits = EquationHwpxLimits::default();
    let mut reader = BoundedZipReader::open(Cursor::new(bytes.as_slice()), limits.package)?;
    let graph = PackageGraph::build(&mut reader, limits.graph)?;
    let index = IdIndex::build(
        &mut reader,
        &graph,
        IdRuleProfile::current_hancom_2020_equation_v4(),
        limits.ids,
    )?;
    let readback = EquationHwpxReader::read_automation_in_package(
        &mut reader,
        &graph,
        SECTION_PATH,
        0,
        limits,
    )?;
    let native_layout = match expected_layout {
        EquationLayoutMode::Inline => EquationLayout::Inline,
        EquationLayoutMode::Display => EquationLayout::Display,
    };
    if readback.object_id() == 0
        || readback.native_object_count() != 1
        || readback.layout() != native_layout
        || readback.script_sha256() != expected_script_sha256
        || readback.semantic_sha256() != expected_semantic_sha256
        || readback.style().base_unit != 1_000
        || readback.style().text_color.red != 0
        || readback.style().text_color.green != 0
        || readback.style().text_color.blue != 0
        || !(1..=100).contains(&readback.style().baseline_percent)
        || readback.extent().width_hwpunit == 0
        || readback.extent().height_hwpunit == 0
    {
        return Err("layout native readback mismatched".into());
    }
    let math_limits = MathAstLimits::default();
    let draft: MathAstDraft =
        serde_json::from_slice(&readback.math_ast().canonical_json(math_limits)?)?;
    let metrics =
        EquationLayoutEstimator::provisional(EquationLayoutLimits::default(), math_limits)
            .measure(draft)?;
    let native_readback = readback.canonical_json(limits)?;
    if fs::read(&input)? != bytes {
        return Err("layout oracle input changed during readback".into());
    }
    println!(
        "{}",
        serde_json::to_string(&json!({
            "schema_version": "hwpx-agent.p07-07-equation-layout-oracle/v1",
            "state": "pass",
            "input_sha256": expected_input_sha256,
            "input_bytes": bytes.len(),
            "input_unchanged": true,
            "package_parts": graph.parts.len(),
            "id_declarations": index.declarations().len(),
            "id_references": index.references().len(),
            "object_id": readback.object_id(),
            "native_object_count": readback.native_object_count(),
            "layout": expected_layout,
            "base_unit": readback.style().base_unit,
            "baseline_percent": readback.style().baseline_percent,
            "width_hwpunit": readback.extent().width_hwpunit,
            "height_hwpunit": readback.extent().height_hwpunit,
            "script_sha256": readback.script_sha256(),
            "semantic_sha256": readback.semantic_sha256(),
            "metrics": metrics,
            "native_readback_sha256": hex::encode(Sha256::digest(native_readback)),
        }))?
    );
    Ok(())
}

fn read_exact(path: &PathBuf, expected_sha256: &str) -> Result<Vec<u8>, Box<dyn Error>> {
    let metadata = fs::symlink_metadata(path)?;
    if !metadata.is_file() || metadata.file_type().is_symlink() || metadata.len() == 0 {
        return Err("layout oracle input is not a bounded regular file".into());
    }
    let length = usize::try_from(metadata.len())?;
    if length > MAX_INPUT_BYTES {
        return Err("layout oracle input exceeds limit".into());
    }
    let bytes = fs::read(path)?;
    if hex::encode(Sha256::digest(&bytes)) != expected_sha256 {
        return Err("layout oracle input identity mismatched".into());
    }
    Ok(bytes)
}

fn parse_layout(value: &str) -> Result<EquationLayoutMode, Box<dyn Error>> {
    match value {
        "inline" => Ok(EquationLayoutMode::Inline),
        "display" => Ok(EquationLayoutMode::Display),
        _ => Err("expected layout is invalid".into()),
    }
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
