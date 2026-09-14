use std::collections::{BTreeMap, BTreeSet};
use std::env;
use std::error::Error;
use std::ffi::OsString;
use std::fs::{self, OpenOptions};
use std::io::Write as _;
use std::path::{Component, Path, PathBuf};

use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};

#[allow(dead_code)]
#[path = "p06_09_table_layout_placement_target_oracle.rs"]
mod layout_placement_oracle;
#[allow(dead_code)]
#[path = "p06_09_table_merge_split_target_oracle.rs"]
mod merge_split_oracle;
#[allow(dead_code)]
#[path = "p06_09_table_remaining_target_oracle.rs"]
mod remaining_oracle;

type AnyError = Box<dyn Error>;

const MAX_MANIFEST_BYTES: u64 = 1024 * 1024;
const MAX_HWPX_BYTES: u64 = 8 * 1024 * 1024;
const MAX_PDF_BYTES: u64 = 32 * 1024 * 1024;
const EXPECTED_CASE_COUNT: usize = 22;
const EXPECTED_PROGRESS_EVENT_COUNT_FIRST_OPEN: u32 = 361;
const EXPECTED_PROGRESS_EVENT_COUNT_RETRY: u32 = 363;
const EXPECTED_MERGE_SPLIT_SHA256: &str =
    "682635284ae5686832dfd89598ea6c106c6b110119e0d54a8e8a24b63e9f3f97";
const EXPECTED_LAYOUT_PLACEMENT_SHA256: &str =
    "33c391ff2b151f815c4e2e79c9144c53547fe87d5e35d1e856e4e796b3978faf";
const EXPECTED_REMAINING_SHA256: &str =
    "1aeddc699c91c4878242a64e7674d1689a86b8abeda704370eeaac337bf95a8e";
const EXPECTED_LAYOUT_TEXT_SHA256: &str =
    "e90f2af9593f587921c00b8c9a4d1c3fed8ed2284bc5463a17d7f259478cdb91";
const EXPECTED_HANCOM_SHA256: &str =
    "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce";
const EXPECTED_ACCESS_CONTROL_SHA256: &str =
    "04f7910b122ded578975f379a7053b3dc62a0a5b73c2ea40505374500e665a0c";
const EXPECTED_ACCESS_CONTROL_DIRECTORY: &str = "p06-09-table-structure-target-20260913-05";
const EXPECTED_ACCESS_CONTROL_FILE: &str = "table-012-insert-row-3x3.hancom-2020-readback.hwpx";

struct Arguments {
    merge_split_manifest: PathBuf,
    merge_split_sha256: String,
    layout_placement_manifest: PathBuf,
    layout_placement_sha256: String,
    remaining_manifest: PathBuf,
    remaining_sha256: String,
    runtime_trace: PathBuf,
    runtime_trace_sha256: String,
    output_receipt: PathBuf,
}

impl Arguments {
    fn parse() -> Result<Self, AnyError> {
        let mut values = env::args_os().skip(1);
        let result = Self {
            merge_split_manifest: path_argument(&mut values, "merge/split fixture manifest")?,
            merge_split_sha256: string_argument(&mut values, "merge/split manifest SHA-256")?,
            layout_placement_manifest: path_argument(
                &mut values,
                "layout/placement fixture manifest",
            )?,
            layout_placement_sha256: string_argument(
                &mut values,
                "layout/placement manifest SHA-256",
            )?,
            remaining_manifest: path_argument(&mut values, "remaining fixture manifest")?,
            remaining_sha256: string_argument(&mut values, "remaining manifest SHA-256")?,
            runtime_trace: path_argument(&mut values, "pending-22 runtime trace")?,
            runtime_trace_sha256: string_argument(&mut values, "pending-22 runtime trace SHA-256")?,
            output_receipt: path_argument(&mut values, "output receipt")?,
        };
        if values.next().is_some() {
            return Err("too many arguments".into());
        }
        Ok(result)
    }
}

struct FixtureGroup {
    id: &'static str,
    expected_manifest_sha256: &'static str,
    directory: PathBuf,
    bytes: Vec<u8>,
    cases: Vec<FixtureCase>,
}

#[derive(Deserialize)]
struct FixtureIndex {
    cases: Vec<FixtureCase>,
}

