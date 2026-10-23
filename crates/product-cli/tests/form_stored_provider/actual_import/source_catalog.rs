use super::field_ranges::fixture;
use super::*;
use domain_ir::{DocumentGraph, DocumentGraphLimits, Properties, PropertyValue};
use hwpx_package::document_import::fields::{
    ImportedDocumentFields,
    semantics::{
        ImportedDocumentFieldSemantics,
        catalog::{CATALOG_IMPORT_PROFILE, CATALOG_IMPORT_SCOPE, ImportedDocumentCatalog},
    },
};
use std::{collections::BTreeSet, sync::atomic::Ordering};

#[test]
fn actual_catalog_matches_direct_whole_graph_with_no_ingest_or_head_write() -> TestResult {
    let bytes = fixture::captured()?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let fields = source.import_field_ranges(&provider, 5)?;
    let meanings = fields.import_semantics(&provider, 6)?;
    let catalog = meanings.import_catalog(&provider, 7)?;
    let direct_forms = fixture::forms(&bytes, "actual-form-document")?;
    let direct_fields = ImportedDocumentFields::import(&direct_forms)?;
    let direct_meanings = ImportedDocumentFieldSemantics::import(&direct_fields)?;
    let direct = ImportedDocumentCatalog::import(&direct_meanings)?;
    assert_eq!(catalog.graph(), direct.graph());
    assert_eq!(catalog.definitions(), direct.definitions());
    assert_eq!(catalog.uses(), direct.uses());
    assert_eq!(catalog.receipt().catalog, *direct.receipt());
    assert_eq!(catalog.verify(&provider, 8)?, *catalog.receipt());
    assert_eq!(catalog.receipt().catalog.named_styles, 22);
    assert_eq!(
        stored
            .metadata
            .audit_events()?
            .iter()
            .filter(|v| v.event == "artifact.ingested")
            .count(),
        2
    );
    assert_eq!(
        stored
            .revisions
            .head(&stored.revision_context, stored.project, stored.branch)?,
        stored.head
    );
    Ok(())
}
#[test]
fn catalog_rechecks_aead_acl_and_head_on_creation_and_cached_verification() -> TestResult {
    let bytes = fixture::captured()?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let fields = source.import_field_ranges(&provider, 5)?;
    let meanings = fields.import_semantics(&provider, 6)?;
    let catalog = meanings.import_catalog(&provider, 7)?;
    stored.blobs.tamper.store(true, Ordering::SeqCst);
    assert!(catalog.verify(&provider, 8).is_err());
    assert!(meanings.import_catalog(&provider, 8).is_err());
    stored.blobs.tamper.store(false, Ordering::SeqCst);
    stored.artifacts.set_permissions(
        &stored.owner,
        stored.result,
        stored.reader.subject(),
        BTreeSet::new(),
        9,
    )?;
    assert!(catalog.verify(&provider, 10).is_err());
    assert!(meanings.import_catalog(&provider, 10).is_err());
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let fields = source.import_field_ranges(&provider, 5)?;
    let meanings = fields.import_semantics(&provider, 6)?;
    let catalog = meanings.import_catalog(&provider, 7)?;
    stored.advance()?;
    assert!(catalog.verify(&provider, 8).is_err());
    assert!(meanings.import_catalog(&provider, 8).is_err());
    Ok(())
}
#[test]
fn all_five_scope_substitutions_reject_existing_catalog_binding() -> TestResult {
    let stored = StoredFixture::new(&fixture::captured()?, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let fields = source.import_field_ranges(&provider, 5)?;
    let meanings = fields.import_semantics(&provider, 6)?;
    let catalog = meanings.import_catalog(&provider, 7)?;
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
            "different-document"
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
        assert!(catalog.verify(&other, 8).is_err());
        assert!(meanings.import_catalog(&other, 8).is_err());
    }
    Ok(())
}
#[test]
fn each_catalog_partial_marker_denies_full_context_independently() -> TestResult {
    let bytes = fixture::captured()?;
    let forms = fixture::forms(&bytes, "actual-form-document")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    let catalog = ImportedDocumentCatalog::import(&meanings)?;
    for (key, value) in [
        ("style_catalog_import_profile", CATALOG_IMPORT_PROFILE),
        ("style_catalog_import_scope", CATALOG_IMPORT_SCOPE),
    ] {
        let mut draft = catalog.graph().clone().into_draft();
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
                catalog.receipt().source_package_sha256,
                RevisionId::parse("catalog-revision")?
            ),
            Err(FullDocumentFormError::Projection)
        ));
    }
    Ok(())
}
