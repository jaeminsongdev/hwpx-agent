use std::env;
use std::error::Error;
use std::fs;
use std::io::Cursor;
use std::path::{Path, PathBuf};

use domain_ir::{
    CellCoordinate, FormulaLimitConfig, FormulaLimits, LogicalId, TableAutoFillRegion,
};
use hwpx_package::{
    BoundedZipReader, PackageLimits, TableAbsoluteReferenceHwpxLimits,
    TableAbsoluteReferenceHwpxReader, TableAutoFillHwpxLimits, TableAutoFillHwpxReader,
    TableFormulaHwpxLimits, TableNumberFormatHwpxReader, TablePaginationHwpxLimits,
    TablePaginationHwpxReadback, TablePaginationHwpxReader, TablePropertiesHwpxBinding,
    TableRulingHwpxBinding, TableRulingHwpxCellBinding, TableRulingHwpxLimits,
    TableRulingHwpxReadback, TableRulingHwpxReader, TableSortHwpxLimits, TableSortHwpxReader,
    TableStyleHwpxLimits, TableStyleHwpxReader, TableThousandsHwpxReader, TableTransposeHwpxLimits,
    TableTransposeHwpxReader,
};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};

const MAX_MANIFEST_BYTES: u64 = 256 * 1024;
const MAX_HWPX_BYTES: u64 = 16 * 1024 * 1024;
const MAX_PDF_BYTES: u64 = 64 * 1024 * 1024;
const MAX_PROGRESS_BYTES: u64 = 64 * 1024;
const EXPECTED_FIXTURE_SCHEMA: &str = "hwpx-agent.p06-09-table-remaining-target-fixture/v1";
const EXPECTED_RUNTIME_SCHEMA: &str = "hwpx-agent.p06-09-table-remaining-target-batch-readback/v1";
const EXPECTED_FIXTURE_MANIFEST_SHA256: &str =
    "1aeddc699c91c4878242a64e7674d1689a86b8abeda704370eeaac337bf95a8e";
const EXPECTED_TRACE_SCHEMA: &str =
    "hwpx-agent.p06-09-hancom-2020-table-properties-target-readback/v1";
const EXPECTED_HANCOM_VERSION: &str = "11.0.0.9136";
const EXPECTED_HANCOM_SHA256: &str =
    "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce";

type AnyError = Box<dyn Error>;

struct Arguments {
    fixture_manifest: PathBuf,
    expected_fixture_manifest_sha256: String,
    runtime_manifest: PathBuf,
    expected_runtime_manifest_sha256: String,
    output_receipt: PathBuf,
}

