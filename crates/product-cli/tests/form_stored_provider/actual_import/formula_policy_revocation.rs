//! Actual source/artifact/product code with an explicit in-memory server; SQL/native `NOT_RUN`.
use super::super::Provider;
use super::formula_compiler::fixture;
use super::*;
use artifact_service::{ArtifactId, ArtifactPermission};
use hwpx_agent_cli::{
    form_product_request::stored_operations::{
        StoredProductRequest, formula::PRODUCT_OPERATION_REQUEST_SCHEMA,
    },
    form_stored_provider::actual_import::{
        StoredImportedDocumentForms,
        source_policy::{
            PolicyReadScope, SourcePolicyVersion,
            formulas::{
                FormulaPolicyRepository, StoredFormulaPolicy, StoredFormulaPolicyError,
                registration::{
                    FormulaPolicyDecision, FormulaPolicyRegistrationError,
                    FormulaPolicyRegistrationRecord, FormulaPolicyRegistrationRepository,
                },
                revocation::{
                    FormulaPolicyRevocationError as Error, FormulaPolicyRevocationRecord,
                    FormulaPolicyRevocationRepository,
                },
            },
        },
    },
};
use hwpx_package::document_import::fields::semantics::ImportedFieldMeaning;
use revision_service::RevisionRequestContext;
use std::sync::{
    Mutex,
    atomic::{AtomicBool, AtomicUsize},
};

