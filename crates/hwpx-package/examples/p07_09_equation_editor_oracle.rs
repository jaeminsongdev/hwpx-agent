use std::env;
use std::error::Error;
use std::fs;
use std::io::Cursor;
use std::path::PathBuf;

use hwpx_package::{
    BoundedZipReader, EQUATION_HWPX_PROFILE_ID, EquationHwpxLimits, EquationHwpxReader, IdIndex,
    IdIndexLimits, IdRuleProfile, PackageGraph, PackageGraphLimits, PackageLimits, PartRole,
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
        || readback.extent().width_hwpunit == 0
        || readback.extent().height_hwpunit == 0
    {
        return Err("native equation editor semantic readback mismatch".into());
    }
    let package_graph_sha256 = package_state_sha256(&graph);
    let native_object_count = u32::try_from(readback.native_object_count())?;
    let document_flow_sha256 = flow_sha256(
        readback.object_id(),
        readback.semantic_sha256(),
        readback.script_sha256(),
        native_object_count,
    );
    let anchor_fingerprint_sha256 = anchor_sha256(
        readback.object_id(),
        readback.style().base_unit,
        readback.style().baseline_percent,
    );
    if fs::read(&input)? != bytes {
        return Err("oracle input changed during readback".into());
    }
    println!(
        "{}",
        serde_json::to_string(&json!({
            "schema_version": "hwpx-agent.p07-09-equation-editor-oracle/v1",
            "state": "pass",
            "input_unchanged": true,
            "snapshot": {
                "artifact_sha256": input_sha256,
                "package_graph_sha256": package_graph_sha256,
                "document_flow_sha256": document_flow_sha256,
                "object_id": readback.object_id(),
                "semantic_sha256": readback.semantic_sha256(),
                "script_sha256": readback.script_sha256(),
                "native_object_count": native_object_count,
            },
            "anchor_fingerprint_sha256": anchor_fingerprint_sha256,
            "package_parts": graph.parts.len(),
            "id_declarations": index.declarations().len(),
            "id_references": index.references().len(),
            "layout": readback.layout(),
            "base_unit": readback.style().base_unit,
            "baseline_percent": readback.style().baseline_percent,
            "width_hwpunit": readback.extent().width_hwpunit,
            "height_hwpunit": readback.extent().height_hwpunit,
        }))?
    );
    Ok(())
}

fn package_state_sha256(graph: &PackageGraph) -> String {
    let mut digest = Sha256::new();
    digest.update(EQUATION_HWPX_PROFILE_ID.as_bytes());
    digest.update(b"\0package-state\0");
    digest.update(graph.package_document.as_str().as_bytes());
    for part in &graph.parts {
        digest.update(b"\0part\0");
        digest.update(part.path.as_str().as_bytes());
        digest.update([match part.role {
            PartRole::Infrastructure => 0,
            PartRole::ManifestListed => 1,
            PartRole::SpineDocument => 2,
        }]);
        digest.update(part.media_type.as_str().as_bytes());
        digest.update(part.expanded_size.to_be_bytes());
        digest.update(part.raw_sha256);
    }
    hex(digest.finalize().into())
}

fn flow_sha256(object_id: u32, semantic: &str, script: &str, count: u32) -> String {
    let mut digest = Sha256::new();
    digest.update(EQUATION_HWPX_PROFILE_ID.as_bytes());
    digest.update(b"\0equation-editor-flow\0");
    digest.update(object_id.to_be_bytes());
    digest.update(semantic.as_bytes());
    digest.update(script.as_bytes());
    digest.update(count.to_be_bytes());
    hex(digest.finalize().into())
}

fn anchor_sha256(object_id: u32, base_unit: u32, baseline_percent: u8) -> String {
    let mut digest = Sha256::new();
    digest.update(EQUATION_HWPX_PROFILE_ID.as_bytes());
    digest.update(b"\0equation-editor-anchor\0");
    digest.update(SECTION_PATH.as_bytes());
    digest.update(object_id.to_be_bytes());
    digest.update(base_unit.to_be_bytes());
    digest.update([baseline_percent]);
    hex(digest.finalize().into())
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
