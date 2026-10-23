#![allow(dead_code)] // Shared read-only source fixture includes unrelated provider helpers.
use std::{cell::Cell, error::Error};
use domain_ir::DocumentId;
use hwpx_agent_cli::stored_revision_commit::*;
use operation_engine::{ExecutionManifest, FaultPlan, RevisionCas, RevisionCasOutcome,
    RevisionCommitRequest as EngineRequest, TransactionError, TransactionState,
    ArtifactDisposition, ValidationOutcome, WorkspaceTransaction};
use revision_service::{RevisionError, RevisionId, RevisionNode, RevisionRepository};
use sha2::{Digest as _, Sha256};
type TestResult = Result<(), Box<dyn Error>>;
include!("support/stored_source_fixture.rs");
#[path="support/stored_commit_manifest.rs"] mod manifest_fixture;

// Synthetic bytes/route/scanner/validation summary; actual service encryption/ingest/CAS code.
// This is NOT a semantic HWPX validator, durable database or authorized P09/Native execution.
const SOURCE: &[u8] = b"synthetic immutable stored source";
const OUTPUT: &[u8] = b"synthetic validated stored output";

fn writer(f: &StoredFixture) -> RequestContext {
    RequestContext::new(f.reader.tenant_id(), f.reader.subject(), [AuthScope::DocumentRead, AuthScope::DocumentWrite])
}
fn binding<'a>(f: &StoredFixture, manifest: &'a ExecutionManifest, output: &'a [u8]) -> StoredCommitBinding<'a> {
    StoredCommitBinding { manifest, output, project: f.project, branch: f.branch, expected_head: f.head,
        commit: CommitId::generate(), new_revision: RevisionId::generate(),
        validation_summary: ContentDigest::of(b"synthetic validation summary, not P09 qualification") }
}
fn fixture() -> Result<StoredFixture, Box<dyn Error>> { StoredFixture::new(SOURCE, ArtifactKind::Result, false) }
fn execute<C: RevisionCas>(root: &std::path::Path, manifest: ExecutionManifest, output: &[u8], cas: &mut C)
    -> Result<operation_engine::TransactionReceipt, operation_engine::TransactionFailure> {
    let mut tx = WorkspaceTransaction::create(root, manifest, Default::default()).unwrap_or_else(|e| panic!("synthetic transaction: {e}"));
    tx.execute_bytes(SOURCE, output, &mut |_: &[u8]| ValidationOutcome::Valid, cas, &mut FaultPlan::none())
}

#[derive(Clone)]
struct FaultRevision { inner: InMemoryRevisionRepository, mode: u8, calls: Arc<std::sync::atomic::AtomicUsize> }
impl FaultRevision {
    fn service(f: &StoredFixture, mode: u8) -> RevisionService<Self> {
        RevisionService::new(Self { inner: f.revisions.repository().clone(), mode, calls: Arc::default() })
    }
}
impl RevisionRepository for FaultRevision {
    fn compare_and_swap(&self, context: &RevisionRequestContext, request: &RevisionCommitRequest)
        -> Result<CommitOutcome, RevisionError> {
        self.calls.fetch_add(1, Ordering::SeqCst);
        match self.mode {
            1 => Err(RevisionError::RepositoryFailure),
            2 => Err(RevisionError::CommitOutcomeUnknown),
            3 => { self.inner.compare_and_swap(context, request)?; Err(RevisionError::CommitOutcomeUnknown) }
            4 | 5 => {
                let competing = RevisionCommitRequest::new(CommitId::generate(), request.project_id(), request.branch_id(),
                    request.expected_head(), RevisionId::generate(), request.parents().to_vec(), request.source_artifact_id(),
                    request.result_artifact_id(), None, request.operation_plan_sha256(), RevisionValidationState::Verified,
                    request.validation_summary_sha256(), request.transaction_receipt_sha256())?;
                let other = self.inner.compare_and_swap(context, &competing)?;
                if self.mode == 5 { Ok(other) } else { self.inner.compare_and_swap(context, request) }
            }
            _ => self.inner.compare_and_swap(context, request),
        }
    }
    fn head(&self, tenant: TenantId, project: revision_service::ProjectId, branch: BranchId) -> Result<RevisionHead, RevisionError> {
        self.inner.head(tenant, project, branch)
    }
    fn node(&self, tenant: TenantId, project: revision_service::ProjectId, revision: RevisionId) -> Result<RevisionNode, RevisionError> {
        self.inner.node(tenant, project, revision)
    }
}

