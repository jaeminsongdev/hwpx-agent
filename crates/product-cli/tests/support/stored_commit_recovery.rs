use super::*;
use revision_service::CommitObservation;

struct Saved {
    intent: artifact_service::ArtifactId,
    sha: ContentDigest,
    request: RevisionCommitRequest,
}
impl Saved {
    fn binding<'a>(&'a self, manifest: &'a ExecutionManifest) -> StoredCommitRecoveryBinding<'a> {
        StoredCommitRecoveryBinding { intent: self.intent, intent_sha256: self.sha, manifest,
            request: &self.request, result_sha256: ContentDigest::of(OUTPUT), result_size: OUTPUT.len() as u64 }
    }
}
fn commit_and_drop_adapter(f: &StoredFixture, manifest: &ExecutionManifest, mode: u8) -> Result<Saved, Box<dyn Error>> {
    let context = writer(f); let revisions = FaultRevision::service(f, mode);
    let mut cas = StoredResultRevisionCas::bind(&f.artifacts, &revisions, &context, &f.revision_context,
        binding(f, manifest, OUTPUT), || 10)?;
    let root = tempfile::tempdir()?;
    let result = execute(&root.path().join("workspace"), manifest.clone(), OUTPUT, &mut cas);
    if mode == 0 { assert!(result.is_ok()); } else { assert_eq!(result.expect_err("unknown").primary(), TransactionError::RevisionOutcomeUnknown); }
    let intent = cas.retained_intent().ok_or("intent must precede CAS")?;
    assert_eq!(intent.kind, ArtifactKind::Receipt);
    assert_eq!(intent.sha256, cas.intent_sha256().ok_or("intent digest")?);
    Ok(Saved { intent: intent.artifact_id, sha: intent.sha256, request: cas.service_request().ok_or("request")?.clone() })
}
fn admin(f: &StoredFixture) -> RequestContext {
    RequestContext::new(f.reader.tenant_id(), f.reader.subject(), [AuthScope::DocumentRead, AuthScope::DocumentWrite,
        AuthScope::ArtifactShare, AuthScope::SecurityModify])
}

#[test]
fn intent_is_exact_encrypted_receipt_and_recovery_works_with_fresh_service_instances() -> TestResult {
    let f = fixture()?; let manifest = manifest_fixture::manifest(&f, "intent-fresh-services")?;
    let saved = commit_and_drop_adapter(&f, &manifest, 0)?;
    let raw = f.artifacts.download(&f.reader, saved.intent, 11)?;
    let json: serde_json::Value = serde_json::from_slice(&raw)?;
    assert_eq!(json["schema_version"], "hwpx-agent.stored-revision-commit-intent/v1");
    assert_eq!(json["request"], serde_json::to_value(&saved.request)?);
    assert_eq!(ContentDigest::of(&raw), saved.sha);
    let artifacts = fixture_artifacts(f.metadata.clone(), f.blobs.clone(), false)?;
    let revisions = FaultRevision::service(&f, 0);
    // Reopened in-memory backings, NOT a database/process restart qualification.
    let recovered = reconcile_stored_commit(&artifacts, &revisions, &f.reader, &f.revision_context, &saved.binding(&manifest), || 12)?;
    match recovered {
        StoredCommitRecoveryOutcome::Committed { receipt, result: RecoveredResult::VerifiedAvailable(result) } => {
            assert_eq!(receipt.request_sha256(), saved.request.canonical_sha256()?);
            assert_eq!(result.artifact_id, saved.request.result_artifact_id());
        }
        _ => return Err("exact committed result not recovered".into()),
    }
    assert_eq!(revisions.repository().calls.load(Ordering::SeqCst), 0); Ok(())
}

