//! Actual artifact AEAD/source/compiler; server actor/scanner/repository remain synthetic.
use super::super::{Fixture, Provider, StoredFixture, TestResult, matrix_request};
use super::{explicit_test_policies, fixture_bytes, fixture_manifest};
use artifact_service::{ArtifactKind, ArtifactMetadataRepository, ArtifactPermission};
use domain_ir::{
    DocumentId, FormControlLimitConfig, FormControlLimits, form_input::FormInputAccessPolicy,
};
use hwpx_agent_cli::{
    form_product_request::{
        FORM_PRODUCT_REQUEST_SCHEMA,
        stored::{StoredProductFormBindings, StoredProductFormRequest},
    },
    form_stored_provider::{
        StoredFormProvider,
        actual_import::{
            StoredImportedDocumentForms,
            source_policy::{
                PolicyReadScope, SourcePolicyRepository, SourcePolicyVersion,
                StoredSourcePolicyError,
                product::StoredPolicyProductError,
                registration::{
                    PolicyRegistrationError, PolicyRegistrationRecord,
                    SourcePolicyRegistrationRepository,
                },
            },
        },
    },
};
use hwpx_package::{
    NativeFormPackageLimits,
    document_import::forms::policies::{FormPolicySourceBinding, PolicyBoundDocumentForms},
    native_form_value_output::NativeFormValueReader,
};
use revision_service::RevisionRequestContext;
use std::{
    collections::BTreeSet,
    sync::{
        Mutex,
        atomic::{AtomicBool, AtomicUsize, Ordering},
    },
};

