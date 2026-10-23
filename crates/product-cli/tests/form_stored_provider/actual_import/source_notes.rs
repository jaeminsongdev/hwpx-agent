use super::field_ranges::fixture;
use super::*;
use domain_ir::{DocumentGraph, DocumentGraphLimits, Properties, PropertyValue};
use hwpx_package::document_import::structure::notes::{NOTE_IMPORT_PROFILE, NOTE_IMPORT_SCOPE};
#[path = "../../../../hwpx-package/tests/support/document_import_note_fixture.rs"]
mod notes;

#[test]
fn nine_actual_note_packages_use_original_stored_source_and_whole_direct_graph() -> TestResult {
    for input in notes::actual_inputs()? {
        let stored = StoredFixture::new(&input.bytes, ArtifactKind::Result, false)?;
        let provider = stored.provider()?;
        let imported = provider.import_actual_forms(stored.head, 4)?;
        let direct = fixture::forms(&input.bytes, "actual-form-document")?;
        assert_eq!(imported.notes(), direct.notes());
        assert_eq!(imported.notes().len(), input.expected_notes);
        assert_eq!(imported.imported().graph(), direct.graph());
        assert_eq!(imported.verify(&provider, 5)?, *imported.receipt());
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
        assert!(matches!(
            FullDocumentFormContext::bind(
                imported.imported().graph(),
                imported.imported().graph().canonical_sha256()?,
                *ContentDigest::of(&input.bytes).as_bytes(),
                RevisionId::parse("notes-revision")?
            ),
            Err(FullDocumentFormError::Projection)
        ));
    }
    Ok(())
}
#[test]
fn actual_note_acl_revocation_denies_fresh_import_and_cached_source_verify() -> TestResult {
    let input = notes::actual_inputs()?
        .into_iter()
        .find(|v| v.lane == "saved")
        .ok_or("saved")?;
    let stored = StoredFixture::new(&input.bytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let imported = provider.import_actual_forms(stored.head, 4)?;
    assert!(!imported.notes().is_empty());
    stored.artifacts.set_permissions(
        &stored.owner,
        stored.result,
        stored.reader.subject(),
        BTreeSet::new(),
        5,
    )?;
    assert!(matches!(
        imported.verify(&provider, 6),
        Err(StoredActualFormImportError::Source(
            StoredFormError::Artifact
        ))
    ));
    assert!(provider.import_actual_forms(stored.head, 6).is_err());
    Ok(())
}
#[test]
fn actual_note_aead_tamper_and_advanced_head_reject_without_native_work() -> TestResult {
    let input = notes::actual_inputs()?
        .into_iter()
        .find(|v| v.lane == "saved")
        .ok_or("saved")?;
    let stored = StoredFixture::new(&input.bytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let imported = provider.import_actual_forms(stored.head, 4)?;
    stored.blobs.tamper.store(true, Ordering::SeqCst);
    assert!(matches!(
        imported.verify(&provider, 5),
        Err(StoredActualFormImportError::Source(
            StoredFormError::Artifact
        ))
    ));
    stored.blobs.tamper.store(false, Ordering::SeqCst);
    stored.advance()?;
    assert!(matches!(
        imported.verify(&provider, 6),
        Err(StoredActualFormImportError::Source(StoredFormError::Head))
    ));
    Ok(())
}
#[test]
fn note_partial_markers_individually_deny_full_context_without_old_markers() -> TestResult {
    let input = notes::actual_inputs()?.into_iter().next().ok_or("note")?;
    let source = fixture::forms(&input.bytes, "actual-form-document")?;
    for (key, value) in [
        ("note_import_profile", NOTE_IMPORT_PROFILE),
        ("note_import_scope", NOTE_IMPORT_SCOPE),
    ] {
        let mut draft = source.graph().clone().into_draft();
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
                *ContentDigest::of(&input.bytes).as_bytes(),
                RevisionId::parse("notes-revision")?
            ),
            Err(FullDocumentFormError::Projection)
        ));
    }
    Ok(())
}

#[test]
fn actual_notes_reject_each_scope5_substitution_on_fresh_bound_and_cached_access() -> TestResult {
    let input = notes::actual_inputs()?
        .into_iter()
        .find(|v| v.lane == "saved")
        .ok_or("saved")?;
    let stored = StoredFixture::new(&input.bytes, ArtifactKind::Result, false)?;
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
            imported.verify(&other, 5),
            Err(StoredActualFormImportError::Binding)
        ));
        // A new authorized provider may independently read its own source.
        // It may not reuse this existing model's authenticated scope to derive
        // a fresh bound field model, even if source bytes happen to be equal.
        assert!(matches!(
            imported.import_field_ranges(&other, 5),
            Err(hwpx_agent_cli::form_stored_provider::actual_import::field_ranges::StoredFieldRangeImportError::Source(
                StoredActualFormImportError::Binding
            ))
        ));
    }
    Ok(())
}
