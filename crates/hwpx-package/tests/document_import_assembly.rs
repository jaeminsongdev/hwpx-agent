use hwpx_package::document_import::fields::{
    ImportedDocumentFields,
    semantics::{
        ImportedDocumentFieldSemantics,
        catalog::{ImportedDocumentCatalog, assembly::ImportedDocumentAssembly},
    },
};
use std::error::Error;
#[path = "support/document_import_fonts_fixture.rs"]
mod fonts_fixture;
#[path = "support/document_import_formula_evaluation_fixture.rs"]
mod formula_fixture;
use formula_fixture::inputs;
#[path = "support/document_import_catalog_fixture.rs"]
mod mutation;
#[path = "support/document_import_assembly_fixture.rs"]
mod oracle;
type TestResult = Result<(), Box<dyn Error>>;
#[test]
fn numeric_and_formula_source_changes_rebind_values_and_nonnumeric_never_defaults() -> TestResult {
    let bytes = inputs::actual_corpus()?.remove(0);
    let forms = fonts_fixture::forms(&bytes, "assembly-formula")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    let catalog = ImportedDocumentCatalog::import(&meanings)?;
    let original = ImportedDocumentAssembly::import(&catalog)?;
    assert_eq!(original.formula_values().len(), 1);
    let numeric = formula_fixture::mutate_first_cell(&bytes, |cell| {
        formula_fixture::replace_first_text(cell, "900001")
    })?;
    let formula = formula_fixture::replace_formula(&bytes, "=900002")?;
    for changed in [numeric, formula] {
        assert!(original.verify_source(&changed).is_err());
        let forms = fonts_fixture::forms(&changed, "assembly-formula")?;
        let fields = ImportedDocumentFields::import(&forms)?;
        let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
        let catalog = ImportedDocumentCatalog::import(&meanings)?;
        let rebound = ImportedDocumentAssembly::import(&catalog)?;
        assert_ne!(
            original.formula_values()[0].value,
            rebound.formula_values()[0].value
        );
        oracle::verify_whole(&catalog, &meanings, &rebound)?;
        assert_eq!(rebound.verify_source(&changed)?, *rebound.receipt());
    }
    let nonnumeric = formula_fixture::mutate_first_cell(&bytes, |cell| {
        formula_fixture::replace_first_text(cell, "not-a-number")
    })?;
    let forms = fonts_fixture::forms(&nonnumeric, "assembly-formula")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    let catalog = ImportedDocumentCatalog::import(&meanings)?;
    assert!(matches!(ImportedDocumentAssembly::import(&catalog),
        Err(hwpx_package::document_import::fields::semantics::catalog::assembly::DocumentAssemblyError::Formulas(
            hwpx_package::document_import::fields::semantics::evaluation::SourceFormulaEvaluationError::Math(
                domain_ir::formula_evaluation::EvaluationError::MissingValue)))));
    Ok(())
}
#[test]
fn every_actual_package_retains_whole_branches_sidecars_and_fresh_identity() -> TestResult {
    let bytes = inputs::actual_corpus()?;
    assert_eq!(bytes.len(), 36);
    assert_eq!(&bytes[..26], mutation::actual_corpus()?.as_slice());
    let mut counts = (0, 0, 0);
    for bytes in bytes {
        let forms = fonts_fixture::forms(&bytes, "assembly-source")?;
        let fields = ImportedDocumentFields::import(&forms)?;
        let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
        let catalog = ImportedDocumentCatalog::import(&meanings)?;
        let before = catalog.graph().clone();
        let assembly = ImportedDocumentAssembly::import(&catalog)?;
        oracle::verify_whole(&catalog, &meanings, &assembly)?;
        let fonts = hwpx_package::document_import::fields::semantics::catalog::fonts::ImportedDocumentFonts::import(&catalog)?;
        fonts_fixture::verify_whole(&forms, &catalog, &fonts)?;
        assert_eq!(assembly.verify_source(&bytes)?, *assembly.receipt());
        assert_eq!(catalog.graph(), &before);
        assert!(!assembly.inventory().activation_allowed());
        for action in [
            hwpx_package::ActivationKind::Ole,
            hwpx_package::ActivationKind::Multimedia,
            hwpx_package::ActivationKind::EmbeddedExecutable,
            hwpx_package::ActivationKind::ScriptMacro,
            hwpx_package::ActivationKind::FormCommand,
            hwpx_package::ActivationKind::ExternalLink,
        ] {
            assert!(assembly.require_activation(action).is_err());
        }
        counts.0 += assembly.font_definitions().len();
        counts.1 += assembly.formula_values().len();
        counts.2 += assembly.native_forms().len();
    }
    assert_eq!(counts, (504, 16, 50));
    Ok(())
}
#[test]
fn changed_font_and_page_source_cannot_reuse_assembly() -> TestResult {
    let bytes = inputs::actual_corpus()?.remove(0);
    let forms = fonts_fixture::forms(&bytes, "assembly-fresh")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    let catalog = ImportedDocumentCatalog::import(&meanings)?;
    let assembly = ImportedDocumentAssembly::import(&catalog)?;
    for (part, tag, key, value) in [
        (
            "Contents/header.xml",
            "font",
            "face",
            "ASSEMBLY-PRIVATE-MARKER",
        ),
        ("Contents/section0.xml", "pagePr", "width", "60000"),
    ] {
        let changed = mutation::change_attribute(&bytes, part, tag, key, value)?;
        assert!(assembly.verify_source(&changed).is_err());
    }
    assert_eq!(
        format!("{assembly:?}"),
        "ImportedDocumentAssembly(<redacted>)"
    );
    let receipt = serde_json::to_string(assembly.receipt())?;
    assert!(!receipt.contains("ASSEMBLY-PRIVATE-MARKER"));
    assert!(!receipt.contains("declared"));
    Ok(())
}
#[test]
fn malformed_original_reader_input_is_not_a_partial_success_fallback() -> TestResult {
    let bytes = inputs::actual_corpus()?.remove(0);
    for (part, tag, key, value) in [
        ("Contents/header.xml", "fontRef", "hangul", "4294967295"),
        ("Contents/header.xml", "head", "secCnt", "999"),
        ("Contents/section0.xml", "pagePr", "width", "0"),
    ] {
        let changed = mutation::change_attribute(&bytes, part, tag, key, value)?;
        let forms = fonts_fixture::forms(&changed, "assembly-invalid")?;
        let fields = ImportedDocumentFields::import(&forms)?;
        let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
        match ImportedDocumentCatalog::import(&meanings) {
            Err(_) => (),
            Ok(catalog) => assert!(ImportedDocumentAssembly::import(&catalog).is_err()),
        }
    }
    Ok(())
}
