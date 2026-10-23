use domain_ir::{DocumentId, LogicalId, ReferenceAuxiliaryLimits};
use hwpx_package::{
    cross_reference_sdk::SdkCrossReferenceDisplay as Display,
    document_import::{
        ImportedSourcePackage, SourceImportLimits,
        reference_targets::sdk::{
            SourceCrossReferenceContext as Context, SourceCrossReferenceError as Error,
        },
        structure::ImportedDocumentStructure,
    },
};
use sha2::{Digest as _, Sha256};
use std::error::Error as StdError;
#[path = "support/document_import_field_fixture.rs"]
#[allow(dead_code)]
mod base;
#[path = "support/document_import_bookmark_fixture.rs"]
#[allow(dead_code)]
mod fixture;
type TestResult = Result<(), Box<dyn StdError>>;

fn source(
    body: &str,
    doc: &str,
) -> Result<(Vec<u8>, ImportedDocumentStructure), Box<dyn StdError>> {
    let bytes = base::package(&fixture::paragraph(body))?;
    let imported = ImportedDocumentStructure::import(ImportedSourcePackage::import(
        &bytes,
        DocumentId::parse(doc)?,
        Sha256::digest(&bytes).into(),
        SourceImportLimits::default(),
    )?)?;
    Ok((bytes, imported))
}
fn limits() -> Result<ReferenceAuxiliaryLimits, Box<dyn StdError>> {
    Ok(ReferenceAuxiliaryLimits::new(Default::default())?)
}

#[test]
fn candidate_retains_source_local_point_without_native_or_flat_flow_claim() -> TestResult {
    let (_, source) = source(
        &format!("<hp:t>text</hp:t>{}{}", fixture::marker("first"), fixture::marker("second")),
        "source-point",
    )?;
    let context = Context::import(&source, limits()?)?;
    for bookmark in source.bookmarks() {
        let candidate = context.prepare(&bookmark.reference_id, Display::Content, false)?;
        assert_eq!(candidate.source_paragraph_id(), &bookmark.paragraph_id);
        assert_eq!(candidate.source_point(), bookmark.source_point());
        assert_eq!(candidate.source_point().non_bookmark_inline_ordinal(), 1);
        let receipt = serde_json::to_string(candidate.receipt())?;
        assert!(!receipt.contains("run_ordinal"));
        assert!(!receipt.contains("source_point"));
        assert!(receipt.contains("\"requires_native_target_qualification\":true"));
    }
    Ok(())
}

#[test]
fn candidate_binds_source_section_order_without_serializing_coordinates_or_native_authority() -> TestResult {
    let (_, source) = source(&format!("{}{}", fixture::table(&fixture::marker("private table")),
        fixture::note(&fixture::marker("private note"))), "sdk-section-order")?;
    let context = Context::import(&source, limits()?)?;
    for (ordinal, bookmark) in source.bookmarks().iter().enumerate() {
        let candidate = context.prepare(&bookmark.reference_id, Display::Content, true)?;
        assert_eq!(candidate.source_section_location(), bookmark.section_location());
        assert_eq!(candidate.source_section_location().paragraph_ordinal(), (ordinal + 1) as u32);
        assert_eq!(candidate.source_section_location().source_paragraph_count(), 3);
        assert_eq!(candidate.source_section_location().section_id(), &source.graph().sections()[0].section_id);
        let receipt = serde_json::to_string(candidate.receipt())?;
        assert!(!receipt.contains("section_location") && !receipt.contains("paragraph_ordinal"));
        assert!(receipt.contains("\"requires_native_target_qualification\":true"));
        assert!(!format!("{:?}", candidate.source_section_location()).contains("private"));
    }
    Ok(())
}

#[test]
fn actual_source_name_is_bound_by_logical_id_and_receipt_never_exposes_name_or_command()
-> TestResult {
    let (bytes, source) = source(&fixture::marker("private source name"), "actual-source")?;
    let context = Context::import(&source, limits()?)?;
    let candidate = context.prepare(&source.bookmarks()[0].reference_id, Display::Content, true)?;
    assert_eq!(
        candidate.command_for_discovery(),
        "?private source name;6;2;1;0"
    );
    let json: serde_json::Value =
        serde_json::from_str(&serde_json::to_string(candidate.receipt())?)?;
    assert_eq!(json["requires_native_target_qualification"], true);
    assert_eq!(json["source"]["complete_reference_state_qualified"], false);
    for rendered in [
        format!("{candidate:?}"),
        format!("{:?}", candidate.receipt()),
        format!("{context:?}"),
        json.to_string(),
    ] {
        assert!(!rendered.contains("private source name"));
        assert!(!rendered.contains(candidate.command_for_discovery()));
    }
    assert_eq!(context.verify_source(&bytes)?.bookmark_targets, 1);
    Ok(())
}

