use domain_ir::{DocumentId, ReferenceAuxiliaryLimitConfig, ReferenceAuxiliaryLimits};
use hwpx_agent_cli::reference_validation_product::{
    ReferenceValidationProductOperation,
    source::{REFERENCE_SOURCE_MAX_ARCHIVE_BYTES, ReferenceSourceError, ReferenceSourceStatus},
};
use hwpx_package::document_import::{SourceImportLimitConfig, SourceImportLimits};
use serde_json::Value;
use sha2::{Digest as _, Sha256};
use std::{
    error::Error,
    ffi::OsStr,
    fs::{self, File},
    process::{Command, Output},
};

#[path = "../../hwpx-package/tests/support/document_import_field_fixture.rs"]
#[allow(dead_code)] // Reuse the unchanged original package fixture, not a second writer.
mod fixture;
use fixture as base;
#[path = "../../hwpx-package/tests/support/document_import_bookmark_fixture.rs"]
#[allow(dead_code)]
mod bookmark_fixture;
type TestResult = Result<(), Box<dyn Error>>;
mod joined_caption_state {include!("reference_source_product/caption_state.rs");}
mod source_note_selection {include!("reference_source_product/note_selection.rs");}
mod source_note_style_selection {include!("reference_source_product/note_style_selection.rs");}
mod source_heading_targets {include!("reference_source_product/heading_targets.rs");}
mod source_field_meanings617 {include!("reference_source_product/field_meanings617.rs");}

fn limits() -> Result<ReferenceAuxiliaryLimits, Box<dyn Error>> {
    Ok(ReferenceAuxiliaryLimits::new(Default::default())?)
}
fn package(body: &str) -> Result<Vec<u8>, Box<dyn Error>> {
    fixture::package(&format!("<hp:p id='1'><hp:run>{body}</hp:run></hp:p>"))
}
fn marker(name: &str) -> String {
    format!("<hp:ctrl><hp:bookmark name='{name}'/></hp:ctrl>")
}
fn assess(
    bytes: &[u8],
) -> Result<
    hwpx_agent_cli::reference_validation_product::source::ReferenceSourceAssessment,
    Box<dyn Error>,
> {
    Ok(ReferenceValidationProductOperation::assess_package_source(
        bytes,
        DocumentId::parse("reference-product")?,
        Sha256::digest(bytes).into(),
        SourceImportLimits::default(),
        limits()?,
    )?)
}
fn cli(args: impl IntoIterator<Item = impl AsRef<OsStr>>) -> Result<Output, Box<dyn Error>> {
    let mut command = Command::new(env!("CARGO_BIN_EXE_hwpx-agent-cli"));
    command.args(args);
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt as _;
        command.creation_flags(0x0800_0000); // No visible console; inherited owned Job remains.
    }
    Ok(command.output()?)
}

#[test]
fn actual_package_targets_are_returned_but_not_a_zero_reference_pass() -> TestResult {
    let bytes = package(&format!(
        "{}<hp:t>private body</hp:t>",
        marker("private name")
    ))?;
    let report = assess(&bytes)?;
    assert_eq!(report.status(), ReferenceSourceStatus::Incomplete);
    assert_eq!(report.targets().len(), 1);
    assert!(report.validation_report().is_none());
    assert!(!report.target_receipt().complete_reference_state_qualified);
    let output = report.canonical_json(limits()?)?;
    let value: Value = serde_json::from_slice(&output)?;
    assert_eq!(value["status"], "incomplete");
    assert!(value["validation_report"].is_null());
    assert_eq!(value["unresolved"].as_array().ok_or("unresolved")?.len(), 4);
    for secret in ["private name", "private body"] {
        assert!(!String::from_utf8_lossy(&output).contains(secret));
        assert!(!format!("{report:?}").contains(secret));
    }
    Ok(())
}

#[test]
fn actual_cli_returns_bookmark_and_note_targets_without_private_body_or_complete_pass() -> TestResult
{
    let bytes = package(&format!(
        "{}<hp:ctrl><hp:endNote instId='101'><hp:subList><hp:p id='9'><hp:run><hp:t>private CLI note body</hp:t></hp:run></hp:p></hp:subList></hp:endNote></hp:ctrl>",
        marker("private CLI bookmark")
    ))?;
    let temp = tempfile::tempdir()?;
    let path = temp.path().join("original-note.hwpx");
    fs::write(&path, &bytes)?;
    let sha = hex::encode(Sha256::digest(&bytes));
    let output = cli([
        OsStr::new("reference-source"),
        OsStr::new("reference-product"),
        OsStr::new(&sha),
        path.as_os_str(),
    ])?;
    assert_eq!(output.status.code(), Some(3));
    assert!(output.stderr.is_empty());
    let value: Value = serde_json::from_slice(&output.stdout)?;
    assert_eq!(value["status"], "incomplete");
    assert!(value["validation_report"].is_null());
    assert_eq!(
        value["target_import"]["profile"],
        "hwpx-agent.document-import-reference-targets/bookmarks-notes-tables-v3"
    );
    assert_eq!(value["target_import"]["bookmark_targets"], 1);
    assert_eq!(value["target_import"]["note_targets"], 1);
    assert_eq!(value["targets"].as_array().ok_or("targets")?.len(), 2);
    assert_eq!(value["targets"][1]["target_kind"], "note");
    assert!(value["targets"][1]["anchor"].is_null());
    assert!(!String::from_utf8_lossy(&output.stdout).contains("private CLI"));
    assert_eq!(fs::read(path)?, bytes);
    Ok(())
}

#[test]
fn actual_cli_includes_source_table_target_and_stays_incomplete() -> TestResult {
    let bytes = package(&bookmark_fixture::table("<hp:t>private table body</hp:t>"))?;
    let temp = tempfile::tempdir()?;
    let path = temp.path().join("source-table.hwpx");
    fs::write(&path, &bytes)?;
    let sha = hex::encode(Sha256::digest(&bytes));
    let output = cli([
        OsStr::new("reference-source"),
        OsStr::new("reference-product"),
        OsStr::new(&sha),
        path.as_os_str(),
    ])?;
    assert_eq!(output.status.code(), Some(3));
    assert!(output.stderr.is_empty());
    let value: Value = serde_json::from_slice(&output.stdout)?;
    assert_eq!(value["status"], "incomplete");
    assert!(value["validation_report"].is_null());
    assert_eq!(value["target_import"]["table_targets"], 1);
    assert_eq!(value["targets"].as_array().ok_or("targets")?.len(), 1);
    assert_eq!(value["targets"][0]["target_kind"], "table");
    assert!(value["targets"][0]["anchor"].is_null());
    assert!(!String::from_utf8_lossy(&output.stdout).contains("private table body"));
    assert_eq!(fs::read(path)?, bytes);
    Ok(())
}

#[test]
fn unknown_crossref_parameters_are_neither_guessed_nor_reported_as_valid() -> TestResult {
    let body = format!(
        "{}<hp:ctrl><hp:fieldBegin id='7' type='CROSSREF'><hp:parameters cnt='1'><hp:stringParam name='unverified'>private target</hp:stringParam></hp:parameters></hp:fieldBegin></hp:ctrl><hp:t>cache</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='7'/></hp:ctrl>",
        marker("point")
    );
    let report = assess(&package(&body)?)?;
    assert_eq!(report.target_receipt().observed_native_fields, 1);
    assert!(report.validation_report().is_none());
    let text = String::from_utf8(report.canonical_json(limits()?)?)?;
    assert!(!text.contains("private target"));
    Ok(())
}

#[test]
fn duplicate_bookmark_names_are_retained_without_first_match_resolution() -> TestResult {
    let report = assess(&package(&format!("{}{}", marker("same"), marker("same")))?)?;
    assert_eq!(report.targets().len(), 2);
    assert_ne!(
        report.targets()[0].logical_target_id,
        report.targets()[1].logical_target_id
    );
    assert_eq!(report.target_receipt().ambiguous_source_names, 1);
    assert!(report.validation_report().is_none());
    Ok(())
}

