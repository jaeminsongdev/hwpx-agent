use super::*;

#[test]
fn exact_engine_json_is_a_distinct_receipt_matching_the_v2_transaction_digest() -> TestResult {
    let f = fixture()?; let context = writer(&f); let manifest = manifest_fixture::manifest(&f, "precommit-v2-digest")?;
    let mut cas = StoredResultRevisionCas::bind(&f.artifacts, &f.revisions, &context, &f.revision_context,
        binding(&f, &manifest, OUTPUT), || 10)?;
    let root = tempfile::tempdir()?; let mut captured = None;
    execute(&root.path().join("workspace"), manifest.clone(), OUTPUT, &mut |request: &EngineRequest| {
        captured = Some(request.clone()); cas.compare_and_swap(request)
    })?;
    let request = captured.ok_or("engine request")?;
    let receipt = cas.retained_precommit().ok_or("precommit")?;
    assert_eq!(receipt.kind, ArtifactKind::Receipt);
    assert_eq!(receipt.file_name.as_str(), "workspace-precommit.json");
    assert_eq!(receipt.media_type.as_str(), "application/json");
    assert_eq!(f.artifacts.download(&context, receipt.artifact_id, 12)?, request.canonical_json()?);
    assert_eq!(receipt.sha256.as_bytes(), &request.canonical_sha256()?);
    assert_eq!(receipt.sha256, cas.service_request().ok_or("service request")?.transaction_receipt_sha256());
    let intent = cas.retained_intent().ok_or("intent")?;
    assert_ne!(receipt.artifact_id, intent.artifact_id); assert_ne!(receipt.sha256, intent.sha256);
    Ok(())
}

#[derive(Debug)]
struct PrecommitDeniedScanner;
impl ArtifactScanner for PrecommitDeniedScanner {
    fn scan(&self, request: ScanRequest<'_>) -> Result<ScanEvidence, artifact_service::ArtifactError> {
        let mut result = FixtureScanner { unavailable: false }.scan(request)?;
        if request.file_name.as_str() == "workspace-precommit.json" {
            result.verdict = ScanVerdict::Unverified(QuarantineReason::parse("FIXTURE_PRECOMMIT_UNVERIFIED")?);
        }
        Ok(result)
    }
}

#[test]
fn unverified_precommit_blocks_intent_and_cas_and_preserves_both_available_and_quarantined_artifacts() -> TestResult {
    let f = fixture()?; let context = writer(&f); let manifest = manifest_fixture::manifest(&f, "precommit-unverified")?;
    let key = KeyReference::parse("fixture.p45-aes")?;
    let artifacts = ArtifactService::new(f.metadata.clone(), f.blobs.clone(), PrecommitDeniedScanner,
        Aes256GcmKeyring::new(key.clone(), [(key, [45; 32])])?,
        DownloadSigner::new("https://fixture.example.test/download", KeyReference::parse("fixture.p45-hmac")?, &[46; 32], 60)?,
        ArtifactServiceConfig::new(32 * 1024 * 1024, 60)?);
    let revisions = FaultRevision::service(&f, 0);
    let mut cas = StoredResultRevisionCas::bind(&artifacts, &revisions, &context, &f.revision_context, binding(&f, &manifest, OUTPUT), || 10)?;
    let root = tempfile::tempdir()?;
    let failure = execute(&root.path().join("workspace"), manifest.clone(), OUTPUT, &mut cas).expect_err("unverified precommit");
    assert_eq!(failure.primary(), TransactionError::RevisionCasFailed);
    assert_eq!(cas.retained_precommit().ok_or("retained")?.storage_state, artifact_service::StorageState::Quarantined);
    assert!(cas.retained_intent().is_none()); assert!(cas.service_receipt().is_none());
    assert_eq!(f.artifacts.download(&context, cas.retained_result().ok_or("result")?.artifact_id, 12)?, OUTPUT);
    assert_eq!(revisions.repository().calls.load(Ordering::SeqCst), 0); Ok(())
}

#[test]
fn precommit_aead_readback_failure_blocks_intent_and_revision_cas() -> TestResult {
    let f = fixture()?; let context = writer(&f); let manifest = manifest_fixture::manifest(&f, "precommit-aead")?;
    let revisions = FaultRevision::service(&f, 0); let clock_calls = Cell::new(0);
    let clock = || { clock_calls.set(clock_calls.get()+1); if clock_calls.get()==7 { f.blobs.tamper.store(true, Ordering::SeqCst); } 10 };
    let mut cas = StoredResultRevisionCas::bind(&f.artifacts, &revisions, &context, &f.revision_context, binding(&f, &manifest, OUTPUT), clock)?;
    let root = tempfile::tempdir()?;
    execute(&root.path().join("workspace"), manifest.clone(), OUTPUT, &mut cas).expect_err("precommit AEAD");
    assert!(cas.retained_precommit().is_some()); assert!(cas.retained_intent().is_none());
    assert_eq!(cas.error(), Some(StoredCommitError::Artifact));
    assert_eq!(revisions.repository().calls.load(Ordering::SeqCst), 0); Ok(())
}

#[test]
fn both_receipts_remain_readable_after_unknown_commit_without_a_second_cas() -> TestResult {
    let f = fixture()?; let context = writer(&f); let manifest = manifest_fixture::manifest(&f, "precommit-unknown")?;
    let revisions = FaultRevision::service(&f, 3);
    let mut cas = StoredResultRevisionCas::bind(&f.artifacts, &revisions, &context, &f.revision_context, binding(&f, &manifest, OUTPUT), || 10)?;
    let root = tempfile::tempdir()?;
    let failure = execute(&root.path().join("workspace"), manifest.clone(), OUTPUT, &mut cas).expect_err("unknown");
    assert_eq!(failure.receipt().state(), TransactionState::Incomplete);
    let precommit = cas.retained_precommit().ok_or("precommit")?; let intent = cas.retained_intent().ok_or("intent")?;
    assert_eq!(ContentDigest::of(&f.artifacts.download(&context, precommit.artifact_id, 12)?), precommit.sha256);
    assert_eq!(ContentDigest::of(&f.artifacts.download(&context, intent.artifact_id, 12)?), intent.sha256);
    assert_eq!(revisions.repository().calls.load(Ordering::SeqCst), 1); Ok(())
}
