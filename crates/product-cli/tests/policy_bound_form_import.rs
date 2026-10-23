use domain_ir::{DocumentGraph, DocumentGraphLimits, DocumentId, Properties, RevisionId};
use hwpx_agent_cli::form_value_operation::full_document::{
    FullDocumentFormContext, FullDocumentFormError,
};
use hwpx_package::document_import::{
    ImportedSourcePackage, SourceImportLimits,
    forms::{
        ImportedDocumentForms,
        policies::{FormPolicySourceBinding, PolicyBoundDocumentForms},
    },
};
use sha2::{Digest as _, Sha256};
use std::error::Error;
#[path = "../../hwpx-package/examples/document_import_form_policies_support/mod.rs"]
mod support;

#[test]
fn actual_policy_bound_form_graph_cannot_be_promoted_to_full_product_input()
-> Result<(), Box<dyn Error>> {
    let bytes = support::fixture_bytes("five-kinds", "source")?;
    let sha = Sha256::digest(&bytes).into();
    let imported = ImportedDocumentForms::import(ImportedSourcePackage::import(
        &bytes,
        DocumentId::parse("policy-product-test")?,
        sha,
        SourceImportLimits::default(),
    )?)?;
    let binding = FormPolicySourceBinding::for_imported(&imported);
    let policies = support::explicit_test_policies(&imported);
    let bound = PolicyBoundDocumentForms::bind(&imported, &binding, &policies)?;
    // Each new marker independently denies even after ALL four earlier partial
    // markers are removed. Removal does not establish importer/issuer authority.
    for keep in [
        None,
        Some("native_form_policy_profile"),
        Some("native_form_policy_scope"),
    ] {
        let mut draft = bound.graph().clone().into_draft();
        if let Some(keep) = keep {
            draft.source_profile = None;
            let mut metadata = Properties::new();
            for (key, value) in draft.metadata.iter() {
                if ![
                    "scope",
                    "native_form_import_profile",
                    "native_form_import_scope",
                    "native_form_policy_profile",
                    "native_form_policy_scope",
                ]
                .contains(&key)
                    || key == keep
                {
                    metadata.insert(key, value.clone());
                }
            }
            draft.metadata = metadata;
        }
        let graph = DocumentGraph::from_draft(draft, DocumentGraphLimits::default())?;
        assert!(matches!(
            FullDocumentFormContext::bind(
                &graph,
                graph.canonical_sha256()?,
                sha,
                RevisionId::parse("baseline")?
            ),
            Err(FullDocumentFormError::Projection)
        ));
    }
    assert_eq!(
        bound.verify_source(&bytes, &binding, &policies)?,
        *bound.receipt()
    );
    Ok(())
}