#[test]
fn source_digest_and_document_identity_are_not_caller_typed_defaults() -> TestResult {
    let bytes = package(&marker("point"))?;
    assert_eq!(
        ReferenceValidationProductOperation::assess_package_source(
            &bytes,
            DocumentId::parse("reference-product")?,
            [0; 32],
            SourceImportLimits::default(),
            limits()?
        ),
        Err(ReferenceSourceError::Binding)
    );
    let first = assess(&bytes)?;
    let second = ReferenceValidationProductOperation::assess_package_source(
        &bytes,
        DocumentId::parse("other-document")?,
        Sha256::digest(&bytes).into(),
        SourceImportLimits::default(),
        limits()?,
    )?;
    assert_ne!(
        first.targets()[0].logical_target_id,
        second.targets()[0].logical_target_id
    );
    Ok(())
}

#[test]
fn source_reference_and_response_limits_fail_without_truncation() -> TestResult {
    let bytes = package(&format!("{}{}", marker("one"), marker("two")))?;
    let source_limits = SourceImportLimits::new(SourceImportLimitConfig {
        archive_bytes: 1,
        ..Default::default()
    })?;
    assert_eq!(
        ReferenceValidationProductOperation::assess_package_source(
            &bytes,
            DocumentId::parse("reference-product")?,
            Sha256::digest(&bytes).into(),
            source_limits,
            limits()?
        ),
        Err(ReferenceSourceError::InputLimit)
    );
    let reference_limits = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {
        items_per_kind: 1,
        ..Default::default()
    })?;
    assert_eq!(
        ReferenceValidationProductOperation::assess_package_source(
            &bytes,
            DocumentId::parse("reference-product")?,
            Sha256::digest(&bytes).into(),
            SourceImportLimits::default(),
            reference_limits
        ),
        Err(ReferenceSourceError::InputLimit)
    );
    let small = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {
        input_bytes: 1,
        output_bytes: 1,
        ..Default::default()
    })?;
    assert_eq!(
        assess(&bytes)?.canonical_json(small),
        Err(ReferenceSourceError::Output)
    );
    Ok(())
}

#[test]
fn actual_cli_returns_incomplete_exit_three_and_preserves_input_bytes() -> TestResult {
    let bytes = package(&marker("private CLI name"))?;
    let temp = tempfile::tempdir()?;
    let path = temp.path().join("original.hwpx");
    fs::write(&path, &bytes)?;
    let sha = hex::encode(Sha256::digest(&bytes));
    let output = cli([
        OsStr::new("reference-source"),
        OsStr::new("reference-product"),
        OsStr::new(&sha),
        path.as_os_str(),
    ])?;
    assert_eq!(output.status.code(), Some(3));
    assert!(output.stderr.is_empty());
    let value: Value = serde_json::from_slice(&output.stdout)?;
    assert_eq!(value["status"], "incomplete");
    assert!(value["validation_report"].is_null());
    assert!(!String::from_utf8_lossy(&output.stdout).contains("private CLI name"));
    assert_eq!(fs::read(path)?, bytes);
    Ok(())
}

#[test]
fn actual_cli_invalid_arguments_and_source_drift_are_not_success_json() -> TestResult {
    let missing = cli(["reference-source"])?;
    assert_eq!(missing.status.code(), Some(2));
    assert!(missing.stdout.is_empty());
    assert_eq!(
        String::from_utf8(missing.stderr)?.trim(),
        "REFERENCE_SOURCE_REQUEST_REJECTED"
    );
    let bytes = package(&marker("point"))?;
    let temp = tempfile::tempdir()?;
    let path = temp.path().join("original.hwpx");
    fs::write(&path, &bytes)?;
    let digest = "0".repeat(64);
    let output = cli([
        OsStr::new("reference-source"),
        OsStr::new("reference-product"),
        OsStr::new(&digest),
        path.as_os_str(),
    ])?;
    assert_eq!(output.status.code(), Some(2));
    assert!(output.stdout.is_empty());
    assert_eq!(
        String::from_utf8(output.stderr)?.trim(),
        "REFERENCE_SOURCE_BINDING_REJECTED"
    );
    Ok(())
}

#[test]
fn actual_cli_rejects_nonfiles_and_oversized_local_source_before_import() -> TestResult {
    let temp = tempfile::tempdir()?;
    let digest = "0".repeat(64);
    let output = cli([
        OsStr::new("reference-source"),
        OsStr::new("reference-product"),
        OsStr::new(&digest),
        temp.path().as_os_str(),
    ])?;
    assert_eq!(output.status.code(), Some(2));
    assert_eq!(
        String::from_utf8(output.stderr)?.trim(),
        "REFERENCE_SOURCE_FILE_REJECTED"
    );
    let path = temp.path().join("oversized.hwpx");
    File::create(&path)?.set_len(REFERENCE_SOURCE_MAX_ARCHIVE_BYTES + 1)?;
    let output = cli([
        OsStr::new("reference-source"),
        OsStr::new("reference-product"),
        OsStr::new(&digest),
        path.as_os_str(),
    ])?;
    assert_eq!(output.status.code(), Some(2));
    assert!(output.stdout.is_empty());
    assert_eq!(
        String::from_utf8(output.stderr)?.trim(),
        "REFERENCE_SOURCE_INPUT_LIMIT"
    );
    Ok(())
}

#[test]
fn legacy_and_unknown_command_error_routing_is_unchanged() -> TestResult {
    for args in [vec!["create-vs0"], vec!["unknown-command"], vec![]] {
        let output = cli(args)?;
        assert_eq!(output.status.code(), Some(2));
        assert!(output.stdout.is_empty());
        assert_eq!(
            String::from_utf8(output.stderr)?.trim(),
            "vs0_invalid_request"
        );
    }
    Ok(())
}

#[test]
fn actual_cli_rejects_extra_arguments_invalid_hash_and_nonlocal_paths() -> TestResult {
    let hash = "0".repeat(64);
    let invalid = cli(["reference-source", "reference-product", "not-hex", "unused"])?;
    assert_eq!(invalid.status.code(), Some(2));
    assert_eq!(
        String::from_utf8(invalid.stderr)?.trim(),
        "REFERENCE_SOURCE_REQUEST_REJECTED"
    );
    let extra = cli([
        "reference-source",
        "reference-product",
        &hash,
        "unused",
        "--repair",
    ])?;
    assert_eq!(extra.status.code(), Some(2));
    assert_eq!(
        String::from_utf8(extra.stderr)?.trim(),
        "REFERENCE_SOURCE_REQUEST_REJECTED"
    );
    for path in [
        "relative.hwpx",
        r"\\example.invalid\share\source.hwpx",
        r"\\.\pipe\hwpx-not-existing",
    ] {
        let output = cli(["reference-source", "reference-product", &hash, path])?;
        assert_eq!(output.status.code(), Some(2));
        assert!(output.stdout.is_empty());
        assert_eq!(
            String::from_utf8(output.stderr)?.trim(),
            "REFERENCE_SOURCE_FILE_REJECTED"
        );
    }
    Ok(())
}

#[cfg(windows)]
#[test]
fn actual_cli_rejects_a_junction_ancestor_before_reading_the_source_leaf() -> TestResult {
    use std::os::windows::process::CommandExt as _;
    let temp = tempfile::tempdir()?;
    let real = temp.path().join("real");
    let junction = temp.path().join("junction");
    assert!(real.starts_with(temp.path()) && junction.starts_with(temp.path()));
    fs::create_dir(&real)?;
    let bytes = package(&marker("junction fixture"))?;
    fs::write(real.join("source.hwpx"), &bytes)?;
    let shell =
        std::path::PathBuf::from(std::env::var_os("SystemRoot").ok_or("missing Windows root")?)
            .join("System32/WindowsPowerShell/v1.0/powershell.exe");
    let made = Command::new(shell)
        .args(["-NoProfile", "-NonInteractive", "-Command",
            "$ErrorActionPreference='Stop'; New-Item -ItemType Junction -Path $env:HWPX_REF_TEST_LINK -Target $env:HWPX_REF_TEST_TARGET | Out-Null"])
        .env("HWPX_REF_TEST_LINK", &junction)
        .env("HWPX_REF_TEST_TARGET", &real)
        .creation_flags(0x0800_0000)
        .output()?;
    if !made.status.success() {
        return Err("synthetic junction creation failed".into());
    }
    let linked = junction.join("source.hwpx");
    let sha = hex::encode(Sha256::digest(&bytes));
    let output = cli([
        OsStr::new("reference-source"),
        OsStr::new("reference-product"),
        OsStr::new(&sha),
        linked.as_os_str(),
    ])?;
    // Non-recursive removal targets only our generated junction, not its data.
    fs::remove_dir(&junction)?;
    assert_eq!(fs::read(real.join("source.hwpx"))?, bytes);
    assert_eq!(output.status.code(), Some(2));
    assert!(output.stdout.is_empty());
    assert_eq!(
        String::from_utf8(output.stderr)?.trim(),
        "REFERENCE_SOURCE_FILE_REJECTED"
    );
    Ok(())
}

