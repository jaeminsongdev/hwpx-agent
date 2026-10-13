#[path = "actual_import/field_ranges.rs"]
mod field_ranges;
#[path = "actual_import/field_semantics.rs"]
mod field_semantics;
#[path = "actual_import/formula_evaluation.rs"]
mod formula_evaluation;
#[path = "actual_import/source_bookmarks.rs"]
mod source_bookmarks;
#[path = "actual_import/source_catalog.rs"]
mod source_catalog;
#[path = "actual_import/source_security.rs"]
mod source_security;
#[path = "actual_import/source_settings.rs"]
mod source_settings;
#[path = "actual_import/source_notes.rs"]
mod source_notes;
#[path = "actual_import/source_fonts.rs"]
mod source_fonts;

use super::{StoredFixture, TestResult};
use artifact_service::{
    ArtifactKind, ArtifactMetadataRepository as _, AuthScope, ContentDigest, RequestContext,
    TenantId,
};
use domain_ir::{DocumentId, RevisionId};
use hwpx_agent_cli::{
    form_stored_provider::{
        StoredFormError, StoredFormProvider, actual_import::StoredActualFormImportError,
    },
    form_value_operation::full_document::{FullDocumentFormContext, FullDocumentFormError},
};
use hwpx_package::document_import::{
    ImportedSourcePackage, SourceImportLimits,
    forms::{
        ImportedDocumentForms,
        policies::{FormPolicyBindingError, FormPolicySourceBinding, PolicyBoundDocumentForms},
    },
};
use std::collections::BTreeSet;
use std::sync::atomic::Ordering;
#[path = "../../../hwpx-package/examples/document_import_form_policies_support/mod.rs"]
mod support;
use support::{explicit_test_policies, fixture_bytes, fixture_manifest};

#[test]
fn all_ten_actual_stored_results_import_without_caller_maps_and_preserve_whole_graphs() -> TestResult
{
    let (_, manifest) = fixture_manifest()?;
    let mut cases = 0;
    let mut forms = 0;
    for row in manifest["cases"].as_array().ok_or("cases")? {
        for kind in ["source", "output"] {
            let bytes = fixture_bytes(row["case"].as_str().ok_or("case")?, kind)?;
            let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
            let provider = stored.provider()?;
            let imported = provider.import_actual_forms(stored.head, 4)?;
            let direct = ImportedDocumentForms::import(ImportedSourcePackage::import(
                &bytes,
                DocumentId::parse("actual-form-document")?,
                *ContentDigest::of(&bytes).as_bytes(),
                SourceImportLimits::default(),
            )?)?;
            assert_eq!(imported.imported().graph(), direct.graph());
            assert_eq!(imported.imported().forms(), direct.forms());
            assert_eq!(imported.receipt().imported, *direct.receipt());
            assert_eq!(imported.receipt().source_artifact, stored.result);
            assert_eq!(imported.verify(&provider, 5)?, *imported.receipt());
            let binding = FormPolicySourceBinding::for_imported(imported.imported());
            let policies = explicit_test_policies(imported.imported());
            let bound = imported.bind_policies(&provider, &binding, &policies, 6)?;
            let original = PolicyBoundDocumentForms::bind(&direct, &binding, &policies)?;
            assert_eq!(bound.graph(), original.graph());
            assert_eq!(bound.state(), original.state());
            assert_eq!(bound.receipt().policy, *original.receipt());
            assert_eq!(
                bound.verify(&provider, &binding, &policies, 7)?,
                *bound.receipt()
            );
            assert!(matches!(
                FullDocumentFormContext::bind(
                    bound.graph(),
                    bound.graph().canonical_sha256()?,
                    *ContentDigest::of(&bytes).as_bytes(),
                    RevisionId::parse(stored.head.revision_id().ok_or("head")?.public_id())?
                ),
                Err(FullDocumentFormError::Projection)
            ));
            assert_eq!(
                stored
                    .revisions
                    .head(&stored.revision_context, stored.project, stored.branch)?,
                stored.head
            );
            let audits = stored.metadata.audit_events()?;
            assert_eq!(
                audits
                    .iter()
                    .filter(|e| e.event == "artifact.ingested")
                    .count(),
                2
            );
            assert!(
                audits
                    .iter()
                    .filter(|e| e.event == "artifact.download")
                    .count()
                    >= 4
            );
            forms += bound.state().controls().len();
            cases += 1;
        }
    }
    assert_eq!((cases, forms), (10, 50));
    Ok(())
}

