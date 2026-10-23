//! Actual source-bound command update candidates, no Native or source overwrite.
use domain_ir::{DocumentId, ReferenceAuxiliaryLimits};
use hwpx_agent_cli::reference_validation_product::{
    ReferenceValidationProductOperation as Product,
    source_field_semantics::ReferenceSourceMeaningKind,
};
use hwpx_package::{
    WriterLimits,
    cross_reference_sdk::SdkCrossReferenceDisplay as Display,
    document_import::{
        SourceImportLimits,
        fields::{
            bookmark_crossref::SourceBookmarkResolution,
            semantics::source_index::bookmark_updates::{
                SourceBookmarkCommandCandidate as Candidate, SourceBookmarkCommandChange as Change,
            },
        },
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
const DOC: &str = "p09-bookmark-update621";
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
        Err("P621_UPDATE_CANDIDATE_REJECTED".into())
    }
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

fn update(bytes: &[u8], target_name: &str, display: Display, hyperlink: bool) -> Result<Candidate> {
    let sha = Sha256::digest(bytes).into();
    let assessment = Product::assess_package_source(
        bytes,
        DocumentId::parse(DOC)?,
        sha,
        SourceImportLimits::default(),
        limits()?,
    )?;
    let field = assessment
        .field_meanings()
        .selections()
        .iter()
        .find(|v| v.kind == ReferenceSourceMeaningKind::BookmarkCrossReference)
        .ok_or("field")?;
    let bindings = Product::read_source_bookmark_crossrefs(
        bytes,
        DocumentId::parse(DOC)?,
        sha,
        SourceImportLimits::default(),
        limits()?,
    )?;
    let target = if target_name.is_empty() {
        let SourceBookmarkResolution::Bound {
            logical_target_id, ..
        } = &bindings.bindings()[0].target
        else {
            return Err("bound target".into());
        };
        logical_target_id.clone()
    } else {
        let forms = base_forms(bytes)?;
        forms
            .body_structure()
            .bookmarks()
            .iter()
            .find(|v| v.name == target_name)
            .ok_or("target")?
            .reference_id
            .clone()
    };
    Ok(Product::prepare_source_bookmark_command_changes(
        bytes,
        DocumentId::parse(DOC)?,
        sha,
        SourceImportLimits::default(),
        limits()?,
        &[Change {
            reference_id: &field.reference_id,
            expected_source_field_sha256: field.source_field_sha256,
            expected_meaning_sha256: field.meaning_sha256,
            target_id: &target,
            display,
            hyperlink,
        }],
        WriterLimits::default(),
    )?)
}
fn base_forms(bytes: &[u8]) -> Result<hwpx_package::document_import::forms::ImportedDocumentForms> {
    use hwpx_package::document_import::{ImportedSourcePackage, forms::ImportedDocumentForms};
    Ok(ImportedDocumentForms::import(
        ImportedSourcePackage::import(
            bytes,
            DocumentId::parse(DOC)?,
            Sha256::digest(bytes).into(),
            SourceImportLimits::default(),
        )?,
    )?)
}
fn fixed_captured() -> Result<Value> {
    require(
        hex::encode(Sha256::digest(CORPUS.as_bytes()))
            == "9e033d551a968c46d982a3a46f5faf6cf96fc99f29b6c9ac6393bff88e9f4e3f",
    )?;
    let corpus: Value = serde_json::from_str(CORPUS)?;
    let mut rows = Vec::new();
    for case in corpus["cases"].as_array().ok_or("cases")? {
        for stage in ["saved", "reopened"] {
            let pin = &case["artifacts"][stage];
            let bytes = read_pin(pin)?;
            let original = bytes.clone();
            let hyper = !case["hyperlink"].as_bool().ok_or("hyperlink")?;
            let display = if case["display"] == "page" {
                Display::BookmarkName
            } else {
                Display::Page
            };
            let candidate = update(&bytes, "", display, hyper)?;
            let receipt = candidate.receipt();
            require(
                receipt.changes.len() == 1
                    && receipt.changed_command_leaves == 1
                    && receipt.outside_selected_command_contents_exact
                    && receipt.cached_values_preserved_not_refreshed
                    && !receipt.native_protection_currentness_execution_or_publication_qualified,
            )?;
            let output = candidate.with_verified_bytes(|v| v.to_vec())?;
            require(
                output != bytes
                    && <[u8; 32]>::from(Sha256::digest(&output)) == receipt.output_package_sha256,
            )?;
            let before = Product::assess_package_source(
                &bytes,
                DocumentId::parse(DOC)?,
                Sha256::digest(&bytes).into(),
                SourceImportLimits::default(),
                limits()?,
            )?;
            let after = Product::assess_package_source(
                &output,
                DocumentId::parse(DOC)?,
                Sha256::digest(&output).into(),
                SourceImportLimits::default(),
                limits()?,
            )?;
            require(
                before
                    .field_cached_source()
                    .observations()
                    .iter()
                    .map(|v| &v.cache)
                    .eq(after
                        .field_cached_source()
                        .observations()
                        .iter()
                        .map(|v| &v.cache)),
            )?;
            require(bytes == original && read_pin(pin)? == original)?;
            rows.push(json!({"case_index":case["case_index"],"stage":stage,"source_sha256":pin["sha256"],"receipt":receipt,"cached_values_preserved":true}));
        }
    }
    require(rows.len() == 16)?;
    Ok(
        json!({"state":"source_bookmark_updates621_candidates_not_native_or_currentness","observations":rows,"actual_native_started":false,"cache_currentness_qualified":false,"source_overwritten":false,"P09_complete":false}),
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
        eprintln!("P621_FIXED_UPDATE_FAILED");
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
    use domain_ir::{LogicalId, ReferenceAuxiliaryLimitConfig};
    use hwpx_package::document_import::fields::{
        ImportedDocumentFields,
        semantics::source_index::{
            SourceFieldMeaningIndex, bookmark_updates::SourceBookmarkCommandError as E,
        },
    };
    fn field(id: u32, name: &str, cache: &str) -> String {
        format!(
            "<hp:ctrl><hp:fieldBegin id='{id}' type='CROSSREF' editable='true'><hp:parameters cnt='2'><hp:stringParam name='Command'>?{name};6;1;0;0</hp:stringParam><hp:stringParam name='Private'>keep&amp;原文</hp:stringParam></hp:parameters></hp:fieldBegin></hp:ctrl><hp:t>{cache}</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='{id}'/></hp:ctrl>"
        )
    }
    fn package(body: &str) -> Result<Vec<u8>> {
        base::package(&fixture::paragraph(body))
    }
    fn sample() -> Result<Vec<u8>> {
        package(&format!(
            "{}{}{}{}",
            fixture::marker("old"),
            fixture::marker("new"),
            field(1, "old", "cached&amp;value"),
            field(2, "old", "UNSELECTED")
        ))
    }
    fn prepare<'a>(
        bytes: &[u8],
        requests: &[Change<'a>],
        budget: ReferenceAuxiliaryLimits,
    ) -> std::result::Result<Candidate, E> {
        Product::prepare_source_bookmark_command_changes(
            bytes,
            DocumentId::parse(DOC).unwrap(),
            Sha256::digest(bytes).into(),
            SourceImportLimits::default(),
            budget,
            requests,
            WriterLimits::default(),
        )
    }
    #[test]
    fn eight_update_options_retarget_actual_bookmark_and_preserve_other_meanings_and_caches()
    -> Result {
        let bytes = sample()?;
        for display in [
            Display::Page,
            Display::BookmarkName,
            Display::Content,
            Display::RelativePosition,
        ] {
            for hyper in [false, true] {
                let c = update(&bytes, "new", display, hyper)?;
                let output = c.with_verified_bytes(|v| v.to_vec())?;
                let b = Product::read_source_bookmark_crossrefs(
                    &output,
                    DocumentId::parse(DOC)?,
                    Sha256::digest(&output).into(),
                    SourceImportLimits::default(),
                    limits()?,
                )?;
                assert_eq!(b.bindings()[0].hyperlink, hyper);
                assert_eq!(
                    b.bindings()[0].exact_target_name_sha256,
                    <[u8; 32]>::from(Sha256::digest(b"new"))
                );
                assert_eq!(
                    b.bindings()[1].exact_target_name_sha256,
                    <[u8; 32]>::from(Sha256::digest(b"old"))
                );
                assert!(
                    c.receipt().outside_selected_command_contents_exact
                        && c.receipt().cached_values_preserved_not_refreshed
                );
                assert!(
                    !c.receipt()
                        .native_protection_currentness_execution_or_publication_qualified
                );
            }
        }
        Ok(())
    }
    #[test]
    fn multiple_updates_commit_one_owned_candidate_and_one_bad_target_denies_entire_batch() -> Result
    {
        let bytes = sample()?;
        let original = bytes.clone();
        let s = Product::assess_package_field_semantics(
            &bytes,
            DocumentId::parse(DOC)?,
            Sha256::digest(&bytes).into(),
            SourceImportLimits::default(),
            limits()?,
        )?;
        let forms = base_forms(&bytes)?;
        let target = &forms.body_structure().bookmarks()[1].reference_id;
        let mut requests: Vec<_> = s
            .selections()
            .iter()
            .map(|f| Change {
                reference_id: &f.reference_id,
                expected_source_field_sha256: f.source_field_sha256,
                expected_meaning_sha256: f.meaning_sha256,
                target_id: target,
                display: Display::Page,
                hyperlink: true,
            })
            .collect();
        let c = prepare(&bytes, &requests, limits()?)?;
        assert_eq!(
            (
                c.receipt().changes.len(),
                c.receipt().changed_parts,
                c.receipt().changed_command_leaves
            ),
            (2, 1, 2)
        );
        let output = c.with_verified_bytes(|v| v.to_vec())?;
        let bindings = Product::read_source_bookmark_crossrefs(
            &output,
            DocumentId::parse(DOC)?,
            Sha256::digest(&output).into(),
            SourceImportLimits::default(),
            limits()?,
        )?;
        assert!(
            bindings
                .bindings()
                .iter()
                .all(
                    |v| v.exact_target_name_sha256 == <[u8; 32]>::from(Sha256::digest(b"new"))
                        && v.hyperlink
                )
        );
        let foreign = LogicalId::parse("missing-target")?;
        requests[1].target_id = &foreign;
        assert_eq!(
            prepare(&bytes, &requests, limits()?).unwrap_err(),
            E::Target
        );
        assert_eq!(bytes, original);
        Ok(())
    }
    #[test]
    fn immutable_sixteen_saved_sources_produce_owned_updates_not_native_execution() -> Result {
        fixed_captured()?;
        Ok(())
    }
    #[test]
    fn stale_field_meaning_missing_foreign_and_duplicate_selectors_deny_whole_batch() -> Result {
        let bytes = sample()?;
        let s = Product::assess_package_field_semantics(
            &bytes,
            DocumentId::parse(DOC)?,
            Sha256::digest(&bytes).into(),
            SourceImportLimits::default(),
            limits()?,
        )?;
        let f = &s.selections()[0];
        let forms = base_forms(&bytes)?;
        let target = &forms.body_structure().bookmarks()[1].reference_id;
        let make = || Change {
            reference_id: &f.reference_id,
            expected_source_field_sha256: f.source_field_sha256,
            expected_meaning_sha256: f.meaning_sha256,
            target_id: target,
            display: Display::Page,
            hyperlink: false,
        };
        let mut bad = make();
        bad.expected_source_field_sha256 = [0; 32];
        assert_eq!(
            prepare(&bytes, &[bad], limits()?).unwrap_err(),
            E::Selection
        );
        let mut bad = make();
        bad.expected_meaning_sha256 = [0; 32];
        assert_eq!(
            prepare(&bytes, &[bad], limits()?).unwrap_err(),
            E::Selection
        );
        let foreign = LogicalId::parse("foreign-field")?;
        let mut bad = make();
        bad.reference_id = &foreign;
        assert_eq!(
            prepare(&bytes, &[bad], limits()?).unwrap_err(),
            E::Selection
        );
        let mut bad = make();
        bad.target_id = &foreign;
        assert_eq!(prepare(&bytes, &[bad], limits()?).unwrap_err(), E::Target);
        assert_eq!(
            prepare(&bytes, &[make(), make()], limits()?).unwrap_err(),
            E::Selection
        );
        Ok(())
    }
    #[test]
    fn no_op_empty_batch_unsupported_destination_and_bad_sha_are_not_candidates() -> Result {
        let bytes = sample()?;
        assert!(update(&bytes, "old", Display::BookmarkName, false).is_err());
        assert_eq!(prepare(&bytes, &[], limits()?).unwrap_err(), E::Limit);
        assert!(update(&bytes, "new", Display::ObjectNumber, false).is_err());
        assert!(
            Product::prepare_source_bookmark_command_changes(
                &bytes,
                DocumentId::parse(DOC)?,
                [0; 32],
                SourceImportLimits::default(),
                limits()?,
                &[],
                WriterLimits::default()
            )
            .is_err()
        );
        Ok(())
    }
    #[test]
    fn observed_locks_tracked_changes_table_protection_and_outer_field_locks_reject() -> Result {
        let plain = format!("{}{}", fixture::marker("old"), field(1, "old", "cache"));
        for body in [
            plain.replace("editable='true'", "editable='true' lock='1'"),
            format!("<hp:insertBegin id='9'/>{plain}"),
            format!("<hp:insertBegin id='9'/>{plain}<hp:insertEnd id='9'/>"),
            fixture::table(&plain).replace("protect=\"0\"", "protect=\"1\""),
            format!(
                "{}<hp:ctrl><hp:fieldBegin id='9' type='DATE' lock='1'/></hp:ctrl>{}<hp:ctrl><hp:fieldEnd beginIDRef='9'/></hp:ctrl>",
                fixture::marker("old"),
                field(1, "old", "cache")
            ),
        ] {
            let error = update(&package(&body)?, "", Display::Page, true).unwrap_err();
            assert_eq!(error.downcast_ref::<E>(), Some(&E::Protection));
        }
        Ok(())
    }
    #[test]
    fn missing_source_target_can_be_repaired_but_ambiguous_destination_is_rejected() -> Result {
        let bytes = package(&format!(
            "{}{}",
            fixture::marker("new"),
            field(1, "missing", "cache")
        ))?;
        let c = update(&bytes, "new", Display::Page, true)?;
        assert_eq!(c.receipt().changes.len(), 1);
        let bytes = package(&format!(
            "{}{}{}",
            fixture::marker("new"),
            fixture::marker("new"),
            field(1, "missing", "cache")
        ))?;
        assert!(update(&bytes, "new", Display::Page, true).is_err());
        Ok(())
    }
    #[test]
    fn fresh_proof_is_bound_to_original_import_not_equal_bytes_from_another_import() -> Result {
        let bytes = sample()?;
        let forms = base_forms(&bytes)?;
        let fields = ImportedDocumentFields::import(&forms)?;
        let index = SourceFieldMeaningIndex::import(&fields, limits()?)?;
        let f = &fields.fields()[0];
        let target = &forms.body_structure().bookmarks()[1].reference_id;
        let request = Change {
            reference_id: &f.reference_id,
            expected_source_field_sha256: f.begin_anchor.fingerprint_sha256,
            expected_meaning_sha256: index.meaning_sha256(0)?,
            target_id: target,
            display: Display::Page,
            hyperlink: false,
        };
        let foreign = base_forms(&bytes)?;
        let proof = foreign.reconstruct_source_for_verification(&bytes)?;
        assert_eq!(
            index
                .lower_bookmark_command_changes(&proof, &[request], WriterLimits::default())
                .unwrap_err(),
            E::Source
        );
        Ok(())
    }
    #[test]
    fn finite_output_budget_and_private_values_never_become_public_authority() -> Result {
        let bytes = sample()?;
        let c = update(&bytes, "new", Display::Page, true)?;
        let text = serde_json::to_string(c.receipt())?;
        assert!(
            !text.contains("cached")
                && !text.contains("?new")
                && !format!("{c:?}").contains("cached")
        );
        let forms = base_forms(&bytes)?;
        let fields = ImportedDocumentFields::import(&forms)?;
        let index = SourceFieldMeaningIndex::import(&fields, limits()?)?;
        let f = &fields.fields()[0];
        let target = &forms.body_structure().bookmarks()[1].reference_id;
        let request = Change {
            reference_id: &f.reference_id,
            expected_source_field_sha256: f.begin_anchor.fingerprint_sha256,
            expected_meaning_sha256: index.meaning_sha256(0)?,
            target_id: target,
            display: Display::Page,
            hyperlink: false,
        };
        let tiny = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {
            input_bytes: 128,
            output_bytes: 128,
            ..Default::default()
        })?;
        assert!(prepare(&bytes, &[request], tiny).is_err());
        Ok(())
    }
}