#[test]
fn source_field_inventory_is_the_original_import_not_an_inferred_reference_state() -> TestResult {
    use hwpx_package::document_import::fields::ImportedDocumentFields;
    let bytes = package(&format!("{}{}", marker("private field target"), bookmark_fixture::field()))?;
    let forms = fixture::forms(&bytes, "reference-product")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let report = assess(&bytes)?;
    assert_eq!(report.form_receipt(), forms.receipt());
    assert_eq!(report.field_range_receipt(), fields.receipt());
    assert_eq!(report.field_range_receipt().field_ranges, 1);
    assert_eq!(report.target_receipt().observed_native_fields, 1);
    assert_eq!(report.form_receipt().body_graph_sha256, report.target_receipt().structure_graph_sha256);
    assert_eq!(report.form_receipt().graph_sha256, report.field_range_receipt().original_form_graph_sha256);
    let value: Value = serde_json::from_slice(&report.canonical_json(limits()?)?)?;
    assert_eq!(value["schema_version"], "hwpx-agent.product.reference-source-assessment/v15");
    assert_eq!(value["status"], "incomplete");
    assert!(value["validation_report"].is_null());
    assert_eq!(value["unresolved"].as_array().ok_or("unresolved")?.len(), 4);
    assert!(!value.to_string().contains("private field target"));
    Ok(())
}

#[test]
fn source_field_inventory_keeps_nested_and_repeated_paragraph_local_ids() -> TestResult {
    let nested = "<hp:ctrl><hp:fieldBegin id='7' type='DATE'/></hp:ctrl><hp:ctrl><hp:fieldBegin id='8' type='DATE'/></hp:ctrl><hp:t>private cache</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='8'/></hp:ctrl><hp:ctrl><hp:fieldEnd beginIDRef='7'/></hp:ctrl>";
    let bytes = fixture::package(&format!("{}{}", bookmark_fixture::paragraph(nested),
        bookmark_fixture::paragraph(bookmark_fixture::field())))?;
    let report = assess(&bytes)?;
    assert_eq!(report.field_range_receipt().field_ranges, 3);
    assert_eq!(report.field_range_receipt().nested_ranges, 1);
    assert_eq!(report.target_receipt().observed_native_fields, 3);
    assert!(report.validation_report().is_none());
    assert!(!String::from_utf8(report.canonical_json(limits()?)?)?.contains("private cache"));
    Ok(())
}

fn with_header_field_markers(bytes: &[u8], markers: &str) -> Result<Vec<u8>, Box<dyn Error>> {
    use std::io::{Cursor, Read as _, Write as _};
    use zip::{CompressionMethod, ZipArchive, ZipWriter, write::SimpleFileOptions};
    let mut source = ZipArchive::new(Cursor::new(bytes))?;
    let mut target = ZipWriter::new(Cursor::new(Vec::new()));
    for index in 0..source.len() {
        let mut entry = source.by_index(index)?;
        let name = entry.name().to_owned();
        let mut data = Vec::new();
        entry.read_to_end(&mut data)?;
        if name == "Contents/header.xml" {
            data = format!("<header xmlns:hp='http://www.hancom.co.kr/hwpml/2011/paragraph'>{markers}</header>").into_bytes();
        }
        target.start_file(name, SimpleFileOptions::default().compression_method(CompressionMethod::Stored))?;
        target.write_all(&data)?;
    }
    Ok(target.finish()?.into_inner())
}

#[test]
fn source_field_inventory_rejects_begin_end_and_balanced_pairs_outside_the_body() -> TestResult {
    let bytes = package(bookmark_fixture::field())?;
    for markers in [
        "<hp:fieldBegin id='901' type='DATE'/>",
        "<hp:fieldEnd beginIDRef='901'/>",
        "<hp:fieldBegin id='901' type='DATE'/><hp:fieldEnd beginIDRef='901'/>",
    ] {
        let hidden = with_header_field_markers(&bytes, markers)?;
        assert_eq!(ReferenceValidationProductOperation::assess_package_source(&hidden,
            DocumentId::parse("reference-product")?, Sha256::digest(&hidden).into(),
            SourceImportLimits::default(), limits()?), Err(ReferenceSourceError::Coverage));
    }
    Ok(())
}

#[test]
fn actual_cli_does_not_publish_an_inventory_for_a_broken_field_pair() -> TestResult {
    let bytes = package(&bookmark_fixture::field().replace("beginIDRef='7'", "beginIDRef='8'"))?;
    let temp = tempfile::tempdir()?;
    let path = temp.path().join("broken-pair.hwpx");
    fs::write(&path, &bytes)?;
    let sha = hex::encode(Sha256::digest(&bytes));
    let output = cli([OsStr::new("reference-source"), OsStr::new("reference-product"),
        OsStr::new(&sha), path.as_os_str()])?;
    assert_eq!(output.status.code(), Some(2));
    assert!(output.stdout.is_empty());
    assert_eq!(String::from_utf8(output.stderr)?.trim(), "REFERENCE_SOURCE_STRUCTURE_REJECTED");
    assert_eq!(fs::read(path)?, bytes);
    Ok(())
}

#[test]
fn source_field_inventory_binds_note_and_table_ranges_and_field_budget() -> TestResult {
    let bytes = package(&format!("{}{}", bookmark_fixture::note(bookmark_fixture::field()),
        bookmark_fixture::table(bookmark_fixture::field())))?;
    let report = assess(&bytes)?;
    assert_eq!(report.field_range_receipt().field_ranges, 2);
    assert_eq!(report.target_receipt().observed_native_fields, 2);
    assert_eq!(report.target_receipt().note_targets, 1);
    assert_eq!(report.target_receipt().table_targets, 1);
    let small = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {
        items_per_kind: 1, ..Default::default()
    })?;
    assert_eq!(ReferenceValidationProductOperation::assess_package_source(&bytes,
        DocumentId::parse("reference-product")?, Sha256::digest(&bytes).into(),
        SourceImportLimits::default(), small), Err(ReferenceSourceError::InputLimit));
    Ok(())
}

#[test]
fn actual_cli_exposes_historical_field_inventory_but_no_resolved_target_or_complete_pass() -> TestResult {
    let bytes = fixture::captured()?;
    let temp = tempfile::tempdir()?;
    let path = temp.path().join("historical-copy.hwpx");
    fs::write(&path, &bytes)?;
    let sha = hex::encode(Sha256::digest(&bytes));
    let output = cli([OsStr::new("reference-source"), OsStr::new("reference-product"),
        OsStr::new(&sha), path.as_os_str()])?;
    assert_eq!(output.status.code(), Some(3));
    assert!(output.stderr.is_empty());
    let value: Value = serde_json::from_slice(&output.stdout)?;
    assert_eq!(value["field_range_import"]["field_ranges"], 1);
    assert_eq!(value["form_import"]["graph_sha256"], value["field_range_import"]["original_form_graph_sha256"]);
    assert_eq!(value["source"]["source_package_sha256"], value["field_range_import"]["source_package_sha256"]);
    assert_eq!(value["status"], "incomplete");
    assert!(value["validation_report"].is_null());
    assert_eq!(fs::read(path)?, bytes);
    assert_eq!(fixture::captured()?, bytes);
    Ok(())
}

