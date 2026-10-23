use std::error::Error;
use std::fmt::Write as _;
use std::io::{Cursor, Read, Write};
use std::path::Path;

use hwpx_package::{BoundedZipReader, PackageGraph, PackageGraphLimits, PackageLimits};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use zip::write::SimpleFileOptions;
use zip::{DateTime, ZipArchive, ZipWriter};

pub const SECTION_PATH: &str = "Contents/section0.xml";
pub const FLOW_BEFORE: &str = "6dbb7d71c2b613710791078547572170b0ed4c941fd57dfae241b15a0bbf2b58";
pub const FLOW_AFTER: &str = "bf8224d4c930213a409e214e88e3fbbcf8c57e80872d075bcdcb058882e61e85";
const MAX_PACKAGE_BYTES: usize = 32 * 1024 * 1024;
const MAX_PART_BYTES: usize = 16 * 1024 * 1024;
const MAX_PARTS: usize = 256;

pub type AnyError = Box<dyn Error>;

#[derive(Clone, Serialize)]
pub struct LoweringEvidence {
    pub profile_id: String,
    pub capability_id: String,
    pub plan_sha256: String,
    pub source_section_sha256: String,
    pub output_section_sha256: String,
    pub modified_unit_count: usize,
}

pub struct PreparedCase {
    pub case_id: String,
    pub feature_id: String,
    pub capability_id: String,
    pub file: String,
    pub bytes: Vec<u8>,
    pub output_section_sha256: String,
    pub lowering_evidence: Vec<LoweringEvidence>,
    pub object_kind: String,
    pub native_object_id: u32,
    pub native_instance_id: u32,
    pub resource_integrity_expected: bool,
}

pub struct InsertionSources {
    pub manifest_sha256: String,
    pub shape: Vec<u8>,
    pub image: Vec<u8>,
    pub text_box: Vec<u8>,
    pub freeform: Vec<u8>,
}

pub fn load_insertion_sources(directory: &Path) -> Result<InsertionSources, AnyError> {
    if !directory.is_absolute() || !directory.is_dir() {
        return Err("insertion fixture directory must be an existing absolute directory".into());
    }
    let manifest_bytes = read_bounded(&directory.join("fixture-manifest.json"), 1024 * 1024)?;
    let manifest: serde_json::Value = serde_json::from_slice(&manifest_bytes)?;
    if manifest["schema_version"] != "hwpx-agent.p08-18-object-insert-target-fixture/v1"
        || manifest["cases"].as_array().map(Vec::len) != Some(4)
        || manifest["actual_hangul_2020"] != false
    {
        return Err("insertion fixture manifest is outside the P08-18 contract".into());
    }
    let shape = load_manifest_case(
        directory,
        &manifest,
        "OBJ-001",
        "obj.shape_insert",
        "obj-001-shape-insert.hwpx",
    )?;
    let image = load_manifest_case(
        directory,
        &manifest,
        "OBJ-002",
        "obj.image_insert",
        "obj-002-image-insert.hwpx",
    )?;
    let text_box = load_manifest_case(
        directory,
        &manifest,
        "OBJ-007",
        "obj.textbox_insert",
        "obj-007-textbox-insert.hwpx",
    )?;
    let freeform = load_manifest_case(
        directory,
        &manifest,
        "OBJ-042",
        "obj.freeform",
        "obj-042-freeform-insert.hwpx",
    )?;
    Ok(InsertionSources {
        manifest_sha256: sha256(&manifest_bytes),
        shape,
        image,
        text_box,
        freeform,
    })
}

fn load_manifest_case(
    directory: &Path,
    manifest: &serde_json::Value,
    feature_id: &str,
    capability_id: &str,
    file: &str,
) -> Result<Vec<u8>, AnyError> {
    let case = manifest["cases"]
        .as_array()
        .ok_or("insertion cases are missing")?
        .iter()
        .find(|case| case["feature_id"] == feature_id)
        .ok_or("required insertion case is missing")?;
    if case["capability_id"] != capability_id || case["file"] != file {
        return Err("insertion case identity is invalid".into());
    }
    let expected_sha256 = case["package_sha256"]
        .as_str()
        .ok_or("insertion package digest is missing")?;
    let expected_bytes = case["package_bytes"]
        .as_u64()
        .ok_or("insertion package length is missing")?;
    let bytes = read_bounded(&directory.join(file), MAX_PACKAGE_BYTES)?;
    if sha256(&bytes) != expected_sha256 || u64::try_from(bytes.len())? != expected_bytes {
        return Err("insertion package differs from manifest evidence".into());
    }
    validate_package(&bytes)?;
    Ok(bytes)
}

