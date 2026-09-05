//! Local, fixed-fixture diagnostics. This is not an accepting inspector or a remap authority.

use std::error::Error;
use std::ffi::OsString;
use std::fs;
use std::io::{Cursor, Read as _};
use std::path::Path;

use hwpx_package::{
    BoundedZipReader, ColumnDefinition, PackageGraph, PackageGraphLimits, PackageLimits, PageSetup,
    PageSetupLimits, PageSetupReader, SectionColumnLimits, SectionColumnReader,
};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};

const TRACE_LIMIT: u64 = 131_072;
const BUILD: &str = "11.0.0.9136";
const EXECUTABLE: &str = "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce";
const USAGE: &str = "usage: diagnose <source.hwpx> <saved.hwpx> <trace.json> <trace-sha256>";

pub(super) fn run(arguments: impl Iterator<Item = OsString>) -> Result<(), Box<dyn Error>> {
    let arguments: Vec<_> = arguments.take(5).collect();
    if arguments.len() != 4 {
        return Err(USAGE.into());
    }
    let source = read_bounded(Path::new(&arguments[0]), super::MAX_TARGET_FIXTURE_BYTES)?;
    let saved = read_bounded(Path::new(&arguments[1]), super::MAX_TARGET_FIXTURE_BYTES)?;
    let trace = read_bounded(Path::new(&arguments[2]), TRACE_LIMIT)?;
    let expected_trace = arguments[3].to_str().ok_or(USAGE)?;
    let report = diagnose(&source, &saved, &trace, expected_trace)?;
    println!("{}", serde_json::to_string_pretty(&report)?);
    if !report.semantic_checks_pass {
        return Err("P05_07_DIAGNOSTIC_DIFFERENCES_RETAINED".into());
    }
    Ok(())
}

fn read_bounded(path: &Path, limit: u64) -> Result<Vec<u8>, Box<dyn Error>> {
    let metadata = fs::symlink_metadata(path)?;
    if !metadata.is_file()
        || metadata.file_type().is_symlink()
        || metadata.len() == 0
        || metadata.len() > limit
    {
        return Err("diagnostic input is not a bounded regular file".into());
    }
    let mut bytes = Vec::new();
    fs::File::open(path)?
        .take(limit + 1)
        .read_to_end(&mut bytes)?;
    if bytes.len() as u64 != metadata.len() {
        return Err("diagnostic input changed while being read".into());
    }
    Ok(bytes)
}

fn digest(bytes: &[u8]) -> String {
    hex::encode(Sha256::digest(bytes))
}

#[derive(Serialize)]
#[expect(
    clippy::struct_excessive_bools,
    reason = "Independent diagnostic claims, not mutually exclusive execution states"
)]
struct DiagnosticReport {
    schema_version: &'static str,
    scope: &'static str,
    overall_acceptance: &'static str,
    semantic_checks_pass: bool,
    trace_binding: &'static str,
    trace_sha256: String,
    source_sha256: String,
    saved_sha256: String,
    target_build: &'static str,
    actual_execution_independently_attested: bool,
    pdf_or_visual_verified: bool,
    logical_identity_remap_verified: bool,
    raw_document_text_or_backend_ids_present: bool,
    sections: Vec<SectionComparison>,
}

#[derive(Serialize)]
#[expect(
    clippy::struct_excessive_bools,
    reason = "Every independent comparison must remain visible even when another comparison fails"
)]
struct SectionComparison {
    section_ordinal: usize,
    comparison_basis: &'static str,
    source_page_matches_target: bool,
    saved_page_matches_target: bool,
    page_values_equal: bool,
    source_columns_admitted_at_actual_body_width: bool,
    saved_columns_admitted_at_actual_body_width: bool,
    source_columns_admitted_in_target_frame: bool,
    saved_columns_admitted_in_target_frame: bool,
    column_values_equal_excluding_ids: bool,
    source_column_values_match_target: bool,
    saved_column_values_match_target: bool,
    source_control_id_matches_target: bool,
    saved_control_id_matches_target: bool,
    control_ids_equal: bool,
    removed_backend_identifier_count: Option<usize>,
    source_text_matches_target: bool,
    saved_text_matches_target: bool,
    text_values_equal: bool,
}

