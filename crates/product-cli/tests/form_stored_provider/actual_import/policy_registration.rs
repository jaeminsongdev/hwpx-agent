//! Synthetic server repository/actor; real `ArtifactService` AEAD and complete source-policy binding.
use super::super::{Provider, StoredFixture, TestResult, fixture_artifacts};
use super::{explicit_test_policies, fixture_bytes};
use artifact_service::{ArtifactKind, ArtifactMetadataRepository, ContentDigest};
use domain_ir::DocumentId;
use hwpx_agent_cli::form_stored_provider::{
    StoredFormProvider,
    actual_import::source_policy::{
        PolicyReadScope, SourcePolicyRepository, SourcePolicyVersion, StoredSourcePolicyError,
        registration::{
            PolicyRegistrationError, PolicyRegistrationRecord, SourcePolicyRegistrationRepository,
        },
    },
};
use revision_service::RevisionRequestContext;
use std::sync::{
    Mutex,
    atomic::{AtomicUsize, Ordering},
};

#[derive(Default)]
struct Repository {
    row: Mutex<Option<SourcePolicyVersion>>,
    calls: AtomicUsize,
    error: Option<PolicyRegistrationError>,
    corrupt_reply: bool,
}
impl SourcePolicyRegistrationRepository for Repository {
    fn register(
        &self,
        scope: &PolicyReadScope,
        r: &PolicyRegistrationRecord,
    ) -> Result<SourcePolicyVersion, PolicyRegistrationError> {
        self.calls.fetch_add(1, Ordering::SeqCst);
        if let Some(ref e) = self.error {
            return Err(match e {
                PolicyRegistrationError::OutcomeUnknown => PolicyRegistrationError::OutcomeUnknown,
                _ => PolicyRegistrationError::Repository,
            });
        }
        let mut row = self
            .row
            .lock()
            .map_err(|_| PolicyRegistrationError::Repository)?;
        let generation = row.as_ref().map_or(0, |x| x.binding.policy_generation);
        if generation != r.expected_generation()
            || scope.subject() != r.version().binding.creator_subject
        {
            return Err(PolicyRegistrationError::Repository);
        }
        *row = Some(r.version().clone());
        let mut reply = r.version().clone();
        if self.corrupt_reply {
            reply.digest = ContentDigest::of(b"wrong fixture reply");
        }
        Ok(reply)
    }
}
impl SourcePolicyRepository for Repository {
    fn read_current(
        &self,
        s: &PolicyReadScope,
    ) -> Result<SourcePolicyVersion, StoredSourcePolicyError> {
        let r = self
            .row
            .lock()
            .map_err(|_| StoredSourcePolicyError::Repository)?
            .clone()
            .ok_or(StoredSourcePolicyError::Repository)?;
        if r.binding.creator_subject != s.subject() || r.binding.document != *s.document() {
            return Err(StoredSourcePolicyError::Repository);
        }
        Ok(r)
    }
}
fn fixture() -> Result<StoredFixture, Box<dyn std::error::Error>> {
    StoredFixture::new(
        &fixture_bytes("five-kinds", "source")?,
        ArtifactKind::Result,
        false,
    )
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
fn ingests(s: &StoredFixture) -> Result<usize, Box<dyn std::error::Error>> {
    Ok(s.metadata
        .audit_events()?
        .iter()
        .filter(|x| x.event == "artifact.ingested")
        .count())
}
#[test]
fn validated_registration_reads_back_whole_policy_and_new_generation_without_source_write()
-> TestResult {
    let s = fixture()?;
    let context = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
    let p = writer(&s, &context)?;
    let imported = p.import_actual_forms(s.head, 4)?;
    let policies = explicit_test_policies(imported.imported());
    let repo = Repository::default();
    let prepared = imported.prepare_policy_registration(&p, &policies, 0, 5)?;
    assert_eq!(
        format!("{prepared:?}"),
        "PreparedSourcePolicyRegistration(<redacted>)"
    );
    assert_eq!(ingests(&s)?, 2);
    let receipt = prepared.register(&p, &repo, 6)?;
    assert_eq!(receipt.version.policy_generation, 1);
    assert_eq!(receipt.version.creator_subject, s.owner.subject());
    let read = imported.bind_stored_policies(&p, &repo, 7)?;
    assert_eq!(read.receipt().policy, receipt.policy);
    assert_eq!(read.receipt().policy_artifact, receipt.artifact);
    assert_eq!(read.verify(&p, &repo, 8)?, *read.receipt());
    assert_eq!(ingests(&s)?, 3);
    assert!(matches!(
        prepared.register(&p, &repo, 9),
        Err(PolicyRegistrationError::Repository)
    ));
    assert_eq!(ingests(&s)?, 3);
    let next = imported
        .prepare_policy_registration(&p, &policies, 1, 10)?
        .register(&p, &repo, 11)?;
    assert_eq!(next.version.policy_generation, 2);
    assert_ne!(next.version.policy_version, receipt.version.policy_version);
    assert!(read.verify(&p, &repo, 12).is_err());
    assert_eq!(ingests(&s)?, 4);
    assert_eq!(s.revisions.head(&context, s.project, s.branch)?, s.head);
    Ok(())
}
#[test]
fn read_only_incomplete_and_exhausted_generation_deny_before_any_policy_ingest() -> TestResult {
    let s = fixture()?;
    let reader = s.provider()?;
    let imported = reader.import_actual_forms(s.head, 4)?;
    let policies = explicit_test_policies(imported.imported());
    assert!(matches!(
        imported.prepare_policy_registration(&reader, &policies, 0, 5),
        Err(PolicyRegistrationError::Scope)
    ));
    let c = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
    let writer = writer(&s, &c)?;
    let imported = writer.import_actual_forms(s.head, 6)?;
    let mut policies = explicit_test_policies(imported.imported());
    policies.pop();
    assert!(matches!(
        imported.prepare_policy_registration(&writer, &policies, 0, 7),
        Err(PolicyRegistrationError::Policy)
    ));
    assert!(matches!(
        imported.prepare_policy_registration(&writer, &[], i64::MAX as u64, 8),
        Err(PolicyRegistrationError::Binding)
    ));
    assert_eq!(ingests(&s)?, 2);
    Ok(())
}
#[test]
fn source_head_change_rejects_prepared_registration_before_artifact_or_repository_write()
-> TestResult {
    let s = fixture()?;
    let c = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
    let p = writer(&s, &c)?;
    let imported = p.import_actual_forms(s.head, 4)?;
    let prepared = imported.prepare_policy_registration(
        &p,
        &explicit_test_policies(imported.imported()),
        0,
        5,
    )?;
    s.advance()?;
    let repo = Repository::default();
    assert!(matches!(
        prepared.register(&p, &repo, 6),
        Err(PolicyRegistrationError::Source)
    ));
    assert_eq!(repo.calls.load(Ordering::SeqCst), 0);
    assert_eq!(ingests(&s)?, 2);
    Ok(())
}
#[test]
fn repository_denial_unknown_ack_and_corrupt_reply_remain_distinct_no_blind_retry() -> TestResult {
    for (error, corrupt, want_unknown) in [
        (Some(PolicyRegistrationError::Repository), false, false),
        (Some(PolicyRegistrationError::OutcomeUnknown), false, true),
        (None, true, true),
    ] {
        let s = fixture()?;
        let c = RevisionRequestContext::new(s.owner.tenant_id(), s.owner.subject());
        let p = writer(&s, &c)?;
        let imported = p.import_actual_forms(s.head, 4)?;
        let repo = Repository {
            error,
            corrupt_reply: corrupt,
            ..Repository::default()
        };
        let prepared = imported.prepare_policy_registration(
            &p,
            &explicit_test_policies(imported.imported()),
            0,
            5,
        )?;
        let result = prepared.register(&p, &repo, 6);
        if want_unknown {
            assert!(matches!(
                result,
                Err(PolicyRegistrationError::OutcomeUnknown)
            ));
        } else {
            assert!(matches!(result, Err(PolicyRegistrationError::Repository)));
        }
        assert_eq!(repo.calls.load(Ordering::SeqCst), 1);
        assert_eq!(ingests(&s)?, 3); // retain unregistered/ambiguous Evidence; never erase source.
        assert_eq!(s.revisions.head(&c, s.project, s.branch)?, s.head);
    }
    Ok(())
}
#[test]
fn unverified_policy_scan_cannot_reach_registration_repository() -> TestResult {
    let s = fixture()?;
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
    let imported = p.import_actual_forms(s.head, 4)?;
    let prepared = imported.prepare_policy_registration(
        &p,
        &explicit_test_policies(imported.imported()),
        0,
        5,
    )?;
    let repo = Repository::default();
    assert!(matches!(
        prepared.register(&p, &repo, 6),
        Err(PolicyRegistrationError::Artifact)
    ));
    assert_eq!(repo.calls.load(Ordering::SeqCst), 0);
    assert_eq!(ingests(&s)?, 3);
    Ok(())
}
