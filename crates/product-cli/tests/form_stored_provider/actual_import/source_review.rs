use super::field_ranges::fixture;
use super::*;
use hwpx_agent_cli::form_stored_provider::actual_import::review::StoredReviewBodyImportError;
use hwpx_package::document_import::structure::review::{
    ImportedDocumentReviewBodies, REVIEW_BODY_IMPORT_PROFILE, REVIEW_BODY_IMPORT_SCOPE,
};

fn synthetic() -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    fixture::package(
        "<hp:p id='1'><hp:run><hp:ctrl><hp:fieldBegin id='1' type='MEMO'><hp:parameters cnt='0'/><hp:subList><hp:p id='2'><hp:run><hp:t>PRIVATE-REVIEW</hp:t></hp:run></hp:p></hp:subList></hp:fieldBegin></hp:ctrl><hp:t>VISIBLE</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='1'/></hp:ctrl><hp:hiddenComment><hp:subList><hp:p id='3'><hp:run><hp:t>PRIVATE-HIDDEN</hp:t></hp:run></hp:p></hp:subList></hp:hiddenComment></hp:run></hp:p>",
    )
}

#[test]
fn source_review_bodies_use_actual_aead_reader_and_whole_direct_graph_without_publication()
-> TestResult {
    for bytes in [synthetic()?, fixture::captured()?] {
        let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
        let provider = stored.provider()?;
        let source = provider.import_actual_forms(stored.head, 4)?;
        let imported = source.import_review_bodies(&provider, 5)?;
        let direct_source = fixture::forms(&bytes, "actual-form-document")?;
        let direct = ImportedDocumentReviewBodies::import(&direct_source)?;
        assert_eq!(imported.graph(), direct.graph());
        assert_eq!(imported.observations(), direct.observations());
        assert_eq!(imported.receipt().review, *direct.receipt());
        assert_eq!(imported.verify(&provider, 6)?, *imported.receipt());
        assert!(
            !imported
                .receipt()
                .review
                .native_author_time_binding_verified
        );
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
                .filter(|a| a.event == "artifact.ingested")
                .count(),
            2
        );
        assert!(matches!(
            FullDocumentFormContext::bind(
                imported.graph(),
                imported.graph().canonical_sha256()?,
                *ContentDigest::of(&bytes).as_bytes(),
                RevisionId::parse("baseline")?
            ),
            Err(FullDocumentFormError::Projection)
        ));
        let debug = format!(
            "{imported:?} {:?} {:?}",
            imported.observations(),
            imported.receipt()
        );
        assert!(!debug.contains("PRIVATE-REVIEW") && !debug.contains("PRIVATE-HIDDEN"));
    }
    Ok(())
}

#[test]
fn review_acl_revocation_and_aead_tamper_block_derivation_and_cached_verification() -> TestResult {
    let stored = StoredFixture::new(&synthetic()?, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let imported = source.import_review_bodies(&provider, 5)?;
    stored.blobs.tamper.store(true, Ordering::SeqCst);
    assert!(matches!(
        imported.verify(&provider, 6),
        Err(StoredReviewBodyImportError::Source(
            StoredActualFormImportError::Source(StoredFormError::Artifact)
        ))
    ));
    assert!(source.import_review_bodies(&provider, 6).is_err());
    stored.blobs.tamper.store(false, Ordering::SeqCst);
    stored.artifacts.set_permissions(
        &stored.owner,
        stored.result,
        stored.reader.subject(),
        BTreeSet::new(),
        7,
    )?;
    assert!(matches!(
        imported.verify(&provider, 8),
        Err(StoredReviewBodyImportError::Source(
            StoredActualFormImportError::Source(StoredFormError::Artifact)
        ))
    ));
    assert!(source.import_review_bodies(&provider, 8).is_err());
    Ok(())
}

#[test]
fn review_head_change_and_provider_scope_rebind_cannot_reuse_cached_body() -> TestResult {
    use artifact_service::TenantId;
    use hwpx_agent_cli::form_stored_provider::StoredFormProvider;
    let stored = StoredFixture::new(&synthetic()?, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let imported = source.import_review_bodies(&provider, 5)?;
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
            imported.verify(&other, 6),
            Err(StoredReviewBodyImportError::Source(
                StoredActualFormImportError::Binding
            ))
        ));
        assert!(source.import_review_bodies(&other, 6).is_err());
    }
    stored.advance()?;
    assert!(matches!(
        imported.verify(&provider, 7),
        Err(StoredReviewBodyImportError::Source(
            StoredActualFormImportError::Source(StoredFormError::Head)
        ))
    ));
    assert!(source.import_review_bodies(&provider, 7).is_err());
    Ok(())
}

#[test]
fn malformed_review_body_fails_product_reader_without_ingest_or_revision_change() -> TestResult {
    let bytes = fixture::package(
        "<hp:p id='1'><hp:run><hp:hiddenComment><hp:subList><hp:p id='invalid'><hp:run><hp:t>BODY</hp:t></hp:run></hp:p></hp:subList></hp:hiddenComment></hp:run></hp:p>",
    )?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    assert!(matches!(
        source.import_review_bodies(&provider, 5),
        Err(StoredReviewBodyImportError::Review(_))
    ));
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
            .filter(|a| a.event == "artifact.ingested")
            .count(),
        2
    );
    Ok(())
}

#[test]
fn review_partial_markers_independently_deny_full_document_promotion() -> TestResult {
    let bytes = synthetic()?;
    let forms = fixture::forms(&bytes, "actual-form-document")?;
    let imported = ImportedDocumentReviewBodies::import(&forms)?;
    for (key, value) in [
        ("review_body_import_profile", REVIEW_BODY_IMPORT_PROFILE),
        ("review_body_import_scope", REVIEW_BODY_IMPORT_SCOPE),
    ] {
        // Deliberately remove all earlier markers to test this NEW denial,
        // never treat the altered graph as an authorized product input.
        let mut draft = imported.graph().clone().into_draft();
        draft.source_profile = None;
        draft.metadata = domain_ir::Properties::new();
        draft
            .metadata
            .insert(key, domain_ir::PropertyValue::Text(value.into()));
        let graph =
            domain_ir::DocumentGraph::from_draft(draft, domain_ir::DocumentGraphLimits::default())?;
        assert!(matches!(
            FullDocumentFormContext::bind(
                &graph,
                graph.canonical_sha256()?,
                *ContentDigest::of(&bytes).as_bytes(),
                RevisionId::parse("baseline")?
            ),
            Err(FullDocumentFormError::Projection)
        ));
    }
    Ok(())
}
