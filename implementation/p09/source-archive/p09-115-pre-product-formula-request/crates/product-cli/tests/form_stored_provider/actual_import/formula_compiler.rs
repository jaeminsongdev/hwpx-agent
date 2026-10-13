use super::*;
use super::field_ranges::fixture as forms_fixture;
use domain_ir::{CanonicalArgumentValue, NodeKind, OperationPlanLimits, PlanId};
use hwpx_package::{WriterLimits, document_import::fields::semantics::evaluation::ImportedSourceFormulaEvaluation};
use hwpx_agent_cli::form_stored_provider::actual_import::field_ranges::semantics::evaluation::output::{
    StoredFormulaOutputError, compiler::StoredFormulaCompilerError,
};
#[path = "formula_compiler/fixture.rs"]
mod fixture;

fn bytes() -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    let bytes = fixture::two_sections(&fixture::batch("5")?, &fixture::batch("101")?)?;
    fixture::index_source(&bytes)?;
    Ok(bytes)
}
#[test]
fn actual_multi_section_compiler_targets_original_source_fields_and_whole_candidate_without_publication()
-> TestResult {
    let bytes = bytes()?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let fields = source.import_field_ranges(&provider, 5)?;
    let meanings = fields.import_semantics(&provider, 6)?;
    let evaluation = meanings.evaluate_table_formulas(&provider, 7)?;
    let results = evaluation.prepare_results(&provider, WriterLimits::default(), 8)?;
    let plan = results.compile(&provider, PlanId::parse("formula-batch-plan")?, 9)?;
    assert_eq!(plan.compiled().operations().len(), 4);
    assert_eq!(
        plan.compiled().base_graph_sha256(),
        meanings.graph().canonical_sha256()?
    );
    assert_eq!(
        plan.compiled().base_revision().as_str(),
        stored.head.revision_id().ok_or("head")?.public_id()
    );
    for (field, operation) in fields.fields().iter().zip(plan.compiled().operations()) {
        assert_eq!(operation.target().node_id(), &field.begin_node_id);
        assert_eq!(operation.target().node_kind(), NodeKind::Field);
        assert_eq!(operation.capability_id().as_str(), "table.formula");
        let expected = evaluation
            .values()
            .iter()
            .find(|v| v.reference_id == field.reference_id)
            .ok_or("value")?;
        assert_eq!(
            operation.arguments()["target_decimal_json"].value(),
            &CanonicalArgumentValue::Text(serde_json::to_string(&expected.value)?)
        );
    }
    assert_eq!(plan.verify(&provider, 10)?, *plan.receipt());
    let candidate = plan.with_verified_bytes(&provider, 11, <[u8]>::to_vec)?;
    let forms = forms_fixture::forms(&bytes, "actual-form-document")?;
    let direct_fields =
        hwpx_package::document_import::fields::ImportedDocumentFields::import(&forms)?;
    let direct_meanings =
        hwpx_package::document_import::fields::semantics::ImportedDocumentFieldSemantics::import(
            &direct_fields,
        )?;
    let direct = ImportedSourceFormulaEvaluation::import(&direct_meanings)?;
    let expected = direct
        .lower_results(&bytes, WriterLimits::default())?
        .with_verified_bytes(<[u8]>::to_vec)?;
    assert_eq!(candidate, expected);
    let restored = domain_ir::CompiledOperationPlan::from_canonical_json(
        &plan.compiled().canonical_json()?,
        OperationPlanLimits::default(),
    )?;
    assert_eq!(&restored, plan.compiled());
    assert!(matches!(
        plan.require_current_product_route(&provider, 12),
        Err(StoredFormulaCompilerError::Source(
            StoredFormulaOutputError::RouteUnqualified
        ))
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
            .filter(|e| e.event == "artifact.ingested")
            .count(),
        2
    );
    Ok(())
}
#[test]
fn mixed_current_and_empty_results_compile_only_changed_actual_fields() -> TestResult {
    let changed = fixture::blank_results(&fixture::batch("5")?, true)?;
    let second = fixture::batch("101")?;
    let forms = forms_fixture::forms(&second, "actual-form-document")?;
    let fields = hwpx_package::document_import::fields::ImportedDocumentFields::import(&forms)?;
    let meanings =
        hwpx_package::document_import::fields::semantics::ImportedDocumentFieldSemantics::import(
            &fields,
        )?;
    let current = ImportedSourceFormulaEvaluation::import(&meanings)?
        .lower_results(&second, WriterLimits::default())?
        .with_verified_bytes(<[u8]>::to_vec)?;
    let mixed = fixture::two_sections(&changed, &current)?;
    let stored = StoredFixture::new(&mixed, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let ranges = source.import_field_ranges(&provider, 5)?;
    let meanings = ranges.import_semantics(&provider, 6)?;
    let evaluated = meanings.evaluate_table_formulas(&provider, 7)?;
    let results = evaluated.prepare_results(&provider, WriterLimits::default(), 8)?;
    let plan = results.compile(&provider, PlanId::parse("formula-mixed-plan")?, 9)?;
    assert_eq!(plan.compiled().operations().len(), 2);
    assert_eq!(plan.receipt().output.formula_targets, 4);
    assert_eq!(plan.receipt().output.changed_parts, 1);
    let candidate = plan.with_verified_bytes(&provider, 10, <[u8]>::to_vec)?;
    assert_eq!(
        fixture::entries(&candidate)?["Contents/section1.xml"],
        fixture::entries(&mixed)?["Contents/section1.xml"]
    );
    let other = results.compile(&provider, PlanId::parse("formula-mixed-another-plan")?, 11)?;
    assert_ne!(
        plan.receipt().compiled_plan_sha256,
        other.receipt().compiled_plan_sha256
    );
    assert_eq!(plan.receipt().output, other.receipt().output);
    Ok(())
}
#[test]
fn fresh_acl_aead_head_and_quarantine_changes_deny_compilation_and_never_invoke_cached_consumer()
-> TestResult {
    for failure in 0..4 {
        let stored = StoredFixture::new(&bytes()?, ArtifactKind::Result, false)?;
        let provider = stored.provider()?;
        let source = provider.import_actual_forms(stored.head, 4)?;
        let fields = source.import_field_ranges(&provider, 5)?;
        let meanings = fields.import_semantics(&provider, 6)?;
        let evaluated = meanings.evaluate_table_formulas(&provider, 7)?;
        let results = evaluated.prepare_results(&provider, WriterLimits::default(), 8)?;
        let plan = results.compile(&provider, PlanId::parse("formula-access-plan")?, 9)?;
        match failure {
            0 => stored.blobs.tamper.store(true, Ordering::SeqCst),
            1 => {
                stored.artifacts.set_permissions(
                    &stored.owner,
                    stored.result,
                    stored.reader.subject(),
                    BTreeSet::new(),
                    10,
                )?;
            }
            2 => {
                stored.advance()?;
            }
            _ => {
                stored.artifacts.quarantine(
                    &stored.owner,
                    stored.result,
                    artifact_service::QuarantineReason::parse("P114_FIXTURE_ONLY")?,
                    10,
                )?;
            }
        }
        assert!(matches!(
            results.compile(&provider, PlanId::parse("formula-access-plan")?, 11),
            Err(StoredFormulaCompilerError::Source(
                StoredFormulaOutputError::Source
            ))
        ));
        let called = std::cell::Cell::new(false);
        assert!(matches!(
            plan.with_verified_bytes(&provider, 11, |_| called.set(true)),
            Err(StoredFormulaCompilerError::Source(
                StoredFormulaOutputError::Source
            ))
        ));
        assert!(!called.get());
        assert!(matches!(
            plan.require_current_product_route(&provider, 11),
            Err(StoredFormulaCompilerError::Source(
                StoredFormulaOutputError::Source
            ))
        ));
    }
    Ok(())
}
#[test]
fn provider_scope_substitutions_cannot_rebind_compiled_batch_or_release_candidates() -> TestResult {
    let stored = StoredFixture::new(&bytes()?, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let fields = source.import_field_ranges(&provider, 5)?;
    let meanings = fields.import_semantics(&provider, 6)?;
    let evaluated = meanings.evaluate_table_formulas(&provider, 7)?;
    let results = evaluated.prepare_results(&provider, WriterLimits::default(), 8)?;
    let plan = results.compile(&provider, PlanId::parse("formula-scope-plan")?, 9)?;
    for variant in 0..5 {
        let tenant = if variant == 4 {
            TenantId::new(uuid::Uuid::from_u128(11401))?
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
            revision_service::ProjectId::parse("prj_11400000000000000000000000000002")?
        } else {
            stored.project
        };
        let branch = if variant == 1 {
            revision_service::BranchId::parse("brn_11400000000000000000000000000002")?
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
        assert!(
            results
                .compile(&other, PlanId::parse("formula-scope-plan")?, 10)
                .is_err()
        );
        let called = std::cell::Cell::new(false);
        assert!(
            plan.with_verified_bytes(&other, 10, |_| called.set(true))
                .is_err()
        );
        assert!(!called.get());
    }
    Ok(())
}
#[test]
fn protected_or_invalid_second_section_never_creates_a_partial_stored_plan() -> TestResult {
    let protected = fixture::protect(&bytes()?, "Contents/section1.xml", 1)?;
    let stored = StoredFixture::new(&protected, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let fields = source.import_field_ranges(&provider, 5)?;
    let meanings = fields.import_semantics(&provider, 6)?;
    let evaluation = meanings.evaluate_table_formulas(&provider, 7)?;
    assert!(matches!(
        evaluation.prepare_results(&provider, WriterLimits::default(), 8),
        Err(StoredFormulaOutputError::Output)
    ));
    let invalid = fixture::two_sections(&fixture::batch("5")?, &fixture::batch("NON-NUMERIC")?)?;
    let stored = StoredFixture::new(&invalid, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let fields = source.import_field_ranges(&provider, 5)?;
    let meanings = fields.import_semantics(&provider, 6)?;
    assert!(meanings.evaluate_table_formulas(&provider, 7).is_err());
    Ok(())
}
#[test]
fn actual_field_graph_and_compiled_candidate_do_not_become_full_import_or_issuer_authority()
-> TestResult {
    let stored = StoredFixture::new(&bytes()?, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let fields = source.import_field_ranges(&provider, 5)?;
    let meanings = fields.import_semantics(&provider, 6)?;
    let evaluation = meanings.evaluate_table_formulas(&provider, 7)?;
    let results = evaluation.prepare_results(&provider, WriterLimits::default(), 8)?;
    let plan = results.compile(&provider, PlanId::parse("formula-incomplete-plan")?, 9)?;
    assert!(matches!(
        FullDocumentFormContext::bind(
            meanings.graph(),
            meanings.graph().canonical_sha256()?,
            evaluation.receipt().evaluation.source_package_sha256,
            plan.compiled().base_revision().clone()
        ),
        Err(FullDocumentFormError::Projection)
    ));
    assert!(!plan.receipt().output.native_recalculation_verified);
    let debug = format!("{plan:?}");
    assert_eq!(debug, "PreparedStoredFormulaPlan(<redacted>)");
    assert!(!serde_json::to_string(plan.receipt())?.contains("target_decimal_json"));
    Ok(())
}
