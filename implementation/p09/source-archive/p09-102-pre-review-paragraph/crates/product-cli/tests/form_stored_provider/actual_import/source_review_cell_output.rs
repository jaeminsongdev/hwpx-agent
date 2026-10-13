//! Existing source/AEAD/revision fixture; no actual SQL or native acceptance.
use super::source_review_assembly::fixture as assembly;
use super::*;
use hwpx_agent_cli::form_stored_provider::actual_import::review::cell_body_output::StoredReviewCellBodyOutputError;
use hwpx_package::WriterLimits;
#[path = "../../../../hwpx-package/tests/support/review_cell_output_fixture.rs"]
mod fixture;

#[test]
fn original_stored_review_lowers_typed_cell_with_same_direct_package_and_no_writes() -> TestResult {
    let bytes = fixture::package()?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let review = source.import_review_bodies(&provider, 5)?;
    let prepared = review.prepare_table_cell_body(
        &provider,
        review.observations()[0].marker_anchor.clone(),
        fixture::cells(source.imported())?[0].clone(),
        vec![fixture::target()?],
        WriterLimits::default(),
        6,
    )?;
    assert_eq!(prepared.verify(&provider, 7)?, *prepared.receipt());
    let result = prepared.with_verified_bytes(&provider, 8, <[u8]>::to_vec)?;
    assert_ne!(result, bytes);
    let direct_forms = super::field_ranges::fixture::forms(&bytes, "actual-form-document")?;
    let direct =
        hwpx_package::document_import::structure::review::ImportedDocumentReviewBodies::import(
            &direct_forms,
        )?;
    let direct_output = direct.lower_table_cell_body(
        &bytes,
        &direct.observations()[0].marker_anchor,
        &fixture::cells(&direct_forms)?[0],
        &[fixture::target()?],
        WriterLimits::default(),
    )?;
    assert_eq!(result, direct_output.with_verified_bytes(<[u8]>::to_vec)?);
    assert_eq!(prepared.receipt(), direct_output.receipt());
    assert!(!prepared.receipt().output.native_author_time_state_verified);
    assert!(!prepared.receipt().output.execution_publication_authority);
    assert_eq!(
        prepared.require_current_product_route(&provider, 9).err(),
        Some(StoredReviewCellBodyOutputError::RouteUnqualified)
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
    assert!(!format!("{prepared:?}").contains("NEW-PRIVATE"));
    Ok(())
}
#[test]
fn cached_body_callback_rechecks_actual_aead_acl_regrant_and_advanced_head() -> TestResult {
    let stored = StoredFixture::new(&fixture::package()?, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let review = source.import_review_bodies(&provider, 5)?;
    let prepared = review.prepare_table_cell_body(
        &provider,
        review.observations()[0].marker_anchor.clone(),
        fixture::cells(source.imported())?[0].clone(),
        vec![fixture::target()?],
        WriterLimits::default(),
        6,
    )?;
    let mut called = false;
    stored.blobs.tamper.store(true, Ordering::SeqCst);
    assert!(
        prepared
            .with_verified_bytes(&provider, 7, |_| called = true)
            .is_err()
    );
    assert!(!called);
    stored.blobs.tamper.store(false, Ordering::SeqCst);
    stored.artifacts.set_permissions(
        &stored.owner,
        stored.result,
        stored.reader.subject(),
        BTreeSet::new(),
        8,
    )?;
    assert!(
        prepared
            .with_verified_bytes(&provider, 9, |_| called = true)
            .is_err()
    );
    assert!(!called);
    stored.artifacts.set_permissions(
        &stored.owner,
        stored.result,
        stored.reader.subject(),
        BTreeSet::from([artifact_service::ArtifactPermission::Read]),
        10,
    )?;
    assert_eq!(prepared.verify(&provider, 11)?, *prepared.receipt());
    stored.advance()?;
    assert!(
        prepared
            .with_verified_bytes(&provider, 12, |_| called = true)
            .is_err()
    );
    assert!(!called);
    Ok(())
}

#[test]
fn cached_cell_callback_rejects_all_provider_scope_substitutions() -> TestResult {
    let stored = StoredFixture::new(&fixture::package()?, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let review = source.import_review_bodies(&provider, 5)?;
    let prepared = review.prepare_table_cell_body(
        &provider,
        review.observations()[0].marker_anchor.clone(),
        fixture::cells(source.imported())?[0].clone(),
        vec![fixture::target()?],
        WriterLimits::default(),
        6,
    )?;
    for variant in 0..5 {
        let tenant = if variant == 4 {
            TenantId::new(uuid::Uuid::from_u128(802))?
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
            revision_service::ProjectId::parse("prj_80000000000000000000000000000002")?
        } else {
            stored.project
        };
        let branch = if variant == 1 {
            revision_service::BranchId::parse("brn_80000000000000000000000000000002")?
        } else {
            stored.branch
        };
        let document = if variant == 0 {
            "foreign-document"
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
        let mut called = false;
        assert_eq!(
            prepared
                .with_verified_bytes(&other, 7, |_| called = true)
                .err(),
            Some(StoredReviewCellBodyOutputError::Source)
        );
        assert!(!called);
    }
    Ok(())
}
