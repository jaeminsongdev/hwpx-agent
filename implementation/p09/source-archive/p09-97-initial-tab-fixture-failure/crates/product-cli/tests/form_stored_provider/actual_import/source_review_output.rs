//! Existing source/AEAD/revision fixture; no actual SQL or native acceptance.
use super::field_ranges::fixture;
use super::*;
use hwpx_agent_cli::form_stored_provider::actual_import::review::body_output::StoredReviewBodyOutputError;
use hwpx_package::{TextFlow, TextFlowLimits, TextFlowReader, WriterLimits};

fn synthetic() -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    fixture::package(
        "<hp:p id='1'><hp:run><hp:ctrl><hp:fieldBegin id='1' type='MEMO'><hp:parameters cnt='0'/><hp:subList><hp:p id='2'><hp:run><hp:t>OLD-PRIVATE</hp:t></hp:run></hp:p></hp:subList><hp:metaTag>UNINTERPRETED</hp:metaTag></hp:fieldBegin></hp:ctrl><hp:t>MAIN-VISIBLE</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='1'/></hp:ctrl></hp:run></hp:p>",
    )
}
fn target() -> Result<TextFlow, Box<dyn std::error::Error>> {
    Ok(TextFlowReader::read(b"<hp:p xmlns:hp='http://www.hancom.co.kr/hwpml/2011/paragraph' id='9'><hp:run><hp:t>NEW-PRIVATE &amp; &lt;xml&gt;<hp:tab/><hp:lineBreak/>END</hp:t></hp:run></hp:p>", TextFlowLimits::default())?)
}
#[test]
fn original_stored_review_lowers_complete_typed_body_without_ingest_commit_or_native_defaults()
-> TestResult {
    let bytes = synthetic()?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let review = source.import_review_bodies(&provider, 5)?;
    let prepared = review.prepare_body(
        &provider,
        review.observations()[0].marker_anchor.clone(),
        vec![target()?],
        WriterLimits::default(),
        6,
    )?;
    assert_eq!(prepared.verify(&provider, 7)?, *prepared.receipt());
    let result = prepared.with_verified_bytes(&provider, 8, <[u8]>::to_vec)?;
    assert_ne!(result, bytes);
    assert!(!prepared.receipt().native_author_time_state_verified);
    assert!(!prepared.receipt().execution_publication_authority);
    assert_eq!(
        prepared.require_current_product_route(&provider, 9).err(),
        Some(StoredReviewBodyOutputError::RouteUnqualified)
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
    let stored = StoredFixture::new(&synthetic()?, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let review = source.import_review_bodies(&provider, 5)?;
    let prepared = review.prepare_body(
        &provider,
        review.observations()[0].marker_anchor.clone(),
        vec![target()?],
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