#[test]
fn actual_services_ingest_encrypt_readback_and_commit_exact_engine_binding() -> TestResult {
    let f = fixture()?; let context = writer(&f); let manifest = manifest_fixture::manifest(&f, "stored-success")?;
    let mut cas = StoredResultRevisionCas::bind(&f.artifacts, &f.revisions, &context, &f.revision_context,
        binding(&f, &manifest, OUTPUT), || 10)?;
    let root = tempfile::tempdir()?;
    let receipt = execute(&root.path().join("workspace"), manifest.clone(), OUTPUT, &mut cas)?;
    assert_eq!(receipt.state(), TransactionState::Completed);
    let result = cas.retained_result().ok_or("result not retained")?;
    assert_eq!(f.artifacts.download(&context, result.artifact_id, 11)?, OUTPUT);
    assert_eq!(f.artifacts.download(&f.reader, f.result, 11)?, SOURCE);
    let request = cas.service_request().ok_or("request missing")?;
    assert_eq!(request.source_artifact_id(), f.result);
    assert_eq!(request.result_artifact_id(), result.artifact_id);
    assert_eq!(request.operation_plan_sha256().as_bytes(), &manifest.compiled_plan_sha256());
    assert_eq!(f.revisions.head(&f.revision_context, f.project, f.branch)?, cas.service_receipt().ok_or("receipt")?.committed_head());
    assert_eq!(f.revisions.node(&f.revision_context, f.project, request.new_revision_id())?.result_artifact_id(), result.artifact_id);
    assert!(cas.error().is_none()); Ok(())
}

#[test]
fn service_unknown_before_and_after_commit_both_preserve_output_without_blind_retry() -> TestResult {
    for mode in [2, 3] {
        let f = fixture()?; let context = writer(&f); let revisions = FaultRevision::service(&f, mode);
        let manifest = manifest_fixture::manifest(&f, "stored-unknown")?;
        let mut cas = StoredResultRevisionCas::bind(&f.artifacts, &revisions, &context, &f.revision_context,
            binding(&f, &manifest, OUTPUT), || 10)?;
        let root = tempfile::tempdir()?;
        let failure = execute(&root.path().join("workspace"), manifest.clone(), OUTPUT, &mut cas).expect_err("unknown");
        assert_eq!(failure.primary(), TransactionError::RevisionOutcomeUnknown);
        assert_eq!(failure.receipt().state(), TransactionState::Incomplete);
        assert_eq!(failure.receipt().artifact_disposition(), ArtifactDisposition::CommittedOutcomeUncertain);
        assert!(failure.recovery().is_none());
        let head = revisions.head(&f.revision_context, f.project, f.branch)?;
        assert_eq!(head == f.head, mode == 2);
        assert_eq!(cas.error(), Some(StoredCommitError::Unknown));
        let result = cas.retained_result().ok_or("result")?;
        assert_eq!(f.artifacts.download(&context, result.artifact_id, 11)?, OUTPUT);
        assert_eq!(std::fs::read(root.path().join("workspace/output/artifacts").join(format!("{}.hwpx", result.sha256.hex())))?, OUTPUT);
        assert_eq!(revisions.repository().calls.load(Ordering::SeqCst), 1);
        if mode == 3 { assert_eq!(head.revision_id(), Some(cas.service_request().ok_or("request")?.new_revision_id())); }
    } Ok(())
}