#[test]
fn actual_cli_v4_includes_original_section_topology_without_page_or_unlock_defaults() -> TestResult {
    let bytes = bookmark_fixture::two_sections()?;
    let forms = fixture::forms(&bytes, "reference-product")?;
    let report = assess(&bytes)?;
    assert_eq!(report.section_flows(), forms.body_structure().section_flows());
    let temp = tempfile::tempdir()?;
    let path = temp.path().join("sections.hwpx");
    fs::write(&path, &bytes)?;
    let sha = hex::encode(Sha256::digest(&bytes));
    let output = cli([OsStr::new("reference-source"), OsStr::new("reference-product"),
        OsStr::new(&sha), path.as_os_str()])?;
    assert_eq!(output.status.code(), Some(3));
    assert!(output.stderr.is_empty());
    let value: Value = serde_json::from_slice(&output.stdout)?;
    assert_eq!(value["schema_version"], "hwpx-agent.product.reference-source-assessment/v15");
    let flows = value["section_flows"].as_array().ok_or("flows")?;
    assert_eq!(flows.len(), 2);
    for flow in flows {
        assert_eq!(flow["paragraphs"], 1);
        assert_eq!(flow["runs"], 1);
        assert_eq!(flow["inline_elements"], 0);
        assert!(flow["page_assignment_sha256"].is_null());
        assert!(flow["locked"].is_null());
        assert_eq!(flow["complete_document_flow_qualified"], false);
    }
    assert!(value["validation_report"].is_null());
    assert_eq!(value["unresolved"].as_array().ok_or("unresolved")?.len(), 4);
    assert!(!String::from_utf8(output.stdout)?.contains("same-across-sections"));
    assert_eq!(fs::read(path)?, bytes);
    Ok(())
}

#[test]
fn source_section_count_and_exact_response_size_budgets_fail_without_truncation() -> TestResult {
    let bytes = bookmark_fixture::two_sections()?;
    let one_section = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {
        sections: 1, ..Default::default()
    })?;
    assert_eq!(ReferenceValidationProductOperation::assess_package_source(&bytes,
        DocumentId::parse("reference-product")?, Sha256::digest(&bytes).into(),
        SourceImportLimits::default(), one_section), Err(ReferenceSourceError::InputLimit));
    let report = assess(&bytes)?;
    let original = report.canonical_json(limits()?)?;
    let exact = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {
        input_bytes: 1, output_bytes: original.len(), ..Default::default()
    })?;
    assert_eq!(report.canonical_json(exact)?, original);
    let small = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {
        input_bytes: 1, output_bytes: original.len() - 1, ..Default::default()
    })?;
    assert_eq!(report.canonical_json(small), Err(ReferenceSourceError::Output));
    Ok(())
}

#[test]
fn historical_source_topology_is_original_body_data_not_complete_flow() -> TestResult {
    let bytes = fixture::captured()?;
    let forms = fixture::forms(&bytes, "reference-product")?;
    let report = assess(&bytes)?;
    assert_eq!(report.section_flows(), forms.body_structure().section_flows());
    assert!(!report.section_flows().is_empty());
    for flow in report.section_flows() {
        assert!(flow.paragraphs() > 0 && flow.runs() > 0);
        let value = serde_json::to_value(flow)?;
        assert!(value["locked"].is_null());
        assert!(value["page_assignment_sha256"].is_null());
        assert_eq!(value["complete_document_flow_qualified"], false);
    }
    assert_eq!(report.status(), ReferenceSourceStatus::Incomplete);
    assert!(report.validation_report().is_none());
    assert_eq!(fixture::captured()?, bytes);
    Ok(())
}

#[test]
fn actual_cli_v4_reports_passive_script_inventory_without_raw_commands_or_native_permission() -> TestResult {
    let bytes = package("<hp:script>PRIVATE-NEVER-EXECUTED</hp:script>")?;
    let report = assess(&bytes)?;
    assert_eq!(report.active_security().counts().controls, 1);
    let temp = tempfile::tempdir()?;
    let path = temp.path().join("passive-script.hwpx");
    fs::write(&path, &bytes)?;
    let sha = hex::encode(Sha256::digest(&bytes));
    let output = cli([OsStr::new("reference-source"), OsStr::new("reference-product"),
        OsStr::new(&sha), path.as_os_str()])?;
    assert_eq!(output.status.code(), Some(3));
    assert!(output.stderr.is_empty());
    let value: Value = serde_json::from_slice(&output.stdout)?;
    assert_eq!(value["schema_version"], "hwpx-agent.product.reference-source-assessment/v15");
    assert_eq!(value["active_security"]["counts"]["controls"], 1);
    assert_eq!(value["active_security"]["counts"]["quarantined"], 1);
    assert_eq!(value["active_security"]["activation_allowed"], false);
    assert_eq!(value["active_security"]["native_security"], "not_assessed_by_active_content_inventory");
    assert_eq!(value["active_security"]["source_package_sha256"], value["source"]["source_package_sha256"]);
    assert_eq!(value["active_security"]["external_data_access_qualified"], false);
    assert!(value["validation_report"].is_null());
    assert_eq!(value["unresolved"].as_array().ok_or("unresolved")?.len(), 4);
    assert!(!String::from_utf8(output.stdout)?.contains("PRIVATE-NEVER-EXECUTED"));
    assert_eq!(fs::read(path)?, bytes);
    Ok(())
}

#[test]
fn actual_cli_rejects_spoofed_active_content_without_a_partial_success_record() -> TestResult {
    let bytes = package("<x:script xmlns:x='urn:foreign'>PRIVATE-NO-EXECUTION</x:script>")?;
    let temp = tempfile::tempdir()?;
    let path = temp.path().join("spoofed-script.hwpx");
    fs::write(&path, &bytes)?;
    let sha = hex::encode(Sha256::digest(&bytes));
    let output = cli([OsStr::new("reference-source"), OsStr::new("reference-product"),
        OsStr::new(&sha), path.as_os_str()])?;
    assert_eq!(output.status.code(), Some(2));
    assert!(output.stdout.is_empty());
    assert_eq!(String::from_utf8(output.stderr)?.trim(), "REFERENCE_SOURCE_ACTIVE_SECURITY_REJECTED");
    assert_eq!(fs::read(path)?, bytes);
    Ok(())
}

#[test]
fn reference_item_budget_also_limits_original_passive_inventory() -> TestResult {
    let bytes = package("<hp:script>one</hp:script><hp:script>two</hp:script>")?;
    let one = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {
        items_per_kind: 1, ..Default::default()
    })?;
    assert_eq!(ReferenceValidationProductOperation::assess_package_source(&bytes,
        DocumentId::parse("reference-product")?, Sha256::digest(&bytes).into(),
        SourceImportLimits::default(), one), Err(ReferenceSourceError::InputLimit));
    let report = assess(&bytes)?;
    assert_eq!(report.active_security().counts().controls, 2);
    assert!(report.validation_report().is_none());
    Ok(())
}

#[test]
fn source_object_targets_product_merges_native_families_but_keeps_legacy_receipt_exact() -> TestResult {
    use hwpx_package::document_import::reference_targets::{ImportedReferenceObjectTargets, ImportedReferenceTargets};
    let bytes = package(&format!("{}<hp:pic id='7'/><hp:equation id='7'/>{}", marker("private target"),
        bookmark_fixture::table("<hp:rect id='7'><hp:t>private geometry text</hp:t></hp:rect>")))?;
    let forms = fixture::forms(&bytes, "reference-product")?;
    let original = ImportedReferenceTargets::import(forms.body_structure(), limits()?)?;
    let objects = ImportedReferenceObjectTargets::import(forms.body_structure(), limits()?)?;
    let report = assess(&bytes)?;
    assert_eq!(report.target_receipt(), original.receipt());
    assert_eq!(report.object_target_receipt(), objects.receipt());
    let expected: Vec<_> = original.targets().iter().chain(objects.targets()).cloned().collect();
    assert_eq!(report.targets(), expected);
    assert_eq!(report.targets().len(), 5);
    assert_eq!((report.object_target_receipt().object_targets, report.object_target_receipt().equation_targets), (2, 1));
    assert_eq!(report.status(), ReferenceSourceStatus::Incomplete);
    assert!(report.validation_report().is_none());
    let json = String::from_utf8(report.canonical_json(limits()?)?)?;
    assert!(!json.contains("private"));
    assert!(!format!("{report:?}").contains("private"));
    Ok(())
}

