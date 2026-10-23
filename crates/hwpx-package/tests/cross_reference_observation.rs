use domain_ir::{DocumentId, ReferenceAuxiliaryLimitConfig, ReferenceAuxiliaryLimits};
use hwpx_package::{
    cross_reference_sdk::SdkCrossReferenceDisplay as Display,
    document_import::{
        ImportedSourcePackage, SourceImportLimits,
        fields::{
            ImportedDocumentFields,
            cross_reference_observation::{
                CrossReferenceCommandObservations as Observations,
                CrossReferenceObservationError as ObsError,
            },
        },
        reference_targets::sdk::{SourceBoundCrossReferenceCandidate, SourceCrossReferenceContext},
        structure::ImportedDocumentStructure,
    },
};
use sha2::{Digest as _, Sha256};
#[path = "support/document_import_field_fixture.rs"]
#[allow(dead_code)]
mod base;
#[path = "support/document_import_bookmark_fixture.rs"]
#[allow(dead_code)]
mod fixture;
type TestResult = Result<(), Box<dyn std::error::Error>>;
fn limits() -> Result<ReferenceAuxiliaryLimits, Box<dyn std::error::Error>> {
    Ok(ReferenceAuxiliaryLimits::new(Default::default())?)
}
fn candidates(
    displays: &[Display],
) -> Result<Vec<SourceBoundCrossReferenceCandidate>, Box<dyn std::error::Error>> {
    let bytes = base::package(&fixture::paragraph(&fixture::marker("private&amp;target")))?;
    let source = ImportedDocumentStructure::import(ImportedSourcePackage::import(
        &bytes,
        DocumentId::parse("observation")?,
        Sha256::digest(&bytes).into(),
        SourceImportLimits::default(),
    )?)?;
    let context = SourceCrossReferenceContext::import(&source, limits()?)?;
    displays
        .iter()
        .map(|d| {
            context
                .prepare(&source.bookmarks()[0].reference_id, *d, false)
                .map_err(Into::into)
        })
        .collect()
}
fn escape(value: &str) -> String {
    value.replace('&', "&amp;").replace('<', "&lt;")
}
fn leaf(name: &str, value: &str) -> String {
    format!(
        "<hp:stringParam name='{name}'>{}</hp:stringParam>",
        escape(value)
    )
}
fn field(id: u32, kind: &str, count: usize, children: &str) -> String {
    format!(
        "<hp:ctrl><hp:fieldBegin id='{id}' type='{kind}'><hp:parameters cnt='{count}'>{children}</hp:parameters></hp:fieldBegin></hp:ctrl><hp:t>private cached display</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='{id}'/></hp:ctrl>"
    )
}
fn observe(
    body: &str,
    expected: &[SourceBoundCrossReferenceCandidate],
) -> Result<serde_json::Value, Box<dyn std::error::Error>> {
    let bytes = base::package(&fixture::paragraph(body))?;
    let forms = base::forms(&bytes, "observation")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let observations = Observations::inspect(&fields, expected, limits()?)?;
    let json = observations.canonical_json(limits()?)?;
    assert!(!format!("{observations:?}").contains("private"));
    assert!(!String::from_utf8_lossy(&json).contains("private"));
    assert_eq!(fields.verify_source(&bytes)?, *fields.receipt());
    Ok(serde_json::from_slice(&json)?)
}

#[test]
fn arbitrary_parameter_key_and_entity_decoding_are_observed_not_native_semantics() -> TestResult {
    let expected = candidates(&[Display::Content])?;
    let report = observe(
        &field(
            1,
            "CROSSREF",
            1,
            &leaf(
                "unverified-key-not-Command",
                expected[0].command_for_discovery(),
            ),
        ),
        &expected,
    )?;
    assert_eq!(report["status"], "source_observation_only");
    assert_eq!(report["crossref_fields"], 1);
    assert_eq!(
        report["candidates"][0]["observation"],
        "single_decoded_leaf_observed"
    );
    for key in [
        "parameter_key_semantics_qualified",
        "native_execution_attested",
        "causal_insertion_or_preservation_proved",
        "complete_reference_validation_qualified",
    ] {
        assert_eq!(report[key], false);
    }
    Ok(())
}

#[test]
fn zero_crossrefs_and_matching_strings_in_other_field_kinds_are_not_success() -> TestResult {
    let expected = candidates(&[Display::Page])?;
    for body in [
        "<hp:t>body</hp:t>".into(),
        field(
            1,
            "HYPERLINK",
            1,
            &leaf("unknown", expected[0].command_for_discovery()),
        ),
    ] {
        let report = observe(&body, &expected)?;
        assert_eq!(report["crossref_fields"], 0);
        assert_eq!(report["candidates"][0]["observation"], "not_observed");
        assert_eq!(report["complete_reference_validation_qualified"], false);
    }
    Ok(())
}

