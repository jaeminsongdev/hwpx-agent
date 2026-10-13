use super::*;
use crate::document_import::{
    ImportedSourcePackage, SourceImportLimits,
    fields::{
        ImportedDocumentFields,
        semantics::{ImportedDocumentFieldSemantics, catalog::ImportedDocumentCatalog},
    },
    forms::ImportedDocumentForms,
};
use domain_ir::DocumentId;
use sha2::{Digest as _, Sha256};
mod fixture {
    use crate as hwpx_package;
    include!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/tests/support/document_import_review_assembly_fixture.rs"
    ));
}
type TestResult = Result<(), Box<dyn std::error::Error>>;
fn forms(bytes: &[u8], name: &str) -> Result<ImportedDocumentForms, Box<dyn std::error::Error>> {
    Ok(ImportedDocumentForms::import(
        ImportedSourcePackage::import(
            bytes,
            DocumentId::parse(name)?,
            Sha256::digest(bytes).into(),
            SourceImportLimits::default(),
        )?,
    )?)
}
#[test]
fn every_cached_review_raw_typed_use_graph_and_receipt_mutation_is_rejected() -> TestResult {
    let bytes = fixture::package(&fixture::markers("PRIVATE-BODY"))?;
    let forms = forms(&bytes, "review-cache")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    let catalog = ImportedDocumentCatalog::import(&meanings)?;
    for fault in 0..8 {
        let mut assembly = super::super::ImportedDocumentAssembly::import(&catalog)?;
        match fault {
            0 => {
                assembly.state.review_bodies.pop();
            }
            1 => {
                assembly.state.review_bodies[0].source.body = None;
            }
            2 => {
                assembly.state.review_bodies[0].catalog_body = None;
            }
            3 => {
                assembly.state.review_bodies[0].catalog_uses.clear();
            }
            4 => assembly.state.receipt.reviews.body_observations_sha256[0] ^= 1,
            5 => assembly.state.receipt.review_catalog_bodies_sha256[0] ^= 1,
            6 => {
                let mut draft = assembly.state.graph.clone().into_draft();
                draft.review[0]
                    .properties
                    .insert("cache_tamper", PropertyValue::Boolean(true));
                assembly.state.graph =
                    DocumentGraph::from_draft(draft, DocumentGraphLimits::default())?;
            }
            _ => {
                assembly
                    .state
                    .receipt
                    .reviews
                    .native_author_time_binding_verified = true
            }
        }
        assert!(matches!(
            assembly.verify_source(&bytes),
            Err(Error::Binding)
        ));
    }
    Ok(())
}
#[test]
fn foreign_original_fields_and_duplicate_or_changed_graph_effects_are_rejected() -> TestResult {
    let bytes = fixture::package(&fixture::markers("BODY"))?;
    let first = forms(&bytes, "first-review")?;
    let other = forms(&bytes, "other-review")?;
    let fields = ImportedDocumentFields::import(&first)?;
    assert!(ImportedDocumentReviewBodies::import_bound_fields(&other, &fields).is_err());
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    let catalog = ImportedDocumentCatalog::import(&meanings)?;
    let review = ReviewAssembly::import(&catalog)?;
    let mut duplicate = catalog.graph().clone().into_draft();
    duplicate.metadata.insert(
        "review_body_import_profile",
        PropertyValue::Text("conflict".into()),
    );
    assert!(matches!(
        review.merge(
            &catalog,
            DocumentGraph::from_draft(duplicate, DocumentGraphLimits::default())?
        ),
        Err(Error::Binding)
    ));
    let mut wrong = ReviewAssembly::import(&catalog)?;
    let mut draft = wrong.source_graph.clone().into_draft();
    draft
        .metadata
        .insert("unknown_effect", PropertyValue::Boolean(true));
    wrong.source_graph = DocumentGraph::from_draft(draft, DocumentGraphLimits::default())?;
    assert!(wrong.require_binding(&catalog).is_err());
    Ok(())
}
