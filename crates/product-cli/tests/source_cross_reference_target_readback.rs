use domain_ir::{DocumentId, ReferenceAuxiliaryLimitConfig, ReferenceAuxiliaryLimits};
use hwpx_agent_cli::reference_validation_product::{
    ReferenceValidationProductOperation as Product,
    source_crossref::{
        SourceCrossReferencePreparation as Preparation,
        SourceCrossReferencePreparationError as Error, SourceCrossReferenceSelection as Selection,
    },
};
use hwpx_package::{
    cross_reference_sdk::SdkCrossReferenceDisplay as Display,
    document_import::{
        ImportedSourcePackage, SourceImportLimits, structure::ImportedDocumentStructure,
    },
};
use sha2::{Digest as _, Sha256};
use std::io::{Cursor, Read, Write};
use zip::{CompressionMethod, ZipArchive, ZipWriter, write::SimpleFileOptions};
#[path = "../../hwpx-package/tests/support/document_import_field_fixture.rs"]
#[allow(dead_code)]
mod base;
#[path = "../../hwpx-package/tests/support/document_import_bookmark_fixture.rs"]
#[allow(dead_code)]
mod fixture;
type TestResult = Result<(), Box<dyn std::error::Error>>;
fn limits() -> Result<ReferenceAuxiliaryLimits, Box<dyn std::error::Error>> {
    Ok(ReferenceAuxiliaryLimits::new(Default::default())?)
}
fn prepared(bytes: &[u8]) -> Result<Preparation, Box<dyn std::error::Error>> {
    let source = ImportedDocumentStructure::import(ImportedSourcePackage::import(
        bytes,
        DocumentId::parse("target-readback-product")?,
        Sha256::digest(bytes).into(),
        SourceImportLimits::default(),
    )?)?;
    let mut selections = Vec::new();
    for display in [
        Display::Page,
        Display::BookmarkName,
        Display::Content,
        Display::RelativePosition,
    ] {
        for hyperlink in [false, true] {
            selections.push(Selection {
                target_id: source.bookmarks()[0].reference_id.clone(),
                display,
                hyperlink,
            });
        }
    }
    Ok(Product::prepare_source_crossref_discovery(
        bytes,
        DocumentId::parse("target-readback-product")?,
        Sha256::digest(bytes).into(),
        SourceImportLimits::default(),
        limits()?,
        &selections,
    )?)
}
fn input() -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    base::package(&fixture::paragraph(&fixture::marker("private target name")))
}
fn observe(
    prepared: &Preparation,
    bytes: &[u8],
) -> Result<serde_json::Value, Box<dyn std::error::Error>> {
    Ok(serde_json::from_slice(
        &prepared
            .observe_bookmark_targets_in_output(
                bytes,
                Sha256::digest(bytes).into(),
                SourceImportLimits::default(),
                limits()?,
            )?
            .canonical_json(limits()?)?,
    )?)
}
fn assert_rows(value: &serde_json::Value, status: &str) -> TestResult {
    let rows = value["candidates"].as_array().ok_or("candidates")?;
    assert_eq!(rows.len(), 8);
    for row in rows {
        assert_eq!(row["observation"], status);
    }
    for key in [
        "native_execution_attested",
        "native_target_resolution_qualified",
        "causal_insertion_or_preservation_proved",
        "complete_reference_validation_qualified",
    ] {
        assert_eq!(value[key], false);
    }
    assert_eq!(value["status"], "source_target_observation_only");
    Ok(())
}

#[test]
fn all_eight_names_are_observed_without_equating_source_local_ids_or_native_authority() -> TestResult
{
    let original = input()?;
    let prepared = prepared(&original)?;
    let output = base::package(&fixture::paragraph(&format!(
        "<hp:t>prefix</hp:t>{}",
        fixture::marker("private target name")
    )))?;
    let copy = output.clone();
    let value = observe(&prepared, &output)?;
    assert_rows(&value, "unique_exact_name_observed")?;
    for row in value["candidates"].as_array().ok_or("rows")? {
        assert_ne!(
            row["expected_source_logical_target_id_sha256"],
            row["observed_source_logical_target_id_sha256"]
        );
    }
    assert!(!value.to_string().contains("private target name"));
    assert_eq!(output, copy);
    prepared.verify_source(&original)?;
    Ok(())
}

#[test]
fn missing_and_duplicate_names_are_distinct_without_a_first_match() -> TestResult {
    let prepared = prepared(&input()?)?;
    for (body, state) in [
        ("<hp:t>empty</hp:t>".to_owned(), "not_observed"),
        (
            format!(
                "{}{}",
                fixture::marker("private target name"),
                fixture::marker("private target name")
            ),
            "ambiguous_exact_name",
        ),
    ] {
        let output = base::package(&fixture::paragraph(&body))?;
        let value = observe(&prepared, &output)?;
        assert_rows(&value, state)?;
        for row in value["candidates"].as_array().ok_or("rows")? {
            assert!(row["observed_source_logical_target_id_sha256"].is_null());
            assert!(row["observed_source_target_state_sha256"].is_null());
        }
    }
    Ok(())
}

