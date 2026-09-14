use std::collections::HashSet;
use std::env;
use std::error::Error;
use std::fmt::Write as _;
use std::fs;
use std::io::{Cursor, Read, Write};
use std::path::{Path, PathBuf};

use domain_ir::MathAstDraft;
use equation_engine::{
    EQEDIT_ADAPTER_SCHEMA_VERSION, EQEDIT_PROFILE_VERSION, EqEditEngine, EqEditParseRequestDraft,
};
use hwpx_package::{
    BoundedZipReader, EQUATION_HWPX_PROFILE_ID, EQUATION_HWPX_SCHEMA_VERSION, EquationExtent,
    EquationExtentSource, EquationHwpxBuilder, EquationHwpxLimits, EquationHwpxLowerer,
    EquationHwpxReader, EquationHwpxRequest, EquationHwpxRequestDraft, EquationLayout,
    EquationStyle, Hancom2020Vs0Builder, IdIndexLimits, PackageGraph, PackageGraphLimits,
    PackageLimits, PreservingWriter, WriterLimits,
};
use serde::Deserialize;
use serde_json::{Value, json};
use sha2::{Digest as _, Sha256};
use zip::write::SimpleFileOptions;
use zip::{DateTime, ZipArchive, ZipWriter};

const PLAN_SCHEMA: &str = "hwpx-agent.p07-07-equation-layout-target-plan/v1";
const TARGET_SCHEMA: &str = "hwpx-agent.p07-07-equation-layout-target-evidence/v1";
const PROFILE: &str = "hwpx-agent.equation-layout.hangul-2020-11.0.0.9136-x86-ko-KR/v1";
const SECTION_PATH: &str = "Contents/section0.xml";
const DIRECT_TARGET_EVIDENCE_SCHEMA: &str =
    "hwpx-agent.p07-05-native-equation-current-2020-evidence/v1";
