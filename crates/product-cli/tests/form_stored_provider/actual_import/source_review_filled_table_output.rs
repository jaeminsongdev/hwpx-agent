//! Child of the unchanged original blank-table fixture suite: native tests loaded once.
//! Actual encrypted in-memory service calls; NOT durable PostgreSQL/native/publication.
use super::*;
use hwpx_agent_cli::form_stored_provider::actual_import::review::filled_table_output::StoredReviewFilledTableRequest;
use hwpx_package::{
    TextFlow, TextFlowLimits, TextFlowReader,
    document_import::structure::review::table_create_context::filled_output::{
        ReviewNewTableCell, ReviewNewTableCells,
    },
};

fn text(id: u32) -> FixtureResult<TextFlow> {
    Ok(TextFlowReader::read(format!("<hp:p xmlns:hp='http://www.hancom.co.kr/hwpml/2011/paragraph' id='{id}' styleIDRef='0' paraPrIDRef='0'><hp:run charPrIDRef='0'><hp:t>FILLED-PRIVATE &amp; 한글<hp:tab width='8000' leader='0' type='0'/><hp:lineBreak/>끝</hp:t></hp:run><hp:run charPrIDRef='0'><hp:t>SECOND RUN</hp:t></hp:run></hp:p>").as_bytes(),TextFlowLimits::default())?)
}
fn cells(reverse: bool) -> FixtureResult<ReviewNewTableCells> {
    let mut contents = vec![
        ReviewNewTableCell {
            row: 0,
            column: 0,
            paragraphs: vec![text(801)?, text(802)?],
        },
        ReviewNewTableCell {
            row: 1,
            column: 2,
            paragraphs: vec![text(803)?],
        },
    ];
    if reverse {
        contents.reverse();
    }
    Ok(ReviewNewTableCells::new(contents)?)
}
fn filled_request<'a>(
    source: &StoredImportedDocumentForms,
    review: &StoredImportedReviewBodies<'_>,
    template: &'a StoredImportedDocumentForms,
    bytes: &[u8],
    tbytes: &[u8],
    observation: usize,
) -> FixtureResult<StoredReviewFilledTableRequest<'a>> {
    Ok(StoredReviewFilledTableRequest {
        selection: request(source, review, template, bytes, tbytes, observation)?,
        cells: cells(false)?,
    })
}
#[test]
fn filled_stored_memo_hidden_match_actual_direct_and_reversed_input_without_heads_or_ingest()
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
    for ordinal in 0..2 {
        let req = filled_request(&source, &review, &template, &bytes, &tbytes, ordinal)?;
        let direct =
            hwpx_package::document_import::structure::review::ImportedDocumentReviewBodies::import(
                source.imported(),
            )?;
        let context = direct.prepare_table_creation(
            &bytes,
            &req.selection.marker,
            &req.selection.paragraph,
            ReviewTableTemplate {
                forms: template.imported(),
                fresh: &tbytes,
                table: &req.selection.table,
            },
            TableCreateHwpxLimits::default(),
        )?;
        let expected = context.lower_table_with_cells(
            &bytes,
            &tbytes,
            &req.selection.dimensions,
            &cells(true)?,
            WriterLimits::default(),
        )?;
        let prepared = review.prepare_filled_table(
            &provider,
            &tp,
            req,
            StoredReviewTableLimits::default(),
            6,
        )?;
        assert_eq!(prepared.verify(&provider, &tp, 7)?, *prepared.receipt());
        assert_eq!(prepared.receipt().output, *expected.receipt());
        assert_eq!(
            prepared.with_verified_bytes(&provider, &tp, 8, <[u8]>::to_vec)?,
            expected.with_verified_bytes(<[u8]>::to_vec)?
        );
        assert_eq!(
            (
                prepared.receipt().output.populated_cells,
                prepared.receipt().output.populated_paragraphs
            ),
            (2, 3)
        );
        assert_ne!(
            prepared.receipt().output.final_package_sha256,
            prepared
                .receipt()
                .output
                .blank_creation
                .output_package_sha256
        );
        assert!(!prepared.receipt().output.full_document_flow_bound);
        assert!(!prepared.receipt().output.full_comment_product_acceptance);
        assert_eq!(
            prepared
                .require_current_product_route(&provider, &tp, 9)
                .err(),
            Some(StoredReviewTableOutputError::RouteUnqualified)
        );
        let debug = format!(
            "{prepared:?} {:?} {}",
            prepared.receipt(),
            serde_json::to_string(prepared.receipt())?
        );
        for private in [
            "FILLED-PRIVATE",
            "OPAQUE-SOURCE-PRIVATE",
            "actual-form-document",
        ] {
            assert!(!debug.contains(private));
        }
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
fn filled_both_services_reject_aead_acl_before_callback_and_route_then_regrant() -> TestResult {
    let bytes = fixture::source()?;
    let tbytes = fixture::template(false)?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let templates = StoredFixture::new(&tbytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let tp = templates.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let template = tp.import_actual_forms(templates.head, 4)?;
    let review = source.import_review_bodies(&provider, 5)?;
    let prepared = review.prepare_filled_table(
        &provider,
        &tp,
        filled_request(&source, &review, &template, &bytes, &tbytes, 0)?,
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
            Some(error.clone())
        );
        assert!(!called);
        assert_eq!(
            prepared
                .require_current_product_route(&provider, &tp, 9)
                .err(),
            Some(error)
        );
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
fn filled_each_head_advance_invalidates_whole_preparation_before_callback() -> TestResult {
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
        let prepared = review.prepare_filled_table(
            &provider,
            &tp,
            filled_request(&source, &review, &template, &bytes, &tbytes, 0)?,
            StoredReviewTableLimits::default(),
            6,
        )?;
        if advance_template {
            templates.advance()?;
        } else {
            stored.advance()?;
        }
        let error = if advance_template {
            StoredReviewTableOutputError::Template
        } else {
            StoredReviewTableOutputError::Source
        };
        let mut called = false;
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
            Some(error)
        );
    }
    Ok(())
}
#[test]
fn filled_both_providers_all_five_scope_substitutions_and_principals_reject() -> TestResult {
    let bytes = fixture::source()?;
    let tbytes = fixture::template(false)?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let templates = StoredFixture::new(&tbytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let tp = templates.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let template = tp.import_actual_forms(templates.head, 4)?;
    let review = source.import_review_bodies(&provider, 5)?;
    let prepared = review.prepare_filled_table(
        &provider,
        &tp,
        filled_request(&source, &review, &template, &bytes, &tbytes, 0)?,
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
fn filled_swapped_service_same_actor_document_generation_and_foreign_anchor_reject() -> TestResult {
    let bytes = fixture::source()?;
    let tbytes = fixture::template(false)?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let templates = StoredFixture::new(&tbytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let tp = templates.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let template = tp.import_actual_forms(templates.head, 4)?;
    let review = source.import_review_bodies(&provider, 5)?;
    let prepared = review.prepare_filled_table(
        &provider,
        &tp,
        filled_request(&source, &review, &template, &bytes, &tbytes, 0)?,
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
    let mut req = filled_request(&source, &review, &template, &bytes, &tbytes, 0)?;
    req.selection.table = req.selection.paragraph.clone();
    assert_eq!(
        review
            .prepare_filled_table(&provider, &tp, req, StoredReviewTableLimits::default(), 8)
            .err(),
        Some(StoredReviewTableOutputError::Output)
    );
    Ok(())
}
#[test]
fn filled_original_style_id_geometry_and_writer_guards_never_prepare_partial_output() -> TestResult
{
    let bytes = fixture::source()?;
    let tbytes = fixture::template(false)?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let templates = StoredFixture::new(&tbytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let tp = templates.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let template = tp.import_actual_forms(templates.head, 4)?;
    let review = source.import_review_bodies(&provider, 5)?;
    let mut bad_style = text(801)?;
    bad_style.paragraph.style_id_ref = Some(999_999);
    for (row, column, paragraphs) in [
        (0, 0, vec![bad_style]),
        (0, 0, vec![text(10)?]),
        (0, 0, vec![text(801)?, text(801)?]),
        (u32::MAX, 0, vec![text(801)?]),
    ] {
        let mut req = filled_request(&source, &review, &template, &bytes, &tbytes, 0)?;
        req.cells = ReviewNewTableCells::new(vec![ReviewNewTableCell {
            row,
            column,
            paragraphs,
        }])?;
        assert_eq!(
            review
                .prepare_filled_table(&provider, &tp, req, StoredReviewTableLimits::default(), 6)
                .err(),
            Some(StoredReviewTableOutputError::Output)
        );
    }
    let limits = StoredReviewTableLimits {
        writer: WriterLimits::new(hwpx_package::WriterLimitConfig {
            max_output_bytes: 1,
        })?,
        ..StoredReviewTableLimits::default()
    };
    assert_eq!(
        review
            .prepare_filled_table(
                &provider,
                &tp,
                filled_request(&source, &review, &template, &bytes, &tbytes, 0)?,
                limits,
                6
            )
            .err(),
        Some(StoredReviewTableOutputError::Output)
    );
    Ok(())
}
#[test]
fn filled_each_quarantined_input_denies_cached_bytes_and_route_without_callback() -> TestResult {
    for quarantine_template in [false, true] {
        let bytes = fixture::source()?;
        let tbytes = fixture::template(false)?;
        let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
        let templates = StoredFixture::new(&tbytes, ArtifactKind::Result, false)?;
        let provider = stored.provider()?;
        let tp = templates.provider()?;
        let source = provider.import_actual_forms(stored.head, 4)?;
        let template = tp.import_actual_forms(templates.head, 4)?;
        let review = source.import_review_bodies(&provider, 5)?;
        let prepared = review.prepare_filled_table(
            &provider,
            &tp,
            filled_request(&source, &review, &template, &bytes, &tbytes, 0)?,
            StoredReviewTableLimits::default(),
            6,
        )?;
        let s = if quarantine_template {
            &templates
        } else {
            &stored
        };
        s.artifacts.quarantine(
            &s.owner,
            s.result,
            artifact_service::QuarantineReason::parse("P107_TEST_ONLY_QUARANTINE")?,
            7,
        )?;
        let error = if quarantine_template {
            StoredReviewTableOutputError::Template
        } else {
            StoredReviewTableOutputError::Source
        };
        let mut called = false;
        assert_eq!(
            prepared
                .with_verified_bytes(&provider, &tp, 8, |_| called = true)
                .err(),
            Some(error.clone())
        );
        assert!(!called);
        assert_eq!(
            prepared
                .require_current_product_route(&provider, &tp, 8)
                .err(),
            Some(error)
        );
    }
    Ok(())
}
#[test]
fn filled_neither_input_bypasses_original_result_kind_and_verified_scanner_admission() -> TestResult
{
    for bytes in [fixture::source()?, fixture::template(false)?] {
        for (kind, unverified) in [(ArtifactKind::Source, false), (ArtifactKind::Result, true)] {
            let stored = StoredFixture::new(&bytes, kind, unverified)?;
            assert!(
                stored
                    .provider()?
                    .import_actual_forms(stored.head, 4)
                    .is_err()
            );
        }
    }
    Ok(())
}
