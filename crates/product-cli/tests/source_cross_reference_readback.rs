use domain_ir::{DocumentId, ReferenceAuxiliaryLimits};
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
fn field(id: usize, value: &str) -> String {
    format!(
        "<hp:ctrl><hp:fieldBegin id='{id}' type='CROSSREF'><hp:parameters cnt='1'><hp:stringParam name='unverified-key'>{}</hp:stringParam></hp:parameters></hp:fieldBegin></hp:ctrl><hp:t>cache</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='{id}'/></hp:ctrl>",
        value.replace('&', "&amp;")
    )
}
fn input(existing: &str, all: bool) -> Result<(Vec<u8>, Preparation), Box<dyn std::error::Error>> {
    let bytes = base::package(&fixture::paragraph(&format!(
        "{}{existing}",
        fixture::marker("private source name")
    )))?;
    let source = ImportedDocumentStructure::import(ImportedSourcePackage::import(
        &bytes,
        DocumentId::parse("readback-product")?,
        Sha256::digest(&bytes).into(),
        SourceImportLimits::default(),
    )?)?;
    let mut requests = Vec::new();
    for display in [
        Display::Page,
        Display::BookmarkName,
        Display::Content,
        Display::RelativePosition,
    ] {
        for hyperlink in [false, true] {
            if all || requests.is_empty() {
                requests.push(Selection {
                    target_id: source.bookmarks()[0].reference_id.clone(),
                    display,
                    hyperlink,
                });
            }
        }
    }
    let prepared = Product::prepare_source_crossref_discovery(
        &bytes,
        DocumentId::parse("readback-product")?,
        Sha256::digest(&bytes).into(),
        SourceImportLimits::default(),
        limits()?,
        &requests,
    )?;
    Ok((bytes, prepared))
}

#[test]
fn prepared_eight_candidates_share_one_actual_output_import_without_native_success_claims()
-> TestResult {
    let (original, prepared) = input("", true)?;
    let controls = prepared
        .candidates_for_discovery()
        .iter()
        .enumerate()
        .map(|(n, c)| field(n + 1, c.command_for_discovery()))
        .collect::<String>();
    let output = base::package(&fixture::paragraph(&controls))?;
    let copy = output.clone();
    let observed = prepared.observe_crossref_output(
        &output,
        Sha256::digest(&output).into(),
        SourceImportLimits::default(),
        limits()?,
    )?;
    let json = observed.canonical_json(limits()?)?;
    let value: serde_json::Value = serde_json::from_slice(&json)?;
    assert_eq!(value["crossref_fields"], 8);
    assert_eq!(value["candidates"].as_array().ok_or("candidates")?.len(), 8);
    for row in value["candidates"].as_array().ok_or("candidates")? {
        assert_eq!(row["observation"], "single_decoded_leaf_observed");
    }
    for key in [
        "parameter_key_semantics_qualified",
        "native_execution_attested",
        "causal_insertion_or_preservation_proved",
        "complete_reference_validation_qualified",
    ] {
        assert_eq!(value[key], false);
    }
    assert!(!String::from_utf8_lossy(&json).contains("private source name"));
    assert_eq!(output, copy);
    prepared.verify_source(&original)?;
    Ok(())
}

#[test]
fn preexisting_matching_field_is_not_evidence_of_insertion_or_preservation() -> TestResult {
    let (bytes, prepared) = input(&field(1, "?private source name;6;0;0;0"), false)?;
    let value: serde_json::Value = serde_json::from_slice(
        &prepared
            .observe_crossref_output(
                &bytes,
                Sha256::digest(&bytes).into(),
                SourceImportLimits::default(),
                limits()?,
            )?
            .canonical_json(limits()?)?,
    )?;
    assert_eq!(
        value["candidates"][0]["observation"],
        "single_decoded_leaf_observed"
    );
    assert_eq!(value["causal_insertion_or_preservation_proved"], false);
    assert_eq!(value["native_execution_attested"], false);
    Ok(())
}