pub fn copied_insertion_cases(sources: &InsertionSources) -> Result<Vec<PreparedCase>, AnyError> {
    Ok(vec![
        copied_case(
            "P08-19-C01",
            "OBJ-001",
            "obj.shape_insert",
            "obj-001-shape-insert.hwpx",
            &sources.shape,
            "rectangle",
            8_101,
            18_101,
            false,
        )?,
        copied_case(
            "P08-19-C02",
            "OBJ-002",
            "obj.image_insert",
            "obj-002-image-insert.hwpx",
            &sources.image,
            "picture",
            8_102,
            18_102,
            true,
        )?,
        copied_case(
            "P08-19-C03",
            "OBJ-007",
            "obj.textbox_insert",
            "obj-007-textbox-insert.hwpx",
            &sources.text_box,
            "textbox",
            8_107,
            18_107,
            false,
        )?,
        copied_case(
            "P08-19-C04",
            "OBJ-042",
            "obj.freeform",
            "obj-042-freeform-insert.hwpx",
            &sources.freeform,
            "polygon",
            8_142,
            18_142,
            false,
        )?,
    ])
}

#[allow(clippy::too_many_arguments)]
fn copied_case(
    case_id: &str,
    feature_id: &str,
    capability_id: &str,
    file: &str,
    bytes: &[u8],
    object_kind: &str,
    native_object_id: u32,
    native_instance_id: u32,
    resource_integrity_expected: bool,
) -> Result<PreparedCase, AnyError> {
    let section = section_from_package(bytes)?;
    Ok(PreparedCase {
        case_id: case_id.to_owned(),
        feature_id: feature_id.to_owned(),
        capability_id: capability_id.to_owned(),
        file: file.to_owned(),
        bytes: bytes.to_vec(),
        output_section_sha256: sha256(&section),
        lowering_evidence: vec![LoweringEvidence {
            profile_id: "hwpx-agent.p08-18-object-insert-target-fixture/v1".to_owned(),
            capability_id: capability_id.to_owned(),
            plan_sha256: sources_digest(bytes, capability_id),
            source_section_sha256: String::new(),
            output_section_sha256: sha256(&section),
            modified_unit_count: 1,
        }],
        object_kind: object_kind.to_owned(),
        native_object_id,
        native_instance_id,
        resource_integrity_expected,
    })
}

#[allow(clippy::too_many_arguments)] // One constructor keeps every manifest identity binding explicit.
pub fn prepared_from_section(
    case_id: &str,
    feature_id: &str,
    capability_id: &str,
    file: &str,
    source_package: &[u8],
    output_section: &[u8],
    lowering_evidence: Vec<LoweringEvidence>,
    object_kind: &str,
    native_object_id: u32,
    native_instance_id: u32,
    resource_integrity_expected: bool,
) -> Result<PreparedCase, AnyError> {
    let package = package_with_section(source_package, output_section)
        .map_err(|error| format!("{feature_id} package rebuild failed: {error}"))?;
    Ok(PreparedCase {
        case_id: case_id.to_owned(),
        feature_id: feature_id.to_owned(),
        capability_id: capability_id.to_owned(),
        file: file.to_owned(),
        bytes: package,
        output_section_sha256: sha256(output_section),
        lowering_evidence,
        object_kind: object_kind.to_owned(),
        native_object_id,
        native_instance_id,
        resource_integrity_expected,
    })
}

pub fn section_from_package(bytes: &[u8]) -> Result<Vec<u8>, AnyError> {
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let entry = reader
        .entries()
        .iter()
        .find(|entry| entry.path.as_str() == SECTION_PATH)
        .map(|entry| entry.index)
        .ok_or("section0 is missing")?;
    Ok(reader.read_entry(entry)?)
}