#[test]
fn response_lost_after_commit_is_observed_without_reingest_or_revision_retry() -> TestResult {
    let f = fixture()?; let manifest = manifest_fixture::manifest(&f, "intent-after-commit")?;
    let saved = commit_and_drop_adapter(&f, &manifest, 3)?;
    let revisions = FaultRevision::service(&f, 0);
    for _ in 0..2 {
        assert!(matches!(reconcile_stored_commit(&f.artifacts, &revisions, &f.reader, &f.revision_context,
            &saved.binding(&manifest), || 12)?, StoredCommitRecoveryOutcome::Committed { result: RecoveredResult::VerifiedAvailable(_), .. }));
    }
    assert_eq!(revisions.repository().calls.load(Ordering::SeqCst), 0);
    assert_eq!(f.revisions.head(&f.revision_context, f.project, f.branch)?.generation(), 2); Ok(())
}

#[test]
fn unknown_before_commit_remains_not_observed_and_is_never_a_retry_authorization() -> TestResult {
    let f = fixture()?; let manifest = manifest_fixture::manifest(&f, "intent-before-commit")?;
    let saved = commit_and_drop_adapter(&f, &manifest, 2)?;
    let revisions = FaultRevision::service(&f, 0);
    for _ in 0..2 {
        assert_eq!(reconcile_stored_commit(&f.artifacts, &revisions, &f.reader, &f.revision_context,
            &saved.binding(&manifest), || 12)?, StoredCommitRecoveryOutcome::NotObserved);
    }
    assert_eq!(revisions.repository().calls.load(Ordering::SeqCst), 0);
    assert_eq!(f.revisions.head(&f.revision_context, f.project, f.branch)?, f.head); Ok(())
}

#[test]
fn later_branch_head_does_not_erase_the_exact_historical_commit() -> TestResult {
    let f = fixture()?; let manifest = manifest_fixture::manifest(&f, "intent-historical")?;
    let saved = commit_and_drop_adapter(&f, &manifest, 0)?;
    let before = f.revisions.head(&f.revision_context, f.project, f.branch)?;
    let next = RevisionCommitRequest::new(CommitId::generate(), f.project, f.branch, before, RevisionId::generate(),
        vec![saved.request.new_revision_id()], saved.request.result_artifact_id(), f.result, None,
        ContentDigest::of(b"next synthetic plan"), RevisionValidationState::Verified, ContentDigest::of(b"next synthetic validation"), ContentDigest::of(b"next transaction"))?;
    f.revisions.commit(&f.revision_context, &next)?;
    let observed = f.revisions.observe_commit(&f.revision_context, &saved.request)?;
    assert!(matches!(observed, CommitObservation::Committed(ref receipt) if receipt.committed_head() == before));
    assert_ne!(before, f.revisions.head(&f.revision_context, f.project, f.branch)?);
    assert!(matches!(reconcile_stored_commit(&f.artifacts, &f.revisions, &f.reader, &f.revision_context,
        &saved.binding(&manifest), || 13)?, StoredCommitRecoveryOutcome::Committed { .. })); Ok(())
}

#[test]
fn sealed_observation_rejects_changed_commit_branch_source_result_plan_summary_receipt_and_subject() -> TestResult {
    let f = fixture()?; let manifest = manifest_fixture::manifest(&f, "intent-exact-node")?;
    let saved = commit_and_drop_adapter(&f, &manifest, 0)?;
    for field in ["commit_id", "branch_id", "source_artifact_id", "result_artifact_id", "operation_plan_sha256", "validation_summary_sha256", "transaction_receipt_sha256"] {
        let mut json = serde_json::to_value(&saved.request)?;
        json[field] = match field {
            "commit_id" => serde_json::to_value(CommitId::generate())?,
            "branch_id" => serde_json::to_value(BranchId::generate())?,
            "source_artifact_id" | "result_artifact_id" => serde_json::to_value(artifact_service::ArtifactId::generate())?,
            _ => serde_json::to_value(ContentDigest::of(b"foreign binding"))?,
        };
        let foreign: RevisionCommitRequest = serde_json::from_value(json)?;
        assert_eq!(f.revisions.observe_commit(&f.revision_context, &foreign).expect_err("changed request"), RevisionError::InvalidRequest);
    }
    let foreign = RevisionRequestContext::new(f.reader.tenant_id(), f.owner.subject());
    assert_eq!(f.revisions.observe_commit(&foreign, &saved.request).expect_err("foreign subject"), RevisionError::InvalidRequest);
    Ok(())
}

