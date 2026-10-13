use super::*;
use crate::document_import::{
    ImportedSourcePackage, SourceImportLimits,
    fields::{ImportedDocumentFields, semantics::ImportedDocumentFieldSemantics},
    forms::ImportedDocumentForms,
};
use domain_ir::DocumentId;
use sha2::{Digest as _, Sha256};
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
fn cached_whole_graph_font_sidecar_and_receipt_tampering_are_each_rejected() -> TestResult {
    let bytes =
        crate::Hancom2020Vs0Builder::build("ASSEMBLY-TEST")?.with_verified_bytes(<[u8]>::to_vec)?;
    let forms = forms(&bytes, "assembly-cache")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    let catalog = ImportedDocumentCatalog::import(&meanings)?;
    for fault in 0..5 {
        let mut assembly = ImportedDocumentAssembly::import(&catalog)?;
        match fault {
            0 => assembly.state.fonts[0].declared.face = "CACHE-TAMPER".into(),
            1 => {
                assembly.state.font_links.pop();
            }
            2 => {
                assembly.state.settings.pop();
            }
            3 => {
                let mut draft = assembly.state.graph.clone().into_draft();
                draft
                    .metadata
                    .insert("cache_tamper", PropertyValue::Boolean(true));
                assembly.state.graph =
                    DocumentGraph::from_draft(draft, DocumentGraphLimits::default())?;
            }
            _ => {
                assembly
                    .state
                    .receipt
                    .formulas
                    .values_and_source_bindings_sha256[0] ^= 1
            }
        }
        assert!(matches!(
            assembly.verify_source(&bytes),
            Err(DocumentAssemblyError::Binding)
        ));
    }
    Ok(())
}
#[test]
fn foreign_document_branch_and_duplicate_metadata_are_rejected() -> TestResult {
    let bytes =
        crate::Hancom2020Vs0Builder::build("ASSEMBLY-TEST")?.with_verified_bytes(<[u8]>::to_vec)?;
    let first = forms(&bytes, "assembly-first")?;
    let first_fields = ImportedDocumentFields::import(&first)?;
    let first_meanings = ImportedDocumentFieldSemantics::import(&first_fields)?;
    let catalog = ImportedDocumentCatalog::import(&first_meanings)?;
    let fonts = ImportedDocumentFonts::import(&catalog)?;
    let formulas = ImportedSourceFormulaEvaluation::import(&first_meanings)?;
    let second = forms(&bytes, "assembly-other")?;
    let second_fields = ImportedDocumentFields::import(&second)?;
    let second_meanings = ImportedDocumentFieldSemantics::import(&second_fields)?;
    let other_catalog = ImportedDocumentCatalog::import(&second_meanings)?;
    let security = ImportedDocumentActiveSecurity::import(&other_catalog)?;
    let settings = ImportedDocumentSectionSettings::import(&security)?;
    assert!(matches!(
        combine(&catalog, &fonts, &settings, formulas.receipt()),
        Err(DocumentAssemblyError::Binding)
    ));
    let mut properties = Properties::new();
    properties.insert("original", PropertyValue::Text("keep".into()));
    let before = properties.clone();
    assert!(matches!(
        insert_new(
            &mut properties,
            "original",
            PropertyValue::Text("overwrite".into())
        ),
        Err(DocumentAssemblyError::Binding)
    ));
    assert!(properties == before);
    Ok(())
}