#[test]
fn known_revision_failure_keeps_recoverable_service_result_and_quarantines_local_copy() -> TestResult {
    let f = fixture()?; let context = writer(&f); let revisions = FaultRevision::service(&f, 1);
    let manifest = manifest_fixture::manifest(&f, "stored-failure")?;
    let mut cas = StoredResultRevisionCas::bind(&f.artifacts, &revisions, &context, &f.revision_context, binding(&f, &manifest, OUTPUT), || 10)?;
    let root = tempfile::tempdir()?;
    let failure = execute(&root.path().join("workspace"), manifest.clone(), OUTPUT, &mut cas).expect_err("failure");
    assert_eq!(failure.primary(), TransactionError::RevisionCasFailed);
    assert_eq!(failure.receipt().state(), TransactionState::Quarantined);
    assert_eq!(cas.error(), Some(StoredCommitError::Revision));
    assert_eq!(revisions.head(&f.revision_context, f.project, f.branch)?, f.head);
    assert_eq!(f.artifacts.download(&context, cas.retained_result().ok_or("retained")?.artifact_id, 11)?, OUTPUT);
    assert_eq!(f.metadata.find_by_content(context.tenant_id(), cas.output_sha256())?.ok_or("recovery digest")?.descriptor().artifact_id,
        cas.retained_result().ok_or("retained")?.artifact_id);
    assert!(cas.service_request().is_some()); Ok(())
}

#[test]
fn concurrent_head_cas_conflict_does_not_report_our_revision_committed() -> TestResult {
    let f = fixture()?; let context = writer(&f); let revisions = FaultRevision::service(&f, 4);
    let manifest = manifest_fixture::manifest(&f, "stored-race")?;
    let mut cas = StoredResultRevisionCas::bind(&f.artifacts, &revisions, &context, &f.revision_context, binding(&f, &manifest, OUTPUT), || 10)?;
    let root = tempfile::tempdir()?;
    let failure = execute(&root.path().join("workspace"), manifest.clone(), OUTPUT, &mut cas).expect_err("conflict");
    assert_eq!(failure.primary(), TransactionError::RevisionConflict);
    assert_eq!(cas.error(), Some(StoredCommitError::Conflict));
    assert!(cas.service_receipt().is_none());
    assert_ne!(revisions.head(&f.revision_context, f.project, f.branch)?.revision_id(), Some(cas.service_request().ok_or("request")?.new_revision_id()));
    assert_eq!(f.artifacts.download(&context, cas.retained_result().ok_or("retained")?.artifact_id, 11)?, OUTPUT); Ok(())
}

#[test]
fn wrong_success_receipt_is_unknown_not_a_false_completion_or_rollback() -> TestResult {
    let f = fixture()?; let context = writer(&f); let revisions = FaultRevision::service(&f, 5);
    let manifest = manifest_fixture::manifest(&f, "stored-wrong-receipt")?;
    let mut cas = StoredResultRevisionCas::bind(&f.artifacts, &revisions, &context, &f.revision_context, binding(&f, &manifest, OUTPUT), || 10)?;
    let root = tempfile::tempdir()?;
    let failure = execute(&root.path().join("workspace"), manifest.clone(), OUTPUT, &mut cas).expect_err("wrong receipt");
    assert_eq!(failure.primary(), TransactionError::RevisionOutcomeUnknown);
    assert_eq!(failure.receipt().artifact_disposition(), ArtifactDisposition::CommittedOutcomeUncertain);
    assert!(cas.service_receipt().is_some()); Ok(())
}

#[test]
fn source_acl_quarantine_or_ciphertext_drift_blocks_ingest_and_revision_cas() -> TestResult {
    for mode in [0, 1, 2] {
        let f = fixture()?; let context = writer(&f); let revisions = FaultRevision::service(&f, 0);
        let manifest = manifest_fixture::manifest(&f, "stored-source-denial")?;
        let mut cas = StoredResultRevisionCas::bind(&f.artifacts, &revisions, &context, &f.revision_context, binding(&f, &manifest, OUTPUT), || 10)?;
        match mode {
            0 => { f.artifacts.set_permissions(&f.owner, f.result, f.reader.subject(), BTreeSet::new(), 9)?; }
            1 => { f.artifacts.quarantine(&f.owner, f.result, QuarantineReason::parse("FIXTURE_DENIED")?, 9)?; }
            _ => f.blobs.tamper.store(true, Ordering::SeqCst),
        }
        let root = tempfile::tempdir()?;
        execute(&root.path().join("workspace"), manifest.clone(), OUTPUT, &mut cas).expect_err("source denial");
        assert_eq!(cas.error(), Some(StoredCommitError::Source));
        assert!(cas.retained_result().is_none());
        assert_eq!(revisions.repository().calls.load(Ordering::SeqCst), 0);
        assert_eq!(revisions.head(&f.revision_context, f.project, f.branch)?, f.head);
    } Ok(())
}

