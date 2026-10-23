//! Immutable captured inputs only; stored equality is not Native/currentness.
use domain_ir::{DocumentId, ReferenceAuxiliaryLimits};
use hwpx_agent_cli::reference_validation_product::ReferenceValidationProductOperation as Product;
use hwpx_package::document_import::{
    SourceImportLimits,
    fields::bookmark_crossref::cache_diagnostics::{
        BookmarkNameCacheDiagnosticKind as Kind, SourceBookmarkNameCacheDiagnostics as Report,
    },
};
use serde_json::{Value, json};
use sha2::{Digest as _, Sha256};
use std::{
    error::Error,
    fs::OpenOptions,
    io::Read,
    path::Path,
    time::{Duration, Instant},
};
type Result<T = ()> = std::result::Result<T, Box<dyn Error>>;
const DOC: &str = "p09-cache-diagnostic620";
const CORPUS: &str = include_str!(
    "../../../implementation/p09/evidence/p09-361-capture010-bookmark-binding-corpus613.v1.json"
);
fn limits() -> Result<ReferenceAuxiliaryLimits> {
    Ok(ReferenceAuxiliaryLimits::new(Default::default())?)
}
fn require(ok: bool) -> Result {
    if ok {
        Ok(())
    } else {
        Err("P620_SOURCE_DIAGNOSTIC_REJECTED".into())
    }
}
fn diagnose(bytes: &[u8], budget: ReferenceAuxiliaryLimits) -> Result<Report> {
    Ok(Product::diagnose_source_bookmark_name_caches(
        bytes,
        DocumentId::parse(DOC)?,
        Sha256::digest(bytes).into(),
        SourceImportLimits::default(),
        budget,
    )?)
}
fn read_pin(pin: &Value) -> Result<Vec<u8>> {
    let name = pin["path"].as_str().ok_or("pin")?;
    require(
        name.starts_with("implementation/p09/evidence/private/")
            && !name.contains('\\')
            && !name.split('/').any(|v| v == ".." || v.is_empty()),
    )?;
    let root = Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(Path::parent)
        .ok_or("root")?;
    let path = root.join(name);
    for ancestor in path.ancestors() {
        let m = ancestor.symlink_metadata()?;
        require(!m.file_type().is_symlink())?;
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt as _;
            require(m.file_attributes() & 0x400 == 0)?;
        }
    }
    let size = pin["bytes"].as_u64().ok_or("size")?;
    require(size > 0 && size <= 4194304 && path.is_file() && path.metadata()?.len() == size)?;
    std::thread::sleep(Duration::from_millis(50));
    let mut options = OpenOptions::new();
    options.read(true);
    #[cfg(windows)]
    {
        use std::os::windows::fs::OpenOptionsExt as _;
        options.share_mode(1);
    }
    let mut file = options.open(path)?;
    let mut bytes = Vec::new();
    let mut buffer = [0; 65536];
    let watch = Instant::now();
    loop {
        let n = file.read(&mut buffer)?;
        if n == 0 {
            break;
        }
        require(bytes.len() + n <= 4194304)?;
        bytes.try_reserve(n)?;
        bytes.extend_from_slice(&buffer[..n]);
        if let Some(delay) =
            Duration::from_secs_f64(bytes.len() as f64 / 2097152.).checked_sub(watch.elapsed())
        {
            std::thread::sleep(delay);
        }
    }
    require(
        bytes.len() as u64 == size
            && hex::encode(Sha256::digest(&bytes)) == pin["sha256"].as_str().ok_or("sha")?,
    )?;
    Ok(bytes)
}
fn check_flags(report: &Report, budget: ReferenceAuxiliaryLimits) -> Result<Value> {
    let v: Value = serde_json::from_slice(&report.canonical_json(budget)?)?;
    for key in [
        "native_display_or_target_resolution_qualified",
        "cache_currentness_qualified",
        "complete_reference_validation_qualified",
    ] {
        require(v[key] == false)?;
    }
    Ok(v)
}
fn fixed_captured() -> Result<Value> {
    require(
        hex::encode(Sha256::digest(CORPUS.as_bytes()))
            == "9e033d551a968c46d982a3a46f5faf6cf96fc99f29b6c9ac6393bff88e9f4e3f",
    )?;
    let corpus: Value = serde_json::from_str(CORPUS)?;
    let cases = corpus["cases"].as_array().ok_or("cases")?;
    require(cases.len() == 8)?;
    let mut rows = Vec::new();
    let (mut matches, mut others) = (0, 0);
    for case in cases {
        for stage in ["opened", "saved", "reopened"] {
            let pin = &case["artifacts"][stage];
            let bytes = read_pin(pin)?;
            let report = diagnose(&bytes, limits()?)?;
            check_flags(&report, limits()?)?;
            require(report.observations().len() == usize::from(stage != "opened"))?;
            if let Some(row) = report.observations().first() {
                let expected = if case["display"] == "bookmark_name" {
                    matches += 1;
                    Kind::StoredNameMatchesCommand
                } else {
                    others += 1;
                    Kind::OtherDisplayNotCompared
                };
                require(row.kind == expected)?;
            }
            rows.push(json!({"case_index":case["case_index"],"stage":stage,"source_sha256":pin["sha256"],"observations":report.observations()}));
            require(read_pin(pin)? == bytes)?;
        }
    }
    require(matches == 4 && others == 12)?;
    Ok(
        json!({"state":"source_bookmark_cache620_observed_not_native_or_currentness","observations":rows,"stored_name_matches_command":matches,"other_display_not_compared":others,
        "actual_native_started":false,"cache_currentness_qualified":false,"P09_complete":false}),
    )
}
fn main() {
    let result = (|| -> Result {
        require(std::env::args().skip(1).collect::<Vec<_>>() == ["--fixed-captured-readonly"])?;
        let out = serde_json::to_vec(&fixed_captured()?)?;
        require(out.len() <= 32768)?;
        println!("{}", String::from_utf8(out)?);
        Ok(())
    })();
    if result.is_err() {
        eprintln!("P620_FIXED_DIAGNOSTIC_FAILED");
        std::process::exit(2);
    }
}
#[cfg(test)]
#[path = "../../hwpx-package/tests/support/document_import_field_fixture.rs"]
#[allow(dead_code)]
mod base;
#[cfg(test)]
#[path = "../../hwpx-package/tests/support/document_import_bookmark_fixture.rs"]
#[allow(dead_code)]
mod fixture;
#[cfg(test)]
mod tests {
    use super::*;
    use domain_ir::ReferenceAuxiliaryLimitConfig;
    use hwpx_package::document_import::fields::{
        ImportedDocumentFields,
        bookmark_crossref::{
            BookmarkCrossReferenceError as BindingError,
            SourceBookmarkCrossReferenceBindings as Bindings,
        },
        cached_source::SourceFieldCachedInlines as Caches,
    };
    fn field(cache: &str, display: u8, hyper: bool) -> String {
        format!(
            "<hp:ctrl><hp:fieldBegin id='1' type='CROSSREF'><hp:parameters cnt='1'><hp:stringParam name='Command'>?private-target;6;{display};{};0</hp:stringParam></hp:parameters></hp:fieldBegin></hp:ctrl>{cache}<hp:ctrl><hp:fieldEnd beginIDRef='1'/></hp:ctrl>",
            u8::from(hyper)
        )
    }
    fn package(body: &str) -> Result<Vec<u8>> {
        base::package(&fixture::paragraph(body))
    }
    fn bound(cache: &str) -> Result<Vec<u8>> {
        package(&format!(
            "{}{}",
            fixture::marker("private-target"),
            field(cache, 1, false)
        ))
    }
    fn kind(bytes: &[u8]) -> Result<Kind> {
        Ok(diagnose(bytes, limits()?)?.observations()[0].kind)
    }
    #[test]
    fn all_eight_options_compare_only_name_and_leave_other_displays_unqualified() -> Result {
        for display in 0..4 {
            for hyper in [false, true] {
                let bytes = package(&format!(
                    "{}{}",
                    fixture::marker("private-target"),
                    field("<hp:t>private-target</hp:t>", display, hyper)
                ))?;
                assert_eq!(
                    kind(&bytes)?,
                    if display == 1 {
                        Kind::StoredNameMatchesCommand
                    } else {
                        Kind::OtherDisplayNotCompared
                    }
                );
            }
        }
        Ok(())
    }
    #[test]
    fn exact_match_mismatch_empty_and_spaces_are_distinct_not_stale_verdicts() -> Result {
        for (cache, expected) in [
            (
                "<hp:t>private-target</hp:t>",
                Kind::StoredNameMatchesCommand,
            ),
            (
                "<hp:t>PRIVATE-TARGET</hp:t>",
                Kind::StoredNameDiffersFromCommand,
            ),
            ("", Kind::StoredNameDiffersFromCommand),
            (
                "<hp:t> private-target </hp:t>",
                Kind::StoredNameDiffersFromCommand,
            ),
        ] {
            assert_eq!(kind(&bound(cache)?)?, expected);
        }
        Ok(())
    }
    #[test]
    fn nested_controls_are_not_flattened_to_a_false_text_match() -> Result {
        let cache = "<hp:ctrl><hp:fieldBegin id='2' type='DATE'/></hp:ctrl><hp:t>private-target</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='2'/></hp:ctrl>";
        assert_eq!(kind(&bound(cache)?)?, Kind::StructuredCacheUnqualified);
        Ok(())
    }
    #[test]
    fn missing_and_ambiguous_source_targets_take_precedence_over_text_equality() -> Result {
        let field = field("<hp:t>private-target</hp:t>", 1, false);
        assert_eq!(kind(&package(&field)?)?, Kind::SourceTargetMissing);
        assert_eq!(
            kind(&package(&format!(
                "{}{}{field}",
                fixture::marker("private-target"),
                fixture::marker("private-target")
            ))?)?,
            Kind::SourceTargetAmbiguous
        );
        Ok(())
    }
    #[test]
    fn foreign_package_and_document_snapshots_cannot_join() -> Result {
        let bytes = bound("<hp:t>private-target</hp:t>")?;
        let forms = base::forms(&bytes, DOC)?;
        let fields = ImportedDocumentFields::import(&forms)?;
        let bindings = Bindings::import(&fields, limits()?)?;
        for (other, doc) in [
            (bound("<hp:t>different</hp:t>")?, DOC),
            (bytes.clone(), "foreign-document"),
        ] {
            let forms = base::forms(&other, doc)?;
            let fields = ImportedDocumentFields::import(&forms)?;
            let caches = Caches::import(&fields, limits()?)?;
            assert_eq!(
                bindings
                    .diagnose_cached_source(&caches, limits()?)
                    .unwrap_err(),
                BindingError::Binding
            );
        }
        Ok(())
    }
    #[test]
    fn separately_imported_identical_snapshot_is_only_a_readonly_diagnostic() -> Result {
        let bytes = bound("<hp:t>private-target</hp:t>")?;
        let forms = base::forms(&bytes, DOC)?;
        let fields = ImportedDocumentFields::import(&forms)?;
        let bindings = Bindings::import(&fields, limits()?)?;
        let other = base::forms(&bytes, DOC)?;
        let other_fields = ImportedDocumentFields::import(&other)?;
        let caches = Caches::import(&other_fields, limits()?)?;
        let before = fields.graph().canonical_sha256()?;
        let result = bindings.diagnose_cached_source(&caches, limits()?)?;
        assert_eq!(before, fields.graph().canonical_sha256()?);
        check_flags(&result, limits()?)?;
        Ok(())
    }
    #[test]
    fn requested_output_boundary_and_text_and_item_limits_remain_effective() -> Result {
        let bytes = bound("<hp:t>private-target</hp:t>")?;
        let forms = base::forms(&bytes, DOC)?;
        let fields = ImportedDocumentFields::import(&forms)?;
        let bindings = Bindings::import(&fields, limits()?)?;
        let caches = Caches::import(&fields, limits()?)?;
        let report = bindings.diagnose_cached_source(&caches, limits()?)?;
        let n = report.canonical_json(limits()?)?.len();
        let exact = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {
            output_bytes: n,
            ..Default::default()
        })?;
        assert_eq!(bindings.diagnose_cached_source(&caches, exact)?, report);
        for config in [
            ReferenceAuxiliaryLimitConfig {
                output_bytes: n - 1,
                ..Default::default()
            },
            ReferenceAuxiliaryLimitConfig {
                text_bytes: 1,
                ..Default::default()
            },
        ] {
            assert_eq!(
                bindings
                    .diagnose_cached_source(&caches, ReferenceAuxiliaryLimits::new(config)?)
                    .unwrap_err(),
                BindingError::Limit
            );
        }
        Ok(())
    }
    #[test]
    fn private_values_and_native_currentness_authority_are_not_exported() -> Result {
        let report = diagnose(&bound("<hp:t>private-target</hp:t>")?, limits()?)?;
        check_flags(&report, limits()?)?;
        assert!(!String::from_utf8(report.canonical_json(limits()?)?)?.contains("private-target"));
        assert!(!format!("{report:?}").contains("private-target"));
        Ok(())
    }
    #[test]
    fn wrong_package_sha_rejects_before_diagnostics() -> Result {
        let bytes = bound("<hp:t>private-target</hp:t>")?;
        let result = Product::diagnose_source_bookmark_name_caches(
            &bytes,
            DocumentId::parse(DOC)?,
            [0; 32],
            SourceImportLimits::default(),
            limits()?,
        );
        assert!(result.is_err());
        Ok(())
    }
    #[test]
    fn absent_fields_and_foreign_command_kinds_never_become_an_all_pass() -> Result {
        let empty = diagnose(&package("<hp:t>no fields</hp:t>")?, limits()?)?;
        assert!(empty.observations().is_empty());
        check_flags(&empty, limits()?)?;
        let foreign = package(&field("<hp:t>x</hp:t>", 1, false).replace(";6;", ";0;"))?;
        assert!(diagnose(&foreign, limits()?).is_err());
        Ok(())
    }
    #[test]
    fn immutable_fixed_twenty_four_inputs_have_four_literal_matches_only() -> Result {
        fixed_captured()?;
        Ok(())
    }
}
