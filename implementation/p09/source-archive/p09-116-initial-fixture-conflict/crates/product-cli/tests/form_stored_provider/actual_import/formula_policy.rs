//! Synthetic policy repository/keys, real original artifact/source/compiler checks. Not SQL/native.
use super::formula_compiler::fixture;
use super::*;
use artifact_service::{ArtifactPermission, FileName, IngestRequest, MediaType, SubjectDigest};
use hwpx_agent_cli::{
    form_product_request::stored_operations::{
        StoredProductRequest,
        formula::{FormulaPreparationReceipt, PRODUCT_OPERATION_REQUEST_SCHEMA},
        policy::{PolicyFormulaProductError, PreparedPolicyFormulaProduct},
    },
    form_stored_provider::actual_import::{
        StoredImportedDocumentForms,
        source_policy::{
            PolicyReadScope, SOURCE_POLICY_MEDIA_TYPE, SourcePolicyBinding, SourcePolicyVersion,
            formulas::*,
        },
    },
};
use hwpx_package::document_import::fields::semantics::ImportedFieldMeaning;
use serde_json::{Value, json};
use std::sync::{Mutex, atomic::AtomicUsize};
use uuid::Uuid;
type AnyResult<T> = Result<T, Box<dyn std::error::Error>>;

struct Repository {
    row: Mutex<SourcePolicyVersion>,
    subject: SubjectDigest,
    calls: AtomicUsize,
    deny_at: AtomicUsize,
}
impl FormulaPolicyRepository for Repository {
    fn read_current_formula_policy(
        &self,
        scope: &PolicyReadScope,
    ) -> Result<SourcePolicyVersion, StoredFormulaPolicyError> {
        let n = self.calls.fetch_add(1, Ordering::SeqCst);
        if n >= self.deny_at.load(Ordering::SeqCst) || scope.subject() != self.subject {
            return Err(StoredFormulaPolicyError::Repository);
        }
        self.row
            .lock()
            .map_err(|_| StoredFormulaPolicyError::Repository)
            .map(|r| r.clone())
    }
}
fn bytes() -> AnyResult<Vec<u8>> {
    fixture::two_sections(&fixture::batch("5")?, &fixture::batch("101")?)
}
fn current(bytes: &[u8]) -> AnyResult<Vec<u8>> {
    let forms = super::field_ranges::fixture::forms(bytes, "actual-form-document")?;
    let fields = hwpx_package::document_import::fields::ImportedDocumentFields::import(&forms)?;
    let meanings =
        hwpx_package::document_import::fields::semantics::ImportedDocumentFieldSemantics::import(
            &fields,
        )?;
    Ok(hwpx_package::document_import::fields::semantics::evaluation::ImportedSourceFormulaEvaluation::import(&meanings)?
        .lower_results(bytes, hwpx_package::WriterLimits::default())?.with_verified_bytes(<[u8]>::to_vec)?)
}
fn payload(stored: &StoredFixture, source: &StoredImportedDocumentForms) -> AnyResult<Value> {
    let imported = source.imported();
    let binding = SourcePolicyBinding {
        tenant: stored.reader.tenant_id(),
        project: stored.project,
        branch: stored.branch,
        document: imported.graph().document_id().clone(),
        source_revision: stored.head.revision_id().ok_or("head")?,
        source_head_generation: stored.head.generation(),
        source_result_artifact: stored.result,
        source_package_sha256: ContentDigest::parse(&hex::encode(
            imported.receipt().source_package_sha256,
        ))?,
        source_provenance_sha256: ContentDigest::parse(&hex::encode(
            imported.receipt().source_provenance_sha256,
        ))?,
        observed_graph_sha256: ContentDigest::parse(&hex::encode(imported.receipt().graph_sha256))?,
        policy_version: Uuid::from_u128(11601),
        policy_generation: 1,
        creator_subject: stored.owner.subject(),
    };
    let provider = stored.provider()?;
    let fields = source.import_field_ranges(&provider, 5)?;
    let meanings = fields.import_semantics(&provider, 5)?;
    let mut targets = Vec::new();
    for m in meanings.observations() {
        if let ImportedFieldMeaning::TableFormula { formula, .. } = &m.meaning {
            let f = fields
                .fields()
                .iter()
                .find(|f| f.reference_id == m.reference_id)
                .ok_or("field")?;
            targets.push(json!({"reference_id":f.reference_id,"begin_anchor":f.begin_anchor,
                "end_anchor":f.end_anchor,"ast_sha256":ContentDigest::of(&serde_json::to_vec(formula.ast())?),
                "allow_recalculation":true}));
        }
    }
    Ok(
        json!({"schema_version":FORMULA_POLICY_SCHEMA,"binding":binding,
        "meaning_graph_sha256":ContentDigest::parse(&hex::encode(meanings.graph().canonical_sha256()?))?,
        "targets":targets}),
    )
}
fn repository(
    stored: &StoredFixture,
    value: &Value,
    raw: Vec<u8>,
    kind: ArtifactKind,
    media: &str,
) -> AnyResult<Repository> {
    let artifact = stored.artifacts.ingest(
        &stored.owner,
        IngestRequest {
            bytes: raw,
            media_type: MediaType::parse(media)?,
            file_name: FileName::parse("synthetic-formula-policy.json")?,
            kind,
        },
        6,
    )?;
    stored.artifacts.set_permissions(
        &stored.owner,
        artifact.artifact_id,
        stored.reader.subject(),
        BTreeSet::from([ArtifactPermission::Read]),
        7,
    )?;
    Ok(Repository {
        row: Mutex::new(SourcePolicyVersion {
            binding: serde_json::from_value(value["binding"].clone())?,
            artifact: artifact.artifact_id,
            digest: artifact.sha256,
        }),
        subject: stored.reader.subject(),
        calls: AtomicUsize::new(0),
        deny_at: AtomicUsize::new(usize::MAX),
    })
}
fn valid(stored: &StoredFixture, source: &StoredImportedDocumentForms) -> AnyResult<Repository> {
    let value = payload(stored, source)?;
    repository(
        stored,
        &value,
        serde_json::to_vec(&value)?,
        ArtifactKind::Evidence,
        FORMULA_POLICY_MEDIA_TYPE,
    )
}
fn request(stored: &StoredFixture, bytes: &[u8]) -> AnyResult<Vec<u8>> {
    Ok(serde_json::to_vec(
        &json!({"schema_version":PRODUCT_OPERATION_REQUEST_SCHEMA,
        "idempotency_key":"P116-private-synthetic-key","project_id":stored.project.public_id(),
        "document_id":"actual-form-document","base_revision":stored.head.revision_id().ok_or("head")?.public_id(),
        "expected_head_generation":stored.head.generation(),"expected_source_package_sha256":ContentDigest::of(bytes),
        "plan_id":"formula-policy-plan","operation":{"kind":"recalculate_table_formulas"}}),
    )?)
}
fn prepare(
    stored: &StoredFixture,
    repo: &Repository,
    bytes: &[u8],
) -> AnyResult<PreparedPolicyFormulaProduct> {
    Ok(StoredProductRequest::prepare_formula_with_policy(
        &stored.provider()?,
        repo,
        &request(stored, bytes)?,
        8,
    )?)
}
fn no_publication(stored: &StoredFixture, ingested: usize) -> TestResult {
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
        ingested
    );
    Ok(())
}