#[test]
fn intent_sha_manifest_result_size_or_request_binding_drift_is_rejected() -> TestResult {
    let f = fixture()?; let manifest = manifest_fixture::manifest(&f, "intent-pins")?;
    let other = manifest_fixture::manifest(&f, "intent-other")?;
    let saved = commit_and_drop_adapter(&f, &manifest, 0)?;
    for mode in 0..5 {
        let mut pin = saved.binding(&manifest);
        match mode { 0 => pin.intent_sha256 = ContentDigest::of(b"wrong digest"), 1 => pin.manifest = &other,
            2 => pin.result_sha256 = ContentDigest::of(b"wrong output"), 3 => pin.result_size += 1, _ => pin.result_size = 0 }
        assert!(reconcile_stored_commit(&f.artifacts, &f.revisions, &f.reader, &f.revision_context, &pin, || 13).is_err());
    } Ok(())
}

fn store_intent(f: &StoredFixture, bytes: Vec<u8>) -> Result<artifact_service::ArtifactDescriptor, Box<dyn Error>> {
    Ok(f.artifacts.ingest(&writer(f), IngestRequest { bytes, media_type: MediaType::parse("application/json")?,
        file_name: FileName::parse("revision-intent.json")?, kind: ArtifactKind::Receipt }, 12)?)
}

#[test]
fn malformed_duplicate_unknown_or_foreign_intent_data_is_not_authority() -> TestResult {
    let f = fixture()?; let manifest = manifest_fixture::manifest(&f, "intent-json")?;
    let saved = commit_and_drop_adapter(&f, &manifest, 0)?;
    let original = f.artifacts.download(&f.reader, saved.intent, 11)?;
    for mode in 0..5 {
        let mut json: serde_json::Value = serde_json::from_slice(&original)?;
        let bytes = match mode {
            0 => { json["unknown_grant"] = true.into(); serde_json::to_vec(&json)? }
            1 => { let text = std::str::from_utf8(&original)?; format!("{{\"schema_version\":\"duplicate\",{}", &text[1..]).into_bytes() }
            2 => { json["schema_version"] = "foreign-schema".into(); serde_json::to_vec(&json)? }
            3 => { json["subject"] = serde_json::to_value(f.owner.subject())?; serde_json::to_vec(&json)? }
            _ => b"{".to_vec(),
        };
        let stored = store_intent(&f, bytes)?; let mut pin = saved.binding(&manifest); pin.intent = stored.artifact_id; pin.intent_sha256 = stored.sha256;
        assert_eq!(reconcile_stored_commit(&f.artifacts, &f.revisions, &f.reader, &f.revision_context, &pin, || 13).expect_err("invalid intent"), StoredCommitError::Binding);
    } Ok(())
}

#[test]
fn oversized_intent_is_refused_before_json_parsing() -> TestResult {
    let f = fixture()?; let manifest = manifest_fixture::manifest(&f, "intent-oversize")?;
    let saved = commit_and_drop_adapter(&f, &manifest, 0)?;
    let stored = store_intent(&f, vec![b'X'; 64 * 1024 + 1])?;
    let mut pin = saved.binding(&manifest); pin.intent = stored.artifact_id; pin.intent_sha256 = stored.sha256;
    assert_eq!(reconcile_stored_commit(&f.artifacts, &f.revisions, &f.reader, &f.revision_context, &pin, || 13).expect_err("oversized"), StoredCommitError::Artifact); Ok(())
}

#[test]
fn quarantined_or_aead_invalid_intent_blocks_recovery_without_a_write() -> TestResult {
    for tamper in [false, true] {
        let f = fixture()?; let manifest = manifest_fixture::manifest(&f, "intent-unreadable")?;
        let saved = commit_and_drop_adapter(&f, &manifest, 0)?; let revisions = FaultRevision::service(&f, 0);
        if tamper { f.blobs.tamper.store(true, Ordering::SeqCst); }
        else { f.artifacts.quarantine(&admin(&f), saved.intent, QuarantineReason::parse("FIXTURE_INTENT_DENIED")?, 12)?; }
        assert_eq!(reconcile_stored_commit(&f.artifacts, &revisions, &f.reader, &f.revision_context,
            &saved.binding(&manifest), || 13).expect_err("intent denied"), StoredCommitError::Artifact);
        assert_eq!(revisions.repository().calls.load(Ordering::SeqCst), 0);
    } Ok(())
}