impl Arguments {
    fn parse() -> Result<Self, AnyError> {
        let mut values = env::args_os().skip(1);
        let result = Self {
            fixture_manifest: path_argument(&mut values, "fixture manifest")?,
            expected_fixture_manifest_sha256: string_argument(
                &mut values,
                "fixture manifest SHA-256",
            )?,
            runtime_manifest: path_argument(&mut values, "runtime manifest")?,
            expected_runtime_manifest_sha256: string_argument(
                &mut values,
                "runtime manifest SHA-256",
            )?,
            output_receipt: path_argument(&mut values, "output receipt")?,
        };
        if values.next().is_some() {
            return Err("too many arguments".into());
        }
        Ok(result)
    }
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct FixtureManifest {
    schema_version: String,
    source_artifacts: Vec<SourceArtifact>,
    cases: Vec<FixtureCase>,
    actual_hangul_2020: bool,
    render: String,
    automation: String,
    differential: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct SourceArtifact {
    role: String,
    path: String,
    sha256: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct FixtureCase {
    case_id: String,
    feature_id: String,
    capability_id: String,
    adapter: String,
    source_role: String,
    file: String,
    sha256: String,
    target_header_sha256: String,
    target_section_sha256: String,
    semantic_sha256: String,
    table_count: usize,
    formula_count: usize,
    primary_binding: Option<BindingEvidence>,
    secondary_binding: Option<BindingEvidence>,
    primary_table_ordinal: usize,
    secondary_table_ordinal: Option<usize>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct BindingEvidence {
    table_id: String,
    row_boundaries_hwpunit: Vec<u32>,
    column_boundaries_hwpunit: Vec<u32>,
    cells: Vec<CellBindingEvidence>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct CellBindingEvidence {
    master_cell_id: String,
    payload_block_ids: Vec<String>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct RuntimeManifest {
    schema_version: String,
    state: String,
    fixture_manifest_sha256: String,
    target: RuntimeTarget,
    text_probes: Vec<RuntimeProbe>,
    cases: Vec<RuntimeCase>,
    remaining_hwp_process_count: u32,
    actual_hangul_2020: bool,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct RuntimeTarget {
    prog_id: String,
    file_version: String,
    executable_sha256: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct RuntimeProbe {
    case_id: String,
    input_sha256: String,
    input_text_sha256: String,
    trace_path: String,
    trace_sha256: String,
    progress_path: String,
    progress_sha256: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct RuntimeCase {
    case_id: String,
    feature_id: String,
    input_path: String,
    input_sha256: String,
    input_text_sha256: String,
    output_hwpx_path: String,
    output_hwpx_sha256: String,
    output_pdf_path: String,
    output_pdf_sha256: String,
    output_pdf_bytes: u64,
    trace_path: String,
    trace_sha256: String,
    progress_path: String,
    progress_sha256: String,
    input_unchanged: bool,
}

#[derive(Deserialize)]
#[allow(clippy::struct_excessive_bools)]
struct LifecycleTrace {
    schema_version: String,
    state: String,
    target: LifecycleTarget,
    input_sha256: String,
    input_unchanged: bool,
    input_text_sha256: Option<String>,
    output_sha256: Option<String>,
    output_text_sha256: Option<String>,
    output_saved: bool,
    render_pdf_requested: bool,
    render_pdf_saved: bool,
    render_pdf_sha256: Option<String>,
    render_pdf_bytes: Option<u64>,
    render_pdf_signature_valid: bool,
    error_code: Option<String>,
    failed_phase: Option<String>,
    raw_document_text_present: bool,
    user_document_scanned: bool,
    external_network_invoked: bool,
    registry_or_system_setting_changed: bool,
    computer_use_click_or_type_invoked: bool,
    watchdog: Watchdog,
}

#[derive(Deserialize)]
struct LifecycleTarget {
    prog_id: String,
    file_version: String,
    executable_sha256: String,
}

#[derive(Deserialize)]
struct Watchdog {
    timed_out: bool,
    remaining_hwp_process_count: u32,
}

#[derive(Serialize)]
struct OracleReceipt {
    schema_version: &'static str,
    state: &'static str,
    fixture_manifest_sha256: String,
    runtime_manifest_sha256: String,
    feature_ids: Vec<String>,
    case_count: usize,
    typed_adapter_passed: usize,
    semantic_readback_passed: usize,
    text_probe_passed: usize,
    lifecycle_trace_passed: usize,
    pdf_signature_passed: usize,
    actual_hangul_2020: bool,
    render: &'static str,
    automation: &'static str,
    differential: &'static str,
}

fn main() -> Result<(), AnyError> {
    run(&Arguments::parse()?)
}

#[allow(clippy::too_many_lines)]
fn run(arguments: &Arguments) -> Result<(), AnyError> {
    require_lower_sha256(&arguments.expected_fixture_manifest_sha256)?;
    require_lower_sha256(&arguments.expected_runtime_manifest_sha256)?;
    if arguments.expected_fixture_manifest_sha256 != EXPECTED_FIXTURE_MANIFEST_SHA256 {
        return Err("fixture manifest identity differs".into());
    }
    if arguments.output_receipt.exists() {
        return Err("output receipt already exists".into());
    }
    let fixture_bytes = read_bounded_file(&arguments.fixture_manifest, MAX_MANIFEST_BYTES)?;
    require_digest(
        &fixture_bytes,
        &arguments.expected_fixture_manifest_sha256,
        "fixture manifest",
    )?;
    let fixture: FixtureManifest = serde_json::from_slice(&fixture_bytes)?;
    require_fixture_manifest(&fixture)?;

    let runtime_bytes = read_bounded_file(&arguments.runtime_manifest, MAX_MANIFEST_BYTES)?;
    require_digest(
        &runtime_bytes,
        &arguments.expected_runtime_manifest_sha256,
        "runtime manifest",
    )?;
    let runtime: RuntimeManifest = serde_json::from_slice(&runtime_bytes)?;
    require_runtime_manifest(
        &runtime,
        &fixture,
        &arguments.expected_fixture_manifest_sha256,
    )?;

    let fixture_directory = arguments
        .fixture_manifest
        .parent()
        .ok_or("fixture manifest has no parent")?;
    let runtime_directory = arguments
        .runtime_manifest
        .parent()
        .ok_or("runtime manifest has no parent")?;
    let mut feature_ids = Vec::new();
    feature_ids.try_reserve_exact(fixture.cases.len())?;
    for ((fixture_case, runtime_probe), runtime_case) in fixture
        .cases
        .iter()
        .zip(&runtime.text_probes)
        .zip(&runtime.cases)
    {
        require_case_identity(fixture_case, runtime_probe, runtime_case)?;
        let input_path = resolve_bound_path(fixture_directory, &runtime_case.input_path)?;
        let output_path = resolve_bound_path(runtime_directory, &runtime_case.output_hwpx_path)?;
        let pdf_path = resolve_bound_path(runtime_directory, &runtime_case.output_pdf_path)?;
        let probe_trace_path = resolve_bound_path(runtime_directory, &runtime_probe.trace_path)?;
        let probe_progress_path =
            resolve_bound_path(runtime_directory, &runtime_probe.progress_path)?;
        let trace_path = resolve_bound_path(runtime_directory, &runtime_case.trace_path)?;
        let progress_path = resolve_bound_path(runtime_directory, &runtime_case.progress_path)?;

        let input = read_bounded_file(&input_path, MAX_HWPX_BYTES)?;
        require_digest(&input, &fixture_case.sha256, "target input")?;
        require_digest(&input, &runtime_case.input_sha256, "runtime target input")?;
        let output = read_bounded_file(&output_path, MAX_HWPX_BYTES)?;
        require_digest(&output, &runtime_case.output_hwpx_sha256, "actual HWPX")?;
        let pdf = read_bounded_file(&pdf_path, MAX_PDF_BYTES)?;
        require_digest(&pdf, &runtime_case.output_pdf_sha256, "actual PDF")?;
        if !pdf.starts_with(b"%PDF-") || pdf.len() as u64 != runtime_case.output_pdf_bytes {
            return Err(format!("{} PDF boundary differs", fixture_case.feature_id).into());
        }

        let probe_trace_bytes = read_bounded_file(&probe_trace_path, MAX_MANIFEST_BYTES)?;
        require_digest(
            &probe_trace_bytes,
            &runtime_probe.trace_sha256,
            "text probe trace",
        )?;
        let probe_trace: LifecycleTrace = serde_json::from_slice(&probe_trace_bytes)?;
        require_probe_trace(&probe_trace, runtime_probe)?;
        require_digest(
            &read_bounded_file(&probe_progress_path, MAX_PROGRESS_BYTES)?,
            &runtime_probe.progress_sha256,
            "text probe progress",
        )?;

        let trace_bytes = read_bounded_file(&trace_path, MAX_MANIFEST_BYTES)?;
        require_digest(&trace_bytes, &runtime_case.trace_sha256, "lifecycle trace")?;
        let trace: LifecycleTrace = serde_json::from_slice(&trace_bytes)?;
        require_lifecycle_trace(&trace, runtime_case)?;
        require_digest(
            &read_bounded_file(&progress_path, MAX_PROGRESS_BYTES)?,
            &runtime_case.progress_sha256,
            "lifecycle progress",
        )?;

        let target = read_package_parts(&input)?;
        let actual = read_package_parts(&output)?;
        require_digest(
            &target.header,
            &fixture_case.target_header_sha256,
            "target header",
        )?;
        require_digest(
            &target.section,
            &fixture_case.target_section_sha256,
            "target section",
        )?;
        require_typed_oracle(fixture_case, &target, &actual)?;
        if !runtime_case.input_unchanged {
            return Err(format!("{} input was not immutable", fixture_case.feature_id).into());
        }
        feature_ids.push(fixture_case.feature_id.clone());
    }

    let receipt = OracleReceipt {
        schema_version: "hwpx-agent.p06-09-table-remaining-target-oracle/v1",
        state: "pass",
        fixture_manifest_sha256: arguments.expected_fixture_manifest_sha256.clone(),
        runtime_manifest_sha256: arguments.expected_runtime_manifest_sha256.clone(),
        feature_ids,
        case_count: fixture.cases.len(),
        typed_adapter_passed: fixture.cases.len(),
        semantic_readback_passed: fixture.cases.len(),
        text_probe_passed: fixture.cases.len(),
        lifecycle_trace_passed: fixture.cases.len(),
        pdf_signature_passed: fixture.cases.len(),
        actual_hangul_2020: true,
        render: "pdf_signature_and_external_original_detail_review_required",
        automation: "not_run",
        differential: "not_run",
    };
    write_create_new(
        &arguments.output_receipt,
        &serde_json::to_vec_pretty(&receipt)?,
    )?;
    println!(
        "schema={} state=pass feature_count={} actual_hangul_2020=true",
        receipt.schema_version, receipt.case_count
    );
    Ok(())
}

fn require_fixture_manifest(value: &FixtureManifest) -> Result<(), AnyError> {
    let expected = expected_cases();
    if value.schema_version != EXPECTED_FIXTURE_SCHEMA
        || value.source_artifacts.len() != 7
        || value.cases.len() != expected.len()
        || value.actual_hangul_2020
        || value.render != "not_run"
        || value.automation != "not_run"
        || value.differential != "not_run"
    {
        return Err("fixture manifest boundary differs".into());
    }
    for source in &value.source_artifacts {
        require_lower_sha256(&source.sha256)?;
        if source.role.is_empty() || source.path.is_empty() {
            return Err("fixture source artifact differs".into());
        }
    }
    for (case, expected_case) in value.cases.iter().zip(expected) {
        if case.case_id != expected_case.0
            || case.feature_id != expected_case.1
            || case.capability_id != expected_case.2
            || case.adapter != expected_case.3
            || case.source_role != expected_case.4
            || case.file != expected_case.5
            || case.formula_count != expected_case.6
            || case.table_count != expected_case.7
            || case.primary_table_ordinal != 0
            || case.secondary_table_ordinal != expected_case.8
        {
            return Err(format!("{} fixture case boundary differs", expected_case.1).into());
        }
        for digest in [
            &case.sha256,
            &case.target_header_sha256,
            &case.target_section_sha256,
            &case.semantic_sha256,
        ] {
            require_lower_sha256(digest)?;
        }
        if expected_case.9 != case.primary_binding.is_some()
            || expected_case.10 != case.secondary_binding.is_some()
        {
            return Err(format!("{} fixture binding boundary differs", case.feature_id).into());
        }
    }
    Ok(())
}

#[allow(clippy::too_many_lines, clippy::type_complexity)]
fn expected_cases() -> [(
    &'static str,
    &'static str,
    &'static str,
    &'static str,
    &'static str,
    &'static str,
    usize,
    usize,
    Option<usize>,
    bool,
    bool,
); 10] {
    [
        (
            "table-020-style",
            "TABLE-020",
            "table.table_style",
            "table_style_hwpx",
            "common",
            "table-020-style.hwpx",
            0,
            1,
            None,
            true,
            false,
        ),
        (
            "table-021-transpose",
            "TABLE-021",
            "table.transpose",
            "table_transpose_hwpx",
            "common",
            "table-021-transpose.hwpx",
            0,
            1,
            None,
            true,
            false,
        ),
        (
            "table-032-thousands-add",
            "TABLE-032",
            "table.thousands_add",
            "table_thousands_hwpx",
            "thousands_removed",
            "table-032-thousands-add.hwpx",
            1,
            1,
            None,
            false,
            false,
        ),
        (
            "table-033-thousands-remove",
            "TABLE-033",
            "table.thousands_remove",
            "table_thousands_hwpx",
            "thousands_baseline",
            "table-033-thousands-remove.hwpx",
            1,
            1,
            None,
            false,
            false,
        ),
        (
            "table-049-number-format",
            "TABLE-049",
            "table.number_format",
            "table_number_format_hwpx",
            "number_baseline",
            "table-049-number-format.hwpx",
            6,
            1,
            None,
            false,
            false,
        ),
        (
            "table-054-nested-table",
            "TABLE-054",
            "table.nested_table",
            "table_nested_table_hwpx",
            "common_envelope_with_inline_nested_template",
            "table-054-nested-table.hwpx",
            1,
            2,
            Some(1),
            true,
            true,
        ),
        (
            "table-056-sort",
            "TABLE-056",
            "table.sort_cells",
            "table_sort_hwpx",
            "common",
            "table-056-sort.hwpx",
            0,
            1,
            None,
            true,
            false,
        ),
        (
            "table-057-auto-fill",
            "TABLE-057",
            "table.auto_fill",
            "table_auto_fill_hwpx",
            "common_envelope_with_inline_auto_fill_section",
            "table-057-auto-fill.hwpx",
            0,
            1,
            None,
            true,
            false,
        ),
        (
            "table-058-auto-fill-series",
            "TABLE-058",
            "table.auto_fill_series",
            "table_auto_fill_hwpx",
            "common_envelope_with_inline_auto_fill_section",
            "table-058-auto-fill-series.hwpx",
            0,
            1,
            None,
            true,
            false,
        ),
        (
            "table-060-absolute-reference",
            "TABLE-060",
            "table.formula_absolute_ref",
            "table_absolute_reference_hwpx",
            "common_envelope_with_inline_absolute_formula_section",
            "table-060-absolute-reference.hwpx",
            2,
            1,
            None,
            false,
            false,
        ),
    ]
}

fn require_runtime_manifest(
    value: &RuntimeManifest,
    fixture: &FixtureManifest,
    fixture_sha256: &str,
) -> Result<(), AnyError> {
    if value.schema_version != EXPECTED_RUNTIME_SCHEMA
        || value.state != "pass"
        || value.fixture_manifest_sha256 != fixture_sha256
        || value.text_probes.len() != fixture.cases.len()
        || value.cases.len() != fixture.cases.len()
        || value.target.prog_id != "HWPFrame.HwpObject.2"
        || value.target.file_version != EXPECTED_HANCOM_VERSION
        || value.target.executable_sha256 != EXPECTED_HANCOM_SHA256
        || value.remaining_hwp_process_count != 0
        || !value.actual_hangul_2020
    {
        return Err("runtime manifest boundary differs".into());
    }
    Ok(())
}

fn require_case_identity(
    fixture: &FixtureCase,
    probe: &RuntimeProbe,
    runtime: &RuntimeCase,
) -> Result<(), AnyError> {
    let stem = fixture
        .file
        .strip_suffix(".hwpx")
        .ok_or("fixture case extension differs")?;
    if probe.case_id != fixture.case_id
        || probe.input_sha256 != fixture.sha256
        || probe.input_text_sha256 != runtime.input_text_sha256
        || probe.trace_path != format!("{stem}.hancom-2020-text-probe-trace.json")
        || probe.progress_path != format!("{stem}.hancom-2020-text-probe-trace.json.progress.jsonl")
        || runtime.case_id != fixture.case_id
        || runtime.feature_id != fixture.feature_id
        || runtime.input_sha256 != fixture.sha256
        || runtime.input_path != fixture.file
        || runtime.output_hwpx_path != format!("{stem}.hancom-2020-readback.hwpx")
        || runtime.output_pdf_path != format!("{stem}.hancom-2020-render.pdf")
        || runtime.trace_path != format!("{stem}.hancom-2020-trace.json")
        || runtime.progress_path != format!("{stem}.hancom-2020-trace.json.progress.jsonl")
        || !runtime.input_unchanged
    {
        return Err(format!("{} runtime case binding differs", fixture.feature_id).into());
    }
    for digest in [
        &probe.input_text_sha256,
        &probe.trace_sha256,
        &probe.progress_sha256,
        &runtime.output_hwpx_sha256,
        &runtime.output_pdf_sha256,
        &runtime.trace_sha256,
        &runtime.progress_sha256,
    ] {
        require_lower_sha256(digest)?;
    }
    Ok(())
}

fn require_probe_trace(trace: &LifecycleTrace, runtime: &RuntimeProbe) -> Result<(), AnyError> {
    if trace.schema_version != EXPECTED_TRACE_SCHEMA
        || trace.state != "failed"
        || !target_matches(&trace.target)
        || trace.input_sha256 != runtime.input_sha256
        || !trace.input_unchanged
        || trace.input_text_sha256.as_deref() != Some(runtime.input_text_sha256.as_str())
        || trace.output_sha256.is_some()
        || trace.output_text_sha256.is_some()
        || trace.output_saved
        || trace.render_pdf_requested
        || trace.render_pdf_saved
        || trace.render_pdf_signature_valid
        || trace.error_code.as_deref()
            != Some("TABLE_PROPERTIES_TARGET_READBACK_INPUT_TEXT_MISMATCH")
        || trace.failed_phase.as_deref() != Some("read_input")
        || !privacy_and_watchdog_match(trace)
    {
        return Err(format!("{} text probe trace differs", runtime.case_id).into());
    }
    Ok(())
}

fn require_lifecycle_trace(trace: &LifecycleTrace, runtime: &RuntimeCase) -> Result<(), AnyError> {
    if trace.schema_version != EXPECTED_TRACE_SCHEMA
        || trace.state != "pass"
        || !target_matches(&trace.target)
        || trace.input_sha256 != runtime.input_sha256
        || !trace.input_unchanged
        || trace.input_text_sha256.as_deref() != Some(runtime.input_text_sha256.as_str())
        || trace.output_text_sha256.as_deref() != Some(runtime.input_text_sha256.as_str())
        || trace.output_sha256.as_deref() != Some(runtime.output_hwpx_sha256.as_str())
        || !trace.output_saved
        || !trace.render_pdf_requested
        || !trace.render_pdf_saved
        || trace.render_pdf_sha256.as_deref() != Some(runtime.output_pdf_sha256.as_str())
        || trace.render_pdf_bytes != Some(runtime.output_pdf_bytes)
        || !trace.render_pdf_signature_valid
        || trace.error_code.is_some()
        || trace.failed_phase.is_some()
        || !privacy_and_watchdog_match(trace)
    {
        return Err(format!("{} lifecycle trace differs", runtime.feature_id).into());
    }
    Ok(())
}

fn target_matches(value: &LifecycleTarget) -> bool {
    value.prog_id == "HWPFrame.HwpObject.2"
        && value.file_version == EXPECTED_HANCOM_VERSION
        && value.executable_sha256 == EXPECTED_HANCOM_SHA256
}

fn privacy_and_watchdog_match(value: &LifecycleTrace) -> bool {
    !value.raw_document_text_present
        && !value.user_document_scanned
        && !value.external_network_invoked
        && !value.registry_or_system_setting_changed
        && !value.computer_use_click_or_type_invoked
        && !value.watchdog.timed_out
        && value.watchdog.remaining_hwp_process_count == 0
}

fn require_typed_oracle(
    case: &FixtureCase,
    target: &PackageParts,
    actual: &PackageParts,
) -> Result<(), AnyError> {
    match case.feature_id.as_str() {
        "TABLE-020" => require_style_oracle(case, target, actual),
        "TABLE-021" => require_transpose_oracle(case, target, actual),
        "TABLE-032" | "TABLE-033" => require_thousands_oracle(case, target, actual),
        "TABLE-049" => require_number_format_oracle(case, target, actual),
        "TABLE-054" => require_nested_oracle(case, target, actual),
        "TABLE-056" => require_sort_oracle(case, target, actual),
        "TABLE-057" | "TABLE-058" => require_auto_fill_oracle(case, target, actual),
        "TABLE-060" => require_absolute_reference_oracle(case, target, actual),
        _ => Err("unsupported remaining table feature".into()),
    }
}

fn require_style_oracle(
    case: &FixtureCase,
    target: &PackageParts,
    actual: &PackageParts,
) -> Result<(), AnyError> {
    let binding = properties_binding(required_binding(case.primary_binding.as_ref())?)?;
    let limits = TableStyleHwpxLimits::default();
    let left = TableStyleHwpxReader::read_existing(
        &target.header,
        &target.section,
        case.primary_table_ordinal,
        &binding,
        limits,
    )?;
    let right = TableStyleHwpxReader::read_existing(
        &actual.header,
        &actual.section,
        case.primary_table_ordinal,
        &binding,
        limits,
    )?;
    if left.properties.grid != right.properties.grid
        || left.properties.state != right.properties.state
        || left.properties.table_value != right.properties.table_value
        || left.properties.cell_values != right.properties.cell_values
        || left.cell_style_sha256 != right.cell_style_sha256
        || left.properties.payload_block_count != right.properties.payload_block_count
        || left.properties.formula_count != right.properties.formula_count
    {
        return Err("TABLE-020 typed style readback differs".into());
    }
    Ok(())
}

fn require_transpose_oracle(
    case: &FixtureCase,
    target: &PackageParts,
    actual: &PackageParts,
) -> Result<(), AnyError> {
    let binding = ruling_binding(required_binding(case.primary_binding.as_ref())?)?;
    let limits = TableTransposeHwpxLimits::default();
    let left = TableTransposeHwpxReader::read_existing(
        &target.header,
        &target.section,
        case.primary_table_ordinal,
        &binding,
        limits,
    )?;
    let right = TableTransposeHwpxReader::read_existing(
        &actual.header,
        &actual.section,
        case.primary_table_ordinal,
        &binding,
        limits,
    )?;
    require_ruling_and_pagination(
        &left.ruling,
        &right.ruling,
        &left.pagination,
        &right.pagination,
    )
}

fn require_thousands_oracle(
    case: &FixtureCase,
    target: &PackageParts,
    actual: &PackageParts,
) -> Result<(), AnyError> {
    let limits = TableFormulaHwpxLimits::default();
    let formula_limits = formula_limits()?;
    let owner = [CellCoordinate { row: 0, column: 2 }];
    let left = TableThousandsHwpxReader::read_selected_in_section(
        &target.section,
        case.primary_table_ordinal,
        &owner,
        limits,
        formula_limits,
    )?;
    let right = TableThousandsHwpxReader::read_selected_in_section(
        &actual.section,
        case.primary_table_ordinal,
        &owner,
        limits,
        formula_limits,
    )?;
    if left.dimensions() != right.dimensions()
        || left.selected_formulas() != right.selected_formulas()
        || left.formula_field_count() != right.formula_field_count()
        || left.grid_sha256() != right.grid_sha256()
        || left.formula_field_count() != case.formula_count
    {
        return Err(format!("{} typed thousands readback differs", case.feature_id).into());
    }
    Ok(())
}

fn require_number_format_oracle(
    case: &FixtureCase,
    target: &PackageParts,
    actual: &PackageParts,
) -> Result<(), AnyError> {
    let limits = TableFormulaHwpxLimits::default();
    let formula_limits = formula_limits()?;
    let owners = (0..6)
        .map(|row| CellCoordinate { row, column: 2 })
        .collect::<Vec<_>>();
    let left = TableNumberFormatHwpxReader::read_selected_in_section(
        &target.section,
        case.primary_table_ordinal,
        &owners,
        limits,
        formula_limits,
    )?;
    let right = TableNumberFormatHwpxReader::read_selected_in_section(
        &actual.section,
        case.primary_table_ordinal,
        &owners,
        limits,
        formula_limits,
    )?;
    if left.dimensions() != right.dimensions()
        || left.selected_formulas() != right.selected_formulas()
        || left.selected_native_grouping() != right.selected_native_grouping()
        || left.formula_field_count() != right.formula_field_count()
        || left.grid_sha256() != right.grid_sha256()
        || left.formula_field_count() != case.formula_count
    {
        return Err("TABLE-049 typed number-format readback differs".into());
    }
    Ok(())
}

fn require_nested_oracle(
    case: &FixtureCase,
    target: &PackageParts,
    actual: &PackageParts,
) -> Result<(), AnyError> {
    let primary = ruling_binding(required_binding(case.primary_binding.as_ref())?)?;
    let secondary = ruling_binding(required_binding(case.secondary_binding.as_ref())?)?;
    let secondary_ordinal = case
        .secondary_table_ordinal
        .ok_or("TABLE-054 secondary ordinal is missing")?;
    let limits = TableRulingHwpxLimits::default();
    let pagination_limits = TablePaginationHwpxLimits::default();
    for (ordinal, binding) in [
        (case.primary_table_ordinal, &primary),
        (secondary_ordinal, &secondary),
    ] {
        let left = TableRulingHwpxReader::read_existing(
            &target.header,
            &target.section,
            ordinal,
            binding,
            limits,
        )?;
        let right = TableRulingHwpxReader::read_existing(
            &actual.header,
            &actual.section,
            ordinal,
            binding,
            limits,
        )?;
        let left_pagination = TablePaginationHwpxReader::read_in_section(
            &target.section,
            ordinal,
            pagination_limits,
        )?;
        let right_pagination = TablePaginationHwpxReader::read_in_section(
            &actual.section,
            ordinal,
            pagination_limits,
        )?;
        require_ruling_and_pagination(&left, &right, &left_pagination, &right_pagination)?;
    }
    Ok(())
}

fn require_sort_oracle(
    case: &FixtureCase,
    target: &PackageParts,
    actual: &PackageParts,
) -> Result<(), AnyError> {
    let binding = ruling_binding(required_binding(case.primary_binding.as_ref())?)?;
    let limits = TableSortHwpxLimits::default();
    let left = TableSortHwpxReader::read_context(
        &target.header,
        &target.section,
        case.primary_table_ordinal,
        &binding,
        limits,
    )?;
    let right = TableSortHwpxReader::read_context(
        &actual.header,
        &actual.section,
        case.primary_table_ordinal,
        &binding,
        limits,
    )?;
    require_ruling_and_pagination(
        &left.ruling,
        &right.ruling,
        &left.pagination,
        &right.pagination,
    )?;
    if left.text_grid != right.text_grid || left.source_table_count != right.source_table_count {
        return Err("TABLE-056 typed sort readback differs".into());
    }
    Ok(())
}

fn require_auto_fill_oracle(
    case: &FixtureCase,
    target: &PackageParts,
    actual: &PackageParts,
) -> Result<(), AnyError> {
    let binding = ruling_binding(required_binding(case.primary_binding.as_ref())?)?;
    let region = TableAutoFillRegion {
        start: CellCoordinate { row: 1, column: 0 },
        end: CellCoordinate { row: 1, column: 2 },
    };
    let auto_limits = TableAutoFillHwpxLimits::default();
    let left = TableAutoFillHwpxReader::read_context(
        &target.header,
        &target.section,
        case.primary_table_ordinal,
        region,
        &binding,
        auto_limits,
    )?;
    let right = TableAutoFillHwpxReader::read_context(
        &actual.header,
        &actual.section,
        case.primary_table_ordinal,
        region,
        &binding,
        auto_limits,
    )?;
    require_ruling_and_pagination(
        &left.ruling,
        &right.ruling,
        &left.pagination,
        &right.pagination,
    )?;
    let sort_limits = TableSortHwpxLimits::default();
    let left_text = TableSortHwpxReader::read_context(
        &target.header,
        &target.section,
        case.primary_table_ordinal,
        &binding,
        sort_limits,
    )?;
    let right_text = TableSortHwpxReader::read_context(
        &actual.header,
        &actual.section,
        case.primary_table_ordinal,
        &binding,
        sort_limits,
    )?;
    if left_text.text_grid != right_text.text_grid
        || left.source_table_count != right.source_table_count
    {
        return Err(format!("{} typed auto-fill readback differs", case.feature_id).into());
    }
    Ok(())
}

fn require_absolute_reference_oracle(
    case: &FixtureCase,
    target: &PackageParts,
    actual: &PackageParts,
) -> Result<(), AnyError> {
    let limits = TableAbsoluteReferenceHwpxLimits {
        formula: formula_limits()?,
        ..TableAbsoluteReferenceHwpxLimits::default()
    };
    let owner = CellCoordinate { row: 1, column: 2 };
    let left = TableAbsoluteReferenceHwpxReader::read_context(
        &target.header,
        &target.section,
        case.primary_table_ordinal,
        owner,
        limits,
    )?;
    let right = TableAbsoluteReferenceHwpxReader::read_context(
        &actual.header,
        &actual.section,
        case.primary_table_ordinal,
        owner,
        limits,
    )?;
    if left.owner != right.owner
        || left.rows != right.rows
        || left.columns != right.columns
        || left.formula != right.formula
        || left.source_table_count != right.source_table_count
        || left.formula_field_count != right.formula_field_count
        || left.formula_field_count != case.formula_count
        || !pagination_semantic_equal(&left.pagination, &right.pagination)
    {
        return Err("TABLE-060 typed absolute-reference readback differs".into());
    }
    Ok(())
}

fn require_ruling_and_pagination(
    left: &TableRulingHwpxReadback,
    right: &TableRulingHwpxReadback,
    left_pagination: &TablePaginationHwpxReadback,
    right_pagination: &TablePaginationHwpxReadback,
) -> Result<(), AnyError> {
    if left.grid != right.grid
        || left.state != right.state
        || left.payload_block_count != right.payload_block_count
        || left.formula_count != right.formula_count
        || !pagination_semantic_equal(left_pagination, right_pagination)
    {
        return Err("typed ruling or pagination readback differs".into());
    }
    Ok(())
}

fn pagination_semantic_equal(
    left: &TablePaginationHwpxReadback,
    right: &TablePaginationHwpxReadback,
) -> bool {
    left.page_split == right.page_split
        && left.repeat_header_rows == right.repeat_header_rows
        && left.row_count == right.row_count
        && left.column_count == right.column_count
        && left.caption.is_none()
        && right.caption.is_none()
}

fn required_binding(value: Option<&BindingEvidence>) -> Result<&BindingEvidence, AnyError> {
    value.ok_or_else(|| "required fixture binding is missing".into())
}

fn properties_binding(value: &BindingEvidence) -> Result<TablePropertiesHwpxBinding, AnyError> {
    Ok(TablePropertiesHwpxBinding {
        table: ruling_binding(value)?,
        diagonals: Vec::new(),
    })
}

fn ruling_binding(value: &BindingEvidence) -> Result<TableRulingHwpxBinding, AnyError> {
    let mut cells = Vec::new();
    cells.try_reserve_exact(value.cells.len())?;
    for cell in &value.cells {
        let mut payload_block_ids = Vec::new();
        payload_block_ids.try_reserve_exact(cell.payload_block_ids.len())?;
        for payload in &cell.payload_block_ids {
            payload_block_ids.push(LogicalId::parse(payload)?);
        }
        cells.push(TableRulingHwpxCellBinding {
            master_cell_id: LogicalId::parse(&cell.master_cell_id)?,
            payload_block_ids,
        });
    }
    Ok(TableRulingHwpxBinding {
        table_id: LogicalId::parse(&value.table_id)?,
        row_boundaries_hwpunit: value.row_boundaries_hwpunit.clone(),
        column_boundaries_hwpunit: value.column_boundaries_hwpunit.clone(),
        cells,
    })
}

fn formula_limits() -> Result<FormulaLimits, AnyError> {
    Ok(FormulaLimits::new(FormulaLimitConfig {
        rows: 32,
        columns: 32,
        ..FormulaLimitConfig::default()
    })?)
}

struct PackageParts {
    header: Vec<u8>,
    section: Vec<u8>,
}

fn read_package_parts(package: &[u8]) -> Result<PackageParts, AnyError> {
    let mut reader = BoundedZipReader::open(Cursor::new(package), PackageLimits::default())?;
    let header_index = reader
        .entries()
        .iter()
        .find(|entry| entry.path.as_str() == "Contents/header.xml")
        .map(|entry| entry.index)
        .ok_or("header part is missing")?;
    let section_index = reader
        .entries()
        .iter()
        .find(|entry| entry.path.as_str() == "Contents/section0.xml")
        .map(|entry| entry.index)
        .ok_or("section part is missing")?;
    Ok(PackageParts {
        header: reader.read_entry(header_index)?,
        section: reader.read_entry(section_index)?,
    })
}

fn resolve_bound_path(parent: &Path, value: &str) -> Result<PathBuf, AnyError> {
    let raw = Path::new(value);
    if raw.is_absolute()
        || raw
            .components()
            .any(|component| !matches!(component, std::path::Component::Normal(_)))
    {
        return Err("runtime path is not one exact relative file name".into());
    }
    let path = fs::canonicalize(parent.join(raw))?;
    let canonical_parent = fs::canonicalize(parent)?;
    if path.parent() != Some(canonical_parent.as_path()) {
        return Err("runtime path escapes its manifest directory".into());
    }
    Ok(path)
}

fn read_bounded_file(path: &Path, maximum: u64) -> Result<Vec<u8>, AnyError> {
    let metadata = fs::symlink_metadata(path)?;
    if !metadata.is_file()
        || metadata.file_type().is_symlink()
        || metadata.len() == 0
        || metadata.len() > maximum
    {
        return Err("input is not a bounded regular file".into());
    }
    let bytes = fs::read(path)?;
    if bytes.len() as u64 != metadata.len() {
        return Err("input changed while being read".into());
    }
    Ok(bytes)
}

fn write_create_new(path: &Path, bytes: &[u8]) -> Result<(), AnyError> {
    use std::io::Write as _;
    let mut file = fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(path)?;
    file.write_all(bytes)?;
    file.sync_all()?;
    Ok(())
}

fn path_argument(
    values: &mut impl Iterator<Item = std::ffi::OsString>,
    name: &str,
) -> Result<PathBuf, AnyError> {
    values
        .next()
        .map(PathBuf::from)
        .ok_or_else(|| format!("missing {name}").into())
}

fn string_argument(
    values: &mut impl Iterator<Item = std::ffi::OsString>,
    name: &str,
) -> Result<String, AnyError> {
    values
        .next()
        .ok_or_else(|| format!("missing {name}"))?
        .into_string()
        .map_err(|_| format!("{name} is not Unicode").into())
}

fn require_digest(bytes: &[u8], expected: &str, label: &str) -> Result<(), AnyError> {
    if hex(Sha256::digest(bytes)) != expected {
        return Err(format!("{label} SHA-256 differs").into());
    }
    Ok(())
}

fn require_lower_sha256(value: &str) -> Result<(), AnyError> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err("SHA-256 must be lowercase hexadecimal".into());
    }
    Ok(())
}

fn hex(value: impl AsRef<[u8]>) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let bytes = value.as_ref();
    let mut output = String::with_capacity(bytes.len() * 2);
    for &byte in bytes {
        output.push(char::from(DIGITS[usize::from(byte >> 4)]));
        output.push(char::from(DIGITS[usize::from(byte & 0x0f)]));
    }
    output
}
