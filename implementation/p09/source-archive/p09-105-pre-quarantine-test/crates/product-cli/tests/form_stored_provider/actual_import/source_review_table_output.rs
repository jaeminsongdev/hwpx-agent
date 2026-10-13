//! Actual encrypted in-memory service instances, not PostgreSQL/Hangul acceptance.
use super::*;
use hwpx_agent_cli::form_stored_provider::actual_import::{
    StoredImportedDocumentForms,
    review::{
        StoredImportedReviewBodies,
        table_output::{
            StoredReviewTableLimits, StoredReviewTableOutputError, StoredReviewTableRequest,
        },
    },
};
use hwpx_package::{
    TableCreateHwpxLimits, WriterLimits,
    document_import::structure::review::table_create_context::{
        ReviewTableTemplate, output::ReviewTableDimensions,
    },
};
#[path = "review_table_fixture.rs"]
mod fixture;
type FixtureResult<T> = Result<T, Box<dyn std::error::Error>>;

fn request<'a>(
    source: &StoredImportedDocumentForms,
    review: &StoredImportedReviewBodies<'_>,
    template: &'a StoredImportedDocumentForms,
    bytes: &[u8],
    tbytes: &[u8],
    observation: usize,
) -> FixtureResult<StoredReviewTableRequest<'a>> {
    Ok(StoredReviewTableRequest {
        template,
        marker: review.observations()[observation].marker_anchor.clone(),
        paragraph: fixture::anchor(
            source.imported(),
            bytes,
            "p",
            if observation == 0 { "101" } else { "102" },
        )?,
        table: fixture::anchor(template.imported(), tbytes, "tbl", "700")?,
        dimensions: ReviewTableDimensions::new(vec![400, 800], vec![500, 900, 600])?,
    })
}