#[test]
fn decoded_unicode_names_are_exact_without_trimming_or_normalization() -> TestResult {
    let input = base::package(&fixture::paragraph(&fixture::marker("자료&amp;é")))?;
    let prepared = prepared(&input)?;
    for (name, state) in [
        ("자료&#38;é", "unique_exact_name_observed"),
        ("자료&amp;e\u{301}", "not_observed"),
        ("자료&amp;é ", "not_observed"),
    ] {
        let output = base::package(&fixture::paragraph(&fixture::marker(name)))?;
        assert_rows(&observe(&prepared, &output)?, state)?;
    }
    Ok(())
}

#[test]
fn sha_and_work_text_and_serialization_budgets_fail_closed() -> TestResult {
    let bytes = input()?;
    let prepared = prepared(&bytes)?;
    assert!(matches!(
        prepared.observe_bookmark_targets_in_output(
            &bytes,
            [0; 32],
            SourceImportLimits::default(),
            limits()?
        ),
        Err(Error::Binding)
    ));
    for config in [
        ReferenceAuxiliaryLimitConfig {
            items_per_kind: 1,
            ..Default::default()
        },
        ReferenceAuxiliaryLimitConfig {
            text_bytes: 1,
            ..Default::default()
        },
        ReferenceAuxiliaryLimitConfig {
            input_bytes: 256,
            output_bytes: 512,
            ..Default::default()
        },
    ] {
        assert!(matches!(
            prepared.observe_bookmark_targets_in_output(
                &bytes,
                Sha256::digest(&bytes).into(),
                SourceImportLimits::default(),
                ReferenceAuxiliaryLimits::new(config)?
            ),
            Err(Error::Limit)
        ));
    }
    let observed = prepared.observe_bookmark_targets_in_output(
        &bytes,
        Sha256::digest(&bytes).into(),
        SourceImportLimits::default(),
        limits()?,
    )?;
    assert!(matches!(
        observed.canonical_json(ReferenceAuxiliaryLimits::new(
            ReferenceAuxiliaryLimitConfig {
                input_bytes: 256,
                output_bytes: 512,
                ..Default::default()
            }
        )?),
        Err(Error::Limit)
    ));
    assert!(!format!("{observed:?}").contains("private target name"));
    Ok(())
}

#[test]
fn a_bookmark_in_a_nonspine_part_cannot_be_ignored() -> TestResult {
    let bytes = input()?;
    let prepared = prepared(&bytes)?;
    let mut source = ZipArchive::new(Cursor::new(&bytes))?;
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    for index in 0..source.len() {
        let mut entry = source.by_index(index)?;
        let name = entry.name().to_owned();
        let mut data = Vec::new();
        entry.read_to_end(&mut data)?;
        if name == "Contents/header.xml" {
            data=b"<header xmlns:hp='http://www.hancom.co.kr/hwpml/2011/paragraph'><hp:ctrl><hp:bookmark name='hidden'/></hp:ctrl></header>".to_vec();
        }
        writer.start_file(
            name,
            SimpleFileOptions::default().compression_method(CompressionMethod::Stored),
        )?;
        writer.write_all(&data)?;
    }
    let output = writer.finish()?.into_inner();
    assert!(matches!(
        prepared.observe_bookmark_targets_in_output(
            &output,
            Sha256::digest(&output).into(),
            SourceImportLimits::default(),
            limits()?
        ),
        Err(Error::Source)
    ));
    Ok(())
}

#[test]
fn actual_generated_discovery_input_observes_all_eight_without_a_native_claim() -> TestResult {
    let path=std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../implementation/p09/evidence/private/p09-361-crossref-discovery-inputs-20261017-r01/source-with-bookmark.hwpx");
    let meta = path.symlink_metadata()?;
    assert!(meta.is_file() && !meta.file_type().is_symlink() && meta.len() == 14425);
    let bytes = std::fs::read(path)?;
    assert_eq!(
        hex::encode(Sha256::digest(&bytes)),
        "64539a2dc6e76f0301c8beba20cf24083810fdf571f1f5dabbbf2764cd1ee184"
    );
    let value = observe(&prepared(&bytes)?, &bytes)?;
    assert_rows(&value, "unique_exact_name_observed")?;
    assert_eq!(value["observed_targets"]["bookmark_targets"], 1);
    assert_eq!(value["observed_targets"]["observed_native_fields"], 1);
    Ok(())
}

#[test]
fn historical_saved_hyperlink_has_no_matching_bookmark_target() -> TestResult {
    let bytes = base::captured()?;
    let copy = bytes.clone();
    let value = observe(&prepared(&input()?)?, &bytes)?;
    assert_rows(&value, "not_observed")?;
    assert_eq!(value["observed_targets"]["bookmark_targets"], 0);
    assert_eq!(bytes, copy);
    Ok(())
}
