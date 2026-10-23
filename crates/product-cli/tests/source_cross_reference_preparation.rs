use domain_ir::{DocumentId, LogicalId, ReferenceAuxiliaryLimitConfig, ReferenceAuxiliaryLimits};
use hwpx_agent_cli::reference_validation_product::{
    ReferenceValidationProductOperation as Product,
    source_crossref::{
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
fn input() -> Result<(Vec<u8>, LogicalId), Box<dyn std::error::Error>> {
    let bytes = base::package(&fixture::paragraph(&fixture::marker("private batch name")))?;
    let source = ImportedDocumentStructure::import(ImportedSourcePackage::import(
        &bytes,
        DocumentId::parse("source-batch")?,
        Sha256::digest(&bytes).into(),
        SourceImportLimits::default(),
    )?)?;
    Ok((bytes, source.bookmarks()[0].reference_id.clone()))
}
fn prepare(
    bytes: &[u8],
    selections: &[Selection],
    reference_limits: ReferenceAuxiliaryLimits,
) -> Result<
    hwpx_agent_cli::reference_validation_product::source_crossref::SourceCrossReferencePreparation,
    Error,
> {
    Product::prepare_source_crossref_discovery(
        bytes,
        DocumentId::parse("source-batch").map_err(|_| Error::Source)?,
        Sha256::digest(bytes).into(),
        SourceImportLimits::default(),
        reference_limits,
        selections,
    )
}
#[test]
fn actual_source_batch_prepares_eight_variants_with_one_boundary_verification_and_private_receipts()
-> TestResult {
    let (bytes, id) = input()?;
    let mut selections = Vec::new();
    for display in [
        Display::Page,
        Display::BookmarkName,
        Display::Content,
        Display::RelativePosition,
    ] {
        for hyperlink in [false, true] {
            selections.push(Selection {
                target_id: id.clone(),
                display,
                hyperlink,
            });
        }
    }
    let original = bytes.clone();
    let prepared = prepare(&bytes, &selections, limits()?)?;
    assert_eq!(prepared.candidates_for_discovery().len(), 8);
    prepared.verify_source(&bytes)?;
    let json = prepared.canonical_receipts_json(limits()?)?;
    let value: serde_json::Value = serde_json::from_slice(&json)?;
    assert_eq!(value["status"], "native_execution_not_run");
    assert_eq!(value["candidates"].as_array().ok_or("candidates")?.len(), 8);
    assert!(!String::from_utf8_lossy(&json).contains("private batch name"));
    assert!(!format!("{prepared:?}").contains("private batch name"));
    assert!(!format!("{:?}", selections[0]).contains(id.as_str()));
    assert_eq!(bytes, original);
    Ok(())
}
#[test]
fn duplicate_empty_missing_and_partially_invalid_batches_return_no_preparation() -> TestResult {
    let (bytes, id) = input()?;
    let valid = Selection {
        target_id: id,
        display: Display::Page,
        hyperlink: false,
    };
    assert!(matches!(
        prepare(&bytes, &[], limits()?),
        Err(Error::Selection)
    ));
    assert!(matches!(
        prepare(&bytes, &[valid.clone(), valid.clone()], limits()?),
        Err(Error::Selection)
    ));
    let invalid = Selection {
        target_id: LogicalId::parse("forged")?,
        display: Display::Page,
        hyperlink: false,
    };
    assert!(matches!(
        prepare(&bytes, &[valid, invalid], limits()?),
        Err(Error::Target)
    ));
    Ok(())
}
#[test]
fn aggregate_receipt_command_budgets_and_original_source_bounds_are_not_bypassed() -> TestResult {
    let (bytes, id) = input()?;
    let selections = [
        Selection {
            target_id: id.clone(),
            display: Display::Page,
            hyperlink: false,
        },
        Selection {
            target_id: id,
            display: Display::Content,
            hyperlink: true,
        },
    ];
    let one = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {
        items_per_kind: 1,
        ..Default::default()
    })?;
    assert!(matches!(
        prepare(&bytes, &selections, one),
        Err(Error::Limit)
    ));
    let prepared = prepare(&bytes, &selections, limits()?)?;
    let first = &prepared.candidates_for_discovery()[0];
    let single_budget =
        256 + serde_json::to_vec(first.receipt())?.len() + first.command_for_discovery().len() + 1;
    let aggregate = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {
        input_bytes: 1,
        output_bytes: single_budget,
        ..Default::default()
    })?;
    assert!(prepare(&bytes, &selections[..1], aggregate).is_ok());
    assert!(matches!(
        prepare(&bytes, &selections, aggregate),
        Err(Error::Limit)
    ));
    let small = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {
        input_bytes: 1,
        output_bytes: 512,
        ..Default::default()
    })?;
    assert!(matches!(
        prepared.canonical_receipts_json(small),
        Err(Error::Limit)
    ));
    Ok(())
}
#[test]
fn wrong_digest_wrong_document_and_fresh_source_drift_reject() -> TestResult {
    let (bytes, id) = input()?;
    let selections = [Selection {
        target_id: id,
        display: Display::Page,
        hyperlink: false,
    }];
    assert!(matches!(
        Product::prepare_source_crossref_discovery(
            &bytes,
            DocumentId::parse("source-batch")?,
            [0; 32],
            SourceImportLimits::default(),
            limits()?,
            &selections
        ),
        Err(Error::Binding)
    ));
    assert!(matches!(
        Product::prepare_source_crossref_discovery(
            &bytes,
            DocumentId::parse("other-document")?,
            Sha256::digest(&bytes).into(),
            SourceImportLimits::default(),
            limits()?,
            &selections
        ),
        Err(Error::Target)
    ));
    let prepared = prepare(&bytes, &selections, limits()?)?;
    let changed = base::package(&fixture::paragraph(&fixture::marker("changed")))?;
    assert!(matches!(
        prepared.verify_source(&changed),
        Err(Error::Binding)
    ));
    Ok(())
}

#[test]
fn actual_product_preparation_keeps_source_section_order_for_all_eight_candidates() -> TestResult {
    let bytes = base::package(&format!("{}{}", fixture::paragraph("<hp:t>prefix</hp:t>"),
        fixture::paragraph(&fixture::table(&fixture::marker("private prepared target")))))?;
    let source = ImportedDocumentStructure::import(ImportedSourcePackage::import(&bytes,
        DocumentId::parse("source-batch")?, Sha256::digest(&bytes).into(), SourceImportLimits::default())?)?;
    let mut requests = Vec::new();
    for display in [Display::Page, Display::BookmarkName, Display::Content, Display::RelativePosition] {
        for hyperlink in [false, true] {
            requests.push(Selection { target_id: source.bookmarks()[0].reference_id.clone(), display, hyperlink });
        }
    }
    let prepared = prepare(&bytes, &requests, limits()?)?;
    for candidate in prepared.candidates_for_discovery() {
        assert_eq!(candidate.source_section_location(), source.bookmarks()[0].section_location());
        assert_eq!(candidate.source_section_location().paragraph_ordinal(), 2);
        assert_eq!(candidate.source_section_location().source_paragraph_count(), 3);
    }
    assert_eq!(prepared.candidates_for_discovery().len(), 8);
    let receipts = String::from_utf8(prepared.canonical_receipts_json(limits()?)?)?;
    assert!(!receipts.contains("section_location") && !receipts.contains("private prepared target"));
    prepared.verify_source(&bytes)?;
    Ok(())
}