#[derive(Deserialize)]
struct FixtureCase {
    case_id: String,
    feature_id: String,
    capability_id: String,
    file: String,
    sha256: String,
}

#[derive(Deserialize)]
struct RuntimeEnvelope {
    schema_version: String,
    state: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
#[allow(clippy::struct_excessive_bools)]
struct RuntimeTrace {
    schema_version: String,
    state: String,
    target: RuntimeTarget,
    session_strategy: String,
    access_approval_strategy: String,
    access_control: RuntimeAccessControl,
    manifest_sha256: RuntimeManifestDigests,
    case_count: usize,
    completed_case_count: usize,
    cases: Vec<RuntimeCase>,
    failed_feature_id: Option<String>,
    error_code: Option<String>,
    failed_phase: Option<String>,
    exception_type: Option<String>,
    exception_hresult: Option<i64>,
    raw_document_text_present: bool,
    user_document_scanned: bool,
    external_network_invoked: bool,
    registry_or_system_setting_changed: bool,
    computer_use_click_or_type_invoked: bool,
    window_visible_for_user_access: bool,
    delegated_engine_schema: String,
    access_approval_user_owned: bool,
    watchdog: RuntimeWatchdog,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct RuntimeAccessControl {
    source: String,
    input_file: String,
    input_sha256: String,
    input_unchanged: bool,
    retry_policy: String,
    open_attempt_count: u32,
    first_open_returned_false: bool,
    open_state: String,
    close_state: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct RuntimeTarget {
    prog_id: String,
    registry_view: String,
    client: String,
    file_version: String,
    executable_sha256: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct RuntimeManifestDigests {
    merge_split: String,
    layout_placement: String,
    remaining: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
#[allow(clippy::struct_excessive_bools)]
struct RuntimeCase {
    group_id: String,
    group_case_index: usize,
    case_id: String,
    feature_id: String,
    capability_id: String,
    manifest_sha256: String,
    input_file: String,
    input_sha256: String,
    input_unchanged: bool,
    expected_text_source: String,
    input_text_sha256: String,
    output_file: String,
    output_sha256: String,
    output_text_sha256: String,
    output_saved: bool,
    render_pdf_file: String,
    render_pdf_saved: bool,
    render_pdf_sha256: String,
    render_pdf_bytes: u64,
    render_pdf_signature_valid: bool,
    render_pdf_export_method: String,
    phases: RuntimePhases,
    error_code: Option<String>,
    failed_phase: Option<String>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct RuntimePhases {
    open_input: String,
    read_input: String,
    save_as_hwpx: String,
    close_input: String,
    reopen_output: String,
    read_output: String,
    export_pdf: String,
    close_output: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
#[allow(clippy::struct_excessive_bools)]
struct RuntimeWatchdog {
    timeout_seconds: u32,
    timed_out: bool,
    child_exit_code: i32,
    output_drained: bool,
    cleaned_process_count: u32,
    cleanup_refused_count: u32,
    cleanup_error_count: u32,
    remaining_hwp_process_count: u32,
    progress_present: bool,
    progress_valid: bool,
    progress_event_count: u32,
    progress_last_phase: String,
    progress_last_state: String,
    progress_observed_phase: String,
    progress_observed_feature_id: String,
    progress_worker_process_id: u32,
    progress_hwp_process_id: u32,
    window_visible_for_user_access: bool,
}

#[derive(Serialize)]
struct OracleReceipt {
    schema_version: &'static str,
    state: &'static str,
    runtime_trace_sha256: String,
    fixture_manifest_sha256: BTreeMap<&'static str, &'static str>,
    feature_ids: Vec<String>,
    group_case_count: BTreeMap<&'static str, usize>,
    case_count: usize,
    lifecycle_trace_passed: usize,
    typed_semantic_readback_passed: usize,
    input_immutability_passed: usize,
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
    require_exact_sha256(
        &arguments.merge_split_sha256,
        EXPECTED_MERGE_SPLIT_SHA256,
        "merge/split manifest",
    )?;
    require_exact_sha256(
        &arguments.layout_placement_sha256,
        EXPECTED_LAYOUT_PLACEMENT_SHA256,
        "layout/placement manifest",
    )?;
    require_exact_sha256(
        &arguments.remaining_sha256,
        EXPECTED_REMAINING_SHA256,
        "remaining manifest",
    )?;
    require_lower_sha256(&arguments.runtime_trace_sha256)?;

    let target_root = target_root()?;
    let access_control_path = canonical_existing_under(
        &target_root
            .join(EXPECTED_ACCESS_CONTROL_DIRECTORY)
            .join(EXPECTED_ACCESS_CONTROL_FILE),
        &target_root,
    )?;
    let access_control = read_bounded_file(&access_control_path, MAX_HWPX_BYTES)?;
    require_digest(
        &access_control,
        EXPECTED_ACCESS_CONTROL_SHA256,
        "pending-22 access control",
    )?;
    let groups = vec![
        read_fixture_group(
            "merge_split",
            &arguments.merge_split_manifest,
            &arguments.merge_split_sha256,
            EXPECTED_MERGE_SPLIT_SHA256,
            &target_root,
        )?,
        read_fixture_group(
            "layout_placement",
            &arguments.layout_placement_manifest,
            &arguments.layout_placement_sha256,
            EXPECTED_LAYOUT_PLACEMENT_SHA256,
            &target_root,
        )?,
        read_fixture_group(
            "remaining",
            &arguments.remaining_manifest,
            &arguments.remaining_sha256,
            EXPECTED_REMAINING_SHA256,
            &target_root,
        )?,
    ];
    require_group_counts(&groups)?;

    let runtime_path = canonical_existing_under(&arguments.runtime_trace, &target_root)?;
    let runtime_bytes = read_bounded_file(&runtime_path, MAX_MANIFEST_BYTES)?;
    require_digest(
        &runtime_bytes,
        &arguments.runtime_trace_sha256,
        "pending-22 runtime trace",
    )?;
    let envelope: RuntimeEnvelope = serde_json::from_slice(&runtime_bytes)?;
    if envelope.schema_version != "hwpx-agent.p06-09-table-pending-22-target-batch-readback/v1"
        || envelope.state != "pass"
    {
        return Err("pending-22 runtime trace is not a complete pass".into());
    }
    let runtime: RuntimeTrace = serde_json::from_slice(&runtime_bytes)?;
    require_runtime_boundary(&runtime)?;

    let expected: Vec<(&FixtureGroup, usize, &FixtureCase)> = groups
        .iter()
        .flat_map(|group| {
            group
                .cases
                .iter()
                .enumerate()
                .map(move |(index, case)| (group, index + 1, case))
        })
        .collect();
    if expected.len() != EXPECTED_CASE_COUNT || runtime.cases.len() != expected.len() {
        return Err("pending-22 flattened case count differs".into());
    }

    let mut feature_ids = Vec::with_capacity(EXPECTED_CASE_COUNT);
    let mut unique_features = BTreeSet::new();
    for (runtime_case, (group, group_case_index, fixture_case)) in
        runtime.cases.iter().zip(expected)
    {
        require_case_boundary(runtime_case, group, group_case_index, fixture_case)?;
        let input_path = resolve_single_file(&group.directory, &runtime_case.input_file)?;
        let output_path = resolve_single_file(&group.directory, &runtime_case.output_file)?;
        let pdf_path = resolve_single_file(&group.directory, &runtime_case.render_pdf_file)?;
        let input = read_bounded_file(&input_path, MAX_HWPX_BYTES)?;
        require_digest(&input, &runtime_case.input_sha256, "pending-22 input")?;
        let output = read_bounded_file(&output_path, MAX_HWPX_BYTES)?;
        require_digest(&output, &runtime_case.output_sha256, "pending-22 output")?;
        let pdf = read_bounded_file(&pdf_path, MAX_PDF_BYTES)?;
        require_digest(&pdf, &runtime_case.render_pdf_sha256, "pending-22 PDF")?;
        if !pdf.starts_with(b"%PDF-") || pdf.len() as u64 != runtime_case.render_pdf_bytes {
            return Err(format!("{} PDF boundary differs", runtime_case.feature_id).into());
        }
        match group.id {
            "merge_split" => merge_split_oracle::validate_pending_22_case(
                &group.bytes,
                &runtime_case.feature_id,
                &input,
                &output,
            )?,
            "layout_placement" => layout_placement_oracle::validate_pending_22_case(
                &group.bytes,
                &runtime_case.feature_id,
                &input,
                &output,
            )?,
            "remaining" => remaining_oracle::validate_pending_22_case(
                &group.bytes,
                &runtime_case.feature_id,
                &input,
                &output,
            )?,
            _ => return Err("unknown pending-22 group".into()),
        }
        if !unique_features.insert(runtime_case.feature_id.clone()) {
            return Err("pending-22 feature ID is duplicated".into());
        }
        feature_ids.push(runtime_case.feature_id.clone());
    }

    require_digest(
        &read_bounded_file(&runtime_path, MAX_MANIFEST_BYTES)?,
        &arguments.runtime_trace_sha256,
        "pending-22 runtime trace recheck",
    )?;
    for group in &groups {
        require_digest(
            &read_bounded_file(
                &canonical_existing_under(
                    match group.id {
                        "merge_split" => &arguments.merge_split_manifest,
                        "layout_placement" => &arguments.layout_placement_manifest,
                        "remaining" => &arguments.remaining_manifest,
                        _ => return Err("unknown pending-22 group".into()),
                    },
                    &target_root,
                )?,
                MAX_MANIFEST_BYTES,
            )?,
            group.expected_manifest_sha256,
            "fixture manifest recheck",
        )?;
    }

    let receipt_path = create_new_path_under(&arguments.output_receipt, &target_root)?;
    let receipt = OracleReceipt {
        schema_version: "hwpx-agent.p06-09-table-pending-22-target-oracle/v1",
        state: "pass",
        runtime_trace_sha256: arguments.runtime_trace_sha256.clone(),
        fixture_manifest_sha256: BTreeMap::from([
            ("merge_split", EXPECTED_MERGE_SPLIT_SHA256),
            ("layout_placement", EXPECTED_LAYOUT_PLACEMENT_SHA256),
            ("remaining", EXPECTED_REMAINING_SHA256),
        ]),
        feature_ids,
        group_case_count: BTreeMap::from([
            ("merge_split", 2),
            ("layout_placement", 10),
            ("remaining", 10),
        ]),
        case_count: EXPECTED_CASE_COUNT,
        lifecycle_trace_passed: EXPECTED_CASE_COUNT,
        typed_semantic_readback_passed: EXPECTED_CASE_COUNT,
        input_immutability_passed: EXPECTED_CASE_COUNT,
        pdf_signature_passed: EXPECTED_CASE_COUNT,
        actual_hangul_2020: true,
        render: "pdf_signature_passed_external_original_detail_review_required",
        automation: "not_run",
        differential: "not_run",
    };
    write_create_new(&receipt_path, &serde_json::to_vec_pretty(&receipt)?)?;
    println!(
        "schema={} state=pass feature_count={} actual_hangul_2020=true",
        receipt.schema_version, receipt.case_count
    );
    Ok(())
}

fn read_fixture_group(
    id: &'static str,
    path: &Path,
    supplied_sha256: &str,
    expected_sha256: &'static str,
    target_root: &Path,
) -> Result<FixtureGroup, AnyError> {
    require_exact_sha256(supplied_sha256, expected_sha256, id)?;
    let canonical = canonical_existing_under(path, target_root)?;
    let bytes = read_bounded_file(&canonical, MAX_MANIFEST_BYTES)?;
    require_digest(&bytes, expected_sha256, id)?;
    let index: FixtureIndex = serde_json::from_slice(&bytes)?;
    let directory = canonical
        .parent()
        .ok_or("fixture manifest has no parent")?
        .to_path_buf();
    Ok(FixtureGroup {
        id,
        expected_manifest_sha256: expected_sha256,
        directory,
        bytes,
        cases: index.cases,
    })
}

fn require_group_counts(groups: &[FixtureGroup]) -> Result<(), AnyError> {
    if groups.len() != 3
        || groups[0].id != "merge_split"
        || groups[0].cases.len() != 2
        || groups[1].id != "layout_placement"
        || groups[1].cases.len() != 10
        || groups[2].id != "remaining"
        || groups[2].cases.len() != 10
    {
        return Err("pending-22 fixture group boundary differs".into());
    }
    Ok(())
}

fn require_runtime_boundary(value: &RuntimeTrace) -> Result<(), AnyError> {
    let expected_progress_event_count = expected_progress_event_count(
        value.access_control.open_attempt_count,
        value.access_control.first_open_returned_false,
    )
    .ok_or("pending-22 access-control retry evidence is inconsistent")?;
    if value.schema_version != "hwpx-agent.p06-09-table-pending-22-target-batch-readback/v1"
        || value.state != "pass"
        || value.target.prog_id != "HWPFrame.HwpObject.2"
        || value.target.registry_view != "Registry32"
        || value.target.client != "windows_powershell_x86_sta"
        || value.target.file_version != "11.0.0.9136"
        || value.target.executable_sha256 != EXPECTED_HANCOM_SHA256
        || value.session_strategy != "single_hwp_process_for_22_cases"
        || value.access_approval_strategy != "user_selects_allow_all_once"
        || value.access_control.source != "verified_hancom_saved_table_012_control"
        || value.access_control.input_file != EXPECTED_ACCESS_CONTROL_FILE
        || value.access_control.input_sha256 != EXPECTED_ACCESS_CONTROL_SHA256
        || !value.access_control.input_unchanged
        || value.access_control.retry_policy
            != "one_same_session_hwp_object_retry_after_first_false"
        || value.access_control.open_state != "pass"
        || value.access_control.close_state != "pass"
        || value.manifest_sha256.merge_split != EXPECTED_MERGE_SPLIT_SHA256
        || value.manifest_sha256.layout_placement != EXPECTED_LAYOUT_PLACEMENT_SHA256
        || value.manifest_sha256.remaining != EXPECTED_REMAINING_SHA256
        || value.case_count != EXPECTED_CASE_COUNT
        || value.completed_case_count != EXPECTED_CASE_COUNT
        || value.cases.len() != EXPECTED_CASE_COUNT
        || value.failed_feature_id.is_some()
        || value.error_code.is_some()
        || value.failed_phase.is_some()
        || value.exception_type.is_some()
        || value.exception_hresult.is_some()
        || value.raw_document_text_present
        || value.user_document_scanned
        || value.external_network_invoked
        || value.registry_or_system_setting_changed
        || value.computer_use_click_or_type_invoked
        || !value.window_visible_for_user_access
        || value.delegated_engine_schema
            != "hwpx-agent.p06-09-hancom-2020-table-pending-22-target-batch-engine/v1"
        || !value.access_approval_user_owned
        || !watchdog_is_complete(&value.watchdog, expected_progress_event_count)
    {
        return Err("pending-22 runtime trace is not a complete exact-target pass".into());
    }
    Ok(())
}

fn expected_progress_event_count(
    open_attempt_count: u32,
    first_open_returned_false: bool,
) -> Option<u32> {
    match (open_attempt_count, first_open_returned_false) {
        (1, false) => Some(EXPECTED_PROGRESS_EVENT_COUNT_FIRST_OPEN),
        (2, true) => Some(EXPECTED_PROGRESS_EVENT_COUNT_RETRY),
        _ => None,
    }
}

fn watchdog_is_complete(value: &RuntimeWatchdog, expected_progress_event_count: u32) -> bool {
    (300..=7200).contains(&value.timeout_seconds)
        && !value.timed_out
        && value.child_exit_code == 0
        && value.output_drained
        && value.cleaned_process_count <= 1
        && value.cleanup_refused_count == 0
        && value.cleanup_error_count == 0
        && value.remaining_hwp_process_count == 0
        && value.progress_present
        && value.progress_valid
        && value.progress_event_count == expected_progress_event_count
        && value.progress_last_phase == "terminal"
        && value.progress_last_state == "pass"
        && value.progress_observed_phase == "close_output"
        && value.progress_observed_feature_id == "TABLE-060"
        && value.progress_worker_process_id > 0
        && value.progress_hwp_process_id > 0
        && value.window_visible_for_user_access
}

fn require_case_boundary(
    runtime: &RuntimeCase,
    group: &FixtureGroup,
    group_case_index: usize,
    fixture: &FixtureCase,
) -> Result<(), AnyError> {
    let stem = fixture
        .file
        .strip_suffix(".hwpx")
        .ok_or("pending-22 fixture extension differs")?;
    let expected_text_source = if group.id == "layout_placement" {
        "fixture_contract"
    } else {
        "same_session_input_readback"
    };
    if runtime.group_id != group.id
        || runtime.group_case_index != group_case_index
        || runtime.case_id != fixture.case_id
        || runtime.feature_id != fixture.feature_id
        || runtime.capability_id != fixture.capability_id
        || runtime.manifest_sha256 != group.expected_manifest_sha256
        || runtime.input_file != fixture.file
        || runtime.input_sha256 != fixture.sha256
        || !runtime.input_unchanged
        || runtime.expected_text_source != expected_text_source
        || !is_lower_sha256(&runtime.input_text_sha256)
        || (group.id == "layout_placement"
            && runtime.input_text_sha256 != EXPECTED_LAYOUT_TEXT_SHA256)
        || runtime.output_file != format!("{stem}.hancom-2020-readback.hwpx")
        || !is_lower_sha256(&runtime.output_sha256)
        || runtime.output_text_sha256 != runtime.input_text_sha256
        || !runtime.output_saved
        || runtime.render_pdf_file != format!("{stem}.hancom-2020-render.pdf")
        || !runtime.render_pdf_saved
        || !is_lower_sha256(&runtime.render_pdf_sha256)
        || runtime.render_pdf_bytes < 5
        || runtime.render_pdf_bytes > MAX_PDF_BYTES
        || !runtime.render_pdf_signature_valid
        || runtime.render_pdf_export_method != "IXHwpDocument.SaveAs/PDF"
        || !phases_are_complete(&runtime.phases)
        || runtime.error_code.is_some()
        || runtime.failed_phase.is_some()
    {
        return Err(format!("{} runtime case boundary differs", runtime.feature_id).into());
    }
    Ok(())
}

fn phases_are_complete(value: &RuntimePhases) -> bool {
    value.open_input == "pass"
        && value.read_input == "pass"
        && value.save_as_hwpx == "pass"
        && value.close_input == "pass"
        && value.reopen_output == "pass"
        && value.read_output == "pass"
        && value.export_pdf == "pass"
        && value.close_output == "pass"
}

fn target_root() -> Result<PathBuf, AnyError> {
    let manifest_directory = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let repository = manifest_directory
        .parent()
        .and_then(Path::parent)
        .ok_or("repository root cannot be resolved")?;
    Ok(fs::canonicalize(
        repository.join("fixtures").join("target-build"),
    )?)
}

fn canonical_existing_under(path: &Path, root: &Path) -> Result<PathBuf, AnyError> {
    let source_metadata = fs::symlink_metadata(path)?;
    if !source_metadata.is_file() || source_metadata.file_type().is_symlink() {
        return Err("evidence path is not a direct regular file".into());
    }
    let canonical = fs::canonicalize(path)?;
    if !canonical.starts_with(root) || canonical == root {
        return Err("path escapes fixtures/target-build".into());
    }
    let metadata = fs::symlink_metadata(&canonical)?;
    if !metadata.is_file() || metadata.file_type().is_symlink() {
        return Err("evidence path is not a regular file".into());
    }
    Ok(canonical)
}

fn create_new_path_under(path: &Path, root: &Path) -> Result<PathBuf, AnyError> {
    if path.exists() {
        return Err("output receipt already exists".into());
    }
    let source_parent = path.parent().ok_or("output receipt has no parent")?;
    if fs::symlink_metadata(source_parent)?
        .file_type()
        .is_symlink()
    {
        return Err("output receipt parent is a reparse path".into());
    }
    let parent = fs::canonicalize(source_parent)?;
    if !parent.starts_with(root) || parent == root {
        return Err("output receipt escapes fixtures/target-build".into());
    }
    let name = path.file_name().ok_or("output receipt has no file name")?;
    Ok(parent.join(name))
}

fn resolve_single_file(directory: &Path, value: &str) -> Result<PathBuf, AnyError> {
    let path = Path::new(value);
    let mut components = path.components();
    if !matches!(components.next(), Some(Component::Normal(_))) || components.next().is_some() {
        return Err("runtime file name is not a single normal component".into());
    }
    canonical_existing_under(&directory.join(path), directory)
}

fn read_bounded_file(path: &Path, maximum: u64) -> Result<Vec<u8>, AnyError> {
    let metadata = fs::symlink_metadata(path)?;
    if !metadata.is_file()
        || metadata.file_type().is_symlink()
        || metadata.len() == 0
        || metadata.len() > maximum
    {
        return Err(format!("bounded file check failed: {}", path.display()).into());
    }
    Ok(fs::read(path)?)
}

fn write_create_new(path: &Path, bytes: &[u8]) -> Result<(), AnyError> {
    let mut file = OpenOptions::new().write(true).create_new(true).open(path)?;
    file.write_all(bytes)?;
    file.sync_all()?;
    Ok(())
}

fn require_exact_sha256(value: &str, expected: &str, label: &str) -> Result<(), AnyError> {
    require_lower_sha256(value)?;
    if value != expected {
        return Err(format!("{label} identity differs").into());
    }
    Ok(())
}

fn require_digest(bytes: &[u8], expected: &str, label: &str) -> Result<(), AnyError> {
    require_lower_sha256(expected)?;
    if hex(Sha256::digest(bytes)) != expected {
        return Err(format!("{label} SHA-256 differs").into());
    }
    Ok(())
}

fn require_lower_sha256(value: &str) -> Result<(), AnyError> {
    if !is_lower_sha256(value) {
        return Err("SHA-256 must be lowercase hexadecimal".into());
    }
    Ok(())
}

fn is_lower_sha256(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

fn hex(bytes: impl AsRef<[u8]>) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let bytes = bytes.as_ref();
    let mut output = String::with_capacity(bytes.len() * 2);
    for byte in bytes {
        output.push(char::from(DIGITS[usize::from(byte >> 4)]));
        output.push(char::from(DIGITS[usize::from(byte & 0x0f)]));
    }
    output
}

fn path_argument(
    values: &mut impl Iterator<Item = OsString>,
    label: &str,
) -> Result<PathBuf, AnyError> {
    values
        .next()
        .map(PathBuf::from)
        .ok_or_else(|| format!("missing {label}").into())
}

fn string_argument(
    values: &mut impl Iterator<Item = OsString>,
    label: &str,
) -> Result<String, AnyError> {
    values
        .next()
        .ok_or_else(|| format!("missing {label}"))?
        .into_string()
        .map_err(|_| format!("{label} is not Unicode").into())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sha256_boundary_is_lowercase_only() {
        assert!(is_lower_sha256(&"a".repeat(64)));
        assert!(!is_lower_sha256(&"A".repeat(64)));
        assert!(!is_lower_sha256(&"g".repeat(64)));
        assert!(!is_lower_sha256(&"a".repeat(63)));
    }

    #[test]
    fn phases_require_every_lifecycle_step() {
        let mut phases = RuntimePhases {
            open_input: "pass".into(),
            read_input: "pass".into(),
            save_as_hwpx: "pass".into(),
            close_input: "pass".into(),
            reopen_output: "pass".into(),
            read_output: "pass".into(),
            export_pdf: "pass".into(),
            close_output: "pass".into(),
        };
        assert!(phases_are_complete(&phases));
        phases.export_pdf = "not_run".into();
        assert!(!phases_are_complete(&phases));
    }

    #[test]
    fn single_file_boundary_rejects_traversal() {
        let directory = Path::new("fixture");
        assert!(resolve_single_file(directory, "../escape.hwpx").is_err());
        assert!(resolve_single_file(directory, "nested/file.hwpx").is_err());
    }

    #[test]
    fn progress_count_covers_one_session_and_all_cases() {
        assert_eq!(
            EXPECTED_PROGRESS_EVENT_COUNT_FIRST_OPEN,
            2 + 4 + 22 * 16 + 2 + 1
        );
        assert_eq!(EXPECTED_PROGRESS_EVENT_COUNT_RETRY, 2 + 6 + 22 * 16 + 2 + 1);
        assert_eq!(expected_progress_event_count(1, false), Some(361));
        assert_eq!(expected_progress_event_count(2, true), Some(363));
        assert_eq!(expected_progress_event_count(1, true), None);
        assert_eq!(expected_progress_event_count(2, false), None);
    }
}