#[test]
fn source_object_targets_actual_cli_v5_emits_both_receipts_and_no_native_success() -> TestResult {
    let bytes = package("<hp:pic id='3'/><hp:equation id='3'><hp:t>private equation</hp:t></hp:equation><u:rect/>")?;
    let temp = tempfile::tempdir()?;
    let path = temp.path().join("source-objects.hwpx");
    fs::write(&path, &bytes)?;
    let sha = hex::encode(Sha256::digest(&bytes));
    let output = cli([OsStr::new("reference-source"), OsStr::new("reference-product"), OsStr::new(&sha), path.as_os_str()])?;
    assert_eq!(output.status.code(), Some(3));
    assert!(output.stderr.is_empty());
    let value: Value = serde_json::from_slice(&output.stdout)?;
    assert_eq!(value["schema_version"], "hwpx-agent.product.reference-source-assessment/v15");
    assert_eq!(value["target_import"]["profile"], "hwpx-agent.document-import-reference-targets/bookmarks-notes-tables-v3");
    assert_eq!(value["object_target_import"]["object_targets"], 1);
    assert_eq!(value["object_target_import"]["equation_targets"], 1);
    assert_eq!(value["object_target_import"]["native_geometry_or_equation_semantics_qualified"], false);
    assert_eq!(value["object_target_import"]["complete_reference_state_qualified"], false);
    assert!(value["validation_report"].is_null());
    assert_eq!(value["unresolved"].as_array().ok_or("unresolved")?.len(), 4);
    assert!(!String::from_utf8_lossy(&output.stdout).contains("private equation"));
    assert_eq!(fs::read(path)?, bytes);
    Ok(())
}

#[test]
fn source_object_targets_product_coverage_failures_publish_no_partial_inventory() -> TestResult {
    let bytes = package("<hp:rect/>")?;
    for hidden in [with_header_field_markers(&bytes, "<hp:equation/>")?, package("<u:future><hp:pic/></u:future>")?] {
        assert_eq!(ReferenceValidationProductOperation::assess_package_source(&hidden,
            DocumentId::parse("reference-product")?, Sha256::digest(&hidden).into(),
            SourceImportLimits::default(), limits()?), Err(ReferenceSourceError::Coverage));
        let temp = tempfile::tempdir()?;
        let path = temp.path().join("uncovered-objects.hwpx");
        fs::write(&path, &hidden)?;
        let sha = hex::encode(Sha256::digest(&hidden));
        let output = cli([OsStr::new("reference-source"), OsStr::new("reference-product"), OsStr::new(&sha), path.as_os_str()])?;
        assert_eq!(output.status.code(), Some(2));
        assert!(output.stdout.is_empty());
        assert_eq!(String::from_utf8(output.stderr)?.trim(), "REFERENCE_SOURCE_TARGET_COVERAGE_REJECTED");
        assert_eq!(fs::read(path)?, hidden);
    }
    Ok(())
}

#[test]
fn source_object_targets_product_respects_family_and_final_response_limits() -> TestResult {
    let bytes = package("<hp:rect/><hp:pic/>")?;
    let one = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig { items_per_kind: 1, ..Default::default() })?;
    assert_eq!(ReferenceValidationProductOperation::assess_package_source(&bytes,
        DocumentId::parse("reference-product")?, Sha256::digest(&bytes).into(), SourceImportLimits::default(), one),
        Err(ReferenceSourceError::InputLimit));
    let report = assess(&bytes)?;
    let length = report.canonical_json(limits()?)?.len();
    let exact = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig { input_bytes: length, output_bytes: length, ..Default::default() })?;
    assert_eq!(report.canonical_json(exact)?.len(), length);
    let short = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig { input_bytes: length - 1, output_bytes: length - 1, ..Default::default() })?;
    assert_eq!(report.canonical_json(short), Err(ReferenceSourceError::Output));
    Ok(())
}

fn source_caption(text:&str)->String {
    format!("<hp:caption side='TOP' fullSz='0' width='1200' gap='30' lastWidth='1100'><hp:subList><hp:p id='99'><hp:run><hp:t>{text}</hp:t></hp:run></hp:p></hp:subList></hp:caption>")
}
#[test]
fn caption_source_envelope_product_merges_original_envelopes_without_sequence_or_flow_defaults() -> TestResult {
    use hwpx_package::document_import::reference_targets::captions::ImportedReferenceCaptions;
    let bytes=package(&format!("{}<hp:rect id='7'>{}</hp:rect>",marker("private bookmark"),source_caption("private caption label")))?;
    let forms=fixture::forms(&bytes,"reference-product")?;
    let original=ImportedReferenceCaptions::import(forms.body_structure(),limits()?)?;
    let report=assess(&bytes)?;
    assert_eq!(report.caption_receipt(),original.receipt()); assert_eq!(report.caption_envelopes(),original.envelopes());
    assert_eq!(report.targets().len(),3); // Original bookmark, object and distinct caption.
    assert_eq!(report.targets()[2],original.targets()[0]);
    assert_eq!(report.caption_envelopes()[0].native_envelope().width_hwpunit,1200);
    assert!(!report.caption_receipt().sub_list_numbering_qualified);
    assert!(!report.caption_receipt().complete_auxiliary_state_qualified);
    assert_eq!(report.status(),ReferenceSourceStatus::Incomplete); assert!(report.validation_report().is_none());
    assert!(!String::from_utf8(report.canonical_json(limits()?)?)?.contains("private"));
    Ok(())
}
#[test]
fn caption_source_envelope_actual_cli_v6_returns_hash_only_source_envelopes_and_original_receipts() -> TestResult {
    let bytes=package(&format!("<hp:rect id='7'>{}</hp:rect><hp:equation id='7'>{}</hp:equation>",source_caption("private picture text"),source_caption("private equation text")))?;
    let temp=tempfile::tempdir()?; let path=temp.path().join("caption-source.hwpx"); fs::write(&path,&bytes)?;
    let sha=hex::encode(Sha256::digest(&bytes));
    let output=cli([OsStr::new("reference-source"),OsStr::new("reference-product"),OsStr::new(&sha),path.as_os_str()])?;
    assert_eq!(output.status.code(),Some(3)); assert!(output.stderr.is_empty());
    let value:Value=serde_json::from_slice(&output.stdout)?;
    assert_eq!(value["schema_version"],"hwpx-agent.product.reference-source-assessment/v15");
    assert_eq!(value["target_import"]["profile"],"hwpx-agent.document-import-reference-targets/bookmarks-notes-tables-v3");
    assert_eq!(value["object_target_import"]["object_targets"],1); assert_eq!(value["object_target_import"]["equation_targets"],1);
    assert_eq!(value["caption_import"]["caption_targets"],2);
    assert_eq!(value["caption_envelopes"][0]["native_envelope"]["semantic_binding"],"unverified_sub_list_numbering");
    assert_eq!(value["caption_import"]["sub_list_numbering_qualified"],false);
    assert_eq!(value["caption_import"]["complete_auxiliary_state_qualified"],false);
    assert_eq!(value["unresolved"].as_array().ok_or("unresolved")?.len(),4); assert!(value["validation_report"].is_null());
    assert!(!String::from_utf8_lossy(&output.stdout).contains("private")); assert_eq!(fs::read(path)?,bytes);
    Ok(())
}
#[test]
fn caption_source_envelope_actual_cli_rejects_malformed_or_unowned_source_without_partial_output() -> TestResult {
    for (body,expected) in [(format!("<hp:rect>{}</hp:rect>",source_caption("private").replace(" gap='30'","")),"REFERENCE_SOURCE_CAPTION_REJECTED"),
        (source_caption("unowned"),"REFERENCE_SOURCE_TARGET_COVERAGE_REJECTED")] {
        let bytes=package(&body)?; let temp=tempfile::tempdir()?; let path=temp.path().join("bad-caption.hwpx"); fs::write(&path,&bytes)?;
        let sha=hex::encode(Sha256::digest(&bytes));
        let output=cli([OsStr::new("reference-source"),OsStr::new("reference-product"),OsStr::new(&sha),path.as_os_str()])?;
        assert_eq!(output.status.code(),Some(2)); assert!(output.stdout.is_empty());
        assert_eq!(String::from_utf8(output.stderr)?.trim(),expected); assert_eq!(fs::read(path)?,bytes);
    }
    Ok(())
}

