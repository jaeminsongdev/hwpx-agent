//! Exact locked actual documents, receipts/counts only; no native/COM/platform fonts.
use hwpx_package::document_import::fields::{
    ImportedDocumentFields,
    semantics::{
        ImportedDocumentFieldSemantics,
        catalog::{
            ImportedDocumentCatalog,
            fonts::{FontCatalogImportReceipt, ImportedDocumentFonts},
        },
    },
};
use serde::Serialize;
use std::error::Error;
#[path = "../tests/support/document_import_fonts_fixture.rs"]
mod fixture;
#[path = "../tests/support/document_import_settings_inputs.rs"]
mod inputs;
#[derive(Default, Serialize)]
struct Evidence {
    actual_packages: usize,
    source_font_groups: usize,
    source_font_definitions: usize,
    character_font_links: usize,
    whole_original_graph_inverses: usize,
    actual_receipts: Vec<FontCatalogImportReceipt>,
    platform_fonts_or_embedding_resolution_qualified: bool,
    native_activated: bool,
    p09_complete: bool,
}
fn main() -> Result<(), Box<dyn Error>> {
    let mut evidence = Evidence::default();
    for bytes in inputs::actual_corpus()? {
        let forms = fixture::forms(&bytes, "actual-font-source-probe")?;
        let fields = ImportedDocumentFields::import(&forms)?;
        let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
        let catalog = ImportedDocumentCatalog::import(&meanings)?;
        let fonts = ImportedDocumentFonts::import(&catalog)?;
        fixture::verify_whole(&forms, &catalog, &fonts)?;
        if fonts.verify_source(&bytes)? != *fonts.receipt() {
            return Err("whole actual fresh font receipt drift".into());
        }
        evidence.actual_packages += 1;
        evidence.source_font_groups += fonts.receipt().source_font_groups;
        evidence.source_font_definitions += fonts.definitions().len();
        evidence.character_font_links += fonts.links().len();
        evidence.whole_original_graph_inverses += 1;
        evidence.actual_receipts.push(fonts.receipt().clone());
    }
    if evidence.actual_packages != 36 || evidence.whole_original_graph_inverses != 36 {
        return Err("locked actual font corpus coverage drift".into());
    }
    println!("{}", serde_json::to_string(&evidence)?);
    Ok(())
}