#[derive(Default)]
struct Repository {
    row: Mutex<Option<SourcePolicyVersion>>,
    deny: AtomicBool,
    reads: AtomicUsize,
    deny_at: AtomicUsize,
}
impl SourcePolicyRegistrationRepository for Repository {
    fn register(
        &self,
        s: &PolicyReadScope,
        r: &PolicyRegistrationRecord,
    ) -> Result<SourcePolicyVersion, PolicyRegistrationError> {
        let mut row = self
            .row
            .lock()
            .map_err(|_| PolicyRegistrationError::Repository)?;
        if row.as_ref().map_or(0, |r| r.binding.policy_generation) != r.expected_generation()
            || s.subject() != r.version().binding.creator_subject
        {
            return Err(PolicyRegistrationError::Repository);
        }
        *row = Some(r.version().clone());
        Ok(r.version().clone())
    }
}
impl SourcePolicyRepository for Repository {
    fn read_current(
        &self,
        s: &PolicyReadScope,
    ) -> Result<SourcePolicyVersion, StoredSourcePolicyError> {
        let n = self.reads.fetch_add(1, Ordering::SeqCst) + 1;
        let limit = self.deny_at.load(Ordering::SeqCst);
        if self.deny.load(Ordering::SeqCst) || (limit > 0 && n >= limit) {
            return Err(StoredSourcePolicyError::Repository);
        }
        let r = self
            .row
            .lock()
            .map_err(|_| StoredSourcePolicyError::Repository)?
            .clone()
            .ok_or(StoredSourcePolicyError::Repository)?;
        if r.binding.tenant != s.tenant()
            || r.binding.project != s.project()
            || r.binding.branch != s.branch()
            || r.binding.document != *s.document()
            || Some(r.binding.source_revision) != s.head().revision_id()
            || r.binding.source_head_generation != s.head().generation()
        {
            return Err(StoredSourcePolicyError::Repository);
        }
        Ok(r)
    }
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
fn publish(s: &StoredFixture, repo: &Repository, expected: u64) -> TestResult {
    let c = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
    let p = writer(s, &c)?;
    let imported = p.import_actual_forms(s.head, 4)?;
    let r = imported
        .prepare_policy_registration(
            &p,
            &explicit_test_policies(imported.imported()),
            expected,
            5,
        )?
        .register(&p, repo, 6)?;
    s.artifacts.set_permissions(
        &s.owner,
        r.artifact,
        s.reader.subject(),
        BTreeSet::from([ArtifactPermission::Read]),
        7,
    )?;
    Ok(())
}
fn setup(label: &str) -> Result<(StoredFixture, Repository), Box<dyn std::error::Error>> {
    let s = StoredFixture::new(
        &fixture_bytes(label, "source")?,
        ArtifactKind::Result,
        false,
    )?;
    let repo = Repository::default();
    publish(&s, &repo, 0)?;
    Ok((s, repo))
}
fn direct(
    imported: &StoredImportedDocumentForms,
) -> Result<PolicyBoundDocumentForms<'_>, Box<dyn std::error::Error>> {
    Ok(PolicyBoundDocumentForms::bind(
        imported.imported(),
        &FormPolicySourceBinding::for_imported(imported.imported()),
        &explicit_test_policies(imported.imported()),
    )?)
}
fn request(
    label: &str,
    s: &StoredFixture,
    bound: &PolicyBoundDocumentForms<'_>,
) -> Result<(serde_json::Value, FormInputAccessPolicy), Box<dyn std::error::Error>> {
    let f = Fixture {
        source: fixture_bytes(label, "source")?,
        map: bound.native_binding().map().clone(),
        policies: bound.native_binding().policies().to_vec(),
    };
    let (input, access) = if label == "actual" {
        let (input, access) = f.request("P86 source-bound 값")?;
        (serde_json::to_vec(&input)?, access)
    } else {
        matrix_request(label, &f)?
    };
    Ok((
        serde_json::json!({"schema_version": FORM_PRODUCT_REQUEST_SCHEMA,
        "idempotency_key": "P86-private-component-key", "project_id": s.project.public_id(),
        "document_id": "actual-form-document", "base_revision": s.head.revision_id().ok_or("head")?.public_id(),
        "expected_head_generation": s.head.generation(),
        "expected_source_package_sha256": hex::encode(bound.receipt().source.source_package_sha256),
        "plan_id": "stored-form-plan", "form_input": serde_json::from_slice::<serde_json::Value>(&input)?}),
        access,
    ))
}
fn ingests(s: &StoredFixture) -> Result<usize, Box<dyn std::error::Error>> {
    Ok(s.metadata
        .audit_events()?
        .iter()
        .filter(|e| e.event == "artifact.ingested")
        .count())
}
#[test]
fn all_five_source_cases_registered_policy_uses_original_whole_product_candidate_no_publication()
-> TestResult {
    let (_, manifest) = fixture_manifest()?;
    let mut cases = 0;
    for row in manifest["cases"].as_array().ok_or("cases")? {
        let label = row["case"].as_str().ok_or("case")?;
        let (s, repo) = setup(label)?;
        let p = s.provider()?;
        let imported = p.import_actual_forms(s.head, 8)?;
        let explicit = direct(&imported)?;
        let native = explicit.native_binding();
        assert_eq!(format!("{native:?}"), "BoundNativeFormPolicies(<redacted>)");
        let limits = FormControlLimits::new(FormControlLimitConfig::default())?;
        let original = NativeFormValueReader::read(
            &fixture_bytes(label, "source")?,
            native.map(),
            native.policies(),
            limits,
            NativeFormPackageLimits::default(),
        )?;
        assert_eq!(
            original
                .native_v1()
                .bind_policies(native.policies(), limits)?,
            *explicit.state()
        );
        assert_eq!(
            original.v1_state_sha256(),
            explicit.state().canonical_sha256(limits)?
        );
        assert_ne!(original.state(), explicit.state());
        let (raw, access) = request(label, &s, &explicit)?;
        let raw = serde_json::to_vec(&raw)?;
        let policy = imported.bind_stored_policies(&p, &repo, 9)?;
        let prepared = policy.prepare_product_json(&p, &repo, &raw, &access, 10)?;
        let original = StoredProductFormRequest::prepare_json(
            &p,
            &raw,
            &StoredProductFormBindings {
                map: native.map(),
                policies: native.policies(),
                access: &access,
            },
            10,
        )?;
        assert_eq!(prepared.candidate_bytes(), original.candidate_bytes());
        assert_eq!(&prepared.receipt().product, original.receipt());
        assert_eq!(&prepared.receipt().policy, policy.receipt());
        assert_eq!(
            prepared.verify(&p, &repo, &access, 11)?,
            *prepared.receipt()
        );
        assert!(matches!(
            prepared.require_current_product_route(&p, &repo, &access, 12),
            Err(StoredPolicyProductError::Product(_))
        ));
        assert_eq!(
            format!("{prepared:?}"),
            "PreparedStoredPolicyProduct(<redacted>)"
        );
        assert_eq!(ingests(&s)?, 3);
        assert_eq!(
            s.revisions.head(&s.revision_context, s.project, s.branch)?,
            s.head
        );
        assert_eq!(
            s.artifacts.download(&s.reader, s.result, 13)?,
            fixture_bytes(label, "source")?
        );
        cases += 1;
    }
    assert_eq!(cases, 5);
    Ok(())
}
#[test]
fn all_ten_observed_sources_retain_exact_original_native_state_and_complete_receipt() -> TestResult
{
    let (_, manifest) = fixture_manifest()?;
    let limits = FormControlLimits::new(FormControlLimitConfig::default())?;
    let mut cases = 0;
    for row in manifest["cases"].as_array().ok_or("cases")? {
        for kind in ["source", "output"] {
            let bytes = fixture_bytes(row["case"].as_str().ok_or("case")?, kind)?;
            let s = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
            let p = s.provider()?;
            let imported = p.import_actual_forms(s.head, 4)?;
            let explicit = direct(&imported)?;
            let native = explicit.native_binding();
            let original = NativeFormValueReader::read(
                &bytes,
                native.map(),
                native.policies(),
                limits,
                NativeFormPackageLimits::default(),
            )?;
            assert_eq!(
                original
                    .native_v1()
                    .bind_policies(native.policies(), limits)?,
                *explicit.state()
            );
            assert_eq!(
                original.v1_state_sha256(),
                explicit.state().canonical_sha256(limits)?
            );
            assert_ne!(original.state(), explicit.state());
            assert_eq!(
                explicit.verify_source(
                    &bytes,
                    &FormPolicySourceBinding::for_imported(imported.imported()),
                    &explicit_test_policies(imported.imported())
                )?,
                *explicit.receipt()
            );
            assert_eq!(ingests(&s)?, 2);
            cases += 1;
        }
    }
    assert_eq!(cases, 10);
    Ok(())
}
#[test]
fn original_strict_envelope_rejects_injected_maps_policies_artifacts_approval_and_stale_scope()
-> TestResult {
    let (s, repo) = setup("five-kinds")?;
    let p = s.provider()?;
    let imported = p.import_actual_forms(s.head, 8)?;
    let explicit = direct(&imported)?;
    let (raw, access) = request("five-kinds", &s, &explicit)?;
    let policy = imported.bind_stored_policies(&p, &repo, 9)?;
    for (key, value) in [
        ("map", serde_json::json!({})),
        ("policies", serde_json::json!([])),
        ("policy_artifact", serde_json::json!(s.result)),
        ("caller_approved", serde_json::json!(true)),
        ("document_id", serde_json::json!("foreign-document")),
        (
            "expected_head_generation",
            serde_json::json!(s.head.generation() + 1),
        ),
        (
            "expected_source_package_sha256",
            serde_json::json!(hex::encode([0; 32])),
        ),
    ] {
        let mut changed = raw.clone();
        changed[key] = value;
        assert!(
            matches!(
                policy.prepare_product_json(&p, &repo, &serde_json::to_vec(&changed)?, &access, 10),
                Err(StoredPolicyProductError::Product(_))
            ),
            "{key}"
        );
    }
    let duplicate = String::from_utf8(serde_json::to_vec(&raw)?)?.replacen(
        "\"schema_version\":",
        "\"schema_version\":\"duplicate\",\"schema_version\":",
        1,
    );
    assert!(
        policy
            .prepare_product_json(&p, &repo, duplicate.as_bytes(), &access, 11)
            .is_err()
    );
    let oversized = vec![b' '; 2 * 1024 * 1024 + 1];
    assert!(
        policy
            .prepare_product_json(&p, &repo, &oversized, &access, 11)
            .is_err()
    );
    assert_eq!(ingests(&s)?, 3);
    Ok(())
}
#[test]
fn same_values_new_policy_generation_invalidates_whole_cached_product_no_old_fallback() -> TestResult
{
    let (s, repo) = setup("five-kinds")?;
    let p = s.provider()?;
    let imported = p.import_actual_forms(s.head, 8)?;
    let explicit = direct(&imported)?;
    let (raw, access) = request("five-kinds", &s, &explicit)?;
    let raw = serde_json::to_vec(&raw)?;
    let policy = imported.bind_stored_policies(&p, &repo, 9)?;
    let prepared = policy.prepare_product_json(&p, &repo, &raw, &access, 10)?;
    publish(&s, &repo, 1)?;
    assert!(matches!(
        prepared.verify(&p, &repo, &access, 11),
        Err(StoredPolicyProductError::Policy(
            StoredSourcePolicyError::Drift
        ))
    ));
    assert!(
        prepared
            .require_current_product_route(&p, &repo, &access, 11)
            .is_err()
    );
    assert!(
        policy
            .prepare_product_json(&p, &repo, &raw, &access, 11)
            .is_err()
    );
    let latest = imported.bind_stored_policies(&p, &repo, 12)?;
    let next = latest.prepare_product_json(&p, &repo, &raw, &access, 13)?;
    assert_eq!(next.candidate_bytes(), prepared.candidate_bytes());
    assert_eq!(next.receipt().policy.policy_generation, 2);
    assert_ne!(
        next.receipt().policy.policy_version,
        prepared.receipt().policy.policy_version
    );
    assert_eq!(ingests(&s)?, 4);
    assert_eq!(
        s.revisions.head(&s.revision_context, s.project, s.branch)?,
        s.head
    );
    Ok(())
}
#[test]
fn repository_revocation_mid_verification_denies_after_original_compiler_reads() -> TestResult {
    let (s, repo) = setup("five-kinds")?;
    let p = s.provider()?;
    let imported = p.import_actual_forms(s.head, 8)?;
    let explicit = direct(&imported)?;
    let (raw, access) = request("five-kinds", &s, &explicit)?;
    let policy = imported.bind_stored_policies(&p, &repo, 9)?;
    let prepared =
        policy.prepare_product_json(&p, &repo, &serde_json::to_vec(&raw)?, &access, 10)?;
    // Original policy verification makes two repository reads; deny at the post-product re-read.
    repo.deny_at
        .store(repo.reads.load(Ordering::SeqCst) + 3, Ordering::SeqCst);
    assert!(matches!(
        prepared.verify(&p, &repo, &access, 11),
        Err(StoredPolicyProductError::Policy(
            StoredSourcePolicyError::Repository
        ))
    ));
    repo.deny.store(true, Ordering::SeqCst);
    assert!(
        policy
            .prepare_product_json(&p, &repo, &serde_json::to_vec(&raw)?, &access, 12)
            .is_err()
    );
    assert_eq!(ingests(&s)?, 3);
    Ok(())
}
#[test]
fn fresh_policy_acl_revocation_and_source_aead_tamper_deny_cached_product() -> TestResult {
    for tamper in [false, true] {
        let (s, repo) = setup("five-kinds")?;
        let p = s.provider()?;
        let imported = p.import_actual_forms(s.head, 8)?;
        let explicit = direct(&imported)?;
        let (raw, access) = request("five-kinds", &s, &explicit)?;
        let policy = imported.bind_stored_policies(&p, &repo, 9)?;
        let prepared =
            policy.prepare_product_json(&p, &repo, &serde_json::to_vec(&raw)?, &access, 10)?;
        if tamper {
            s.blobs.tamper.store(true, Ordering::SeqCst);
        } else {
            s.artifacts.set_permissions(
                &s.owner,
                policy.receipt().policy_artifact,
                s.reader.subject(),
                BTreeSet::new(),
                11,
            )?;
        }
        assert!(matches!(
            prepared.verify(&p, &repo, &access, 12),
            Err(StoredPolicyProductError::Policy(_))
        ));
        assert!(
            prepared
                .require_current_product_route(&p, &repo, &access, 12)
                .is_err()
        );
        assert_eq!(ingests(&s)?, 3);
    }
    Ok(())
}
#[test]
fn changed_head_provider_and_trusted_input_access_deny_without_source_or_policy_write() -> TestResult
{
    let (s, repo) = setup("five-kinds")?;
    let p = s.provider()?;
    let imported = p.import_actual_forms(s.head, 8)?;
    let explicit = direct(&imported)?;
    let (raw, access) = request("five-kinds", &s, &explicit)?;
    let policy = imported.bind_stored_policies(&p, &repo, 9)?;
    let prepared =
        policy.prepare_product_json(&p, &repo, &serde_json::to_vec(&raw)?, &access, 10)?;
    let mut denied = access.clone();
    denied.input_allowed = false;
    assert!(matches!(
        prepared.verify(&p, &repo, &denied, 11),
        Err(StoredPolicyProductError::Product(_))
    ));
    let c = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
    let foreign = writer(&s, &c)?;
    assert!(matches!(
        prepared.verify(&foreign, &repo, &access, 11),
        Err(StoredPolicyProductError::Policy(
            StoredSourcePolicyError::Source
        ))
    ));
    s.advance()?;
    assert!(matches!(
        prepared.verify(&p, &repo, &access, 12),
        Err(StoredPolicyProductError::Policy(
            StoredSourcePolicyError::Source
        ))
    ));
    assert_eq!(ingests(&s)?, 3);
    Ok(())
}
