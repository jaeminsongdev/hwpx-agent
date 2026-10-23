use domain_ir::{DocumentGraph, DocumentGraphLimits, DocumentId, Properties, RevisionId};
use hwpx_agent_cli::form_value_operation::full_document::{
    FullDocumentFormContext, FullDocumentFormError,
};
use hwpx_package::document_import::{
    ImportedSourcePackage, SourceImportLimits, forms::ImportedDocumentForms,
};
use sha2::{Digest as _, Sha256};
use std::{error::Error, path::PathBuf};

type TestResult = Result<(), Box<dyn Error>>;

#[test]
fn actual_five_kind_source_backed_forms_are_still_partial_product_input() -> TestResult {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../fixtures/target-build/p09-42-product-form-values-01/output");
    let bytes = std::fs::read(root.join("five-kinds-source.hwpx"))?;
    assert_eq!(
        hex::encode(Sha256::digest(&bytes)),
        "5e64b52de6db2fa7a028a80757c2480b223de74bf9aedc6d0333741f96d83de7"
    );
    assert_eq!(bytes.len(), 16405);
    let package_sha = Sha256::digest(&bytes).into();
    let imported = ImportedDocumentForms::import(ImportedSourcePackage::import(
        &bytes,
        DocumentId::parse("observed-product-form-input")?,
        package_sha,
        SourceImportLimits::default(),
    )?)?;
    assert_eq!(imported.receipt().form_controls, 6);
    for only_profile in [None, Some(true), Some(false)] {
        let mut draft = imported.graph().clone().into_draft();
        match only_profile {
            Some(true) => {
                let mut metadata = Properties::new();
                for (key, value) in draft.metadata.iter() {
                    if key != "scope" {
                        metadata.insert(key, value.clone());
                    }
                }
                draft.metadata = metadata;
            }
            Some(false) => draft.source_profile = None,
            None => {}
        }
        let graph = DocumentGraph::from_draft(draft, DocumentGraphLimits::default())?;
        assert!(matches!(
            FullDocumentFormContext::bind(
                &graph,
                graph.canonical_sha256()?,
                package_sha,
                RevisionId::parse("baseline")?
            ),
            Err(FullDocumentFormError::Projection)
        ));
    }
    assert_eq!(imported.verify_source(&bytes)?, *imported.receipt());
    // Independently qualify the two new observed-form markers after removing
    // BOTH P67 markers, without claiming marker removal creates authority.
    for keep in ["native_form_import_profile", "native_form_import_scope"] {
        let mut draft = imported.graph().clone().into_draft();
        draft.source_profile = None;
        let mut metadata = Properties::new();
        for (key, value) in draft.metadata.iter() {
            if key == keep
                || ![
                    "scope",
                    "native_form_import_profile",
                    "native_form_import_scope",
                ]
                .contains(&key)
            {
                metadata.insert(key, value.clone());
            }
        }
        draft.metadata = metadata;
        let graph = DocumentGraph::from_draft(draft, DocumentGraphLimits::default())?;
        assert!(matches!(
            FullDocumentFormContext::bind(
                &graph,
                graph.canonical_sha256()?,
                package_sha,
                RevisionId::parse("baseline")?
            ),
            Err(FullDocumentFormError::Projection)
        ));
    }
    Ok(())
}