fn source_numbering_auto()->&'static str {"<hp:ctrl><hp:autoNum num='19' numType='PICTURE'><hp:autoNumFormat type='DIGIT' userChar='' prefixChar='private prefix' suffixChar='' supscript='0'/></hp:autoNum></hp:ctrl>"}
fn source_numbering_body()->String {
    let caption=source_caption("private caption label").replace("</hp:run>",&format!("{}</hp:run>",source_numbering_auto()));
    format!("<hp:secPr><hp:startNum pageStartsOn='BOTH' page='0' pic='5' tbl='0' equation='0'/></hp:secPr><hp:ctrl><hp:newNum num='4' numType='PICTURE'/></hp:ctrl><hp:rect id='7'>{caption}</hp:rect>")
}
#[test]
fn caption_numbering_source_product_keeps_original_caption_model_and_hash_only_number_controls() -> TestResult {
    use hwpx_package::document_import::reference_targets::numbering::ImportedCaptionNumbering;
    let bytes=package(&source_numbering_body())?;let forms=fixture::forms(&bytes,"reference-product")?;
    let original=ImportedCaptionNumbering::import(forms.body_structure(),limits()?)?;let report=assess(&bytes)?;
    assert_eq!(report.numbering_receipt(),original.receipt());assert_eq!(report.numbering_controls(),original.controls());assert_eq!(report.numbering_section_starts(),original.section_starts());
    assert_eq!(report.caption_receipt(),original.caption_import().receipt());assert_eq!(report.caption_envelopes(),original.caption_import().envelopes());
    assert_eq!(report.numbering_controls()[1].stored_number,19);assert_eq!(report.numbering_section_starts()[0].picture,5);
    assert!(!report.numbering_receipt().sequence_interpretation_qualified&&!report.numbering_receipt().native_recalculation_qualified);
    assert_eq!(report.status(),ReferenceSourceStatus::Incomplete);assert!(report.validation_report().is_none());
    assert!(!String::from_utf8(report.canonical_json(limits()?)?)?.contains("private"));Ok(())
}
#[test]
fn caption_numbering_source_actual_cli_v7_distinguishes_cache_and_restart_without_resolved_sequence() -> TestResult {
    let bytes=package(&source_numbering_body())?;let temp=tempfile::tempdir()?;let path=temp.path().join("numbering.hwpx");fs::write(&path,&bytes)?;
    let sha=hex::encode(Sha256::digest(&bytes));let output=cli([OsStr::new("reference-source"),OsStr::new("reference-product"),OsStr::new(&sha),path.as_os_str()])?;
    assert_eq!(output.status.code(),Some(3));assert!(output.stderr.is_empty());let value:Value=serde_json::from_slice(&output.stdout)?;
    assert_eq!(value["schema_version"],"hwpx-agent.product.reference-source-assessment/v15");assert_eq!(value["numbering_import"]["auto_numbers"],1);
    assert_eq!(value["numbering_controls"][0]["kind"],"restart");assert_eq!(value["numbering_controls"][0]["stored_number"],4);
    assert_eq!(value["numbering_controls"][1]["stored_number"],19);assert_eq!(value["numbering_controls"][1]["format"]["native_type"],"DIGIT");
    assert_eq!(value["numbering_controls"][1]["format"]["typed_format"],"decimal");assert_eq!(value["numbering_section_starts"][0]["picture"],5);
    assert_eq!(value["numbering_import"]["sequence_interpretation_qualified"],false);assert_eq!(value["numbering_import"]["native_recalculation_qualified"],false);
    assert_eq!(value["caption_import"]["sub_list_numbering_qualified"],false);assert_eq!(value["target_import"]["profile"],"hwpx-agent.document-import-reference-targets/bookmarks-notes-tables-v3");
    assert_eq!(value["unresolved"].as_array().ok_or("unresolved")?.len(),4);assert!(value["validation_report"].is_null());
    assert!(!String::from_utf8_lossy(&output.stdout).contains("private"));assert_eq!(fs::read(path)?,bytes);Ok(())
}
#[test]
fn caption_numbering_source_actual_cli_rejects_invalid_and_unrepresented_controls_without_partial_output() -> TestResult {
    for (body,expected) in [(source_numbering_body().replace("num='19'","num='2147483648'"),"REFERENCE_SOURCE_NUMBERING_REJECTED"),
        (source_numbering_body().replace("type='DIGIT'","type='DIGTI'"),"REFERENCE_SOURCE_NUMBERING_REJECTED"),
        (format!("<u:future><hp:p id='9'><hp:run>{}</hp:run></hp:p></u:future>",source_numbering_auto()),"REFERENCE_SOURCE_TARGET_COVERAGE_REJECTED")] {
        let bytes=package(&body)?;let temp=tempfile::tempdir()?;let path=temp.path().join("bad-numbering.hwpx");fs::write(&path,&bytes)?;
        let sha=hex::encode(Sha256::digest(&bytes));let output=cli([OsStr::new("reference-source"),OsStr::new("reference-product"),OsStr::new(&sha),path.as_os_str()])?;
        assert_eq!(output.status.code(),Some(2));assert!(output.stdout.is_empty());assert_eq!(String::from_utf8(output.stderr)?.trim(),expected);assert_eq!(fs::read(path)?,bytes);
    }Ok(())
}

