use std::env;
use std::error::Error;
use std::fs;
use std::io::Cursor;
use std::path::PathBuf;

use hwpx_package::{
    BoundedZipReader, EquationHwpxLimits, EquationHwpxReader, IdIndex, IdIndexLimits,
    IdRuleProfile, PackageGraph, PackageGraphLimits, PackageLimits,
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
    let expected_script_sha256 = argument(&mut arguments, "expected script SHA-256")?;
    let expected_semantic_sha256 = argument(&mut arguments, "expected semantic SHA-256")?;
    if arguments.next().is_some()
        || !is_digest(&expected_input_sha256)
        || !is_digest(&expected_script_sha256)
        || !is_digest(&expected_semantic_sha256)
    {
        return Err("target oracle arguments are invalid".into());
    }
    let metadata = fs::symlink_metadata(&input)?;
    if !metadata.is_file() || metadata.file_type().is_symlink() || metadata.len() == 0 {
        return Err("input is not a bounded regular file".into());
    }
    let length = usize::try_from(metadata.len())?;
    if length > MAX_INPUT_BYTES {
        return Err("input exceeds target oracle limit".into());
    }
    let bytes = fs::read(&input)?;
    let input_sha256 = hex(Sha256::digest(&bytes).into());
    if input_sha256 != expected_input_sha256 {
        return Err("input identity mismatch".into());
    }
    let mut reader =
        BoundedZipReader::open(Cursor::new(bytes.as_slice()), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    let index = IdIndex::build(
        &mut reader,
        &graph,
        IdRuleProfile::current_hancom_2020_equation_v4(),
        IdIndexLimits::default(),
    )?;
    let readback = EquationHwpxReader::read_automation_in_package(
        &mut reader,
        &graph,
        SECTION_PATH,
        0,
        EquationHwpxLimits::default(),
    )?;
    if readback.object_id() == 0
        || readback.native_object_count() != 1
        || readback.script_sha256() != expected_script_sha256
        || readback.semantic_sha256() != expected_semantic_sha256
        || readback.style().base_unit != 1_000
        || readback.style().text_color.red != 0
        || readback.style().text_color.green != 0
        || readback.style().text_color.blue != 0
        || readback.extent().width_hwpunit == 0
        || readback.extent().height_hwpunit == 0
    {
        return Err("native equation automation semantic readback mismatch".into());
    }
    if fs::read(&input)? != bytes {
        return Err("oracle input changed during readback".into());
    }
    println!(
        "{}",
        serde_json::to_string(&json!({
            "schema_version": "hwpx-agent.p07-06-equation-automation-oracle/v1",
            "state": "pass",
            "input_sha256": input_sha256,
            "input_bytes": bytes.len(),
            "input_unchanged": true,
            "package_parts": graph.parts.len(),
            "id_declarations": index.declarations().len(),
            "id_references": index.references().len(),
            "object_id": readback.object_id(),
            "layout": readback.layout(),
            "semantic_sha256": readback.semantic_sha256(),
            "script_sha256": readback.script_sha256(),
            "native_object_count": readback.native_object_count(),
            "base_unit": readback.style().base_unit,
            "baseline_percent": readback.style().baseline_percent,
            "text_color": readback.style().text_color,
            "width_hwpunit": readback.extent().width_hwpunit,
            "height_hwpunit": readback.extent().height_hwpunit,
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

fn hex(value: [u8; 32]) -> String {
    hex::encode(value)
}
