//! Real service/owned-disk negatives, not production scanner/keys or SQL admission.
//! Exactly one NEW synthetic control artifact; existing user/source artifacts untouched.
use super::{Probe, ProbeBlobStore, Result};
use artifact_service::{
    Aes256GcmKeyring, ArtifactError, ArtifactKind, ArtifactMetadataRepository, ArtifactPermission,
    ArtifactScanner, ArtifactService, ArtifactServiceConfig, AuthScope, ContentDigest, DownloadSigner,
    EncryptedBlobStore, FileName, IngestRequest, KeyReference, MediaType, QuarantineReason,
    RequestContext, ScanEvidence, ScanRequest, StorageState, SubjectDigest,
};
use ring::rand::{SecureRandom, SystemRandom};
use std::time::{SystemTime, UNIX_EPOCH};

pub(super) const PAYLOAD: &[u8] = br#"{"schema_version":"hwpx-agent.p151-private-negative-fixture/v1","synthetic_test_only":true}"#;
pub(super) const CHECKS: [&str; 8] = [
    "durable_negative_new_fixture_whole_AEAD_disk_read",
    "durable_negative_wrong_key_denied",
    "durable_negative_ACL_grant_fresh_whole_read",
    "durable_negative_ACL_revoke_deny_restore_fresh_read",
    "durable_negative_disk_tag_one_byte_tamper_exact",
    "durable_negative_tampered_disk_ciphertext_denied",
    "durable_negative_quarantine_disk_relocation_and_read_denied",
    "durable_negative_no_head_or_additional_ingest_change",
];

#[derive(Debug)]
struct ControlScanner;
impl ArtifactScanner for ControlScanner {
    fn scan(&self, request: ScanRequest<'_>) -> std::result::Result<ScanEvidence, ArtifactError> {
        if request.bytes != PAYLOAD || request.kind != ArtifactKind::Receipt
            || request.file_name.as_str() != "p151-negative-control.json"
            || request.media_type.as_str() != "application/json"
        {
            return Err(ArtifactError::ScanNotClean);
        }
        super::scan_evidence() // Explicitly synthetic, never production qualification.
    }
}

fn services<R: ArtifactMetadataRepository + Clone>(
    metadata: &R, blobs: &ProbeBlobStore,
) -> Result<(ArtifactService<R, ProbeBlobStore, ControlScanner>, ArtifactService<R, ProbeBlobStore, ControlScanner>)> {
    let random = SystemRandom::new();
    let mut key = [0; 32];
    random.fill(&mut key).map_err(|_| "control_random_unavailable")?;
    let mut wrong = key;
    wrong[0] ^= 1; // Guaranteed different key, same reference/AAD/ciphertext digest.
    let reference = KeyReference::parse("kms.p151-control-ephemeral")?;
    let valid = Aes256GcmKeyring::new(reference.clone(), [(reference.clone(), key)]);
    let invalid = Aes256GcmKeyring::new(reference.clone(), [(reference, wrong)]);
    key.fill(0); wrong.fill(0);
    let construct = |keyring| -> Result<_> {
        let mut hmac = [0; 32];
        random.fill(&mut hmac).map_err(|_| "control_random_unavailable")?;
        let signer = DownloadSigner::new("https://artifact.invalid/v1/download",
            KeyReference::parse("hmac.p151-control-ephemeral")?, &hmac, 60);
        hmac.fill(0);
        Ok(ArtifactService::new(metadata.clone(), blobs.clone(), ControlScanner, keyring, signer?,
            ArtifactServiceConfig::new(1024, 60)?))
    };
    Ok((construct(valid?)?, construct(invalid?)?))
}

fn ingests<R: ArtifactMetadataRepository>(metadata: &R) -> Result<usize> {
    Ok(metadata.audit_events()?.iter().filter(|e| e.event == "artifact.ingested").count())
}

