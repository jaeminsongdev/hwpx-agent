use super::*;
use super::formula_evaluation::fixture;
use hwpx_package::WriterLimits;
use hwpx_agent_cli::form_stored_provider::actual_import::field_ranges::semantics::evaluation::output::StoredFormulaOutputError;
fn changed() -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    fixture::mutate_first_cell(&fixture::inputs::actual_corpus()?.remove(0), |cell| {
        fixture::replace_first_text(cell, "900001")
    })
}
#[test]
fn authenticated_actual_result_output_is_replayable_but_does_not_ingest_commit_or_authorize_route()
-> TestResult {
    let bytes = changed()?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let fields = source.import_field_ranges(&provider, 5)?;
    let meanings = fields.import_semantics(&provider, 6)?;
    let evaluated = meanings.evaluate_table_formulas(&provider, 7)?;
    let downloads = || -> Result<usize, artifact_service::ArtifactError> {
        Ok(stored
            .metadata
            .audit_events()?
            .iter()
            .filter(|event| event.event == "artifact.download")
            .count())
    };
    let before = downloads()?;
    let prepared = evaluated.prepare_results(&provider, WriterLimits::default(), 8)?;
    assert_eq!(downloads()?, before + 7);
    let before = downloads()?;
    assert_eq!(prepared.verify(&provider, 9)?, *prepared.receipt());
    assert_eq!(downloads()?, before + 7);
    let before = downloads()?;
    let candidate = prepared.with_verified_bytes(&provider, 10, <[u8]>::to_vec)?;
    assert_eq!(downloads()?, before + 7);
    let before = downloads()?;
    assert_ne!(candidate, bytes);
    assert!(matches!(
        prepared.require_current_product_route(&provider, 11),
        Err(StoredFormulaOutputError::RouteUnqualified)
    ));
    assert_eq!(downloads()?, before + 7);
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
    Ok(())
}
#[test]
fn revoked_acl_tampered_aead_head_advance_and_quarantine_never_release_cached_result_bytes()
-> TestResult {
    for failure in 0..4 {
        let bytes = changed()?;
        let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
        let provider = stored.provider()?;
        let source = provider.import_actual_forms(stored.head, 4)?;
        let fields = source.import_field_ranges(&provider, 5)?;
        let meanings = fields.import_semantics(&provider, 6)?;
        let evaluated = meanings.evaluate_table_formulas(&provider, 7)?;
        let prepared = evaluated.prepare_results(&provider, WriterLimits::default(), 8)?;
        match failure {
            0 => stored.blobs.tamper.store(true, Ordering::SeqCst),
            1 => {
                stored.artifacts.set_permissions(
                    &stored.owner,
                    stored.result,
                    stored.reader.subject(),
                    BTreeSet::new(),
                    9,
                )?;
            }
            2 => {
                stored.advance()?;
            }
            _ => {
                stored.artifacts.quarantine(
                    &stored.owner,
                    stored.result,
                    artifact_service::QuarantineReason::parse("P112_FIXTURE_ONLY")?,
                    9,
                )?;
            }
        }
        assert!(matches!(
            evaluated.prepare_results(&provider, WriterLimits::default(), 10),
            Err(StoredFormulaOutputError::Source)
        ));
        let called = std::cell::Cell::new(false);
        assert!(matches!(
            prepared.with_verified_bytes(&provider, 10, |_| called.set(true)),
            Err(StoredFormulaOutputError::Source)
        ));
        assert!(!called.get());
        assert!(matches!(
            prepared.require_current_product_route(&provider, 10),
            Err(StoredFormulaOutputError::Source)
        ));
    }
    Ok(())
}
#[test]
fn five_actor_and_document_scope_substitutions_reject_preparation_and_cached_consumption()
-> TestResult {
    let bytes = changed()?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let fields = source.import_field_ranges(&provider, 5)?;
    let meanings = fields.import_semantics(&provider, 6)?;
    let evaluated = meanings.evaluate_table_formulas(&provider, 7)?;
    let prepared = evaluated.prepare_results(&provider, WriterLimits::default(), 8)?;
    for variant in 0..5 {
        let tenant = if variant == 4 {
            TenantId::new(uuid::Uuid::from_u128(11201))?
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
            revision_service::ProjectId::parse("prj_11200000000000000000000000000002")?
        } else {
            stored.project
        };
        let branch = if variant == 1 {
            revision_service::BranchId::parse("brn_11200000000000000000000000000002")?
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
            evaluated.prepare_results(&other, WriterLimits::default(), 9),
            Err(StoredFormulaOutputError::Source)
        ));
        let called = std::cell::Cell::new(false);
        assert!(matches!(
            prepared.with_verified_bytes(&other, 9, |_| called.set(true)),
            Err(StoredFormulaOutputError::Source)
        ));
        assert!(!called.get());
    }
    Ok(())
}
