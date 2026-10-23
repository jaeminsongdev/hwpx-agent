// Main Source/CLI integration. Never Native evaluation or complete validation.
use super::*;
use hwpx_agent_cli::reference_validation_product::{
    ReferenceValidationProductOperation as Product,
    source_field_semantics::ReferenceSourceMeaningKind,
};
use hwpx_package::document_import::{
    fields::{
        ImportedDocumentFields,
        semantics::{FieldSemanticImportError, source_index::SourceFieldMeaningIndex},
    },
    reference_targets::ImportedReferenceTargets,
};
use std::{
    io::Read,
    path::{Path, PathBuf},
    time::{Duration, Instant},
};
const CORPUS: &str = include_str!(
    "../../../../implementation/p09/evidence/p09-361-capture010-bookmark-binding-corpus613.v1.json"
);
fn field(id: u32, command: Option<&str>) -> String {
    let parameters=command.map(|text|format!("<hp:parameters cnt='1'><hp:stringParam name='Command'>{}</hp:stringParam></hp:parameters>",text.replace('&',"&amp;").replace('<',"&lt;"))).unwrap_or_default();
    format!(
        "<hp:ctrl><hp:fieldBegin id='{id}' type='CROSSREF'>{parameters}</hp:fieldBegin></hp:ctrl><hp:t>private cache</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='{id}'/></hp:ctrl>"
    )
}
fn source(name: &str, display: u8, hyperlink: bool) -> Result<Vec<u8>, Box<dyn Error>> {
    package(&format!(
        "{}{}",
        marker(name),
        field(
            1,
            Some(&format!(
                "?private-target;6;{display};{};0",
                u8::from(hyperlink)
            ))
        )
    ))
}
fn assert_incomplete(value: &Value) -> TestResult {
    assert_eq!(
        value["schema_version"],
        "hwpx-agent.product.reference-source-assessment/v14"
    );
    assert_eq!(value["status"], "incomplete");
    assert!(value["validation_report"].is_null());
    let unresolved = value["unresolved"].as_array().ok_or("unresolved")?;
    assert_eq!(
        unresolved,
        &[
            "other_target_families",
            "reference_edge_semantics",
            "complete_auxiliary_state",
            "document_flow"
        ]
    );
    assert_eq!(value["field_meanings"]["status"], "incomplete");
    assert_eq!(
        value["field_meanings"]["reference_validation_or_external_approval"],
        false
    );
    assert_eq!(
        value["field_meanings"]["meaning_import"]["complete_reference_state_or_external_approval"],
        false
    );
    assert_eq!(
        value["field_meanings"]["meaning_import"]["additional_document_graph_clones"],
        0
    );
    Ok(())
}
#[test]
fn source_v14_all_eight_options_include_exact_field_meaning_receipt_and_selectors() -> TestResult {
    for display in 0..4 {
        for hyperlink in [false, true] {
            let bytes = source("private-target", display, hyperlink)?;
            let report = assess(&bytes)?;
            let meanings = Product::assess_package_field_semantics(
                &bytes,
                DocumentId::parse("reference-product")?,
                Sha256::digest(&bytes).into(),
                SourceImportLimits::default(),
                limits()?,
            )?;
            assert_eq!(report.field_meanings(), &meanings);
            assert_eq!(meanings.receipt().bookmark_crossrefs, 1);
            assert_eq!(
                meanings.selections()[0].kind,
                ReferenceSourceMeaningKind::BookmarkCrossReference
            );
            let value: Value = serde_json::from_slice(&report.canonical_json(limits()?)?)?;
            assert_eq!(
                value["field_meanings"],
                serde_json::from_slice::<Value>(&meanings.canonical_json(limits()?)?)?
            );
            assert_incomplete(&value)?;
            for secret in ["private-target", "private cache", "?private-target;"] {
                assert!(!format!("{report:?}").contains(secret));
                assert!(!String::from_utf8(report.canonical_json(limits()?)?)?.contains(secret));
            }
        }
    }
    Ok(())
}
#[test]
fn target_inventory_reuse_requires_exact_original_and_limits_even_without_crossrefs() -> TestResult
{
    for bytes in [
        source("private-target", 0, false)?,
        package(&marker("private-target"))?,
    ] {
        let forms = base::forms(&bytes, "reference-product")?;
        let fields = ImportedDocumentFields::import(&forms)?;
        let targets = ImportedReferenceTargets::import(forms.body_structure(), limits()?)?;
        let reused = SourceFieldMeaningIndex::import_using_targets(&fields, limits()?, &targets)?;
        let standalone = SourceFieldMeaningIndex::import(&fields, limits()?)?;
        assert_eq!(reused.receipt(), standalone.receipt());
        assert_eq!(reused.observations(), standalone.observations());
        let foreign = base::forms(&bytes, "reference-product")?;
        let foreign_targets =
            ImportedReferenceTargets::import(foreign.body_structure(), limits()?)?;
        assert!(matches!(
            SourceFieldMeaningIndex::import_using_targets(&fields, limits()?, &foreign_targets),
            Err(FieldSemanticImportError::Binding)
        ));
        let smaller = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {
            text_bytes: 1,
            ..Default::default()
        })?;
        assert!(matches!(
            SourceFieldMeaningIndex::import_using_targets(&fields, smaller, &targets),
            Err(FieldSemanticImportError::Binding)
        ));
        let tighter = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {
            items_per_kind: 1,
            ..Default::default()
        })?;
        let tighter_targets = ImportedReferenceTargets::import(forms.body_structure(), tighter)?;
        assert!(matches!(
            SourceFieldMeaningIndex::import_using_targets(&fields, limits()?, &tighter_targets),
            Err(FieldSemanticImportError::Binding)
        ));
        let fresh = forms.reconstruct_source_for_verification(&bytes)?;
        assert_eq!(reused.verify_reconstruction(&fresh)?, *reused.receipt());
    }
    Ok(())
}
#[test]
fn main_source_missing_and_duplicate_bookmarks_remain_incomplete_not_native_resolution()
-> TestResult {
    for bytes in [
        source("different-target", 0, false)?,
        package(&format!(
            "{}{}{}",
            marker("private-target"),
            marker("private-target"),
            field(1, Some("?private-target;6;0;0;0"))
        ))?,
    ] {
        let report = assess(&bytes)?;
        assert_eq!(report.field_meanings().receipt().bookmark_crossrefs, 1);
        assert!(report.validation_report().is_none());
        assert_incomplete(&serde_json::from_slice(&report.canonical_json(limits()?)?)?)?;
    }
    Ok(())
}
#[test]
fn malformed_keyed_bookmark_command_rejects_main_api_and_actual_cli_without_partial_json()
-> TestResult {
    let bytes = source("private-target", 9, false)?;
    assert_eq!(
        Product::assess_package_source(
            &bytes,
            DocumentId::parse("reference-product")?,
            Sha256::digest(&bytes).into(),
            SourceImportLimits::default(),
            limits()?
        ),
        Err(ReferenceSourceError::FieldRanges)
    );
    let temp = tempfile::tempdir()?;
    let path = temp.path().join("malformed.hwpx");
    fs::write(&path, &bytes)?;
    let sha = hex::encode(Sha256::digest(&bytes));
    let out = cli([
        OsStr::new("reference-source"),
        OsStr::new("reference-product"),
        OsStr::new(&sha),
        path.as_os_str(),
    ])?;
    assert_eq!(out.status.code(), Some(2));
    assert!(out.stdout.is_empty());
    assert_eq!(
        String::from_utf8(out.stderr)?.trim(),
        "REFERENCE_SOURCE_FIELD_RANGES_REJECTED"
    );
    assert_eq!(fs::read(path)?, bytes);
    Ok(())
}
#[test]
fn main_source_mixed_foreign_and_missing_command_fields_are_not_omitted_or_approved() -> TestResult
{
    let mut body = marker("private-target");
    body.push_str(&field(1, Some("?private-target;6;0;0;0")));
    body.push_str(&field(2, Some("?other;0;0;0;0")));
    body.push_str(&field(3, None));
    let report = assess(&package(&body)?)?;
    let meaning = report.field_meanings();
    assert_eq!(meaning.receipt().ranges, 3);
    assert_eq!(meaning.receipt().bookmark_crossrefs, 1);
    assert_eq!(meaning.receipt().unsupported_meanings, 2);
    assert_eq!(
        meaning
            .selections()
            .iter()
            .filter(|s| s.kind == ReferenceSourceMeaningKind::Unsupported)
            .count(),
        2
    );
    assert_incomplete(&serde_json::from_slice(&report.canonical_json(limits()?)?)?)?;
    Ok(())
}
#[test]
fn main_source_field_meanings_bind_package_document_and_target_changes() -> TestResult {
    let bytes = source("private-target", 0, false)?;
    let report = assess(&bytes)?;
    let foreign = Product::assess_package_source(
        &bytes,
        DocumentId::parse("foreign-document")?,
        Sha256::digest(&bytes).into(),
        SourceImportLimits::default(),
        limits()?,
    )?;
    assert_ne!(
        report.field_meanings().selections()[0].reference_id,
        foreign.field_meanings().selections()[0].reference_id
    );
    let changed = assess(&source("other-target", 0, false)?)?;
    assert_ne!(
        report.field_meanings().selections()[0].meaning_sha256,
        changed.field_meanings().selections()[0].meaning_sha256
    );
    assert_eq!(
        Product::assess_package_source(
            &bytes,
            DocumentId::parse("reference-product")?,
            [0; 32],
            SourceImportLimits::default(),
            limits()?
        ),
        Err(ReferenceSourceError::Binding)
    );
    Ok(())
}
#[test]
fn main_source_nested_meaning_output_and_item_budgets_never_truncate_or_suppress_errors()
-> TestResult {
    let bytes = source("private-target", 0, false)?;
    let report = assess(&bytes)?;
    let size = report.canonical_json(limits()?)?.len();
    let exact = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {
        input_bytes: size,
        output_bytes: size,
        ..Default::default()
    })?;
    let short = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {
        input_bytes: size - 1,
        output_bytes: size - 1,
        ..Default::default()
    })?;
    assert_eq!(report.canonical_json(exact)?.len(), size);
    assert_eq!(
        report.canonical_json(short),
        Err(ReferenceSourceError::Output)
    );
    let tiny = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {
        input_bytes: 128,
        output_bytes: 128,
        ..Default::default()
    })?;
    assert_eq!(
        Product::assess_package_source(
            &bytes,
            DocumentId::parse("reference-product")?,
            Sha256::digest(&bytes).into(),
            SourceImportLimits::default(),
            tiny
        ),
        Err(ReferenceSourceError::InputLimit)
    );
    Ok(())
}
fn corpus() -> Result<Value, Box<dyn Error>> {
    assert_eq!(
        hex::encode(Sha256::digest(CORPUS.as_bytes())),
        "9e033d551a968c46d982a3a46f5faf6cf96fc99f29b6c9ac6393bff88e9f4e3f"
    );
    let value: Value = serde_json::from_str(CORPUS)?;
    assert_eq!(value["cases"].as_array().ok_or("cases")?.len(), 8);
    Ok(value)
}
fn fixed_path(pin: &Value) -> Result<PathBuf, Box<dyn Error>> {
    let name = pin["path"].as_str().ok_or("pin")?;
    if !name.starts_with("implementation/p09/evidence/private/")
        || name.contains('\\')
        || name.split('/').any(|v| v == ".." || v.is_empty())
    {
        return Err("fixed path".into());
    }
    let root = Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(Path::parent)
        .ok_or("root")?;
    let path = root.join(name);
    for ancestor in path.ancestors().collect::<Vec<_>>().into_iter().rev() {
        let m = ancestor.symlink_metadata()?;
        if m.file_type().is_symlink() {
            return Err("symlink".into());
        }
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt as _;
            if m.file_attributes() & 0x400 != 0 {
                return Err("reparse".into());
            }
        }
    }
    if !path.is_file() {
        return Err("file required".into());
    }
    Ok(path)
}
fn read_pin(pin: &Value) -> Result<Vec<u8>, Box<dyn Error>> {
    let path = fixed_path(pin)?;
    let size = pin["bytes"].as_u64().ok_or("bytes")?;
    if size == 0 || size > 4194304 || path.metadata()?.len() != size {
        return Err("read budget".into());
    }
    std::thread::sleep(Duration::from_millis(50));
    let mut options = fs::OpenOptions::new();
    options.read(true);
    #[cfg(windows)]
    {
        use std::os::windows::fs::OpenOptionsExt as _;
        options.share_mode(1);
    }
    let mut file = options.open(path)?;
    let mut bytes = Vec::new();
    let mut chunk = [0; 65536];
    let clock = Instant::now();
    loop {
        let n = file.read(&mut chunk)?;
        if n == 0 {
            break;
        }
        if bytes.len() + n > 4194304 {
            return Err("read budget".into());
        }
        bytes.try_reserve(n)?;
        bytes.extend_from_slice(&chunk[..n]);
        if let Some(delay) =
            Duration::from_secs_f64(bytes.len() as f64 / 2097152.).checked_sub(clock.elapsed())
        {
            std::thread::sleep(delay);
        }
    }
    assert_eq!(bytes.len() as u64, size);
    assert_eq!(hex::encode(Sha256::digest(&bytes)), pin["sha256"]);
    Ok(bytes)
}
#[test]
fn actual010_twenty_four_outputs_are_connected_to_main_source_v14_not_only_side_api() -> TestResult
{
    let value = corpus()?;
    let mut count = 0;
    for case in value["cases"].as_array().ok_or("cases")? {
        for stage in ["opened", "saved", "reopened"] {
            let pin = &case["artifacts"][stage];
            let bytes = read_pin(pin)?;
            let report = assess(&bytes)?;
            let standalone = Product::assess_package_field_semantics(
                &bytes,
                DocumentId::parse("reference-product")?,
                Sha256::digest(&bytes).into(),
                SourceImportLimits::default(),
                limits()?,
            )?;
            assert_eq!(report.field_meanings(), &standalone);
            assert_eq!(
                report.field_meanings().receipt().bookmark_crossrefs,
                usize::from(stage != "opened")
            );
            assert_incomplete(&serde_json::from_slice(&report.canonical_json(limits()?)?)?)?;
            assert_eq!(read_pin(pin)?, bytes);
            count += 1;
        }
    }
    assert_eq!(count, 24);
    Ok(())
}
#[test]
fn actual_cli_fixed010_open_saved_reopened_emit_nested_meanings_and_exit_three() -> TestResult {
    let value = corpus()?;
    let case = &value["cases"][7];
    for stage in ["opened", "saved", "reopened"] {
        let pin = &case["artifacts"][stage];
        let path = fixed_path(pin)?;
        let bytes = read_pin(pin)?;
        let sha = pin["sha256"].as_str().ok_or("sha")?;
        let out = cli([
            OsStr::new("reference-source"),
            OsStr::new("reference-product"),
            OsStr::new(sha),
            path.as_os_str(),
        ])?;
        assert_eq!(out.status.code(), Some(3));
        assert!(out.stderr.is_empty());
        let actual: Value = serde_json::from_slice(&out.stdout)?;
        assert_incomplete(&actual)?;
        let expected: Value = serde_json::from_slice(&assess(&bytes)?.canonical_json(limits()?)?)?;
        assert_eq!(actual, expected);
        assert_eq!(
            actual["field_meanings"]["meaning_import"]["bookmark_crossrefs"],
            usize::from(stage != "opened")
        );
        assert_eq!(read_pin(pin)?, bytes);
    }
    Ok(())
}