#[test]
fn no_observation_wrong_digest_and_malformed_field_pairs_are_not_promoted() -> TestResult {
    let (bytes, prepared) = input("", false)?;
    let value: serde_json::Value = serde_json::from_slice(
        &prepared
            .observe_crossref_output(
                &bytes,
                Sha256::digest(&bytes).into(),
                SourceImportLimits::default(),
                limits()?,
            )?
            .canonical_json(limits()?)?,
    )?;
    assert_eq!(value["crossref_fields"], 0);
    assert_eq!(value["candidates"][0]["observation"], "not_observed");
    assert!(matches!(
        prepared.observe_crossref_output(&bytes, [0; 32], SourceImportLimits::default(), limits()?),
        Err(Error::Binding)
    ));
    let malformed = base::package(&fixture::paragraph(
        &field(1, "candidate").replace("beginIDRef='1'", "beginIDRef='2'"),
    ))?;
    assert!(matches!(
        prepared.observe_crossref_output(
            &malformed,
            Sha256::digest(&malformed).into(),
            SourceImportLimits::default(),
            limits()?
        ),
        Err(Error::Source)
    ));
    Ok(())
}

#[test]
fn historical_hangul_saved_hyperlink_is_not_a_crossref_observation() -> TestResult {
    let (_, prepared) = input("", false)?;
    let output = base::captured()?;
    let copy = output.clone();
    let observed = prepared.observe_crossref_output(
        &output,
        Sha256::digest(&output).into(),
        SourceImportLimits::default(),
        limits()?,
    )?;
    let report: serde_json::Value = serde_json::from_slice(&observed.canonical_json(limits()?)?)?;
    assert_eq!(report["crossref_fields"], 0);
    assert_eq!(report["candidates"][0]["observation"], "not_observed");
    assert_eq!(report["native_execution_attested"], false);
    assert_eq!(report["complete_reference_validation_qualified"], false);
    assert_eq!(output, copy);
    Ok(())
}

#[test]
fn combined_output_binds_both_original_observations_to_the_same_package() -> TestResult {
    let (original, prepared) = input("", true)?;
    let controls = prepared.candidates_for_discovery().iter().enumerate()
        .map(|(n, c)| field(n + 1, c.command_for_discovery())).collect::<String>();
    let output = base::package(&fixture::paragraph(&format!(
        "{}{controls}", fixture::marker("private source name")
    )))?;
    let digest = Sha256::digest(&output).into();
    let combined = prepared.observe_output_for_discovery(&output, digest, SourceImportLimits::default(), limits()?)?;
    let value: serde_json::Value = serde_json::from_slice(&combined.canonical_json(limits()?)?)?;
    let commands: serde_json::Value = serde_json::from_slice(&prepared.observe_crossref_output(
        &output, digest, SourceImportLimits::default(), limits()?)?.canonical_json(limits()?)?)?;
    let targets: serde_json::Value = serde_json::from_slice(&prepared.observe_bookmark_targets_in_output(
        &output, digest, SourceImportLimits::default(), limits()?)?.canonical_json(limits()?)?)?;
    assert_eq!(value["commands"], commands);
    assert_eq!(value["targets"], targets);
    assert_eq!(value["observed_source_package_sha256"], value["commands"]["observed_source_package_sha256"]);
    assert_eq!(value["observed_source_package_sha256"], value["targets"]["observed_targets"]["source_package_sha256"]);
    assert_eq!(value["status"], "source_output_observation_only");
    for key in ["native_execution_attested", "native_target_resolution_qualified",
        "causal_insertion_or_preservation_proved", "complete_reference_validation_qualified"] {
        assert_eq!(value[key], false);
    }
    assert!(!value.to_string().contains("private source name"));
    assert!(!format!("{combined:?}").contains("private source name"));
    prepared.verify_source(&original)?;
    Ok(())
}