#[test]
fn stored_two_sources_match_actual_direct_memo_and_hidden_packages_without_publication()
-> TestResult {
    let bytes = fixture::source()?;
    let tbytes = fixture::template(false)?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let templates = StoredFixture::new(&tbytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let tp = templates.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let template = tp.import_actual_forms(templates.head, 4)?;
    let review = source.import_review_bodies(&provider, 5)?;
    for i in 0..2 {
        let req = request(&source, &review, &template, &bytes, &tbytes, i)?;
        let direct =
            hwpx_package::document_import::structure::review::ImportedDocumentReviewBodies::import(
                source.imported(),
            )?;
        let context = direct.prepare_table_creation(
            &bytes,
            &req.marker,
            &req.paragraph,
            ReviewTableTemplate {
                forms: template.imported(),
                fresh: &tbytes,
                table: &req.table,
            },
            TableCreateHwpxLimits::default(),
        )?;
        let expected =
            context.lower_table(&bytes, &tbytes, &req.dimensions, WriterLimits::default())?;
        let prepared =
            review.prepare_table(&provider, &tp, req, StoredReviewTableLimits::default(), 6)?;
        assert_eq!(prepared.verify(&provider, &tp, 7)?, *prepared.receipt());
        assert_eq!(prepared.receipt().output, *expected.receipt());
        let actual = prepared.with_verified_bytes(&provider, &tp, 8, <[u8]>::to_vec)?;
        assert_eq!(actual, expected.with_verified_bytes(<[u8]>::to_vec)?);
        assert!(prepared.receipt().output.new_table_inserted);
        assert!(!prepared.receipt().output.full_document_flow_bound);
        assert!(!prepared.receipt().output.full_comment_product_acceptance);
        assert!(!format!("{prepared:?}").contains("PRIVATE"));
        assert_eq!(
            prepared
                .require_current_product_route(&provider, &tp, 9)
                .err(),
            Some(StoredReviewTableOutputError::RouteUnqualified)
        );
    }
    for s in [&stored, &templates] {
        assert_eq!(
            s.revisions.head(&s.revision_context, s.project, s.branch)?,
            s.head
        );
        assert_eq!(
            s.metadata
                .audit_events()?
                .iter()
                .filter(|e| e.event == "artifact.ingested")
                .count(),
            2
        );
    }
    Ok(())
}

#[test]
fn both_independent_sources_recheck_actual_aead_acl_regrant_and_callback_denial() -> TestResult {
    let bytes = fixture::source()?;
    let tbytes = fixture::template(false)?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let templates = StoredFixture::new(&tbytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let tp = templates.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let template = tp.import_actual_forms(templates.head, 4)?;
    let review = source.import_review_bodies(&provider, 5)?;
    let prepared = review.prepare_table(
        &provider,
        &tp,
        request(&source, &review, &template, &bytes, &tbytes, 0)?,
        StoredReviewTableLimits::default(),
        6,
    )?;
    for (s, error) in [
        (&stored, StoredReviewTableOutputError::Source),
        (&templates, StoredReviewTableOutputError::Template),
    ] {
        let mut called = false;
        s.blobs.tamper.store(true, Ordering::SeqCst);
        assert_eq!(
            prepared
                .with_verified_bytes(&provider, &tp, 7, |_| called = true)
                .err(),
            Some(error.clone())
        );
        assert!(!called);
        assert_eq!(
            prepared
                .require_current_product_route(&provider, &tp, 7)
                .err(),
            Some(error.clone())
        );
        s.blobs.tamper.store(false, Ordering::SeqCst);
        s.artifacts
            .set_permissions(&s.owner, s.result, s.reader.subject(), BTreeSet::new(), 8)?;
        assert_eq!(
            prepared
                .with_verified_bytes(&provider, &tp, 9, |_| called = true)
                .err(),
            Some(error)
        );
        assert!(!called);
        s.artifacts.set_permissions(
            &s.owner,
            s.result,
            s.reader.subject(),
            BTreeSet::from([artifact_service::ArtifactPermission::Read]),
            10,
        )?;
        assert_eq!(prepared.verify(&provider, &tp, 11)?, *prepared.receipt());
    }
    Ok(())
}

#[test]
fn either_original_head_advance_invalidates_cached_candidate_without_callback() -> TestResult {
    for advance_template in [false, true] {
        let bytes = fixture::source()?;
        let tbytes = fixture::template(false)?;
        let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
        let templates = StoredFixture::new(&tbytes, ArtifactKind::Result, false)?;
        let provider = stored.provider()?;
        let tp = templates.provider()?;
        let source = provider.import_actual_forms(stored.head, 4)?;
        let template = tp.import_actual_forms(templates.head, 4)?;
        let review = source.import_review_bodies(&provider, 5)?;
        let prepared = review.prepare_table(
            &provider,
            &tp,
            request(&source, &review, &template, &bytes, &tbytes, 0)?,
            StoredReviewTableLimits::default(),
            6,
        )?;
        if advance_template {
            templates.advance()?;
        } else {
            stored.advance()?;
        }
        let mut called = false;
        assert_eq!(
            prepared
                .with_verified_bytes(&provider, &tp, 7, |_| called = true)
                .err(),
            Some(if advance_template {
                StoredReviewTableOutputError::Template
            } else {
                StoredReviewTableOutputError::Source
            })
        );
        assert!(!called);
    }
    Ok(())
}

#[test]
fn either_provider_scope_substitution_or_different_principal_rejects_cached_bytes() -> TestResult {
    let bytes = fixture::source()?;
    let tbytes = fixture::template(false)?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let templates = StoredFixture::new(&tbytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let tp = templates.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let template = tp.import_actual_forms(templates.head, 4)?;
    let review = source.import_review_bodies(&provider, 5)?;
    let prepared = review.prepare_table(
        &provider,
        &tp,
        request(&source, &review, &template, &bytes, &tbytes, 0)?,
        StoredReviewTableLimits::default(),
        6,
    )?;
    for use_template in [false, true] {
        for variant in 0..5 {
            let s = if use_template { &templates } else { &stored };
            let tenant = if variant == 4 {
                TenantId::new(uuid::Uuid::from_u128(802))?
            } else {
                s.reader.tenant_id()
            };
            let subject = if variant == 3 {
                s.owner.subject()
            } else {
                s.reader.subject()
            };
            let actor = RequestContext::new(tenant, subject, [AuthScope::DocumentRead]);
            let revision_actor = revision_service::RevisionRequestContext::new(tenant, subject);
            let project = if variant == 2 {
                revision_service::ProjectId::parse("prj_80000000000000000000000000000002")?
            } else {
                s.project
            };
            let branch = if variant == 1 {
                revision_service::BranchId::parse("brn_80000000000000000000000000000002")?
            } else {
                s.branch
            };
            let document = if variant == 0 {
                "foreign-document"
            } else {
                "actual-form-document"
            };
            let other = StoredFormProvider::bind(
                &s.artifacts,
                &s.revisions,
                &actor,
                &revision_actor,
                project,
                branch,
                DocumentId::parse(document)?,
            )?;
            let mut called = false;
            let result = if use_template {
                prepared.with_verified_bytes(&provider, &other, 7, |_| called = true)
            } else {
                prepared.with_verified_bytes(&other, &tp, 7, |_| called = true)
            };
            assert_eq!(
                result.err(),
                Some(if variant >= 3 {
                    StoredReviewTableOutputError::Actor
                } else if use_template {
                    StoredReviewTableOutputError::Template
                } else {
                    StoredReviewTableOutputError::Source
                })
            );
            assert!(!called);
        }
    }
    Ok(())
}

#[test]
fn swapped_services_do_not_rebind_even_when_actor_document_and_generation_equal() -> TestResult {
    let bytes = fixture::source()?;
    let tbytes = fixture::template(false)?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let templates = StoredFixture::new(&tbytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let tp = templates.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let template = tp.import_actual_forms(templates.head, 4)?;
    let review = source.import_review_bodies(&provider, 5)?;
    let prepared = review.prepare_table(
        &provider,
        &tp,
        request(&source, &review, &template, &bytes, &tbytes, 0)?,
        StoredReviewTableLimits::default(),
        6,
    )?;
    let mut called = false;
    assert_eq!(
        prepared
            .with_verified_bytes(&tp, &provider, 7, |_| called = true)
            .err(),
        Some(StoredReviewTableOutputError::Source)
    );
    assert!(!called);
    assert_eq!(
        prepared
            .with_verified_bytes(&provider, &provider, 7, |_| called = true)
            .err(),
        Some(StoredReviewTableOutputError::Template)
    );
    assert!(!called);
    Ok(())
}

#[test]
fn no_template_import_can_bypass_original_kind_or_scanner_admission() -> TestResult {
    let bytes = fixture::template(false)?;
    for (kind, unverified) in [(ArtifactKind::Source, false), (ArtifactKind::Result, true)] {
        let templates = StoredFixture::new(&bytes, kind, unverified)?;
        assert!(
            templates
                .provider()?
                .import_actual_forms(templates.head, 4)
                .is_err()
        );
    }
    Ok(())
}

#[test]
fn foreign_table_anchor_and_finite_writer_limits_do_not_prepare_partial_outputs() -> TestResult {
    let bytes = fixture::source()?;
    let tbytes = fixture::template(false)?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let templates = StoredFixture::new(&tbytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let tp = templates.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let template = tp.import_actual_forms(templates.head, 4)?;
    let review = source.import_review_bodies(&provider, 5)?;
    let mut req = request(&source, &review, &template, &bytes, &tbytes, 0)?;
    req.table = req.paragraph.clone();
    assert_eq!(
        review
            .prepare_table(&provider, &tp, req, StoredReviewTableLimits::default(), 6)
            .err(),
        Some(StoredReviewTableOutputError::Output)
    );
    let limits = StoredReviewTableLimits {
        writer: WriterLimits::new(hwpx_package::WriterLimitConfig {
            max_output_bytes: 1,
        })?,
        ..StoredReviewTableLimits::default()
    };
    assert_eq!(
        review
            .prepare_table(
                &provider,
                &tp,
                request(&source, &review, &template, &bytes, &tbytes, 0)?,
                limits,
                6
            )
            .err(),
        Some(StoredReviewTableOutputError::Output)
    );
    Ok(())
}