#[test]
fn actual_four_target_policy_gates_original_changed_and_current_product_candidates() -> TestResult {
    let original = bytes()?;
    for bytes in [original.clone(), current(&original)?] {
        fixture::index_source(&bytes)?;
        let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
        let provider = stored.provider()?;
        let source = provider.import_actual_forms(stored.head, 4)?;
        let repo = valid(&stored, &source)?;
        let bound = source.bind_stored_formula_policy(&provider, &repo, 8)?;
        assert_eq!(bound.receipt().formula_targets, 4);
        assert_eq!(bound.receipt().allowed_targets, 4);
        assert_eq!(
            bound.verify(&source, &provider, &repo, 9)?,
            *bound.receipt()
        );
        let prepared = prepare(&stored, &repo, &bytes)?;
        assert_eq!(prepared.verify(&provider, &repo, 9)?, *prepared.receipt());
        assert_eq!(
            prepared.with_verified_bytes(&provider, &repo, 9, <[u8]>::to_vec)?,
            current(&original)?
        );
        assert_eq!(
            matches!(
                prepared.receipt().product.formula,
                FormulaPreparationReceipt::Changed { .. }
            ),
            bytes == original
        );
        assert!(matches!(
            prepared.require_current_product_route(&provider, &repo, 9),
            Err(PolicyFormulaProductError::Product(_))
        ));
        assert!(
            prepared
                .receipt()
                .qualification
                .contains("NOT_trusted_issuer")
        );
        assert_eq!(format!("{bound:?}"), "StoredFormulaPolicy(<redacted>)");
        assert_eq!(
            format!("{prepared:?}"),
            "PreparedPolicyFormulaProduct(<redacted>)"
        );
        let receipt = serde_json::to_string(prepared.receipt())?;
        for private in [
            "P116-private-synthetic-key",
            "actual-form-document",
            "formula-policy-plan",
            "creator_subject",
        ] {
            assert!(!receipt.contains(private));
        }
        no_publication(&stored, 3)?;
    }
    Ok(())
}
#[test]
fn strict_policy_shape_unknown_duplicate_coercion_and_bounds_never_become_permissions() -> TestResult
{
    let stored = StoredFixture::new(&bytes()?, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let base = payload(&stored, &source)?;
    let mut bad = Vec::new();
    for case in 0..16 {
        let mut v = base.clone();
        match case {
            0 => v["schema_version"] = json!("wrong"),
            1 => v["approved"] = json!(true),
            2 => v["binding"]["issuer_verified"] = json!(true),
            3 => v["targets"][0]["approval"] = json!(true),
            4 => v["targets"][0]["begin_anchor"]["extra"] = json!(true),
            5 => {
                v["targets"][0]
                    .as_object_mut()
                    .ok_or("rule")?
                    .remove("allow_recalculation");
            }
            6 => v["targets"][0]["allow_recalculation"] = json!(1),
            7 => v["targets"][0]["allow_recalculation"] = json!("true"),
            8 => v["targets"][0]["allow_recalculation"] = Value::Null,
            9 => v["targets"] = json!({}),
            10 => v["binding"] = json!([]),
            11 => v["targets"][0] = json!([]),
            12 => v["targets"][0]["end_anchor"] = json!([]),
            13 => {
                v["targets"][0]["begin_anchor"] = json!([
                    base["targets"][0]["begin_anchor"]["opaque_handle"],
                    base["targets"][0]["begin_anchor"]["fingerprint_sha256"]
                ])
            }
            14 => {
                v.as_object_mut()
                    .ok_or("object")?
                    .remove("meaning_graph_sha256");
            }
            _ => v["targets"] = json!([]),
        }
        bad.push(serde_json::to_vec(&v)?);
    }
    let canonical = serde_json::to_string(&base)?;
    for (old, new) in [
        (
            "\"schema_version\":",
            "\"schema_version\":\"wrong\",\"schema_version\":",
        ),
        (
            "\"policy_generation\":1",
            "\"policy_generation\":1,\"policy_generation\":1",
        ),
        (
            "\"allow_recalculation\":true",
            "\"allow_recalculation\":true,\"allow_recalculat\\u0069on\":true",
        ),
        (
            "\"opaque_handle\":",
            "\"opaque_handle\":\"foreign\",\"opaque_handle\":",
        ),
    ] {
        assert!(canonical.contains(old));
        bad.push(canonical.replacen(old, new, 1).into_bytes());
    }
    bad.extend([
        format!("{canonical} {{}}").into_bytes(),
        serde_json::to_vec(
            &base
                .as_object()
                .ok_or("object")?
                .values()
                .collect::<Vec<_>>(),
        )?,
        b"{invalid".to_vec(),
        Vec::new(),
        vec![b' '; 1_048_577],
    ]);
    for (i, raw) in bad.into_iter().enumerate() {
        let repo = repository(
            &stored,
            &base,
            raw,
            ArtifactKind::Evidence,
            FORMULA_POLICY_MEDIA_TYPE,
        )?;
        assert!(
            source
                .bind_stored_formula_policy(&provider, &repo, 8)
                .is_err(),
            "strict_case={i}"
        );
    }
    Ok(())
}
#[test]
fn whole_actual_target_coverage_anchors_ast_graph_and_source_bindings_are_required() -> TestResult {
    let stored = StoredFixture::new(&bytes()?, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let base = payload(&stored, &source)?;
    for case in 0..10 {
        let mut v = base.clone();
        match case {
            0 => {
                v["targets"].as_array_mut().ok_or("rules")?.pop();
            }
            1 => {
                let r = v["targets"][0].clone();
                v["targets"].as_array_mut().ok_or("rules")?.push(r);
            }
            2 => v["targets"][1] = v["targets"][0].clone(),
            3 => v["targets"][0]["reference_id"] = json!("foreign-field"),
            4 => v["targets"][0]["begin_anchor"] = v["targets"][1]["begin_anchor"].clone(),
            5 => v["targets"][0]["end_anchor"] = v["targets"][1]["end_anchor"].clone(),
            6 => v["targets"][0]["ast_sha256"] = json!(ContentDigest::of(b"different AST")),
            7 => v["meaning_graph_sha256"] = json!(ContentDigest::of(b"different graph")),
            8 => v["targets"][0]["end_anchor"]["fingerprint_sha256"][0] = json!(99),
            _ => v["binding"]["policy_generation"] = json!(2),
        }
        let mut repo = repository(
            &stored,
            &v,
            serde_json::to_vec(&v)?,
            ArtifactKind::Evidence,
            FORMULA_POLICY_MEDIA_TYPE,
        )?;
        if case == 9 {
            repo.row
                .get_mut()
                .map_err(|_| "row")?
                .binding
                .policy_generation = 1;
        }
        assert!(
            source
                .bind_stored_formula_policy(&provider, &repo, 8)
                .is_err(),
            "target_case={case}"
        );
    }
    for case in 0..15 {
        let repo = valid(&stored, &source)?;
        {
            let mut row = repo.row.lock().map_err(|_| "row")?;
            let b = &mut row.binding;
            match case {
                0 => b.tenant = TenantId::new(Uuid::from_u128(11699))?,
                1 => b.project = revision_service::ProjectId::generate(),
                2 => b.branch = revision_service::BranchId::generate(),
                3 => b.document = DocumentId::parse("foreign-document")?,
                4 => b.source_revision = revision_service::RevisionId::generate(),
                5 => b.source_head_generation += 1,
                6 => b.source_result_artifact = artifact_service::ArtifactId::generate(),
                7 => b.source_package_sha256 = ContentDigest::of(b"foreign source"),
                8 => b.source_provenance_sha256 = ContentDigest::of(b"foreign provenance"),
                9 => b.observed_graph_sha256 = ContentDigest::of(b"foreign graph"),
                10 => b.policy_version = Uuid::nil(),
                11 => b.policy_generation = 0,
                12 => b.policy_generation = u64::MAX,
                13 => row.artifact = stored.result,
                _ => row.digest = ContentDigest::of(b"foreign policy"),
            }
        }
        assert!(
            source
                .bind_stored_formula_policy(&provider, &repo, 8)
                .is_err(),
            "binding_case={case}"
        );
    }
    Ok(())
}
#[test]
fn form_policy_media_or_non_evidence_artifact_never_grants_formula_permission() -> TestResult {
    let stored = StoredFixture::new(&bytes()?, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let v = payload(&stored, &source)?;
    for (kind, media) in [
        (ArtifactKind::Evidence, SOURCE_POLICY_MEDIA_TYPE),
        (ArtifactKind::Evidence, "application/json"),
        (ArtifactKind::Source, FORMULA_POLICY_MEDIA_TYPE),
        (ArtifactKind::Result, FORMULA_POLICY_MEDIA_TYPE),
        (ArtifactKind::DocumentIr, FORMULA_POLICY_MEDIA_TYPE),
    ] {
        let repo = repository(&stored, &v, serde_json::to_vec(&v)?, kind, media)?;
        assert_eq!(
            source.bind_stored_formula_policy(&provider, &repo, 8).err(),
            Some(StoredFormulaPolicyError::Artifact)
        );
    }
    Ok(())
}
#[test]
fn explicit_denial_including_current_results_prevents_product_preparation() -> TestResult {
    let original = bytes()?;
    for bytes in [original.clone(), current(&original)?] {
        let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
        let provider = stored.provider()?;
        let source = provider.import_actual_forms(stored.head, 4)?;
        let mut v = payload(&stored, &source)?;
        v["targets"][3]["allow_recalculation"] = json!(false);
        let repo = repository(
            &stored,
            &v,
            serde_json::to_vec(&v)?,
            ArtifactKind::Evidence,
            FORMULA_POLICY_MEDIA_TYPE,
        )?;
        let bound = source.bind_stored_formula_policy(&provider, &repo, 8)?;
        assert_eq!(bound.receipt().allowed_targets, 3);
        assert_eq!(
            bound.require_recalculation_data_permission(),
            Err(StoredFormulaPolicyError::Denied)
        );
        assert!(matches!(
            StoredProductRequest::prepare_formula_with_policy(
                &provider,
                &repo,
                &request(&stored, &bytes)?,
                8
            ),
            Err(PolicyFormulaProductError::Policy(
                StoredFormulaPolicyError::Denied
            ))
        ));
        no_publication(&stored, 3)?;
    }
    Ok(())
}
#[test]
fn latest_version_order_and_revocation_are_rechecked_without_old_policy_fallback() -> TestResult {
    let bytes = bytes()?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let repo = valid(&stored, &source)?;
    let bound = source.bind_stored_formula_policy(&provider, &repo, 8)?;
    let prepared = prepare(&stored, &repo, &bytes)?;
    let mut v = payload(&stored, &source)?;
    v["targets"].as_array_mut().ok_or("rules")?.reverse();
    v["binding"]["policy_version"] = json!(Uuid::from_u128(11602));
    v["binding"]["policy_generation"] = json!(2);
    let latest = repository(
        &stored,
        &v,
        serde_json::to_vec(&v)?,
        ArtifactKind::Evidence,
        FORMULA_POLICY_MEDIA_TYPE,
    )?;
    *repo.row.lock().map_err(|_| "row")? = latest.row.lock().map_err(|_| "row")?.clone();
    let fresh = source.bind_stored_formula_policy(&provider, &repo, 9)?;
    assert_eq!(
        fresh.receipt().target_bindings_sha256,
        bound.receipt().target_bindings_sha256
    );
    assert_ne!(
        fresh.receipt().policy_raw_sha256,
        bound.receipt().policy_raw_sha256
    );
    assert_eq!(
        bound.verify(&source, &provider, &repo, 9).err(),
        Some(StoredFormulaPolicyError::Drift)
    );
    let called = std::cell::Cell::new(false);
    assert!(
        prepared
            .with_verified_bytes(&provider, &repo, 9, |_| called.set(true))
            .is_err()
    );
    assert!(!called.get());
    assert!(prepare(&stored, &repo, &bytes).is_ok());
    repo.deny_at.store(0, Ordering::SeqCst);
    assert_eq!(
        fresh.verify(&source, &provider, &repo, 10).err(),
        Some(StoredFormulaPolicyError::Repository)
    );
    assert!(prepare(&stored, &repo, &bytes).is_err());
    no_publication(&stored, 4)
}
#[test]
fn policy_revocation_during_binding_and_immediately_before_callback_is_not_cached() -> TestResult {
    let bytes = bytes()?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let repo = valid(&stored, &source)?;
    repo.deny_at.store(1, Ordering::SeqCst);
    assert_eq!(
        source.bind_stored_formula_policy(&provider, &repo, 8).err(),
        Some(StoredFormulaPolicyError::Repository)
    );
    repo.deny_at.store(usize::MAX, Ordering::SeqCst);
    let prepared = prepare(&stored, &repo, &bytes)?;
    let calls = repo.calls.load(Ordering::SeqCst);
    // verify's before+after policy checks use four repository reads. Deny in the callback guard.
    repo.deny_at.store(calls + 4, Ordering::SeqCst);
    let called = std::cell::Cell::new(false);
    assert!(matches!(
        prepared.with_verified_bytes(&provider, &repo, 9, |_| called.set(true)),
        Err(PolicyFormulaProductError::Policy(
            StoredFormulaPolicyError::Repository
        ))
    ));
    assert!(!called.get());
    assert_eq!(repo.calls.load(Ordering::SeqCst), calls + 5);
    no_publication(&stored, 3)
}
#[test]
fn cached_changed_and_current_products_recheck_source_policy_acl_aead_quarantine_and_head()
-> TestResult {
    let original = bytes()?;
    for bytes in [original.clone(), current(&original)?] {
        for failure in 0..6 {
            let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
            let provider = stored.provider()?;
            let source = provider.import_actual_forms(stored.head, 4)?;
            let repo = valid(&stored, &source)?;
            let prepared = prepare(&stored, &repo, &bytes)?;
            let policy = repo.row.lock().map_err(|_| "row")?.artifact;
            match failure {
                0 | 1 => {
                    stored.artifacts.set_permissions(
                        &stored.owner,
                        if failure == 0 { policy } else { stored.result },
                        stored.reader.subject(),
                        BTreeSet::new(),
                        9,
                    )?;
                }
                2 | 3 => {
                    stored.artifacts.quarantine(
                        &stored.owner,
                        if failure == 2 { policy } else { stored.result },
                        artifact_service::QuarantineReason::parse("P116_SYNTHETIC_ONLY")?,
                        9,
                    )?;
                }
                4 => stored.blobs.tamper.store(true, Ordering::SeqCst),
                _ => stored.advance()?,
            }
            let called = std::cell::Cell::new(false);
            assert!(
                prepared
                    .with_verified_bytes(&provider, &repo, 10, |_| called.set(true))
                    .is_err()
            );
            assert!(!called.get());
            assert!(prepare(&stored, &repo, &bytes).is_err());
            if failure != 5 {
                no_publication(&stored, 3)?;
            }
        }
    }
    Ok(())
}
#[test]
fn allowed_policy_never_overrides_original_native_protection_or_invalid_second_section()
-> TestResult {
    for bytes in [
        fixture::protect(&current(&bytes()?)?, "Contents/section1.xml", 1)?,
        fixture::protect(&bytes()?, "Contents/section1.xml", 1)?,
        fixture::two_sections(&fixture::batch("5")?, &fixture::batch("NON-NUMERIC")?)?,
    ] {
        let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
        let provider = stored.provider()?;
        let source = provider.import_actual_forms(stored.head, 4)?;
        let repo = valid(&stored, &source)?;
        source
            .bind_stored_formula_policy(&provider, &repo, 8)?
            .require_recalculation_data_permission()?;
        assert!(prepare(&stored, &repo, &bytes).is_err());
        no_publication(&stored, 3)?;
    }
    Ok(())
}
#[test]
fn strict_request_refuses_caller_policy_and_other_operations_before_source_or_policy_reads()
-> TestResult {
    let bytes = bytes()?;
    let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let provider = stored.provider()?;
    let source = provider.import_actual_forms(stored.head, 4)?;
    let repo = valid(&stored, &source)?;
    let raw = request(&stored, &bytes)?;
    let base: Value = serde_json::from_slice(&raw)?;
    let mut bad = Vec::new();
    for field in [
        "policy",
        "issuer",
        "approval",
        "expected_results",
        "artifact_id",
    ] {
        let mut v = base.clone();
        v[field] = json!({});
        bad.push(serde_json::to_vec(&v)?);
    }
    for operation in [
        json!({"kind":"recalculate_table_formulas","policy":{}}),
        json!(["recalculate_table_formulas"]),
        json!({"kind":"form"}),
    ] {
        let mut v = base.clone();
        v["operation"] = operation;
        bad.push(serde_json::to_vec(&v)?);
    }
    let before = stored.metadata.audit_events()?.len();
    for raw in bad {
        assert!(
            StoredProductRequest::prepare_formula_with_policy(&provider, &repo, &raw, 8).is_err()
        );
    }
    assert_eq!(repo.calls.load(Ordering::SeqCst), 0);
    assert_eq!(stored.metadata.audit_events()?.len(), before);
    no_publication(&stored, 3)
}
