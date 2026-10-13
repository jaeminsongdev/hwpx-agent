//! Shared whole-graph/source oracle. No font availability or native execution.
use domain_ir::{DocumentGraph, DocumentGraphLimits, DocumentId, Properties};
use hwpx_package::document_import::{
    ImportedSourcePackage, SourceImportLimits,
    fields::semantics::catalog::{ImportedDocumentCatalog, fonts::ImportedDocumentFonts},
    forms::ImportedDocumentForms,
};
use sha2::{Digest as _, Sha256};
use std::{collections::BTreeSet, error::Error};
pub fn forms(bytes: &[u8], name: &str) -> Result<ImportedDocumentForms, Box<dyn Error>> {
    Ok(ImportedDocumentForms::import(
        ImportedSourcePackage::import(
            bytes,
            DocumentId::parse(name)?,
            Sha256::digest(bytes).into(),
            SourceImportLimits::default(),
        )?,
    )?)
}
pub fn verify_whole(
    forms: &ImportedDocumentForms,
    catalog: &ImportedDocumentCatalog<'_, '_, '_>,
    fonts: &ImportedDocumentFonts<'_, '_, '_, '_>,
) -> Result<(), Box<dyn Error>> {
    let declared: Vec<_> = catalog
        .character_catalog()
        .font_faces
        .iter()
        .flat_map(|group| group.fonts.iter())
        .collect();
    if declared.len() != fonts.definitions().len()
        || declared
            .iter()
            .zip(fonts.definitions())
            .any(|(old, new)| **old != new.declared)
    {
        return Err("whole original typed font declarations drift".into());
    }
    let ids: BTreeSet<_> = fonts
        .definitions()
        .iter()
        .map(|f| f.font_id.clone())
        .collect();
    if ids.len() != fonts.definitions().len() {
        return Err("font identities collide".into());
    }
    for definition in fonts.definitions() {
        let resolved = forms.source().resolve_anchor(&definition.source_anchor)?;
        if !resolved
            .element()
            .is_some_and(|e| e.name().local_name() == "font")
        {
            return Err("font source position drift".into());
        }
    }
    for link in fonts.links() {
        let resolved = forms.source().resolve_anchor(&link.font_reference_anchor)?;
        if !resolved
            .element()
            .is_some_and(|e| e.name().local_name() == "fontRef")
            || !fonts
                .definitions()
                .iter()
                .any(|f| f.font_id == link.font_id && f.language == link.language)
        {
            return Err("font language/source target drift".into());
        }
    }
    if fonts.links().len() != catalog.character_catalog().styles.len() * 7 {
        return Err("all seven language axes missing".into());
    }
    let mut draft = fonts.graph().clone().into_draft();
    draft.metadata = catalog.graph().clone().into_draft().metadata;
    draft.styles.retain(|style| !ids.contains(&style.style_id));
    for style in &mut draft.styles {
        let mut properties = Properties::new();
        for (key, value) in style
            .properties
            .iter()
            .filter(|(key, _)| *key != "source_font_links")
        {
            properties.insert(key, value.clone());
        }
        style.properties = properties;
    }
    if DocumentGraph::from_draft(draft, DocumentGraphLimits::default())? != *catalog.graph() {
        return Err("whole original catalog graph inverse drift".into());
    }
    Ok(())
}
