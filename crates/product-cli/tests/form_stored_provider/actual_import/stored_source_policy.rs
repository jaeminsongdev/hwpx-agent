//! Synthetic repository/scanner authority; actual encryption/service/parser/source-binding tests.
use super::super::{FaultBlob, FixtureScanner, StoredFixture};
use super::*;
use artifact_service::{
    Aes256GcmKeyring, ArtifactPermission, ArtifactService, ArtifactServiceConfig, DownloadSigner,
    EncryptedBlobStore, FileName, IngestRequest, KeyReference, MediaType, ObjectKey,
    QuarantineReason, SubjectDigest,
};
use hwpx_agent_cli::form_stored_provider::actual_import::source_policy::*;
use std::sync::{
    Mutex,
    atomic::{AtomicBool, AtomicUsize},
};
use uuid::Uuid;

#[derive(Debug)]
struct FixtureRepository {
    row: Mutex<SourcePolicyVersion>,
    subject: SubjectDigest,
    deny: AtomicBool,
    calls: AtomicUsize,
    deny_after_first: AtomicBool,
}
impl SourcePolicyRepository for FixtureRepository {
    fn read_current(
        &self,
        s: &PolicyReadScope,
    ) -> Result<SourcePolicyVersion, StoredSourcePolicyError> {
        let n = self.calls.fetch_add(1, Ordering::SeqCst);
        if self.deny.load(Ordering::SeqCst)
            || (self.deny_after_first.load(Ordering::SeqCst) && n > 0)
            || s.subject() != self.subject
        {
            return Err(StoredSourcePolicyError::Repository);
        }
        let row = self
            .row
            .lock()
            .map_err(|_| StoredSourcePolicyError::Repository)?
            .clone();
        // Tests deliberately allow corrupt row bindings to exercise the consumer's own checks.
        Ok(row)
    }
}
fn binding(
    stored: &StoredFixture,
    imported: &ImportedDocumentForms,
) -> Result<SourcePolicyBinding, Box<dyn std::error::Error>> {
    Ok(SourcePolicyBinding {
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
        policy_version: Uuid::from_u128(8301),
        policy_generation: 1,
        creator_subject: stored.owner.subject(),
    })
}
fn envelope(b: &SourcePolicyBinding, imported: &ImportedDocumentForms) -> serde_json::Value {
    serde_json::json!({"schema_version": SOURCE_POLICY_PAYLOAD_SCHEMA,
        "binding": b, "policies": explicit_test_policies(imported)})
}
fn repository(
    stored: &StoredFixture,
    b: SourcePolicyBinding,
    bytes: Vec<u8>,
    kind: ArtifactKind,
    media: &str,
) -> Result<FixtureRepository, Box<dyn std::error::Error>> {
    let d = stored.artifacts.ingest(
        &stored.owner,
        IngestRequest {
            bytes,
            media_type: MediaType::parse(media)?,
            file_name: FileName::parse("fixture-policy.json")?,
            kind,
        },
        7,
    )?;
    stored.artifacts.set_permissions(
        &stored.owner,
        d.artifact_id,
        stored.reader.subject(),
        BTreeSet::from([ArtifactPermission::Read]),
        8,
    )?;
    Ok(FixtureRepository {
        row: Mutex::new(SourcePolicyVersion {
            binding: b,
            artifact: d.artifact_id,
            digest: d.sha256,
        }),
        subject: stored.reader.subject(),
        deny: AtomicBool::new(false),
        calls: AtomicUsize::new(0),
        deny_after_first: AtomicBool::new(false),
    })
}
fn new_fixture() -> Result<StoredFixture, Box<dyn std::error::Error>> {
    StoredFixture::new(
        &fixture_bytes("five-kinds", "source")?,
        ArtifactKind::Result,
        false,
    )
}
fn valid_repository(
    stored: &StoredFixture,
    imported: &ImportedDocumentForms,
) -> Result<FixtureRepository, Box<dyn std::error::Error>> {
    let b = binding(stored, imported)?;
    let bytes = serde_json::to_vec(&envelope(&b, imported))?;
    repository(
        stored,
        b,
        bytes,
        ArtifactKind::Evidence,
        SOURCE_POLICY_MEDIA_TYPE,
    )
}
#[test]
fn actual_ten_sources_stored_encrypted_policy_matches_whole_original_component_no_writes()
-> TestResult {
    let (_, manifest) = fixture_manifest()?;
    let mut cases = 0;
    for row in manifest["cases"].as_array().ok_or("cases")? {
        for kind in ["source", "output"] {
            let stored = StoredFixture::new(
                &fixture_bytes(row["case"].as_str().ok_or("case")?, kind)?,
                ArtifactKind::Result,
                false,
            )?;
            let provider = stored.provider()?;
            let imported = provider.import_actual_forms(stored.head, 4)?;
            let repo = valid_repository(&stored, imported.imported())?;
            let bound = imported.bind_stored_policies(&provider, &repo, 9)?;
            let explicit = PolicyBoundDocumentForms::bind(
                imported.imported(),
                &FormPolicySourceBinding::for_imported(imported.imported()),
                &explicit_test_policies(imported.imported()),
            )?;
            assert_eq!(bound.graph(), explicit.graph());
            assert_eq!(bound.state(), explicit.state());
            assert_eq!(bound.receipt().policy, *explicit.receipt());
            assert_eq!(bound.verify(&provider, &repo, 10)?, *bound.receipt());
            assert_eq!(format!("{bound:?}"), "StoredSourceFormPolicies(<redacted>)");
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
                3
            );
            assert!(bound.receipt().qualification.contains("not_sql_adapter"));
            cases += 1;
        }
    }
    assert_eq!(cases, 10);
    Ok(())
}
#[test]
fn consumer_rejects_every_foreign_or_stale_repository_binding() -> TestResult {
    let stored = new_fixture()?;
    let provider = stored.provider()?;
    let imported = provider.import_actual_forms(stored.head, 4)?;
    for i in 0..16 {
        let repo = valid_repository(&stored, imported.imported())?;
        {
            let mut row = repo.row.lock().map_err(|_| "row")?;
            let b = &mut row.binding;
            match i {
                0 => b.tenant = TenantId::new(Uuid::from_u128(999))?,
                1 => b.project = revision_service::ProjectId::generate(),
                2 => b.branch = revision_service::BranchId::generate(),
                3 => b.document = DocumentId::parse("foreign-document")?,
                4 => b.source_revision = revision_service::RevisionId::generate(),
                5 => b.source_head_generation += 1,
                6 => b.source_result_artifact = artifact_service::ArtifactId::generate(),
                7 => b.source_package_sha256 = ContentDigest::of(b"bad-package"),
                8 => b.source_provenance_sha256 = ContentDigest::of(b"bad-provenance"),
                9 => b.observed_graph_sha256 = ContentDigest::of(b"bad-graph"),
                10 => b.policy_version = Uuid::nil(),
                11 => b.policy_generation = 0,
                12 => b.policy_generation = u64::MAX,
                13 => row.artifact = stored.result,
                14 => row.digest = ContentDigest::of(b"wrong-policy"),
                _ => {
                    b.creator_subject =
                        SubjectDigest::from_authenticated_subject("different-author")?;
                }
            }
        }
        assert!(
            imported.bind_stored_policies(&provider, &repo, 9).is_err(),
            "binding mutation {i}"
        );
    }
    Ok(())
}
#[test]
fn strict_payload_rejects_unknown_missing_duplicate_and_unbound_fields_no_defaults() -> TestResult {
    let stored = new_fixture()?;
    let provider = stored.provider()?;
    let imported = provider.import_actual_forms(stored.head, 4)?;
    let b = binding(&stored, imported.imported())?;
    let base = envelope(&b, imported.imported());
    for i in 0..21 {
        let mut raw = base.clone();
        match i {
            0 => raw["schema_version"] = "unsupported".into(),
            1 => raw["caller_approved"] = true.into(),
            2 => raw["binding"]["unknown"] = true.into(),
            3 => {
                raw.as_object_mut().ok_or("object")?.remove("binding");
            }
            4 => {
                raw.as_object_mut().ok_or("object")?.remove("policies");
            }
            5 => raw["policies"][0]["values"]["value"] = "forged-current-value".into(),
            6 => {
                raw["policies"][0]["values"]["validation"]
                    .as_object_mut()
                    .ok_or("validation")?
                    .remove("maximum_characters");
            }
            7 => {
                raw["policies"][0]["values"]["validation"]
                    .as_object_mut()
                    .ok_or("validation")?
                    .remove("external_validator_sha256");
            }
            8 => {
                raw["policies"][0]["values"]["validation"]
                    .as_object_mut()
                    .ok_or("validation")?
                    .remove("required");
            }
            9 => raw["policies"][0]["values"]["validation"]["unknown"] = true.into(),
            10 => raw["policies"][0]["unknown"] = true.into(),
            11 => raw["policies"][0]["source_anchor"]["unknown"] = true.into(),
            12 => raw["policies"][0]["values"]["kind"] = "date".into(),
            13 => raw["binding"]["policy_generation"] = 2.into(),
            14 => raw["policies"][0]["node_id"] = "foreign-node".into(),
            15 => raw["policies"][0]["source_anchor"]["fingerprint_sha256"][0] = 99.into(),
            16 => {
                raw["policies"].as_array_mut().ok_or("array")?.swap(0, 1);
            }
            17 => {
                let p = raw["policies"][0].clone();
                raw["policies"].as_array_mut().ok_or("array")?.push(p);
            }
            18 => {
                raw["policies"].as_array_mut().ok_or("array")?.clear();
            }
            19 => raw["policies"][0]["values"]["validation"]["minimum_characters"] = 100.into(),
            _ => raw["policies"][0]["values"]["validation"]["maximum_characters"] = 0.into(),
        }
        let repo = repository(
            &stored,
            b.clone(),
            serde_json::to_vec(&raw)?,
            ArtifactKind::Evidence,
            SOURCE_POLICY_MEDIA_TYPE,
        )?;
        assert!(
            imported.bind_stored_policies(&provider, &repo, 9).is_err(),
            "payload mutation {i}"
        );
    }
    let canonical = serde_json::to_string(&base)?;
    let duplicate = canonical.replacen(
        "\"schema_version\":",
        "\"schema_version\":\"duplicate\",\"schema_version\":",
        1,
    );
    for bytes in [
        duplicate.into_bytes(),
        format!("{canonical} {{}}").into_bytes(),
        b"{invalid".to_vec(),
        vec![b' '; 1024 * 1024 + 1],
    ] {
        let repo = repository(
            &stored,
            b.clone(),
            bytes,
            ArtifactKind::Evidence,
            SOURCE_POLICY_MEDIA_TYPE,
        )?;
        assert!(imported.bind_stored_policies(&provider, &repo, 9).is_err());
    }
    Ok(())
}
#[test]
fn wrong_media_or_artifact_role_never_becomes_policy() -> TestResult {
    for (kind, media) in [
        (ArtifactKind::Evidence, "application/json"),
        (ArtifactKind::Result, SOURCE_POLICY_MEDIA_TYPE),
        (ArtifactKind::Source, SOURCE_POLICY_MEDIA_TYPE),
        (ArtifactKind::DocumentIr, SOURCE_POLICY_MEDIA_TYPE),
    ] {
        let stored = new_fixture()?;
        let provider = stored.provider()?;
        let imported = provider.import_actual_forms(stored.head, 4)?;
        let b = binding(&stored, imported.imported())?;
        let bytes = serde_json::to_vec(&envelope(&b, imported.imported()))?;
        let repo = repository(&stored, b.clone(), bytes.clone(), kind, media)?;
        assert_eq!(
            imported.bind_stored_policies(&provider, &repo, 9).err(),
            Some(StoredSourcePolicyError::Artifact)
        );
    }
    Ok(())
}
#[test]
fn latest_policy_revocation_is_checked_during_create_and_cached_verification() -> TestResult {
    let stored = new_fixture()?;
    let provider = stored.provider()?;
    let imported = provider.import_actual_forms(stored.head, 4)?;
    let repo = valid_repository(&stored, imported.imported())?;
    repo.deny_after_first.store(true, Ordering::SeqCst);
    assert_eq!(
        imported.bind_stored_policies(&provider, &repo, 9).err(),
        Some(StoredSourcePolicyError::Repository)
    );
    repo.deny_after_first.store(false, Ordering::SeqCst);
    let bound = imported.bind_stored_policies(&provider, &repo, 9)?;
    repo.deny.store(true, Ordering::SeqCst);
    assert_eq!(
        bound.verify(&provider, &repo, 10).err(),
        Some(StoredSourcePolicyError::Repository)
    );
    assert_eq!(
        imported.bind_stored_policies(&provider, &repo, 10).err(),
        Some(StoredSourcePolicyError::Repository)
    );
    Ok(())
}
#[test]
fn cached_policy_rechecks_both_acls_policy_quarantine_and_source_head() -> TestResult {
    for i in 0..4 {
        let stored = new_fixture()?;
        let provider = stored.provider()?;
        let imported = provider.import_actual_forms(stored.head, 4)?;
        let repo = valid_repository(&stored, imported.imported())?;
        let bound = imported.bind_stored_policies(&provider, &repo, 9)?;
        let policy = repo.row.lock().map_err(|_| "row")?.artifact;
        match i {
            0 | 1 => {
                stored.artifacts.set_permissions(
                    &stored.owner,
                    if i == 0 { policy } else { stored.result },
                    stored.reader.subject(),
                    BTreeSet::new(),
                    10,
                )?;
            }
            2 => {
                stored.artifacts.quarantine(
                    &stored.owner,
                    policy,
                    QuarantineReason::parse("POLICY_FIXTURE_QUARANTINE")?,
                    10,
                )?;
            }
            _ => stored.advance()?,
        }
        assert!(bound.verify(&provider, &repo, 11).is_err());
        assert!(imported.bind_stored_policies(&provider, &repo, 11).is_err());
    }
    Ok(())
}