#[test]
fn fresh_acl_revocation_blocks_import_verification_and_policy_binding() -> TestResult {
    let bytes = fixture_bytes("five-kinds", "source")?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let imported = provider.import_actual_forms(stored.head, 4)?;
    let binding = FormPolicySourceBinding::for_imported(imported.imported());
    let policies = explicit_test_policies(imported.imported());
    let bound = imported.bind_policies(&provider, &binding, &policies, 5)?;
    stored.artifacts.set_permissions(
        &stored.owner,
        stored.result,
        stored.reader.subject(),
        BTreeSet::new(),
        6,
    )?;
    assert!(matches!(
        provider.import_actual_forms(stored.head, 7),
        Err(StoredActualFormImportError::Source(
            StoredFormError::Artifact
        ))
    ));
    assert!(matches!(
        imported.verify(&provider, 7),
        Err(StoredActualFormImportError::Source(
            StoredFormError::Artifact
        ))
    ));
    assert!(matches!(
        imported.bind_policies(&provider, &binding, &policies, 7),
        Err(StoredActualFormImportError::Source(
            StoredFormError::Artifact
        ))
    ));
    assert!(matches!(
        bound.verify(&provider, &binding, &policies, 7),
        Err(StoredActualFormImportError::Source(
            StoredFormError::Artifact
        ))
    ));
    Ok(())
}

#[test]
fn actual_head_advance_invalidates_old_import_even_with_identical_result_bytes() -> TestResult {
    let bytes = fixture_bytes("actual", "source")?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let imported = provider.import_actual_forms(stored.head, 4)?;
    let binding = FormPolicySourceBinding::for_imported(imported.imported());
    let policies = explicit_test_policies(imported.imported());
    let bound = imported.bind_policies(&provider, &binding, &policies, 5)?;
    stored.advance()?;
    assert!(matches!(
        provider.import_actual_forms(stored.head, 6),
        Err(StoredActualFormImportError::Source(StoredFormError::Head))
    ));
    assert!(matches!(
        imported.verify(&provider, 6),
        Err(StoredActualFormImportError::Source(StoredFormError::Head))
    ));
    assert!(matches!(
        bound.verify(&provider, &binding, &policies, 6),
        Err(StoredActualFormImportError::Source(StoredFormError::Head))
    ));
    let head = stored
        .revisions
        .head(&stored.revision_context, stored.project, stored.branch)?;
    let fresh = provider.import_actual_forms(head, 7)?;
    assert_eq!(fresh.imported().graph(), imported.imported().graph());
    assert_eq!(fresh.receipt().head_generation, 2);
    assert_eq!(imported.receipt().head_generation, 1);
    Ok(())
}

#[test]
fn provider_document_branch_project_subject_and_tenant_cannot_rebind_import_or_policy() -> TestResult
{
    let bytes = fixture_bytes("actual", "source")?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let imported = provider.import_actual_forms(stored.head, 4)?;
    let binding = FormPolicySourceBinding::for_imported(imported.imported());
    let policies = explicit_test_policies(imported.imported());
    for variant in 0..5 {
        let tenant = if variant == 4 {
            TenantId::new(uuid::Uuid::from_u128(702))?
        } else {
            stored.reader.tenant_id()
        };
        let subject = if variant == 3 {
            stored.owner.subject()
        } else {
            stored.reader.subject()
        };
        let actor = RequestContext::new(tenant, subject, [AuthScope::DocumentRead]);
        let revision_actor = revision_service::RevisionRequestContext::new(tenant, subject);
        let project = if variant == 2 {
            revision_service::ProjectId::parse("prj_70000000000000000000000000000002")?
        } else {
            stored.project
        };
        let branch = if variant == 1 {
            revision_service::BranchId::parse("brn_70000000000000000000000000000002")?
        } else {
            stored.branch
        };
        let document = if variant == 0 {
            "other-document"
        } else {
            "actual-form-document"
        };
        let other = StoredFormProvider::bind(
            &stored.artifacts,
            &stored.revisions,
            &actor,
            &revision_actor,
            project,
            branch,
            DocumentId::parse(document)?,
        )?;
        assert!(matches!(
            imported.verify(&other, 5),
            Err(StoredActualFormImportError::Binding)
        ));
        assert!(matches!(
            imported.bind_policies(&other, &binding, &policies, 5),
            Err(StoredActualFormImportError::Binding)
        ));
    }
    Ok(())
}