fn source_caption_context_begin()->&'static str {"<hh:beginNum page='0' footnote='2' endnote='3' pic='4' tbl='5' equation='6'/>"}
fn source_caption_context_package(body:&str,begin:&str)->Result<Vec<u8>,Box<dyn Error>> {
    use std::io::{Cursor,Read,Write};
    let bytes=package(body)?;let mut input=zip::ZipArchive::new(Cursor::new(bytes))?;let mut output=zip::ZipWriter::new(Cursor::new(Vec::new()));
    for i in 0..input.len(){let mut entry=input.by_index(i)?;let name=entry.name().to_owned();let mut data=Vec::new();entry.read_to_end(&mut data)?;
        if name=="Contents/header.xml" {data=format!("<hh:head xmlns:hh='http://www.hancom.co.kr/hwpml/2011/head' xmlns:u='urn:future'>{begin}</hh:head>").into_bytes();}
        output.start_file(name,zip::write::SimpleFileOptions::default().compression_method(zip::CompressionMethod::Stored))?;output.write_all(&data)?;}
    Ok(output.finish()?.into_inner())
}
#[test]
fn source_caption_context_product_reuses_exact_context_and_object_projections_without_counter_defaults() -> TestResult {
    use hwpx_package::document_import::reference_targets::numbering::{ImportedCaptionNumbering,context::NativeOwnerNumberingType};
    let body=format!("{}<hp:rect id='8' numberingType='NONE'/><hp:equation id='9'/>",source_numbering_body().replace("<hp:rect id='7'>","<hp:rect id='7' numberingType='PICTURE'>"));
    let bytes=source_caption_context_package(&body,source_caption_context_begin())?;let forms=fixture::forms(&bytes,"reference-product")?;
    let original=ImportedCaptionNumbering::import(forms.body_structure(),limits()?)?;let context=original.import_context(limits()?)?;let objects=context.project_object_states(limits()?)?;
    let report=assess(&bytes)?;
    assert_eq!(report.numbering_context_receipt(),context.receipt());assert_eq!(report.document_numbering_start(),context.document_start());
    assert_eq!(report.numbering_owners(),context.owners());assert_eq!(report.numbering_control_order(),context.ordered_controls());
    assert_eq!(report.caption_object_state_receipt(),objects.receipt());assert_eq!(report.caption_object_states(),objects.objects());
    assert_eq!((report.numbering_context_receipt().known_owners,report.numbering_context_receipt().uncaptioned_owners,report.numbering_context_receipt().missing_owner_numbering_types),(3,2,1));
    let start=report.document_numbering_start().ok_or("document start")?;
    assert_eq!((start.page,start.footnote,start.endnote,start.picture,start.table,start.equation),(0,2,3,4,5,6));
    assert_eq!(report.numbering_owners()[1].numbering_type,Some(NativeOwnerNumberingType::None));assert_eq!(report.numbering_owners()[2].numbering_type,None);
    assert_eq!(report.numbering_controls()[1].stored_number,19);assert_eq!(report.numbering_section_starts()[0].picture,5);
    assert!(!report.numbering_context_receipt().complete_auxiliary_state_and_sequence_interpretation_qualified);
    assert!(!report.caption_object_state_receipt().complete_auxiliary_state_and_protection_qualified&&!report.caption_object_state_receipt().execution_publication_authority);
    // Same body digest, different whole original/caption identity. No result or
    // authorization from the first package is used to assess the changed bytes.
    let changed=source_caption_context_package(&body.replace("private caption label","different caption"),source_caption_context_begin())?;let after=assess(&changed)?;
    assert_eq!(report.caption_object_states()[0].object_state_sha256,after.caption_object_states()[0].object_state_sha256);
    assert_ne!(report.caption_receipt(),after.caption_receipt());assert_ne!(report.caption_object_state_receipt(),after.caption_object_state_receipt());
    assert_eq!(report.status(),ReferenceSourceStatus::Incomplete);assert!(report.validation_report().is_none());Ok(())
}
#[test]
fn source_caption_context_actual_cli_v8_emits_bound_context_hash_only_states_and_keeps_incomplete_exit() -> TestResult {
    let body=format!("{}<hp:rect id='8' numberingType='NONE'/>",source_numbering_body());
    let bytes=source_caption_context_package(&body,source_caption_context_begin())?;let temp=tempfile::tempdir()?;let path=temp.path().join("numbering-context.hwpx");fs::write(&path,&bytes)?;
    let sha=hex::encode(Sha256::digest(&bytes));let output=cli([OsStr::new("reference-source"),OsStr::new("reference-product"),OsStr::new(&sha),path.as_os_str()])?;
    assert_eq!(output.status.code(),Some(3));assert!(output.stderr.is_empty());
    let value:Value=serde_json::from_slice(&output.stdout)?;
    assert_eq!(value,serde_json::from_slice::<Value>(&assess(&bytes)?.canonical_json(limits()?)?)?);
    assert_eq!(value["schema_version"],"hwpx-agent.product.reference-source-assessment/v15");
    assert_eq!(value["document_numbering_start"]["picture"],4);assert_eq!(value["document_numbering_start"]["page"],0);
    assert_eq!(value["numbering_context_import"]["known_owners"],2);assert_eq!(value["numbering_context_import"]["uncaptioned_owners"],1);
    assert!(value["numbering_owners"][0]["numbering_type"].is_null());assert_eq!(value["numbering_owners"][1]["numbering_type"],"none");
    assert_eq!(value["numbering_control_order"].as_array().ok_or("control order")?.len(),3);
    assert_eq!(value["caption_object_states"].as_array().ok_or("object states")?.len(),2);
    assert_eq!(value["caption_object_states"][0]["excluded_caption_subtrees"],1);
    assert_eq!(value["caption_object_state_import"]["complete_auxiliary_state_and_protection_qualified"],false);
    assert_eq!(value["caption_object_state_import"]["execution_publication_authority"],false);
    assert_eq!(value["status"],"incomplete");assert!(value["validation_report"].is_null());assert_eq!(value["unresolved"].as_array().ok_or("unresolved")?.len(),4);
    assert!(!String::from_utf8_lossy(&output.stdout).contains("private"));assert_eq!(fs::read(path)?,bytes);Ok(())
}
#[test]
fn source_caption_context_product_and_actual_cli_reject_invalid_context_without_partial_evidence() -> TestResult {
    let body=source_numbering_body();let start=source_caption_context_begin();
    for (bytes,expected) in [
        (source_caption_context_package(&body,&start.replace(" pic='4'",""))?,"REFERENCE_SOURCE_NUMBERING_REJECTED"),
        (source_caption_context_package(&body,&format!("{start}{start}"))?,"REFERENCE_SOURCE_NUMBERING_REJECTED"),
        (source_caption_context_package(&body,&format!("<u:future>{start}</u:future>"))?,"REFERENCE_SOURCE_TARGET_COVERAGE_REJECTED"),
        (source_caption_context_package(&body.replace("<hp:rect id='7'>","<hp:rect id='7' numberingType='INVALID'>"),start)?,"REFERENCE_SOURCE_NUMBERING_REJECTED"),
        (source_caption_context_package(&format!("{body}<hp:chart numberingType='PICTURE'/>"),start)?,"REFERENCE_SOURCE_TARGET_COVERAGE_REJECTED"),
    ] {
        assert!(assess(&bytes).is_err());let temp=tempfile::tempdir()?;let path=temp.path().join("bad-context.hwpx");fs::write(&path,&bytes)?;
        let sha=hex::encode(Sha256::digest(&bytes));let output=cli([OsStr::new("reference-source"),OsStr::new("reference-product"),OsStr::new(&sha),path.as_os_str()])?;
        assert_eq!(output.status.code(),Some(2));assert!(output.stdout.is_empty());assert_eq!(String::from_utf8(output.stderr)?.trim(),expected);assert_eq!(fs::read(path)?,bytes);
    }
    let report=assess(&source_caption_context_package(&body,start)?)?;let length=report.canonical_json(limits()?)?.len();
    let exact=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig{input_bytes:length,output_bytes:length,..Default::default()})?;
    let short=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig{input_bytes:length-1,output_bytes:length-1,..Default::default()})?;
    assert_eq!(report.canonical_json(exact)?.len(),length);assert_eq!(report.canonical_json(short),Err(ReferenceSourceError::Output));Ok(())
}