#[test]
fn duplicate_leaves_in_one_or_two_fields_are_ambiguous_without_first_match_selection() -> TestResult
{
    let expected = candidates(&[Display::Page])?;
    let one = leaf("unknown", expected[0].command_for_discovery());
    for (body, fields) in [
        (
            field(
                1,
                "CROSSREF",
                2,
                &format!(
                    "{one}{}",
                    leaf("second-key", expected[0].command_for_discovery())
                ),
            ),
            1,
        ),
        (
            format!(
                "{}{}",
                field(1, "CROSSREF", 1, &one),
                field(2, "CROSSREF", 1, &one)
            ),
            2,
        ),
    ] {
        let report = observe(&body, &expected)?;
        assert_eq!(
            report["candidates"][0]["observation"],
            "ambiguous_decoded_leaves"
        );
        assert_eq!(report["candidates"][0]["matching_leaves"], 2);
        assert_eq!(report["candidates"][0]["matching_fields"], fields);
        assert!(report["candidates"][0]["only_matching_field_reference_sha256"].is_null());
    }
    Ok(())
}

#[test]
fn two_candidates_sharing_one_source_field_are_not_two_distinct_native_results() -> TestResult {
    let expected = candidates(&[Display::Page, Display::Content])?;
    let leaves = expected
        .iter()
        .enumerate()
        .map(|(n, c)| leaf(&format!("unverified-{n}"), c.command_for_discovery()))
        .collect::<String>();
    let report = observe(&field(1, "CROSSREF", 2, &leaves), &expected)?;
    for row in report["candidates"].as_array().ok_or("candidates")? {
        assert_eq!(row["matching_leaves"], 1);
        assert_eq!(row["shares_field_with_other_candidates"], true);
        assert_eq!(row["observation"], "ambiguous_decoded_leaves");
        assert!(row["only_matching_field_reference_sha256"].is_null());
    }
    Ok(())
}

#[test]
fn nonstring_and_comment_payloads_remain_opaque_not_concatenated_commands() -> TestResult {
    let expected = candidates(&[Display::Page])?;
    let value = escape(expected[0].command_for_discovery());
    let payload = format!(
        "<hp:stringParam name='x'>{}<!--comment-->{}</hp:stringParam><hp:integerParam name='n'>7</hp:integerParam>",
        &value[..1],
        &value[1..]
    );
    let report = observe(&field(1, "CROSSREF", 2, &payload), &expected)?;
    assert_eq!(report["opaque_parameter_children"], 2);
    assert_eq!(report["candidates"][0]["observation"], "not_observed");
    Ok(())
}

#[test]
fn missing_parameters_and_exact_whitespace_are_not_repaired_or_normalized() -> TestResult {
    let expected = candidates(&[Display::Page])?;
    let bare = "<hp:ctrl><hp:fieldBegin id='1' type='CROSSREF'/></hp:ctrl><hp:t>cache</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='1'/></hp:ctrl>";
    let report = observe(bare, &expected)?;
    assert_eq!(report["crossrefs_without_parameters"], 1);
    let report = observe(
        &field(
            1,
            "CROSSREF",
            1,
            &leaf("x", &format!(" {} ", expected[0].command_for_discovery())),
        ),
        &expected,
    )?;
    assert_eq!(report["candidates"][0]["observation"], "not_observed");
    Ok(())
}

#[test]
fn duplicate_candidates_text_work_and_output_limits_fail_closed() -> TestResult {
    let expected = candidates(&[Display::Page, Display::Page])?;
    let bytes = base::package(&fixture::paragraph(&field(
        1,
        "CROSSREF",
        1,
        &leaf("x", expected[0].command_for_discovery()),
    )))?;
    let forms = base::forms(&bytes, "observation")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    assert!(matches!(
        Observations::inspect(&fields, &expected, limits()?),
        Err(ObsError::Duplicate)
    ));
    let tight = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {
        text_bytes: 1,
        ..Default::default()
    })?;
    assert!(matches!(
        Observations::inspect(&fields, &expected[..1], tight),
        Err(ObsError::Limit)
    ));
    let one_byte = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {
        input_bytes: 1,
        output_bytes: 1,
        ..Default::default()
    })?;
    let result = Observations::inspect(&fields, &expected[..1], limits()?)?;
    assert!(matches!(
        result.canonical_json(one_byte),
        Err(ObsError::Limit)
    ));
    Ok(())
}

#[test]
fn crossref_in_nonspine_header_is_rejected_instead_of_silent_absence() -> TestResult {
    use std::io::{Cursor, Read, Write};
    use zip::{ZipArchive, ZipWriter, write::SimpleFileOptions};
    let expected = candidates(&[Display::Page])?;
    let bytes = base::package(&fixture::paragraph("<hp:t>body</hp:t>"))?;
    let mut input = ZipArchive::new(Cursor::new(bytes))?;
    let mut output = ZipWriter::new(Cursor::new(Vec::new()));
    for index in 0..input.len() {
        let mut entry = input.by_index(index)?;
        let name = entry.name().to_owned();
        let mut value = Vec::new();
        entry.read_to_end(&mut value)?;
        if name == "Contents/header.xml" {
            value = format!(
                "<head xmlns:hp='http://www.hancom.co.kr/hwpml/2011/paragraph'>{}</head>",
                fixture::paragraph(&field(
                    1,
                    "CROSSREF",
                    1,
                    &leaf("x", expected[0].command_for_discovery())
                ))
            )
            .into_bytes();
        }
        output.start_file(
            name,
            SimpleFileOptions::default().compression_method(zip::CompressionMethod::Stored),
        )?;
        output.write_all(&value)?;
    }
    let forms = base::forms(&output.finish()?.into_inner(), "observation")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    assert!(matches!(
        Observations::inspect(&fields, &expected, limits()?),
        Err(ObsError::Coverage)
    ));
    Ok(())
}