const TARGET_EXE_SHA256: &str = "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce";
const MAX_JSON_BYTES: u64 = 8 * 1024 * 1024;
const MAX_HWPX_BYTES: u64 = 16 * 1024 * 1024;
const MAX_BASE_BYTES: usize = 2 * 1024 * 1024;
const MAX_PART_BYTES: usize = 1024 * 1024;
const MAX_PARTS: usize = 32;

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
#[allow(clippy::struct_field_names)]
struct Plan {
    schema_version: String,
    profile_version: String,
    revision: String,
    sample_manifest_sha256: String,
    tier_b_plan_file_sha256: String,
    tier_b_plan_sha256: String,
    harness_sha256: String,
    oracle_executable_sha256: String,
    samples: Vec<PlanSample>,
    plan_sha256: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct PlanSample {
    id: String,
    ordinal: usize,
    corpus_case_id: String,
    layout: String,
    base_unit: u32,
    script: String,
    script_sha256: String,
    semantic_sha256: String,
    metrics: Value,
}

#[allow(clippy::too_many_lines)]
fn main() -> Result<(), Box<dyn Error>> {
    let mut arguments = env::args_os();
    let _program = arguments.next();
    let plan_path = PathBuf::from(arguments.next().ok_or("plan path is required")?);
    let expected_plan_sha256 = argument(&mut arguments, "expected plan SHA-256")?;
    let target_evidence_path =
        PathBuf::from(arguments.next().ok_or("target evidence path is required")?);
    let expected_target_evidence_sha256 =
        argument(&mut arguments, "expected target evidence SHA-256")?;
    let direct_target_evidence_path = PathBuf::from(
        arguments
            .next()
            .ok_or("direct target evidence path is required")?,
    );
    let expected_direct_target_evidence_sha256 =
        argument(&mut arguments, "expected direct target evidence SHA-256")?;
    if arguments.next().is_some()
        || !is_digest(&expected_plan_sha256)
        || !is_digest(&expected_target_evidence_sha256)
        || !is_digest(&expected_direct_target_evidence_sha256)
    {
        return Err("differential arguments are invalid".into());
    }

    let plan_bytes = read_exact(&plan_path, &expected_plan_sha256, MAX_JSON_BYTES)?;
    let target_evidence_bytes = read_exact(
        &target_evidence_path,
        &expected_target_evidence_sha256,
        MAX_JSON_BYTES,
    )?;
    let direct_target_evidence_bytes = read_exact(
        &direct_target_evidence_path,
        &expected_direct_target_evidence_sha256,
        MAX_JSON_BYTES,
    )?;
    let plan: Plan = serde_json::from_slice(&plan_bytes)?;
    let target_evidence: Value = serde_json::from_slice(&target_evidence_bytes)?;
    let direct_target_evidence: Value = serde_json::from_slice(&direct_target_evidence_bytes)?;
    validate_top_level(
        &plan,
        &target_evidence,
        &direct_target_evidence,
        &expected_plan_sha256,
    )?;

    let run_directory = plan_path
        .parent()
        .ok_or("plan parent is missing")?
        .canonicalize()?;
    if target_evidence_path.canonicalize()?.parent() != Some(run_directory.as_path()) {
        return Err("target evidence is outside the plan run".into());
    }
    let target_samples = target_evidence["samples"]
        .as_array()
        .ok_or("target sample list is invalid")?;
    if target_samples.len() != 8 || plan.samples.len() != 8 {
        return Err("differential sample count is invalid".into());
    }

    let mut ids = HashSet::with_capacity(8);
    let mut receipts = Vec::with_capacity(8);
    for (index, sample) in plan.samples.iter().enumerate() {
        validate_plan_sample(sample, index, &mut ids)?;
        let target_sample = target_samples
            .iter()
            .find(|value| value["id"].as_str() == Some(sample.id.as_str()))
            .ok_or("target sample is missing")?;
        let target_artifact_sha256 = target_sample["artifact_sha256"]
            .as_str()
            .filter(|value| is_digest(value))
            .ok_or("target artifact digest is invalid")?;
        let target_artifact_path = run_directory.join(format!("{}.hwpx", sample.id));
        let target_bytes = read_exact(
            &target_artifact_path,
            target_artifact_sha256,
            MAX_HWPX_BYTES,
        )?;
        let target_readback = read_target(&target_bytes)?;
        let expected_layout = parse_layout(&sample.layout)?;
        if target_readback.layout() != expected_layout
            || target_readback.semantic_sha256() != sample.semantic_sha256
            || target_readback.script_sha256() != sample.script_sha256
            || target_readback.style().base_unit != sample.base_unit
            || target_readback.native_object_count() != 1
        {
            return Err("target automation semantic state mismatched".into());
        }

        let direct = build_direct(sample, expected_layout, u32::try_from(index)?)?;
        if direct.semantic_sha256 != sample.semantic_sha256
            || direct.script_sha256 != sample.script_sha256
        {
            return Err("direct semantic state mismatched".into());
        }
        if fs::read(&target_artifact_path)? != target_bytes {
            return Err("target artifact changed during differential read".into());
        }
        receipts.push(json!({
            "id": sample.id,
            "ordinal": index,
            "layout": sample.layout,
            "semantic_sha256": sample.semantic_sha256,
            "script_sha256": sample.script_sha256,
            "direct_artifact_sha256": direct.artifact_sha256,
            "direct_artifact_bytes": direct.artifact_bytes,
            "target_artifact_sha256": target_artifact_sha256,
            "direct_and_automation_semantic_equal": true,
            "direct_and_automation_script_equal": true,
            "direct_and_automation_layout_equal": true
        }));
    }
    if fs::read(&plan_path)? != plan_bytes
        || fs::read(&target_evidence_path)? != target_evidence_bytes
        || fs::read(&direct_target_evidence_path)? != direct_target_evidence_bytes
    {
        return Err("differential input changed during validation".into());
    }

    println!(
        "{}",
        serde_json::to_string(&json!({
            "schema_version": "hwpx-agent.p07-equation-differential-receipt/v1",
            "state": "pass",
            "profile_version": PROFILE,
            "plan_file_sha256": expected_plan_sha256,
            "target_evidence_sha256": expected_target_evidence_sha256,
            "direct_target_evidence_sha256": expected_direct_target_evidence_sha256,
            "case_count": 8,
            "semantic_equal_count": 8,
            "script_equal_count": 8,
            "layout_equal_count": 8,
            "silent_fallback_count": 0,
            "cases": receipts,
            "direct_component_generation": true,
            "direct_exact_target_compatibility": true,
            "automation_exact_target_execution": true,
            "actual_hangul_target_side": true,
            "byte_identity_required": false,
            "object_id_identity_required": false,
            "render_claimed_by_differential": false,
            "other_hangul_versions": false,
            "p07_complete_asserted_by_oracle": false,
            "product_complete": false
        }))?
    );
    Ok(())
}

struct DirectResult {
    semantic_sha256: String,
    script_sha256: String,
    artifact_sha256: String,
    artifact_bytes: usize,
}

fn build_direct(
    sample: &PlanSample,
    layout: EquationLayout,
    index: u32,
) -> Result<DirectResult, Box<dyn Error>> {
    let source_bytes = build_source(layout)?;
    let mut reader = BoundedZipReader::open(
        Cursor::new(source_bytes.as_slice()),
        PackageLimits::default(),
    )?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    let limits = EquationHwpxLimits::default();
    let run_ordinal = usize::from(layout == EquationLayout::Inline);
    let source = EquationHwpxBuilder::inspect_source(
        &mut reader,
        &graph,
        SECTION_PATH,
        1,
        run_ordinal,
        layout,
        limits,
    )
    .map_err(|error| format!("{} direct source inspection failed: {error}", sample.id))?;
    let parsed = EqEditEngine::new(limits.eqedit, limits.math)?.parse(EqEditParseRequestDraft {
        schema_version: EQEDIT_ADAPTER_SCHEMA_VERSION.to_owned(),
        profile_version: EQEDIT_PROFILE_VERSION.to_owned(),
        source: sample.script.clone(),
    })?;
    let math_ast: MathAstDraft =
        serde_json::from_slice(&parsed.ast().canonical_json(limits.math)?)?;
    let before_flow = digest_label(format!("p07-differential-before-{index}").as_bytes());
    let after_flow = digest_label(format!("p07-differential-after-{index}").as_bytes());
    let request = EquationHwpxRequest::from_draft(
        EquationHwpxRequestDraft {
            schema_version: EQUATION_HWPX_SCHEMA_VERSION.to_owned(),
            profile_id: EQUATION_HWPX_PROFILE_ID.to_owned(),
            section_part: source.section_part().to_owned(),
            paragraph_ordinal: 1,
            run_ordinal,
            expected_package_state_sha256: source.package_state_sha256().to_owned(),
            expected_section_sha256: source.section_sha256().to_owned(),
            expected_paragraph_sha256: source.paragraph_sha256().to_owned(),
            expected_run_sha256: source.run_sha256().to_owned(),
            expected_object_ids_sha256: source.object_ids_sha256().to_owned(),
            expected_document_flow_sha256: before_flow.clone(),
            target_document_flow_sha256: after_flow,
            object_id: 2_300_000_001_u32
                .checked_add(index)
                .ok_or("object ID overflow")?,
            layout,
            style: EquationStyle::default(),
            extent: EquationExtent {
                width_hwpunit: 20_000,
                height_hwpunit: 8_000,
                source: EquationExtentSource::Provisional,
                source_evidence_sha256: None,
                render_required: true,
            },
            math_ast,
        },
        &source,
        &before_flow,
        limits,
    )
    .map_err(|error| format!("{} direct request admission failed: {error}", sample.id))?;
    let request_json: Value = serde_json::from_slice(&request.canonical_json(limits)?)?;
    let direct_script_sha256 = request_json["script_sha256"]
        .as_str()
        .filter(|value| is_digest(value))
        .ok_or("direct request script digest is invalid")?
        .to_owned();
    let lowered = EquationHwpxLowerer::lower(&mut reader, &graph, &request, &before_flow, limits)
        .map_err(|error| format!("{} direct lowering failed: {error}", sample.id))?;
    let artifact = PreservingWriter::build(
        lowered.patch(),
        PackageLimits::default(),
        PackageGraphLimits::default(),
        IdIndexLimits::default(),
        WriterLimits::default(),
    )?;
    artifact.verify()?;
    Ok(DirectResult {
        semantic_sha256: request.semantic_sha256().to_owned(),
        script_sha256: direct_script_sha256,
        artifact_sha256: hex(artifact.sha256()),
        artifact_bytes: artifact.size_bytes(),
    })
}

fn read_target(bytes: &[u8]) -> Result<hwpx_package::EquationHwpxReadback, Box<dyn Error>> {
    let limits = EquationHwpxLimits::default();
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), limits.package)?;
    let graph = PackageGraph::build(&mut reader, limits.graph)?;
    Ok(EquationHwpxReader::read_automation_in_package(
        &mut reader,
        &graph,
        SECTION_PATH,
        0,
        limits,
    )?)
}