impl SectionComparison {
    fn passes(&self) -> bool {
        self.source_page_matches_target
            && self.saved_page_matches_target
            && self.page_values_equal
            && self.source_columns_admitted_at_actual_body_width
            && self.saved_columns_admitted_at_actual_body_width
            && self.source_columns_admitted_in_target_frame
            && self.saved_columns_admitted_in_target_frame
            && self.column_values_equal_excluding_ids
            && self.source_column_values_match_target
            && self.saved_column_values_match_target
            && self.source_control_id_matches_target
            && self.saved_control_id_matches_target
            && self.control_ids_equal
            && self.removed_backend_identifier_count == Some(0)
            && self.source_text_matches_target
            && self.saved_text_matches_target
            && self.text_values_equal
    }
}

struct SectionSnapshot {
    page: Option<PageSetup>,
    // The target frame is deliberately separate from admission at the actual page body width.
    // A wrong orientation must not hide an independently observable identifier removal.
    columns_in_target_frame: Option<Vec<ColumnDefinition>>,
    columns_admitted_at_actual_body_width: bool,
    text: String,
}

fn snapshot(bytes: &[u8]) -> Result<Vec<SectionSnapshot>, Box<dyn Error>> {
    if bytes.is_empty() || bytes.len() as u64 > super::MAX_TARGET_FIXTURE_BYTES {
        return Err("diagnostic package exceeds fixture bound".into());
    }
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    super::verify_linear_spine(&graph)?;
    let expected_spine = [
        "Contents/header.xml",
        "Contents/section0.xml",
        "Contents/section1.xml",
    ];
    if graph
        .spine
        .iter()
        .map(hwpx_package::PackagePath::as_str)
        .ne(expected_spine)
        || graph.parts.len() != reader.entries().len()
    {
        return Err("diagnostic fixture package closure or order mismatch".into());
    }
    let header = super::read_part(&mut reader, "Contents/header.xml")?;
    if SectionColumnReader::read_header_section_count(&header, SectionColumnLimits::default())? != 2
    {
        return Err("diagnostic fixture header count mismatch".into());
    }
    let target_width = super::expected_body_width()?;
    let mut result = Vec::with_capacity(2);
    for path in [&expected_spine[1], &expected_spine[2]] {
        let section = super::read_part(&mut reader, path)?;
        let page = PageSetupReader::read(&section, PageSetupLimits::default()).ok();
        let columns_admitted_at_actual_body_width = page
            .as_ref()
            .and_then(|value| value.metrics(PageSetupLimits::default()).ok())
            .is_some_and(|metrics| {
                SectionColumnReader::read_section(
                    &section,
                    metrics.body_width,
                    SectionColumnLimits::default(),
                )
                .is_ok()
            });
        let columns_in_target_frame = SectionColumnReader::read_section(
            &section,
            target_width,
            SectionColumnLimits::default(),
        )
        .ok()
        .map(|value| value.spans);
        result.push(SectionSnapshot {
            page,
            columns_in_target_frame,
            columns_admitted_at_actual_body_width,
            text: super::visible_text(&section)?,
        });
    }
    Ok(result)
}

fn equal_values(left: &ColumnDefinition, right: &ColumnDefinition) -> bool {
    left.column_type == right.column_type
        && left.layout == right.layout
        && left.sizing == right.sizing
        && left.separator == right.separator
}

fn one_column(snapshot: &SectionSnapshot) -> Option<&ColumnDefinition> {
    match snapshot.columns_in_target_frame.as_deref()? {
        [column] => Some(column),
        _ => None,
    }
}

