//! Locked actual source receipts/counts only; no UI/COM/native execution.
use hwpx_package::document_import::fields::{
    ImportedDocumentFields,
    semantics::{
        ImportedDocumentFieldSemantics,
        catalog::{
            ImportedDocumentCatalog,
            assembly::{DocumentAssemblyReceipt, ImportedDocumentAssembly},
        },
    },
};
use serde::Serialize;
use std::error::Error;
#[path = "../tests/support/document_import_fonts_fixture.rs"]
mod fonts_fixture;
#[path = "../tests/support/document_import_settings_inputs.rs"]
mod inputs;
#[path = "../tests/support/document_import_assembly_fixture.rs"]
mod oracle;
#[derive(Default, Serialize)]
struct Evidence {
    actual_packages: usize,
    whole_graph_inverses: usize,
    font_definitions: usize,
    font_links: usize,
    section_settings: usize,
    native_form_bindings: usize,
    formula_values: usize,
    formula_source_bindings: usize,
    receipts: Vec<DocumentAssemblyReceipt>,
    full_import_qualified: bool,
    native_executed: bool,
    p09_complete: bool,
}
fn main() -> Result<(), Box<dyn Error>> {
    let mut evidence = Evidence::default();
    for bytes in inputs::actual_corpus()? {
        let forms = fonts_fixture::forms(&bytes, "assembly-source-probe")?;
        let fields = ImportedDocumentFields::import(&forms)?;
        let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
        let catalog = ImportedDocumentCatalog::import(&meanings)?;
        let assembly = ImportedDocumentAssembly::import(&catalog)?;
        oracle::verify_whole(&catalog, &meanings, &assembly)?;
        let fonts = hwpx_package::document_import::fields::semantics::catalog::fonts::ImportedDocumentFonts::import(&catalog)?;
        fonts_fixture::verify_whole(&forms, &catalog, &fonts)?;
        if assembly.verify_source(&bytes)? != *assembly.receipt() {
            return Err("actual whole fresh assembly drift".into());
        }
        evidence.actual_packages += 1;
        evidence.whole_graph_inverses += 1;
        evidence.font_definitions += assembly.font_definitions().len();
        evidence.font_links += assembly.font_links().len();
        evidence.section_settings += assembly.section_settings().len();
        evidence.native_form_bindings += assembly.native_forms().len();
        evidence.formula_values += assembly.formula_values().len();
        evidence.formula_source_bindings += assembly.formula_source_bindings().len();
        evidence.receipts.push(assembly.receipt().clone());
    }
    if evidence.actual_packages != 36 || evidence.whole_graph_inverses != 36 {
        return Err("actual source coverage drift".into());
    }
    println!("{}", serde_json::to_string(&evidence)?);
    Ok(())
}
