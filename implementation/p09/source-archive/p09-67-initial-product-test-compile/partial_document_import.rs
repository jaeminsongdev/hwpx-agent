use std::error::Error;

use domain_ir::{DocumentGraph, DocumentGraphLimits, DocumentId, PropertyValue, RevisionId};
use hwpx_agent_cli::form_value_operation::full_document::{
    FullDocumentFormContext, FullDocumentFormError,
};
use hwpx_package::{
    Hancom2020Vs0Builder,
    document_import::{
        ImportedSourcePackage, SourceImportLimits,
        structure::{ImportedDocumentStructure, STRUCTURE_IMPORT_PROFILE, STRUCTURE_IMPORT_SCOPE},
    },
};
use sha2::{Digest as _, Sha256};

type TestResult = Result<(), Box<dyn Error>>;

#[test]
fn real_source_backed_partial_body_import_is_not_full_document_product_input() -> TestResult {
    let native = Hancom2020Vs0Builder::build("본문 원본 연결")?;
    let bytes = native.bytes();
    let package_sha256: [u8; 32] = Sha256::digest(bytes).into();
    let source = ImportedSourcePackage::import(
        bytes,
        DocumentId::parse("actual-body-import")?,
        package_sha256,
        SourceImportLimits::default(),
    )?;
    let imported = ImportedDocumentStructure::import(source)?;
    assert!(imported.receipt().paragraphs > 0);
    assert!(matches!(
        FullDocumentFormContext::bind(
            imported.graph(),
            imported.receipt().graph_sha256,
            package_sha256,
            RevisionId::parse("baseline")?
        ),
        Err(FullDocumentFormError::Projection)
    ));
    assert_eq!(imported.verify_source(bytes)?, *imported.receipt());
    Ok(())
}

#[test]
fn partial_marker_guard_is_independent_for_source_profile_and_scope() -> TestResult {
    let native = Hancom2020Vs0Builder::build("partial marker contract")?;
    let sha256: [u8; 32] = Sha256::digest(native.bytes()).into();
    let imported = ImportedDocumentStructure::import(ImportedSourcePackage::import(
        native.bytes(),
        DocumentId::parse("marker-contract")?,
        sha256,
        SourceImportLimits::default(),
    )?)?;
    let draft = imported.graph().clone().into_draft();
    assert_eq!(
        draft
            .source_profile
            .as_ref()
            .map(domain_ir::LogicalId::as_str),
        Some(STRUCTURE_IMPORT_PROFILE)
    );
    for profile_only in [true, false] {
        let mut changed = draft.clone();
        if profile_only {
            let mut metadata = domain_ir::Properties::new();
            for (key, value) in changed.metadata.iter() {
                if key != "scope" {
                    metadata.insert(key, value.clone());
                }
            }
            changed.metadata = metadata;
        } else {
            changed.source_profile = None;
        }
        if !profile_only {
            assert!(changed.metadata.iter().any(|(key, value)| key == "scope"
                && matches!(value, PropertyValue::Text(scope) if scope == STRUCTURE_IMPORT_SCOPE)));
        }
        let graph = DocumentGraph::from_draft(changed, DocumentGraphLimits::default())?;
        assert!(matches!(
            FullDocumentFormContext::bind(
                &graph,
                graph.canonical_sha256()?,
                sha256,
                RevisionId::parse("baseline")?
            ),
            Err(FullDocumentFormError::Projection)
        ));
    }
    Ok(())
}
