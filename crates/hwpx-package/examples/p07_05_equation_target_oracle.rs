use std::env;
use std::error::Error;
use std::fmt::Write as _;
use std::fs;
use std::io::Cursor;
use std::path::PathBuf;

use hwpx_package::{
    BoundedZipReader, EquationExtentSource, EquationHwpxLimits, EquationHwpxReader, EquationLayout,
    IdIndex, IdIndexLimits, IdRuleProfile, PackageGraph, PackageGraphLimits, PackageLimits,
};
use serde_json::json;
use sha2::{Digest as _, Sha256};

const MAX_INPUT_BYTES: usize = 8 * 1024 * 1024;
const SECTION_PATH: &str = "Contents/section0.xml";
const OBJECT_ID: u32 = 2_200_000_001;

fn main() -> Result<(), Box<dyn Error>> {
    let mut arguments = env::args_os();
    let _program = arguments.next();
    let input = PathBuf::from(arguments.next().ok_or("input HWPX is required")?);
    let expected_sha256 = argument(&mut arguments, "expected input SHA-256")?;
    let expected_semantic_sha256 = argument(&mut arguments, "expected semantic SHA-256")?;
    if arguments.next().is_some()
        || !is_digest(&expected_sha256)
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
    if input_sha256 != expected_sha256 {
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
    let readback = EquationHwpxReader::read_in_package(
        &mut reader,
        &graph,
        SECTION_PATH,
        0,
        EquationHwpxLimits::default(),
    )?;
    if readback.object_id() == 0
        || readback.layout() != EquationLayout::Display
        || readback.style().base_unit != 1_000
        || readback.style().baseline_percent != 85
        || readback.style().text_color.red != 0
        || readback.style().text_color.green != 0
        || readback.style().text_color.blue != 0
        || readback.extent().width_hwpunit != 17_000
        || readback.extent().height_hwpunit != 6_000
        || readback.extent().source != EquationExtentSource::Provisional
        || !readback.extent().render_required
        || readback.semantic_sha256() != expected_semantic_sha256
        || readback.native_object_count() != 1
    {
        return Err("native equation semantic readback mismatch".into());
    }
    if fs::read(&input)? != bytes {
        return Err("oracle input changed during readback".into());
    }
    let result = json!({
        "schema_version": "hwpx-agent.p07-05-equation-target-oracle/v1",
        "state": "pass",
        "input_sha256": input_sha256,
        "input_unchanged": true,
        "package_parts": graph.parts.len(),
        "id_declarations": index.declarations().len(),
        "id_references": index.references().len(),
        "source_object_id": OBJECT_ID,
        "saved_object_id": readback.object_id(),
        "object_id_remapped": readback.object_id() != OBJECT_ID,
        "layout": "display",
        "semantic_sha256": readback.semantic_sha256(),
        "script_sha256": readback.script_sha256(),
        "native_object_count": readback.native_object_count(),
        "render_required": readback.extent().render_required,
        "native_readback": serde_json::from_slice::<serde_json::Value>(
            &readback.canonical_json(EquationHwpxLimits::default())?
        )?
    });
    println!("{}", serde_json::to_string(&result)?);
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
    let mut output = String::with_capacity(64);
    for byte in value {
        let _ = write!(output, "{byte:02x}");
    }
    output
}
