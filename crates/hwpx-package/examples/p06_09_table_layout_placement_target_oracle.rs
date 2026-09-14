use std::env;
use std::error::Error;
use std::fs;
use std::io::Cursor;
use std::path::{Path, PathBuf};

use domain_ir::{
    TableHorizontalAlignment, TableHorizontalReference, TableTextFlow, TableTextWrap,
    TableVerticalAlignment, TableVerticalReference,
};
use hwpx_package::{
    BoundedZipReader, PackageLimits, TableLayoutHwpxLimits, TableLayoutHwpxReadback,
    TableLayoutHwpxReader, TablePlacementHwpxReadback, TablePlacementHwpxReader,
    TablePropertiesHwpxBinding, TablePropertiesHwpxLimits, TablePropertiesHwpxReader,
    TableRulingHwpxBinding, TableRulingHwpxCellBinding,
};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};

const MAX_MANIFEST_BYTES: u64 = 256 * 1024;
const MAX_HWPX_BYTES: u64 = 16 * 1024 * 1024;
const MAX_PDF_BYTES: u64 = 64 * 1024 * 1024;
const EXPECTED_FIXTURE_SCHEMA: &str = "hwpx-agent.p06-09-table-layout-placement-target-fixture/v1";
const EXPECTED_RUNTIME_SCHEMA: &str =
    "hwpx-agent.p06-09-table-layout-placement-target-batch-readback/v1";
const EXPECTED_FIXTURE_MANIFEST_SHA256: &str =
    "053b401cbcd2a21b3e845a29ffef28b9c1f633dfa825ac3f52d520cb5f6a3430";
const EXPECTED_TRACE_SCHEMA: &str =
    "hwpx-agent.p06-09-hancom-2020-table-properties-target-readback/v1";
const EXPECTED_ANCESTOR_SHA256: &str =
    "0459a05b8543edb2e05c9c0117f76df999c8543bad255d06d26d4b3b57388252";
const EXPECTED_HANCOM_VERSION: &str = "11.0.0.9136";
const EXPECTED_HANCOM_SHA256: &str =
    "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce";

struct Arguments {
    fixture_manifest: PathBuf,
    expected_fixture_manifest_sha256: String,
    runtime_manifest: PathBuf,
    expected_runtime_manifest_sha256: String,
    output_receipt: PathBuf,
}

