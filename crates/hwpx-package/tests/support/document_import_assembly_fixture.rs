//! Independent whole-output comparison and graph inverse for the qualified assembly.
use domain_ir::{DocumentGraph, DocumentGraphLimits, Properties};
use hwpx_package::document_import::fields::semantics::{
    ImportedDocumentFieldSemantics,
    catalog::{
        ImportedDocumentCatalog,
        assembly::ImportedDocumentAssembly,
        fonts::ImportedDocumentFonts,
        security::{ImportedDocumentActiveSecurity, settings::ImportedDocumentSectionSettings},
    },
    evaluation::ImportedSourceFormulaEvaluation,
};
use std::error::Error;
pub fn verify_whole(
    catalog: &ImportedDocumentCatalog<'_, '_, '_>,
    meanings: &ImportedDocumentFieldSemantics<'_, '_>,
    assembly: &ImportedDocumentAssembly<'_, '_, '_, '_>,
) -> Result<(), Box<dyn Error>> {
    let fonts = ImportedDocumentFonts::import(catalog)?;
    let security = ImportedDocumentActiveSecurity::import(catalog)?;
    let settings = ImportedDocumentSectionSettings::import(&security)?;
    let formulas = ImportedSourceFormulaEvaluation::import(meanings)?;
    verify_components(assembly, &fonts, &security, &settings, &formulas)
}
pub fn verify_components(
    assembly: &ImportedDocumentAssembly<'_, '_, '_, '_>,
    fonts: &ImportedDocumentFonts<'_, '_, '_, '_>,
    security: &ImportedDocumentActiveSecurity<'_, '_, '_, '_>,
    settings: &ImportedDocumentSectionSettings<'_, '_, '_, '_, '_>,
    formulas: &ImportedSourceFormulaEvaluation<'_, '_, '_>,
) -> Result<(), Box<dyn Error>> {
    if assembly.font_definitions() != fonts.definitions()
        || assembly.font_links() != fonts.links()
        || assembly.inventory() != security.inventory()
        || assembly.active_controls() != security.controls()
        || assembly.active_resources() != security.resources()
        || assembly.native_forms() != security.native_forms()
        || assembly.section_settings() != settings.settings()
        || assembly.formula_values() != formulas.values()
        || assembly.formula_source_bindings() != formulas.source_bindings()
        || assembly.receipt().fonts != *fonts.receipt()
        || assembly.receipt().security != *security.receipt()
        || assembly.receipt().settings != *settings.receipt()
        || assembly.receipt().formulas != *formulas.receipt()
    {
        return Err("whole original branch output/receipt lost during assembly".into());
    }
    let mut inverse = assembly.graph().clone().into_draft();
    let expected = settings.graph().clone().into_draft();
    if inverse.styles != fonts.graph().clone().into_draft().styles {
        return Err("font graph branch lost".into());
    }
    inverse.styles = expected.styles;
    let mut metadata = Properties::new();
    for (key, value) in inverse.metadata.iter().filter(|(key, _)| {
        ![
            "font_catalog_import_profile",
            "font_catalog_import_scope",
            "document_assembly_profile",
            "document_assembly_scope",
            "source_formula_sidecar_sha256",
        ]
        .contains(key)
    }) {
        metadata.insert(key, value.clone());
    }
    inverse.metadata = metadata;
    if DocumentGraph::from_draft(inverse, DocumentGraphLimits::default())? != *settings.graph() {
        return Err("whole security/settings graph inverse differs".into());
    }
    Ok(())
}
