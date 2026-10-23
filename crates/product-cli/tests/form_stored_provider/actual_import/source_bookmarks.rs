use super::field_ranges::fixture as base;
use super::*;
use domain_ir::{DocumentGraph, DocumentGraphLimits, Properties, PropertyValue};
use hwpx_package::document_import::structure::bookmarks::{
    BOOKMARK_IMPORT_PROFILE, BOOKMARK_IMPORT_SCOPE,
};
#[path = "../../../../hwpx-package/tests/support/document_import_bookmark_fixture.rs"]
mod fixture;

#[test]
fn generated_bookmark_packages_use_original_authenticated_stored_read_and_direct_whole_graph()
-> TestResult {
    for bytes in fixture::generated()? {
        let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
        let provider = stored.provider()?;
        let imported = provider.import_actual_forms(stored.head, 4)?;
        let direct = base::forms(&bytes, "actual-form-document")?;
        assert_eq!(imported.bookmarks(), direct.bookmarks());
        assert_eq!(imported.imported().graph(), direct.graph());
        assert_eq!(imported.verify(&provider, 5)?, *imported.receipt());
        assert_eq!(
            stored
                .metadata
                .audit_events()?
                .iter()
                .filter(|v| v.event == "artifact.ingested")
                .count(),
            2
        );
        let fields = imported.import_field_ranges(&provider, 6)?;
        let meanings = fields.import_semantics(&provider, 7)?;
        assert_eq!(meanings.verify(&provider, 8)?, *meanings.receipt());
    }
    Ok(())
}

#[test]
fn source_name_selection_rechecks_acl_aead_head_and_duplicate_ambiguity() -> TestResult {
    let bytes = base::package(&fixture::paragraph(&fixture::marker("private bookmark")))?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let imported = provider.import_actual_forms(stored.head, 4)?;
    assert_eq!(
        imported.observed_bookmark_by_name(&provider, "private bookmark", 5)?,
        &imported.bookmarks()[0]
    );
    assert!(
        imported
            .observed_bookmark_by_name(&provider, "absent", 5)
            .is_err()
    );
    stored.blobs.tamper.store(true, Ordering::SeqCst);
    assert!(matches!(
        imported.observed_bookmark_by_name(&provider, "private bookmark", 6),
        Err(StoredActualFormImportError::Source(
            StoredFormError::Artifact
        ))
    ));
    stored.blobs.tamper.store(false, Ordering::SeqCst);
    stored.artifacts.set_permissions(
        &stored.owner,
        stored.result,
        stored.reader.subject(),
        BTreeSet::new(),
        7,
    )?;
    assert!(matches!(
        imported.observed_bookmark_by_name(&provider, "private bookmark", 8),
        Err(StoredActualFormImportError::Source(
            StoredFormError::Artifact
        ))
    ));
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let imported = provider.import_actual_forms(stored.head, 4)?;
    stored.advance()?;
    assert!(matches!(
        imported.observed_bookmark_by_name(&provider, "private bookmark", 5),
        Err(StoredActualFormImportError::Source(StoredFormError::Head))
    ));
    let bytes = base::package(&fixture::paragraph(&format!(
        "{}{}",
        fixture::marker("same"),
        fixture::marker("same")
    )))?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let imported = provider.import_actual_forms(stored.head, 4)?;
    assert_eq!(imported.bookmarks().len(), 2);
    assert!(
        imported
            .observed_bookmark_by_name(&provider, "same", 5)
            .is_err()
    );
    Ok(())
}

#[test]
fn bookmark_markers_individually_deny_full_context_even_without_old_partial_metadata() -> TestResult
{
    let bytes = base::package(&fixture::paragraph(&fixture::marker("point")))?;
    let forms = base::forms(&bytes, "actual-form-document")?;
    for (key, value) in [
        ("bookmark_import_profile", BOOKMARK_IMPORT_PROFILE),
        ("bookmark_import_scope", BOOKMARK_IMPORT_SCOPE),
    ] {
        let mut draft = forms.graph().clone().into_draft();
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
                RevisionId::parse("bookmark-revision")?
            ),
            Err(FullDocumentFormError::Projection)
        ));
    }
    Ok(())
}

#[test]
fn native_capture_is_only_negative_bookmark_evidence_and_stays_source_fresh() -> TestResult {
    let bytes = base::captured()?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let imported = provider.import_actual_forms(stored.head, 4)?;
    assert!(imported.bookmarks().is_empty());
    assert!(
        imported
            .observed_bookmark_by_name(&provider, "not present", 5)
            .is_err()
    );
    assert_eq!(imported.verify(&provider, 6)?, *imported.receipt());
    Ok(())
}

#[test]
fn all_scope5_substitutions_deny_fresh_observed_name_selection_on_the_existing_model() -> TestResult
{
    let bytes = base::package(&fixture::paragraph(&fixture::marker("point")))?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let imported = provider.import_actual_forms(stored.head, 4)?;
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
        assert!(matches!(
            imported.observed_bookmark_by_name(&other, "point", 5),
            Err(StoredActualFormImportError::Binding)
        ));
        assert!(matches!(
            imported.verify(&other, 5),
            Err(StoredActualFormImportError::Binding)
        ));
    }
    Ok(())
}
