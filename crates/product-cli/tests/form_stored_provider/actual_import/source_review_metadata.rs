//! Original fixture/service/importer path with synthetic metadata bytes; NOT native meaning.
use super::field_ranges::fixture;
use super::*;
use hwpx_package::document_import::structure::review::ImportedDocumentReviewBodies;
fn synthetic() -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    fixture::package(
        "<hp:p id='1'><hp:run><hp:ctrl><hp:fieldBegin id='1' type='MEMO'><hp:parameters cnt='0'/><hp:subList><hp:p id='2'><hp:run><hp:t>PRIVATE-BODY</hp:t></hp:run></hp:p></hp:subList><hp:metaTag>{&quot;author&quot;:&quot;SYNTHETIC_PRIVATE_AUTHOR&quot;}</hp:metaTag></hp:fieldBegin></hp:ctrl><hp:t>VISIBLE</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='1'/></hp:ctrl></hp:run></hp:p>",
    )
}
#[test]
fn original_authenticated_source_reader_carries_exact_meta_sidecar_and_whole_graph_without_writes()
-> TestResult {
    let bytes = synthetic()?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let imported = source.import_review_bodies(&provider, 5)?;
    let direct_source = fixture::forms(&bytes, "actual-form-document")?;
    let direct = ImportedDocumentReviewBodies::import(&direct_source)?;
    assert_eq!(imported.graph(), direct.graph());
    assert_eq!(imported.observations(), direct.observations());
    assert!(imported.observations()[0].meta_tag.is_some());
    assert_eq!(imported.verify(&provider, 6)?, *imported.receipt());
    assert!(
        !imported
            .receipt()
            .review
            .native_author_time_binding_verified
    );
    assert!(
        !imported
            .receipt()
            .review
            .native_visibility_resolution_binding_verified
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
            .filter(|v| v.event == "artifact.ingested")
            .count(),
        2
    );
    assert!(matches!(
        FullDocumentFormContext::bind(
            imported.graph(),
            imported.graph().canonical_sha256()?,
            *ContentDigest::of(&bytes).as_bytes(),
            RevisionId::parse("r1")?
        ),
        Err(FullDocumentFormError::Projection)
    ));
    assert!(
        !format!(
            "{imported:?} {:?} {:?}",
            imported.observations(),
            imported.receipt()
        )
        .contains("SYNTHETIC_PRIVATE_AUTHOR")
    );
    Ok(())
}
#[test]
fn cached_meta_sidecar_never_bypasses_fresh_actual_aead_acl_or_head_checks() -> TestResult {
    let stored = StoredFixture::new(&synthetic()?, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let imported = source.import_review_bodies(&provider, 5)?;
    stored.blobs.tamper.store(true, Ordering::SeqCst);
    assert!(imported.verify(&provider, 6).is_err());
    assert!(source.import_review_bodies(&provider, 6).is_err());
    stored.blobs.tamper.store(false, Ordering::SeqCst);
    stored.artifacts.set_permissions(
        &stored.owner,
        stored.result,
        stored.reader.subject(),
        BTreeSet::new(),
        7,
    )?;
    assert!(imported.verify(&provider, 8).is_err());
    assert!(source.import_review_bodies(&provider, 8).is_err());
    stored.artifacts.set_permissions(
        &stored.owner,
        stored.result,
        stored.reader.subject(),
        BTreeSet::from([artifact_service::ArtifactPermission::Read]),
        9,
    )?;
    assert_eq!(imported.verify(&provider, 10)?, *imported.receipt());
    stored.advance()?;
    assert!(imported.verify(&provider, 11).is_err());
    assert!(source.import_review_bodies(&provider, 11).is_err());
    Ok(())
}
#[test]
fn malformed_meta_cannot_fall_back_to_an_old_valid_body_or_fake_author_time() -> TestResult {
    for meta in [
        "<hp:metaTag><hp:p/></hp:metaTag>",
        "<hp:metaTag extra='1'>UNBOUND</hp:metaTag>",
    ] {
        let invalid = fixture::package(&format!(
            "<hp:p id='1'><hp:run><hp:ctrl><hp:fieldBegin id='1' type='MEMO'>{meta}</hp:fieldBegin></hp:ctrl><hp:ctrl><hp:fieldEnd beginIDRef='1'/></hp:ctrl></hp:run></hp:p>"
        ))?;
        let stored = StoredFixture::new(&invalid, ArtifactKind::Result, false)?;
        let provider = stored.provider()?;
        if let Ok(source) = provider.import_actual_forms(stored.head, 4) {
            assert!(source.import_review_bodies(&provider, 5).is_err());
        }
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
    }
    Ok(())
}