fn compare(
    source: &[SectionSnapshot],
    saved: &[SectionSnapshot],
) -> Result<Vec<SectionComparison>, Box<dyn Error>> {
    if source.len() != 2 || saved.len() != 2 {
        return Err("diagnostic snapshot count mismatch".into());
    }
    let target_page = super::expected_page_setup()?;
    let target_columns = [super::section_one_columns(), super::section_two_columns()];
    let target_text = [super::SECTION_ONE_TEXT, super::SECTION_TWO_TEXT];
    let mut sections = Vec::with_capacity(2);
    for ordinal in 0..2 {
        let before = &source[ordinal];
        let after = &saved[ordinal];
        let left = one_column(before);
        let right = one_column(after);
        sections.push(SectionComparison {
            section_ordinal: ordinal,
            comparison_basis: "positional_target_frame_not_logical_identity_proof",
            source_page_matches_target: before.page.as_ref() == Some(&target_page),
            saved_page_matches_target: after.page.as_ref() == Some(&target_page),
            page_values_equal: before.page.is_some() && before.page == after.page,
            source_columns_admitted_at_actual_body_width: before
                .columns_admitted_at_actual_body_width,
            saved_columns_admitted_at_actual_body_width: after
                .columns_admitted_at_actual_body_width,
            source_columns_admitted_in_target_frame: left.is_some(),
            saved_columns_admitted_in_target_frame: right.is_some(),
            column_values_equal_excluding_ids: left
                .zip(right)
                .is_some_and(|(a, b)| equal_values(a, b)),
            source_column_values_match_target: left
                .is_some_and(|a| equal_values(a, &target_columns[ordinal])),
            saved_column_values_match_target: right
                .is_some_and(|a| equal_values(a, &target_columns[ordinal])),
            source_control_id_matches_target: left
                .is_some_and(|a| a.control_id == target_columns[ordinal].control_id),
            saved_control_id_matches_target: right
                .is_some_and(|a| a.control_id == target_columns[ordinal].control_id),
            control_ids_equal: left
                .zip(right)
                .is_some_and(|(a, b)| a.control_id == b.control_id),
            removed_backend_identifier_count: left
                .zip(right)
                .map(|(a, b)| usize::from(!a.control_id.is_empty() && b.control_id.is_empty())),
            source_text_matches_target: before.text == target_text[ordinal],
            saved_text_matches_target: after.text == target_text[ordinal],
            text_values_equal: before.text == after.text,
        });
    }
    Ok(sections)
}

fn diagnose(
    source: &[u8],
    saved: &[u8],
    trace_bytes: &[u8],
    expected_trace: &str,
) -> Result<DiagnosticReport, Box<dyn Error>> {
    if trace_bytes.is_empty()
        || trace_bytes.len() as u64 > TRACE_LIMIT
        || expected_trace.len() != 64
        || !expected_trace
            .bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
        || digest(trace_bytes) != expected_trace
    {
        return Err("diagnostic trace digest or bound mismatch".into());
    }
    let trace: Trace =
        serde_json::from_slice(trace_bytes).map_err(|_| "diagnostic trace shape invalid")?;
    trace.validate(source, saved)?;
    let source_snapshot = snapshot(source).map_err(|_| "diagnostic source structure invalid")?;
    let saved_snapshot = snapshot(saved).map_err(|_| "diagnostic saved structure invalid")?;
    let text_digest = |sections: &[SectionSnapshot]| {
        digest(
            sections
                .iter()
                .map(|value| value.text.as_str())
                .collect::<Vec<_>>()
                .join("\n")
                .as_bytes(),
        )
    };
    if trace.input_text_sha256 != text_digest(&source_snapshot)
        || trace.output_text_sha256 != text_digest(&saved_snapshot)
    {
        return Err("diagnostic trace text binding mismatch".into());
    }
    let sections = compare(&source_snapshot, &saved_snapshot)?;
    Ok(DiagnosticReport {
        schema_version: "hwpx-agent.p05-07-source-bound-diagnostic/v1",
        scope: "fixed_synthetic_fixture_current_2020_only",
        overall_acceptance: "not_granted_diagnostic_only",
        semantic_checks_pass: sections.iter().all(SectionComparison::passes),
        trace_binding: "consistent_local_claim_not_independent_attestation",
        trace_sha256: digest(trace_bytes),
        source_sha256: digest(source),
        saved_sha256: digest(saved),
        target_build: BUILD,
        actual_execution_independently_attested: false,
        pdf_or_visual_verified: false,
        logical_identity_remap_verified: false,
        raw_document_text_or_backend_ids_present: false,
        sections,
    })
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Target {
    prog_id: String,
    registry_view: String,
    client: String,
    file_version: String,
    executable_sha256: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Phases {
    com_create: String,
    open_input: String,
    read_input: String,
    save_as_hwpx: String,
    close_input: String,
    reopen_output: String,
    read_output: String,
    export_pdf: String,
    close_output: String,
    quit: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
#[expect(
    clippy::struct_excessive_bools,
    reason = "Exact existing watchdog JSON wire shape; each flag is validated independently"
)]
struct Watchdog {
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
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
#[expect(
    clippy::struct_excessive_bools,
    reason = "Exact existing readback JSON wire shape; not an alternative execution state machine"
)]
struct Trace {
    schema_version: String,
    state: String,
    target: Target,
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
    render_pdf_export_method: String,
    phases: Phases,
    error_code: serde_json::Value,
    failed_phase: serde_json::Value,
    exception_type: serde_json::Value,
    exception_hresult: serde_json::Value,
    raw_document_text_present: bool,
    user_document_scanned: bool,
    external_network_invoked: bool,
    registry_or_system_setting_changed: bool,
    computer_use_click_or_type_invoked: bool,
    window_visible_for_user_access: bool,
    delegated_engine_schema: String,
    watchdog: Watchdog,
}