#[test]
fn actual_aead_tamper_cannot_be_reclassified_as_an_importer_or_policy_failure() -> TestResult {
    let bytes = fixture_bytes("actual", "source")?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let imported = provider.import_actual_forms(stored.head, 4)?;
    let binding = FormPolicySourceBinding::for_imported(imported.imported());
    let policies = explicit_test_policies(imported.imported());
    let bound = imported.bind_policies(&provider, &binding, &policies, 5)?;
    stored.blobs.tamper.store(true, Ordering::SeqCst);
    assert!(matches!(
        provider.import_actual_forms(stored.head, 6),
        Err(StoredActualFormImportError::Source(
            StoredFormError::Artifact
        ))
    ));
    assert!(matches!(
        imported.verify(&provider, 6),
        Err(StoredActualFormImportError::Source(
            StoredFormError::Artifact
        ))
    ));
    assert!(matches!(
        bound.verify(&provider, &binding, &policies, 6),
        Err(StoredActualFormImportError::Source(
            StoredFormError::Artifact
        ))
    ));
    Ok(())
}

#[test]
fn wrong_artifact_role_unverified_and_invalid_package_stay_fail_closed() -> TestResult {
    let bytes = fixture_bytes("actual", "source")?;
    for (kind, unavailable) in [(ArtifactKind::Source, false), (ArtifactKind::Result, true)] {
        let stored = StoredFixture::new(&bytes, kind, unavailable)?;
        assert!(matches!(
            stored.provider()?.import_actual_forms(stored.head, 4),
            Err(StoredActualFormImportError::Source(
                StoredFormError::Artifact
            ))
        ));
    }
    let invalid = StoredFixture::new(b"not a HWPX document", ArtifactKind::Result, false)?;
    assert!(matches!(
        invalid.provider()?.import_actual_forms(invalid.head, 4),
        Err(StoredActualFormImportError::Import(_))
    ));
    Ok(())
}

#[test]
fn fresh_service_read_does_not_turn_stale_or_wrong_policy_into_authority() -> TestResult {
    let bytes = fixture_bytes("five-kinds", "source")?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let imported = provider.import_actual_forms(stored.head, 4)?;
    let binding = FormPolicySourceBinding::for_imported(imported.imported());
    let policies = explicit_test_policies(imported.imported());
    let bound = imported.bind_policies(&provider, &binding, &policies, 5)?;
    let mut wrong = binding.clone();
    wrong.source_package_sha256[0] ^= 1;
    assert!(matches!(
        imported.bind_policies(&provider, &wrong, &policies, 6),
        Err(StoredActualFormImportError::Policy(
            FormPolicyBindingError::Binding
        ))
    ));
    assert!(matches!(
        bound.verify(&provider, &wrong, &policies, 6),
        Err(StoredActualFormImportError::Policy(
            FormPolicyBindingError::Binding
        ))
    ));
    let mut wrong = policies.clone();
    wrong.swap(0, 1);
    assert!(matches!(
        imported.bind_policies(&provider, &binding, &wrong, 6),
        Err(StoredActualFormImportError::Policy(
            FormPolicyBindingError::Binding
        ))
    ));
    Ok(())
}

#[test]
fn no_form_stored_source_preserves_real_body_without_policy_attestation() -> TestResult {
    let bytes = hwpx_package::Hancom2020Vs0Builder::build("NO FORMS")?
        .with_verified_bytes(<[u8]>::to_vec)?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let imported = provider.import_actual_forms(stored.head, 4)?;
    assert!(imported.imported().forms().is_empty());
    assert_eq!(imported.receipt().imported.native_binding_sha256, None);
    assert_eq!(imported.verify(&provider, 5)?, *imported.receipt());
    assert!(matches!(
        imported.bind_policies(
            &provider,
            &FormPolicySourceBinding::for_imported(imported.imported()),
            &[],
            6
        ),
        Err(StoredActualFormImportError::Policy(
            FormPolicyBindingError::NoForms
        ))
    ));
    Ok(())
}

#[test]
fn debug_and_receipts_do_not_expose_raw_package_graph_or_policy_values() -> TestResult {
    let bytes = fixture_bytes("five-kinds", "source")?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let imported = provider.import_actual_forms(stored.head, 4)?;
    let binding = FormPolicySourceBinding::for_imported(imported.imported());
    let policies = explicit_test_policies(imported.imported());
    let bound = imported.bind_policies(&provider, &binding, &policies, 5)?;
    assert_eq!(
        format!("{imported:?}"),
        "StoredImportedDocumentForms(<redacted>)"
    );
    assert_eq!(format!("{bound:?}"), "StoredBoundFormPolicies(<redacted>)");
    let receipt = serde_json::to_value(bound.receipt())?;
    for field in [
        "bytes", "graph", "state", "policies", "tenant", "subject", "scope",
    ] {
        assert!(receipt.get(field).is_none());
    }
    assert!(bound.receipt().qualification.contains("not_policy_issuer"));
    Ok(())
}