#[test]
fn strict_nested_duplicates_and_missing_nullable_selection_fields_are_rejected() -> TestResult {
    let stored = new_fixture()?;
    let provider = stored.provider()?;
    let imported = provider.import_actual_forms(stored.head, 4)?;
    let b = binding(&stored, imported.imported())?;
    let base = envelope(&b, imported.imported());
    for kind in ["combo", "list"] {
        for field in ["default_selected_value", "external_validator_sha256"] {
            let mut raw = base.clone();
            let values = raw["policies"]
                .as_array_mut()
                .ok_or("policies")?
                .iter_mut()
                .find(|p| p["values"]["kind"] == kind)
                .ok_or("selection")?
                .get_mut("values")
                .ok_or("values")?;
            if field == "default_selected_value" {
                values.as_object_mut().ok_or("object")?.remove(field);
            } else {
                values["validation"]
                    .as_object_mut()
                    .ok_or("validation")?
                    .remove(field);
            }
            let repo = repository(
                &stored,
                b.clone(),
                serde_json::to_vec(&raw)?,
                ArtifactKind::Evidence,
                SOURCE_POLICY_MEDIA_TYPE,
            )?;
            assert_eq!(
                imported.bind_stored_policies(&provider, &repo, 9).err(),
                Some(StoredSourcePolicyError::Payload)
            );
        }
    }
    let canonical = serde_json::to_string(&base)?;
    for (old, new) in [
        (
            "\"policy_generation\":1",
            "\"policy_generation\":1,\"policy_generation\":1",
        ),
        ("\"kind\":\"text\"", "\"kind\":\"text\",\"kind\":\"text\""),
        (
            "\"required\":false",
            "\"required\":false,\"required\":false",
        ),
        (
            "\"default_value\":\"\"",
            "\"default_value\":\"\",\"default_value\":\"\"",
        ),
    ] {
        assert!(canonical.contains(old));
        let raw = canonical.replacen(old, new, 1);
        let repo = repository(
            &stored,
            b.clone(),
            raw.into_bytes(),
            ArtifactKind::Evidence,
            SOURCE_POLICY_MEDIA_TYPE,
        )?;
        assert_eq!(
            imported.bind_stored_policies(&provider, &repo, 9).err(),
            Some(StoredSourcePolicyError::Payload)
        );
    }
    Ok(())
}
#[test]
fn new_latest_valid_policy_can_be_loaded_but_cached_old_version_is_stale() -> TestResult {
    let stored = new_fixture()?;
    let provider = stored.provider()?;
    let imported = provider.import_actual_forms(stored.head, 4)?;
    let old = valid_repository(&stored, imported.imported())?;
    let bound = imported.bind_stored_policies(&provider, &old, 9)?;
    let mut b = binding(&stored, imported.imported())?;
    b.policy_version = Uuid::from_u128(8302);
    b.policy_generation = 2;
    let latest = repository(
        &stored,
        b.clone(),
        serde_json::to_vec(&envelope(&b, imported.imported()))?,
        ArtifactKind::Evidence,
        SOURCE_POLICY_MEDIA_TYPE,
    )?;
    assert_eq!(
        imported
            .bind_stored_policies(&provider, &latest, 10)?
            .receipt()
            .policy_generation,
        2
    );
    assert_eq!(
        bound.verify(&provider, &latest, 10).err(),
        Some(StoredSourcePolicyError::Drift)
    );
    Ok(())
}
#[test]
fn cached_policy_from_another_authenticated_provider_is_denied_before_policy_read() -> TestResult {
    let stored = new_fixture()?;
    let provider = stored.provider()?;
    let imported = provider.import_actual_forms(stored.head, 4)?;
    let repo = valid_repository(&stored, imported.imported())?;
    let bound = imported.bind_stored_policies(&provider, &repo, 9)?;
    let before = repo.calls.load(Ordering::SeqCst);
    let rc = revision_service::RevisionRequestContext::new(
        stored.owner.tenant_id(),
        stored.owner.subject(),
    );
    let foreign = StoredFormProvider::bind(
        &stored.artifacts,
        &stored.revisions,
        &stored.owner,
        &rc,
        stored.project,
        stored.branch,
        DocumentId::parse("actual-form-document")?,
    )?;
    assert_eq!(
        bound.verify(&foreign, &repo, 10).err(),
        Some(StoredSourcePolicyError::Source)
    );
    assert_eq!(repo.calls.load(Ordering::SeqCst), before);
    Ok(())
}