fn validate_top_level(
    plan: &Plan,
    target: &Value,
    direct_target: &Value,
    expected_plan_sha256: &str,
) -> Result<(), Box<dyn Error>> {
    for digest in [
        &plan.sample_manifest_sha256,
        &plan.tier_b_plan_file_sha256,
        &plan.tier_b_plan_sha256,
        &plan.harness_sha256,
        &plan.oracle_executable_sha256,
        &plan.plan_sha256,
    ] {
        if !is_digest(digest) {
            return Err("plan digest is invalid".into());
        }
    }
    if plan.schema_version != PLAN_SCHEMA
        || plan.profile_version != PROFILE
        || plan.revision.is_empty()
        || target["schema_version"] != TARGET_SCHEMA
        || target["profile_version"] != PROFILE
        || target["state"] != "native_pass_visual_not_run"
        || target["plan_file_sha256"] != expected_plan_sha256
        || target["actual_hangul"] != true
        || direct_target["schema_version"] != DIRECT_TARGET_EVIDENCE_SCHEMA
        || direct_target["target"]["executable_sha256"] != TARGET_EXE_SHA256
        || direct_target["claims"]["new_lowerer_actual_hangul_execution"] != true
        || direct_target["claims"]["new_lowerer_save_reopen"] != true
        || direct_target["claims"]["native_semantic_readback"] != true
    {
        return Err("differential top-level identity mismatched".into());
    }
    Ok(())
}

