//! Original stored-source location inspection; no native/SQL/publication acceptance.
use super::field_ranges::fixture;
use super::*;
use hwpx_agent_cli::form_stored_provider::actual_import::review::locations::StoredReviewLocationError;

fn synthetic() -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    fixture::package(
        "<hp:p id='1'><hp:run><hp:t>BEFORE</hp:t><hp:ctrl><hp:fieldBegin id='1' type='MEMO'><hp:parameters cnt='0'/><hp:subList><hp:p id='2'><hp:run><hp:t>PRIVATE-BODY</hp:t></hp:run></hp:p></hp:subList><hp:metaTag>UNINTERPRETED</hp:metaTag></hp:fieldBegin></hp:ctrl><hp:t>VISIBLE</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='1'/></hp:ctrl></hp:run></hp:p>",
    )
}
#[test]
fn actual_original_stored_locations_match_direct_graph_without_state_defaults_or_writes()
-> TestResult {
    let bytes = synthetic()?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let review = source.import_review_bodies(&provider, 5)?;
    let locations = review.locate(&provider, 6)?;
    let direct_forms = fixture::forms(&bytes, "actual-form-document")?;
    let direct_review =
        hwpx_package::document_import::structure::review::ImportedDocumentReviewBodies::import(
            &direct_forms,
        )?;
    let direct = direct_review.locate(&bytes)?;
    assert_eq!(locations.locations(), direct.locations());
    assert_eq!(locations.receipt(), direct.receipt());
    assert_eq!(locations.verify(&provider, 7)?, *locations.receipt());
    assert_eq!(
        locations
            .with_verified_locations(&provider, 8, |values| values[0].start.point.inline_ordinal)?,
        1
    );
    assert!(
        !locations
            .receipt()
            .native_caret_or_visual_coordinates_verified
    );
    assert!(!locations.receipt().native_author_time_state_verified);
    assert_eq!(
        locations.require_current_product_route(&provider, 9).err(),
        Some(StoredReviewLocationError::RouteUnqualified)
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
            .filter(|e| e.event == "artifact.ingested")
            .count(),
        2
    );
    assert!(!format!("{locations:?} {:?}", locations.locations()).contains("PRIVATE"));
    Ok(())
}
#[test]
fn location_callback_rejects_actual_ciphertext_revoked_acl_and_advanced_head() -> TestResult {
    let stored = StoredFixture::new(&synthetic()?, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let review = source.import_review_bodies(&provider, 5)?;
    let locations = review.locate(&provider, 6)?;
    let mut called = false;
    stored.blobs.tamper.store(true, Ordering::SeqCst);
    assert_eq!(
        locations
            .with_verified_locations(&provider, 7, |_| called = true)
            .err(),
        Some(StoredReviewLocationError::Source)
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
    assert_eq!(
        locations
            .with_verified_locations(&provider, 9, |_| called = true)
            .err(),
        Some(StoredReviewLocationError::Source)
    );
    assert!(!called);
    stored.artifacts.set_permissions(
        &stored.owner,
        stored.result,
        stored.reader.subject(),
        BTreeSet::from([artifact_service::ArtifactPermission::Read]),
        10,
    )?;
    assert_eq!(locations.verify(&provider, 11)?, *locations.receipt());
    stored.advance()?;
    assert_eq!(
        locations
            .with_verified_locations(&provider, 12, |_| called = true)
            .err(),
        Some(StoredReviewLocationError::Source)
    );
    assert!(!called);
    Ok(())
}
#[test]
fn cached_locations_reject_all_original_provider_scope_substitutions_before_callback() -> TestResult
{
    use artifact_service::TenantId;
    use hwpx_agent_cli::form_stored_provider::StoredFormProvider;
    let stored = StoredFixture::new(&synthetic()?, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let review = source.import_review_bodies(&provider, 5)?;
    let locations = review.locate(&provider, 6)?;
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
            locations
                .with_verified_locations(&other, 7, |_| called = true)
                .err(),
            Some(StoredReviewLocationError::Source)
        );
        assert!(!called);
    }
    Ok(())
}