#[test]
fn combined_matching_command_does_not_resolve_missing_or_duplicate_targets() -> TestResult {
    let (_, prepared) = input("", false)?;
    let control = field(1, prepared.candidates_for_discovery()[0].command_for_discovery());
    for (targets, expected) in [
        (String::new(), "not_observed"),
        (fixture::marker("private source name").repeat(2), "ambiguous_exact_name"),
    ] {
        let output = base::package(&fixture::paragraph(&format!("{targets}{control}")))?;
        let result = prepared.observe_output_for_discovery(&output, Sha256::digest(&output).into(),
            SourceImportLimits::default(), limits()?)?;
        let value: serde_json::Value = serde_json::from_slice(&result.canonical_json(limits()?)?)?;
        assert_eq!(value["commands"]["candidates"][0]["observation"], "single_decoded_leaf_observed");
        assert_eq!(value["targets"]["candidates"][0]["observation"], expected);
        assert_eq!(value["native_target_resolution_qualified"], false);
        assert_eq!(value["complete_reference_validation_qualified"], false);
    }
    Ok(())
}

#[test]
fn combined_rejects_wrong_sha_and_original_field_pair_failure_without_partial_result() -> TestResult {
    let (bytes, prepared) = input("", false)?;
    assert!(matches!(prepared.observe_output_for_discovery(&bytes, [0; 32],
        SourceImportLimits::default(), limits()?), Err(Error::Binding)));
    let malformed = base::package(&fixture::paragraph(
        &field(1, "command").replace("beginIDRef='1'", "beginIDRef='2'")
    ))?;
    assert!(matches!(prepared.observe_output_for_discovery(&malformed, Sha256::digest(&malformed).into(),
        SourceImportLimits::default(), limits()?), Err(Error::Source)));
    Ok(())
}

#[test]
fn combined_output_budget_is_one_limit_not_two_individually_permitted_reports() -> TestResult {
    use domain_ir::ReferenceAuxiliaryLimitConfig;
    let (_, prepared) = input("", true)?;
    let controls = prepared.candidates_for_discovery().iter().enumerate()
        .map(|(n, c)| field(n + 1, c.command_for_discovery())).collect::<String>();
    let output = base::package(&fixture::paragraph(&format!("{}{controls}", fixture::marker("private source name"))))?;
    let digest = Sha256::digest(&output).into();
    let commands = prepared.observe_crossref_output(&output, digest, SourceImportLimits::default(), limits()?)?;
    let targets = prepared.observe_bookmark_targets_in_output(&output, digest, SourceImportLimits::default(), limits()?)?;
    let maximum = commands.canonical_json(limits()?)?.len().max(targets.canonical_json(limits()?)?.len());
    let tight = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {
        input_bytes: maximum, output_bytes: maximum, ..Default::default()
    })?;
    assert!(prepared.observe_crossref_output(&output, digest, SourceImportLimits::default(), tight).is_ok());
    assert!(prepared.observe_bookmark_targets_in_output(&output, digest, SourceImportLimits::default(), tight).is_ok());
    assert!(matches!(prepared.observe_output_for_discovery(&output, digest, SourceImportLimits::default(), tight), Err(Error::Limit)));
    Ok(())
}

#[test]
fn combined_historical_saved_hyperlink_has_no_crossref_or_native_success() -> TestResult {
    let (_, prepared) = input("", false)?;
    let output = base::captured()?;
    let original = output.clone();
    let report = prepared.observe_output_for_discovery(&output, Sha256::digest(&output).into(),
        SourceImportLimits::default(), limits()?)?;
    let value: serde_json::Value = serde_json::from_slice(&report.canonical_json(limits()?)?)?;
    assert_eq!(value["commands"]["crossref_fields"], 0);
    assert_eq!(value["commands"]["candidates"][0]["observation"], "not_observed");
    assert_eq!(value["targets"]["candidates"][0]["observation"], "not_observed");
    assert_eq!(value["native_execution_attested"], false);
    assert_eq!(value["complete_reference_validation_qualified"], false);
    assert_eq!(output, original);
    Ok(())
}
