use super::{StoredFixture, TestResult};
use artifact_service::{ArtifactKind, ArtifactMetadataRepository as _, ContentDigest};
use domain_ir::{DocumentGraph, DocumentGraphLimits, Properties, PropertyValue, RevisionId};
use hwpx_agent_cli::{
    form_stored_provider::{
        StoredFormError,
        actual_import::{StoredActualFormImportError, field_ranges::StoredFieldRangeImportError},
    },
    form_value_operation::full_document::{FullDocumentFormContext, FullDocumentFormError},
};
use hwpx_package::document_import::fields::{
    FIELD_RANGE_IMPORT_PROFILE, FIELD_RANGE_IMPORT_SCOPE, ImportedDocumentFields,
};
use std::{collections::BTreeSet, sync::atomic::Ordering};
#[path = "../../../../hwpx-package/tests/support/document_import_field_fixture.rs"]
mod fixture;

fn synthetic() -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    fixture::package(
        "<hp:p id='1'><hp:run><hp:ctrl><hp:fieldBegin id='1' type='DATE'/></hp:ctrl><hp:t>A</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='1'/></hp:ctrl></hp:run></hp:p>",
    )
}

#[test]
fn cached_field_ranges_cannot_rebind_document_branch_project_subject_or_tenant() -> TestResult {
    use artifact_service::{AuthScope, RequestContext, TenantId};
    use domain_ir::DocumentId;
    use hwpx_agent_cli::form_stored_provider::StoredFormProvider;
    let stored = StoredFixture::new(&synthetic()?, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let fields = source.import_field_ranges(&provider, 5)?;
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
            fields.verify(&other, 6),
            Err(StoredFieldRangeImportError::Source(
                StoredActualFormImportError::Binding
            ))
        ));
        assert!(matches!(
            source.import_field_ranges(&other, 6),
            Err(StoredFieldRangeImportError::Source(
                StoredActualFormImportError::Binding
            ))
        ));
    }
    Ok(())
}
#[test]
fn captured_stored_result_field_ranges_match_whole_direct_graph_without_ingest_or_head_change()
-> TestResult {
    let bytes = fixture::captured()?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let imported = source.import_field_ranges(&provider, 5)?;
    let direct_source = fixture::forms(&bytes, "actual-form-document")?;
    let direct = ImportedDocumentFields::import(&direct_source)?;
    assert_eq!(imported.graph(), direct.graph());
    assert_eq!(imported.fields(), direct.fields());
    assert_eq!(imported.receipt().fields, *direct.receipt());
    assert_eq!(imported.receipt().fields.field_ranges, 1);
    assert_eq!(imported.verify(&provider, 6)?, *imported.receipt());
    assert_eq!(
        stored
            .revisions
            .head(&stored.revision_context, stored.project, stored.branch)?,
        stored.head
    );
    assert_eq!(
        stored
            .metadata
            .audit_events()?
            .iter()
            .filter(|v| v.event == "artifact.ingested")
            .count(),
        2
    );
    let receipt = serde_json::to_string(imported.receipt())?;
    assert!(!receipt.contains("http") && !receipt.contains("Command"));
    Ok(())
}
#[test]
fn revoked_source_acl_denies_new_range_import_and_cached_range_verification() -> TestResult {
    let stored = StoredFixture::new(&synthetic()?, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let fields = source.import_field_ranges(&provider, 5)?;
    stored.artifacts.set_permissions(
        &stored.owner,
        stored.result,
        stored.reader.subject(),
        BTreeSet::new(),
        6,
    )?;
    for denied in [
        source
            .import_field_ranges(&provider, 7)
            .map(|v| v.receipt().clone()),
        fields.verify(&provider, 7),
    ] {
        assert!(matches!(
            denied,
            Err(StoredFieldRangeImportError::Source(
                StoredActualFormImportError::Source(StoredFormError::Artifact)
            ))
        ));
    }
    Ok(())
}
#[test]
fn actual_aead_tamper_is_original_service_failure_not_field_projection_failure() -> TestResult {
    let stored = StoredFixture::new(&synthetic()?, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let fields = source.import_field_ranges(&provider, 5)?;
    stored.blobs.tamper.store(true, Ordering::SeqCst);
    assert!(matches!(
        fields.verify(&provider, 6),
        Err(StoredFieldRangeImportError::Source(
            StoredActualFormImportError::Source(StoredFormError::Artifact)
        ))
    ));
    assert!(source.import_field_ranges(&provider, 6).is_err());
    Ok(())
}
#[test]
fn advanced_head_invalidates_cached_source_and_range_even_when_result_bytes_equal() -> TestResult {
    let stored = StoredFixture::new(&synthetic()?, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let fields = source.import_field_ranges(&provider, 5)?;
    stored.advance()?;
    assert!(matches!(
        fields.verify(&provider, 6),
        Err(StoredFieldRangeImportError::Source(
            StoredActualFormImportError::Source(StoredFormError::Head)
        ))
    ));
    assert!(source.import_field_ranges(&provider, 6).is_err());
    Ok(())
}
#[test]
fn each_new_partial_marker_independently_denies_full_product_without_old_markers() -> TestResult {
    let bytes = synthetic()?;
    let source = fixture::forms(&bytes, "actual-form-document")?;
    let fields = ImportedDocumentFields::import(&source)?;
    for (key, value) in [
        ("field_range_import_profile", FIELD_RANGE_IMPORT_PROFILE),
        ("field_range_import_scope", FIELD_RANGE_IMPORT_SCOPE),
    ] {
        let mut draft = fields.graph().clone().into_draft();
        draft.source_profile = None;
        draft.metadata = Properties::new();
        draft
            .metadata
            .insert(key, PropertyValue::Text(value.into()));
        let graph = DocumentGraph::from_draft(draft, DocumentGraphLimits::default())?;
        assert!(matches!(
            FullDocumentFormContext::bind(
                &graph,
                graph.canonical_sha256()?,
                *ContentDigest::of(&bytes).as_bytes(),
                RevisionId::parse("field-ranges-revision")?
            ),
            Err(FullDocumentFormError::Projection)
        ));
    }
    Ok(())
}
#[test]
fn stored_range_debug_and_receipt_do_not_disclose_cached_field_content() -> TestResult {
    let bytes = synthetic()?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let fields = source.import_field_ranges(&provider, 5)?;
    assert!(!format!("{fields:?}").contains("field-ranges-revision"));
    let json = serde_json::to_value(fields.receipt())?;
    assert!(json["fields"].get("native_header_attributes").is_none());
    assert!(json["fields"].get("inline_start").is_none());
    assert_eq!(fields.verify(&provider, 6)?, *fields.receipt());
    Ok(())
}
