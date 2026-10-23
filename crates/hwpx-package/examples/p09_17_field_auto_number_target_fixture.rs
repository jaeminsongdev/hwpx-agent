use std::env;
use std::error::Error;
use std::fs::{self, OpenOptions};
use std::io::{Cursor, Read, Write};
use std::path::{Path, PathBuf};

use domain_ir::{
    FIELD_ENGINE_SCHEMA_VERSION, FieldAnchor, FieldCacheStatus, FieldCachedResult, FieldDefinition,
    FieldDocumentState, FieldDocumentStateDraft, FieldEngineBuilder, FieldEngineLimitConfig,
    FieldEngineLimits, FieldIdentity, FieldNumberFormat, FieldOperation, FieldRequest,
    FieldRequestDraft, FieldState, FieldUpdatePolicy, LogicalId, ObjectNumberKind,
};
use hwpx_package::{
    BoundedZipReader, FieldAutoNumberHwpxBuilder, FieldAutoNumberHwpxLimitConfig,
    FieldAutoNumberHwpxLimits, FieldAutoNumberHwpxLowerer, FieldAutoNumberHwpxReader,
    Hancom2020Vs0Builder, PackageGraph, PackageGraphLimits, PackageLimits,
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use zip::write::SimpleFileOptions;
use zip::{DateTime, ZipArchive, ZipWriter};

const SECTION_PATH: &str = "Contents/section0.xml";
const EMPTY_SHA256: &str = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";
const MAX_PACKAGE_BYTES: usize = 4 * 1024 * 1024;
const MAX_PART_BYTES: usize = 2 * 1024 * 1024;
const MAX_PARTS: usize = 64;

#[derive(Serialize)]
struct Manifest {
    schema_version: &'static str,
    target_profile: TargetProfile,
    input_file: &'static str,
    input_package_sha256: String,
    input_package_bytes: usize,
    input_section_sha256: String,
    field_projection: Vec<FieldProjection>,
    operations: Vec<OperationEvidence>,
    static_evidence: StaticEvidence,
    target_evidence: TargetEvidence,
}

#[derive(Serialize)]
struct StaticEvidence {
    retry_package_byte_exact: bool,
    stale_source_rejected_without_output: bool,
    complete_package_hwpx: bool,
}

#[derive(Serialize)]
struct TargetEvidence {
    actual_hangul_2020: bool,
    save_reopen: &'static str,
    field_readback: &'static str,
    reference_update: &'static str,
    render: &'static str,
    differential: &'static str,
}

#[derive(Serialize)]
struct TargetProfile {
    product: &'static str,
    build: &'static str,
    architecture: &'static str,
    locale: &'static str,
    executable_sha256: &'static str,
}

#[derive(Clone, Serialize)]
struct FieldProjection {
    feature_id: &'static str,
    case_id: &'static str,
    native_type: &'static str,
    number: i64,
}

#[derive(Clone, Serialize)]
struct OperationEvidence {
    feature_id: &'static str,
    case_id: &'static str,
    capability_id: String,
    operation: &'static str,
    plan_sha256: String,
    source_section_sha256: String,
    output_section_sha256: String,
    source_state_sha256: String,
    target_state_sha256: String,
    target_document_flow_sha256: String,
    inserted_auto_numbers: usize,
    updated_auto_numbers: usize,
}

struct BuiltFieldSection {
    section: Vec<u8>,
    stale_source_rejected_without_output: bool,
    operations: Vec<OperationEvidence>,
}

struct FieldBuildProgress {
    section: Vec<u8>,
    state: FieldDocumentState,
    flow: String,
    operations: Vec<OperationEvidence>,
}

struct AppliedOperation {
    section: Vec<u8>,
    state: FieldDocumentState,
    evidence: OperationEvidence,
}

fn main() -> Result<(), Box<dyn Error>> {
    let output_directory = parse_output_directory()?;
    if output_directory.exists() {
        return Err("output directory already exists".into());
    }
    let parent = output_directory
        .parent()
        .ok_or("output directory has no parent")?;
    if !parent.is_dir() {
        return Err("output parent does not exist".into());
    }
    let (first_package, first_manifest) = build_fixture()?;
    let (retry_package, _) = build_fixture()?;
    if first_package != retry_package {
        return Err("fixture generation is not byte deterministic".into());
    }
    validate_package(&first_package)?;

    fs::create_dir(&output_directory)?;
    let output = output_directory.join("output");
    fs::create_dir(&output)?;

    let input_path = output.join("p09-17-field-auto-number-input.hwpx");
    write_new(&input_path, &first_package)?;
    let manifest_bytes = serde_json::to_vec_pretty(&first_manifest)?;
    let manifest_path = output.join("fixture-manifest.json");
    write_new(&manifest_path, &manifest_bytes)?;

    println!(
        "{}",
        serde_json::to_string(&serde_json::json!({
            "state": "pass",
            "schema_version": first_manifest.schema_version,
            "output_directory": output,
            "input_package_sha256": first_manifest.input_package_sha256,
            "manifest_sha256": sha256(&manifest_bytes),
            "operation_count": first_manifest.operations.len(),
            "actual_hangul_2020": false
        }))?
    );
    Ok(())
}

fn build_fixture() -> Result<(Vec<u8>, Manifest), Box<dyn Error>> {
    let base = Hancom2020Vs0Builder::build("P09-17 field auto number target")?;
    let base_bytes = base.with_verified_bytes(<[u8]>::to_vec)?;
    let source_section = read_part(&base_bytes, SECTION_PATH)?;
    let built = build_field_section(&source_section)?;
    let package = replace_part(&base_bytes, SECTION_PATH, &built.section)?;
    if package.len() > MAX_PACKAGE_BYTES {
        return Err("fixture package exceeds bound".into());
    }
    let manifest = build_manifest(&package, &built);
    Ok((package, manifest))
}

fn build_field_section(source_section: &[u8]) -> Result<BuiltFieldSection, Box<dyn Error>> {
    let section = append_field_paragraph(source_section)?;
    let paragraph_ids = vec![logical_id("paragraph-1")?, logical_id("paragraph-2")?];
    let state_limits = state_limits()?;
    let hwpx_limits = hwpx_limits()?;
    let progress = FieldBuildProgress {
        section,
        state: empty_state(state_limits)?,
        flow: sha256(b"p09-17-flow-0"),
        operations: Vec::new(),
    };
    let progress = insert_auto_numbers(progress, &paragraph_ids, state_limits, hwpx_limits)?;
    let progress = update_page_result(progress, &paragraph_ids, state_limits, hwpx_limits)?;
    let readback = FieldAutoNumberHwpxReader::read_section(
        &progress.section,
        &progress.state,
        &paragraph_ids,
        state_limits,
        hwpx_limits,
    )?;
    if readback.auto_number_count != 4 {
        return Err("final adapter readback count mismatch".into());
    }
    let stale_source_rejected_without_output = stale_source_rejected(
        &progress.section,
        &progress.state,
        &progress.flow,
        &paragraph_ids,
        state_limits,
        hwpx_limits,
    )?;
    Ok(BuiltFieldSection {
        section: progress.section,
        stale_source_rejected_without_output,
        operations: progress.operations,
    })
}

fn insert_auto_numbers(
    mut progress: FieldBuildProgress,
    paragraph_ids: &[LogicalId],
    state_limits: FieldEngineLimits,
    hwpx_limits: FieldAutoNumberHwpxLimits,
) -> Result<FieldBuildProgress, Box<dyn Error>> {
    let insertions = vec![
        (
            "REF-006",
            "P09-17-C01",
            0_usize,
            1_u32,
            FieldDefinition::PageNumber {
                format: FieldNumberFormat::Digit,
            },
            1_i64,
        ),
        (
            "REF-008",
            "P09-17-C02",
            1,
            2,
            FieldDefinition::ObjectNumber {
                object_kind: ObjectNumberKind::Picture,
                format: FieldNumberFormat::Digit,
            },
            2,
        ),
        (
            "REF-008",
            "P09-17-C03",
            2,
            3,
            FieldDefinition::ObjectNumber {
                object_kind: ObjectNumberKind::Table,
                format: FieldNumberFormat::Digit,
            },
            3,
        ),
        (
            "REF-008",
            "P09-17-C04",
            3,
            4,
            FieldDefinition::ObjectNumber {
                object_kind: ObjectNumberKind::Equation,
                format: FieldNumberFormat::Digit,
            },
            4,
        ),
    ];
    for (ordinal, (feature, case, insertion_index, inline_ordinal, definition, number)) in
        insertions.into_iter().enumerate()
    {
        let target_flow = sha256(format!("p09-17-flow-{}", ordinal + 1).as_bytes());
        let field = field(
            &progress.section,
            u32::try_from(ordinal + 1)?,
            inline_ordinal,
            definition,
            number,
            state_limits,
            hwpx_limits,
        )?;
        let operation = FieldOperation::Insert {
            insertion_index,
            field,
        };
        let applied = apply_operation(
            &progress.section,
            &progress.state,
            &progress.flow,
            &target_flow,
            operation,
            feature,
            case,
            "insert",
            paragraph_ids,
            state_limits,
            hwpx_limits,
        )?;
        progress.section = applied.section;
        progress.state = applied.state;
        progress.flow = target_flow;
        progress.operations.push(applied.evidence);
    }
    Ok(progress)
}

fn update_page_result(
    mut progress: FieldBuildProgress,
    paragraph_ids: &[LogicalId],
    state_limits: FieldEngineLimits,
    hwpx_limits: FieldAutoNumberHwpxLimits,
) -> Result<FieldBuildProgress, Box<dyn Error>> {
    let updated_flow = sha256(b"p09-17-flow-5");
    let operation = FieldOperation::UpdateResult {
        target: progress
            .state
            .fields()
            .first()
            .ok_or("page field missing")?
            .identity
            .clone(),
        cached_result: FieldCachedResult::Number {
            value: 9,
            display: "9".to_owned(),
        },
        evaluation_context_sha256: sha256(b"p09-17-direct-update-context"),
    };
    let applied = apply_operation(
        &progress.section,
        &progress.state,
        &progress.flow,
        &updated_flow,
        operation,
        "REF-009",
        "P09-17-C05",
        "update_numeric_result",
        paragraph_ids,
        state_limits,
        hwpx_limits,
    )?;
    progress.section = applied.section;
    progress.state = applied.state;
    progress.flow = updated_flow;
    progress.operations.push(applied.evidence);
    Ok(progress)
}

fn build_manifest(package: &[u8], built: &BuiltFieldSection) -> Manifest {
    let projection = vec![
        FieldProjection {
            feature_id: "REF-006",
            case_id: "P09-17-C01",
            native_type: "PAGE",
            number: 9,
        },
        FieldProjection {
            feature_id: "REF-008",
            case_id: "P09-17-C02",
            native_type: "PICTURE",
            number: 2,
        },
        FieldProjection {
            feature_id: "REF-008",
            case_id: "P09-17-C03",
            native_type: "TABLE",
            number: 3,
        },
        FieldProjection {
            feature_id: "REF-008",
            case_id: "P09-17-C04",
            native_type: "EQUATION",
            number: 4,
        },
    ];
    Manifest {
        schema_version: "hwpx-agent.p09-17-field-auto-number-target-fixture/v1",
        target_profile: TargetProfile {
            product: "Hancom Hangul 2020",
            build: "11.0.0.9136",
            architecture: "x86",
            locale: "ko-KR",
            executable_sha256: "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce",
        },
        input_file: "p09-17-field-auto-number-input.hwpx",
        input_package_sha256: sha256(package),
        input_package_bytes: package.len(),
        input_section_sha256: sha256(&built.section),
        field_projection: projection,
        operations: built.operations.clone(),
        static_evidence: StaticEvidence {
            retry_package_byte_exact: true,
            stale_source_rejected_without_output: built.stale_source_rejected_without_output,
            complete_package_hwpx: true,
        },
        target_evidence: TargetEvidence {
            actual_hangul_2020: false,
            save_reopen: "not_run",
            field_readback: "not_run",
            reference_update: "direct_pre_target_pass_target_not_run",
            render: "not_run",
            differential: "not_run",
        },
    }
}

#[allow(clippy::too_many_arguments)]
fn apply_operation(
    section: &[u8],
    source_state: &FieldDocumentState,
    source_flow: &str,
    target_flow: &str,
    operation: FieldOperation,
    feature_id: &'static str,
    case_id: &'static str,
    operation_name: &'static str,
    paragraph_ids: &[LogicalId],
    state_limits: FieldEngineLimits,
    hwpx_limits: FieldAutoNumberHwpxLimits,
) -> Result<AppliedOperation, Box<dyn Error>> {
    let request = FieldRequest::from_draft(
        FieldRequestDraft {
            schema_version: FIELD_ENGINE_SCHEMA_VERSION.to_owned(),
            request_id: logical_id(&format!("{}-request", case_id.to_ascii_lowercase()))?,
            expected_source_state_sha256: source_state.canonical_sha256(state_limits)?,
            expected_document_flow_sha256: source_flow.to_owned(),
            target_document_flow_sha256: target_flow.to_owned(),
            operation,
        },
        source_state,
        source_flow,
        state_limits,
    )
    .map_err(|error| std::io::Error::other(format!("{case_id}: domain request: {error:?}")))?;
    let domain_plan =
        FieldEngineBuilder::plan(source_state, &request, source_flow, state_limits)
            .map_err(|error| std::io::Error::other(format!("{case_id}: domain plan: {error:?}")))?;
    let plan = FieldAutoNumberHwpxBuilder::plan(
        section,
        source_state,
        &domain_plan,
        source_flow,
        paragraph_ids,
        state_limits,
        hwpx_limits,
    )
    .map_err(|error| std::io::Error::other(format!("{case_id}: adapter plan: {error:?}")))?;
    let (output, receipt) = FieldAutoNumberHwpxLowerer::lower_section_with_receipt(
        section,
        &plan,
        source_state,
        source_flow,
        paragraph_ids,
        state_limits,
        hwpx_limits,
    )
    .map_err(|error| std::io::Error::other(format!("{case_id}: adapter lower: {error:?}")))?;
    let target_state = domain_plan.target_state().clone();
    let evidence = OperationEvidence {
        feature_id,
        case_id,
        capability_id: receipt.capability_id.to_owned(),
        operation: operation_name,
        plan_sha256: receipt.plan_sha256,
        source_section_sha256: hex(receipt.source_section_sha256),
        output_section_sha256: hex(receipt.output_section_sha256),
        source_state_sha256: receipt.source_state_sha256,
        target_state_sha256: receipt.target_state_sha256,
        target_document_flow_sha256: receipt.target_document_flow_sha256,
        inserted_auto_numbers: receipt.inserted_auto_numbers,
        updated_auto_numbers: receipt.updated_auto_numbers,
    };
    Ok(AppliedOperation {
        section: output,
        state: target_state,
        evidence,
    })
}

fn stale_source_rejected(
    section: &[u8],
    state: &FieldDocumentState,
    flow: &str,
    paragraph_ids: &[LogicalId],
    state_limits: FieldEngineLimits,
    hwpx_limits: FieldAutoNumberHwpxLimits,
) -> Result<bool, Box<dyn Error>> {
    let target_flow = sha256(b"p09-17-stale-target-flow");
    let operation = FieldOperation::UpdateResult {
        target: state.fields()[0].identity.clone(),
        cached_result: FieldCachedResult::Number {
            value: 7,
            display: "7".to_owned(),
        },
        evaluation_context_sha256: sha256(b"p09-17-stale-context"),
    };
    let request = FieldRequest::from_draft(
        FieldRequestDraft {
            schema_version: FIELD_ENGINE_SCHEMA_VERSION.to_owned(),
            request_id: logical_id("p09-17-stale-request")?,
            expected_source_state_sha256: state.canonical_sha256(state_limits)?,
            expected_document_flow_sha256: flow.to_owned(),
            target_document_flow_sha256: target_flow,
            operation,
        },
        state,
        flow,
        state_limits,
    )?;
    let domain_plan = FieldEngineBuilder::plan(state, &request, flow, state_limits)?;
    let plan = FieldAutoNumberHwpxBuilder::plan(
        section,
        state,
        &domain_plan,
        flow,
        paragraph_ids,
        state_limits,
        hwpx_limits,
    )?;
    let drifted = String::from_utf8(section.to_vec())?.replacen("P09-17-PAGE=", "P09-17-DRIFT=", 1);
    Ok(FieldAutoNumberHwpxLowerer::lower_section(
        drifted.as_bytes(),
        &plan,
        state,
        flow,
        paragraph_ids,
        state_limits,
        hwpx_limits,
    )
    .is_err())
}

fn field(
    section: &[u8],
    index: u32,
    inline_ordinal: u32,
    definition: FieldDefinition,
    number: i64,
    state_limits: FieldEngineLimits,
    hwpx_limits: FieldAutoNumberHwpxLimits,
) -> Result<FieldState, Box<dyn Error>> {
    let (paragraph_style_sha256, character_style_sha256) =
        FieldAutoNumberHwpxReader::style_sha256_at(section, 1, 0, hwpx_limits)?;
    let value = FieldState {
        identity: FieldIdentity {
            logical_field_id: logical_id(&format!("p09-17-field-{index}"))?,
            native_begin_id: index.checked_mul(2).ok_or("field id overflow")?,
            native_end_id: index
                .checked_mul(2)
                .and_then(|value| value.checked_add(1))
                .ok_or("field id overflow")?,
        },
        anchor: FieldAnchor {
            paragraph_id: logical_id("paragraph-2")?,
            run_ordinal: 0,
            inline_ordinal,
        },
        definition,
        cached_result: FieldCachedResult::Number {
            value: number,
            display: number.to_string(),
        },
        update_policy: FieldUpdatePolicy::RecomputeDirect,
        cache_status: FieldCacheStatus::Current,
        locked: false,
        evaluation_context_sha256: None,
        character_style_sha256,
        paragraph_style_sha256,
        field_payload_sha256: EMPTY_SHA256.to_owned(),
        opaque_properties: Vec::new(),
    };
    let _ = FieldDocumentState::from_draft(
        FieldDocumentStateDraft {
            schema_version: FIELD_ENGINE_SCHEMA_VERSION.to_owned(),
            fields: vec![value.clone()],
            non_field_content_sha256: sha256(b"p09-17-non-field"),
            style_catalog_sha256: sha256(b"p09-17-style-catalog"),
            reference_inventory_sha256: sha256(b"p09-17-reference-inventory"),
            resource_inventory_sha256: sha256(b"p09-17-resource-inventory"),
            opaque_document_state_sha256: sha256(b"p09-17-opaque-document"),
        },
        state_limits,
    )?;
    Ok(value)
}

fn empty_state(limits: FieldEngineLimits) -> Result<FieldDocumentState, Box<dyn Error>> {
    Ok(FieldDocumentState::from_draft(
        FieldDocumentStateDraft {
            schema_version: FIELD_ENGINE_SCHEMA_VERSION.to_owned(),
            fields: Vec::new(),
            non_field_content_sha256: sha256(b"p09-17-non-field"),
            style_catalog_sha256: sha256(b"p09-17-style-catalog"),
            reference_inventory_sha256: sha256(b"p09-17-reference-inventory"),
            resource_inventory_sha256: sha256(b"p09-17-resource-inventory"),
            opaque_document_state_sha256: sha256(b"p09-17-opaque-document"),
        },
        limits,
    )?)
}

fn append_field_paragraph(section: &[u8]) -> Result<Vec<u8>, Box<dyn Error>> {
    let source = std::str::from_utf8(section)?;
    let closing = source
        .rfind("</hs:sec>")
        .ok_or("section closing tag is missing")?;
    if source.contains("P09-17-PAGE=") {
        return Err("field fixture paragraph already exists".into());
    }
    let paragraph = concat!(
        "<hp:p id=\"2\" paraPrIDRef=\"0\" styleIDRef=\"0\" pageBreak=\"0\" ",
        "columnBreak=\"0\" merged=\"0\"><hp:run charPrIDRef=\"0\">",
        "<hp:t>P09-17-PAGE=</hp:t><hp:t>;PICTURE=</hp:t><hp:t>;TABLE=</hp:t>",
        "<hp:t>;EQUATION=</hp:t><hp:t>;END</hp:t></hp:run>",
        "<hp:linesegarray><hp:lineseg textpos=\"0\" vertpos=\"0\" vertsize=\"1000\" ",
        "textheight=\"1000\" baseline=\"850\" spacing=\"600\" horzpos=\"0\" ",
        "horzsize=\"42520\" flags=\"393216\"/></hp:linesegarray></hp:p>"
    );
    let mut output = String::with_capacity(source.len() + paragraph.len());
    output.push_str(&source[..closing]);
    output.push_str(paragraph);
    output.push_str(&source[closing..]);
    Ok(output.into_bytes())
}

fn replace_part(
    source: &[u8],
    target_path: &str,
    target: &[u8],
) -> Result<Vec<u8>, Box<dyn Error>> {
    let mut archive = ZipArchive::new(Cursor::new(source))?;
    if archive.is_empty() || archive.len() > MAX_PARTS {
        return Err("source package part count is invalid".into());
    }
    let mut parts = Vec::with_capacity(archive.len());
    let mut replaced = false;
    for index in 0..archive.len() {
        let mut entry = archive.by_index(index)?;
        if entry.is_dir() || entry.name().contains('\\') || entry.size() > MAX_PART_BYTES as u64 {
            return Err("source package part is outside fixture policy".into());
        }
        let name = entry.name().to_owned();
        let method = entry.compression();
        let mut bytes = Vec::new();
        entry.read_to_end(&mut bytes)?;
        if name == target_path {
            if replaced {
                return Err("target package part is duplicated".into());
            }
            bytes = target.to_vec();
            replaced = true;
        }
        parts.push((name, method, bytes));
    }
    if !replaced {
        return Err("target package part is missing".into());
    }
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    for (name, method, bytes) in parts {
        let options = SimpleFileOptions::default()
            .compression_method(method)
            .last_modified_time(DateTime::default())
            .system(zip::System::Unix)
            .unix_permissions(0o644);
        writer.start_file(name, options)?;
        writer.write_all(&bytes)?;
    }
    Ok(writer.finish()?.into_inner())
}

fn read_part(package: &[u8], target_path: &str) -> Result<Vec<u8>, Box<dyn Error>> {
    let mut archive = ZipArchive::new(Cursor::new(package))?;
    let mut matched = None;
    for index in 0..archive.len() {
        let mut entry = archive.by_index(index)?;
        if entry.name() != target_path {
            continue;
        }
        if matched.is_some() || entry.size() > MAX_PART_BYTES as u64 {
            return Err("target package part is duplicated or oversized".into());
        }
        let mut bytes = Vec::new();
        entry.read_to_end(&mut bytes)?;
        matched = Some(bytes);
    }
    matched.ok_or_else(|| "target package part is missing".into())
}

fn validate_package(bytes: &[u8]) -> Result<(), Box<dyn Error>> {
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    if graph.parts.is_empty() {
        return Err("package graph is empty".into());
    }
    Ok(())
}

fn state_limits() -> Result<FieldEngineLimits, Box<dyn Error>> {
    Ok(FieldEngineLimits::new(FieldEngineLimitConfig::default())?)
}

fn hwpx_limits() -> Result<FieldAutoNumberHwpxLimits, Box<dyn Error>> {
    Ok(FieldAutoNumberHwpxLimits::new(
        FieldAutoNumberHwpxLimitConfig::default(),
    )?)
}

fn logical_id(value: &str) -> Result<LogicalId, Box<dyn Error>> {
    Ok(LogicalId::parse(value)?)
}

fn parse_output_directory() -> Result<PathBuf, Box<dyn Error>> {
    let mut arguments = env::args_os();
    let _program = arguments.next();
    let output = arguments
        .next()
        .ok_or("usage: p09_17_field_auto_number_target_fixture <new-output-directory>")?;
    if arguments.next().is_some() {
        return Err("unexpected extra arguments".into());
    }
    Ok(PathBuf::from(output))
}

fn write_new(path: &Path, bytes: &[u8]) -> Result<(), Box<dyn Error>> {
    let mut file = OpenOptions::new().write(true).create_new(true).open(path)?;
    file.write_all(bytes)?;
    file.sync_all()?;
    Ok(())
}

fn sha256(bytes: &[u8]) -> String {
    hex(Sha256::digest(bytes).into())
}

fn hex(bytes: [u8; 32]) -> String {
    let mut output = String::with_capacity(64);
    for byte in bytes {
        use std::fmt::Write as _;
        let _ = write!(output, "{byte:02x}");
    }
    output
}
