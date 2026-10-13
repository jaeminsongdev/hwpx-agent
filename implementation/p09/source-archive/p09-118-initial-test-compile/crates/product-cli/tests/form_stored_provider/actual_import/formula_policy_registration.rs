//! In-memory server/keys; original source, artifact AEAD, policy and product code. Not actual SQL/issuer.
use super::super::{Provider, fixture_artifacts};
use super::formula_compiler::fixture;
use super::*;
use artifact_service::{ArtifactId, ArtifactPermission};
use domain_ir::LogicalId;
use hwpx_agent_cli::{
    form_product_request::stored_operations::{
        StoredProductRequest,
        formula::{FormulaPreparationReceipt, PRODUCT_OPERATION_REQUEST_SCHEMA},
    },
    form_stored_provider::actual_import::{
        StoredImportedDocumentForms,
        source_policy::{
            PolicyReadScope, SourcePolicyVersion,
            formulas::{
                FormulaPolicyRepository, StoredFormulaPolicyError,
                registration::{
                    FormulaPolicyDecision, FormulaPolicyRegistrationError as Error,
                    FormulaPolicyRegistrationRecord, FormulaPolicyRegistrationRepository,
                },
            },
        },
    },
};
use hwpx_package::document_import::fields::semantics::ImportedFieldMeaning;
use revision_service::RevisionRequestContext;
use std::sync::{Mutex, atomic::AtomicUsize};