pub(super) fn exercise<R, F>(
    probe: &mut Probe, metadata: &R, blobs: &ProbeBlobStore, owner: &RequestContext, head_unchanged: F,
) -> Result<()>
where R: ArtifactMetadataRepository + Clone, F: Fn() -> Result<bool> {
    if !blobs.is_durable() { return Err("negative_control_requires_owned_local".into()); }
    probe.stage = "durable_negative_new_fixture_admission";
    let digest = ContentDigest::of(PAYLOAD);
    if metadata.find_by_content(owner.tenant_id(), digest)?.is_some() {
        return Err("negative_control_fixture_already_present".into());
    }
    let before = ingests(metadata)?;
    let now = SystemTime::now().duration_since(UNIX_EPOCH)?.as_secs();
    let (service, wrong_key_service) = services(metadata, blobs)?;
    let artifact = service.ingest(owner, IngestRequest { bytes: PAYLOAD.to_vec(),
        file_name: FileName::parse("p151-negative-control.json")?, media_type: MediaType::parse("application/json")?,
        kind: ArtifactKind::Receipt }, now)?;
    let record = metadata.find(owner.tenant_id(), artifact.artifact_id)?.ok_or("negative_control_metadata_missing")?;
    blobs.reopen()?;
    let original = blobs.get(record.object_key())?.ok_or("negative_control_disk_missing")?;
    probe.check(CHECKS[0], original.len() == PAYLOAD.len() + 16 && artifact.sha256 == digest
        && ContentDigest::of(&original) == record.encryption().ciphertext_sha256
        && !original.windows(PAYLOAD.len()).any(|part| part == PAYLOAD)
        && service.download(owner, artifact.artifact_id, now)? == PAYLOAD
        && ingests(metadata)? == before.checked_add(1).ok_or("control_ingest_count_overflow")? && head_unchanged()?)?;
    let baseline = ingests(metadata)?;
    probe.check(CHECKS[1], matches!(wrong_key_service.download(owner, artifact.artifact_id, now), Err(ArtifactError::CryptoFailure)))?;
    let admin = RequestContext::new(owner.tenant_id(), owner.subject(),
        [AuthScope::DocumentRead, AuthScope::DocumentWrite, AuthScope::ArtifactShare, AuthScope::SecurityModify]);
    let guest = RequestContext::new(owner.tenant_id(), SubjectDigest::from_authenticated_subject("p151-private-control-reader")?,
        [AuthScope::DocumentRead]);
    let permissions = [ArtifactPermission::Read].into_iter().collect();
    let granted = service.set_permissions(&admin, artifact.artifact_id, guest.subject(), permissions, now)?;
    blobs.reopen()?;
    probe.check(CHECKS[2], service.download(&guest, artifact.artifact_id, now)? == PAYLOAD)?;
    let revoked = service.set_permissions(&admin, artifact.artifact_id, guest.subject(), Default::default(), now)?;
    let denied = matches!(service.download(&guest, artifact.artifact_id, now), Err(ArtifactError::AccessDenied));
    let restored = service.set_permissions(&admin, artifact.artifact_id, guest.subject(), [ArtifactPermission::Read].into_iter().collect(), now)?;
    blobs.reopen()?;
    probe.check(CHECKS[3], granted < revoked && revoked < restored && denied
        && service.download(&guest, artifact.artifact_id, now)? == PAYLOAD
        && blobs.get(record.object_key())? == Some(original.clone()))?;
    let tampered = blobs.tamper_negative_fixture(&record)?;
    blobs.reopen()?;
    probe.check(CHECKS[4], tampered.len() == original.len()
        && original.iter().zip(&tampered).filter(|(a,b)| a != b).count() == 1
        && original.last().zip(tampered.last()).is_some_and(|(a,b)| a ^ b == 1)
        && ContentDigest::of(&tampered) != record.encryption().ciphertext_sha256
        && blobs.get(record.object_key())? == Some(tampered.clone()))?;
    probe.check(CHECKS[5], matches!(service.download(owner, artifact.artifact_id, now), Err(ArtifactError::IntegrityMismatch)))?;
    let quarantined = service.quarantine(&admin, artifact.artifact_id, QuarantineReason::parse("P151_CONTROL_TAMPER")?, now)?;
    let changed = metadata.find(owner.tenant_id(), artifact.artifact_id)?.ok_or("negative_control_metadata_missing")?;
    blobs.reopen()?;
    probe.check(CHECKS[6], quarantined.storage_state == StorageState::Quarantined
        && blobs.get(record.object_key())?.is_none()
        && blobs.get(changed.object_key())? == Some(tampered)
        && matches!(service.download(owner, artifact.artifact_id, now), Err(ArtifactError::Quarantined)))?;
    probe.check(CHECKS[7], ingests(metadata)? == baseline && head_unchanged()?)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use artifact_service::{InMemoryMetadataRepository, TenantId};
    use uuid::Uuid;

    fn owner() -> Result<RequestContext> {
        Ok(RequestContext::new(TenantId::new(Uuid::new_v4())?,
            SubjectDigest::from_authenticated_subject("p151-owned-control-fixture")?,
            [AuthScope::DocumentRead, AuthScope::DocumentWrite]))
    }

    #[test]
    fn actual_service_local_disk_all_eight_controls_exact() -> Result<()> {
        let metadata = InMemoryMetadataRepository::default();
        let blobs = ProbeBlobStore::negative_unit_fixture()?;
        let mut probe = Probe::default();
        exercise(&mut probe, &metadata, &blobs, &owner()?, || Ok(true))?;
        assert_eq!(probe.checks, CHECKS);
        assert_eq!(ingests(&metadata)?, 1);
        Ok(())
    }

    #[test]
    fn memory_mode_cannot_claim_durable_negative_qualification() -> Result<()> {
        let metadata = InMemoryMetadataRepository::default();
        let blobs = ProbeBlobStore::Memory(super::super::InMemoryBlobStore::default());
        let mut probe = Probe::default();
        assert!(exercise(&mut probe, &metadata, &blobs, &owner()?, || Ok(true)).is_err());
        assert!(probe.checks.is_empty());assert_eq!(ingests(&metadata)?, 0);Ok(())
    }

    #[test]
    fn head_change_never_becomes_negative_controls_pass() -> Result<()> {
        let metadata = InMemoryMetadataRepository::default();
        let blobs = ProbeBlobStore::negative_unit_fixture()?;
        let mut probe = Probe::default();
        assert!(exercise(&mut probe, &metadata, &blobs, &owner()?, || Ok(false)).is_err());
        assert!(probe.checks.is_empty());assert_eq!(probe.stage, CHECKS[0]);Ok(())
    }

    #[test]
    fn already_present_control_is_not_reingested_or_restamped() -> Result<()> {
        let metadata = InMemoryMetadataRepository::default();
        let blobs = ProbeBlobStore::negative_unit_fixture()?;
        let owner = owner()?;let mut probe = Probe::default();
        exercise(&mut probe, &metadata, &blobs, &owner, || Ok(true))?;
        let mut second = Probe::default();
        assert!(exercise(&mut second, &metadata, &blobs, &owner, || Ok(true)).is_err());
        assert!(second.checks.is_empty());assert_eq!(ingests(&metadata)?, 1);Ok(())
    }

    #[test]
    fn synthetic_scanner_rejects_arbitrary_plaintext_or_kind() -> Result<()> {
        let file = FileName::parse("p151-negative-control.json")?;
        let media = MediaType::parse("application/json")?;
        for (bytes, kind) in [(b"not-a-control".as_slice(), ArtifactKind::Receipt), (PAYLOAD, ArtifactKind::Source)] {
            assert!(matches!(ControlScanner.scan(ScanRequest { bytes, kind, file_name: &file, media_type: &media }),
                Err(ArtifactError::ScanNotClean)));
        }
        Ok(())
    }

    #[test]
    fn caller_without_write_scope_is_denied_before_control_ingest() -> Result<()> {
        let metadata = InMemoryMetadataRepository::default();
        let blobs = ProbeBlobStore::negative_unit_fixture()?;
        let owner = owner()?;let readonly = RequestContext::new(owner.tenant_id(), owner.subject(), [AuthScope::DocumentRead]);
        let mut probe = Probe::default();
        assert!(exercise(&mut probe, &metadata, &blobs, &readonly, || Ok(true)).is_err());
        assert!(probe.checks.is_empty());assert_eq!(ingests(&metadata)?, 0);Ok(())
    }

    #[test]
    fn already_tampered_disk_is_not_rewritten_again() -> Result<()> {
        let metadata = InMemoryMetadataRepository::default();
        let blobs = ProbeBlobStore::negative_unit_fixture()?;
        let owner = owner()?;let (service, _) = services(&metadata, &blobs)?;
        let artifact = service.ingest(&owner, IngestRequest { bytes: PAYLOAD.to_vec(),
            file_name: FileName::parse("p151-negative-control.json")?, media_type: MediaType::parse("application/json")?,
            kind: ArtifactKind::Receipt }, 1)?;
        let record = metadata.find(owner.tenant_id(), artifact.artifact_id)?.ok_or("control_missing")?;
        let first = blobs.tamper_negative_fixture(&record)?;
        assert!(matches!(blobs.tamper_negative_fixture(&record), Err(ArtifactError::IntegrityMismatch)));
        assert_eq!(blobs.get(record.object_key())?, Some(first));Ok(())
    }

    #[test]
    fn quarantined_record_cannot_be_selected_for_available_disk_tamper() -> Result<()> {
        let metadata = InMemoryMetadataRepository::default();
        let blobs = ProbeBlobStore::negative_unit_fixture()?;
        let owner = owner()?;let mut probe = Probe::default();
        exercise(&mut probe, &metadata, &blobs, &owner, || Ok(true))?;
        let record = metadata.find_by_content(owner.tenant_id(), ContentDigest::of(PAYLOAD))?.ok_or("control_missing")?;
        let before = blobs.get(record.object_key())?;
        assert!(matches!(blobs.tamper_negative_fixture(&record), Err(ArtifactError::InvalidState)));
        assert_eq!(blobs.get(record.object_key())?, before);assert_eq!(ingests(&metadata)?, 1);Ok(())
    }
}