impl Trace {
    fn validate(&self, source: &[u8], saved: &[u8]) -> Result<(), Box<dyn Error>> {
        let target = &self.target;
        let phases = &self.phases;
        let watchdog = &self.watchdog;
        if self.schema_version != "hwpx-agent.p05-07-hancom-2020-section-columns-readback/v1"
            || self.delegated_engine_schema != "hwpx-agent.p05-04-hancom-2020-tab-readback/v1"
            || self.state != "pass"
            || target.file_version != BUILD
            || target.executable_sha256 != EXECUTABLE
            || target.prog_id != "HWPFrame.HwpObject.2"
            || target.registry_view != "Registry32"
            || target.client != "windows_powershell_x86_sta"
            || !self.input_unchanged
            || !self.output_saved
            || self.input_sha256 != digest(source)
            || self.output_sha256 != digest(saved)
            || !self.error_code.is_null()
            || !self.failed_phase.is_null()
            || !self.exception_type.is_null()
            || !self.exception_hresult.is_null()
            || self.raw_document_text_present
            || self.user_document_scanned
            || self.external_network_invoked
            || self.registry_or_system_setting_changed
            || self.computer_use_click_or_type_invoked
            || !self.window_visible_for_user_access
            || !self.render_pdf_requested
            || !self.render_pdf_saved
            || !self.render_pdf_signature_valid
            || self.render_pdf_export_method != "IXHwpDocument.SaveAs/PDF"
            || !(5..=33_554_432).contains(&self.render_pdf_bytes)
            || self.render_pdf_sha256.len() != 64
            || !self
                .render_pdf_sha256
                .bytes()
                .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
            || [
                &phases.com_create,
                &phases.open_input,
                &phases.read_input,
                &phases.save_as_hwpx,
                &phases.close_input,
                &phases.reopen_output,
                &phases.read_output,
                &phases.export_pdf,
                &phases.close_output,
                &phases.quit,
            ]
            .iter()
            .any(|value| value.as_str() != "pass")
            || !(30..=900).contains(&watchdog.timeout_seconds)
            || watchdog.timed_out
            || watchdog.child_exit_code != 0
            || !watchdog.output_drained
            || watchdog.cleaned_process_count != 0
            || watchdog.cleanup_refused_count != 0
            || watchdog.cleanup_error_count != 0
            || watchdog.remaining_hwp_process_count != 0
            || !watchdog.progress_present
            || !watchdog.progress_valid
            || watchdog.progress_event_count != 21
            || watchdog.progress_last_phase != "terminal"
            || watchdog.progress_last_state != "pass"
        {
            return Err("diagnostic trace is not consistent with the bounded target run".into());
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::{Value, json};
    use std::io::Write as _;
    use zip::{ZipArchive, ZipWriter, write::SimpleFileOptions};

    fn fixture() -> Result<Vec<u8>, Box<dyn Error>> {
        let source = crate::Hancom2020Vs0Builder::build(crate::SECTION_ONE_TEXT)?;
        crate::rebuild_with_two_sections(&source.with_verified_bytes(ToOwned::to_owned)?)
    }

    fn rewrite(bytes: &[u8], part: &str, from: &str, to: &str) -> Result<Vec<u8>, Box<dyn Error>> {
        let mut archive = ZipArchive::new(Cursor::new(bytes))?;
        let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
        let mut changed = false;
        for index in 0..archive.len() {
            let mut entry = archive.by_index(index)?;
            let mut payload = Vec::new();
            entry.read_to_end(&mut payload)?;
            if entry.name() == part {
                let text = std::str::from_utf8(&payload)?;
                assert_eq!(text.matches(from).count(), 1, "unique test anchor required");
                payload = text.replace(from, to).into_bytes();
                changed = true;
            }
            writer.start_file(
                entry.name(),
                SimpleFileOptions::default().compression_method(entry.compression()),
            )?;
            writer.write_all(&payload)?;
        }
        assert!(changed);
        Ok(writer.finish()?.into_inner())
    }

    fn trace_value(source: &[u8], saved: &[u8]) -> Result<Value, Box<dyn Error>> {
        let text_hash = |bytes| -> Result<String, Box<dyn Error>> {
            Ok(digest(
                snapshot(bytes)?
                    .iter()
                    .map(|s| s.text.as_str())
                    .collect::<Vec<_>>()
                    .join("\n")
                    .as_bytes(),
            ))
        };
        Ok(json!({
            "schema_version": "hwpx-agent.p05-07-hancom-2020-section-columns-readback/v1",
            "delegated_engine_schema": "hwpx-agent.p05-04-hancom-2020-tab-readback/v1", "state": "pass",
            "target": { "prog_id": "HWPFrame.HwpObject.2", "registry_view": "Registry32", "client": "windows_powershell_x86_sta", "file_version": BUILD, "executable_sha256": EXECUTABLE },
            "input_sha256": digest(source), "output_sha256": digest(saved), "input_unchanged": true,
            "input_text_sha256": text_hash(source)?, "output_text_sha256": text_hash(saved)?, "output_saved": true,
            "render_pdf_requested": true, "render_pdf_saved": true, "render_pdf_signature_valid": true,
            "render_pdf_sha256": "a".repeat(64), "render_pdf_bytes": 100, "render_pdf_export_method": "IXHwpDocument.SaveAs/PDF",
            "phases": { "com_create": "pass", "open_input": "pass", "read_input": "pass", "save_as_hwpx": "pass", "close_input": "pass", "reopen_output": "pass", "read_output": "pass", "export_pdf": "pass", "close_output": "pass", "quit": "pass" },
            "error_code": null, "failed_phase": null, "exception_type": null, "exception_hresult": null,
            "raw_document_text_present": false, "user_document_scanned": false, "external_network_invoked": false,
            "registry_or_system_setting_changed": false, "computer_use_click_or_type_invoked": false,
            "window_visible_for_user_access": true,
            "watchdog": { "timeout_seconds": 600, "timed_out": false, "child_exit_code": 0, "output_drained": true,
                "cleaned_process_count": 0, "cleanup_refused_count": 0, "cleanup_error_count": 0, "remaining_hwp_process_count": 0,
                "progress_present": true, "progress_valid": true, "progress_event_count": 21,
                "progress_last_phase": "terminal", "progress_last_state": "pass" }
        }))
    }

    fn checked(source: &[u8], saved: &[u8]) -> Result<DiagnosticReport, Box<dyn Error>> {
        let trace = serde_json::to_vec(&trace_value(source, saved)?)?;
        diagnose(source, saved, &trace, &digest(&trace))
    }

    #[test]
    fn diagnostics_identical_fixture_is_comparable_but_never_attests_execution()
    -> Result<(), Box<dyn Error>> {
        let source = fixture()?;
        let report = checked(&source, &source)?;
        assert!(report.semantic_checks_pass);
        assert_eq!(report.sections.len(), 2);
        assert_eq!(report.overall_acceptance, "not_granted_diagnostic_only");
        assert!(!report.actual_execution_independently_attested);
        assert!(!report.pdf_or_visual_verified);
        assert!(!report.logical_identity_remap_verified);
        let serialized = serde_json::to_string(&report)?;
        for private_value in [
            "P05-07-SECTION-ONE",
            "p05-07-equal",
            "p05-07-custom",
            "Contents/",
            "<hp:",
        ] {
            assert!(!serialized.contains(private_value));
        }
        Ok(())
    }

    #[test]
    fn diagnostics_reports_orientation_and_id_removal_independently() -> Result<(), Box<dyn Error>>
    {
        let source = fixture()?;
        let saved = rewrite(
            &source,
            "Contents/section1.xml",
            "landscape=\"NARROWLY\"",
            "landscape=\"WIDELY\"",
        )?;
        let saved = rewrite(
            &saved,
            "Contents/section1.xml",
            "id=\"p05-07-custom\"",
            "id=\"\"",
        )?;
        let report = checked(&source, &saved)?;
        let changed = &report.sections[1];
        assert!(!report.semantic_checks_pass);
        assert!(!changed.saved_page_matches_target);
        assert!(!changed.saved_columns_admitted_at_actual_body_width);
        assert!(changed.saved_columns_admitted_in_target_frame);
        assert!(changed.column_values_equal_excluding_ids);
        assert!(!changed.control_ids_equal);
        assert_eq!(changed.removed_backend_identifier_count, Some(1));
        assert!(changed.text_values_equal);
        assert!(crate::inspect_bytes(&saved).is_err());
        Ok(())
    }

    #[test]
    fn diagnostics_id_only_change_remains_failed() -> Result<(), Box<dyn Error>> {
        let source = fixture()?;
        let saved = rewrite(
            &source,
            "Contents/section0.xml",
            "id=\"p05-07-equal\"",
            "id=\"\"",
        )?;
        let report = checked(&source, &saved)?;
        assert!(!report.semantic_checks_pass);
        assert!(report.sections[0].saved_page_matches_target);
        assert!(report.sections[0].column_values_equal_excluding_ids);
        assert!(!report.sections[0].control_ids_equal);
        assert!(crate::inspect_bytes(&saved).is_err());
        Ok(())
    }

    #[test]
    fn diagnostics_two_removed_ids_are_not_a_shared_empty_identity() -> Result<(), Box<dyn Error>> {
        let source = fixture()?;
        let saved = rewrite(
            &source,
            "Contents/section0.xml",
            "id=\"p05-07-equal\"",
            "id=\"\"",
        )?;
        let saved = rewrite(
            &saved,
            "Contents/section1.xml",
            "id=\"p05-07-custom\"",
            "id=\"\"",
        )?;
        let report = checked(&source, &saved)?;
        assert_eq!(
            report
                .sections
                .iter()
                .map(|s| s.removed_backend_identifier_count)
                .collect::<Vec<_>>(),
            vec![Some(1), Some(1)]
        );
        assert!(!report.semantic_checks_pass);
        assert!(!report.logical_identity_remap_verified);
        Ok(())
    }

    #[test]
    fn diagnostics_equal_wrong_orientation_still_fails_target() -> Result<(), Box<dyn Error>> {
        let source = fixture()?;
        let changed = rewrite(
            &source,
            "Contents/section0.xml",
            "landscape=\"NARROWLY\"",
            "landscape=\"WIDELY\"",
        )?;
        let report = checked(&changed, &changed)?;
        assert!(report.sections[0].page_values_equal);
        assert!(!report.sections[0].source_page_matches_target);
        assert!(!report.semantic_checks_pass);
        Ok(())
    }

    #[test]
    fn diagnostics_both_empty_ids_do_not_turn_a_modified_source_into_pass()
    -> Result<(), Box<dyn Error>> {
        let source = fixture()?;
        let changed = rewrite(
            &source,
            "Contents/section0.xml",
            "id=\"p05-07-equal\"",
            "id=\"\"",
        )?;
        assert!(!checked(&changed, &changed)?.semantic_checks_pass);
        Ok(())
    }

    #[test]
    fn diagnostics_semantic_changes_are_not_labeled_id_only() -> Result<(), Box<dyn Error>> {
        let source = fixture()?;
        for (from, to) in [
            ("sameGap=\"1700\"", "sameGap=\"1800\""),
            ("type=\"BALANCED_NEWSPAPER\"", "type=\"NEWSPAPER\""),
            ("layout=\"LEFT\"", "layout=\"RIGHT\""),
            ("color=\"#336699\"", "color=\"#123456\""),
        ] {
            let saved = rewrite(&source, "Contents/section0.xml", from, to)?;
            let report = checked(&source, &saved)?;
            assert!(!report.semantic_checks_pass);
            assert!(!report.sections[0].column_values_equal_excluding_ids);
        }
        let saved = rewrite(
            &source,
            "Contents/section1.xml",
            "width=\"48520\"",
            "width=\"48519\"",
        )?;
        let report = checked(&source, &saved)?;
        assert!(!report.semantic_checks_pass);
        assert!(!report.sections[1].saved_columns_admitted_in_target_frame);
        assert_eq!(report.sections[1].removed_backend_identifier_count, None);
        let saved = rewrite(
            &source,
            "Contents/section0.xml",
            crate::SECTION_ONE_TEXT,
            "CHANGED-TEXT",
        )?;
        let report = checked(&source, &saved)?;
        assert!(!report.semantic_checks_pass);
        assert!(!report.sections[0].text_values_equal);
        Ok(())
    }

    #[test]
    fn diagnostics_invalid_header_spine_and_graph_reject() -> Result<(), Box<dyn Error>> {
        let source = fixture()?;
        for (part, from, to) in [
            ("Contents/header.xml", "secCnt=\"2\"", "secCnt=\"1\""),
            (
                "Contents/content.hpf",
                "idref=\"section0\" linear=\"yes\"",
                "idref=\"section0\" linear=\"no\"",
            ),
            (
                "Contents/content.hpf",
                "idref=\"section0\" linear=\"yes\"",
                "idref=\"missing\" linear=\"yes\"",
            ),
        ] {
            let invalid = rewrite(&source, part, from, to)?;
            assert!(snapshot(&invalid).is_err());
        }
        Ok(())
    }

    #[test]
    fn diagnostics_trace_rejects_stale_source_build_and_lifecycle() -> Result<(), Box<dyn Error>> {
        let source = fixture()?;
        let base = trace_value(&source, &source)?;
        for (pointer, value) in [
            ("/input_sha256", json!("b".repeat(64))),
            ("/output_sha256", json!("b".repeat(64))),
            ("/input_text_sha256", json!("b".repeat(64))),
            ("/target/file_version", json!("2024")),
            ("/watchdog/timed_out", json!(true)),
            ("/watchdog/remaining_hwp_process_count", json!(1)),
            ("/phases/reopen_output", json!("failed")),
            ("/raw_document_text_present", json!(true)),
            (
                "/exception_type",
                json!("private error must not be printed"),
            ),
            ("/watchdog/progress_valid", json!(false)),
        ] {
            let mut invalid = base.clone();
            *invalid.pointer_mut(pointer).ok_or("test pointer missing")? = value;
            let bytes = serde_json::to_vec(&invalid)?;
            assert!(diagnose(&source, &source, &bytes, &digest(&bytes)).is_err());
        }
        let bytes = serde_json::to_vec(&base)?;
        assert!(diagnose(&source, &source, &bytes, &"0".repeat(64)).is_err());
        assert!(diagnose(&source, &source, &[], &digest(&[])).is_err());
        Ok(())
    }

    #[test]
    fn diagnostics_trace_requires_explicit_error_fields_and_target() -> Result<(), Box<dyn Error>> {
        let source = fixture()?;
        for field in [
            "error_code",
            "failed_phase",
            "exception_type",
            "exception_hresult",
            "target",
        ] {
            let mut invalid = trace_value(&source, &source)?;
            invalid
                .as_object_mut()
                .ok_or("test object missing")?
                .remove(field);
            let bytes = serde_json::to_vec(&invalid)?;
            assert!(
                diagnose(&source, &source, &bytes, &digest(&bytes)).is_err(),
                "missing field {field}"
            );
        }
        Ok(())
    }

    #[test]
    fn diagnostics_trace_rejects_duplicate_unknown_and_wrong_types() -> Result<(), Box<dyn Error>> {
        let source = fixture()?;
        let text = serde_json::to_string(&trace_value(&source, &source)?)?;
        for fragment in [
            "\"state\":\"pass\",",
            "\"unknown\":true,",
            "\"input_unchanged\":\"true\",",
        ] {
            let invalid = text.replacen('{', &format!("{{{fragment}"), 1).into_bytes();
            assert!(diagnose(&source, &source, &invalid, &digest(&invalid)).is_err());
        }
        Ok(())
    }

    #[test]
    fn diagnostics_bounded_reader_rejects_empty_oversized_and_directory()
    -> Result<(), Box<dyn Error>> {
        let root = tempfile::tempdir()?;
        let path = root.path().join("bounded.bin");
        fs::File::create(&path)?.write_all(b"12345")?;
        assert!(read_bounded(&path, 4).is_err());
        assert_eq!(read_bounded(&path, 5)?, b"12345");
        assert!(read_bounded(root.path(), 5).is_err());
        let empty = root.path().join("empty.bin");
        fs::File::create(&empty)?;
        assert!(read_bounded(&empty, 5).is_err());
        Ok(())
    }
}