#[test]
fn quarantined_result_keeps_commit_observed_but_is_not_servable() -> TestResult {
    let f = fixture()?; let manifest = manifest_fixture::manifest(&f, "intent-result-denied")?;
    let saved = commit_and_drop_adapter(&f, &manifest, 0)?;
    f.artifacts.quarantine(&admin(&f), saved.request.result_artifact_id(), QuarantineReason::parse("FIXTURE_RESULT_DENIED")?, 12)?;
    let recovered = reconcile_stored_commit(&f.artifacts, &f.revisions, &f.reader, &f.revision_context, &saved.binding(&manifest), || 13)?;
    assert!(matches!(recovered, StoredCommitRecoveryOutcome::Committed { result: RecoveredResult::Unavailable, .. })); Ok(())
}

#[test]
fn foreign_recovery_context_cannot_use_another_subjects_intent() -> TestResult {
    let f = fixture()?; let manifest = manifest_fixture::manifest(&f, "intent-scope")?;
    let saved = commit_and_drop_adapter(&f, &manifest, 0)?;
    assert_eq!(reconcile_stored_commit(&f.artifacts, &f.revisions, &f.owner, &f.revision_context,
        &saved.binding(&manifest), || 13).expect_err("scope"), StoredCommitError::Scope);
    let no_read = RequestContext::new(f.reader.tenant_id(), f.reader.subject(), [AuthScope::DocumentWrite]);
    assert_eq!(reconcile_stored_commit(&f.artifacts, &f.revisions, &no_read, &f.revision_context,
        &saved.binding(&manifest), || 13).expect_err("read scope"), StoredCommitError::Scope); Ok(())
}

#[derive(Debug)]
struct DeniedReceiptScanner;
impl ArtifactScanner for DeniedReceiptScanner {
    fn scan(&self, request: ScanRequest<'_>) -> Result<ScanEvidence, artifact_service::ArtifactError> {
        let mut evidence = FixtureScanner { unavailable: false }.scan(request)?;
        if request.kind == ArtifactKind::Receipt && request.file_name.as_str() == "revision-intent.json" { evidence.verdict = ScanVerdict::Unverified(QuarantineReason::parse("FIXTURE_RECEIPT_UNVERIFIED")?); }
        Ok(evidence)
    }
}

#[test]
fn unverified_intent_is_retained_and_blocks_the_only_revision_cas() -> TestResult {
    let f = fixture()?; let context = writer(&f); let manifest = manifest_fixture::manifest(&f, "intent-scanner")?;
    let key = KeyReference::parse("fixture.p45-aes")?;
    let artifacts = ArtifactService::new(f.metadata.clone(), f.blobs.clone(), DeniedReceiptScanner,
        Aes256GcmKeyring::new(key.clone(), [(key, [45; 32])])?,
        DownloadSigner::new("https://fixture.example.test/download", KeyReference::parse("fixture.p45-hmac")?, &[46; 32], 60)?,
        ArtifactServiceConfig::new(32 * 1024 * 1024, 60)?);
    let revisions = FaultRevision::service(&f, 0);
    let mut cas = StoredResultRevisionCas::bind(&artifacts, &revisions, &context, &f.revision_context, binding(&f, &manifest, OUTPUT), || 10)?;
    let root = tempfile::tempdir()?;
    execute(&root.path().join("workspace"), manifest.clone(), OUTPUT, &mut cas).expect_err("unverified intent");
    assert_eq!(cas.retained_intent().ok_or("retained")?.storage_state, artifact_service::StorageState::Quarantined);
    assert!(cas.service_request().is_some()); assert!(cas.service_receipt().is_none());
    assert_eq!(revisions.repository().calls.load(Ordering::SeqCst), 0); Ok(())
}