#[test]
fn unverified_policy_scan_is_denied_while_original_source_remains_readable() -> TestResult {
    let stored = new_fixture()?;
    let provider = stored.provider()?;
    let imported = provider.import_actual_forms(stored.head, 4)?;
    let b = binding(&stored, imported.imported())?;
    let scanner_unavailable =
        super::super::fixture_artifacts(stored.metadata.clone(), stored.blobs.clone(), true)?;
    let d = scanner_unavailable.ingest(
        &stored.owner,
        IngestRequest {
            bytes: serde_json::to_vec(&envelope(&b, imported.imported()))?,
            media_type: MediaType::parse(SOURCE_POLICY_MEDIA_TYPE)?,
            file_name: FileName::parse("unverified-policy.json")?,
            kind: ArtifactKind::Evidence,
        },
        7,
    )?;
    stored.artifacts.set_permissions(
        &stored.owner,
        d.artifact_id,
        stored.reader.subject(),
        BTreeSet::from([ArtifactPermission::Read]),
        8,
    )?;
    let repo = FixtureRepository {
        row: Mutex::new(SourcePolicyVersion {
            binding: b,
            artifact: d.artifact_id,
            digest: d.sha256,
        }),
        subject: stored.reader.subject(),
        deny: AtomicBool::new(false),
        calls: AtomicUsize::new(0),
        deny_after_first: AtomicBool::new(false),
    };
    assert!(imported.verify(&provider, 9).is_ok());
    assert_eq!(
        imported.bind_stored_policies(&provider, &repo, 9).err(),
        Some(StoredSourcePolicyError::Artifact)
    );
    Ok(())
}