#[derive(Default)]
struct Repository {
    row: Mutex<Option<SourcePolicyVersion>>,
    revoked: AtomicBool,
    writes: AtomicUsize,
    failure: Option<Error>,
    corrupt: Option<usize>,
}
impl FormulaPolicyRegistrationRepository for Repository {
    fn register_formula_policy(
        &self,
        scope: &PolicyReadScope,
        record: &FormulaPolicyRegistrationRecord,
    ) -> Result<SourcePolicyVersion, FormulaPolicyRegistrationError> {
        let v = record.version();
        assert_eq!(v.binding.creator_subject, scope.subject());
        assert_eq!(record.expected_generation(), 0);
        let mut row = self
            .row
            .lock()
            .map_err(|_| FormulaPolicyRegistrationError::Repository)?;
        if row.is_some() {
            return Err(FormulaPolicyRegistrationError::Repository);
        }
        *row = Some(v.clone());
        Ok(v.clone())
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
        let v = self
            .row
            .lock()
            .map_err(|_| StoredFormulaPolicyError::Repository)?
            .clone()
            .ok_or(StoredFormulaPolicyError::Repository)?;
        let b = &v.binding;
        if b.tenant != scope.tenant()
            || b.project != scope.project()
            || b.branch != scope.branch()
            || &b.document != scope.document()
            || Some(b.source_revision) != scope.head().revision_id()
            || b.source_head_generation != scope.head().generation()
        {
            return Err(StoredFormulaPolicyError::Repository);
        }
        Ok(v)
    }
}
impl FormulaPolicyRevocationRepository for Repository {
    fn revoke_formula_policy(
        &self,
        scope: &PolicyReadScope,
        record: &FormulaPolicyRevocationRecord,
    ) -> Result<SourcePolicyVersion, Error> {
        self.writes.fetch_add(1, Ordering::SeqCst);
        if let Some(ref e) = self.failure {
            return Err(if *e == Error::OutcomeUnknown {
                Error::OutcomeUnknown
            } else {
                Error::Repository
            });
        }
        let mut v = self
            .read_current_formula_policy(scope)
            .map_err(|_| Error::Repository)?;
        if record.version() != &v {
            return Err(Error::Binding);
        }
        assert_eq!(
            format!("{record:?}"),
            "FormulaPolicyRevocationRecord(<redacted>)"
        );
        self.revoked.store(true, Ordering::SeqCst);
        if let Some(case) = self.corrupt {
            let b = &mut v.binding;
            match case {
                0 => {
                    b.tenant = TenantId::new(uuid::Uuid::from_u128(13499))
                        .map_err(|_| Error::Repository)?;
                }
                1 => b.project = revision_service::ProjectId::generate(),
                2 => b.branch = revision_service::BranchId::generate(),
                3 => {
                    b.document =
                        DocumentId::parse("different-document").map_err(|_| Error::Repository)?;
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
                        "different actor",
                    )
                    .map_err(|_| Error::Repository)?;
                }
                13 => v.artifact = ArtifactId::generate(),
                _ => v.digest = ContentDigest::of(b"different policy"),
            }
        }
        Ok(v)
    }
}
fn bytes() -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    fixture::two_sections(&fixture::batch("5")?, &fixture::batch("101")?)
}
fn writer<'a>(
    s: &'a StoredFixture,
    c: &'a RevisionRequestContext,
) -> Result<Provider<'a>, Box<dyn std::error::Error>> {
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
fn register(
    source: &StoredImportedDocumentForms,
    p: &Provider<'_>,
    repo: &Repository,
) -> Result<StoredFormulaPolicy, Box<dyn std::error::Error>> {
    let fields = source.import_field_ranges(p, 4)?;
    let meanings = fields.import_semantics(p, 4)?;
    let decisions = meanings
        .observations()
        .iter()
        .filter(|m| matches!(m.meaning, ImportedFieldMeaning::TableFormula { .. }))
        .map(|m| FormulaPolicyDecision::new(m.reference_id.clone(), true))
        .collect::<Vec<_>>();
    source
        .prepare_formula_policy_registration(p, &decisions, 0, 5)?
        .register(p, repo, 6)?;
    Ok(source.bind_stored_formula_policy(p, repo, 7)?)
}
fn ingests(s: &StoredFixture) -> Result<usize, Box<dyn std::error::Error>> {
    Ok(s.metadata
        .audit_events()?
        .iter()
        .filter(|e| e.event == "artifact.ingested")
        .count())
}
#[test]
fn revocation_denies_existing_prepared_formula_callback_and_preserves_original_artifacts()
-> TestResult {
    let original = bytes()?;
    let s = StoredFixture::new(&original, ArtifactKind::Result, false)?;
    let c = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
    let p = writer(&s, &c)?;
    let source = p.import_actual_forms(s.head, 4)?;
    let repo = Repository::default();
    let policy = register(&source, &p, &repo)?;
    let raw = serde_json::to_vec(
        &serde_json::json!({"schema_version":PRODUCT_OPERATION_REQUEST_SCHEMA,
        "idempotency_key":"P134-private-test-key","project_id":s.project.public_id(),"document_id":"actual-form-document",
        "base_revision":s.head.revision_id().ok_or("head")?.public_id(),"expected_head_generation":s.head.generation(),
        "expected_source_package_sha256":ContentDigest::of(&original),"plan_id":"revoke-formula-plan",
        "operation":{"kind":"recalculate_table_formulas"}}),
    )?;
    let product = StoredProductRequest::prepare_formula_with_policy(&p, &repo, &raw, 8)?;
    assert!(product.with_verified_bytes(&p, &repo, 9, <[u8]>::len)? > 0);
    assert!(product.require_current_product_route(&p, &repo, 9).is_err());
    let receipt = policy.revoke(&source, &p, &repo, 10)?;
    assert_eq!(receipt.generation, 1);
    assert_eq!(receipt.policy_sha256, policy.receipt().policy_raw_sha256);
    assert_eq!(repo.writes.load(Ordering::SeqCst), 1);
    let callback = AtomicBool::new(false);
    assert!(
        product
            .with_verified_bytes(&p, &repo, 11, |_| callback.store(true, Ordering::SeqCst))
            .is_err()
    );
    assert!(!callback.load(Ordering::SeqCst));
    assert!(source.bind_stored_formula_policy(&p, &repo, 11).is_err());
    assert_eq!(policy.revoke(&source, &p, &repo, 11), Err(Error::Policy));
    assert_eq!(repo.writes.load(Ordering::SeqCst), 1);
    assert_eq!(source.verify(&p, 12)?, *source.receipt());
    assert!(s.artifacts.download(&s.owner, s.result, 12)? == original);
    assert_eq!(s.revisions.head(&c, s.project, s.branch)?, s.head);
    assert_eq!(ingests(&s)?, 3);
    assert_eq!(
        format!("{receipt:?}"),
        "RevokedFormulaPolicyReceipt(<redacted>)"
    );
    let safe = serde_json::to_string(&receipt)?;
    for forbidden in [
        "actual-form-document",
        "creator_subject",
        "P134-private-test-key",
        "begin_anchor",
    ] {
        assert!(!safe.contains(forbidden));
    }
    assert!(receipt.qualification.contains("NOT_actual_SQL"));
    Ok(())
}
#[test]
fn read_only_revoke_denies_before_any_repository_write() -> TestResult {
    let s = StoredFixture::new(&bytes()?, ArtifactKind::Result, false)?;
    let c = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
    let p = writer(&s, &c)?;
    let source = p.import_actual_forms(s.head, 4)?;
    let repo = Repository::default();
    let policy = register(&source, &p, &repo)?;
    assert_eq!(
        policy.revoke(&source, &s.provider()?, &repo, 8),
        Err(Error::Scope)
    );
    assert_eq!(repo.writes.load(Ordering::SeqCst), 0);
    assert_eq!(ingests(&s)?, 3);
    Ok(())
}
#[test]
fn stale_head_quarantine_and_aead_tamper_deny_before_revocation_write() -> TestResult {
    for failure in 0..3 {
        let s = StoredFixture::new(&bytes()?, ArtifactKind::Result, false)?;
        let c = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
        let p = writer(&s, &c)?;
        let source = p.import_actual_forms(s.head, 4)?;
        let repo = Repository::default();
        let policy = register(&source, &p, &repo)?;
        match failure {
            0 => s.advance()?,
            1 => {
                s.artifacts.quarantine(
                    &s.owner,
                    s.result,
                    artifact_service::QuarantineReason::parse("P134_SYNTHETIC_ONLY")?,
                    8,
                )?;
            }
            _ => s.blobs.tamper.store(true, Ordering::SeqCst),
        }
        assert_eq!(policy.revoke(&source, &p, &repo, 9), Err(Error::Policy));
        assert_eq!(repo.writes.load(Ordering::SeqCst), 0);
        assert_eq!(ingests(&s)?, 3);
    }
    Ok(())
}
#[test]
fn changed_current_policy_denies_before_revocation_write() -> TestResult {
    let s = StoredFixture::new(&bytes()?, ArtifactKind::Result, false)?;
    let c = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
    let p = writer(&s, &c)?;
    let source = p.import_actual_forms(s.head, 4)?;
    let repo = Repository::default();
    let policy = register(&source, &p, &repo)?;
    repo.row
        .lock()
        .map_err(|_| "test lock")?
        .as_mut()
        .ok_or("test row")?
        .digest = ContentDigest::of(b"changed policy");
    assert_eq!(policy.revoke(&source, &p, &repo, 8), Err(Error::Policy));
    assert_eq!(repo.writes.load(Ordering::SeqCst), 0);
    Ok(())
}
#[test]
fn denied_unknown_and_all_15_inexact_commit_replies_are_never_retried() -> TestResult {
    for case in 0..17 {
        let s = StoredFixture::new(&bytes()?, ArtifactKind::Result, false)?;
        let c = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
        let p = writer(&s, &c)?;
        let source = p.import_actual_forms(s.head, 4)?;
        let repo = Repository {
            failure: match case {
                0 => Some(Error::Repository),
                1 => Some(Error::OutcomeUnknown),
                _ => None,
            },
            corrupt: if case >= 2 { Some(case - 2) } else { None },
            ..Repository::default()
        };
        let policy = register(&source, &p, &repo)?;
        let expected = if case == 0 {
            Error::Repository
        } else {
            Error::OutcomeUnknown
        };
        assert_eq!(policy.revoke(&source, &p, &repo, 8), Err(expected));
        assert_eq!(repo.writes.load(Ordering::SeqCst), 1);
        assert_eq!(ingests(&s)?, 3);
        assert_eq!(s.revisions.head(&c, s.project, s.branch)?, s.head);
    }
    Ok(())
}
#[test]
fn current_writer_can_revoke_another_creators_policy_without_author_defaults() -> TestResult {
    let s = StoredFixture::new(&bytes()?, ArtifactKind::Result, false)?;
    let c = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
    let p = writer(&s, &c)?;
    let source = p.import_actual_forms(s.head, 4)?;
    let repo = Repository::default();
    let policy = register(&source, &p, &repo)?;
    let artifact = repo
        .row
        .lock()
        .map_err(|_| "test lock")?
        .as_ref()
        .ok_or("test row")?
        .artifact;
    s.artifacts.set_permissions(
        &s.owner,
        artifact,
        s.reader.subject(),
        BTreeSet::from([ArtifactPermission::Read]),
        8,
    )?;
    let editor = RequestContext::new(
        s.reader.tenant_id(),
        s.reader.subject(),
        [AuthScope::DocumentRead, AuthScope::DocumentWrite],
    );
    let editor_provider = StoredFormProvider::bind(
        &s.artifacts,
        &s.revisions,
        &editor,
        &s.revision_context,
        s.project,
        s.branch,
        DocumentId::parse("actual-form-document")?,
    )?;
    let editor_source = editor_provider.import_actual_forms(s.head, 9)?;
    let receipt = policy.revoke(&editor_source, &editor_provider, &repo, 10)?;
    assert_eq!(repo.writes.load(Ordering::SeqCst), 1);
    assert_eq!(receipt.generation, 1);
    assert_ne!(s.owner.subject(), editor.subject());
    assert_eq!(
        repo.row
            .lock()
            .map_err(|_| "test lock")?
            .as_ref()
            .ok_or("test row")?
            .binding
            .creator_subject,
        s.owner.subject()
    );
    Ok(())
}