#[test]
fn two_actual_duplicate_names_reject_either_identity_instead_of_picking_first() -> TestResult {
    let (_, source) = source(
        &format!("{}{}", fixture::marker("same"), fixture::marker("same")),
        "actual-source",
    )?;
    let context = Context::import(&source, limits()?)?;
    for bookmark in source.bookmarks() {
        assert!(matches!(
            context.prepare(&bookmark.reference_id, Display::Page, false),
            Err(Error::Ambiguous)
        ));
    }
    Ok(())
}

#[test]
fn forged_cross_document_and_changed_package_target_ids_cannot_be_rebound() -> TestResult {
    let (bytes, first) = source(&fixture::marker("same"), "first")?;
    let (_, other) = source(&fixture::marker("same"), "other")?;
    let (changed, changed_source) = source(&fixture::marker("changed"), "first")?;
    let context = Context::import(&first, limits()?)?;
    for id in [
        LogicalId::parse("forged-target")?,
        other.bookmarks()[0].reference_id.clone(),
        changed_source.bookmarks()[0].reference_id.clone(),
    ] {
        assert!(matches!(
            context.prepare(&id, Display::Page, false),
            Err(Error::Missing)
        ));
    }
    assert_eq!(context.verify_source(&changed), Err(Error::Binding));
    assert!(context.verify_source(&bytes).is_ok());
    Ok(())
}

#[test]
fn table_native_ids_and_note_instids_are_not_guessed_as_sdk_targets() -> TestResult {
    let (_, source) = source(
        &format!(
            "{}{}",
            fixture::table("<hp:t>table</hp:t>"),
            fixture::note("<hp:t>note</hp:t>")
        ),
        "actual-source",
    )?;
    let targets =
        hwpx_package::document_import::reference_targets::ImportedReferenceTargets::import(
            &source,
            limits()?,
        )?;
    let context = Context::import(&source, limits()?)?;
    assert_eq!(targets.targets().len(), 2);
    for target in targets.targets() {
        assert!(matches!(
            context.prepare(&target.logical_target_id, Display::Page, false),
            Err(Error::NativeTargetKindUnqualified)
        ));
    }
    Ok(())
}

#[test]
fn nested_table_note_bookmarks_remain_source_bound_without_fabricated_flat_coordinates()
-> TestResult {
    let (_, source) = source(
        &fixture::note(&fixture::table(&fixture::marker("nested"))),
        "actual-source",
    )?;
    let context = Context::import(&source, limits()?)?;
    let candidate = context.prepare(
        &source.bookmarks()[0].reference_id,
        Display::BookmarkName,
        false,
    )?;
    assert_eq!(candidate.command_for_discovery(), "?nested;6;1;0;0");
    assert!(!serde_json::to_string(candidate.receipt())?.contains("paragraph_ordinal"));
    Ok(())
}

#[test]
fn source_names_are_not_normalized_and_unsafe_command_encodings_reject() -> TestResult {
    let (_, imported) = source(
        &format!("{}{}", fixture::marker("e&#x301;"), fixture::marker("é")),
        "actual-source",
    )?;
    let context = Context::import(&imported, limits()?)?;
    for bookmark in imported.bookmarks() {
        assert_eq!(
            context
                .prepare(&bookmark.reference_id, Display::Content, false)?
                .command_for_discovery(),
            format!("?{};6;2;0;0", bookmark.name)
        );
        assert!(matches!(
            context.prepare(&bookmark.reference_id, Display::ObjectNumber, false),
            Err(Error::Command)
        ));
    }
    let (_, unsafe_source) = source(&fixture::marker("ambiguous;name"), "actual-source")?;
    assert!(matches!(
        Context::import(&unsafe_source, limits()?)?.prepare(
            &unsafe_source.bookmarks()[0].reference_id,
            Display::Page,
            false
        ),
        Err(Error::Command)
    ));
    Ok(())
}
