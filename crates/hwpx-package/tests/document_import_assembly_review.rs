use domain_ir::{DocumentGraph, DocumentGraphLimits, DocumentId, Flow, Inline, Node};
use hwpx_package::document_import::{
    ImportedSourcePackage, SourceImportLimits,
    fields::{
        ImportedDocumentFields,
        semantics::{
            ImportedDocumentFieldSemantics,
            catalog::{
                ImportedDocumentCatalog,
                assembly::ImportedDocumentAssembly,
                fonts::ImportedDocumentFonts,
                security::{
                    ImportedDocumentActiveSecurity, settings::ImportedDocumentSectionSettings,
                },
            },
        },
    },
    forms::ImportedDocumentForms,
    structure::review::ImportedDocumentReviewBodies,
};
use sha2::{Digest as _, Sha256};
use std::error::Error;
#[path = "support/document_import_review_assembly_fixture.rs"]
mod fixture;
type TestResult = Result<(), Box<dyn Error>>;
fn forms(bytes: &[u8]) -> Result<ImportedDocumentForms, Box<dyn Error>> {
    Ok(ImportedDocumentForms::import(
        ImportedSourcePackage::import(
            bytes,
            DocumentId::parse("review-assembly")?,
            Sha256::digest(bytes).into(),
            SourceImportLimits::default(),
        )?,
    )?)
}
fn visible(flow: &Flow) -> String {
    flow.children
        .iter()
        .filter_map(|n| {
            if let Node::Paragraph(p) = n {
                Some(
                    p.inlines
                        .iter()
                        .filter_map(|i| {
                            if let Inline::Text { text } = i {
                                Some(text.as_str())
                            } else {
                                None
                            }
                        })
                        .collect::<String>(),
                )
            } else {
                None
            }
        })
        .collect()
}
#[test]
fn assembled_reviews_keep_whole_original_source_and_existing_style_links_not_visible_cache()
-> TestResult {
    let bytes = fixture::package(&fixture::markers("PRIVATE-BODY"))?;
    let forms = forms(&bytes)?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    let catalog = ImportedDocumentCatalog::import(&meanings)?;
    let assembly = ImportedDocumentAssembly::import(&catalog)?;
    let direct = ImportedDocumentReviewBodies::import(&forms)?;
    assert_eq!(assembly.review_bodies().len(), 2);
    assert_eq!(assembly.receipt().reviews, *direct.receipt());
    for (assembled, raw) in assembly.review_bodies().iter().zip(direct.observations()) {
        assert_eq!(&assembled.source, raw);
        assert_eq!(assembled.catalog_uses.len(), 1);
        assert!(assembled.catalog_uses[0].named_style.is_some());
        assert!(assembled.catalog_uses[0].paragraph_property.is_some());
        assert!(
            assembled.catalog_uses[0].runs[0]
                .character_property
                .is_some()
        );
        assert_eq!(
            visible(assembled.catalog_body.as_ref().ok_or("body")?),
            visible(raw.body.as_ref().ok_or("body")?)
        );
        assert!(
            forms
                .source()
                .resolve_anchor(&assembled.catalog_uses[0].source_anchor)?
                .element()
                .is_some()
        );
    }
    let main = visible(&assembly.graph().sections()[0].body);
    assert!(main.contains("MAIN") && main.contains("VISIBLE-CACHE"));
    assert!(!main.contains("PRIVATE-BODY") && !main.contains("HIDDEN-REVIEW"));
    assert!(
        !assembly
            .receipt()
            .reviews
            .native_author_time_binding_verified
    );
    assert_eq!(assembly.verify_source(&bytes)?, *assembly.receipt());
    let fonts = ImportedDocumentFonts::import(&catalog)?;
    let security = ImportedDocumentActiveSecurity::import(&catalog)?;
    let settings = ImportedDocumentSectionSettings::import(&security)?;
    let mut inverse = assembly.graph().clone().into_draft();
    let original = settings.graph().clone().into_draft();
    assert_eq!(inverse.styles, fonts.graph().clone().into_draft().styles);
    inverse.styles.clone_from(&original.styles);
    inverse.review.clone_from(&original.review);
    inverse.metadata.clone_from(&original.metadata);
    assert_eq!(
        DocumentGraph::from_draft(inverse, DocumentGraphLimits::default())?,
        *settings.graph()
    );
    assert_eq!(assembly.font_definitions(), fonts.definitions());
    assert_eq!(assembly.active_controls(), security.controls());
    assert_eq!(assembly.section_settings(), settings.settings());
    Ok(())
}
#[test]
fn wrong_body_style_references_and_malformed_body_never_fall_back_to_opaque_assembly() -> TestResult
{
    let good = fixture::markers("BODY");
    for changed in [
        good.replace("styleIDRef='0'", "styleIDRef='999999'"),
        good.replace("paraPrIDRef='0'", "paraPrIDRef='999999'"),
        good.replace("charPrIDRef='0'", "charPrIDRef='999999'"),
        good.replace("id='101'", "id='invalid'"),
    ] {
        let bytes = fixture::package(&changed)?;
        let forms = forms(&bytes)?;
        let fields = ImportedDocumentFields::import(&forms)?;
        let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
        let catalog = ImportedDocumentCatalog::import(&meanings)?;
        assert!(ImportedDocumentAssembly::import(&catalog).is_err());
    }
    Ok(())
}
#[test]
fn review_body_change_and_style_change_invalidate_whole_cached_assembly_without_source_writes()
-> TestResult {
    let bytes = fixture::package(&fixture::markers("FIRST"))?;
    let forms = forms(&bytes)?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    let catalog = ImportedDocumentCatalog::import(&meanings)?;
    let assembly = ImportedDocumentAssembly::import(&catalog)?;
    for changed in [
        fixture::markers("SECOND"),
        fixture::markers("FIRST").replace("charPrIDRef='0'", "charPrIDRef='999999'"),
    ] {
        assert!(
            assembly
                .verify_source(&fixture::package(&changed)?)
                .is_err()
        );
    }
    assert_eq!(assembly.verify_source(&bytes)?, *assembly.receipt());
    let debug = format!(
        "{assembly:?} {:?} {:?}",
        assembly.review_bodies(),
        assembly.receipt()
    );
    assert!(
        !debug.contains("FIRST") && !debug.contains("HIDDEN-REVIEW") && !debug.contains("<hp:")
    );
    Ok(())
}
