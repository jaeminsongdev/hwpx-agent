//! Actual original repositories/services with synthetic in-memory keys; not native/SQL/publication.
use super::super::fixture as form_fixture;
use super::formula_compiler::fixture;
use super::*;
use domain_ir::PlanId;
use hwpx_agent_cli::form_product_request::{
    FORM_PRODUCT_REQUEST_SCHEMA,
    stored::{StoredProductFormBindings, StoredProductFormRequest},
    stored_operations::{
        PreparedStoredProductOperation, StoredProductOperationError, StoredProductRequest,
        formula::{FormulaPreparationReceipt, PRODUCT_OPERATION_REQUEST_SCHEMA},
    },
};
use hwpx_package::WriterLimits;
use serde_json::{Value, json};
fn bytes() -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    fixture::two_sections(&fixture::batch("5")?, &fixture::batch("101")?)
}
fn request(stored: &StoredFixture, bytes: &[u8]) -> TestResultValue {
    Ok(json!({
        "schema_version": PRODUCT_OPERATION_REQUEST_SCHEMA,
        "idempotency_key": "P115-private-synthetic-key",
        "project_id":stored.project.public_id(),"document_id":"actual-form-document",
        "base_revision":stored.head.revision_id().ok_or("head")?.public_id(),
        "expected_head_generation":stored.head.generation(),
        "expected_source_package_sha256":ContentDigest::of(bytes).hex(),
        "plan_id":"product-formula-plan","operation":{"kind":"recalculate_table_formulas"}
    }))
}
type TestResultValue = Result<Value, Box<dyn std::error::Error>>;
fn prepare(
    stored: &StoredFixture,
    request: &Value,
) -> Result<PreparedStoredProductOperation, Box<dyn std::error::Error>> {
    Ok(StoredProductRequest::prepare_json(
        &stored.provider()?,
        &serde_json::to_vec(request)?,
        None,
        8,
    )?)
}
fn assert_no_publication(stored: &StoredFixture) -> TestResult {
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
fn current(bytes: &[u8]) -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    let forms = super::field_ranges::fixture::forms(bytes, "actual-form-document")?;
    let fields = hwpx_package::document_import::fields::ImportedDocumentFields::import(&forms)?;
    let meanings =
        hwpx_package::document_import::fields::semantics::ImportedDocumentFieldSemantics::import(
            &fields,
        )?;
    Ok(hwpx_package::document_import::fields::semantics::evaluation::ImportedSourceFormulaEvaluation::import(&meanings)?
        .lower_results(bytes,WriterLimits::default())?.with_verified_bytes(<[u8]>::to_vec)?)
}
#[test]
fn common_strict_product_entry_compiles_source_four_fields_and_preserves_original_whole_candidate()
-> TestResult {
    let bytes = bytes()?;
    fixture::index_source(&bytes)?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let prepared = prepare(&stored, &request(&stored, &bytes)?)?;
    let PreparedStoredProductOperation::TableFormulas(formula) = &prepared else {
        return Err("formula variant".into());
    };
    assert_eq!(formula.compiled().ok_or("plan")?.operations().len(), 4);
    assert_eq!(
        formula.compiled().ok_or("plan")?.plan_id(),
        &PlanId::parse("product-formula-plan")?
    );
    assert!(matches!(
        formula.receipt().formula,
        FormulaPreparationReceipt::Changed { .. }
    ));
    let candidate = prepared.with_verified_bytes(&stored.provider()?, None, 9, <[u8]>::to_vec)?;
    assert_eq!(candidate, current(&bytes)?);
    assert!(
        prepared
            .require_current_product_route(&stored.provider()?, None, 10)
            .is_err()
    );
    assert_no_publication(&stored)
}
#[test]
fn current_whole_formula_results_are_true_noop_without_fabricating_empty_plan_or_execution()
-> TestResult {
    let bytes = current(&bytes()?)?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let prepared = prepare(&stored, &request(&stored, &bytes)?)?;
    let PreparedStoredProductOperation::TableFormulas(formula) = &prepared else {
        return Err("formula variant".into());
    };
    assert!(formula.compiled().is_none());
    let FormulaPreparationReceipt::Unchanged { source } = &formula.receipt().formula else {
        return Err("unchanged receipt".into());
    };
    assert_eq!(source.formula_targets, 4);
    assert!(source.original_lowerer_no_change_and_protection_checks_verified);
    assert!(!source.native_recalculation_verified);
    assert_eq!(source.execution_publication_authority, "unqualified");
    assert_eq!(
        prepared.with_verified_bytes(&stored.provider()?, None, 9, <[u8]>::to_vec)?,
        bytes
    );
    assert!(matches!(
        prepared.require_current_product_route(&stored.provider()?, None, 10),
        Err(StoredProductOperationError::RouteUnqualified)
    ));
    assert_no_publication(&stored)
}
#[test]
fn mixed_empty_and_current_sections_keep_original_unchanged_part_and_only_two_changed_operations()
-> TestResult {
    let bytes = fixture::two_sections(
        &fixture::blank_results(&fixture::batch("5")?, true)?,
        &current(&fixture::batch("101")?)?,
    )?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let prepared = prepare(&stored, &request(&stored, &bytes)?)?;
    let PreparedStoredProductOperation::TableFormulas(formula) = &prepared else {
        return Err("formula variant".into());
    };
    assert_eq!(formula.compiled().ok_or("plan")?.operations().len(), 2);
    let candidate = prepared.with_verified_bytes(&stored.provider()?, None, 9, <[u8]>::to_vec)?;
    assert_eq!(
        fixture::entries(&candidate)?["Contents/section1.xml"],
        fixture::entries(&bytes)?["Contents/section1.xml"]
    );
    assert_no_publication(&stored)
}
#[test]
fn strict_original_duplicate_parser_rejects_unknown_values_operations_coercions_and_limits_before_reads()
-> TestResult {
    let bytes = bytes()?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let base = request(&stored, &bytes)?;
    let raw = serde_json::to_string(&base)?;
    let mut bad = vec![
        format!("{{\"schema_version\":\"wrong\",{}", &raw[1..]).into_bytes(),
        format!("{raw} trailing").into_bytes(),
        Vec::new(),
        vec![b' '; 2 * 1024 * 1024 + 1],
    ];
    for field in [
        "schema_version",
        "project_id",
        "document_id",
        "base_revision",
        "idempotency_key",
        "plan_id",
        "operation",
    ] {
        let mut v = base.clone();
        v.as_object_mut().ok_or("object")?.remove(field);
        bad.push(serde_json::to_vec(&v)?);
    }
    for operation in [
        json!({"kind":"recalculate_table_formulas","values":[1]}),
        json!({"kind":"caller_ast"}),
        json!(["recalculate_table_formulas"]),
        json!({"kind":1}),
        Value::Null,
    ] {
        let mut v = base.clone();
        v["operation"] = operation;
        bad.push(serde_json::to_vec(&v)?);
    }
    for field in [
        "artifact_id",
        "path",
        "graph",
        "map",
        "policy",
        "access",
        "approval",
        "form_input",
        "expected_results",
    ] {
        let mut v = base.clone();
        v[field] = json!({});
        bad.push(serde_json::to_vec(&v)?);
    }
    for generation in [json!(0), json!("1"), json!(1.5), Value::Null] {
        let mut v = base.clone();
        v["expected_head_generation"] = generation;
        bad.push(serde_json::to_vec(&v)?);
    }
    bad.push(
        raw.replace(
            "\"kind\":\"recalculate_table_formulas\"",
            "\"kind\":\"recalculate_table_formulas\",\"k\\u0069nd\":\"recalculate_table_formulas\"",
        )
        .into_bytes(),
    );
    let before = stored.metadata.audit_events()?.len();
    for raw in bad {
        assert!(matches!(
            StoredProductRequest::prepare_json(&stored.provider()?, &raw, None, 8),
            Err(StoredProductOperationError::Request(_))
        ));
    }
    assert_eq!(stored.metadata.audit_events()?.len(), before);
    assert_no_publication(&stored)
}
#[test]
fn identity_mismatches_and_advanced_head_deny_original_provider_before_formula_preparation()
-> TestResult {
    let bytes = bytes()?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let base = request(&stored, &bytes)?;
    for (field, value) in [
        ("project_id", json!("prj_11500000000000000000000000000001")),
        ("document_id", json!("other-document")),
        (
            "base_revision",
            json!("rev_11500000000000000000000000000001"),
        ),
        (
            "expected_head_generation",
            json!(stored.head.generation() + 1),
        ),
        ("expected_source_package_sha256", json!("0".repeat(64))),
    ] {
        let mut v = base.clone();
        v[field] = value;
        assert!(
            StoredProductRequest::prepare_json(
                &stored.provider()?,
                &serde_json::to_vec(&v)?,
                None,
                8
            )
            .is_err()
        );
    }
    let prepared = prepare(&stored, &base)?;
    stored.advance()?;
    let called = std::cell::Cell::new(false);
    assert!(
        prepared
            .with_verified_bytes(&stored.provider()?, None, 9, |_| called.set(true))
            .is_err()
    );
    assert!(!called.get());
    assert!(prepare(&stored, &base).is_err());
    Ok(())
}
#[test]
fn changed_and_noop_cached_products_recheck_acl_aead_quarantine_before_candidate_or_route()
-> TestResult {
    for noop in [false, true] {
        for failure in 0..3 {
            let changed = bytes()?;
            let bytes = if noop { current(&changed)? } else { changed };
            let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
            let base = request(&stored, &bytes)?;
            let prepared = prepare(&stored, &base)?;
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
                _ => {
                    stored.artifacts.quarantine(
                        &stored.owner,
                        stored.result,
                        artifact_service::QuarantineReason::parse("P115_FIXTURE_ONLY")?,
                        9,
                    )?;
                }
            }
            let called = std::cell::Cell::new(false);
            assert!(
                prepared
                    .with_verified_bytes(&stored.provider()?, None, 10, |_| called.set(true))
                    .is_err()
            );
            assert!(!called.get());
            assert!(
                prepared
                    .require_current_product_route(&stored.provider()?, None, 10)
                    .is_err()
            );
            assert!(prepare(&stored, &base).is_err());
            assert_no_publication(&stored)?;
        }
    }
    Ok(())
}
#[test]
fn nochange_protected_and_invalid_second_section_cannot_be_successful_noop_or_partial_product()
-> TestResult {
    for bytes in [
        fixture::protect(&current(&bytes()?)?, "Contents/section1.xml", 1)?,
        fixture::protect(&bytes()?, "Contents/section1.xml", 1)?,
        fixture::two_sections(&fixture::batch("5")?, &fixture::batch("NON-NUMERIC")?)?,
    ] {
        let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
        assert!(prepare(&stored, &request(&stored, &bytes)?).is_err());
        assert_no_publication(&stored)?;
    }
    Ok(())
}
#[test]
fn canonical_retry_key_and_plan_id_are_request_data_not_idempotency_claims_or_public_secrets()
-> TestResult {
    let bytes = bytes()?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let mut base = request(&stored, &bytes)?;
    let compact = serde_json::to_vec(&base)?;
    let pretty = serde_json::to_vec_pretty(&base)?;
    let a = StoredProductRequest::prepare_json(&stored.provider()?, &compact, None, 8)?;
    let b = StoredProductRequest::prepare_json(&stored.provider()?, &pretty, None, 8)?;
    let PreparedStoredProductOperation::TableFormulas(a) = a else {
        return Err("formula".into());
    };
    let PreparedStoredProductOperation::TableFormulas(b) = b else {
        return Err("formula".into());
    };
    assert_ne!(
        a.receipt().raw_request_sha256,
        b.receipt().raw_request_sha256
    );
    assert_eq!(
        a.receipt().canonical_request_sha256,
        b.receipt().canonical_request_sha256
    );
    assert_eq!(
        a.receipt().request_identity_sha256,
        b.receipt().request_identity_sha256
    );
    assert_eq!(a.compiled(), b.compiled());
    base["idempotency_key"] = json!("P115-another-private-key");
    let other = prepare(&stored, &base)?;
    let PreparedStoredProductOperation::TableFormulas(other) = other else {
        return Err("formula".into());
    };
    assert_ne!(
        a.receipt().request_identity_sha256,
        other.receipt().request_identity_sha256
    );
    assert_eq!(a.compiled(), other.compiled());
    base["plan_id"] = json!("product-formula-another-plan");
    let other = prepare(&stored, &base)?;
    let PreparedStoredProductOperation::TableFormulas(other) = other else {
        return Err("formula".into());
    };
    assert_ne!(a.compiled(), other.compiled());
    let receipt = serde_json::to_string(a.receipt())?;
    for private in [
        "P115-private-synthetic-key",
        "actual-form-document",
        "product-formula-plan",
        "target_decimal_json",
        "artifact_id",
    ] {
        assert!(!receipt.contains(private));
    }
    assert_eq!(format!("{a:?}"), "PreparedStoredProductFormula(<redacted>)");
    assert_no_publication(&stored)
}
#[test]
fn common_dispatch_keeps_v1_original_form_candidate_and_rejects_missing_or_cross_kind_bindings()
-> TestResult {
    let form = form_fixture()?;
    let stored = StoredFixture::new(&form.source, ArtifactKind::Result, false)?;
    let (input, access) = form.request("P115 synthetic new value")?;
    let binding = StoredProductFormBindings {
        map: &form.map,
        policies: &form.policies,
        access: &access,
    };
    let mut v = request(&stored, &form.source)?;
    v["schema_version"] = json!(FORM_PRODUCT_REQUEST_SCHEMA);
    v.as_object_mut().ok_or("object")?.remove("operation");
    v["form_input"] = input;
    let raw = serde_json::to_vec(&v)?;
    let old = StoredProductFormRequest::prepare_json(&stored.provider()?, &raw, &binding, 8)?;
    let new = StoredProductRequest::prepare_json(&stored.provider()?, &raw, Some(&binding), 8)?;
    assert!(matches!(new, PreparedStoredProductOperation::Form(_)));
    assert_eq!(
        new.with_verified_bytes(&stored.provider()?, Some(&binding), 9, <[u8]>::to_vec)?,
        old.candidate_bytes()
    );
    assert!(StoredProductRequest::prepare_json(&stored.provider()?, &raw, None, 8).is_err());
    assert!(
        new.with_verified_bytes(&stored.provider()?, None, 9, |_| ())
            .is_err()
    );
    assert!(
        new.require_current_product_route(&stored.provider()?, Some(&binding), 9)
            .is_err()
    );
    let formula = request(&stored, &form.source)?;
    let before = stored.metadata.audit_events()?.len();
    assert!(matches!(
        StoredProductRequest::prepare_json(
            &stored.provider()?,
            &serde_json::to_vec(&formula)?,
            Some(&binding),
            9
        ),
        Err(StoredProductOperationError::Bindings)
    ));
    assert_eq!(stored.metadata.audit_events()?.len(), before);
    assert_no_publication(&stored)
}