#[test]
fn mismatched_scope_and_read_only_context_cannot_bind_writer() -> TestResult {
    let f = fixture()?; let manifest = manifest_fixture::manifest(&f, "stored-scope")?;
    for context in [f.reader.clone(), RequestContext::new(f.owner.tenant_id(), f.owner.subject(), [AuthScope::DocumentRead, AuthScope::DocumentWrite]),
        RequestContext::new(TenantId::new(Uuid::from_u128(999))?, f.reader.subject(), [AuthScope::DocumentRead, AuthScope::DocumentWrite])] {
        assert_eq!(StoredResultRevisionCas::bind(&f.artifacts, &f.revisions, &context, &f.revision_context, binding(&f, &manifest, OUTPUT), || 10).expect_err("scope"), StoredCommitError::Scope);
    } Ok(())
}

#[test]
fn foreign_engine_manifest_or_output_is_rejected_before_service_ingest() -> TestResult {
    for foreign_output in [false, true] {
        let f = fixture()?; let context = writer(&f); let manifest = manifest_fixture::manifest(&f, "stored-bound")?;
        let other = if foreign_output { manifest.clone() } else { manifest_fixture::manifest(&f, "stored-foreign")? };
        let mut cas = StoredResultRevisionCas::bind(&f.artifacts, &f.revisions, &context, &f.revision_context, binding(&f, &manifest, OUTPUT), || 10)?;
        let root = tempfile::tempdir()?;
        execute(&root.path().join("workspace"), other, if foreign_output { b"different output" } else { OUTPUT }, &mut cas).expect_err("binding");
        assert_eq!(cas.error(), Some(StoredCommitError::Binding)); assert!(cas.retained_result().is_none());
        assert_eq!(f.revisions.head(&f.revision_context, f.project, f.branch)?, f.head);
    } Ok(())
}

#[test]
fn unverified_result_scanner_preserves_quarantine_and_never_commits_revision() -> TestResult {
    let f = fixture()?; let context = writer(&f); let revisions = FaultRevision::service(&f, 0);
    let artifacts = fixture_artifacts(f.metadata.clone(), f.blobs.clone(), true)?;
    let manifest = manifest_fixture::manifest(&f, "stored-scanner")?;
    let mut cas = StoredResultRevisionCas::bind(&artifacts, &revisions, &context, &f.revision_context, binding(&f, &manifest, OUTPUT), || 10)?;
    let root = tempfile::tempdir()?;
    execute(&root.path().join("workspace"), manifest.clone(), OUTPUT, &mut cas).expect_err("unverified");
    assert_eq!(cas.error(), Some(StoredCommitError::Artifact));
    assert_eq!(cas.retained_result().ok_or("retained")?.storage_state, artifact_service::StorageState::Quarantined);
    assert_eq!(revisions.repository().calls.load(Ordering::SeqCst), 0); Ok(())
}

#[test]
fn result_aead_readback_failure_blocks_revision_and_retains_recovery_identity() -> TestResult {
    let f = fixture()?; let context = writer(&f); let revisions = FaultRevision::service(&f, 0);
    let manifest = manifest_fixture::manifest(&f, "stored-output-tamper")?; let calls = Cell::new(0);
    let clock = || { calls.set(calls.get() + 1); if calls.get() == 3 { f.blobs.tamper.store(true, Ordering::SeqCst); } 10 };
    let mut cas = StoredResultRevisionCas::bind(&f.artifacts, &revisions, &context, &f.revision_context, binding(&f, &manifest, OUTPUT), clock)?;
    let root = tempfile::tempdir()?;
    execute(&root.path().join("workspace"), manifest.clone(), OUTPUT, &mut cas).expect_err("AEAD");
    assert_eq!(cas.error(), Some(StoredCommitError::Artifact)); assert!(cas.retained_result().is_some());
    assert_eq!(cas.output_sha256(), ContentDigest::of(OUTPUT)); assert_eq!(revisions.repository().calls.load(Ordering::SeqCst), 0); Ok(())
}