pub fn package_with_section(
    source_package: &[u8],
    output_section: &[u8],
) -> Result<Vec<u8>, AnyError> {
    let package = replace_section_archive(source_package, output_section)?;
    validate_package(&package)?;
    Ok(package)
}

pub fn package_with_section_and_text_replacement(
    source_package: &[u8],
    output_section: &[u8],
    part_path: &str,
    source_text: &str,
    target_text: &str,
) -> Result<Vec<u8>, AnyError> {
    let package = replace_archive(
        source_package,
        output_section,
        Some((part_path, source_text, target_text)),
    )?;
    validate_package(&package)?;
    Ok(package)
}

fn validate_package(bytes: &[u8]) -> Result<(), AnyError> {
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    Ok(())
}

fn replace_section_archive(source: &[u8], section: &[u8]) -> Result<Vec<u8>, AnyError> {
    replace_archive(source, section, None)
}

fn replace_archive(
    source: &[u8],
    section: &[u8],
    text_replacement: Option<(&str, &str, &str)>,
) -> Result<Vec<u8>, AnyError> {
    if source.len() > MAX_PACKAGE_BYTES || section.len() > MAX_PART_BYTES {
        return Err("package or section exceeds the fixture limit".into());
    }
    let mut archive = ZipArchive::new(Cursor::new(source))?;
    if archive.is_empty() || archive.len() > MAX_PARTS {
        return Err("package part count is outside the fixture limit".into());
    }
    let mut parts = Vec::with_capacity(archive.len());
    let mut replaced = 0_usize;
    let mut text_replaced = usize::from(text_replacement.is_none());
    for index in 0..archive.len() {
        let mut entry = archive.by_index(index)?;
        if entry.size() > MAX_PART_BYTES as u64 || entry.name().contains('\\') {
            return Err("package part is outside the fixture policy".into());
        }
        let name = entry.name().to_owned();
        let method = entry.compression();
        let mut bytes = Vec::new();
        entry.read_to_end(&mut bytes)?;
        if name == SECTION_PATH {
            bytes = section.to_vec();
            replaced += 1;
        }
        if let Some((part_path, source_text, target_text)) = text_replacement
            && name == part_path
        {
            let current = std::str::from_utf8(&bytes)?;
            let updated = current.replacen(source_text, target_text, 1);
            if updated == current || updated.contains(source_text) {
                return Err("package text replacement is absent or ambiguous".into());
            }
            bytes = updated.into_bytes();
            text_replaced += 1;
        }
        parts.push((name, bytes, method));
    }
    if replaced != 1 || text_replaced != 1 {
        return Err("package replacement is absent or ambiguous".into());
    }
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    for (name, bytes, method) in parts {
        let options = SimpleFileOptions::default()
            .compression_method(method)
            .last_modified_time(DateTime::default());
        writer.start_file(name, options)?;
        writer.write_all(&bytes)?;
    }
    let output = writer.finish()?.into_inner();
    if output.len() > MAX_PACKAGE_BYTES {
        return Err("output package exceeds the fixture limit".into());
    }
    Ok(output)
}

fn read_bounded(path: &Path, limit: usize) -> Result<Vec<u8>, AnyError> {
    let metadata = path.metadata()?;
    if !metadata.is_file() || metadata.len() > limit as u64 {
        return Err("fixture input is outside its finite file limit".into());
    }
    Ok(std::fs::read(path)?)
}

fn sources_digest(bytes: &[u8], label: &str) -> String {
    let mut digest = Sha256::new();
    digest.update(label.as_bytes());
    digest.update([0]);
    digest.update(bytes);
    hex(digest.finalize().into())
}

pub fn sha256(bytes: &[u8]) -> String {
    hex(Sha256::digest(bytes).into())
}

pub fn hex(bytes: [u8; 32]) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let mut output = String::with_capacity(64);
    for byte in bytes {
        let _ = write!(output, "{byte:02x}");
    }
    debug_assert!(output.bytes().all(|byte| DIGITS.contains(&byte)));
    output
}