type AnyResult<T> = Result<T, Box<dyn std::error::Error>>;
#[derive(Default)]
struct Repository {
    row: Mutex<Option<SourcePolicyVersion>>,
    calls: AtomicUsize,
    error: Option<Error>,
    corrupt: Option<usize>,
    revoked: std::sync::atomic::AtomicBool,
}
impl FormulaPolicyRegistrationRepository for Repository {
    fn register_formula_policy(
        &self,
        scope: &PolicyReadScope,
        record: &FormulaPolicyRegistrationRecord,
    ) -> Result<SourcePolicyVersion, Error> {
        self.calls.fetch_add(1, Ordering::SeqCst);
        if let Some(ref e) = self.error {
            return Err(if *e == Error::OutcomeUnknown {
                Error::OutcomeUnknown
            } else {
                Error::Repository
            });
        }
        let mut row = self.row.lock().map_err(|_| Error::Repository)?;
        let b = &record.version().binding;
        if row.as_ref().map_or(0, |r| r.binding.policy_generation) != record.expected_generation()
            || scope.tenant() != b.tenant
            || scope.subject() != b.creator_subject
            || scope.project() != b.project
            || scope.branch() != b.branch
            || scope.document() != &b.document
            || scope.head().revision_id() != Some(b.source_revision)
            || scope.head().generation() != b.source_head_generation
            || b.policy_generation != record.expected_generation() + 1
        {
            return Err(Error::Repository);
        }
        *row = Some(record.version().clone());
        let mut reply = record.version().clone();
        if let Some(case) = self.corrupt {
            let b = &mut reply.binding;
            match case {
                0 => {
                    b.tenant = TenantId::new(uuid::Uuid::from_u128(11899))
                        .map_err(|_| Error::Repository)?
                }
                1 => b.project = revision_service::ProjectId::generate(),
                2 => b.branch = revision_service::BranchId::generate(),
                3 => {
                    b.document =
                        DocumentId::parse("different-document").map_err(|_| Error::Repository)?
                }
                4 => b.source_revision = revision_service::RevisionId::generate(),
                5 => b.source_head_generation += 1,
                6 => b.source_result_artifact = ArtifactId::generate(),
                7 => b.source_package_sha256 = ContentDigest::of(b"different source"),
                8 => b.source_provenance_sha256 = ContentDigest::of(b"different provenance"),
                9 => b.observed_graph_sha256 = ContentDigest::of(b"different graph"),
                10 => b.policy_version = uuid::Uuid::new_v4(),
                11 => b.policy_generation += 1,
                12 => {
                    b.creator_subject = artifact_service::SubjectDigest::from_authenticated_subject(
                        "different fixture actor",
                    )
                    .map_err(|_| Error::Repository)?
                }
                13 => reply.artifact = ArtifactId::generate(),
                _ => reply.digest = ContentDigest::of(b"different policy"),
            }
        }
        assert_eq!(
            format!("{record:?}"),
            "FormulaPolicyRegistrationRecord(<redacted>)"
        );
        Ok(reply)
    }
}
impl FormulaPolicyRepository for Repository {
    fn read_current_formula_policy(
        &self,
        scope: &PolicyReadScope,
    ) -> Result<SourcePolicyVersion, StoredFormulaPolicyError> {
        if self.revoked.load(Ordering::SeqCst) {
            return Err(StoredFormulaPolicyError::Repository);
        }
        let r = self
            .row
            .lock()
            .map_err(|_| StoredFormulaPolicyError::Repository)?
            .clone()
            .ok_or(StoredFormulaPolicyError::Repository)?;
        let b = &r.binding;
        if b.tenant != scope.tenant()
            || b.creator_subject != scope.subject()
            || b.project != scope.project()
            || b.branch != scope.branch()
            || &b.document != scope.document()
            || Some(b.source_revision) != scope.head().revision_id()
            || b.source_head_generation != scope.head().generation()
        {
            return Err(StoredFormulaPolicyError::Repository);
        }
        Ok(r)
    }
}
fn bytes() -> AnyResult<Vec<u8>> {
    fixture::two_sections(&fixture::batch("5")?, &fixture::batch("101")?)
}
fn writer<'a>(s: &'a StoredFixture, c: &'a RevisionRequestContext) -> AnyResult<Provider<'a>> {
    Ok(StoredFormProvider::bind(
        &s.artifacts,
        &s.revisions,
        &s.owner,
        c,
        s.project,
        s.branch,
        DocumentId::parse("actual-form-document")?,
    )?)
}
fn decisions(
    source: &StoredImportedDocumentForms,
    p: &Provider<'_>,
    allow: bool,
) -> AnyResult<Vec<FormulaPolicyDecision>> {
    let fields = source.import_field_ranges(p, 4)?;
    let meanings = fields.import_semantics(p, 4)?;
    Ok(meanings
        .observations()
        .iter()
        .filter(|m| matches!(m.meaning, ImportedFieldMeaning::TableFormula { .. }))
        .map(|m| FormulaPolicyDecision::new(m.reference_id.clone(), allow))
        .collect())
}
fn ingests(s: &StoredFixture) -> AnyResult<usize> {
    Ok(s.metadata
        .audit_events()?
        .iter()
        .filter(|e| e.event == "artifact.ingested")
        .count())
}
fn request(s: &StoredFixture, bytes: &[u8]) -> AnyResult<Vec<u8>> {
    Ok(serde_json::to_vec(
        &serde_json::json!({"schema_version": PRODUCT_OPERATION_REQUEST_SCHEMA,
        "idempotency_key": "P118-private-synthetic-key", "project_id": s.project.public_id(), "document_id":"actual-form-document",
        "base_revision":s.head.revision_id().ok_or("head")?.public_id(), "expected_head_generation":s.head.generation(),
        "expected_source_package_sha256":ContentDigest::of(bytes), "plan_id":"registered-formula-plan",
        "operation":{"kind":"recalculate_table_formulas"}}),
    )?)
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

#[test]
fn generated_four_target_registration_is_consumed_by_original_changed_and_current_product_paths()
-> TestResult {
    let original = bytes()?;
    for bytes in [original.clone(), current(&original)?] {
        fixture::index_source(&bytes)?;
        let s = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
        let c = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
        let p = writer(&s, &c)?;
        let source = p.import_actual_forms(s.head, 4)?;
        let explicit = decisions(&source, &p, true)?;
        assert_eq!(explicit.len(), 4);
        let repo = Repository::default();
        let prepared = source.prepare_formula_policy_registration(&p, &explicit, 0, 5)?;
        assert_eq!(
            format!("{prepared:?}"),
            "PreparedFormulaPolicyRegistration(<redacted>)"
        );
        assert_eq!(ingests(&s)?, 2);
        let receipt = prepared.register(&p, &repo, 6)?;
        assert_eq!(receipt.generation, 1);
        assert_eq!(receipt.formula_targets, 4);
        let policy = source.bind_stored_formula_policy(&p, &repo, 7)?;
        assert_eq!(
            policy.receipt().target_bindings_sha256,
            receipt.target_bindings_sha256
        );
        assert_eq!(
            policy.receipt().field_meaning_graph_sha256,
            receipt.field_meaning_graph_sha256
        );
        assert_eq!(policy.receipt().policy_raw_sha256, receipt.digest);
        assert_eq!(policy.receipt().allowed_targets, 4);
        let product =
            StoredProductRequest::prepare_formula_with_policy(&p, &repo, &request(&s, &bytes)?, 8)?;
        assert_eq!(
            product.with_verified_bytes(&p, &repo, 9, <[u8]>::to_vec)?,
            current(&original)?
        );
        assert_eq!(
            matches!(
                product.receipt().product.formula,
                FormulaPreparationReceipt::Changed { .. }
            ),
            bytes == original
        );
        assert!(
            product
                .require_current_product_route(&p, &repo, 10)
                .is_err()
        );
        assert_eq!(s.revisions.head(&c, s.project, s.branch)?, s.head);
        assert_eq!(ingests(&s)?, 3);
        let raw = serde_json::to_string(&receipt)?;
        for forbidden in [
            "actual-form-document",
            "creator_subject",
            "allow_recalculation",
            "begin_anchor",
            "P118-private-synthetic-key",
        ] {
            assert!(!raw.contains(forbidden));
        }
        assert!(
            receipt
                .qualification
                .contains("NOT_trusted_issuer_actual_SQL")
        );
        assert_eq!(
            format!("{receipt:?}"),
            "RegisteredFormulaPolicyReceipt(<redacted>)"
        );
        assert_eq!(
            format!("{:?}", explicit[0]),
            "FormulaPolicyDecision(<redacted>)"
        );
    }
    Ok(())
}
#[test]
fn all_36_locked_originals_generate_complete_consumable_metadata_without_source_publication()
-> TestResult {
    let mut cases = 0;
    for bytes in super::formula_evaluation::fixture::inputs::actual_corpus()? {
        let s = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
        let c = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
        let p = writer(&s, &c)?;
        let source = p.import_actual_forms(s.head, 4)?;
        let rules = decisions(&source, &p, true)?;
        let repo = Repository::default();
        let receipt = source
            .prepare_formula_policy_registration(&p, &rules, 0, 5)?
            .register(&p, &repo, 6)?;
        let read = source.bind_stored_formula_policy(&p, &repo, 7)?;
        assert_eq!(read.receipt().formula_targets, rules.len());
        assert_eq!(
            read.receipt().target_bindings_sha256,
            receipt.target_bindings_sha256
        );
        read.require_recalculation_data_permission()?;
        assert_eq!(s.revisions.head(&c, s.project, s.branch)?, s.head);
        assert_eq!(ingests(&s)?, 3);
        cases += 1;
    }
    assert_eq!(cases, 36);
    Ok(())
}
#[test]
fn missing_duplicate_extra_non_formula_empty_and_oversized_decisions_fail_before_ingest()
-> TestResult {
    let s = StoredFixture::new(&bytes()?, ArtifactKind::Result, false)?;
    let c = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
    let p = writer(&s, &c)?;
    let source = p.import_actual_forms(s.head, 4)?;
    let rules = decisions(&source, &p, true)?;
    for case in 0..6 {
        let mut bad = rules.clone();
        match case {
            0 => {
                bad.pop();
            }
            1 => bad[1] = bad[0].clone(),
            2 => bad.push(FormulaPolicyDecision::new(
                LogicalId::parse("foreign-target")?,
                true,
            )),
            3 => bad[0] = FormulaPolicyDecision::new(LogicalId::parse("foreign-target")?, true),
            4 => bad.clear(),
            _ => bad = vec![bad[0].clone(); 4097],
        }
        assert!(
            matches!(
                source.prepare_formula_policy_registration(&p, &bad, 0, 5),
                Err(Error::Policy)
            ),
            "case={case}"
        );
    }
    assert_eq!(ingests(&s)?, 2);
    Ok(())
}
#[test]
fn read_only_exhausted_generation_and_no_formula_source_cannot_create_policy() -> TestResult {
    let s = StoredFixture::new(&bytes()?, ArtifactKind::Result, false)?;
    let reader = s.provider()?;
    let source = reader.import_actual_forms(s.head, 4)?;
    assert!(matches!(
        source.prepare_formula_policy_registration(
            &reader,
            &decisions(&source, &reader, true)?,
            0,
            5
        ),
        Err(Error::Scope)
    ));
    let c = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
    let p = writer(&s, &c)?;
    let source = p.import_actual_forms(s.head, 4)?;
    for generation in [i64::MAX as u64, u64::MAX] {
        assert!(matches!(
            source.prepare_formula_policy_registration(&p, &[], generation, 5),
            Err(Error::Binding)
        ));
    }
    let prepared =
        source.prepare_formula_policy_registration(&p, &decisions(&source, &p, true)?, 0, 5)?;
    let repo = Repository::default();
    assert!(matches!(
        prepared.register(&reader, &repo, 6),
        Err(Error::Scope)
    ));
    assert_eq!(repo.calls.load(Ordering::SeqCst), 0);
    assert_eq!(ingests(&s)?, 2);
    let blank = hwpx_package::Hancom2020Vs0Builder::build("NO FORMULA")?
        .with_verified_bytes(<[u8]>::to_vec)?;
    let s = StoredFixture::new(&blank, ArtifactKind::Result, false)?;
    let c = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
    let p = writer(&s, &c)?;
    let source = p.import_actual_forms(s.head, 4)?;
    assert!(matches!(
        source.prepare_formula_policy_registration(
            &p,
            &[FormulaPolicyDecision::new(
                LogicalId::parse("invented")?,
                true
            )],
            0,
            5
        ),
        Err(Error::Policy)
    ));
    assert_eq!(ingests(&s)?, 2);
    Ok(())
}
#[test]
fn source_head_quarantine_and_aead_drift_deny_before_any_registration_write() -> TestResult {
    for failure in 0..3 {
        let s = StoredFixture::new(&bytes()?, ArtifactKind::Result, false)?;
        let c = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
        let p = writer(&s, &c)?;
        let source = p.import_actual_forms(s.head, 4)?;
        let prepared =
            source.prepare_formula_policy_registration(&p, &decisions(&source, &p, true)?, 0, 5)?;
        match failure {
            0 => s.advance()?,
            1 => s.artifacts.quarantine(
                &s.owner,
                s.result,
                artifact_service::QuarantineReason::parse("P118_SYNTHETIC_ONLY")?,
                6,
            )?,
            _ => s.blobs.tamper.store(true, Ordering::SeqCst),
        }
        let repo = Repository::default();
        assert!(matches!(
            prepared.register(&p, &repo, 7),
            Err(Error::Source)
        ));
        assert_eq!(repo.calls.load(Ordering::SeqCst), 0);
        assert_eq!(ingests(&s)?, 2);
    }
    Ok(())
}
#[test]
fn unverified_policy_artifact_is_retained_but_never_sent_to_registrar() -> TestResult {
    let s = StoredFixture::new(&bytes()?, ArtifactKind::Result, false)?;
    let c = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
    let a = fixture_artifacts(s.metadata.clone(), s.blobs.clone(), true)?;
    let p = StoredFormProvider::bind(
        &a,
        &s.revisions,
        &s.owner,
        &c,
        s.project,
        s.branch,
        DocumentId::parse("actual-form-document")?,
    )?;
    let source = p.import_actual_forms(s.head, 4)?;
    let prepared =
        source.prepare_formula_policy_registration(&p, &decisions(&source, &p, true)?, 0, 5)?;
    let repo = Repository::default();
    assert!(matches!(
        prepared.register(&p, &repo, 6),
        Err(Error::Artifact)
    ));
    assert_eq!(repo.calls.load(Ordering::SeqCst), 0);
    assert_eq!(ingests(&s)?, 3);
    Ok(())
}
#[test]
fn repository_denial_unknown_ack_and_all_15_reply_mismatches_never_retry_or_erase_evidence()
-> TestResult {
    for case in 0..17 {
        let s = StoredFixture::new(&bytes()?, ArtifactKind::Result, false)?;
        let c = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
        let p = writer(&s, &c)?;
        let source = p.import_actual_forms(s.head, 4)?;
        let repo = Repository {
            error: match case {
                0 => Some(Error::Repository),
                1 => Some(Error::OutcomeUnknown),
                _ => None,
            },
            corrupt: if case >= 2 { Some(case - 2) } else { None },
            ..Repository::default()
        };
        let result = source
            .prepare_formula_policy_registration(&p, &decisions(&source, &p, true)?, 0, 5)?
            .register(&p, &repo, 6);
        assert_eq!(
            result.err(),
            Some(if case == 0 {
                Error::Repository
            } else {
                Error::OutcomeUnknown
            })
        );
        assert_eq!(repo.calls.load(Ordering::SeqCst), 1);
        assert_eq!(ingests(&s)?, 3);
        assert_eq!(s.revisions.head(&c, s.project, s.branch)?, s.head);
    }
    Ok(())
}
#[test]
fn sorted_generation_cas_and_latest_revocation_flow_keep_old_products_unusable() -> TestResult {
    let bytes = bytes()?;
    let s = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
    let c = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
    let p = writer(&s, &c)?;
    let source = p.import_actual_forms(s.head, 4)?;
    let mut rules = decisions(&source, &p, true)?;
    let repo = Repository::default();
    let prepared = source.prepare_formula_policy_registration(&p, &rules, 0, 5)?;
    let first = prepared.register(&p, &repo, 6)?;
    let old =
        StoredProductRequest::prepare_formula_with_policy(&p, &repo, &request(&s, &bytes)?, 7)?;
    assert_eq!(
        prepared.register(&p, &repo, 8).err(),
        Some(Error::Repository)
    );
    assert_eq!(ingests(&s)?, 3); // same bytes dedup; no destructive orphan cleanup.
    rules.reverse();
    let next = source
        .prepare_formula_policy_registration(&p, &rules, 1, 9)?
        .register(&p, &repo, 10)?;
    assert_eq!(next.generation, 2);
    assert_ne!(next.version, first.version);
    assert_eq!(next.target_bindings_sha256, first.target_bindings_sha256);
    let called = std::cell::Cell::new(false);
    assert!(
        old.with_verified_bytes(&p, &repo, 11, |_| called.set(true))
            .is_err()
    );
    assert!(!called.get());
    let new =
        StoredProductRequest::prepare_formula_with_policy(&p, &repo, &request(&s, &bytes)?, 11)?;
    repo.revoked.store(true, Ordering::SeqCst);
    assert!(
        new.with_verified_bytes(&p, &repo, 12, |_| called.set(true))
            .is_err()
    );
    assert!(!called.get());
    assert_eq!(ingests(&s)?, 4);
    assert_eq!(s.revisions.head(&c, s.project, s.branch)?, s.head);
    Ok(())
}
#[test]
fn explicit_denials_are_storable_data_but_never_allow_current_or_changed_recalculation()
-> TestResult {
    let original = bytes()?;
    for bytes in [original.clone(), current(&original)?] {
        let s = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
        let c = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
        let p = writer(&s, &c)?;
        let source = p.import_actual_forms(s.head, 4)?;
        let repo = Repository::default();
        source
            .prepare_formula_policy_registration(&p, &decisions(&source, &p, false)?, 0, 5)?
            .register(&p, &repo, 6)?;
        let read = source.bind_stored_formula_policy(&p, &repo, 7)?;
        assert_eq!(read.receipt().formula_targets, 4);
        assert_eq!(read.receipt().allowed_targets, 0);
        assert_eq!(
            read.require_recalculation_data_permission().err(),
            Some(StoredFormulaPolicyError::Denied)
        );
        assert!(
            StoredProductRequest::prepare_formula_with_policy(&p, &repo, &request(&s, &bytes)?, 8)
                .is_err()
        );
        assert_eq!(ingests(&s)?, 3);
    }
    Ok(())
}
#[test]
fn generated_allowance_never_bypasses_native_protection_or_invalid_second_section() -> TestResult {
    for bytes in [
        fixture::protect(&bytes()?, "Contents/section1.xml", 1)?,
        fixture::protect(&current(&bytes()?)?, "Contents/section1.xml", 1)?,
        fixture::two_sections(&fixture::batch("5")?, &fixture::batch("NON-NUMERIC")?)?,
    ] {
        let s = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
        let c = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
        let p = writer(&s, &c)?;
        let source = p.import_actual_forms(s.head, 4)?;
        let repo = Repository::default();
        source
            .prepare_formula_policy_registration(&p, &decisions(&source, &p, true)?, 0, 5)?
            .register(&p, &repo, 6)?;
        source
            .bind_stored_formula_policy(&p, &repo, 7)?
            .require_recalculation_data_permission()?;
        assert!(
            StoredProductRequest::prepare_formula_with_policy(&p, &repo, &request(&s, &bytes)?, 8)
                .is_err()
        );
        assert_eq!(ingests(&s)?, 3);
    }
    Ok(())
}