#[derive(Debug)]
struct EvidenceTamperBlob(FaultBlob);
impl EncryptedBlobStore for EvidenceTamperBlob {
    fn put_if_absent(
        &self,
        key: &ObjectKey,
        bytes: &[u8],
    ) -> Result<(), artifact_service::ArtifactError> {
        self.0.put_if_absent(key, bytes)
    }
    fn get(&self, key: &ObjectKey) -> Result<Option<Vec<u8>>, artifact_service::ArtifactError> {
        let mut bytes = self.0.get(key)?;
        if key.as_str().split('/').nth(3) == Some("evidence")
            && let Some(b) = &mut bytes
            && let Some(first) = b.first_mut()
        {
            *first ^= 1;
        }
        Ok(bytes)
    }
    fn relocate_if_absent(
        &self,
        source: &ObjectKey,
        target: &ObjectKey,
    ) -> Result<(), artifact_service::ArtifactError> {
        self.0.relocate_if_absent(source, target)
    }
}
#[test]
fn policy_only_ciphertext_tamper_fails_with_original_source_read_still_valid() -> TestResult {
    let stored = new_fixture()?;
    let provider = stored.provider()?;
    let imported = provider.import_actual_forms(stored.head, 4)?;
    let repo = valid_repository(&stored, imported.imported())?;
    let bound = imported.bind_stored_policies(&provider, &repo, 9)?;
    let r = KeyReference::parse("fixture.p45-aes")?;
    let artifacts = ArtifactService::new(
        stored.metadata.clone(),
        EvidenceTamperBlob(stored.blobs.clone()),
        FixtureScanner { unavailable: false },
        Aes256GcmKeyring::new(r.clone(), [(r, [45; 32])])?,
        DownloadSigner::new(
            "https://fixture.example.test/download",
            KeyReference::parse("fixture.p45-hmac")?,
            &[46; 32],
            60,
        )?,
        ArtifactServiceConfig::new(32 * 1024 * 1024, 60)?,
    );
    let p = StoredFormProvider::bind(
        &artifacts,
        &stored.revisions,
        &stored.reader,
        &stored.revision_context,
        stored.project,
        stored.branch,
        DocumentId::parse("actual-form-document")?,
    )?;
    assert!(imported.verify(&p, 10).is_ok());
    assert_eq!(
        imported.bind_stored_policies(&p, &repo, 10).err(),
        Some(StoredSourcePolicyError::Artifact)
    );
    assert_eq!(
        bound.verify(&p, &repo, 10).err(),
        Some(StoredSourcePolicyError::Artifact)
    );
    Ok(())
}