#[test]
fn shared_deduplicated_result_is_never_quarantined_or_deleted_on_cas_failure() -> TestResult {
    let f = fixture()?; let context = writer(&f); let revisions = FaultRevision::service(&f, 1);
    let prior = f.artifacts.ingest(&f.owner, IngestRequest { bytes: OUTPUT.to_vec(), media_type: MediaType::parse("application/vnd.hancom.hwpx+zip")?,
        file_name: FileName::parse("result.hwpx")?, kind: ArtifactKind::Result }, 4)?;
    f.artifacts.set_permissions(&f.owner, prior.artifact_id, f.reader.subject(), BTreeSet::from([ArtifactPermission::Read]), 5)?;
    let manifest = manifest_fixture::manifest(&f, "stored-shared")?;
    let mut cas = StoredResultRevisionCas::bind(&f.artifacts, &revisions, &context, &f.revision_context, binding(&f, &manifest, OUTPUT), || 10)?;
    let root = tempfile::tempdir()?;
    execute(&root.path().join("workspace"), manifest.clone(), OUTPUT, &mut cas).expect_err("CAS failure");
    assert_eq!(cas.retained_result().ok_or("retained")?.artifact_id, prior.artifact_id);
    assert_eq!(f.artifacts.get_descriptor(&f.owner, prior.artifact_id, 11)?, prior);
    assert_eq!(f.artifacts.download(&f.owner, prior.artifact_id, 11)?, OUTPUT);
    assert_eq!(f.artifacts.download(&f.reader, prior.artifact_id, 11)?, OUTPUT); Ok(())
}

#[test]
fn single_use_adapter_preserves_unknown_on_second_callback_without_recommitting() -> TestResult {
    let f = fixture()?; let context = writer(&f); let revisions = FaultRevision::service(&f, 3);
    let manifest = manifest_fixture::manifest(&f, "stored-single-use")?;
    let mut cas = StoredResultRevisionCas::bind(&f.artifacts, &revisions, &context, &f.revision_context, binding(&f, &manifest, OUTPUT), || 10)?;
    let mut captured = None; let root = tempfile::tempdir()?;
    execute(&root.path().join("workspace"), manifest.clone(), OUTPUT, &mut |request: &EngineRequest| { captured = Some(request.clone()); cas.compare_and_swap(request) }).expect_err("unknown");
    assert_eq!(cas.compare_and_swap(captured.as_ref().ok_or("request")?), RevisionCasOutcome::Unknown);
    assert_eq!(revisions.repository().calls.load(Ordering::SeqCst), 1);
    let debug = format!("{cas:?}"); assert!(!debug.contains(std::str::from_utf8(SOURCE)?));
    assert!(!debug.contains(std::str::from_utf8(OUTPUT)?)); assert!(!debug.contains(&f.project.public_id())); Ok(())
}

#[test]
fn invalid_output_alias_limits_or_base_binding_cannot_prepare_storage_adapter() -> TestResult {
    let f = fixture()?; let context = writer(&f); let manifest = manifest_fixture::manifest(&f, "stored-invalid")?;
    for mode in 0..5 {
        let oversized; let mut input = binding(&f, &manifest, OUTPUT);
        match mode { 0 => input.output = b"", 1 => input.output = SOURCE,
            2 => { oversized = vec![b'X'; 32 * 1024 * 1024 + 1]; input.output = &oversized; }
            3 => input.new_revision = f.head.revision_id().ok_or("head")?,
            _ => input.expected_head = RevisionHead::new(Some(RevisionId::generate()), 1)?, }
        assert_eq!(StoredResultRevisionCas::bind(&f.artifacts, &f.revisions, &context, &f.revision_context, input, || 10).expect_err("binding"), StoredCommitError::Binding);
    } Ok(())
}
#[path="support/stored_commit_recovery.rs"] mod recovery_v1;
#[path="support/stored_precommit_receipt.rs"] mod precommit_v1;
#[path="support/stored_registered_commit.rs"] mod registered_v1;
#[path="support/stored_job_coordinator.rs"] mod job_v1;