fn validate_plan_sample(
    sample: &PlanSample,
    index: usize,
    ids: &mut HashSet<String>,
) -> Result<(), Box<dyn Error>> {
    let _ = (&sample.corpus_case_id, &sample.metrics);
    if sample.ordinal != index
        || sample.base_unit != 1_000
        || sample.script.is_empty()
        || !is_digest(&sample.script_sha256)
        || !is_digest(&sample.semantic_sha256)
        || !ids.insert(sample.id.clone())
        || parse_layout(&sample.layout).is_err()
    {
        return Err("differential plan sample is invalid".into());
    }
    if digest_label(sample.script.as_bytes()) != sample.script_sha256 {
        return Err("differential plan script digest mismatched".into());
    }
    Ok(())
}

fn build_source(layout: EquationLayout) -> Result<Vec<u8>, Box<dyn Error>> {
    let base = Hancom2020Vs0Builder::build("P07 EQUATION DIFFERENTIAL")?;
    let bytes = base.with_verified_bytes(<[u8]>::to_vec)?;
    if bytes.len() > MAX_BASE_BYTES {
        return Err("base artifact exceeds differential limit".into());
    }
    let mut archive = ZipArchive::new(Cursor::new(bytes))?;
    if archive.is_empty() || archive.len() > MAX_PARTS {
        return Err("base artifact part count is invalid".into());
    }
    let mut parts = Vec::with_capacity(archive.len());
    for index in 0..archive.len() {
        let mut entry = archive.by_index(index)?;
        if entry.size() > MAX_PART_BYTES as u64 || entry.name().contains('\\') {
            return Err("base artifact part is outside differential policy".into());
        }
        let mut part = Vec::new();
        entry.read_to_end(&mut part)?;
        let method = entry.compression();
        let name = entry.name().to_owned();
        if name == SECTION_PATH {
            part = insert_empty_equation_paragraph(&part, layout)?;
        }
        parts.push((name, part, method));
    }
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    for (name, part, method) in parts {
        let options = SimpleFileOptions::default()
            .compression_method(method)
            .last_modified_time(DateTime::default());
        writer.start_file(name, options)?;
        writer.write_all(&part)?;
    }
    Ok(writer.finish()?.into_inner())
}