impl Arguments {
    fn parse() -> Result<Self, Box<dyn Error>> {
        let mut values = env::args_os();
        let _program = values.next();
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
    source_ancestor_sha256: String,
    source_section_sha256: String,
    prepared_section_sha256: String,
    grid_sha256: String,
    font_metric_profile_id: String,
    font_metric_receipt_sha256: String,
    cases: Vec<FixtureCase>,
    shared_content_sha256: String,
    all_cases_content_preserved: bool,
    actual_hangul_2020: bool,
    render: String,
    automation: String,
    differential: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct FixtureCase {
    case_id: String,
    feature_id: String,
    capability_id: String,
    adapter: String,
    file: String,
    sha256: String,
    target_section_sha256: String,
    semantic_sha256: String,
    modified_attribute_count: usize,
    layout: LayoutEvidence,
    placement: PlacementEvidence,
    formula_count: usize,
    page_split: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct LayoutEvidence {
    rows: u32,
    columns: u32,
    table_width_hwpunit: u32,
    table_height_hwpunit: u32,
    column_widths_hwpunit: Vec<u32>,
    row_heights_hwpunit: Vec<u32>,
    content_sha256: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
#[allow(clippy::struct_excessive_bools)]
struct PlacementEvidence {
    treat_as_char: bool,
    affect_line_spacing: bool,
    horizontal_reference: TableHorizontalReference,
    vertical_reference: TableVerticalReference,
    horizontal_alignment: TableHorizontalAlignment,
    vertical_alignment: TableVerticalAlignment,
    horizontal_offset_hwpunit: i64,
    vertical_offset_hwpunit: i64,
    flow_with_text: bool,
    allow_overlap: bool,
    hold_anchor_and_shape: bool,
    text_wrap: TableTextWrap,
    text_flow: TableTextFlow,
    outer_margins_hwpunit: [u32; 4],
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct RuntimeManifest {
    schema_version: String,
    state: String,
    fixture_manifest_sha256: String,
    target: RuntimeTarget,
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
struct RuntimeCase {
    case_id: String,
    feature_id: String,
    input_path: String,
    input_sha256: String,
    output_hwpx_path: String,
    output_hwpx_sha256: String,
    output_pdf_path: String,
    output_pdf_sha256: String,
    output_pdf_bytes: u64,
    trace_path: String,
    trace_sha256: String,
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
    input_text_sha256: String,
    output_sha256: String,
    output_text_sha256: String,
    output_saved: bool,
    render_pdf_requested: bool,
    render_pdf_saved: bool,
    render_pdf_sha256: String,
    render_pdf_bytes: u64,
    render_pdf_signature_valid: bool,
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
    typed_layout_passed: usize,
    typed_placement_passed: usize,
    typed_properties_passed: usize,
    content_payload_passed: usize,
    lifecycle_trace_passed: usize,
    pdf_signature_passed: usize,
    actual_hangul_2020: bool,
    render: &'static str,
    automation: &'static str,
    differential: &'static str,
}

fn main() -> Result<(), Box<dyn Error>> {
    run(&Arguments::parse()?)
}

fn run(arguments: &Arguments) -> Result<(), Box<dyn Error>> {
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
    for (fixture_case, runtime_case) in fixture.cases.iter().zip(&runtime.cases) {
        require_case_identity(fixture_case, runtime_case)?;
        let input_path = resolve_bound_path(fixture_directory, &runtime_case.input_path)?;
        let output_path = resolve_bound_path(runtime_directory, &runtime_case.output_hwpx_path)?;
        let pdf_path = resolve_bound_path(runtime_directory, &runtime_case.output_pdf_path)?;
        let trace_path = resolve_bound_path(runtime_directory, &runtime_case.trace_path)?;

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
        let trace_bytes = read_bounded_file(&trace_path, MAX_MANIFEST_BYTES)?;
        require_digest(&trace_bytes, &runtime_case.trace_sha256, "lifecycle trace")?;
        let trace: LifecycleTrace = serde_json::from_slice(&trace_bytes)?;
        require_lifecycle_trace(&trace, runtime_case)?;

        let target_section = read_section(&input)?;
        let actual_section = read_section(&output)?;
        require_fixture_target(fixture_case, &target_section)?;
        require_typed_actual(fixture_case, &actual_section)?;
        require_properties_oracle(fixture_case, &input, &output)?;
        require_payload_oracle(&target_section, &actual_section)?;
        if !runtime_case.input_unchanged {
            return Err(format!("{} input was not immutable", fixture_case.feature_id).into());
        }
        feature_ids.push(fixture_case.feature_id.clone());
    }

    let receipt = OracleReceipt {
        schema_version: "hwpx-agent.p06-09-table-layout-placement-target-oracle/v1",
        state: "pass",
        fixture_manifest_sha256: arguments.expected_fixture_manifest_sha256.clone(),
        runtime_manifest_sha256: arguments.expected_runtime_manifest_sha256.clone(),
        feature_ids,
        case_count: fixture.cases.len(),
        typed_layout_passed: fixture.cases.len(),
        typed_placement_passed: fixture.cases.len(),
        typed_properties_passed: fixture.cases.len(),
        content_payload_passed: fixture.cases.len(),
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

#[allow(dead_code)]
pub(crate) fn validate_pending_22_case(
    manifest_bytes: &[u8],
    feature_id: &str,
    target_bytes: &[u8],
    actual_bytes: &[u8],
) -> Result<(), Box<dyn Error>> {
    let fixture: FixtureManifest = serde_json::from_slice(manifest_bytes)?;
    require_fixture_manifest(&fixture)?;
    let fixture_case = fixture
        .cases
        .iter()
        .find(|case| case.feature_id == feature_id)
        .ok_or("pending-22 layout/placement feature is absent from fixture manifest")?;
    require_digest(
        target_bytes,
        &fixture_case.sha256,
        "pending-22 target input",
    )?;
    let target_section = read_section(target_bytes)?;
    let actual_section = read_section(actual_bytes)?;
    require_fixture_target(fixture_case, &target_section)?;
    require_typed_actual(fixture_case, &actual_section)?;
    require_properties_oracle(fixture_case, target_bytes, actual_bytes)?;
    require_payload_oracle(&target_section, &actual_section)
}

#[allow(clippy::too_many_lines)]
fn require_fixture_manifest(value: &FixtureManifest) -> Result<(), Box<dyn Error>> {
    let expected_cases = [
        (
            "TABLE-018",
            "table.equal_row_height",
            "table_geometry_hwpx",
            "table-018-equal-row-height-4x3.hwpx",
        ),
        (
            "TABLE-019",
            "table.equal_column_width",
            "table_geometry_hwpx",
            "table-019-equal-column-width-4x3.hwpx",
        ),
        (
            "TABLE-050",
            "table.row_min_height",
            "table_geometry_hwpx",
            "table-050-row-min-height-4x3.hwpx",
        ),
        (
            "TABLE-051",
            "table.column_fixed_width",
            "table_layout_hwpx",
            "table-051-column-fixed-width-4x3.hwpx",
        ),
        (
            "TABLE-052",
            "table.autofit_content",
            "table_layout_hwpx",
            "table-052-autofit-content-4x3.hwpx",
        ),
        (
            "TABLE-053",
            "table.autofit_page",
            "table_layout_hwpx",
            "table-053-autofit-page-4x3.hwpx",
        ),
        (
            "TABLE-034",
            "table.position",
            "table_placement_hwpx",
            "table-034-position-4x3.hwpx",
        ),
        (
            "TABLE-036",
            "table.inline_floating",
            "table_placement_hwpx",
            "table-036-inline-floating-4x3.hwpx",
        ),
        (
            "TABLE-037",
            "table.wrap",
            "table_placement_hwpx",
            "table-037-wrap-4x3.hwpx",
        ),
        (
            "TABLE-038",
            "table.outer_margin",
            "table_placement_hwpx",
            "table-038-outer-margin-4x3.hwpx",
        ),
    ];
    if value.schema_version != EXPECTED_FIXTURE_SCHEMA
        || value.source_ancestor_sha256 != EXPECTED_ANCESTOR_SHA256
        || value.cases.len() != expected_cases.len()
        || !value.all_cases_content_preserved
        || value.actual_hangul_2020
        || value.render != "not_run"
        || value.automation != "not_run"
        || value.differential != "not_run"
    {
        return Err("fixture manifest boundary differs".into());
    }
    for digest in [
        &value.source_section_sha256,
        &value.prepared_section_sha256,
        &value.grid_sha256,
        &value.font_metric_receipt_sha256,
        &value.shared_content_sha256,
    ] {
        require_lower_sha256(digest)?;
    }
    if value.font_metric_profile_id
        != "hwpx-agent.font-metric.hancom-2020-line-box-100-hwpunit-bucket/1"
    {
        return Err("font metric profile differs".into());
    }
    for (case, expected) in value.cases.iter().zip(expected_cases) {
        if case.feature_id != expected.0
            || case.capability_id != expected.1
            || case.adapter != expected.2
            || case.file != expected.3
            || case.modified_attribute_count == 0
            || case.formula_count != 0
            || case.page_split != "cell"
            || case.layout.content_sha256 != value.shared_content_sha256
        {
            return Err(format!("{} fixture case boundary differs", expected.0).into());
        }
        for digest in [
            &case.sha256,
            &case.target_section_sha256,
            &case.semantic_sha256,
        ] {
            require_lower_sha256(digest)?;
        }
    }
    Ok(())
}

fn require_runtime_manifest(
    value: &RuntimeManifest,
    fixture: &FixtureManifest,
    fixture_sha256: &str,
) -> Result<(), Box<dyn Error>> {
    if value.schema_version != EXPECTED_RUNTIME_SCHEMA
        || value.state != "pass"
        || value.fixture_manifest_sha256 != fixture_sha256
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
    runtime: &RuntimeCase,
) -> Result<(), Box<dyn Error>> {
    let stem = fixture
        .file
        .strip_suffix(".hwpx")
        .ok_or("fixture case extension differs")?;
    if runtime.case_id != fixture.case_id
        || runtime.feature_id != fixture.feature_id
        || runtime.input_sha256 != fixture.sha256
        || runtime.input_path != fixture.file
        || runtime.output_hwpx_path != format!("{stem}.hancom-2020-readback.hwpx")
        || runtime.output_pdf_path != format!("{stem}.hancom-2020-render.pdf")
        || runtime.trace_path != format!("{stem}.hancom-2020-trace.json")
        || !runtime.input_unchanged
    {
        return Err(format!("{} runtime case binding differs", fixture.feature_id).into());
    }
    for digest in [
        &runtime.output_hwpx_sha256,
        &runtime.output_pdf_sha256,
        &runtime.trace_sha256,
    ] {
        require_lower_sha256(digest)?;
    }
    Ok(())
}

fn require_lifecycle_trace(
    trace: &LifecycleTrace,
    runtime: &RuntimeCase,
) -> Result<(), Box<dyn Error>> {
    if trace.schema_version != EXPECTED_TRACE_SCHEMA
        || trace.state != "pass"
        || trace.target.prog_id != "HWPFrame.HwpObject.2"
        || trace.target.file_version != EXPECTED_HANCOM_VERSION
        || trace.target.executable_sha256 != EXPECTED_HANCOM_SHA256
        || trace.input_sha256 != runtime.input_sha256
        || !trace.input_unchanged
        || trace.input_text_sha256 != trace.output_text_sha256
        || trace.output_sha256 != runtime.output_hwpx_sha256
        || !trace.output_saved
        || !trace.render_pdf_requested
        || !trace.render_pdf_saved
        || trace.render_pdf_sha256 != runtime.output_pdf_sha256
        || trace.render_pdf_bytes != runtime.output_pdf_bytes
        || !trace.render_pdf_signature_valid
        || trace.raw_document_text_present
        || trace.user_document_scanned
        || trace.external_network_invoked
        || trace.registry_or_system_setting_changed
        || trace.computer_use_click_or_type_invoked
        || trace.watchdog.timed_out
        || trace.watchdog.remaining_hwp_process_count != 0
    {
        return Err(format!("{} lifecycle trace differs", runtime.feature_id).into());
    }
    Ok(())
}

fn require_fixture_target(case: &FixtureCase, section: &[u8]) -> Result<(), Box<dyn Error>> {
    require_digest(section, &case.target_section_sha256, "target section")?;
    require_typed_actual(case, section)
}

fn require_typed_actual(case: &FixtureCase, section: &[u8]) -> Result<(), Box<dyn Error>> {
    let layout =
        TableLayoutHwpxReader::read_in_section(section, 0, TableLayoutHwpxLimits::default())?;
    let placement =
        TablePlacementHwpxReader::read_in_section(section, 0, TableLayoutHwpxLimits::default())?;
    let mismatches = typed_target_mismatches(case, &layout, &placement)?;
    if !mismatches.is_empty() {
        return Err(format!(
            "{} typed target differs: {}",
            case.feature_id,
            mismatches.join(",")
        )
        .into());
    }
    Ok(())
}

fn typed_target_mismatches(
    case: &FixtureCase,
    layout: &TableLayoutHwpxReadback,
    placement: &TablePlacementHwpxReadback,
) -> Result<Vec<String>, Box<dyn Error>> {
    let mut mismatches = Vec::new();
    if layout.rows != case.layout.rows {
        mismatches.push(format!(
            "layout.rows(expected={},actual={})",
            case.layout.rows, layout.rows
        ));
    }
    if layout.columns != case.layout.columns {
        mismatches.push(format!(
            "layout.columns(expected={},actual={})",
            case.layout.columns, layout.columns
        ));
    }
    if layout.table_width_hwpunit != case.layout.table_width_hwpunit {
        mismatches.push(format!(
            "layout.table_width_hwpunit(expected={},actual={})",
            case.layout.table_width_hwpunit, layout.table_width_hwpunit
        ));
    }
    if layout.table_height_hwpunit != case.layout.table_height_hwpunit {
        mismatches.push(format!(
            "layout.table_height_hwpunit(expected={},actual={})",
            case.layout.table_height_hwpunit, layout.table_height_hwpunit
        ));
    }
    let actual_widths = track_widths(layout)?;
    if actual_widths != case.layout.column_widths_hwpunit {
        mismatches.push(format!(
            "layout.column_widths_hwpunit(expected={:?},actual={actual_widths:?})",
            case.layout.column_widths_hwpunit
        ));
    }
    let actual_heights = track_heights(layout)?;
    if actual_heights != case.layout.row_heights_hwpunit {
        mismatches.push(format!(
            "layout.row_heights_hwpunit(expected={:?},actual={actual_heights:?})",
            case.layout.row_heights_hwpunit
        ));
    }
    placement_mismatches(&mut mismatches, placement, &case.placement);
    Ok(mismatches)
}

fn placement_mismatches(
    mismatches: &mut Vec<String>,
    actual: &TablePlacementHwpxReadback,
    expected: &PlacementEvidence,
) {
    macro_rules! compare {
        ($name:literal, $actual:expr, $expected:expr) => {
            if $actual != $expected {
                mismatches.push(format!(
                    concat!($name, "(expected={:?},actual={:?})"),
                    $expected, $actual
                ));
            }
        };
    }
    compare!(
        "placement.treat_as_char",
        actual.attachment_flags.treat_as_char,
        expected.treat_as_char
    );
    compare!(
        "placement.affect_line_spacing",
        actual.attachment_flags.affect_line_spacing,
        expected.affect_line_spacing
    );
    compare!(
        "placement.horizontal_reference",
        actual.horizontal_reference,
        expected.horizontal_reference
    );
    compare!(
        "placement.vertical_reference",
        actual.vertical_reference,
        expected.vertical_reference
    );
    compare!(
        "placement.horizontal_alignment",
        actual.horizontal_alignment,
        expected.horizontal_alignment
    );
    compare!(
        "placement.vertical_alignment",
        actual.vertical_alignment,
        expected.vertical_alignment
    );
    compare!(
        "placement.horizontal_offset_hwpunit",
        actual.horizontal_offset_hwpunit,
        expected.horizontal_offset_hwpunit
    );
    compare!(
        "placement.vertical_offset_hwpunit",
        actual.vertical_offset_hwpunit,
        expected.vertical_offset_hwpunit
    );
    compare!(
        "placement.flow_with_text",
        actual.floating_flags.flow_with_text,
        expected.flow_with_text
    );
    compare!(
        "placement.allow_overlap",
        actual.floating_flags.allow_overlap,
        expected.allow_overlap
    );
    compare!(
        "placement.hold_anchor_and_shape",
        actual.floating_flags.hold_anchor_and_shape,
        expected.hold_anchor_and_shape
    );
    compare!("placement.text_wrap", actual.text_wrap, expected.text_wrap);
    compare!("placement.text_flow", actual.text_flow, expected.text_flow);
    compare!(
        "placement.outer_margins_hwpunit",
        [
            actual.outer_margins.left_hwpunit,
            actual.outer_margins.right_hwpunit,
            actual.outer_margins.top_hwpunit,
            actual.outer_margins.bottom_hwpunit,
        ],
        expected.outer_margins_hwpunit
    );
}

fn require_properties_oracle(
    case: &FixtureCase,
    target_package: &[u8],
    actual_package: &[u8],
) -> Result<(), Box<dyn Error>> {
    let binding = properties_binding(case)?;
    let target_parts = read_package_parts(target_package)?;
    let actual_parts = read_package_parts(actual_package)?;
    let limits = TablePropertiesHwpxLimits::default();
    let target = TablePropertiesHwpxReader::read_existing(
        &target_parts.header,
        &target_parts.section,
        0,
        &binding,
        limits,
    )?;
    let actual = TablePropertiesHwpxReader::read_existing(
        &actual_parts.header,
        &actual_parts.section,
        0,
        &binding,
        limits,
    )?;
    let mismatches = properties_mismatches(&target, &actual);
    if !mismatches.is_empty() {
        return Err(format!(
            "{} typed properties differ: {}",
            case.feature_id,
            mismatches.join(",")
        )
        .into());
    }
    Ok(())
}

fn properties_mismatches(
    target: &hwpx_package::TablePropertiesHwpxReadback,
    actual: &hwpx_package::TablePropertiesHwpxReadback,
) -> Vec<String> {
    let mut mismatches = Vec::new();
    if target.grid != actual.grid {
        mismatches.push("grid".to_owned());
    }
    if target.state.table_id() != actual.state.table_id() {
        mismatches.push("state.table_id".to_owned());
    }
    if target.state.grid_sha256() != actual.state.grid_sha256() {
        mismatches.push("state.grid_sha256".to_owned());
    }
    if target.state.table_properties_sha256() != actual.state.table_properties_sha256() {
        mismatches.push("state.table_properties_sha256".to_owned());
    }
    if target.state.cells().len() != actual.state.cells().len() {
        mismatches.push("state.cells.length".to_owned());
    }
    for (index, (target_cell, actual_cell)) in target
        .state
        .cells()
        .iter()
        .zip(actual.state.cells())
        .enumerate()
    {
        if target_cell.master_cell_id != actual_cell.master_cell_id {
            mismatches.push(format!("state.cells[{index}].master_cell_id"));
        }
        if target_cell.coordinate != actual_cell.coordinate {
            mismatches.push(format!("state.cells[{index}].coordinate"));
        }
        if target_cell.formula_sha256 != actual_cell.formula_sha256 {
            mismatches.push(format!("state.cells[{index}].formula_sha256"));
        }
        if target_cell.properties != actual_cell.properties {
            mismatches.push(format!("state.cells[{index}].properties"));
        }
    }
    if target.table_value != actual.table_value {
        mismatches.push("table_value".to_owned());
    }
    if target.cell_values.len() != actual.cell_values.len() {
        mismatches.push("cell_values.length".to_owned());
    }
    for (index, (target_cell, actual_cell)) in target
        .cell_values
        .iter()
        .zip(&actual.cell_values)
        .enumerate()
    {
        if target_cell != actual_cell {
            mismatches.push(format!("cell_values[{index}]"));
        }
    }
    if target.payload_block_count != actual.payload_block_count {
        mismatches.push("payload_block_count".to_owned());
    }
    if target.formula_count != actual.formula_count {
        mismatches.push("formula_count".to_owned());
    }
    if target.payload_block_count != 9 {
        mismatches.push("target.payload_block_count_expected_9".to_owned());
    }
    if target.formula_count != 0 {
        mismatches.push("target.formula_count_expected_0".to_owned());
    }
    mismatches
}

fn properties_binding(case: &FixtureCase) -> Result<TablePropertiesHwpxBinding, Box<dyn Error>> {
    let mut row_boundaries = vec![0_u32];
    row_boundaries.try_reserve_exact(case.layout.row_heights_hwpunit.len())?;
    for height in &case.layout.row_heights_hwpunit {
        let next = row_boundaries
            .last()
            .copied()
            .ok_or("row boundary is missing")?
            .checked_add(*height)
            .ok_or("row boundary overflow")?;
        row_boundaries.push(next);
    }
    let mut column_boundaries = vec![0_u32];
    column_boundaries.try_reserve_exact(case.layout.column_widths_hwpunit.len())?;
    for width in &case.layout.column_widths_hwpunit {
        let next = column_boundaries
            .last()
            .copied()
            .ok_or("column boundary is missing")?
            .checked_add(*width)
            .ok_or("column boundary overflow")?;
        column_boundaries.push(next);
    }
    let mut cells = Vec::new();
    cells.try_reserve_exact(12)?;
    for row in 0..4_u32 {
        for column in 0..3_u32 {
            cells.push(TableRulingHwpxCellBinding {
                master_cell_id: domain_ir::LogicalId::parse(format!(
                    "layout-placement-cell-{row}-{column}"
                ))?,
                payload_block_ids: if row == 1 {
                    Vec::new()
                } else {
                    vec![domain_ir::LogicalId::parse(format!(
                        "layout-placement-payload-{row}-{column}"
                    ))?]
                },
            });
        }
    }
    Ok(TablePropertiesHwpxBinding {
        table: TableRulingHwpxBinding {
            table_id: domain_ir::LogicalId::parse("layout-placement-target-table")?,
            row_boundaries_hwpunit: row_boundaries,
            column_boundaries_hwpunit: column_boundaries,
            cells,
        },
        diagonals: Vec::new(),
    })
}

fn require_payload_oracle(target: &[u8], actual: &[u8]) -> Result<(), Box<dyn Error>> {
    let labels = [
        b"R1C1".as_slice(),
        b"R1C2".as_slice(),
        b"R1C3".as_slice(),
        b"R2C1".as_slice(),
        b"R2C2".as_slice(),
        b"R2C3".as_slice(),
        b"R3C1".as_slice(),
        b"R3C2".as_slice(),
        b"R3C3".as_slice(),
    ];
    for source in [target, actual] {
        if labels
            .iter()
            .any(|label| count_occurrences(source, label) != 1)
            || count_occurrences(source, b"<hp:fieldBegin") != 0
            || count_occurrences(source, b"pageBreak=\"CELL\"") != 1
            || count_occurrences(source, b"<hp:tc ") != 12
        {
            return Err("formula-free payload oracle differs".into());
        }
    }
    Ok(())
}

fn track_widths(value: &TableLayoutHwpxReadback) -> Result<Vec<u32>, Box<dyn Error>> {
    let columns = usize::try_from(value.columns)?;
    let slots = value
        .rows
        .checked_mul(value.columns)
        .ok_or("layout grid cardinality overflow")?;
    if columns == 0 || value.cells.len() != usize::try_from(slots)? {
        return Err("layout grid cardinality differs".into());
    }
    Ok(value
        .cells
        .iter()
        .take(columns)
        .map(|cell| cell.width_hwpunit)
        .collect())
}

fn track_heights(value: &TableLayoutHwpxReadback) -> Result<Vec<u32>, Box<dyn Error>> {
    let columns = usize::try_from(value.columns)?;
    let slots = value
        .rows
        .checked_mul(value.columns)
        .ok_or("layout grid cardinality overflow")?;
    if columns == 0 || value.cells.len() != usize::try_from(slots)? {
        return Err("layout grid cardinality differs".into());
    }
    Ok(value
        .cells
        .iter()
        .step_by(columns)
        .map(|cell| cell.height_hwpunit)
        .collect())
}

fn resolve_bound_path(parent: &Path, value: &str) -> Result<PathBuf, Box<dyn Error>> {
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

fn read_section(package: &[u8]) -> Result<Vec<u8>, Box<dyn Error>> {
    Ok(read_package_parts(package)?.section)
}

struct PackageParts {
    header: Vec<u8>,
    section: Vec<u8>,
}

fn read_package_parts(package: &[u8]) -> Result<PackageParts, Box<dyn Error>> {
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

fn count_occurrences(source: &[u8], needle: &[u8]) -> usize {
    source
        .windows(needle.len())
        .filter(|window| *window == needle)
        .count()
}

fn read_bounded_file(path: &Path, maximum: u64) -> Result<Vec<u8>, Box<dyn Error>> {
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

fn write_create_new(path: &Path, bytes: &[u8]) -> Result<(), Box<dyn Error>> {
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
) -> Result<PathBuf, Box<dyn Error>> {
    values
        .next()
        .map(PathBuf::from)
        .ok_or_else(|| format!("missing {name}").into())
}

fn string_argument(
    values: &mut impl Iterator<Item = std::ffi::OsString>,
    name: &str,
) -> Result<String, Box<dyn Error>> {
    values
        .next()
        .ok_or_else(|| format!("missing {name}"))?
        .into_string()
        .map_err(|_| format!("{name} is not Unicode").into())
}

fn require_digest(bytes: &[u8], expected: &str, label: &str) -> Result<(), Box<dyn Error>> {
    if hex(Sha256::digest(bytes).into()) != expected {
        return Err(format!("{label} SHA-256 differs").into());
    }
    Ok(())
}

fn require_lower_sha256(value: &str) -> Result<(), Box<dyn Error>> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err("SHA-256 must be lowercase hexadecimal".into());
    }
    Ok(())
}

fn hex(value: [u8; 32]) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let mut output = String::with_capacity(64);
    for byte in value {
        output.push(char::from(DIGITS[usize::from(byte >> 4)]));
        output.push(char::from(DIGITS[usize::from(byte & 0x0f)]));
    }
    output
}
