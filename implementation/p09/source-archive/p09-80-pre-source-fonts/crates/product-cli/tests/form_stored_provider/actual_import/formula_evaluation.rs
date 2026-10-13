use super::field_ranges::fixture as forms_fixture;
use super::*;
use domain_ir::formula_evaluation::EvaluationError;
use hwpx_agent_cli::form_stored_provider::actual_import::field_ranges::semantics::{
    StoredFieldSemanticImportError, evaluation::StoredFormulaEvaluationError,
};
use hwpx_package::document_import::fields::{
    ImportedDocumentFields,
    semantics::{
        ImportedDocumentFieldSemantics,
        evaluation::{ImportedSourceFormulaEvaluation, SourceFormulaEvaluationError},
    },
};
#[path = "../../../../hwpx-package/tests/support/document_import_formula_evaluation_fixture.rs"]
mod fixture;

#[test]
fn every_locked_actual_source_evaluates_like_direct_without_ingest_head_or_full_route() -> TestResult
{
    let mut counts = (0, 0, 0);
    for bytes in fixture::inputs::actual_corpus()? {
        let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
        let provider = stored.provider()?;
        let source = provider.import_actual_forms(stored.head, 4)?;
        let fields = source.import_field_ranges(&provider, 5)?;
        let meanings = fields.import_semantics(&provider, 6)?;
        let before = meanings.graph().clone();
        let evaluated = meanings.evaluate_table_formulas(&provider, 7)?;
        let forms = forms_fixture::forms(&bytes, "actual-form-document")?;
        let direct_fields = ImportedDocumentFields::import(&forms)?;
        let direct_meanings = ImportedDocumentFieldSemantics::import(&direct_fields)?;
        let direct = ImportedSourceFormulaEvaluation::import(&direct_meanings)?;
        assert_eq!(evaluated.values(), direct.values());
        assert_eq!(evaluated.source_bindings(), direct.source_bindings());
        assert_eq!(evaluated.receipt().evaluation, *direct.receipt());
        assert_eq!(meanings.graph(), &before);
        assert_eq!(evaluated.verify(&provider, 8)?, *evaluated.receipt());
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
        assert!(matches!(
            FullDocumentFormContext::bind(
                meanings.graph(),
                meanings.graph().canonical_sha256()?,
                evaluated.receipt().evaluation.source_package_sha256,
                RevisionId::parse("formula-evaluation-revision")?,
            ),
            Err(FullDocumentFormError::Projection)
        ));
        counts.0 += 1;
        counts.1 += evaluated.receipt().evaluation.formula_targets;
        counts.2 += evaluated.receipt().evaluation.source_cell_bindings;
    }
    assert_eq!(counts, (36, 16, 128));
    Ok(())
}

#[test]
fn fresh_and_cached_evaluation_reject_actual_aead_acl_head_and_quarantine_changes() -> TestResult {
    let bytes = fixture::inputs::actual_corpus()?.remove(0);
    for failure in 0..4 {
        let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
        let provider = stored.provider()?;
        let source = provider.import_actual_forms(stored.head, 4)?;
        let fields = source.import_field_ranges(&provider, 5)?;
        let meanings = fields.import_semantics(&provider, 6)?;
        let evaluated = meanings.evaluate_table_formulas(&provider, 7)?;
        match failure {
            0 => stored.blobs.tamper.store(true, Ordering::SeqCst),
            1 => {
                stored.artifacts.set_permissions(
                    &stored.owner,
                    stored.result,
                    stored.reader.subject(),
                    BTreeSet::new(),
                    8,
                )?;
            }
            2 => {
                stored.advance()?;
            }
            _ => {
                stored.artifacts.quarantine(
                    &stored.owner,
                    stored.result,
                    artifact_service::QuarantineReason::parse("P79_FIXTURE_QUARANTINE")?,
                    8,
                )?;
            }
        }
        for denied in [
            meanings
                .evaluate_table_formulas(&provider, 9)
                .map(|v| v.receipt().clone()),
            evaluated.verify(&provider, 9),
        ] {
            assert!(matches!(
                denied,
                Err(StoredFormulaEvaluationError::Source(
                    StoredFieldSemanticImportError::Source(_)
                ))
            ));
        }
    }
    Ok(())
}

#[test]
fn five_authentication_scope_substitutions_reject_new_and_cached_numeric_models() -> TestResult {
    let bytes = fixture::inputs::actual_corpus()?.remove(0);
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let fields = source.import_field_ranges(&provider, 5)?;
    let meanings = fields.import_semantics(&provider, 6)?;
    let evaluated = meanings.evaluate_table_formulas(&provider, 7)?;
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
        assert!(meanings.evaluate_table_formulas(&other, 8).is_err());
        assert!(evaluated.verify(&other, 8).is_err());
    }
    Ok(())
}

#[test]
fn missing_document_read_scope_rejects_provider_before_numeric_model_reuse() -> TestResult {
    let bytes = fixture::inputs::actual_corpus()?.remove(0);
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let fields = source.import_field_ranges(&provider, 5)?;
    let meanings = fields.import_semantics(&provider, 6)?;
    let evaluated = meanings.evaluate_table_formulas(&provider, 7)?;
    let actor = RequestContext::new(stored.reader.tenant_id(), stored.reader.subject(), []);
    let denied = StoredFormProvider::bind(
        &stored.artifacts,
        &stored.revisions,
        &actor,
        &stored.revision_context,
        stored.project,
        stored.branch,
        DocumentId::parse("actual-form-document")?,
    );
    assert!(matches!(denied, Err(StoredFormError::Scope)));
    // The original bind guard stops the unauthorized path before a provider
    // exists. The separately authorized immutable provider remains valid.
    assert_eq!(evaluated.verify(&provider, 8)?, *evaluated.receipt());
    Ok(())
}

#[test]
fn authorized_nonnumeric_source_rejects_math_without_ingest_or_cache_fallback() -> TestResult {
    let bytes = fixture::inputs::actual_corpus()?.remove(0);
    let changed = fixture::mutate_first_cell(&bytes, |cell| fixture::replace_first_text(cell, ""))?;
    let stored = StoredFixture::new(&changed, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let fields = source.import_field_ranges(&provider, 5)?;
    let meanings = fields.import_semantics(&provider, 6)?;
    let before = meanings.graph().clone();
    assert!(matches!(
        meanings.evaluate_table_formulas(&provider, 7),
        Err(StoredFormulaEvaluationError::Evaluation(
            SourceFormulaEvaluationError::Math(EvaluationError::MissingValue)
        ))
    ));
    assert_eq!(meanings.graph(), &before);
    assert_eq!(
        stored
            .metadata
            .audit_events()?
            .iter()
            .filter(|e| e.event == "artifact.ingested")
            .count(),
        2
    );
    assert_eq!(
        stored
            .revisions
            .head(&stored.revision_context, stored.project, stored.branch)?,
        stored.head
    );
    Ok(())
}

#[test]
fn authorized_actual_source_cycle_rejects_without_using_old_cached_value() -> TestResult {
    let original = fixture::inputs::actual_corpus()?.remove(0);
    let bytes = fixture::replace_formula(&original, "=SUM(D2:D2)")?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let fields = source.import_field_ranges(&provider, 5)?;
    let meanings = fields.import_semantics(&provider, 6)?;
    assert!(matches!(
        meanings.evaluate_table_formulas(&provider, 7),
        Err(StoredFormulaEvaluationError::Evaluation(
            SourceFormulaEvaluationError::Math(EvaluationError::Cycle)
        ))
    ));
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