fn insert_empty_equation_paragraph(
    section: &[u8],
    layout: EquationLayout,
) -> Result<Vec<u8>, Box<dyn Error>> {
    let source = std::str::from_utf8(section)?;
    let closing = source
        .rfind("</hs:sec>")
        .ok_or("section closing tag is missing")?;
    if source.contains("<hp:equation ") || source.contains("<hp:p id=\"2\"") {
        return Err("base section already owns the target identity".into());
    }
    let paragraph = match layout {
        EquationLayout::Inline => concat!(
            "<hp:p id=\"2\" paraPrIDRef=\"0\" styleIDRef=\"0\" pageBreak=\"0\" ",
            "columnBreak=\"0\" merged=\"0\"><hp:run charPrIDRef=\"0\"><hp:t>I</hp:t>",
            "</hp:run><hp:run charPrIDRef=\"0\"><hp:t/></hp:run></hp:p>"
        ),
        EquationLayout::Display => concat!(
            "<hp:p id=\"2\" paraPrIDRef=\"0\" styleIDRef=\"0\" pageBreak=\"0\" ",
            "columnBreak=\"0\" merged=\"0\"><hp:run charPrIDRef=\"0\"><hp:t/>",
            "</hp:run></hp:p>"
        ),
    };
    let mut output = String::with_capacity(source.len() + paragraph.len());
    output.push_str(&source[..closing]);
    output.push_str(paragraph);
    output.push_str(&source[closing..]);
    Ok(output.into_bytes())
}

fn read_exact(path: &Path, expected_sha256: &str, maximum: u64) -> Result<Vec<u8>, Box<dyn Error>> {
    let metadata = fs::symlink_metadata(path)?;
    if !metadata.is_file()
        || metadata.file_type().is_symlink()
        || metadata.len() == 0
        || metadata.len() > maximum
    {
        return Err("differential input is not a bounded regular file".into());
    }
    let bytes = fs::read(path)?;
    if hex::encode(Sha256::digest(&bytes)) != expected_sha256 {
        return Err("differential input identity mismatched".into());
    }
    Ok(bytes)
}

fn parse_layout(value: &str) -> Result<EquationLayout, Box<dyn Error>> {
    match value {
        "inline" => Ok(EquationLayout::Inline),
        "display" => Ok(EquationLayout::Display),
        _ => Err("differential layout is invalid".into()),
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

fn digest_label(value: &[u8]) -> String {
    hex(Sha256::digest(value).into())
}

fn hex(value: [u8; 32]) -> String {
    let mut output = String::with_capacity(64);
    for byte in value {
        let _ = write!(output, "{byte:02x}");
    }
    output
}