fn source_frame_styles()->&'static str {
    "<hh:refList><hh:charProperties><hh:charPr id='4' private='private frame style'/></hh:charProperties><hh:paraProperties><hh:paraPr id='5'/></hh:paraProperties><hh:styles><hh:style id='6' name='private frame style name'/></hh:styles></hh:refList>"
}
fn source_frame_body()->String {
    source_numbering_body().replace("<hp:p id='99'>","<hp:p id='99' paraPrIDRef='5' styleIDRef='6'>")
        .replace("<hp:run><hp:t>private caption label","<hp:run charPrIDRef='4'><hp:t>private caption label")
}
#[test]
fn source_caption_frames_product_joins_exact_original_models_and_selectors_drive_one_batch_output() -> TestResult {
    use hwpx_package::document_import::{reference_targets::{numbering::ImportedCaptionNumbering,caption_frames::CaptionFrameSegmentKind as Kind},
        structure::caption_text_batch::CaptionTextReplacement};
    let bytes=source_caption_context_package(&source_frame_body(),&format!("{}{}",source_caption_context_begin(),source_frame_styles()))?;
    let original=bytes.clone();let forms=fixture::forms(&bytes,"reference-product")?;
    let numbers=ImportedCaptionNumbering::import(forms.body_structure(),limits()?)?;
    let frames=numbers.import_frames(limits()?)?;let report=assess(&bytes)?;
    assert_eq!(report.caption_frame_receipt(),frames.receipt());assert_eq!(report.caption_frames(),frames.frames());
    assert_eq!(&report.caption_frame_receipt().numbering,report.numbering_receipt());
    assert_eq!(report.caption_envelopes(),numbers.caption_import().envelopes());
    let frame=&report.caption_frames()[0];let owner=&report.numbering_owners()[0];
    assert_eq!(frame.logical_object_id,owner.logical_object_id);assert_eq!(Some(&frame.logical_caption_id),owner.logical_caption_id.as_ref());
    assert_eq!(frame.segments.iter().map(|s|s.kind).collect::<Vec<_>>(),[Kind::PlainText,Kind::AutoNumber]);
    assert_eq!(frame.segments[1].number_control_id.as_ref(),Some(&report.numbering_controls()[1].logical_control_id));
    assert_eq!(report.caption_frame_receipt().unresolved_style_references,0);
    assert!(frame.single_auto_number_linear_layout_observed);
    assert_eq!(report.numbering_controls()[1].stored_number,19);
    let replacement="changed \u{ac00} & <text>\r\nend";
    let requests=[CaptionTextReplacement {caption_id:&frame.logical_caption_id,text_id:&frame.segments[0].logical_source_id,replacement}];
    let candidate=forms.body_structure().lower_caption_text_batch_candidate(&bytes,&requests,limits()?,hwpx_package::WriterLimits::default())?;
    assert_eq!(candidate.receipt().source_package_sha256,<[u8;32]>::from(Sha256::digest(&bytes)));
    candidate.with_verified_bytes(|output|->TestResult {
        let after=assess(output)?;let segment=&after.caption_frames()[0].segments[0];
        assert_eq!(segment.decoded_text_sha256,Some(Sha256::digest(replacement.as_bytes()).into()));
        assert_eq!(segment.decoded_text_bytes,replacement.len());
        assert_eq!(after.numbering_controls()[1].stored_number,19);
        assert_eq!(report.caption_object_states()[0].object_state_sha256,after.caption_object_states()[0].object_state_sha256);
        assert_ne!(report.caption_frame_receipt(),after.caption_frame_receipt());
        assert_eq!(after.status(),ReferenceSourceStatus::Incomplete);assert!(after.validation_report().is_none());Ok(())
    })??;
    assert_eq!(bytes,original);
    let safe=format!("{report:?}{}",String::from_utf8(report.canonical_json(limits()?)?)?);
    assert!(!safe.contains("private")&&!safe.contains(replacement));
    assert!(!report.caption_frame_receipt().effective_style_and_sequence_semantics_qualified
        &&!report.caption_frame_receipt().complete_auxiliary_state_and_protection_qualified
        &&!report.caption_frame_receipt().execution_publication_authority);Ok(())
}
#[test]
fn source_caption_frames_actual_cli_v9_emits_hash_only_bound_frames_and_explicit_unresolved_styles() -> TestResult {
    use hwpx_package::document_import::reference_targets::caption_frames::CaptionStyleReferenceStatus as Style;
    for (body,styles,status) in [
        (source_frame_body(),source_frame_styles().to_owned(),Style::UniqueSourceDeclaration),
        (source_frame_body().replace(" charPrIDRef='4'",""),source_frame_styles().to_owned(),Style::MissingReference),
        (source_frame_body().replace("charPrIDRef='4'","charPrIDRef='999'"),source_frame_styles().to_owned(),Style::MissingDeclaration),
        (source_frame_body(),source_frame_styles().replace("<hh:charPr id='4' private='private frame style'/>","<hh:charPr id='4'/><hh:charPr id='4'/>"),Style::AmbiguousDeclarations),
        (source_frame_body(),"<u:future><hh:charPr id='4'/></u:future>".to_owned(),Style::UnverifiedDeclarationLocation),
    ] {
        let bytes=source_caption_context_package(&body,&format!("{}{styles}",source_caption_context_begin()))?;
        let report=assess(&bytes)?;assert_eq!(report.caption_frames()[0].runs[0].character_style.status,status);
        let temp=tempfile::tempdir()?;let path=temp.path().join("frame-source.hwpx");fs::write(&path,&bytes)?;
        let sha=hex::encode(Sha256::digest(&bytes));let output=cli([OsStr::new("reference-source"),OsStr::new("reference-product"),OsStr::new(&sha),path.as_os_str()])?;
        assert_eq!(output.status.code(),Some(3));assert!(output.stderr.is_empty());
        let value:Value=serde_json::from_slice(&output.stdout)?;assert_eq!(value,serde_json::from_slice::<Value>(&report.canonical_json(limits()?)?)?);
        assert_eq!(value["schema_version"],"hwpx-agent.product.reference-source-assessment/v15");
        assert_eq!(value["caption_frame_import"]["captions"],1);assert_eq!(value["caption_frame_import"]["plain_text_segments"],1);
        assert_eq!(value["caption_frames"][0]["logical_caption_id"],value["caption_envelopes"][0]["logical_caption_id"]);
        assert_eq!(value["caption_frames"][0]["logical_object_id"],value["caption_object_states"][0]["logical_object_id"]);
        assert_eq!(value["caption_frames"][0]["segments"][1]["number_control_id"],value["numbering_controls"][1]["logical_control_id"]);
        assert_eq!(value["caption_frame_import"]["effective_style_and_sequence_semantics_qualified"],false);
        assert_eq!(value["caption_frame_import"]["execution_publication_authority"],false);
        assert_eq!(value["status"],"incomplete");assert!(value["validation_report"].is_null());assert_eq!(value["unresolved"].as_array().ok_or("unresolved")?.len(),4);
        assert!(!String::from_utf8_lossy(&output.stdout).contains("private"));assert_eq!(fs::read(path)?,bytes);
    }Ok(())
}
#[test]
fn source_caption_frames_product_and_actual_cli_reject_invalid_styles_and_preserve_exact_output_limits() -> TestResult {
    for body in [
        source_frame_body().replace("charPrIDRef='4'","charPrIDRef='-1'"),
        source_frame_body().replace("paraPrIDRef='5'","paraPrIDRef='4294967296'"),
        source_frame_body().replace("styleIDRef='6'","styleIDRef='not-an-id'"),
    ] {
        let bytes=source_caption_context_package(&body,source_frame_styles())?;
        assert_eq!(ReferenceValidationProductOperation::assess_package_source(&bytes,DocumentId::parse("reference-product")?,
            Sha256::digest(&bytes).into(),SourceImportLimits::default(),limits()?),Err(ReferenceSourceError::Numbering));
        let temp=tempfile::tempdir()?;let path=temp.path().join("bad-frame-source.hwpx");fs::write(&path,&bytes)?;
        let sha=hex::encode(Sha256::digest(&bytes));let output=cli([OsStr::new("reference-source"),OsStr::new("reference-product"),OsStr::new(&sha),path.as_os_str()])?;
        assert_eq!(output.status.code(),Some(2));assert!(output.stdout.is_empty());
        assert_eq!(String::from_utf8(output.stderr)?.trim(),"REFERENCE_SOURCE_NUMBERING_REJECTED");assert_eq!(fs::read(path)?,bytes);
    }
    let bytes=source_caption_context_package(&source_frame_body(),source_frame_styles())?;let report=assess(&bytes)?;
    let length=report.canonical_json(limits()?)?.len();
    let exact=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {input_bytes:length,output_bytes:length,..Default::default()})?;
    let short=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {input_bytes:length-1,output_bytes:length-1,..Default::default()})?;
    assert_eq!(report.canonical_json(exact)?.len(),length);assert_eq!(report.canonical_json(short),Err(ReferenceSourceError::Output));
    let many=source_frame_body().replace("<hp:t>private caption label</hp:t>","<hp:t>A</hp:t><hp:t>B</hp:t><hp:t>C</hp:t><hp:t>D</hp:t><hp:t>E</hp:t>");
    let bytes=source_caption_context_package(&many,source_frame_styles())?;
    let bounded=ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {items_per_kind:4,..Default::default()})?;
    assert_eq!(ReferenceValidationProductOperation::assess_package_source(&bytes,DocumentId::parse("reference-product")?,
        Sha256::digest(&bytes).into(),SourceImportLimits::default(),bounded),Err(ReferenceSourceError::InputLimit));Ok(())
}

